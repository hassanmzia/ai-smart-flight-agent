from django.contrib import admin
from .models import RiskAssessment, HealthAdvisory, SafetyAlert


@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    """Admin interface for RiskAssessment model."""
    list_display = [
        'destination', 'country', 'overall_risk_score', 'risk_level',
        'crime_score', 'health_score', 'ai_generated', 'last_updated',
    ]
    list_filter = ['risk_level', 'country', 'ai_generated']
    search_fields = ['destination', 'country', 'summary']
    readonly_fields = ['last_updated']


@admin.register(HealthAdvisory)
class HealthAdvisoryAdmin(admin.ModelAdmin):
    """Admin interface for HealthAdvisory model."""
    list_display = [
        'destination', 'country', 'water_safety',
        'medical_facilities_rating', 'health_insurance_required',
        'last_updated',
    ]
    list_filter = ['water_safety', 'country', 'health_insurance_required']
    search_fields = ['destination', 'country']
    readonly_fields = ['last_updated']


@admin.register(SafetyAlert)
class SafetyAlertAdmin(admin.ModelAdmin):
    """Admin interface for SafetyAlert model."""
    list_display = [
        'title', 'destination', 'country', 'alert_type',
        'severity', 'is_active', 'issued_at', 'expires_at',
    ]
    list_filter = ['alert_type', 'severity', 'is_active', 'country']
    search_fields = ['title', 'description', 'destination', 'country']
    readonly_fields = ['created_at']
