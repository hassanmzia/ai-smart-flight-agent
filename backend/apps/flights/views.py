from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg, Min
from django.utils import timezone
from datetime import timedelta

from .models import Flight, FlightSearch, PriceAlert
from .serializers import (
    FlightSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
    FlightSearchSerializer,
    FlightSearchCreateSerializer,
    PriceAlertSerializer,
    PriceAlertCreateSerializer
)


@api_view(['GET'])
@permission_classes([AllowAny])
def search_flights(request):
    """
    Simple flight search endpoint that accepts GET parameters.
    This is a simplified interface for frontend compatibility.
    """
    import os
    from datetime import datetime, timedelta

    # Get query parameters
    origin = request.query_params.get('origin', 'NYC')
    destination = request.query_params.get('destination', 'LAX')
    departure_date = request.query_params.get('departureDate')
    passengers = request.query_params.get('passengers', '1')
    travel_class = request.query_params.get('class', 'economy')

    # Check if SERP_API_KEY is configured
    serp_api_key = os.getenv('SERP_API_KEY', '')

    if serp_api_key and serp_api_key != 'your_serpapi_key_here':
        # TODO: Integrate with SerpAPI Google Flights
        # For now, return mock data even with API key
        pass

    # Generate mock flight data for testing
    if not departure_date:
        departure_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

    mock_flights = [
        {
            'id': 'FL001',
            'airline': 'American Airlines',
            'airline_code': 'AA',
            'flight_number': 'AA 1234',
            'origin': origin,
            'origin_airport': f'{origin} Airport',
            'destination': destination,
            'destination_airport': f'{destination} Airport',
            'departure_time': f'{departure_date}T08:00:00Z',
            'arrival_time': f'{departure_date}T11:30:00Z',
            'duration': '3h 30m',
            'duration_minutes': 210,
            'stops': 0,
            'is_direct': True,
            'price': 299,
            'currency': 'USD',
            'travel_class': travel_class,
            'available_seats': 12,
            'baggage': '1 checked bag included',
        },
        {
            'id': 'FL002',
            'airline': 'Delta Airlines',
            'airline_code': 'DL',
            'flight_number': 'DL 5678',
            'origin': origin,
            'origin_airport': f'{origin} Airport',
            'destination': destination,
            'destination_airport': f'{destination} Airport',
            'departure_time': f'{departure_date}T10:30:00Z',
            'arrival_time': f'{departure_date}T14:15:00Z',
            'duration': '3h 45m',
            'duration_minutes': 225,
            'stops': 0,
            'is_direct': True,
            'price': 349,
            'currency': 'USD',
            'travel_class': travel_class,
            'available_seats': 8,
            'baggage': '1 checked bag included',
        },
        {
            'id': 'FL003',
            'airline': 'United Airlines',
            'airline_code': 'UA',
            'flight_number': 'UA 9012',
            'origin': origin,
            'origin_airport': f'{origin} Airport',
            'destination': destination,
            'destination_airport': f'{destination} Airport',
            'departure_time': f'{departure_date}T14:00:00Z',
            'arrival_time': f'{departure_date}T17:45:00Z',
            'duration': '3h 45m',
            'duration_minutes': 225,
            'stops': 0,
            'is_direct': True,
            'price': 275,
            'currency': 'USD',
            'travel_class': travel_class,
            'available_seats': 15,
            'baggage': '1 checked bag included',
        },
        {
            'id': 'FL004',
            'airline': 'Southwest Airlines',
            'airline_code': 'WN',
            'flight_number': 'WN 3456',
            'origin': origin,
            'origin_airport': f'{origin} Airport',
            'destination': destination,
            'destination_airport': f'{destination} Airport',
            'departure_time': f'{departure_date}T16:30:00Z',
            'arrival_time': f'{departure_date}T21:00:00Z',
            'duration': '4h 30m',
            'duration_minutes': 270,
            'stops': 1,
            'is_direct': False,
            'price': 199,
            'currency': 'USD',
            'travel_class': travel_class,
            'available_seats': 20,
            'baggage': '2 checked bags included',
        },
    ]

    return Response({
        'count': len(mock_flights),
        'total': len(mock_flights),
        'items': mock_flights,  # Frontend expects 'items' for PaginatedResponse
        'results': mock_flights,  # Keep for backward compatibility
        'message': 'Showing mock flight data for testing. Add SERP_API_KEY to .env for real flight data.' if not serp_api_key or serp_api_key == 'your_serpapi_key_here' else 'Real flight data coming soon!'
    })


class FlightViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Flight model.
    Provides CRUD operations and search functionality for flights.
    """

    queryset = Flight.objects.all()
    serializer_class = FlightSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['flight_number', 'airline_name', 'origin_city', 'destination_city']
    filterset_fields = [
        'origin_airport', 'destination_airport', 'airline_code',
        'travel_class', 'status', 'is_direct'
    ]
    ordering_fields = ['departure_time', 'base_price', 'duration_minutes']
    ordering = ['departure_time']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return FlightListSerializer
        elif self.action == 'retrieve':
            return FlightDetailSerializer
        return FlightSerializer

    def get_queryset(self):
        """Filter and optimize queryset based on query parameters."""
        queryset = Flight.objects.all()

        # Filter by date range
        departure_from = self.request.query_params.get('departure_from')
        departure_to = self.request.query_params.get('departure_to')

        if departure_from:
            queryset = queryset.filter(departure_time__gte=departure_from)
        if departure_to:
            queryset = queryset.filter(departure_time__lte=departure_to)

        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')

        if min_price:
            queryset = queryset.filter(base_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(base_price__lte=max_price)

        # Filter by availability
        available_only = self.request.query_params.get('available_only', 'false').lower() == 'true'
        if available_only:
            queryset = queryset.filter(available_seats__gt=0, status='scheduled')

        # Filter by stops
        max_stops = self.request.query_params.get('max_stops')
        if max_stops is not None:
            queryset = queryset.filter(stops_count__lte=int(max_stops))

        return queryset

    @action(detail=False, methods=['post'])
    def search(self, request):
        """Advanced flight search with multiple criteria."""
        origin = request.data.get('origin_airport')
        destination = request.data.get('destination_airport')
        departure_date = request.data.get('departure_date')

        if not all([origin, destination, departure_date]):
            return Response(
                {'error': 'origin_airport, destination_airport, and departure_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Build query
        queryset = Flight.objects.filter(
            origin_airport=origin,
            destination_airport=destination,
            departure_time__date=departure_date,
            status='scheduled'
        )

        # Apply filters
        travel_class = request.data.get('travel_class')
        if travel_class:
            queryset = queryset.filter(travel_class=travel_class)

        max_price = request.data.get('max_price')
        if max_price:
            queryset = queryset.filter(base_price__lte=max_price)

        direct_only = request.data.get('direct_only', False)
        if direct_only:
            queryset = queryset.filter(is_direct=True)

        airlines = request.data.get('airlines', [])
        if airlines:
            queryset = queryset.filter(airline_code__in=airlines)

        # Sort by price or departure time
        sort_by = request.data.get('sort_by', 'price')
        if sort_by == 'price':
            queryset = queryset.order_by('base_price')
        elif sort_by == 'duration':
            queryset = queryset.order_by('duration_minutes')
        else:
            queryset = queryset.order_by('departure_time')

        serializer = FlightListSerializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'])
    def popular_routes(self, request):
        """Get popular flight routes based on searches."""
        # Get top 10 most searched routes
        popular = FlightSearch.objects.values(
            'origin_airport', 'destination_airport'
        ).annotate(
            search_count=Count('id')
        ).order_by('-search_count')[:10]

        return Response(popular)

    @action(detail=False, methods=['get'])
    def cheapest(self, request):
        """Find cheapest flights for given route and date."""
        origin = request.query_params.get('origin_airport')
        destination = request.query_params.get('destination_airport')
        departure_date = request.query_params.get('departure_date')

        if not all([origin, destination, departure_date]):
            return Response(
                {'error': 'origin_airport, destination_airport, and departure_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        flights = Flight.objects.filter(
            origin_airport=origin,
            destination_airport=destination,
            departure_time__date=departure_date,
            status='scheduled',
            available_seats__gt=0
        ).order_by('base_price')[:5]

        serializer = FlightListSerializer(flights, many=True)
        return Response(serializer.data)


class FlightSearchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for FlightSearch model.
    Tracks user flight searches for analytics.
    """

    queryset = FlightSearch.objects.all()
    serializer_class = FlightSearchSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['origin_airport', 'destination_airport', 'trip_type']
    ordering_fields = ['created_at', 'departure_date']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return FlightSearchCreateSerializer
        return FlightSearchSerializer

    def get_queryset(self):
        """Filter queryset based on user."""
        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                return FlightSearch.objects.all()
            return FlightSearch.objects.filter(user=self.request.user)
        return FlightSearch.objects.none()

    def perform_create(self, serializer):
        """Save search with user if authenticated."""
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()

    @action(detail=False, methods=['get'])
    def my_searches(self, request):
        """Get authenticated user's search history."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        searches = FlightSearch.objects.filter(user=request.user).order_by('-created_at')[:20]
        serializer = self.get_serializer(searches, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get flight search trends."""
        # Last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)

        searches = FlightSearch.objects.filter(created_at__gte=thirty_days_ago)

        trends = {
            'total_searches': searches.count(),
            'popular_routes': list(
                searches.values('origin_airport', 'destination_airport')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            ),
            'popular_destinations': list(
                searches.values('destination_airport', 'destination_city')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            ),
            'average_passengers': searches.aggregate(
                Avg('adults'), Avg('children')
            ),
            'preferred_class_distribution': list(
                searches.values('preferred_class')
                .annotate(count=Count('id'))
            ),
        }

        return Response(trends)


class PriceAlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet for PriceAlert model.
    Manages price alerts for flight routes.
    """

    queryset = PriceAlert.objects.all()
    serializer_class = PriceAlertSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'origin_airport', 'destination_airport']
    ordering_fields = ['created_at', 'departure_date', 'target_price']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return PriceAlertCreateSerializer
        return PriceAlertSerializer

    def get_queryset(self):
        """Filter queryset to only show authenticated user's alerts unless staff."""
        if self.request.user.is_staff:
            return PriceAlert.objects.all()
        return PriceAlert.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Save alert with authenticated user."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a price alert."""
        alert = self.get_object()
        alert.status = 'cancelled'
        alert.save()

        serializer = self.get_serializer(alert)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active price alerts for the user."""
        alerts = self.get_queryset().filter(
            status='active',
            expiry_date__gte=timezone.now().date()
        )
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def triggered(self, request):
        """Get all triggered price alerts."""
        alerts = self.get_queryset().filter(status='triggered')
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def check_price(self, request, pk=None):
        """Manually check and update price for an alert."""
        alert = self.get_object()
        current_price = request.data.get('current_price')

        if not current_price:
            return Response(
                {'error': 'current_price is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        alert.check_price(float(current_price))
        serializer = self.get_serializer(alert)
        return Response(serializer.data)
