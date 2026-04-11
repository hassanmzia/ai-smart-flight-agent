from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Booking(models.Model):
    """Main booking model for all types of travel bookings."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    booking_number = models.CharField(max_length=50, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Financial
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3, default='USD')
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Traveler information
    primary_traveler_name = models.CharField(max_length=255)
    primary_traveler_email = models.EmailField()
    primary_traveler_phone = models.CharField(max_length=20)

    # Special requests
    special_requests = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    # Timestamps
    booking_date = models.DateTimeField(auto_now_add=True)
    confirmation_date = models.DateTimeField(null=True, blank=True)
    cancellation_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings'
        ordering = ['-booking_date']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        indexes = [
            models.Index(fields=['user', '-booking_date']),
            models.Index(fields=['booking_number']),
            models.Index(fields=['status', '-booking_date']),
        ]

    def __str__(self):
        return f"{self.booking_number} - {self.user.email} ({self.status})"

    def save(self, *args, **kwargs):
        """Generate booking number if not set."""
        if not self.booking_number:
            self.booking_number = f"BK{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def final_amount(self):
        """Calculate final amount after tax and discount."""
        return self.total_amount + self.tax_amount - self.discount_amount


class BookingItem(models.Model):
    """Polymorphic booking item for flights, hotels, cars, etc."""

    ITEM_TYPE_CHOICES = [
        ('flight', 'Flight'),
        ('hotel', 'Hotel'),
        ('rental', 'Vacation Rental'),
        ('car', 'Car Rental'),
        ('attraction', 'Attraction'),
        ('restaurant', 'Restaurant'),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='items')

    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)

    # Generic relation to the actual item (Flight, Hotel, etc.)
    # Nullable because booking items may reference external services without local DB records.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Item details
    item_name = models.CharField(max_length=500)
    item_description = models.TextField(blank=True)

    # Pricing
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Dates (flexible for different item types)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    # Additional data specific to item type
    item_data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'booking_items'
        ordering = ['start_date']
        verbose_name = 'Booking Item'
        verbose_name_plural = 'Booking Items'
        indexes = [
            models.Index(fields=['booking', 'item_type']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.booking.booking_number} - {self.item_type}: {self.item_name}"


class BookingStatus(models.Model):
    """Track booking status changes for history."""

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='status_history')

    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='booking_status_changes'
    )

    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'booking_status_history'
        ordering = ['-timestamp']
        verbose_name = 'Booking Status'
        verbose_name_plural = 'Booking Status History'

    def __str__(self):
        return f"{self.booking.booking_number}: {self.old_status} → {self.new_status}"
