from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import logging
from datetime import datetime, timedelta
import random

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
def search_events(request):
    """
    Search for local events and festivals

    Query Parameters:
    - city: City name or airport code (required)
    - start_date: Start date YYYY-MM-DD (optional)
    - end_date: End date YYYY-MM-DD (optional)
    - category: Event category (optional): music, arts, food, sports, cultural, festivals
    """
    try:
        city_raw = request.query_params.get('city', '')
        start_date_str = request.query_params.get('start_date', '')
        end_date_str = request.query_params.get('end_date', '')
        category = request.query_params.get('category', '')

        if not city_raw:
            return Response({
                'success': False,
                'error': 'City parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Convert airport code to city name
        city = convert_airport_to_city(city_raw)

        # Parse dates
        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            else:
                start_date = datetime.now()

            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            else:
                end_date = start_date + timedelta(days=30)
        except ValueError:
            return Response({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Generate sample events
        events = generate_sample_events(city, start_date, end_date, category)

        return Response({
            'success': True,
            'results': events,
            'total': len(events),
            'location': city,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        })

    except Exception as e:
        logger.error(f"Error searching events: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def generate_sample_events(city: str, start_date: datetime, end_date: datetime, category: str = '') -> list:
    """Generate sample events and festivals data"""

    event_templates = {
        'music': [
            {'name': 'Summer Music Festival', 'icon': '🎵', 'duration': 3},
            {'name': 'Jazz in the Park', 'icon': '🎷', 'duration': 1},
            {'name': 'Rock Concert Series', 'icon': '🎸', 'duration': 1},
            {'name': 'Classical Symphony Night', 'icon': '🎻', 'duration': 1},
            {'name': 'Live Music Weekend', 'icon': '🎤', 'duration': 2},
        ],
        'arts': [
            {'name': 'Art Gallery Opening', 'icon': '🎨', 'duration': 1},
            {'name': 'Street Art Festival', 'icon': '🖼️', 'duration': 2},
            {'name': 'Photography Exhibition', 'icon': '📸', 'duration': 7},
            {'name': 'Theater Performance', 'icon': '🎭', 'duration': 1},
            {'name': 'Film Festival', 'icon': '🎬', 'duration': 5},
        ],
        'food': [
            {'name': 'Food Truck Festival', 'icon': '🍔', 'duration': 2},
            {'name': 'Wine & Cheese Tasting', 'icon': '🍷', 'duration': 1},
            {'name': 'Street Food Market', 'icon': '🌮', 'duration': 1},
            {'name': 'Farmers Market', 'icon': '🥬', 'duration': 1},
            {'name': 'International Food Fair', 'icon': '🍱', 'duration': 3},
        ],
        'sports': [
            {'name': 'Marathon Run', 'icon': '🏃', 'duration': 1},
            {'name': 'Championship Game', 'icon': '⚽', 'duration': 1},
            {'name': 'Tennis Tournament', 'icon': '🎾', 'duration': 7},
            {'name': 'Cycling Race', 'icon': '🚴', 'duration': 1},
            {'name': 'Extreme Sports Show', 'icon': '🏂', 'duration': 2},
        ],
        'cultural': [
            {'name': 'Heritage Day Celebration', 'icon': '🎊', 'duration': 1},
            {'name': 'Cultural Dance Festival', 'icon': '💃', 'duration': 2},
            {'name': 'Traditional Crafts Fair', 'icon': '🎎', 'duration': 3},
            {'name': 'Historical Reenactment', 'icon': '🏛️', 'duration': 1},
            {'name': 'Lantern Festival', 'icon': '🏮', 'duration': 1},
        ],
        'festivals': [
            {'name': 'City Summer Festival', 'icon': '🎉', 'duration': 5},
            {'name': 'Carnival Celebration', 'icon': '🎪', 'duration': 7},
            {'name': 'Fireworks Festival', 'icon': '🎆', 'duration': 1},
            {'name': 'Cherry Blossom Festival', 'icon': '🌸', 'duration': 14},
            {'name': 'Harvest Festival', 'icon': '🌾', 'duration': 3},
        ]
    }

    # Select templates based on category
    if category and category in event_templates:
        templates = event_templates[category]
    else:
        # Mix events from all categories
        templates = []
        for cat_templates in event_templates.values():
            templates.extend(cat_templates[:2])  # Take 2 from each category

    events = []
    days_range = (end_date - start_date).days

    # Generate events
    num_events = min(random.randint(8, 15), days_range // 2)

    for i in range(num_events):
        template = random.choice(templates)

        # Random date within range
        days_offset = random.randint(0, max(0, days_range - template['duration']))
        event_date = start_date + timedelta(days=days_offset)
        end_event_date = event_date + timedelta(days=template['duration'] - 1)

        # Detect category from template
        event_category = 'general'
        for cat, cat_templates in event_templates.items():
            if template in cat_templates:
                event_category = cat
                break

        # Generate price
        price_ranges = ['free', '$', '$$', '$$$']
        price_range = random.choice(price_ranges)

        if price_range == 'free':
            ticket_price = 0
        elif price_range == '$':
            ticket_price = random.randint(10, 25)
        elif price_range == '$$':
            ticket_price = random.randint(30, 60)
        else:
            ticket_price = random.randint(75, 150)

        # Generate venue
        venues = [
            'City Center Plaza',
            'Central Park',
            'Convention Center',
            'Downtown Square',
            'Riverside Amphitheater',
            'Cultural Center',
            'Memorial Hall',
            'Exhibition Grounds',
            'Sports Stadium',
            'Community Theater'
        ]

        events.append({
            'name': f"{city} {template['name']}",
            'category': event_category,
            'icon': template['icon'],
            'start_date': event_date.strftime('%Y-%m-%d'),
            'end_date': end_event_date.strftime('%Y-%m-%d'),
            'is_multi_day': template['duration'] > 1,
            'duration_days': template['duration'],
            'venue': random.choice(venues),
            'description': f"Join us for an amazing {template['name'].lower()} in {city}. Don't miss this exciting event!",
            'price_range': price_range,
            'ticket_price': ticket_price,
            'expected_attendance': random.randint(100, 10000),
            'organizer': f"{city} Events Committee",
            'website': f"https://events.{city.lower().replace(' ', '')}.com",
            'tags': get_event_tags(event_category),
            'rating': round(random.uniform(3.5, 5.0), 1),
            'review_count': random.randint(10, 500)
        })

    # Sort by date
    events.sort(key=lambda x: x['start_date'])

    return events


def get_event_tags(category: str) -> list:
    """Get relevant tags for event category"""
    tag_map = {
        'music': ['live music', 'entertainment', 'concert', 'performance'],
        'arts': ['culture', 'art', 'exhibition', 'creative'],
        'food': ['culinary', 'tasting', 'local food', 'gastronomy'],
        'sports': ['athletic', 'competition', 'outdoor', 'active'],
        'cultural': ['tradition', 'heritage', 'community', 'celebration'],
        'festivals': ['celebration', 'family-friendly', 'outdoor', 'entertainment']
    }
    base_tags = tag_map.get(category, ['event', 'local'])
    return random.sample(base_tags, min(3, len(base_tags)))
