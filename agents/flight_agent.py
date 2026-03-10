from pydantic import BaseModel

from core.llm import chat
from core.prompts import FLIGHT_REASONING_PROMPT
from states.graph_state import GraphState
from tools.amadeus_tools import search_flights


class FlightInsights(BaseModel):
    cheapest_option_summary: str
    best_overall_summary: str
    traveler_advice: str


reasoner = chat().with_structured_output(FlightInsights)


async def run_flight(state: GraphState) -> GraphState:
    flights = await search_flights(state.get('trip_context', {}))
    if not flights:
        summary = 'No flight options available yet. Origin, destination, or travel date may be missing, or the provider returned no results.'
        return {
            'flights': [],
            'flight_insights': {
                'cheapest_option_summary': summary,
                'best_overall_summary': summary,
                'traveler_advice': 'Add origin, destination, and date to fetch better flight suggestions.',
            },
            'results': [{'source': 'flight', 'result': summary}],
        }

    insights = reasoner.invoke(
        f"{FLIGHT_REASONING_PROMPT}\n\nTrip context:\n{state.get('trip_context', {})}\n\nRaw flight options:\n{flights}"
    ).model_dump()

    summary = (
        f"{insights['cheapest_option_summary']}\n"
        f"{insights['best_overall_summary']}\n"
        f"{insights['traveler_advice']}"
    )

    return {
        'flights': flights,
        'flight_insights': insights,
        'results': [{'source': 'flight', 'result': summary}],
    }
