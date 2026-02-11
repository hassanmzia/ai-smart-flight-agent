"""
Multi-Agent AI System for Travel Planning
Uses LangGraph for agent orchestration
Implements Flight Agent, Hotel Agent, Manager Agent, Goal-Based Agent, and Utility-Based Agent
"""
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
import operator
import logging
from django.conf import settings

from .agent_tools import (
    FlightSearchTool,
    HotelSearchTool,
    CarRentalSearchTool,
    GoalBasedEvaluator,
    UtilityBasedEvaluator,
    CarRentalEvaluator,
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
    flight_results: Optional[Dict]
    hotel_results: Optional[Dict]
    car_rental_results: Optional[Dict]
    goal_evaluation: Optional[Dict]
    utility_evaluation: Optional[Dict]
    car_evaluation: Optional[Dict]
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

    def execute(self, state: TravelAgentState) -> TravelAgentState:
        """Execute flight search"""
        try:
            logger.info(f"FlightAgent executing for: {state['user_query']}")

            # Search for flights
            flight_results = self.tool.search_flights(
                origin=state.get('origin', 'CDG'),
                destination=state.get('destination', 'BER'),
                date=state.get('departure_date', '2025-10-10'),
                trip_type=2 if not state.get('return_date') else 1,
                return_date=state.get('return_date'),
                passengers=state.get('passengers', 1)
            )

            state['flight_results'] = flight_results
            state['current_agent'] = 'hotel'
            state['messages'].append(AIMessage(content=f"Found {len(flight_results.get('flights', []))} flight options"))

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
        """Execute hotel search"""
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

            state['hotel_results'] = hotel_results
            state['current_agent'] = 'goal_evaluator'
            state['messages'].append(AIMessage(content=f"Found {len(hotel_results.get('hotels', []))} hotel options"))

            return state

        except Exception as e:
            logger.error(f"HotelAgent error: {str(e)}")
            state['error'] = str(e)
            state['current_agent'] = 'error'
            return state

    def _get_hotel_search_location(self, destination: str) -> str:
        """Convert airport code to city/location for hotel search"""
        # Common airport code to city mappings
        airport_to_city = {
            'LAX': 'Los Angeles Airport',
            'JFK': 'New York JFK Airport',
            'LGA': 'New York LaGuardia Airport',
            'EWR': 'Newark Airport',
            'ORD': 'Chicago O\'Hare Airport',
            'SFO': 'San Francisco Airport',
            'MIA': 'Miami Airport',
            'DFW': 'Dallas Fort Worth Airport',
            'SEA': 'Seattle Airport',
            'BOS': 'Boston Airport',
            'ATL': 'Atlanta Airport',
            'DEN': 'Denver Airport',
            'IAD': 'Washington DC Dulles Airport',
            'DCA': 'Washington DC Reagan Airport',
            'LAS': 'Las Vegas Airport',
            'PHX': 'Phoenix Airport',
            'IAH': 'Houston Airport',
            'MCO': 'Orlando Airport',
            'CDG': 'Paris Charles de Gaulle Airport',
            'LHR': 'London Heathrow Airport',
            'BER': 'Berlin Airport',
            'FCO': 'Rome Fiumicino Airport',
            'NRT': 'Tokyo Narita Airport',
        }

        # Return mapped city or use destination as-is
        return airport_to_city.get(destination.upper(), f"{destination} Airport")


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
        """Execute car rental search"""
        try:
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
                car_type=None  # No filter by default
            )

            # Parse JSON results
            import json
            car_results = json.loads(car_rental_results) if isinstance(car_rental_results, str) else car_rental_results

            state['car_rental_results'] = car_results
            state['current_agent'] = 'goal_evaluator'
            state['messages'].append(AIMessage(content=f"Found {len(car_results.get('cars', []))} car rental options"))

            return state

        except Exception as e:
            logger.error(f"CarRentalAgent error: {str(e)}")
            # Set empty results so downstream agents can continue
            state['car_rental_results'] = {"cars": [], "error": str(e)}
            state['current_agent'] = 'goal_evaluator'
            state['messages'].append(AIMessage(content="Car rental search failed, continuing without car options"))
            return state

    def _get_car_rental_location(self, destination: str) -> str:
        """Convert destination to car rental search location"""
        # Use same airport mappings as hotel search
        airport_to_city = {
            'LAX': 'Los Angeles',
            'JFK': 'New York JFK',
            'LGA': 'New York LaGuardia',
            'EWR': 'Newark',
            'ORD': 'Chicago',
            'SFO': 'San Francisco',
            'MIA': 'Miami',
            'DFW': 'Dallas',
            'SEA': 'Seattle',
            'BOS': 'Boston',
            'ATL': 'Atlanta',
            'DEN': 'Denver',
            'IAD': 'Washington DC',
            'DCA': 'Washington DC',
            'LAS': 'Las Vegas',
            'PHX': 'Phoenix',
            'IAH': 'Houston',
            'MCO': 'Orlando',
            'CDG': 'Paris',
            'LHR': 'London',
            'BER': 'Berlin',
            'FCO': 'Rome',
            'NRT': 'Tokyo',
        }

        return airport_to_city.get(destination.upper(), destination)


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

            goal_eval = state.get('goal_evaluation', {})
            utility_eval = state.get('utility_evaluation', {})
            car_eval = state.get('car_evaluation', {})

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
                    "budget": state.get('budget', 'Not specified')
                },
                "recommended_flight": recommended_flight,
                "alternative_flight": alternative_flight,
                "recommended_hotel": utility_eval.get('top_recommendation') if utility_eval else None,
                "recommended_car": car_eval.get('top_recommendation') if car_eval else None,
                "top_5_hotels": utility_eval.get('ranked_hotels', [])[:5] if utility_eval else [],
                "top_5_cars": car_eval.get('ranked_cars', [])[:5] if car_eval else [],
                "budget_analysis": goal_eval,
                "hotel_rankings": utility_eval,
                "car_rankings": car_eval,
                "total_estimated_cost": self._calculate_total_cost(goal_eval, utility_eval, car_eval)
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

    def _calculate_total_cost(self, goal_eval: Dict, utility_eval: Dict, car_eval: Dict = None) -> Optional[float]:
        """Calculate total estimated trip cost including flight, hotel, and car rental"""
        try:
            # Get flight price
            flight_price = goal_eval.get('cheapest flight', {}).get('price', 0)

            # Get hotel price with multiple fallbacks
            hotel = utility_eval.get('top_recommendation', {})
            hotel_price = 0
            if hotel:
                # Try multiple field names (price, price_per_night, pricePerNight, price_range_min)
                hotel_price = (hotel.get('price') or
                             hotel.get('price_per_night') or
                             hotel.get('pricePerNight') or
                             hotel.get('price_range_min') or 0)

            # Get car rental price with fallbacks
            car_price = 0
            if car_eval:
                car = car_eval.get('top_recommendation', {})
                if car:
                    # Try multiple field names (total_price, price)
                    car_price = car.get('total_price') or car.get('price') or 0

            total = round(flight_price + hotel_price + car_price, 2)
            logger.info(f"Total cost calculation: Flight ${flight_price} + Hotel ${hotel_price} + Car ${car_price} = ${total}")
            return total
        except Exception as e:
            logger.error(f"Error calculating total cost: {e}")
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
        self.goal_agent = GoalBasedAgent(self.model)
        self.utility_agent = UtilityBasedAgent(self.model)
        self.car_evaluator_agent = CarRentalEvaluatorAgent(self.model)
        self.manager_agent = ManagerAgent(self.model)

        # Build the graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with car rental support"""
        workflow = StateGraph(TravelAgentState)

        # Add nodes
        workflow.add_node("flight", self.flight_agent.execute)
        workflow.add_node("hotel", self.hotel_agent.execute)
        workflow.add_node("car_rental", self.car_rental_agent.execute)
        workflow.add_node("goal_evaluator", self.goal_agent.execute)
        workflow.add_node("utility_evaluator", self.utility_agent.execute)
        workflow.add_node("car_evaluator", self.car_evaluator_agent.execute)
        workflow.add_node("manager", self.manager_agent.execute)

        # Define edges (sequential workflow)
        workflow.set_entry_point("flight")
        workflow.add_edge("flight", "hotel")
        workflow.add_edge("hotel", "car_rental")
        workflow.add_edge("car_rental", "goal_evaluator")
        workflow.add_edge("goal_evaluator", "utility_evaluator")
        workflow.add_edge("utility_evaluator", "car_evaluator")
        workflow.add_edge("car_evaluator", "manager")
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
                "flight_results": None,
                "hotel_results": None,
                "goal_evaluation": None,
                "utility_evaluation": None,
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
                "goal_evaluation": final_state.get('goal_evaluation'),
                "utility_evaluation": final_state.get('utility_evaluation'),
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
