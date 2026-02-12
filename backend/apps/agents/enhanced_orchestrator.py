"""
Enhanced Multi-Agent Orchestrator with RAG Integration
Combines existing agents with new specialized agents and RAG pipeline
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from django.core.cache import cache
from django.conf import settings

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from .enhanced_agents import (
    HealthSafetyAgent,
    VisaRequirementsAgent,
    PackingListAgent,
    EnhancedLocalExpertAgent
)
from .rag_system import get_rag_pipeline, get_knowledge_base
from .multi_agent_system import TravelAgentState
from .agent_tools import FlightSearchTool, HotelSearchTool, WeatherTool

logger = logging.getLogger(__name__)


class EnhancedTravelOrchestrator:
    """
    Enhanced orchestrator that coordinates all travel agents including:
    - Existing agents (Flight, Hotel, etc.)
    - New specialized agents (Health, Visa, Packing, Enhanced Local Expert)
    - RAG-enhanced knowledge retrieval
    - Redis caching for performance
    """

    def __init__(
        self,
        model_name: str = "gpt-4",
        use_cache: bool = True,
        use_rag: bool = True
    ):
        """
        Initialize the enhanced orchestrator.

        Args:
            model_name: LLM model to use
            use_cache: Whether to use Redis caching
            use_rag: Whether to use RAG for knowledge enhancement
        """
        self.model = ChatOpenAI(model_name=model_name, temperature=0.7)
        self.use_cache = use_cache
        self.use_rag = use_rag

        # Initialize tools
        self.flight_tool = FlightSearchTool()
        self.hotel_tool = HotelSearchTool()
        self.weather_tool = WeatherTool()

        # Initialize enhanced agents
        self.health_safety_agent = HealthSafetyAgent(model_name=model_name)
        self.visa_agent = VisaRequirementsAgent()
        self.packing_agent = PackingListAgent()
        self.local_expert_agent = EnhancedLocalExpertAgent()

        # Initialize RAG pipeline
        if self.use_rag:
            self.rag_pipeline = get_rag_pipeline()
            self.knowledge_base = get_knowledge_base()

        logger.info(f"Enhanced orchestrator initialized with model: {model_name}")

    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from parameters"""
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        return ":".join(key_parts)

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get value from cache if enabled"""
        if not self.use_cache:
            return None
        return cache.get(cache_key)

    def _set_in_cache(self, cache_key: str, value: Any, timeout: int = 3600) -> None:
        """Set value in cache if enabled"""
        if self.use_cache:
            cache.set(cache_key, value, timeout)

    def plan_trip(
        self,
        origin: str,
        destination: str,
        country: str,
        start_date: str,
        end_date: str,
        budget: float,
        passengers: int = 1,
        interests: List[str] = None,
        dietary_restrictions: List[str] = None,
        citizenship: str = "USA"
    ) -> Dict[str, Any]:
        """
        Plan a complete trip using all available agents.

        Args:
            origin: Origin city/airport
            destination: Destination city
            country: Destination country
            start_date: Trip start date (YYYY-MM-DD)
            end_date: Trip end date (YYYY-MM-DD)
            budget: Total budget in USD
            passengers: Number of travelers
            interests: List of interests
            dietary_restrictions: Dietary restrictions
            citizenship: Traveler's citizenship for visa requirements

        Returns:
            Complete trip plan with all details
        """
        try:
            logger.info(f"Planning trip to {destination}, {country} from {start_date} to {end_date}")

            # Check cache first
            cache_key = self._get_cache_key(
                "trip_plan",
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                budget=budget
            )

            cached_plan = self._get_from_cache(cache_key)
            if cached_plan:
                logger.info("Returning cached trip plan")
                return cached_plan

            # Parallel execution of independent agents
            with ThreadPoolExecutor(max_workers=8) as executor:
                # Submit all agent tasks
                futures = {
                    'flights': executor.submit(self._search_flights, origin, destination, start_date, end_date, passengers),
                    'hotels': executor.submit(self._search_hotels, destination, start_date, end_date, budget, passengers),
                    'weather': executor.submit(self._get_weather, destination, start_date, end_date),
                    'health_safety': executor.submit(self._get_health_safety, destination, country, start_date, end_date),
                    'visa': executor.submit(self._get_visa_requirements, origin, country, citizenship),
                    'dining': executor.submit(self._get_dining_recommendations, destination, country, dietary_restrictions, interests),
                }

                # Collect results
                results = {}
                for key, future in futures.items():
                    try:
                        results[key] = future.result(timeout=60)
                    except Exception as e:
                        logger.error(f"Error in {key} agent: {str(e)}")
                        results[key] = {'error': str(e)}

            # Generate packing list based on weather
            packing_list = self._generate_packing_list(
                destination,
                start_date,
                end_date,
                results.get('weather', {})
            )

            # Get RAG-enhanced destination insights
            destination_insights = {}
            if self.use_rag:
                destination_insights = self._get_rag_insights(destination, interests or [])

            # Synthesize final itinerary
            final_plan = self._synthesize_itinerary(
                origin=origin,
                destination=destination,
                country=country,
                start_date=start_date,
                end_date=end_date,
                budget=budget,
                passengers=passengers,
                flights=results.get('flights', {}),
                hotels=results.get('hotels', {}),
                weather=results.get('weather', {}),
                health_safety=results.get('health_safety', {}),
                visa=results.get('visa', {}),
                dining=results.get('dining', {}),
                packing=packing_list,
                insights=destination_insights
            )

            # Cache the result
            self._set_in_cache(cache_key, final_plan, timeout=1800)  # 30 minutes

            logger.info(f"Trip plan completed successfully for {destination}")
            return final_plan

        except Exception as e:
            logger.error(f"Error planning trip: {str(e)}")
            return {
                'error': str(e),
                'destination': destination,
                'status': 'failed'
            }

    def _search_flights(self, origin: str, destination: str, start_date: str, end_date: str, passengers: int) -> Dict:
        """Search for flights"""
        try:
            cache_key = self._get_cache_key("flights", origin=origin, dest=destination, date=start_date)
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached

            result = self.flight_tool.search_flights(
                origin=origin,
                destination=destination,
                date=start_date,
                trip_type=1,
                return_date=end_date,
                passengers=passengers
            )

            self._set_in_cache(cache_key, result, timeout=900)  # 15 minutes
            return result

        except Exception as e:
            logger.error(f"Flight search error: {str(e)}")
            return {'error': str(e)}

    def _search_hotels(self, destination: str, start_date: str, end_date: str, budget: float, passengers: int) -> Dict:
        """Search for hotels"""
        try:
            cache_key = self._get_cache_key("hotels", dest=destination, checkin=start_date, checkout=end_date)
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached

            result = self.hotel_tool.search_hotels(
                destination=destination,
                check_in_date=start_date,
                check_out_date=end_date,
                guests=passengers,
                budget_per_night=budget / 5  # Rough estimate
            )

            self._set_in_cache(cache_key, result, timeout=900)  # 15 minutes
            return result

        except Exception as e:
            logger.error(f"Hotel search error: {str(e)}")
            return {'error': str(e)}

    def _get_weather(self, destination: str, start_date: str, end_date: str) -> Dict:
        """Get weather forecast"""
        try:
            cache_key = self._get_cache_key("weather", dest=destination, start=start_date)
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached

            # Use weather tool to get forecast
            result = self.weather_tool.get_weather(
                location=destination,
                start_date=start_date,
                end_date=end_date
            )

            self._set_in_cache(cache_key, result, timeout=1800)  # 30 minutes
            return result

        except Exception as e:
            logger.error(f"Weather fetch error: {str(e)}")
            return {'error': str(e)}

    def _get_health_safety(self, destination: str, country: str, start_date: str, end_date: str) -> Dict:
        """Get health and safety information"""
        try:
            cache_key = self._get_cache_key("health_safety", country=country)
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached

            result = self.health_safety_agent.get_health_safety_report(
                destination=destination,
                country=country,
                start_date=start_date,
                end_date=end_date
            )

            self._set_in_cache(cache_key, result, timeout=86400)  # 24 hours
            return result

        except Exception as e:
            logger.error(f"Health/safety fetch error: {str(e)}")
            return {'error': str(e)}

    def _get_visa_requirements(self, origin: str, destination_country: str, citizenship: str) -> Dict:
        """Get visa requirements"""
        try:
            cache_key = self._get_cache_key("visa", origin=origin, dest=destination_country, citizenship=citizenship)
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached

            result = self.visa_agent.get_visa_requirements(
                origin_country=origin,
                destination_country=destination_country,
                citizenship=citizenship
            )

            self._set_in_cache(cache_key, result, timeout=604800)  # 7 days
            return result

        except Exception as e:
            logger.error(f"Visa requirements fetch error: {str(e)}")
            return {'error': str(e)}

    def _get_dining_recommendations(
        self,
        destination: str,
        country: str,
        dietary_restrictions: List[str],
        interests: List[str]
    ) -> Dict:
        """Get dining recommendations"""
        try:
            cache_key = self._get_cache_key(
                "dining",
                dest=destination,
                dietary=','.join(dietary_restrictions or [])
            )
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached

            result = self.local_expert_agent.get_dining_recommendations(
                city=destination,
                country=country,
                dietary_restrictions=dietary_restrictions,
                cuisine_preferences=interests,
                budget="moderate"
            )

            self._set_in_cache(cache_key, result, timeout=3600)  # 1 hour
            return result

        except Exception as e:
            logger.error(f"Dining recommendations fetch error: {str(e)}")
            return {'error': str(e)}

    def _generate_packing_list(self, destination: str, start_date: str, end_date: str, weather_data: Dict) -> Dict:
        """Generate packing list"""
        try:
            result = self.packing_agent.generate_packing_list(
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                weather_data=weather_data,
                trip_type="leisure"
            )

            return result

        except Exception as e:
            logger.error(f"Packing list generation error: {str(e)}")
            return {'error': str(e)}

    def _get_rag_insights(self, destination: str, interests: List[str]) -> Dict:
        """Get RAG-enhanced destination insights"""
        try:
            if not self.use_rag:
                return {}

            # Build queries based on interests
            queries = [
                f"What are the must-see attractions in {destination}?",
                f"What is the local culture and customs in {destination}?",
                f"What are the best {interest} activities in {destination}?"
                for interest in (interests or ['general'])[:3]
            ]

            insights = {}
            for query in queries:
                response = self.rag_pipeline.generate_response(
                    query=query,
                    destination=destination,
                    n_context_docs=2
                )
                insights[query] = response

            return insights

        except Exception as e:
            logger.error(f"RAG insights fetch error: {str(e)}")
            return {}

    def _synthesize_itinerary(self, **kwargs) -> Dict[str, Any]:
        """Synthesize final itinerary from all agent results"""
        try:
            # Use LLM to create coherent narrative
            prompt = f"""
            Create a comprehensive travel itinerary based on the following information:

            Destination: {kwargs['destination']}, {kwargs['country']}
            Dates: {kwargs['start_date']} to {kwargs['end_date']}
            Origin: {kwargs['origin']}
            Budget: ${kwargs['budget']}
            Passengers: {kwargs['passengers']}

            Flight Options:
            {json.dumps(kwargs.get('flights', {}), indent=2)}

            Hotel Options:
            {json.dumps(kwargs.get('hotels', {}), indent=2)}

            Weather Forecast:
            {json.dumps(kwargs.get('weather', {}), indent=2)}

            Health & Safety:
            {json.dumps(kwargs.get('health_safety', {}), indent=2)}

            Visa Requirements:
            {json.dumps(kwargs.get('visa', {}), indent=2)}

            Dining Recommendations:
            {json.dumps(kwargs.get('dining', {}), indent=2)}

            Packing List:
            {json.dumps(kwargs.get('packing', {}), indent=2)}

            Additional Insights:
            {json.dumps(kwargs.get('insights', {}), indent=2)}

            Create a detailed day-by-day itinerary in markdown format with:
            1. Overview and trip summary
            2. Flight and hotel recommendations
            3. Daily activities and schedules
            4. Dining suggestions
            5. Health and safety reminders
            6. Packing checklist
            7. Budget breakdown
            """

            response = self.model.invoke([HumanMessage(content=prompt)])

            return {
                'destination': kwargs['destination'],
                'country': kwargs['country'],
                'dates': f"{kwargs['start_date']} to {kwargs['end_date']}",
                'itinerary_text': response.content,
                'raw_data': {
                    'flights': kwargs.get('flights', {}),
                    'hotels': kwargs.get('hotels', {}),
                    'weather': kwargs.get('weather', {}),
                    'health_safety': kwargs.get('health_safety', {}),
                    'visa': kwargs.get('visa', {}),
                    'dining': kwargs.get('dining', {}),
                    'packing': kwargs.get('packing', {}),
                },
                'budget': kwargs['budget'],
                'passengers': kwargs['passengers'],
                'generated_at': datetime.now().isoformat(),
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Itinerary synthesis error: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
