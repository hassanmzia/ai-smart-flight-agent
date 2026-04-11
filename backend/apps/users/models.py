from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with email authentication."""

    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name


class UserProfile(models.Model):
    """Extended user profile with travel preferences and history."""

    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('CAD', 'Canadian Dollar'),
        ('AUD', 'Australian Dollar'),
        ('JPY', 'Japanese Yen'),
        ('CNY', 'Chinese Yuan'),
        ('INR', 'Indian Rupee'),
    ]

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('it', 'Italian'),
        ('pt', 'Portuguese'),
        ('zh', 'Chinese'),
        ('ja', 'Japanese'),
    ]

    TRAVEL_CLASS_CHOICES = [
        ('economy', 'Economy'),
        ('premium_economy', 'Premium Economy'),
        ('business', 'Business'),
        ('first', 'First Class'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    passport_number = models.CharField(max_length=50, blank=True)
    passport_expiry = models.DateField(null=True, blank=True)

    # Travel Preferences
    preferred_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    preferred_language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    preferred_travel_class = models.CharField(
        max_length=20,
        choices=TRAVEL_CLASS_CHOICES,
        default='economy'
    )
    preferred_airlines = models.JSONField(default=list, blank=True)
    preferred_hotel_chains = models.JSONField(default=list, blank=True)

    # Loyalty Programs
    frequent_flyer_programs = models.JSONField(default=dict, blank=True)
    hotel_loyalty_programs = models.JSONField(default=dict, blank=True)

    # Preferences
    dietary_restrictions = models.JSONField(default=list, blank=True)
    accessibility_needs = models.TextField(blank=True)
    seat_preference = models.CharField(
        max_length=20,
        choices=[('window', 'Window'), ('aisle', 'Aisle'), ('any', 'Any')],
        default='any'
    )

    # Travel Stats
    total_trips = models.IntegerField(default=0)
    total_flights = models.IntegerField(default=0)
    total_hotel_nights = models.IntegerField(default=0)
    countries_visited = models.JSONField(default=list, blank=True)
    cities_visited = models.JSONField(default=list, blank=True)

    # Notification Preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)

    # Profile
    avatar = models.CharField(max_length=500, blank=True)
    bio = models.TextField(blank=True, max_length=500)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        ordering = ['-created_at']
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"Profile for {self.user.email}"

    def increment_travel_stats(self, flights=0, hotel_nights=0):
        """Increment travel statistics."""
        self.total_flights += flights
        self.total_hotel_nights += hotel_nights
        if flights > 0 or hotel_nights > 0:
            self.total_trips += 1
        self.save()


class TravelHistory(models.Model):
    """Track user's travel history."""

    TRIP_TYPE_CHOICES = [
        ('business', 'Business'),
        ('leisure', 'Leisure'),
        ('both', 'Both'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_history')

    destination_city = models.CharField(max_length=200)
    destination_country = models.CharField(max_length=100)
    origin_city = models.CharField(max_length=200)
    origin_country = models.CharField(max_length=100)

    departure_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)

    trip_type = models.CharField(max_length=20, choices=TRIP_TYPE_CHOICES, default='leisure')
    number_of_travelers = models.IntegerField(default=1)

    # Associated bookings
    booking_reference = models.CharField(max_length=50, blank=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'travel_history'
        ordering = ['-departure_date']
        verbose_name = 'Travel History'
        verbose_name_plural = 'Travel Histories'
        indexes = [
            models.Index(fields=['user', '-departure_date']),
            models.Index(fields=['destination_country']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.origin_city} to {self.destination_city} ({self.departure_date})"
