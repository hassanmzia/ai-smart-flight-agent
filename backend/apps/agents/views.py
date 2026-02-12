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
    and return their data. Each agent call is wrapped in a try/except so failures
    don't block the overall plan.
    """
    enhanced = {}

    # ── Weather (try real client first, fall back to stub) ──
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

    if 'weather' not in enhanced:
        # Use LLM general knowledge instead of the fake stub
        enhanced['weather'] = {
            'note': f'No live weather data available. Use general climate knowledge for {destination} around {departure_date}.',
            'source': 'general_knowledge'
        }

    # ── Health & Safety ──
    try:
        from .enhanced_agents import HealthSafetyAgent
        health_agent = HealthSafetyAgent.__new__(HealthSafetyAgent)
        health_agent.data_provider = __import__(
            'apps.agents.enhanced_agents', fromlist=['HealthSafetyDataProvider']
        ).HealthSafetyDataProvider()
        # Call data providers directly (no LLM needed)
        safety_data = health_agent.data_provider.get_travel_safety_score(destination)
        cdc_data = health_agent.data_provider.get_cdc_travel_health_notices(destination)
        enhanced['health_safety'] = {
            'safety_score': safety_data.get('overall_safety_score', 'N/A'),
            'crime_level': safety_data.get('crime_level', 'N/A'),
            'terrorism_threat': safety_data.get('terrorism_threat', 'N/A'),
            'political_stability': safety_data.get('political_stability', 'N/A'),
            'health_infrastructure': safety_data.get('health_infrastructure', 'N/A'),
            'emergency_numbers': safety_data.get('emergency_numbers', {}),
            'cdc_alert_level': cdc_data.get('alert_level', 'N/A'),
            'vaccinations_required': cdc_data.get('vaccinations_required', []),
            'health_recommendations': cdc_data.get('notices', []),
        }
    except Exception as e:
        logger.debug(f"Health/safety agent failed: {e}")
        enhanced['health_safety'] = {}

    # ── Visa Requirements ──
    try:
        from .enhanced_agents import VisaRequirementsAgent
        visa_agent = VisaRequirementsAgent()
        visa_data = visa_agent.get_visa_requirements(
            origin_country=origin,
            destination_country=destination,
        )
        enhanced['visa'] = {
            'visa_required': visa_data.get('visa_required', 'Check with embassy'),
            'max_stay': visa_data.get('max_stay', 'Varies'),
            'required_documents': visa_data.get('required_documents', []),
            'important_notes': visa_data.get('important_notes', []),
        }
    except Exception as e:
        logger.debug(f"Visa agent failed: {e}")
        enhanced['visa'] = {}

    # ── Packing List ──
    try:
        from .enhanced_agents import PackingListAgent
        packing_agent = PackingListAgent()
        weather_for_packing = enhanced.get('weather', {})
        packing_data = packing_agent.generate_packing_list(
            destination=destination,
            start_date=departure_date,
            end_date=return_date or departure_date,
            weather_data=weather_for_packing,
        )
        enhanced['packing'] = packing_data.get('packing_list', {})
        enhanced['packing_tips'] = packing_data.get('packing_tips', [])
    except Exception as e:
        logger.debug(f"Packing agent failed: {e}")
        enhanced['packing'] = {}

    # ── Local Expert (dining customs, cuisine info) ──
    try:
        from .enhanced_agents import EnhancedLocalExpertAgent
        local_agent = EnhancedLocalExpertAgent()
        dining_data = local_agent.get_dining_recommendations(
            city=destination,
            country=destination,  # approximate
            cuisine_preferences=[cuisine] if cuisine else None,
        )
        enhanced['local_dining'] = {
            'must_try_dishes': dining_data.get('must_try_dishes', []),
            'food_customs': dining_data.get('food_customs', []),
            'dietary_considerations': dining_data.get('dietary_considerations', {}),
            'budget_guide': dining_data.get('budget_guide', {}),
            'dining_tips': dining_data.get('tips', []),
        }
    except Exception as e:
        logger.debug(f"Local expert agent failed: {e}")
        enhanced['local_dining'] = {}

    return enhanced


def _synthesize_narrative(*, result, origin, destination, departure_date,
                         return_date, passengers, budget, cuisine,
                         enhanced_data=None):
    """Use LLM to generate a day-by-day narrative itinerary from ALL agent results."""
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage

    rec = result.get('recommendation', {})
    enhanced = enhanced_data or {}

    # ── Flight information ──
    flight_summary = ''
    if rec.get('recommended_flight'):
        f = rec['recommended_flight']
        flight_summary = (
            f"Best Flight: {f.get('airline', '')} {f.get('flight_number', '')} "
            f"from {f.get('departure_airport_code', origin)} to {f.get('arrival_airport_code', destination)}, "
            f"${f.get('price', 'N/A')}, {f.get('stops', 0)} stops, "
            f"departs {f.get('departure_time', '')}, arrives {f.get('arrival_time', '')}, "
            f"duration: {f.get('duration', 'N/A')} min, class: {f.get('travel_class', 'Economy')}"
        )
    if rec.get('alternative_flight'):
        af = rec['alternative_flight']
        flight_summary += (
            f"\nAlternative Flight: {af.get('airline', '')} {af.get('flight_number', '')} "
            f"${af.get('price', 'N/A')}, {af.get('stops', 0)} stops"
        )

    # ── Hotel information ──
    hotel_summary = ''
    if rec.get('recommended_hotel'):
        h = rec['recommended_hotel']
        hotel_summary = (
            f"Top Hotel: {h.get('name') or h.get('hotel_name', '')}, "
            f"${h.get('price') or h.get('price_per_night', 'N/A')}/night, "
            f"{h.get('stars') or h.get('star_rating', '')} stars, "
            f"address: {h.get('address', '')}"
        )
    top_hotels = rec.get('top_5_hotels', [])
    if top_hotels and len(top_hotels) > 1:
        hotel_summary += "\nOther Hotel Options:"
        for idx, h in enumerate(top_hotels[1:4], 2):
            hotel_summary += (
                f"\n  {idx}. {h.get('name') or h.get('hotel_name', '')} - "
                f"${h.get('price') or h.get('price_per_night', 'N/A')}/night, "
                f"{h.get('stars') or h.get('star_rating', '')} stars"
            )

    # ── Restaurant information ──
    restaurant_summary = ''
    if rec.get('recommended_restaurant'):
        r = rec['recommended_restaurant']
        restaurant_summary = (
            f"Top Restaurant: {r.get('name', '')}, "
            f"{r.get('cuisine_type', '')} cuisine, "
            f"${r.get('average_cost_per_person', 'N/A')}/person, "
            f"rating: {r.get('rating', 'N/A')}/5, "
            f"address: {r.get('address', '')}"
        )
    top_restaurants = rec.get('top_5_restaurants', [])
    if top_restaurants:
        restaurant_summary += "\nAll Recommended Restaurants:"
        for idx, r in enumerate(top_restaurants[:5], 1):
            restaurant_summary += (
                f"\n  {idx}. {r.get('name', '')} - {r.get('cuisine_type', '')} cuisine, "
                f"${r.get('average_cost_per_person', 'N/A')}/person, "
                f"rating: {r.get('rating', 'N/A')}/5, {r.get('address', '')}"
            )

    # ── Car rental information ──
    car_summary = ''
    if rec.get('recommended_car'):
        c = rec['recommended_car']
        car_summary = (
            f"Top Car Rental: {c.get('rental_company', '')} - {c.get('vehicle', c.get('car_type', ''))}, "
            f"${c.get('price_per_day', 'N/A')}/day, total: ${c.get('total_price', 'N/A')}, "
            f"rating: {c.get('rating', 'N/A')}"
        )
    top_cars = rec.get('top_5_cars', [])
    if top_cars and len(top_cars) > 1:
        car_summary += "\nOther Car Rental Options:"
        for idx, c in enumerate(top_cars[1:4], 2):
            car_summary += (
                f"\n  {idx}. {c.get('rental_company', '')} - {c.get('car_type', '')}, "
                f"${c.get('price_per_day', 'N/A')}/day"
            )

    # ── Budget analysis ──
    budget_summary = ''
    budget_analysis = rec.get('budget_analysis', {})
    total_cost = rec.get('total_estimated_cost')
    if total_cost:
        budget_summary = f"Total Estimated Trip Cost: ${total_cost}"
    if budget_analysis:
        cheapest = budget_analysis.get('cheapest flight', {})
        if cheapest:
            budget_summary += f"\nCheapest flight: ${cheapest.get('price', 'N/A')} ({cheapest.get('status', '')})"

    # ── Weather (from enhanced agents) ──
    weather_section = ''
    weather = enhanced.get('weather', {})
    if weather.get('source') == 'OpenWeatherMap':
        weather_section = (
            f"Current weather in {destination}: {weather.get('temperature')}, "
            f"feels like {weather.get('feels_like')}, "
            f"{weather.get('description', weather.get('condition', ''))}, "
            f"humidity: {weather.get('humidity')}, "
            f"wind: {weather.get('wind_speed')}"
        )
    else:
        weather_section = weather.get('note', f'Use general climate knowledge for {destination}.')

    # ── Health & Safety (from enhanced agents) ──
    safety_section = ''
    hs = enhanced.get('health_safety', {})
    if hs:
        safety_section = (
            f"Safety score: {hs.get('safety_score', 'N/A')}/10, "
            f"crime level: {hs.get('crime_level', 'N/A')}, "
            f"terrorism threat: {hs.get('terrorism_threat', 'N/A')}, "
            f"political stability: {hs.get('political_stability', 'N/A')}, "
            f"health infrastructure: {hs.get('health_infrastructure', 'N/A')}"
        )
        emergency = hs.get('emergency_numbers', {})
        if emergency:
            safety_section += f"\nEmergency numbers - Police: {emergency.get('police', '911')}, Ambulance: {emergency.get('ambulance', '911')}"
        vacc = hs.get('vaccinations_required', [])
        if vacc:
            safety_section += f"\nRequired vaccinations: {', '.join(vacc)}"

    # ── Visa Requirements (from enhanced agents) ──
    visa_section = ''
    visa = enhanced.get('visa', {})
    if visa:
        visa_section = (
            f"Visa: {visa.get('visa_required', 'Check with embassy')}, "
            f"max stay: {visa.get('max_stay', 'Varies')} days"
        )
        docs = visa.get('required_documents', [])
        if docs:
            visa_section += f"\nRequired documents: {', '.join(docs[:5])}"

    # ── Local Dining Culture (from enhanced agents) ──
    local_section = ''
    local = enhanced.get('local_dining', {})
    if local:
        dishes = local.get('must_try_dishes', [])
        if dishes:
            local_section += f"Must-try local dishes: {', '.join(dishes)}"
        customs = local.get('food_customs', [])
        if customs:
            local_section += f"\nDining customs: {', '.join(customs)}"
        budget_guide = local.get('budget_guide', {})
        if budget_guide:
            local_section += (
                f"\nMeal price guide - Budget: {budget_guide.get('budget_meal', 'N/A')}, "
                f"Mid-range: {budget_guide.get('mid_range_meal', 'N/A')}, "
                f"Fine dining: {budget_guide.get('fine_dining', 'N/A')}"
            )
        tips = local.get('dining_tips', [])
        if tips:
            local_section += f"\nDining tips: {'; '.join(tips)}"

    # ── Packing Suggestions (from enhanced agents) ──
    packing_section = ''
    packing = enhanced.get('packing', {})
    if packing:
        parts = []
        for category, items in packing.items():
            if items:
                parts.append(f"{category.title()}: {', '.join(items[:5])}")
        if parts:
            packing_section = '\n'.join(parts)
    packing_tips = enhanced.get('packing_tips', [])
    if packing_tips:
        packing_section += f"\nTips: {'; '.join(packing_tips)}"

    prompt = f"""Create a comprehensive, detailed day-by-day travel itinerary in markdown format.
