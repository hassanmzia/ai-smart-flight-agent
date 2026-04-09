"""
Multi-Modal Input Agent
- Voice-to-Trip: Transcribe voice via OpenAI Whisper, extract travel intent
- Image-to-Trip: Analyze travel photos via GPT-4 Vision, identify destination
- Screenshot parsing: Extract deal info from flight/hotel screenshots
"""
import os
import logging
import json
from typing import Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)


class MultiModalAgent:
    """Handles voice and image inputs for trip planning."""

    def __init__(self):
        self.api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))

    def _has_key(self):
        return self.api_key and self.api_key not in ('your_openai_api_key_here', '')

    def transcribe_voice(self, audio_file) -> Dict[str, Any]:
        """Transcribe voice input using OpenAI Whisper API."""
        try:
            if not self._has_key():
                return {'success': False, 'error': 'OpenAI API key not configured'}

            import openai
            client = openai.OpenAI(api_key=self.api_key)

            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
            )
            text = transcription if isinstance(transcription, str) else transcription.text
            intent = self._extract_travel_intent(text)

            return {'success': True, 'transcription': text, 'intent': intent}

        except Exception as e:
            logger.error(f"Voice transcription failed: {e}")
            return {'success': False, 'error': str(e), 'transcription': ''}

    def analyze_image(self, image_data: str, image_type: str = 'base64') -> Dict[str, Any]:
        """Analyze a travel image using GPT-4 Vision to identify destination."""
        try:
            if not self._has_key():
                return {'success': False, 'error': 'OpenAI API key not configured'}

            import openai
            client = openai.OpenAI(api_key=self.api_key)

            if image_type == 'base64':
                img_content = {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}", "detail": "low"}
                }
            else:
                img_content = {
                    "type": "image_url",
                    "image_url": {"url": image_data, "detail": "low"}
                }

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a travel expert. Analyze images to identify destinations. Return JSON only."},
                    {"role": "user", "content": [
                        {"type": "text", "text": """Analyze this travel image. Return JSON (no markdown):
{
    "destination": "City, Country",
    "landmark": "Specific landmark if identifiable",
    "description": "Brief description",
    "confidence": 0.0-1.0,
    "suggested_trip": {
        "duration_days": number,
        "best_season": "spring/summer/fall/winter",
        "budget_estimate": "$X-$Y per person",
        "must_see": ["attraction1", "attraction2", "attraction3"],
        "cuisine_to_try": ["dish1", "dish2"],
        "travel_tip": "Key tip for visiting"
    }
}"""},
                        img_content
                    ]}
                ],
                max_tokens=500,
                temperature=0.3,
            )

            content = response.choices[0].message.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            result = json.loads(content)
            result['success'] = True
            return result

        except json.JSONDecodeError:
            return {'success': True, 'destination': 'Unknown', 'confidence': 0.0}
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return {'success': False, 'error': str(e)}

    def analyze_screenshot(self, image_data: str) -> Dict[str, Any]:
        """Analyze a screenshot of a flight/hotel deal to extract booking details."""
        try:
            if not self._has_key():
                return {'success': False, 'error': 'OpenAI API key not configured'}

            import openai
            client = openai.OpenAI(api_key=self.api_key)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract travel deal info from screenshots. Return JSON only."},
                    {"role": "user", "content": [
                        {"type": "text", "text": """Extract deal info. Return JSON (no markdown):
{
    "deal_type": "flight/hotel/package/other",
    "origin": "airport or city",
    "destination": "airport or city",
    "dates": {"departure": "YYYY-MM-DD or desc", "return": "YYYY-MM-DD or desc"},
    "price": {"amount": number, "currency": "USD", "original_price": null},
    "airline_or_hotel": "name",
    "class_or_room_type": "economy/business/etc",
    "details": "additional details",
    "is_deal": true/false,
    "savings_percent": null
}"""},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}", "detail": "high"}}
                    ]}
                ],
                max_tokens=500,
                temperature=0.1,
            )

            content = response.choices[0].message.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            result = json.loads(content)
            result['success'] = True
            return result

        except Exception as e:
            logger.error(f"Screenshot analysis failed: {e}")
            return {'success': False, 'error': str(e)}

    def _extract_travel_intent(self, text: str) -> Dict[str, Any]:
        """Extract structured travel intent from transcribed text."""
        try:
            if not self._has_key():
                return {'raw_text': text, 'parsed': False}

            import openai
            client = openai.OpenAI(api_key=self.api_key)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract travel intent from speech. Return JSON only."},
                    {"role": "user", "content": f"""Extract travel intent from: "{text}"
Return JSON (no markdown):
{{
    "intent": "plan_trip/search_flights/search_hotels/general_question",
    "destination": "destination or null",
    "origin": "origin or null",
    "dates": {{"start": "YYYY-MM-DD or null", "end": "YYYY-MM-DD or null"}},
    "travelers": null,
    "budget": null,
    "preferences": [],
    "summary": "one-sentence summary"
}}"""}
                ],
                max_tokens=300,
                temperature=0.1,
            )

            content = response.choices[0].message.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            result = json.loads(content)
            result['parsed'] = True
            result['raw_text'] = text
            return result

        except Exception as e:
            logger.warning(f"Intent extraction failed: {e}")
            return {'raw_text': text, 'parsed': False}
