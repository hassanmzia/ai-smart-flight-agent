"""
Multi-Agent AI System for Travel Planning
Uses LangGraph for agent orchestration
Implements Flight Agent, Hotel Agent, Manager Agent, Goal-Based Agent, and Utility-Based Agent
"""
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from concurrent.futures import ThreadPoolExecutor, as_completed
import copy
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
import operator
import logging
from django.conf import settings

from utils.airport_resolver import resolve_airport_to_city, AIRPORT_TO_CITY, get_hub_airport, get_hub_airport, AIRPORT_TO_CITY
from .agent_tools import (
    FlightSearchTool,
    HotelSearchTool,
    CarRentalSearchTool,
    RestaurantSearchTool,
    GoalBasedEvaluator,
    UtilityBasedEvaluator,
    CarRentalEvaluator,
    RestaurantEvaluator,
    WeatherTool
)

logger = logging.getLogger(__name__)


# State definition for LangGraph
class TravelAgentState(TypedDict):
    """State shared across all agents in the graph"""
    messages: Annotated[List, operator.add]
    user_query: str
    origin: Optional[str]
    destination: Optional[str]
    departure_date: Optional[str]
    return_date: Optional[str]
    passengers: int
    budget: Optional[float]
    cuisine: Optional[str]
    flight_results: Optional[Dict]
    hotel_results: Optional[Dict]
    car_rental_results: Optional[Dict]
    restaurant_results: Optional[Dict]
    goal_evaluation: Optional[Dict]
    utility_evaluation: Optional[Dict]
    car_evaluation: Optional[Dict]
    restaurant_evaluation: Optional[Dict]
    final_recommendation: Optional[Dict]
    current_agent: str
    error: Optional[str]


