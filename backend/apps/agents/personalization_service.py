"""
Personalization Service
Learns from user behavior to build a "Travel DNA" profile and
serve personalized recommendations.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Avg, Q

logger = logging.getLogger(__name__)


class PersonalizationService:
    """Builds and uses personalized travel profiles."""

    def build_travel_dna(self, user) -> Dict[str, Any]:
        """
        Analyze user's booking history, searches, and feedback to build
        a comprehensive Travel DNA profile (v2 — includes dietary, faith,
        health, pace, and language dimensions).
        """
        dna = {
            'destinations': self._analyze_destinations(user),
            'budget': self._analyze_budget(user),
            'style': self._analyze_style(user),
            'timing': self._analyze_timing(user),
            'preferences': self._analyze_preferences(user),
            'dietary': self._analyze_dietary(user),
            'faith': self._analyze_faith(user),
            'health': self._analyze_health(user),
            'pace': self._analyze_pace(user),
            'languages': self._analyze_languages(user),
        }

        # Save to UserPreference
        self._save_dna(user, dna)

        return dna

    def get_recommendations(self, user, limit: int = 5) -> Dict[str, Any]:
        """Get personalized trip recommendations based on Travel DNA."""
        dna = self._load_dna(user)
        if not dna:
            dna = self.build_travel_dna(user)

        recommendations = self._generate_recommendations(user, dna, limit)
        return {
            'success': True,
            'travel_dna': dna,
            'recommendations': recommendations,
        }

    def _analyze_destinations(self, user) -> Dict[str, Any]:
        """Analyze destination preferences."""
        try:
            from apps.bookings.models import Booking
            bookings = Booking.objects.filter(user=user, status__in=['confirmed', 'completed'])

            destinations = {}
            for b in bookings:
                for item in b.items.all():
                    dest = item.item_name or ''
                    if dest:
                        destinations[dest] = destinations.get(dest, 0) + 1

            top = sorted(destinations.items(), key=lambda x: x[1], reverse=True)[:5]
            return {
                'favorite_destinations': [d[0] for d in top],
                'total_destinations': len(destinations),
                'repeat_visitor': any(c > 1 for _, c in destinations.items()),
            }
        except Exception:
            return {'favorite_destinations': [], 'total_destinations': 0}

    def _analyze_budget(self, user) -> Dict[str, Any]:
        """Analyze spending patterns."""
        try:
            from apps.bookings.models import Booking
            bookings = Booking.objects.filter(user=user, status__in=['confirmed', 'completed'])

            amounts = [float(b.total_amount) for b in bookings if b.total_amount]
            if not amounts:
                return {'range': 'unknown', 'average': 0}

            avg = sum(amounts) / len(amounts)
            if avg < 500:
                range_label = 'budget'
            elif avg < 1500:
                range_label = 'moderate'
            elif avg < 3000:
                range_label = 'premium'
            else:
                range_label = 'luxury'

            return {
                'range': range_label,
                'average_spend': round(avg, 2),
                'total_spend': round(sum(amounts), 2),
                'booking_count': len(amounts),
            }
        except Exception:
            return {'range': 'unknown', 'average': 0}

    def _analyze_style(self, user) -> Dict[str, Any]:
        """Infer travel style from behavior."""
        try:
            from apps.itineraries.models import Itinerary, TripFeedback

            itineraries = Itinerary.objects.filter(user=user)
            feedbacks = TripFeedback.objects.filter(user=user)

            avg_duration = 0
            if itineraries.exists():
                durations = []
                for it in itineraries:
                    if it.start_date and it.end_date:
                        d = (it.end_date - it.start_date).days
                        if d > 0:
                            durations.append(d)
                if durations:
                    avg_duration = sum(durations) / len(durations)

            # Analyze feedback tags
            tags = {}
            for fb in feedbacks:
                if fb.tags:
                    for tag in fb.tags:
                        tags[tag] = tags.get(tag, 0) + 1

            top_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)[:5]

            style = 'balanced'
            if avg_duration <= 3:
                style = 'weekend_warrior'
            elif avg_duration <= 7:
                style = 'week_tripper'
            elif avg_duration > 14:
                style = 'extended_traveler'

            return {
                'style': style,
                'avg_trip_duration': round(avg_duration, 1),
                'top_interests': [t[0] for t in top_tags],
            }
        except Exception:
            return {'style': 'balanced', 'avg_trip_duration': 0}

    def _analyze_timing(self, user) -> Dict[str, Any]:
        """Analyze booking timing patterns."""
        try:
            from apps.bookings.models import Booking

            bookings = Booking.objects.filter(user=user).order_by('-booking_date')[:20]
            advance_days = []
            months = {}

            for b in bookings:
                if b.booking_date:
                    month = b.booking_date.strftime('%B')
                    months[month] = months.get(month, 0) + 1

            preferred_months = sorted(months.items(), key=lambda x: x[1], reverse=True)[:3]

            return {
                'preferred_booking_months': [m[0] for m in preferred_months],
                'avg_advance_days': round(sum(advance_days) / len(advance_days)) if advance_days else 14,
                'is_last_minute': (sum(advance_days) / len(advance_days)) < 7 if advance_days else False,
            }
        except Exception:
            return {'preferred_booking_months': [], 'avg_advance_days': 14}

    def _analyze_preferences(self, user) -> Dict[str, Any]:
        """Compile explicit preferences."""
        try:
            from .models import UserPreference
            pref = UserPreference.objects.filter(user=user).first()
            if pref:
                return {
                    'preferred_airlines': pref.preferred_airlines or [],
                    'preferred_hotel_chains': pref.preferred_hotel_chains or [],
                    'preferred_cuisines': pref.preferred_cuisines or [],
                    'budget_range': pref.budget_range,
                    'trip_style': pref.trip_style,
                }
        except Exception:
            pass
        return {}

    # ------------------------------------------------------------------
    # Travel DNA v2 analysis methods
    # ------------------------------------------------------------------

    def _analyze_dietary(self, user) -> Dict[str, Any]:
        """Analyze dietary preferences and restrictions."""
        try:
            from .models import UserPreference
            pref = UserPreference.objects.filter(user=user).first()
            if pref:
                return {
                    'preference': pref.dietary_preference,
                    'allergies': pref.dietary_allergies or [],
                    'preferred_cuisines': pref.preferred_cuisines or [],
                }
        except Exception:
            pass
        return {'preference': 'none', 'allergies': [], 'preferred_cuisines': []}

    def _analyze_faith(self, user) -> Dict[str, Any]:
        """Analyze faith-related travel preferences."""
        try:
            from .models import UserPreference
            pref = UserPreference.objects.filter(user=user).first()
            if pref:
                return {
                    'faith': pref.faith,
                    'prayer_reminders': pref.prayer_reminders,
                    'faith_site_interest': pref.faith_site_interest,
                }
        except Exception:
            pass
        return {'faith': 'none', 'prayer_reminders': False, 'faith_site_interest': False}

    def _analyze_health(self, user) -> Dict[str, Any]:
        """Analyze health and mobility preferences."""
        try:
            from .models import UserPreference
            pref = UserPreference.objects.filter(user=user).first()
            if pref:
                return {
                    'mobility': pref.mobility,
                    'max_walking_km': float(pref.max_walking_km_per_day),
                    'health_conditions': pref.health_conditions or [],
                    'medications': pref.medications or [],
                }
        except Exception:
            pass
        return {'mobility': 'full', 'max_walking_km': 10.0, 'health_conditions': [], 'medications': []}

    def _analyze_pace(self, user) -> Dict[str, Any]:
        """Analyze pace and activity density preferences."""
        try:
            from .models import UserPreference
            pref = UserPreference.objects.filter(user=user).first()
            if pref:
                return {
                    'pace': pref.pace,
                    'max_activities_per_day': pref.max_activities_per_day,
                }
        except Exception:
            pass
        return {'pace': 'moderate', 'max_activities_per_day': 5}

    def _analyze_languages(self, user) -> Dict[str, Any]:
        """Analyze language proficiency."""
        try:
            from .models import UserPreference
            pref = UserPreference.objects.filter(user=user).first()
            if pref and pref.languages_spoken:
                return {'spoken': pref.languages_spoken}
        except Exception:
            pass
        return {'spoken': ['en']}

    def _generate_recommendations(self, user, dna, limit):
        """Generate personalized recommendations using LLM + behavioral data."""
        import os, json

        fav_dests = dna.get('destinations', {}).get('favorite_destinations', [])
        budget_range = dna.get('budget', {}).get('range', 'moderate')
        style = dna.get('style', {}).get('style', 'balanced')
        interests = dna.get('style', {}).get('top_interests', [])
        avg_duration = dna.get('style', {}).get('avg_trip_duration', 5)
        avg_spend = dna.get('budget', {}).get('average_spend', 0)

        # Gather behavioral signals from recent searches
        search_history = self._get_search_behavior(user)

        # Try LLM-powered recommendations
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if api_key and api_key not in ('your_openai_api_key_here', ''):
            try:
                from langchain_openai import ChatOpenAI
                from langchain.schema import HumanMessage, SystemMessage

                model = ChatOpenAI(
                    model='gpt-4o-mini', temperature=0.7,
                    api_key=api_key, request_timeout=30,
                )

                # Gather v2 DNA dimensions
                dietary = dna.get('dietary', {})
                faith_info = dna.get('faith', {})
                health_info = dna.get('health', {})
                pace_info = dna.get('pace', {})
                langs = dna.get('languages', {}).get('spoken', ['en'])

                response = model.invoke([
                    SystemMessage(content="You are a travel recommendation engine. Return JSON only, no markdown."),
                    HumanMessage(content=f"""Generate {limit} personalized trip recommendations for a traveler with this profile:
