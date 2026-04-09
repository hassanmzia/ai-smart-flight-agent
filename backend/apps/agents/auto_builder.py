"""
Smart Itinerary Auto-Builder
Given minimal input (destination + dates), automatically builds a complete
day-by-day itinerary using all available sub-agents.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.conf import settings

logger = logging.getLogger(__name__)


class SmartItineraryBuilder:
    """
    Automatically builds a complete trip itinerary by orchestrating
    all available agents in parallel.
    """

    def __init__(self, user=None):
        self.user = user

    def build(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        origin: str = '',
        budget: float = None,
        travelers: int = 1,
        trip_style: str = 'balanced',
        preferences: dict = None,
    ) -> Dict[str, Any]:
        """
        Build a complete itinerary from minimal input.

        Returns a comprehensive trip plan with flights, hotels, restaurants,
        attractions, weather, and day-by-day schedule.
        """
        preferences = preferences or {}

        # Calculate trip duration
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        num_days = (end - start).days + 1

        logger.info(f"Building {num_days}-day itinerary: {origin} -> {destination}")

        # Phase 1: Gather all data in parallel
        gathered_data = self._gather_all_data(
            destination=destination,
            origin=origin,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            travelers=travelers,
            preferences=preferences,
        )

        # Phase 2: Use LLM to build optimized day-by-day plan
        itinerary = self._build_day_plan(
            destination=destination,
            origin=origin,
            start_date=start_date,
            end_date=end_date,
            num_days=num_days,
            budget=budget,
            travelers=travelers,
            trip_style=trip_style,
            gathered_data=gathered_data,
            preferences=preferences,
        )

        return itinerary

    def _gather_all_data(self, **kwargs) -> Dict[str, Any]:
        """Gather data from all sub-agents in parallel."""
        data = {}

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {}

            # Flight search
            if kwargs.get('origin'):
                futures['flights'] = executor.submit(
                    self._search_flights, kwargs
                )

            # Hotel search
            futures['hotels'] = executor.submit(
                self._search_hotels, kwargs
            )

            # Restaurant search
            futures['restaurants'] = executor.submit(
                self._search_restaurants, kwargs
            )

            # Weather forecast
            futures['weather'] = executor.submit(
                self._get_weather, kwargs
            )

            # Tourist attractions
            futures['attractions'] = executor.submit(
                self._search_attractions, kwargs
            )

            # Destination intelligence
            futures['intelligence'] = executor.submit(
                self._get_destination_intelligence, kwargs
            )

            # Collect results
            for key, future in futures.items():
                try:
                    data[key] = future.result(timeout=30)
                except Exception as e:
                    logger.warning(f"Failed to gather {key}: {e}")
                    data[key] = None

        return data

    def _search_flights(self, kwargs):
        """Search for flights."""
        try:
            from .agent_tools import FlightSearchTool
            return FlightSearchTool.search_flights(
                origin=kwargs['origin'],
                destination=kwargs['destination'],
                date=kwargs['start_date'],
                return_date=kwargs['end_date'],
                passengers=kwargs.get('travelers', 1),
            )
        except Exception as e:
            logger.warning(f"Flight search failed: {e}")
            return None

    def _search_hotels(self, kwargs):
        """Search for hotels."""
        try:
            from .agent_tools import HotelSearchTool
            return HotelSearchTool.search_hotels(
                location=kwargs['destination'],
                check_in=kwargs['start_date'],
                check_out=kwargs['end_date'],
                guests=kwargs.get('travelers', 1),
            )
        except Exception as e:
            logger.warning(f"Hotel search failed: {e}")
            return None

    def _search_restaurants(self, kwargs):
        """Search for restaurants."""
        try:
            from .agent_tools import RestaurantSearchTool
            tool = RestaurantSearchTool()
            return tool.search(
                location=kwargs['destination'],
                cuisine=kwargs.get('preferences', {}).get('cuisine', ''),
            )
        except Exception as e:
            logger.warning(f"Restaurant search failed: {e}")
            return None

    def _get_weather(self, kwargs):
        """Get weather forecast."""
        try:
            from .integrations.weather_client import WeatherClient
            client = WeatherClient()
            return client.get_weather_by_city(kwargs['destination'])
        except Exception as e:
            logger.warning(f"Weather fetch failed: {e}")
            return None

    def _search_attractions(self, kwargs):
        """Search for tourist attractions."""
        try:
            from .integrations.maps_client import MapsClient
            client = MapsClient()
            return client.nearby_search(
                location=kwargs['destination'],
                type='tourist_attraction',
                radius=10000,
            )
        except Exception as e:
            logger.warning(f"Attraction search failed: {e}")
            return None

    def _get_destination_intelligence(self, kwargs):
        """Get enhanced destination intelligence from LLM."""
        try:
            import os
            openai_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
            if not openai_key or openai_key in ('your_openai_api_key_here', ''):
                return None

            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage

            model = ChatOpenAI(
                model='gpt-4o-mini',
                temperature=0.3,
                api_key=openai_key,
                request_timeout=30,
            )

            prompt = f"""Provide a brief travel intelligence summary for {kwargs['destination']}
