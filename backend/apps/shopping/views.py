from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import logging
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
def search_shopping(request):
    """
    Search for local shopping venues and districts

    Query Parameters:
    - city: City name or airport code (required)
    - category: Shopping category (optional): malls, markets, boutiques, outlets, souvenirs, local_crafts
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

        # Generate sample shopping venues
        shopping_venues = generate_sample_shopping_data(city, category)

        return Response({
            'success': True,
            'results': shopping_venues,
            'total': len(shopping_venues),
            'location': city
        })

    except Exception as e:
        logger.error(f"Error searching shopping venues: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def generate_sample_shopping_data(city: str, category: str = '') -> list:
    """Generate sample shopping venues data"""

    shopping_templates = {
        'malls': [
            {'name': 'Downtown Shopping Mall', 'icon': '🏬', 'stores': 150},
            {'name': 'City Center Plaza', 'icon': '🏢', 'stores': 200},
            {'name': 'Grand Mall', 'icon': '🛍️', 'stores': 180},
            {'name': 'Fashion District Mall', 'icon': '👗', 'stores': 120},
            {'name': 'Luxury Shopping Center', 'icon': '💎', 'stores': 80},
        ],
        'markets': [
            {'name': 'Local Farmers Market', 'icon': '🥬', 'stores': 50},
            {'name': 'Flea Market', 'icon': '🛒', 'stores': 100},
            {'name': 'Night Market', 'icon': '🌙', 'stores': 75},
            {'name': 'Artisan Market', 'icon': '🎨', 'stores': 40},
            {'name': 'Food Market', 'icon': '🍎', 'stores': 60},
        ],
        'boutiques': [
            {'name': 'Fashion Boutique District', 'icon': '👠', 'stores': 30},
            {'name': 'Designer Row', 'icon': '👔', 'stores': 25},
            {'name': 'Vintage Shopping Street', 'icon': '🕰️', 'stores': 20},
            {'name': 'Local Designer Quarter', 'icon': '✨', 'stores': 15},
            {'name': 'Arts & Crafts Lane', 'icon': '🎭', 'stores': 18},
        ],
        'outlets': [
            {'name': 'Premium Outlets', 'icon': '🏷️', 'stores': 120},
            {'name': 'Designer Outlet Village', 'icon': '💰', 'stores': 90},
            {'name': 'Brand Factory Outlets', 'icon': '🎁', 'stores': 110},
            {'name': 'Discount Shopping Center', 'icon': '💵', 'stores': 80},
        ],
        'souvenirs': [
            {'name': 'Tourist Souvenir Shop', 'icon': '🎁', 'stores': 5},
            {'name': 'Local Gifts & Crafts', 'icon': '🎀', 'stores': 8},
            {'name': 'Heritage Souvenir Store', 'icon': '🏺', 'stores': 6},
            {'name': 'City Memorabilia Shop', 'icon': '🗽', 'stores': 4},
        ],
        'local_crafts': [
            {'name': 'Handmade Crafts Market', 'icon': '🧶', 'stores': 25},
            {'name': 'Local Artisan Gallery', 'icon': '🖼️', 'stores': 15},
            {'name': 'Traditional Crafts Center', 'icon': '🎎', 'stores': 20},
            {'name': 'Cultural Heritage Shop', 'icon': '🏮', 'stores': 12},
        ]
    }

    # Select templates based on category
    if category and category in shopping_templates:
        templates = shopping_templates[category]
    else:
        # Mix venues from all categories
        templates = []
        for cat_templates in shopping_templates.values():
            templates.extend(cat_templates[:2])  # Take 2 from each category

    venues = []
    num_venues = min(random.randint(10, 15), len(templates))

    for i in range(num_venues):
        template = random.choice(templates)
        if template in venues:
            continue

        # Detect category from template
        venue_category = 'general'
        for cat, cat_templates in shopping_templates.items():
            if template in cat_templates:
                venue_category = cat
                break

        # Generate price level
        price_levels = ['$', '$$', '$$$', '$$$$']
        if venue_category in ['outlets', 'markets']:
            price_level = random.choice(['$', '$$'])
        elif venue_category in ['malls']:
            price_level = random.choice(['$$', '$$$'])
        elif venue_category in ['boutiques']:
            price_level = random.choice(['$$$', '$$$$'])
        else:
            price_level = random.choice(price_levels)

        # Generate location
        areas = [
            'Downtown',
            'City Center',
            'Shopping District',
            'Historic Quarter',
            'Waterfront',
            'Old Town',
            'Financial District',
            'Arts District',
            'Fashion Row',
            'Main Street'
        ]

        # Opening hours
        if venue_category == 'markets' and 'Night Market' in template['name']:
            hours = '6:00 PM - 12:00 AM'
        elif venue_category == 'markets':
            hours = '7:00 AM - 3:00 PM'
        else:
            hours = '10:00 AM - 9:00 PM'

        # Generate features
        features = []
        all_features = [
            'Free WiFi', 'Parking Available', 'ATM', 'Food Court',
            'Restrooms', 'Wheelchair Accessible', 'Gift Wrapping',
            'Tax-Free Shopping', 'Currency Exchange', 'Delivery Service'
        ]
        features = random.sample(all_features, random.randint(4, 7))

        venues.append({
            'name': f"{city} {template['name']}",
            'category': venue_category,
            'icon': template['icon'],
            'description': f"Popular shopping destination in {city} with a wide variety of stores and brands.",
            'location': random.choice(areas),
            'address': f"{random.randint(100, 999)} {random.choice(areas)} {random.choice(['Street', 'Avenue', 'Road', 'Boulevard'])}",
            'price_level': price_level,
            'store_count': template['stores'],
            'opening_hours': hours,
            'features': features,
            'popular_for': get_popular_items(venue_category),
            'payment_methods': ['Cash', 'Credit Card', 'Debit Card', 'Mobile Payment'],
            'rating': round(random.uniform(3.8, 4.9), 1),
            'review_count': random.randint(50, 2000),
            'busy_hours': get_busy_hours(venue_category),
            'distance_from_center': round(random.uniform(0.5, 8.0), 1),
        })

    # Sort by rating
    venues.sort(key=lambda x: x['rating'], reverse=True)

    return venues


def get_popular_items(category: str) -> list:
    """Get popular items for shopping category"""
    item_map = {
        'malls': ['Fashion', 'Electronics', 'Cosmetics', 'Shoes', 'Accessories'],
        'markets': ['Fresh Produce', 'Local Foods', 'Handicrafts', 'Antiques'],
        'boutiques': ['Designer Fashion', 'Jewelry', 'Accessories', 'Luxury Goods'],
        'outlets': ['Brand Discounts', 'Fashion Deals', 'Sports Apparel', 'Home Goods'],
        'souvenirs': ['Local Crafts', 'Postcards', 'Magnets', 'T-shirts', 'Keychains'],
        'local_crafts': ['Handmade Items', 'Traditional Art', 'Pottery', 'Textiles']
    }
    items = item_map.get(category, ['Shopping', 'Retail', 'Goods'])
    return random.sample(items, min(4, len(items)))


def get_busy_hours(category: str) -> str:
    """Get typical busy hours for shopping category"""
    if category == 'markets':
        return 'Saturdays 8:00 AM - 12:00 PM'
    else:
        return 'Weekends 2:00 PM - 7:00 PM'
