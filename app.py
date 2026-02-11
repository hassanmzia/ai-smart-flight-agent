# Multi-Agent Trip Planner (CrewAI)
# Refactor of single-crew app into a hierarchical multi-agent system
# - Adds specialized agents (weather, events, health, safety, budget, flights, hotels, traffic)
# - Introduces a Supervisor (Orchestrator) to coordinate tasks
# - Keeps Gradio UI, expands inputs, and streams a final consolidated markdown plan
#
# Notes:
# * External fetchers use public APIs where possible. Provide API keys via env vars.
# * Serper Dev Tool remains for robust web search fallbacks.
# * All external calls are wrapped with failsafes so the app continues even if a provider fails.
# * You can remove/replace providers per your preferences.


from __future__ import annotations

import os
import json
import time
from textwrap import dedent
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import faulthandler; faulthandler.enable()
import requests
#import requests_cache
import concurrent
import concurrent.futures
import asyncio
import gradio as gr

# CrewAI
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools.tools import SerperDevTool

# ===============
# LLM & Tools
# ===============

# HTTP caching to speed up repeated runs (1 hour cache)
##requests_cache.install_cache("trip_cache", expire_after=3600)
##requests_cache.install_cache(backend="memory", expire_after=3600)

### DEEPSEEK MODEL ###
#import os
#from langchain_deepseek import ChatDeepSeek

# Load your DeepSeek API key from environment variables
#os.environ["DEEPSEEK_API_KEY"] = os.getenv("DEEPSEEK_API_KEY")

# Initialize the DeepSeek Reasoning Model using ChatDeepSeek
# DEESEEK_LLM = ChatDeepSeek(
#    model="deepseek-r1",  # Use the reasoning-enabled DeepSeek model
#    api_key=os.environ.get("DEEPSEEK_API_KEY"),
#    temperature=0.0,            # Deterministic output
#    max_tokens=1024             # Limit response length as appropriate
#)

#regular Deepseek 

#DEEPSEEK_LLM = LLM(
#    model="deepseek-r1",
#    api_key=os.environ["DEEPSEEK_API_KEY"],
#    temperature=0.0
#)

### ANTHROPIC CLAUDE MODEL 

#import os

#from langchain_anthropic import ChatAnthropic


# Load your Anthropic API key from environment variables
#os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")

# Instantiate the Claude LLM in LangChain style with correct param names
#CLAUDE_LLM = ChatAnthropic(
#    model="claude-sonnet-4",                 # or other valid model name you have access to
#    anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
#    temperature=0.0                          # Deterministic output
#)

###### OPENAI MODEL ####
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

OPENAI_LLM = LLM(
    model="openai/gpt-4o",
    #model="openai/gpt-4o-mini",
    api_key=os.environ.get("OPENAI_API_KEY"),
    temperature=0,
)


### OLLAMA MODELS #### 

# --- Use local Ollama instead of OpenAI ---
#OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


##OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://108.48.39.238:12434")
#OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://172.168.1.95:12434")
##OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral-nemo:latest")

#LOCAL_LLM = LLM(
#    model=f"{OLLAMA_MODEL}",  # e.g., "ollama/llama3.2:3b"
#    base_url=OLLAMA_BASE,            # Ollama endpoint (OpenAI-compatible)
#    temperature=0,
#    timeout=520,
#)

#OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL")
#OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

#LOCAL_LLM = LLM(
#    model="ollama/llama3.2",      # e.g., "ollama/llama3.1:8b-instruct"
#    base_url="172.168.1.95:12434",    # local Ollama endpoint
#    temperature=0.2,
#    timeout=60,
#)



# Search fallback
os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY")
os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")

SERPER_API_KEY = os.environ["SERPER_API_KEY"]
HF_TOKEN = os.environ["HF_TOKEN"]
#SERPER_API_KEY = os.getenv("SERPER_API_KEY")
#USE_SEARCH = bool(SERPER_API_KEY)
##serper_tool = SerperDevTool(num_results=7) if SERPER_API_KEY else None
#global USE_SEARCH, SERPER_API_KEY
#USE_SEARCH = (not fast) and bool(SERPER_API_KEY)

from crewai_tools.tools import SerperDevTool

#SERPER_API_KEY = os.getenv("SERPER_API_KEY")

if SERPER_API_KEY:
    serper_tool = SerperDevTool(num_results=3)
else:
    serper_tool = None


# Helper: basic safe GET

def http_get(url: str, params: Optional[dict] = None, headers: Optional[dict] = None, timeout: int = 8):
    backoff = 0.5
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == 2:
                return {"_error": str(e), "_url": url, "_params": params}
            time.sleep(backoff)
            backoff *= 2




#def search_tools():
#    return [serper_tool] if USE_SEARCH and serper_tool else []
def search_tools():
    return [serper_tool] if (USE_SEARCH and serper_tool) else []

