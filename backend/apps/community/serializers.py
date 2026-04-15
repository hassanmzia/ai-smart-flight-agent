from rest_framework import serializers

from .models import DestinationMedia, TravelStory, TravelTip, DestinationInfo, CuratedGuide


class RelativeFileField(serializers.FileField):
    """
    FileField variant that always serializes to a **relative** URL
    (e.g. ``/media/community/media/photo.jpg``) instead of building an
    absolute URL via ``request.build_absolute_uri()``.

    DRF's default FileField.to_representation uses the request host, which
    in Docker / Vite-proxy / cloud deployments points to a hostname the
    browser cannot reach, resulting in ``ERR_CONNECTION_REFUSED``. Emitting
    a relative URL lets the same-origin Vite ``/media`` proxy handle it in
    dev and the same origin serve it in prod.
    """

    def to_representation(self, value):
        if not value:
            return None
        try:
            return value.url
        except (AttributeError, ValueError):
            return None


class OwnerFlagMixin:
    """
    Adds an ``is_owner`` boolean to the serialized output based on
    whether the requesting user created the object. Lets the frontend
    decide whether to render "Delete" / "Edit" controls without the
    serializer ever leaking raw user IDs.
    """

    def get_is_owner(self, obj):
        request = self.context.get('request') if hasattr(self, 'context') else None
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        return getattr(obj, 'user_id', None) == user.id


class DestinationMediaSerializer(OwnerFlagMixin, serializers.ModelSerializer):
    """Serializer for DestinationMedia model."""

    user = serializers.StringRelatedField(read_only=True)
    media_type_display = serializers.CharField(
        source='get_media_type_display', read_only=True,
    )
    file = RelativeFileField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = DestinationMedia
        fields = [
            'id', 'user', 'destination', 'media_type', 'media_type_display',
            'file', 'title', 'description', 'latitude', 'longitude',
            'tags', 'is_approved', 'upvotes', 'created_at', 'is_owner',
        ]
        read_only_fields = [
            'id', 'user', 'is_approved', 'upvotes', 'created_at', 'is_owner',
        ]


class TravelStorySerializer(OwnerFlagMixin, serializers.ModelSerializer):
    """Serializer for TravelStory model."""

    user = serializers.StringRelatedField(read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = TravelStory
        fields = [
            'id', 'user', 'destination', 'title', 'content', 'language',
            'translated_content', 'cover_image', 'rating', 'is_approved',
            'upvotes', 'created_at', 'updated_at', 'is_owner',
        ]
        read_only_fields = [
            'id', 'user', 'is_approved', 'upvotes', 'translated_content',
            'created_at', 'updated_at', 'is_owner',
        ]


class TravelTipSerializer(OwnerFlagMixin, serializers.ModelSerializer):
    """Serializer for TravelTip model."""

    user = serializers.StringRelatedField(read_only=True)
    category_display = serializers.CharField(
        source='get_category_display', read_only=True,
    )
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = TravelTip
        fields = [
            'id', 'user', 'destination', 'category', 'category_display',
            'title', 'content', 'is_approved', 'upvotes', 'created_at',
            'is_owner',
        ]
        read_only_fields = [
            'id', 'user', 'is_approved', 'upvotes', 'created_at', 'is_owner',
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


class CuratedGuideSerializer(serializers.ModelSerializer):
    """Serializer for CuratedGuide model."""

    guide_type_display = serializers.CharField(
        source='get_guide_type_display', read_only=True,
    )
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = CuratedGuide
        fields = [
            'id', 'destination', 'guide_type', 'guide_type_display',
            'title', 'description', 'items', 'item_count',
            'ai_generated', 'last_updated', 'created_at',
        ]
        read_only_fields = [
            'id', 'ai_generated', 'last_updated', 'created_at',
        ]

    def get_item_count(self, obj):
        if isinstance(obj.items, list):
            return len(obj.items)
        return 0
