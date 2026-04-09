"""
Flight Search Agent service for async task execution.
Wraps the multi_agent_system flight search for use in Celery tasks.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class FlightSearchAgent:
    """Search for flights using SerpAPI Google Flights integration."""

    def search(self, params: dict) -> dict:
        """
        Execute flight search.

        Args:
            params: dict with origin, destination, departure_date, return_date, passengers, etc.
        """
        try:
            from apps.agents.integrations.serpapi_client import SerpAPIClient
            client = SerpAPIClient()

            result = client.search_flights(
                origin=params.get('origin', ''),
                destination=params.get('destination', ''),
                departure_date=params.get('departure_date', ''),
                return_date=params.get('return_date'),
                adults=params.get('passengers', 1),
                cabin_class=params.get('cabin_class', 'economy'),
            )
            return result or {'flights': [], 'message': 'No flights found'}

        except Exception as e:
            logger.error(f"Flight search failed: {e}")
            return {'error': str(e), 'flights': []}
