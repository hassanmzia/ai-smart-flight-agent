import logging
import random
import requests

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
#  Interest category → SerpAPI search queries                         #
# ------------------------------------------------------------------ #

INTEREST_QUERIES = {
    'birding': 'birdwatching spots bird sanctuary wildlife refuge',
    'hiking': 'hiking trails trailheads national park',
    'boating': 'marinas boat rentals kayak launches lake river',
    'camping': 'campgrounds camping sites RV parks glamping',
    'picnic': 'parks picnic areas scenic overlooks gardens',
    'fishing': 'fishing spots charter boats fishing piers',
    'golfing': 'golf courses driving ranges country clubs',
    'scouting': 'scout camps outdoor education centers nature centers',
    'cross_country': 'scenic byways scenic overlook rest stops road trip',
    'student_travel': 'university campus tours student hostels budget restaurants',
}

# Fallback sample data templates per interest
SAMPLE_TEMPLATES = {
    'birding': [
        {'name': '{city} Bird Sanctuary', 'desc': 'Popular birdwatching haven with over 200 species.', 'icon': '🐦'},
        {'name': '{city} Wetlands Nature Reserve', 'desc': 'Marshland reserve ideal for spotting migratory waterfowl.', 'icon': '🦆'},
        {'name': '{city} Audubon Center', 'desc': 'Educational center with guided birding walks and observation blinds.', 'icon': '🦅'},
        {'name': 'Eagle Point Lookout near {city}', 'desc': 'Elevated viewpoint for raptor sighting, especially during migration season.', 'icon': '🦉'},
        {'name': '{city} Botanical Gardens — Bird Trail', 'desc': 'Shaded nature trail through tropical gardens frequented by songbirds.', 'icon': '🐤'},
    ],
    'hiking': [
        {'name': '{city} Summit Trail', 'desc': 'Moderate 5-mile loop with panoramic views of the surrounding area.', 'icon': '🥾'},
        {'name': 'Sunset Ridge Trail near {city}', 'desc': 'Scenic ridge walk with wildflower meadows in spring.', 'icon': '🏔️'},
        {'name': '{city} National Park — Main Loop', 'desc': 'Well-maintained trail through old-growth forest.', 'icon': '🌲'},
        {'name': '{city} Waterfall Trail', 'desc': 'Short hike to a 50-foot cascading waterfall. Family-friendly.', 'icon': '💧'},
        {'name': '{city} Canyon Trail', 'desc': 'Challenging descent into a scenic canyon with rock formations.', 'icon': '🏜️'},
    ],
    'boating': [
        {'name': '{city} Marina & Boat Rentals', 'desc': 'Full-service marina with kayaks, paddleboards, and motorboats.', 'icon': '⛵'},
        {'name': '{city} Lake — Public Boat Launch', 'desc': 'Free public launch with dock access and parking.', 'icon': '🚤'},
        {'name': 'River Adventures {city}', 'desc': 'Guided kayak and canoe tours through scenic waterways.', 'icon': '🛶'},
        {'name': '{city} Sailing Club', 'desc': 'Day-pass sailing and sunset cruises available.', 'icon': '⛵'},
        {'name': '{city} Waterfront Kayak Center', 'desc': 'Hourly kayak and SUP rentals on calm waters.', 'icon': '🏄'},
    ],
    'camping': [
        {'name': '{city} State Park Campground', 'desc': 'Full-hookup sites with showers, fire pits, and a camp store.', 'icon': '⛺'},
        {'name': 'Pinewoods Campground near {city}', 'desc': 'Secluded tent-only sites surrounded by pine forest.', 'icon': '🏕️'},
        {'name': '{city} Lakeside RV Park', 'desc': 'RV and tent sites with lake access and boat ramp.', 'icon': '🚐'},
        {'name': 'Glamping {city}', 'desc': 'Luxury canvas tents with beds, electricity, and private fire pits.', 'icon': '✨'},
        {'name': '{city} Wilderness Backcountry Camp', 'desc': 'Primitive camping for experienced outdoors enthusiasts.', 'icon': '🌌'},
    ],
    'picnic': [
        {'name': '{city} Central Park — Picnic Meadow', 'desc': 'Large open lawn with shade trees and BBQ grills.', 'icon': '🧺'},
        {'name': '{city} Riverside Picnic Area', 'desc': 'Tables along the river with restrooms and playground nearby.', 'icon': '🌳'},
        {'name': '{city} Botanical Garden Grounds', 'desc': 'Bring a blanket and enjoy lunch among curated gardens.', 'icon': '🌸'},
        {'name': 'Sunset Overlook — {city}', 'desc': 'Scenic hilltop spot with benches and panoramic views.', 'icon': '🌅'},
        {'name': '{city} Community Park', 'desc': 'Family-friendly park with pavilions, trails, and open fields.', 'icon': '🏞️'},
    ],
    'fishing': [
        {'name': '{city} Fishing Pier', 'desc': 'Public pier open year-round. No license required for pier fishing.', 'icon': '🎣'},
        {'name': '{city} Charter Fishing Co.', 'desc': 'Half-day and full-day deep sea charters with gear provided.', 'icon': '🚢'},
        {'name': 'Trout Creek near {city}', 'desc': 'Stocked trout stream popular with fly fishermen.', 'icon': '🐟'},
        {'name': '{city} Lake — North Shore', 'desc': 'Bass and catfish fishing from shore or boat.', 'icon': '🐠'},
        {'name': 'River Bend Fishing Area — {city}', 'desc': 'Quiet bend in the river with easy bank access.', 'icon': '🎣'},
    ],
    'golfing': [
        {'name': '{city} Country Club — Public Course', 'desc': '18-hole championship course open to visitors.', 'icon': '⛳'},
        {'name': '{city} Municipal Golf Course', 'desc': 'Affordable public course with driving range and pro shop.', 'icon': '🏌️'},
        {'name': 'The Links at {city}', 'desc': 'Scottish-style links course with ocean views.', 'icon': '⛳'},
        {'name': '{city} Golf Academy & Range', 'desc': 'Driving range, putting green, and lesson packages.', 'icon': '🏌️‍♂️'},
        {'name': 'Eagle Ridge Golf Resort — {city}', 'desc': '36-hole resort course with stay-and-play packages.', 'icon': '⛳'},
    ],
    'scouting': [
        {'name': '{city} Scout Camp', 'desc': 'Overnight and day camp programs with orienteering and survival skills.', 'icon': '🏕️'},
        {'name': '{city} Outdoor Education Center', 'desc': 'Ropes course, archery range, and ecology workshops.', 'icon': '🎯'},
        {'name': '{city} Nature Center', 'desc': 'Exhibits on local wildlife with guided group hikes.', 'icon': '🔬'},
        {'name': 'Wilderness Skills Academy — {city}', 'desc': 'Fire-building, navigation, and first-aid training courses.', 'icon': '🧭'},
        {'name': '{city} Conservation Area', 'desc': 'Service project site with camping and trail maintenance activities.', 'icon': '🌿'},
    ],
    'cross_country': [
        {'name': 'Scenic Overlook — Highway near {city}', 'desc': 'Panoramic roadside viewpoint with photo opportunities.', 'icon': '🛣️'},
        {'name': '{city} Rest Area & Visitors Center', 'desc': 'Clean rest stop with local maps, food, and fuel nearby.', 'icon': '🅿️'},
        {'name': '{city} Roadside Diner', 'desc': 'Classic American diner popular with road-trippers.', 'icon': '🍔'},
        {'name': '{city} Historic Downtown — Road Trip Stop', 'desc': 'Walkable downtown with cafes, antiques, and local charm.', 'icon': '🏘️'},
        {'name': 'Gas & Go — {city} Highway Exit', 'desc': 'Fuel, snacks, and EV charging available 24/7.', 'icon': '⛽'},
    ],
    'student_travel': [
        {'name': '{city} University — Campus Tours', 'desc': 'Free guided campus tours daily at 10 AM and 2 PM.', 'icon': '🎓'},
        {'name': '{city} Student Hostel', 'desc': 'Budget dorm-style accommodation near the university district.', 'icon': '🛏️'},
        {'name': '{city} Student Union — Budget Dining', 'desc': 'Affordable cafeterias and food courts open to visitors.', 'icon': '🍕'},
        {'name': '{city} Public Library', 'desc': 'Free Wi-Fi, study spaces, and local tourist information.', 'icon': '📚'},
        {'name': '{city} Student Discount Office', 'desc': 'ISIC card processing and local student discount listings.', 'icon': '💳'},
    ],
}

NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'


def _geocode_city(city: str) -> tuple:
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={'q': city, 'format': 'json', 'limit': 1},
            headers={'User-Agent': 'AI-Travel-Planner/1.0'},
            timeout=5,
        )
        data = resp.json()
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        logger.warning('Geocoding failed for %s: %s', city, e)
    return None, None


def _search_serpapi(city: str, interest: str):
    """Try SerpAPI Google Maps local results for interest near city."""
    api_key = getattr(settings, 'SERP_API_KEY', '')
    if not api_key:
        return None

    query_suffix = INTEREST_QUERIES.get(interest, interest)
    query = f"{query_suffix} near {city}"

    try:
        resp = requests.get(
            'https://serpapi.com/search.json',
            params={
                'api_key': api_key,
                'engine': 'google_maps',
                'q': query,
                'type': 'search',
                'll': '',
            },
            timeout=15,
        )
        data = resp.json()
        results = data.get('local_results', [])
        if not results:
            return None

        places = []
        for r in results[:12]:
            lat = r.get('gps_coordinates', {}).get('latitude')
            lng = r.get('gps_coordinates', {}).get('longitude')
            places.append({
                'name': r.get('title', 'Unknown'),
                'description': r.get('description', '') or r.get('type', ''),
                'address': r.get('address', ''),
                'latitude': lat,
                'longitude': lng,
                'rating': r.get('rating', 0),
                'reviews': r.get('reviews', 0),
                'website': r.get('website', ''),
                'phone': r.get('phone', ''),
                'thumbnail': r.get('thumbnail', ''),
                'icon': _icon_for_interest(interest),
                'hours': r.get('operating_hours', {}).get('today', ''),
            })
        return places
    except Exception as e:
        logger.warning('SerpAPI activities search failed: %s', e)
        return None


