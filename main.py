'''
# pip install langgraph langchain langchain-openai langchain-groq langchain-community langchain-tavily psycopg[binary] psycopg_pool python-dotenv tavily-python pip install requests streamlit

# install PostgresSql and create database
CREATE DATABASE langgraph_memory;  ( or open pgadmin4 and create database there )
'''
# LangGraph Multi-Agent Travel Booking System with Long-Term Memory

# main.py

import os
from typing import TypedDict, Annotated, Optional
import operator

from pydantic import BaseModel, Field

import psycopg
from psycopg.rows import dict_row
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)

import groq
from langchain_core.exceptions import OutputParserException
from langchain_groq import ChatGroq

from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# LLM
llm = ChatGroq(
    model="openai/gpt-oss-120b"
)

# State
class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    llm_calls: int

class FlightRoute(BaseModel):
    """Airports for the outbound flight of the user's trip."""
    origin_iata: Optional[str] = Field(
        default=None,
        description="3-letter IATA code of the main airport of the city the user is travelling FROM. "
                    "Null unless the user explicitly says where they depart from; never guess it.",
    )
    destination_iata: Optional[str] = Field(
        default=None,
        description="3-letter IATA code of the main international airport of the trip's (first) destination, "
                    "e.g. Paris -> CDG, Japan -> NRT, Dubai -> DXB.",
    )


# Deterministic, with high reasoning effort: at the default effort the model sometimes derives a code
# from the airport's name instead of recalling it (e.g. Nairobi "Jomo Kenyatta" -> JNB instead of NBO).
_route_extractor = ChatGroq(
    model=llm.model_name, temperature=0, reasoning_effort="high"
).with_structured_output(FlightRoute)


def extract_route(query: str) -> FlightRoute:
    return _route_extractor.invoke(
        "Identify the outbound flight route for the travel request below. The user will name places, "
        "not airports: convert each city or country to the IATA code of its main international airport "
        "(e.g. Japan -> NRT, Paris -> CDG, Bali -> DPS). Only set origin_iata if the user says where "
        f"they are travelling from.\n\nTravel request: {query}"
    )


# Flight Agent
def flight_agent(state: TravelState):
    try:
        route = extract_route(state["user_query"])
    except (groq.BadRequestError, OutputParserException):
        # Model declined to fill the route (tool_use_failed) or returned unparseable output:
        # skip the flight search rather than failing the whole pipeline. Auth/network errors still raise.
        route = FlightRoute()
    flight_data = search_flights(route.origin_iata, route.destination_iata)
    return {
        "flight_results": flight_data,
        "messages": [
            AIMessage(content=f"Flight results fetched")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

# Hotel Agent
def hotel_agent(state: TravelState):
    query = f"Best hotels for {state['user_query']}"
    hotel_results = tavily_search(query)

    return {
        "hotel_results": hotel_results,
        "messages": [
            AIMessage(content="Hotel information fetched")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

# Itinerary Agent
def itinerary_agent(state: TravelState):

    prompt = f"""
    Create a travel itinerary.
    User Query:
    {state['user_query']}

    Flight Results:
    {state['flight_results']}

    Hotel Results:
    {state['hotel_results']}
    """

    response = llm.invoke([
        SystemMessage(
            content="You are an expert travel planner"
        ),
        HumanMessage(content=prompt)
    ])

    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

# Final Response Agent
def final_agent(state: TravelState):

    final_prompt = f"""
    Generate final travel response.

    Flights:
    {state['flight_results']}

    Hotels:
    {state['hotel_results']}

    Itinerary:
    {state['itinerary']}
    """

    response = llm.invoke([
        HumanMessage(content=final_prompt)
    ])

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


graph = StateGraph(TravelState)

graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_agent)

graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END)


# Persistent connection so both CLI and Streamlit can share the compiled app
# PostgresSaver requires autocommit (setup() runs CREATE INDEX CONCURRENTLY) and dict rows
_conn = psycopg.connect(
    DATABASE_URL, autocommit=True, prepare_threshold=0, row_factory=dict_row
)
checkpointer = PostgresSaver(_conn)
checkpointer.setup()

app = graph.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    config = {
        "configurable": {
            "thread_id": "user_aarohi"
        }
    }

    user_input = input("Enter travel request: ")

    result = app.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ],
            "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0
        },
        config=config
    )

    print("\nFINAL RESPONSE:\n")

    for msg in result["messages"]:
        print(msg.content)
