from django.urls import path
from . import views

urlpatterns = [
    path('info/', views.get_commute_info, name='commute-info'),
]
