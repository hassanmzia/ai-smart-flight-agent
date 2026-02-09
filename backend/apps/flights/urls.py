from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .views import FlightViewSet, FlightSearchViewSet, PriceAlertViewSet, search_flights

app_name = 'flights'

router = DefaultRouter()
router.register(r'flights', FlightViewSet, basename='flight')
router.register(r'searches', FlightSearchViewSet, basename='search')
router.register(r'price-alerts', PriceAlertViewSet, basename='price-alert')

urlpatterns = [
    path('search/', search_flights, name='search_flights'),
    path('', include(router.urls)),
]
