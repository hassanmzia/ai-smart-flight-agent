from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Itinerary(models.Model):
    """Travel itinerary for trip planning."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('approved', 'Approved'),
        ('booking', 'Booking in Progress'),
        ('booked', 'Booked'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='itineraries'
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    ai_narrative = models.TextField(blank=True, default='',
                                    help_text='Full AI-generated day-by-day narrative for PDF export')

    destination = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Travelers
    travelers = models.JSONField(default=list, blank=True)
    number_of_travelers = models.IntegerField(default=1)

    # Budget
    estimated_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')

    # Sharing
    is_public = models.BooleanField(default=False)
    is_shared = models.BooleanField(default=False)
    shared_with = models.JSONField(default=list, blank=True)

    # Cover image
    cover_image = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'itineraries'
        ordering = ['-start_date']
        verbose_name = 'Itinerary'
        verbose_name_plural = 'Itineraries'
        indexes = [
            models.Index(fields=['user', '-start_date']),
            models.Index(fields=['status', '-start_date']),
        ]

    def __str__(self):
        return f"{self.title} - {self.destination} ({self.start_date})"

    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1


class ItineraryDay(models.Model):
    """Individual day within an itinerary."""

    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='days')

    day_number = models.IntegerField()
    date = models.DateField()
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    # Weather forecast
    weather_temp_high = models.IntegerField(null=True, blank=True)
    weather_temp_low = models.IntegerField(null=True, blank=True)
    weather_condition = models.CharField(max_length=100, blank=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'itinerary_days'
        ordering = ['day_number']
        unique_together = ['itinerary', 'day_number']
        verbose_name = 'Itinerary Day'
        verbose_name_plural = 'Itinerary Days'

    def __str__(self):
        return f"{self.itinerary.title} - Day {self.day_number}"


class ItineraryItem(models.Model):
    """Individual activity/item within an itinerary day."""

    ITEM_TYPE_CHOICES = [
        ('flight', 'Flight'),
        ('hotel', 'Hotel'),
        ('restaurant', 'Restaurant'),
        ('attraction', 'Attraction'),
        ('activity', 'Activity'),
        ('transport', 'Transportation'),
        ('note', 'Note'),
    ]

    day = models.ForeignKey(ItineraryDay, on_delete=models.CASCADE, related_name='items')

    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    order = models.IntegerField(default=0)

    # Generic relation to actual object (flight, hotel, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Item details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Time
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)

    # Location
    location_name = models.CharField(max_length=255, blank=True)
    location_address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Cost
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Booking
    is_booked = models.BooleanField(default=False)
    booking_reference = models.CharField(max_length=100, blank=True)

    # Additional info
    notes = models.TextField(blank=True)
    url = models.URLField(blank=True)
    images = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'itinerary_items'
        ordering = ['day', 'start_time', 'order']
        verbose_name = 'Itinerary Item'
        verbose_name_plural = 'Itinerary Items'

    def __str__(self):
        return f"{self.day} - {self.title}"


class Weather(models.Model):
    """Weather forecast storage."""

    location = models.CharField(max_length=200, db_index=True)
    date = models.DateField(db_index=True)

    # Temperature (Celsius)
    temp_high = models.IntegerField()
    temp_low = models.IntegerField()
    temp_avg = models.IntegerField()

    # Conditions
    condition = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)

    # Additional data
    humidity = models.IntegerField(null=True, blank=True)
    wind_speed = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    precipitation_chance = models.IntegerField(null=True, blank=True)
    uv_index = models.IntegerField(null=True, blank=True)

    # Source
    source = models.CharField(max_length=50, default='openweather')
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'weather'
        ordering = ['date']
        unique_together = ['location', 'date', 'source']
        verbose_name = 'Weather'
        verbose_name_plural = 'Weather Forecasts'

    def __str__(self):
        return f"{self.location} - {self.date}: {self.condition}"
