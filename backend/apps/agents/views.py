from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Sum, Count, Q
from django.conf import settings
from django.utils import timezone
import json
import logging
import uuid

from .models import AgentSession, AgentExecution, AgentLog
from .serializers import (
    AgentSessionSerializer,
    AgentSessionListSerializer,
    AgentSessionCreateSerializer,
    AgentExecutionSerializer,
    AgentExecutionListSerializer,
    AgentExecutionCreateSerializer,
    AgentLogSerializer
)

logger = logging.getLogger(__name__)


class AgentSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AgentSession model.
    Provides CRUD operations for agent sessions.
    """

    queryset = AgentSession.objects.all()
    serializer_class = AgentSessionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['session_id', 'user_intent']
    filterset_fields = ['status', 'started_at']
    ordering_fields = ['started_at', 'completed_at', 'total_executions', 'total_cost']
    ordering = ['-started_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return AgentSessionListSerializer
        elif self.action == 'create':
            return AgentSessionCreateSerializer
        return AgentSessionSerializer

    def get_queryset(self):
        """Filter queryset to only show authenticated user's sessions unless staff."""
        if self.request.user.is_staff:
            return AgentSession.objects.all()
        return AgentSession.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Create session with generated session_id."""
        session_id = f"session_{uuid.uuid4().hex[:16]}"
        serializer.save(user=self.request.user, session_id=session_id)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark session as completed."""
        session = self.get_object()
        session.mark_completed()
        serializer = self.get_serializer(session)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """Mark session as failed."""
        session = self.get_object()
        session.mark_failed()
        serializer = self.get_serializer(session)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get analytics for a specific session."""
        session = self.get_object()
        executions = session.executions.all()

        analytics = {
            'total_executions': executions.count(),
            'completed_executions': executions.filter(status='completed').count(),
            'failed_executions': executions.filter(status='failed').count(),
            'total_tokens': session.total_tokens_used,
            'total_cost': float(session.total_cost),
            'average_execution_time': executions.filter(
                status='completed'
            ).aggregate(Avg('execution_time_ms'))['execution_time_ms__avg'],
            'agents_used': executions.values('agent_type').distinct().count(),
            'execution_by_agent': list(
                executions.values('agent_type').annotate(
                    count=Count('id'),
                    avg_time=Avg('execution_time_ms'),
                    total_tokens=Sum('tokens_used')
                )
            ),
        }
        return Response(analytics)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get overall statistics for user's sessions."""
        sessions = self.get_queryset()

        stats = {
            'total_sessions': sessions.count(),
            'active_sessions': sessions.filter(status='active').count(),
            'completed_sessions': sessions.filter(status='completed').count(),
            'failed_sessions': sessions.filter(status='failed').count(),
            'total_executions': sessions.aggregate(Sum('total_executions'))['total_executions__sum'] or 0,
            'total_tokens_used': sessions.aggregate(Sum('total_tokens_used'))['total_tokens_used__sum'] or 0,
            'total_cost': float(sessions.aggregate(Sum('total_cost'))['total_cost__sum'] or 0),
        }
        return Response(stats)


class AgentExecutionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AgentExecution model.
    Provides CRUD operations for agent executions.
    """

    queryset = AgentExecution.objects.all()
    serializer_class = AgentExecutionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['execution_id', 'agent_type']
    filterset_fields = ['session', 'agent_type', 'status', 'started_at']
    ordering_fields = ['started_at', 'completed_at', 'execution_time_ms', 'cost']
    ordering = ['-started_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return AgentExecutionListSerializer
        elif self.action == 'create':
            return AgentExecutionCreateSerializer
        return AgentExecutionSerializer

    def get_queryset(self):
        """Filter queryset to only show authenticated user's executions unless staff."""
        if self.request.user.is_staff:
            return AgentExecution.objects.all()
        return AgentExecution.objects.filter(session__user=self.request.user)

    def perform_create(self, serializer):
        """Create execution with generated execution_id."""
        session_id = self.request.data.get('session_id')
        try:
            session = AgentSession.objects.get(
                session_id=session_id,
                user=self.request.user
            )
        except AgentSession.DoesNotExist:
            raise serializers.ValidationError({'session_id': 'Invalid session_id'})

        execution_id = f"exec_{uuid.uuid4().hex[:16]}"
        serializer.save(session=session, execution_id=execution_id)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark execution as completed."""
        execution = self.get_object()
        output_data = request.data.get('output_data', {})
        tokens_used = request.data.get('tokens_used', 0)
        cost = request.data.get('cost', 0)

        execution.tokens_used = tokens_used
        execution.cost = cost
        execution.mark_completed(output_data)

        serializer = self.get_serializer(execution)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """Mark execution as failed."""
        execution = self.get_object()
        error_message = request.data.get('error_message', 'Unknown error')
        execution.mark_failed(error_message)

        serializer = self.get_serializer(execution)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_agent_type(self, request):
        """Get executions grouped by agent type."""
        executions = self.get_queryset()
        agent_type = request.query_params.get('agent_type')

        if agent_type:
            executions = executions.filter(agent_type=agent_type)

        stats = executions.values('agent_type').annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed')),
            failed=Count('id', filter=Q(status='failed')),
            avg_time=Avg('execution_time_ms'),
            total_tokens=Sum('tokens_used'),
            total_cost=Sum('cost')
        )

        return Response(stats)


class AgentLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for AgentLog model.
    Provides read-only access to agent logs.
    """

    queryset = AgentLog.objects.all()
    serializer_class = AgentLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['message', 'agent_type', 'function_name']
    filterset_fields = ['session', 'execution', 'log_level', 'agent_type', 'timestamp']
    ordering_fields = ['timestamp', 'log_level']
    ordering = ['-timestamp']

    def get_queryset(self):
        """Filter queryset to only show authenticated user's logs unless staff."""
        if self.request.user.is_staff:
            return AgentLog.objects.all()
        return AgentLog.objects.filter(session__user=self.request.user)

    @action(detail=False, methods=['get'])
    def errors(self, request):
        """Get all error and critical logs."""
        logs = self.get_queryset().filter(
            log_level__in=['error', 'critical']
        )
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_session(self, request):
        """Get logs for a specific session."""
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response(
                {'error': 'session_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            session = AgentSession.objects.get(
                session_id=session_id,
                user=request.user
            )
        except AgentSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        logs = self.get_queryset().filter(session=session)
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)


