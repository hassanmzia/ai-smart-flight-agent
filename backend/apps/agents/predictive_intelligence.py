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
