"""
Memory & Learning Service
Records trip memories, generates AI insights, and provides
proactive suggestions based on a user's travel history.
"""
import logging
import os
from collections import Counter
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db.models import Avg, Count, Q, Sum

logger = logging.getLogger(__name__)

# Deterministic fallback mapping for destination similarity
SIMILAR_DESTINATIONS = {
    'Paris': ['Rome', 'Barcelona', 'Vienna', 'Prague'],
    'Tokyo': ['Seoul', 'Osaka', 'Taipei', 'Singapore'],
    'New York': ['Chicago', 'London', 'Toronto', 'San Francisco'],
    'Bali': ['Phuket', 'Maldives', 'Sri Lanka', 'Fiji'],
    'London': ['Edinburgh', 'Amsterdam', 'Dublin', 'Brussels'],
    'Rome': ['Florence', 'Athens', 'Lisbon', 'Naples'],
    'Bangkok': ['Ho Chi Minh City', 'Kuala Lumpur', 'Jakarta', 'Manila'],
    'Dubai': ['Abu Dhabi', 'Doha', 'Muscat', 'Riyadh'],
    'Sydney': ['Melbourne', 'Auckland', 'Cape Town', 'Honolulu'],
    'Barcelona': ['Valencia', 'Seville', 'Nice', 'Marseille'],
}


