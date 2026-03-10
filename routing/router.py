from typing import List

from pydantic import BaseModel, Field

from core.llm import chat
from core.prompts import ROUTER_PROMPT
from states.graph_state import GraphState


class RoutePlan(BaseModel):
    routes: List[str] = Field(default_factory=list)
    reason: str = ''


router_llm = chat().with_structured_output(RoutePlan)


async def classify(state: GraphState) -> GraphState:
    query = state.get('query', '')
    context = state.get('trip_context', {})

    plan = router_llm.invoke(
        f"{ROUTER_PROMPT}\n\nStored trip context:\n{context}\n\nCurrent query:\n{query}"
    )

    supported = {'flight', 'hotel', 'weather', 'places', 'budget', 'itinerary', 'visa', 'pdf'}
    routes = []
    for route in plan.routes:
        if route in supported:
            routes.append({'source': route, 'query': query})

    if not routes:
        routes = [{'source': 'itinerary', 'query': query}]

    return {**state, 'routes': routes, 'results': []}
