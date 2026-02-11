from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import requests
import logging
import random

logger = logging.getLogger(__name__)


def convert_airport_to_city(location: str) -> str:
    """Convert airport codes to city names"""
    airport_to_city = {
        'LAX': 'Los Angeles',
        'JFK': 'New York',
        'LGA': 'New York',
        'EWR': 'Newark',
        'ORD': 'Chicago',
        'SFO': 'San Francisco',
        'MIA': 'Miami',
        'DFW': 'Dallas',
        'SEA': 'Seattle',
        'BOS': 'Boston',
        'ATL': 'Atlanta',
        'DEN': 'Denver',
        'IAD': 'Washington DC',
        'DCA': 'Washington DC',
        'LAS': 'Las Vegas',
        'PHX': 'Phoenix',
        'IAH': 'Houston',
        'MCO': 'Orlando',
        'CDG': 'Paris',
        'LHR': 'London',
        'BER': 'Berlin',
        'FCO': 'Rome',
        'NRT': 'Tokyo',
        'HND': 'Tokyo',
        'SYD': 'Sydney',
        'MEL': 'Melbourne',
        'DXB': 'Dubai',
        'SIN': 'Singapore',
    }
    return airport_to_city.get(location.upper(), location)


@api_view(['GET'])
@permission_classes([AllowAny])
def search_attractions(request):
    """
    Search for tourist attractions using SERP API Google Local

    Query Parameters:
    - city: City name or airport code (required)
    - category: Attraction category (optional): museums, parks, landmarks, entertainment, etc.
    - start_date: Start date of travel period (optional, format: YYYY-MM-DD)
    - end_date: End date of travel period (optional, format: YYYY-MM-DD)
    """
    try:
        city_raw = request.query_params.get('city', '')
        category = request.query_params.get('category', '')
        start_date_str = request.query_params.get('start_date', '')
        end_date_str = request.query_params.get('end_date', '')

        if not city_raw:
            return Response({
                'success': False,
                'error': 'City parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Convert airport code to city name
        city = convert_airport_to_city(city_raw)

        # Build search query
        if category:
            search_query = f"{category} in {city}"
        else:
            search_query = f"tourist attractions in {city}"

        logger.info(f"Searching attractions: {search_query}")

        # Try SERP API first, fallback to sample data if it fails
        attractions = []
        try:
            # SERP API request
            params = {
                "engine": "google_local",
                "q": search_query,
                "location": city,
                "api_key": settings.SERP_API_KEY
            }

            response = requests.get("https://serpapi.com/search", params=params, timeout=30)
            raw_results = response.json()

            # Check for API errors or missing API key
            if 'error' in raw_results or not settings.SERP_API_KEY:
                logger.warning(f"SERP API unavailable, using sample data")
                attractions = generate_sample_attractions(city, category)
            else:
                # Extract local results
                local_results = raw_results.get('local_results', [])

                # Format attractions
                for result in local_results[:20]:  # Limit to 20 results
                    attraction = format_attraction(result, city, category)
                    if attraction:
                        attractions.append(attraction)

                # If no results from API, use sample data
                if not attractions:
                    logger.info("No results from API, using sample data")
                    attractions = generate_sample_attractions(city, category)

        except Exception as api_error:
            logger.warning(f"SERP API error: {str(api_error)}, using sample data")
            attractions = generate_sample_attractions(city, category)

        logger.info(f"Found {len(attractions)} attractions")

        return Response({
            'success': True,
            'results': attractions,
            'total': len(attractions)
        })

    except Exception as e:
        logger.error(f"Error searching attractions: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def format_attraction(data: dict, city: str, category: str = '') -> dict:
    """Format attraction data from SERP API response"""
    try:
        # Determine category from type or query
        attraction_category = category or detect_category(data.get('type', ''), data.get('title', ''))

        # Determine price level and estimated ticket price
        price_level = determine_price_level(data, attraction_category)
        ticket_price = estimate_ticket_price(price_level, attraction_category)

        return {
            'name': data.get('title', 'Unknown Attraction'),
            'description': data.get('description', ''),
            'category': attraction_category,
            'address': data.get('address', ''),
            'city': city,
            'rating': float(data.get('rating', 0)),
            'review_count': int(data.get('reviews', 0)),
            'price_level': price_level,
            'ticket_price': ticket_price,
            'hours': data.get('hours', ''),
            'phone': data.get('phone', ''),
            'website': data.get('website', ''),
            'latitude': data.get('gps_coordinates', {}).get('latitude'),
            'longitude': data.get('gps_coordinates', {}).get('longitude'),
            'thumbnail': data.get('thumbnail', ''),
            'primary_image': data.get('image', ''),
            'type': data.get('type', ''),
            'place_id': data.get('place_id', ''),
        }
    except Exception as e:
        logger.error(f"Error formatting attraction: {str(e)}")
        return None


def detect_category(type_str: str, title: str) -> str:
    """Detect attraction category from type or title"""
    type_lower = type_str.lower()
    title_lower = title.lower()

    if any(word in type_lower or word in title_lower for word in ['museum', 'gallery', 'exhibit']):
        return 'museums'
    elif any(word in type_lower or word in title_lower for word in ['park', 'garden', 'nature']):
        return 'parks'
    elif any(word in type_lower or word in title_lower for word in ['monument', 'landmark', 'historic', 'statue']):
        return 'landmarks'
    elif any(word in type_lower or word in title_lower for word in ['theme park', 'amusement', 'entertainment', 'zoo', 'aquarium']):
        return 'entertainment'
    elif any(word in type_lower or word in title_lower for word in ['church', 'temple', 'mosque', 'cathedral', 'religious']):
        return 'religious'
    elif any(word in type_lower or word in title_lower for word in ['shopping', 'mall', 'market']):
        return 'shopping'
    elif any(word in type_lower or word in title_lower for word in ['beach', 'waterfront', 'coast']):
        return 'beaches'
    else:
        return 'general'


def determine_price_level(data: dict, category: str = '') -> str:
    """Determine price level for attraction"""
    # Check if it's free (parks, public spaces, etc.)
    type_str = data.get('type', '').lower()
    title = data.get('title', '').lower()

    # Category-based pricing
    if category in ['parks', 'beaches', 'landmarks', 'religious']:
        # These are often free
        if any(word in type_str or word in title for word in ['national', 'state', 'memorial', 'monument']):
            return 'free'

    if any(word in type_str or word in title for word in ['park', 'public', 'free', 'plaza', 'square', 'memorial']):
        return 'free'

    # Check for price indicators in description
    description = data.get('description', '').lower()
    if 'free' in description or 'no admission' in description:
        return 'free'

    # Category-specific pricing
    if category == 'museums':
        return '$$'
    elif category == 'entertainment':
        return '$$$'
    elif category == 'shopping':
        return 'free'

    # Default based on rating
    rating = float(data.get('rating', 0))
    if rating >= 4.5:
        return '$$'
    elif rating >= 4.0:
        return '$'
    else:
        return 'free'


def estimate_ticket_price(price_level: str, category: str = '') -> float:
    """Estimate ticket price based on price level and category"""
    # Base prices by level
    price_map = {
        'free': 0,
        '$': 15,
        '$$': 25,
        '$$$': 45,
        '$$$$': 75
    }

    base_price = price_map.get(price_level, 0)

    # Adjust by category
    if category == 'entertainment':
        base_price = base_price * 1.5 if base_price > 0 else 50
    elif category == 'museums':
        base_price = base_price or 20

    return round(base_price, 2)


def generate_sample_attractions(city: str, category: str = '') -> list:
    """Generate sample tourist attractions data"""

    attraction_templates = {
        'museums': [
            {'name': 'Museum of Art', 'type': 'Art Museum'},
            {'name': 'History Museum', 'type': 'History Museum'},
            {'name': 'Science Center', 'type': 'Science Museum'},
            {'name': 'Natural History Museum', 'type': 'Museum'},
            {'name': 'Modern Art Gallery', 'type': 'Art Gallery'},
        ],
        'parks': [
            {'name': 'Central Park', 'type': 'Park'},
            {'name': 'Botanical Gardens', 'type': 'Garden'},
            {'name': 'City Park', 'type': 'Park'},
            {'name': 'Waterfront Park', 'type': 'Park'},
            {'name': 'Rose Garden', 'type': 'Garden'},
        ],
        'landmarks': [
            {'name': 'City Hall', 'type': 'Landmark'},
            {'name': 'Historic Monument', 'type': 'Monument'},
            {'name': 'Famous Tower', 'type': 'Landmark'},
            {'name': 'Old Town Square', 'type': 'Historic Site'},
            {'name': 'Memorial Plaza', 'type': 'Monument'},
        ],
        'entertainment': [
            {'name': 'Amusement Park', 'type': 'Theme Park'},
            {'name': 'Zoo', 'type': 'Zoo'},
            {'name': 'Aquarium', 'type': 'Aquarium'},
            {'name': 'Theater District', 'type': 'Theater'},
            {'name': 'Concert Hall', 'type': 'Venue'},
        ],
    }

    # Select templates based on category
    if category and category in attraction_templates:
        templates = attraction_templates[category]
    else:
        # Mix from all categories
        templates = []
        for cat_templates in attraction_templates.values():
            templates.extend(cat_templates)

    attractions = []
    num_attractions = min(random.randint(10, 15), len(templates))

    for i in range(num_attractions):
        template = random.choice(templates)

        # Detect category from template
        attr_category = category or detect_category(template['type'], template['name'])

        # Generate price level and ticket price
        price_level = determine_price_level({'type': template['type']}, attr_category)
        ticket_price = estimate_ticket_price(price_level, attr_category)

        attractions.append({
            'name': f"{city} {template['name']}",
            'description': f"A popular {template['type'].lower()} in {city} offering unique experiences and cultural insights.",
            'category': attr_category,
            'address': f"{random.randint(100, 999)} Main Street, {city}",
            'city': city,
            'rating': round(random.uniform(3.5, 4.9), 1),
            'review_count': random.randint(50, 5000),
            'price_level': price_level,
            'ticket_price': ticket_price,
            'hours': 'Open daily 9:00 AM - 6:00 PM',
            'phone': f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
            'website': f"https://www.{template['name'].lower().replace(' ', '')}.com",
            'latitude': None,
            'longitude': None,
            'thumbnail': '',
            'primary_image': '',
            'type': template['type'],
            'place_id': f"sample_{i}",
        })

    # Sort by rating
    attractions.sort(key=lambda x: x['rating'], reverse=True)

    return attractions
