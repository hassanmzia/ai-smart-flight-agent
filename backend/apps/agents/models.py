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

    PACE_CHOICES = [
        ('slow', 'Slow Traveler'),
        ('moderate', 'Moderate'),
        ('packed', 'Packed Schedule'),
    ]

    DIETARY_CHOICES = [
        ('none', 'No Restrictions'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('halal', 'Halal'),
        ('kosher', 'Kosher'),
        ('gluten_free', 'Gluten Free'),
        ('other', 'Other'),
    ]

    FAITH_CHOICES = [
        ('none', 'Not Specified'),
        ('islam', 'Islam'),
        ('christianity', 'Christianity'),
        ('judaism', 'Judaism'),
        ('hinduism', 'Hinduism'),
        ('buddhism', 'Buddhism'),
        ('sikhism', 'Sikhism'),
        ('other', 'Other'),
    ]

    MOBILITY_CHOICES = [
        ('full', 'Full Mobility'),
        ('limited', 'Limited Mobility'),
        ('wheelchair', 'Wheelchair'),
        ('elderly', 'Elderly-Friendly'),
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

    # --- Travel DNA v2 fields ---
    # Dietary needs
    dietary_preference = models.CharField(
        max_length=20, choices=DIETARY_CHOICES, default='none',
    )
    dietary_allergies = models.JSONField(
        default=list, blank=True,
        help_text='List of food allergies, e.g. ["peanuts", "shellfish"]',
    )

    # Faith profile
    faith = models.CharField(
        max_length=20, choices=FAITH_CHOICES, default='none',
    )
    prayer_reminders = models.BooleanField(default=False)
    faith_site_interest = models.BooleanField(
        default=False,
        help_text='Show mosques, temples, churches near itinerary stops',
    )

    # Health profile
    mobility = models.CharField(
        max_length=20, choices=MOBILITY_CHOICES, default='full',
    )
    max_walking_km_per_day = models.DecimalField(
        max_digits=4, decimal_places=1, default=10.0,
        help_text='Maximum comfortable walking distance in km per day',
    )
    health_conditions = models.JSONField(
        default=list, blank=True,
        help_text='List of health conditions to consider, e.g. ["asthma", "diabetes"]',
    )
    medications = models.JSONField(
        default=list, blank=True,
        help_text='Medications with timezone adjustment needs',
    )

    # Pace preference
    pace = models.CharField(
        max_length=20, choices=PACE_CHOICES, default='moderate',
    )
    max_activities_per_day = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1)],
    )

    # Language proficiency
    languages_spoken = models.JSONField(
        default=list, blank=True,
        help_text='Languages the user speaks, e.g. ["en", "es", "fr"]',
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
        ('rental', 'Vacation Rental'),
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
        ('rental', 'Vacation Rental'),
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


class TripMemory(models.Model):
    """Long-term memory of user's travel experiences for learning."""

    SENTIMENT_CHOICES = [
        ('loved', 'Loved'),
        ('liked', 'Liked'),
        ('neutral', 'Neutral'),
        ('disliked', 'Disliked'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trip_memories',
    )
    destination = models.CharField(max_length=200, db_index=True)
    trip_date = models.DateField(null=True, blank=True)
    sentiment = models.CharField(max_length=20, choices=SENTIMENT_CHOICES, default='neutral')
    highlights = models.JSONField(default=list, blank=True, help_text='Things the user loved')
    lowlights = models.JSONField(default=list, blank=True, help_text='Things the user disliked')
    tags = models.JSONField(default=list, blank=True, help_text='e.g. ["beach", "food", "history"]')
    budget_spent = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    travel_style_used = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    rating = models.IntegerField(default=0, help_text='1-5 overall rating')

    # AI-generated insights
    ai_insights = models.JSONField(default=dict, blank=True, help_text='AI analysis of the trip')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'trip_memories'
        ordering = ['-trip_date', '-created_at']
        verbose_name = 'Trip Memory'
        verbose_name_plural = 'Trip Memories'
        indexes = [
            models.Index(fields=['user', '-trip_date'], name='trip_mem_user_date_idx'),
            models.Index(fields=['destination'], name='trip_mem_dest_idx'),
            models.Index(fields=['sentiment'], name='trip_mem_sentiment_idx'),
        ]

    def __str__(self):
        return f"{self.user} - {self.destination} ({self.sentiment})"


# ─────────────────────────────────────────────────
# Phase 5: Monetization & Partnerships Models
# ─────────────────────────────────────────────────

class PartnerBusiness(models.Model):
    """Local businesses that partner with the platform for coupons/deals."""

    CATEGORY_CHOICES = [
        ('hotel', 'Hotel'),
        ('restaurant', 'Restaurant'),
        ('attraction', 'Attraction'),
        ('tour', 'Tour Operator'),
        ('transport', 'Transport'),
        ('shopping', 'Shopping'),
        ('spa', 'Spa & Wellness'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    destination = models.CharField(max_length=200, db_index=True, help_text='City or region')
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=30, blank=True)
    logo_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00,
                                          help_text='Revenue share % when AI saves money')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    total_coupons_redeemed = models.IntegerField(default=0)
    total_revenue_generated = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    onboarded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='onboarded_partners')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'partner_businesses'
        ordering = ['-rating', 'name']
        verbose_name_plural = 'Partner Businesses'
        indexes = [
            models.Index(fields=['category', 'destination'], name='partner_cat_dest_idx'),
            models.Index(fields=['status'], name='partner_status_idx'),
        ]

    def __str__(self):
        return f"{self.name} ({self.category}) - {self.destination}"


class PartnerCoupon(models.Model):
    """Coupon codes offered by partner businesses."""

    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage Off'),
        ('fixed', 'Fixed Amount Off'),
        ('bogo', 'Buy One Get One'),
        ('freebie', 'Free Item/Service'),
    ]

    partner = models.ForeignKey(PartnerBusiness, on_delete=models.CASCADE, related_name='coupons')
    code = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2,
                                          help_text='Percentage or fixed amount')
    min_spend = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                     help_text='Minimum spend to use coupon')
    max_uses = models.IntegerField(default=0, help_text='0 = unlimited')
    times_used = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    terms = models.TextField(blank=True, help_text='Terms and conditions')
    qr_data = models.TextField(blank=True, help_text='QR code data for in-store redemption')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'partner_coupons'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['partner', 'is_active'], name='coupon_partner_active_idx'),
            models.Index(fields=['valid_until'], name='coupon_valid_until_idx'),
        ]

    def __str__(self):
        return f"{self.code} - {self.title} ({self.partner.name})"

    @property
    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.max_uses > 0 and self.times_used >= self.max_uses:
            return False
        return True


