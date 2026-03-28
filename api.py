from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timezone
import logging
import os
import re
import time
import uuid
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from pydantic import BaseModel, Field, field_validator
from langchain_core.messages import HumanMessage

from auth.auth import get_current_user
from workflow import build_workflow
from repository.chat_repository import ChatRepository

load_dotenv()

AGENT_NAME_MAP = {
    "flight": "Flight Agent",
    "hotel": "Hotel Agent",
    "weather": "Weather Agent",
    "places": "Places Agent",
    "budget": "Budget Agent",
    "itinerary": "Itinerary Agent",
    "visa": "Visa Info Agent",
    "pdf": "PDF Agent",
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

workflow = None
chat_repo = None

STOPWORDS = {
    "i", "im", "i’m", "am", "the", "a", "an", "to", "for", "of", "on", "in",
    "my", "me", "please", "tell", "give", "show", "what", "how", "when",
    "is", "are", "was", "were", "next", "this", "that", "about", "and",
    "or", "with", "trip", "traveling", "travelling"
}

TOPIC_HINTS = {
    "itinerary": "Itinerary",
    "budget": "Budget",
    "visa": "Visa",
    "weather": "Weather",
    "holiday": "Holidays",
    "holidays": "Holidays",
    "currency": "Currency",
    "exchange": "Exchange Rate",
    "rate": "Exchange Rate",
    "time": "Local Time",
    "timezone": "Local Time",
    "flight": "Flights",
    "hotel": "Hotels",
    "hotels": "Hotels",
    "places": "Places to Visit",
    "facts": "Travel Facts",
}


def generate_chat_title(query: str) -> str:
    cleaned = " ".join(query.strip().split())
    if not cleaned:
        return "New Chat"

    lower = cleaned.lower()

    destination = None
    match = re.search(r"\b(?:to|for|in)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)", cleaned)
    if match:
        destination = match.group(1).strip()

    topic = None
    for key, label in TOPIC_HINTS.items():
        if re.search(rf"\b{re.escape(key)}\b", lower):
            topic = label
            break

    if destination and topic:
        title = f"{destination} {topic}"
    elif destination:
        title = f"{destination} Trip"
    elif topic:
        title = topic
    else:
        words = re.findall(r"[A-Za-z]+", cleaned)
        filtered = [w for w in words if w.lower() not in STOPWORDS]
        title = " ".join(filtered[:4]) if filtered else "New Chat"

    return title[:48].strip() or "New Chat"


def to_epoch_seconds(value: Optional[datetime]) -> float:
    if not value:
        return 0

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)

    return value.timestamp()


class AskRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1600)
    session_id: Optional[str] = None

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
    latency_ms: int = 0
    pdf_url: Optional[str] = None


class ChatSessionItem(BaseModel):
    session_id: str
    title: str
    updated_at: float


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: float
    classifications: List[str] = Field(default_factory=list)
    agents_used: List[str] = Field(default_factory=list)
    pdf_url: Optional[str] = None


class ChatSessionDetail(BaseModel):
    session_id: str
    title: str
    messages: List[ChatMessage]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global workflow, chat_repo

    workflow, db = await build_workflow()
    chat_repo = ChatRepository(db)

    logger.info("workflow initialized successfully")
    logger.info("chat repository initialized successfully")
    yield


app = FastAPI(title="Travel Concierge", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "supabase_url": os.getenv("SUPABASE_URL"),
            "supabase_anon_key": os.getenv("SUPABASE_ANON_KEY"),
        },
    )


@app.get("/api/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/downloads/{filename}")
async def download_file(filename: str):
    path = Path("generated") / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.get("/api/chats", response_model=List[ChatSessionItem])
async def list_chats(current_user: Dict[str, Any] = Depends(get_current_user)):
    global chat_repo

    if chat_repo is None:
        raise HTTPException(status_code=503, detail="Chat repository is not initialized yet.")

    user_id = current_user["user_id"]
    sessions = chat_repo.list_sessions(user_id=user_id)

    return [
        ChatSessionItem(
            session_id=session["session_id"],
            title=session.get("title", "New Chat"),
            updated_at=to_epoch_seconds(session.get("updated_at")),
        )
        for session in sessions
    ]


