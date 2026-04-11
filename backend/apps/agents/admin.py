from django.contrib import admin
from django.utils.html import format_html
from .models import (
    AgentSession, AgentExecution, AgentLog,
    AgentConversation, AgentMessage, AgentTask, UserPreference,
    AgentAnalytics, AIModel, TripCollaboration, TripCollaborator,
    CollaborationVote, Subscription, AffiliateClick, PriceWatch,
    TripMemory,
    # Phase 5: Monetization & Partnerships
    PartnerBusiness, PartnerCoupon, CouponRedemption,
    ReferralCode, Referral,
    DestinationKnowledge, CulturalInfo, UserDestinationTip,
    # Phase 6: Social & Viral Growth
    TravelStoryGenerated, StoryLike, StoryComment,
    TripTemplate, TemplateClone, ContentItem,
    # Phase 7: Faith & Health Awareness
    PrayerTimeCache, WorshipPlace, SpiritualSite,
    MedicalFacility, AccessibilityRating, MedicationReminder,
    HealthInsuranceInfo,
)


class AgentExecutionInline(admin.TabularInline):
    """Inline admin for AgentExecution."""

    model = AgentExecution
    extra = 0
    fields = ['execution_id', 'agent_type', 'status', 'tokens_used', 'execution_time_ms', 'cost']
    readonly_fields = ['execution_id', 'tokens_used', 'execution_time_ms', 'cost']
    can_delete = False


class AgentLogInline(admin.TabularInline):
    """Inline admin for AgentLog."""

    model = AgentLog
    extra = 0
    fields = ['log_level', 'agent_type', 'message', 'timestamp']
    readonly_fields = ['log_level', 'agent_type', 'message', 'timestamp']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AgentSession)
