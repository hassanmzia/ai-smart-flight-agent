from rest_framework import serializers
from .models import Itinerary, ItineraryDay, ItineraryItem, Weather


class ItineraryItemSerializer(serializers.ModelSerializer):
    """Serializer for ItineraryItem model."""
    item_type_display = serializers.CharField(source='get_item_type_display', read_only=True)

    class Meta:
        model = ItineraryItem
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ItineraryDaySerializer(serializers.ModelSerializer):
    """Serializer for ItineraryDay model."""
    items = ItineraryItemSerializer(many=True, read_only=True)

    class Meta:
        model = ItineraryDay
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ItinerarySerializer(serializers.ModelSerializer):
    """Serializer for Itinerary model."""
    days = ItineraryDaySerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = Itinerary
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class WeatherSerializer(serializers.ModelSerializer):
    """Serializer for Weather model."""

    class Meta:
        model = Weather
        fields = '__all__'
        read_only_fields = ['id', 'fetched_at']
