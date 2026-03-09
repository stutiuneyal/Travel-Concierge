from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from pydantic import BaseModel, Field, field_validator
from typing import List,Optional,Dict, Any
import logging
import uuid
import time
import re

from workflow import build_workflow  # must expose `workflow` object

AGENT_NAME_MAP = {
    "time": "Time Agent",
    "holidays": "Holidays Agent",
    "holiday": "Holidays Agent",
    "fx": "FX Agent",
    "exchange_rate": "FX Agent",
    "country_facts": "Country Facts Agent",
    "facts": "Country Facts Agent",
    "router": "Router"
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Travel Concierge", version="1.0.0")

# Serve static assets
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve HTML templates
templates = Jinja2Templates(directory="templates")


class AskRequest(BaseModel):
    query: str = Field(...,min_length=6,max_length=1600)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value:str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("Query cannot be empty.")
        return normalized

class AgentOutput(BaseModel):
    name: str
    content: str


class AskResponse(BaseModel):
    request_id: str
    final_answer: str
    classifications: List[str] = Field(default_factory=list)
    agents_used: List[str] = Field(default_factory=list)
    agent_outputs: List[AgentOutput] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    freshness: Optional[str] = None
    latency_ms: int = 0


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    
    initial_state: Dict[str,Any] = {
        "query": req.query,
        "classifications": [],
        "results":[],
        "final_answer":"",
        "sources":[],
        "freshness": None,
        "agents_used":[]
    }
    
    try:
        logger.info("ask request started request_id=%s query=%s", request_id, req.query)
        
        workflow = build_workflow()
        out = workflow.invoke(initial_state)

        latency_ms = int((time.perf_counter() - start) * 1000)

        classifications = normalize_classifications(out.get("classifications", []))
        agent_outputs = normalize_agent_outputs(out.get("results", []), classifications)
        agents_used = derive_agents_used(classifications, agent_outputs)
        sources = normalize_sources(out.get("sources", []))
        freshness = normalize_freshness(out.get("freshness"))

        response = AskResponse(
            request_id=request_id,
            final_answer=str(out.get("final_answer", "") or ""),
            classifications=classifications,
            agents_used=agents_used,
            agent_outputs=agent_outputs,
            sources=sources,
            freshness=freshness,
            latency_ms=latency_ms,
        )

        logger.info(
            "ask request completed request_id=%s latency_ms=%s agents_used=%s",
            request_id,
            latency_ms,
            agents_used,
        )

        return response

    except Exception as exc:
        logger.exception("ask request failed request_id=%s", request_id)
        raise HTTPException(
            status_code=500,
            detail="Unable to process the travel request right now."
        ) from exc

def normalize_classifications(raw: Any) -> List[str]:
    if not isinstance(raw, list):
        return []

    normalized: List[str] = []
    for item in raw:
        if item is None:
            continue
        text = str(item).strip()
        if text:
            normalized.append(text)
    return normalized

def prettify_agent_name(value: str) -> str:
    logger.info("agent_name value: %s", value)
    key = value.strip().lower().replace(" ", "_").replace("-", "_")
    if key in AGENT_NAME_MAP:
        return AGENT_NAME_MAP[key]

    text = value.strip().replace("_", " ").replace("-", " ")
    return " ".join(word.capitalize() for word in text.split())


def is_generic_agent_name(value: str) -> bool:
    return bool(re.fullmatch(r"Agent \d+", value.strip()))

def normalize_agent_outputs(raw_results: Any, classifications: List[str]) -> List[AgentOutput]:
    if not isinstance(raw_results, list):
        return []

    outputs: List[AgentOutput] = []

    for index, item in enumerate(raw_results):
        fallback_from_classification = (
            prettify_agent_name(classifications[index])
            if index < len(classifications) and classifications[index]
            else "Workflow Step"
        )

        if isinstance(item, dict):
            raw_name = item.get("name") or item.get("agent") or fallback_from_classification
            content = str(item.get("content") or item.get("result") or item.get("output") or "")
        else:
            raw_name = fallback_from_classification
            content = str(item)

        name = str(raw_name).strip() or "Workflow Step"
        content = content.strip()

        if content:
            outputs.append(AgentOutput(name=name, content=content))

    return outputs

def derive_agents_used(classifications: List[str], agent_outputs: List[AgentOutput]) -> List[str]:
    ordered: List[str] = []

    for item in classifications:
        pretty = prettify_agent_name(item)
        if pretty and not is_generic_agent_name(pretty) and pretty not in ordered:
            ordered.append(pretty)

    for output in agent_outputs:
        pretty = prettify_agent_name(output.name)
        if pretty and not is_generic_agent_name(pretty) and pretty not in ordered:
            ordered.append(pretty)

    return ordered


def normalize_sources(raw: Any) -> List[str]:
    if not isinstance(raw, list):
        return []

    sources: List[str] = []
    for item in raw:
        if item is None:
            continue
        text = str(item).strip()
        if text:
            sources.append(text)
    return sources

def normalize_freshness(raw: Any) -> Optional[str]:
    if raw is None:
        return None

    text = str(raw).strip()
    return text or None