class AgentSessionAdmin(admin.ModelAdmin):
    """Admin interface for AgentSession model."""

    list_display = [
        'session_id', 'user', 'status', 'total_executions',
        'total_tokens_used', 'total_cost', 'started_at', 'duration'
    ]
    list_filter = ['status', 'started_at']
    search_fields = ['session_id', 'user__email', 'user_intent']
    readonly_fields = [
        'session_id', 'total_executions', 'total_tokens_used', 'total_cost',
        'started_at', 'completed_at', 'last_activity_at', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'started_at'
    inlines = [AgentExecutionInline, AgentLogInline]

    fieldsets = (
        ('Session Info', {
            'fields': ('user', 'session_id', 'status')
        }),
        ('Context & Intent', {
            'fields': ('user_intent', 'conversation_context', 'detected_entities'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('total_executions', 'total_tokens_used', 'total_cost')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at', 'last_activity_at', 'created_at', 'updated_at')
        }),
    )

    def duration(self, obj):
        """Calculate and display session duration."""
        if obj.started_at and obj.completed_at:
            duration = obj.completed_at - obj.started_at
            seconds = duration.total_seconds()
            if seconds < 60:
                return f"{seconds:.1f}s"
            elif seconds < 3600:
                return f"{seconds/60:.1f}m"
            else:
                return f"{seconds/3600:.1f}h"
        return "-"
    duration.short_description = 'Duration'

    def has_add_permission(self, request):
        """Disable manual creation through admin."""
        return False


@admin.register(AgentExecution)
class AgentExecutionAdmin(admin.ModelAdmin):
    """Admin interface for AgentExecution model."""

    list_display = [
        'execution_id', 'session', 'agent_type', 'status_badge',
        'tokens_used', 'execution_time', 'cost', 'started_at'
    ]
    list_filter = ['agent_type', 'status', 'started_at']
    search_fields = ['execution_id', 'session__session_id', 'agent_type']
    readonly_fields = [
        'execution_id', 'execution_time_ms', 'started_at', 'completed_at',
        'created_at', 'updated_at'
    ]
    date_hierarchy = 'started_at'
    inlines = [AgentLogInline]

    fieldsets = (
        ('Execution Info', {
            'fields': ('session', 'execution_id', 'agent_type', 'status')
        }),
        ('Input/Output', {
            'fields': ('input_data', 'output_data', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Configuration', {
            'fields': ('agent_config', 'model_used'),
            'classes': ('collapse',)
        }),
        ('Performance Metrics', {
            'fields': ('tokens_used', 'execution_time_ms', 'cost', 'tools_called', 'function_calls')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at', 'created_at', 'updated_at')
        }),
    )

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'pending': '#6c757d',
            'running': '#0dcaf0',
            'completed': '#198754',
            'failed': '#dc3545',
            'timeout': '#ffc107',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def execution_time(self, obj):
        """Display execution time in human-readable format."""
        if obj.execution_time_ms:
            if obj.execution_time_ms < 1000:
                return f"{obj.execution_time_ms}ms"
            else:
                return f"{obj.execution_time_ms/1000:.2f}s"
        return "-"
    execution_time.short_description = 'Exec Time'

    def has_add_permission(self, request):
        """Disable manual creation through admin."""
        return False


@admin.register(AgentLog)
class AgentLogAdmin(admin.ModelAdmin):
    """Admin interface for AgentLog model."""

    list_display = [
        'timestamp', 'log_level_badge', 'agent_type',
        'function_name', 'short_message', 'session', 'execution'
    ]
    list_filter = ['log_level', 'agent_type', 'timestamp']
    search_fields = ['message', 'agent_type', 'function_name', 'session__session_id']
    readonly_fields = [
        'session', 'execution', 'log_level', 'message', 'log_data',
        'agent_type', 'function_name', 'line_number', 'exception_type',
        'exception_traceback', 'timestamp', 'created_at'
    ]
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Log Info', {
            'fields': ('log_level', 'agent_type', 'message')
        }),
        ('Context', {
            'fields': ('session', 'execution', 'function_name', 'line_number')
        }),
        ('Data', {
            'fields': ('log_data',),
            'classes': ('collapse',)
        }),
        ('Exception Details', {
            'fields': ('exception_type', 'exception_traceback'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('timestamp', 'created_at')
        }),
    )

    def log_level_badge(self, obj):
        """Display log level as colored badge."""
        colors = {
            'debug': '#6c757d',
            'info': '#0dcaf0',
            'warning': '#ffc107',
            'error': '#dc3545',
            'critical': '#8b0000',
        }
        color = colors.get(obj.log_level, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.log_level.upper()
        )
    log_level_badge.short_description = 'Level'

    def short_message(self, obj):
        """Display truncated message."""
        if len(obj.message) > 100:
            return f"{obj.message[:100]}..."
        return obj.message
    short_message.short_description = 'Message'

    def has_add_permission(self, request):
        """Disable manual creation through admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Make logs read-only."""
        return False


# ─────────────────────────────────────────────────
# Commercialization Models Admin
# ─────────────────────────────────────────────────

class AgentMessageInline(admin.TabularInline):
    model = AgentMessage
    extra = 0
    fields = ['sender_type', 'message_type', 'content', 'created_at']
    readonly_fields = ['sender_type', 'message_type', 'content', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AgentConversation)
class AgentConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'status', 'conversation_type', 'created_at', 'updated_at']
    list_filter = ['status', 'conversation_type', 'is_archived', 'created_at']
    search_fields = ['title', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [AgentMessageInline]


@admin.register(AgentTask)
class AgentTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'task_type', 'status', 'started_at', 'completed_at']
    list_filter = ['status', 'task_type', 'created_at']
    search_fields = ['user__email', 'task_type']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'budget_range', 'trip_style', 'last_trained', 'updated_at']
    list_filter = ['budget_range', 'trip_style']
    search_fields = ['user__email']
    readonly_fields = ['travel_dna', 'last_trained', 'created_at', 'updated_at']


@admin.register(AgentAnalytics)
class AgentAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'created_at']
    date_hierarchy = 'date'
    readonly_fields = ['date', 'metrics', 'created_at']


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'model_type', 'is_active', 'created_at']
    list_filter = ['model_type', 'is_active']
    search_fields = ['name', 'version']