for dates {kwargs['start_date']} to {kwargs['end_date']}. Include:
- Best neighborhoods to stay
- Must-try local dishes (top 5)
- Key safety tips
- Local transport recommendations
- Cultural tips
Return as concise bullet points."""

            response = model.invoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            logger.warning(f"Destination intelligence failed: {e}")
            return None

    def _build_day_plan(self, **kwargs) -> Dict[str, Any]:
        """Use LLM to create an optimized day-by-day plan from gathered data."""
        import os
        import json

        gathered = kwargs.get('gathered_data', {})

        # Build context summary for LLM
        context_parts = []

        if gathered.get('flights'):
            flights = gathered['flights']
            if isinstance(flights, dict) and flights.get('best_flights'):
                top_flights = flights['best_flights'][:3]
                context_parts.append(f"Top flights found: {json.dumps(top_flights, default=str)[:1000]}")

        if gathered.get('hotels'):
            hotels = gathered['hotels']
            if isinstance(hotels, dict) and hotels.get('properties'):
                top_hotels = hotels['properties'][:5]
                context_parts.append(f"Top hotels: {json.dumps(top_hotels, default=str)[:1000]}")

        if gathered.get('restaurants'):
            context_parts.append(f"Restaurant data: {json.dumps(gathered['restaurants'], default=str)[:500]}")

        if gathered.get('weather'):
            context_parts.append(f"Weather: {json.dumps(gathered['weather'], default=str)[:300]}")

        if gathered.get('intelligence'):
            context_parts.append(f"Local intelligence: {gathered['intelligence'][:500]}")

        if gathered.get('attractions'):
            context_parts.append(f"Attractions: {json.dumps(gathered['attractions'], default=str)[:500]}")

        context_text = '\n\n'.join(context_parts)

        try:
            openai_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
            if not openai_key or openai_key in ('your_openai_api_key_here', ''):
                return self._build_basic_plan(**kwargs)

            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(
                model=getattr(settings, 'AGENT_CONFIG', {}).get('MODEL', 'gpt-4o-mini'),
                temperature=0.5,
                api_key=openai_key,
                request_timeout=90,
            )

            system = """You are an expert travel planner AI. Create a detailed day-by-day itinerary.
Return a JSON object with this structure (no markdown, raw JSON only):
{
  "title": "Trip title",
  "summary": "Brief trip overview",
  "estimated_budget": {
    "flights": number,
    "hotels": number,
    "food": number,
    "activities": number,
    "transport": number,
    "total": number
  },
  "recommended_flight": {"summary": "flight details", "price": number},
  "recommended_hotel": {"name": "hotel name", "price_per_night": number, "rating": number},
  "days": [
    {
      "day_number": 1,
      "date": "YYYY-MM-DD",
      "title": "Day theme",
      "items": [
        {
          "time": "09:00",
          "title": "Activity name",
          "type": "flight|checkin|attraction|restaurant|transport|shopping|relaxation",
          "description": "Brief description",
          "location": "Specific place name",
          "estimated_cost": number,
          "duration_hours": number,
          "tips": "Helpful tip"
        }
      ]
    }
  ],
  "packing_list": ["item1", "item2"],
  "travel_tips": ["tip1", "tip2"]
}"""

            prompt = f"""Plan a {kwargs['num_days']}-day trip:
- Destination: {kwargs['destination']}
- Origin: {kwargs.get('origin', 'Not specified')}
- Dates: {kwargs['start_date']} to {kwargs['end_date']}
- Travelers: {kwargs.get('travelers', 1)}
- Budget: {'$' + str(kwargs['budget']) if kwargs.get('budget') else 'Flexible'}
- Style: {kwargs.get('trip_style', 'balanced')}

Available data:
{context_text}

Create an optimized day-by-day plan. Schedule outdoor activities on good weather days.
Group nearby attractions together. Include breakfast, lunch, and dinner spots.
First day should include arrival/check-in, last day should include checkout/departure."""

            response = model.invoke([
                SystemMessage(content=system),
                HumanMessage(content=prompt),
            ])

            # Parse JSON response
            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]

            result = json.loads(content)
            result['gathered_data_summary'] = {
                'flights_found': bool(gathered.get('flights')),
                'hotels_found': bool(gathered.get('hotels')),
                'restaurants_found': bool(gathered.get('restaurants')),
                'weather_available': bool(gathered.get('weather')),
                'attractions_found': bool(gathered.get('attractions')),
            }
            return result

        except Exception as e:
            logger.error(f"LLM itinerary build failed: {e}")
            return self._build_basic_plan(**kwargs)

    def _build_basic_plan(self, **kwargs):
        """Fallback basic plan when LLM is unavailable."""
        from datetime import datetime, timedelta

        start = datetime.strptime(kwargs['start_date'], '%Y-%m-%d')
        days = []
        for i in range(kwargs['num_days']):
            day_date = start + timedelta(days=i)
            days.append({
                'day_number': i + 1,
                'date': day_date.strftime('%Y-%m-%d'),
                'title': f"Day {i + 1} in {kwargs['destination']}",
                'items': [
                    {'time': '09:00', 'title': 'Morning exploration', 'type': 'attraction',
                     'description': f'Explore {kwargs["destination"]}', 'estimated_cost': 0, 'duration_hours': 3},
                    {'time': '12:30', 'title': 'Lunch', 'type': 'restaurant',
                     'description': 'Try local cuisine', 'estimated_cost': 20, 'duration_hours': 1},
                    {'time': '14:00', 'title': 'Afternoon activity', 'type': 'attraction',
                     'description': 'Visit local attractions', 'estimated_cost': 15, 'duration_hours': 3},
                    {'time': '19:00', 'title': 'Dinner', 'type': 'restaurant',
                     'description': 'Evening dining', 'estimated_cost': 35, 'duration_hours': 1.5},
                ]
            })

        return {
            'title': f"Trip to {kwargs['destination']}",
            'summary': f"A {kwargs['num_days']}-day trip to {kwargs['destination']}",
            'days': days,
            'packing_list': ['Passport', 'Phone charger', 'Comfortable shoes', 'Weather-appropriate clothing'],
            'travel_tips': ['Book activities in advance', 'Learn a few local phrases', 'Keep copies of important documents'],
        }
