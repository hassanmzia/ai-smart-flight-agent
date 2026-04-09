"""
Personalization Service
Learns from user behavior to build a "Travel DNA" profile and
serve personalized recommendations.
"""
import logging
from typing import Dict, Any, List, Optional
from django.utils import timezone
from django.db.models import Count, Avg, Q

logger = logging.getLogger(__name__)


class PersonalizationService:
    """Builds and uses personalized travel profiles."""

    def build_travel_dna(self, user) -> Dict[str, Any]:
        """
        Analyze user's booking history, searches, and feedback to build
        a comprehensive Travel DNA profile.
        """
        dna = {
            'destinations': self._analyze_destinations(user),
            'budget': self._analyze_budget(user),
            'style': self._analyze_style(user),
            'timing': self._analyze_timing(user),
            'preferences': self._analyze_preferences(user),
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

    def _generate_recommendations(self, user, dna, limit):
        """Generate personalized recommendations based on DNA."""
        recs = []

        fav_dests = dna.get('destinations', {}).get('favorite_destinations', [])
        budget_range = dna.get('budget', {}).get('range', 'moderate')
        style = dna.get('style', {}).get('style', 'balanced')

        # Simple rule-based recommendations
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

        for rec in recs:
            rec['match_score'] = 85  # Simplified scoring
            rec['based_on'] = f"Your {budget_range} budget preference and {style} travel style"

        return recs

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