def _icon_for_interest(interest: str) -> str:
    icons = {
        'birding': '🐦', 'hiking': '🥾', 'boating': '⛵', 'camping': '⛺',
        'picnic': '🧺', 'fishing': '🎣', 'golfing': '⛳', 'scouting': '🏕️',
        'cross_country': '🚗', 'student_travel': '🎓',
    }
    return icons.get(interest, '📍')


def _generate_sample_data(city: str, interest: str):
    """Generate realistic sample places when SerpAPI is unavailable."""
    templates = SAMPLE_TEMPLATES.get(interest)
    if not templates:
        templates = [
            {'name': f'{city} {interest.replace("_", " ").title()} Spot #{i+1}',
             'desc': f'Popular {interest.replace("_", " ")} destination near {city}.',
             'icon': '📍'}
            for i in range(5)
        ]

    city_lat, city_lng = _geocode_city(city)
    places = []
    for i, t in enumerate(templates):
        lat = (city_lat + random.uniform(-0.08, 0.08)) if city_lat else None
        lng = (city_lng + random.uniform(-0.08, 0.08)) if city_lng else None
        places.append({
            'name': t['name'].replace('{city}', city),
            'description': t['desc'].replace('{city}', city),
            'address': f'{random.randint(100, 999)} {random.choice(["Oak", "Elm", "Pine", "Maple", "River", "Lake", "Park"])} {random.choice(["St", "Ave", "Rd", "Dr", "Blvd"])}, {city}',
            'latitude': round(lat, 6) if lat else None,
            'longitude': round(lng, 6) if lng else None,
            'rating': round(random.uniform(3.5, 4.9), 1),
            'reviews': random.randint(20, 800),
            'website': '',
            'phone': '',
            'thumbnail': '',
            'icon': t.get('icon', '📍'),
            'hours': random.choice(['8:00 AM - 6:00 PM', '6:00 AM - 8:00 PM', 'Open 24 hours', '9:00 AM - 5:00 PM', 'Dawn to Dusk']),
        })

    return places


