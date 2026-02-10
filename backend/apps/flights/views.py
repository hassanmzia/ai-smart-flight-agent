from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg, Min
from django.utils import timezone
from datetime import timedelta, datetime
import os

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


def transform_serp_flight(flight_data, idx, departure_date=None):
    """Transform SERP API flight data to match frontend Flight interface."""
    from datetime import datetime, timedelta

    # Get first flight segment for departure info
    first_leg = flight_data['flights'][0] if 'flights' in flight_data else {}
    last_leg = flight_data['flights'][-1] if 'flights' in flight_data else {}

    # Extract layovers/stops
    layovers = flight_data.get('layovers', [])
    stops = len(layovers)

    # Calculate total duration in minutes
    duration_mins = flight_data.get('total_duration', 0)

    # Helper to create airport object
    def make_airport_from_serp(airport_data):
        return {
            'code': airport_data.get('id', airport_data.get('code', 'N/A')),
            'name': airport_data.get('name', 'Unknown Airport'),
            'city': airport_data.get('city', airport_data.get('name', 'Unknown')),
            'country': airport_data.get('country', 'Unknown'),
            'timezone': airport_data.get('timezone', 'UTC')
        }

    # Format departure and arrival times as ISO datetime strings
    dep_time_str = first_leg.get('departure_time', '')
    arr_time_str = last_leg.get('arrival_time', '')

    # Try to create ISO datetime strings if we have the departure date
    if departure_date and dep_time_str:
        try:
            # Parse time string (handle both 12-hour and 24-hour formats)
            # SERP API returns times like "10:30 AM" or "22:30"
            if 'AM' in dep_time_str or 'PM' in dep_time_str:
                # 12-hour format
                time_obj = datetime.strptime(dep_time_str, '%I:%M %p').time()
            else:
                # 24-hour format
                time_obj = datetime.strptime(dep_time_str, '%H:%M').time()

            # Combine date with parsed time
            dep_dt = datetime.fromisoformat(departure_date).replace(
                hour=time_obj.hour,
                minute=time_obj.minute,
                second=0
            )
            dep_datetime = dep_dt.isoformat()

            # Calculate arrival datetime based on duration
            if duration_mins:
                arr_dt = dep_dt + timedelta(minutes=duration_mins)
                arr_datetime = arr_dt.isoformat()
            elif arr_time_str:
                # Try to parse arrival time
                if 'AM' in arr_time_str or 'PM' in arr_time_str:
                    arr_time_obj = datetime.strptime(arr_time_str, '%I:%M %p').time()
                else:
                    arr_time_obj = datetime.strptime(arr_time_str, '%H:%M').time()
                arr_dt = datetime.fromisoformat(departure_date).replace(
                    hour=arr_time_obj.hour,
                    minute=arr_time_obj.minute,
                    second=0
                )
                # Handle overnight flights (arrival next day)
                if arr_time_obj.hour < time_obj.hour:
                    arr_dt = arr_dt + timedelta(days=1)
                arr_datetime = arr_dt.isoformat()
            else:
                arr_datetime = dep_datetime
        except Exception as e:
            # Fallback: if parsing fails, just use the date
            print(f"Error parsing times: {e}")
            dep_datetime = f"{departure_date}T12:00:00"
            arr_datetime = f"{departure_date}T14:00:00"
    else:
        # No date available, use placeholder
        dep_datetime = f"2026-01-01T12:00:00"
        arr_datetime = f"2026-01-01T14:00:00"

    # Extract and clean price (handle currency strings)
    price_value = flight_data.get('price', 0)
    if isinstance(price_value, str):
        # Remove currency symbols and commas
        price_value = price_value.replace('$', '').replace(',', '').strip()
    try:
        price = float(price_value) if price_value else 0.0
    except (ValueError, TypeError):
        price = 0.0

    return {
        'id': f"SERP_{idx}_{flight_data.get('departure_token', '')}",
        'airline': first_leg.get('airline', 'Unknown'),
        'flightNumber': first_leg.get('flight_number', 'N/A'),
        'origin': make_airport_from_serp(first_leg.get('departure_airport', {})),
        'destination': make_airport_from_serp(last_leg.get('arrival_airport', {})),
        'departureTime': dep_datetime,
        'arrivalTime': arr_datetime,
        'duration': duration_mins,
        'price': price,
        'currency': 'USD',
        'class': flight_data.get('type', 'economy'),
        'stops': stops,
        'availableSeats': 9,  # SERP API doesn't provide this
        'aircraft': first_leg.get('airplane', 'Unknown'),
        'amenities': flight_data.get('extensions', [])
    }


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
    return_date = request.query_params.get('returnDate')
    passengers = request.query_params.get('passengers', '1')
    travel_class = request.query_params.get('class', 'economy')

    # Check if SERP_API_KEY is configured
    serp_api_key = os.getenv('SERP_API_KEY', '')

    # Try to fetch real flight data if API key is configured
    if serp_api_key and serp_api_key not in ['your_serpapi_key_here', 'YOUR_ACTUAL_SERPAPI_KEY_HERE']:
        try:
            from serpapi import GoogleSearch

            # Set default departure date if not provided
            if not departure_date:
                departure_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

            # Map travel class to SERP API format
            class_map = {
                'economy': '1',
                'premium_economy': '2',
                'business': '3',
                'first': '4'
            }

            # Build SERP API search parameters
            params = {
                "engine": "google_flights",
                "departure_id": origin,
                "arrival_id": destination,
                "outbound_date": departure_date,
                "currency": "USD",
                "hl": "en",
                "api_key": serp_api_key,
                "type": "1" if return_date else "2",  # 1=round-trip, 2=one-way
                "travel_class": class_map.get(travel_class, '1'),
                "adults": passengers
            }

            # Add return_date for round-trip flights
            if return_date:
                params["return_date"] = return_date

            # Make API request
            search = GoogleSearch(params)
            results = search.get_dict()

            # Transform SERP API response to our Flight format
            if 'best_flights' in results or 'other_flights' in results:
                flights = []
                all_flights = results.get('best_flights', []) + results.get('other_flights', [])

                print(f"\n=== SERP API returned {len(all_flights)} total flights ===")
                print(f"best_flights: {len(results.get('best_flights', []))}, other_flights: {len(results.get('other_flights', []))}")
                print(f"Processing first {min(20, len(all_flights))} flights...")

                for idx, flight_data in enumerate(all_flights[:20]):  # Limit to 20 flights
                    try:
                        transformed = transform_serp_flight(flight_data, idx, departure_date)
                        flights.append(transformed)
                        print(f"✓ Flight {idx}: {transformed.get('airline')} - ${transformed.get('price')}")
                    except Exception as e:
                        print(f"✗ Error transforming flight {idx}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue

                print(f"\n=== Successfully transformed {len(flights)} out of {min(20, len(all_flights))} flights ===\n")

                if flights:
                    return Response({
                        'count': len(flights),
                        'total': len(flights),
                        'items': flights,
                        'results': flights,
                        'message': f'Found {len(flights)} real flights from {origin} to {destination} on {departure_date}'
                    })

        except ImportError:
            print("serpapi package not installed. Using mock data.")
        except Exception as e:
            print(f"SERP API error: {e}")
            # Fall through to mock data on error

    # Generate mock flight data for testing (fallback)
    if not departure_date:
        departure_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

    # Helper to create airport object matching frontend Airport interface
    def make_airport(code, city):
        return {
            'code': code,
            'name': f'{code} Airport',
            'city': city,
            'country': 'USA',
            'timezone': 'America/New_York'
        }

    mock_flights = [
        {
            'id': 'FL001',
            'airline': 'American Airlines',
            'flightNumber': 'AA 1234',
            'origin': make_airport(origin, origin),
            'destination': make_airport(destination, destination),
            'departureTime': f'{departure_date}T08:00:00-05:00',
            'arrivalTime': f'{departure_date}T11:30:00-08:00',
            'duration': 210,  # minutes
            'price': 299,
            'currency': 'USD',
            'class': travel_class,
            'stops': 0,
            'availableSeats': 12,
            'aircraft': 'Boeing 737',
            'amenities': ['WiFi', 'In-flight entertainment']
        },
        {
            'id': 'FL002',
            'airline': 'Delta Airlines',
            'flightNumber': 'DL 5678',
            'origin': make_airport(origin, origin),
            'destination': make_airport(destination, destination),
            'departureTime': f'{departure_date}T10:30:00-05:00',
            'arrivalTime': f'{departure_date}T14:15:00-08:00',
            'duration': 225,  # minutes
            'price': 349,
            'currency': 'USD',
            'class': travel_class,
            'stops': 0,
            'availableSeats': 8,
            'aircraft': 'Airbus A320',
            'amenities': ['WiFi', 'Power outlets', 'Snacks']
        },
        {
            'id': 'FL003',
            'airline': 'United Airlines',
            'flightNumber': 'UA 9012',
            'origin': make_airport(origin, origin),
            'destination': make_airport(destination, destination),
            'departureTime': f'{departure_date}T14:00:00-05:00',
            'arrivalTime': f'{departure_date}T17:45:00-08:00',
            'duration': 225,  # minutes
            'price': 275,
            'currency': 'USD',
            'class': travel_class,
            'stops': 0,
            'availableSeats': 15,
            'aircraft': 'Boeing 787',
            'amenities': ['WiFi', 'Power outlets', 'Meals included']
        },
        {
            'id': 'FL004',
            'airline': 'Southwest Airlines',
            'flightNumber': 'WN 3456',
            'origin': make_airport(origin, origin),
            'destination': make_airport(destination, destination),
            'departureTime': f'{departure_date}T16:30:00-05:00',
            'arrivalTime': f'{departure_date}T21:00:00-08:00',
            'duration': 270,  # minutes
            'price': 199,
            'currency': 'USD',
            'class': travel_class,
            'stops': 1,
            'availableSeats': 20,
            'aircraft': 'Boeing 737',
            'amenities': ['2 checked bags included']
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
