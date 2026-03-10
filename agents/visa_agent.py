from pydantic import BaseModel

from core.llm import chat
from core.prompts import VISA_REASONING_PROMPT
from states.graph_state import GraphState
from tools.visa_tools import get_visa_information


class VisaSummary(BaseModel):
    response: str


reasoner = chat().with_structured_output(VisaSummary)


async def run_visa(state: GraphState) -> GraphState:
    visa_info = get_visa_information(state.get('trip_context', {}))
    summary = reasoner.invoke(f"{VISA_REASONING_PROMPT}\n\nVisa data:\n{visa_info}").model_dump()
    visa_info['ai_summary'] = summary['response']
    return {
        'visa_info': visa_info,
        'results': [{'source': 'visa', 'result': summary['response']}],
    }
