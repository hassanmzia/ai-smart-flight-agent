from django.urls import path
from . import views

urlpatterns = [
    path('forecast/', views.get_weather_forecast, name='weather-forecast'),
]