class FlightAgent:
    """
    Flight search agent - searches for flights using SerpAPI
    Based on notebook implementation
    """

    def __init__(self, model: ChatOpenAI):
        self.model = model
        self.tool = FlightSearchTool()

        self.system_prompt = """
You are a Travel Assistant Agent responsible for searching flight details between origin and destination locations.

Extract the following from the user query:
- origin: airport code or city (e.g., 'CDG', 'Paris')
- destination: airport code or city (e.g., 'BER', 'Berlin')
- date: departure date in YYYY-MM-DD format
- trip_type: 1=Round trip, 2=One way, 3=Multi-city
- return_date: for round trips
- passengers: number of travelers

Use the search_flights tool to find flight options.
Return flight details in a structured format.
"""

    # US metro area airports - try alternatives when primary returns no results
    US_AIRPORT_ALTERNATIVES = {
        'IAD': ['JFK', 'EWR'],  # DC area → try NYC airports
        'DCA': ['JFK', 'EWR', 'IAD'],
        'BWI': ['JFK', 'EWR', 'IAD'],
        'SFO': ['SJC', 'OAK'],
        'OAK': ['SFO', 'SJC'],
        'SJC': ['SFO', 'OAK'],
        'BUR': ['LAX'],
        'LGB': ['LAX'],
        'ONT': ['LAX'],
        'MDW': ['ORD'],
        'HOU': ['IAH'],
        'DAL': ['DFW'],
        'FLL': ['MIA'],
    }

    def _search_flights_with_retry(self, origin, destination, state):
        """Search flights, retrying with one-way if round-trip fails"""
        for trip_type in ([1, 2] if state.get('return_date') else [2]):
            results = self.tool.search_flights(
                origin=origin,
                destination=destination,
                date=state.get('departure_date', '2025-10-10'),
                trip_type=trip_type,
                return_date=state.get('return_date') if trip_type == 1 else None,
                passengers=state.get('passengers', 1)
            )
            if results.get('flights'):
                return results
        return results  # Return last attempt even if empty

    def execute(self, state: TravelAgentState) -> TravelAgentState:
        """Execute flight search, with hub-airport and alternative airport fallbacks"""
        try:
            origin = state.get('origin', 'CDG')
            destination = state.get('destination', 'BER')
            logger.info(f"FlightAgent executing: {origin} -> {destination}")

            # Search for direct flights
            flight_results = self._search_flights_with_retry(origin, destination, state)
            flights_found = len(flight_results.get('flights', []))

            # If no flights found, try via hub airports
            transit_notes = []
            if flights_found == 0:
                dest_hub = get_hub_airport(destination)
                origin_hub = get_hub_airport(origin)

                hub_destination = dest_hub or destination
                hub_origin = origin_hub or origin

                # Build transit notes regardless
                if dest_hub and dest_hub != destination:
                    dest_city = AIRPORT_TO_CITY.get(destination, destination)
                    hub_city = AIRPORT_TO_CITY.get(dest_hub, dest_hub)
                    transit_notes.append(
                        f"Fly to {hub_city} ({dest_hub}), then take a domestic flight or ground transport to {dest_city} ({destination})"
                    )
                if origin_hub and origin_hub != origin:
                    origin_city = AIRPORT_TO_CITY.get(origin, origin)
                    hub_city = AIRPORT_TO_CITY.get(origin_hub, origin_hub)
                    transit_notes.append(
                        f"From {origin_city}: travel to {hub_city} ({origin_hub}) for international departure"
                    )

                # Try hub route if different
                search_origin = hub_origin or origin
                search_dest = hub_destination

                if hub_destination != destination or hub_origin != origin:
                    hub_route = f"{search_origin} -> {search_dest}"
                    logger.info(f"No direct flights. Trying hub route: {hub_route}")

                    hub_results = self._search_flights_with_retry(search_origin, search_dest, state)
                    hub_flights = hub_results.get('flights', [])

                    # If hub route also fails, try alternative origin airports
                    if not hub_flights and search_origin in self.US_AIRPORT_ALTERNATIVES:
                        for alt_origin in self.US_AIRPORT_ALTERNATIVES[search_origin]:
                            logger.info(f"Hub route failed. Trying alternative origin: {alt_origin} -> {search_dest}")
                            alt_results = self._search_flights_with_retry(alt_origin, search_dest, state)
                            alt_flights = alt_results.get('flights', [])
                            if alt_flights:
                                hub_results = alt_results
                                hub_flights = alt_flights
                                alt_city = AIRPORT_TO_CITY.get(alt_origin, alt_origin)
                                origin_city = AIRPORT_TO_CITY.get(origin, origin)
                                transit_notes.insert(0,
                                    f"Flights found from {alt_city} ({alt_origin}) instead of {origin_city} ({search_origin})"
                                )
                                logger.info(f"Found {len(alt_flights)} flights from alt origin: {alt_origin}")
                                break

                    if hub_flights:
                        flight_results = hub_results
                        flights_found = len(hub_flights)
                        logger.info(f"Found {flights_found} flights via routing")

                # Always attach hub route info
                if dest_hub or origin_hub:
                    flight_results['hub_route'] = True
                    flight_results['original_destination'] = destination
                    flight_results['hub_destination'] = hub_destination
                    flight_results['transit_notes'] = transit_notes

            state['flight_results'] = flight_results
            state['current_agent'] = 'hotel'

            msg = f"Found {flights_found} flight options"
            if flight_results.get('hub_route'):
                hub_city = AIRPORT_TO_CITY.get(flight_results['hub_destination'], flight_results['hub_destination'])
                msg += f" (via {hub_city} hub)"
                if flight_results.get('transit_notes'):
                    msg += ". " + " | ".join(flight_results['transit_notes'])
            state['messages'].append(AIMessage(content=msg))

            return state

        except Exception as e:
            logger.error(f"FlightAgent error: {str(e)}")
            state['error'] = str(e)
            state['current_agent'] = 'error'
            return state


