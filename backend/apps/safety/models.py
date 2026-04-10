from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class RiskAssessment(models.Model):
    """Risk assessment for a travel destination."""

    RISK_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('extreme', 'Extreme'),
    ]

    destination = models.CharField(max_length=200, db_index=True)
    country = models.CharField(max_length=100)
    overall_risk_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    crime_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    health_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    natural_disaster_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    political_stability_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    terrorism_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES)
    summary = models.TextField()
    recommendations = models.JSONField(default=list)
    last_updated = models.DateTimeField(auto_now=True)
    ai_generated = models.BooleanField(default=True)

    class Meta:
        unique_together = ['destination', 'country']
        ordering = ['-last_updated']
        verbose_name = 'Risk Assessment'
        verbose_name_plural = 'Risk Assessments'

    def __str__(self):
        return f"{self.destination}, {self.country} - {self.risk_level} ({self.overall_risk_score}/100)"


class HealthAdvisory(models.Model):
    """Health advisory information for a travel destination."""

    WATER_SAFETY_CHOICES = [
        ('safe', 'Safe to Drink'),
        ('boil', 'Boil Before Drinking'),
        ('bottled_only', 'Bottled Water Only'),
        ('unsafe', 'Unsafe'),
    ]

    destination = models.CharField(max_length=200, db_index=True)
    country = models.CharField(max_length=100)
    vaccination_requirements = models.JSONField(default=list)
    health_risks = models.JSONField(default=list)
    water_safety = models.CharField(max_length=15, choices=WATER_SAFETY_CHOICES)
    altitude_info = models.TextField(blank=True)
    medical_facilities_rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    health_insurance_required = models.BooleanField(default=False)
    emergency_numbers = models.JSONField(default=dict)
    nearby_hospitals = models.JSONField(default=list)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_updated']
        verbose_name = 'Health Advisory'
        verbose_name_plural = 'Health Advisories'

    def __str__(self):
        return f"Health Advisory: {self.destination}, {self.country}"


class SafetyAlert(models.Model):
    """Active safety alerts for destinations."""

    ALERT_TYPE_CHOICES = [
        ('weather', 'Weather'),
        ('political', 'Political'),
        ('health', 'Health'),
        ('crime', 'Crime'),
        ('natural_disaster', 'Natural Disaster'),
        ('travel_advisory', 'Travel Advisory'),
        ('terrorism', 'Terrorism'),
    ]

    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
        ('emergency', 'Emergency'),
    ]

    destination = models.CharField(max_length=200, db_index=True)
    country = models.CharField(max_length=100)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    source = models.CharField(max_length=200, blank=True)
    source_url = models.URLField(blank=True)
    issued_at = models.DateTimeField()
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issued_at']
        verbose_name = 'Safety Alert'
        verbose_name_plural = 'Safety Alerts'

    def __str__(self):
        return f"[{self.severity.upper()}] {self.title} - {self.destination}"
