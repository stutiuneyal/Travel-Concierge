from pydantic import BaseModel
from langchain_core.messages import AIMessage, HumanMessage

from config.settings import settings
from core.llm import chat
from core.prompts import TRIP_CONTEXT_PROMPT
from core.utils import merge_context
from states.graph_state import GraphState


class TripContextModel(BaseModel):
    origin_city: str | None = None
    origin_country: str | None = None
    destination_city: str | None = None
    destination_country: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    duration_days: int | None = None
    budget_level: str | None = None
    traveler_type: str | None = None
    interests: list[str] | None = None
    home_currency: str | None = None
    pdf_requested: bool | None = None


extractor = chat().with_structured_output(TripContextModel)


def _history_text(messages, limit: int = 8) -> str:
    lines = []
    for msg in (messages or [])[-limit:]:
        role = 'assistant' if isinstance(msg, AIMessage) else 'user'
        if isinstance(msg, HumanMessage):
            role = 'user'
        lines.append(f"{role}: {getattr(msg, 'content', '')}")
    return '\n'.join(lines)


async def update_trip_context(state: GraphState) -> GraphState:
    existing = state.get('trip_context', {})
    history = _history_text(state.get('messages', []))
    query = state.get('query', '')

    extracted = extractor.invoke(
        f"{TRIP_CONTEXT_PROMPT}\n\nStored context:\n{existing}\n\nRecent conversation:\n{history}\n\nCurrent query:\n{query}"
    )

    merged = merge_context(existing, extracted.model_dump())
    if not merged.get('home_currency'):
        merged['home_currency'] = settings.DEFAULT_HOME_CURRENCY

    return {
        **state,
        'trip_context': merged,
        'pdf_requested': bool(merged.get('pdf_requested')),
    }