class TripCollaboratorInline(admin.TabularInline):
    model = TripCollaborator
    extra = 0
    fields = ['user', 'role', 'joined_at']
    readonly_fields = ['joined_at']


@admin.register(TripCollaboration)
class TripCollaborationAdmin(admin.ModelAdmin):
    list_display = ['invite_code', 'itinerary', 'owner', 'status', 'max_participants', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['invite_code', 'owner__email']
    readonly_fields = ['invite_code', 'created_at', 'updated_at']
    inlines = [TripCollaboratorInline]


@admin.register(CollaborationVote)
class CollaborationVoteAdmin(admin.ModelAdmin):
    list_display = ['collaboration', 'user', 'item_type', 'vote', 'created_at']
    list_filter = ['item_type', 'vote', 'created_at']
    search_fields = ['user__email']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'ai_plans_used', 'price_alerts_used', 'current_period_end', 'updated_at']
    list_filter = ['plan', 'status']
    search_fields = ['user__email', 'stripe_customer_id']
    readonly_fields = ['stripe_customer_id', 'stripe_subscription_id', 'created_at', 'updated_at']

    fieldsets = (
        ('User & Plan', {'fields': ('user', 'plan', 'status')}),
        ('Usage', {'fields': ('ai_plans_used', 'ai_plans_limit', 'price_alerts_used', 'price_alerts_limit')}),
        ('Stripe', {'fields': ('stripe_customer_id', 'stripe_subscription_id'), 'classes': ('collapse',)}),
        ('Period', {'fields': ('current_period_start', 'current_period_end')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(AffiliateClick)
class AffiliateClickAdmin(admin.ModelAdmin):
    list_display = ['tracking_id', 'partner', 'click_type', 'status', 'revenue', 'user', 'clicked_at']
    list_filter = ['partner', 'click_type', 'status', 'clicked_at']
    search_fields = ['tracking_id', 'partner', 'user__email']
    readonly_fields = ['tracking_id', 'clicked_at', 'converted_at']
    date_hierarchy = 'clicked_at'


@admin.register(PriceWatch)
class PriceWatchAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'watch_type', 'target_price', 'current_price', 'lowest_price', 'is_active', 'last_checked']
    list_filter = ['watch_type', 'is_active', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['price_history', 'last_checked', 'created_at', 'updated_at']


@admin.register(TripMemory)
class TripMemoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'destination', 'sentiment', 'rating', 'trip_date', 'created_at']
    list_filter = ['sentiment', 'rating', 'trip_date', 'created_at']
    search_fields = ['user__email', 'destination', 'notes']
    readonly_fields = ['ai_insights', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


# ─────────────────────────────────────────────────
# Phase 5: Monetization & Partnerships Admin
# ─────────────────────────────────────────────────

class PartnerCouponInline(admin.TabularInline):
    model = PartnerCoupon
    extra = 0
    fields = ['code', 'title', 'discount_type', 'discount_value', 'is_active', 'times_used']
    readonly_fields = ['times_used']


@admin.register(PartnerBusiness)
class PartnerBusinessAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'destination', 'status', 'rating',
                    'total_coupons_redeemed', 'total_revenue_generated', 'created_at']
    list_filter = ['category', 'status', 'created_at']
    search_fields = ['name', 'destination', 'contact_email']
    readonly_fields = ['total_coupons_redeemed', 'total_revenue_generated', 'created_at', 'updated_at']
    inlines = [PartnerCouponInline]

    fieldsets = (
        ('Business Info', {'fields': ('name', 'category', 'description', 'destination', 'address', 'website')}),
        ('Contact', {'fields': ('contact_email', 'contact_phone', 'logo_url')}),
        ('Status & Revenue', {'fields': ('status', 'commission_rate', 'rating',
                                          'total_coupons_redeemed', 'total_revenue_generated', 'onboarded_by')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(PartnerCoupon)
class PartnerCouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'partner', 'discount_type', 'discount_value',
                    'is_active', 'times_used', 'valid_until']
    list_filter = ['discount_type', 'is_active', 'partner__category', 'created_at']
    search_fields = ['code', 'title', 'partner__name']
    readonly_fields = ['times_used', 'created_at', 'updated_at']


@admin.register(CouponRedemption)
class CouponRedemptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'coupon', 'savings_amount', 'order_total', 'platform_commission', 'redeemed_at']
    list_filter = ['redeemed_at']
    search_fields = ['user__email', 'coupon__code']
    readonly_fields = ['redeemed_at']
    date_hierarchy = 'redeemed_at'


@admin.register(ReferralCode)
class ReferralCodeAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'total_referrals', 'successful_referrals', 'total_earnings', 'is_active']
    list_filter = ['is_active']
    search_fields = ['user__email', 'code']
    readonly_fields = ['total_referrals', 'successful_referrals', 'total_earnings', 'created_at']


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['referrer', 'referred_email', 'referred_user', 'status', 'reward_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['referrer__email', 'referred_email']
    readonly_fields = ['created_at', 'converted_at']
    date_hierarchy = 'created_at'


class CulturalInfoInline(admin.TabularInline):
    model = CulturalInfo
    extra = 0
    fields = ['category', 'title', 'severity', 'ai_generated']
    readonly_fields = ['ai_generated']


class UserDestinationTipInline(admin.TabularInline):
    model = UserDestinationTip
    extra = 0
    fields = ['user', 'title', 'status', 'upvotes', 'downvotes', 'ai_moderation_score']
    readonly_fields = ['upvotes', 'downvotes', 'ai_moderation_score']


@admin.register(DestinationKnowledge)
class DestinationKnowledgeAdmin(admin.ModelAdmin):
    list_display = ['destination', 'country', 'continent', 'views_count', 'ai_generated', 'updated_at']
    list_filter = ['continent', 'ai_generated', 'created_at']
    search_fields = ['destination', 'country']
    readonly_fields = ['views_count', 'created_at', 'updated_at']
    inlines = [CulturalInfoInline, UserDestinationTipInline]

    fieldsets = (
        ('Location', {'fields': ('destination', 'country', 'continent', 'currency', 'timezone_info')}),
        ('Content', {'fields': ('summary', 'history', 'culture', 'visa_info')}),
        ('Structured Data', {'fields': ('heritage_sites', 'festivals', 'customs', 'best_months',
                                         'languages_spoken', 'emergency_numbers'), 'classes': ('collapse',)}),
        ('Links & Meta', {'fields': ('official_tourism_url', 'ai_generated', 'views_count')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(CulturalInfo)
class CulturalInfoAdmin(admin.ModelAdmin):
    list_display = ['destination', 'category', 'title', 'severity', 'ai_generated']
    list_filter = ['category', 'severity', 'ai_generated']
    search_fields = ['destination__destination', 'title']


@admin.register(UserDestinationTip)
class UserDestinationTipAdmin(admin.ModelAdmin):
    list_display = ['user', 'destination', 'title', 'status', 'upvotes', 'downvotes',
                    'ai_moderation_score', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email', 'destination__destination', 'title']
    readonly_fields = ['upvotes', 'downvotes', 'ai_moderation_score', 'ai_moderation_notes',
                       'created_at', 'updated_at']


# ─────────────────────────────────────────────────
# Phase 6: Social & Viral Growth Admin
# ─────────────────────────────────────────────────

class StoryCommentInline(admin.TabularInline):
    model = StoryComment
    extra = 0
    fields = ['user', 'content', 'created_at']
    readonly_fields = ['created_at']


@admin.register(TravelStoryGenerated)
class TravelStoryGeneratedAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'destination', 'format', 'status', 'is_public',
                    'views_count', 'likes_count', 'shares_count', 'created_at']
    list_filter = ['format', 'status', 'is_public', 'created_at']
    search_fields = ['title', 'destination', 'user__email']
    readonly_fields = ['share_token', 'views_count', 'likes_count', 'shares_count', 'created_at', 'updated_at']
    inlines = [StoryCommentInline]


@admin.register(StoryLike)
class StoryLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'story', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email']


class TemplateCloneInline(admin.TabularInline):
    model = TemplateClone
    extra = 0
    fields = ['user', 'itinerary_id', 'created_at']
    readonly_fields = ['created_at']


@admin.register(TripTemplate)
class TripTemplateAdmin(admin.ModelAdmin):
    list_display = ['title', 'creator', 'destination', 'style', 'duration_days',
                    'estimated_budget', 'clone_count', 'likes_count', 'rating', 'is_featured', 'is_verified']
    list_filter = ['style', 'is_featured', 'is_verified', 'created_at']
    search_fields = ['title', 'destination', 'creator__email']
    readonly_fields = ['clone_count', 'likes_count', 'views_count', 'rating', 'rating_count',
                       'created_at', 'updated_at']
    inlines = [TemplateCloneInline]


@admin.register(TemplateClone)
class TemplateCloneAdmin(admin.ModelAdmin):
    list_display = ['user', 'template', 'itinerary_id', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'template__title']
    readonly_fields = ['created_at']


@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'destination', 'content_type', 'status',
                    'upvotes', 'downvotes', 'ai_moderation_score', 'created_at']
    list_filter = ['content_type', 'status', 'created_at']
    search_fields = ['title', 'destination', 'user__email']
    readonly_fields = ['upvotes', 'downvotes', 'views_count', 'ai_moderation_score',
                       'created_at', 'updated_at']


# ──────────────────────────────────────────────────────────────────────
# Phase 7: Faith & Health Awareness
# ──────────────────────────────────────────────────────────────────────

@admin.register(PrayerTimeCache)
class PrayerTimeCacheAdmin(admin.ModelAdmin):
    list_display = ['destination', 'date', 'fajr', 'dhuhr', 'asr', 'maghrib', 'isha', 'method']
    list_filter = ['method', 'date']
    search_fields = ['destination']
    readonly_fields = ['created_at']


@admin.register(WorshipPlace)
class WorshipPlaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'destination', 'worship_type', 'faith', 'rating',
                    'halal_food_nearby', 'kosher_food_nearby', 'views_count']
    list_filter = ['worship_type', 'faith', 'created_at']
    search_fields = ['name', 'destination', 'address']
    readonly_fields = ['views_count', 'created_at', 'updated_at']


@admin.register(SpiritualSite)
class SpiritualSiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'destination', 'category', 'best_time_to_visit', 'views_count']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'destination']
    readonly_fields = ['views_count', 'created_at']


@admin.register(MedicalFacility)
class MedicalFacilityAdmin(admin.ModelAdmin):
    list_display = ['name', 'destination', 'facility_type', 'emergency_24h',
                    'english_speaking', 'accepts_travel_insurance', 'wheelchair_accessible', 'rating']
    list_filter = ['facility_type', 'emergency_24h', 'english_speaking', 'wheelchair_accessible']
    search_fields = ['name', 'destination', 'address']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AccessibilityRating)
class AccessibilityRatingAdmin(admin.ModelAdmin):
    list_display = ['venue_name', 'destination', 'venue_type', 'mobility_rating',
                    'wheelchair_accessible', 'elevator_available', 'user', 'created_at']
    list_filter = ['venue_type', 'mobility_rating', 'wheelchair_accessible']
    search_fields = ['venue_name', 'destination', 'user__email']
    readonly_fields = ['created_at']


@admin.register(MedicationReminder)
class MedicationReminderAdmin(admin.ModelAdmin):
    list_display = ['medication_name', 'user', 'dosage', 'home_time', 'home_timezone',
                    'frequency', 'is_active']
    list_filter = ['frequency', 'is_active', 'created_at']
    search_fields = ['medication_name', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(HealthInsuranceInfo)
class HealthInsuranceInfoAdmin(admin.ModelAdmin):
    list_display = ['country', 'risk_level', 'avg_hospital_cost_per_day_usd',
                    'public_healthcare_available', 'malaria_risk', 'altitude_risk', 'emergency_number']
    list_filter = ['risk_level', 'public_healthcare_available', 'malaria_risk', 'altitude_risk']
    search_fields = ['country']
    readonly_fields = ['created_at', 'updated_at']