class HotelAgent:
    """
    Hotel search agent - searches for hotels using SerpAPI
    Based on notebook implementation
    """

    def __init__(self, model: ChatOpenAI):
        self.model = model
        self.tool = HotelSearchTool()

        self.system_prompt = """
You are a Travel Assistant Agent responsible for finding hotel accommodations.

Extract the following from the user query or context:
- location: destination city
- check_in_date: arrival date
- check_out_date: departure date
- adults: number of adults
- star_rating: filter by stars (1-5)

Use the search_hotels tool to find accommodation options.
Focus on hotels near the destination airport or city center.
"""

    def execute(self, state: TravelAgentState) -> TravelAgentState:
        """Execute hotel search with hub-city fallback for small towns"""
        try:
            destination = state.get('destination', 'Berlin')
            logger.info(f"HotelAgent executing for destination: {destination}")

            # Convert airport code to city name for better hotel search
            location_query = self._get_hotel_search_location(destination)
            logger.info(f"Hotel search location: {location_query}")

            # Search for hotels
            hotel_results = self.tool.search_hotels(
                location=location_query,
                check_in_date=state.get('departure_date', '2025-10-10'),
                check_out_date=state.get('return_date', '2025-10-12'),
                adults=state.get('passengers', 2)
            )

            hotels_found = len(hotel_results.get('hotels', []))

            # If no hotels found, try the nearest major city (hub)
            if hotels_found == 0:
                hub_code = get_hub_airport(destination)
                if hub_code:
                    hub_city = resolve_airport_to_city(hub_code)
                    logger.info(f"No hotels in {location_query}. Trying hub city: {hub_city}")

                    hub_results = self.tool.search_hotels(
                        location=hub_city,
                        check_in_date=state.get('departure_date', '2025-10-10'),
                        check_out_date=state.get('return_date', '2025-10-12'),
                        adults=state.get('passengers', 2)
                    )

                    hub_hotels = hub_results.get('hotels', [])
                    if hub_hotels:
                        hotel_results = hub_results
                        hotel_results['fallback_city'] = hub_city
                        hotel_results['original_city'] = location_query
                        hotels_found = len(hub_hotels)
                        logger.info(f"Found {hotels_found} hotels in {hub_city} (fallback from {location_query})")

            state['hotel_results'] = hotel_results
            state['current_agent'] = 'goal_evaluator'

            msg = f"Found {hotels_found} hotel options"
            if hotel_results.get('fallback_city'):
                msg += f" in nearby {hotel_results['fallback_city']} (no hotels found in {hotel_results['original_city']})"
            state['messages'].append(AIMessage(content=msg))

            return state

        except Exception as e:
            logger.error(f"HotelAgent error: {str(e)}")
            state['error'] = str(e)
            state['current_agent'] = 'error'
            return state

    def _get_hotel_search_location(self, destination: str) -> str:
        """Convert airport code to city/location for hotel search"""
        return resolve_airport_to_city(destination)


class CarRentalAgent:
    """
    Car rental search agent - searches for car rentals using SerpAPI
    """

    def __init__(self, model: ChatOpenAI):
        self.model = model
        self.tool = CarRentalSearchTool()

        self.system_prompt = """
You are a Travel Assistant Agent responsible for finding car rental options.

Extract the following from the user query or context:
- pickup_location: destination city or airport
- pickup_date: start date for rental
- dropoff_date: end date for rental
- car_type: optional filter (economy, suv, luxury, etc.)

Use the car_rental_search tool to find available rental cars.
Focus on finding cost-effective and reliable options.
"""

    def execute(self, state: TravelAgentState) -> TravelAgentState:
        """Execute car rental search with hub-city fallback"""
        try:
            import json
            destination = state.get('destination', 'Berlin')
            logger.info(f"CarRentalAgent executing for destination: {destination}")

            # Use destination/airport as pickup location
            pickup_location = self._get_car_rental_location(destination)
            logger.info(f"Car rental search location: {pickup_location}")

            # Search for car rentals
            car_rental_results = self.tool._run(
                pickup_location=pickup_location,
                pickup_date=state.get('departure_date', '2025-10-10'),
                dropoff_date=state.get('return_date', '2025-10-12'),
                car_type=None
            )

            car_results = json.loads(car_rental_results) if isinstance(car_rental_results, str) else car_rental_results
            cars_found = len(car_results.get('cars', []))

            # If no cars found, try hub city
            if cars_found == 0:
                hub_code = get_hub_airport(destination)
                if hub_code:
                    hub_city = resolve_airport_to_city(hub_code)
                    logger.info(f"No cars in {pickup_location}. Trying hub city: {hub_city}")
                    hub_raw = self.tool._run(
                        pickup_location=hub_city,
                        pickup_date=state.get('departure_date', '2025-10-10'),
                        dropoff_date=state.get('return_date', '2025-10-12'),
                        car_type=None
                    )
                    hub_results = json.loads(hub_raw) if isinstance(hub_raw, str) else hub_raw
                    if hub_results.get('cars'):
                        car_results = hub_results
                        car_results['fallback_city'] = hub_city
                        cars_found = len(car_results['cars'])

            state['car_rental_results'] = car_results
            state['current_agent'] = 'goal_evaluator'
            state['messages'].append(AIMessage(content=f"Found {cars_found} car rental options"))

            return state

        except Exception as e:
            logger.error(f"CarRentalAgent error: {str(e)}")
            state['car_rental_results'] = {"cars": [], "error": str(e)}
            state['current_agent'] = 'goal_evaluator'
            state['messages'].append(AIMessage(content="Car rental search failed, continuing without car options"))
            return state

    def _get_car_rental_location(self, destination: str) -> str:
        """Convert destination to car rental search location (city names only for SERP API)"""
        return resolve_airport_to_city(destination)


