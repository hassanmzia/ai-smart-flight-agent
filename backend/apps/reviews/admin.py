from django.contrib import admin
from django.utils.html import format_html
from .models import Review, Rating, AIRating


class RatingInline(admin.TabularInline):
    """Inline admin for Rating."""
    model = Rating
    extra = 0


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin interface for Review model."""
    list_display = [
        'title', 'user', 'rating_badge', 'status_badge',
        'is_verified_purchase', 'helpful_count', 'created_at'
    ]
    list_filter = ['status', 'rating', 'is_verified_purchase', 'created_at']
    search_fields = ['title', 'content', 'user__email']
    date_hierarchy = 'created_at'
    readonly_fields = ['helpful_count', 'not_helpful_count', 'created_at', 'updated_at']
    inlines = [RatingInline]

    actions = ['approve_reviews', 'reject_reviews']

    def rating_badge(self, obj):
        """Display rating with stars."""
        full_stars = int(obj.rating)
        stars = '⭐' * full_stars
        return format_html('<span>{} {}/5</span>', stars, obj.rating)
    rating_badge.short_description = 'Rating'

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'pending': '#ffc107',
            'approved': '#198754',
            'rejected': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def approve_reviews(self, request, queryset):
        """Approve selected reviews."""
        from django.utils import timezone
        queryset.update(
            status='approved',
            moderated_by=request.user,
            moderated_at=timezone.now()
        )
    approve_reviews.short_description = "Approve selected reviews"

    def reject_reviews(self, request, queryset):
        """Reject selected reviews."""
        from django.utils import timezone
        queryset.update(
            status='rejected',
            moderated_by=request.user,
            moderated_at=timezone.now()
        )
    reject_reviews.short_description = "Reject selected reviews"


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    """Admin interface for Rating model."""
    list_display = ['review', 'aspect', 'score']
    list_filter = ['aspect']
    search_fields = ['review__title']


@admin.register(AIRating)
class AIRatingAdmin(admin.ModelAdmin):
    """Admin interface for AI-generated quality ratings."""
    list_display = [
        'entity_name', 'entity_type', 'destination',
        'overall_score_badge', 'safety_score', 'value_score',
        'review_count', 'ai_generated', 'last_updated',
    ]
    list_filter = ['entity_type', 'ai_generated', 'destination']
    search_fields = ['entity_name', 'destination']
    readonly_fields = [
        'overall_score', 'safety_score', 'value_score',
        'food_score', 'culture_score', 'accessibility_score',
        'community_rating', 'review_count', 'summary',
        'pros', 'cons', 'best_for', 'enjoyment_factors',
        'ai_generated', 'last_updated', 'created_at',
    ]
    date_hierarchy = 'created_at'

    def overall_score_badge(self, obj):
        """Display overall score with color coding."""
        score = float(obj.overall_score)
        if score >= 8.0:
            color = '#198754'
        elif score >= 6.0:
            color = '#ffc107'
        else:
            color = '#dc3545'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}/10</span>',
            color, obj.overall_score,
        )
    overall_score_badge.short_description = 'Overall Score'