@app.get("/api/chats/{session_id}", response_model=ChatSessionDetail)
async def get_chat(session_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    global chat_repo

    if chat_repo is None:
        raise HTTPException(status_code=503, detail="Chat repository is not initialized yet.")

    user_id = current_user["user_id"]
    session = chat_repo.get_session(session_id=session_id, user_id=user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = chat_repo.get_messages(session_id=session_id, user_id=user_id)

    return ChatSessionDetail(
        session_id=session["session_id"],
        title=session.get("title", "New Chat"),
        messages=[
            ChatMessage(
                role=message["role"],
                content=message["content"],
                timestamp=to_epoch_seconds(message.get("timestamp")),
                classifications=message.get("classifications", []),
                agents_used=message.get("agents_used", []),
                pdf_url=message.get("pdf_url"),
            )
            for message in messages
        ],
    )


@app.delete("/api/chats/{session_id}")
async def delete_chat(session_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    global chat_repo

    if chat_repo is None:
        raise HTTPException(status_code=503, detail="Chat repository is not initialized yet.")

    user_id = current_user["user_id"]
    session = chat_repo.get_session(session_id=session_id, user_id=user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    chat_repo.delete_chat(session_id=session_id, user_id=user_id)
    return {"status": "deleted"}


@app.post("/api/ask", response_model=AskResponse)
async def ask(req: AskRequest, current_user: Dict[str, Any] = Depends(get_current_user)) -> AskResponse:
    global workflow, chat_repo

    if workflow is None:
        raise HTTPException(status_code=503, detail="Workflow is not initialized yet.")

    if chat_repo is None:
        raise HTTPException(status_code=503, detail="Chat repository is not initialized yet.")

    user_id = current_user["user_id"]
    request_id = str(uuid.uuid4())
    session_id = req.session_id or str(uuid.uuid4())
    start = time.perf_counter()

    existing_session = chat_repo.get_session(session_id=session_id, user_id=user_id)
    if not existing_session:
        chat_repo.create_session(
            session_id=session_id,
            title=generate_chat_title(req.query),
            user_id=user_id,
        )

    chat_repo.add_message(
        session_id=session_id,
        user_id=user_id,
        role="user",
        content=req.query,
    )

    initial_state: Dict[str, Any] = {
        "query": req.query,
        "session_id": session_id,
        "messages": [HumanMessage(content=req.query)],
        "results": [],
        "routes": [],
        "user_id": user_id,
    }

    try:
        out = await workflow.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": session_id}},
        )

        latency_ms = int((time.perf_counter() - start) * 1000)

        classifications = [
            item.get("source", "")
            for item in out.get("routes", [])
            if isinstance(item, dict)
        ]

        agent_outputs: List[AgentOutput] = []
        agents_used: List[str] = []

        for item in out.get("results", []):
            if not isinstance(item, dict):
                continue

            source = item.get("source", "")
            pretty = AGENT_NAME_MAP.get(source, source.title() or "Agent")

            agent_outputs.append(
                AgentOutput(
                    name=pretty,
                    content=item.get("result", ""),
                )
            )

            if pretty not in agents_used:
                agents_used.append(pretty)

        final_answer = out.get("final_answer", "")

        chat_repo.add_message(
            session_id=session_id,
            user_id=user_id,
            role="assistant",
            content=final_answer,
            classifications=classifications,
            agents_used=agents_used,
            pdf_url=out.get("pdf_url"),
        )

        return AskResponse(
            request_id=request_id,
            session_id=session_id,
            final_answer=final_answer,
            classifications=classifications,
            agents_used=agents_used,
            agent_outputs=agent_outputs,
            latency_ms=latency_ms,
            pdf_url=out.get("pdf_url"),
        )

    except Exception as exc:
        logger.exception("ask request failed request_id=%s", request_id)
        raise HTTPException(
            status_code=500,
            detail="Unable to process the travel request right now.",
        ) from exc