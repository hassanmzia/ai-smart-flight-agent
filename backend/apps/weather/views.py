from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# OpenWeatherMap API (you can also use WeatherAPI.com or others)
OPENWEATHER_API_KEY = getattr(settings, 'OPENWEATHER_API_KEY', '')


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
        'IAD': 'Washington',
        'DCA': 'Washington',
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
def get_weather_forecast(request):
    """
    Get weather forecast for a location and date range

    Query Parameters:
    - city: City name or airport code (required)
    - start_date: Start date YYYY-MM-DD (optional, defaults to today)
    - end_date: End date YYYY-MM-DD (optional, defaults to start_date + 7 days)
    """
    try:
        city_raw = request.query_params.get('city', '')
        start_date_str = request.query_params.get('start_date', '')
        end_date_str = request.query_params.get('end_date', '')

        if not city_raw:
            return Response({
                'success': False,
                'error': 'City parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Convert airport code to city name
        city = convert_airport_to_city(city_raw)

        # Parse dates
        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            else:
                start_date = datetime.now()

            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            else:
                end_date = start_date + timedelta(days=7)
        except ValueError:
            return Response({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get weather data - using sample data for now
        weather_data = generate_sample_weather_data(city, start_date, end_date)

        return Response(weather_data)

    except Exception as e:
        logger.error(f"Error getting weather forecast: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_weather_icon(condition: str) -> str:
    """Get weather emoji icon based on condition"""
    icons = {
        'Clear': '☀️',
        'Clouds': '☁️',
        'Rain': '🌧️',
        'Drizzle': '🌦️',
        'Thunderstorm': '⛈️',
        'Snow': '❄️',
        'Mist': '🌫️',
        'Fog': '🌫️',
        'Haze': '🌫️',
        'Partly Cloudy': '⛅'
    }
    return icons.get(condition, '🌤️')


def generate_sample_weather_data(city: str, start_date: datetime, end_date: datetime) -> dict:
    """Generate sample weather data"""
    import random

    days = (end_date - start_date).days + 1
    forecasts = []

    conditions = ['Clear', 'Clouds', 'Rain', 'Partly Cloudy', 'Drizzle']
    descriptions = {
        'Clear': 'clear sky',
        'Clouds': 'scattered clouds',
        'Rain': 'moderate rain',
        'Partly Cloudy': 'partly cloudy',
        'Drizzle': 'light drizzle'
    }

    for i in range(min(days, 14)):  # Limit to 14 days
        date = start_date + timedelta(days=i)
        condition = random.choice(conditions)

        # More realistic temperature ranges
        base_temp = random.randint(18, 28)
        temp_min = base_temp - random.randint(3, 6)
        temp_max = base_temp + random.randint(3, 6)

        forecasts.append({
            'date': date.strftime('%Y-%m-%d'),
            'day_of_week': date.strftime('%A'),
            'temp_min': temp_min,
            'temp_max': temp_max,
            'temp_avg': round((temp_min + temp_max) / 2, 1),
            'condition': condition,
            'description': descriptions.get(condition, condition.lower()),
            'humidity': random.randint(40, 85),
            'wind_speed': round(random.uniform(2, 18), 1),
            'precipitation_mm': round(random.uniform(0, 8), 1) if condition in ['Rain', 'Drizzle'] else 0,
            'precipitation_chance': random.randint(20, 90) if condition in ['Rain', 'Drizzle', 'Clouds'] else random.randint(0, 20),
            'icon': get_weather_icon(condition),
            'uv_index': random.randint(3, 9) if condition == 'Clear' else random.randint(1, 5)
        })

    return {
        'success': True,
        'location': {
            'city': city,
            'country': 'Various',
            'latitude': 0,
            'longitude': 0
        },
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'forecasts': forecasts,
        'total_days': len(forecasts)
    }
