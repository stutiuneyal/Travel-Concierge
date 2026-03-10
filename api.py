from contextlib import asynccontextmanager
from pathlib import Path
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from pydantic import BaseModel, Field, field_validator
from langchain_core.messages import HumanMessage

from workflow import build_workflow


AGENT_NAME_MAP = {
    'flight': 'Flight Agent',
    'hotel': 'Hotel Agent',
    'weather': 'Weather Agent',
    'places': 'Places Agent',
    'budget': 'Budget Agent',
    'itinerary': 'Itinerary Agent',
    'visa': 'Visa Info Agent',
    'pdf': 'PDF Agent',
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
workflow = None


class AskRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1600)
    session_id: Optional[str] = None
    user_id: Optional[str] = None

    @field_validator('query')
    @classmethod
    def validate_query(cls, value: str) -> str:
        normalized = ' '.join(value.strip().split())
        if not normalized:
            raise ValueError('Query cannot be empty.')
        return normalized


class AgentOutput(BaseModel):
    name: str
    content: str


class AskResponse(BaseModel):
    request_id: str
    session_id: str
    final_answer: str
    classifications: List[str] = Field(default_factory=list)
    agents_used: List[str] = Field(default_factory=list)
    agent_outputs: List[AgentOutput] = Field(default_factory=list)
    latency_ms: int = 0
    pdf_url: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global workflow
    workflow = await build_workflow()
    logger.info('workflow initialized successfully')
    yield


app = FastAPI(title='Travel Concierge', version='1.0.0', lifespan=lifespan)
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')


@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@app.get('/api/health')
async def health() -> Dict[str, str]:
    return {'status': 'ok'}


@app.get('/downloads/{filename}')
async def download_file(filename: str):
    path = Path('generated') / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail='File not found')
    return FileResponse(path)


@app.post('/api/ask', response_model=AskResponse)
async def ask(req: AskRequest) -> AskResponse:
    global workflow

    if workflow is None:
        raise HTTPException(status_code=503, detail='Workflow is not initialized yet.')

    request_id = str(uuid.uuid4())
    session_id = req.session_id or str(uuid.uuid4())
    start = time.perf_counter()

    initial_state: Dict[str, Any] = {
        'query': req.query,
        'session_id': session_id,
        'messages': [HumanMessage(content=req.query)],
        'results': [],
        'routes': [],
    }
    if req.user_id:
        initial_state['user_id'] = req.user_id

    try:
        out = await workflow.ainvoke(initial_state, config={'configurable': {'thread_id': session_id}})
        latency_ms = int((time.perf_counter() - start) * 1000)

        classifications = [item.get('source', '') for item in out.get('routes', []) if isinstance(item, dict)]
        agent_outputs = []
        agents_used = []
        for item in out.get('results', []):
            if not isinstance(item, dict):
                continue
            source = item.get('source', '')
            pretty = AGENT_NAME_MAP.get(source, source.title() or 'Agent')
            agent_outputs.append(AgentOutput(name=pretty, content=item.get('result', '')))
            if pretty not in agents_used:
                agents_used.append(pretty)

        return AskResponse(
            request_id=request_id,
            session_id=session_id,
            final_answer=out.get('final_answer', ''),
            classifications=classifications,
            agents_used=agents_used,
            agent_outputs=agent_outputs,
            latency_ms=latency_ms,
            pdf_url=out.get('pdf_url'),
        )
    except Exception as exc:
        logger.exception('ask request failed request_id=%s', request_id)
        raise HTTPException(status_code=500, detail='Unable to process the travel request right now.') from exc