# =====================
# External Fetcher Utils
# =====================

class DataFetchers:
    """Provider-agnostic helpers. Replace with your preferred providers.
    All methods return dicts (JSON-like) and never raise.
    """

    @staticmethod
    def weather(lat: float, lon: float, start_date: str, end_date: str) -> Dict[str, Any]:
        # Open-Meteo free endpoint (no key)
        url = "https://api.open-meteo.com/v1/forecast"
        url = "https://www.weatherbit.io/api"
        url = "https://developer.accuweather.com/apis"
        url = "https://www.iqair.com/air-pollution-data-api"
        url = "https://www.getambee.com/api/"
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,precipitation,wind_speed_10m",
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
            "timezone": "auto",
            "start_date": start_date,
            "end_date": end_date,
        }
        return http_get(url, params=params)

    @staticmethod
    def events(city: str, start: str, end: str) -> Dict[str, Any]:
        # Ticketmaster Discovery API (optional key)
        key = os.getenv("TICKETMASTER_API_KEY", "")
        url = "https://app.ticketmaster.com/discovery/v2/events.json"
        url = "https://www.eventbrite.com/platform/api/"
        url = "https://www.meetup.com/api/"
        url = "https://rapidapi.com/eventful/api/eventful"
        url = "https://developers.google.com/maps/documentation/places/web-service/overview"
        params = {"city": city, "startDateTime": f"{start}T00:00:00Z", "endDateTime": f"{end}T23:59:59Z", "apikey": key}
        return http_get(url, params=params)

    @staticmethod
    def health_alerts(country: str) -> Dict[str, Any]:
        # CDC Travelers' Health (scraped proxy via RKI as placeholder if CDC blocks CORS)
        # This is a simple placeholder; in production you may need an official source or backend proxy.
        url = "https://disease.sh/v3/covid-19/countries/" + country
        url = "https://delphi.cmu.edu/epidata/api/"
        url = "https://www.cdc.gov/places/"
        url = "https://www.who.int/data/gho/info/disease-outbreak-news"
        url = "https://developer.tugo.com/travel-advisory-api"
        url = "https://developers.google.com/maps/documentation/air-quality"
        return http_get(url)

    @staticmethod
    def disasters() -> Dict[str, Any]:
        # GDACS public RSS to JSON via gdacs.org (use a static JSON mirror service)
        url = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/COUNTRY/ALL"
        url = "https://disasters.opendatasoft.com/api"
        url = "https://riskline.com/travel-safety-data/"
        url = "https://api.weather.gov/alerts"
        url = "https://earthquake.usgs.gov/fdsnws/event/1/"
        return http_get(url)

    @staticmethod
    def crime(city: str, state_or_country: str) -> Dict[str, Any]:
        # Placeholder: open crime APIs vary by locale. Using search fallback in agents if this fails.
        url = "https://api.crimeometer.com/v1/incidents/raw-data"
        url = "https://zylalabs.com/api-marketplace/data/crimedatabyzipcode-api/2320"
        key = os.getenv("CRIMEOMETER_API_KEY", "")
        url = "https://crimeometer.com"
        url = "https://crime-data-explorer.fr.cloud.gov/api"
        return {"note": "Crime API placeholder. Agent will search via web if insufficient."}

    @staticmethod
    def traffic(city: str) -> Dict[str, Any]:
        # Placeholder; real-time traffic often requires paid APIs (TomTom, Here, Google).
        url = "https://developers.google.com/maps/documentation/traffic"
        url = "https://docs.mapbox.com/api/navigation/traffic/"
        url = "https://developer.tomtom.com/traffic-api"
        url = "https://developer.here.com/traffic-api"
        return {"note": "Traffic API placeholder. Agent will suggest peak hours & bottlenecks via search."}

    @staticmethod
    def currency_rates(base: str = "USD") -> Dict[str, Any]:
        url = f"https://open.er-api.com/v6/latest/{base}"
        url = "https://www.exchangerate-api.com/"
        url = "https://www.alphavantage.co/"
        url = "https://currencylayer.com/"
        return http_get(url)

    @staticmethod
    def flights(origin: str, dest: str, start: str, end: str) -> Dict[str, Any]:
        # Placeholder; most flight APIs require keys. The agent will use search when enabled.
        url = "http://amadeus.com/en/solutions/for-developers"
        url = "http://rapidapi.com/skyscanner/api/skyscanner-flight-search"
        url = "http://flightaware.com/commercial/firehose/firehose_documentation.rvt"
        return {"note": "Flights API placeholder. Agent will provide sample itineraries via search if enabled."}

    @staticmethod
    def hotels(city: str, start: str, end: str, budget: int) -> Dict[str, Any]:
        # Placeholder; hotel APIs often require keys. The agent will use search when enabled.
        url = "http://developer.expedia.com"
        url = "http://amadeus.com/en/solutions/for-developers"
        url = "http://partners.booking.com"
        return {"note": "Hotels API placeholder. Agent will suggest options via search if enabled."}

    @staticmethod
    def carrentals(city: str, start: str, end: str, budget: int) -> Dict[str, Any]:
        # Placeholder; hotel APIs often require keys. The agent will use search when enabled.
        url = "https://www.rentalcars.com/connectapi/"
        url = "https://developer.avis.com/"
        url = "https://developer.hertz.com/"
        url = "https://www.expediapartnersolutions.com/"
        url = "https://developer.kayak.com/api/"
        return {"note": "Hotels API placeholder. Agent will suggest options via search if enabled."}

    @staticmethod
    def visas(origin: str, dest: str, start: str, end: str) -> Dict[str, Any]:
        # Placeholder; most flight APIs require keys. The agent will use search when enabled.
        url = "https://www.visahq.com/visa-api/"
        url = "https://www.joinsherpa.com/"
        url = "https://www.iata.org/en/publications/timatic/"
        return {"note": "Flights API placeholder. Agent will provide sample itineraries via search if enabled."}

    @staticmethod
    def uber(origin: str, dest: str, start: str, end: str) -> Dict[str, Any]:
        # Placeholder; most flight APIs require keys. The agent will use search when enabled.
        url = "https://developer.uber.com/docs/riders/references/api/v1.2/estimates-price-get"
        return {"note": "Flights API placeholder. Agent will provide sample itineraries via search if enabled."}

    @staticmethod
    def commuteoptions(origin: str, dest: str, start: str, end: str) -> Dict[str, Any]:
        # Placeholder; most flight APIs require keys. The agent will use search when enabled.
        url = "https://developers.google.com/maps/documentation/transit"
        url = "https://transit.land/documentation/datastore/api-endpoints.html"
        url = "https://citymapper.com/tools/api"
        url = "https://transitfeeds.com/api"
        return {"note": "Flights API placeholder. Agent will provide sample itineraries via search if enabled."}

    @staticmethod
    def userreviews(origin: str, dest: str, start: str, end: str) -> Dict[str, Any]:
        # Placeholder; most flight APIs require keys. The agent will use search when enabled.
        url = "https://developer-tripadvisor.com/"
        url = "https://www.yelp.com/developers/documentation/v3"
        url = "https://developers.google.com/maps/documentation/places/web-service/overview"
        return {"note": "Flights API placeholder. Agent will provide sample itineraries via search if enabled."}



