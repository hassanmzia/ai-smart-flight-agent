from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CarTypeViewSet, CarRentalViewSet, RentalBookingViewSet, search_car_rentals

app_name = 'car_rentals'

router = DefaultRouter()
router.register(r'types', CarTypeViewSet, basename='type')
router.register(r'rentals', CarRentalViewSet, basename='rental')
router.register(r'bookings', RentalBookingViewSet, basename='booking')

urlpatterns = [
    path('search/', search_car_rentals, name='car-rental-search'),
    path('', include(router.urls)),
]