class CarRentalEvaluatorAgent:
    """
    Utility-based agent for evaluating car rentals
    Implements utility scoring (price + type + rating)
    """

    def __init__(self, model: ChatOpenAI):
        self.model = model
        self.evaluator = CarRentalEvaluator()

    def execute(self, state: TravelAgentState) -> TravelAgentState:
        """Execute car rental utility evaluation"""
        try:
            logger.info("CarRentalEvaluatorAgent executing")

            # Handle None or missing car_rental_results
            car_rental_results = state.get('car_rental_results')
            if car_rental_results is None or not isinstance(car_rental_results, dict):
                state['car_evaluation'] = {"error": "No car rental results available"}
                state['current_agent'] = 'manager'
                return state

            cars = car_rental_results.get('cars', [])

            if not cars:
                state['car_evaluation'] = {"error": "No cars to evaluate"}
                state['current_agent'] = 'manager'
                return state

            # Rank cars by utility
            ranked_cars = self.evaluator.rank_cars(cars)

            state['car_evaluation'] = {
                "ranked_cars": ranked_cars,
                "top_recommendation": ranked_cars[0] if ranked_cars else None,
                "total_evaluated": len(ranked_cars)
            }

            state['current_agent'] = 'manager'
            state['messages'].append(AIMessage(content=f"Ranked {len(ranked_cars)} car rental options by utility"))

            return state

        except Exception as e:
            logger.error(f"CarRentalEvaluatorAgent error: {str(e)}")
            state['error'] = str(e)
            state['current_agent'] = 'error'
            return state


class RestaurantAgent:
    """
    Restaurant search agent - searches for restaurants using SerpAPI
    """

    def __init__(self, model: ChatOpenAI):
        self.model = model
        self.tool = RestaurantSearchTool()

    def execute(self, state: TravelAgentState) -> TravelAgentState:
        """Execute restaurant search with hub-city fallback"""
        try:
            import json
            destination = state.get('destination', 'Berlin')
            cuisine = state.get('cuisine')
            logger.info(f"RestaurantAgent executing for destination: {destination}, cuisine: {cuisine}")

            search_city = self._get_restaurant_location(destination)
            logger.info(f"Restaurant search location: {search_city}")

            restaurant_results = self.tool._run(city=search_city, cuisine=cuisine)
            restaurant_data = json.loads(restaurant_results) if isinstance(restaurant_results, str) else restaurant_results
            restaurants_found = len(restaurant_data.get('restaurants', []))

            # If no restaurants found, try hub city
            if restaurants_found == 0:
                hub_code = get_hub_airport(destination)
                if hub_code:
                    hub_city = resolve_airport_to_city(hub_code)
                    logger.info(f"No restaurants in {search_city}. Trying hub city: {hub_city}")
                    hub_raw = self.tool._run(city=hub_city, cuisine=cuisine)
                    hub_data = json.loads(hub_raw) if isinstance(hub_raw, str) else hub_raw
                    if hub_data.get('restaurants'):
                        restaurant_data = hub_data
                        restaurant_data['fallback_city'] = hub_city
                        restaurants_found = len(restaurant_data['restaurants'])

            state['restaurant_results'] = restaurant_data
            state['current_agent'] = 'restaurant_evaluator'
            state['messages'].append(AIMessage(content=f"Found {restaurants_found} restaurant options"))

            return state

        except Exception as e:
            logger.error(f"RestaurantAgent error: {str(e)}")
            state['restaurant_results'] = {"restaurants": [], "error": str(e)}
            state['current_agent'] = 'goal_evaluator'
            state['messages'].append(AIMessage(content="Restaurant search failed, continuing without restaurant options"))
            return state

    def _get_restaurant_location(self, destination: str) -> str:
        """Convert destination to restaurant search location"""
        return resolve_airport_to_city(destination)


