from django.contrib import admin

from .models import DestinationMedia, TravelStory, TravelTip, DestinationInfo


@admin.register(DestinationMedia)
class DestinationMediaAdmin(admin.ModelAdmin):
    """Admin interface for DestinationMedia model."""

    list_display = [
        'title', 'user', 'destination', 'media_type', 'is_approved',
        'upvotes', 'created_at',
    ]
    list_filter = ['media_type', 'is_approved', 'created_at']
    search_fields = ['title', 'description', 'destination', 'user__email']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    actions = ['approve_media', 'reject_media']

    def approve_media(self, request, queryset):
        queryset.update(is_approved=True)
    approve_media.short_description = "Approve selected media"

    def reject_media(self, request, queryset):
        queryset.update(is_approved=False)
    reject_media.short_description = "Reject selected media"


@admin.register(TravelStory)
class TravelStoryAdmin(admin.ModelAdmin):
    """Admin interface for TravelStory model."""

    list_display = [
        'title', 'user', 'destination', 'language', 'rating',
        'is_approved', 'upvotes', 'created_at',
    ]
    list_filter = ['is_approved', 'language', 'created_at']
    search_fields = ['title', 'content', 'destination', 'user__email']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_stories', 'reject_stories']

    def approve_stories(self, request, queryset):
        queryset.update(is_approved=True)
    approve_stories.short_description = "Approve selected stories"

    def reject_stories(self, request, queryset):
        queryset.update(is_approved=False)
    reject_stories.short_description = "Reject selected stories"


@admin.register(TravelTip)
class TravelTipAdmin(admin.ModelAdmin):
    """Admin interface for TravelTip model."""

    list_display = [
        'title', 'user', 'destination', 'category', 'is_approved',
        'upvotes', 'created_at',
    ]
    list_filter = ['category', 'is_approved', 'created_at']
    search_fields = ['title', 'content', 'destination', 'user__email']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    actions = ['approve_tips', 'reject_tips']

    def approve_tips(self, request, queryset):
        queryset.update(is_approved=True)
    approve_tips.short_description = "Approve selected tips"

    def reject_tips(self, request, queryset):
        queryset.update(is_approved=False)
    reject_tips.short_description = "Reject selected tips"


@admin.register(DestinationInfo)
class DestinationInfoAdmin(admin.ModelAdmin):
    """Admin interface for DestinationInfo model."""

    list_display = [
        'destination', 'country', 'ai_generated', 'updated_at',
    ]
    list_filter = ['ai_generated', 'country']
    search_fields = ['destination', 'country', 'summary']
    readonly_fields = ['updated_at']
