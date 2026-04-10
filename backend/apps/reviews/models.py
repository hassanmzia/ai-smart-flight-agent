from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):
    """Generic review model for flights, hotels, restaurants, etc."""

    STATUS_CHOICES = [
        ('pending', 'Pending Moderation'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    # Generic relation to reviewed object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Review content
    title = models.CharField(max_length=255)
    content = models.TextField()

    # Overall rating
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Verification
    is_verified_purchase = models.BooleanField(default=False)
    booking_reference = models.CharField(max_length=100, blank=True)

    # Moderation
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_reviews'
    )
    moderation_notes = models.TextField(blank=True)
    moderated_at = models.DateTimeField(null=True, blank=True)

    # Helpfulness
    helpful_count = models.IntegerField(default=0)
    not_helpful_count = models.IntegerField(default=0)

    # Media
    images = models.JSONField(default=list, blank=True)
    videos = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.rating}/5)"


class Rating(models.Model):
    """Detailed ratings for specific aspects."""

    ASPECT_CHOICES = [
        # Flight aspects
        ('flight_comfort', 'Comfort'),
        ('flight_service', 'Service'),
        ('flight_food', 'Food & Beverage'),
        ('flight_entertainment', 'Entertainment'),
        ('flight_value', 'Value for Money'),
        # Hotel aspects
        ('hotel_cleanliness', 'Cleanliness'),
        ('hotel_comfort', 'Comfort'),
        ('hotel_location', 'Location'),
        ('hotel_facilities', 'Facilities'),
        ('hotel_staff', 'Staff'),
        ('hotel_value', 'Value for Money'),
        # Restaurant aspects
        ('restaurant_food', 'Food Quality'),
        ('restaurant_service', 'Service'),
        ('restaurant_ambiance', 'Ambiance'),
        ('restaurant_value', 'Value for Money'),
        # Attraction aspects
        ('attraction_experience', 'Experience'),
        ('attraction_value', 'Value for Money'),
        ('attraction_organization', 'Organization'),
    ]

    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='ratings')

    aspect = models.CharField(max_length=50, choices=ASPECT_CHOICES)
    score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )

    class Meta:
        db_table = 'ratings'
        unique_together = ['review', 'aspect']
        verbose_name = 'Rating'
        verbose_name_plural = 'Ratings'

    def __str__(self):
        return f"{self.review} - {self.get_aspect_display()}: {self.score}/5"


class AIRating(models.Model):
    """AI-generated quality rating for destinations, hotels, restaurants, and attractions."""

    ENTITY_TYPE_CHOICES = [
        ('destination', 'Destination'),
        ('hotel', 'Hotel'),
        ('restaurant', 'Restaurant'),
        ('attraction', 'Attraction'),
    ]

    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPE_CHOICES)
    entity_name = models.CharField(max_length=255, db_index=True)
    destination = models.CharField(max_length=200, db_index=True)

    # AI-generated scores (1-10)
    overall_score = models.DecimalField(max_digits=3, decimal_places=1)
    safety_score = models.DecimalField(max_digits=3, decimal_places=1, null=True)
    value_score = models.DecimalField(max_digits=3, decimal_places=1, null=True)
    food_score = models.DecimalField(max_digits=3, decimal_places=1, null=True)
    culture_score = models.DecimalField(max_digits=3, decimal_places=1, null=True)
    accessibility_score = models.DecimalField(max_digits=3, decimal_places=1, null=True)

    # Community data
    community_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    review_count = models.IntegerField(default=0)

    # AI analysis
    summary = models.TextField()
    pros = models.JSONField(default=list)
    cons = models.JSONField(default=list)
    best_for = models.JSONField(default=list)  # e.g. ["families", "couples", "solo travelers"]

    # Vacation predictor
    enjoyment_factors = models.JSONField(default=dict)  # factors that affect enjoyment

    ai_generated = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews_ai_rating'
        unique_together = ['entity_type', 'entity_name', 'destination']
        ordering = ['-overall_score']

    def __str__(self):
        return f"{self.entity_name} ({self.entity_type}) - {self.overall_score}/10"
