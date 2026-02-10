from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Q
import logging

logger = logging.getLogger(__name__)

from .models import Hotel, HotelAmenity, HotelSearch
from .serializers import (
    HotelSerializer,
    HotelListSerializer,
    HotelAmenitySerializer,
    HotelSearchSerializer,
    HotelSearchCreateSerializer
)


class HotelViewSet(viewsets.ModelViewSet):
    """ViewSet for Hotel model."""

    queryset = Hotel.objects.filter(is_active=True)
    serializer_class = HotelSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'city', 'country', 'chain']
    filterset_fields = ['city', 'country', 'star_rating', 'property_type', 'is_featured']
    ordering_fields = ['guest_rating', 'star_rating', 'price_range_min', 'name']
    ordering = ['-guest_rating']

    def get_serializer_class(self):
        if self.action == 'list':
            return HotelListSerializer
        return HotelSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by guest rating
        min_rating = self.request.query_params.get('min_guest_rating')
        if min_rating:
            queryset = queryset.filter(guest_rating__gte=min_rating)

        # Filter by price range
        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(price_range_min__lte=max_price)

        # Filter by amenities
        amenities = self.request.query_params.getlist('amenities')
        if amenities:
            for amenity in amenities:
                queryset = queryset.filter(amenities__name__icontains=amenity)

        return queryset.distinct()

    @action(detail=False, methods=['post'])
    def search(self, request):
        """Advanced hotel search."""
        city = request.data.get('city')
        check_in = request.data.get('check_in_date')
        check_out = request.data.get('check_out_date')

        queryset = self.get_queryset().filter(city__iexact=city)

        # Apply additional filters
        min_star = request.data.get('min_star_rating')
        if min_star:
            queryset = queryset.filter(star_rating__gte=min_star)

        serializer = HotelListSerializer(queryset, many=True)
        return Response({'count': queryset.count(), 'results': serializer.data})

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured hotels."""
        hotels = self.get_queryset().filter(is_featured=True)[:10]
        serializer = HotelListSerializer(hotels, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def amenities(self, request, pk=None):
        """Get hotel amenities grouped by category."""
        hotel = self.get_object()
        amenities = hotel.amenities.all()

        grouped = {}
        for amenity in amenities:
            category = amenity.get_category_display()
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(HotelAmenitySerializer(amenity).data)

        return Response(grouped)


class HotelSearchViewSet(viewsets.ModelViewSet):
    """ViewSet for HotelSearch model."""

    queryset = HotelSearch.objects.all()
    serializer_class = HotelSearchSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['city', 'country']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return HotelSearchCreateSerializer
        return HotelSearchSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                return HotelSearch.objects.all()
            return HotelSearch.objects.filter(user=self.request.user)
        return HotelSearch.objects.none()

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()

    @action(detail=False, methods=['get'])
    def popular_destinations(self, request):
        """Get popular hotel search destinations."""
        destinations = HotelSearch.objects.values('city', 'country').annotate(
            search_count=Count('id')
        ).order_by('-search_count')[:10]
        return Response(destinations)


@api_view(['GET'])
@permission_classes([AllowAny])
def search_hotels(request):
    """
    Simple hotel search endpoint that accepts GET parameters.
    Uses SERP API for real hotel data from Google Hotels.
    """
    import os
    from datetime import datetime, timedelta

    # Get query parameters
    destination = request.query_params.get('destination', '')
    check_in_date = request.query_params.get('checkInDate')
    check_out_date = request.query_params.get('checkOutDate')
    guests = request.query_params.get('guests', '1')
    rooms = request.query_params.get('rooms', '1')

    # Check if SERP_API_KEY is configured
    serp_api_key = os.getenv('SERP_API_KEY', '')

    # Try to fetch real hotel data if API key is configured
    if serp_api_key and serp_api_key not in ['your_serpapi_key_here', 'YOUR_ACTUAL_SERPAPI_KEY_HERE']:
        try:
            from serpapi import GoogleSearch

            # Set default dates if not provided
            if not check_in_date:
                check_in_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            if not check_out_date:
                check_out_date = (datetime.now() + timedelta(days=9)).strftime('%Y-%m-%d')

            # Build SERP API search parameters for Google Hotels
            params = {
                "engine": "google_hotels",
                "q": destination,
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "adults": guests,
                "currency": "USD",
                "gl": "us",
                "hl": "en",
                "api_key": serp_api_key
            }

            # Make API request
            search = GoogleSearch(params)
            results = search.get_dict()

            # Transform SERP API response to our Hotel format
            if 'properties' in results and len(results['properties']) > 0:
                hotels = []
                for idx, hotel_data in enumerate(results['properties'][:20]):  # Limit to 20
                    try:
                        # Extract rating and derive star rating from it
                        overall_rating = hotel_data.get('overall_rating', 0)
                        if overall_rating:
                            # Derive star rating from overall rating (4.0+ = 5 stars, 3.5+ = 4 stars, etc.)
                            if overall_rating >= 4.5:
                                star_rating = 5
                            elif overall_rating >= 4.0:
                                star_rating = 4
                            elif overall_rating >= 3.0:
                                star_rating = 3
                            else:
                                star_rating = 2
                        else:
                            star_rating = 3  # Default

                        # Extract price
                        rate_per_night = hotel_data.get('rate_per_night', {})
                        if isinstance(rate_per_night, dict):
                            price_str = rate_per_night.get('lowest', '150')
                            # Remove currency symbols and commas, then convert to float
                            if isinstance(price_str, str):
                                price_str = price_str.replace('$', '').replace(',', '').strip()
                            price = float(price_str) if price_str else 150.0
                        else:
                            price = 150.0

                        # Extract images
                        images_data = hotel_data.get('images', [])
                        image_urls = [img.get('thumbnail', '') for img in images_data[:5] if isinstance(img, dict)]
                        primary_image = image_urls[0] if image_urls else ''

                        # Extract amenities
                        amenities_list = hotel_data.get('amenities', [])
                        if isinstance(amenities_list, list):
                            amenities = amenities_list[:5]
                        else:
                            amenities = []

                        # Extract additional details
                        extracted_price = hotel_data.get('extracted_price', {})
                        total_rate = hotel_data.get('total_rate', {})
                        nearby_places = hotel_data.get('nearby_places', [])
                        essential_info = hotel_data.get('essential_info', [])

                        # Extract location rating
                        location_rating = hotel_data.get('location_rating', 0)

                        # Extract check-in/out times
                        check_in_time = hotel_data.get('check_in_time', '')
                        check_out_time = hotel_data.get('check_out_time', '')

                        # Extract description
                        description = hotel_data.get('description', '')

                        # Format nearby places
                        nearby_formatted = []
                        if isinstance(nearby_places, list):
                            for place in nearby_places[:5]:
                                if isinstance(place, dict):
                                    nearby_formatted.append({
                                        'name': place.get('name', ''),
                                        'transportations': place.get('transportations', [])
                                    })

                        # Build hotel object with maximum details
                        hotel = {
                            'id': f"serp_{idx}",
                            'name': hotel_data.get('name', 'Unknown Hotel'),
                            'city': destination.split(',')[0].strip() if ',' in destination else destination,
                            'country': 'USA',
                            'address': hotel_data.get('link', ''),
                            'description': description,
                            'star_rating': star_rating,
                            'star_rating_display': f"{star_rating} Star",
                            'guest_rating': float(overall_rating) if overall_rating else 0.0,
                            'location_rating': float(location_rating) if location_rating else 0.0,
                            'review_count': hotel_data.get('reviews', 0),
                            'property_type': hotel_data.get('type', 'hotel'),
                            'primary_image': primary_image,
                            'price_range_min': price,
                            'price_range_max': price * 1.5,
                            'extracted_price': extracted_price,
                            'total_rate': total_rate,
                            'currency': 'USD',
                            'amenity_count': len(amenities),
                            'stars': star_rating,
                            'rating': float(overall_rating) if overall_rating else 0.0,
                            'pricePerNight': price,
                            'images': image_urls,
                            'amenities': amenities,
                            'nearby_places': nearby_formatted,
                            'essential_info': essential_info if isinstance(essential_info, list) else [],
                            'check_in_time': check_in_time,
                            'check_out_time': check_out_time,
                            'hotel_class': hotel_data.get('hotel_class', ''),
                            'gps_coordinates': hotel_data.get('gps_coordinates', {}),
                            'link': hotel_data.get('link', ''),
                            'property_token': hotel_data.get('property_token', '')
                        }
                        hotels.append(hotel)
                    except Exception as e:
                        logger.error(f"Error transforming hotel {idx}: {e}", exc_info=True)
                        continue

                if hotels:
                    return Response({
                        'count': len(hotels),
                        'total': len(hotels),
                        'items': hotels,
                        'results': hotels,
                        'message': f'Found {len(hotels)} real hotels in {destination} from {check_in_date} to {check_out_date}'
                    })
                else:
                    # No hotels after transformation
                    return Response({
                        'count': 0,
                        'total': 0,
                        'items': [],
                        'results': [],
                        'message': f'No hotels available in {destination} for selected dates'
                    })
            else:
                # No properties in SERP API response
                return Response({
                    'count': 0,
                    'total': 0,
                    'items': [],
                    'results': [],
                    'message': f'No hotels found in {destination}. Please try a different location or dates.'
                })

        except ImportError:
            logger.error("serpapi package not installed.")
            return Response({
                'count': 0,
                'total': 0,
                'items': [],
                'results': [],
                'message': 'Hotel search unavailable. Please contact support.',
                'error': 'SERP API package not installed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"SERP API error for hotels: {e}", exc_info=True)
            return Response({
                'count': 0,
                'total': 0,
                'items': [],
                'results': [],
                'message': f'Unable to search hotels at this time. Please try again later.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # No API key configured
    return Response({
        'count': 0,
        'total': 0,
        'items': [],
        'results': [],
        'message': 'Hotel search requires SERP API key configuration.',
        'error': 'API key not configured'
    }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
