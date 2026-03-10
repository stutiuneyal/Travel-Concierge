from typing import Any, Dict, List, Literal, TypedDict, Annotated
import operator

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


RouteSource = Literal['flight', 'hotel', 'weather', 'places', 'budget', 'itinerary', 'visa', 'pdf']


class RouteItem(TypedDict):
    source: RouteSource
    query: str


class AgentOutput(TypedDict):
    source: str
    result: str


class GraphState(TypedDict, total=False):
    query: str
    session_id: str
    user_id: str
    messages: Annotated[List[BaseMessage], add_messages]

    trip_context: Dict[str, Any]
    routes: List[RouteItem]
    results: Annotated[List[AgentOutput], operator.add]

    flights: List[Dict[str, Any]]
    flight_insights: Dict[str, Any]
    hotels: List[Dict[str, Any]]
    hotel_insights: Dict[str, Any]
    weather_summary: Dict[str, Any]
    weather_insights: Dict[str, Any]
    places: List[Dict[str, Any]]
    places_insights: Dict[str, Any]
    budget_summary: Dict[str, Any]
    itinerary: Dict[str, Any]
    visa_info: Dict[str, Any]

    pdf_requested: bool
    pdf_path: str
    pdf_url: str

    final_answer: str
