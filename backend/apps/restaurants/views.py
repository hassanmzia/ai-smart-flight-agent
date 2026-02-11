from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
import logging
import os

from .models import Restaurant, Cuisine, RestaurantBooking
from .serializers import (
    RestaurantSerializer, RestaurantListSerializer,
    CuisineSerializer, RestaurantBookingSerializer
)

logger = logging.getLogger(__name__)


class RestaurantViewSet(viewsets.ModelViewSet):
    """ViewSet for Restaurant model."""
    queryset = Restaurant.objects.filter(is_active=True)
    serializer_class = RestaurantSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'city', 'country', 'description']
    filterset_fields = ['city', 'country', 'price_range', 'has_delivery', 'is_featured']
    ordering_fields = ['rating', 'name', 'average_cost_per_person']
    ordering = ['-rating']

    def get_serializer_class(self):
        if self.action == 'list':
            return RestaurantListSerializer
        return RestaurantSerializer

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured restaurants."""
        restaurants = self.get_queryset().filter(is_featured=True)[:10]
        serializer = RestaurantListSerializer(restaurants, many=True)
        return Response(serializer.data)


class CuisineViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Cuisine model."""
    queryset = Cuisine.objects.all()
    serializer_class = CuisineSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class RestaurantBookingViewSet(viewsets.ModelViewSet):
    """ViewSet for RestaurantBooking model."""
    queryset = RestaurantBooking.objects.all()
    serializer_class = RestaurantBookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'restaurant', 'reservation_date']
    ordering = ['-reservation_date', '-reservation_time']

    def get_queryset(self):
        if self.request.user.is_staff:
            return RestaurantBooking.objects.all()
        return RestaurantBooking.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a restaurant booking."""
        booking = self.get_object()
        booking.status = 'cancelled'
        booking.save()
        return Response(self.get_serializer(booking).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def search_restaurants(request):
    """
    Search for restaurants using SERP API Google Local.
    """
    from datetime import datetime

    # Helper function to convert airport codes to city names
    def convert_airport_to_city(location):
        """Convert airport codes to city names for Google Local search"""
        airport_to_city_map = {
            'LAX': 'Los Angeles, CA',
            'JFK': 'New York, NY',
            'LGA': 'New York, NY',
            'EWR': 'Newark, NJ',
            'ORD': 'Chicago, IL',
            'SFO': 'San Francisco, CA',
            'MIA': 'Miami, FL',
            'DFW': 'Dallas, TX',
            'SEA': 'Seattle, WA',
            'BOS': 'Boston, MA',
            'ATL': 'Atlanta, GA',
            'DEN': 'Denver, CO',
            'IAD': 'Washington, DC',
            'DCA': 'Washington, DC',
            'LAS': 'Las Vegas, NV',
            'PHX': 'Phoenix, AZ',
            'IAH': 'Houston, TX',
            'MCO': 'Orlando, FL',
            'CDG': 'Paris, France',
            'LHR': 'London, UK',
            'BER': 'Berlin, Germany',
            'FCO': 'Rome, Italy',
            'NRT': 'Tokyo, Japan',
        }
        return airport_to_city_map.get(location.upper(), location)

    # Get query parameters
    city_raw = request.query_params.get('city', '')
    cuisine = request.query_params.get('cuisine', '')
    price_level = request.query_params.get('price_level', '')

    # Convert airport code to city name
    city = convert_airport_to_city(city_raw) if city_raw else ''
    logger.info(f"Converted location: '{city_raw}' -> '{city}'")

    # Check if SERP_API_KEY is configured
    serp_api_key = os.getenv('SERP_API_KEY', '')

    # Try to fetch real restaurant data if API key is configured
    if serp_api_key and serp_api_key not in ['your_serpapi_key_here', 'YOUR_ACTUAL_SERPAPI_KEY_HERE']:
        logger.info(f"=== Using SERP API for restaurant search: {city}, cuisine: {cuisine} ===")
        try:
            from serpapi import GoogleSearch

            # Build search query
            search_query = f"restaurants {city}"
            if cuisine:
                search_query = f"{cuisine} restaurants {city}"

            # Build SERP API search parameters for Google Local
            params = {
                "engine": "google_local",
                "q": search_query,
                "location": city,
                "hl": "en",
                "gl": "us",
                "api_key": serp_api_key
            }

            # Make API request
            search = GoogleSearch(params)
            results = search.get_dict()

            logger.info(f"SERP API response keys: {results.keys()}")
            if 'error' in results:
                logger.error(f"SERP API returned error: {results.get('error')}")

            # Transform SERP API response to Restaurant format
            if 'local_results' in results and len(results['local_results']) > 0:
                restaurants = []
                for idx, restaurant_data in enumerate(results['local_results'][:20]):  # Limit to 20
                    try:
                        # Extract restaurant name
                        name = restaurant_data.get('title', 'Unknown Restaurant')

                        # Extract rating
                        rating = float(restaurant_data.get('rating', 0))

                        # Extract reviews count
                        reviews = restaurant_data.get('reviews', 0)

                        # Determine price level
                        price_info = restaurant_data.get('price', '')
                        if isinstance(price_info, str):
                            price_level_val = len([c for c in price_info if c == '$'])
                        else:
                            price_level_val = 2  # Default to $$

                        # Extract cuisine type from type or description
                        restaurant_type = restaurant_data.get('type', '')
                        cuisine_type = 'Other'
                        common_cuisines = ['American', 'Italian', 'Mexican', 'Chinese', 'Japanese',
                                         'Indian', 'Thai', 'French', 'Mediterranean', 'Seafood']
                        for c in common_cuisines:
                            if c.lower() in restaurant_type.lower() or c.lower() in name.lower():
                                cuisine_type = c
                                break

                        # Extract address and location
                        address = restaurant_data.get('address', '')
                        phone = restaurant_data.get('phone', '')

                        # Extract thumbnail
                        thumbnail = restaurant_data.get('thumbnail', '')

                        # Estimate average cost per person based on price level
                        cost_map = {1: 15, 2: 30, 3: 50, 4: 100}
                        avg_cost = cost_map.get(price_level_val, 30)

                        # Extract hours if available
                        hours = restaurant_data.get('hours', '')

                        # Build restaurant object
                        restaurant = {
                            'id': f"serp_{idx}",
                            'name': name,
                            'cuisine_type': cuisine_type,
                            'city': city,
                            'address': address,
                            'rating': rating,
                            'review_count': reviews,
                            'price_level': price_level_val,
                            'price_range': '$' * price_level_val,
                            'average_cost_per_person': avg_cost,
                            'currency': 'USD',
                            'phone': phone,
                            'website': restaurant_data.get('website', ''),
                            'thumbnail': thumbnail,
                            'primary_image': thumbnail,
                            'has_delivery': 'delivery' in restaurant_type.lower(),
                            'has_takeout': 'takeout' in restaurant_type.lower() or 'take out' in restaurant_type.lower(),
                            'has_reservation': rating >= 4.0,  # Assume higher-rated places take reservations
                            'hours': hours,
                        }
                        restaurants.append(restaurant)
                        logger.info(f"✓ Restaurant {idx}: {name} - {rating}★, {price_level_val}$")
                    except Exception as e:
                        logger.error(f"✗ Error transforming restaurant {idx}: {e}", exc_info=True)
                        continue

                logger.info(f"=== Successfully transformed {len(restaurants)} restaurants ===")

                if restaurants:
                    return Response({
                        'count': len(restaurants),
                        'total': len(restaurants),
                        'results': restaurants,
                        'restaurants': restaurants,
                        'message': f'Found {len(restaurants)} restaurants in {city}'
                    })
                else:
                    return Response({
                        'count': 0,
                        'total': 0,
                        'results': [],
                        'restaurants': [],
                        'message': f'No restaurants found in {city}'
                    })
            else:
                logger.warning(f"SERP API response has no 'local_results'. Keys: {results.keys()}")
                return Response({
                    'count': 0,
                    'total': 0,
                    'results': [],
                    'restaurants': [],
                    'message': f'No restaurants found in {city}. Please try a different location.'
                })

        except ImportError:
            logger.error("serpapi package not installed.")
            return Response({
                'count': 0,
                'total': 0,
                'results': [],
                'restaurants': [],
                'message': 'Restaurant search unavailable. Please contact support.',
                'error': 'SERP API package not installed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"SERP API error for restaurants: {e}", exc_info=True)
            return Response({
                'count': 0,
                'total': 0,
                'results': [],
                'restaurants': [],
                'message': f'Unable to search restaurants at this time. Please try again later.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # No API key configured
    return Response({
        'count': 0,
        'total': 0,
        'results': [],
        'restaurants': [],
        'message': 'Restaurant search requires SERP API key configuration.',
        'error': 'API key not configured'
    }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