# =====================
# Agent Factory
# =====================

class TripAgents:
    def supervisor(self) -> Agent:
        return Agent(
            role="Supervisor Orchestrator",
            goal=dedent(
                """
                Coordinate a team of travel-specialist agents to select a destination, assess risks,collect the best prices for flight, hotels, commute , rent a car. It will also collect the local weather and 
                temperature, humidity, air quality, wind , storm, rain, pollen etc and provide them in a tabular format. It will collect local data of crime, events, sales, health alerts, traffic information
                and suggest the traveler based on the situation. it will also provide the contact information of local law enforcement , hospital, embessy etc. it will also show the visa requirements of the destination city
                and country and show the link of the nearest embessy to proceed. It will produce intenary with day by day items in tabular format of all days. it will include the the best end-to-end itinerary with budgets, 
                logistics, and safety guidance for the user-provided dates. Show the iternary of all days in tabular format with color headlines always with professional looking output. 
                """
            ),
            backstory="A seasoned chief travel planner with a strict focus on factual data and safety-first decisions.",
            #tools=[serper_tool] if (USE_SEARCH and serper_tool) else [],
            tools=search_tools(),
            allow_delegation=True,
            verbose=False,
            #llm=LOCAL_LLM,
            llm=OPENAI_LLM,
            #llm=DEEPSEEK_LLM,
            #llm=CLAUDE_LLM,
        )

    def city_selector(self) -> Agent:
        return Agent(
            role="City Selection Expert",
            goal="Pick the best city from candidates based on weather, seasonality, pricing, and fit to interests.",
            backstory="Analyst skilled in multi-criterion decision-making and destination ranking.",
            #tools=[serper_tool] if (USE_SEARCH and serper_tool) else [],
            tools=search_tools(),
            allow_delegation=False,
            verbose=False,
            #llm=LOCAL_LLM,
            llm=OPENAI_LLM,
            #llm=DEEPSEEK_LLM,
            #llm=CLAUDE_LLM,
        )

    def local_expert(self) -> Agent:
        return Agent(
            role="Local City Expert",
            goal="Provide nuanced, on-the-ground insights, neighborhoods, customs, and must-do experiences.",
            backstory="Friendly local who knows both signature spots and off-the-beaten-path gems.",
            #tools=[serper_tool] if (USE_SEARCH and serper_tool) else [],
            tools=search_tools(),
            allow_delegation=False,
            verbose=False,
            #llm=LOCAL_LLM,
            llm=OPENAI_LLM,
            #llm=DEEPSEEK_LLM,
            #llm=CLAUDE_LLM,
        )

    def weather_analyst(self) -> Agent:
        return Agent(
            role="Weather Analyst",
            goal="Summarize forecast ranges and risks (rain, wind) for the date window; advise packing.",
            backstory="Meteorology-savvy analyst using Open-Meteo and web data.",
            #tools=[serper_tool] if (USE_SEARCH and serper_tool) else [],
            tools=search_tools(),
            allow_delegation=False,
            verbose=False,
            #llm=LOCAL_LLM,
            llm=OPENAI_LLM,
            #llm=DEEPSEEK_LLM,
            #llm=CLAUDE_LLM,
        )

    def events_researcher(self) -> Agent:
        return Agent(
            role="Events & Festivals Researcher",
            goal="Find concerts, festivals, conferences, and local happenings within the date range.",
            backstory="Curator of culture, food, sports, and music events.",
            #tools=[serper_tool] if (USE_SEARCH and serper_tool) else [],
            tools=search_tools(),
            allow_delegation=False,
            verbose=False,
            #llm=LOCAL_LLM,
            llm=OPENAI_LLM,
            #llm=DEEPSEEK_LLM,
            #llm=CLAUDE_LLM,
        )

    def health_safety(self) -> Agent:
        return Agent(
            role="Health & Safety Advisor",
            goal="Summarize health alerts (CDC/WHO proxies), vaccination advice, crime overview, and emergency contacts.",
            backstory="Public health risk assessor with travel safety background.",
            #tools=[serper_tool] if (USE_SEARCH and serper_tool) else [],
            tools=search_tools(),
            allow_delegation=False,
            verbose=False,
            #llm=LOCAL_LLM,
            llm=OPENAI_LLM,
            #llm=DEEPSEEK_LLM,
            #llm=CLAUDE_LLM,
        )

    def logistics_budget(self) -> Agent:
        return Agent(
            role="Logistics & Budget Planner",
            goal="Estimate flights, hotels, ground transport, and create a budget that fits constraints.",
            backstory="Travel operations specialist balancing comfort vs. cost.",
            #tools=[serper_tool] if (USE_SEARCH and serper_tool) else [],
            tools=search_tools(),
            allow_delegation=False,
            verbose=False,
            #llm=LOCAL_LLM,
            llm=OPENAI_LLM,
            #llm=DEEPSEEK_LLM,
            #llm=CLAUDE_LLM,
        )

    def itinerary_builder(self) -> Agent:
        return Agent(
            role="Itinerary Synthesizer",
            goal="Assemble a day-by-day plan with addresses/URLs, schedule, and rationale; includes packing list. Present the output in tabular nice format with color headlines.",
            backstory="Detail-obsessed planner who turns research into an actionable schedule.",
            #tools=[serper_tool] if (USE_SEARCH and serper_tool) else [],
            tools=search_tools(),
            allow_delegation=False,
            verbose=False,
            #llm=LOCAL_LLM,
            llm=OPENAI_LLM,
            #llm=DEEPSEEK_LLM,
            #llm=CLAUDE_LLM,
        )

    def flights_planner(self) -> Agent:
        return Agent(
            role="Flights Planner",
            goal="Find example round-trip flight options for the date window with URLs and rough prices.",
            backstory="Airfare hunter optimizing for price vs. duration and layovers.",
            #tools=[serper_tool] if (USE_SEARCH and serper_tool) else [],
            tools=search_tools(),
            allow_delegation=False,
            verbose=False,
            #llm=LOCAL_LLM,
            llm=OPENAI_LLM,
            #llm=DEEPSEEK_LLM,
            #llm=CLAUDE_LLM,
        )

    def hotels_planner(self) -> Agent:
        return Agent(
            role="Hotels Planner",
            goal="Suggest 3–6 hotels across price tiers with locations, ratings, and official links.",
            backstory="Lodging expert balancing neighborhood fit and budget.",
            #tools=[serper_tool] if (USE_SEARCH and serper_tool) else [],
            tools=search_tools(),
            allow_delegation=False,
            verbose=False,
            #llm=LOCAL_LLM,
            llm=OPENAI_LLM,
            #llm=DEEPSEEK_LLM,
            #llm=CLAUDE_LLM,
        )

    def traffic_analyst(self) -> Agent:
        return Agent(
            role="Traffic & Mobility Analyst",
            goal="Summarize typical traffic bottlenecks, peak hours, and best routes; include transit options.",
            backstory="Mobility researcher familiar with urban traffic patterns and public transit.",
            #tools=[serper_tool] if (USE_SEARCH and serper_tool) else [],
            tools=search_tools(),
            allow_delegation=False,
            verbose=False,
            #llm=LOCAL_LLM,
            llm=OPENAI_LLM,
            #llm=DEEPSEEK_LLM,
            #llm=CLAUDE_LLM,
        )