class CouponRedemption(models.Model):
    """Tracks when users redeem coupons."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='coupon_redemptions')
    coupon = models.ForeignKey(PartnerCoupon, on_delete=models.CASCADE, related_name='redemptions')
    redeemed_at = models.DateTimeField(auto_now_add=True)
    savings_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    order_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'coupon_redemptions'
        ordering = ['-redeemed_at']
        indexes = [
            models.Index(fields=['user', '-redeemed_at'], name='redemption_user_date_idx'),
        ]

    def __str__(self):
        return f"{self.user} redeemed {self.coupon.code}"


class ReferralCode(models.Model):
    """User referral codes for earning rewards."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='referral_code')
    code = models.CharField(max_length=20, unique=True, db_index=True)
    total_referrals = models.IntegerField(default=0)
    successful_referrals = models.IntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'referral_codes'

    def __str__(self):
        return f"{self.user} - {self.code}"


class Referral(models.Model):
    """Individual referral tracking."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('signed_up', 'Signed Up'),
        ('converted', 'Converted'),
        ('rewarded', 'Rewarded'),
    ]

    referrer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='referrals_made')
    referred_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='referred_by')
    referral_code = models.ForeignKey(ReferralCode, on_delete=models.CASCADE, related_name='referrals')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    referred_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    converted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'referrals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['referrer', 'status'], name='referral_referrer_status_idx'),
        ]

    def __str__(self):
        return f"{self.referrer} → {self.referred_email or self.referred_user}"


class DestinationKnowledge(models.Model):
    """Structured destination knowledge base entry."""

    destination = models.CharField(max_length=200, unique=True, db_index=True)
    country = models.CharField(max_length=100, db_index=True)
    continent = models.CharField(max_length=50, blank=True)
    summary = models.TextField(blank=True, help_text='AI-generated overview')
    history = models.TextField(blank=True)
    culture = models.TextField(blank=True)
    heritage_sites = models.JSONField(default=list, blank=True)
    festivals = models.JSONField(default=list, blank=True, help_text='Major festivals with dates')
    customs = models.JSONField(default=list, blank=True, help_text='Local customs and norms')
    best_months = models.JSONField(default=list, blank=True)
    languages_spoken = models.JSONField(default=list, blank=True)
    currency = models.CharField(max_length=10, blank=True)
    timezone_info = models.CharField(max_length=50, blank=True)
    official_tourism_url = models.URLField(blank=True)
    emergency_numbers = models.JSONField(default=dict, blank=True)
    visa_info = models.TextField(blank=True)
    ai_generated = models.BooleanField(default=True)
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'destination_knowledge'
        ordering = ['-views_count']
        verbose_name_plural = 'Destination Knowledge'
        indexes = [
            models.Index(fields=['country'], name='dest_knowledge_country_idx'),
        ]

    def __str__(self):
        return f"{self.destination}, {self.country}"


class CulturalInfo(models.Model):
    """Religion & etiquette guides for destinations."""

    CATEGORY_CHOICES = [
        ('dress_code', 'Dress Code'),
        ('tipping', 'Tipping Etiquette'),
        ('greetings', 'Greetings & Gestures'),
        ('dining', 'Dining Etiquette'),
        ('religious', 'Religious Customs'),
        ('business', 'Business Etiquette'),
        ('photography', 'Photography Rules'),
        ('laws', 'Local Laws & Regulations'),
        ('taboos', 'Cultural Taboos'),
    ]

    destination = models.ForeignKey(DestinationKnowledge, on_delete=models.CASCADE,
                                     related_name='cultural_info')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    severity = models.CharField(max_length=20, default='advisory',
                                 choices=[('info', 'Info'), ('advisory', 'Advisory'),
                                          ('important', 'Important'), ('critical', 'Critical')])
    ai_generated = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cultural_info'
        ordering = ['category', '-created_at']
        verbose_name_plural = 'Cultural Info'
        indexes = [
            models.Index(fields=['destination', 'category'], name='cultural_dest_cat_idx'),
        ]

    def __str__(self):
        return f"{self.destination.destination} - {self.title}"


class UserDestinationTip(models.Model):
    """User-contributed tips moderated by AI."""

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='destination_tips')
    destination = models.ForeignKey(DestinationKnowledge, on_delete=models.CASCADE,
                                     related_name='user_tips')
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=50, blank=True, help_text='e.g. food, transport, safety')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    ai_moderation_score = models.FloatField(default=0, help_text='AI quality score 0-1')
    ai_moderation_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_destination_tips'
        ordering = ['-upvotes', '-created_at']
        indexes = [
            models.Index(fields=['destination', 'status'], name='user_tip_dest_status_idx'),
            models.Index(fields=['user'], name='user_tip_user_idx'),
        ]

    def __str__(self):
        return f"{self.user} tip: {self.title}"


# ─────────────────────────────────────────────────
# Phase 6: Social & Viral Growth Models
# ─────────────────────────────────────────────────

class TravelStoryGenerated(models.Model):
    """AI-generated travel story from a trip, shareable on social media."""

    FORMAT_CHOICES = [
        ('journal', 'Daily Journal'),
        ('instagram', 'Instagram Story'),
        ('blog', 'Blog Post'),
        ('social', 'Social Media Post'),
        ('thread', 'Twitter/X Thread'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='generated_stories')
    itinerary_id = models.IntegerField(null=True, blank=True, help_text='Source itinerary ID')
    title = models.CharField(max_length=300)
    content = models.TextField(help_text='AI-generated narrative')
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='journal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    destination = models.CharField(max_length=200, db_index=True)
    cover_image_url = models.URLField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    story_cards = models.JSONField(default=list, blank=True,
                                    help_text='Array of {day, title, content, mood, image_url}')
    share_token = models.CharField(max_length=32, unique=True, db_index=True)
    views_count = models.IntegerField(default=0)
    likes_count = models.IntegerField(default=0)
    dislikes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    shares_count = models.IntegerField(default=0)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'travel_stories_generated'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='gen_story_user_date_idx'),
            models.Index(fields=['destination'], name='gen_story_dest_idx'),
            models.Index(fields=['share_token'], name='gen_story_token_idx'),
        ]

    def __str__(self):
        return f"{self.title} by {self.user}"


class StoryLike(models.Model):
    """Track individual likes on generated stories."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='story_likes')
    story = models.ForeignKey(TravelStoryGenerated, on_delete=models.CASCADE,
                               related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'story_likes'
        unique_together = ('user', 'story')


class StoryDislike(models.Model):
    """Track individual dislikes on generated stories."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='story_dislikes')
    story = models.ForeignKey(TravelStoryGenerated, on_delete=models.CASCADE,
                               related_name='dislikes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'story_dislikes'
        unique_together = ('user', 'story')


class StoryComment(models.Model):
    """Comments on generated stories."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='story_comments')
    story = models.ForeignKey(TravelStoryGenerated, on_delete=models.CASCADE,
                               related_name='comments')
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'story_comments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} on {self.story.title}"


class TripTemplate(models.Model):
    """Cloneable trip templates created by influencers/users."""

    STYLE_CHOICES = [
        ('adventure', 'Adventure'),
        ('luxury', 'Luxury'),
        ('budget', 'Budget'),
        ('cultural', 'Cultural'),
        ('romantic', 'Romantic'),
        ('family', 'Family'),
        ('solo', 'Solo'),
        ('foodie', 'Foodie'),
        ('spiritual', 'Spiritual'),
        ('nature', 'Nature'),
    ]

    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='trip_templates')
    title = models.CharField(max_length=300)
    description = models.TextField()
    destination = models.CharField(max_length=200, db_index=True)
    country = models.CharField(max_length=100, blank=True)
    duration_days = models.IntegerField(default=1)
    style = models.CharField(max_length=20, choices=STYLE_CHOICES, default='adventure')
    estimated_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')
    cover_image_url = models.URLField(blank=True)
    itinerary_data = models.JSONField(default=list, blank=True,
                                       help_text='Array of {day, activities: [{time, title, description, category, cost}]}')
    tags = models.JSONField(default=list, blank=True)
    highlights = models.JSONField(default=list, blank=True, help_text='Top 3-5 highlights')
    is_featured = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False, help_text='Verified influencer template')
    clone_count = models.IntegerField(default=0)
    likes_count = models.IntegerField(default=0)
    dislikes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    views_count = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    rating_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'trip_templates'
        ordering = ['-clone_count', '-likes_count', '-created_at']
        indexes = [
            models.Index(fields=['destination'], name='template_dest_idx'),
            models.Index(fields=['style'], name='template_style_idx'),
            models.Index(fields=['creator'], name='template_creator_idx'),
            models.Index(fields=['-clone_count'], name='template_clones_idx'),
        ]

    def __str__(self):
        return f"{self.title} ({self.destination}) by {self.creator}"


