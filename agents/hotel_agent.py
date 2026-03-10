from pydantic import BaseModel

from core.llm import chat
from core.prompts import HOTEL_REASONING_PROMPT
from states.graph_state import GraphState
from tools.amadeus_tools import search_hotels


class HotelInsights(BaseModel):
    shortlist_summary: str
    best_area_advice: str
    booking_advice: str


reasoner = chat().with_structured_output(HotelInsights)


async def run_hotel(state: GraphState) -> GraphState:
    hotels = await search_hotels(state.get('trip_context', {}))
    if not hotels:
        summary = 'No hotel shortlist available yet. Destination may be missing or provider returned no results.'
        return {
            'hotels': [],
            'hotel_insights': {
                'shortlist_summary': summary,
                'best_area_advice': 'Set a destination city to improve hotel suggestions.',
                'booking_advice': 'For v1, hotel pricing in the budget module is still an estimate unless you add live hotel-offer pricing.',
            },
            'results': [{'source': 'hotel', 'result': summary}],
        }

    insights = reasoner.invoke(
        f"{HOTEL_REASONING_PROMPT}\n\nTrip context:\n{state.get('trip_context', {})}\n\nRaw hotel candidates:\n{hotels}"
    ).model_dump()

    summary = (
        f"{insights['shortlist_summary']}\n"
        f"{insights['best_area_advice']}\n"
        f"{insights['booking_advice']}"
    )

    return {
        'hotels': hotels,
        'hotel_insights': insights,
        'results': [{'source': 'hotel', 'result': summary}],
    }