# =====================
# Task Factory
# =====================

class TripTasks:
    def select_city(self, agent: Agent, origin: str, cities: str, interests: str, date_range: str) -> Task:
        return Task(
            description=dedent(f"""
                Evaluate and rank candidate cities using weather expectations, seasonal events, typical costs,
                political stability, and fit to interests. Return a shortlist (top-3) and pick a primary city with reasons.

                Inputs:
                - Origin: {origin}
                - City options: {cities}
                - Interests: {interests}
                - Date range: {date_range}

                Output a JSON block with keys: shortlist[], winner, rationale.
            """),
            agent=agent,
            expected_output="JSON with shortlist[], winner, rationale",
        )

    def weather_task(self, agent: Agent, city: str, lat: float, lon: float, start_date: str, end_date: str) -> Task:
        # Fetch data first, hand it to the agent for summarization
        meteo = DataFetchers.weather(lat, lon, start_date, end_date)
        payload = json.dumps(meteo)[:2000]  # keep token use sane
        return Task(
            description=dedent(f"""
                You are given Open-Meteo JSON (truncated if large). Provide a concise weather summary for the window
                including min/max temperatures, precipitation expectations, wind considerations, and packing guidance.

                City: {city}
                Start: {start_date}
                End: {end_date}

                Open-Meteo JSON (sampled):
                {payload}

                Produce bullet points and a 1-paragraph takeaway.

            """),
            agent=agent,
            expected_output="Weather bullets + takeaway paragraph.",
        )

    def events_task(self, agent: Agent, city: str, start_iso: str, end_iso: str) -> Task:
        ev = DataFetchers.events(city, start_iso.split("T")[0], end_iso.split("T")[0])
        payload = json.dumps(ev)[:2000]
        return Task(
            description=dedent(f"""
                From the Ticketmaster-like JSON results and web search if needed, list notable events matching
                the travel window and typical traveler interests. Include names, dates, venues, and official URLs.

                City: {city}
                Date window: {start_iso} to {end_iso}

                Events JSON (sampled):
                {payload}

                If insufficient, search the web.
            """),
            agent=agent,
            expected_output="Events list with date, venue, and URL.",
        )

    def health_safety_task(self, agent: Agent, city: str, country: str) -> Task:
        health = DataFetchers.health_alerts(country)
        disasters = DataFetchers.disasters()
        crime = DataFetchers.crime(city, country)
        payload = json.dumps({"health": health, "disasters": disasters, "crime": crime})[:2000]
        return Task(
            description=dedent(f"""
                Using provided JSON and web research as needed, summarize health advisories (vaccines, outbreaks),
                active natural disaster alerts (GDACS), crime/safety profile for travelers, and emergency contacts
                (police, ambulance, embassy/consulate if applicable). Include links to official sources.

                City: {city}
                Country/Region: {country}

                JSON snapshot (sampled):
                {payload}
            """),
            agent=agent,
            expected_output="Health & safety brief with emergency contacts and links.",
        )

    def logistics_budget_task(self, agent: Agent, origin: str, city: str, budget_usd: int) -> Task:
        rates = DataFetchers.currency_rates("USD")
        payload = json.dumps(rates)[:1500]
        return Task(
            description=dedent(f"""
                Build a budget for flights, hotels, local transport, food, and activities for a trip
                from {origin} to {city}. Provide low/med/high options and a recommended plan within ${budget_usd}.
                Use exchange rates JSON as needed. Include example flight & hotel candidates with URLs.

                FX JSON (USD base, sampled):
                {payload}
            """),
            agent=agent,
            expected_output="Budget table (USD) + recommended plan with URLs.",
        )

    def local_expert_task(self, agent: Agent, city: str, interests: str) -> Task:
        return Task(
            description=dedent(f"""
                Provide a locally-savvy mini-guide for {city}: best neighborhoods, transit tips, customs, scams to avoid,
                and 6-10 curated experiences tailored to: {interests}. Include addresses and official URLs.
            """),
            agent=agent,
            expected_output="Local mini-guide with addresses & URLs.",
        )

    def itinerary_task(self, agent: Agent, city: str, start_date: str, end_date: str, constraints: Dict[str, Any]) -> Task:
        return Task(
            description=dedent(f"""
                Using prior agents' outputs (weather, events, health/safety, budget, local guide, flight, hotels, traffic,), compile a daily
                itinerary for {city} from {start_date} to {end_date}. Include:
                - AM/PM blocks with activities and travel times (approx.)
                - Dining suggestions (note diet prefs if provided)
                - Addresses, phone, official URLs
                - Rainy-day alternates
                - Packing checklist (weather-aware)
                - Safety considerations and local emergency contacts

                Constraints: {json.dumps(constraints)}

                Final output must be valid Markdown with clear sections and a grand total budget. Make sure final output shows all days in tabular format. 
            """),
            agent=agent,
            expected_output="Full markdown itinerary with totals and links.",
        )

    def flights_task(self, agent: Agent, origin: str, dest: str, start_date: str, end_date: str, prefetched: Optional[Dict[str, Any]] = None) -> Task:
        flights_json = prefetched if prefetched is not None else DataFetchers.flights(origin, dest, start_date, end_date)
        payload = json.dumps(flights_json)[:2000]
        return Task(
            description=dedent(f"""
                Using the flights JSON (may be placeholder) and web search if enabled, list 3–6 round-trip flight options
                for {origin} → {dest} between {start_date} and {end_date}. Include airline, duration, layovers, price range, and official URLs.
                JSON snapshot:
                {payload}
            """),
            agent=agent,
            expected_output="Table of 3–6 round-trip options with URLs and notes.",
        )

    def hotels_task(self, agent: Agent, city: str, start_date: str, end_date: str, budget_usd: int, prefetched: Optional[Dict[str, Any]] = None) -> Task:
        hotels_json = prefetched if prefetched is not None else DataFetchers.hotels(city, start_date, end_date, budget_usd)
        payload = json.dumps(hotels_json)[:2000]
        return Task(
            description=dedent(f"""
                Recommend 3–6 hotels in {city} for {start_date}–{end_date}, covering budget/mid/high tiers.
                Include neighborhood, rating, price range, and official URLs.
                JSON snapshot:
                {payload}
            """),
            agent=agent,
            expected_output="Hotel shortlist (3–6) with neighborhoods, price tiers, and URLs.",
        )

    def traffic_task(self, agent: Agent, city: str) -> Task:
        tjson = DataFetchers.traffic(city)
        payload = json.dumps(tjson)[:1500]
        return Task(
            description=dedent(f"""
                Provide a traffic & mobility brief for {city}: peak congestion windows, common bottlenecks,
                airport-to-downtown routes, and public transit tips. Include references/links if search is enabled.
                JSON snapshot:
                {payload}
            """),
            agent=agent,
            expected_output="Traffic/mobility brief with peak times, bottlenecks, and route suggestions.",
        )


