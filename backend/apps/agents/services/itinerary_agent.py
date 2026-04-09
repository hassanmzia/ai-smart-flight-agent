"""
Itinerary Generation Agent service for async task execution.
Wraps the auto-builder for use in Celery tasks.
"""
import logging

logger = logging.getLogger(__name__)


class ItineraryAgent:
    """Generate complete itineraries using the Smart Auto-Builder."""

    def generate_itinerary(self, params: dict) -> dict:
        """
        Generate a complete trip itinerary.

        Args:
            params: dict with destination, start_date, end_date, origin, budget, travelers, etc.
        """
        try:
            from apps.agents.auto_builder import SmartItineraryBuilder
            from apps.users.models import User

            user = None
            if params.get('user_id'):
                try:
                    user = User.objects.get(id=params['user_id'])
                except User.DoesNotExist:
                    pass

            builder = SmartItineraryBuilder(user=user)
            result = builder.build(
                destination=params.get('destination', ''),
                start_date=params.get('start_date', ''),
                end_date=params.get('end_date', ''),
                origin=params.get('origin', ''),
                budget=params.get('budget'),
                travelers=params.get('travelers', 1),
                trip_style=params.get('trip_style', 'balanced'),
                preferences=params.get('preferences', {}),
            )
            return result

        except Exception as e:
            logger.error(f"Itinerary generation failed: {e}")
            return {'error': str(e)}
