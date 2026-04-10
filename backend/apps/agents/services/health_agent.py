"""
Health Agent Service
AI-powered health assessment, pacing plans, and medication timezone adjustment for trips.
"""
import hashlib
import json
import logging
import os
import random
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class HealthAgent:
    """Assesses trip health risks, generates pacing plans, and adjusts medication schedules."""

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def assess_trip_health(
        self,
        destination: str,
        user_conditions: Optional[List[str]] = None,
        medications: Optional[List[str]] = None,
        pace: str = 'moderate',
        max_walking_km: float = 10,
    ) -> Dict[str, Any]:
        """
        Assess health considerations for a trip.

        Returns dict with risk_level, health_tips, medication_reminders,
        pacing_suggestions, hydration_tips, altitude_info, heat_info,
        vaccination_notes.
        """
        result = self._assess_openai(
            destination, user_conditions, medications, pace, max_walking_km,
        )
        if result is not None:
            return result
        return self._assess_fallback(
            destination, user_conditions, medications, pace, max_walking_km,
        )

    def generate_pacing_plan(
        self,
        activities_per_day: int,
        max_walking_km: float,
        pace: str,
        trip_days: int = 1,
    ) -> Dict[str, Any]:
        """
        Generate an hourly schedule template.

        Returns dict with morning_block, midday_rest, afternoon_block,
        evening_block, total_walking_km, activity_count, rest_periods.
        """
        result = self._pacing_openai(activities_per_day, max_walking_km, pace, trip_days)
        if result is not None:
            return result
        return self._pacing_fallback(activities_per_day, max_walking_km, pace, trip_days)

    def medication_timezone_adjust(
        self,
        medications: List[Dict[str, str]],
        origin_tz: str,
        destination_tz: str,
    ) -> List[Dict[str, Any]]:
        """
        Adjust medication schedule for timezone changes.

        Parameters
        ----------
        medications : list[dict]
            Each dict has 'name' and 'time' (e.g. '08:00').
        origin_tz : str
            Origin timezone, e.g. 'America/New_York'.
        destination_tz : str
            Destination timezone, e.g. 'Europe/London'.

        Returns list of {name, original_time, adjusted_time, note}.
        """
        result = self._medication_openai(medications, origin_tz, destination_tz)
        if result is not None:
            return result
        return self._medication_fallback(medications, origin_tz, destination_tz)

    # ------------------------------------------------------------------ #
    #  OpenAI helpers
    # ------------------------------------------------------------------ #

    def _assess_openai(
        self, destination, user_conditions, medications, pace, max_walking_km,
    ) -> Optional[Dict[str, Any]]:
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return None
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(
                model='gpt-4o-mini', temperature=0.3,
                api_key=api_key, request_timeout=30,
            )
            conds = ', '.join(user_conditions) if user_conditions else 'None reported'
            meds = ', '.join(medications) if medications else 'None reported'
            response = model.invoke([
                SystemMessage(content=(
                    "You are a travel health advisor. "
                    "Return JSON only, no markdown fences."
                )),
                HumanMessage(content=(
                    f"Assess health considerations for traveling to {destination}.\n"
                    f"Health conditions: {conds}\n"
                    f"Medications: {meds}\n"
                    f"Pace: {pace}, Max walking: {max_walking_km} km/day\n\n"
                    "Return JSON:\n"
                    '{"risk_level": "<low|moderate|high>", '
                    '"health_tips": ["tip1", "tip2", "tip3"], '
                    '"medication_reminders": ["reminder1", "reminder2"], '
                    '"pacing_suggestions": "<pacing advice>", '
                    '"hydration_tips": "<hydration advice>", '
                    '"altitude_info": "<altitude info or N/A>", '
                    '"heat_info": "<heat info or N/A>", '
                    '"vaccination_notes": "<vaccination notes>"}'
                )),
            ])
            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            data = json.loads(content)
            if isinstance(data, dict):
                return data
            return None
        except Exception as e:
            logger.warning("OpenAI health assessment failed for %s: %s", destination, e)
            return None

    def _pacing_openai(
        self, activities_per_day, max_walking_km, pace, trip_days,
    ) -> Optional[Dict[str, Any]]:
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return None
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(
                model='gpt-4o-mini', temperature=0.3,
                api_key=api_key, request_timeout=30,
            )
            response = model.invoke([
                SystemMessage(content=(
                    "You are a travel pacing advisor. "
                    "Return JSON only, no markdown fences."
                )),
                HumanMessage(content=(
                    f"Create a daily pacing plan.\n"
                    f"Activities per day: {activities_per_day}\n"
                    f"Max walking: {max_walking_km} km/day\n"
                    f"Pace: {pace}\nTrip days: {trip_days}\n\n"
                    "Return JSON:\n"
                    '{"morning_block": "<schedule>", '
                    '"midday_rest": "<rest period>", '
                    '"afternoon_block": "<schedule>", '
                    '"evening_block": "<schedule>", '
                    '"total_walking_km": <float>, '
                    '"activity_count": <int>, '
                    '"rest_periods": <int>}'
                )),
            ])
            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            data = json.loads(content)
            if isinstance(data, dict):
                return data
            return None
        except Exception as e:
            logger.warning("OpenAI pacing plan failed: %s", e)
            return None

    def _medication_openai(
        self, medications, origin_tz, destination_tz,
    ) -> Optional[List[Dict[str, Any]]]:
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return None
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(
                model='gpt-4o-mini', temperature=0.2,
                api_key=api_key, request_timeout=30,
            )
            response = model.invoke([
                SystemMessage(content=(
                    "You are a medication schedule advisor. "
                    "Return JSON only, no markdown fences."
                )),
                HumanMessage(content=(
                    f"Adjust medication schedule for timezone change.\n"
                    f"Origin: {origin_tz}\nDestination: {destination_tz}\n"
                    f"Medications: {json.dumps(medications)}\n\n"
                    "Return JSON array:\n"
                    '[{"name": "<med>", "original_time": "<HH:MM>", '
                    '"adjusted_time": "<HH:MM>", "note": "<advice>"}]'
                )),
            ])
            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            data = json.loads(content)
            if isinstance(data, list):
                return data
            return None
        except Exception as e:
            logger.warning("OpenAI medication adjustment failed: %s", e)
            return None

    # ------------------------------------------------------------------ #
    #  Deterministic fallbacks
    # ------------------------------------------------------------------ #

    # Keywords for high-altitude destinations
    _HIGH_ALTITUDE = [
        'cusco', 'la paz', 'lhasa', 'quito', 'bogota', 'addis ababa',
        'denver', 'mexico city', 'kathmandu', 'tibet',
    ]
    # Keywords for hot-climate destinations
    _HOT_CLIMATE = [
        'dubai', 'doha', 'riyadh', 'phoenix', 'bangkok', 'delhi',
        'mumbai', 'cairo', 'marrakech', 'singapore', 'jakarta',
        'abu dhabi', 'bahrain', 'kuwait',
    ]
    # Keywords for tropical destinations
    _TROPICAL = [
        'bali', 'phuket', 'cancun', 'caribbean', 'hawaii', 'maldives',
        'fiji', 'zanzibar', 'goa', 'sri lanka', 'costa rica',
    ]

    def _assess_fallback(
        self, destination, user_conditions, medications, pace, max_walking_km,
    ) -> Dict[str, Any]:
        seed = int(
            hashlib.md5(
                f"health:{destination}:{pace}".encode()
            ).hexdigest()[:8], 16,
        )
        rng = random.Random(seed)

        dest_lower = destination.lower()
        conditions = user_conditions or []
        meds = medications or []

        # Determine risk level
        risk_level = 'low'
        if len(conditions) >= 2 or any(
            c.lower() in ('diabetes', 'heart disease', 'asthma', 'epilepsy')
            for c in conditions
        ):
            risk_level = 'high'
        elif conditions:
            risk_level = 'moderate'

        # Health tips
        base_tips = [
            'Carry a basic first-aid kit with band-aids, antiseptic, and pain relievers.',
            'Stay hydrated by drinking at least 2-3 litres of water daily.',
            'Pack any prescription medications in your carry-on luggage.',
            'Get adequate sleep to maintain your immune system while traveling.',
            'Wear comfortable walking shoes to prevent blisters and foot pain.',
            'Apply sunscreen (SPF 30+) regularly, even on cloudy days.',
            'Wash hands frequently or use hand sanitiser.',
            'Take breaks every 1-2 hours during extended walking.',
        ]
        rng.shuffle(base_tips)
        health_tips = base_tips[:5]

        # Condition-specific tips
        for condition in conditions:
            cl = condition.lower()
            if 'diabetes' in cl:
                health_tips.append('Carry glucose tablets and snacks for blood sugar management.')
            elif 'asthma' in cl:
                health_tips.append('Keep your inhaler accessible and be cautious of air quality.')
            elif 'heart' in cl:
                health_tips.append('Avoid strenuous activities at high altitude. Rest when needed.')
            elif 'allergy' in cl or 'allergies' in cl:
                health_tips.append('Carry antihistamines and be aware of local allergens.')

        # Medication reminders
        medication_reminders = []
        if meds:
            medication_reminders.append('Set phone alarms for each medication time adjusted to the local timezone.')
            medication_reminders.append('Carry a printed list of your medications with generic names.')
            medication_reminders.append('Keep medications in original labeled containers for customs.')
        else:
            medication_reminders.append('No medications reported. Carry basic over-the-counter remedies.')

        # Pacing suggestions
        pace_map = {
            'slow': (
                f'Take it easy with no more than {max_walking_km * 0.7:.1f} km of walking per day. '
                'Schedule long rest periods between activities.'
            ),
            'moderate': (
                f'Aim for {max_walking_km * 0.85:.1f} km of walking per day with regular '
                'breaks every 90 minutes.'
            ),
            'packed': (
                f'You can walk up to {max_walking_km:.1f} km per day but ensure at least '
                '30-minute rest breaks between major activities.'
            ),
        }
        pacing_suggestions = pace_map.get(pace, pace_map['moderate'])

        # Hydration
        hydration_tips = 'Drink at least 2 litres of water daily. Increase to 3+ litres in hot or humid climates.'

        # Altitude info
        altitude_info = 'N/A'
        for kw in self._HIGH_ALTITUDE:
            if kw in dest_lower:
                altitude_info = (
                    f'{destination} is at high altitude. Acclimatise gradually over 2-3 days. '
                    'Avoid alcohol and strenuous activity on arrival. Watch for symptoms of '
                    'altitude sickness: headache, nausea, dizziness.'
                )
                if risk_level == 'low':
                    risk_level = 'moderate'
                break

        # Heat info
        heat_info = 'N/A'
        for kw in self._HOT_CLIMATE:
            if kw in dest_lower:
                heat_info = (
                    f'{destination} can be extremely hot. Avoid outdoor activities during midday '
                    '(11am-3pm). Wear light, breathable clothing and a hat. '
                    'Watch for heat exhaustion symptoms.'
                )
                break
        if heat_info == 'N/A':
            for kw in self._TROPICAL:
                if kw in dest_lower:
                    heat_info = (
                        f'{destination} has a tropical climate with high humidity. '
                        'Stay hydrated, use mosquito repellent, and take breaks in air-conditioned spaces.'
                    )
                    break

        # Vaccination notes
        vaccination_notes = (
            f'Consult your doctor or a travel clinic at least 4-6 weeks before traveling to {destination}. '
            'Ensure routine vaccinations are up to date. Check CDC or WHO recommendations for destination-specific vaccines.'
        )

        return {
            'risk_level': risk_level,
            'health_tips': health_tips,
            'medication_reminders': medication_reminders,
            'pacing_suggestions': pacing_suggestions,
            'hydration_tips': hydration_tips,
            'altitude_info': altitude_info,
            'heat_info': heat_info,
            'vaccination_notes': vaccination_notes,
        }

    def _pacing_fallback(
        self, activities_per_day, max_walking_km, pace, trip_days,
    ) -> Dict[str, Any]:
        seed = int(
            hashlib.md5(
                f"pacing:{activities_per_day}:{max_walking_km}:{pace}".encode()
            ).hexdigest()[:8], 16,
        )
        rng = random.Random(seed)

        # Distribute activities across time blocks
        pace_config = {
            'slow': {'morning_acts': 1, 'afternoon_acts': 1, 'rest_mins': 120, 'walk_factor': 0.6},
            'moderate': {'morning_acts': 2, 'afternoon_acts': 1, 'rest_mins': 90, 'walk_factor': 0.8},
            'packed': {'morning_acts': 2, 'afternoon_acts': 2, 'rest_mins': 45, 'walk_factor': 1.0},
        }
        config = pace_config.get(pace, pace_config['moderate'])

        morning_acts = min(config['morning_acts'], activities_per_day)
        remaining = max(0, activities_per_day - morning_acts)
        afternoon_acts = min(config['afternoon_acts'], remaining)
        remaining = max(0, remaining - afternoon_acts)
        evening_acts = remaining

        total_walking = round(max_walking_km * config['walk_factor'], 1)

        # Calculate rest periods
        total_activities = morning_acts + afternoon_acts + evening_acts
        rest_periods = max(1, total_activities - 1) + 1  # rest between activities + midday

        morning_block = (
            f"8:00 AM - 12:00 PM: {morning_acts} activity(ies). "
            f"Walk ~{round(total_walking * 0.4, 1)} km. "
            f"Take a {config['rest_mins'] // 2}-minute break between activities."
        )

        midday_rest = (
            f"12:00 PM - {1 if pace == 'packed' else 2}:00 PM: "
            f"Lunch and rest for {config['rest_mins']} minutes. "
            "Rehydrate and recharge."
        )

        afternoon_start = '1:00 PM' if pace == 'packed' else '2:00 PM'
        afternoon_block = (
            f"{afternoon_start} - 5:00 PM: {afternoon_acts} activity(ies). "
            f"Walk ~{round(total_walking * 0.35, 1)} km. "
            "Take breaks as needed."
        )

        evening_block = (
            f"6:00 PM - 9:00 PM: "
            + (f"{evening_acts} activity(ies). " if evening_acts else "Free time. ")
            + f"Walk ~{round(total_walking * 0.25, 1)} km. "
            + "Enjoy dinner and leisure."
        )

        return {
            'morning_block': morning_block,
            'midday_rest': midday_rest,
            'afternoon_block': afternoon_block,
            'evening_block': evening_block,
            'total_walking_km': total_walking,
            'activity_count': total_activities,
            'rest_periods': rest_periods,
        }

    def _medication_fallback(
        self, medications, origin_tz, destination_tz,
    ) -> List[Dict[str, Any]]:
        """Adjust medication times using UTC offset estimation."""
        offset_hours = self._estimate_tz_offset(origin_tz, destination_tz)

        results = []
        for med in medications:
            name = med.get('name', 'Unknown medication')
            original_time = med.get('time', '08:00')

            # Parse time
            try:
                parts = original_time.split(':')
                hours = int(parts[0])
                minutes = int(parts[1]) if len(parts) > 1 else 0
            except (ValueError, IndexError):
                hours, minutes = 8, 0

            # Adjust
            new_hours = (hours + offset_hours) % 24
            adjusted_time = f"{new_hours:02d}:{minutes:02d}"

            # Determine note
            abs_diff = abs(offset_hours)
            if abs_diff == 0:
                note = 'No timezone change. Continue your normal schedule.'
            elif abs_diff <= 3:
                note = (
                    f'Small timezone shift ({offset_hours:+d}h). '
                    'Adjust by 1 hour per day until you reach the new time.'
                )
            elif abs_diff <= 6:
                note = (
                    f'Moderate timezone shift ({offset_hours:+d}h). '
                    'Gradually adjust over 2-3 days. Set phone alarms for reminders.'
                )
            else:
                note = (
                    f'Large timezone shift ({offset_hours:+d}h). '
                    'Consult your doctor about adjustment strategy. '
                    'Consider splitting the adjustment over several days.'
                )

            results.append({
                'name': name,
                'original_time': original_time,
                'adjusted_time': adjusted_time,
                'note': note,
            })

        return results

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    # Simplified UTC offset map for common timezones
    _TZ_OFFSETS = {
        'US/Eastern': -5, 'America/New_York': -5,
        'US/Central': -6, 'America/Chicago': -6,
        'US/Mountain': -7, 'America/Denver': -7,
        'US/Pacific': -8, 'America/Los_Angeles': -8,
        'Europe/London': 0, 'GMT': 0, 'UTC': 0,
        'Europe/Paris': 1, 'Europe/Berlin': 1, 'Europe/Rome': 1,
        'Europe/Madrid': 1, 'Europe/Amsterdam': 1,
        'Europe/Athens': 2, 'Europe/Istanbul': 3,
        'Europe/Moscow': 3, 'Asia/Dubai': 4,
        'Asia/Karachi': 5, 'Asia/Kolkata': 5,
        'Asia/Dhaka': 6, 'Asia/Bangkok': 7,
        'Asia/Singapore': 8, 'Asia/Shanghai': 8,
        'Asia/Hong_Kong': 8, 'Asia/Tokyo': 9,
        'Asia/Seoul': 9, 'Australia/Sydney': 11,
        'Pacific/Auckland': 12, 'Pacific/Honolulu': -10,
        'America/Sao_Paulo': -3, 'America/Buenos_Aires': -3,
        'America/Mexico_City': -6, 'America/Bogota': -5,
        'America/Lima': -5, 'Africa/Cairo': 2,
        'Africa/Nairobi': 3, 'Africa/Lagos': 1,
        'Asia/Jakarta': 7, 'Asia/Taipei': 8,
    }

    def _estimate_tz_offset(self, origin_tz: str, destination_tz: str) -> int:
        """Estimate hour offset between two timezones."""
        origin_offset = self._TZ_OFFSETS.get(origin_tz, 0)
        dest_offset = self._TZ_OFFSETS.get(destination_tz, 0)
        return dest_offset - origin_offset