class MemoryService:
    """Manages long-term trip memories and learning."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_trip(
        self,
        user,
        destination: str,
        trip_date=None,
        sentiment: str = 'neutral',
        highlights: Optional[List[str]] = None,
        lowlights: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        budget_spent=None,
        rating: int = 0,
        notes: str = '',
    ) -> Dict[str, Any]:
        """Save a TripMemory and trigger AI insight generation."""
        from ..models import TripMemory

        memory = TripMemory.objects.create(
            user=user,
            destination=destination,
            trip_date=trip_date,
            sentiment=sentiment,
            highlights=highlights or [],
            lowlights=lowlights or [],
            tags=tags or [],
            budget_spent=Decimal(str(budget_spent)) if budget_spent is not None else None,
            rating=rating,
            notes=notes,
        )

        # Generate AI insights asynchronously (best-effort)
        try:
            insights = self._generate_trip_insights(memory)
            if insights:
                memory.ai_insights = insights
                memory.save(update_fields=['ai_insights', 'updated_at'])
        except Exception as exc:
            logger.warning("AI insight generation failed for memory %s: %s", memory.id, exc)

        return self._serialize_memory(memory)

    def get_trip_history(self, user) -> List[Dict[str, Any]]:
        """Return all TripMemory records for a user, serialized."""
        from ..models import TripMemory

        memories = TripMemory.objects.filter(user=user)
        return [self._serialize_memory(m) for m in memories]

    def generate_insights(self, user) -> Dict[str, Any]:
        """
        Analyze all trip memories to produce high-level travel insights.

        Returns dict with keys:
            travel_personality, favorite_destinations, preferred_styles,
            budget_pattern, seasonal_preferences, growth_areas
        """
        from ..models import TripMemory

        memories = TripMemory.objects.filter(user=user)
        if not memories.exists():
            return {
                'travel_personality': 'New Explorer',
                'favorite_destinations': [],
                'preferred_styles': [],
                'budget_pattern': 'unknown',
                'seasonal_preferences': [],
                'growth_areas': [],
            }

        # Try OpenAI first
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if api_key and api_key not in ('your_openai_api_key_here', ''):
            try:
                return self._generate_insights_llm(memories, api_key)
            except Exception as exc:
                logger.warning("LLM insights failed, falling back to rules: %s", exc)

        # Fallback: rule-based analysis
        return self._generate_insights_rules(memories)

    def get_proactive_suggestions(self, user) -> List[Dict[str, Any]]:
        """
        Based on trip memories and preferences, suggest next destinations.
        Returns list of {destination, reason, match_score, based_on}.
        """
        from ..models import TripMemory

        memories = TripMemory.objects.filter(user=user)
        if not memories.exists():
            return self._default_suggestions()

        visited = set(memories.values_list('destination', flat=True))
        loved = list(
            memories.filter(sentiment__in=['loved', 'liked'])
            .order_by('-rating')
            .values_list('destination', flat=True)[:10]
        )

        # Try OpenAI
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if api_key and api_key not in ('your_openai_api_key_here', ''):
            try:
                return self._suggest_llm(loved, visited, api_key)
            except Exception as exc:
                logger.warning("LLM suggestions failed, falling back to rules: %s", exc)

        # Deterministic fallback
        return self._suggest_rules(loved, visited)

    def get_feedback_summary(self, user) -> Dict[str, Any]:
        """Aggregated stats about a user's travel feedback."""
        from ..models import TripMemory

        memories = TripMemory.objects.filter(user=user)
        total = memories.count()
        if total == 0:
            return {
                'total_trips': 0,
                'avg_rating': 0,
                'top_sentiments': [],
                'most_visited': [],
                'favorite_tags': [],
                'spending_trend': [],
            }

        avg_rating = memories.aggregate(avg=Avg('rating'))['avg'] or 0

        # Top sentiments
        sentiment_counts = (
            memories.values('sentiment')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        top_sentiments = [
            {'sentiment': s['sentiment'], 'count': s['count']}
            for s in sentiment_counts
        ]

        # Most visited
        dest_counts = (
            memories.values('destination')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        most_visited = [
            {'destination': d['destination'], 'count': d['count']}
            for d in dest_counts
        ]

        # Favorite tags
        all_tags: list = []
        for tags in memories.values_list('tags', flat=True):
            if isinstance(tags, list):
                all_tags.extend(tags)
        tag_counter = Counter(all_tags)
        favorite_tags = [
            {'tag': tag, 'count': cnt}
            for tag, cnt in tag_counter.most_common(10)
        ]

        # Spending trend (chronological)
        spending_qs = (
            memories.filter(budget_spent__isnull=False)
            .order_by('trip_date')
            .values_list('destination', 'trip_date', 'budget_spent')
        )
        spending_trend = [
            {
                'destination': dest,
                'date': str(dt) if dt else None,
                'amount': float(amt),
            }
            for dest, dt, amt in spending_qs
        ]

        return {
            'total_trips': total,
            'avg_rating': round(float(avg_rating), 2),
            'top_sentiments': top_sentiments,
            'most_visited': most_visited,
            'favorite_tags': favorite_tags,
            'spending_trend': spending_trend,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _serialize_memory(self, memory) -> Dict[str, Any]:
        return {
            'id': memory.id,
            'destination': memory.destination,
            'trip_date': str(memory.trip_date) if memory.trip_date else None,
            'sentiment': memory.sentiment,
            'highlights': memory.highlights,
            'lowlights': memory.lowlights,
            'tags': memory.tags,
            'budget_spent': float(memory.budget_spent) if memory.budget_spent is not None else None,
            'travel_style_used': memory.travel_style_used,
            'notes': memory.notes,
            'rating': memory.rating,
            'ai_insights': memory.ai_insights,
            'created_at': memory.created_at.isoformat() if memory.created_at else None,
            'updated_at': memory.updated_at.isoformat() if memory.updated_at else None,
        }

    # ------------------------------------------------------------------
    # AI insight generation for a single trip
    # ------------------------------------------------------------------

    def _generate_trip_insights(self, memory) -> Optional[Dict[str, Any]]:
        """Generate AI insights for a single trip memory."""
        import json

        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return None

        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(
                model='gpt-4o-mini', temperature=0.5,
                api_key=api_key, request_timeout=20,
            )
            response = model.invoke([
                SystemMessage(content="You are a travel analyst. Return JSON only, no markdown."),
                HumanMessage(content=(
                    f"Analyze this trip memory and give brief insights.\n"
                    f"Destination: {memory.destination}\n"
                    f"Sentiment: {memory.sentiment}\n"
                    f"Highlights: {memory.highlights}\n"
                    f"Lowlights: {memory.lowlights}\n"
                    f"Tags: {memory.tags}\n"
                    f"Rating: {memory.rating}/5\n"
                    f"Notes: {memory.notes}\n\n"
                    f"Return JSON: {{\"summary\": \"...\", \"personality_trait\": \"...\", "
                    f"\"next_time_tip\": \"...\"}}"
                )),
            ])
            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            return json.loads(content)
        except Exception as exc:
            logger.warning("Trip insight generation failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # LLM-powered insights
    # ------------------------------------------------------------------

    def _generate_insights_llm(self, memories, api_key: str) -> Dict[str, Any]:
        import json
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage, SystemMessage

        summaries = []
        for m in memories[:30]:
            summaries.append(
                f"- {m.destination} ({m.sentiment}, {m.rating}/5): "
                f"highlights={m.highlights}, tags={m.tags}"
            )

        model = ChatOpenAI(
            model='gpt-4o-mini', temperature=0.5,
            api_key=api_key, request_timeout=30,
        )
        summaries_text = '\n'.join(summaries)
        prompt = (
            f"Analyze these trip memories and produce insights:\n"
            f"{summaries_text}\n\n"
            f"Return JSON: {{"
            f"\"travel_personality\": \"short label\", "
            f"\"favorite_destinations\": [\"...\"], "
            f"\"preferred_styles\": [\"...\"], "
            f"\"budget_pattern\": \"...\", "
            f"\"seasonal_preferences\": [\"...\"], "
            f"\"growth_areas\": [\"...\"]}}"
        )
        response = model.invoke([
            SystemMessage(content="You are a travel analyst. Return JSON only, no markdown."),
            HumanMessage(content=prompt),
        ])
        content = response.content.strip()
        if content.startswith('```'):
            content = content.split('\n', 1)[1].rsplit('```', 1)[0]
        result = json.loads(content)
        # Ensure all expected keys exist
        for key in ('travel_personality', 'favorite_destinations', 'preferred_styles',
                     'budget_pattern', 'seasonal_preferences', 'growth_areas'):
            result.setdefault(key, [] if key != 'travel_personality' and key != 'budget_pattern' else '')
        return result

    def _generate_insights_rules(self, memories) -> Dict[str, Any]:
        """Rule-based travel insight generation."""
        dest_counter = Counter(memories.values_list('destination', flat=True))
        tag_counter: Counter = Counter()
        sentiments = Counter()
        budgets: list = []
        months: Counter = Counter()

        for m in memories:
            sentiments[m.sentiment] += 1
            if isinstance(m.tags, list):
                tag_counter.update(m.tags)
            if m.budget_spent is not None:
                budgets.append(float(m.budget_spent))
            if m.trip_date:
                months[m.trip_date.strftime('%B')] += 1

        # Travel personality
        top_sentiment = sentiments.most_common(1)[0][0] if sentiments else 'neutral'
        personality_map = {
            'loved': 'Passionate Explorer',
            'liked': 'Enthusiastic Traveler',
            'neutral': 'Curious Wanderer',
            'disliked': 'Selective Adventurer',
        }
        travel_personality = personality_map.get(top_sentiment, 'Curious Wanderer')

        # Budget pattern
        if budgets:
            avg_budget = sum(budgets) / len(budgets)
            if avg_budget < 500:
                budget_pattern = 'budget-conscious'
            elif avg_budget < 1500:
                budget_pattern = 'moderate spender'
            elif avg_budget < 3000:
                budget_pattern = 'comfort traveler'
            else:
                budget_pattern = 'luxury traveler'
        else:
            budget_pattern = 'unknown'

        # Seasonal preferences
        seasonal_preferences = [m for m, _ in months.most_common(3)]

        # Growth areas (tags they haven't explored much)
        all_possible = {'beach', 'food', 'history', 'adventure', 'culture', 'nature', 'nightlife', 'shopping'}
        explored = set(tag_counter.keys())
        growth_areas = list(all_possible - explored)[:3]

        return {
            'travel_personality': travel_personality,
            'favorite_destinations': [d for d, _ in dest_counter.most_common(5)],
            'preferred_styles': [t for t, _ in tag_counter.most_common(5)],
            'budget_pattern': budget_pattern,
            'seasonal_preferences': seasonal_preferences,
            'growth_areas': growth_areas,
        }

    # ------------------------------------------------------------------
    # Proactive suggestions
    # ------------------------------------------------------------------

    def _suggest_llm(self, loved: List[str], visited: set, api_key: str) -> List[Dict[str, Any]]:
        import json
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage, SystemMessage

        model = ChatOpenAI(
            model='gpt-4o-mini', temperature=0.7,
            api_key=api_key, request_timeout=25,
        )
        response = model.invoke([
            SystemMessage(content="You are a travel recommendation engine. Return JSON only, no markdown."),
            HumanMessage(content=(
                f"A traveler loved these destinations: {', '.join(loved)}.\n"
                f"They have already visited: {', '.join(visited)}.\n\n"
                f"Suggest 5 NEW destinations they haven't visited. "
                f"Return JSON array: ["
                f"{{\"destination\": \"...\", \"reason\": \"you loved X, try Y because...\", "
                f"\"match_score\": 70-99, \"based_on\": \"which loved destination inspired this\"}}]"
            )),
        ])
        content = response.content.strip()
        if content.startswith('```'):
            content = content.split('\n', 1)[1].rsplit('```', 1)[0]
        suggestions = json.loads(content)
        if isinstance(suggestions, list):
            return suggestions[:5]
        return self._suggest_rules(loved, visited)

    def _suggest_rules(self, loved: List[str], visited: set) -> List[Dict[str, Any]]:
        """Deterministic fallback using the similarity mapping."""
        suggestions: List[Dict[str, Any]] = []
        seen: set = set()

        for dest in loved:
            similar = SIMILAR_DESTINATIONS.get(dest, [])
            for sim in similar:
                if sim not in visited and sim not in seen:
                    suggestions.append({
                        'destination': sim,
                        'reason': f"You loved {dest} — try {sim} for a similar vibe.",
                        'match_score': max(70, 95 - len(suggestions) * 3),
                        'based_on': dest,
                    })
                    seen.add(sim)
                    if len(suggestions) >= 5:
                        return suggestions

        # If we still need more, fill from all values
        if len(suggestions) < 5:
            for dests in SIMILAR_DESTINATIONS.values():
                for d in dests:
                    if d not in visited and d not in seen:
                        suggestions.append({
                            'destination': d,
                            'reason': f"Popular destination you haven't explored yet.",
                            'match_score': 70,
                            'based_on': 'general',
                        })
                        seen.add(d)
                        if len(suggestions) >= 5:
                            return suggestions

        return suggestions

    def _default_suggestions(self) -> List[Dict[str, Any]]:
        """Default suggestions for users with no trip history."""
        return [
            {
                'destination': 'Paris',
                'reason': 'A classic first destination with world-class culture and cuisine.',
                'match_score': 90,
                'based_on': 'popular',
            },
            {
                'destination': 'Tokyo',
                'reason': 'A vibrant blend of tradition and modernity.',
                'match_score': 88,
                'based_on': 'popular',
            },
            {
                'destination': 'Barcelona',
                'reason': 'Beautiful architecture, beaches, and incredible food scene.',
                'match_score': 85,
                'based_on': 'popular',
            },
            {
                'destination': 'Bali',
                'reason': 'Affordable paradise with stunning temples and nature.',
                'match_score': 83,
                'based_on': 'popular',
            },
            {
                'destination': 'New York',
                'reason': 'The city that never sleeps — endless things to see and do.',
                'match_score': 80,
                'based_on': 'popular',
            },
        ]
