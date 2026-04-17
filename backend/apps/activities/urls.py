from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search_activities, name='activities-search'),
    path('road-trip/', views.road_trip_waypoints, name='activities-road-trip'),
]
