import os
import uuid

from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.utils import timezone


class AgentSession(models.Model):
    """Track multi-agent AI conversation sessions."""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='agent_sessions'
    )

    session_id = models.CharField(max_length=100, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Session metadata
    conversation_context = models.JSONField(default=dict, blank=True)
    user_intent = models.TextField(blank=True)
    detected_entities = models.JSONField(default=dict, blank=True)

    # Session stats
    total_executions = models.IntegerField(default=0)
    total_tokens_used = models.IntegerField(default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=4, default=0)

    # Timestamps
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_activity_at = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'agent_sessions'
        ordering = ['-started_at']
        verbose_name = 'Agent Session'
        verbose_name_plural = 'Agent Sessions'
        indexes = [
            models.Index(fields=['user', '-started_at']),
            models.Index(fields=['status', '-started_at']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        return f"Session {self.session_id} - {self.user.email} ({self.status})"

    def mark_completed(self):
        """Mark session as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

    def mark_failed(self):
        """Mark session as failed."""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.save()


class AgentExecution(models.Model):
    """Track individual agent executions within a session."""

    AGENT_TYPE_CHOICES = [
        ('orchestrator', 'Orchestrator Agent'),
        ('flight_search', 'Flight Search Agent'),
        ('hotel_search', 'Hotel Search Agent'),
        ('car_rental', 'Car Rental Agent'),
        ('itinerary_planner', 'Itinerary Planner Agent'),
        ('booking', 'Booking Agent'),
        ('recommendation', 'Recommendation Agent'),
        ('customer_support', 'Customer Support Agent'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
    ]

    session = models.ForeignKey(
        AgentSession,
        on_delete=models.CASCADE,
        related_name='executions'
    )

    execution_id = models.CharField(max_length=100, unique=True, db_index=True)
    agent_type = models.CharField(max_length=50, choices=AGENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Execution details
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    # Agent configuration
    agent_config = models.JSONField(default=dict, blank=True)
    model_used = models.CharField(max_length=100, blank=True)

    # Performance metrics
    tokens_used = models.IntegerField(default=0)
    execution_time_ms = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=4, default=0)

    # Tool/function calls made by the agent
    tools_called = models.JSONField(default=list, blank=True)
    function_calls = models.JSONField(default=list, blank=True)

    # Timestamps
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'agent_executions'
        ordering = ['-started_at']
        verbose_name = 'Agent Execution'
        verbose_name_plural = 'Agent Executions'
        indexes = [
            models.Index(fields=['session', '-started_at']),
            models.Index(fields=['agent_type', '-started_at']),
            models.Index(fields=['status']),
            models.Index(fields=['execution_id']),
        ]

    def __str__(self):
        return f"{self.agent_type} - {self.execution_id} ({self.status})"

    def mark_completed(self, output_data=None):
        """Mark execution as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if output_data:
            self.output_data = output_data
        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds() * 1000
            self.execution_time_ms = int(duration)
        self.save()

        # Update session stats
        self.session.total_executions += 1
        self.session.total_tokens_used += self.tokens_used
        self.session.total_cost += self.cost
        self.session.save()

    def mark_failed(self, error_message):
        """Mark execution as failed."""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds() * 1000
            self.execution_time_ms = int(duration)
        self.save()


class AgentLog(models.Model):
    """Detailed logging for agent operations."""

    LOG_LEVEL_CHOICES = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]

    execution = models.ForeignKey(
        AgentExecution,
        on_delete=models.CASCADE,
        related_name='logs',
        null=True,
        blank=True
    )

    session = models.ForeignKey(
        AgentSession,
        on_delete=models.CASCADE,
        related_name='logs'
    )

    log_level = models.CharField(max_length=20, choices=LOG_LEVEL_CHOICES, default='info')
    message = models.TextField()

    # Structured log data
    log_data = models.JSONField(default=dict, blank=True)

    # Context
    agent_type = models.CharField(max_length=50, blank=True)
    function_name = models.CharField(max_length=200, blank=True)
    line_number = models.IntegerField(null=True, blank=True)

    # Exception details if error
    exception_type = models.CharField(max_length=200, blank=True)
    exception_traceback = models.TextField(blank=True)

    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'agent_logs'
        ordering = ['-timestamp']
        verbose_name = 'Agent Log'
        verbose_name_plural = 'Agent Logs'
        indexes = [
            models.Index(fields=['session', '-timestamp']),
            models.Index(fields=['execution', '-timestamp']),
            models.Index(fields=['log_level', '-timestamp']),
        ]

    def __str__(self):
        return f"[{self.log_level.upper()}] {self.agent_type} - {self.message[:50]}"


def rag_document_upload_path(instance, filename):
    """Upload documents to rag_documents/<user_id>/<uuid>_<filename>."""
    ext = os.path.splitext(filename)[1]
    safe_name = f"{uuid.uuid4().hex[:12]}{ext}"
    return f"rag_documents/{instance.uploaded_by_id}/{safe_name}"


class RAGDocument(models.Model):
    """
    Company/user-uploaded documents for RAG context.
    Supports PDF, TXT, DOCX, and Markdown files.
    Files are parsed, chunked, and embedded into ChromaDB
    so the AI assistant can reference them during chat.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending Processing'),
        ('processing', 'Processing'),
        ('indexed', 'Indexed'),
        ('failed', 'Failed'),
    ]

    SCOPE_CHOICES = [
        ('global', 'Global (all users)'),
        ('user', 'User-specific'),
    ]

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rag_documents',
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(
        upload_to=rag_document_upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'txt', 'md', 'docx', 'csv']
        )],
    )
    file_type = models.CharField(max_length=10, blank=True)
    file_size = models.PositiveIntegerField(default=0, help_text='File size in bytes')

    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)

    # Indexing metadata
    chunk_count = models.PositiveIntegerField(default=0)
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES, default='global')

    # Tags for filtering
    tags = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rag_documents'
        ordering = ['-created_at']
        verbose_name = 'RAG Document'
        verbose_name_plural = 'RAG Documents'
        indexes = [
            models.Index(fields=['uploaded_by', '-created_at'], name='rag_documen_uploade_84f4bf_idx'),
            models.Index(fields=['status'], name='rag_documen_status_71a194_idx'),
            models.Index(fields=['scope'], name='rag_documen_scope_6a2018_idx'),
        ]

    def __str__(self):
        return f"{self.title} ({self.file_type}) - {self.status}"

    def save(self, *args, **kwargs):
        if self.file and not self.file_type:
            self.file_type = os.path.splitext(self.file.name)[1].lstrip('.').lower()
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except Exception:
                pass
        super().save(*args, **kwargs)


class AgentConversation(models.Model):
    """Chat conversation sessions with the AI agent."""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),
    ]

    CONVERSATION_TYPE_CHOICES = [
        ('trip_planning', 'Trip Planning'),
        ('general', 'General'),
        ('booking_assist', 'Booking Assistance'),
        ('price_monitor', 'Price Monitor'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='agent_conversations'
    )
    title = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_archived = models.BooleanField(default=False)
    conversation_type = models.CharField(
        max_length=20,
        choices=CONVERSATION_TYPE_CHOICES,
        default='trip_planning'
    )
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'agent_conversations'
        ordering = ['-updated_at']
        verbose_name = 'Agent Conversation'
        verbose_name_plural = 'Agent Conversations'
        indexes = [
            models.Index(fields=['user', '-updated_at'], name='agent_conv_user_updated_idx'),
            models.Index(fields=['status'], name='agent_conve_status_idx'),
            models.Index(fields=['conversation_type'], name='agent_conve_conv_type_idx'),
            models.Index(fields=['is_archived'], name='agent_conve_archived_idx'),
        ]

    def __str__(self):
        title = self.title or 'Untitled'
        return f"Conversation {self.id} - {title} ({self.status})"


class AgentMessage(models.Model):
    """Individual chat messages within a conversation."""

    SENDER_TYPE_CHOICES = [
        ('user', 'User'),
        ('agent', 'Agent'),
        ('system', 'System'),
    ]

    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('suggestion', 'Suggestion'),
        ('action', 'Action'),
        ('flight_result', 'Flight Result'),
        ('hotel_result', 'Hotel Result'),
        ('itinerary', 'Itinerary'),
        ('price_alert', 'Price Alert'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        AgentConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    content = models.TextField()
    sender_type = models.CharField(max_length=10, choices=SENDER_TYPE_CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agent_messages'
    )
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        default='text'
    )
    metadata = models.JSONField(default=dict, blank=True)
    intent = models.CharField(max_length=100, blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    tokens_used = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'agent_messages'
        ordering = ['created_at']
        verbose_name = 'Agent Message'
        verbose_name_plural = 'Agent Messages'
        indexes = [
            models.Index(fields=['conversation', 'created_at'], name='agent_msg_conv_created_idx'),
            models.Index(fields=['sender_type'], name='agent_msg_sender_idx'),
            models.Index(fields=['message_type'], name='agent_msg_type_idx'),
            models.Index(fields=['intent'], name='agent_msg_intent_idx'),
        ]

    def __str__(self):
        return f"[{self.sender_type}] {self.content[:50]}"


class AgentTask(models.Model):
    """Async agent tasks for background processing."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='agent_tasks'
    )
    task_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    parameters = models.JSONField(default=dict, blank=True)
    result = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'agent_tasks'
        ordering = ['-created_at']
        verbose_name = 'Agent Task'
        verbose_name_plural = 'Agent Tasks'
        indexes = [
            models.Index(fields=['user', '-created_at'], name='agent_task_user_created_idx'),
            models.Index(fields=['status'], name='agent_task_status_idx'),
            models.Index(fields=['task_type', 'status'], name='agent_task_type_status_idx'),
            models.Index(fields=['completed_at'], name='agent_task_completed_idx'),
        ]

    def __str__(self):
        return f"Task {self.id} - {self.task_type} ({self.status})"


class UserPreference(models.Model):
    """Learned user preferences for AI personalization."""

    BUDGET_RANGE_CHOICES = [
        ('budget', 'Budget'),
        ('moderate', 'Moderate'),
        ('luxury', 'Luxury'),
        ('any', 'Any'),
    ]

    TRIP_STYLE_CHOICES = [
        ('adventure', 'Adventure'),
        ('relaxation', 'Relaxation'),
        ('cultural', 'Cultural'),
        ('business', 'Business'),
        ('family', 'Family'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_preferences'
    )
    preferences = models.JSONField(default=dict, blank=True)
    travel_dna = models.JSONField(default=dict, blank=True)
    preferred_airlines = models.JSONField(default=list, blank=True)
    preferred_hotel_chains = models.JSONField(default=list, blank=True)
    preferred_cuisines = models.JSONField(default=list, blank=True)
    budget_range = models.CharField(
        max_length=20,
        choices=BUDGET_RANGE_CHOICES,
        default='any'
    )
    trip_style = models.CharField(
        max_length=20,
        choices=TRIP_STYLE_CHOICES,
        default='cultural'
    )
    booking_advance_days = models.IntegerField(
        default=14,
        validators=[MinValueValidator(0)]
    )
    last_trained = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_preferences'
        verbose_name = 'User Preference'
        verbose_name_plural = 'User Preferences'

    def __str__(self):
        return f"Preferences for {self.user} - {self.trip_style}/{self.budget_range}"


class AgentAnalytics(models.Model):
    """Daily analytics aggregation for agent performance."""

    date = models.DateField(unique=True)
    metrics = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'agent_analytics'
        ordering = ['-date']
        verbose_name = 'Agent Analytics'
        verbose_name_plural = 'Agent Analytics'
        indexes = [
            models.Index(fields=['-date'], name='agent_analytics_date_idx'),
        ]

    def __str__(self):
        return f"Analytics for {self.date}"


class AIModel(models.Model):
    """Track AI model versions and configurations."""

    name = models.CharField(max_length=100)
    version = models.CharField(max_length=50)
    model_type = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_models'
        ordering = ['-created_at']
        verbose_name = 'AI Model'
        verbose_name_plural = 'AI Models'
        indexes = [
            models.Index(fields=['name', 'version'], name='ai_model_name_version_idx'),
            models.Index(fields=['model_type'], name='ai_model_type_idx'),
            models.Index(fields=['is_active'], name='ai_model_active_idx'),
        ]

    def __str__(self):
        status = 'active' if self.is_active else 'inactive'
        return f"{self.name} v{self.version} ({status})"


class TripCollaboration(models.Model):
    """Collaborative trip planning sessions."""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]

    itinerary = models.ForeignKey(
        'itineraries.Itinerary',
        on_delete=models.CASCADE,
        related_name='collaborations'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_collaborations'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    invite_code = models.CharField(max_length=20, unique=True)
    max_participants = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1)]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'trip_collaborations'
        ordering = ['-created_at']
        verbose_name = 'Trip Collaboration'
        verbose_name_plural = 'Trip Collaborations'
        indexes = [
            models.Index(fields=['owner', '-created_at'], name='trip_collab_owner_created_idx'),
            models.Index(fields=['invite_code'], name='trip_collab_invite_code_idx'),
            models.Index(fields=['status'], name='trip_collab_status_idx'),
        ]

    def __str__(self):
        return f"Collaboration {self.invite_code} - {self.itinerary} ({self.status})"


