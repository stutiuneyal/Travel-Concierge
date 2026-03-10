from pydantic import BaseModel

from core.llm import chat
from core.prompts import ITINERARY_PROMPT
from states.graph_state import GraphState


class DayPlan(BaseModel):
    day: int
    title: str
    morning: str
    afternoon: str
    evening: str
    notes: str | None = None


class ItineraryModel(BaseModel):
    overview: str
    days: list[DayPlan]
    budget_notes: str


planner = chat().with_structured_output(ItineraryModel)


async def run_itinerary(state: GraphState) -> GraphState:
    payload = {
        'trip_context': state.get('trip_context', {}),
        'flights': state.get('flights', []),
        'flight_insights': state.get('flight_insights', {}),
        'hotels': state.get('hotels', []),
        'hotel_insights': state.get('hotel_insights', {}),
        'weather_summary': state.get('weather_summary', {}),
        'weather_insights': state.get('weather_insights', {}),
        'places': state.get('places', []),
        'places_insights': state.get('places_insights', {}),
        'budget_summary': state.get('budget_summary', {}),
        'visa_info': state.get('visa_info', {}),
    }

    itinerary = planner.invoke(f"{ITINERARY_PROMPT}\n\nData:\n{payload}").model_dump()
    return {
        'itinerary': itinerary,
        'results': [{'source': 'itinerary', 'result': 'Built day-wise itinerary successfully.'}],
    }
