import uuid
from django.conf import settings
from django.db import models


class UserContact(models.Model):
    """
    A friend or family member the user added manually.
    The contact does NOT need an account in this app.

    Future-proof fields (linked_user, invite_status, invite_code) let us
    upgrade to mutual visibility if the contact creates an account later.
    """

    RELATIONSHIP_CHOICES = [
        ('friend', 'Friend'),
        ('family', 'Family'),
        ('colleague', 'Colleague'),
        ('other', 'Other'),
    ]

    INVITE_STATUS_CHOICES = [
        ('none', 'None'),
        ('invited', 'Invited'),
        ('accepted', 'Accepted'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contacts',
    )
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    country = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=500, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    relationship = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_CHOICES,
        default='friend',
    )
    notes = models.TextField(blank=True)

    # Geocoded coordinates (populated on save via Nominatim)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # ---- Future-proof: account linking ----
    linked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_contacts',
    )
    invite_status = models.CharField(
        max_length=10,
        choices=INVITE_STATUS_CHOICES,
        default='none',
    )
    invite_code = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        unique=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_contacts'
        ordering = ['name']
        indexes = [
            models.Index(fields=['owner', 'city']),
        ]

    def __str__(self):
        return f"{self.name} ({self.city}) — {self.get_relationship_display()}"

    def save(self, *args, **kwargs):
        # Generate invite_code on first save
        if not self.invite_code:
            self.invite_code = str(uuid.uuid4())
        super().save(*args, **kwargs)