# =====================
# Crew Runner
# =====================

class TripCrew:
    def __init__(self, origin: str, cities: str, start_date: str, end_date: str, interests: str,
                 budget_usd: int,  country: str,
                 diet: str = "", risk_tolerance: str = "medium",
                 run_weather: bool = True, run_events: bool = True, run_safety: bool = True, run_budget: bool = True, run_flights: bool = True, run_hotels: bool = True, run_traffic: bool = True):
        self.origin = origin
        self.cities = cities
        self.start_date = start_date
        self.end_date = end_date
        self.interests = interests
        self.budget_usd = budget_usd
        self.country = country
        self.diet = diet
        self.risk_tolerance = risk_tolerance
        self.run_weather = run_weather
        self.run_events = run_events
        self.run_safety = run_safety
        self.run_budget = run_budget
        self.run_flights = run_flights
        self.run_hotels = run_hotels
        self.run_traffic = run_traffic


    def run(self):
        agents = TripAgents()
        tasks = TripTasks()

        supervisor = agents.supervisor()
        city_selector = agents.city_selector()
        local = agents.local_expert()
        weather = agents.weather_analyst()
        events = agents.events_researcher()
        health = agents.health_safety()
        budget = agents.logistics_budget()
        itinerary = agents.itinerary_builder()
        flights = agents.flights_planner()
        hotels = agents.hotels_planner()
        traffic = agents.traffic_analyst()

        # 1) Pick city (LLM ranking). We'll assume geocoding done via search inside the agent if needed.
        select_city_t = tasks.select_city(city_selector, self.origin, self.cities, self.interests, f"{self.start_date} to {self.end_date}")

        # Optional geocoding and conditional task creation
        def geocode_city(name: str):
            try:
                data = http_get(
                    "https://nominatim.openstreetmap.org/search",
                    params={"q": name, "format": "json", "limit": 1},
                    headers={"User-Agent": "trip-planner/1.0"},
                    timeout=8,
                )
                if isinstance(data, list) and data:
                    return float(data[0]["lat"]), float(data[0]["lon"]) 
            except Exception:
                pass
            return 0.0, 0.0

        lat, lon = geocode_city("<winner-from-select>")

        # --- Parallel prefetch for max performance ---
        futs = []
        pre = {"weather": None, "events": None, "health": None, "disasters": None, "crime": None, "flights": None, "hotels": None, "traffic": None, "rates": None}
        max_workers = 9
        #with concurrent.futures.ThreadPoolExecutor(max_workers) as pool: 
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        #futs = []
            if self.run_weather:
                futs.append(("weather", pool.submit(DataFetchers.weather, lat, lon, self.start_date, self.end_date)))
            if self.run_events:
                futs.append(("events", pool.submit(DataFetchers.events, "<winner-from-select>", self.start_date, self.end_date)))
            if self.run_safety:
                futs.append(("health", pool.submit(DataFetchers.health_alerts, self.country)))
                futs.append(("disasters", pool.submit(DataFetchers.disasters)))
                futs.append(("crime", pool.submit(DataFetchers.crime, "<winner-from-select>", self.country)))
            if self.run_flights:
                futs.append(("flights", pool.submit(DataFetchers.flights, self.origin, "<winner-from-select>", self.start_date, self.end_date)))
            if self.run_hotels:
                futs.append(("hotels", pool.submit(DataFetchers.hotels, "<winner-from-select>", self.start_date, self.end_date, self.budget_usd)))
            if self.run_traffic:
                futs.append(("traffic", pool.submit(DataFetchers.traffic, "<winner-from-select>")))
            if self.run_budget:
                futs.append(("rates", pool.submit(DataFetchers.currency_rates, "USD")))
            for key, f in futs:
                try:
                    pre[key] = f.result(timeout=12)
                except Exception as _e:
                    pre[key] = {"_error": str(_e)}      


        task_list = [select_city_t]
        if self.run_weather:
            weather_t = tasks.weather_task(weather, city="<winner-from-select>", lat=lat, lon=lon,
                                           start_date=self.start_date, end_date=self.end_date)
            task_list.append(weather_t)
        if self.run_events:
            events_t = tasks.events_task(events, city="<winner-from-select>", start_iso=f"{self.start_date}T00:00:00Z", end_iso=f"{self.end_date}T23:59:59Z")
            task_list.append(events_t)
        if self.run_safety:
            health_t = tasks.health_safety_task(health, city="<winner-from-select>", country=self.country)
            task_list.append(health_t)
        if self.run_flights:
            flights_t = tasks.flights_task(flights, origin=self.origin, dest="<winner-from-select>",
                                           start_date=self.start_date, end_date=self.end_date,
                                           prefetched=pre.get("flights"))
            task_list.append(flights_t)

        if self.run_hotels:
            hotels_t = tasks.hotels_task(hotels, city="<winner-from-select>",
                                         start_date=self.start_date, end_date=self.end_date,
                                         budget_usd=self.budget_usd,
                                         prefetched=pre.get("hotels"))
            task_list.append(hotels_t)

        if self.run_traffic:
            traffic_t = tasks.traffic_task(traffic, city="<winner-from-select>")
            task_list.append(traffic_t)
                
        if self.run_budget:
            budget_t = tasks.logistics_budget_task(budget, origin=self.origin, city="<winner-from-select>",
                                                   budget_usd=self.budget_usd)
            task_list.append(budget_t)

        local_t = tasks.local_expert_task(local, city="<winner-from-select>", interests=self.interests)
        task_list.append(local_t)

        constraints = {
            "diet": self.diet,
            "risk_tolerance": self.risk_tolerance,
            "origin": self.origin,
            "budget": self.budget_usd,
        }
        itinerary_t = tasks.itinerary_task(itinerary, city="<winner-from-select>",
                                           start_date=self.start_date, end_date=self.end_date,
                                           constraints=constraints)
        task_list.append(itinerary_t)

        crew = Crew(
            agents=[supervisor, city_selector, local, weather, events, health, budget, itinerary, flights, hotels, traffic],
            tasks=task_list,
            process=Process.sequential,
            manager_llm=OPENAI_LLM,
            #manager_llm=LOCAL_LLM,
            #manager_llm=DEEPSEEK_LLM,
            #manager_llm=CLAUDE_LLM,
            verbose=False,
        )

        result = crew.kickoff()
        return result