- Budget range: {budget_range} (avg spend: ${avg_spend:.0f})
- Travel style: {style}
- Interests: {', '.join(interests) if interests else 'general sightseeing'}
- Avg trip duration: {avg_duration} days
- Past destinations: {', '.join(fav_dests[:5]) if fav_dests else 'none yet'}
- Recent searches: {json.dumps(search_history[:5], default=str) if search_history else 'none'}
- Dietary: {dietary.get('preference', 'none')}, allergies: {dietary.get('allergies', [])}
- Faith: {faith_info.get('faith', 'none')}, wants faith sites: {faith_info.get('faith_site_interest', False)}
- Mobility: {health_info.get('mobility', 'full')}, max walking: {health_info.get('max_walking_km', 10)} km/day
- Pace: {pace_info.get('pace', 'moderate')}, max {pace_info.get('max_activities_per_day', 5)} activities/day
- Languages spoken: {', '.join(langs)}

Return JSON array:
[{{"title": "Trip title", "destination": "City, Country", "reason": "Why this matches their profile", "match_score": 70-99, "based_on": "Which profile traits drove this"}}]

Factor in dietary/faith/mobility needs when scoring destinations. Avoid recommending places they have already visited. Vary destinations across regions. Score higher for closer matches to their interests, budget, and accessibility needs.""")
                ])

                content = response.content.strip()
                if content.startswith('```'):
                    content = content.split('\n', 1)[1].rsplit('```', 1)[0]
                recs = json.loads(content)
                if isinstance(recs, list):
                    return recs[:limit]
            except Exception as e:
                logger.warning(f"LLM recommendations failed: {e}")

        # Fallback: rule-based recommendations with computed scores
        suggestions = {
            'budget': [
                {'title': 'Budget-Friendly Southeast Asia', 'destination': 'Bangkok, Thailand', 'reason': 'Great value for budget travelers'},
                {'title': 'Affordable European City Break', 'destination': 'Prague, Czech Republic', 'reason': 'Cheap flights and affordable hotels'},
                {'title': 'Budget Beach Getaway', 'destination': 'Bali, Indonesia', 'reason': 'Affordable luxury in paradise'},
            ],
            'moderate': [
                {'title': 'Mediterranean Escape', 'destination': 'Barcelona, Spain', 'reason': 'Perfect mid-range destination'},
                {'title': 'Japanese Culture Trip', 'destination': 'Tokyo, Japan', 'reason': 'Excellent public transport, diverse budget options'},
                {'title': 'Greek Island Hopping', 'destination': 'Santorini, Greece', 'reason': 'Stunning views, good value shoulder season'},
            ],
            'premium': [
                {'title': 'Swiss Alps Adventure', 'destination': 'Interlaken, Switzerland', 'reason': 'Premium outdoor experiences'},
                {'title': 'Northern Lights Experience', 'destination': 'Reykjavik, Iceland', 'reason': 'Once-in-a-lifetime natural wonder'},
                {'title': 'Safari Experience', 'destination': 'Nairobi, Kenya', 'reason': 'Unforgettable wildlife encounters'},
            ],
            'luxury': [
                {'title': 'Maldives Overwater Villa', 'destination': 'Maldives', 'reason': 'Ultimate luxury escape'},
                {'title': 'French Riviera Retreat', 'destination': 'Nice, France', 'reason': 'World-class dining and beaches'},
                {'title': 'Dubai Luxury Experience', 'destination': 'Dubai, UAE', 'reason': 'Ultra-luxury hotels and shopping'},
            ],
        }

        recs = suggestions.get(budget_range, suggestions['moderate'])[:limit]
        # Filter out already-visited destinations
        recs = [r for r in recs if r['destination'] not in fav_dests][:limit]
        for i, rec in enumerate(recs):
            rec['match_score'] = max(70, 95 - i * 5)  # Descending scores
            rec['based_on'] = f"Your {budget_range} budget preference and {style} travel style"
        return recs

    def _get_search_behavior(self, user):
        """Gather recent search behavior for behavioral learning."""
        try:
            from apps.analytics.models import UserActivity
            from django.utils import timezone as tz
            recent = tz.now() - timedelta(days=60)
            activities = UserActivity.objects.filter(
                user=user,
                action__in=['search_flight', 'search_hotel', 'view_attraction'],
                timestamp__gte=recent,
            ).order_by('-timestamp').values_list('metadata', flat=True)[:20]
            searches = []
            for meta in activities:
                if isinstance(meta, dict):
                    dest = meta.get('destination') or meta.get('location', '')
                    if dest:
                        searches.append({'destination': dest, 'type': meta.get('type', 'search')})
            return searches
        except Exception:
            return []

    def _save_dna(self, user, dna):
        """Save Travel DNA to UserPreference model."""
        try:
            from .models import UserPreference
            pref, _ = UserPreference.objects.get_or_create(user=user)
            pref.travel_dna = dna
            pref.last_trained = timezone.now()
            pref.save()
        except Exception as e:
            logger.warning(f"Failed to save DNA: {e}")

    def _load_dna(self, user):
        """Load existing Travel DNA."""
        try:
            from .models import UserPreference
            pref = UserPreference.objects.filter(user=user).first()
            if pref and pref.travel_dna:
                return pref.travel_dna
        except Exception:
            pass
        return None
