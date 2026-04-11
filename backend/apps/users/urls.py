from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserProfileViewSet, TravelHistoryViewSet

app_name = 'users'

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')
router.register(r'profiles', UserProfileViewSet, basename='profile')
router.register(r'travel-history', TravelHistoryViewSet, basename='travel-history')

urlpatterns = [
    path('', include(router.urls)),
]
