from pydantic import BaseModel

from core.llm import chat
from core.prompts import WEATHER_REASONING_PROMPT
from states.graph_state import GraphState
from tools.weather_tools import get_weather_summary


class WeatherInsights(BaseModel):
    weather_summary: str
    planning_advice: str
    packing_advice: str


reasoner = chat().with_structured_output(WeatherInsights)


async def run_weather(state: GraphState) -> GraphState:
    weather = await get_weather_summary(state.get('trip_context', {}))
    if not weather:
        summary = 'Weather information is not available yet.'
        return {
            'weather_summary': {},
            'weather_insights': {
                'weather_summary': summary,
                'planning_advice': 'Add a destination to load forecast data.',
                'packing_advice': 'Packing guidance will appear after forecast data is available.',
            },
            'results': [{'source': 'weather', 'result': summary}],
        }

    insights = reasoner.invoke(
        f"{WEATHER_REASONING_PROMPT}\n\nTrip context:\n{state.get('trip_context', {})}\n\nForecast data:\n{weather}"
    ).model_dump()

    summary = (
        f"{insights['weather_summary']}\n"
        f"{insights['planning_advice']}\n"
        f"{insights['packing_advice']}"
    )

    return {
        'weather_summary': weather,
        'weather_insights': insights,
        'results': [{'source': 'weather', 'result': summary}],
    }
