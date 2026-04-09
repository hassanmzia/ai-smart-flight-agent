from rest_framework import serializers
from django.db.models import Avg
from .models import AgentSession, AgentExecution, AgentLog, RAGDocument


class AgentLogSerializer(serializers.ModelSerializer):
    """Serializer for AgentLog model."""

    class Meta:
        model = AgentLog
        fields = [
            'id', 'log_level', 'message', 'log_data', 'agent_type',
            'function_name', 'line_number', 'exception_type',
            'exception_traceback', 'timestamp', 'created_at'
        ]
        read_only_fields = ['id', 'timestamp', 'created_at']


class AgentExecutionSerializer(serializers.ModelSerializer):
    """Serializer for AgentExecution model."""

    logs = AgentLogSerializer(many=True, read_only=True)
    agent_type_display = serializers.CharField(source='get_agent_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = AgentExecution
        fields = [
            'id', 'execution_id', 'agent_type', 'agent_type_display',
            'status', 'status_display', 'input_data', 'output_data',
            'error_message', 'agent_config', 'model_used', 'tokens_used',
            'execution_time_ms', 'duration_seconds', 'cost', 'tools_called',
            'function_calls', 'started_at', 'completed_at', 'created_at',
            'updated_at', 'logs'
        ]
        read_only_fields = [
            'id', 'execution_id', 'execution_time_ms', 'started_at',
            'completed_at', 'created_at', 'updated_at'
        ]

    def get_duration_seconds(self, obj):
        """Calculate duration in seconds."""
        if obj.started_at and obj.completed_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None


class AgentExecutionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for AgentExecution list views."""

    agent_type_display = serializers.CharField(source='get_agent_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AgentExecution
        fields = [
            'id', 'execution_id', 'agent_type', 'agent_type_display',
            'status', 'status_display', 'tokens_used', 'execution_time_ms',
            'cost', 'started_at', 'completed_at'
        ]
        read_only_fields = fields


class AgentSessionSerializer(serializers.ModelSerializer):
    """Serializer for AgentSession model."""

    executions = AgentExecutionListSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_seconds = serializers.SerializerMethodField()
    average_execution_time = serializers.SerializerMethodField()

    class Meta:
        model = AgentSession
        fields = [
            'id', 'session_id', 'status', 'status_display',
            'conversation_context', 'user_intent', 'detected_entities',
            'total_executions', 'total_tokens_used', 'total_cost',
            'started_at', 'completed_at', 'last_activity_at',
            'duration_seconds', 'average_execution_time',
            'created_at', 'updated_at', 'executions'
        ]
        read_only_fields = [
            'id', 'session_id', 'total_executions', 'total_tokens_used',
            'total_cost', 'started_at', 'completed_at', 'last_activity_at',
            'created_at', 'updated_at'
        ]

    def get_duration_seconds(self, obj):
        """Calculate session duration in seconds."""
        if obj.started_at and obj.completed_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None

    def get_average_execution_time(self, obj):
        """Calculate average execution time across all executions."""
        executions = obj.executions.filter(status='completed')
        if not executions.exists():
            return None
        avg_time = executions.aggregate(Avg('execution_time_ms'))['execution_time_ms__avg']
        return avg_time


class AgentSessionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for AgentSession list views."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    execution_count = serializers.SerializerMethodField()

    class Meta:
        model = AgentSession
        fields = [
            'id', 'session_id', 'status', 'status_display', 'user_intent',
            'total_executions', 'total_tokens_used', 'total_cost',
            'started_at', 'completed_at', 'execution_count'
        ]
        read_only_fields = fields

    def get_execution_count(self, obj):
        """Get count of executions by status."""
        return {
            'total': obj.executions.count(),
            'completed': obj.executions.filter(status='completed').count(),
            'failed': obj.executions.filter(status='failed').count(),
            'running': obj.executions.filter(status='running').count(),
        }


class AgentSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new agent sessions."""

    class Meta:
        model = AgentSession
        fields = ['user_intent', 'conversation_context', 'detected_entities']


class AgentExecutionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new agent executions."""

    class Meta:
        model = AgentExecution
        fields = [
            'agent_type', 'input_data', 'agent_config', 'model_used'
        ]


class RAGDocumentSerializer(serializers.ModelSerializer):
    """Serializer for RAGDocument model."""

    uploaded_by_email = serializers.EmailField(source='uploaded_by.email', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = RAGDocument
        fields = [
            'id', 'title', 'description', 'file', 'file_url', 'file_type',
            'file_size', 'status', 'error_message', 'chunk_count', 'scope',
            'tags', 'uploaded_by', 'uploaded_by_email', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'file_type', 'file_size', 'status', 'error_message',
            'chunk_count', 'uploaded_by', 'uploaded_by_email',
            'created_at', 'updated_at',
        ]

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class RAGDocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading a new RAG document."""

    class Meta:
        model = RAGDocument
        fields = ['title', 'description', 'file', 'scope', 'tags']


# ─────────────────────────────────────────────────
# Commercialization Models Serializers
# ─────────────────────────────────────────────────

from .models import (
    AgentConversation, AgentMessage, AgentTask, UserPreference,
    AgentAnalytics, AIModel, TripCollaboration, TripCollaborator,
    CollaborationVote, Subscription, AffiliateClick, PriceWatch,
)


class AgentMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentMessage
        fields = [
            'id', 'conversation', 'content', 'sender_type', 'user',
            'message_type', 'metadata', 'intent', 'response_time_ms',
            'tokens_used', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class AgentConversationSerializer(serializers.ModelSerializer):
    messages = AgentMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = AgentConversation
        fields = [
            'id', 'user', 'title', 'status', 'is_archived',
            'conversation_type', 'metadata', 'created_at', 'updated_at',
            'messages', 'message_count',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()


class AgentConversationListSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = AgentConversation
        fields = [
            'id', 'title', 'status', 'conversation_type',
            'created_at', 'updated_at', 'message_count',
        ]
        read_only_fields = fields

    def get_message_count(self, obj):
        return obj.messages.count()


class AgentTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentTask
        fields = [
            'id', 'user', 'task_type', 'status', 'parameters', 'result',
            'error_message', 'started_at', 'completed_at', 'created_at',
        ]
        read_only_fields = ['id', 'user', 'started_at', 'completed_at', 'created_at']


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = [
            'id', 'user', 'preferences', 'travel_dna', 'preferred_airlines',
            'preferred_hotel_chains', 'preferred_cuisines', 'budget_range',
            'trip_style', 'booking_advance_days', 'last_trained',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'travel_dna', 'last_trained', 'created_at', 'updated_at']


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'plan', 'status', 'stripe_customer_id',
            'stripe_subscription_id', 'current_period_start', 'current_period_end',
            'ai_plans_used', 'ai_plans_limit', 'price_alerts_used',
            'price_alerts_limit', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'user', 'stripe_customer_id', 'stripe_subscription_id',
            'ai_plans_used', 'price_alerts_used', 'created_at', 'updated_at',
        ]


class AffiliateClickSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffiliateClick
        fields = [
            'id', 'user', 'partner', 'click_type', 'destination',
            'tracking_id', 'revenue', 'status', 'clicked_at', 'converted_at',
        ]
        read_only_fields = [
            'id', 'tracking_id', 'revenue', 'clicked_at', 'converted_at',
        ]


class PriceWatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceWatch
        fields = [
            'id', 'user', 'watch_type', 'search_params', 'target_price',
            'current_price', 'lowest_price', 'price_history', 'is_active',
            'last_checked', 'notify_on_any_drop', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'user', 'current_price', 'lowest_price', 'price_history',
            'last_checked', 'created_at', 'updated_at',
        ]


class TripCollaborationSerializer(serializers.ModelSerializer):
    collaborators = serializers.SerializerMethodField()

    class Meta:
        model = TripCollaboration
        fields = [
            'id', 'itinerary', 'owner', 'status', 'invite_code',
            'max_participants', 'created_at', 'updated_at', 'collaborators',
        ]
        read_only_fields = ['id', 'owner', 'invite_code', 'created_at', 'updated_at']

    def get_collaborators(self, obj):
        return TripCollaboratorSerializer(obj.collaborators.all(), many=True).data


class TripCollaboratorSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = TripCollaborator
        fields = ['id', 'collaboration', 'user', 'username', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class CollaborationVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollaborationVote
        fields = [
            'id', 'collaboration', 'user', 'item_type', 'item_id',
            'vote', 'comment', 'created_at',
        ]
        read_only_fields = ['id', 'user', 'created_at']


class AgentAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentAnalytics
        fields = ['id', 'date', 'metrics', 'created_at']
        read_only_fields = fields


class AIModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIModel
        fields = ['id', 'name', 'version', 'model_type', 'is_active', 'config', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