# ------------------------------------------------------------------ #
#  Endpoints                                                          #
# ------------------------------------------------------------------ #

@api_view(['GET'])
@permission_classes([AllowAny])
def search_activities(request):
    """
    Search for interest/hobby-specific places near a destination.

    Query params:
        city      (required) — destination city
        interest  (required) — category key or free-text interest
    """
    city = request.query_params.get('city', '').strip()
    interest = request.query_params.get('interest', '').strip().lower().replace(' ', '_')

    if not city or not interest:
        return Response(
            {'success': False, 'error': 'city and interest are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Try real SerpAPI data first, fall back to samples
    places = _search_serpapi(city, interest)
    source = 'serpapi'
    if not places:
        places = _generate_sample_data(city, interest)
        source = 'sample'

    city_lat, city_lng = _geocode_city(city)

    return Response({
        'success': True,
        'results': places,
        'total': len(places),
        'city': city,
        'interest': interest,
        'interest_label': interest.replace('_', ' ').title(),
        'icon': _icon_for_interest(interest),
        'source': source,
        'city_lat': city_lat,
        'city_lng': city_lng,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def road_trip_waypoints(request):
    """
    Generate scenic waypoints for a cross-country driving route.

    Query params:
        from_city  (required) — starting city
        to_city    (required) — destination city
        stops      (optional) — number of stops (default 5)
    """
    from_city = request.query_params.get('from_city', '').strip()
    to_city = request.query_params.get('to_city', '').strip()
    num_stops = min(int(request.query_params.get('stops', 5)), 10)

    if not from_city or not to_city:
        return Response(
            {'success': False, 'error': 'from_city and to_city are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from_lat, from_lng = _geocode_city(from_city)
    to_lat, to_lng = _geocode_city(to_city)

    if not from_lat or not to_lat:
        return Response({
            'success': False,
            'error': 'Could not geocode one or both cities',
        }, status=status.HTTP_400_BAD_REQUEST)

    waypoints = []
    stop_types = [
        ('Scenic Overlook', '🛣️', 'Panoramic viewpoint with photo opportunities'),
        ('Rest Area', '🅿️', 'Clean facilities with food and fuel nearby'),
        ('Historic Downtown', '🏘️', 'Walkable main street with local restaurants and shops'),
        ('State Park', '🌲', 'Nature trails, picnic areas, and restrooms'),
        ('Roadside Diner', '🍔', 'Classic road-trip food stop with local flavor'),
        ('Campground', '⛺', 'Overnight camping with hookups available'),
        ('Fuel & Charging', '⛽', 'Gas station and EV charging available 24/7'),
        ('Lake / River Access', '🏞️', 'Stretch your legs with a short walk along the water'),
    ]

    for i in range(num_stops):
        frac = (i + 1) / (num_stops + 1)
        lat = round(from_lat + (to_lat - from_lat) * frac + random.uniform(-0.3, 0.3), 6)
        lng = round(from_lng + (to_lng - from_lng) * frac + random.uniform(-0.3, 0.3), 6)
        stop = random.choice(stop_types)
        waypoints.append({
            'name': f'{stop[0]} — Stop {i + 1}',
            'icon': stop[1],
            'description': stop[2],
            'latitude': lat,
            'longitude': lng,
            'stop_number': i + 1,
            'distance_fraction': round(frac, 2),
        })

    return Response({
        'success': True,
        'from_city': from_city,
        'to_city': to_city,
        'from_lat': from_lat,
        'from_lng': from_lng,
        'to_lat': to_lat,
        'to_lng': to_lng,
        'waypoints': waypoints,
        'total_stops': len(waypoints),
    })
