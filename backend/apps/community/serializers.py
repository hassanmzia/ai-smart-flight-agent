from rest_framework import serializers

from .models import (
    DestinationMedia,
    TravelStory,
    TravelTip,
    DestinationInfo,
    CuratedGuide,
    MediaComment,
    StoryComment,
    TipComment,
)


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


class ReactionFieldsMixin:
    """
    Exposes ``like_count``, ``dislike_count``, ``my_reaction`` (one of
    ``'like' | 'dislike' | null``), and ``comment_count`` on community
    models that have ``liked_by`` / ``disliked_by`` M2Ms and a reverse
    ``comments`` relation.
    """

    def get_like_count(self, obj):
        return obj.liked_by.count()

    def get_dislike_count(self, obj):
        return obj.disliked_by.count()

    def get_my_reaction(self, obj):
        request = self.context.get('request') if hasattr(self, 'context') else None
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            return None
        if obj.liked_by.filter(pk=user.pk).exists():
            return 'like'
        if obj.disliked_by.filter(pk=user.pk).exists():
            return 'dislike'
        return None

    def get_comment_count(self, obj):
        return obj.comments.count() if hasattr(obj, 'comments') else 0


class CommunityCommentSerializer(serializers.ModelSerializer):
    """Shared serializer for MediaComment / StoryComment / TipComment."""

    user = serializers.StringRelatedField(read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = None  # set by subclass
        fields = ['id', 'user', 'text', 'created_at', 'is_owner']
        read_only_fields = ['id', 'user', 'created_at', 'is_owner']

    def get_is_owner(self, obj):
        request = self.context.get('request') if hasattr(self, 'context') else None
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        return getattr(obj, 'user_id', None) == user.id


class MediaCommentSerializer(CommunityCommentSerializer):
    class Meta(CommunityCommentSerializer.Meta):
        model = MediaComment


class StoryCommentSerializer(CommunityCommentSerializer):
    class Meta(CommunityCommentSerializer.Meta):
        model = StoryComment


class TipCommentSerializer(CommunityCommentSerializer):
    class Meta(CommunityCommentSerializer.Meta):
        model = TipComment


class DestinationMediaSerializer(
    OwnerFlagMixin, ReactionFieldsMixin, serializers.ModelSerializer,
):
    """Serializer for DestinationMedia model."""

    user = serializers.StringRelatedField(read_only=True)
    media_type_display = serializers.CharField(
        source='get_media_type_display', read_only=True,
    )
    file = RelativeFileField()
    is_owner = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    dislike_count = serializers.SerializerMethodField()
    my_reaction = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = DestinationMedia
        fields = [
            'id', 'user', 'destination', 'media_type', 'media_type_display',
            'file', 'title', 'description', 'latitude', 'longitude',
            'tags', 'is_approved', 'upvotes', 'created_at', 'is_owner',
            'like_count', 'dislike_count', 'my_reaction', 'comment_count',
        ]
        read_only_fields = [
            'id', 'user', 'is_approved', 'upvotes', 'created_at', 'is_owner',
            'like_count', 'dislike_count', 'my_reaction', 'comment_count',
        ]


class TravelStorySerializer(
    OwnerFlagMixin, ReactionFieldsMixin, serializers.ModelSerializer,
):
    """Serializer for TravelStory model."""

    user = serializers.StringRelatedField(read_only=True)
    is_owner = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    dislike_count = serializers.SerializerMethodField()
    my_reaction = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = TravelStory
        fields = [
            'id', 'user', 'destination', 'title', 'content', 'language',
            'translated_content', 'cover_image', 'rating', 'is_approved',
            'upvotes', 'created_at', 'updated_at', 'is_owner',
            'like_count', 'dislike_count', 'my_reaction', 'comment_count',
        ]
        read_only_fields = [
            'id', 'user', 'is_approved', 'upvotes', 'translated_content',
            'created_at', 'updated_at', 'is_owner',
            'like_count', 'dislike_count', 'my_reaction', 'comment_count',
        ]


class TravelTipSerializer(
    OwnerFlagMixin, ReactionFieldsMixin, serializers.ModelSerializer,
):
    """Serializer for TravelTip model."""

    user = serializers.StringRelatedField(read_only=True)
    category_display = serializers.CharField(
        source='get_category_display', read_only=True,
    )
    is_owner = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    dislike_count = serializers.SerializerMethodField()
    my_reaction = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = TravelTip
        fields = [
            'id', 'user', 'destination', 'category', 'category_display',
            'title', 'content', 'is_approved', 'upvotes', 'created_at',
            'is_owner',
            'like_count', 'dislike_count', 'my_reaction', 'comment_count',
        ]
        read_only_fields = [
            'id', 'user', 'is_approved', 'upvotes', 'created_at', 'is_owner',
            'like_count', 'dislike_count', 'my_reaction', 'comment_count',
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