class RestaurantEvaluatorAgent:
    """
    Utility-based agent for evaluating restaurants
    Implements utility scoring (rating + price + reviews)
    """

    def __init__(self, model: ChatOpenAI):
        self.model = model
        self.evaluator = RestaurantEvaluator()

    def execute(self, state: TravelAgentState) -> TravelAgentState:
        """Execute restaurant utility evaluation"""
        try:
            logger.info("RestaurantEvaluatorAgent executing")

            # Handle None or missing restaurant_results
            restaurant_results = state.get('restaurant_results')
            if restaurant_results is None or not isinstance(restaurant_results, dict):
                state['restaurant_evaluation'] = {"error": "No restaurant results available"}
                state['current_agent'] = 'manager'
                return state

            restaurants = restaurant_results.get('restaurants', [])

            if not restaurants:
                state['restaurant_evaluation'] = {"error": "No restaurants to evaluate"}
                state['current_agent'] = 'manager'
                return state

            # Rank restaurants by utility
            ranked_restaurants = self.evaluator.rank_restaurants(restaurants)

            state['restaurant_evaluation'] = {
                "ranked_restaurants": ranked_restaurants,
                "top_recommendation": ranked_restaurants[0] if ranked_restaurants else None,
                "total_evaluated": len(ranked_restaurants)
            }

            state['current_agent'] = 'manager'
            state['messages'].append(AIMessage(content=f"Ranked {len(ranked_restaurants)} restaurant options by utility"))

            return state

        except Exception as e:
            logger.error(f"RestaurantEvaluatorAgent error: {str(e)}")
            state['restaurant_evaluation'] = {"error": str(e)}
            state['current_agent'] = 'manager'
            return state


class GoalBasedAgent:
    """
    Goal-based agent for evaluating flights against budget goals
    Implements penalty/reward scoring from notebook
    """

    def __init__(self, model: ChatOpenAI):
        self.model = model
        self.evaluator = GoalBasedEvaluator()

        self.system_prompt = """
You are a Goal Checker Agent that evaluates flight options based on budget constraints.

Your task:
1. Compare each flight's price against the budget goal
2. Calculate scores with penalty for over-budget flights
3. Identify the cheapest and most expensive options
4. Provide clear recommendations

Score calculation:
- Within budget: positive score based on savings
- Over budget: negative penalty score
"""

    def execute(self, state: TravelAgentState) -> TravelAgentState:
        """Execute goal-based evaluation"""
        try:
            logger.info("GoalBasedAgent executing")

            flights = state.get('flight_results', {}).get('flights', [])
            budget = state.get('budget', 200.0)

            if not flights:
                state['goal_evaluation'] = {"error": "No flights to evaluate"}
                state['current_agent'] = 'utility_evaluator'
                return state

            # Find best and worst flights and evaluate
            evaluation = self.evaluator.find_best_and_worst(
                flights=flights,
                budget_goal=budget,
                penalty_factor=0.1
            )

            state['goal_evaluation'] = evaluation
            state['current_agent'] = 'utility_evaluator'
            state['messages'].append(AIMessage(content="Completed budget evaluation"))

            return state

        except Exception as e:
            logger.error(f"GoalBasedAgent error: {str(e)}")
            state['error'] = str(e)
            state['current_agent'] = 'error'
            return state


class UtilityBasedAgent:
    """
    Utility-based agent for evaluating hotels based on multiple factors
    Implements utility scoring from notebook (price + star rating)
    """

    def __init__(self, model: ChatOpenAI):
        self.model = model
        self.evaluator = UtilityBasedEvaluator()

        self.system_prompt = """
You are a Utility Evaluation Agent that ranks hotels based on multiple factors.

Evaluation criteria:
1. Price utility (range: -40 to +40)
   - < $120: +40 (excellent value)
   - $120-149: +20 (good)
   - $150-179: 0 (moderate)
   - $180-249: -20 (expensive)
   - >= $250: -40 (very expensive)

2. Star rating utility (range: -40 to +40)
   - 5 stars: +40 (luxury)
   - 4 stars: +20 (upscale)
   - 3 stars: 0 (standard)
   - 2 stars: -20 (budget)
   - 1 star: -40 (basic)

Combine scores and rank hotels by total utility.
"""

    def execute(self, state: TravelAgentState) -> TravelAgentState:
        """Execute utility-based evaluation"""
        try:
            logger.info("UtilityBasedAgent executing")

            hotels = state.get('hotel_results', {}).get('hotels', [])

            if not hotels:
                state['utility_evaluation'] = {"error": "No hotels to evaluate"}
                state['current_agent'] = 'manager'
                return state

            # Rank hotels by utility
            ranked_hotels = self.evaluator.rank_hotels(hotels)

            state['utility_evaluation'] = {
                "ranked_hotels": ranked_hotels,
                "top_recommendation": ranked_hotels[0] if ranked_hotels else None,
                "total_evaluated": len(ranked_hotels)
            }

            state['current_agent'] = 'manager'
            state['messages'].append(AIMessage(content=f"Ranked {len(ranked_hotels)} hotels by utility"))

            return state

        except Exception as e:
            logger.error(f"UtilityBasedAgent error: {str(e)}")
            state['error'] = str(e)
            state['current_agent'] = 'error'
            return state


