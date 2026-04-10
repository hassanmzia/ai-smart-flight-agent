from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'risk-assessments', views.RiskAssessmentViewSet, basename='risk-assessment')
router.register(r'health-advisories', views.HealthAdvisoryViewSet, basename='health-advisory')
router.register(r'alerts', views.SafetyAlertViewSet, basename='safety-alert')

urlpatterns = [
    # Original function-based view (backward compatible)
    path('info/', views.get_safety_info, name='safety-info'),
    # DRF viewset routes
    path('', include(router.urls)),
]
