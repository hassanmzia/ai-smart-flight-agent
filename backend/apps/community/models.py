from django.db import models
from django.conf import settings


class DestinationMedia(models.Model):
    """User-uploaded media (photos, audio, PDFs, videos) for destinations."""

    MEDIA_TYPE_CHOICES = [
        ('photo', 'Photo'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('document', 'Document'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_media',
    )
    destination = models.CharField(max_length=200, db_index=True)
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES)
    file = models.FileField(upload_to='community/media/')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
    )
    tags = models.JSONField(default=list)
    is_approved = models.BooleanField(default=False)
    upvotes = models.IntegerField(default=0)
    liked_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='liked_community_media',
        blank=True,
    )
    disliked_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='disliked_community_media',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'community_destination_media'
        ordering = ['-created_at']
        verbose_name = 'Destination Media'
        verbose_name_plural = 'Destination Media'
        indexes = [
            models.Index(fields=['destination', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['media_type']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_media_type_display()}) - {self.destination}"


class TravelStory(models.Model):
    """Short travel stories written by users."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='travel_stories',
    )
    destination = models.CharField(max_length=200, db_index=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    language = models.CharField(max_length=10, default='en')
    translated_content = models.TextField(blank=True)
    cover_image = models.URLField(blank=True)
    rating = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True,
    )
    is_approved = models.BooleanField(default=False)
    upvotes = models.IntegerField(default=0)
    liked_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='liked_travel_stories',
        blank=True,
    )
    disliked_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='disliked_travel_stories',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'community_travel_stories'
        ordering = ['-created_at']
        verbose_name = 'Travel Story'
        verbose_name_plural = 'Travel Stories'
        indexes = [
            models.Index(fields=['destination', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['language']),
        ]

    def __str__(self):
        return f"{self.title} - {self.destination} by {self.user}"


class TravelTip(models.Model):
    """Tips and tricks for destinations."""

    CATEGORY_CHOICES = [
        ('money_saving', 'Money Saving'),
        ('safety', 'Safety'),
        ('food', 'Food'),
        ('transport', 'Transport'),
        ('culture', 'Culture'),
        ('general', 'General'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='travel_tips',
    )
    destination = models.CharField(max_length=200, db_index=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_approved = models.BooleanField(default=False)
    upvotes = models.IntegerField(default=0)
    liked_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='liked_travel_tips',
        blank=True,
    )
    disliked_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='disliked_travel_tips',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'community_travel_tips'
        ordering = ['-created_at']
        verbose_name = 'Travel Tip'
        verbose_name_plural = 'Travel Tips'
        indexes = [
            models.Index(fields=['destination', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_category_display()}) - {self.destination}"


class DestinationInfo(models.Model):
    """Curated destination knowledge, often AI-generated."""

    destination = models.CharField(max_length=200, unique=True, db_index=True)
    country = models.CharField(max_length=100)
    summary = models.TextField()
    history = models.TextField(blank=True)
    culture = models.TextField(blank=True)
    customs_etiquette = models.TextField(blank=True)
    dress_code = models.TextField(blank=True)
    religion_info = models.TextField(blank=True)
    festivals = models.JSONField(default=list)
    local_language = models.CharField(max_length=100, blank=True)
    common_phrases = models.JSONField(default=dict)
    currency = models.CharField(max_length=50, blank=True)
    emergency_numbers = models.JSONField(default=dict)
    official_tourism_url = models.URLField(blank=True)
    ai_generated = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'community_destination_info'
        ordering = ['destination']
        verbose_name = 'Destination Info'
        verbose_name_plural = 'Destination Info'

    def __str__(self):
        return f"{self.destination}, {self.country}"


class CuratedGuide(models.Model):
    """AI-curated must-visit/eat/see lists per destination."""

    GUIDE_TYPE_CHOICES = [
        ('must_visit', 'Must Visit'),
        ('must_eat', 'Must Eat'),
        ('must_see', 'Must See'),
        ('must_do', 'Must Do'),
        ('hidden_gem', 'Hidden Gem'),
    ]

    destination = models.CharField(max_length=200, db_index=True)
    guide_type = models.CharField(max_length=20, choices=GUIDE_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    items = models.JSONField(
        default=list,
        help_text=(
            'Array of {name, description, rating, price_range, '
            'best_time, address, website_url, image_url, tags}'
        ),
    )
    ai_generated = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'community_curated_guides'
        unique_together = ['destination', 'guide_type']
        ordering = ['destination', 'guide_type']
        verbose_name = 'Curated Guide'
        verbose_name_plural = 'Curated Guides'

    def __str__(self):
        return f"{self.get_guide_type_display()} - {self.destination}"


class BaseCommunityComment(models.Model):
    """
    Abstract base for a user comment attached to a piece of community
    content (media, story, tip). Subclasses only need to declare the
    parent FK named ``parent``.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='+',
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def __str__(self):
        preview = (self.text or '')[:40]
        return f"{self.user} · {preview}"


class MediaComment(BaseCommunityComment):
    parent = models.ForeignKey(
        DestinationMedia,
        on_delete=models.CASCADE,
        related_name='comments',
    )

    class Meta(BaseCommunityComment.Meta):
        db_table = 'community_media_comments'
        verbose_name = 'Media Comment'
        verbose_name_plural = 'Media Comments'


class StoryComment(BaseCommunityComment):
    parent = models.ForeignKey(
        TravelStory,
        on_delete=models.CASCADE,
        related_name='comments',
    )

    class Meta(BaseCommunityComment.Meta):
        db_table = 'community_story_comments'
        verbose_name = 'Story Comment'
        verbose_name_plural = 'Story Comments'


class TipComment(BaseCommunityComment):
    parent = models.ForeignKey(
        TravelTip,
        on_delete=models.CASCADE,
        related_name='comments',
    )

    class Meta(BaseCommunityComment.Meta):
        db_table = 'community_tip_comments'
        verbose_name = 'Tip Comment'
        verbose_name_plural = 'Tip Comments'
