"""
Recommendation Agent service for async task execution.
Wraps the personalization service for use in Celery tasks.
"""
import logging

logger = logging.getLogger(__name__)


class RecommendationAgent:
    """Generate personalized trip recommendations."""

    def get_recommendations(self, params: dict) -> dict:
        """
        Get personalized recommendations.

        Args:
            params: dict with user_id, limit, etc.
        """
        try:
            from apps.agents.personalization_service import PersonalizationService
            from apps.users.models import User

            user = None
            if params.get('user_id'):
                try:
                    user = User.objects.get(id=params['user_id'])
                except User.DoesNotExist:
                    return {'error': 'User not found', 'recommendations': []}

            service = PersonalizationService()
            result = service.get_recommendations(
                user=user,
                limit=params.get('limit', 5),
            )
            return result

        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return {'error': str(e), 'recommendations': []}
