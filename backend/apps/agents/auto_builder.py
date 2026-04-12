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
        accommodation_preference: str = '',
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

        # Load per-user personalization (dietary/faith/mobility/pace/memories)
        # so the LLM honors the traveler's profile, not just the route.
        try:
            from .personalization_service import build_user_planning_context
            user_context = build_user_planning_context(self.user)
        except Exception as e:
            logger.warning(f"Personalization context load failed: {e}")
            user_context = {}

        # Phase 1: Gather all data in parallel
        gathered_data = self._gather_all_data(
            destination=destination,
            origin=origin,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            travelers=travelers,
            preferences=preferences,
            accommodation_preference=accommodation_preference,
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
            user_context=user_context,
        )

        # Echo personalization signals so the API response can display a
        # "Personalized for you" badge on the frontend.
        if isinstance(itinerary, dict):
            itinerary['personalization'] = {
                'applied': bool(user_context.get('has_personalization')),
                'signals': user_context.get('signals', []),
            }

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

            # Rental search — for groups of 4+ or when explicitly requested
            travelers = kwargs.get('travelers', 1)
            accom_pref = kwargs.get('accommodation_preference', '')
            if travelers >= 4 or accom_pref in ('rental', 'both', 'all'):
                futures['rentals'] = executor.submit(
                    self._search_rentals, kwargs
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

    def _search_rentals(self, kwargs):
        """Search for vacation rentals — reuses hotel search and filters for rental-type properties."""
        try:
            from .agent_tools import HotelSearchTool
            raw = HotelSearchTool.search_hotels(
                location=kwargs['destination'],
                check_in_date=kwargs['start_date'],
                check_out_date=kwargs['end_date'],
                adults=kwargs.get('travelers', 1),
            )

            rental_keywords = ('villa', 'apartment', 'cabin', 'cottage', 'home', 'house',
                               'townhouse', 'condo', 'chalet', 'farmhouse', 'rental', 'entire')
            amenity_keywords = ('kitchen', 'washer', 'laundry', 'dishwasher')

            rentals = []
            for prop in (raw or {}).get('properties', raw.get('hotels', [])) if isinstance(raw, dict) else []:
                name_lower = (prop.get('name', '') + ' ' + prop.get('type', '')).lower()
                prop_amenities = ' '.join(prop.get('amenities', [])).lower() if prop.get('amenities') else ''
                if (any(kw in name_lower for kw in rental_keywords) or
                        any(kw in prop_amenities for kw in amenity_keywords)):
                    prop['is_rental'] = True
                    rentals.append(prop)

            return {'rentals': rentals, 'total_found': len(rentals)}
        except Exception as e:
            logger.warning(f"Rental search failed: {e}")
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
        """
        Reuse the full structured destination-intelligence agent from views.py
        (weather_by_day, safety, best_transport, local_events, must_see_attractions,
        food_scene, local_customs, packing_essentials) so the Smart Itinerary
        Builder is as informed as the main /plan-travel narrative path.

        Falls back to None on any failure — callers handle that.
        """
        try:
            from .views import _gather_enhanced_agent_data
            enhanced = _gather_enhanced_agent_data(
                destination=kwargs['destination'],
                origin=kwargs.get('origin', ''),
                departure_date=kwargs['start_date'],
                return_date=kwargs['end_date'],
                cuisine=kwargs.get('preferences', {}).get('cuisine', ''),
            )
            # Return the full structured intel dict (same shape the Intelligence tab renders).
            return enhanced.get('destination_intelligence') or None
        except Exception as e:
            logger.warning(f"Destination intelligence failed: {e}")
            return None

    def _build_day_plan(self, **kwargs) -> Dict[str, Any]:
        """Use LLM to create an optimized day-by-day plan from gathered data."""
        import os
        import json

        gathered = kwargs.get('gathered_data', {})
        user_context = kwargs.get('user_context', {}) or {}

        # Render the traveler profile as a natural-language block the LLM can
        # honor alongside the route/weather context.
        personalization_block = ''
        try:
            from .personalization_service import format_user_context_for_prompt
            personalization_block = format_user_context_for_prompt(user_context)
        except Exception as e:
            logger.warning(f"Personalization prompt formatting failed: {e}")

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

        if gathered.get('rentals'):
            rentals = gathered['rentals']
            if isinstance(rentals, dict) and rentals.get('rentals'):
                top_rentals = rentals['rentals'][:5]
                context_parts.append(f"Top vacation rentals (villas/apartments): {json.dumps(top_rentals, default=str)[:1000]}")

        if gathered.get('restaurants'):
            context_parts.append(f"Restaurant data: {json.dumps(gathered['restaurants'], default=str)[:500]}")

        if gathered.get('weather'):
            context_parts.append(f"Weather: {json.dumps(gathered['weather'], default=str)[:300]}")

        # ── Structured destination intelligence (same shape as the Intelligence
        # tab in the UI). Surface each sub-field under its own header so the
        # LLM can actually use safety / transport / customs / food_scene / events
        # / must_see when making day-by-day choices, rather than treating this
        # as an opaque text blob.
        intel = gathered.get('intelligence') if isinstance(gathered.get('intelligence'), dict) else None
        if intel:
            if intel.get('weather_by_day'):
                context_parts.append(
                    f"Weather by day (use to pick indoor/outdoor activities): "
                    f"{json.dumps(intel['weather_by_day'], default=str)[:800]}"
                )
            if intel.get('safety'):
                context_parts.append(
                    f"Safety (AVOID `areas_to_avoid` for hotels/restaurants; cite `scam_warnings` "
                    f"in tips; if `tap_water_safe` is false, add water-bottle to packing): "
                    f"{json.dumps(intel['safety'], default=str)[:800]}"
                )
            if intel.get('best_transport'):
                context_parts.append(
                    f"Transport (adopt `recommendation` — public_transit/car_rental/mixed — "
                    f"everywhere in the plan): {json.dumps(intel['best_transport'], default=str)[:600]}"
                )
            if intel.get('local_events'):
                context_parts.append(
                    f"Local events during the trip (schedule onto the matching date): "
                    f"{json.dumps(intel['local_events'], default=str)[:800]}"
                )
            if intel.get('local_customs'):
                context_parts.append(
                    f"Local customs (reflect `dress_code` / `dining_etiquette` in notes; "
                    f"use `useful_phrases` as source for phrase_of_the_day): "
                    f"{json.dumps(intel['local_customs'], default=str)[:800]}"
                )
            if intel.get('must_see_attractions'):
                context_parts.append(
                    f"Must-see attractions (pick 2-3 per day across the trip, use real names): "
                    f"{json.dumps(intel['must_see_attractions'], default=str)[:1200]}"
                )
            if intel.get('food_scene'):
                context_parts.append(
                    f"Food scene (weave 2-3 `must_try_dishes` into dinners across different days): "
                    f"{json.dumps(intel['food_scene'], default=str)[:600]}"
                )
            if intel.get('packing_essentials'):
                context_parts.append(
                    f"Packing essentials: {json.dumps(intel['packing_essentials'], default=str)[:400]}"
                )

        if gathered.get('attractions'):
            context_parts.append(f"Attractions (from Maps API): {json.dumps(gathered['attractions'], default=str)[:500]}")

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
  "recommended_rental": {"name": "property name", "price_per_night": number, "bedrooms": number, "max_guests": number, "cleaning_fee": number} or null,
  "days": [
    {
      "day_number": 1,
      "date": "YYYY-MM-DD",
      "title": "Day theme",
      "phrase_of_the_day": "Optional — a useful local-language phrase + pronunciation. Include when the local language is NOT in the traveler's languages_spoken list. Omit if not applicable.",
      "faith_note": "Optional — 1 line naming a nearby worship place / halal-or-kosher option / faith etiquette. Include when traveler's faith is set (not 'none'). Omit otherwise.",
      "walking_km_estimate": "Optional number — total walking km for the day. Include when the traveler has a max_walking_km_per_day limit.",
      "items": [
        {
          "time": "09:00",
          "title": "Activity name",
          "type": "flight|checkin|attraction|restaurant|transport|shopping|relaxation|prayer_break",
          "description": "Brief description",
          "location": "Specific place name",
          "estimated_cost": number,
          "duration_hours": number,
          "tips": "Helpful tip",
          "personalization_notes": "Short note on how this honors the Traveler Profile — e.g. 'Halal-certified', 'Wheelchair-accessible entrance', 'Vegan menu available', 'Near mosque', 'Quiet pace'. Include whenever a profile dimension applies. Use empty string if no profile dimension applies."
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

{personalization_block}

Create an optimized day-by-day plan following these rules:
1. WEATHER-AWARE: Schedule outdoor activities (parks, beaches, walking tours) on sunny/clear days using `weather_by_day`. Move indoor activities (museums, shopping, spas) to rainy or overcast days. Reference the per-day condition/rain_chance when assigning activities.
2. PROXIMITY GROUPING: Cluster nearby attractions on the same day to minimize transit time. Order activities geographically so travelers move in one direction, not back-and-forth.
3. MEALS: Include breakfast, lunch, and dinner spots near the day's activities. Weave 2-3 dishes from `food_scene.must_try_dishes` into dinners across different days — name the dish AND the restaurant.
4. PACING: Alternate high-energy and relaxed activities. No more than 3 major attractions per day (or the Traveler Profile's max_activities_per_day if stricter).
5. LOGISTICS: First day should include arrival/check-in with lighter activities. Last day should include checkout/departure with morning-only plans.
6. TRANSPORT: Every transport item between distant locations MUST match `best_transport.recommendation`. If it's `public_transit`, use metro/bus/walk/rideshare; if `car_rental`, use the car; if `mixed`, choose whichever fits the stop. Include estimated travel time for each transfer.
7. ACCOMMODATION: If vacation rental data is available and there are 4+ travelers, compare hotel vs rental total cost and recommend the better value. Include "recommended_rental" in the JSON if a rental is a good fit (shared kitchen saves on meals, whole-property pricing split across travelers). Set it to null if hotels are clearly better. Also cross-check every hotel/rental against `safety.areas_to_avoid` — skip picks that fall inside those areas.
8. PERSONALIZATION (BINDING — the plan MUST visibly reflect the Traveler Profile above):
   - DIETARY/ALLERGIES: Every restaurant item MUST be compatible with the traveler's dietary_preference and allergies. Name only compatible restaurants and put the compatibility in `personalization_notes` (e.g., "Halal", "Vegan menu", "No peanuts").
   - FAITH: If faith is set and faith_site_interest is true, include at least one worship-site visit across the trip. On every day, set `faith_note` to a short faith-aware line (nearby mosque/church/temple, kosher deli, dress code tip). If prayer_reminders is true, add `prayer_break` items at midday/afternoon/sunset windows (15-min duration, $0 cost).
   - MOBILITY: If mobility is not 'full', every attraction/restaurant item MUST be accessible — state "wheelchair-accessible" or "step-free" in `personalization_notes`. Exclude stairs-only or steep-terrain venues.
   - WALKING: If max_walking_km_per_day is set, keep each day's walking under it. Set `walking_km_estimate` on each day.
   - LANGUAGE: If the destination's primary language is NOT in the traveler's languages_spoken, set `phrase_of_the_day` on every day. Source phrases from `local_customs.useful_phrases` when available, otherwise use your knowledge. Different phrase each day (greeting → ordering food → directions → thank-you → emergency help).
   - PACE: Never exceed max_activities_per_day major activities (meals don't count).
   - PREFERENCES: Prefer the traveler's favored cuisines, airlines, and hotel chains when options are equivalent. Avoid patterns on the traveler's "disliked previously" list.
9. MUST-SEE ATTRACTIONS: Each day (except arrival/departure) must include 2-3 items from `must_see_attractions`, using the exact `name` field. Spread the top picks across days so no single day is empty.
10. LOCAL EVENTS: Any event in `local_events` whose `date` falls within the trip MUST be scheduled onto that exact date as an item. Don't invent dates — match them.
11. SAFETY NOTES: Include 1-2 of `safety.scam_warnings` in `travel_tips`. If `safety.tap_water_safe` is false, add "Water bottle / water purification" to `packing_list` AND add a morning "Grab bottled water" line on Day 1. Put `safety.emergency_number` in `travel_tips`.
12. LOCAL CUSTOMS: If `local_customs.dress_code` is notable (e.g., cover shoulders in temples), add it to `travel_tips`. If `local_customs.dining_etiquette` has a specific rule (tipping %, remove shoes, no pork), reflect it in the `tips` field of relevant restaurant items."""

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
                'rentals_found': bool(gathered.get('rentals')),
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