# =====================
# UI (Gradio)
# =====================

def run_trip(origin, cities, date_range, interests, budget,  country, diet, risk, toggles, mode):
    # Status line (single line to avoid syntax issues)
    yield gr.update(value="> 🔎 Orchestrating multi-agent planning…, working on the plan..., please wait for a while...")

    # Toggle search based on UI
    global USE_SEARCH, SERPER_API_KEY
   # USE_SEARCH = False if fast else bool(SERPER_API_KEY)
    #USE_SEARCH = (not fast) and bool(SERPER_API_KEY)
    # Fast mode OFF + a Serper key + checkbox ON -> allow web search
    #USE_SEARCH = (not fast) and bool(SERPER_API_KEY) and bool(web_search)
    fast = (mode == "Fast Search (API based)")
    global USE_SEARCH
    #USE_SEARCH = (not fast) and bool(SERPER_API_KEY)
    USE_SEARCH = (mode == "Deep Search (Web based)") and bool(SERPER_API_KEY)



    try:
        # Parse inputs
        try:
            start_date, end_date = [s.strip() for s in date_range.split("to")]
            ##start_date, _end = [s.strip() for s in date_range.split("to")]
        except Exception:
            yield gr.update(value="**Error:** Please enter date range like `YYYY-MM-DD to YYYY-MM-DD`.")
            return

        #duration_days = int(duration) if str(duration).strip().isdigit() else 3
        
        ##try:
        ##    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        ##    end_dt_from_duration = start_dt + timedelta(days=duration_days - 1)
        ##    _end_dt = datetime.strptime(_end, "%Y-%m-%d") if _end else end_dt_from_duration
        ##    end_dt = end_dt_from_duration if end_dt_from_duration <= _end_dt else _end_dt
        ##    end_date = end_dt.strftime("%Y-%m-%d")
        ##except Exception: 
            # if parsing failed, fall back to given end (or start)
        ##    end_date = _end or start_date



        budget_usd = int(float(budget)) if str(budget).strip() else 1500

        # Per-agent toggles
        enable_weather = "Weather" in (toggles or [])
        enable_events = "Events" in (toggles or [])
        enable_safety = "Safety" in (toggles or [])
        enable_budget = "Budget" in (toggles or [])
        enable_flights = "Flights" in (toggles or [])
        enable_hotels  = "Hotels"  in (toggles or [])
        enable_traffic = "Traffic" in (toggles or [])

        crew = TripCrew(
            origin=origin.strip(),
            cities=cities.strip(),
            start_date=start_date,
            end_date=end_date,
            interests=interests.strip(),
            budget_usd=budget_usd,
            country=country.strip() or "USA",
            diet=diet.strip(),
            risk_tolerance=risk or "medium",
            run_weather=enable_weather,
            run_events=enable_events,
            run_safety=enable_safety,
            run_budget=enable_budget,
            run_flights=enable_flights,
            run_hotels=enable_hotels,
            run_traffic=enable_traffic,            
        )

        # Kick off crew
        res = crew.run()
        text = res.raw if hasattr(res, "raw") else str(res)
        yield gr.update(value=text)
    except Exception as e:
        yield gr.update(value=f"**Runtime error:** {e}")


