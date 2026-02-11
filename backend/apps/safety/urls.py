from django.urls import path
from . import views

urlpatterns = [
    path('info/', views.get_safety_info, name='safety-info'),
]
