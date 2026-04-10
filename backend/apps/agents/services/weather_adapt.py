"""
WeatherAdaptAgent — Weather-triggered itinerary adaptation.

Monitors weather conditions and automatically suggests or applies
itinerary changes when weather impacts travel plans.
"""
import hashlib
import json
import logging
import os
import random
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


# Indoor alternatives by activity category
_INDOOR_ALTERNATIVES = {
    'sightseeing': [
        'Visit a museum or gallery',
        'Explore a covered market or food hall',
        'Take a guided indoor tour',
        'Visit a historic cathedral or temple',
    ],
    'outdoor_adventure': [
        'Indoor rock climbing or bouldering',
        'Visit an aquarium or indoor zoo',
        'Try an escape room experience',
        'Indoor go-karting or bowling',
    ],
    'beach': [
        'Spa and wellness day',
        'Indoor pool and hot tub session',
        'Cooking class with local cuisine',
        'Shopping at a local mall or boutique',
    ],
    'walking_tour': [
        'Hop-on-hop-off bus tour (covered)',
        'Underground or subway exploration',
        'Visit a bookshop cafe and relax',
        'Take a local cooking or craft workshop',
    ],
    'nature': [
        'Botanical garden with covered sections',
        'Natural history museum',
        'Indoor butterfly garden',
        'Local cinema showing regional films',
    ],
    'dining': [
        'Indoor food market exploration',
        'Wine or cocktail tasting class',
        'Fine dining reservation',
        'Street food hall visit',
    ],
    'general': [
        'Visit a local museum',
        'Explore indoor markets',
        'Take a cooking class',
        'Spa and relaxation',
    ],
}


