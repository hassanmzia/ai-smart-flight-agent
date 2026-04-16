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

from .models import AgentSession, AgentExecution, AgentLog, RAGDocument
from .serializers import (
    AgentSessionSerializer,
    AgentSessionListSerializer,
    AgentSessionCreateSerializer,
    AgentExecutionSerializer,
    AgentExecutionListSerializer,
    AgentExecutionCreateSerializer,
    AgentLogSerializer,
    RAGDocumentSerializer,
    RAGDocumentUploadSerializer,
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
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY not in ('your_openai_api_key_here', ''):
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage

            model = ChatOpenAI(
                model=settings.AGENT_CONFIG.get('MODEL', 'gpt-4o-mini'),
                temperature=0.3,
                api_key=settings.OPENAI_API_KEY,
                request_timeout=60,
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
    {{"date": "YYYY-MM-DD", "name": "event name", "type": "festival/market/concert/exhibition/sports/religious", "description": "brief description", "cost": "free or price", "location": "specific location"}}
  ],
  IMPORTANT: Include local events, festivals, weekly markets, and cultural happenings that occur during the travel dates ({departure_date} to {return_date or departure_date}). Include recurring events like weekend markets, weekly bazaars, etc.
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
    {{"name": "string (REAL place name)", "type": "museum/landmark/park/market/neighborhood/temple/beach/fort/palace", "description": "1-2 sentence description", "estimated_hours": number, "cost": "string", "best_time": "morning/afternoon/evening", "indoor_outdoor": "indoor/outdoor/both"}}
  ],
  IMPORTANT: Include at least 8-10 must_see_attractions with REAL, SPECIFIC names of famous landmarks, temples, museums, parks, markets, and neighborhoods in {destination}. These are the most popular tourist attractions that every visitor should know about.
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

            logger.info(f"Calling LLM for destination intelligence (key starts with: {settings.OPENAI_API_KEY[:10]}...)")
            response = model.invoke([HumanMessage(content=intel_prompt)])
            content = response.content.strip()
            logger.info(f"LLM destination intelligence response received ({len(content)} chars)")

            # Strip markdown code fences if present (handles ```json ... ``` etc)
            import re
            fence_match = re.search(r'```(?:json)?\s*\n?(.*?)```', content, re.DOTALL)
            if fence_match:
                content = fence_match.group(1).strip()
            elif content.startswith('```'):
                content = content.split('\n', 1)[1] if '\n' in content else content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()

            intel = json.loads(content)
            enhanced['destination_intelligence'] = intel
            logger.info(f"Destination intelligence parsed successfully with keys: {list(intel.keys())}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse destination intelligence JSON: {e}")
            logger.error(f"Raw LLM response was: {content[:1000] if content else 'empty'}")
            enhanced['destination_intelligence'] = {}
            enhanced['_intel_error'] = f"JSON parse error: {str(e)}"
        except Exception as e:
            logger.error(f"Destination intelligence LLM call failed: {type(e).__name__}: {e}", exc_info=True)
            enhanced['destination_intelligence'] = {}
            enhanced['_intel_error'] = f"{type(e).__name__}: {str(e)}"

    # Always provide basic destination intelligence even if LLM is unavailable
    if not enhanced.get('destination_intelligence'):
        enhanced['destination_intelligence'] = _build_static_intelligence(
            destination=destination,
            origin=origin,
            departure_date=departure_date,
            return_date=return_date,
        )

    return enhanced


def _build_static_intelligence(*, destination, origin, departure_date, return_date):
    """Build basic destination intelligence without LLM, using available data."""
    from datetime import datetime, timedelta

    intel = {}

    # Generate weather_by_day stub from dates
    try:
        start = datetime.strptime(departure_date, '%Y-%m-%d')
        end = datetime.strptime(return_date, '%Y-%m-%d') if return_date else start + timedelta(days=3)
        days = (end - start).days or 1
        intel['weather_by_day'] = [
            {
                "date": (start + timedelta(days=i)).strftime('%Y-%m-%d'),
                "high_c": "N/A",
                "low_c": "N/A",
                "condition": "Check local forecast",
                "rain_chance_pct": 0,
                "recommendation": f"Check weather forecast for {destination} closer to your travel date",
            }
            for i in range(min(days, 7))
        ]
    except Exception:
        intel['weather_by_day'] = []

    # Safety stub
    intel['safety'] = {
        "overall_score": "N/A",
        "crime_level": "Check local advisories",
        "areas_to_avoid": [],
        "safe_areas": [f"Major tourist areas in {destination}"],
        "scam_warnings": ["Be cautious with unlicensed taxis", "Verify prices before purchasing"],
        "emergency_number": "Check local emergency number",
        "tourist_police_available": False,
        "health_alerts": [],
        "tap_water_safe": False,
    }

    # Transport stub
    intel['best_transport'] = {
        "recommendation": "mixed",
        "reason": f"Research local transport options in {destination} before your trip",
        "metro_available": False,
        "bus_system": True,
        "ride_sharing": True,
        "taxi_affordable": True,
        "daily_transit_pass_cost": "Check locally",
        "airport_to_city": f"Check airport transfer options for {destination}",
    }

    # Local customs stub
    intel['local_customs'] = {
        "tipping": "Check local tipping customs",
        "language": "Research the local language before traveling",
        "dress_code": "Dress modestly when visiting religious sites",
        "dining_etiquette": "Observe local customs at restaurants",
        "useful_phrases": [
            "Hello / Thank you / Please / Excuse me / Where is...?",
        ],
    }

    # Food scene stub
    intel['food_scene'] = {
        "must_try_dishes": [f"Research local cuisine of {destination}"],
        "food_markets": [],
        "restaurant_areas": [],
        "budget_meal_cost": "Varies",
        "mid_range_meal_cost": "Varies",
        "fine_dining_cost": "Varies",
        "street_food_safe": True,
    }

    # Packing
    intel['packing_essentials'] = [
        "Passport and travel documents",
        "Adapter plug for local outlets",
        "Comfortable walking shoes",
        "Sunscreen and sunglasses",
        "Light layers for variable weather",
        "Copies of important documents",
        "Basic first-aid kit",
        "Reusable water bottle",
    ]

    # Must-see attractions (generic but prompts LLM to fill in real ones)
    intel['must_see_attractions'] = [
        {"name": f"Top landmark in {destination}", "type": "landmark", "estimated_hours": 2, "cost": "Check locally", "best_time": "morning", "indoor_outdoor": "outdoor"},
        {"name": f"Main museum in {destination}", "type": "museum", "estimated_hours": 2, "cost": "Check locally", "best_time": "afternoon", "indoor_outdoor": "indoor"},
        {"name": f"Popular market in {destination}", "type": "market", "estimated_hours": 1.5, "cost": "Free entry", "best_time": "morning", "indoor_outdoor": "both"},
        {"name": f"Historic district of {destination}", "type": "neighborhood", "estimated_hours": 3, "cost": "Free", "best_time": "afternoon", "indoor_outdoor": "outdoor"},
        {"name": f"Scenic viewpoint or park in {destination}", "type": "park", "estimated_hours": 1.5, "cost": "Free", "best_time": "evening", "indoor_outdoor": "outdoor"},
    ]

    # Local events stub
    intel['local_events'] = []

    return intel


