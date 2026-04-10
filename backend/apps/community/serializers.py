from rest_framework import serializers

from .models import DestinationMedia, TravelStory, TravelTip, DestinationInfo


class DestinationMediaSerializer(serializers.ModelSerializer):
    """Serializer for DestinationMedia model."""

    user = serializers.StringRelatedField(read_only=True)
    media_type_display = serializers.CharField(
        source='get_media_type_display', read_only=True,
    )

    class Meta:
        model = DestinationMedia
        fields = [
            'id', 'user', 'destination', 'media_type', 'media_type_display',
            'file', 'title', 'description', 'latitude', 'longitude',
            'tags', 'is_approved', 'upvotes', 'created_at',
        ]
        read_only_fields = [
            'id', 'user', 'is_approved', 'upvotes', 'created_at',
        ]


class TravelStorySerializer(serializers.ModelSerializer):
    """Serializer for TravelStory model."""

    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = TravelStory
        fields = [
            'id', 'user', 'destination', 'title', 'content', 'language',
            'translated_content', 'cover_image', 'rating', 'is_approved',
            'upvotes', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'user', 'is_approved', 'upvotes', 'translated_content',
            'created_at', 'updated_at',
        ]


class TravelTipSerializer(serializers.ModelSerializer):
    """Serializer for TravelTip model."""

    user = serializers.StringRelatedField(read_only=True)
    category_display = serializers.CharField(
        source='get_category_display', read_only=True,
    )

    class Meta:
        model = TravelTip
        fields = [
            'id', 'user', 'destination', 'category', 'category_display',
            'title', 'content', 'is_approved', 'upvotes', 'created_at',
        ]
        read_only_fields = [
            'id', 'user', 'is_approved', 'upvotes', 'created_at',
        ]


class DestinationInfoSerializer(serializers.ModelSerializer):
    """Serializer for DestinationInfo model."""

    class Meta:
        model = DestinationInfo
        fields = [
            'id', 'destination', 'country', 'summary', 'history', 'culture',
            'customs_etiquette', 'dress_code', 'religion_info', 'festivals',
            'local_language', 'common_phrases', 'currency', 'emergency_numbers',
            'official_tourism_url', 'ai_generated', 'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']
