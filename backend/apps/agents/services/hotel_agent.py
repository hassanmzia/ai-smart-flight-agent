"""
Hotel Search Agent service for async task execution.
Wraps the SerpAPI hotel search for use in Celery tasks.
"""
import logging

logger = logging.getLogger(__name__)


class HotelSearchAgent:
    """Search for hotels using SerpAPI Google Hotels integration."""

    def search(self, params: dict) -> dict:
        """
        Execute hotel search.

        Args:
            params: dict with location, check_in, check_out, guests, etc.
        """
        try:
            from apps.agents.integrations.serpapi_client import SerpAPIClient
            client = SerpAPIClient()

            result = client.search_hotels(
                location=params.get('location', params.get('destination', '')),
                check_in=params.get('check_in', params.get('departure_date', '')),
                check_out=params.get('check_out', params.get('return_date', '')),
                adults=params.get('guests', params.get('passengers', 1)),
            )
            return result or {'hotels': [], 'message': 'No hotels found'}

        except Exception as e:
            logger.error(f"Hotel search failed: {e}")
            return {'error': str(e), 'hotels': []}