def _gather_enhanced_agent_data(*, destination, origin, departure_date, return_date, cuisine):
    """
    Call all enhanced agents (weather, health/safety, visa, packing, local expert)
    and return their data.  Then use LLM to generate *smart* destination intelligence
    that is date-aware, location-specific, and decision-ready.
    """
    enhanced = {}

    # ── 1. Try real weather API first ──
    try:
        from .integrations.weather_client import WeatherClient
        client = WeatherClient()
        if client.api_key:
            weather = client.get_weather_by_city(destination, units='metric')
            if weather:
                enhanced['weather'] = {
                    'temperature': f"{weather.get('temperature', 'N/A')}°C",
                    'feels_like': f"{weather.get('feels_like', 'N/A')}°C",
                    'condition': weather.get('condition', ''),
                    'description': weather.get('description', ''),
                    'humidity': f"{weather.get('humidity', 'N/A')}%",
                    'wind_speed': f"{weather.get('wind_speed', 'N/A')} m/s",
                    'source': 'OpenWeatherMap'
                }
    except Exception as e:
        logger.debug(f"Real weather client failed: {e}")

    # ── 2. Gather basic data from enhanced agents ──
    try:
        from .enhanced_agents import HealthSafetyDataProvider
        safety_data = HealthSafetyDataProvider.get_travel_safety_score(destination)
        cdc_data = HealthSafetyDataProvider.get_cdc_travel_health_notices(destination)
        enhanced['health_safety_raw'] = {
            'safety_score': safety_data.get('overall_safety_score', 'N/A'),
            'crime_level': safety_data.get('crime_level', 'N/A'),
            'terrorism_threat': safety_data.get('terrorism_threat', 'N/A'),
            'political_stability': safety_data.get('political_stability', 'N/A'),
            'health_infrastructure': safety_data.get('health_infrastructure', 'N/A'),
            'emergency_numbers': safety_data.get('emergency_numbers', {}),
        }
    except Exception as e:
        logger.debug(f"Health/safety data failed: {e}")

    try:
        from .enhanced_agents import VisaRequirementsAgent
        visa_agent = VisaRequirementsAgent()
        visa_data = visa_agent.get_visa_requirements(
            origin_country=origin, destination_country=destination,
        )
        enhanced['visa_raw'] = {
            'visa_required': visa_data.get('visa_required', 'Check with embassy'),
            'max_stay': visa_data.get('max_stay', 'Varies'),
            'required_documents': visa_data.get('required_documents', []),
        }
    except Exception as e:
        logger.debug(f"Visa agent failed: {e}")

    # ── 3. LLM-powered destination intelligence (the smart part) ──
    # Instead of relying on placeholder data, use the LLM's knowledge
    # to generate REAL, destination-specific, date-aware intelligence.
    if settings.OPENAI_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage

            model = ChatOpenAI(
                model=settings.AGENT_CONFIG.get('MODEL', 'gpt-4o-mini'),
                temperature=0.3,
                api_key=settings.OPENAI_API_KEY,
            )

            intel_prompt = f"""You are a travel intelligence agent. Provide REAL, SPECIFIC data for a trip.
Destination: {destination}
Origin: {origin}
Travel dates: {departure_date} to {return_date or departure_date}
{f'Cuisine preference: {cuisine}' if cuisine else ''}

Return a JSON object (no markdown, no code fences, just raw JSON) with these keys:

{{
  "weather_by_day": [
    {{"date": "YYYY-MM-DD", "high_c": number, "low_c": number, "condition": "string", "rain_chance_pct": number, "recommendation": "string"}}
  ],
  "best_transport": {{
    "recommendation": "public_transit" or "car_rental" or "mixed",
    "reason": "string explaining why",
    "metro_available": boolean,
    "bus_system": boolean,
    "ride_sharing": boolean,
    "taxi_affordable": boolean,
    "daily_transit_pass_cost": "string like $5-10",
    "airport_to_city": "string - best way to get from airport to city center with cost"
  }},
  "safety": {{
    "overall_score": number 1-10,
    "crime_level": "low/moderate/high",
    "areas_to_avoid": ["list of specific neighborhoods or areas"],
    "safe_areas": ["list of safe tourist areas"],
    "scam_warnings": ["common tourist scams"],
    "emergency_number": "string",
    "tourist_police_available": boolean,
    "health_alerts": ["any current health concerns"],
    "tap_water_safe": boolean
  }},
  "local_events": [
    {{"date": "YYYY-MM-DD", "name": "event name", "type": "festival/market/concert/exhibition/sports", "description": "brief description", "cost": "free or price", "location": "specific location"}}
  ],
  "local_customs": {{
    "tipping": "string - tipping customs",
    "greeting": "string - how locals greet",
    "dress_code": "string - what to wear",
    "language": "string - primary language and English proficiency",
    "useful_phrases": ["list of 5 useful local phrases with translations"],
    "dining_etiquette": "string",
    "business_hours": "string - typical shop/restaurant hours"
  }},
  "must_see_attractions": [
    {{"name": "string", "type": "museum/landmark/park/market/neighborhood", "estimated_hours": number, "cost": "string", "best_time": "morning/afternoon/evening", "indoor_outdoor": "indoor/outdoor/both"}}
  ],
  "food_scene": {{
    "must_try_dishes": ["list of 5 specific local dishes"],
    "food_markets": ["list of famous food markets"],
    "restaurant_areas": ["neighborhoods known for dining"],
    "budget_meal_cost": "string like $5-10",
    "mid_range_meal_cost": "string like $15-30",
    "fine_dining_cost": "string like $50+",
    "street_food_safe": boolean
  }},
  "packing_essentials": ["list of 8-10 items specific to this destination and these dates"]
}}

Be SPECIFIC to {destination}. Use real place names, real neighborhoods, real dishes.
For weather, use your knowledge of {destination}'s typical climate for these dates.
For events, include any major festivals, markets, or events typical for this time of year.
Return ONLY valid JSON, no explanation."""

            response = model.invoke([HumanMessage(content=intel_prompt)])
            content = response.content.strip()
            # Strip markdown code fences if present
            if content.startswith('```'):
                content = content.split('\n', 1)[1] if '\n' in content else content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()

            intel = json.loads(content)
            enhanced['destination_intelligence'] = intel

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse destination intelligence JSON: {e}")
            enhanced['destination_intelligence'] = {}
        except Exception as e:
            logger.warning(f"Destination intelligence LLM call failed: {e}")
            enhanced['destination_intelligence'] = {}

    return enhanced