You are an expert travel planner creating a real, actionable trip plan using data from multiple specialized AI agents.

## Trip Details
- Origin: {origin}
- Destination: {destination}
- Dates: {departure_date} to {return_date or departure_date}
- Passengers: {passengers}
- Budget: ${budget or 'flexible'}
{f'- Cuisine preference: {cuisine}' if cuisine else ''}

## Flight Options (from Flight Search Agent)
{flight_summary or 'No specific flight data available - suggest checking major airlines.'}

## Accommodation (from Hotel Search Agent)
{hotel_summary or 'No specific hotel data available - suggest checking major booking sites.'}

## Dining Options (from Restaurant Search Agent)
{restaurant_summary or 'No specific restaurant data available.'}

## Transportation (from Car Rental Agent)
{car_summary or 'No specific car rental data - suggest public transit or ride-sharing.'}

## Weather & Climate (from Weather Agent)
{weather_section}

## Health & Safety (from Health/Safety Agent)
{safety_section or f'Check travel advisories for {destination} before departure.'}

## Visa & Documents (from Visa Agent)
{visa_section or f'Check visa requirements for {destination} based on your citizenship.'}

## Local Dining Culture (from Local Expert Agent)
{local_section or f'Explore local cuisine in {destination}.'}

## Packing Recommendations (from Packing Agent)
{packing_section or 'Pack according to weather and trip duration.'}

