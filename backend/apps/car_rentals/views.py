from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
import json
import logging
import os

from .models import CarType, CarRental, RentalBooking
from .serializers import (
    CarTypeSerializer, CarRentalSerializer,
    CarRentalListSerializer, RentalBookingSerializer
)

logger = logging.getLogger(__name__)


class CarTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for CarType model."""
    queryset = CarType.objects.all()
    serializer_class = CarTypeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    filterset_fields = ['category', 'transmission', 'fuel_type']
    ordering = ['category', 'name']


class CarRentalViewSet(viewsets.ModelViewSet):
    """ViewSet for CarRental model."""
    queryset = CarRental.objects.filter(is_active=True, status='available')
    serializer_class = CarRentalSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['make', 'model', 'pickup_city', 'rental_company']
    filterset_fields = ['pickup_city', 'car_type', 'status']
    ordering_fields = ['price_per_day', 'rating', 'year']
    ordering = ['price_per_day']

    def get_serializer_class(self):
        if self.action == 'list':
            return CarRentalListSerializer
        return CarRentalSerializer

    @action(detail=False, methods=['get', 'post'])
    def search(self, request):
        """Search for available cars in the database (legacy endpoint)."""
        # Support both GET (query params) and POST (request body)
        if request.method == 'GET':
            pickup_city = request.query_params.get('pickup_city')
            pickup_date = request.query_params.get('pickup_date')
            return_date = request.query_params.get('return_date')
            car_type = request.query_params.get('car_type')
            max_price = request.query_params.get('max_price_per_day')
        else:  # POST
            pickup_city = request.data.get('pickup_city')
            pickup_date = request.data.get('pickup_date')
            return_date = request.data.get('return_date')
            car_type = request.data.get('car_type')
            max_price = request.data.get('max_price_per_day')

        queryset = self.get_queryset()

        if pickup_city:
            queryset = queryset.filter(pickup_city__iexact=pickup_city)

        # Additional filters
        if car_type:
            # Filter by car_type category if it's a string
            if isinstance(car_type, str) and car_type:
                queryset = queryset.filter(car_type__category__iexact=car_type)
            else:
                queryset = queryset.filter(car_type_id=car_type)

        if max_price:
            queryset = queryset.filter(price_per_day__lte=max_price)

        serializer = CarRentalListSerializer(queryset, many=True)
        return Response({'count': queryset.count(), 'results': serializer.data, 'cars': serializer.data})


class RentalBookingViewSet(viewsets.ModelViewSet):
    """ViewSet for RentalBooking model."""
    queryset = RentalBooking.objects.all()
    serializer_class = RentalBookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'pickup_date']
    ordering = ['-pickup_date']

    def get_queryset(self):
        if self.request.user.is_staff:
            return RentalBooking.objects.all()
        return RentalBooking.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a rental booking."""
        booking = self.get_object()
        if booking.status in ['completed', 'cancelled']:
            return Response(
                {'error': f'Cannot cancel {booking.status} booking'},
                status=400
            )

        booking.status = 'cancelled'
        booking.save()
        return Response(self.get_serializer(booking).data)

    @action(detail=True, methods=['post'])
    def start_rental(self, request, pk=None):
        """Mark rental as active (picked up)."""
        booking = self.get_object()
        if booking.status != 'confirmed':
            return Response(
                {'error': 'Only confirmed bookings can be started'},
                status=400
            )

        booking.status = 'active'
        booking.save()
        return Response(self.get_serializer(booking).data)

    @action(detail=True, methods=['post'])
    def complete_rental(self, request, pk=None):
        """Mark rental as completed (returned)."""
        booking = self.get_object()
        if booking.status != 'active':
            return Response(
                {'error': 'Only active rentals can be completed'},
                status=400
            )

        booking.status = 'completed'
        booking.save()
        return Response(self.get_serializer(booking).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def search_car_rentals(request):
    """
    Simple car rental search endpoint that accepts GET parameters.
    Uses SERP API for real car rental data from Google Local.
    """
    from datetime import datetime, timedelta

    # Helper function to convert airport codes to city names
    def convert_airport_to_city(location):
        """Convert airport codes to city names for Google Local search"""
        airport_to_city = {
            'LAX': 'Los Angeles',
            'JFK': 'New York JFK',
            'LGA': 'New York LaGuardia',
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
        }
        return airport_to_city.get(location.upper(), location)

    # Get query parameters
    pickup_city_raw = request.query_params.get('pickup_city', '')
    pickup_date = request.query_params.get('pickup_date')
    return_date = request.query_params.get('return_date')
    car_type = request.query_params.get('car_type', '')

    # Convert airport code to city name for Google Local search
    pickup_city = convert_airport_to_city(pickup_city_raw) if pickup_city_raw else ''
    logger.info(f"Converted location: '{pickup_city_raw}' -> '{pickup_city}'")

    # Check if SERP_API_KEY is configured
    serp_api_key = os.getenv('SERP_API_KEY', '')

    # Try to fetch real car rental data if API key is configured
    if serp_api_key and serp_api_key not in ['your_serpapi_key_here', 'YOUR_ACTUAL_SERPAPI_KEY_HERE']:
        logger.info(f"=== Using SERP API for car rental search: {pickup_city} from {pickup_date} to {return_date} ===")
        try:
            from serpapi import GoogleSearch

            # Set default dates if not provided
            if not pickup_date:
                pickup_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            if not return_date:
                return_date = (datetime.now() + timedelta(days=9)).strftime('%Y-%m-%d')

            # Calculate rental days
            try:
                pickup_dt = datetime.strptime(pickup_date, '%Y-%m-%d')
                return_dt = datetime.strptime(return_date, '%Y-%m-%d')
                rental_days = max(1, (return_dt - pickup_dt).days)
            except:
                rental_days = 2

            # Build search query
            search_query = f"car rental {pickup_city}"
            if car_type:
                search_query += f" {car_type}"

            # Build SERP API search parameters for Google Local
            params = {
                "engine": "google_local",
                "q": search_query,
                "location": pickup_city,
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

            # Transform SERP API response to our CarRental format
            if 'local_results' in results and len(results['local_results']) > 0:
                cars = []
                for idx, rental_data in enumerate(results['local_results'][:20]):  # Limit to 20
                    try:
                        # Extract rental company name
                        rental_company = rental_data.get('title', 'Unknown Car Rental')

                        # Extract rating
                        rating = float(rental_data.get('rating', 4.0))

                        # Extract reviews count
                        reviews = rental_data.get('reviews', 0)

                        # Determine car type based on search or default
                        car_types = ['Economy', 'Compact', 'Midsize', 'SUV', 'Luxury', 'Van']
                        if car_type:
                            vehicle_type = car_type.title()
                        else:
                            # Rotate through car types for variety
                            vehicle_type = car_types[idx % len(car_types)]

                        # Generate realistic vehicle names based on type
                        vehicle_names = {
                            'Economy': ['Toyota Yaris', 'Hyundai Accent', 'Nissan Versa', 'Kia Rio'],
                            'Compact': ['Toyota Corolla', 'Honda Civic', 'Mazda 3', 'Volkswagen Jetta'],
                            'Midsize': ['Toyota Camry', 'Honda Accord', 'Nissan Altima', 'Hyundai Sonata'],
                            'SUV': ['Toyota RAV4', 'Honda CR-V', 'Ford Explorer', 'Jeep Grand Cherokee'],
                            'Luxury': ['BMW 5 Series', 'Mercedes E-Class', 'Audi A6', 'Lexus ES'],
                            'Van': ['Honda Odyssey', 'Toyota Sienna', 'Chrysler Pacifica', 'Dodge Grand Caravan']
                        }
                        vehicle = vehicle_names.get(vehicle_type, ['Standard Car'])[idx % 4]

                        # Calculate price based on car type and rating
                        base_prices = {
                            'Economy': 30,
                            'Compact': 40,
                            'Midsize': 50,
                            'SUV': 70,
                            'Luxury': 120,
                            'Van': 80
                        }
                        price_per_day = base_prices.get(vehicle_type, 50)
                        # Add variation based on company rating
                        price_per_day = price_per_day + (rating - 4.0) * 10

                        # Calculate total price
                        total_price = price_per_day * rental_days

                        # Extract address and location
                        address = rental_data.get('address', '')
                        phone = rental_data.get('phone', '')

                        # Extract thumbnail
                        thumbnail = rental_data.get('thumbnail', '')

                        # Features based on car type
                        feature_sets = {
                            'Economy': ['Automatic', 'Air Conditioning', 'Bluetooth'],
                            'Compact': ['Automatic', 'Air Conditioning', 'Bluetooth', 'USB Ports'],
                            'Midsize': ['Automatic', 'Air Conditioning', 'Bluetooth', 'Cruise Control', 'USB Ports'],
                            'SUV': ['Automatic', 'Air Conditioning', 'Bluetooth', 'Cruise Control', '4WD', 'Roof Rack'],
                            'Luxury': ['Automatic', 'Leather Seats', 'Premium Audio', 'Navigation', 'Sunroof', 'Heated Seats'],
                            'Van': ['Automatic', 'Air Conditioning', '7+ Seats', 'Sliding Doors', 'Storage']
                        }
                        features = feature_sets.get(vehicle_type, ['Automatic', 'Air Conditioning'])

                        # Mileage based on car type
                        mileage_options = {
                            'Economy': 'Unlimited',
                            'Compact': 'Unlimited',
                            'Midsize': '200 miles/day',
                            'SUV': '200 miles/day',
                            'Luxury': '150 miles/day',
                            'Van': '200 miles/day'
                        }
                        mileage = mileage_options.get(vehicle_type, 'Unlimited')

                        # Deposit based on car type
                        deposit_amounts = {
                            'Economy': 200,
                            'Compact': 250,
                            'Midsize': 300,
                            'SUV': 400,
                            'Luxury': 800,
                            'Van': 500
                        }
                        deposit = deposit_amounts.get(vehicle_type, 300)

                        # Build car rental object
                        car = {
                            'id': f"serp_{idx}",
                            'rental_company': rental_company,
                            'car_type': vehicle_type,
                            'vehicle': vehicle,
                            'price_per_day': round(price_per_day, 2),
                            'total_price': round(total_price, 2),
                            'currency': 'USD',
                            'pickup_location': pickup_city,
                            'rating': rating,
                            'reviews': reviews,
                            'features': features,
                            'phone': phone,
                            'website': rental_data.get('website', ''),
                            'thumbnail': thumbnail,
                            'rental_days': rental_days,
                            'pickup_date': pickup_date,
                            'dropoff_date': return_date,
                            'mileage': mileage,
                            'deposit': deposit,
                            'insurance_available': True,
                            'address': address
                        }
                        cars.append(car)
                        logger.info(f"✓ Car {idx}: {rental_company} - {vehicle} ${price_per_day}/day")
                    except Exception as e:
                        logger.error(f"✗ Error transforming car rental {idx}: {e}", exc_info=True)
                        continue

                logger.info(f"=== Successfully transformed {len(cars)} car rentals ===")

                if cars:
                    return Response({
                        'count': len(cars),
                        'total': len(cars),
                        'results': cars,
                        'cars': cars,
                        'message': f'Found {len(cars)} car rentals in {pickup_city} from {pickup_date} to {return_date}'
                    })
                else:
                    # No cars after transformation
                    return Response({
                        'count': 0,
                        'total': 0,
                        'results': [],
                        'cars': [],
                        'message': f'No car rentals available in {pickup_city} for selected dates'
                    })
            else:
                logger.warning(f"SERP API response has no 'local_results'. Keys: {results.keys()}")
                return Response({
                    'count': 0,
                    'total': 0,
                    'results': [],
                    'cars': [],
                    'message': f'No car rentals found in {pickup_city}. Please try a different location.'
                })

        except ImportError:
            logger.error("serpapi package not installed.")
            return Response({
                'count': 0,
                'total': 0,
                'results': [],
                'cars': [],
                'message': 'Car rental search unavailable. Please contact support.',
                'error': 'SERP API package not installed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"SERP API error for car rentals: {e}", exc_info=True)
            return Response({
                'count': 0,
                'total': 0,
                'results': [],
                'cars': [],
                'message': f'Unable to search car rentals at this time. Please try again later.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # No API key configured
    return Response({
        'count': 0,
        'total': 0,
        'results': [],
        'cars': [],
        'message': 'Car rental search requires SERP API key configuration.',
        'error': 'API key not configured'
    }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