def _synthesize_narrative(*, result, origin, destination, departure_date,
                         return_date, passengers, budget, cuisine,
                         enhanced_data=None):
    """
    Use LLM to generate a smart, decision-driven day-by-day itinerary.
    The LLM REASONS about all agent data to make real choices and MUST
    include the specific hotel, restaurants, flights, and car rental
    details from the search agents in the day-by-day plan.
    """
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage

    rec = result.get('recommendation', {})
    enhanced = enhanced_data or {}
    intel = enhanced.get('destination_intelligence', {})

    # ── Build DETAILED search agent summaries ──

    # --- Flight details (rich) ---
    flight_summary = 'No flights found by search agent.'
    if rec.get('recommended_flight'):
        f = rec['recommended_flight']
        dur = f.get('duration')
        try:
            dur = int(dur) if dur else None
            dur_str = f"{dur // 60}h {dur % 60}m" if dur else 'N/A'
        except (TypeError, ValueError):
            dur_str = str(dur) if dur else 'N/A'
        flight_summary = (
            f"BOOKED FLIGHT:\n"
            f"  Airline: {f.get('airline', 'Unknown')}\n"
            f"  Flight Number: {f.get('flight_number', 'N/A')}\n"
            f"  Route: {f.get('departure_airport', origin)} ({f.get('departure_airport_code', origin)}) → "
            f"{f.get('arrival_airport', destination)} ({f.get('arrival_airport_code', destination)})\n"
            f"  Departure: {f.get('departure_time', 'N/A')}\n"
            f"  Arrival: {f.get('arrival_time', 'N/A')}\n"
            f"  Duration: {dur_str}\n"
            f"  Stops: {f.get('stops', 0)} {'(Nonstop)' if f.get('stops', 0) == 0 else ''}\n"
            f"  Class: {f.get('travel_class', 'Economy')}\n"
            f"  Price: ${f.get('price', 'N/A')} per person"
        )

    # --- Hotel details (rich) ---
    hotel_summary = 'No hotel found by search agent.'
    if rec.get('recommended_hotel'):
        h = rec['recommended_hotel']
        hotel_name = h.get('name') or h.get('hotel_name', 'Unknown Hotel')
        hotel_price = h.get('price') or h.get('price_per_night', 'N/A')
        hotel_stars = h.get('stars') or h.get('star_rating', 'N/A')
        hotel_address = h.get('address', 'Address not available')
        hotel_checkin = h.get('check_in_time', '3:00 PM')
        hotel_checkout = h.get('check_out_time', '11:00 AM')
        hotel_amenities = h.get('amenities', [])
        hotel_distance = h.get('distance_from_center', '')
        hotel_total = h.get('total_rate', '')
        hotel_summary = (
            f"BOOKED HOTEL:\n"
            f"  Name: {hotel_name}\n"
            f"  Stars: {hotel_stars}\n"
            f"  Address: {hotel_address}\n"
            f"  Price: ${hotel_price}/night"
            f"{f' (Total: ${hotel_total})' if hotel_total else ''}\n"
            f"  Check-in: {hotel_checkin}\n"
            f"  Check-out: {hotel_checkout}\n"
            f"  Distance from center: {hotel_distance}\n"
            f"  Key amenities: {', '.join(hotel_amenities[:8]) if hotel_amenities else 'N/A'}"
        )

    # --- Restaurant details (rich, all top 5) ---
    restaurant_lines = []
    top_restaurants = rec.get('top_5_restaurants', [])
    for idx, r in enumerate(top_restaurants[:5], 1):
        r_name = r.get('name', 'Unknown')
        r_cuisine = r.get('cuisine_type', '')
        r_cost = r.get('average_cost_per_person', 'N/A')
        r_rating = r.get('rating', 'N/A')
        r_address = r.get('address', '')
        r_hours = r.get('hours', '')
        r_price_range = r.get('price_range', '')
        r_phone = r.get('phone', '')
        restaurant_lines.append(
            f"  RESTAURANT #{idx}: {r_name}\n"
            f"    Cuisine: {r_cuisine}\n"
            f"    Cost: ${r_cost}/person ({r_price_range})\n"
            f"    Rating: {r_rating}/5\n"
            f"    Address: {r_address}\n"
            f"    Hours: {r_hours}\n"
            f"    Phone: {r_phone}"
        )
    restaurant_summary = '\n'.join(restaurant_lines) if restaurant_lines else 'No restaurant data from search agent.'

    # --- Car rental details (rich) ---
    car_summary = 'No car rentals found by search agent.'
    if rec.get('recommended_car'):
        c = rec['recommended_car']
        car_summary = (
            f"AVAILABLE CAR RENTAL:\n"
            f"  Company: {c.get('rental_company', 'Unknown')}\n"
            f"  Vehicle: {c.get('vehicle', c.get('car_type', 'N/A'))}\n"
            f"  Type: {c.get('car_type', 'N/A')}\n"
            f"  Price: ${c.get('price_per_day', 'N/A')}/day (Total: ${c.get('total_price', 'N/A')})\n"
            f"  Pickup Location: {c.get('pickup_location', 'N/A')}\n"
            f"  Pickup Date: {c.get('pickup_date', departure_date)}\n"
            f"  Dropoff Date: {c.get('dropoff_date', return_date or departure_date)}\n"
            f"  Features: {', '.join(c.get('features', [])[:5]) if c.get('features') else 'N/A'}\n"
            f"  Mileage: {c.get('mileage', 'N/A')}"
        )

    budget_summary = ''
    total_cost = rec.get('total_estimated_cost')
    if total_cost:
        budget_summary = f"Estimated Trip Cost from search agents: ${total_cost}"

    # ── Build intelligence sections from destination_intelligence ──
    weather_by_day = json.dumps(intel.get('weather_by_day', []), indent=2) if intel.get('weather_by_day') else 'Not available'
    transport_intel = json.dumps(intel.get('best_transport', {}), indent=2) if intel.get('best_transport') else 'Not available'
    safety_intel = json.dumps(intel.get('safety', {}), indent=2) if intel.get('safety') else 'Not available'
    events_intel = json.dumps(intel.get('local_events', []), indent=2) if intel.get('local_events') else 'None found'
    customs_intel = json.dumps(intel.get('local_customs', {}), indent=2) if intel.get('local_customs') else 'Not available'
    attractions_intel = json.dumps(intel.get('must_see_attractions', []), indent=2) if intel.get('must_see_attractions') else 'Not available'
    food_intel = json.dumps(intel.get('food_scene', {}), indent=2) if intel.get('food_scene') else 'Not available'
    packing_intel = json.dumps(intel.get('packing_essentials', []), indent=2) if intel.get('packing_essentials') else 'Not available'

    # --- Count trip days ---
    try:
        from datetime import datetime as _dt
        d1 = _dt.strptime(departure_date, '%Y-%m-%d')
        d2 = _dt.strptime(return_date or departure_date, '%Y-%m-%d')
        num_nights = max(1, (d2 - d1).days)
    except Exception:
        num_nights = 1

    # --- Determine hotel name for prompt injection ---
    hotel_name_for_prompt = ''
    if rec.get('recommended_hotel'):
        h = rec['recommended_hotel']
        hotel_name_for_prompt = h.get('name') or h.get('hotel_name', 'the hotel')

    prompt = f"""You are a SMART Agentic AI Travel Planner. You have data from 10+ specialized agents.
Your job is to create a COMPLETE, ACTIONABLE day-by-day travel plan that integrates ALL search results.

## !!!!! MANDATORY INTEGRATION RULES (YOU MUST FOLLOW THESE) !!!!!

### Rule 1: FLIGHT — Day 1 MUST start with the exact flight details
- Start Day 1 with: "[Departure time] - Depart on [Airline] Flight [Flight Number] from [Departure Airport] to [Arrival Airport]"
- Include arrival time and duration
- After arrival, include "Getting to your hotel" with transit/taxi directions from the arrival airport to {hotel_name_for_prompt or 'the hotel'}

### Rule 2: HOTEL — Reference BY NAME throughout the plan
- Day 1 MUST include: "Check in at {hotel_name_for_prompt}" with the hotel address and check-in time
- Each morning MUST start with: "Start from {hotel_name_for_prompt}" with brief transit directions to the first activity
- Last day MUST include: "Check out of {hotel_name_for_prompt}" with the check-out time
- When returning to the hotel mid-day, say: "Return to {hotel_name_for_prompt}"

### Rule 3: RESTAURANTS — Distribute ALL {len(top_restaurants)} recommended restaurants across meal slots BY NAME
- You have {len(top_restaurants)} restaurants from the search agent. You MUST use their EXACT names and addresses.
- Assign each restaurant to a specific meal on a specific day (e.g., "Lunch at [Restaurant Name], [address]")
- Include the cost per person and cuisine type
- For remaining meals, suggest local dishes from the Food Scene data
- NEVER use generic "find a local restaurant" — always name a specific place

### Rule 4: CAR RENTAL vs TRANSIT — Make a clear decision
- If transport analysis says public transit is good → DO NOT mention car rental. Plan metro/bus/taxi into directions.
- If car rental is recommended → Include pickup on Day 1 (after airport arrival) and dropoff on last day
- Include "Getting there:" directions for EVERY activity

### Rule 5: LAST DAY — Include hotel checkout and departure logistics
- Start with checking out of {hotel_name_for_prompt}
- If return flight data available, include getting to the airport and flight details
- Include luggage storage options if there's time before the flight

---

## SEARCH AGENT DATA (these are REAL bookings — use exact names/details):

### Flight Agent Result
{flight_summary}

### Hotel Agent Result
{hotel_summary}

### Restaurant Agent Results (USE ALL OF THESE BY NAME)
{restaurant_summary}

### Car Rental Agent Result
{car_summary}

### Budget
{budget_summary}
Planned budget: ${budget or 'flexible'}

---

## INTELLIGENCE AGENT DATA:

### Weather Forecast Per Day
{weather_by_day}

### Local Transportation Analysis
{transport_intel}

### Safety Intelligence
{safety_intel}

### Local Events During Travel Dates
{events_intel}

### Local Customs & Culture
{customs_intel}

### Must-See Attractions
{attractions_intel}

### Food Scene
{food_intel}

### Packing Essentials
{packing_intel}

---

## Trip: {origin} → {destination}
Dates: {departure_date} to {return_date or departure_date} ({num_nights} night{'s' if num_nights > 1 else ''})
Passengers: {passengers}
{f'Cuisine preference: {cuisine}' if cuisine else ''}

---

## OUTPUT FORMAT (follow exactly):

## Trip Overview
(2-3 sentences. Mention the hotel name and neighborhood.)

## Transportation Recommendation
(DECIDE: car rental vs public transit. Explain WHY. Include airport transfer method and cost, daily transit pass info.)

## Day 1: Arrival in {destination} ({departure_date})
**Weather: [condition, high/low temp]**

[Flight departure time] - Depart on [Airline] Flight [#] from [Airport] (~$[price])
[Flight arrival time] - Arrive at [Airport]
[Time] - Travel to {hotel_name_for_prompt or 'hotel'} [explain how: taxi/metro/bus with cost] (~$cost)
[Check-in time] - Check in at {hotel_name_for_prompt or 'hotel'}, [address] (~$[price]/night)
[Time] - [Afternoon activity in the hotel neighborhood] (~$cost)
  → Getting there: [directions from hotel]
[Time] - Dinner at [RESTAURANT #1 NAME from search results], [address] (~$cost/person)
  → Getting there: [directions from hotel]
**Day cost estimate: $X**

## Day 2: [Title] (next date)
**Weather: [condition, high/low temp]**

8:00 AM - Breakfast at {hotel_name_for_prompt or 'hotel'} or nearby café (~$cost)
9:30 AM - [Morning activity — choose indoor/outdoor based on weather] (~$cost)
  → Getting there: [directions from hotel]
12:30 PM - Lunch at [RESTAURANT #2 NAME from search results], [address] (~$cost/person)
  → Getting there: [directions]
...continue with afternoon and evening...
7:30 PM - Dinner at [RESTAURANT #3 NAME from search results], [address] (~$cost/person)
  → Getting there: [directions]
**Day cost estimate: $X**

(Continue for ALL {num_nights + 1} days, using remaining restaurants from the list)

## Day {num_nights + 1}: Departure ({return_date or departure_date})
**Weather: [condition]**

[Check-out time] - Check out of {hotel_name_for_prompt or 'hotel'}
[Time] - [Morning activity if time allows]
[Time] - Travel to airport [explain how with cost]
[Time] - Departure flight

## Local Events to Catch
(Events happening during the travel dates)

## Safety Tips
(Areas to avoid, scam warnings, emergency numbers)

## Packing List
(Weather-specific for these dates)

## Budget Summary
| Category | Cost |
|----------|------|
| Flights | $X |
| Hotel (${rec.get('recommended_hotel', {}).get('price') or rec.get('recommended_hotel', {}).get('price_per_night', 'N/A')}/night × {num_nights} nights) | $X |
| Food & Dining | $X |
| Transportation (local) | $X |
| Activities & Attractions | $X |
| **Total** | **$X** |
| Budget | ${budget or 'flexible'} |
| Remaining / Over | $X |

IMPORTANT REMINDERS:
- Use the EXACT hotel name "{hotel_name_for_prompt}" every time you reference the hotel
- Use the EXACT restaurant names from the search results for meals
- Include "Getting there:" transit directions for every activity
- Include specific times and costs for everything
- Make weather-driven activity choices (indoor on rainy days, outdoor on sunny)
- Avoid unsafe areas mentioned in the safety data"""

    model = ChatOpenAI(
        model=settings.AGENT_CONFIG.get('MODEL', 'gpt-4o-mini'),
        temperature=0.7,
        api_key=settings.OPENAI_API_KEY,
        request_timeout=120,
    )

    logger.info("Calling LLM for narrative generation (prompt length: %d chars)", len(prompt))
    try:
        response = model.invoke([HumanMessage(content=prompt)])
        logger.info("LLM narrative generated successfully (%d chars)", len(response.content))
        return response.content
    except Exception as exc:
        logger.error("LLM narrative call failed: %s", exc, exc_info=True)
        raise


