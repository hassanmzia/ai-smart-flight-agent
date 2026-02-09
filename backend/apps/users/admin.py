from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile, TravelHistory


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""

    list_display = ['email', 'first_name', 'last_name', 'is_active', 'is_verified', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_verified', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-date_joined']
    readonly_fields = ['date_joined', 'last_login', 'created_at', 'updated_at']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('first_name', 'last_name', 'phone_number')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    def get_inline_instances(self, request, obj=None):
        """Only show inlines when editing existing user."""
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model."""

    list_display = [
        'user', 'nationality', 'preferred_currency', 'preferred_language',
        'total_trips', 'total_flights', 'total_hotel_nights'
    ]
    list_filter = ['preferred_currency', 'preferred_language', 'preferred_travel_class']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'nationality']
    readonly_fields = ['total_trips', 'total_flights', 'total_hotel_nights', 'created_at', 'updated_at']

    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Personal Information', {
            'fields': ('date_of_birth', 'nationality', 'passport_number', 'passport_expiry', 'avatar', 'bio')
        }),
        ('Travel Preferences', {
            'fields': (
                'preferred_currency', 'preferred_language', 'preferred_travel_class',
                'preferred_airlines', 'preferred_hotel_chains', 'seat_preference'
            )
        }),
        ('Loyalty Programs', {
            'fields': ('frequent_flyer_programs', 'hotel_loyalty_programs'),
            'classes': ('collapse',)
        }),
        ('Special Requirements', {
            'fields': ('dietary_restrictions', 'accessibility_needs'),
            'classes': ('collapse',)
        }),
        ('Travel Statistics', {
            'fields': (
                'total_trips', 'total_flights', 'total_hotel_nights',
                'countries_visited', 'cities_visited'
            )
        }),
        ('Notification Preferences', {
            'fields': ('email_notifications', 'sms_notifications', 'push_notifications'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(TravelHistory)
class TravelHistoryAdmin(admin.ModelAdmin):
    """Admin interface for TravelHistory model."""

    list_display = [
        'user', 'origin_city', 'destination_city', 'departure_date',
        'return_date', 'trip_type', 'number_of_travelers'
    ]
    list_filter = ['trip_type', 'departure_date', 'destination_country']
    search_fields = [
        'user__email', 'origin_city', 'destination_city',
        'origin_country', 'destination_country', 'booking_reference'
    ]
    date_hierarchy = 'departure_date'
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Trip Details', {
            'fields': (
                'origin_city', 'origin_country', 'destination_city', 'destination_country',
                'departure_date', 'return_date', 'trip_type', 'number_of_travelers'
            )
        }),
        ('Booking Information', {'fields': ('booking_reference', 'notes')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
