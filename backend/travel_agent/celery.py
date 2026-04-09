"""
Celery configuration for AI Travel Agent project.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_agent.settings')

app = Celery('travel_agent')

# Load task modules from all registered Django apps
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    # Check for price drops every hour
    'check-price-alerts': {
        'task': 'apps.flights.tasks.check_price_alerts',
        'schedule': crontab(minute=0),  # Every hour
    },
    # Update flight status every 30 minutes
    'update-flight-status': {
        'task': 'apps.flights.tasks.update_flight_status',
        'schedule': crontab(minute='*/30'),
    },
    # Send booking reminders 24 hours before departure
    'send-booking-reminders': {
        'task': 'apps.bookings.tasks.send_booking_reminders',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    # Clean up expired sessions
    'cleanup-expired-sessions': {
        'task': 'apps.users.tasks.cleanup_expired_sessions',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    # Update weather data
    'update-weather-data': {
        'task': 'apps.itineraries.tasks.update_weather_data',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
    # Check price watches every 2 hours
    'check-price-watches': {
        'task': 'apps.agents.tasks.check_price_watches',
        'schedule': crontab(minute=30, hour='*/2'),  # Every 2 hours at :30
    },
    # Clean up old agent logs weekly
    'cleanup-old-agent-logs': {
        'task': 'apps.agents.tasks.cleanup_old_logs',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sundays at 3 AM
    },
    # Process conversation analytics daily
    'process-conversation-analytics': {
        'task': 'apps.agents.tasks.process_conversation_analytics',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    # Train personalization models weekly
    'train-personalization-models': {
        'task': 'apps.agents.tasks.train_personalization_model',
        'schedule': crontab(hour=4, minute=0, day_of_week=1),  # Mondays at 4 AM
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')
