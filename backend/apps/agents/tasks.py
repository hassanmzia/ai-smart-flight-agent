"""
Celery tasks for AI agent operations.
"""
import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def run_agent_task_async(self, task_type, user_id, params=None):
    """
    Run an AI agent task asynchronously.

    Args:
        task_type: Type of agent task (e.g., 'flight_search', 'itinerary_generation', 'chat')
        user_id: ID of the user requesting the task
        params: Task parameters (dict)
    """
    try:
        from .models import AgentTask, AgentConversation
        from apps.users.models import User
        from apps.notifications.tasks import send_notification

        logger.info(f"Starting agent task: {task_type} for user {user_id}")

        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found")
            return {'status': 'error', 'message': 'User not found'}

        # Create task record
        task = AgentTask.objects.create(
            user=user,
            task_type=task_type,
            status='processing',
            parameters=params or {},
            started_at=timezone.now()
        )

        try:
            result = None

            # Route to appropriate agent handler
            if task_type == 'flight_search':
                from .services.flight_agent import FlightSearchAgent
                agent = FlightSearchAgent()
                result = agent.search(params)

            elif task_type == 'itinerary_generation':
                from .services.itinerary_agent import ItineraryAgent
                agent = ItineraryAgent()
                result = agent.generate_itinerary(params)

            elif task_type == 'hotel_search':
                from .services.hotel_agent import HotelSearchAgent
                agent = HotelSearchAgent()
                result = agent.search(params)

            elif task_type == 'recommendation':
                from .services.recommendation_agent import RecommendationAgent
                agent = RecommendationAgent()
                result = agent.get_recommendations(params)

            elif task_type == 'chat':
                from .services.chat_agent import ChatAgent
                agent = ChatAgent()
                result = agent.process_message(params)

            else:
                raise ValueError(f"Unknown task type: {task_type}")

            # Update task with result
            task.status = 'completed'
            task.result = result
            task.completed_at = timezone.now()
            task.save()

            # Send notification to user
            send_notification.delay(
                user_id=user_id,
                notification_type='agent_task_completed',
                title='AI Task Completed',
                message=f'Your {task_type} request has been completed.',
                data={
                    'task_id': str(task.id),
                    'task_type': task_type,
                    'result': result
                },
                channels=['database', 'websocket']
            )

            logger.info(f"Agent task {task.id} completed successfully")

            return {
                'status': 'success',
                'task_id': str(task.id),
                'result': result
            }

        except Exception as e:
            # Task failed
            task.status = 'failed'
            task.error_message = str(e)
            task.completed_at = timezone.now()
            task.save()

            logger.error(f"Agent task {task.id} failed: {str(e)}")

            # Notify user of failure
            send_notification.delay(
                user_id=user_id,
                notification_type='agent_task_failed',
                title='AI Task Failed',
                message=f'Your {task_type} request encountered an error.',
                data={
                    'task_id': str(task.id),
                    'task_type': task_type,
                    'error': str(e)
                },
                channels=['database', 'websocket']
            )

            raise

    except Exception as exc:
        logger.error(f"Error in run_agent_task_async: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def cleanup_old_logs(self, days=90):
    """
    Clean up old agent logs and conversations.

    Args:
        days: Delete logs older than this many days
    """
    try:
        from .models import AgentTask, AgentLog, AgentConversation

        logger.info(f"Cleaning up agent logs older than {days} days")

        cutoff_date = timezone.now() - timedelta(days=days)

        # Delete old completed tasks
        deleted_tasks, _ = AgentTask.objects.filter(
            status__in=['completed', 'failed'],
            completed_at__lt=cutoff_date
        ).delete()

        # Delete old logs
        deleted_logs, _ = AgentLog.objects.filter(
            created_at__lt=cutoff_date
        ).delete()

        # Archive old conversations (don't delete, just mark as archived)
        archived_conversations = AgentConversation.objects.filter(
            updated_at__lt=cutoff_date,
            is_archived=False
        ).update(is_archived=True)

        logger.info(
            f"Cleanup completed. Tasks deleted: {deleted_tasks}, "
            f"Logs deleted: {deleted_logs}, Conversations archived: {archived_conversations}"
        )

        return {
            'status': 'success',
            'deleted_tasks': deleted_tasks,
            'deleted_logs': deleted_logs,
            'archived_conversations': archived_conversations
        }

    except Exception as exc:
        logger.error(f"Error in cleanup_old_logs task: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def train_personalization_model(self, user_id=None):
    """
    Train or update personalization models for users.

    Args:
        user_id: Optional specific user ID. If None, updates all users.
    """
    try:
        from .models import UserPreference
        from apps.users.models import User
        from apps.bookings.models import Booking

        logger.info(f"Training personalization model for user: {user_id or 'all'}")

        if user_id:
            users = User.objects.filter(id=user_id)
        else:
            # Only train for users with sufficient activity
            users = User.objects.filter(
                is_active=True,
                bookings__isnull=False
            ).distinct()

        trained_count = 0

        for user in users:
            try:
                # Gather user history
                bookings = Booking.objects.filter(
                    user=user,
                    status='completed'
                ).order_by('-created_at')[:50]

                if bookings.count() < 3:
                    # Not enough data
                    continue

                # Extract preferences
                preferences = {
                    'preferred_airlines': [],
                    'preferred_cabin_class': None,
                    'price_sensitivity': 'medium',
                    'preferred_destinations': [],
                    'booking_advance_days': 0,
                    'trip_duration_preference': 0,
                }

                # Analyze booking patterns
                airlines = {}
                cabin_classes = {}
                destinations = {}
                total_advance_days = 0
                total_duration = 0

                for booking in bookings:
                    # Count airlines
                    if hasattr(booking, 'flight') and booking.flight:
                        airline = booking.flight.airline
                        airlines[airline] = airlines.get(airline, 0) + 1

                        # Cabin class
                        cabin = booking.cabin_class
                        cabin_classes[cabin] = cabin_classes.get(cabin, 0) + 1

                    # Destinations
                    dest = booking.destination
                    destinations[dest] = destinations.get(dest, 0) + 1

                    # Booking advance time
                    if booking.departure_time and booking.created_at:
                        advance_days = (booking.departure_time.date() - booking.created_at.date()).days
                        total_advance_days += advance_days

                    # Trip duration
                    if booking.return_time and booking.departure_time:
                        duration = (booking.return_time.date() - booking.departure_time.date()).days
                        total_duration += duration

                # Calculate preferences
                if airlines:
                    preferences['preferred_airlines'] = sorted(airlines, key=airlines.get, reverse=True)[:3]

                if cabin_classes:
                    preferences['preferred_cabin_class'] = max(cabin_classes, key=cabin_classes.get)

                if destinations:
                    preferences['preferred_destinations'] = sorted(destinations, key=destinations.get, reverse=True)[:5]

                if bookings.count() > 0:
                    preferences['booking_advance_days'] = total_advance_days // bookings.count()
                    preferences['trip_duration_preference'] = total_duration // bookings.count()

                # Save preferences
                user_pref, created = UserPreference.objects.update_or_create(
                    user=user,
                    defaults={
                        'preferences': preferences,
                        'last_trained': timezone.now()
                    }
                )

                trained_count += 1
                logger.info(f"Personalization model updated for user {user.id}")

            except Exception as e:
                logger.error(f"Error training model for user {user.id}: {str(e)}")
                continue

        logger.info(f"Personalization training completed. {trained_count} users trained.")

        return {
            'status': 'success',
            'users_trained': trained_count
        }

    except Exception as exc:
        logger.error(f"Error in train_personalization_model task: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def process_conversation_analytics(self):
    """
    Process analytics for agent conversations to improve performance.
    """
    try:
        from .models import AgentConversation, AgentAnalytics
        from datetime import timedelta

        logger.info("Processing conversation analytics")

        # Get conversations from last 24 hours
        yesterday = timezone.now() - timedelta(hours=24)
        conversations = AgentConversation.objects.filter(
            updated_at__gte=yesterday
        )

        analytics = {
            'total_conversations': conversations.count(),
            'avg_messages_per_conversation': 0,
            'successful_bookings': 0,
            'abandoned_conversations': 0,
            'avg_response_time': 0,
            'common_intents': {},
            'user_satisfaction': {},
        }

        total_messages = 0
        total_response_time = 0

        for conversation in conversations:
            # Count messages
            message_count = conversation.messages.count()
            total_messages += message_count

            # Check if led to booking
            if hasattr(conversation, 'booking') and conversation.booking:
                analytics['successful_bookings'] += 1

            # Check if abandoned
            if message_count > 2 and not hasattr(conversation, 'booking'):
                time_since_last = timezone.now() - conversation.updated_at
                if time_since_last > timedelta(hours=24):
                    analytics['abandoned_conversations'] += 1

            # Analyze intents
            for message in conversation.messages.all():
                if hasattr(message, 'intent'):
                    intent = message.intent
                    analytics['common_intents'][intent] = analytics['common_intents'].get(intent, 0) + 1

                # Response time
                if hasattr(message, 'response_time_ms'):
                    total_response_time += message.response_time_ms

        # Calculate averages
        if conversations.count() > 0:
            analytics['avg_messages_per_conversation'] = total_messages / conversations.count()

        if total_messages > 0:
            analytics['avg_response_time'] = total_response_time / total_messages

        # Save analytics
        AgentAnalytics.objects.create(
            date=timezone.now().date(),
            metrics=analytics
        )

        logger.info("Conversation analytics processed successfully")

        return {
            'status': 'success',
            'analytics': analytics
        }

    except Exception as exc:
        logger.error(f"Error in process_conversation_analytics task: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2)
def sync_ai_model_updates(self):
    """
    Check for and sync AI model updates from the model registry.
    """
    try:
        from .models import AIModel

        logger.info("Checking for AI model updates")

        # TODO: Implement actual model registry sync
        # This would check for new model versions and download them

        models_updated = 0

        logger.info(f"AI model sync completed. {models_updated} models updated.")

        return {
            'status': 'success',
            'models_updated': models_updated
        }

    except Exception as exc:
        logger.error(f"Error in sync_ai_model_updates task: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2)
def check_price_watches(self):
    """Check all active price watches for price changes. Runs every 2 hours."""
    try:
        from .price_monitor import PriceMonitorService
        alerts_sent = PriceMonitorService.check_price_watches()
        logger.info(f"Price watch check completed. {alerts_sent} alerts sent.")
        return {'status': 'success', 'alerts_sent': alerts_sent}
    except Exception as exc:
        logger.error(f"Error in check_price_watches: {str(exc)}")
        raise self.retry(exc=exc)