class TripCollaborator(models.Model):
    """Individual collaborator in a trip collaboration."""

    ROLE_CHOICES = [
        ('viewer', 'Viewer'),
        ('editor', 'Editor'),
        ('admin', 'Admin'),
    ]

    collaboration = models.ForeignKey(
        TripCollaboration,
        on_delete=models.CASCADE,
        related_name='collaborators'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trip_collaborations'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='editor')

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'trip_collaborators'
        ordering = ['-joined_at']
        verbose_name = 'Trip Collaborator'
        verbose_name_plural = 'Trip Collaborators'
        unique_together = [('collaboration', 'user')]
        indexes = [
            models.Index(fields=['collaboration', 'user'], name='trip_collabr_collab_user_idx'),
            models.Index(fields=['user'], name='trip_collabr_user_idx'),
        ]

    def __str__(self):
        return f"{self.user} - {self.collaboration.invite_code} ({self.role})"


class CollaborationVote(models.Model):
    """Voting on options within a collaborative trip."""

    ITEM_TYPE_CHOICES = [
        ('flight', 'Flight'),
        ('hotel', 'Hotel'),
        ('restaurant', 'Restaurant'),
        ('attraction', 'Attraction'),
    ]

    VOTE_CHOICES = [
        ('up', 'Up'),
        ('down', 'Down'),
        ('neutral', 'Neutral'),
    ]

    collaboration = models.ForeignKey(
        TripCollaboration,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collaboration_votes'
    )
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    item_id = models.CharField(max_length=255)
    vote = models.CharField(max_length=10, choices=VOTE_CHOICES, default='neutral')
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'collaboration_votes'
        ordering = ['-created_at']
        verbose_name = 'Collaboration Vote'
        verbose_name_plural = 'Collaboration Votes'
        indexes = [
            models.Index(fields=['collaboration', 'item_type', 'item_id'], name='collab_vote_collab_item_idx'),
            models.Index(fields=['user'], name='collab_vote_user_idx'),
        ]

    def __str__(self):
        return f"{self.user} voted {self.vote} on {self.item_type} {self.item_id}"


class Subscription(models.Model):
    """Freemium tier subscription management."""

    PLAN_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('business', 'Business'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('past_due', 'Past Due'),
        ('trialing', 'Trialing'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    ai_plans_used = models.IntegerField(default=0)
    ai_plans_limit = models.IntegerField(default=3)
    price_alerts_used = models.IntegerField(default=0)
    price_alerts_limit = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscriptions'
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        indexes = [
            models.Index(fields=['plan'], name='sub_plan_idx'),
            models.Index(fields=['status'], name='sub_status_idx'),
            models.Index(fields=['stripe_customer_id'], name='sub_stripe_cust_idx'),
        ]

    def __str__(self):
        return f"{self.user} - {self.plan} ({self.status})"


class AffiliateClick(models.Model):
    """Track affiliate link clicks and revenue."""

    CLICK_TYPE_CHOICES = [
        ('flight', 'Flight'),
        ('hotel', 'Hotel'),
        ('car', 'Car'),
        ('activity', 'Activity'),
    ]

    STATUS_CHOICES = [
        ('clicked', 'Clicked'),
        ('converted', 'Converted'),
        ('paid', 'Paid'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='affiliate_clicks'
    )
    partner = models.CharField(max_length=100)
    click_type = models.CharField(max_length=20, choices=CLICK_TYPE_CHOICES)
    destination = models.CharField(max_length=255, blank=True)
    tracking_id = models.CharField(max_length=255, unique=True)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='clicked')

    clicked_at = models.DateTimeField(auto_now_add=True)
    converted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'affiliate_clicks'
        ordering = ['-clicked_at']
        verbose_name = 'Affiliate Click'
        verbose_name_plural = 'Affiliate Clicks'
        indexes = [
            models.Index(fields=['partner', '-clicked_at'], name='aff_partner_clicked_idx'),
            models.Index(fields=['tracking_id'], name='aff_tracking_idx'),
            models.Index(fields=['status'], name='aff_status_idx'),
            models.Index(fields=['click_type'], name='aff_click_type_idx'),
            models.Index(fields=['user', '-clicked_at'], name='aff_user_clicked_idx'),
        ]

    def __str__(self):
        return f"{self.partner} - {self.click_type} ({self.status}) [{self.tracking_id}]"


class PriceWatch(models.Model):
    """Enhanced price monitoring for flights and hotels."""

    WATCH_TYPE_CHOICES = [
        ('flight', 'Flight'),
        ('hotel', 'Hotel'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='price_watches'
    )
    watch_type = models.CharField(max_length=10, choices=WATCH_TYPE_CHOICES)
    search_params = models.JSONField()
    target_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    current_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    lowest_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    price_history = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    notify_on_any_drop = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'price_watches'
        ordering = ['-created_at']
        verbose_name = 'Price Watch'
        verbose_name_plural = 'Price Watches'
        indexes = [
            models.Index(fields=['user', '-created_at'], name='pw_user_created_idx'),
            models.Index(fields=['watch_type'], name='pw_watch_type_idx'),
            models.Index(fields=['is_active'], name='pw_active_idx'),
            models.Index(fields=['is_active', 'last_checked'], name='pw_active_checked_idx'),
        ]

    def __str__(self):
        status = 'active' if self.is_active else 'paused'
        return f"{self.watch_type} watch for {self.user} ({status})"