class ManagerAgent:
    """
    Manager agent that orchestrates the workflow and compiles final recommendations
    """

    def __init__(self, model: ChatOpenAI):
        self.model = model

        self.system_prompt = """
You are the Manager Agent coordinating travel planning.

Your responsibilities:
1. Compile results from all agents
2. Create comprehensive travel recommendations
3. Present options clearly with pros/cons
4. Consider budget, quality, and value
5. Provide actionable next steps
"""

    def execute(self, state: TravelAgentState) -> TravelAgentState:
        """Compile final recommendations"""
        try:
            logger.info("ManagerAgent compiling final recommendations")

            # Extract all results with safe handling of None values
            flight_results = state.get('flight_results')
            flights = flight_results.get('flights', []) if flight_results and isinstance(flight_results, dict) else []

            hotel_results = state.get('hotel_results')
            hotels = hotel_results.get('hotels', []) if hotel_results and isinstance(hotel_results, dict) else []

            car_rental_results = state.get('car_rental_results')
            cars = car_rental_results.get('cars', []) if car_rental_results and isinstance(car_rental_results, dict) else []

            restaurant_results = state.get('restaurant_results')
            restaurants = restaurant_results.get('restaurants', []) if restaurant_results and isinstance(restaurant_results, dict) else []

            goal_eval = state.get('goal_evaluation', {})
            utility_eval = state.get('utility_evaluation', {})
            car_eval = state.get('car_evaluation', {})
            restaurant_eval = state.get('restaurant_evaluation', {})

            # Compile final recommendation
            # Merge flight with its goal evaluation scores
            recommended_flight = None
            if goal_eval and goal_eval.get('cheapest flight'):
                cheapest = goal_eval['cheapest flight']
                if cheapest.get('flight'):
                    recommended_flight = dict(cheapest['flight'])
                    recommended_flight.update({
                        'goal_score': cheapest.get('score', 0),
                        'budget_status': cheapest.get('status', ''),
                        'savings': cheapest.get('savings', 0),
                        'budget_difference': cheapest.get('difference', 0)
                    })

            alternative_flight = None
            if goal_eval and goal_eval.get('most expensive flight'):
                expensive = goal_eval['most expensive flight']
                if expensive.get('flight'):
                    alternative_flight = dict(expensive['flight'])
                    alternative_flight.update({
                        'goal_score': expensive.get('score', 0),
                        'budget_status': expensive.get('status', ''),
                        'savings': expensive.get('savings', 0),
                        'budget_difference': expensive.get('difference', 0)
                    })

            final_recommendation = {
                "summary": {
                    "flights_found": len(flights),
                    "hotels_found": len(hotels),
                    "cars_found": len(cars),
                    "restaurants_found": len(restaurants),
                    "budget": state.get('budget', 'Not specified')
                },
                "recommended_flight": recommended_flight,
                "alternative_flight": alternative_flight,
                "recommended_hotel": utility_eval.get('top_recommendation') if utility_eval else None,
                "recommended_car": car_eval.get('top_recommendation') if car_eval else None,
                "recommended_restaurant": restaurant_eval.get('top_recommendation') if restaurant_eval else None,
                "top_5_hotels": utility_eval.get('ranked_hotels', [])[:5] if utility_eval else [],
                "top_5_cars": car_eval.get('ranked_cars', [])[:5] if car_eval else [],
                "top_5_restaurants": restaurant_eval.get('ranked_restaurants', [])[:5] if restaurant_eval else [],
                "budget_analysis": goal_eval,
                "hotel_rankings": utility_eval,
                "car_rankings": car_eval,
                "restaurant_rankings": restaurant_eval,
                "total_estimated_cost": self._calculate_total_cost(goal_eval, utility_eval, car_eval, restaurant_eval, state)
            }

            state['final_recommendation'] = final_recommendation
            state['current_agent'] = 'end'
            state['messages'].append(AIMessage(content="Travel planning complete!"))

            return state

        except Exception as e:
            logger.error(f"ManagerAgent error: {str(e)}")
            state['error'] = str(e)
            state['current_agent'] = 'error'
            return state

    def _calculate_total_cost(self, goal_eval: Dict, utility_eval: Dict, car_eval: Dict = None, restaurant_eval: Dict = None, state: Dict = None) -> Optional[float]:
        """Calculate total estimated trip cost including flight, hotel (total for all nights), car rental, and estimated restaurant costs"""
        try:
            from datetime import datetime

            # Get flight price (round-trip total)
            flight_price = goal_eval.get('cheapest flight', {}).get('price', 0)

            # Calculate number of nights for hotel and days for restaurant estimate
            nights = 1  # Default to 1 night
            days = 1  # Default to 1 day
            if state:
                departure_date = state.get('departure_date', '')
                return_date = state.get('return_date', '')
                if departure_date and return_date:
                    try:
                        dep = datetime.strptime(departure_date, '%Y-%m-%d')
                        ret = datetime.strptime(return_date, '%Y-%m-%d')
                        nights = max(1, (ret - dep).days)
                        days = max(1, (ret - dep).days + 1)  # Including departure day
                    except Exception as e:
                        logger.warning(f"Error calculating nights: {e}, using default 1 night")

            # Get hotel price per night with multiple fallbacks
            hotel = utility_eval.get('top_recommendation', {})
            hotel_price_per_night = 0
            if hotel:
                # Try multiple field names (price, price_per_night, pricePerNight, price_range_min)
                hotel_price_per_night = (hotel.get('price') or
                                        hotel.get('price_per_night') or
                                        hotel.get('pricePerNight') or
                                        hotel.get('price_range_min') or 0)

            # Calculate TOTAL hotel cost for entire stay
            hotel_total_price = hotel_price_per_night * nights

            # Get car rental price with fallbacks (already total for rental period)
            car_price = 0
            if car_eval:
                car = car_eval.get('top_recommendation', {})
                if car:
                    # Try multiple field names (total_price, price)
                    car_price = car.get('total_price') or car.get('price') or 0

            # Calculate estimated restaurant cost (3 meals per day per passenger)
            restaurant_price = 0
            if restaurant_eval:
                restaurant = restaurant_eval.get('top_recommendation', {})
                if restaurant:
                    avg_cost_per_person = restaurant.get('average_cost_per_person') or 0
                    passengers = state.get('passengers', 1) if state else 1
                    meals_per_day = 3  # Breakfast, lunch, dinner
                    restaurant_price = avg_cost_per_person * passengers * meals_per_day * days

            total = round(flight_price + hotel_total_price + car_price + restaurant_price, 2)
            logger.info(f"Total cost calculation: Flight ${flight_price} + Hotel ${hotel_price_per_night}/night × {nights} nights = ${hotel_total_price} + Car ${car_price} + Restaurant ~${restaurant_price} = ${total}")
            return total
        except Exception as e:
            logger.error(f"Error calculating total cost: {e}", exc_info=True)
            return None