@api_view(['POST'])
@permission_classes([AllowAny])
def plan_travel(request):
    """
    Main endpoint to run the multi-agent travel planning system.
    
    Request body:
    {
        "query": "I want to travel from Paris to Berlin",
        "origin": "CDG",
        "destination": "BER", 
        "departure_date": "2025-10-10",
        "return_date": "2025-10-15",
        "passengers": 2,
        "budget": 500.0
    }
    """
    try:
        # Get request data
        query = request.data.get('query', 'Plan my travel')
        origin = request.data.get('origin')
        destination = request.data.get('destination')
        departure_date = request.data.get('departure_date')
        return_date = request.data.get('return_date')
        passengers = request.data.get('passengers', 1)
        budget = request.data.get('budget')
        cuisine = request.data.get('cuisine')

        # Validate required fields
        if not all([origin, destination, departure_date]):
            return Response({
                'success': False,
                'error': 'origin, destination, and departure_date are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get the travel system
        from .multi_agent_system import get_travel_system
        travel_system = get_travel_system()

        # Run the multi-agent system
        result = travel_system.run(
            user_query=query,
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            passengers=passengers,
            budget=budget,
            cuisine=cuisine
        )

        # Gather data from ALL enhanced agents (weather, safety, visa, packing, local expert)
        enhanced_data = {}
        if result.get('success'):
            try:
                enhanced_data = _gather_enhanced_agent_data(
                    destination=destination,
                    origin=origin,
                    departure_date=departure_date,
                    return_date=return_date,
                    cuisine=cuisine,
                )
                result['enhanced_data'] = enhanced_data
            except Exception as e:
                logger.warning(f"Enhanced agent data gathering failed: {e}")

        # Generate LLM day-by-day narrative itinerary using ALL agent data
        if result.get('success') and settings.OPENAI_API_KEY:
            try:
                result['itinerary_text'] = _synthesize_narrative(
                    result=result,
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date,
                    passengers=passengers,
                    budget=budget,
                    cuisine=cuisine,
                    enhanced_data=enhanced_data,
                )
            except Exception as e:
                logger.error(f"LLM narrative generation failed: {e}", exc_info=True)
                # Provide a fallback plan so the user still sees something
                result['itinerary_text'] = (
                    f"## Trip Overview\n\n"
                    f"AI-planned trip from {origin} to {destination}, "
                    f"{departure_date} to {return_date or departure_date}.\n\n"
                    f"## Day 1: Arrival\n\n"
                    f"- Arrive in {destination}\n"
                    f"- Check in to hotel\n"
                    f"- Explore the area\n\n"
                    f"*Note: Detailed AI itinerary generation encountered an error. "
                    f"Please try again or check your search results below for "
                    f"flight, hotel, and restaurant recommendations.*"
                )

        # Create session record if user is authenticated
        if request.user.is_authenticated:
            try:
                session = AgentSession.objects.create(
                    user=request.user,
                    session_id=f"session_{uuid.uuid4().hex[:16]}",
                    user_intent=query,
                    context_data={
                        'origin': origin,
                        'destination': destination,
                        'departure_date': departure_date,
                        'return_date': return_date,
                        'passengers': passengers,
                        'budget': budget,
                        'cuisine': cuisine
                    },
                    status='completed' if result.get('success') else 'failed'
                )
                result['session_id'] = session.session_id
            except Exception as e:
                # Don't fail the request if session creation fails
                print(f"Session creation error: {e}")

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat(request):
    """
    Chat endpoint for conversational travel planning.
    
    Request body:
    {
        "message": "I need a cheap flight to Berlin next month",
        "session_id": "session_abc123" (optional, for continuing a conversation)
    }
    """
    try:
        message = request.data.get('message')
        session_id = request.data.get('session_id')

        if not message:
            return Response({
                'success': False,
                'error': 'message is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # TODO: Implement NLP to extract travel parameters from message
        # For now, return a helpful response
        return Response({
            'success': True,
            'message': 'Chat interface coming soon! Please use the search form for now.',
            'suggestion': 'Use the /api/agents/plan endpoint with specific origin, destination, and dates.'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
