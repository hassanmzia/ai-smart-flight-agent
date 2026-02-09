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
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

def health_check(request):
    """Simple health check endpoint for Docker health checks."""
    return JsonResponse({'status': 'healthy', 'message': 'AI Travel Agent API is running'})

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
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
