from rest_framework import serializers
from .models import RiskAssessment, HealthAdvisory, SafetyAlert


class RiskAssessmentSerializer(serializers.ModelSerializer):
    """Serializer for RiskAssessment model."""
    risk_level_display = serializers.CharField(
        source='get_risk_level_display', read_only=True
    )

    class Meta:
        model = RiskAssessment
        fields = [
            'id', 'destination', 'country', 'overall_risk_score',
            'crime_score', 'health_score', 'natural_disaster_score',
            'political_stability_score', 'terrorism_score',
            'risk_level', 'risk_level_display', 'summary',
            'recommendations', 'last_updated', 'ai_generated',
        ]
        read_only_fields = ['id', 'last_updated']


class HealthAdvisorySerializer(serializers.ModelSerializer):
    """Serializer for HealthAdvisory model."""
    water_safety_display = serializers.CharField(
        source='get_water_safety_display', read_only=True
    )

    class Meta:
        model = HealthAdvisory
        fields = [
            'id', 'destination', 'country', 'vaccination_requirements',
            'health_risks', 'water_safety', 'water_safety_display',
            'altitude_info', 'medical_facilities_rating',
            'health_insurance_required', 'emergency_numbers',
            'nearby_hospitals', 'last_updated',
        ]
        read_only_fields = ['id', 'last_updated']


class SafetyAlertSerializer(serializers.ModelSerializer):
    """Serializer for SafetyAlert model."""
    alert_type_display = serializers.CharField(
        source='get_alert_type_display', read_only=True
    )
    severity_display = serializers.CharField(
        source='get_severity_display', read_only=True
    )

    class Meta:
        model = SafetyAlert
        fields = [
            'id', 'destination', 'country', 'alert_type',
            'alert_type_display', 'severity', 'severity_display',
            'title', 'description', 'source', 'source_url',
            'issued_at', 'expires_at', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']
