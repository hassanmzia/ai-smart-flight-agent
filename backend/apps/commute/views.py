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
def get_commute_info(request):
    """
    Get commute and traffic information for a location

    Query Parameters:
    - city: City name or airport code (required)
    """
    try:
        city_raw = request.query_params.get('city', '')

        if not city_raw:
            return Response({
                'success': False,
                'error': 'City parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Convert airport code to city name
        city = convert_airport_to_city(city_raw)

        # Generate commute information
        commute_data = generate_commute_data(city)

        return Response({
            'success': True,
            'location': city,
            **commute_data
        })

    except Exception as e:
        logger.error(f"Error getting commute information: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def generate_commute_data(city: str) -> dict:
    """Generate commute and traffic information for a city"""

    # Current traffic conditions
    traffic_conditions = generate_current_traffic(city)

    # Public transportation options
    public_transport = generate_public_transport_options(city)

    # Peak hours
    peak_hours = {
        'morning': {
            'start': '7:00 AM',
            'end': '9:30 AM',
            'severity': random.choice(['Heavy', 'Moderate', 'Light']),
        },
        'evening': {
            'start': '4:30 PM',
            'end': '7:00 PM',
            'severity': random.choice(['Heavy', 'Moderate', 'Light']),
        }
    }

    # Major routes and highways
    major_routes = generate_major_routes(city)

    # Traffic incidents
    current_incidents = generate_traffic_incidents(city)

    # Average commute times from city center
    commute_times = {
        'airport': {
            'public_transport': f"{random.randint(30, 60)} min",
            'driving': f"{random.randint(20, 45)} min",
            'taxi': f"{random.randint(25, 50)} min",
        },
        'downtown_to_suburbs': {
            'public_transport': f"{random.randint(35, 70)} min",
            'driving': f"{random.randint(25, 50)} min",
        },
        'cross_city': {
            'public_transport': f"{random.randint(45, 90)} min",
            'driving': f"{random.randint(30, 60)} min",
        }
    }

    # Parking information
    parking_info = {
        'availability': random.choice(['Limited', 'Moderate', 'Abundant']),
        'average_cost_hourly': f"${random.randint(3, 15)}/hour",
        'average_cost_daily': f"${random.randint(15, 45)}/day",
        'recommendations': [
            'Use park-and-ride facilities near transit stations',
            'Book parking in advance for popular areas',
            'Consider street parking with time limits',
            'Check for early bird specials at parking garages'
        ]
    }

    # Traffic patterns by day
    traffic_patterns = generate_traffic_patterns()

    # Commute tips
    commute_tips = [
        {
            'icon': '🚇',
            'title': 'Use Public Transit',
            'description': 'Often faster and more reliable during peak hours.'
        },
        {
            'icon': '📱',
            'title': 'Check Live Traffic',
            'description': 'Use navigation apps for real-time traffic updates.'
        },
        {
            'icon': '🚴',
            'title': 'Consider Alternatives',
            'description': 'Bike-sharing or walking for short distances.'
        },
        {
            'icon': '🕐',
            'title': 'Travel Off-Peak',
            'description': 'Avoid rush hours when possible to save time.'
        },
        {
            'icon': '🎫',
            'title': 'Get Transit Pass',
            'description': 'Day or week passes often cheaper than single tickets.'
        },
        {
            'icon': '🗺️',
            'title': 'Plan Your Route',
            'description': 'Know your options before you travel.'
        },
    ]

    # Road conditions and construction
    road_conditions = {
        'overall': random.choice(['Good', 'Fair', 'Poor']),
        'active_construction': random.randint(3, 15),
        'major_closures': random.randint(0, 3),
        'detour_info': 'Check local traffic authority for latest updates'
    }

    return {
        'traffic_conditions': traffic_conditions,
        'public_transport': public_transport,
        'peak_hours': peak_hours,
        'major_routes': major_routes,
        'current_incidents': current_incidents,
        'commute_times': commute_times,
        'parking_info': parking_info,
        'traffic_patterns': traffic_patterns,
        'commute_tips': commute_tips,
        'road_conditions': road_conditions,
    }


def generate_current_traffic(city: str) -> dict:
    """Generate current traffic conditions"""
    conditions = ['Light', 'Moderate', 'Heavy', 'Very Heavy']
    current_condition = random.choice(conditions)

    # Traffic level (0-100)
    traffic_level = random.randint(30, 85)

    return {
        'current_condition': current_condition,
        'traffic_level': traffic_level,
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'description': f"Traffic is currently {current_condition.lower()} in {city}.",
    }


def generate_public_transport_options(city: str) -> list:
    """Generate public transportation options"""
    transport_types = [
        {
            'type': 'Metro/Subway',
            'icon': '🚇',
            'availability': 'Extensive network',
            'frequency': '3-8 minutes',
            'operating_hours': '5:00 AM - 1:00 AM',
            'fare': f"${random.uniform(2.5, 4.5):.2f}",
            'coverage': 'City-wide',
        },
        {
            'type': 'Bus',
            'icon': '🚌',
            'availability': 'Comprehensive routes',
            'frequency': '10-20 minutes',
            'operating_hours': '24/7 on major routes',
            'fare': f"${random.uniform(2.0, 3.5):.2f}",
            'coverage': 'City-wide and suburbs',
        },
        {
            'type': 'Light Rail/Tram',
            'icon': '🚊',
            'availability': 'Selected routes',
            'frequency': '8-15 minutes',
            'operating_hours': '6:00 AM - 11:00 PM',
            'fare': f"${random.uniform(2.5, 4.0):.2f}",
            'coverage': 'Central areas',
        },
        {
            'type': 'Commuter Rail',
            'icon': '🚆',
            'availability': 'Suburban connections',
            'frequency': '15-30 minutes',
            'operating_hours': '5:30 AM - 12:00 AM',
            'fare': f"${random.uniform(5.0, 12.0):.2f}",
            'coverage': 'City to suburbs',
        },
        {
            'type': 'Taxi/Ride Share',
            'icon': '🚕',
            'availability': 'On-demand',
            'frequency': 'Immediate',
            'operating_hours': '24/7',
            'fare': 'Variable by distance',
            'coverage': 'City-wide',
        },
    ]

    # Return 3-5 random transport options
    return random.sample(transport_types, random.randint(3, 5))


def generate_major_routes(city: str) -> list:
    """Generate major routes and highways"""
    route_prefixes = ['I-', 'Route ', 'Highway ', 'Expressway ']
    route_numbers = [random.randint(1, 99) for _ in range(5)]

    routes = []
    for i in range(random.randint(4, 6)):
        prefix = random.choice(route_prefixes)
        number = random.choice(route_numbers)
        condition = random.choice(['Clear', 'Moderate traffic', 'Heavy traffic', 'Slow moving'])

        routes.append({
            'name': f"{prefix}{number}",
            'description': f"Major {random.choice(['north-south', 'east-west', 'ring'])} route",
            'current_condition': condition,
            'average_speed': f"{random.randint(25, 65)} mph",
        })

    return routes


def generate_traffic_incidents(city: str) -> list:
    """Generate current traffic incidents"""
    incident_types = [
        {'type': 'Accident', 'icon': '🚗', 'severity': 'high'},
        {'type': 'Road Work', 'icon': '🚧', 'severity': 'medium'},
        {'type': 'Lane Closure', 'icon': '⚠️', 'severity': 'medium'},
        {'type': 'Disabled Vehicle', 'icon': '🔧', 'severity': 'low'},
        {'type': 'Heavy Volume', 'icon': '🚦', 'severity': 'medium'},
    ]

    incidents = []
    num_incidents = random.randint(2, 5)

    for i in range(num_incidents):
        incident = random.choice(incident_types)
        routes = ['I-', 'Route ', 'Highway ']
        route_num = random.randint(1, 99)

        incidents.append({
            'type': incident['type'],
            'icon': incident['icon'],
            'severity': incident['severity'],
            'location': f"{random.choice(routes)}{route_num} near {random.choice(['Exit', 'Mile marker'])} {random.randint(1, 50)}",
            'description': f"{incident['type']} causing delays",
            'reported': f"{random.randint(5, 60)} minutes ago",
            'estimated_clearance': f"{random.randint(15, 90)} minutes",
        })

    return incidents


def generate_traffic_patterns() -> dict:
    """Generate typical traffic patterns by day of week"""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    patterns = {}

    for day in days:
        if day in ['Saturday', 'Sunday']:
            severity = random.choice(['Light', 'Moderate'])
        else:
            severity = random.choice(['Moderate', 'Heavy'])

        patterns[day] = {
            'morning_rush': severity,
            'midday': 'Light' if day in ['Saturday', 'Sunday'] else 'Moderate',
            'evening_rush': severity,
            'typical_description': f"Typically {severity.lower()} traffic on {day}s"
        }

    return patterns
