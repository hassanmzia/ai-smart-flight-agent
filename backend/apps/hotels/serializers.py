from rest_framework import serializers
from .models import Hotel, HotelAmenity, HotelSearch


class HotelAmenitySerializer(serializers.ModelSerializer):
    """Serializer for HotelAmenity model."""

    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = HotelAmenity
        fields = [
            'id', 'name', 'category', 'category_display', 'description',
            'icon', 'is_free', 'additional_cost'
        ]
        read_only_fields = ['id']


class HotelSerializer(serializers.ModelSerializer):
    """Serializer for Hotel model — includes vacation rental fields."""

    amenities = HotelAmenitySerializer(many=True, read_only=True)
    star_rating_display = serializers.CharField(source='get_star_rating_display', read_only=True)
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)
    distance_km = serializers.SerializerMethodField()
    is_rental = serializers.BooleanField(read_only=True)
    cancellation_policy_display = serializers.CharField(
        source='get_cancellation_policy_display', read_only=True
    )

    class Meta:
        model = Hotel
        fields = [
            'id', 'name', 'chain', 'brand', 'address', 'city', 'state_province',
            'country', 'postal_code', 'latitude', 'longitude', 'star_rating',
            'star_rating_display', 'guest_rating', 'review_count', 'property_type',
            'property_type_display', 'total_rooms', 'check_in_time', 'check_out_time',
            'description', 'short_description', 'phone', 'email', 'website',
            'primary_image', 'images', 'price_range_min', 'price_range_max',
            'currency', 'is_active', 'is_featured', 'amenities', 'distance_km',
            # Vacation rental fields
            'is_rental', 'is_entire_property', 'bedrooms', 'bathrooms', 'beds',
            'max_guests', 'has_kitchen', 'has_washer_dryer', 'has_parking',
            'has_pool', 'pet_friendly', 'pricing_model', 'cleaning_fee',
            'service_fee_percent', 'minimum_stay_nights', 'host_name',
            'host_response_rate', 'is_superhost', 'house_rules',
            'cancellation_policy', 'cancellation_policy_display',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'review_count', 'created_at', 'updated_at']

    def get_distance_km(self, obj):
        """Calculate distance from search location if provided in context."""
        return None


class HotelListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for Hotel list views — includes rental summary."""

    star_rating_display = serializers.CharField(source='get_star_rating_display', read_only=True)
    amenity_count = serializers.SerializerMethodField()

    # Frontend compatibility fields
    stars = serializers.IntegerField(source='star_rating', read_only=True)
    rating = serializers.FloatField(source='guest_rating', read_only=True)
    pricePerNight = serializers.FloatField(source='price_range_min', read_only=True)
    amenities = serializers.SerializerMethodField()
    distanceFromCenter = serializers.SerializerMethodField()

    # Rental summary fields
    is_rental = serializers.BooleanField(read_only=True)
    is_entire_property = serializers.BooleanField(read_only=True)
    bedrooms = serializers.IntegerField(read_only=True)
    max_guests = serializers.IntegerField(read_only=True)
    pricing_model = serializers.CharField(read_only=True)
    cleaning_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_superhost = serializers.BooleanField(read_only=True)
    pet_friendly = serializers.BooleanField(read_only=True)
    has_kitchen = serializers.BooleanField(read_only=True)
    has_pool = serializers.BooleanField(read_only=True)

    class Meta:
        model = Hotel
        fields = [
            'id', 'name', 'city', 'country', 'address', 'star_rating', 'star_rating_display',
            'guest_rating', 'review_count', 'property_type', 'primary_image',
            'price_range_min', 'price_range_max', 'currency', 'amenity_count',
            'stars', 'rating', 'pricePerNight', 'images', 'amenities', 'distanceFromCenter',
            # Rental fields
            'is_rental', 'is_entire_property', 'bedrooms', 'max_guests',
            'pricing_model', 'cleaning_fee', 'is_superhost', 'pet_friendly',
            'has_kitchen', 'has_pool',
        ]

    def get_amenity_count(self, obj):
        """Get count of amenities."""
        return obj.amenities.count()

    def get_amenities(self, obj):
        """Get list of amenity names for frontend compatibility."""
        return list(obj.amenities.values_list('name', flat=True))[:5]  # Limit to 5 for list view

    def get_distanceFromCenter(self, obj):
        """Get distance from city center (placeholder)."""
        # This would calculate actual distance if we had city center coordinates
        # For now, return a placeholder value
        return 2.5  # km


class HotelSearchSerializer(serializers.ModelSerializer):
    """Serializer for HotelSearch model."""

    total_guests = serializers.IntegerField(read_only=True)

    class Meta:
        model = HotelSearch
        fields = [
            'id', 'city', 'country', 'check_in_date', 'check_out_date',
            'nights', 'rooms', 'adults', 'children', 'total_guests',
            'min_star_rating', 'min_guest_rating', 'property_types',
            'amenities', 'max_price_per_night', 'results_count',
            'search_duration_ms', 'created_at'
        ]
        read_only_fields = ['id', 'results_count', 'search_duration_ms', 'created_at']


class HotelSearchCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating hotel searches."""

    class Meta:
        model = HotelSearch
        fields = [
            'city', 'country', 'check_in_date', 'check_out_date',
            'rooms', 'adults', 'children', 'min_star_rating',
            'min_guest_rating', 'property_types', 'amenities',
            'max_price_per_night',
            # Rental-specific filters
            'include_rentals', 'include_hotels', 'min_bedrooms',
            'min_bathrooms', 'entire_property_only', 'pet_friendly_only',
        ]

    def validate(self, data):
        """Validate search parameters."""
        from django.utils import timezone

        # Validate check-in date is in the future
        if data.get('check_in_date') < timezone.now().date():
            raise serializers.ValidationError({
                'check_in_date': 'Check-in date must be in the future.'
            })

        # Validate check-out date is after check-in date
        if data.get('check_out_date') <= data.get('check_in_date'):
            raise serializers.ValidationError({
                'check_out_date': 'Check-out date must be after check-in date.'
            })

        return data

    def create(self, validated_data):
        """Calculate nights when creating search."""
        check_in = validated_data['check_in_date']
        check_out = validated_data['check_out_date']
        validated_data['nights'] = (check_out - check_in).days
        return super().create(validated_data)
