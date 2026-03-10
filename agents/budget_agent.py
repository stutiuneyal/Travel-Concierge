from pydantic import BaseModel

from core.llm import chat
from core.prompts import BUDGET_REASONING_PROMPT
from core.utils import safe_float
from states.graph_state import GraphState


class BudgetInsights(BaseModel):
    budget_summary: str
    savings_tips: str
    daily_spend_guidance: str


reasoner = chat().with_structured_output(BudgetInsights)


async def run_budget(state: GraphState) -> GraphState:
    context = state.get('trip_context', {})
    home_currency = context.get('home_currency', 'INR')
    duration_days = int(context.get('duration_days') or 5)
    nights = max(duration_days - 1, 1)

    flight_estimate = 0.0
    if state.get('flights'):
        flight_estimate = safe_float(state['flights'][0].get('price'), 0.0)

    hotel_estimate = 3500.0 * nights
    local_spend_estimate = 2500.0 * max(duration_days, 1)
    total_estimate = flight_estimate + hotel_estimate + local_spend_estimate

    budget = {
        'currency': home_currency,
        'flight_estimate': round(flight_estimate, 2),
        'hotel_estimate': round(hotel_estimate, 2),
        'local_spend_estimate': round(local_spend_estimate, 2),
        'total_estimate': round(total_estimate, 2),
        'notes': 'Hotel and local spend are practical v1 estimates until live hotel pricing is fully integrated.',
    }

    insights = reasoner.invoke(
        f"{BUDGET_REASONING_PROMPT}\n\nTrip context:\n{context}\n\nBudget data:\n{budget}"
    ).model_dump()

    summary = (
        f"{insights['budget_summary']}\n"
        f"{insights['savings_tips']}\n"
        f"{insights['daily_spend_guidance']}"
    )

    budget['insights'] = insights
    return {
        'budget_summary': budget,
        'results': [{'source': 'budget', 'result': summary}],
    }
