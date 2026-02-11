from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import logging
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


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
