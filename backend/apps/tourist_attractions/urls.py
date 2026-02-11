from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search_attractions, name='attraction-search'),
]
