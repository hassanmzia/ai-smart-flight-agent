from rest_framework import viewsets, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Q

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
                        # Extract hotel info
                        hotel = {
                            'id': f"serp_{idx}",
                            'name': hotel_data.get('name', 'Unknown Hotel'),
                            'city': destination.split(',')[0].strip() if ',' in destination else destination,
                            'country': 'USA',
                            'address': hotel_data.get('description', ''),
                            'star_rating': int(hotel_data.get('hotel_class', 3)),
                            'star_rating_display': f"{int(hotel_data.get('hotel_class', 3))} Star",
                            'guest_rating': float(hotel_data.get('overall_rating', 8.0)),
                            'review_count': hotel_data.get('reviews', 0),
                            'property_type': hotel_data.get('type', 'hotel'),
                            'primary_image': hotel_data.get('images', [{}])[0].get('thumbnail', '') if hotel_data.get('images') else '',
                            'price_range_min': float(hotel_data.get('rate_per_night', {}).get('lowest', 150)),
                            'price_range_max': float(hotel_data.get('rate_per_night', {}).get('lowest', 150)) * 1.5,
                            'currency': 'USD',
                            'amenity_count': len(hotel_data.get('amenities', [])),
                            'stars': int(hotel_data.get('hotel_class', 3)),
                            'rating': float(hotel_data.get('overall_rating', 8.0)),
                            'pricePerNight': float(hotel_data.get('rate_per_night', {}).get('lowest', 150)),
                            'images': [img.get('thumbnail', '') for img in hotel_data.get('images', [])[:5]],
                            'amenities': hotel_data.get('amenities', [])[:5],
                            'distanceFromCenter': 2.5  # SERP API doesn't always provide this
                        }
                        hotels.append(hotel)
                    except Exception as e:
                        print(f"Error transforming hotel {idx}: {e}")
                        continue

                if hotels:
                    return Response({
                        'count': len(hotels),
                        'total': len(hotels),
                        'items': hotels,
                        'results': hotels,
                        'message': f'Found {len(hotels)} real hotels in {destination} from {check_in_date} to {check_out_date}'
                    })

        except ImportError:
            print("serpapi package not installed. Using database hotels.")
        except Exception as e:
            print(f"SERP API error for hotels: {e}")
            # Fall through to database hotels on error

    # Fallback to database hotels if SERP API is not available
    queryset = Hotel.objects.filter(is_active=True)

    # Filter by destination (city or country)
    if destination:
        queryset = queryset.filter(
            Q(city__icontains=destination) |
            Q(country__icontains=destination) |
            Q(name__icontains=destination)
        )

    # Apply additional filters if provided
    min_rating = request.query_params.get('minRating')
    if min_rating:
        queryset = queryset.filter(guest_rating__gte=min_rating)

    max_price = request.query_params.get('maxPrice')
    if max_price:
        queryset = queryset.filter(price_range_min__lte=max_price)

    star_rating = request.query_params.get('starRating')
    if star_rating:
        queryset = queryset.filter(star_rating__gte=star_rating)

    # Order by rating
    queryset = queryset.order_by('-guest_rating', '-star_rating')[:20]  # Limit to 20 hotels

    # Serialize results
    serializer = HotelListSerializer(queryset, many=True)

    return Response({
        'count': queryset.count(),
        'total': queryset.count(),
        'items': serializer.data,
        'results': serializer.data,
        'message': f'Found {queryset.count()} database hotels in {destination}' if destination else f'Found {queryset.count()} database hotels'
    })
