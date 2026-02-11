"""
URL configuration for AI Travel Agent project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from apps.users.serializers import UserRegistrationSerializer, UserDetailSerializer

def health_check(request):
    """Simple health check endpoint for Docker health checks."""
    return JsonResponse({'status': 'healthy', 'message': 'AI Travel Agent API is running'})

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """User login endpoint that returns user data and JWT tokens."""
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({
            'error': 'Email and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    from django.contrib.auth import authenticate
    user = authenticate(request, username=email, password=password)

    if user is None:
        return Response({
            'error': 'Invalid email or password'
        }, status=status.HTTP_401_UNAUTHORIZED)

    # Generate tokens
    refresh = RefreshToken.for_user(user)

    return Response({
        'user': UserDetailSerializer(user).data,
        'tokens': {
            'accessToken': str(refresh.access_token),
            'refreshToken': str(refresh),
        }
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """User registration endpoint with automatic login."""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # Generate tokens for automatic login
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserDetailSerializer(user).data,
            'tokens': {
                'accessToken': str(refresh.access_token),
                'refreshToken': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout(request):
    """User logout endpoint (client-side token removal)."""
    return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)

@api_view(['GET', 'PUT', 'PATCH'])
def current_user(request):
    """Get or update current authenticated user."""
    # Check authentication
    if not request.user.is_authenticated:
        return Response({
            'error': 'Authentication required'
        }, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Handle PUT/PATCH for updating user
    from apps.users.serializers import UserUpdateSerializer
    serializer = UserUpdateSerializer(request.user, data=request.data, partial=(request.method == 'PATCH'))
    if serializer.is_valid():
        serializer.save()
        return Response(UserDetailSerializer(request.user).data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """Refresh access token using refresh token."""
    refresh_token = request.data.get('refreshToken')

    if not refresh_token:
        return Response({
            'error': 'Refresh token is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        refresh = RefreshToken(refresh_token)
        return Response({
            'accessToken': str(refresh.access_token),
            'refreshToken': str(refresh),
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'Invalid or expired refresh token'
        }, status=status.HTTP_401_UNAUTHORIZED)

urlpatterns = [
    # Health check
    path('api/health', health_check, name='health_check'),

    # Admin
    path('admin/', admin.site.urls),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Authentication
    path('api/auth/login', login, name='login'),
    path('api/auth/register', register, name='register'),
    path('api/auth/logout', logout, name='logout'),
    path('api/auth/refresh', refresh_token, name='refresh_token'),
    path('api/auth/me', current_user, name='current_user'),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # App URLs
    path('api/users/', include('apps.users.urls')),
    path('api/agents/', include('apps.agents.urls')),
    path('api/flights/', include('apps.flights.urls')),
    path('api/hotels/', include('apps.hotels.urls')),
    path('api/bookings/', include('apps.bookings.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/itineraries/', include('apps.itineraries.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/reviews/', include('apps.reviews.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/attractions/', include('apps.attractions.urls')),
    path('api/restaurants/', include('apps.restaurants.urls')),
    path('api/car-rentals/', include('apps.car_rentals.urls')),
    path('api/tourist-attractions/', include('apps.tourist_attractions.urls')),
    path('api/weather/', include('apps.weather.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
