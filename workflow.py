from __future__ import annotations
from langgraph.graph import StateGraph, END
from pymongo import MongoClient
from states import RouterState
from routing import classify, dispatch, run_country, run_time, run_holidays, run_fx, synthesize
from langgraph.checkpoint.mongodb import MongoDBSaver
import os


def build_workflow():
    g = StateGraph(RouterState)

    g.add_node("classify", classify)
    g.add_node("run_country", run_country)
    g.add_node("run_time", run_time)
    g.add_node("run_holidays", run_holidays)
    g.add_node("run_fx", run_fx)
    g.add_node("synthesize", synthesize)

    g.set_entry_point("classify")
    g.add_conditional_edges(
        "classify",
        dispatch,
        ["run_country", "run_time", "run_holidays", "run_fx"],
    )

    g.add_edge("run_country", "synthesize")
    g.add_edge("run_time", "synthesize")
    g.add_edge("run_holidays", "synthesize")
    g.add_edge("run_fx", "synthesize")
    g.add_edge("synthesize", END)
    
    mongodb_uri = os.getenv("MONGODB_URI")
    mongodb_db = os.getenv("MONGODB_DB","travel_concierge")
    
    if not mongodb_uri:
        raise ValueError("MONGODB_URI is not set")

    client = MongoClient(mongodb_uri)
    checkpointer = MongoDBSaver(client=client,db_name=mongodb_db)

    return g.compile(checkpointer=checkpointer)