with gr.Blocks() as demo:
    gr.Markdown("## 🌍 Trip Planner — Agentic AI App")
    #gr.Markdown("## 🌍 Trip Planner — Multi‑Agent Agentic AI App")
    with gr.Row():
        origin = gr.Textbox(label="Traveling From", placeholder="e.g., Seattle")
        cities = gr.Textbox(label="City Options (comma‑separated)", placeholder="e.g., Orlando, Chicago, Toronto")
    with gr.Row():
        date_range = gr.Textbox(label="Date Range", placeholder="YYYY-MM-DD to YYYY-MM-DD")
        interests = gr.Textbox(label="Interests & Hobbies", placeholder="e.g., Food, History, Tourist Attractions")
    with gr.Row():
        budget = gr.Textbox(label="Budget (USD)", value="1500")
        #duration = gr.Textbox(label="Duration (days)", value="3")
    with gr.Row():
        country = gr.Textbox(label="Destination Country/Region", value="USA")
        diet = gr.Textbox(label="Dietary needs (optional)", placeholder="e.g., Normal, Halal, Vegan, Gluten‑free")
        risk = gr.Dropdown(["low", "medium", "high"], value="medium", label="Risk Tolerance")
#    with gr.Row():
#        fast = gr.Checkbox(value=True,  label="Fast mode (skip web search)")
#        web_search = gr.Checkbox(value=False, label="Enable web search ")

    agent_toggles = gr.CheckboxGroup(["Weather", "Events", "Safety", "Budget", "Flights", "Hotels", "Traffic"], value=["Weather", "Events", "Safety", "Budget", "Flights", "Hotels", "Traffic"], label="Agents to run")
    #agent_toggles = gr.CheckboxGroup(["Weather", "Events",  "Budget", "Flights", "Hotels"], value=["Weather", "Events", "Budget", "Flights", "Hotels"], label="Agents to run")
    #agent_toggles = gr.CheckboxGroup(["Weather", "Events", "Safety", "Budget", "Flights", "Hotels", "Traffic"], value=[], label="Agents to run")
    #fast = gr.Checkbox(value=True, label="Fast mode (disable web search)")

    mode = gr.Radio(
        ["Fast Search (API Based)", "Long Search (Web Based)"],
        value="Fast Search (API Based)",
        label="Run mode"
    )


    go = gr.Button("Plan My Trip ✈️")
    out = gr.Markdown("_Results appear here…_")

    go.click(run_trip, [origin, cities, date_range, interests, budget,  country, diet, risk, agent_toggles, mode], out)

# --- Deployment glue: expose as ASGI app and support local launch ---
try:
    from fastapi import FastAPI
    _fa = FastAPI()
    app = gr.mount_gradio_app(_fa, demo, path="/")
except Exception:
    app = None

if __name__ == "__main__":
    demo.launch(share=False, debug=False, ssr_mode=False)