class TemplateClone(models.Model):
    """Track when users clone a trip template."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='cloned_templates')
    template = models.ForeignKey(TripTemplate, on_delete=models.CASCADE,
                                  related_name='clones')
    itinerary_id = models.IntegerField(null=True, blank=True,
                                        help_text='Created itinerary ID from the clone')
    customizations = models.JSONField(default=dict, blank=True,
                                       help_text='Changes the user made')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'template_clones'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} cloned {self.template.title}"


class TemplateLike(models.Model):
    """Track individual likes on trip templates (per-user)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='template_likes')
    template = models.ForeignKey(TripTemplate, on_delete=models.CASCADE,
                                  related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'template_likes'
        unique_together = ('user', 'template')


class TemplateDislike(models.Model):
    """Track individual dislikes on trip templates (per-user)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='template_dislikes')
    template = models.ForeignKey(TripTemplate, on_delete=models.CASCADE,
                                  related_name='dislikes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'template_dislikes'
        unique_together = ('user', 'template')


class TemplateComment(models.Model):
    """Comments on trip templates."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='template_comments')
    template = models.ForeignKey(TripTemplate, on_delete=models.CASCADE,
                                  related_name='comments')
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'template_comments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} on {self.template.title}"


class ContentItem(models.Model):
    """Unified content hub item — photos, stories, tips from community."""

    CONTENT_TYPE_CHOICES = [
        ('photo', 'Photo'),
        ('story', 'Story'),
        ('tip', 'Tip'),
        ('video', 'Video'),
        ('audio', 'Audio'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='content_items')
    destination = models.CharField(max_length=200, db_index=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    media_url = models.URLField(blank=True, help_text='Photo/video/audio URL')
    body = models.TextField(blank=True, help_text='Text content for stories/tips')
    tags = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ai_moderation_score = models.FloatField(default=0)
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'content_items'
        ordering = ['-upvotes', '-created_at']
        indexes = [
            models.Index(fields=['destination', 'content_type', 'status'], name='content_dest_type_idx'),
            models.Index(fields=['user'], name='content_user_idx'),
        ]

    def __str__(self):
        return f"{self.content_type}: {self.title} ({self.destination})"


class ContentVote(models.Model):
    """Track individual up/down votes on content items (per-user, mutually exclusive)."""

    VOTE_CHOICES = [
        ('up', 'Upvote'),
        ('down', 'Downvote'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='content_votes')
    content_item = models.ForeignKey(ContentItem, on_delete=models.CASCADE,
                                      related_name='votes')
    vote = models.CharField(max_length=4, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'content_votes'
        unique_together = ('user', 'content_item')


class ContentComment(models.Model):
    """Comments on content items."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='content_comments')
    content_item = models.ForeignKey(ContentItem, on_delete=models.CASCADE,
                                      related_name='comments')
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'content_comments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} on {self.content_item.title}"


# ──────────────────────────────────────────────────────────────────────
# Phase 7: Faith & Health Awareness
# ──────────────────────────────────────────────────────────────────────

class PrayerTimeCache(models.Model):
    """Cached prayer times for a destination on a given date."""

    destination = models.CharField(max_length=200, db_index=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    date = models.DateField()
    fajr = models.CharField(max_length=10)
    sunrise = models.CharField(max_length=10)
    dhuhr = models.CharField(max_length=10)
    asr = models.CharField(max_length=10)
    maghrib = models.CharField(max_length=10)
    isha = models.CharField(max_length=10)
    method = models.CharField(max_length=50, default='ISNA', help_text='Calculation method')
    timezone_name = models.CharField(max_length=60, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'prayer_time_cache'
        unique_together = ['destination', 'date', 'method']
        indexes = [
            models.Index(fields=['destination', 'date'], name='prayer_dest_date_idx'),
        ]

    def __str__(self):
        return f"Prayer times for {self.destination} on {self.date}"


class WorshipPlace(models.Model):
    """Places of worship near a destination."""

    WORSHIP_TYPE_CHOICES = [
        ('mosque', 'Mosque'),
        ('church', 'Church'),
        ('synagogue', 'Synagogue'),
        ('temple', 'Temple'),
        ('gurdwara', 'Gurdwara'),
        ('monastery', 'Monastery'),
        ('shrine', 'Shrine'),
        ('other', 'Other'),
    ]

    destination = models.CharField(max_length=200, db_index=True)
    name = models.CharField(max_length=300)
    worship_type = models.CharField(max_length=20, choices=WORSHIP_TYPE_CHOICES)
    faith = models.CharField(max_length=20, choices=[
        ('islam', 'Islam'), ('christianity', 'Christianity'),
        ('judaism', 'Judaism'), ('hinduism', 'Hinduism'),
        ('buddhism', 'Buddhism'), ('sikhism', 'Sikhism'),
        ('other', 'Other'),
    ])
    address = models.TextField(blank=True, default='')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True, default='')
    services = models.JSONField(default=list, blank=True, help_text='Available services e.g. ["friday_prayer","sunday_mass"]')
    amenities = models.JSONField(default=list, blank=True, help_text='e.g. ["wudu_facility","parking","wheelchair_access"]')
    operating_hours = models.JSONField(default=dict, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    halal_food_nearby = models.BooleanField(default=False)
    kosher_food_nearby = models.BooleanField(default=False)
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'worship_places'
        indexes = [
            models.Index(fields=['destination', 'faith'], name='worship_dest_faith_idx'),
            models.Index(fields=['worship_type'], name='worship_type_idx'),
        ]

    def __str__(self):
        return f"{self.name} ({self.worship_type}) - {self.destination}"


class SpiritualSite(models.Model):
    """Spiritual and religious heritage sites / pilgrimage destinations."""

    CATEGORY_CHOICES = [
        ('pilgrimage', 'Pilgrimage Site'),
        ('heritage', 'Religious Heritage'),
        ('meditation', 'Meditation / Retreat'),
        ('festival_venue', 'Festival Venue'),
        ('sacred_natural', 'Sacred Natural Site'),
    ]

    destination = models.CharField(max_length=200, db_index=True)
    name = models.CharField(max_length=300)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    faiths = models.JSONField(default=list, help_text='Relevant faiths e.g. ["hinduism","buddhism"]')
    description = models.TextField()
    significance = models.TextField(blank=True, default='')
    visitor_tips = models.TextField(blank=True, default='')
    dress_code = models.CharField(max_length=300, blank=True, default='')
    best_time_to_visit = models.CharField(max_length=200, blank=True, default='')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    image_url = models.URLField(blank=True, default='')
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'spiritual_sites'
        indexes = [
            models.Index(fields=['destination', 'category'], name='spiritual_dest_cat_idx'),
        ]

    def __str__(self):
        return f"{self.name} ({self.category}) - {self.destination}"


class MedicalFacility(models.Model):
    """Medical facilities near travel destinations."""

    FACILITY_TYPE_CHOICES = [
        ('hospital', 'Hospital'),
        ('clinic', 'Clinic'),
        ('pharmacy', 'Pharmacy'),
        ('emergency', 'Emergency Room'),
        ('dental', 'Dental Clinic'),
        ('specialist', 'Specialist'),
    ]

    destination = models.CharField(max_length=200, db_index=True)
    name = models.CharField(max_length=300)
    facility_type = models.CharField(max_length=20, choices=FACILITY_TYPE_CHOICES)
    address = models.TextField(blank=True, default='')
    phone = models.CharField(max_length=50, blank=True, default='')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    emergency_24h = models.BooleanField(default=False)
    english_speaking = models.BooleanField(default=False)
    accepts_travel_insurance = models.BooleanField(default=False)
    specialties = models.JSONField(default=list, blank=True)
    operating_hours = models.JSONField(default=dict, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    wheelchair_accessible = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'medical_facilities'
        verbose_name_plural = 'Medical facilities'
        indexes = [
            models.Index(fields=['destination', 'facility_type'], name='medical_dest_type_idx'),
        ]

    def __str__(self):
        return f"{self.name} ({self.facility_type}) - {self.destination}"


class AccessibilityRating(models.Model):
    """Accessibility ratings for venues and destinations."""

    VENUE_TYPE_CHOICES = [
        ('hotel', 'Hotel'),
        ('restaurant', 'Restaurant'),
        ('attraction', 'Tourist Attraction'),
        ('transport', 'Transport Hub'),
        ('worship', 'Place of Worship'),
        ('medical', 'Medical Facility'),
        ('shopping', 'Shopping'),
    ]

    MOBILITY_RATING_CHOICES = [
        (1, 'Not Accessible'),
        (2, 'Limited Access'),
        (3, 'Partially Accessible'),
        (4, 'Mostly Accessible'),
        (5, 'Fully Accessible'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='accessibility_ratings',
    )
    destination = models.CharField(max_length=200, db_index=True)
    venue_name = models.CharField(max_length=300)
    venue_type = models.CharField(max_length=20, choices=VENUE_TYPE_CHOICES)
    mobility_rating = models.IntegerField(choices=MOBILITY_RATING_CHOICES)
    wheelchair_accessible = models.BooleanField(default=False)
    elevator_available = models.BooleanField(default=False)
    accessible_restroom = models.BooleanField(default=False)
    braille_signage = models.BooleanField(default=False)
    hearing_loop = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'accessibility_ratings'
        unique_together = ['user', 'destination', 'venue_name']
        indexes = [
            models.Index(fields=['destination', 'venue_type'], name='access_dest_venue_idx'),
        ]

    def __str__(self):
        return f"{self.venue_name} - {self.mobility_rating}/5 ({self.destination})"


class MedicationReminder(models.Model):
    """User medication reminders with timezone awareness."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='medication_reminders',
    )
    medication_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100, blank=True, default='')
    home_time = models.TimeField(help_text='Time to take medication in home timezone')
    home_timezone = models.CharField(max_length=60)
    frequency = models.CharField(max_length=50, default='daily', help_text='e.g. daily, twice_daily, weekly')
    notes = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'medication_reminders'
        indexes = [
            models.Index(fields=['user', 'is_active'], name='med_user_active_idx'),
        ]

    def __str__(self):
        return f"{self.medication_name} - {self.home_time} ({self.user})"


class HealthInsuranceInfo(models.Model):
    """Travel health insurance recommendations per country."""

    country = models.CharField(max_length=100, unique=True)
    risk_level = models.CharField(max_length=20, choices=[
        ('low', 'Low'), ('moderate', 'Moderate'), ('high', 'High'),
    ], default='moderate')
    recommended_coverage = models.JSONField(
        default=list, blank=True,
        help_text='e.g. ["emergency_evacuation","hospitalization","dental"]',
    )
    avg_hospital_cost_per_day_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    public_healthcare_available = models.BooleanField(default=False)
    reciprocal_agreements = models.JSONField(
        default=list, blank=True,
        help_text='Countries with reciprocal health agreements',
    )
    emergency_number = models.CharField(max_length=20, default='112')
    notes = models.TextField(blank=True, default='')
    vaccination_requirements = models.JSONField(default=list, blank=True)
    malaria_risk = models.BooleanField(default=False)
    altitude_risk = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'health_insurance_info'
        verbose_name_plural = 'Health insurance info'

    def __str__(self):
        return f"Health Insurance Info: {self.country} ({self.risk_level})"
