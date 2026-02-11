from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RestaurantViewSet, CuisineViewSet, RestaurantBookingViewSet, search_restaurants

app_name = 'restaurants'

router = DefaultRouter()
router.register(r'restaurants', RestaurantViewSet, basename='restaurant')
router.register(r'cuisines', CuisineViewSet, basename='cuisine')
router.register(r'bookings', RestaurantBookingViewSet, basename='booking')

urlpatterns = [
    path('search/', search_restaurants, name='restaurant-search'),
    path('', include(router.urls)),
]
