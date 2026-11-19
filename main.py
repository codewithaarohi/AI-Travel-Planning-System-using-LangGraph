'''
# pip install langgraph langchain langchain-openai langchain-groq langchain-community langchain-tavily psycopg[binary] psycopg_pool python-dotenv tavily-python pip install requests streamlit

# install PostgresSql and create database
CREATE DATABASE langgraph_memory;  ( or open pgadmin4 and create database there )
'''
# LangGraph Multi-Agent Travel Booking System with Long-Term Memory

# main.py

import os  # Read configuration values from environment variables.
from typing import TypedDict, Annotated  # Describe the graph state and its update rules.
import operator  # Provide the list-concatenation reducer used by message history.

import psycopg  # Connect to the PostgreSQL database used for graph checkpoints.
from langgraph.graph import StateGraph, START, END  # Build the workflow and mark its entry and exit.
from langgraph.checkpoint.postgres import PostgresSaver  # Persist graph state in PostgreSQL.
from langchain_core.messages import (
    AnyMessage,  # Type accepted for any message stored in the graph state.
    HumanMessage,  # Represent the travel request supplied by the user.
    AIMessage,  # Represent status notes and model responses.
    SystemMessage,  # Set the assistant's role for itinerary generation.
)

from langchain_groq import ChatGroq  # Connect LangChain to a Groq-hosted language model.
from psycopg.rows import dict_row  # Provide mapping-style rows for database cursors.

from tools.tavily_tool import tavily_search  # Search the web for hotel information.
from tools.flight_tool import search_flights  # Look up flight options for the travel request.
from dotenv import load_dotenv  # Load local environment settings from a .env file.
load_dotenv()  # Make .env settings available through os.environ.

from groq import Groq

DATABASE_URL = os.getenv("DATABASE_URL")  # Read the PostgreSQL connection string.

# LLM
# Configure the language model used to write the itinerary and final response.
llm = ChatGroq(
    model="openai/gpt-oss-120b"  # Select the Groq model for travel planning.
)

# State
# Define the shared data shape passed between LangGraph nodes.
class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]  # Accumulate conversation and agent messages.
    user_query: str  # Keep the original request available to every agent.
    flight_results: str  # Store the results returned by the flight lookup.
    hotel_results: str  # Store the results returned by the hotel search.
    itinerary: str  # Store the itinerary drafted by the language model.
    llm_calls: int  # Track how many agent steps have run.

