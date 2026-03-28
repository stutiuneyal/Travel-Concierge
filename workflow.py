from __future__ import annotations

from pymongo import MongoClient
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.mongodb import MongoDBSaver
from langchain_core.messages import AIMessage

from config.settings import settings
from core.llm import chat
from core.prompts import FINAL_SYNTHESIS_PROMPT
from states.graph_state import GraphState
from memory.trip_context import update_trip_context
from routing.router import classify
from agents.flight_agent import run_flight
from agents.hotel_agent import run_hotel
from agents.weather_agent import run_weather
from agents.places_agent import run_places
from agents.budget_agent import run_budget
from agents.itinerary_agent import run_itinerary
from agents.visa_agent import run_visa
from agents.pdf_agent import run_pdf

import json


final_llm = chat()


def _needs_route(state: GraphState, route_name: str) -> bool:
    return any(route.get('source') == route_name for route in state.get('routes', []))


async def maybe_run_flight(state: GraphState) -> GraphState:
    if _needs_route(state, 'flight'):
        return await run_flight(state)
    return {}


async def maybe_run_hotel(state: GraphState) -> GraphState:
    if _needs_route(state, 'hotel'):
        return await run_hotel(state)
    return {}


async def maybe_run_weather(state: GraphState) -> GraphState:
    if _needs_route(state, 'weather'):
        return await run_weather(state)
    return {}


async def maybe_run_places(state: GraphState) -> GraphState:
    if _needs_route(state, 'places'):
        return await run_places(state)
    return {}


async def maybe_run_visa(state: GraphState) -> GraphState:
    if _needs_route(state, 'visa'):
        return await run_visa(state)
    return {}


async def maybe_run_budget(state: GraphState) -> GraphState:
    if _needs_route(state, 'budget'):
        return await run_budget(state)
    return {}


async def maybe_run_itinerary(state: GraphState) -> GraphState:
    if _needs_route(state, 'itinerary'):
        return await run_itinerary(state)
    return {}


async def maybe_run_pdf(state: GraphState) -> GraphState:
    if _needs_route(state, 'pdf') and state.get('pdf_requested'):
        return await run_pdf(state)
    return {}


async def synthesize(state: GraphState) -> GraphState:
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
        'itinerary': state.get('itinerary', {}),
        'visa_info': state.get('visa_info', {}),
        'pdf_url': state.get('pdf_url', ''),
        'results': state.get('results', []),
    }

    compressed = compress_payload(payload)

    final = final_llm.invoke(
        f"{FINAL_SYNTHESIS_PROMPT}\n\nData:\n{json.dumps(compressed, indent=2)}"
    ).content
    return {
        'final_answer': final,
        'messages': [AIMessage(content=final)],
    }

def compress_payload(payload: dict) -> dict:
    return {
        "trip_context": payload.get("trip_context"),

        "flights": [
            {
                "airline": f.get("airline"),
                "origin": f.get("origin"),
                "destination": f.get("destination"),
                "departure": f.get("departure"),
                "arrival": f.get("arrival"),
                "stops": f.get("stops"),
                "price": f.get("price"),
                "currency": f.get("currency"),
            }
            for f in payload.get("flights", [])[:3]
        ],

        "hotels": [
            {
                "name": h.get("name") or h.get("hotel_name"),
                "address": h.get("address"),
                "rating": h.get("rating"),
                "price": h.get("price") or h.get("amount"),
                "currency": h.get("currency"),
                "distance_km": h.get("distance_km"),
            }
            for h in payload.get("hotels", [])[:3]
        ],

        "places": [
            {
                "name": (
                    p.get("displayName", {}).get("text")
                    if isinstance(p.get("displayName"), dict)
                    else p.get("name")
                ),
                "rating": p.get("rating"),
                "type": p.get("primaryType"),
            }
            for p in payload.get("places", [])[:5]
        ],

        "weather_summary": payload.get("weather_summary"),
        "budget_summary": payload.get("budget_summary"),
        "itinerary": payload.get("itinerary"),

        "hotel_insights": payload.get("hotel_insights"),
        "flight_insights": payload.get("flight_insights"),
        "places_insights": payload.get("places_insights"),
        "weather_insights": payload.get("weather_insights"),

        "visa_info": payload.get("visa_info"),
        "pdf_url": payload.get("pdf_url"),
    }


async def build_workflow():
    graph = StateGraph(GraphState)

    graph.add_node('update_trip_context', update_trip_context)
    graph.add_node('classify', classify)
    graph.add_node('flight', maybe_run_flight)
    graph.add_node('hotel', maybe_run_hotel)
    graph.add_node('weather', maybe_run_weather)
    graph.add_node('places', maybe_run_places)
    graph.add_node('visa', maybe_run_visa)
    graph.add_node('budget', maybe_run_budget)
    graph.add_node('itinerary', maybe_run_itinerary)
    graph.add_node('pdf', maybe_run_pdf)
    graph.add_node('synthesize', synthesize)

    graph.set_entry_point('update_trip_context')
    graph.add_edge('update_trip_context', 'classify')
    graph.add_edge('classify', 'flight')
    graph.add_edge('flight', 'hotel')
    graph.add_edge('hotel', 'weather')
    graph.add_edge('weather', 'places')
    graph.add_edge('places', 'visa')
    graph.add_edge('visa', 'budget')
    graph.add_edge('budget', 'itinerary')
    graph.add_edge('itinerary', 'pdf')
    graph.add_edge('pdf', 'synthesize')
    graph.add_edge('synthesize', END)

    client = MongoClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB]
    checkpointer = MongoDBSaver(client=client, db_name=settings.MONGODB_DB)
    return graph.compile(checkpointer=checkpointer),db