def _synthesize_narrative(*, result, origin, destination, departure_date,
                         return_date, passengers, budget, cuisine,
                         enhanced_data=None, interests=None, travel_style=None,
                         user_context=None):
    """
    Use LLM to generate a smart, decision-driven day-by-day itinerary.
    The LLM REASONS about all agent data to make real choices and MUST
    include the specific hotel, restaurants, flights, and car rental
    details from the search agents in the day-by-day plan.

    If ``user_context`` (from build_user_planning_context) is provided,
    a Traveler Profile section is appended to the prompt so the LLM
    personalizes dining, pace, mobility, faith, and activity choices.
    """
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage
    from .personalization_service import format_user_context_for_prompt

    rec = result.get('recommendation', {})
    enhanced = enhanced_data or {}
    intel = enhanced.get('destination_intelligence', {})

    # ── Build DETAILED search agent summaries ──

    # --- Flight details (rich) ---
    flight_data = result.get('flights', {}) if isinstance(result.get('flights'), dict) else {}
    hub_route = flight_data.get('hub_route', False)
    transit_notes = flight_data.get('transit_notes', [])
    hub_destination_code = flight_data.get('hub_destination', '')
    original_destination_code = flight_data.get('original_destination', '')
    hub_origin_code = flight_data.get('hub_origin', '')
    original_origin_code = flight_data.get('original_origin', '')

    flight_summary = 'No flights found by search agent.'
    if rec.get('recommended_flight'):
        f = rec['recommended_flight']
        dur = f.get('duration')
        try:
            dur = int(dur) if dur else None
            dur_str = f"{dur // 60}h {dur % 60}m" if dur else 'N/A'
        except (TypeError, ValueError):
            dur_str = str(dur) if dur else 'N/A'
        flight_url = f.get('bookingUrl') or f.get('booking_url') or f.get('link') or (
            f"https://www.google.com/travel/flights/booking?token={f['booking_token']}"
            if f.get('booking_token') else ''
        )
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
            f"{f'{chr(10)}  Booking URL: {flight_url}' if flight_url else ''}"
        )

    # Initialize hub city names (used in f-strings in prompt template)
    hub_dest_city = hub_destination_code or ''
    orig_dest_city = original_destination_code or ''

    # Add hub routing info if flights go through a hub airport
    if hub_route:
        from utils.airport_resolver import AIRPORT_TO_CITY
        hub_dest_city = AIRPORT_TO_CITY.get(hub_destination_code, hub_destination_code)
        orig_dest_city = AIRPORT_TO_CITY.get(original_destination_code, original_destination_code)
        origin_city = AIRPORT_TO_CITY.get(original_origin_code or origin, origin)
        # Use the user's actual destination name (e.g. "Khulna") when it differs from airport city (e.g. "Jessore")
        user_dest = destination  # This is the human-readable label like "Khulna"
        dest_display = f"{user_dest} (via {orig_dest_city}/{original_destination_code} airport)" if user_dest.lower() != orig_dest_city.lower() else f"{orig_dest_city} ({original_destination_code})"

        hub_info = "\n\nIMPORTANT - HUB ROUTING (CONNECTING FLIGHTS REQUIRED):\n"
        hub_info += f"  There are NO direct international flights to {dest_display}.\n"
        hub_info += f"  The nearest international airport is {hub_dest_city} ({hub_destination_code}).\n"
        if user_dest.lower() != orig_dest_city.lower():
            hub_info += f"  NOTE: The traveler's final destination is {user_dest}, which is served by {orig_dest_city} Airport ({original_destination_code}). {user_dest} is near {orig_dest_city}.\n"
        hub_info += "\n"

        hub_info += f"  OUTBOUND JOURNEY ({origin_city} → {user_dest}):\n"
        hub_info += f"    Leg 1: International flight {origin_city} ({original_origin_code or origin}) → {hub_dest_city} ({hub_destination_code}) [this is the flight above]\n"
        hub_info += f"    Leg 2: Domestic flight or ground transport {hub_dest_city} ({hub_destination_code}) → {orig_dest_city} ({original_destination_code}) → {user_dest} [~1 hour domestic flight or ~4-6 hour drive]\n\n"

        hub_info += f"  RETURN JOURNEY ({user_dest} → {origin_city}):\n"
        hub_info += f"    Leg 1: Ground transport from {user_dest} → {orig_dest_city} ({original_destination_code}) → {hub_dest_city} ({hub_destination_code}) [traveler MUST reach the hub airport]\n"
        hub_info += f"    Leg 2: International flight {hub_dest_city} ({hub_destination_code}) → {origin_city} ({original_origin_code or origin}) [the return flight]\n\n"

        for note in transit_notes:
            hub_info += f"  → {note}\n"

        hub_info += "\n  ITINERARY INSTRUCTIONS:\n"
        hub_info += f"  - Day 1: The traveler lands at {hub_dest_city} ({hub_destination_code}), NOT at {user_dest}. You MUST show: landing at {hub_dest_city}, then the connecting journey ({hub_dest_city} → {orig_dest_city} → {user_dest}). Plan activities ONLY after arriving in {user_dest}.\n"
        hub_info += f"  - Last Day: The traveler must leave {user_dest} early, travel to {orig_dest_city} ({original_destination_code}), then to {hub_dest_city} ({hub_destination_code}) for the international return flight. Account for ~3-4 hours for this transfer plus airport check-in."
        flight_summary += hub_info
    elif not rec.get('recommended_flight'):
        # No flights found at all — give the LLM context about the route
        from utils.airport_resolver import get_hub_airport, AIRPORT_TO_CITY
        dest_hub = get_hub_airport(destination) if destination else None
        if dest_hub:
            hub_city = AIRPORT_TO_CITY.get(dest_hub, dest_hub)
            dest_city = AIRPORT_TO_CITY.get(destination, destination)
            flight_summary += (
                f"\n\nNOTE: No flights were found. The nearest international airport to {dest_city} ({destination}) "
                f"is {hub_city} ({dest_hub}). Suggest the traveler book a flight to {hub_city} and then take "
                f"domestic transport to {dest_city}."
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
        hotel_url = h.get('booking_url') or h.get('link') or h.get('website_url') or ''
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
            f"{f'{chr(10)}  Booking URL: {hotel_url}' if hotel_url else ''}"
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
        r_url = (
            r.get('website')
            or r.get('website_url')
            or r.get('booking_url')
            or r.get('url')
            or r.get('link')
            or ''
        )
        restaurant_lines.append(
            f"  RESTAURANT #{idx}: {r_name}\n"
            f"    Cuisine: {r_cuisine}\n"
            f"    Cost: ${r_cost}/person ({r_price_range})\n"
            f"    Rating: {r_rating}/5\n"
            f"    Address: {r_address}\n"
            f"    Hours: {r_hours}\n"
            f"    Phone: {r_phone}"
            f"{f'{chr(10)}    Website/Booking URL: {r_url}' if r_url else ''}"
        )
    restaurant_summary = '\n'.join(restaurant_lines) if restaurant_lines else 'No restaurant data from search agent.'

    # --- Vacation rental details (rich) ---
    rental_summary = 'No vacation rental found by search agent.'
    if rec.get('recommended_rental'):
        vr = rec['recommended_rental']
        vr_name = vr.get('name') or vr.get('hotel_name', 'Unknown Rental')
        vr_price = vr.get('price') or vr.get('price_per_night', 'N/A')
        vr_type = vr.get('type', 'Vacation Rental')
        vr_bedrooms = vr.get('bedrooms', 'N/A')
        vr_bathrooms = vr.get('bathrooms', 'N/A')
        vr_max_guests = vr.get('max_guests', 'N/A')
        vr_address = vr.get('address', '')
        vr_amenities = vr.get('amenities', [])
        vr_rating = vr.get('star_rating') or vr.get('guest_rating', 'N/A')
        rental_summary = (
            f"BOOKED VACATION RENTAL (Airbnb/VRBO):\n"
            f"  Property Name: {vr_name}\n"
            f"  Type: {vr_type}\n"
            f"  Bedrooms: {vr_bedrooms}\n"
            f"  Bathrooms: {vr_bathrooms}\n"
            f"  Max Guests: {vr_max_guests}\n"
            f"  Price: ${vr_price}/night\n"
            f"  Rating: {vr_rating}\n"
            f"  Location: {vr_address}\n"
            f"  Key amenities: {', '.join(vr_amenities[:8]) if vr_amenities else 'N/A'}"
        )
    elif rec.get('top_rentals'):
        # Even if no single "recommended", list the top option
        vr = rec['top_rentals'][0]
        vr_name = vr.get('name') or vr.get('hotel_name', 'Unknown Rental')
        vr_price = vr.get('price') or vr.get('price_per_night', 'N/A')
        vr_type = vr.get('type', 'Vacation Rental')
        rental_summary = (
            f"AVAILABLE VACATION RENTAL:\n"
            f"  Property Name: {vr_name}\n"
            f"  Type: {vr_type}\n"
            f"  Price: ${vr_price}/night"
        )

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

    # --- Count trip days (needed for hotel cost calculation) ---
    try:
        from datetime import datetime as _dt
        d1 = _dt.strptime(departure_date, '%Y-%m-%d')
        d2 = _dt.strptime(return_date or departure_date, '%Y-%m-%d')
        num_nights = max(1, (d2 - d1).days)
    except Exception:
        num_nights = 1

    budget_summary = ''
    total_cost = rec.get('total_estimated_cost')

    # Pre-compute actual costs from search agent data for the LLM
    num_passengers = int(passengers or 1)
    flight_price_pp = 0  # per person
    flight_price = 0     # total for all passengers
    hotel_price_per_night = 0
    hotel_total = 0
    car_total = 0
    connecting_flight_cost = 0
    try:
        rf = rec.get('recommended_flight') or {}
        flight_price_pp = float(rf.get('price', 0) or 0)
        flight_price = flight_price_pp * num_passengers
    except (ValueError, TypeError, AttributeError):
        flight_price = 0
        flight_price_pp = 0

    # Estimate connecting domestic flight cost for hub routes
    if hub_route and hub_destination_code and original_destination_code:
        # Domestic flights in most countries cost $30-80 per person
        connecting_flight_cost = 50 * num_passengers  # ~$50/person each way × 2 legs (there + back)
        connecting_flight_cost *= 2  # round trip
    hotel_price_estimated = False
    rental_price_per_night = 0
    rental_total = 0
    using_rental_as_accommodation = False

    # Check if a vacation rental is available (preferred for groups of 4+)
    try:
        rr = rec.get('recommended_rental') or (rec.get('top_rentals', [None])[0] if rec.get('top_rentals') else None) or {}
        rental_price_per_night = float(rr.get('price') or rr.get('price_per_night', 0) or 0)
        if rental_price_per_night > 0:
            rental_total = rental_price_per_night * num_nights
            using_rental_as_accommodation = True
    except (ValueError, TypeError, AttributeError):
        rental_total = 0

    try:
        rh = rec.get('recommended_hotel') or {}
        hotel_price_per_night = float(rh.get('price') or rh.get('price_per_night', 0) or 0)
        # If price is still 0, try total_rate divided by nights
        if hotel_price_per_night <= 0:
            total_rate = float(rh.get('total_rate', 0) or 0)
            if total_rate > 0 and num_nights > 0:
                hotel_price_per_night = total_rate / num_nights
        # If still 0, use the estimated_price from the evaluator
        if hotel_price_per_night <= 0:
            estimated = float(rh.get('estimated_price', 0) or 0)
            if estimated > 0:
                hotel_price_per_night = estimated
                hotel_price_estimated = True
        # Last resort: estimate from star rating
        if hotel_price_per_night <= 0:
            star_rating = float(rh.get('star_rating') or rh.get('stars') or rh.get('overall_rating', 0) or 0)
            star_estimates = {5: 180, 4: 100, 3: 60, 2: 40, 1: 25}
            hotel_price_per_night = star_estimates.get(round(star_rating) if star_rating > 0 else 3, 60)
            hotel_price_estimated = True
        # Account for multiple rooms if more than 2 travelers
        num_rooms = -(-num_passengers // 2) if num_passengers > 2 else 1  # ceiling division
        hotel_total = hotel_price_per_night * num_nights * num_rooms
    except (ValueError, TypeError, AttributeError):
        hotel_total = 0
        num_rooms = 1

    # Use rental cost as accommodation cost when rental is available (better value for groups)
    if using_rental_as_accommodation:
        accommodation_total = rental_total
    else:
        accommodation_total = hotel_total
    try:
        rc = rec.get('recommended_car') or {}
        car_total = float(rc.get('total_price', 0) or 0)
    except (ValueError, TypeError, AttributeError):
        car_total = 0

    known_costs_total = flight_price + accommodation_total + car_total + connecting_flight_cost
    budget_display = f"${budget}" if budget else "flexible (no limit set)"
    budget_remaining_instruction = ""
    if budget:
        try:
            b = float(budget)
            if known_costs_total > 0:
                budget_remaining_instruction = f"Known costs so far: ${known_costs_total:.0f}. Remaining for food/activities/transport: ${max(0, b - known_costs_total):.0f}."
        except (ValueError, TypeError):
            pass

    hotel_price_note = " (estimated — exact pricing unavailable)" if hotel_price_estimated else ""
    hotel_rooms_note = f" × {num_rooms} rooms" if num_rooms > 1 else ""
    connecting_note = f"\nConnecting domestic flights (hub route, round trip, {num_passengers} passengers): ~${connecting_flight_cost:.0f}" if connecting_flight_cost > 0 else ""

    # Build accommodation line (rental or hotel)
    if using_rental_as_accommodation:
        accom_line = f"Vacation rental: ${rental_price_per_night:.0f}/night × {num_nights} nights = ${rental_total:.0f} (entire property — no per-room cost)"
        if hotel_total > 0:
            accom_line += f"\n(Hotel alternative: ${hotel_price_per_night:.0f}/night{hotel_rooms_note} = ${hotel_total:.0f}{hotel_price_note})"
    else:
        accom_line = f"Hotel cost: ${hotel_price_per_night:.0f}/night × {num_nights} nights{hotel_rooms_note} = ${hotel_total:.0f}{hotel_price_note}"

    budget_summary = (
        f"NUMBER OF TRAVELERS: {num_passengers}\n"
        f"International flights: ${flight_price_pp:.0f}/person × {num_passengers} passengers = ${flight_price:.0f}\n"
        f"{accom_line}\n"
        f"Car rental: ${car_total:.0f}\n"
        f"{connecting_note}\n"
        f"Customer budget: {budget_display}\n"
        f"{budget_remaining_instruction}\n"
        f"IMPORTANT: You MUST multiply per-person costs (food, activities, transport) by {num_passengers} travelers.\n"
        f"IMPORTANT: You MUST calculate real dollar amounts for Food & Dining, Transportation, "
        f"and Activities in the Budget Summary table — estimate from restaurant prices, transit costs, "
        f"and activity costs mentioned in the plan. Never leave $X as placeholder."
    )

    # ── Build intelligence sections from destination_intelligence ──
    weather_by_day = json.dumps(intel.get('weather_by_day', []), indent=2) if intel.get('weather_by_day') else 'Not available'
    transport_intel = json.dumps(intel.get('best_transport', {}), indent=2) if intel.get('best_transport') else 'Not available'
    safety_intel = json.dumps(intel.get('safety', {}), indent=2) if intel.get('safety') else 'Not available'
    events_intel = json.dumps(intel.get('local_events', []), indent=2) if intel.get('local_events') else 'None found'
    customs_intel = json.dumps(intel.get('local_customs', {}), indent=2) if intel.get('local_customs') else 'Not available'
    attractions_intel = json.dumps(intel.get('must_see_attractions', []), indent=2) if intel.get('must_see_attractions') else 'Not available'
    food_intel = json.dumps(intel.get('food_scene', {}), indent=2) if intel.get('food_scene') else 'Not available'
    packing_intel = json.dumps(intel.get('packing_essentials', []), indent=2) if intel.get('packing_essentials') else 'Not available'

    # --- Determine hotel/rental name and checkout time for prompt ---
    hotel_name_for_prompt = ''
    rental_name_for_prompt = ''
    hotel_checkout = '11:00 AM'
    if rec.get('recommended_hotel'):
        h = rec['recommended_hotel']
        hotel_name_for_prompt = h.get('name') or h.get('hotel_name', 'the hotel')
        hotel_checkout = h.get('check_out_time', '11:00 AM') or '11:00 AM'
    if rec.get('recommended_rental'):
        vr = rec['recommended_rental']
        rental_name_for_prompt = vr.get('name') or vr.get('hotel_name', 'the vacation rental')
    elif rec.get('top_rentals'):
        rental_name_for_prompt = rec['top_rentals'][0].get('name') or rec['top_rentals'][0].get('hotel_name', '')
    # For groups with a rental, prefer the rental as the accommodation in the itinerary
    accommodation_name_for_prompt = rental_name_for_prompt or hotel_name_for_prompt or 'the accommodation'

    # The personalization block — put it FIRST so its binding constraints shape
    # every subsequent choice the model makes (restaurant picks, activity mix,
    # prayer breaks, phrase-of-the-day). Passive mentions get ignored; leading
    # with it, then re-referencing it in WRITING RULES, actually changes output.
    personalization_block = format_user_context_for_prompt(user_context)

    prompt = f"""You are an expert Travel Planner AI creating a polished, ready-to-follow travel itinerary for a public travel website.
Write in a warm, professional, and conversational tone — like a knowledgeable travel advisor writing for a real person.
Your output will be displayed directly to travelers, so make it clear, detailed, and genuinely useful.
{personalization_block}
## YOUR DATA SOURCES (from 10+ specialized AI agents):

### Flight Details
{flight_summary}

### Hotel Details
{hotel_summary}

### Vacation Rental Details
{rental_summary}

### Recommended Restaurants (use these EXACT names)
{restaurant_summary}

### Car Rental Options
{car_summary}

### Budget Analysis
{budget_summary}

### Trip-Specific Preferences (in addition to the Traveler Profile above)
{f'Interests: {interests}' if interests else 'No specific interests.'}
{f'Travel style: {travel_style}' if travel_style else ''}
{f'Cuisine preference: {cuisine}' if cuisine else ''}

### Weather Forecast
{weather_by_day}

### Local Transportation
{transport_intel}

### Safety Information
{safety_intel}

### Local Events (schedule these into the right days!)
{events_intel}

### Local Customs & Culture
{customs_intel}

### Must-See Attractions (USE THESE in the day-by-day plan — spread across all days)
{attractions_intel}
If the above attractions data is limited, use your knowledge to add the top 8-10 most famous tourist attractions, landmarks, temples, historical sites, and popular local markets in {destination}. Every traveler should visit these.

### Food Scene
{food_intel}

### Packing Recommendations
{packing_intel}

---

## TRIP DETAILS
- Route: {origin} → {destination}
- Dates: {departure_date} to {return_date or departure_date} ({num_nights} night{'s' if num_nights > 1 else ''})
- Travelers: {passengers}

---

## WRITING RULES

1. **FLIGHT TIMES DRIVE THE SCHEDULE**: Day 1 starts with the actual departure time from the flight data. Plan afternoon activities ONLY after the flight lands and the traveler reaches the hotel. On the departure day, plan activities BEFORE the flight and ensure enough time to get to the airport.

2. **USE REAL NAMES**: Always use the exact accommodation name "{accommodation_name_for_prompt}" and the exact restaurant names from search results. Never say "a local restaurant" — name specific places.{f' For this group of {num_passengers} travelers, a vacation rental ("{rental_name_for_prompt}") has been booked — reference this property by name when mentioning check-in, check-out, and the home base. Mention it is a vacation rental/Airbnb-style property with kitchen, living space, etc.' if rental_name_for_prompt else ''}

3. **REALISTIC TIME FLOW**: Every activity must have a specific time (e.g., "9:30 AM"). Times should flow logically — account for travel between locations (15-45 min), meal duration (45-90 min), and activity duration. Don't schedule 5 attractions in 3 hours.

4. **EVERY COST IS A REAL NUMBER**: Write (~$15) or (~$45/person) for every item. Never use placeholders like "$X" or "[cost]". Estimate realistically based on the destination.

5. **WEATHER-SMART**: Check the weather data for each day. Suggest indoor activities on rainy days, outdoor on sunny days. Mention the weather naturally ("It's a sunny 28°C day, perfect for...").

6. **PRACTICAL DIRECTIONS**: For each activity, briefly mention how to get there from the previous location ("a 10-minute walk" or "take the metro Line 2, about 20 minutes").

7. **DEPARTURE DAY IS COMPLETE**: The last day must include check-out, any morning activities, travel to airport with timing, and the return flight. Never end abruptly.

8. **MUST INCLUDE LOCAL ATTRACTIONS**: Every day MUST include at least 2-3 specific tourist attractions, landmarks, temples, museums, parks, or markets from the Must-See Attractions list. Use their REAL names. Never say "visit local attractions" — name the specific place, describe what makes it worth visiting, and include admission cost. Spread the top attractions across different days.

9. **INCLUDE LOCAL EVENTS**: If there are any local events, festivals, markets, or cultural happenings during the travel dates, schedule them into the appropriate day. Weekly markets and recurring events should be included on the right day of the week.

{'10. **TAILOR TO INTERESTS**: The traveler enjoys ' + interests + '. Prioritize activities that match these interests.' if interests else ''}

{"11. **HONOR THE TRAVELER PROFILE (BINDING)**: The Traveler Profile section at the top lists dietary, faith, mobility, language, pace, and allergy constraints. Every single restaurant, activity, transport note, and venue you write MUST be consistent with those constraints. If the profile says halal, name halal restaurants. If it says wheelchair-accessible, every major stop must be accessible and you must say so inline. If it says prayer-reminders, leave gaps for prayer and add a 🕌 line at the right times. If the traveler's languages do not include the local language, add a **Phrase of the Day** line under each day header with a useful local phrase and pronunciation. If the profile says low-walking, cap each day's walking and include a walking-km note. Never ignore these — the plan must visibly demonstrate the profile was honored." if personalization_block else ""}

12. **SAFETY-AWARE SELECTION**: Cross-reference every hotel, restaurant, and neighborhood suggestion against the Safety Information above. If a place falls inside `safety.areas_to_avoid`, SKIP it and pick a safer alternative. Surface 1-2 of the top `safety.scam_warnings` as bullets in the "Good to Know" section. If `safety.tap_water_safe` is false, add "Refillable water bottle + water purification tablets or bottled water budget" to the Packing Checklist and mention it briefly in "Good to Know".

13. **MUST-TRY DISHES**: Using `food_scene.must_try_dishes`, weave 2-3 of those SPECIFIC named dishes into dinner/lunch stops across different days — name the dish AND a restaurant where it's known (e.g., "Try **pad kra pao** at ..."). Don't list dishes in isolation; schedule them.

14. **USE LOCAL PHRASES AS SOURCE**: When you produce a "Phrase of the Day" line (per Traveler Profile), source it from `local_customs.useful_phrases` if available — pick a different phrase each day (greeting → ordering → asking for help → thank-you). If `useful_phrases` is empty, use your knowledge of the destination's primary language.

15. **LOCAL CUSTOMS DRIVE RECOMMENDATIONS**: If `local_customs.dress_code` notes a specific rule (e.g., "cover shoulders in temples"), add it to "Good to Know" AND remind the traveler to dress appropriately on days that include religious/faith sites. Reflect `local_customs.dining_etiquette` in the tone of restaurant notes (e.g., "remove shoes at entry", "tipping ~10% is expected").

16. **TRANSPORT DECISION IS BINDING**: The "Getting Around" section MUST adopt whatever `best_transport.recommendation` says (public_transit / car_rental / mixed). Do NOT contradict it elsewhere in the plan — if it says public_transit, every transport line should be metro/bus/walk/rideshare, not rentals.

17. **EMBED BOOKING / REFERENCE URLS AS MARKDOWN LINKS (IMPORTANT)**: Whenever a place you reference has a known URL (flight "Booking URL", hotel "Booking URL", restaurant "Website/Booking URL", vacation rental, car rental, a ticket/event link, an official site, etc.), write the place name as a clickable markdown link: `[Place Name](https://url...)`. Use the EXACT URL from the data above — do NOT invent URLs. For attractions, museums, tourist sites, shopping markets, and local events where the data sources above don't include a URL, you MAY fall back to a Google search link of the form `https://www.google.com/search?q=<URL-encoded place name + destination>` so the traveler can still click through. Every timed line in the day-by-day plan SHOULD have at least one markdown link to the place being visited, booked, or eaten at. Do not emit bare "https://..." strings on their own — always wrap them with the place name.

---

## OUTPUT FORMAT (follow this structure exactly):

## Trip Overview
Write 2-3 welcoming sentences about this trip. Mention the hotel name and its neighborhood, the vibe of the destination, and what makes this trip special.

## Getting Around
Recommend car rental OR public transit (pick one based on the transport data). Explain why, mention costs, and describe how to get from the airport to the hotel.

## Day 1: Arrival in {destination}
**{departure_date} · [Weather summary from data]**

{f"[Use the actual flight departure time] - Depart on [Airline] [Flight #] from [Origin Airport] (~${flight_price:.0f})" }
{f"[Use the actual flight arrival time] - Land at {hub_dest_city} ({hub_destination_code}) after a [duration] flight" if hub_route else "[Use the actual flight arrival time] - Land at [Destination Airport] after a [duration] flight"}
{f"[Time] - CONNECTING JOURNEY: Take domestic flight or bus/car from {hub_dest_city} ({hub_destination_code}) to {destination} (~$cost, ~X hours)" if hub_route else ""}
[Time after arrival] - Head to {hotel_name_for_prompt or 'your hotel'} by [taxi/metro/bus] (~$cost)
[Time] - Check in at **{hotel_name_for_prompt or 'your hotel'}**, [address] (~${hotel_price_per_night:.0f}/night)
[Afternoon/Evening time] - [First activity — something easy near the hotel to start the trip] (~$cost)
[Evening time] - Dinner at **[Restaurant Name from search data]**, [cuisine type], [address] (~$cost/person)
**Day total: ~$[real sum]**

## Day 2: [Descriptive Title]
**[Next date] · [Weather]**
{'**🗣️ Phrase of the Day:** [1 useful local-language phrase + pronunciation + meaning]' if personalization_block and user_context and user_context.get('profile', {}).get('languages_spoken') else ''}
{'**🕌 Faith note:** [1 line — nearby worship place, halal/kosher option, or etiquette tip]' if personalization_block and user_context and user_context.get('profile', {}).get('faith') and user_context['profile']['faith'] != 'none' else ''}

8:00 AM - Breakfast at {hotel_name_for_prompt or 'the hotel'} or a nearby café (~$cost)
[Continue with a full day of timed activities, meals at named restaurants, and practical directions]
{'[Include a 🕌 Prayer break line at the typical midday / afternoon / sunset windows]' if personalization_block and user_context and user_context.get('profile', {}).get('prayer_reminders') else ''}
**Day total: ~$[real sum]**
{'**Walking today: ≈[X] km** (keep under profile limit)' if personalization_block and user_context and user_context.get('profile', {}).get('max_walking_km_per_day') else ''}

[Continue for each day — every day should have 6-10 timed entries covering morning, afternoon, and evening. Each day MUST include the Phrase of the Day / Faith note / Walking total / Prayer break lines above when applicable per the Traveler Profile.]

## Day {num_nights + 1}: Departure Day
**{return_date or departure_date} · [Weather]**

[Early time] - Check out of **{hotel_name_for_prompt or 'your hotel'}** (checkout by {hotel_checkout or '11:00 AM'})
{f"[Time] - CONNECTING JOURNEY BACK: Travel from {destination} to {hub_dest_city} ({hub_destination_code}) by domestic flight or car/bus (~$cost, ~X hours). You MUST reach {hub_dest_city} airport in time for the international flight." if hub_route else "[If time allows] - [Quick morning activity — café, walk, or last-minute shopping] (~$cost)"}
{f"[Time] - Arrive at {hub_dest_city} ({hub_destination_code}) airport. Allow 2-3 hours before your international flight." if hub_route else "[Time] - Head to [Airport] by [transport method] (~$cost). Allow 2-3 hours before your flight."}
[Time] - Return flight to {origin}, arriving at approximately [time]
**Day total: ~$[real sum]**

## Don't Miss
- [2-3 local events happening during the travel dates, or seasonal highlights]

## Good to Know
- [3-4 practical safety tips, local customs, or helpful advice for this destination]

## Packing Checklist
- [5-8 weather-specific and destination-specific items]

## Budget Summary ({num_passengers} travelers)
| Category | Cost |
|----------|------|
| Flights ({num_passengers} × ${flight_price_pp:.0f}) | ${flight_price:.0f} |
{f"| Connecting Domestic Flights (hub route) | ${connecting_flight_cost:.0f} |" if connecting_flight_cost > 0 else ""}
| Hotel ({num_nights} nights @ ${hotel_price_per_night:.0f}{hotel_rooms_note}) | ${hotel_total:.0f} |
| Car Rental | ${car_total:.0f} |
| Food & Dining ({num_passengers} people) | $[sum all meal costs × {num_passengers} from daily plans] |
| Local Transport | $[sum all taxi/metro/bus costs] |
| Activities & Attractions ({num_passengers} people) | $[sum all entry fees × {num_passengers}] |
| **Total** | **$[sum of all rows above]** |
| Budget | {budget_display} |
| Remaining | $[budget minus total, or "Flexible" if no budget set] |

CRITICAL REMINDERS:
- There are {num_passengers} travelers — ALL per-person costs (meals, activities, entry fees) must be multiplied by {num_passengers}
- Every [bracketed instruction] must be replaced with real content — never output brackets
- Budget Summary must contain REAL dollar amounts — add up the costs from your daily plans
- Fixed costs: Flights = ${flight_price:.0f}, Hotel = ${hotel_total:.0f}{f', Connecting flights = ${connecting_flight_cost:.0f}' if connecting_flight_cost > 0 else ''}
- Use ALL {len(top_restaurants)} restaurant names from the search data across different meals
- Make the plan feel like a real travel guide someone would follow step by step"""

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


def _generate_fallback_itinerary(*, result, origin, destination, departure_date, return_date, passengers):
    """
    Generate a structured day-by-day itinerary from search results without LLM.
    Used when OPENAI_API_KEY is not configured.
    """
    from datetime import datetime, timedelta

    rec = result.get('recommendation', {})
    flights = result.get('flights', {})
    flight_list = flights.get('flights', []) if isinstance(flights, dict) else []

    # Calculate trip duration
    try:
        dep = datetime.strptime(departure_date, '%Y-%m-%d')
        ret = datetime.strptime(return_date, '%Y-%m-%d') if return_date else dep + timedelta(days=3)
        num_days = max(1, (ret - dep).days + 1)
    except (ValueError, TypeError):
        dep = datetime.now()
        ret = dep + timedelta(days=3)
        num_days = 4

    # Extract top recommendations
    rec_flight = rec.get('recommended_flight', {}) or {}
    rec_hotel = rec.get('recommended_hotel', {}) or {}
    rec_rental = rec.get('recommended_rental', {}) or {}
    rec_restaurant = rec.get('recommended_restaurant', {}) or {}
    rec_car = rec.get('recommended_car', {}) or {}

    flight_price = rec_flight.get('price', 0)
    hotel_name = rec_hotel.get('name') or rec_hotel.get('hotel_name', 'your hotel')
    hotel_price = rec_hotel.get('price') or rec_hotel.get('price_per_night', 0)

    # Prefer rental for groups
    rental_name = rec_rental.get('name') or rec_rental.get('hotel_name', '')
    rental_price = rec_rental.get('price') or rec_rental.get('price_per_night', 0)
    has_rental = bool(rental_name and float(rental_price or 0) > 0)

    accom_name = rental_name if has_rental else hotel_name
    accom_price = float(rental_price) if has_rental else float(hotel_price)
    accom_type = 'Vacation Rental' if has_rental else 'Hotel'

    lines = []
    lines.append(f"## Trip Overview")
    lines.append(f"Your trip from {origin} to {destination} spans {num_days} days and {num_days - 1} night{'s' if num_days > 2 else ''}.")
    if accom_name and accom_name not in ('your hotel', ''):
        if has_rental:
            lines.append(f"You'll be staying at **{accom_name}** — a vacation rental perfect for your group of {passengers}.")
        else:
            lines.append(f"You'll be staying at **{accom_name}**.")
    lines.append("")

    # Budget summary
    total = rec.get('total_estimated_cost', 0) or 0
    accom_total = accom_price * max(1, num_days - 1)
    lines.append(f"## Budget Summary")
    lines.append(f"| Category | Cost |")
    lines.append(f"|----------|------|")
    lines.append(f"| Flights | ${float(flight_price):.0f} |")
    lines.append(f"| {accom_type} ({num_days - 1} nights @ ${accom_price:.0f}) | ${accom_total:.0f} |")
    lines.append(f"| **Total** | **${float(total):.0f}** |")
    lines.append("")

    for day_num in range(1, num_days + 1):
        current_date = dep + timedelta(days=day_num - 1)
        date_str = current_date.strftime('%A, %B %d, %Y')

        if day_num == 1:
            lines.append(f"## Day {day_num}: Arrival in {destination}")
            lines.append(f"**{date_str}**\n")
            if rec_flight:
                airline = rec_flight.get('airline', 'Flight')
                flight_num = rec_flight.get('flight_number', '')
                dep_code = rec_flight.get('departure_airport_code', origin)
                arr_code = rec_flight.get('arrival_airport_code', destination)
                dep_time = rec_flight.get('departure_time', '')
                arr_time = rec_flight.get('arrival_time', '')
                if dep_time:
                    lines.append(f"{dep_time} - Depart on **{airline} {flight_num}** from {dep_code} (~${float(flight_price):.0f})")
                else:
                    lines.append(f"Morning - Depart on **{airline} {flight_num}** from {dep_code} → {arr_code} (~${float(flight_price):.0f})")
                if arr_time:
                    lines.append(f"{arr_time} - Arrive at {arr_code}")
                else:
                    lines.append(f"Afternoon - Arrive in {destination}")
            else:
                lines.append(f"Morning - Depart from {origin}")
                lines.append(f"Afternoon - Arrive in {destination}")
            lines.append(f"3:00 PM - Check in at **{hotel_name}** (~${float(hotel_price):.0f}/night)")
            lines.append(f"4:00 PM - Settle in and explore the neighborhood around your hotel (~$0)")
            if rec_restaurant:
                r_name = rec_restaurant.get('name', 'a local restaurant')
                r_cuisine = rec_restaurant.get('cuisine', 'local cuisine')
                r_price = rec_restaurant.get('price', '$')
                lines.append(f"7:00 PM - Dinner at **{r_name}** ({r_cuisine}) (~$25/person)")
        elif day_num == num_days:
            lines.append(f"## Day {day_num}: Departure from {destination}")
            lines.append(f"**{date_str}**\n")
            lines.append(f"8:00 AM - Breakfast at the hotel or a nearby café (~$10)")
            lines.append(f"9:00 AM - Last-minute sightseeing or souvenir shopping near the hotel (~$20)")
            lines.append(f"11:00 AM - Check out of **{hotel_name}** and store luggage if needed")
            lines.append(f"12:00 PM - Head to the airport by taxi or public transit (~$20)")
            lines.append(f"2:00 PM - Arrive at airport for check-in and security")
            lines.append(f"4:00 PM - Return flight to {origin}")
        else:
            lines.append(f"## Day {day_num}: Explore {destination}")
            lines.append(f"**{date_str}**\n")
            lines.append(f"8:00 AM - Breakfast at **{hotel_name}** or nearby café (~$10)")
            lines.append(f"9:30 AM - Visit local attractions and landmarks (~$15)")
            lines.append(f"12:30 PM - Lunch — try local cuisine at a recommended spot (~$20/person)")
            lines.append(f"2:00 PM - Afternoon cultural activities or guided tour (~$25)")
            if rec_car and rec_car.get('company'):
                lines.append(f"4:00 PM - Drive to a scenic spot with your {rec_car.get('company', '')} {rec_car.get('car_type', 'rental car')}")
            else:
                lines.append(f"4:00 PM - Explore a different neighborhood or park (~$5)")
            lines.append(f"7:30 PM - Dinner at a local restaurant (~$25/person)")

        lines.append(f"**Day total: ~$100**")
        lines.append("")

    return '\n'.join(lines)


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
        from .agent_tools import resolve_city_to_airport

        # Get request data — supports both city/country AND legacy airport codes
        query = request.data.get('query', 'Plan my travel')
        departure_date = request.data.get('departure_date')
        return_date = request.data.get('return_date')
        passengers = request.data.get('passengers', 1)
        budget = request.data.get('budget')
        cuisine = request.data.get('cuisine')
        travel_style = request.data.get('travel_style')
        interests = request.data.get('interests')
        accommodation_preference = request.data.get('accommodation_preference', '')  # 'hotel', 'rental', 'both', 'friend_family', or ''
        friend_stay = request.data.get('friend_stay')  # dict with friend_name, friend_address, etc.

        # Resolve origin: prefer city/country, fall back to legacy airport code
        origin_city = request.data.get('origin_city', '')
        origin_country = request.data.get('origin_country', '')
        origin = request.data.get('origin') or resolve_city_to_airport(origin_city, origin_country)

        # Resolve destination: prefer city/country, fall back to legacy airport code
        destination_city = request.data.get('destination_city', '')
        destination_country = request.data.get('destination_country', '')
        destination = request.data.get('destination') or resolve_city_to_airport(destination_city, destination_country)

        # For hotel/restaurant searches use the human-readable city name
        destination_label = destination_city or destination
        origin_label = origin_city or origin

        # Validate required fields
        if not all([origin, destination, departure_date]):
            return Response({
                'success': False,
                'error': 'origin (or origin_city), destination (or destination_city), and departure_date are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get the travel system
        from .multi_agent_system import get_travel_system
        travel_system = get_travel_system()

        # Load personalized user context (Travel DNA, UserPreference, memories)
        # so the planner respects dietary/faith/mobility/pace, past likes, etc.
        # Trip dates enable Ramadan Mode auto-detection for Muslim travelers.
        from .personalization_service import build_user_planning_context
        user_context = build_user_planning_context(
            request.user,
            trip_start_date=departure_date,
            trip_end_date=return_date,
        )

        # Enrich query with interests/style if provided
        enriched_query = query
        if interests:
            enriched_query += f"\nUser interests: {interests}"
        if travel_style:
            enriched_query += f"\nTravel style: {travel_style}"
        # Surface the user's profile signals in the natural-language query too,
        # so every downstream agent (not just the narrative synthesizer) sees them.
        if user_context.get('signals'):
            enriched_query += "\nTraveler profile signals: " + "; ".join(user_context['signals'])

        # When staying with friend/family, inject context so the AI uses
        # their address as the home base and skips hotel recommendations.
        if accommodation_preference == 'friend_family' and friend_stay:
            friend_name = friend_stay.get('friend_name', 'a friend')
            friend_address = friend_stay.get('friend_address', '')
            friend_rel = friend_stay.get('friend_relationship', 'friend')
            enriched_query += (
                f"\n\nACCOMMODATION: The traveler is staying at their {friend_rel}'s house "
                f"({friend_name}) at {friend_address}. "
                f"Do NOT recommend hotels or vacation rentals. "
                f"Set accommodation cost to $0. "
                f"Use this address as the home base for all daily itinerary routes."
            )

        # Run the multi-agent system
        result = travel_system.run(
            user_query=enriched_query,
            origin=origin,
            destination=destination,
            destination_country=destination_country,
            origin_country=origin_country,
            departure_date=departure_date,
            return_date=return_date,
            passengers=passengers,
            budget=budget,
            cuisine=cuisine,
            accommodation_preference=accommodation_preference,
        )

        # Gather data from ALL enhanced agents (weather, safety, visa, packing, local expert)
        enhanced_data = {}
        if result.get('success'):
            try:
                enhanced_data = _gather_enhanced_agent_data(
                    destination=destination_label,
                    origin=origin_label,
                    departure_date=departure_date,
                    return_date=return_date,
                    cuisine=cuisine,
                )
                result['enhanced_data'] = enhanced_data
            except Exception as e:
                logger.warning(f"Enhanced agent data gathering failed: {e}")

        # Pass friend_stay through so the frontend can render the tab
        if friend_stay and result.get('success'):
            result['friend_stay'] = friend_stay

        # Generate LLM day-by-day narrative itinerary using ALL agent data
        if result.get('success') and settings.OPENAI_API_KEY and settings.OPENAI_API_KEY not in ('your_openai_api_key_here', ''):
            try:
                result['itinerary_text'] = _synthesize_narrative(
                    result=result,
                    origin=origin_label,
                    destination=destination_label,
                    departure_date=departure_date,
                    return_date=return_date,
                    passengers=passengers,
                    budget=budget,
                    cuisine=cuisine,
                    enhanced_data=enhanced_data,
                    interests=interests,
                    travel_style=travel_style,
                    user_context=user_context,
                )
            except Exception as e:
                logger.error(f"LLM narrative generation failed: {e}", exc_info=True)

        # Always provide a fallback itinerary if itinerary_text was not set
        if result.get('success') and not result.get('itinerary_text'):
            result['itinerary_text'] = _generate_fallback_itinerary(
                result=result,
                origin=origin_label,
                destination=destination_label,
                departure_date=departure_date,
                return_date=return_date,
                passengers=passengers,
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
                        'origin_city': origin_city or origin_label,
                        'origin_country': origin_country,
                        'destination': destination,
                        'destination_city': destination_city or destination_label,
                        'destination_country': destination_country,
                        'departure_date': departure_date,
                        'return_date': return_date,
                        'passengers': passengers,
                        'budget': budget,
                        'cuisine': cuisine,
                        'travel_style': travel_style,
                        'interests': interests,
                    },
                    status='completed' if result.get('success') else 'failed'
                )
                result['session_id'] = session.session_id
            except Exception as e:
                # Don't fail the request if session creation fails
                print(f"Session creation error: {e}")

        # Include resolved airport/city info for the frontend
        result['resolved'] = {
            'origin_airport': origin,
            'origin_city': origin_label,
            'origin_country': origin_country,
            'destination_airport': destination,
            'destination_city': destination_label,
            'destination_country': destination_country,
        }

        # Echo personalization signals back so the frontend can show a
        # "Personalized for you" badge with the exact traits applied.
        result['personalization'] = {
            'applied': bool(user_context.get('has_personalization')),
            'signals': user_context.get('signals', []),
        }

        # Add debug info to result for diagnosing search issues
        if result.get('success'):
            result['_search_debug'] = {
                'resolved_origin': origin,
                'resolved_destination': destination,
                'origin_label': origin_label,
                'destination_label': destination_label,
                'flights_found': len(result.get('flights', {}).get('flights', [])) if isinstance(result.get('flights'), dict) else 0,
                'hotels_found': len(result.get('hotels', {}).get('hotels', [])) if isinstance(result.get('hotels'), dict) else 0,
                'hub_route': result.get('flights', {}).get('hub_route', False) if isinstance(result.get('flights'), dict) else False,
                'hub_destination': result.get('flights', {}).get('hub_destination') if isinstance(result.get('flights'), dict) else None,
                'transit_notes': result.get('flights', {}).get('transit_notes', []) if isinstance(result.get('flights'), dict) else [],
                'hotel_fallback': result.get('hotels', {}).get('fallback_city') if isinstance(result.get('hotels'), dict) else None,
            }

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RAGDocumentViewSet(viewsets.ModelViewSet):
    """
    API for uploading, listing, and managing RAG documents.
    Supports PDF, TXT, DOCX, MD, and CSV files.
    Uploaded files are parsed, chunked, and indexed into ChromaDB
    so the AI assistant can reference them during chat.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = RAGDocumentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'scope', 'file_type']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title', 'file_size']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return RAGDocument.objects.all()
        return RAGDocument.objects.filter(
            Q(uploaded_by=user) | Q(scope='global')
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return RAGDocumentUploadSerializer
        return RAGDocumentSerializer

    def perform_create(self, serializer):
        doc = serializer.save(uploaded_by=self.request.user)
        # Process and index the document
        try:
            from apps.agents.document_processor import process_and_index_document
            chunk_count = process_and_index_document(doc)
            logger.info(f"Document '{doc.title}' uploaded and indexed: {chunk_count} chunks")
        except Exception as e:
            logger.error(f"Document processing failed for '{doc.title}': {e}")
            doc.status = 'failed'
            doc.error_message = str(e)[:500]
            doc.save(update_fields=['status', 'error_message'])

    def perform_destroy(self, instance):
        # Delete ChromaDB chunks before deleting the model
        try:
            from apps.agents.document_processor import delete_document_chunks
            delete_document_chunks(instance)
        except Exception as e:
            logger.warning(f"Error cleaning up document chunks: {e}")
        # Delete the file from storage
        if instance.file:
            instance.file.delete(save=False)
        instance.delete()

    @action(detail=True, methods=['post'])
    def reindex(self, request, pk=None):
        """Re-process and re-index a document."""
        doc = self.get_object()
        try:
            from apps.agents.document_processor import process_and_index_document
            chunk_count = process_and_index_document(doc)
            return Response({
                'success': True,
                'message': f'Document re-indexed with {chunk_count} chunks',
                'chunk_count': chunk_count,
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat(request):
    """
    Fully conversational AI travel assistant endpoint.
    Requires authentication so the assistant can access user data.

    Handles:
    - Trip planning with NLP parameter extraction
    - Questions about user's existing trips, bookings, itineraries
    - Travel recommendations and advice
    - General travel knowledge questions
    - Future travel planning suggestions
    """
    try:
        message = request.data.get('message', '')
        conversation = request.data.get('conversation', [])
        prev_params = request.data.get('extracted_params', {})
        confirmed = request.data.get('confirmed', False)
        user_context = request.data.get('user_context', '')

        if not message and not confirmed:
            return Response({
                'success': False,
                'error': 'message is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # ── If user confirmed and params are complete → run the planner ──
        if confirmed and prev_params.get('origin') and prev_params.get('destination') and prev_params.get('departure_date'):
            from .multi_agent_system import get_travel_system
            from .personalization_service import build_user_planning_context
            travel_system = get_travel_system()

            # Load traveler profile so the chat-initiated plan honors dietary /
            # faith / mobility / language constraints, same as /plan-travel.
            # Trip dates enable Ramadan Mode auto-detection.
            chat_user_context = build_user_planning_context(
                request.user,
                trip_start_date=prev_params.get('departure_date'),
                trip_end_date=prev_params.get('return_date'),
            )

            p = prev_params
            chat_query = f"Plan a trip from {p['origin']} to {p['destination']}"
            if chat_user_context.get('signals'):
                chat_query += "\nTraveler profile signals: " + "; ".join(chat_user_context['signals'])

            result = travel_system.run(
                user_query=chat_query,
                origin=p['origin'],
                destination=p['destination'],
                departure_date=p['departure_date'],
                return_date=p.get('return_date'),
                passengers=p.get('passengers', 1),
                budget=p.get('budget'),
                cuisine=p.get('cuisine'),
            )

            # Gather enhanced agent data
            enhanced_data = {}
            if result.get('success'):
                try:
                    enhanced_data = _gather_enhanced_agent_data(
                        destination=p['destination'],
                        origin=p['origin'],
                        departure_date=p['departure_date'],
                        return_date=p.get('return_date'),
                        cuisine=p.get('cuisine'),
                    )
                    result['enhanced_data'] = enhanced_data
                except Exception as e:
                    logger.warning(f"Enhanced agent data gathering failed: {e}")

            # Generate narrative (only if we have a real API key)
            if result.get('success') and settings.OPENAI_API_KEY and settings.OPENAI_API_KEY not in ('your_openai_api_key_here', ''):
                try:
                    result['itinerary_text'] = _synthesize_narrative(
                        result=result,
                        origin=p['origin'],
                        destination=p['destination'],
                        departure_date=p['departure_date'],
                        return_date=p.get('return_date'),
                        passengers=p.get('passengers', 1),
                        budget=p.get('budget'),
                        cuisine=p.get('cuisine'),
                        enhanced_data=enhanced_data,
                        user_context=chat_user_context,
                    )
                except Exception as e:
                    logger.error(f"LLM narrative failed: {e}", exc_info=True)

            # Echo personalization so the chat-UI can show a "Personalized" badge.
            if result.get('success'):
                result['personalization'] = {
                    'applied': bool(chat_user_context.get('has_personalization')),
                    'signals': chat_user_context.get('signals', []),
                }

            # Always ensure we have an itinerary, even without LLM
            if result.get('success') and not result.get('itinerary_text'):
                result['itinerary_text'] = _generate_fallback_itinerary(
                    result=result,
                    origin=p['origin'],
                    destination=p['destination'],
                    departure_date=p['departure_date'],
                    return_date=p.get('return_date'),
                    passengers=p.get('passengers', 1),
                )

            return Response({
                'success': True,
                'reply': "Your trip is being planned! Here are the results.",
                'planning_result': result,
                'extracted_params': prev_params,
                'params_complete': True,
                'ready_to_plan': True,
            })

        # ── Otherwise, use LLM for conversation ──
        if not settings.OPENAI_API_KEY:
            return Response({
                'success': False,
                'error': 'AI service not configured'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage, SystemMessage, AIMessage

        model = ChatOpenAI(
            model=settings.AGENT_CONFIG.get('MODEL', 'gpt-4o-mini'),
            temperature=0.4,
            api_key=settings.OPENAI_API_KEY,
            request_timeout=45,
        )

        # ── RAG: Retrieve only the most relevant user data for this query ──
        user_data_section = ''
        rag_context = ''
        try:
            from apps.agents.chat_rag import get_user_data_rag

            user_rag = get_user_data_rag()
            rag_context = user_rag.retrieve(
                user=request.user,
                query=message,
                n_results=8,
            )
            rag_stats = user_rag.get_user_stats(request.user)
            total_chunks = rag_stats.get('total_chunks', 0)

            # Build user data section from RAG results
            user_name = f"{request.user.first_name or ''} {request.user.last_name or ''}".strip() or 'Traveler'
            user_data_section = f"Logged-in user: {user_name} ({request.user.email})\n"

            if rag_context:
                user_data_section += (
                    f"\n--- RELEVANT USER DATA (retrieved via semantic search from {total_chunks} indexed records) ---\n"
                    f"{rag_context}\n"
                    f"--- END RELEVANT DATA ---"
                )
            else:
                user_data_section += "User has no bookings or trip plans yet."

        except Exception as e:
            logger.warning(f"RAG retrieval failed, falling back to basic context: {e}")
            # Fallback: basic user info without full data dump
            try:
                user_name = f"{request.user.first_name or ''} {request.user.last_name or ''}".strip() or 'Traveler'
                user_data_section = f"Logged-in user: {user_name} ({request.user.email})"
            except Exception:
                user_data_section = ''

        if user_context:
            user_data_section += f"\nAdditional user context:\n{user_context}"

        system_prompt = f"""You are a friendly, knowledgeable AI travel assistant for the AI Smart Flight Agent platform.
You are talking to an AUTHENTICATED USER. You have access to their real booking data, trip plans, itineraries, and feedback.
The user data below was retrieved via RAG (semantic search) — it shows the MOST RELEVANT records for the user's current question.
Always reference their actual data when answering questions about their trips.

## YOUR CAPABILITIES:
1. **Trip Planning**: Extract travel parameters and help plan new trips using our multi-agent AI system
2. **Trip Q&A**: Answer questions about the user's EXISTING bookings and itineraries (use the RETRIEVED USER DATA below)
3. **Recommendations**: Suggest destinations, restaurants, activities, hotels based on their preferences and travel history
4. **Travel Knowledge**: Answer questions about visa requirements, weather, safety, culture, customs
5. **Budget Advice**: Help users optimize their travel budget and find deals
6. **Comparison**: Compare destinations, flights, hotels, help users decide
7. **Future Planning**: Suggest future trip ideas based on user's past trips, feedback, and preferences
8. **Site Help**: Help users navigate the platform features

## PLATFORM FEATURES (mention these when relevant):
- AI Trip Planner: Plan complete trips with flights, hotels, cars, restaurants
- Flight Search & Booking: Search and book flights
- Hotel Search & Booking: Find and book hotels
- Car Rental: Rent cars at destinations
- Restaurant Finder: Find restaurants by cuisine
- Itinerary Builder: Create day-by-day trip plans with PDF export
- Weather Forecasts: Check weather at destinations
- Events & Attractions: Discover local events and attractions
- Safety Info: Get health and safety info for destinations
- Dashboard: View all bookings and trip plans in one place

## RETRIEVED USER DATA (semantically matched to user's question — THIS IS REAL DATA):
{user_data_section if user_data_section else 'User has no bookings or trip plans yet.'}

NOTE: The data above is the most relevant subset retrieved from all of the user's records. If the user asks about something not shown above, let them know you can look up more details or suggest they check their Dashboard.

## TRAVEL PARAMETER EXTRACTION:
When the user wants to plan a NEW trip, extract these parameters:
- origin: departure city/airport
- destination: arrival city/airport
- departure_date: YYYY-MM-DD format (today is {timezone.now().strftime('%Y-%m-%d')})
- return_date: YYYY-MM-DD format
- passengers: number of travelers (default 1)
- budget: total budget in USD
- cuisine: preferred cuisine

PREVIOUSLY EXTRACTED parameters:
{json.dumps(prev_params, indent=2) if prev_params else '{{}}'}

## RESPONSE FORMAT:
Always respond with TWO parts separated by "---PARAMS---":

Part 1: Your conversational reply (be warm, helpful, specific, and concise)
Part 2: A JSON object with extracted travel parameters (or {{}} if no trip planning is happening)

## IMPORTANT RULES:
- If the user asks a GENERAL question (weather, recommendations, visa, culture), just answer it helpfully. Still include ---PARAMS--- with the current params (or empty {{}}).
- If the user asks about THEIR trips/bookings, reference the user data above.
- If the user is planning a trip and you have origin + destination + departure_date, summarize and ask to confirm.
- Convert relative dates ("next Friday", "in March") to exact YYYY-MM-DD dates.
- Be concise (2-4 sentences for simple questions, more for complex ones).
- Use a warm, travel-enthusiast tone with specific, actionable advice.
- If asked about something outside travel, politely redirect to travel topics.
- For recommendation questions, give specific names of places/restaurants/attractions."""

        # Build conversation messages for LLM
        llm_messages = [SystemMessage(content=system_prompt)]
        for msg in conversation[-20:]:
            if msg.get('role') == 'user':
                llm_messages.append(HumanMessage(content=msg['content']))
            elif msg.get('role') == 'assistant':
                content = msg['content'].split('---PARAMS---')[0].strip()
                llm_messages.append(AIMessage(content=content))

        llm_messages.append(HumanMessage(content=message))

        response = model.invoke(llm_messages)
        full_response = response.content.strip()

        # Parse the response
        if '---PARAMS---' in full_response:
            parts = full_response.split('---PARAMS---', 1)
            reply = parts[0].strip()
            params_json = parts[1].strip()
        else:
            reply = full_response
            params_json = '{}'

        # Parse extracted parameters
        try:
            clean_json = params_json
            if clean_json.startswith('```'):
                clean_json = clean_json.split('\n', 1)[1] if '\n' in clean_json else clean_json[3:]
                if clean_json.endswith('```'):
                    clean_json = clean_json[:-3]
                clean_json = clean_json.strip()
            extracted = json.loads(clean_json)
        except json.JSONDecodeError:
            extracted = prev_params

        # Merge with previous params
        merged = {**prev_params}
        for key, value in extracted.items():
            if value is not None and value != '' and value != 0:
                merged[key] = value

        params_complete = bool(
            merged.get('origin') and
            merged.get('destination') and
            merged.get('departure_date')
        )

        return Response({
            'success': True,
            'reply': reply,
            'extracted_params': merged,
            'params_complete': params_complete,
            'ready_to_plan': False,
        })

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def text_to_speech(request):
    """
    Convert text to speech using OpenAI TTS API (with ElevenLabs fallback).

    Request body:
    {
        "text": "The text to convert to speech",
        "voice": "optional voice name (default: nova)"
    }

    Returns: audio/mpeg binary stream
    """
    import requests as http_requests

    text = request.data.get('text', '')
    if not text:
        return Response({'error': 'text is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Try OpenAI TTS first (most likely configured)
    openai_key = settings.OPENAI_API_KEY
    if openai_key and openai_key not in ('your_openai_api_key_here', ''):
        try:
            voice = request.data.get('voice', 'nova')  # nova, alloy, echo, fable, onyx, shimmer
            logger.info(f"Calling OpenAI TTS: voice={voice}, text_len={len(text)}")
            el_response = http_requests.post(
                'https://api.openai.com/v1/audio/speech',
                headers={
                    'Authorization': f'Bearer {openai_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': 'tts-1',
                    'input': text[:4096],
                    'voice': voice,
                    'response_format': 'mp3',
                },
                timeout=30,
            )

            if el_response.status_code == 200:
                from django.http import HttpResponse as DjangoHttpResponse
                logger.info(f"OpenAI TTS success: {len(el_response.content)} bytes")
                response = DjangoHttpResponse(
                    el_response.content,
                    content_type='audio/mpeg',
                )
                response['Content-Disposition'] = 'inline; filename="speech.mp3"'
                response['Content-Length'] = len(el_response.content)
                response['Access-Control-Allow-Origin'] = '*'
                return response
            else:
                logger.warning(f"OpenAI TTS error: {el_response.status_code} {el_response.text[:200]}")
        except Exception as e:
            logger.warning(f"OpenAI TTS failed, trying ElevenLabs: {e}")

    # Fallback to ElevenLabs if configured
    api_key = getattr(settings, 'ELEVENLABS_API_KEY', '')
    if api_key:
        try:
            voice_id = request.data.get('voice_id', '21m00Tcm4TlvDq8ikWAM')  # Rachel voice
            el_response = http_requests.post(
                f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}',
                headers={
                    'Accept': 'audio/mpeg',
                    'Content-Type': 'application/json',
                    'xi-api-key': api_key,
                },
                json={
                    'text': text[:5000],
                    'model_id': 'eleven_monolingual_v1',
                    'voice_settings': {
                        'stability': 0.5,
                        'similarity_boost': 0.75,
                    },
                },
                timeout=30,
            )

            if el_response.status_code == 200:
                from django.http import HttpResponse as DjangoHttpResponse
                response = DjangoHttpResponse(
                    el_response.content,
                    content_type='audio/mpeg',
                )
                response['Content-Disposition'] = 'inline; filename="speech.mp3"'
                return response
            else:
                logger.warning(f"ElevenLabs API error: {el_response.status_code}")
        except Exception as e:
            logger.warning(f"ElevenLabs TTS failed: {e}")

    return Response(
        {'error': 'No TTS service available. Configure OPENAI_API_KEY or ELEVENLABS_API_KEY.'},
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auto_build_itinerary(request):
    """
    Smart Auto-Builder: Build a complete itinerary from minimal input.
    """
    destination = request.data.get('destination')
    start_date = request.data.get('start_date')
    end_date = request.data.get('end_date')

    if not all([destination, start_date, end_date]):
        return Response(
            {'error': 'destination, start_date, and end_date are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        from .auto_builder import SmartItineraryBuilder
        builder = SmartItineraryBuilder(user=request.user)
        result = builder.build(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            origin=request.data.get('origin', ''),
            budget=request.data.get('budget'),
            travelers=request.data.get('travelers', 1),
            trip_style=request.data.get('trip_style', 'balanced'),
            preferences=request.data.get('preferences', {}),
            accommodation_preference=request.data.get('accommodation_preference', ''),
        )
        return Response({'success': True, 'itinerary': result})
    except Exception as e:
        logger.error(f"Auto-build failed: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ─────────────────────────────────────────────────
# Multi-Modal Agent Endpoints (Voice + Image)
# ─────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def voice_to_trip(request):
    """Transcribe voice input and extract travel intent."""
    audio_file = request.FILES.get('audio')
    if not audio_file:
        return Response({'error': 'audio file is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from .multimodal_agent import MultiModalAgent
        agent = MultiModalAgent()
        result = agent.transcribe_voice(audio_file)
        return Response(result)
    except Exception as e:
        logger.error(f"Voice transcription failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def image_to_trip(request):
    """Analyze an image to identify destinations and suggest trips."""
    image_file = request.FILES.get('image')
    if not image_file:
        return Response({'error': 'image file is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from .multimodal_agent import MultiModalAgent
        agent = MultiModalAgent()
        result = agent.analyze_image(image_file)
        return Response(result)
    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_screenshot(request):
    """Extract flight/hotel deal info from a screenshot."""
    image_file = request.FILES.get('image')
    if not image_file:
        return Response({'error': 'image file is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from .multimodal_agent import MultiModalAgent
        agent = MultiModalAgent()
        result = agent.analyze_screenshot(image_file)
        return Response(result)
    except Exception as e:
        logger.error(f"Screenshot analysis failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────
# Autonomous Booking Endpoints
# ─────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def autonomous_book(request):
    """Plan an entire trip autonomously — search, evaluate, and recommend."""
    destination = request.data.get('destination')
    start_date = request.data.get('start_date')
    end_date = request.data.get('end_date')

    if not all([destination, start_date, end_date]):
        return Response(
            {'error': 'destination, start_date, and end_date are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        from .autonomous_booking import AutonomousBookingAgent
        agent = AutonomousBookingAgent(user=request.user)
        result = agent.plan_and_book(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            origin=request.data.get('origin', ''),
            budget=request.data.get('budget'),
            travelers=request.data.get('travelers', 1),
            preferences=request.data.get('preferences', {}),
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Autonomous booking failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_autonomous_booking(request):
    """Confirm a previously planned autonomous booking."""
    task_id = request.data.get('task_id')
    package = request.data.get('package', {})
    payment_method_id = request.data.get('payment_method_id')

    if not task_id and not package:
        return Response(
            {'error': 'task_id or package is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from .autonomous_booking import AutonomousBookingAgent
        from .models import AgentTask
        agent = AutonomousBookingAgent(user=request.user)

        # Resolve package from task_id if not provided directly
        if not package and task_id:
            try:
                task = AgentTask.objects.get(id=task_id, user=request.user)
                package = task.result.get('package', {}) if task.result else {}
            except AgentTask.DoesNotExist:
                return Response(
                    {'error': 'Task not found'},
                    status=status.HTTP_404_NOT_FOUND,
                )

        result = agent.confirm_booking(package, payment_method_id=payment_method_id)
        return Response(result)
    except Exception as e:
        logger.error(f"Booking confirmation failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────
# Multi-Agent Debate Endpoints
# ─────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def debate_options(request):
    """Run a multi-agent debate on travel options."""
    options = request.data.get('options', [])
    context = request.data.get('context', {})
    use_llm = request.data.get('use_llm', False)

    if not options:
        return Response({'error': 'options list is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from .debate_system import TravelDebateSystem
        system = TravelDebateSystem()
        if use_llm:
            result = system.debate_with_llm(options, context)
        else:
            result = system.debate(options, context)
        return Response(result)
    except Exception as e:
        logger.error(f"Debate failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────
# Predictive Intelligence Endpoints
# ─────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_prices(request):
    """Predict flight price trends for a route."""
    origin = request.data.get('origin')
    destination = request.data.get('destination')
    target_date = request.data.get('target_date')

    if not all([origin, destination, target_date]):
        return Response(
            {'error': 'origin, destination, and target_date are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        from .predictive_intelligence import PredictiveIntelligence
        pi = PredictiveIntelligence()
        result = pi.predict_price_trend(
            origin=origin,
            destination=destination,
            target_date=target_date,
            days_ahead=request.data.get('days_ahead', 30),
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Price prediction failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def best_time_to_visit(request):
    """Get the best time to visit a destination."""
    destination = request.query_params.get('destination')
    if not destination:
        return Response({'error': 'destination query param is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from .predictive_intelligence import PredictiveIntelligence
        pi = PredictiveIntelligence()
        result = pi.best_time_to_visit(destination)
        return Response(result)
    except Exception as e:
        logger.error(f"Best time analysis failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crowd_levels(request):
    """Get estimated crowd levels for a destination by month."""
    destination = request.query_params.get('destination')
    if not destination:
        return Response({'error': 'destination query param is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from .predictive_intelligence import PredictiveIntelligence
        pi = PredictiveIntelligence()
        result = pi.predict_crowd_levels(destination)
        return Response(result)
    except Exception as e:
        logger.error(f"Crowd level prediction failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def destination_trends(request):
    """Get trending destinations."""
    limit = int(request.query_params.get('limit', 10))

    try:
        from .predictive_intelligence import PredictiveIntelligence
        pi = PredictiveIntelligence()
        result = pi.destination_trends(limit=limit)
        return Response(result)
    except Exception as e:
        logger.error(f"Destination trends failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trip_experience_preview(request):
    """Generate an immersive AI-powered trip experience preview."""
    destination = request.data.get('destination')
    start_date = request.data.get('start_date')
    end_date = request.data.get('end_date')

    if not all([destination, start_date, end_date]):
        return Response(
            {'error': 'destination, start_date, and end_date are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        from .predictive_intelligence import PredictiveIntelligence
        pi = PredictiveIntelligence()
        result = pi.generate_trip_experience(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            travelers=request.data.get('travelers', 1),
            interests=request.data.get('interests', []),
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Trip experience preview failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────
# Personalization Endpoints
# ─────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def get_travel_dna(request):
    """Build and return the user's Travel DNA profile."""
    try:
        from .personalization_service import PersonalizationService
        service = PersonalizationService()
        dna = service.build_travel_dna(request.user)
        return Response({'success': True, 'travel_dna': dna})
    except Exception as e:
        logger.error(f"Travel DNA failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PATCH', 'PUT'])
@permission_classes([IsAuthenticated])
def user_preferences(request):
    """Get or update the user's Travel DNA v2 preferences."""
    from .models import UserPreference
    from .serializers import UserPreferenceSerializer

    pref, _ = UserPreference.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        return Response(UserPreferenceSerializer(pref).data)

    serializer = UserPreferenceSerializer(pref, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recommendations(request):
    """Get personalized trip recommendations based on Travel DNA."""
    limit = int(request.query_params.get('limit', 5))

    try:
        from .personalization_service import PersonalizationService
        service = PersonalizationService()
        result = service.get_recommendations(request.user, limit=limit)
        return Response(result)
    except Exception as e:
        logger.error(f"Recommendations failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────
# Language Translation
# ─────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def translate_text(request):
    """Translate text between languages using LLM."""
    text = request.data.get('text', '').strip()
    source_lang = request.data.get('source_lang', 'auto')
    target_lang = request.data.get('target_lang', 'en')

    if not text:
        return Response({'error': 'Text is required'}, status=status.HTTP_400_BAD_REQUEST)

    import os
    api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
    if api_key and api_key not in ('your_openai_api_key_here', ''):
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(model='gpt-4o-mini', temperature=0.1,
                               api_key=api_key, request_timeout=15)
            src = f"from {source_lang}" if source_lang != 'auto' else "(auto-detect language)"
            resp = model.invoke([
                SystemMessage(content="You are a precise translator. Return ONLY the translated text."),
                HumanMessage(content=f"Translate {src} to {target_lang}:\n\n{text}"),
            ])
            return Response({
                'translated_text': resp.content.strip(),
                'source_lang': source_lang, 'target_lang': target_lang,
                'original_text': text,
            })
        except Exception as e:
            logger.warning(f"LLM translation failed: {e}")

    return Response({
        'translated_text': text, 'source_lang': source_lang,
        'target_lang': target_lang, 'original_text': text,
        'note': 'Translation service unavailable',
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def common_phrases(request):
    """Get common travel phrases for a destination language."""
    language = request.query_params.get('language', 'en')
    PACKS = {
        'es': {'language_name': 'Spanish', 'phrases': [
            {'phrase': 'Hola', 'translation': 'Hello', 'category': 'greeting'},
            {'phrase': 'Gracias', 'translation': 'Thank you', 'category': 'greeting'},
            {'phrase': 'Por favor', 'translation': 'Please', 'category': 'greeting'},
            {'phrase': '\u00bfCu\u00e1nto cuesta?', 'translation': 'How much?', 'category': 'shopping'},
            {'phrase': '\u00bfD\u00f3nde est\u00e1...?', 'translation': 'Where is...?', 'category': 'directions'},
            {'phrase': 'La cuenta, por favor', 'translation': 'The bill, please', 'category': 'restaurant'},
            {'phrase': 'No entiendo', 'translation': "I don't understand", 'category': 'general'},
            {'phrase': 'Necesito ayuda', 'translation': 'I need help', 'category': 'emergency'},
            {'phrase': '\u00bfHabla ingl\u00e9s?', 'translation': 'Do you speak English?', 'category': 'general'},
            {'phrase': 'Adi\u00f3s', 'translation': 'Goodbye', 'category': 'greeting'},
        ]},
        'fr': {'language_name': 'French', 'phrases': [
            {'phrase': 'Bonjour', 'translation': 'Hello', 'category': 'greeting'},
            {'phrase': 'Merci', 'translation': 'Thank you', 'category': 'greeting'},
            {'phrase': "S'il vous pla\u00eet", 'translation': 'Please', 'category': 'greeting'},
            {'phrase': 'Combien \u00e7a co\u00fbte?', 'translation': 'How much?', 'category': 'shopping'},
            {'phrase': 'O\u00f9 est...?', 'translation': 'Where is...?', 'category': 'directions'},
            {'phrase': "L'addition, s'il vous pla\u00eet", 'translation': 'The bill, please', 'category': 'restaurant'},
            {'phrase': 'Je ne comprends pas', 'translation': "I don't understand", 'category': 'general'},
            {'phrase': "J'ai besoin d'aide", 'translation': 'I need help', 'category': 'emergency'},
            {'phrase': 'Parlez-vous anglais?', 'translation': 'Do you speak English?', 'category': 'general'},
            {'phrase': 'Au revoir', 'translation': 'Goodbye', 'category': 'greeting'},
        ]},
        'de': {'language_name': 'German', 'phrases': [
            {'phrase': 'Hallo', 'translation': 'Hello', 'category': 'greeting'},
            {'phrase': 'Danke', 'translation': 'Thank you', 'category': 'greeting'},
            {'phrase': 'Bitte', 'translation': 'Please', 'category': 'greeting'},
            {'phrase': 'Wie viel kostet das?', 'translation': 'How much?', 'category': 'shopping'},
            {'phrase': 'Wo ist...?', 'translation': 'Where is...?', 'category': 'directions'},
            {'phrase': 'Die Rechnung, bitte', 'translation': 'The bill, please', 'category': 'restaurant'},
            {'phrase': 'Ich verstehe nicht', 'translation': "I don't understand", 'category': 'general'},
            {'phrase': 'Ich brauche Hilfe', 'translation': 'I need help', 'category': 'emergency'},
            {'phrase': 'Sprechen Sie Englisch?', 'translation': 'Do you speak English?', 'category': 'general'},
            {'phrase': 'Tsch\u00fcss', 'translation': 'Goodbye', 'category': 'greeting'},
        ]},
        'ja': {'language_name': 'Japanese', 'phrases': [
            {'phrase': '\u3053\u3093\u306b\u3061\u306f', 'translation': 'Hello', 'category': 'greeting'},
            {'phrase': '\u3042\u308a\u304c\u3068\u3046', 'translation': 'Thank you', 'category': 'greeting'},
            {'phrase': '\u304a\u306d\u304c\u3044\u3057\u307e\u3059', 'translation': 'Please', 'category': 'greeting'},
            {'phrase': '\u3044\u304f\u3089\u3067\u3059\u304b?', 'translation': 'How much?', 'category': 'shopping'},
            {'phrase': '...\u306f\u3069\u3053\u3067\u3059\u304b?', 'translation': 'Where is...?', 'category': 'directions'},
            {'phrase': '\u304a\u4f1a\u8a08\u304a\u306d\u304c\u3044\u3057\u307e\u3059', 'translation': 'Check please', 'category': 'restaurant'},
            {'phrase': '\u308f\u304b\u308a\u307e\u305b\u3093', 'translation': "I don't understand", 'category': 'general'},
            {'phrase': '\u52a9\u3051\u3066\u304f\u3060\u3055\u3044', 'translation': 'Help me', 'category': 'emergency'},
            {'phrase': '\u82f1\u8a9e\u3092\u8a71\u305b\u307e\u3059\u304b?', 'translation': 'Do you speak English?', 'category': 'general'},
            {'phrase': '\u3055\u3088\u3046\u306a\u3089', 'translation': 'Goodbye', 'category': 'greeting'},
        ]},
        'ar': {'language_name': 'Arabic', 'phrases': [
            {'phrase': '\u0645\u0631\u062d\u0628\u0627', 'translation': 'Hello', 'category': 'greeting'},
            {'phrase': '\u0634\u0643\u0631\u0627', 'translation': 'Thank you', 'category': 'greeting'},
            {'phrase': '\u0645\u0646 \u0641\u0636\u0644\u0643', 'translation': 'Please', 'category': 'greeting'},
            {'phrase': '\u0628\u0643\u0645 \u0647\u0630\u0627\u061f', 'translation': 'How much?', 'category': 'shopping'},
            {'phrase': '\u0623\u064a\u0646...?\u200f', 'translation': 'Where is...?', 'category': 'directions'},
            {'phrase': '\u0627\u0644\u062d\u0633\u0627\u0628 \u0645\u0646 \u0641\u0636\u0644\u0643', 'translation': 'The bill please', 'category': 'restaurant'},
            {'phrase': '\u0644\u0627 \u0623\u0641\u0647\u0645', 'translation': "I don't understand", 'category': 'general'},
            {'phrase': '\u0623\u062d\u062a\u0627\u062c \u0645\u0633\u0627\u0639\u062f\u0629', 'translation': 'I need help', 'category': 'emergency'},
            {'phrase': '\u0647\u0644 \u062a\u062a\u0643\u0644\u0645 \u0627\u0644\u0625\u0646\u062c\u0644\u064a\u0632\u064a\u0629\u061f', 'translation': 'Do you speak English?', 'category': 'general'},
            {'phrase': '\u0645\u0639 \u0627\u0644\u0633\u0644\u0627\u0645\u0629', 'translation': 'Goodbye', 'category': 'greeting'},
        ]},
        'zh': {'language_name': 'Chinese', 'phrases': [
            {'phrase': '\u4f60\u597d', 'translation': 'Hello', 'category': 'greeting'},
            {'phrase': '\u8c22\u8c22', 'translation': 'Thank you', 'category': 'greeting'},
            {'phrase': '\u8bf7', 'translation': 'Please', 'category': 'greeting'},
            {'phrase': '\u591a\u5c11\u94b1\uff1f', 'translation': 'How much?', 'category': 'shopping'},
            {'phrase': '...\u5728\u54ea\u91cc\uff1f', 'translation': 'Where is...?', 'category': 'directions'},
            {'phrase': '\u4e70\u5355', 'translation': 'The bill', 'category': 'restaurant'},
            {'phrase': '\u6211\u4e0d\u61c2', 'translation': "I don't understand", 'category': 'general'},
            {'phrase': '\u6211\u9700\u8981\u5e2e\u52a9', 'translation': 'I need help', 'category': 'emergency'},
            {'phrase': '\u4f60\u4f1a\u8bf4\u82f1\u8bed\u5417\uff1f', 'translation': 'Do you speak English?', 'category': 'general'},
            {'phrase': '\u518d\u89c1', 'translation': 'Goodbye', 'category': 'greeting'},
        ]},
        'hi': {'language_name': 'Hindi', 'phrases': [
            {'phrase': '\u0928\u092e\u0938\u094d\u0924\u0947', 'translation': 'Hello', 'category': 'greeting'},
            {'phrase': '\u0927\u0928\u094d\u092f\u0935\u093e\u0926', 'translation': 'Thank you', 'category': 'greeting'},
            {'phrase': '\u0915\u0943\u092a\u092f\u093e', 'translation': 'Please', 'category': 'greeting'},
            {'phrase': '\u092f\u0939 \u0915\u093f\u0924\u0928\u0947 \u0915\u093e \u0939\u0948?', 'translation': 'How much?', 'category': 'shopping'},
            {'phrase': '...\u0915\u0939\u093e\u0901 \u0939\u0948?', 'translation': 'Where is...?', 'category': 'directions'},
            {'phrase': '\u092c\u093f\u0932 \u0926\u0940\u091c\u093f\u090f', 'translation': 'The bill please', 'category': 'restaurant'},
            {'phrase': '\u092e\u0941\u091d\u0947 \u0938\u092e\u091d \u0928\u0939\u0940\u0902 \u0906\u092f\u093e', 'translation': "I don't understand", 'category': 'general'},
            {'phrase': '\u092e\u0941\u091d\u0947 \u092e\u0926\u0926 \u091a\u093e\u0939\u093f\u090f', 'translation': 'I need help', 'category': 'emergency'},
            {'phrase': '\u0915\u094d\u092f\u093e \u0906\u092a \u0905\u0902\u0917\u094d\u0930\u0947\u091c\u0940 \u092c\u094b\u0932\u0924\u0947 \u0939\u0948\u0902?', 'translation': 'Do you speak English?', 'category': 'general'},
            {'phrase': '\u0905\u0932\u0935\u093f\u0926\u093e', 'translation': 'Goodbye', 'category': 'greeting'},
        ]},
        'ko': {'language_name': 'Korean', 'phrases': [
            {'phrase': '\uc548\ub155\ud558\uc138\uc694', 'translation': 'Hello', 'category': 'greeting'},
            {'phrase': '\uac10\uc0ac\ud569\ub2c8\ub2e4', 'translation': 'Thank you', 'category': 'greeting'},
            {'phrase': '\uc8fc\uc138\uc694', 'translation': 'Please', 'category': 'greeting'},
            {'phrase': '\uc5bc\ub9c8\uc608\uc694?', 'translation': 'How much?', 'category': 'shopping'},
            {'phrase': '...\uc5b4\ub514\uc5d0\uc694?', 'translation': 'Where is...?', 'category': 'directions'},
            {'phrase': '\uacc4\uc0b0\uc11c \uc8fc\uc138\uc694', 'translation': 'Check please', 'category': 'restaurant'},
            {'phrase': '\ubabb \uc54c\uc544\ub4e3\uaca0\uc5b4\uc694', 'translation': "I don't understand", 'category': 'general'},
            {'phrase': '\ub3c4\uc640\uc8fc\uc138\uc694', 'translation': 'Help me', 'category': 'emergency'},
            {'phrase': '\uc601\uc5b4 \ud560 \uc218 \uc788\uc5b4\uc694?', 'translation': 'Do you speak English?', 'category': 'general'},
            {'phrase': '\uc548\ub155\ud788 \uac00\uc138\uc694', 'translation': 'Goodbye', 'category': 'greeting'},
        ]},
        'tr': {'language_name': 'Turkish', 'phrases': [
            {'phrase': 'Merhaba', 'translation': 'Hello', 'category': 'greeting'},
            {'phrase': 'Te\u015fekk\u00fcr ederim', 'translation': 'Thank you', 'category': 'greeting'},
            {'phrase': 'L\u00fctfen', 'translation': 'Please', 'category': 'greeting'},
            {'phrase': 'Bu ne kadar?', 'translation': 'How much?', 'category': 'shopping'},
            {'phrase': '...nerede?', 'translation': 'Where is...?', 'category': 'directions'},
            {'phrase': 'Hesap l\u00fctfen', 'translation': 'The bill please', 'category': 'restaurant'},
            {'phrase': 'Anlam\u0131yorum', 'translation': "I don't understand", 'category': 'general'},
            {'phrase': 'Yard\u0131ma ihtiyac\u0131m var', 'translation': 'I need help', 'category': 'emergency'},
            {'phrase': '\u0130ngilizce biliyor musunuz?', 'translation': 'Do you speak English?', 'category': 'general'},
            {'phrase': 'Ho\u015f\u00e7a kal\u0131n', 'translation': 'Goodbye', 'category': 'greeting'},
        ]},
        'it': {'language_name': 'Italian', 'phrases': [
            {'phrase': 'Ciao', 'translation': 'Hello', 'category': 'greeting'},
            {'phrase': 'Grazie', 'translation': 'Thank you', 'category': 'greeting'},
            {'phrase': 'Per favore', 'translation': 'Please', 'category': 'greeting'},
            {'phrase': 'Quanto costa?', 'translation': 'How much?', 'category': 'shopping'},
            {'phrase': "Dov'\u00e8...?", 'translation': 'Where is...?', 'category': 'directions'},
            {'phrase': 'Il conto, per favore', 'translation': 'The bill, please', 'category': 'restaurant'},
            {'phrase': 'Non capisco', 'translation': "I don't understand", 'category': 'general'},
            {'phrase': 'Ho bisogno di aiuto', 'translation': 'I need help', 'category': 'emergency'},
            {'phrase': 'Parla inglese?', 'translation': 'Do you speak English?', 'category': 'general'},
            {'phrase': 'Arrivederci', 'translation': 'Goodbye', 'category': 'greeting'},
        ]},
        'pt': {'language_name': 'Portuguese', 'phrases': [
            {'phrase': 'Ol\u00e1', 'translation': 'Hello', 'category': 'greeting'},
            {'phrase': 'Obrigado', 'translation': 'Thank you', 'category': 'greeting'},
            {'phrase': 'Por favor', 'translation': 'Please', 'category': 'greeting'},
            {'phrase': 'Quanto custa?', 'translation': 'How much?', 'category': 'shopping'},
            {'phrase': 'Onde fica...?', 'translation': 'Where is...?', 'category': 'directions'},
            {'phrase': 'A conta, por favor', 'translation': 'The bill, please', 'category': 'restaurant'},
            {'phrase': 'N\u00e3o entendo', 'translation': "I don't understand", 'category': 'general'},
            {'phrase': 'Preciso de ajuda', 'translation': 'I need help', 'category': 'emergency'},
            {'phrase': 'Voc\u00ea fala ingl\u00eas?', 'translation': 'Do you speak English?', 'category': 'general'},
            {'phrase': 'Tchau', 'translation': 'Goodbye', 'category': 'greeting'},
        ]},
    }
    pack = PACKS.get(language)
    if pack:
        return Response({'success': True, 'language': language, **pack})
    available = {k: v['language_name'] for k, v in PACKS.items()}
    return Response({
        'success': True, 'language': language, 'language_name': 'Unknown',
        'phrases': [], 'available_languages': available,
    })


# ─────────────────────────────────────────────────
# Subscription Endpoints
# ─────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_status(request):
    """Get the current user's subscription status and usage."""
    try:
        from .subscription_middleware import get_subscription_status
        result = get_subscription_status(request.user)
        return Response(result)
    except Exception as e:
        logger.error(f"Subscription status failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_feature_access(request):
    """Check if user can access a specific feature."""
    feature = request.data.get('feature')
    if not feature:
        return Response({'error': 'feature is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from .subscription_middleware import check_usage
        result = check_usage(request.user, feature)
        return Response(result)
    except Exception as e:
        logger.error(f"Feature check failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────
# Affiliate Endpoints
# ─────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_affiliate_link(request):
    """Generate a tracked affiliate link for a partner."""
    partner = request.data.get('partner')
    click_type = request.data.get('click_type')
    destination = request.data.get('destination', '')

    if not all([partner, click_type]):
        return Response(
            {'error': 'partner and click_type are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        from .affiliate_service import AffiliateService
        result = AffiliateService.generate_tracking_link(
            partner=partner,
            click_type=click_type,
            destination=destination,
            user=request.user,
            metadata=request.data.get('metadata'),
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Affiliate link generation failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def affiliate_report(request):
    """Get affiliate revenue report."""
    days = int(request.query_params.get('days', 30))

    try:
        from .affiliate_service import AffiliateService
        result = AffiliateService.get_revenue_report(user=request.user, days=days)
        return Response(result)
    except Exception as e:
        logger.error(f"Affiliate report failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def affiliate_partners(request):
    """Get list of available affiliate partners."""
    click_type = request.query_params.get('type')

    try:
        from .affiliate_service import AffiliateService
        partners = AffiliateService.get_available_partners(click_type=click_type)
        return Response({'success': True, 'partners': partners})
    except Exception as e:
        logger.error(f"Affiliate partners failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────
# Price Watch Endpoints
# ─────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_price_watch(request):
    """Create a new price watch alert."""
    watch_type = request.data.get('watch_type')
    search_params = request.data.get('search_params', {})
    target_price = request.data.get('target_price')

    if not all([watch_type, search_params]):
        return Response(
            {'error': 'watch_type and search_params are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        from .price_monitor import PriceMonitorService
        monitor = PriceMonitorService()
        result = monitor.create_watch(
            user=request.user,
            watch_type=watch_type,
            search_params=search_params,
            target_price=target_price,
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Create price watch failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_price_watches(request):
    """List user's active price watches."""
    try:
        from .models import PriceWatch
        watches = PriceWatch.objects.filter(user=request.user, is_active=True).order_by('-created_at')
        data = []
        for w in watches:
            data.append({
                'id': w.id,
                'watch_type': w.watch_type,
                'search_params': w.search_params,
                'target_price': float(w.target_price) if w.target_price else None,
                'current_price': float(w.current_price) if w.current_price else None,
                'lowest_price': float(w.lowest_price) if w.lowest_price else None,
                'price_history': w.price_history[-10:] if w.price_history else [],
                'created_at': w.created_at.isoformat(),
                'updated_at': w.updated_at.isoformat(),
            })
        return Response({'success': True, 'watches': data})
    except Exception as e:
        logger.error(f"List price watches failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────
# Subscription Management (Stripe)
# ─────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_subscription(request):
    """Create or upgrade a subscription via Stripe."""
    plan = request.data.get('plan', 'pro')
    payment_method_id = request.data.get('payment_method_id')

    if plan not in ('free', 'pro', 'business'):
        return Response({'error': 'Invalid plan'}, status=status.HTTP_400_BAD_REQUEST)

    # Free plan — activate directly without payment
    if plan == 'free':
        from .subscription_middleware import get_user_subscription
        sub = get_user_subscription(request.user)
        sub.plan = 'free'
        sub.status = 'active'
        sub.save(update_fields=['plan', 'status'])
        return Response({'success': True, 'plan': 'free', 'status': 'active'})

    try:
        import stripe
        from .subscription_middleware import get_user_subscription
        from django.conf import settings as s

        stripe_key = getattr(s, 'STRIPE_SECRET_KEY', '')

        # If Stripe is not configured, activate in demo mode
        if not stripe_key or stripe_key.startswith('sk_test_placeholder') or len(stripe_key) < 20:
            raise ImportError("Stripe not configured")

        stripe.api_key = stripe_key

        sub = get_user_subscription(request.user)

        # Create or retrieve Stripe customer
        if not sub.stripe_customer_id:
            customer = stripe.Customer.create(
                email=request.user.email,
                name=f"{request.user.first_name} {request.user.last_name}".strip(),
                metadata={'user_id': str(request.user.id)},
            )
            sub.stripe_customer_id = customer.id
            sub.save(update_fields=['stripe_customer_id'])
        else:
            customer = stripe.Customer.retrieve(sub.stripe_customer_id)

        # Attach payment method
        if payment_method_id:
            stripe.PaymentMethod.attach(payment_method_id, customer=customer.id)
            stripe.Customer.modify(
                customer.id,
                invoice_settings={'default_payment_method': payment_method_id},
            )

        # Price IDs should be configured in settings
        price_ids = getattr(s, 'STRIPE_PRICE_IDS', {
            'pro': 'price_pro_monthly',
            'business': 'price_business_monthly',
        })

        # Cancel existing Stripe subscription if upgrading
        if sub.stripe_subscription_id:
            try:
                stripe.Subscription.delete(sub.stripe_subscription_id)
            except Exception:
                pass

        # Create new subscription
        stripe_sub = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': price_ids.get(plan)}],
            payment_behavior='default_incomplete',
            expand=['latest_invoice.payment_intent'],
        )

        sub.plan = plan
        sub.status = 'active' if stripe_sub.status == 'active' else 'trialing'
        sub.stripe_subscription_id = stripe_sub.id
        from django.utils import timezone as tz
        from datetime import timedelta
        sub.current_period_start = tz.now()
        sub.current_period_end = tz.now() + timedelta(days=30)
        sub.save()

        return Response({
            'success': True,
            'plan': plan,
            'status': sub.status,
            'stripe_subscription_id': stripe_sub.id,
            'client_secret': getattr(
                getattr(stripe_sub.latest_invoice, 'payment_intent', None),
                'client_secret', None
            ),
        })

    except ImportError:
        # Stripe not installed — activate plan directly for demo
        from .subscription_middleware import get_user_subscription
        from django.utils import timezone as tz
        from datetime import timedelta
        sub = get_user_subscription(request.user)
        sub.plan = plan
        sub.status = 'active'
        sub.current_period_start = tz.now()
        sub.current_period_end = tz.now() + timedelta(days=30)
        sub.save()
        return Response({'success': True, 'plan': plan, 'status': 'active', 'mode': 'demo'})
    except Exception as e:
        logger.error(f"Subscription creation failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    """Handle Stripe webhook events for subscription lifecycle."""
    import json

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        import stripe
        from django.conf import settings as s
        stripe.api_key = getattr(s, 'STRIPE_SECRET_KEY', '')
        webhook_secret = getattr(s, 'STRIPE_WEBHOOK_SECRET', '')

        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            event = json.loads(payload)

        event_type = event.get('type', '') if isinstance(event, dict) else event.type
        data_obj = event.get('data', {}).get('object', {}) if isinstance(event, dict) else event.data.object

        if event_type == 'customer.subscription.updated':
            _handle_subscription_update(data_obj)
        elif event_type == 'customer.subscription.deleted':
            _handle_subscription_cancelled(data_obj)
        elif event_type == 'invoice.payment_succeeded':
            _handle_payment_success(data_obj)
        elif event_type == 'invoice.payment_failed':
            _handle_payment_failed(data_obj)

        return Response({'received': True})

    except ImportError:
        return Response({'received': True, 'mode': 'demo'})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


def _handle_subscription_update(sub_obj):
    from .models import Subscription
    try:
        sub = Subscription.objects.get(stripe_subscription_id=sub_obj.get('id', ''))
        status_val = sub_obj.get('status', 'active')
        sub.status = 'active' if status_val == 'active' else status_val
        sub.save(update_fields=['status'])
    except Subscription.DoesNotExist:
        pass


def _handle_subscription_cancelled(sub_obj):
    from .models import Subscription
    try:
        sub = Subscription.objects.get(stripe_subscription_id=sub_obj.get('id', ''))
        sub.plan = 'free'
        sub.status = 'cancelled'
        sub.stripe_subscription_id = ''
        sub.save()
    except Subscription.DoesNotExist:
        pass


def _handle_payment_success(invoice_obj):
    from .models import Subscription
    customer_id = invoice_obj.get('customer', '')
    try:
        sub = Subscription.objects.get(stripe_customer_id=customer_id)
        sub.status = 'active'
        sub.save(update_fields=['status'])
    except Subscription.DoesNotExist:
        pass


def _handle_payment_failed(invoice_obj):
    from .models import Subscription
    customer_id = invoice_obj.get('customer', '')
    try:
        sub = Subscription.objects.get(stripe_customer_id=customer_id)
        sub.status = 'past_due'
        sub.save(update_fields=['status'])
    except Subscription.DoesNotExist:
        pass


# ─────────────────────────────────────────────────
# Affiliate Redirect & Admin Dashboard
# ─────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def affiliate_redirect(request, tracking_id):
    """Redirect user through affiliate link and record the click."""
    try:
        from .models import AffiliateClick
        click = AffiliateClick.objects.get(tracking_id=tracking_id)

        # Build redirect URL from partner config
        from .affiliate_service import AFFILIATE_PARTNERS
        partner_config = AFFILIATE_PARTNERS.get(click.partner, {})
        base_url = partner_config.get('base_url', '')
        dest = click.destination or ''
        redirect_url = f"{base_url}?dest={dest}&ref={tracking_id}" if base_url else '#'

        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(redirect_url)

    except Exception:
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect('/')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def affiliate_admin_dashboard(request):
    """Admin-level affiliate revenue dashboard with detailed analytics."""
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)

    days = int(request.query_params.get('days', 30))

    try:
        from .models import AffiliateClick
        from django.db.models import Sum, Count, Avg
        from django.utils import timezone as tz

        cutoff = tz.now() - tz.timedelta(days=days)
        qs = AffiliateClick.objects.filter(clicked_at__gte=cutoff)

        total_clicks = qs.count()
        conversions = qs.filter(status='converted')
        total_revenue = conversions.aggregate(t=Sum('revenue'))['t'] or 0

        by_partner = list(qs.values('partner').annotate(
            clicks=Count('id'),
            conversions_count=Count('id', filter=models_Q(status='converted')),
            revenue=Sum('revenue'),
        ))

        by_day = list(qs.extra(select={'day': 'DATE(clicked_at)'}).values('day').annotate(
            clicks=Count('id'),
            revenue=Sum('revenue'),
        ).order_by('day'))

        top_destinations = list(qs.exclude(destination='').values('destination').annotate(
            clicks=Count('id'),
            revenue=Sum('revenue'),
        ).order_by('-clicks')[:10])

        return Response({
            'success': True,
            'period_days': days,
            'summary': {
                'total_clicks': total_clicks,
                'total_conversions': conversions.count(),
                'conversion_rate': f"{(conversions.count() / total_clicks * 100):.1f}%" if total_clicks else "0%",
                'total_revenue': float(total_revenue),
                'avg_revenue_per_conversion': float(
                    conversions.aggregate(a=Avg('revenue'))['a'] or 0
                ),
            },
            'by_partner': by_partner,
            'by_day': by_day,
            'top_destinations': top_destinations,
        })
    except Exception as e:
        logger.error(f"Admin dashboard failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def models_Q(**kwargs):
    from django.db.models import Q
    return Q(**kwargs)


# ─────────────────────────────────────────────────
# Collaborative Trip — Cost Splitting
# ─────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def collaboration_cost_split(request, collaboration_id):
    """Calculate cost splitting for a collaborative trip."""
    try:
        from .models import TripCollaboration, TripCollaborator
        from apps.itineraries.models import Itinerary

        collab = TripCollaboration.objects.get(id=collaboration_id)
        # Verify access
        is_member = (
            collab.owner == request.user
            or TripCollaborator.objects.filter(collaboration=collab, user=request.user).exists()
        )
        if not is_member:
            return Response({'error': 'Not a member'}, status=status.HTTP_403_FORBIDDEN)

        # Gather costs from itinerary
        itinerary = collab.itinerary
        total_cost = float(itinerary.estimated_budget or 0)

        # Count participants
        collaborators = list(TripCollaborator.objects.filter(
            collaboration=collab
        ).select_related('user'))
        participants = [collab.owner] + [c.user for c in collaborators]
        n = len(participants)

        per_person = total_cost / n if n > 0 else 0

        # Itemized breakdown from itinerary days — rental-aware
        item_costs = []
        category_totals = {}  # group by item_type
        if hasattr(itinerary, 'days'):
            for day in itinerary.days.all():
                for item in day.items.all():
                    if item.estimated_cost:
                        cost = float(item.estimated_cost)
                        item_info = {
                            'day': day.day_number,
                            'title': item.title,
                            'type': item.item_type,
                            'total': cost,
                        }

                        if item.item_type == 'rental':
                            # Whole-property rental: split total equally
                            item_info['split_type'] = 'equal_share'
                            item_info['per_person'] = round(cost / n, 2) if n > 0 else 0
                            item_info['note'] = 'Entire property cost split equally'
                            # Include cleaning fee if stored in item_data
                            cleaning = item.item_data.get('cleaning_fee') if hasattr(item, 'item_data') and item.item_data else None
                            if cleaning:
                                item_info['cleaning_fee'] = float(cleaning)
                                item_info['cleaning_per_person'] = round(float(cleaning) / n, 2) if n > 0 else 0
                        elif item.item_type == 'hotel':
                            room_assignments = item.item_data.get('room_assignments', {}) if hasattr(item, 'item_data') and item.item_data else {}
                            if room_assignments:
                                item_info['split_type'] = 'per_room'
                                item_info['room_assignments'] = room_assignments
                            else:
                                item_info['split_type'] = 'equal_share'
                            item_info['per_person'] = round(cost / n, 2) if n > 0 else 0
                        else:
                            item_info['split_type'] = 'equal_share'
                            item_info['per_person'] = round(cost / n, 2) if n > 0 else 0

                        item_costs.append(item_info)

                        # Accumulate by category
                        cat = item.item_type
                        if cat not in category_totals:
                            category_totals[cat] = 0
                        category_totals[cat] += cost

        cost_by_category = [
            {
                'category': cat,
                'total': round(total, 2),
                'per_person': round(total / n, 2) if n > 0 else 0,
            }
            for cat, total in category_totals.items()
        ]

        return Response({
            'success': True,
            'collaboration_id': collaboration_id,
            'total_cost': total_cost,
            'num_participants': n,
            'per_person': round(per_person, 2),
            'participants': [
                {'name': p.get_full_name() or p.email, 'share': round(per_person, 2)}
                for p in participants
            ],
            'itemized': item_costs,
            'cost_by_category': cost_by_category,
        })
    except TripCollaboration.DoesNotExist:
        return Response({'error': 'Collaboration not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Cost split failed: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────
# Real-Time Awareness / Live Context Endpoints
# ─────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def live_context(request):
    """
    Aggregated live context for a destination.

    Query Parameters:
    - destination (required): City / destination name
    - latitude (optional): float
    - longitude (optional): float
    - date (optional): YYYY-MM-DD
    - attraction (optional): attraction name for crowd detail
    """
    destination = request.query_params.get('destination')
    if not destination:
        return Response(
            {'error': 'destination query parameter is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    latitude = request.query_params.get('latitude')
    longitude = request.query_params.get('longitude')
    date = request.query_params.get('date')
    attraction = request.query_params.get('attraction')

    try:
        lat = float(latitude) if latitude else None
        lng = float(longitude) if longitude else None
    except (ValueError, TypeError):
        lat = None
        lng = None

    try:
        from .services.live_context import LiveContextService
        service = LiveContextService()
        result = service.get_live_context(
            destination=destination,
            latitude=lat,
            longitude=lng,
            date=date,
        )

        # If an attraction was specified, include its crowd detail
        if attraction:
            result['attraction_crowd_detail'] = service.get_crowd_levels(
                destination=destination,
                attraction_name=attraction,
            )

        return Response({'success': True, **result})
    except Exception as e:
        logger.error(f"Live context failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def crowd_levels_detail(request):
    """
    Hourly crowd-level heatmap for a destination or specific attraction.

    Query Parameters:
    - destination (required): City / destination name
    - attraction_name (optional): Specific attraction within the destination
    """
    destination = request.query_params.get('destination')
    if not destination:
        return Response(
            {'error': 'destination query parameter is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    attraction_name = request.query_params.get('attraction_name')

    try:
        from .services.live_context import LiveContextService
        service = LiveContextService()
        result = service.get_crowd_levels(
            destination=destination,
            attraction_name=attraction_name,
        )
        return Response({'success': True, **result})
    except Exception as e:
        logger.error(f"Crowd levels detail failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────
# Memory & Learning System
# ─────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_trip_memory(request):
    """Record a trip memory for the learning system."""
    destination = request.data.get('destination', '').strip()
    if not destination:
        return Response(
            {'error': 'destination is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    trip_date = request.data.get('trip_date')
    sentiment = request.data.get('sentiment', 'neutral')
    highlights = request.data.get('highlights', [])
    lowlights = request.data.get('lowlights', [])
    tags = request.data.get('tags', [])
    budget_spent = request.data.get('budget_spent')
    rating = request.data.get('rating', 0)
    notes = request.data.get('notes', '')

    try:
        from .services.memory_service import MemoryService
        service = MemoryService()
        memory = service.record_trip(
            user=request.user,
            destination=destination,
            trip_date=trip_date,
            sentiment=sentiment,
            highlights=highlights,
            lowlights=lowlights,
            tags=tags,
            budget_spent=budget_spent,
            rating=rating,
            notes=notes,
        )
        return Response({'success': True, 'memory': memory}, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Record trip memory failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trip_memories(request):
    """Get all trip memories for the authenticated user."""
    try:
        from .services.memory_service import MemoryService
        service = MemoryService()
        memories = service.get_trip_history(user=request.user)
        return Response({'success': True, 'memories': memories})
    except Exception as e:
        logger.error(f"Get trip memories failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def travel_insights(request):
    """Get AI-generated insights from trip history."""
    try:
        from .services.memory_service import MemoryService
        service = MemoryService()
        insights = service.generate_insights(user=request.user)
        return Response({'success': True, 'insights': insights})
    except Exception as e:
        logger.error(f"Travel insights failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def proactive_suggestions(request):
    """Get proactive destination suggestions based on travel history."""
    try:
        from .services.memory_service import MemoryService
        service = MemoryService()
        suggestions = service.get_proactive_suggestions(user=request.user)
        return Response({'success': True, 'suggestions': suggestions})
    except Exception as e:
        logger.error(f"Proactive suggestions failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def feedback_summary(request):
    """Get aggregated travel feedback summary."""
    try:
        from .services.memory_service import MemoryService
        service = MemoryService()
        summary = service.get_feedback_summary(user=request.user)
        return Response({'success': True, 'summary': summary})
    except Exception as e:
        logger.error(f"Feedback summary failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────
# Phase 4.1: Autonomous Agent Endpoints
# ─────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def flight_status_check(request):
    """Check real-time flight status and disruption recovery options."""
    flight_number = request.data.get('flight_number')
    date = request.data.get('date')
    airline = request.data.get('airline', '')

    if not flight_number or not date:
        return Response(
            {'error': 'flight_number and date are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from .services.flight_monitor import FlightMonitorAgent
        agent = FlightMonitorAgent()
        result = agent.check_flight_status(flight_number, date, airline)
        return Response({'success': True, **result})
    except Exception as e:
        logger.error(f"Flight status check failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def flight_rebooking(request):
    """Get rebooking options for disrupted flights."""
    origin = request.data.get('origin')
    destination = request.data.get('destination')
    date = request.data.get('date')

    if not all([origin, destination, date]):
        return Response(
            {'error': 'origin, destination, and date are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from .services.flight_monitor import FlightMonitorAgent
        agent = FlightMonitorAgent()
        options = agent.get_rebooking_options(
            origin=origin,
            destination=destination,
            date=date,
            original_price=float(request.data.get('original_price', 0)),
            airline_preference=request.data.get('airline_preference', ''),
        )
        return Response({'success': True, 'alternatives': options})
    except Exception as e:
        logger.error(f"Flight rebooking failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def weather_adapt(request):
    """Adapt itinerary based on weather conditions."""
    destination = request.data.get('destination')
    activities = request.data.get('activities', [])
    weather = request.data.get('weather', {})

    if not destination:
        return Response(
            {'error': 'destination is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from .services.weather_adapt import WeatherAdaptAgent

        # If no weather provided, fetch from LiveContextService
        if not weather:
            from .services.live_context import LiveContextService
            ctx_service = LiveContextService()
            weather = ctx_service.get_weather_impact(destination)

        agent = WeatherAdaptAgent()
        result = agent.adapt_itinerary(destination, activities, weather)
        result['weather'] = weather
        return Response({'success': True, **result})
    except Exception as e:
        logger.error(f"Weather adaptation failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disruption_impact(request):
    """Assess impact of a flight disruption on the trip."""
    disruption_type = request.data.get('disruption_type', 'none')
    delay_minutes = int(request.data.get('delay_minutes', 0))
    trip_items = request.data.get('trip_items', [])

    try:
        from .services.flight_monitor import FlightMonitorAgent
        agent = FlightMonitorAgent()
        result = agent.assess_disruption_impact(disruption_type, delay_minutes, trip_items)
        return Response({'success': True, **result})
    except Exception as e:
        logger.error(f"Disruption impact failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────
# Phase 4.2: Specialized Agent Endpoints
# ─────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def budget_tracker(request):
    """Track and analyze trip budget."""
    destination = request.data.get('destination')
    budget = request.data.get('budget')
    items = request.data.get('items', [])

    if not destination or budget is None:
        return Response(
            {'error': 'destination and budget are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from .services.finance_agent import FinanceAgent
        agent = FinanceAgent()
        result = agent.track_budget(destination, float(budget), items)
        return Response({'success': True, **result})
    except Exception as e:
        logger.error(f"Budget tracking failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def budget_optimizer(request):
    """Get optimal budget allocation."""
    destination = request.data.get('destination')
    budget = request.data.get('budget')
    start_date = request.data.get('start_date')
    end_date = request.data.get('end_date')
    travelers = request.data.get('travelers', 1)

    if not destination or budget is None:
        return Response(
            {'error': 'destination and budget are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from .services.finance_agent import FinanceAgent
        agent = FinanceAgent()
        result = agent.optimize_budget(
            destination, float(budget), start_date or '', end_date or '', int(travelers)
        )
        return Response({'success': True, **result})
    except Exception as e:
        logger.error(f"Budget optimization failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def etiquette_guide(request):
    """Get cultural etiquette for a destination."""
    destination = request.query_params.get('destination')
    if not destination:
        return Response(
            {'error': 'destination query parameter is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    faith = request.query_params.get('faith')

    try:
        from .services.culture_agent import CultureAgent
        agent = CultureAgent()
        result = agent.get_etiquette_guide(destination, user_faith=faith)
        return Response({'success': True, **result})
    except Exception as e:
        logger.error(f"Etiquette guide failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def local_customs(request):
    """Get local customs for a destination."""
    destination = request.query_params.get('destination')
    if not destination:
        return Response(
            {'error': 'destination query parameter is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from .services.culture_agent import CultureAgent
        agent = CultureAgent()
        result = agent.get_local_customs(destination)
        return Response({'success': True, **result})
    except Exception as e:
        logger.error(f"Local customs failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trip_health_check(request):
    """Assess health considerations for a trip."""
    destination = request.data.get('destination')
    if not destination:
        return Response(
            {'error': 'destination is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from .services.health_agent import HealthAgent
        agent = HealthAgent()
        result = agent.assess_trip_health(
            destination=destination,
            user_conditions=request.data.get('conditions', []),
            medications=request.data.get('medications', []),
            pace=request.data.get('pace', 'moderate'),
            max_walking_km=float(request.data.get('max_walking_km', 10)),
        )
        return Response({'success': True, **result})
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pacing_plan(request):
    """Generate an activity pacing plan."""
    try:
        from .services.health_agent import HealthAgent
        agent = HealthAgent()
        result = agent.generate_pacing_plan(
            activities_per_day=int(request.data.get('activities_per_day', 5)),
            max_walking_km=float(request.data.get('max_walking_km', 10)),
            pace=request.data.get('pace', 'moderate'),
            trip_days=int(request.data.get('trip_days', 1)),
        )
        return Response({'success': True, **result})
    except Exception as e:
        logger.error(f"Pacing plan failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────
# Phase 5: Monetization & Partnerships Endpoints
# ─────────────────────────────────────────────────

# --- Partner & Coupon Endpoints ---

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_partner(request):
    """Register a new partner business."""
    try:
        from .services.partnership_service import PartnershipService
        result = PartnershipService.register_partner(
            data=request.data,
            onboarded_by=request.user,
        )
        return Response(result, status=status.HTTP_201_CREATED if result.get('success') else status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Partner registration failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_coupon(request):
    """Create a coupon for a partner business."""
    try:
        from .services.partnership_service import PartnershipService
        partner_id = request.data.get('partner_id')
        if not partner_id:
            return Response({'error': 'partner_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = PartnershipService.create_coupon(
            partner_id=int(partner_id),
            data=request.data,
        )
        return Response(result, status=status.HTTP_201_CREATED if result.get('success') else status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Coupon creation failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_coupons(request):
    """List active coupons, optionally filtered by destination or category."""
    try:
        from .services.partnership_service import PartnershipService
        result = PartnershipService.get_coupons(
            destination=request.query_params.get('destination'),
            category=request.query_params.get('category'),
        )
        return Response(result)
    except Exception as e:
        logger.error(f"List coupons failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def redeem_coupon(request):
    """Redeem a coupon code."""
    try:
        from .services.partnership_service import PartnershipService
        coupon_code = request.data.get('coupon_code')
        order_total = float(request.data.get('order_total', 0))
        if not coupon_code:
            return Response({'error': 'coupon_code is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = PartnershipService.redeem_coupon(
            user=request.user,
            coupon_code=coupon_code,
            order_total=order_total,
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Coupon redemption failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_referral(request):
    """Get or create the user's referral code and stats."""
    try:
        from .services.partnership_service import PartnershipService
        # Auto-create referral code if user doesn't have one
        PartnershipService.get_or_create_referral_code(user=request.user)
        result = PartnershipService.get_referral_stats(user=request.user)
        return Response(result)
    except Exception as e:
        logger.error(f"Referral stats failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_referral(request):
    """Record a new referral invitation."""
    try:
        from .services.partnership_service import PartnershipService
        referral_code = request.data.get('referral_code')
        referred_email = request.data.get('email')
        if not referral_code or not referred_email:
            return Response({'error': 'referral_code and email are required'}, status=status.HTTP_400_BAD_REQUEST)
        result = PartnershipService.record_referral(
            referral_code=referral_code,
            referred_email=referred_email,
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Send referral failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def partner_dashboard(request):
    """Get partner business dashboard (for partner owners)."""
    try:
        from .services.partnership_service import PartnershipService
        partner_id = request.query_params.get('partner_id')
        if not partner_id:
            return Response({'error': 'partner_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = PartnershipService.get_partner_dashboard(partner_id=int(partner_id))
        return Response({'success': True, **result})
    except Exception as e:
        logger.error(f"Partner dashboard failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_savings(request):
    """Calculate revenue share: AI saved you $X -> 10% fee."""
    try:
        from .services.partnership_service import PartnershipService
        savings = float(request.data.get('savings_amount', 0))
        result = PartnershipService.calculate_revenue_share(
            user=request.user,
            savings_amount=savings,
        )
        return Response({'success': True, **result})
    except Exception as e:
        logger.error(f"Savings calculation failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- Destination Knowledge Base Endpoints ---

@api_view(['GET'])
@permission_classes([AllowAny])
def destination_knowledge(request):
    """Get comprehensive destination knowledge, generating if needed."""
    try:
        from .services.destination_kb_service import DestinationKBService
        destination = request.query_params.get('destination')
        country = request.query_params.get('country', '')
        if not destination:
            return Response({'error': 'destination parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = DestinationKBService.get_or_generate_destination(
            destination_name=destination,
            country=country,
        )
        return Response({'success': True, **result})
    except Exception as e:
        logger.error(f"Destination knowledge failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def destination_cultural_info(request):
    """Get cultural info for a destination."""
    try:
        from .services.destination_kb_service import DestinationKBService
        destination_id = request.query_params.get('destination_id')
        if not destination_id:
            return Response({'error': 'destination_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = DestinationKBService.generate_cultural_info(destination_id=int(destination_id))
        return Response({'success': True, 'cultural_info': result})
    except Exception as e:
        logger.error(f"Cultural info failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_destination_tip(request):
    """Submit a user tip for a destination (AI moderated)."""
    try:
        from .services.destination_kb_service import DestinationKBService
        destination_id = request.data.get('destination_id')
        if not destination_id:
            return Response({'error': 'destination_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = DestinationKBService.submit_user_tip(
            user=request.user,
            destination_id=int(destination_id),
            data=request.data,
        )
        return Response(result, status=status.HTTP_201_CREATED if result.get('success') else status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Submit tip failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vote_destination_tip(request):
    """Upvote or downvote a user tip."""
    try:
        from .services.destination_kb_service import DestinationKBService
        tip_id = request.data.get('tip_id')
        vote = request.data.get('vote')
        if not tip_id or vote not in ('up', 'down'):
            return Response({'error': 'tip_id and vote (up/down) are required'}, status=status.HTTP_400_BAD_REQUEST)
        result = DestinationKBService.vote_tip(
            user=request.user,
            tip_id=int(tip_id),
            vote=vote,
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Vote tip failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def search_destinations_kb(request):
    """Search the destination knowledge base."""
    try:
        from .services.destination_kb_service import DestinationKBService
        query = request.query_params.get('q', '')
        limit = int(request.query_params.get('limit', 10))
        results = DestinationKBService.search_destinations(query=query, limit=limit)
        return Response({'success': True, 'destinations': results})
    except Exception as e:
        logger.error(f"Destination search failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def destination_festivals(request):
    """Get festivals for a destination."""
    try:
        from .services.destination_kb_service import DestinationKBService
        destination = request.query_params.get('destination')
        if not destination:
            return Response({'error': 'destination parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = DestinationKBService.get_festivals(destination_name=destination)
        return Response({'success': True, **result})
    except Exception as e:
        logger.error(f"Festivals lookup failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def destination_etiquette(request):
    """Get etiquette summary for a destination."""
    try:
        from .services.destination_kb_service import DestinationKBService
        destination = request.query_params.get('destination')
        if not destination:
            return Response({'error': 'destination parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = DestinationKBService.get_etiquette_summary(destination_name=destination)
        return Response({'success': True, **result})
    except Exception as e:
        logger.error(f"Etiquette summary failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────
# Phase 6: Social & Viral Growth Endpoints
# ─────────────────────────────────────────────────

# --- Travel Story Generator ---

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_story(request):
    """Generate an AI travel story from trip data."""
    try:
        from .services.story_generator_service import StoryGeneratorService
        result = StoryGeneratorService.generate_story(user=request.user, data=request.data)
        return Response(result, status=status.HTTP_201_CREATED if result.get('success') else status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Story generation failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_social_cards(request):
    """Generate Instagram-ready story cards."""
    try:
        from .services.story_generator_service import StoryGeneratorService
        story_id = request.data.get('story_id')
        if not story_id:
            return Response({'error': 'story_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = StoryGeneratorService.generate_social_cards(story_id=int(story_id))
        return Response(result)
    except Exception as e:
        logger.error(f"Social cards generation failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_story(request, share_token):
    """Get a published story by share token."""
    try:
        from .services.story_generator_service import StoryGeneratorService
        user = request.user if getattr(request.user, 'is_authenticated', False) else None
        result = StoryGeneratorService.get_story(share_token=share_token, user=user)
        if not result.get('success'):
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        return Response(result)
    except Exception as e:
        logger.error(f"Get story failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_stories(request):
    """List current user's generated stories."""
    try:
        from .services.story_generator_service import StoryGeneratorService
        result = StoryGeneratorService.list_user_stories(user=request.user)
        return Response(result)
    except Exception as e:
        logger.error(f"List stories failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_stories(request):
    """List public published stories."""
    try:
        from .services.story_generator_service import StoryGeneratorService
        user = request.user if getattr(request.user, 'is_authenticated', False) else None
        result = StoryGeneratorService.list_public_stories(
            destination=request.query_params.get('destination'),
            format=request.query_params.get('format'),
            limit=int(request.query_params.get('limit', 20)),
            user=user,
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Public stories failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_story_like(request):
    """Toggle like on a story (accepts optional 'reaction' = 'like'|'dislike')."""
    try:
        from .services.story_generator_service import StoryGeneratorService
        story_id = request.data.get('story_id')
        reaction = request.data.get('reaction', 'like')
        if not story_id:
            return Response({'error': 'story_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = StoryGeneratorService.set_reaction(
            user=request.user, story_id=int(story_id), reaction=reaction,
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Toggle like failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def react_story(request):
    """Set a like or dislike reaction on a story."""
    try:
        from .services.story_generator_service import StoryGeneratorService
        story_id = request.data.get('story_id')
        reaction = request.data.get('reaction')
        if not story_id or reaction not in ('like', 'dislike'):
            return Response(
                {'error': "story_id and reaction ('like'|'dislike') are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = StoryGeneratorService.set_reaction(
            user=request.user, story_id=int(story_id), reaction=reaction,
        )
        return Response(result)
    except Exception as e:
        logger.error(f"React story failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_story_comment(request):
    """Add a comment to a story."""
    try:
        from .services.story_generator_service import StoryGeneratorService
        story_id = request.data.get('story_id')
        content = request.data.get('content', '').strip()
        if not story_id or not content:
            return Response({'error': 'story_id and content are required'}, status=status.HTTP_400_BAD_REQUEST)
        result = StoryGeneratorService.add_comment(user=request.user, story_id=int(story_id), content=content)
        return Response(result, status=status.HTTP_201_CREATED if result.get('success') else status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Add comment failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_story_comment(request, comment_id):
    """Delete a story comment (author only)."""
    try:
        from .services.story_generator_service import StoryGeneratorService
        result = StoryGeneratorService.delete_comment(user=request.user, comment_id=int(comment_id))
        if not result.get('success'):
            code = (
                status.HTTP_404_NOT_FOUND
                if 'not found' in (result.get('error') or '').lower()
                else status.HTTP_403_FORBIDDEN
            )
            return Response(result, status=code)
        return Response(result)
    except Exception as e:
        logger.error(f"Delete story comment failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def publish_story(request):
    """Publish a story (make it public)."""
    try:
        from .services.story_generator_service import StoryGeneratorService
        story_id = request.data.get('story_id')
        if not story_id:
            return Response({'error': 'story_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = StoryGeneratorService.publish_story(user=request.user, story_id=int(story_id))
        return Response(result)
    except Exception as e:
        logger.error(f"Publish story failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- Trip Templates & Clone ---

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_trip_template(request):
    """Create a new trip template."""
    try:
        from .services.trip_template_service import TripTemplateService
        result = TripTemplateService.create_template(user=request.user, data=request.data)
        return Response(result, status=status.HTTP_201_CREATED if result.get('success') else status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Create template failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_trip_template(request):
    """AI-generate a trip template."""
    try:
        from .services.trip_template_service import TripTemplateService
        destination = request.data.get('destination')
        if not destination:
            return Response({'error': 'destination is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = TripTemplateService.generate_template_from_ai(
            user=request.user,
            destination=destination,
            duration_days=int(request.data.get('duration_days', 3)),
            style=request.data.get('style', 'adventure'),
            budget=float(request.data.get('budget', 0)),
        )
        return Response(result, status=status.HTTP_201_CREATED if result.get('success') else status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Generate template failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def browse_templates(request):
    """Browse community trip templates."""
    try:
        from .services.trip_template_service import TripTemplateService
        user = request.user if getattr(request.user, 'is_authenticated', False) else None
        result = TripTemplateService.browse_templates(
            destination=request.query_params.get('destination'),
            style=request.query_params.get('style'),
            min_budget=float(request.query_params['min_budget']) if request.query_params.get('min_budget') else None,
            max_budget=float(request.query_params['max_budget']) if request.query_params.get('max_budget') else None,
            sort_by=request.query_params.get('sort_by', 'popular'),
            limit=int(request.query_params.get('limit', 20)),
            user=user,
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Browse templates failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_template_detail(request, template_id):
    """Get trip template details."""
    try:
        from .services.trip_template_service import TripTemplateService
        user = request.user if getattr(request.user, 'is_authenticated', False) else None
        result = TripTemplateService.get_template(template_id=int(template_id), user=user)
        if not result.get('success'):
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        return Response(result)
    except Exception as e:
        logger.error(f"Get template failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clone_template(request):
    """Clone a trip template."""
    try:
        from .services.trip_template_service import TripTemplateService
        template_id = request.data.get('template_id')
        if not template_id:
            return Response({'error': 'template_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = TripTemplateService.clone_template(
            user=request.user,
            template_id=int(template_id),
            customizations=request.data.get('customizations'),
        )
        return Response(result, status=status.HTTP_201_CREATED if result.get('success') else status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Clone template failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_template(request):
    """Toggle a like on a trip template."""
    try:
        from .services.trip_template_service import TripTemplateService
        template_id = request.data.get('template_id')
        reaction = request.data.get('reaction', 'like')
        if not template_id:
            return Response({'error': 'template_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = TripTemplateService.set_reaction(
            user=request.user, template_id=int(template_id), reaction=reaction,
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Like template failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def react_template(request):
    """Toggle like/dislike on a trip template."""
    try:
        from .services.trip_template_service import TripTemplateService
        template_id = request.data.get('template_id')
        reaction = request.data.get('reaction')
        if not template_id or reaction not in ('like', 'dislike'):
            return Response(
                {'error': "template_id and reaction ('like'|'dislike') are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = TripTemplateService.set_reaction(
            user=request.user, template_id=int(template_id), reaction=reaction,
        )
        return Response(result)
    except Exception as e:
        logger.error(f"React template failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def template_comments(request):
    """GET list_comments or POST add_comment for a template."""
    try:
        from .services.trip_template_service import TripTemplateService
        if request.method == 'GET':
            template_id = request.query_params.get('template_id')
            if not template_id:
                return Response({'error': 'template_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            result = TripTemplateService.list_comments(template_id=int(template_id))
            return Response(result)
        # POST
        if not getattr(request.user, 'is_authenticated', False):
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        template_id = request.data.get('template_id')
        content = (request.data.get('content') or '').strip()
        if not template_id or not content:
            return Response({'error': 'template_id and content are required'}, status=status.HTTP_400_BAD_REQUEST)
        result = TripTemplateService.add_comment(
            user=request.user, template_id=int(template_id), content=content,
        )
        return Response(
            result,
            status=status.HTTP_201_CREATED if result.get('success') else status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.error(f"Template comments failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_template_comment(request, comment_id):
    """Delete a template comment (author only)."""
    try:
        from .services.trip_template_service import TripTemplateService
        result = TripTemplateService.delete_comment(user=request.user, comment_id=int(comment_id))
        if not result.get('success'):
            code = (
                status.HTTP_404_NOT_FOUND
                if 'not found' in (result.get('error') or '').lower()
                else status.HTTP_403_FORBIDDEN
            )
            return Response(result, status=code)
        return Response(result)
    except Exception as e:
        logger.error(f"Delete template comment failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rate_template(request):
    """Rate a trip template."""
    try:
        from .services.trip_template_service import TripTemplateService
        template_id = request.data.get('template_id')
        rating = request.data.get('rating')
        if not template_id or rating is None:
            return Response({'error': 'template_id and rating are required'}, status=status.HTTP_400_BAD_REQUEST)
        result = TripTemplateService.rate_template(user=request.user, template_id=int(template_id), rating=float(rating))
        return Response(result)
    except Exception as e:
        logger.error(f"Rate template failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def featured_templates(request):
    """Get featured trip templates."""
    try:
        from .services.trip_template_service import TripTemplateService
        user = request.user if getattr(request.user, 'is_authenticated', False) else None
        result = TripTemplateService.get_featured_templates(
            limit=int(request.query_params.get('limit', 6)),
            user=user,
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Featured templates failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_templates(request):
    """Get current user's templates."""
    try:
        from .services.trip_template_service import TripTemplateService
        result = TripTemplateService.get_creator_templates(user=request.user)
        return Response(result)
    except Exception as e:
        logger.error(f"My templates failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- Content Hub ---

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_content(request):
    """Submit user content (photo, story, tip, etc.)."""
    try:
        from .services.content_hub_service import ContentHubService
        result = ContentHubService.submit_content(user=request.user, data=request.data)
        return Response(result, status=status.HTTP_201_CREATED if result.get('success') else status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Submit content failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def destination_content(request):
    """Get community content for a destination."""
    try:
        from .services.content_hub_service import ContentHubService
        destination = request.query_params.get('destination')
        if not destination:
            return Response({'error': 'destination parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user if getattr(request.user, 'is_authenticated', False) else None
        result = ContentHubService.get_destination_content(
            destination=destination,
            content_type=request.query_params.get('type'),
            sort_by=request.query_params.get('sort_by', 'popular'),
            limit=int(request.query_params.get('limit', 20)),
            user=user,
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Destination content failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vote_content(request):
    """Cast or toggle a vote on content. Accepts vote='up'|'down' or reaction='like'|'dislike'."""
    try:
        from .services.content_hub_service import ContentHubService
        content_id = request.data.get('content_id')
        vote = request.data.get('vote')
        reaction = request.data.get('reaction')
        if reaction in ('like', 'dislike'):
            vote = 'up' if reaction == 'like' else 'down'
        if not content_id or vote not in ('up', 'down', 'upvote', 'downvote'):
            return Response(
                {'error': "content_id and vote ('up'|'down') or reaction ('like'|'dislike') are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = ContentHubService.vote_content(user=request.user, content_id=int(content_id), vote=vote)
        return Response(result)
    except Exception as e:
        logger.error(f"Vote content failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def content_comments(request):
    """GET list_comments or POST add_comment for a content item."""
    try:
        from .services.content_hub_service import ContentHubService
        if request.method == 'GET':
            content_id = request.query_params.get('content_id')
            if not content_id:
                return Response({'error': 'content_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            result = ContentHubService.list_comments(content_id=int(content_id))
            return Response(result)
        if not getattr(request.user, 'is_authenticated', False):
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        content_id = request.data.get('content_id')
        content = (request.data.get('content') or '').strip()
        if not content_id or not content:
            return Response({'error': 'content_id and content are required'}, status=status.HTTP_400_BAD_REQUEST)
        result = ContentHubService.add_comment(
            user=request.user, content_id=int(content_id), content=content,
        )
        return Response(
            result,
            status=status.HTTP_201_CREATED if result.get('success') else status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.error(f"Content comments failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_content_comment(request, comment_id):
    """Delete a content comment (author only)."""
    try:
        from .services.content_hub_service import ContentHubService
        result = ContentHubService.delete_comment(user=request.user, comment_id=int(comment_id))
        if not result.get('success'):
            code = (
                status.HTTP_404_NOT_FOUND
                if 'not found' in (result.get('error') or '').lower()
                else status.HTTP_403_FORBIDDEN
            )
            return Response(result, status=code)
        return Response(result)
    except Exception as e:
        logger.error(f"Delete content comment failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def trending_content(request):
    """Get trending content from the past week."""
    try:
        from .services.content_hub_service import ContentHubService
        user = request.user if getattr(request.user, 'is_authenticated', False) else None
        result = ContentHubService.get_trending_content(
            limit=int(request.query_params.get('limit', 10)),
            user=user,
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Trending content failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_content(request):
    """Get current user's submitted content."""
    try:
        from .services.content_hub_service import ContentHubService
        result = ContentHubService.get_user_content(
            user=request.user,
            status=request.query_params.get('status'),
        )
        return Response(result)
    except Exception as e:
        logger.error(f"My content failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def destination_content_stats(request):
    """Get content stats for a destination."""
    try:
        from .services.content_hub_service import ContentHubService
        destination = request.query_params.get('destination')
        if not destination:
            return Response({'error': 'destination parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = ContentHubService.get_destination_stats(destination=destination)
        return Response({'success': True, **result})
    except Exception as e:
        logger.error(f"Content stats failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ──────────────────────────────────────────────────────────────────────
# Phase 7: Faith & Health Awareness
# ──────────────────────────────────────────────────────────────────────

# --- Faith Travel ---

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def prayer_times(request):
    """Get prayer times for a destination."""
    try:
        from .services.faith_service import FaithTravelService
        destination = request.query_params.get('destination')
        if not destination:
            return Response({'error': 'destination parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        date_str = request.query_params.get('date')
        result = FaithTravelService.get_prayer_times(destination=destination, date_str=date_str)
        return Response(result)
    except Exception as e:
        logger.error(f"Prayer times failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def worship_places(request):
    """Find nearby worship places."""
    try:
        from .services.faith_service import FaithTravelService
        destination = request.query_params.get('destination')
        if not destination:
            return Response({'error': 'destination parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = FaithTravelService.find_worship_places(
            destination=destination,
            faith=request.query_params.get('faith'),
            worship_type=request.query_params.get('type'),
            limit=int(request.query_params.get('limit', 10)),
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Worship places failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def spiritual_sites(request):
    """Get spiritual and religious heritage sites."""
    try:
        from .services.faith_service import FaithTravelService
        destination = request.query_params.get('destination')
        if not destination:
            return Response({'error': 'destination parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = FaithTravelService.get_spiritual_sites(
            destination=destination,
            category=request.query_params.get('category'),
            faith=request.query_params.get('faith'),
            limit=int(request.query_params.get('limit', 10)),
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Spiritual sites failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dietary_restaurants(request):
    """Find halal/kosher/vegetarian restaurants."""
    try:
        from .services.faith_service import FaithTravelService
        destination = request.query_params.get('destination')
        dietary_type = request.query_params.get('type', 'halal')
        if not destination:
            return Response({'error': 'destination parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = FaithTravelService.get_dietary_restaurants(
            destination=destination,
            dietary_type=dietary_type,
            limit=int(request.query_params.get('limit', 10)),
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Dietary restaurants failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ramadan_schedule(request):
    """Get Ramadan-aware daily schedule."""
    try:
        from .services.faith_service import FaithTravelService
        destination = request.query_params.get('destination')
        if not destination:
            return Response({'error': 'destination parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = FaithTravelService.get_ramadan_schedule(
            destination=destination,
            date_str=request.query_params.get('date'),
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Ramadan schedule failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def faith_travel_summary(request):
    """Comprehensive faith travel summary for a destination."""
    try:
        from .services.faith_service import FaithTravelService
        destination = request.query_params.get('destination')
        faith = request.query_params.get('faith')
        if not destination or not faith:
            return Response({'error': 'destination and faith parameters are required'}, status=status.HTTP_400_BAD_REQUEST)
        result = FaithTravelService.get_faith_travel_summary(destination=destination, faith=faith)
        return Response(result)
    except Exception as e:
        logger.error(f"Faith travel summary failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- Health Travel ---

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def medical_facilities(request):
    """Find nearby medical facilities."""
    try:
        from .services.health_travel_service import HealthTravelService
        destination = request.query_params.get('destination')
        if not destination:
            return Response({'error': 'destination parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = HealthTravelService.find_medical_facilities(
            destination=destination,
            facility_type=request.query_params.get('type'),
            emergency_only=request.query_params.get('emergency') == 'true',
            limit=int(request.query_params.get('limit', 10)),
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Medical facilities failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def accessibility_info(request):
    """Get accessibility info for a destination."""
    try:
        from .services.health_travel_service import HealthTravelService
        destination = request.query_params.get('destination')
        if not destination:
            return Response({'error': 'destination parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = HealthTravelService.get_accessibility_info(
            destination=destination,
            venue_type=request.query_params.get('venue_type'),
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Accessibility info failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_accessibility_rating(request):
    """Submit an accessibility rating for a venue."""
    try:
        from .services.health_travel_service import HealthTravelService
        result = HealthTravelService.submit_accessibility_rating(user=request.user, data=request.data)
        return Response(result, status=status.HTTP_201_CREATED if result.get('success') else status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Submit accessibility rating failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def medication_reminders(request):
    """Manage medication reminders (CRUD)."""
    try:
        from .services.health_travel_service import HealthTravelService
        if request.method == 'GET':
            result = HealthTravelService.manage_medication_reminders(user=request.user, action='list')
        else:
            action = request.data.get('action', 'add')
            result = HealthTravelService.manage_medication_reminders(
                user=request.user, action=action, data=request.data,
            )
        return Response(result)
    except Exception as e:
        logger.error(f"Medication reminders failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def medication_timezone_adjust(request):
    """Adjust medication schedule for a destination timezone."""
    try:
        from .services.health_travel_service import HealthTravelService
        destination_tz = request.query_params.get('timezone')
        if not destination_tz:
            return Response({'error': 'timezone parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = HealthTravelService.adjust_medications_for_trip(
            user=request.user, destination_timezone=destination_tz,
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Medication timezone adjust failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_insurance_info(request):
    """Get health insurance recommendations for a country."""
    try:
        from .services.health_travel_service import HealthTravelService
        country = request.query_params.get('country')
        if not country:
            return Response({'error': 'country parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = HealthTravelService.get_health_insurance_info(country=country)
        return Response(result)
    except Exception as e:
        logger.error(f"Health insurance info failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fatigue_itinerary(request):
    """Generate a fatigue-aware itinerary plan."""
    try:
        from .services.health_travel_service import HealthTravelService
        destination = request.query_params.get('destination')
        if not destination:
            return Response({'error': 'destination parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = HealthTravelService.get_fatigue_aware_itinerary(
            destination=destination,
            user_conditions=request.query_params.getlist('conditions'),
            max_walking_km=float(request.query_params.get('max_walking_km', 10)),
            pace=request.query_params.get('pace', 'moderate'),
            trip_days=int(request.query_params.get('days', 3)),
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Fatigue itinerary failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_travel_summary(request):
    """Comprehensive health travel summary."""
    try:
        from .services.health_travel_service import HealthTravelService
        destination = request.query_params.get('destination')
        country = request.query_params.get('country')
        if not destination:
            return Response({'error': 'destination parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = HealthTravelService.get_health_travel_summary(
            user=request.user,
            destination=destination,
            country=country or destination,
        )
        return Response(result)
    except Exception as e:
        logger.error(f"Health travel summary failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def voice_to_voice_translate(request):
    """Translate text and optionally generate speech audio."""
    try:
        text = request.data.get('text')
        source_lang = request.data.get('source_lang', 'en')
        target_lang = request.data.get('target_lang', 'es')
        if not text:
            return Response({'error': 'text is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Use existing translate logic
        import os, json
        from django.conf import settings as django_settings
        api_key = getattr(django_settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        translated = text  # fallback

        if api_key and api_key not in ('your_openai_api_key_here', ''):
            try:
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(model='gpt-4o-mini', temperature=0.2, api_key=api_key, request_timeout=30)
                response = llm.invoke(f"Translate the following from {source_lang} to {target_lang}. Return ONLY the translated text, nothing else:\n\n{text}")
                translated = response.content.strip()
            except Exception:
                pass

        # Try TTS
        audio_url = None
        if api_key and api_key not in ('your_openai_api_key_here', ''):
            try:
                import openai
                client = openai.OpenAI(api_key=api_key)
                speech = client.audio.speech.create(model='tts-1', voice='alloy', input=translated)
                import base64
                audio_b64 = base64.b64encode(speech.content).decode()
                audio_url = f"data:audio/mp3;base64,{audio_b64}"
            except Exception:
                pass

        return Response({
            'success': True,
            'original': text,
            'translated': translated,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'audio_url': audio_url,
        })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Voice-to-voice translate failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def offline_phrase_pack(request):
    """Download a phrase pack for offline use."""
    try:
        language = request.query_params.get('language', 'es')

        phrase_packs = {
            'es': {'language': 'Spanish', 'code': 'es', 'phrases': [
                {'category': 'greetings', 'original': 'Hello', 'translated': 'Hola', 'pronunciation': 'OH-lah'},
                {'category': 'greetings', 'original': 'Thank you', 'translated': 'Gracias', 'pronunciation': 'GRAH-see-ahs'},
                {'category': 'greetings', 'original': 'Please', 'translated': 'Por favor', 'pronunciation': 'por fah-VOR'},
                {'category': 'greetings', 'original': 'Excuse me', 'translated': 'Disculpe', 'pronunciation': 'dees-KOOL-peh'},
                {'category': 'greetings', 'original': 'Goodbye', 'translated': 'Adiós', 'pronunciation': 'ah-dee-OHS'},
                {'category': 'dining', 'original': 'The bill, please', 'translated': 'La cuenta, por favor', 'pronunciation': 'lah KWEN-tah por fah-VOR'},
                {'category': 'dining', 'original': 'Water', 'translated': 'Agua', 'pronunciation': 'AH-gwah'},
                {'category': 'dining', 'original': 'I am vegetarian', 'translated': 'Soy vegetariano', 'pronunciation': 'soy veh-heh-tah-ree-AH-noh'},
                {'category': 'directions', 'original': 'Where is...?', 'translated': '¿Dónde está...?', 'pronunciation': 'DON-deh ehs-TAH'},
                {'category': 'directions', 'original': 'How far?', 'translated': '¿Qué tan lejos?', 'pronunciation': 'keh tahn LEH-hohs'},
                {'category': 'emergency', 'original': 'Help!', 'translated': '¡Ayuda!', 'pronunciation': 'ah-YOO-dah'},
                {'category': 'emergency', 'original': 'I need a doctor', 'translated': 'Necesito un médico', 'pronunciation': 'neh-seh-SEE-toh oon MEH-dee-koh'},
                {'category': 'transport', 'original': 'How much does this cost?', 'translated': '¿Cuánto cuesta?', 'pronunciation': 'KWAHN-toh KWES-tah'},
                {'category': 'transport', 'original': 'Stop here', 'translated': 'Pare aquí', 'pronunciation': 'PAH-reh ah-KEE'},
            ]},
            'fr': {'language': 'French', 'code': 'fr', 'phrases': [
                {'category': 'greetings', 'original': 'Hello', 'translated': 'Bonjour', 'pronunciation': 'bohn-ZHOOR'},
                {'category': 'greetings', 'original': 'Thank you', 'translated': 'Merci', 'pronunciation': 'mehr-SEE'},
                {'category': 'greetings', 'original': 'Please', 'translated': "S'il vous plaît", 'pronunciation': 'seel voo PLEH'},
                {'category': 'greetings', 'original': 'Excuse me', 'translated': 'Excusez-moi', 'pronunciation': 'ex-koo-ZAY mwah'},
                {'category': 'greetings', 'original': 'Goodbye', 'translated': 'Au revoir', 'pronunciation': 'oh ruh-VWAHR'},
                {'category': 'dining', 'original': 'The bill, please', 'translated': "L'addition, s'il vous plaît", 'pronunciation': 'lah-dee-SYOHN seel voo PLEH'},
                {'category': 'dining', 'original': 'Water', 'translated': "De l'eau", 'pronunciation': 'duh LOH'},
                {'category': 'directions', 'original': 'Where is...?', 'translated': 'Où est...?', 'pronunciation': 'oo EH'},
                {'category': 'emergency', 'original': 'Help!', 'translated': 'Au secours!', 'pronunciation': 'oh suh-KOOR'},
                {'category': 'emergency', 'original': 'I need a doctor', 'translated': "J'ai besoin d'un médecin", 'pronunciation': 'zhay buh-ZWAHN duhn meh-duh-SAHN'},
                {'category': 'transport', 'original': 'How much does this cost?', 'translated': 'Combien ça coûte?', 'pronunciation': 'kohm-BYAHN sah KOOT'},
            ]},
            'ar': {'language': 'Arabic', 'code': 'ar', 'phrases': [
                {'category': 'greetings', 'original': 'Hello', 'translated': 'مرحبا (Marhaba)', 'pronunciation': 'MAR-ha-ba'},
                {'category': 'greetings', 'original': 'Thank you', 'translated': 'شكراً (Shukran)', 'pronunciation': 'SHOOK-ran'},
                {'category': 'greetings', 'original': 'Please', 'translated': 'من فضلك (Min fadlak)', 'pronunciation': 'min FAD-lak'},
                {'category': 'greetings', 'original': 'Peace be upon you', 'translated': 'السلام عليكم', 'pronunciation': 'as-sa-LAA-mu a-LAY-kum'},
                {'category': 'dining', 'original': 'Is this halal?', 'translated': 'هل هذا حلال؟', 'pronunciation': 'hal HAA-tha ha-LAAL'},
                {'category': 'dining', 'original': 'Water', 'translated': 'ماء (Ma)', 'pronunciation': 'MAA'},
                {'category': 'emergency', 'original': 'Help!', 'translated': 'مساعدة! (Musaada!)', 'pronunciation': 'mu-SAA-a-da'},
                {'category': 'directions', 'original': 'Where is the mosque?', 'translated': 'أين المسجد؟', 'pronunciation': 'AY-na al-MAS-jid'},
            ]},
            'ja': {'language': 'Japanese', 'code': 'ja', 'phrases': [
                {'category': 'greetings', 'original': 'Hello', 'translated': 'こんにちは (Konnichiwa)', 'pronunciation': 'kohn-NEE-chee-wah'},
                {'category': 'greetings', 'original': 'Thank you', 'translated': 'ありがとう (Arigatou)', 'pronunciation': 'ah-ree-GAH-toh'},
                {'category': 'greetings', 'original': 'Excuse me', 'translated': 'すみません (Sumimasen)', 'pronunciation': 'soo-mee-mah-SEN'},
                {'category': 'dining', 'original': 'The bill, please', 'translated': 'お会計お願いします', 'pronunciation': 'oh-KAI-keh oh-neh-GAI-shee-mahss'},
                {'category': 'emergency', 'original': 'Help!', 'translated': '助けて! (Tasukete!)', 'pronunciation': 'tah-SOO-keh-teh'},
                {'category': 'transport', 'original': 'How much?', 'translated': 'いくら? (Ikura?)', 'pronunciation': 'ee-KOO-rah'},
            ]},
            'hi': {'language': 'Hindi', 'code': 'hi', 'phrases': [
                {'category': 'greetings', 'original': 'Hello', 'translated': 'नमस्ते (Namaste)', 'pronunciation': 'nah-mah-STAY'},
                {'category': 'greetings', 'original': 'Thank you', 'translated': 'धन्यवाद (Dhanyavaad)', 'pronunciation': 'dhan-yah-VAAD'},
                {'category': 'dining', 'original': 'I am vegetarian', 'translated': 'मैं शाकाहारी हूँ', 'pronunciation': 'main SHAH-kah-hah-ree hoon'},
                {'category': 'emergency', 'original': 'Help!', 'translated': 'मदद! (Madad!)', 'pronunciation': 'MAH-dahd'},
                {'category': 'directions', 'original': 'Where is...?', 'translated': '...कहाँ है? (...kahan hai?)', 'pronunciation': 'kah-HAAN hai'},
            ]},
            'tr': {'language': 'Turkish', 'code': 'tr', 'phrases': [
                {'category': 'greetings', 'original': 'Hello', 'translated': 'Merhaba', 'pronunciation': 'mer-HA-ba'},
                {'category': 'greetings', 'original': 'Thank you', 'translated': 'Teşekkür ederim', 'pronunciation': 'teh-shek-KOOR eh-deh-REEM'},
                {'category': 'dining', 'original': 'Is this halal?', 'translated': 'Bu helal mi?', 'pronunciation': 'boo heh-LAAL mee'},
                {'category': 'emergency', 'original': 'Help!', 'translated': 'İmdat!', 'pronunciation': 'eem-DAHT'},
            ]},
        }

        pack = phrase_packs.get(language)
        if not pack:
            # Generate a minimal pack for unknown languages
            pack = {'language': language, 'code': language, 'phrases': [
                {'category': 'greetings', 'original': 'Hello', 'translated': f'[{language}] Hello', 'pronunciation': ''},
                {'category': 'greetings', 'original': 'Thank you', 'translated': f'[{language}] Thank you', 'pronunciation': ''},
                {'category': 'emergency', 'original': 'Help!', 'translated': f'[{language}] Help!', 'pronunciation': ''},
            ]}

        return Response({
            'success': True,
            'pack': pack,
            'download_ready': True,
            'total_phrases': len(pack['phrases']),
        })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Offline phrase pack failed: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ──────────────────────────────────────────────────────────────
# Collaborative Filtering (Phase 2.4 Gap Fix)
# ──────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def similar_users(request):
    """Find users with the most similar Travel DNA profiles."""
    try:
        from .services.collaborative_filter_service import CollaborativeFilterService
        limit = int(request.query_params.get('limit', 5))
        result = CollaborativeFilterService.get_similar_users(request.user, limit=limit)
        return Response(result)
    except Exception as e:
        logger.error("Similar users failed: %s", e, exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def people_like_you(request):
    """Get destination recommendations based on similar travelers."""
    try:
        from .services.collaborative_filter_service import CollaborativeFilterService
        limit = int(request.query_params.get('limit', 10))
        result = CollaborativeFilterService.get_people_like_you_recommendations(request.user, limit=limit)
        return Response(result)
    except Exception as e:
        logger.error("People-like-you failed: %s", e, exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def social_proof(request):
    """Get social proof stats for a destination."""
    try:
        from .services.collaborative_filter_service import CollaborativeFilterService
        destination = request.query_params.get('destination', '')
        if not destination:
            return Response({'error': 'destination parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = CollaborativeFilterService.get_social_proof(destination)
        return Response(result)
    except Exception as e:
        logger.error("Social proof failed: %s", e, exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def enjoyment_prediction(request):
    """Predict how much a user will enjoy a destination."""
    try:
        from .services.collaborative_filter_service import CollaborativeFilterService
        destination = request.query_params.get('destination', '')
        if not destination:
            return Response({'error': 'destination parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = CollaborativeFilterService.get_enjoyment_prediction(request.user, destination)
        return Response(result)
    except Exception as e:
        logger.error("Enjoyment prediction failed: %s", e, exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