class MultiAgentTravelSystem:
    """
    Main multi-agent system using LangGraph for orchestration
    """

    def __init__(self):
        """Initialize the multi-agent system"""
        self.model = ChatOpenAI(
            model=settings.AGENT_CONFIG.get('MODEL', 'gpt-4o-mini'),
            temperature=settings.AGENT_CONFIG.get('TEMPERATURE', 0.7),
            api_key=settings.OPENAI_API_KEY
        )

        # Initialize agents
        self.flight_agent = FlightAgent(self.model)
        self.hotel_agent = HotelAgent(self.model)
        self.car_rental_agent = CarRentalAgent(self.model)
        self.restaurant_agent = RestaurantAgent(self.model)
        self.goal_agent = GoalBasedAgent(self.model)
        self.utility_agent = UtilityBasedAgent(self.model)
        self.car_evaluator_agent = CarRentalEvaluatorAgent(self.model)
        self.restaurant_evaluator_agent = RestaurantEvaluatorAgent(self.model)
        self.manager_agent = ManagerAgent(self.model)

        # Build the graph
        self.graph = self._build_graph()

    def _parallel_search(self, state: TravelAgentState) -> TravelAgentState:
        """Run flight, hotel, car rental, and restaurant searches in parallel"""
        logger.info("Starting parallel search across all agents")

        agents = {
            "flight": self.flight_agent,
            "hotel": self.hotel_agent,
            "car_rental": self.car_rental_agent,
            "restaurant": self.restaurant_agent,
        }

        results = {}

        def run_agent(name, agent, agent_state):
            """Run a single agent with its own copy of state"""
            try:
                local_state = copy.copy(agent_state)
                local_state['messages'] = list(agent_state['messages'])
                return name, agent.execute(local_state)
            except Exception as e:
                logger.error(f"Parallel {name} agent error: {e}")
                return name, None

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(run_agent, name, agent, state): name
                for name, agent in agents.items()
            }
            for future in as_completed(futures):
                name, result_state = future.result()
                if result_state:
                    results[name] = result_state

        # Merge results back into main state
        if "flight" in results:
            state['flight_results'] = results["flight"].get('flight_results')
        if "hotel" in results:
            state['hotel_results'] = results["hotel"].get('hotel_results')
        if "car_rental" in results:
            state['car_rental_results'] = results["car_rental"].get('car_rental_results')
        if "restaurant" in results:
            state['restaurant_results'] = results["restaurant"].get('restaurant_results')

        # Collect messages from all agents
        for name in ["flight", "hotel", "car_rental", "restaurant"]:
            if name in results:
                for msg in results[name].get('messages', []):
                    if msg not in state['messages']:
                        state['messages'].append(msg)

        state['current_agent'] = 'goal_evaluator'
        logger.info("Parallel search complete")
        return state

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with parallel search and sequential evaluation"""
        workflow = StateGraph(TravelAgentState)

        # Single node runs all 4 searches in parallel via ThreadPoolExecutor
        workflow.add_node("parallel_search", self._parallel_search)
        workflow.add_node("goal_evaluator", self.goal_agent.execute)
        workflow.add_node("utility_evaluator", self.utility_agent.execute)
        workflow.add_node("car_evaluator", self.car_evaluator_agent.execute)
        workflow.add_node("restaurant_evaluator", self.restaurant_evaluator_agent.execute)
        workflow.add_node("manager", self.manager_agent.execute)

        # Parallel search first, then sequential evaluation
        workflow.set_entry_point("parallel_search")
        workflow.add_edge("parallel_search", "goal_evaluator")
        workflow.add_edge("goal_evaluator", "utility_evaluator")
        workflow.add_edge("utility_evaluator", "car_evaluator")
        workflow.add_edge("car_evaluator", "restaurant_evaluator")
        workflow.add_edge("restaurant_evaluator", "manager")
        workflow.add_edge("manager", END)

        return workflow.compile()

    def run(self, user_query: str, **kwargs) -> Dict[str, Any]:
        """
        Run the multi-agent system

        Args:
            user_query: User's travel request
            **kwargs: Additional parameters (origin, destination, dates, budget, etc.)

        Returns:
            Dict containing final recommendations and all intermediate results
        """
        try:
            logger.info(f"Starting multi-agent travel planning: {user_query}")

            # Initialize state
            initial_state = {
                "messages": [HumanMessage(content=user_query)],
                "user_query": user_query,
                "origin": kwargs.get('origin'),
                "destination": kwargs.get('destination'),
                "departure_date": kwargs.get('departure_date'),
                "return_date": kwargs.get('return_date'),
                "passengers": kwargs.get('passengers', 1),
                "budget": kwargs.get('budget'),
                "cuisine": kwargs.get('cuisine'),
                "flight_results": None,
                "hotel_results": None,
                "car_rental_results": None,
                "restaurant_results": None,
                "goal_evaluation": None,
                "utility_evaluation": None,
                "car_evaluation": None,
                "restaurant_evaluation": None,
                "final_recommendation": None,
                "current_agent": "flight",
                "error": None
            }

            # Run the graph
            final_state = self.graph.invoke(initial_state)

            logger.info("Multi-agent travel planning completed successfully")

            return {
                "success": True,
                "user_query": user_query,
                "parameters": kwargs,
                "flights": final_state.get('flight_results'),
                "hotels": final_state.get('hotel_results'),
                "car_rentals": final_state.get('car_rental_results'),
                "restaurants": final_state.get('restaurant_results'),
                "goal_evaluation": final_state.get('goal_evaluation'),
                "utility_evaluation": final_state.get('utility_evaluation'),
                "car_evaluation": final_state.get('car_evaluation'),
                "restaurant_evaluation": final_state.get('restaurant_evaluation'),
                "recommendation": final_state.get('final_recommendation'),
                "messages": [msg.content for msg in final_state.get('messages', [])]
            }

        except Exception as e:
            logger.error(f"Multi-agent system error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "user_query": user_query
            }


# Singleton instance
_travel_system = None


def get_travel_system() -> MultiAgentTravelSystem:
    """Get or create the singleton travel system instance"""
    global _travel_system
    if _travel_system is None:
        _travel_system = MultiAgentTravelSystem()
    return _travel_system
