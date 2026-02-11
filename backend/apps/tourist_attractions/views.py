from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import requests
import logging

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
    """
    try:
        city_raw = request.query_params.get('city', '')
        category = request.query_params.get('category', '')

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

        # SERP API request
        params = {
            "engine": "google_local",
            "q": search_query,
            "location": city,
            "api_key": settings.SERP_API_KEY
        }

        response = requests.get("https://serpapi.com/search", params=params, timeout=30)
        raw_results = response.json()

        # Check for API errors
        if 'error' in raw_results:
            logger.error(f"SERP API error: {raw_results['error']}")
            return Response({
                'success': False,
                'error': raw_results['error']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Extract local results
        local_results = raw_results.get('local_results', [])

        # Format attractions
        attractions = []
        for result in local_results[:20]:  # Limit to 20 results
            attraction = format_attraction(result, city, category)
            if attraction:
                attractions.append(attraction)

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

        # Determine price level
        price_level = determine_price_level(data)

        return {
            'name': data.get('title', 'Unknown Attraction'),
            'description': data.get('description', ''),
            'category': attraction_category,
            'address': data.get('address', ''),
            'city': city,
            'rating': float(data.get('rating', 0)),
            'review_count': int(data.get('reviews', 0)),
            'price_level': price_level,
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


def determine_price_level(data: dict) -> str:
    """Determine price level for attraction"""
    # Check if it's free (parks, public spaces, etc.)
    type_str = data.get('type', '').lower()
    title = data.get('title', '').lower()

    if any(word in type_str or word in title for word in ['park', 'public', 'free', 'plaza', 'square']):
        return 'free'

    # Check for price indicators in description
    description = data.get('description', '').lower()
    if 'free' in description or 'no admission' in description:
        return 'free'

    # Default to moderate pricing
    rating = float(data.get('rating', 0))
    if rating >= 4.5:
        return '$$'  # Popular attractions tend to charge
    elif rating >= 4.0:
        return '$'
    else:
        return 'free'  # Assume free if no clear price info
