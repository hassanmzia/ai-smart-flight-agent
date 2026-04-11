from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HotelViewSet, HotelSearchViewSet, search_hotels, search_rentals, featured_rentals

app_name = 'hotels'

router = DefaultRouter()
router.register(r'hotels', HotelViewSet, basename='hotel')
router.register(r'searches', HotelSearchViewSet, basename='search')

urlpatterns = [
    path('', include(router.urls)),
    path('search', search_hotels, name='hotel_search'),
    # Vacation Rentals
    path('rentals/search', search_rentals, name='rental_search'),
    path('rentals/featured', featured_rentals, name='featured_rentals'),
]
