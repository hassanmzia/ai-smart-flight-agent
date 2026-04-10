from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DestinationMediaViewSet,
    TravelStoryViewSet,
    TravelTipViewSet,
    DestinationInfoViewSet,
    CuratedGuideViewSet,
    destination_content,
)

app_name = 'community'

router = DefaultRouter()
router.register(r'media', DestinationMediaViewSet, basename='destination-media')
router.register(r'stories', TravelStoryViewSet, basename='travel-story')
router.register(r'tips', TravelTipViewSet, basename='travel-tip')
router.register(r'info', DestinationInfoViewSet, basename='destination-info')
router.register(r'curated-guides', CuratedGuideViewSet, basename='curated-guide')

urlpatterns = [
    path('destination-content/<str:destination>/', destination_content, name='destination-content'),
    path('', include(router.urls)),
]