class WeatherAdaptAgent:
    """Adapts itinerary based on weather conditions."""

    def adapt_itinerary(
        self,
        destination: str,
        activities: List[Dict[str, Any]],
        weather: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Given current/forecast weather and planned activities,
        suggest adaptations.

        Parameters
        ----------
        destination : str
        activities : list of {name, type, time, is_outdoor}
        weather : dict with temperature, condition, wind_speed, humidity

        Returns
        -------
        dict with adapted_activities, changes_made, overall_impact, tips
        """
        condition = weather.get('condition', 'Clear')
        temp = weather.get('temperature', 22)
        wind = weather.get('wind_speed', 5)

        # Determine weather severity
        severity = self._assess_severity(condition, temp, wind)

        if severity == 'none':
            return {
                'adapted_activities': activities,
                'changes_made': [],
                'overall_impact': 'none',
                'tips': ['Weather looks great — enjoy your planned activities!'],
            }

        # Try LLM adaptation
        result = self._adapt_with_llm(destination, activities, weather, severity)
        if result is not None:
            return result

        # Fallback: rule-based adaptation
        return self._adapt_fallback(destination, activities, weather, severity)

    def get_weather_alternatives(
        self,
        destination: str,
        activity_type: str,
        weather_condition: str,
    ) -> List[Dict[str, Any]]:
        """
        Get alternative activity suggestions for bad weather.
        """
        seed = int(
            hashlib.md5(
                f'{destination}:{activity_type}:{weather_condition}'.encode()
            ).hexdigest()[:8],
            16,
        )
        rng = random.Random(seed)

        category = self._categorize_activity(activity_type)
        alternatives = _INDOOR_ALTERNATIVES.get(category, _INDOOR_ALTERNATIVES['general'])

        suggestions = []
        for alt in alternatives:
            suggestions.append({
                'name': alt,
                'reason': f'Great indoor alternative when weather is {weather_condition.lower()}',
                'category': category,
                'match_score': round(rng.uniform(0.7, 0.95), 2),
            })

        suggestions.sort(key=lambda x: x['match_score'], reverse=True)
        return suggestions

    def should_reschedule(
        self,
        activity: Dict[str, Any],
        weather: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Determine if a specific activity should be rescheduled.
        """
        is_outdoor = activity.get('is_outdoor', True)
        condition = weather.get('condition', 'Clear')
        temp = weather.get('temperature', 22)

        if not is_outdoor:
            return {
                'should_reschedule': False,
                'reason': 'Indoor activity — weather does not affect it.',
                'urgency': 'none',
            }

        severity = self._assess_severity(condition, temp, weather.get('wind_speed', 5))

        if severity == 'none':
            return {
                'should_reschedule': False,
                'reason': 'Weather is suitable for this activity.',
                'urgency': 'none',
            }
        elif severity == 'low':
            return {
                'should_reschedule': False,
                'reason': 'Minor weather concern — bring appropriate gear.',
                'urgency': 'low',
                'gear_suggestion': self._gear_for_condition(condition, temp),
            }
        elif severity == 'moderate':
            return {
                'should_reschedule': True,
                'reason': f'{condition} expected — consider rescheduling outdoor activities.',
                'urgency': 'moderate',
                'alternatives': self.get_weather_alternatives(
                    '', activity.get('type', 'general'), condition
                ),
            }
        else:
            return {
                'should_reschedule': True,
                'reason': f'Severe weather ({condition}) — strongly recommend rescheduling.',
                'urgency': 'high',
                'alternatives': self.get_weather_alternatives(
                    '', activity.get('type', 'general'), condition
                ),
            }

    # ── Private helpers ──────────────────────────────────────

    @staticmethod
    def _assess_severity(condition: str, temp: float, wind: float) -> str:
        """Assess weather severity: none, low, moderate, high."""
        if condition in ('Thunderstorm',):
            return 'high'
        if condition in ('Rain', 'Snow') and wind > 20:
            return 'high'
        if condition in ('Rain', 'Snow', 'Drizzle'):
            return 'moderate'
        if condition in ('Mist', 'Clouds') and wind > 30:
            return 'moderate'
        if temp > 40 or temp < -5:
            return 'moderate'
        if temp > 35 or temp < 0:
            return 'low'
        if wind > 25:
            return 'low'
        return 'none'

    @staticmethod
    def _categorize_activity(activity_type: str) -> str:
        """Map activity type to indoor alternative category."""
        mapping = {
            'sightseeing': 'sightseeing',
            'tour': 'walking_tour',
            'walking': 'walking_tour',
            'hiking': 'outdoor_adventure',
            'adventure': 'outdoor_adventure',
            'beach': 'beach',
            'swimming': 'beach',
            'nature': 'nature',
            'park': 'nature',
            'dining': 'dining',
            'food': 'dining',
            'restaurant': 'dining',
        }
        lower = activity_type.lower()
        for key, cat in mapping.items():
            if key in lower:
                return cat
        return 'general'

    @staticmethod
    def _gear_for_condition(condition: str, temp: float) -> str:
        if condition in ('Rain', 'Drizzle'):
            return 'Bring an umbrella and waterproof jacket.'
        if condition == 'Snow':
            return 'Wear warm waterproof boots and layered clothing.'
        if temp > 35:
            return 'Bring sunscreen, hat, and plenty of water.'
        if temp < 5:
            return 'Dress in warm layers — hat, gloves, and scarf recommended.'
        return 'Dress in comfortable layers.'

    def _adapt_with_llm(
        self,
        destination: str,
        activities: List[Dict],
        weather: Dict,
        severity: str,
    ) -> Optional[Dict[str, Any]]:
        """Try LLM-based itinerary adaptation."""
        api_key = getattr(
            settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', '')
        )
        if not api_key or api_key in ('', 'your_openai_api_key_here'):
            return None

        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(
                model='gpt-4o-mini', temperature=0.4,
                api_key=api_key, request_timeout=30,
            )
            act_text = json.dumps(activities[:10], default=str)
            resp = model.invoke([
                SystemMessage(content=(
                    'You are a travel itinerary adaptation specialist. '
                    'Return JSON only, no markdown fences.'
                )),
                HumanMessage(content=f"""Weather in {destination}: {weather.get('condition')} {weather.get('temperature')}°C, wind {weather.get('wind_speed')}km/h. Severity: {severity}.

Planned activities: {act_text}

Adapt the itinerary. Return JSON:
{{
  "adapted_activities": [{{...same fields as input, with changes noted...}}],
  "changes_made": ["description of each change"],
  "overall_impact": "{severity}",
  "tips": ["practical tip 1", "practical tip 2"]
}}"""),
            ])
            content = resp.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            return json.loads(content)
        except Exception as e:
            logger.warning('LLM adaptation failed: %s', e)
            return None

    def _adapt_fallback(
        self,
        destination: str,
        activities: List[Dict],
        weather: Dict,
        severity: str,
    ) -> Dict[str, Any]:
        """Rule-based itinerary adaptation."""
        condition = weather.get('condition', 'Clear')
        temp = weather.get('temperature', 22)

        adapted = []
        changes = []

        for act in activities:
            new_act = dict(act)
            is_outdoor = act.get('is_outdoor', True)

            if is_outdoor and severity in ('moderate', 'high'):
                category = self._categorize_activity(act.get('type', 'general'))
                alts = _INDOOR_ALTERNATIVES.get(category, _INDOOR_ALTERNATIVES['general'])

                seed = int(
                    hashlib.md5(
                        f"{act.get('name', '')}:{condition}".encode()
                    ).hexdigest()[:8],
                    16,
                )
                rng = random.Random(seed)
                replacement = rng.choice(alts)

                new_act['original_name'] = act.get('name', '')
                new_act['name'] = replacement
                new_act['is_outdoor'] = False
                new_act['adapted'] = True
                changes.append(
                    f"Replaced '{act.get('name', 'outdoor activity')}' "
                    f"with '{replacement}' due to {condition.lower()}"
                )
            else:
                new_act['adapted'] = False

            adapted.append(new_act)

        tips = []
        if condition in ('Rain', 'Drizzle', 'Thunderstorm'):
            tips.append('Carry an umbrella and waterproof bag for electronics.')
        if condition == 'Snow':
            tips.append('Wear waterproof boots and dress in layers.')
        if temp > 35:
            tips.append('Stay hydrated and take breaks in air-conditioned spaces.')
        if temp < 5:
            tips.append('Dress warmly and plan for shorter outdoor sessions.')
        if not tips:
            tips.append('Check weather updates throughout the day.')

        return {
            'adapted_activities': adapted,
            'changes_made': changes,
            'overall_impact': severity,
            'tips': tips,
        }
