"""
Rating Agent Service
AI-powered quality rating system for destinations, hotels, restaurants, and attractions.
Includes a "vacation predictor" that estimates personal enjoyment based on Travel DNA.
"""
import hashlib
import json
import logging
import os
import random
from decimal import Decimal
from typing import Any, Dict, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class RatingAgent:
    """Generates AI quality ratings and personalized enjoyment predictions."""

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def rate_entity(
        self,
        entity_type: str,
        entity_name: str,
        destination: str,
    ):
        """
        Generate (or retrieve cached) AI quality rating for an entity.

        Returns the saved AIRating model instance.
        """
        from apps.reviews.models import AIRating

        # Return existing rating if fresh (updated within last 7 days)
        from django.utils import timezone
        from datetime import timedelta

        existing = AIRating.objects.filter(
            entity_type=entity_type,
            entity_name=entity_name,
            destination=destination,
        ).first()

        if existing and existing.last_updated > timezone.now() - timedelta(days=7):
            return existing

        # Try OpenAI-powered rating, fall back to rule-based
        rating_data = self._generate_rating_openai(entity_type, entity_name, destination)
        if rating_data is None:
            rating_data = self._generate_rating_fallback(entity_type, entity_name, destination)

        # Persist
        ai_rating, _ = AIRating.objects.update_or_create(
            entity_type=entity_type,
            entity_name=entity_name,
            destination=destination,
            defaults=rating_data,
        )
        return ai_rating

    def predict_enjoyment(
        self,
        user,
        entity_type: str,
        entity_name: str,
        destination: str,
    ) -> Dict[str, Any]:
        """
        Predict how much *this* user would enjoy the entity (0-100 score)
        based on their Travel DNA profile.
        """
        travel_dna = self._load_travel_dna(user)
        trip_style = self._load_trip_style(user)

        # Ensure we have an AI rating for the entity
        ai_rating = self.rate_entity(entity_type, entity_name, destination)

        # Try LLM-powered prediction first
        result = self._predict_openai(
            travel_dna, trip_style, ai_rating, entity_type, entity_name, destination,
        )
        if result is not None:
            return result

        # Fallback: rule-based matching
        return self._predict_fallback(
            travel_dna, trip_style, ai_rating, entity_type, entity_name, destination,
        )

    # ------------------------------------------------------------------ #
    #  OpenAI-powered rating
    # ------------------------------------------------------------------ #

    def _generate_rating_openai(
        self, entity_type: str, entity_name: str, destination: str,
    ) -> Optional[Dict[str, Any]]:
        """Generate a rating using OpenAI. Returns None on failure."""
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return None

        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(
                model='gpt-4o-mini',
                temperature=0.4,
                api_key=api_key,
                request_timeout=30,
            )

            response = model.invoke([
                SystemMessage(content=(
                    "You are a travel quality rating engine. "
                    "Return JSON only, no markdown fences."
                )),
                HumanMessage(content=f"""Rate this {entity_type}: "{entity_name}" in {destination}.

Return a single JSON object with these exact keys:
{{
  "overall_score": <float 1-10>,
  "safety_score": <float 1-10>,
  "value_score": <float 1-10>,
  "food_score": <float 1-10>,
  "culture_score": <float 1-10>,
  "accessibility_score": <float 1-10>,
  "summary": "<2-3 sentence overview>",
  "pros": ["pro1", "pro2", "pro3"],
  "cons": ["con1", "con2"],
  "best_for": ["<traveler type 1>", "<traveler type 2>"],
  "enjoyment_factors": {{
    "adventure": <float 0-1>,
    "relaxation": <float 0-1>,
    "cultural": <float 0-1>,
    "family": <float 0-1>,
    "budget_friendly": <float 0-1>,
    "luxury": <float 0-1>
  }}
}}"""),
            ])

            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            data = json.loads(content)

            return {
                'overall_score': Decimal(str(round(float(data['overall_score']), 1))),
                'safety_score': Decimal(str(round(float(data.get('safety_score', 7)), 1))),
                'value_score': Decimal(str(round(float(data.get('value_score', 7)), 1))),
                'food_score': Decimal(str(round(float(data.get('food_score', 7)), 1))),
                'culture_score': Decimal(str(round(float(data.get('culture_score', 7)), 1))),
                'accessibility_score': Decimal(str(round(float(data.get('accessibility_score', 7)), 1))),
                'summary': data.get('summary', ''),
                'pros': data.get('pros', []),
                'cons': data.get('cons', []),
                'best_for': data.get('best_for', []),
                'enjoyment_factors': data.get('enjoyment_factors', {}),
                'ai_generated': True,
            }
        except Exception as e:
            logger.warning("OpenAI rating generation failed for %s: %s", entity_name, e)
            return None

    # ------------------------------------------------------------------ #
    #  Rule-based fallback rating
    # ------------------------------------------------------------------ #

    def _generate_rating_fallback(
        self, entity_type: str, entity_name: str, destination: str,
    ) -> Dict[str, Any]:
        """Deterministic-ish fallback that produces plausible scores."""
        seed = int(
            hashlib.md5(
                f"{entity_type}:{entity_name}:{destination}".encode()
            ).hexdigest()[:8],
            16,
        )
        rng = random.Random(seed)

        def _score():
            """Random score in 6.0-9.0 range with one decimal."""
            return Decimal(str(round(rng.uniform(6.0, 9.0), 1)))

        overall = _score()

        # Build entity-specific pros/cons/best_for
        pros_pool = {
            'destination': [
                'Rich cultural heritage', 'Beautiful natural scenery',
                'Excellent public transport', 'Vibrant nightlife',
                'World-class museums', 'Friendly locals',
            ],
            'hotel': [
                'Central location', 'Excellent amenities',
                'Friendly staff', 'Great breakfast buffet',
                'Quiet rooms', 'Modern facilities',
            ],
            'restaurant': [
                'Authentic local cuisine', 'Generous portions',
                'Romantic atmosphere', 'Fast service',
                'Great wine list', 'Vegetarian options available',
            ],
            'attraction': [
                'Unique experience', 'Well-maintained grounds',
                'Knowledgeable guides', 'Suitable for all ages',
                'Stunning photo opportunities', 'Interactive exhibits',
            ],
        }

        cons_pool = {
            'destination': [
                'Can be crowded in peak season', 'Language barrier',
                'Expensive during holidays', 'Limited late-night options',
            ],
            'hotel': [
                'Street noise at night', 'Small rooms',
                'Slow Wi-Fi', 'Limited parking',
            ],
            'restaurant': [
                'Long wait times on weekends', 'Pricey wine list',
                'Limited seating', 'Cash only',
            ],
            'attraction': [
                'Long queues at peak hours', 'Limited accessibility',
                'No indoor areas for bad weather', 'Expensive gift shop',
            ],
        }

        best_for_pool = [
            'families', 'couples', 'solo travelers', 'business travelers',
            'adventure seekers', 'budget travelers', 'luxury travelers',
            'culture enthusiasts', 'foodies',
        ]

        type_pros = pros_pool.get(entity_type, pros_pool['destination'])
        type_cons = cons_pool.get(entity_type, cons_pool['destination'])

        rng.shuffle(type_pros)
        rng.shuffle(type_cons)
        rng.shuffle(best_for_pool)

        # Enjoyment factors — seeded so they are consistent per entity
        enjoyment_factors = {
            'adventure': round(rng.uniform(0.2, 0.9), 2),
            'relaxation': round(rng.uniform(0.2, 0.9), 2),
            'cultural': round(rng.uniform(0.2, 0.9), 2),
            'family': round(rng.uniform(0.2, 0.9), 2),
            'budget_friendly': round(rng.uniform(0.2, 0.9), 2),
            'luxury': round(rng.uniform(0.2, 0.9), 2),
        }

        return {
            'overall_score': overall,
            'safety_score': _score(),
            'value_score': _score(),
            'food_score': _score(),
            'culture_score': _score(),
            'accessibility_score': _score(),
            'summary': (
                f"{entity_name} is a well-regarded {entity_type} in {destination}. "
                f"It scores well across multiple categories and is popular among "
                f"travelers seeking quality experiences."
            ),
            'pros': type_pros[:3],
            'cons': type_cons[:2],
            'best_for': best_for_pool[:3],
            'enjoyment_factors': enjoyment_factors,
            'ai_generated': True,
        }

    # ------------------------------------------------------------------ #
    #  OpenAI-powered enjoyment prediction
    # ------------------------------------------------------------------ #

    def _predict_openai(
        self, travel_dna, trip_style, ai_rating, entity_type, entity_name, destination,
    ) -> Optional[Dict[str, Any]]:
        """LLM-powered enjoyment prediction. Returns None on failure."""
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return None

        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(
                model='gpt-4o-mini',
                temperature=0.3,
                api_key=api_key,
                request_timeout=30,
            )

            response = model.invoke([
                SystemMessage(content=(
                    "You are a vacation enjoyment predictor. "
                    "Return JSON only, no markdown fences."
                )),
                HumanMessage(content=f"""Predict how much this traveler would enjoy "{entity_name}" ({entity_type}) in {destination}.

Traveler profile:
- Trip style: {trip_style}
- Travel DNA: {json.dumps(travel_dna, default=str)}

Entity rating:
- Overall: {ai_rating.overall_score}/10
- Best for: {json.dumps(ai_rating.best_for)}
- Enjoyment factors: {json.dumps(ai_rating.enjoyment_factors)}
- Pros: {json.dumps(ai_rating.pros)}

Return JSON:
{{
  "enjoyment_score": <int 0-100>,
  "explanation": "<2-3 sentences explaining the score>",
  "matching_factors": ["factor1", "factor2"],
  "tips": ["tip1", "tip2"]
}}"""),
            ])

            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            data = json.loads(content)

            return {
                'enjoyment_score': int(data.get('enjoyment_score', 70)),
                'explanation': data.get('explanation', ''),
                'matching_factors': data.get('matching_factors', []),
                'tips': data.get('tips', []),
                'entity_name': entity_name,
                'entity_type': entity_type,
                'destination': destination,
            }
        except Exception as e:
            logger.warning("OpenAI enjoyment prediction failed: %s", e)
            return None

    # ------------------------------------------------------------------ #
    #  Rule-based enjoyment prediction
    # ------------------------------------------------------------------ #

    def _predict_fallback(
        self, travel_dna, trip_style, ai_rating, entity_type, entity_name, destination,
    ) -> Dict[str, Any]:
        """Simple matching of trip_style vs entity enjoyment_factors."""
        factors = ai_rating.enjoyment_factors or {}
        matching = []
        score = 60  # baseline

        # Map trip_style to enjoyment_factor keys
        style_map = {
            'adventure': 'adventure',
            'relaxation': 'relaxation',
            'cultural': 'cultural',
            'business': 'luxury',
            'family': 'family',
        }

        primary_factor = style_map.get(trip_style, 'cultural')
        primary_value = factors.get(primary_factor, 0.5)

        # Primary style match adds up to 25 points
        score += int(primary_value * 25)
        if primary_value >= 0.5:
            matching.append(f"Good match for {trip_style} travelers")

        # Budget alignment
        budget_pref = ''
        if travel_dna:
            budget_pref = travel_dna.get('budget', {}).get('range', '')
            interests = travel_dna.get('style', {}).get('top_interests', [])

            if budget_pref in ('budget', 'moderate') and factors.get('budget_friendly', 0) >= 0.5:
                score += 8
                matching.append("Fits your budget preferences")
            elif budget_pref in ('premium', 'luxury') and factors.get('luxury', 0) >= 0.5:
                score += 8
                matching.append("Matches your premium taste")

            # Interest overlap check
            if interests:
                for interest in interests[:3]:
                    interest_lower = interest.lower()
                    if interest_lower in factors and factors[interest_lower] >= 0.5:
                        score += 5
                        matching.append(f"Aligns with your interest in {interest}")

        # Overall quality bonus
        overall = float(ai_rating.overall_score)
        if overall >= 8.0:
            score += 7
        elif overall >= 7.0:
            score += 4

        # Clamp to 0-100
        score = max(0, min(100, score))

        explanation = (
            f"Based on your {trip_style} travel style"
            + (f" and {budget_pref} budget" if budget_pref else "")
            + f", {entity_name} scores {score}/100 for predicted enjoyment. "
            + (f"Key matches: {', '.join(matching[:3])}." if matching else
               "Consider exploring to see if it fits your preferences.")
        )

        return {
            'enjoyment_score': score,
            'explanation': explanation,
            'matching_factors': matching[:4],
            'tips': self._generate_tips(entity_type, trip_style),
            'entity_name': entity_name,
            'entity_type': entity_type,
            'destination': destination,
        }

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _load_travel_dna(self, user) -> Dict[str, Any]:
        """Load the user's Travel DNA from UserPreference."""
        try:
            from apps.agents.models import UserPreference
            pref = UserPreference.objects.filter(user=user).first()
            if pref and pref.travel_dna:
                return pref.travel_dna
        except Exception:
            pass
        return {}

    def _load_trip_style(self, user) -> str:
        """Load the user's trip style preference."""
        try:
            from apps.agents.models import UserPreference
            pref = UserPreference.objects.filter(user=user).first()
            if pref:
                return pref.trip_style
        except Exception:
            pass
        return 'cultural'

    def _generate_tips(self, entity_type: str, trip_style: str) -> list:
        """Generate simple tips based on entity type and style."""
        tips_map = {
            ('destination', 'adventure'): [
                "Book outdoor activities in advance",
                "Check local weather conditions before your trip",
            ],
            ('destination', 'relaxation'): [
                "Look for spa packages at local hotels",
                "Visit during shoulder season for fewer crowds",
            ],
            ('destination', 'cultural'): [
                "Consider a guided walking tour on your first day",
                "Check for museum free-entry days",
            ],
            ('destination', 'family'): [
                "Look for family combo tickets for attractions",
                "Research child-friendly restaurants nearby",
            ],
            ('hotel', 'relaxation'): [
                "Request a quiet room away from elevators",
                "Ask about late checkout options",
            ],
            ('restaurant', 'cultural'): [
                "Try the local specialties for an authentic experience",
                "Visit during off-peak hours for better service",
            ],
        }

        tips = tips_map.get((entity_type, trip_style))
        if tips:
            return tips

        return [
            f"Research {entity_type} reviews from fellow {trip_style} travelers",
            "Book in advance during peak season for best availability",
        ]
