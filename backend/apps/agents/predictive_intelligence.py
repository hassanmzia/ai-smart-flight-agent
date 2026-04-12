"""
Predictive Travel Intelligence
- Flight price forecasting based on historical patterns
- Best-time-to-visit predictions (weather, crowds, prices)
- Destination trend analysis
"""
import os
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class PredictiveIntelligence:
    """Price forecasting and travel intelligence predictions."""

    def predict_price_trend(self, origin: str, destination: str,
                            target_date: str, days_ahead: int = 30) -> Dict[str, Any]:
        """
        Predict flight price trends for a route.
        Uses historical price watch data + LLM analysis.
        """
        # Gather historical data from PriceWatch
        history = self._get_price_history(origin, destination)

        # Try LLM first, then statistical fallback
        prediction = self._llm_price_prediction(origin, destination, target_date, days_ahead, history)
        if not prediction or prediction.get('current_estimate') is None:
            stat = self._statistical_prediction(history, days_ahead)
            if stat:
                prediction = stat

        return {
            'success': True,
            'route': f"{origin} → {destination}",
            'target_date': target_date,
            'prediction': prediction,
            'historical_data': history[:30] if history else [],
        }

    def best_time_to_visit(self, destination: str) -> Dict[str, Any]:
        """Predict the best time to visit a destination."""
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return self._fallback_best_time(destination)

        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(model='gpt-4o-mini', temperature=0.3, api_key=api_key, request_timeout=30)

            response = model.invoke([
                SystemMessage(content="You are a travel data analyst. Return JSON only, no markdown."),
                HumanMessage(content=f"""Analyze the best time to visit {destination}. Return JSON:
{{
    "destination": "{destination}",
    "best_months": [
        {{"month": "January", "score": 0-100, "weather": "desc", "crowds": "low/moderate/high", "prices": "low/moderate/high", "events": ["event1"]}}
    ],
    "peak_season": {{"months": ["Jun", "Jul", "Aug"], "reason": "why"}},
    "shoulder_season": {{"months": ["Apr", "May"], "reason": "why"}},
    "off_season": {{"months": ["Nov", "Dec"], "reason": "why"}},
    "overall_recommendation": "2-3 sentence recommendation",
    "budget_tip": "When to go for cheapest flights/hotels",
    "weather_tip": "Best weather window"
}}
Include all 12 months in best_months.""")
            ])

            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            result = json.loads(content)
            result['success'] = True
            return result

        except Exception as e:
            logger.error(f"Best time prediction failed: {e}")
            return self._fallback_best_time(destination)

    def destination_trends(self, limit: int = 10) -> Dict[str, Any]:
        """Analyze trending destinations based on user search patterns."""
        try:
            from apps.analytics.models import UserActivity

            recent = timezone.now() - timedelta(days=30)
            activities = UserActivity.objects.filter(
                action__in=['search_flight', 'search_hotel'],
                timestamp__gte=recent,
            ).values_list('metadata', flat=True)[:500]

            dest_counts = {}
            for meta in activities:
                if isinstance(meta, dict):
                    dest = meta.get('destination', '') or meta.get('location', '')
                    if dest:
                        dest_counts[dest] = dest_counts.get(dest, 0) + 1

            trending = sorted(dest_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

            return {
                'success': True,
                'trending_destinations': [
                    {'destination': d, 'search_count': c, 'rank': i + 1}
                    for i, (d, c) in enumerate(trending)
                ],
                'period': '30 days',
            }
        except Exception as e:
            logger.warning(f"Trend analysis failed: {e}")
            return {'success': True, 'trending_destinations': [], 'period': '30 days'}

    def _get_price_history(self, origin: str, destination: str) -> List[Dict]:
        """Get historical price data from PriceWatch records."""
        try:
            from .models import PriceWatch
            watches = PriceWatch.objects.filter(
                watch_type='flight',
                search_params__origin=origin,
                search_params__destination=destination,
            ).order_by('-updated_at')[:5]

            all_history = []
            for w in watches:
                if w.price_history:
                    all_history.extend(w.price_history)

            all_history.sort(key=lambda x: x.get('date', ''))
            return all_history
        except Exception:
            return []

    def _llm_price_prediction(self, origin, destination, target_date, days_ahead, history):
        """Use LLM to generate price predictions."""
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return self._fallback_prediction(target_date, days_ahead)

        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(model='gpt-4o-mini', temperature=0.2, api_key=api_key, request_timeout=30)

            history_text = json.dumps(history[-20:], default=str) if history else "No historical data available"

            response = model.invoke([
                SystemMessage(content="You are a flight pricing analyst. Return JSON only."),
                HumanMessage(content=f"""Predict flight prices for {origin} to {destination} around {target_date}.
Historical data: {history_text}

Return JSON:
{{
    "current_estimate": number,
    "trend": "rising/falling/stable",
    "confidence": 0.0-1.0,
    "forecast": [
        {{"days_from_now": 7, "estimated_price": number, "range": [low, high]}},
        {{"days_from_now": 14, "estimated_price": number, "range": [low, high]}},
        {{"days_from_now": 21, "estimated_price": number, "range": [low, high]}},
        {{"days_from_now": 30, "estimated_price": number, "range": [low, high]}}
    ],
    "recommendation": "buy_now/wait/monitor",
    "reasoning": "2 sentences explaining the prediction",
    "best_booking_window": "X-Y days before departure"
}}""")
            ])

            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            return json.loads(content)

        except Exception as e:
            logger.warning(f"LLM price prediction failed: {e}")
            return self._fallback_prediction(target_date, days_ahead)

    def _fallback_prediction(self, target_date, days_ahead):
        """Statistical fallback using moving-average when LLM unavailable."""
        return {
            'current_estimate': None,
            'trend': 'unknown',
            'confidence': 0.0,
            'recommendation': 'monitor',
            'reasoning': 'Insufficient data for prediction. Set up a price watch to gather data.',
            'best_booking_window': '21-45 days before departure',
        }

    def _statistical_prediction(self, history, days_ahead):
        """Simple moving-average price prediction from historical data."""
        if not history or len(history) < 3:
            return None

        prices = [h['price'] for h in history if 'price' in h]
        if len(prices) < 3:
            return None

        # 7-point moving average (or less if not enough data)
        window = min(7, len(prices))
        recent_avg = sum(prices[-window:]) / window
        overall_avg = sum(prices) / len(prices)

        # Simple trend: compare recent avg to overall avg
        if recent_avg < overall_avg * 0.97:
            trend = 'falling'
        elif recent_avg > overall_avg * 1.03:
            trend = 'rising'
        else:
            trend = 'stable'

        # Forecast using linear extrapolation
        forecast = []
        if len(prices) >= 2:
            slope = (prices[-1] - prices[0]) / max(len(prices), 1)
            for d in [7, 14, 21, 30]:
                est = recent_avg + slope * (d / 7)
                margin = recent_avg * 0.1
                forecast.append({
                    'days_from_now': d,
                    'estimated_price': round(est, 2),
                    'range': [round(est - margin, 2), round(est + margin, 2)],
                })

        return {
            'current_estimate': round(recent_avg, 2),
            'trend': trend,
            'confidence': min(0.3 + len(prices) * 0.02, 0.7),
            'forecast': forecast,
            'recommendation': 'buy_now' if trend == 'rising' else ('wait' if trend == 'falling' else 'monitor'),
            'reasoning': f'Based on {len(prices)} historical data points. Recent average ${recent_avg:.0f} vs overall ${overall_avg:.0f}.',
            'best_booking_window': '21-45 days before departure',
            'method': 'statistical_moving_average',
        }

    def predict_crowd_levels(self, destination: str, month: str = None) -> Dict[str, Any]:
        """Estimate crowd levels at a destination by month."""
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return self._fallback_crowd(destination)

        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(model='gpt-4o-mini', temperature=0.2, api_key=api_key, request_timeout=30)

            response = model.invoke([
                SystemMessage(content="You are a tourism analytics expert. Return JSON only."),
                HumanMessage(content=f"""Estimate crowd/tourism levels for {destination} throughout the year.
Return JSON:
{{
    "destination": "{destination}",
    "months": [
        {{"month": "January", "crowd_level": "low/moderate/high/very_high", "score": 1-10, "notes": "brief note"}}
    ],
    "peak_periods": ["period1"],
    "best_for_avoiding_crowds": "recommendation",
    "major_events_driving_crowds": ["event1 (month)"]
}}
Include all 12 months.""")
            ])

            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            result = json.loads(content)
            result['success'] = True
            return result

        except Exception as e:
            logger.warning(f"Crowd prediction failed: {e}")
            return self._fallback_crowd(destination)

    def _fallback_crowd(self, destination):
        return {
            'success': True,
            'destination': destination,
            'best_for_avoiding_crowds': f'Visit {destination} during shoulder season for fewer crowds.',
            'months': [],
        }

    def _fallback_best_time(self, destination):
        return {
            'success': True,
            'destination': destination,
            'overall_recommendation': f'Visit {destination} during shoulder season (spring or fall) for best balance of weather, crowds, and prices.',
            'budget_tip': 'Book 6-8 weeks in advance during off-season for cheapest rates.',
            'weather_tip': 'Check the 10-day forecast before packing.',
        }

    def generate_trip_experience(self, destination: str, start_date: str,
                                  end_date: str, travelers: int = 1,
                                  interests: List[str] = None) -> Dict[str, Any]:
        """Generate an immersive trip experience preview with AI."""
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return self._fallback_trip_experience(destination, start_date, end_date, travelers)

        interests_text = ', '.join(interests) if interests else 'general sightseeing'

        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(model='gpt-4o-mini', temperature=0.5, api_key=api_key, request_timeout=45)

            response = model.invoke([
                SystemMessage(content="You are an expert travel experience designer. Return JSON only, no markdown fences. Be vivid, specific, and inspiring."),
                HumanMessage(content=f"""Create an immersive trip experience preview for {travelers} traveler(s) visiting {destination} from {start_date} to {end_date}.
Interests: {interests_text}

Return JSON:
{{
    "destination": "{destination}",
    "tagline": "A short inspiring tagline for the trip (max 10 words)",
    "vibe_emoji": "3-4 emojis that capture the destination vibe",
    "weather_preview": {{
        "summary": "2-sentence weather description for these dates",
        "avg_temp_high_c": number,
        "avg_temp_low_c": number,
        "condition": "sunny/partly_cloudy/rainy/snowy/mild/hot/cold",
        "what_to_wear": "1-sentence packing advice"
    }},
    "crowd_forecast": {{
        "level": "low/moderate/high/very_high",
        "description": "1-sentence crowd description",
        "tip": "1-sentence tip for managing crowds"
    }},
    "daily_budget": {{
        "budget_usd": number,
        "mid_range_usd": number,
        "luxury_usd": number,
        "currency": "local currency name",
        "exchange_note": "brief exchange rate note"
    }},
    "cultural_highlights": [
        {{"title": "name", "description": "1 sentence", "icon": "single emoji"}}
    ],
    "food_scene": {{
        "summary": "2-sentence food scene overview",
        "must_try": [
            {{"dish": "name", "description": "brief desc", "price_range": "$-$$$$"}}
        ],
        "dining_tip": "1-sentence tip"
    }},
    "a_day_in_your_trip": {{
        "morning": "2-sentence vivid morning description",
        "afternoon": "2-sentence vivid afternoon description",
        "evening": "2-sentence vivid evening description"
    }},
    "hidden_gems": [
        {{"name": "place/experience", "why": "1 sentence why it's special", "icon": "single emoji"}}
    ],
    "local_phrases": [
        {{"phrase": "hello in local language", "meaning": "Hello", "pronunciation": "phonetic"}}
    ],
    "packing_essentials": ["item1", "item2", "item3", "item4", "item5"],
    "safety_wellness": {{
        "safety_level": "very_safe/safe/moderate/caution",
        "tips": ["tip1", "tip2"],
        "health_note": "1-sentence health advisory"
    }},
    "trip_score": {{
        "overall": 1-100,
        "adventure": 1-100,
        "relaxation": 1-100,
        "culture": 1-100,
        "food": 1-100,
        "value": 1-100
    }}
}}
Keep cultural_highlights to 4 items, must_try to 4 dishes, hidden_gems to 3 items, local_phrases to 4 phrases. Be specific to {destination}.""")
            ])

            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            result = json.loads(content)
            result['success'] = True
            return result

        except Exception as e:
            logger.error(f"Trip experience generation failed: {e}")
            return self._fallback_trip_experience(destination, start_date, end_date, travelers)

    def _fallback_trip_experience(self, destination: str, start_date: str,
                                   end_date: str, travelers: int) -> Dict[str, Any]:
        """Rich fallback when LLM is unavailable."""
        return {
            'success': True,
            'destination': destination,
            'tagline': f'Discover the magic of {destination}',
            'vibe_emoji': '🌍✨🗺️',
            'weather_preview': {
                'summary': f'Check local forecasts for {destination} closer to your travel dates for the most accurate weather information.',
                'avg_temp_high_c': 25,
                'avg_temp_low_c': 15,
                'condition': 'mild',
                'what_to_wear': 'Pack layers to prepare for varying conditions.',
            },
            'crowd_forecast': {
                'level': 'moderate',
                'description': f'{destination} typically sees moderate tourist traffic during this period.',
                'tip': 'Visit popular attractions early in the morning for a better experience.',
            },
            'daily_budget': {
                'budget_usd': 50,
                'mid_range_usd': 120,
                'luxury_usd': 300,
                'currency': 'Local currency',
                'exchange_note': 'Check current exchange rates before your trip.',
            },
            'cultural_highlights': [
                {'title': 'Local Heritage', 'description': f'Explore the rich cultural heritage of {destination}.', 'icon': '🏛️'},
                {'title': 'Architecture', 'description': 'Admire the stunning local architecture and landmarks.', 'icon': '🏗️'},
                {'title': 'Markets', 'description': 'Wander through vibrant local markets and bazaars.', 'icon': '🛍️'},
                {'title': 'Art Scene', 'description': 'Discover galleries and street art throughout the city.', 'icon': '🎨'},
            ],
            'food_scene': {
                'summary': f'{destination} offers a diverse culinary landscape blending traditional flavors with modern cuisine. Street food and local restaurants provide authentic experiences.',
                'must_try': [
                    {'dish': 'Local Specialty', 'description': 'A beloved traditional dish of the region', 'price_range': '$$'},
                    {'dish': 'Street Food Favorite', 'description': 'Popular quick bites from local vendors', 'price_range': '$'},
                ],
                'dining_tip': 'Ask locals for their favorite spots — the best food is often off the beaten path.',
            },
            'a_day_in_your_trip': {
                'morning': f'Start your day with a local breakfast and a stroll through the historic quarter of {destination}. The morning light reveals the city at its most peaceful.',
                'afternoon': 'Spend the afternoon exploring top attractions and savoring a leisurely lunch at a local favorite. Take time to wander side streets and discover hidden corners.',
                'evening': 'As the sun sets, find a rooftop bar or waterfront restaurant for dinner. End the night soaking in the local nightlife and atmosphere.',
            },
            'hidden_gems': [
                {'name': 'Secret Viewpoint', 'why': 'A lesser-known spot with breathtaking panoramic views.', 'icon': '🌅'},
                {'name': 'Local Neighborhood', 'why': 'An authentic neighborhood away from tourist crowds.', 'icon': '🏘️'},
                {'name': 'Hidden Café', 'why': 'A tucked-away café beloved by locals for decades.', 'icon': '☕'},
            ],
            'local_phrases': [
                {'phrase': 'Hello', 'meaning': 'Greeting', 'pronunciation': 'Check local language guide'},
                {'phrase': 'Thank you', 'meaning': 'Gratitude', 'pronunciation': 'Check local language guide'},
                {'phrase': 'Please', 'meaning': 'Polite request', 'pronunciation': 'Check local language guide'},
                {'phrase': 'Goodbye', 'meaning': 'Farewell', 'pronunciation': 'Check local language guide'},
            ],
            'packing_essentials': [
                'Comfortable walking shoes',
                'Universal power adapter',
                'Sunscreen and sunglasses',
                'Reusable water bottle',
                'Light rain jacket',
            ],
            'safety_wellness': {
                'safety_level': 'safe',
                'tips': [
                    'Keep valuables secure and be aware of your surroundings in crowded areas.',
                    'Save emergency numbers and your embassy contact in your phone.',
                ],
                'health_note': 'Carry basic medications and check if any vaccinations are recommended.',
            },
            'trip_score': {
                'overall': 78,
                'adventure': 70,
                'relaxation': 75,
                'culture': 80,
                'food': 82,
                'value': 76,
            },
        }
