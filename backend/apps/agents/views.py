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

    return intel


def _synthesize_narrative(*, result, origin, destination, departure_date,
                         return_date, passengers, budget, cuisine,
                         enhanced_data=None, interests=None, travel_style=None):
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
    flight_price = 0
    hotel_price_per_night = 0
    hotel_total = 0
    car_total = 0
    try:
        rf = rec.get('recommended_flight') or {}
        flight_price = float(rf.get('price', 0) or 0)
    except (ValueError, TypeError, AttributeError):
        flight_price = 0
    try:
        rh = rec.get('recommended_hotel') or {}
        hotel_price_per_night = float(rh.get('price') or rh.get('price_per_night', 0) or 0)
        hotel_total = hotel_price_per_night * num_nights
    except (ValueError, TypeError, AttributeError):
        hotel_total = 0
    try:
        rc = rec.get('recommended_car') or {}
        car_total = float(rc.get('total_price', 0) or 0)
    except (ValueError, TypeError, AttributeError):
        car_total = 0

    known_costs_total = flight_price + hotel_total + car_total
    budget_display = f"${budget}" if budget else "flexible (no limit set)"
    budget_remaining_instruction = ""
    if budget:
        try:
            b = float(budget)
            if known_costs_total > 0:
                budget_remaining_instruction = f"Known costs so far: ${known_costs_total:.0f}. Remaining for food/activities/transport: ${max(0, b - known_costs_total):.0f}."
        except (ValueError, TypeError):
            pass

    budget_summary = (
        f"Flight cost: ${flight_price:.0f}\n"
        f"Hotel cost: ${hotel_price_per_night:.0f}/night × {num_nights} nights = ${hotel_total:.0f}\n"
        f"Car rental: ${car_total:.0f}\n"
        f"Agent estimated total: ${total_cost or 'N/A'}\n"
        f"Customer budget: {budget_display}\n"
        f"{budget_remaining_instruction}\n"
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

    # --- Determine hotel name and checkout time for prompt ---
    hotel_name_for_prompt = ''
    hotel_checkout = '11:00 AM'
    if rec.get('recommended_hotel'):
        h = rec['recommended_hotel']
        hotel_name_for_prompt = h.get('name') or h.get('hotel_name', 'the hotel')
        hotel_checkout = h.get('check_out_time', '11:00 AM') or '11:00 AM'

    prompt = f"""You are an expert Travel Planner AI creating a polished, ready-to-follow travel itinerary for a public travel website.
Write in a warm, professional, and conversational tone — like a knowledgeable travel advisor writing for a real person.
Your output will be displayed directly to travelers, so make it clear, detailed, and genuinely useful.

## YOUR DATA SOURCES (from 10+ specialized AI agents):

### Flight Details
{flight_summary}

### Hotel Details
{hotel_summary}

### Recommended Restaurants (use these EXACT names)
{restaurant_summary}

### Car Rental Options
{car_summary}

### Budget Analysis
{budget_summary}

### User Preferences
{f'Interests: {interests}' if interests else 'No specific interests.'}
{f'Travel style: {travel_style}' if travel_style else ''}
{f'Cuisine preference: {cuisine}' if cuisine else ''}

### Weather Forecast
{weather_by_day}

### Local Transportation
{transport_intel}

### Safety Information
{safety_intel}

### Local Events
{events_intel}

### Local Customs & Culture
{customs_intel}

### Must-See Attractions
{attractions_intel}

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

2. **USE REAL NAMES**: Always use the exact hotel name "{hotel_name_for_prompt}" and the exact restaurant names from search results. Never say "a local restaurant" — name specific places.

3. **REALISTIC TIME FLOW**: Every activity must have a specific time (e.g., "9:30 AM"). Times should flow logically — account for travel between locations (15-45 min), meal duration (45-90 min), and activity duration. Don't schedule 5 attractions in 3 hours.

4. **EVERY COST IS A REAL NUMBER**: Write (~$15) or (~$45/person) for every item. Never use placeholders like "$X" or "[cost]". Estimate realistically based on the destination.

5. **WEATHER-SMART**: Check the weather data for each day. Suggest indoor activities on rainy days, outdoor on sunny days. Mention the weather naturally ("It's a sunny 28°C day, perfect for...").

6. **PRACTICAL DIRECTIONS**: For each activity, briefly mention how to get there from the previous location ("a 10-minute walk" or "take the metro Line 2, about 20 minutes").

7. **DEPARTURE DAY IS COMPLETE**: The last day must include check-out, any morning activities, travel to airport with timing, and the return flight. Never end abruptly.

{'8. **TAILOR TO INTERESTS**: The traveler enjoys ' + interests + '. Prioritize activities that match these interests.' if interests else ''}

---

## OUTPUT FORMAT (follow this structure exactly):

## Trip Overview
Write 2-3 welcoming sentences about this trip. Mention the hotel name and its neighborhood, the vibe of the destination, and what makes this trip special.

## Getting Around
Recommend car rental OR public transit (pick one based on the transport data). Explain why, mention costs, and describe how to get from the airport to the hotel.

## Day 1: Arrival in {destination}
**{departure_date} · [Weather summary from data]**

[Use the actual flight departure time] - Depart on [Airline] [Flight #] from [Origin Airport] (~${flight_price:.0f})
[Use the actual flight arrival time] - Land at [Destination Airport] after a [duration] flight
[Time after landing + 30-45 min] - Head to {hotel_name_for_prompt or 'your hotel'} by [taxi/metro/bus] (~$cost)
[Time] - Check in at **{hotel_name_for_prompt or 'your hotel'}**, [address] (~${hotel_price_per_night:.0f}/night)
[Afternoon time] - [First activity — something easy near the hotel to start the trip] (~$cost)
[Evening time] - Dinner at **[Restaurant Name from search data]**, [cuisine type], [address] (~$cost/person)
**Day total: ~$[real sum]**

## Day 2: [Descriptive Title]
**[Next date] · [Weather]**

8:00 AM - Breakfast at {hotel_name_for_prompt or 'the hotel'} or a nearby café (~$cost)
[Continue with a full day of timed activities, meals at named restaurants, and practical directions]
**Day total: ~$[real sum]**

[Continue for each day — every day should have 6-10 timed entries covering morning, afternoon, and evening]

## Day {num_nights + 1}: Departure Day
**{return_date or departure_date} · [Weather]**

[Early time] - Check out of **{hotel_name_for_prompt or 'your hotel'}** (checkout by {hotel_checkout or '11:00 AM'})
[If time allows] - [Quick morning activity — café, walk, or last-minute shopping] (~$cost)
[Time] - Head to [Airport] by [transport method] (~$cost). Allow 2-3 hours before your flight.
[Time] - Return flight to {origin}, arriving at approximately [time]
**Day total: ~$[real sum]**

## Don't Miss
- [2-3 local events happening during the travel dates, or seasonal highlights]

## Good to Know
- [3-4 practical safety tips, local customs, or helpful advice for this destination]

## Packing Checklist
- [5-8 weather-specific and destination-specific items]

## Budget Summary
| Category | Cost |
|----------|------|
| Flights | ${flight_price:.0f} |
| Hotel ({num_nights} nights @ ${hotel_price_per_night:.0f}) | ${hotel_total:.0f} |
| Car Rental | ${car_total:.0f} |
| Food & Dining | $[sum all meal costs from the daily plans] |
| Local Transport | $[sum all taxi/metro/bus costs] |
| Activities & Attractions | $[sum all entry fees and tour costs] |
| **Total** | **$[sum of all rows above]** |
| Budget | {budget_display} |
| Remaining | $[budget minus total, or "Flexible" if no budget set] |

CRITICAL REMINDERS:
- Every [bracketed instruction] must be replaced with real content — never output brackets
- Budget Summary must contain REAL dollar amounts — add up the costs from your daily plans
- Fixed costs: Flights = ${flight_price:.0f}, Hotel = ${hotel_total:.0f}
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
    rec_restaurant = rec.get('recommended_restaurant', {}) or {}
    rec_car = rec.get('recommended_car', {}) or {}

    flight_price = rec_flight.get('price', 0)
    hotel_name = rec_hotel.get('name', 'your hotel')
    hotel_price = rec_hotel.get('price', 0)

    lines = []
    lines.append(f"## Trip Overview")
    lines.append(f"Your trip from {origin} to {destination} spans {num_days} days and {num_days - 1} night{'s' if num_days > 2 else ''}.")
    if hotel_name and hotel_name != 'your hotel':
        lines.append(f"You'll be staying at **{hotel_name}**.")
    lines.append("")

    # Budget summary
    total = rec.get('total_estimated_cost', 0) or 0
    hotel_total = float(hotel_price) * max(1, num_days - 1)
    lines.append(f"## Budget Summary")
    lines.append(f"| Category | Cost |")
    lines.append(f"|----------|------|")
    lines.append(f"| Flights | ${float(flight_price):.0f} |")
    lines.append(f"| Hotel ({num_days - 1} nights @ ${float(hotel_price):.0f}) | ${hotel_total:.0f} |")
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

        # Enrich query with interests/style if provided
        enriched_query = query
        if interests:
            enriched_query += f"\nUser interests: {interests}"
        if travel_style:
            enriched_query += f"\nTravel style: {travel_style}"

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
            cuisine=cuisine
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
            travel_system = get_travel_system()

            p = prev_params
            result = travel_system.run(
                user_query=f"Plan a trip from {p['origin']} to {p['destination']}",
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
                    )
                except Exception as e:
                    logger.error(f"LLM narrative failed: {e}", exc_info=True)

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
    Convert text to speech using ElevenLabs API.

    Request body:
    {
        "text": "The text to convert to speech",
        "voice_id": "optional voice ID (default: Rachel)"
    }

    Returns: audio/mpeg binary stream
    """
    import requests as http_requests

    text = request.data.get('text', '')
    if not text:
        return Response({'error': 'text is required'}, status=status.HTTP_400_BAD_REQUEST)

    api_key = settings.ELEVENLABS_API_KEY
    if not api_key:
        return Response({'error': 'ElevenLabs API key not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    voice_id = request.data.get('voice_id', '21m00Tcm4TlvDq8ikWAM')  # Rachel voice

    try:
        el_response = http_requests.post(
            f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}',
            headers={
                'Accept': 'audio/mpeg',
                'Content-Type': 'application/json',
                'xi-api-key': api_key,
            },
            json={
                'text': text[:5000],  # Limit text length
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
            logger.warning(f"ElevenLabs API error: {el_response.status_code} {el_response.text[:200]}")
            return Response(
                {'error': f'ElevenLabs API error: {el_response.status_code}'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

    except http_requests.Timeout:
        return Response({'error': 'TTS request timed out'}, status=status.HTTP_504_GATEWAY_TIMEOUT)
    except Exception as e:
        logger.error(f"TTS error: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
