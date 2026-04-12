"""
Personalization Service
Learns from user behavior to build a "Travel DNA" profile and
serve personalized recommendations.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import date, datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Avg, Q

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Ramadan detection (approximate Gregorian ranges — subject to local
# moon sighting; source: astronomical calculations / published almanacs).
# The Islamic lunar calendar shifts ~10-11 days earlier each year.
# Update this table as new years are planned for.
# ──────────────────────────────────────────────────────────────────────
RAMADAN_APPROX_RANGES: Dict[int, Tuple[date, date]] = {
    2024: (date(2024, 3, 10), date(2024, 4, 9)),
    2025: (date(2025, 2, 28), date(2025, 3, 29)),
    2026: (date(2026, 2, 17), date(2026, 3, 19)),
    2027: (date(2027, 2, 6),  date(2027, 3, 8)),
    2028: (date(2028, 1, 27), date(2028, 2, 25)),
    2029: (date(2029, 1, 15), date(2029, 2, 13)),
    2030: (date(2030, 1, 5),  date(2030, 2, 3)),
    # 2030 also has a second Ramadan starting late Dec 2030 (→ Jan 2031).
    # We represent that window under 2031 since the bulk of fasting days
    # fall in Jan 2031 when most travel itineraries would use it.
    2031: (date(2030, 12, 25), date(2031, 1, 23)),
}


def _parse_trip_date(d) -> Optional[date]:
    """Coerce ISO string / date / datetime → date. None on failure."""
    if not d:
        return None
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        # Try the common shapes. First 10 chars is always the ISO date
        # portion for anything like '2026-03-01...' — that's the fast path.
        head = d[:10]
        try:
            return datetime.strptime(head, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass
        # Fall back to full-string parse for other shapes.
        for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ', '%Y/%m/%d'):
            try:
                return datetime.strptime(d, fmt).date()
            except (ValueError, TypeError):
                continue
    return None


def compute_ramadan_overlap(trip_start, trip_end) -> Optional[Dict[str, Any]]:
    """
    Return {'active': True, 'ramadan_start': ISO, 'ramadan_end': ISO,
    'overlap_start': ISO, 'overlap_end': ISO} when the trip window
    intersects a known Ramadan range; None otherwise.
    """
    ts = _parse_trip_date(trip_start)
    te = _parse_trip_date(trip_end) or ts
    if not ts:
        return None
    if te < ts:
        ts, te = te, ts

    for year in range(ts.year, te.year + 2):
        window = RAMADAN_APPROX_RANGES.get(year)
        if not window:
            continue
        rs, re = window
        overlap_start = max(ts, rs)
        overlap_end = min(te, re)
        if overlap_start <= overlap_end:
            return {
                'active': True,
                'ramadan_start': rs.isoformat(),
                'ramadan_end': re.isoformat(),
                'overlap_start': overlap_start.isoformat(),
                'overlap_end': overlap_end.isoformat(),
            }
    return None


# ISO-639-1 -> human name. The LLM handles codes, but expanded names are
# unambiguous (especially for less common codes like bn, ur, ta, te, etc.)
# when we inject them into a prompt rule about phrase-of-the-day.
ISO_639_NAMES: Dict[str, str] = {
    'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
    'it': 'Italian', 'pt': 'Portuguese', 'nl': 'Dutch', 'sv': 'Swedish',
    'no': 'Norwegian', 'da': 'Danish', 'fi': 'Finnish', 'pl': 'Polish',
    'ru': 'Russian', 'uk': 'Ukrainian', 'cs': 'Czech', 'sk': 'Slovak',
    'hu': 'Hungarian', 'ro': 'Romanian', 'bg': 'Bulgarian', 'el': 'Greek',
    'tr': 'Turkish', 'he': 'Hebrew', 'ar': 'Arabic', 'fa': 'Persian/Farsi',
    'ur': 'Urdu', 'hi': 'Hindi', 'bn': 'Bengali', 'pa': 'Punjabi',
    'ta': 'Tamil', 'te': 'Telugu', 'ml': 'Malayalam', 'kn': 'Kannada',
    'gu': 'Gujarati', 'mr': 'Marathi', 'si': 'Sinhala', 'ne': 'Nepali',
    'th': 'Thai', 'vi': 'Vietnamese', 'id': 'Indonesian', 'ms': 'Malay',
    'tl': 'Filipino/Tagalog', 'ja': 'Japanese', 'ko': 'Korean',
    'zh': 'Chinese (Mandarin)', 'yue': 'Cantonese', 'sw': 'Swahili',
    'am': 'Amharic', 'so': 'Somali', 'ha': 'Hausa', 'yo': 'Yoruba',
    'zu': 'Zulu', 'af': 'Afrikaans',
}


def _expand_languages(langs: List[str]) -> str:
    """Return 'Bengali (bn), English (en)' style for prompt injection."""
    out = []
    for code in langs:
        c = (code or '').lower().strip()
        name = ISO_639_NAMES.get(c)
        out.append(f"{name} ({c})" if name else c)
    return ', '.join(out) if out else ''


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


def _build_islam_rules(ctx: Dict[str, Any]) -> List[str]:
    """
    Return the full set of binding rules for a Muslim traveler. All 5
    pillars of faith-aware travel fire unconditionally (Prayer Times,
    Worship Places, Dietary Options, Spiritual Sites, Ramadan Mode).

    When ctx['ramadan_mode'] is present, a dedicated Ramadan block is
    appended that shifts meals to Iftar/Suhoor and adds Taraweeh prayer.
    """
    out: List[str] = []

    # 1) PRAYER TIMES — 5 daily prayers, non-negotiable scheduling gaps.
    out.append(
        "ISLAM — PRAYER TIMES (mandatory): Observe the 5 daily prayers — "
        "Fajr (pre-dawn), Dhuhr (just after midday), Asr (mid-afternoon), "
        "Maghrib (just after sunset), Isha (night). Leave a 15-minute gap "
        "around each window. Never schedule unbreakable timed activities "
        "(shows, tours with fixed start, timed restaurant bookings) inside "
        "those windows. On EVERY day's schedule, add explicit "
        "\"🕌 Prayer break — Dhuhr / Asr / Maghrib (~15 min at [nearby "
        "mosque or quiet spot])\" lines at the right times."
    )

    # 2) WORSHIP PLACES — mosque mapping, day 1 anchor.
    out.append(
        "ISLAM — WORSHIP PLACES (mandatory): On Day 1, identify the "
        "closest mosque to the hotel by name (distance in minutes walk / "
        "taxi) and include its Jumu'ah (Friday) prayer start time if the "
        "trip spans a Friday. For each day's activity cluster, name ONE "
        "mosque or musallah (prayer room) within a 10-minute reach of the "
        "midday activity, so the traveler always has a prayer option. "
        "Where applicable, note mosque etiquette (shoes off, modest dress, "
        "women's section entrance)."
    )

    # 3) DIETARY OPTIONS — halal-first, pork/alcohol exclusion.
    out.append(
        "ISLAM — DIETARY OPTIONS (mandatory): Every restaurant, café, "
        "street-food stop, and meal line MUST be halal-certified, "
        "halal-friendly, or explicitly pork-and-alcohol-free. Name the "
        "specific halal option inline — e.g., \"Dinner: Maroosh Grill "
        "(halal-certified — try the mixed grill platter)\". Exclude bars, "
        "pork-centric venues, and venues where alcohol is the primary "
        "draw. When the city has a well-known Muslim quarter or halal "
        "district, prefer restaurants from that area and name it. If halal "
        "options are scarce at a destination, flag that upfront and "
        "suggest vegetarian/seafood fallbacks."
    )

    # 4) SPIRITUAL SITES — at least one prominent Islamic site per trip.
    out.append(
        "ISLAM — SPIRITUAL SITES (mandatory): Include at least ONE "
        "prominent Islamic heritage or spiritual site visit across the "
        "trip — a historic mosque, Islamic museum, Sufi shrine, or "
        "notable madrasa. For each such site, name it and add: visiting "
        "hours, prayer-time access rules (non-Muslims are often restricted "
        "during prayers), dress code (women: headscarf; men: long trousers), "
        "and entry cost. If multiple days allow, spread 2–3 sites across "
        "the trip — don't cluster them all on Day 1."
    )

    # 5) FAITH NOTE — per-day visible line.
    out.append(
        "ISLAM — FAITH NOTE (per day): In each day, include one "
        "**Faith note** line (1 sentence) — e.g., a nearby mosque's "
        "congregation reputation, a neighborhood with strong Muslim "
        "community/food scene, an etiquette tip, or a local Islamic "
        "cultural detail the traveler will appreciate."
    )

    # 6) RAMADAN MODE — auto-enabled when trip dates overlap Ramadan.
    ramadan = ctx.get('ramadan_mode')
    if ramadan and ramadan.get('active'):
        out.append(
            "ISLAM — RAMADAN MODE ACTIVE (mandatory): The trip overlaps "
            f"Ramadan ({ramadan['ramadan_start']} → {ramadan['ramadan_end']}). "
            f"Days inside the overlap window ({ramadan['overlap_start']} → "
            f"{ramadan['overlap_end']}) MUST be re-shaped for a fasting "
            "traveler:\n"
            "  • NO midday meals — skip lunch. Replace with a light "
            "shaded walking tour or indoor activity (museum / gallery / "
            "bazaar browse).\n"
            "  • **Suhoor**: add a pre-dawn meal line (~90 min before "
            "Fajr) — name a 24-hour or pre-dawn-opening halal spot, or "
            "recommend hotel room-service / grocery provisions.\n"
            "  • **Iftar**: the main social meal moves to just after "
            "Maghrib (sunset). Name a specific Iftar buffet or restaurant "
            "known for Ramadan spread — reservations are often required "
            "during Ramadan, flag that.\n"
            "  • Expect many restaurants to be closed from Fajr to "
            "Maghrib — do NOT schedule daytime café/restaurant stops. "
            "For non-fasters in the party, suggest hotel-based options.\n"
            "  • Add an optional **Taraweeh prayer** slot after Isha "
            "(~90 min, at a nearby mosque) — a signature Ramadan "
            "spiritual experience for those interested.\n"
            "  • Include 1 **Ramadan night-market / souq / cultural "
            "evening** activity where available — night energy is much "
            "higher than daytime during Ramadan.\n"
            "  • Activity pacing: lighter mornings, more rest at "
            "midday, evenings extend later (9 pm - midnight is typical)."
        )
    else:
        # Light-touch nudge even when not active, so the LLM knows it's
        # been considered (prevents hallucinated Ramadan planning).
        out.append(
            "ISLAM — RAMADAN MODE: Not active for these dates (trip "
            "does not overlap Ramadan). Plan for normal meal schedule."
        )

    return out


def build_user_planning_context(
    user,
    trip_start_date=None,
    trip_end_date=None,
) -> Dict[str, Any]:
    """
    Build a compact personalization context dict for the AI planner.

    Pulls from UserPreference (dietary, faith, mobility, pace, languages,
    travel style, budget range), Travel DNA, and the most recent trip
    memories. Returns a shape safe to inject into an LLM system prompt
    and to echo back to the frontend for a "Personalized for you" banner.

    If ``trip_start_date`` / ``trip_end_date`` are supplied and the traveler's
    faith is Islam, we additionally compute Ramadan overlap and, when positive,
    inject a ``ramadan_mode`` block so the itinerary shifts to Iftar/Suhoor
    scheduling, adds Taraweeh prayer options, and flags daytime restaurant
    closures.

    Non-authenticated users (or any lookup failure) get an empty dict, so
    callers can unconditionally call this and still get a valid result.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return {}

    ctx: Dict[str, Any] = {
        'has_personalization': False,
        'signals': [],  # short human-readable labels for the UI banner
    }

    # 1) UserPreference — structured profile
    try:
        from .models import UserPreference
        pref = UserPreference.objects.filter(user=user).first()
        if pref:
            ctx['has_personalization'] = True
            profile: Dict[str, Any] = {}

            # Dietary
            if pref.dietary_preference and pref.dietary_preference != 'none':
                profile['dietary_preference'] = pref.dietary_preference
                ctx['signals'].append(f"Dietary: {pref.get_dietary_preference_display()}")
            if pref.dietary_allergies:
                profile['dietary_allergies'] = list(pref.dietary_allergies)
                ctx['signals'].append(f"Allergies: {', '.join(pref.dietary_allergies)}")

            # Faith
            if pref.faith and pref.faith != 'none':
                profile['faith'] = pref.faith
                profile['prayer_reminders'] = pref.prayer_reminders
                profile['faith_site_interest'] = pref.faith_site_interest
                ctx['signals'].append(f"Faith: {pref.get_faith_display()}")

            # Health / mobility
            if pref.mobility and pref.mobility != 'full':
                profile['mobility'] = pref.mobility
                ctx['signals'].append(f"Mobility: {pref.get_mobility_display()}")
            if pref.max_walking_km_per_day and float(pref.max_walking_km_per_day) < 10:
                profile['max_walking_km_per_day'] = float(pref.max_walking_km_per_day)
            if pref.health_conditions:
                profile['health_conditions'] = list(pref.health_conditions)
                ctx['signals'].append(f"Health: {', '.join(pref.health_conditions)}")
            if pref.medications:
                profile['medications'] = list(pref.medications)

            # Pace
            if pref.pace:
                profile['pace'] = pref.pace
            if pref.max_activities_per_day:
                profile['max_activities_per_day'] = pref.max_activities_per_day
            if pref.pace and pref.pace != 'moderate':
                ctx['signals'].append(f"Pace: {pref.get_pace_display()}")

            # Languages
            if pref.languages_spoken:
                profile['languages_spoken'] = list(pref.languages_spoken)
                ctx['signals'].append(f"Languages: {', '.join(pref.languages_spoken)}")

            # Style / budget
            if pref.trip_style:
                profile['trip_style'] = pref.trip_style
                ctx['signals'].append(f"Style: {pref.trip_style}")
            if pref.budget_range and pref.budget_range != 'any':
                profile['budget_range'] = pref.budget_range
                ctx['signals'].append(f"Budget: {pref.get_budget_range_display()}")

            # Preferred airlines / hotels / cuisines
            if pref.preferred_airlines:
                profile['preferred_airlines'] = list(pref.preferred_airlines)
            if pref.preferred_hotel_chains:
                profile['preferred_hotel_chains'] = list(pref.preferred_hotel_chains)
            if pref.preferred_cuisines:
                profile['preferred_cuisines'] = list(pref.preferred_cuisines)
                ctx['signals'].append(f"Cuisines: {', '.join(pref.preferred_cuisines[:3])}")

            ctx['profile'] = profile

            # Travel DNA (structured learned profile)
            if pref.travel_dna:
                ctx['travel_dna'] = pref.travel_dna
                ctx['signals'].insert(0, 'Travel DNA')
    except Exception as e:
        logger.warning(f"Failed to load UserPreference for planning context: {e}")

    # 2) Recent trip memories — learned likes/dislikes
    try:
        from .models import TripMemory
        memories = (
            TripMemory.objects.filter(user=user)
            .order_by('-created_at')[:5]
        )
        mem_snippets: List[Dict[str, Any]] = []
        for m in memories:
            highlights = m.highlights if isinstance(m.highlights, list) else []
            lowlights = m.lowlights if isinstance(m.lowlights, list) else []
            mem_snippets.append({
                'destination': m.destination,
                'sentiment': m.sentiment,
                'rating': m.rating,
                'highlights': highlights[:3],
                'lowlights': lowlights[:3],
            })
        if mem_snippets:
            ctx['recent_memories'] = mem_snippets
            ctx['has_personalization'] = True
            ctx['signals'].append(f"{len(mem_snippets)} past trip memories")
    except Exception as e:
        logger.warning(f"Failed to load TripMemory for planning context: {e}")

    # 3) Ramadan Mode — auto-activate when faith=islam AND trip dates
    # overlap a known Ramadan window. The LLM uses this to shift meals
    # to Iftar/Suhoor, skip daytime dining, add Taraweeh, etc.
    try:
        profile = ctx.get('profile') or {}
        if profile.get('faith') == 'islam' and (trip_start_date or trip_end_date):
            overlap = compute_ramadan_overlap(trip_start_date, trip_end_date)
            if overlap:
                ctx['ramadan_mode'] = overlap
                ctx['signals'].append('Ramadan Mode')
    except Exception as e:
        logger.warning(f"Ramadan overlap detection failed: {e}")

    return ctx


