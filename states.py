from typing import TypedDict, Literal, List, Annotated, Dict, Any
import operator

class AgentInput(TypedDict):
    query: str

class AgentOutput(TypedDict):
    source: str
    result: str

class RouteItem(TypedDict):
    source: Literal["country" , "time" , "holidays" , "fx"]
    query: str

class RouterState(TypedDict):
    query: str
    routes: List[RouteItem]
    results: Annotated[List[AgentOutput], operator.add]
    final_answer: str
    
    user_id: str
    user_profile: Dict[str,Any]
    trip_context: Dict[str,Any]