# Flight Agent
# Fetch flight options and add the results and a status message to the shared state.
def flight_agent(state: TravelState):
    query = state["user_query"]  # Use the user's request as the flight-search input.
    flight_data = search_flights(query)  # Call the flight tool to retrieve matching options.
    return {
        "flight_results": flight_data,  # Make flight data available to later agents.
        "messages": [  # Add a progress message to the accumulated conversation.
            AIMessage(content=f"Flight results fetched")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1  # Increment the workflow-step counter.
    }

# Hotel Agent
# Search for lodging related to the destination or trip in the user's request.
def hotel_agent(state: TravelState):
    query = f"Best hotels for {state['user_query']}"  # Turn the request into a hotel-search query.
    hotel_results = tavily_search(query)  # Call Tavily to retrieve hotel information.

    return {
        "hotel_results": hotel_results,  # Save search results for itinerary generation.
        "messages": [  # Record that the lodging lookup has completed.
            AIMessage(content="Hotel information fetched")  # Append a status message to history.
        ],
        "llm_calls": state.get("llm_calls", 0) + 1  # Increment the workflow-step counter.
    }

# Itinerary Agent
# Combine the user's request and tool results into a model-generated itinerary.
def itinerary_agent(state: TravelState):

    # Keep the model prompt's existing structure while supplying all gathered trip details.
    prompt = f"""
    Create a travel itinerary.
    User Query:
    {state['user_query']}

    Flight Results:
    {state['flight_results']}

    Hotel Results:
    {state['hotel_results']}
    """

    # Ask the model to create an itinerary using its travel-planner role and the assembled prompt.
    response = llm.invoke([
        SystemMessage(
            content="You are an expert travel planner"  # Give the model its planning role.
        ),
        HumanMessage(content=prompt)  # Pass the trip details as the user's task.
    ])

    return {
        "itinerary": response.content,  # Save the generated itinerary for the final response.
        "messages": [response],  # Add the model's itinerary message to conversation history.
        "llm_calls": state.get("llm_calls", 0) + 1  # Increment the workflow-step counter.
    }

# Final Response Agent
# Use the gathered flight, hotel, and itinerary details to compose the final answer.
def final_agent(state: TravelState):

    # Present all planning results together so the model can produce a cohesive response.
    final_prompt = f"""
    Generate final travel response.

    Flights:
    {state['flight_results']}

    Hotels:
    {state['hotel_results']}

    Itinerary:
    {state['itinerary']}
    """

    # Ask the model to turn the collected planning data into a user-facing response.
    response = llm.invoke([
        HumanMessage(content=final_prompt)  # Supply the final response request and trip details.
    ])

    return {
        "messages": [response],  # Append the final answer to the conversation history.
        "llm_calls": state.get("llm_calls", 0) + 1  # Increment the workflow-step counter.
    }


graph = StateGraph(TravelState)  # Create a workflow whose nodes share TravelState.

graph.add_node("flight_agent", flight_agent)  # Register the flight-search step.
graph.add_node("hotel_agent", hotel_agent)  # Register the hotel-search step.
graph.add_node("itinerary_agent", itinerary_agent)  # Register the itinerary-generation step.
graph.add_node("final_agent", final_agent)  # Register the final-response step.

graph.add_edge(START, "flight_agent")  # Begin each run by searching for flights.
graph.add_edge("flight_agent", "hotel_agent")  # Search for hotels after flight lookup.
graph.add_edge("hotel_agent", "itinerary_agent")  # Draft the itinerary after gathering both results.
graph.add_edge("itinerary_agent", "final_agent")  # Compose the final answer after drafting the itinerary.
graph.add_edge("final_agent", END)  # End the workflow after the final response.


# Persistent connection so both CLI and Streamlit can share the compiled app
# Checkpoint migrations include CREATE INDEX CONCURRENTLY, which cannot run in a transaction.
_conn = psycopg.connect(
    DATABASE_URL, autocommit=True, prepare_threshold=0, row_factory=dict_row
)

checkpointer = PostgresSaver(_conn)  # Create a PostgreSQL-backed LangGraph state saver.
checkpointer.setup()  # Create the checkpointer's required database tables if needed.



app = graph.compile(checkpointer=checkpointer)  # Compile the workflow with persistent state support.


if __name__ == "__main__":
    # Identify this conversation thread so the checkpointer can associate its state.
    config = {
        "configurable": {
            "thread_id": "user_aarohi"  # Use a stable ID for this CLI conversation.
        }
    }

    user_input = input("Enter travel request: ")  # Read a travel-planning request from the terminal.

    # Start the graph with the user's message and empty result fields.
    result = app.invoke(
        {
            "messages": [  # Initialize message history with the user's request.
                HumanMessage(content=user_input)  # Store the request as a LangChain message.
            ],
            "user_query": user_input,  # Provide the request in the field read by each agent.
            "flight_results": "",  # Initialize the flight results before the flight agent runs.
            "hotel_results": "",  # Initialize the hotel results before the hotel agent runs.
            "itinerary": "",  # Initialize the itinerary before the itinerary agent runs.
            "llm_calls": 0  # Start the workflow-step counter at zero.
        },
        config=config  # Associate this run with the configured persistent thread.
    )

    print("\nFINAL RESPONSE:\n")  # Label the output section in the terminal.

    for msg in result["messages"]:  # Iterate over the messages accumulated during the run.
        print(msg.content)  # Display each message's text, including the final response.
