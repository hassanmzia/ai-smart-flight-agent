import json
import os
import logging
import random
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import RiskAssessment, HealthAdvisory, SafetyAlert
from .serializers import (
    RiskAssessmentSerializer,
    HealthAdvisorySerializer,
    SafetyAlertSerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: airport code to city name
# ---------------------------------------------------------------------------

def convert_airport_to_city(location: str) -> str:
    """Convert airport codes to city names"""
    airport_to_city = {
        'LAX': 'Los Angeles',
        'JFK': 'New York',
        'LGA': 'New York',
        'ORD': 'Chicago',
        'SFO': 'San Francisco',
        'MIA': 'Miami',
        'DFW': 'Dallas',
        'SEA': 'Seattle',
        'BOS': 'Boston',
        'ATL': 'Atlanta',
        'DEN': 'Denver',
        'IAD': 'Washington',
        'LAS': 'Las Vegas',
        'PHX': 'Phoenix',
        'IAH': 'Houston',
        'MCO': 'Orlando',
        'CDG': 'Paris',
        'LHR': 'London',
        'BER': 'Berlin',
        'FCO': 'Rome',
        'NRT': 'Tokyo',
        'SYD': 'Sydney',
        'MEL': 'Melbourne',
        'DXB': 'Dubai',
        'SIN': 'Singapore',
    }
    return airport_to_city.get(location.upper(), location)


# ---------------------------------------------------------------------------
# Original function-based view (kept for backward compatibility)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([AllowAny])
def get_safety_info(request):
    """
    Get safety information and alerts for a location

    Query Parameters:
    - city: City name or airport code (required)
    - start_date: Start date of travel period (optional, format: YYYY-MM-DD)
    - end_date: End date of travel period (optional, format: YYYY-MM-DD)
    """
    try:
        city_raw = request.query_params.get('city', '')
        start_date_str = request.query_params.get('start_date', '')
        end_date_str = request.query_params.get('end_date', '')

        if not city_raw:
            return Response({
                'success': False,
                'error': 'City parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Convert airport code to city name
        city = convert_airport_to_city(city_raw)

        # Parse dates if provided
        start_date = None
        end_date = None
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Invalid start_date format. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Invalid end_date format. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Generate safety information
        safety_data = generate_safety_data(city, start_date, end_date)

        result = {
            'success': True,
            'location': city,
            **safety_data
        }

        if start_date:
            result['start_date'] = start_date.strftime('%Y-%m-%d')
        if end_date:
            result['end_date'] = end_date.strftime('%Y-%m-%d')

        return Response(result)

    except Exception as e:
        logger.error(f"Error getting safety information: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# DRF ViewSets
# ---------------------------------------------------------------------------

class RiskAssessmentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for browsing and generating risk assessments."""
    queryset = RiskAssessment.objects.all()
    serializer_class = RiskAssessmentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['destination', 'country', 'risk_level', 'ai_generated']
    search_fields = ['destination', 'country', 'summary']
    ordering_fields = ['overall_risk_score', 'last_updated']
    ordering = ['-last_updated']

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def assess(self, request):
        """
        Generate or retrieve a risk assessment for a destination.

        POST body: {"destination": "Paris", "country": "France"}
        Returns an existing recent assessment (< 7 days old) or generates a new one.
        """
        destination = request.data.get('destination', '').strip()
        country = request.data.get('country', '').strip()

        if not destination or not country:
            return Response(
                {'error': 'Both "destination" and "country" are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check for a recent assessment (updated within the last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        existing = RiskAssessment.objects.filter(
            destination__iexact=destination,
            country__iexact=country,
            last_updated__gte=seven_days_ago,
        ).first()

        if existing:
            serializer = self.get_serializer(existing)
            return Response(serializer.data)

        # Try AI generation, fall back to rule-based
        assessment_data = _generate_risk_assessment_ai(destination, country)
        if assessment_data is None:
            assessment_data = _generate_risk_assessment_rules(destination, country)

        # Upsert the assessment
        assessment, _created = RiskAssessment.objects.update_or_create(
            destination__iexact=destination,
            country__iexact=country,
            defaults={
                'destination': destination,
                'country': country,
                **assessment_data,
            },
        )

        serializer = self.get_serializer(assessment)
        return Response(serializer.data, status=status.HTTP_201_CREATED if _created else status.HTTP_200_OK)


class HealthAdvisoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for browsing and generating health advisories."""
    queryset = HealthAdvisory.objects.all()
    serializer_class = HealthAdvisorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['destination', 'country', 'water_safety', 'health_insurance_required']
    search_fields = ['destination', 'country']
    ordering_fields = ['last_updated', 'medical_facilities_rating']
    ordering = ['-last_updated']

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def check(self, request):
        """
        Generate or retrieve a health advisory for a destination.

        POST body: {"destination": "Bangkok", "country": "Thailand"}
        """
        destination = request.data.get('destination', '').strip()
        country = request.data.get('country', '').strip()

        if not destination or not country:
            return Response(
                {'error': 'Both "destination" and "country" are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check for a recent advisory (updated within the last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        existing = HealthAdvisory.objects.filter(
            destination__iexact=destination,
            country__iexact=country,
            last_updated__gte=seven_days_ago,
        ).first()

        if existing:
            serializer = self.get_serializer(existing)
            return Response(serializer.data)

        # Try AI generation, fall back to rule-based
        advisory_data = _generate_health_advisory_ai(destination, country)
        if advisory_data is None:
            advisory_data = _generate_health_advisory_rules(destination, country)

        # Upsert the advisory
        advisory, _created = HealthAdvisory.objects.update_or_create(
            destination__iexact=destination,
            country__iexact=country,
            defaults={
                'destination': destination,
                'country': country,
                **advisory_data,
            },
        )

        serializer = self.get_serializer(advisory)
        return Response(serializer.data, status=status.HTTP_201_CREATED if _created else status.HTTP_200_OK)


class SafetyAlertViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for browsing safety alerts with filtering."""
    queryset = SafetyAlert.objects.all()
    serializer_class = SafetyAlertSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['destination', 'country', 'alert_type', 'severity', 'is_active']
    search_fields = ['title', 'description', 'destination', 'country']
    ordering_fields = ['issued_at', 'severity', 'created_at']
    ordering = ['-issued_at']


# ---------------------------------------------------------------------------
# AI-powered generation helpers
# ---------------------------------------------------------------------------

def _get_openai_api_key() -> str:
    """Return the OpenAI API key if available and valid."""
    api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
    if api_key and api_key not in ('your_openai_api_key_here', ''):
        return api_key
    return ''


def _generate_risk_assessment_ai(destination: str, country: str) -> dict | None:
    """Try to generate a risk assessment using OpenAI. Returns None on failure."""
    api_key = _get_openai_api_key()
    if not api_key:
        return None

    try:
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage, SystemMessage

        model = ChatOpenAI(
            model='gpt-4o-mini',
            temperature=0.3,
            api_key=api_key,
            request_timeout=30,
        )

        response = model.invoke([
            SystemMessage(content="You are a travel risk analyst. Return valid JSON only, no markdown fences."),
            HumanMessage(content=f"""Provide a risk assessment for {destination}, {country}. Return JSON:
{{
    "overall_risk_score": <0-100 integer, higher=more risky>,
    "crime_score": <0-100>,
    "health_score": <0-100>,
    "natural_disaster_score": <0-100>,
    "political_stability_score": <0-100>,
    "terrorism_score": <0-100>,
    "risk_level": "<low|moderate|high|extreme>",
    "summary": "<2-3 sentence summary>",
    "recommendations": ["recommendation1", "recommendation2", "recommendation3"]
}}"""),
        ])

        content = response.content.strip()
        if content.startswith('```'):
            content = content.split('\n', 1)[1].rsplit('```', 1)[0].strip()
        data = json.loads(content)
        data['ai_generated'] = True

        # Clamp scores to valid range
        for field in ('overall_risk_score', 'crime_score', 'health_score',
                      'natural_disaster_score', 'political_stability_score',
                      'terrorism_score'):
            data[field] = max(0, min(100, int(data.get(field, 50))))

        if data.get('risk_level') not in ('low', 'moderate', 'high', 'extreme'):
            data['risk_level'] = 'moderate'

        return data

    except Exception as e:
        logger.warning(f"AI risk assessment failed for {destination}, {country}: {e}")
        return None


def _generate_risk_assessment_rules(destination: str, country: str) -> dict:
    """Generate a plausible rule-based risk assessment as a fallback."""
    # Simple heuristic: hash the destination name to get deterministic-ish scores
    seed = hash(f"{destination.lower()}:{country.lower()}")
    rng = random.Random(seed)

    crime_score = rng.randint(10, 55)
    health_score = rng.randint(10, 50)
    natural_disaster_score = rng.randint(5, 45)
    political_stability_score = rng.randint(5, 40)
    terrorism_score = rng.randint(5, 35)

    overall = int(
        crime_score * 0.25
        + health_score * 0.20
        + natural_disaster_score * 0.20
        + political_stability_score * 0.20
        + terrorism_score * 0.15
    )
    overall = max(0, min(100, overall))

    if overall <= 25:
        risk_level = 'low'
    elif overall <= 50:
        risk_level = 'moderate'
    elif overall <= 75:
        risk_level = 'high'
    else:
        risk_level = 'extreme'

    recommendations = [
        f"Register with your embassy before traveling to {destination}.",
        "Purchase comprehensive travel insurance covering medical evacuation.",
        "Keep copies of important documents in a separate location.",
        f"Research local customs and laws in {country} before arrival.",
        "Share your itinerary with a trusted contact back home.",
    ]

    return {
        'overall_risk_score': overall,
        'crime_score': crime_score,
        'health_score': health_score,
        'natural_disaster_score': natural_disaster_score,
        'political_stability_score': political_stability_score,
        'terrorism_score': terrorism_score,
        'risk_level': risk_level,
        'summary': (
            f"{destination}, {country} has a {risk_level} overall risk level. "
            f"Travelers should exercise standard precautions and stay informed "
            f"about local conditions."
        ),
        'recommendations': recommendations[:rng.randint(3, 5)],
        'ai_generated': False,
    }


def _generate_health_advisory_ai(destination: str, country: str) -> dict | None:
    """Try to generate a health advisory using OpenAI. Returns None on failure."""
    api_key = _get_openai_api_key()
    if not api_key:
        return None

    try:
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage, SystemMessage

        model = ChatOpenAI(
            model='gpt-4o-mini',
            temperature=0.3,
            api_key=api_key,
            request_timeout=30,
        )

        response = model.invoke([
            SystemMessage(content="You are a travel health advisor. Return valid JSON only, no markdown fences."),
            HumanMessage(content=f"""Provide a health advisory for travelers to {destination}, {country}. Return JSON:
{{
    "vaccination_requirements": ["vaccine1", "vaccine2"],
    "health_risks": [
        {{"name": "risk name", "severity": "low|moderate|high", "description": "brief description"}}
    ],
    "water_safety": "<safe|boil|bottled_only|unsafe>",
    "altitude_info": "<altitude info or empty string>",
    "medical_facilities_rating": <0-5 integer>,
    "health_insurance_required": <true|false>,
    "emergency_numbers": {{"police": "number", "ambulance": "number", "fire": "number"}},
    "nearby_hospitals": ["hospital name 1", "hospital name 2"]
}}"""),
        ])

        content = response.content.strip()
        if content.startswith('```'):
            content = content.split('\n', 1)[1].rsplit('```', 1)[0].strip()
        data = json.loads(content)

        # Validate and clamp
        data['medical_facilities_rating'] = max(0, min(5, int(data.get('medical_facilities_rating', 3))))
        if data.get('water_safety') not in ('safe', 'boil', 'bottled_only', 'unsafe'):
            data['water_safety'] = 'bottled_only'

        return data

    except Exception as e:
        logger.warning(f"AI health advisory failed for {destination}, {country}: {e}")
        return None


def _generate_health_advisory_rules(destination: str, country: str) -> dict:
    """Generate a plausible rule-based health advisory as a fallback."""
    seed = hash(f"health:{destination.lower()}:{country.lower()}")
    rng = random.Random(seed)

    water_choices = ['safe', 'boil', 'bottled_only', 'unsafe']
    water_safety = rng.choice(water_choices[:3])  # Lean towards safer options

    vaccination_pool = [
        'Routine vaccinations (MMR, DPT, Polio)',
        'Hepatitis A',
        'Hepatitis B',
        'Typhoid',
        'Yellow Fever',
        'Japanese Encephalitis',
        'Rabies',
        'Malaria prophylaxis',
    ]
    vaccinations = rng.sample(vaccination_pool, rng.randint(1, 4))

    health_risks = [
        {'name': 'Traveler\'s Diarrhea', 'severity': 'moderate',
         'description': 'Common among visitors. Practice good hygiene and drink safe water.'},
        {'name': 'Mosquito-borne Diseases', 'severity': rng.choice(['low', 'moderate']),
         'description': 'Use insect repellent and wear long sleeves at dusk and dawn.'},
        {'name': 'Sun Exposure', 'severity': 'low',
         'description': 'Apply sunscreen and stay hydrated, especially during summer months.'},
    ]

    # US cities use 911; most international destinations use 112
    us_cities = {
        'Los Angeles', 'New York', 'Chicago', 'Miami', 'Dallas', 'Seattle',
        'Boston', 'Atlanta', 'Denver', 'Washington', 'Las Vegas', 'Phoenix',
        'Houston', 'Orlando', 'San Francisco',
    }
    if destination in us_cities:
        emergency = {'police': '911', 'ambulance': '911', 'fire': '911'}
    else:
        emergency = {'police': '112', 'ambulance': '112', 'fire': '112'}

    return {
        'vaccination_requirements': vaccinations,
        'health_risks': health_risks[:rng.randint(2, 3)],
        'water_safety': water_safety,
        'altitude_info': '',
        'medical_facilities_rating': rng.randint(2, 5),
        'health_insurance_required': rng.choice([True, False]),
        'emergency_numbers': emergency,
        'nearby_hospitals': [
            f'{destination} General Hospital',
            f'{destination} Medical Center',
        ],
    }


# ---------------------------------------------------------------------------
# Legacy mock data generators (used by the original get_safety_info view)
# ---------------------------------------------------------------------------

def generate_safety_data(city: str, start_date=None, end_date=None) -> dict:
    """Generate safety information and alerts for a city"""

    # Overall safety rating
    safety_ratings = ['Very Safe', 'Safe', 'Moderately Safe', 'Exercise Caution']
    overall_rating = random.choice(safety_ratings[:3])  # Most cities are safe

    # Safety score (0-100)
    safety_score = random.randint(65, 95)

    # Current alerts
    active_alerts = generate_active_alerts(city)

    # Emergency contacts
    emergency_contacts = {
        'police': '911' if city in ['Los Angeles', 'New York', 'Chicago', 'Miami', 'Dallas', 'Seattle', 'Boston', 'Atlanta', 'Denver', 'Washington', 'Las Vegas', 'Phoenix', 'Houston', 'Orlando'] else '112',
        'ambulance': '911' if city in ['Los Angeles', 'New York', 'Chicago', 'Miami', 'Dallas', 'Seattle', 'Boston', 'Atlanta', 'Denver', 'Washington', 'Las Vegas', 'Phoenix', 'Houston', 'Orlando'] else '112',
        'fire': '911' if city in ['Los Angeles', 'New York', 'Chicago', 'Miami', 'Dallas', 'Seattle', 'Boston', 'Atlanta', 'Denver', 'Washington', 'Las Vegas', 'Phoenix', 'Houston', 'Orlando'] else '112',
        'tourist_police': f'{city} Tourist Police Hotline',
        'embassy': 'Contact your embassy',
    }

    # Safety tips
    safety_tips = generate_safety_tips(city)

    # Areas to avoid
    areas_to_avoid = generate_areas_to_avoid(city)

    # Safe areas
    safe_areas = generate_safe_areas(city)

    # Transportation safety
    transportation_safety = {
        'public_transport': {
            'rating': random.choice(['Very Safe', 'Safe', 'Moderately Safe']),
            'tips': [
                'Use official taxi services or ride-sharing apps',
                'Keep valuables secure on public transport',
                'Be aware of your surroundings, especially at night'
            ]
        },
        'walking': {
            'rating': random.choice(['Very Safe', 'Safe', 'Moderately Safe']),
            'tips': [
                'Stick to well-lit main streets at night',
                'Walk in groups when possible',
                'Use pedestrian crossings'
            ]
        }
    }

    # Health and medical
    health_info = {
        'tap_water': random.choice(['Safe to drink', 'Bottled water recommended', 'Boil before drinking']),
        'vaccinations_required': random.choice([[], ['COVID-19'], ['COVID-19', 'Routine vaccinations']]),
        'hospitals': f'{random.randint(5, 20)} major hospitals',
        'pharmacies': 'Widely available',
        'air_quality': random.choice(['Good', 'Moderate', 'Fair']),
    }

    # Local laws and customs
    local_laws = generate_local_laws(city)

    # Travel advisories
    travel_advisory = {
        'level': random.choice(['Level 1 - Exercise Normal Precautions', 'Level 2 - Exercise Increased Caution']),
        'last_updated': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
        'summary': f'Exercise standard safety precautions when visiting {city}.'
    }

    return {
        'overall_rating': overall_rating,
        'safety_score': safety_score,
        'active_alerts': active_alerts,
        'emergency_contacts': emergency_contacts,
        'safety_tips': safety_tips,
        'areas_to_avoid': areas_to_avoid,
        'safe_areas': safe_areas,
        'transportation_safety': transportation_safety,
        'health_info': health_info,
        'local_laws': local_laws,
        'travel_advisory': travel_advisory,
    }


def generate_active_alerts(city: str) -> list:
    """Generate active safety alerts"""
    alerts = []

    alert_templates = [
        {
            'type': 'weather',
            'severity': 'low',
            'icon': '🌧️',
            'title': 'Weather Advisory',
            'message': 'Rain expected this week. Carry an umbrella.',
        },
        {
            'type': 'event',
            'severity': 'low',
            'icon': '🎉',
            'title': 'Major Event',
            'message': 'Large festival this weekend. Expect increased crowds.',
        },
        {
            'type': 'traffic',
            'severity': 'medium',
            'icon': '🚗',
            'title': 'Traffic Alert',
            'message': 'Road construction on main highway. Plan extra travel time.',
        },
    ]

    # Add 1-3 random alerts
    num_alerts = random.randint(1, 3)
    alerts = random.sample(alert_templates, num_alerts)

    for alert in alerts:
        alert['issued_at'] = (datetime.now() - timedelta(hours=random.randint(1, 48))).strftime('%Y-%m-%d %H:%M')

    return alerts


def generate_safety_tips(city: str) -> list:
    """Generate safety tips for travelers"""
    tips = [
        {
            'icon': '🎒',
            'title': 'Keep Valuables Secure',
            'description': 'Use hotel safes and avoid displaying expensive items in public.'
        },
        {
            'icon': '📱',
            'title': 'Stay Connected',
            'description': 'Keep your phone charged and share your itinerary with family.'
        },
        {
            'icon': '🗺️',
            'title': 'Know Your Location',
            'description': 'Keep hotel address and emergency contacts saved in your phone.'
        },
        {
            'icon': '💳',
            'title': 'Protect Your Cards',
            'description': 'Use credit cards over cash and notify your bank of travel plans.'
        },
        {
            'icon': '🚕',
            'title': 'Use Licensed Transport',
            'description': 'Only use official taxis or verified ride-sharing services.'
        },
        {
            'icon': '👥',
            'title': 'Travel in Groups',
            'description': 'Especially at night, avoid walking alone in unfamiliar areas.'
        },
    ]

    return tips


def generate_areas_to_avoid(city: str) -> list:
    """Generate list of areas to avoid"""
    areas = [
        f'{city} Industrial Zone - Limited lighting at night',
        f'Remote outskirts - Better to stick to tourist areas',
    ]
    return random.sample(areas, random.randint(1, 2))


def generate_safe_areas(city: str) -> list:
    """Generate list of safe areas"""
    areas = [
        'Downtown/City Center - Well-patrolled and tourist-friendly',
        'Hotel Districts - Safe and well-lit',
        'Tourist Attractions - High security presence',
        'Shopping Districts - Active day and night',
        'Waterfront Areas - Popular and monitored',
    ]
    return random.sample(areas, random.randint(3, 5))


def generate_local_laws(city: str) -> list:
    """Generate important local laws and customs"""
    laws = [
        {
            'icon': '🚭',
            'title': 'Smoking Regulations',
            'description': 'Smoking prohibited in most public indoor spaces.'
        },
        {
            'icon': '🍺',
            'title': 'Alcohol Laws',
            'description': 'Drinking age restrictions apply. No open containers in public.'
        },
        {
            'icon': '📸',
            'title': 'Photography Rules',
            'description': 'Ask permission before photographing people or private property.'
        },
        {
            'icon': '👔',
            'title': 'Dress Code',
            'description': 'Dress modestly when visiting religious sites.'
        },
        {
            'icon': '🚦',
            'title': 'Traffic Laws',
            'description': 'Follow local traffic rules. Jaywalking may be prohibited.'
        },
    ]

    return random.sample(laws, random.randint(3, 5))
