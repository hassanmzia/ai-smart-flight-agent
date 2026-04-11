from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Booking, BookingItem, BookingStatus


class BookingItemSerializer(serializers.ModelSerializer):
    """Serializer for BookingItem model."""

    item_type_display = serializers.CharField(source='get_item_type_display', read_only=True)
    content_type = serializers.PrimaryKeyRelatedField(
        queryset=ContentType.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = BookingItem
        fields = [
            'id', 'item_type', 'item_type_display', 'item_name',
            'item_description', 'unit_price', 'quantity', 'total_price',
            'start_date', 'end_date', 'item_data',
            'content_type', 'object_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BookingStatusSerializer(serializers.ModelSerializer):
    """Serializer for BookingStatus model."""

    changed_by_email = serializers.EmailField(source='changed_by.email', read_only=True)

    class Meta:
        model = BookingStatus
        fields = [
            'id', 'old_status', 'new_status', 'changed_by_email',
            'reason', 'notes', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for Booking model."""

    items = BookingItemSerializer(many=True, read_only=True)
    status_history = BookingStatusSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    final_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_number', 'status', 'status_display', 'total_amount',
            'currency', 'tax_amount', 'discount_amount', 'final_amount',
            'primary_traveler_name', 'primary_traveler_email', 'primary_traveler_phone',
            'special_requests', 'notes', 'booking_date', 'confirmation_date',
            'cancellation_date', 'items', 'status_history', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'booking_number', 'booking_date', 'confirmation_date',
            'cancellation_date', 'created_at', 'updated_at'
        ]


class BookingListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for Booking list views."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_number', 'status', 'status_display', 'total_amount',
            'currency', 'primary_traveler_name', 'booking_date', 'notes', 'item_count'
        ]
        read_only_fields = ['id', 'booking_number', 'booking_date']

    def get_item_count(self, obj):
        return obj.items.count()


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bookings.

    Accepts both canonical field names (primary_traveler_name, etc.) and
    the shorter aliases used by the frontend (guest_name, guest_email, guest_phone).
    Item data can be provided as a nested ``items`` list **or** as flat fields
    (item_type, item_name / item_id, check_in, check_out).
    """

    items = BookingItemSerializer(many=True, required=False)

    # Accept frontend aliases
    guest_name = serializers.CharField(write_only=True, required=False)
    guest_email = serializers.EmailField(write_only=True, required=False)
    guest_phone = serializers.CharField(write_only=True, required=False)

    # Accept flat item fields sent by the frontend
    item_type = serializers.CharField(write_only=True, required=False)
    item_id = serializers.CharField(write_only=True, required=False)
    item_name = serializers.CharField(write_only=True, required=False)
    check_in = serializers.CharField(write_only=True, required=False)
    check_out = serializers.CharField(write_only=True, required=False)
    guests = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Booking
        fields = [
            'total_amount', 'currency', 'tax_amount', 'discount_amount',
            'primary_traveler_name', 'primary_traveler_email',
            'primary_traveler_phone', 'special_requests', 'notes', 'items',
            # Frontend aliases
            'guest_name', 'guest_email', 'guest_phone',
            'item_type', 'item_id', 'item_name', 'check_in', 'check_out', 'guests',
        ]
        extra_kwargs = {
            'primary_traveler_name': {'required': False},
            'primary_traveler_email': {'required': False},
            'primary_traveler_phone': {'required': False},
        }

    def create(self, validated_data):
        # Pop non-model fields
        items_data = validated_data.pop('items', [])
        guest_name = validated_data.pop('guest_name', '')
        guest_email = validated_data.pop('guest_email', '')
        guest_phone = validated_data.pop('guest_phone', '')
        item_type = validated_data.pop('item_type', '')
        item_id = validated_data.pop('item_id', '')
        flat_item_name = validated_data.pop('item_name', '')
        check_in = validated_data.pop('check_in', None)
        check_out = validated_data.pop('check_out', None)
        guests = validated_data.pop('guests', 1)

        # Map frontend aliases to model fields (alias wins if canonical field is empty)
        if not validated_data.get('primary_traveler_name'):
            validated_data['primary_traveler_name'] = guest_name or 'Guest'
        if not validated_data.get('primary_traveler_email'):
            validated_data['primary_traveler_email'] = guest_email or 'guest@example.com'
        if not validated_data.get('primary_traveler_phone'):
            validated_data['primary_traveler_phone'] = guest_phone or ''

        booking = Booking.objects.create(**validated_data)

        # Create nested items
        for item_data in items_data:
            BookingItem.objects.create(booking=booking, **item_data)

        # Create a booking item from flat fields if present
        if item_type:
            BookingItem.objects.create(
                booking=booking,
                item_type=item_type,
                item_name=flat_item_name or f'{item_type} #{item_id}',
                unit_price=validated_data.get('total_amount', 0),
                quantity=guests or 1,
                total_price=validated_data.get('total_amount', 0),
                start_date=check_in,
                end_date=check_out,
                item_data={'external_id': item_id, 'guests': guests},
            )

        return booking