def format_user_context_for_prompt(ctx: Dict[str, Any]) -> str:
    """
    Render the planning context as a DIRECTIVE block of instructions
    suitable for appending to an LLM system prompt. The LLM must treat
    these as binding and explicitly reflect them in each day's output.

    Returns an empty string if there's nothing to personalize on.
    """
    if not ctx or not ctx.get('has_personalization'):
        return ''

    profile = ctx.get('profile') or {}

    # Build a concise checklist the LLM MUST satisfy in its output.
    # Each entry is a (constraint, enforcement) pair — enforcement is
    # worded as an imperative the model can comply with per-activity.
    rules: List[str] = []

    # ── Dietary ──
    diet = profile.get('dietary_preference')
    if diet:
        rules.append(
            f"DIETARY: Traveler is **{diet}**. Every restaurant, café, meal stop, and "
            f"food activity you suggest MUST be {diet}-friendly. When you name a restaurant, "
            f"add \"({diet}-friendly — [specific dish or note])\" inline. If a famous local "
            f"restaurant is not {diet}-compatible, skip it and pick a compatible alternative."
        )
    if profile.get('dietary_allergies'):
        allergies = ', '.join(profile['dietary_allergies'])
        rules.append(
            f"ALLERGIES: Traveler is allergic to **{allergies}**. Never suggest a dish "
            f"containing these. For every meal, add a note like \"(Ask staff to avoid {allergies})\"."
        )

    # ── Faith ──
    faith = profile.get('faith')
    if faith and faith != 'none':
        # Faith values match UserPreference.FAITH_CHOICES (models.py:505):
        #   islam / christianity / judaism / hinduism / buddhism / sikhism / other
        if faith == 'islam':
            # Comprehensive Islam plan: ALWAYS includes all 5 pillars of
            # faith-aware travel — Prayer Times, Worship Places, Dietary
            # Options, Spiritual Sites, Ramadan Mode. Do NOT gate these on
            # profile toggles; Muslim travelers expect the full set.
            rules.extend(_build_islam_rules(ctx))
        else:
            faith_rule = (
                f"FAITH: Traveler is **{faith}**. "
            )
            if faith == 'judaism':
                faith_rule += (
                    "Prefer kosher or kosher-style dining — name specific kosher restaurants. Avoid "
                    "shellfish/pork and meat+dairy mixing. Note Shabbat (Fri sundown - Sat sundown) — "
                    "many kosher venues close then, so plan accordingly. "
                )
            elif faith == 'hinduism':
                faith_rule += (
                    "Avoid beef entirely. Prefer vegetarian-forward restaurants; many Hindus avoid "
                    "onion/garlic too — offer a sattvic-friendly option when possible. "
                )
            elif faith == 'buddhism':
                faith_rule += (
                    "Prefer vegetarian restaurants where possible. Respect temple etiquette (silence, "
                    "no pointing feet at altars). "
                )
            elif faith == 'christianity':
                faith_rule += (
                    "Note a nearby church suitable for Sunday service if the trip spans a Sunday "
                    "(name the church and service time if known). "
                )
            elif faith == 'sikhism':
                faith_rule += (
                    "Avoid beef and pork. Prefer vegetarian or Punjabi-friendly restaurants. If a "
                    "Gurdwara is nearby, mention it — langar meals are free and welcoming to visitors. "
                )
            faith_rule += (
                f"In each day, add a brief **Faith note** item (1 line) mentioning either a "
                f"nearby {faith} worship place, faith-relevant etiquette (dress, entry rules), "
                f"or a neighborhood with strong {faith} community/food."
            )
            rules.append(faith_rule)
            if profile.get('faith_site_interest'):
                rules.append(
                    f"FAITH SITES: Include at least 1 prominent {faith} worship site visit across the trip "
                    f"(name it, add visiting hours, dress code, and entry cost)."
                )
            if profile.get('prayer_reminders'):
                rules.append(
                    "PRAYER TIMES: Leave gaps around the traveler's typical prayer windows. "
                    "Do NOT schedule unbreakable timed activities inside those windows. Add a "
                    "\"Prayer break — ~15 min\" line at the right times."
                )

    # ── Mobility / health ──
    mobility = profile.get('mobility')
    if mobility and mobility != 'full':
        rules.append(
            f"MOBILITY: Traveler has **{mobility}** mobility. Every venue you recommend MUST be "
            f"wheelchair-accessible or have elevators/ramps. Avoid hike-only sights, stairs-only "
            f"attractions, and uneven cobblestone-heavy routes. Add \"(accessible entrance / "
            f"elevator / step-free)\" notes to each major stop."
        )
    if profile.get('max_walking_km_per_day'):
        km = profile['max_walking_km_per_day']
        rules.append(
            f"WALKING LIMIT: Keep each day's total walking under **{km} km**. Use taxis/metro for "
            f"longer transfers. Add a daily walking estimate like \"≈ {min(km, 3)} km walking\" at "
            f"the end of each day."
        )
    if profile.get('health_conditions'):
        conds = ', '.join(profile['health_conditions'])
        rules.append(
            f"HEALTH: Traveler manages **{conds}**. Avoid strenuous hikes/altitude spikes. "
            f"Note the nearest pharmacy/hospital near the hotel on Day 1."
        )
    if profile.get('medications'):
        rules.append(
            "MEDICATIONS: Traveler takes regular medication — remind them in the Packing list "
            "to carry prescriptions + a printed note in English and local language."
        )

    # ── Pace ──
    pace = profile.get('pace')
    if pace:
        max_acts = profile.get('max_activities_per_day', 5)
        rules.append(
            f"PACE: Keep it **{pace}** — NO MORE than **{max_acts} major activities per day** "
            f"(meals don't count). Include a mid-afternoon rest/café break."
        )

    # ── Languages — make this ACTIVE, not passive ──
    if profile.get('languages_spoken'):
        # Expand ISO codes (e.g. 'bn' → 'Bengali (bn)') so the LLM treats
        # less-common codes unambiguously.
        langs = _expand_languages(profile['languages_spoken'])
        rules.append(
            f"LANGUAGE: Traveler speaks **{langs}**. For a destination where the local language is "
            f"NOT in this list, add a **\"Phrase of the day\"** line to each day with 1 useful "
            f"local-language phrase (with pronunciation) — e.g., greeting, ordering, asking for "
            f"help, directions. Also flag 2 venues where English/traveler's language is reliably "
            f"spoken. If the local language IS one of the traveler's languages, skip the phrase "
            f"coaching and instead note cultural speech nuances (formal vs. informal)."
        )

    # ── Style / budget / prefs ──
    if profile.get('trip_style'):
        rules.append(f"STYLE: Traveler prefers **{profile['trip_style']}** trips — tune activity "
                     f"selection to match (e.g., adventure ≠ luxury spa day).")
    if profile.get('budget_range'):
        rules.append(f"BUDGET RANGE: **{profile['budget_range']}** — scale every recommended "
                     f"restaurant/activity/hotel tier accordingly.")
    if profile.get('preferred_airlines'):
        rules.append(f"AIRLINES: Prefer {', '.join(profile['preferred_airlines'])} when flight "
                     f"options are roughly equivalent on price and schedule.")
    if profile.get('preferred_hotel_chains'):
        rules.append(f"HOTEL CHAINS: Prefer {', '.join(profile['preferred_hotel_chains'])} "
                     f"properties when available and comparable.")
    if profile.get('preferred_cuisines'):
        rules.append(f"FAVORED CUISINES: Lean toward {', '.join(profile['preferred_cuisines'])} "
                     f"when picking meals (still respect dietary/faith rules above).")

    # ── Travel DNA + memory signals ──
    dna = ctx.get('travel_dna') or {}
    dest_dna = dna.get('destinations') or {}
    if dest_dna.get('favorite_destinations'):
        favs = ', '.join(dest_dna['favorite_destinations'][:5])
        rules.append(f"PAST FAVORITES: Traveler enjoyed {favs}. Echo patterns they liked if relevant.")

    memories = ctx.get('recent_memories') or []
    loved: List[str] = []
    disliked: List[str] = []
    for m in memories[:3]:
        for h in (m.get('highlights') or [])[:3]:
            loved.append(h)
        for l in (m.get('lowlights') or [])[:3]:
            disliked.append(l)
    if loved:
        rules.append(f"LOVED PREVIOUSLY: {', '.join(loved[:5])}. Try to include similar experiences.")
    if disliked:
        rules.append(f"DISLIKED PREVIOUSLY: {', '.join(disliked[:5])}. AVOID these patterns entirely.")

    if not rules:
        return ''

    lines: List[str] = [
        '',
        '## 🎯 TRAVELER PROFILE — BINDING CONSTRAINTS (NOT SUGGESTIONS)',
        '',
        'The following rules come from the traveler\'s saved preferences. You MUST honor',
        'every one of them in the itinerary. For each day you produce, silently verify the',
        'plan against each rule below — if any activity violates a rule, REPLACE it before',
        'writing the final output. Do not simply list the preferences back; the plan itself',
        'must visibly reflect them (e.g., name a halal restaurant, include a prayer break,',
        'add a local phrase, flag accessible venues).',
        '',
    ]
    for i, r in enumerate(rules, start=1):
        lines.append(f"{i}. {r}")

    lines.append('')
    lines.append('## 📋 PER-DAY PERSONALIZATION CHECK (include in each day)')
    checks: List[str] = []
    if diet or profile.get('dietary_allergies'):
        checks.append("meals are dietary/allergy-compatible and labeled so")
    if faith == 'islam':
        # Islam always runs the full 5-pillar check (Prayer / Worship /
        # Dietary / Spiritual / Faith note). Ramadan block fires separately
        # below when active.
        checks.append("5 prayer windows (Fajr/Dhuhr/Asr/Maghrib/Isha) have 15-min gaps")
        checks.append("a nearby mosque/musallah is named for the midday cluster")
        checks.append("every food stop is halal-certified or halal-friendly (labeled inline)")
        checks.append("a Faith note line is present")
        if ctx.get('ramadan_mode', {}).get('active'):
            checks.append("Ramadan Mode is active: lunch replaced by Iftar, Suhoor included, Taraweeh optional")
    elif faith and faith != 'none':
        checks.append("a Faith note / worship cue / halal-or-kosher restaurant is present")
        if profile.get('prayer_reminders'):
            checks.append("prayer-time gaps are respected")
    if mobility and mobility != 'full':
        checks.append("every venue is accessible")
    if profile.get('max_walking_km_per_day'):
        checks.append(f"walking stays under {profile['max_walking_km_per_day']} km")
    if profile.get('languages_spoken'):
        checks.append("a Phrase of the Day is included (when local language differs)")
    if pace:
        checks.append(f"no more than {profile.get('max_activities_per_day', 5)} major activities")
    if checks:
        lines.append('Each day must silently satisfy ALL of: ' + '; '.join(checks) + '.')
    lines.append('')

    return '\n'.join(lines)
