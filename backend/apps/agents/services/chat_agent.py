"""
Chat Agent service for async task execution.
Processes chat messages through the LangChain-based agent for Celery tasks.
"""
import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)


class ChatAgent:
    """Process chat messages through the AI agent system."""

    def process_message(self, params: dict) -> dict:
        """
        Process a chat message and return an AI response.

        Args:
            params: dict with message, conversation_id, user_id, etc.
        """
        message = params.get('message', '')
        if not message:
            return {'error': 'No message provided', 'response': ''}

        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return {
                'response': self._fallback_response(message),
                'source': 'fallback',
            }

        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(
                model='gpt-4o-mini',
                temperature=0.7,
                api_key=api_key,
                request_timeout=30,
            )

            response = model.invoke([
                SystemMessage(content=(
                    "You are an AI travel assistant. Help the user plan trips, "
                    "find flights, hotels, and activities. Be helpful and concise."
                )),
                HumanMessage(content=message),
            ])

            return {
                'response': response.content,
                'source': 'llm',
            }

        except Exception as e:
            logger.error(f"Chat processing failed: {e}")
            return {
                'response': self._fallback_response(message),
                'source': 'fallback',
                'error': str(e),
            }

    def _fallback_response(self, message: str) -> str:
        """Generate a basic fallback response when LLM is unavailable."""
        msg_lower = message.lower()
        if any(w in msg_lower for w in ['flight', 'fly', 'airport']):
            return "I can help you find flights! Please provide your origin, destination, and travel dates."
        elif any(w in msg_lower for w in ['hotel', 'stay', 'accommodation']):
            return "I can help you find hotels! Where are you traveling and what are your check-in/check-out dates?"
        elif any(w in msg_lower for w in ['plan', 'trip', 'itinerary']):
            return "I'd love to help plan your trip! Where would you like to go and for how long?"
        return "I'm your AI travel assistant. I can help with flights, hotels, trip planning, and more. How can I help?"