## Budget Analysis (from Budget Evaluator Agent)
{budget_summary or 'No budget analysis available.'}

---

Please create a comprehensive day-by-day itinerary that incorporates ALL the agent data above:

1. **Trip Overview** - Brief exciting summary highlighting key experiences

2. **Day-by-day schedule** - For EACH day of the trip:
   - Morning activities with times (e.g., "8:00 AM - Breakfast at [restaurant name]")
   - Afternoon activities with times (sightseeing, tours, attractions specific to {destination})
   - Evening activities with times (dinner, entertainment, nightlife)
   - Include specific place names, famous landmarks, and popular attractions in {destination}
   - Use the restaurant data above for meal suggestions
   - Include estimated costs for each activity
   - Add transportation notes between activities
   - **Include weather-appropriate activity suggestions** (indoor activities if rain expected, etc.)

3. **Practical Tips** incorporating agent data:
   - Weather: what to expect and how to dress
   - Safety: emergency numbers, crime level, health precautions
   - Visa/documents: what to prepare
   - Local customs: tipping, dining etiquette, language tips
   - Packing essentials based on weather

4. **Budget Summary** - Complete breakdown:
   - Flights cost
   - Accommodation cost (per night x number of nights)
   - Daily food budget
   - Transportation/car rental
   - Activities and attractions
   - Total estimated trip cost vs. planned budget

Use markdown ## for day headings (e.g., "## Day 1: Arrival in {destination}").
Use specific times like "8:00 AM", "12:30 PM", "7:00 PM".
Be specific with real place names, real attractions, and real restaurant suggestions for {destination}.
This should read like a professional travel guide that considers weather, safety, and local culture."""

    model = ChatOpenAI(
        model=settings.AGENT_CONFIG.get('MODEL', 'gpt-4o-mini'),
        temperature=0.7,
        api_key=settings.OPENAI_API_KEY,
    )

    response = model.invoke([HumanMessage(content=prompt)])
    return response.content


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
                logger.warning(f"LLM narrative generation failed: {e}")
                result['itinerary_text'] = None

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
