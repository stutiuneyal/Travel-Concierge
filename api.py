from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from langchain_core.messages import HumanMessage
import logging
import uuid
import time
import re

from workflow import build_workflow

AGENT_NAME_MAP = {
    "time": "Time Agent",
    "holidays": "Holidays Agent",
    "holiday": "Holidays Agent",
    "fx": "FX Agent",
    "exchange_rate": "FX Agent",
    "country": "Country Facts Agent",
    "country_facts": "Country Facts Agent",
    "facts": "Country Facts Agent",
    "router": "Router",
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

workflow = None


class AskRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1600)
    session_id: Optional[str] = Field(
        default=None,
        description="Conversation/session id used for LangGraph thread persistence",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="Optional user id for future long-term memory",
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("Query cannot be empty.")
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
    sources: List[str] = Field(default_factory=list)
    freshness: Optional[str] = None
    latency_ms: int = 0

@asynccontextmanager
async def lifespan(app: FastAPI):
    global workflow
    workflow = build_workflow()
    logger.info("workflow initialized successfully")
    yield


app = FastAPI(title="Travel Concierge", version="1.0.0", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/ask", response_model=AskResponse)
async def ask(req: AskRequest) -> AskResponse:
    global workflow

    if workflow is None:
        raise HTTPException(status_code=503, detail="Workflow is not initialized yet.")

    request_id = str(uuid.uuid4())
    session_id = req.session_id or str(uuid.uuid4())
    start = time.perf_counter()

    initial_state: Dict[str, Any] = {
        "query": req.query,
        "messages": [HumanMessage(content=req.query)],
        "results": [],
        "final_answer": "",
        "routes": [],
    }

    if req.user_id:
        initial_state["user_id"] = req.user_id

    config = {
        "configurable": {
            "thread_id": session_id
        }
    }

    try:
        logger.info(
            "ask request started request_id=%s session_id=%s query=%s",
            request_id,
            session_id,
            req.query,
        )

        out = await workflow.ainvoke(initial_state, config=config)

        latency_ms = int((time.perf_counter() - start) * 1000)

        classifications = normalize_classifications_from_routes(out.get("routes", []))
        agent_outputs = normalize_agent_outputs(out.get("results", []), classifications)
        agents_used = derive_agents_used(classifications, agent_outputs)

        # Your current workflow does not explicitly return sources/freshness.
        # Keeping response shape stable.
        sources = normalize_sources(out.get("sources", []))
        freshness = normalize_freshness(out.get("freshness"))

        response = AskResponse(
            request_id=request_id,
            session_id=session_id,
            final_answer=str(out.get("final_answer", "") or ""),
            classifications=classifications,
            agents_used=agents_used,
            agent_outputs=agent_outputs,
            sources=sources,
            freshness=freshness,
            latency_ms=latency_ms,
        )

        logger.info(
            "ask request completed request_id=%s session_id=%s latency_ms=%s agents_used=%s",
            request_id,
            session_id,
            latency_ms,
            agents_used,
        )

        return response

    except Exception as exc:
        logger.exception(
            "ask request failed request_id=%s session_id=%s",
            request_id,
            session_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to process the travel request right now.",
        ) from exc


def normalize_classifications_from_routes(raw_routes: Any) -> List[str]:
    if not isinstance(raw_routes, list):
        return []

    normalized: List[str] = []
    for item in raw_routes:
        if not isinstance(item, dict):
            continue
        source = str(item.get("source", "")).strip()
        if source:
            normalized.append(source)
    return normalized


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
            raw_name = (
                item.get("name")
                or item.get("agent")
                or item.get("source")
                or fallback_from_classification
            )
            content = str(
                item.get("content")
                or item.get("result")
                or item.get("output")
                or ""
            )
        else:
            raw_name = fallback_from_classification
            content = str(item)

        name = prettify_agent_name(str(raw_name).strip() or "Workflow Step")
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