from typing import List
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Send
import os

from states import RouterState, AgentInput
from agents import country_agent, time_agent, holidays_agent, fx_agent

def _agent_text(res) -> str:
    # Compatible across versions: most prebuilt agents return {"messages":[...]}
    if isinstance(res, dict) and "messages" in res and res["messages"]:
        return getattr(res["messages"][-1], "content", str(res["messages"][-1]))
    return str(res)

def _recent_history_text(messages,limit:int = 8) -> str:
    if not messages:
        return ""
    
    lines = []
    for m in messages[-limit:]:
        if isinstance(m, HumanMessage):
            role = "user"
        elif isinstance(m,AIMessage):
            role = "assisstant"
        else:
            role = getattr(m, "type", "unknown")
    
        content = getattr(m,"content","")
        if isinstance(content,List):
            content = str(content)
        
        lines.append(f"{role}: {content}")
    
    return "\n".join(lines)
    
class RoutePlan(BaseModel):
    routes: List[str] = Field(
        description="List of routes to run. Allowed: country, time, holidays, fx"
    )
    country: str | None = Field(default=None, description="Country name if applicable")
    from_ccy: str | None = Field(default=None, description="Currency code like INR")
    to_ccy: str | None = Field(default=None, description="Currency code like JPY")



assert os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY not set"
router_llm = init_chat_model("openai:gpt-4o-mini").with_structured_output(RoutePlan)


def classify(state: RouterState) -> RouterState:
    q = state["query"].strip()
    history = _recent_history_text(state.get("messages", []))

    plan: RoutePlan = router_llm.invoke(
        f"""
You are routing a travel assistant query.

Return a plan:
- routes: include any of: country, time, holidays, fx
- country: the country name if user is asking about a country
- from_ccy, to_ccy: for fx if present

Recent conversation:
{history}

Current query:
{q}
"""
    )

    routes = []
    # Build per-agent sub-queries. No parsing, just use structured fields.
    if "country" in plan.routes and plan.country:
        routes.append({"source": "country", "query": plan.country})
    if "time" in plan.routes and plan.country:
        routes.append({"source": "time", "query": plan.country})
    if "holidays" in plan.routes and plan.country:
        routes.append({"source": "holidays", "query": plan.country})
    if "fx" in plan.routes:
        # If missing, pass original query so FX agent can ask for clarification in response.
        if plan.from_ccy and plan.to_ccy:
            routes.append({"source": "fx", "query": f"{plan.from_ccy} to {plan.to_ccy}"})
        else:
            routes.append({"source": "fx", "query": q})

    # Safe fallback
    if not routes:
        routes = [{"source": "country", "query": q}]

    return {**state, "routes": routes}


def dispatch(state: RouterState):
    sends = []
    for r in state["routes"]:
        sends.append(Send(f"run_{r['source']}", {"query": r["query"]}))
    return sends


def run_country(inp: AgentInput) -> dict:
    res = country_agent.invoke({"input": inp["query"]})
    return {"results": [{"source": "country", "result": _agent_text(res)}]}

def run_time(inp: AgentInput) -> dict:
    res = time_agent.invoke({"input": inp["query"]})
    return {"results": [{"source": "time", "result": _agent_text(res)}]}

def run_holidays(inp: AgentInput) -> dict:
    res = holidays_agent.invoke({"input": inp["query"]})
    return {"results": [{"source": "holidays", "result": _agent_text(res)}]}

def run_fx(inp: AgentInput) -> dict:
    res = fx_agent.invoke({"input": inp["query"]})
    return {"results": [{"source": "fx", "result": _agent_text(res)}]}


def synthesize(state: RouterState) -> RouterState:
    history = _recent_history_text(state.get("messages", []))
    chunks = "\n\n".join([f"[{r['source'].upper()}]\n{r['result']}" for r in state["results"]])

    final_llm = init_chat_model("openai:gpt-4o-mini")
    final = final_llm.invoke(
        f"""
You are the final travel assistant.

Use:
1. the current user query
2. the recent conversation history
3. the specialist outputs

Recent conversation:
{history}

Current user query:
{state["query"]}

Specialist results:
{chunks}

Write one clear consolidated answer with short sections where useful.
Resolve follow-up references correctly.
Do not mention internal agents.
"""
    ).content #returns the content returned from llm

    return {**state, "final_answer": final}