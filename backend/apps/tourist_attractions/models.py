from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AttractionCategory(models.Model):
    """Categories for tourist attractions"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name_plural = "Attraction Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class TouristAttraction(models.Model):
    """Model for tourist attractions"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        AttractionCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attractions'
    )

    # Location
    address = models.CharField(max_length=500, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Ratings and Reviews
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.IntegerField(default=0)

    # Pricing
    PRICE_LEVEL_CHOICES = [
        ('free', 'Free'),
        ('$', 'Budget ($)'),
        ('$$', 'Moderate ($$)'),
        ('$$$', 'Expensive ($$$)'),
        ('$$$$', 'Very Expensive ($$$$)'),
    ]
    price_level = models.CharField(max_length=10, choices=PRICE_LEVEL_CHOICES, default='$')
    ticket_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    # Hours and Accessibility
    hours = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=50, blank=True)

    # Features
    wheelchair_accessible = models.BooleanField(default=False)
    family_friendly = models.BooleanField(default=True)

    # Images
    primary_image = models.URLField(blank=True)
    thumbnail = models.URLField(blank=True)

    # External Data
    external_id = models.CharField(max_length=255, blank=True, unique=True)
    source = models.CharField(max_length=50, default='serp_api')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-rating', '-review_count']
        indexes = [
            models.Index(fields=['city', 'category']),
            models.Index(fields=['rating']),
        ]

    def __str__(self):
        return f"{self.name} - {self.city}"


class AttractionVisit(models.Model):
    """Track user visits/bookmarks for attractions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attraction_visits')
    attraction = models.ForeignKey(TouristAttraction, on_delete=models.CASCADE, related_name='visits')

    visit_date = models.DateField(null=True, blank=True)
    is_bookmarked = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'attraction']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.attraction.name}"
