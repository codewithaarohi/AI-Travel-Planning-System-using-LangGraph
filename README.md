# AI Travel Planning System using LangGraph

This project is a Real-World Multi-Agent AI System built using LangGraph.

The system uses 4 AI agents that work together to plan a complete trip automatically.

## Features

- ✈️ Flight Search Agent
- 🏨 Hotel Search Agent
- 🗓️ Itinerary Planning Agent
- 🤖 Final Response Agent
- 🧠 Memory using PostgreSQL
- 🌐 Real-time API Integration
- 💻 Streamlit Web Interface

---

# Tech Stack

- LangGraph
- LangChain
- Groq
- Llama 3.3 70B
- PostgreSQL
- Streamlit
- Tavily API
- AviationStack API

---

# Step 1: Create Python Environment

Open the terminal inside the project folder and run:

		python -m venv langgraph_env3


Now activate the environment:

#### Windows

		langgraph_env3\Scripts\activate


#### YouTube Tuturial (Hindi) - https://youtu.be/ctHby5vhDqg

#### YouTube Tuturial (English) -  https://youtu.be/_5XF5CCnbDk

---

# Step 2: Install Dependencies

Run the following command:

		pip install langgraph langchain langchain-openai langchain-groq langchain-community langchain-tavily psycopg[binary] psycopg_pool python-dotenv tavily-python requests streamlit

		pip install -U "psycopg[binary,pool]"  langgraph-checkpoint-postgres

---

# Step 3: Install PostgreSQL

Download and install PostgreSQL: https://www.postgresql.org/download/

⚠️ Important:
While installing PostgreSQL, remember:
- PostgreSQL Password
- Port Number

You will need them later while creating the database connection string.

---

# Step 4: Create Database

Open PostgreSQL and run:

CREATE DATABASE langgraph_memory_demo;


---

# Step 5: Setup `.env` File

Create a `.env` file inside the project folder.

Add the following keys:

GROQ_API_KEY=your_groq_api_key

TAVILY_API_KEY=your_tavily_api_key

AVIATIONSTACK_API_KEY=your_aviationstack_api_key

DATABASE_URL=postgresql://postgres:postgres@localhost:5433/langgraph_memory_demo


---

# Step 6: Get API Keys

## Get Groq API Key

https://console.groq.com

---

## Get Tavily API Key

https://tavily.com
  
---

## Get AviationStack API Key

https://aviationstack.com

---

# Step 7: Run the Application

#### Run Multi-Agent System in Terminal

		python main.py


This will test the multi-agent system through the terminal.

---

#### Run Streamlit Web App


		streamlit run frontend.py


This will launch the Multi-Agent AI web application.

---

#### Example Prompt

Plan a complete 7 days Japan trip including flights, hotels and sightseeing under 2 lakhs.


---

# Project Workflow

1. Flight Agent searches flights
2. Hotel Agent searches hotels
3. Itinerary Agent creates travel plan
4. Final Agent combines everything together
5. PostgreSQL stores conversation memory

