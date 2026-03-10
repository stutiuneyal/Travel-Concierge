from pydantic import BaseModel

from core.llm import chat
from core.prompts import PLACES_REASONING_PROMPT
from states.graph_state import GraphState
from tools.places_tools import search_places


class PlacesInsights(BaseModel):
    must_visit_summary: str
    grouped_themes: str
    planning_advice: str


reasoner = chat().with_structured_output(PlacesInsights)


async def run_places(state: GraphState) -> GraphState:
    places = await search_places(state.get('trip_context', {}))
    if not places:
        summary = 'No place recommendations available yet.'
        return {
            'places': [],
            'places_insights': {
                'must_visit_summary': summary,
                'grouped_themes': 'No place categories available yet.',
                'planning_advice': 'Add a destination and interests to improve place recommendations.',
            },
            'results': [{'source': 'places', 'result': summary}],
        }

    insights = reasoner.invoke(
        f"{PLACES_REASONING_PROMPT}\n\nTrip context:\n{state.get('trip_context', {})}\n\nRaw places:\n{places}"
    ).model_dump()

    summary = (
        f"{insights['must_visit_summary']}\n"
        f"{insights['grouped_themes']}\n"
        f"{insights['planning_advice']}"
    )

    return {
        'places': places,
        'places_insights': insights,
        'results': [{'source': 'places', 'result': summary}],
    }
