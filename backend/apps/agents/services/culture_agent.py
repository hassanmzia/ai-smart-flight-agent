"""
Culture Agent Service
AI-powered cultural etiquette, faith recommendations, and local customs guidance.
"""
import hashlib
import json
import logging
import os
import random
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class CultureAgent:
    """Provides cultural etiquette guides, faith-specific advice, and local customs."""

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def get_etiquette_guide(
        self,
        destination: str,
        user_faith: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return cultural etiquette for a destination.

        Returns dict with greeting, tipping, dress_code, taboos,
        dining_etiquette, religious_considerations, do_list, dont_list.
        """
        result = self._etiquette_openai(destination, user_faith)
        if result is not None:
            return result
        return self._etiquette_fallback(destination, user_faith)

    def get_faith_recommendations(
        self,
        destination: str,
        faith: str,
        interests: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Return faith-specific places and guidance.

        Returns dict with prayer_times_info, nearby_places,
        dietary_guidance, dress_guidance.
        """
        result = self._faith_openai(destination, faith, interests)
        if result is not None:
            return result
        return self._faith_fallback(destination, faith, interests)

    def get_local_customs(
        self,
        destination: str,
    ) -> Dict[str, Any]:
        """
        Return local customs for a destination.

        Returns dict with language_tips, bargaining_culture,
        safety_customs, transport_customs, greeting_customs.
        """
        result = self._customs_openai(destination)
        if result is not None:
            return result
        return self._customs_fallback(destination)

    # ------------------------------------------------------------------ #
    #  OpenAI helpers
    # ------------------------------------------------------------------ #

    def _etiquette_openai(self, destination, user_faith) -> Optional[Dict[str, Any]]:
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return None
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(
                model='gpt-4o-mini', temperature=0.4,
                api_key=api_key, request_timeout=30,
            )
            faith_note = f"\nThe traveler follows {user_faith}." if user_faith and user_faith != 'none' else ""
            response = model.invoke([
                SystemMessage(content=(
                    "You are a cultural etiquette expert. "
                    "Return JSON only, no markdown fences."
                )),
                HumanMessage(content=(
                    f"Provide cultural etiquette guidance for visiting {destination}.{faith_note}\n\n"
                    "Return JSON:\n"
                    '{"greeting": "<how to greet locals>", '
                    '"tipping": "<tipping customs>", '
                    '"dress_code": "<appropriate dress>", '
                    '"taboos": ["taboo1", "taboo2", "taboo3"], '
                    '"dining_etiquette": "<dining tips>", '
                    '"religious_considerations": ["consideration1", "consideration2"], '
                    '"do_list": ["do1", "do2", "do3", "do4"], '
                    '"dont_list": ["dont1", "dont2", "dont3", "dont4"]}'
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
            logger.warning("OpenAI etiquette guide failed for %s: %s", destination, e)
            return None

    def _faith_openai(self, destination, faith, interests) -> Optional[Dict[str, Any]]:
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return None
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(
                model='gpt-4o-mini', temperature=0.4,
                api_key=api_key, request_timeout=30,
            )
            interests_note = f"\nInterests: {', '.join(interests)}" if interests else ""
            response = model.invoke([
                SystemMessage(content=(
                    "You are a faith-sensitive travel advisor. "
                    "Return JSON only, no markdown fences."
                )),
                HumanMessage(content=(
                    f"Provide {faith} faith-specific travel guidance for {destination}.{interests_note}\n\n"
                    "Return JSON:\n"
                    '{"prayer_times_info": "<info about prayer times>", '
                    '"nearby_places": [{"name": "<place>", "type": "<type>", '
                    '"distance": "<distance>", "description": "<desc>"}], '
                    '"dietary_guidance": "<dietary advice>", '
                    '"dress_guidance": "<dress advice>"}'
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
            logger.warning("OpenAI faith recommendations failed for %s: %s", destination, e)
            return None

    def _customs_openai(self, destination) -> Optional[Dict[str, Any]]:
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return None
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(
                model='gpt-4o-mini', temperature=0.4,
                api_key=api_key, request_timeout=30,
            )
            response = model.invoke([
                SystemMessage(content=(
                    "You are a local customs expert. "
                    "Return JSON only, no markdown fences."
                )),
                HumanMessage(content=(
                    f"Provide local customs guidance for {destination}.\n\n"
                    "Return JSON:\n"
                    '{"language_tips": "<language advice>", '
                    '"bargaining_culture": "<bargaining info>", '
                    '"safety_customs": "<safety advice>", '
                    '"transport_customs": "<transport tips>", '
                    '"greeting_customs": "<greeting customs>"}'
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
            logger.warning("OpenAI local customs failed for %s: %s", destination, e)
            return None

    # ------------------------------------------------------------------ #
    #  Template-based fallbacks keyed by destination keyword matching
    # ------------------------------------------------------------------ #

    _REGION_KEYWORDS = {
        'middle_east': [
            'dubai', 'abu dhabi', 'doha', 'riyadh', 'jeddah', 'muscat',
            'amman', 'beirut', 'cairo', 'istanbul', 'tehran', 'kuwait',
            'bahrain', 'oman', 'qatar', 'saudi', 'jordan', 'egypt',
            'morocco', 'marrakech', 'casablanca', 'tunis',
        ],
        'east_asia': [
            'tokyo', 'kyoto', 'osaka', 'seoul', 'beijing', 'shanghai',
            'hong kong', 'taipei', 'japan', 'china', 'korea', 'taiwan',
        ],
        'south_asia': [
            'delhi', 'mumbai', 'bangkok', 'singapore', 'kuala lumpur',
            'bali', 'jakarta', 'hanoi', 'ho chi minh', 'india',
            'thailand', 'malaysia', 'indonesia', 'vietnam', 'sri lanka',
            'kathmandu', 'nepal', 'dhaka', 'colombo',
        ],
        'europe': [
            'london', 'paris', 'rome', 'berlin', 'madrid', 'barcelona',
            'amsterdam', 'vienna', 'prague', 'lisbon', 'athens',
            'zurich', 'brussels', 'dublin', 'copenhagen', 'stockholm',
            'oslo', 'helsinki', 'warsaw', 'budapest', 'italy', 'france',
            'germany', 'spain', 'portugal', 'greece', 'switzerland',
            'uk', 'england', 'scotland',
        ],
        'americas': [
            'new york', 'los angeles', 'miami', 'mexico city', 'cancun',
            'rio', 'buenos aires', 'lima', 'bogota', 'toronto',
            'vancouver', 'usa', 'canada', 'brazil', 'mexico',
            'colombia', 'peru', 'argentina', 'chile', 'san francisco',
            'chicago', 'havana', 'cuba',
        ],
    }

    def _detect_region(self, destination: str) -> str:
        dest_lower = destination.lower()
        for region, keywords in self._REGION_KEYWORDS.items():
            for kw in keywords:
                if kw in dest_lower:
                    return region
        return 'general'

    # -- Etiquette fallback ------------------------------------------------

    def _etiquette_fallback(self, destination, user_faith) -> Dict[str, Any]:
        region = self._detect_region(destination)
        seed = int(
            hashlib.md5(f"etiquette:{destination}:{user_faith}".encode()).hexdigest()[:8], 16,
        )
        rng = random.Random(seed)

        templates = {
            'middle_east': {
                'greeting': 'Use "As-salamu alaykum" (peace be upon you). Handshakes are common between same genders.',
                'tipping': 'Tipping 10-15% is customary in restaurants. Round up taxi fares.',
                'dress_code': 'Dress modestly. Cover shoulders and knees, especially near religious sites.',
                'taboos': [
                    'Avoid public displays of affection',
                    'Do not photograph people without permission',
                    'Do not eat, drink, or smoke in public during Ramadan daylight hours',
                ],
                'dining_etiquette': 'Eat with your right hand. Accept tea or coffee when offered as a sign of respect.',
                'religious_considerations': [
                    'Friday is the holy day; some businesses close',
                    'Prayer times are observed five times daily',
                    'Remove shoes before entering mosques',
                ],
                'do_list': [
                    'Learn a few Arabic phrases',
                    'Dress conservatively in public',
                    'Accept hospitality graciously',
                    'Bargain politely in souks and markets',
                ],
                'dont_list': [
                    'Do not point the soles of your feet at others',
                    'Avoid discussing politics or religion casually',
                    'Do not take photos of government buildings',
                    'Avoid public intoxication',
                ],
            },
            'east_asia': {
                'greeting': 'Bow slightly when greeting. In Japan, bowing depth shows respect level.',
                'tipping': 'Tipping is generally not expected and may be considered rude in Japan. In China and Korea, it is becoming more common in tourist areas.',
                'dress_code': 'Smart casual is generally appropriate. Remove shoes when entering homes and some traditional restaurants.',
                'taboos': [
                    'Do not stick chopsticks upright in rice',
                    'Avoid blowing your nose loudly in public',
                    'Do not tip in Japan',
                ],
                'dining_etiquette': 'Wait for the host to begin eating. Slurping noodles is acceptable in Japan.',
                'religious_considerations': [
                    'Remove shoes before entering temples',
                    'Dress modestly at religious sites',
                    'Do not touch Buddhist statues or monks',
                ],
                'do_list': [
                    'Carry cash; many places do not accept cards',
                    'Learn basic phrases in the local language',
                    'Respect queuing culture',
                    'Use both hands when giving and receiving items',
                ],
                'dont_list': [
                    'Do not raise your voice in public',
                    'Avoid physical contact with strangers',
                    'Do not litter; keep spaces clean',
                    'Avoid discussing sensitive historical topics',
                ],
            },
            'south_asia': {
                'greeting': 'Use "Namaste" with palms pressed together in India and Nepal. A slight bow is respectful in Southeast Asia.',
                'tipping': 'Tipping 10% is appreciated in restaurants. Tip tour guides and drivers.',
                'dress_code': 'Dress modestly, especially at temples. Remove shoes before entering religious sites.',
                'taboos': [
                    'Do not touch someone\'s head',
                    'Avoid pointing your feet at people or religious objects',
                    'Do not use your left hand for eating or passing items',
                ],
                'dining_etiquette': 'Eating with your hands is common in many areas. Always use your right hand.',
                'religious_considerations': [
                    'Temples may require specific dress codes',
                    'Some sites restrict entry during ceremonies',
                    'Respect local prayer and meditation times',
                ],
                'do_list': [
                    'Bargain politely at markets',
                    'Try street food from busy stalls',
                    'Carry small denominations for tips',
                    'Respect local wildlife and nature',
                ],
                'dont_list': [
                    'Do not wear shoes inside temples',
                    'Avoid public displays of affection',
                    'Do not disrespect local currency',
                    'Avoid taking photos without permission at sacred sites',
                ],
            },
            'europe': {
                'greeting': 'A handshake is standard. In France and Southern Europe, cheek kisses are common among acquaintances.',
                'tipping': 'Tipping 5-10% is customary in restaurants. Service charge is often included.',
                'dress_code': 'Smart casual for most occasions. Cover shoulders and knees when visiting churches.',
                'taboos': [
                    'Do not skip greetings; always say hello and goodbye',
                    'Avoid being overly loud in public spaces',
                    'Do not assume everyone speaks English',
                ],
                'dining_etiquette': 'Keep hands on the table (not in your lap). Bread is often placed directly on the table in France.',
                'religious_considerations': [
                    'Churches may restrict entry during services',
                    'Dress modestly when visiting cathedrals',
                    'Photography may be prohibited inside religious buildings',
                ],
                'do_list': [
                    'Learn basic local phrases (hello, please, thank you)',
                    'Validate train tickets before boarding',
                    'Enjoy leisurely meals; rushing is frowned upon',
                    'Respect quiet hours in residential areas',
                ],
                'dont_list': [
                    'Do not touch produce at markets unless invited',
                    'Avoid sitting at reserved tables in restaurants',
                    'Do not expect free water at restaurants everywhere',
                    'Avoid wearing athletic clothing to nice restaurants',
                ],
            },
            'americas': {
                'greeting': 'A firm handshake and smile is standard in North America. In Latin America, a light hug or cheek kiss is common.',
                'tipping': 'Tip 15-20% in the US and Canada. In Latin America, 10% is standard.',
                'dress_code': 'Casual dress is widely accepted. Some upscale restaurants require smart casual.',
                'taboos': [
                    'Avoid discussing politics with strangers',
                    'Do not make assumptions about nationality',
                    'Avoid skipping the queue',
                ],
                'dining_etiquette': 'In the US, the check will not come until you ask for it. In Latin America, meals are leisurely.',
                'religious_considerations': [
                    'Churches welcome visitors but be respectful during services',
                    'Some indigenous sites have specific visitor rules',
                    'Sunday is a rest day in many communities',
                ],
                'do_list': [
                    'Tip service workers generously in the US',
                    'Try local regional cuisines',
                    'Be punctual in North America; expect flexible timing in Latin America',
                    'Carry ID at all times',
                ],
                'dont_list': [
                    'Do not jaywalk in cities with strict traffic laws',
                    'Avoid flashing expensive jewelry in crowded areas',
                    'Do not photograph military or police installations',
                    'Avoid discussing salaries or personal finances',
                ],
            },
        }

        template = templates.get(region)
        if not template:
            # General fallback
            template = {
                'greeting': f'A polite greeting with a smile goes a long way in {destination}.',
                'tipping': 'Check local customs; 10-15% is a safe default in most restaurants.',
                'dress_code': 'Dress modestly and appropriately for the climate and local customs.',
                'taboos': [
                    'Avoid loud or disruptive behaviour in public',
                    'Do not photograph people without consent',
                    'Respect local religious and cultural practices',
                ],
                'dining_etiquette': 'Follow the lead of locals. When in doubt, observe before acting.',
                'religious_considerations': [
                    'Dress modestly at religious sites',
                    'Ask before entering places of worship',
                ],
                'do_list': [
                    'Learn a few words in the local language',
                    'Respect local customs and traditions',
                    'Be open-minded and patient',
                    'Carry local currency for small purchases',
                ],
                'dont_list': [
                    'Do not litter',
                    'Avoid discussing sensitive political topics',
                    'Do not disrespect local symbols or flags',
                    'Avoid being loud in quiet or sacred spaces',
                ],
            }

        # Add faith-specific note if provided
        if user_faith and user_faith != 'none':
            faith_considerations = {
                'islam': 'Look for halal food options and nearby mosques for prayer.',
                'judaism': 'Seek kosher dining options and locate nearby synagogues.',
                'hinduism': 'Vegetarian options are widely available; locate nearby temples.',
                'buddhism': 'Seek meditation spaces and respect local Buddhist customs.',
                'christianity': 'Locate nearby churches for services and fellowship.',
                'sikhism': 'Look for gurdwaras which often serve free community meals.',
            }
            extra = faith_considerations.get(user_faith)
            if extra:
                template['religious_considerations'] = list(template['religious_considerations']) + [extra]

        # Shuffle lists deterministically
        for key in ('taboos', 'do_list', 'dont_list', 'religious_considerations'):
            if isinstance(template.get(key), list):
                items = list(template[key])
                rng.shuffle(items)
                template[key] = items

        return template

    # -- Faith recommendations fallback ------------------------------------

    def _faith_fallback(self, destination, faith, interests) -> Dict[str, Any]:
        seed = int(
            hashlib.md5(f"faith:{destination}:{faith}".encode()).hexdigest()[:8], 16,
        )
        rng = random.Random(seed)

        faith_data = {
            'islam': {
                'prayer_times_info': (
                    'Prayer times vary by location and season. Use a local prayer times app '
                    f'or check the nearest mosque in {destination} for accurate schedules.'
                ),
                'place_types': ['Mosque', 'Islamic Cultural Center', 'Halal Restaurant', 'Islamic Heritage Site'],
                'dietary_guidance': (
                    'Seek halal-certified restaurants. Many international chains offer halal options. '
                    'Seafood and vegetarian dishes are generally safe alternatives.'
                ),
                'dress_guidance': (
                    'Modest clothing is recommended. Women may want to carry a headscarf '
                    'for mosque visits. Men should wear long trousers at religious sites.'
                ),
            },
            'christianity': {
                'prayer_times_info': (
                    f'Sunday services are widely available in {destination}. '
                    'Check local church websites for service times and language options.'
                ),
                'place_types': ['Church', 'Cathedral', 'Christian Bookshop', 'Historic Chapel'],
                'dietary_guidance': (
                    'No specific dietary restrictions for most denominations. '
                    'During Lent, some travelers may wish to find fish-based meal options.'
                ),
                'dress_guidance': (
                    'Smart casual is appropriate for most churches. '
                    'Cover shoulders and knees when visiting cathedrals or historic churches.'
                ),
            },
            'judaism': {
                'prayer_times_info': (
                    f'Shabbat begins Friday evening and ends Saturday evening in {destination}. '
                    'Check local synagogue listings for service schedules.'
                ),
                'place_types': ['Synagogue', 'Kosher Restaurant', 'Jewish Heritage Site', 'Jewish Community Center'],
                'dietary_guidance': (
                    'Look for kosher-certified restaurants. Many cities have kosher grocery stores. '
                    'Vegetarian and seafood (check for kosher species) are generally safer options.'
                ),
                'dress_guidance': (
                    'Men should bring a kippah for synagogue visits. '
                    'Modest dress is expected at religious sites.'
                ),
            },
            'hinduism': {
                'prayer_times_info': (
                    f'Temple hours in {destination} typically run from early morning to evening. '
                    'Major puja times are usually at dawn and dusk.'
                ),
                'place_types': ['Hindu Temple', 'Meditation Center', 'Vegetarian Restaurant', 'Cultural Center'],
                'dietary_guidance': (
                    'Vegetarian food is widely available. Avoid beef in areas with large Hindu communities. '
                    'Many restaurants clearly label vegetarian options.'
                ),
                'dress_guidance': (
                    'Remove shoes before entering temples. '
                    'Cover shoulders and legs. Avoid leather items at some temples.'
                ),
            },
            'buddhism': {
                'prayer_times_info': (
                    f'Meditation sessions and chanting are often held at dawn and dusk in {destination}. '
                    'Many temples welcome visitors for morning meditation.'
                ),
                'place_types': ['Buddhist Temple', 'Meditation Retreat', 'Vegetarian Restaurant', 'Monastery'],
                'dietary_guidance': (
                    'Many Buddhist practitioners prefer vegetarian food. '
                    'Temple-adjacent restaurants often serve vegetarian meals.'
                ),
                'dress_guidance': (
                    'Dress modestly and remove shoes before entering temples. '
                    'Avoid clothing with Buddha images, which is considered disrespectful.'
                ),
            },
            'sikhism': {
                'prayer_times_info': (
                    f'Gurdwara services (diwan) in {destination} are usually held in the morning and evening. '
                    'The langar (community kitchen) serves free meals to all visitors.'
                ),
                'place_types': ['Gurdwara', 'Sikh Community Center', 'Vegetarian Restaurant', 'Heritage Site'],
                'dietary_guidance': (
                    'Langar meals at gurdwaras are always vegetarian and free. '
                    'Avoid beef and halal meat at Sikh establishments.'
                ),
                'dress_guidance': (
                    'Cover your head when entering a gurdwara. Headscarves are often provided. '
                    'Remove shoes and wash hands before entering.'
                ),
            },
        }

        data = faith_data.get(faith, {
            'prayer_times_info': f'Check locally in {destination} for worship schedules.',
            'place_types': ['Place of Worship', 'Cultural Center', 'Community Center'],
            'dietary_guidance': 'Check local options that align with your dietary needs.',
            'dress_guidance': 'Dress modestly when visiting religious or cultural sites.',
        })

        # Generate nearby places
        place_types = data.get('place_types', ['Place of Worship'])
        places = []
        distances = ['0.5 km', '1.2 km', '2.0 km', '3.5 km']
        rng.shuffle(distances)
        for i, ptype in enumerate(place_types):
            places.append({
                'name': f'{destination} {ptype}',
                'type': ptype,
                'distance': distances[i % len(distances)],
                'description': f'A well-known {ptype.lower()} serving the {faith} community in {destination}.',
            })

        return {
            'prayer_times_info': data['prayer_times_info'],
            'nearby_places': places,
            'dietary_guidance': data['dietary_guidance'],
            'dress_guidance': data['dress_guidance'],
        }

    # -- Local customs fallback --------------------------------------------

    def _customs_fallback(self, destination) -> Dict[str, Any]:
        region = self._detect_region(destination)
        seed = int(
            hashlib.md5(f"customs:{destination}".encode()).hexdigest()[:8], 16,
        )
        rng = random.Random(seed)

        templates = {
            'middle_east': {
                'language_tips': 'Arabic is widely spoken. English is common in tourist areas and hotels. Learning "Shukran" (thank you) and "Marhaba" (hello) is appreciated.',
                'bargaining_culture': 'Bargaining is expected in souks and local markets. Start at about half the asking price and negotiate politely.',
                'safety_customs': 'Generally safe for tourists. Dress modestly, stay aware of your surroundings, and respect local laws.',
                'transport_customs': 'Taxis are common; agree on the fare before starting. Ride-hailing apps are widely used in major cities.',
                'greeting_customs': 'Greet with "As-salamu alaykum." Handshakes are common between same genders. Wait for a woman to extend her hand first.',
            },
            'east_asia': {
                'language_tips': 'Local language is primary. English proficiency varies. Translation apps are invaluable. Learn basic numbers and polite phrases.',
                'bargaining_culture': 'Bargaining is common in street markets but not in shops or malls. Be polite and smile while negotiating.',
                'safety_customs': 'Very safe for tourists. Petty theft can occur in crowded areas. Follow local rules and regulations carefully.',
                'transport_customs': 'Public transit is excellent and punctual. Get a rechargeable transit card. Taxis use meters in most cities.',
                'greeting_customs': 'Bow slightly when greeting. Exchange business cards with both hands. Avoid excessive physical contact.',
            },
            'south_asia': {
                'language_tips': 'English is widely understood in tourist areas. Learn local greetings and "thank you" in the local language.',
                'bargaining_culture': 'Bargaining is a way of life in markets and with tuk-tuk drivers. Always negotiate before agreeing to a price.',
                'safety_customs': 'Stay aware in crowded areas. Use registered taxis and avoid isolated areas at night. Drink bottled water.',
                'transport_customs': 'Tuk-tuks, motorbike taxis, and ride-hailing apps are common. Agree on prices before rides. Trains are popular for longer trips.',
                'greeting_customs': 'Use "Namaste" with palms together in India and Nepal. A friendly smile goes a long way across the region.',
            },
            'europe': {
                'language_tips': 'English is widely spoken in Northern and Western Europe. In Southern and Eastern Europe, basic local phrases are helpful.',
                'bargaining_culture': 'Bargaining is generally not practised in shops. Flea markets and some street vendors may allow light negotiation.',
                'safety_customs': 'Generally very safe. Watch for pickpockets in tourist hotspots. Keep valuables secure on public transport.',
                'transport_customs': 'Excellent public transport in most cities. Validate tickets before boarding. Consider rail passes for multi-city trips.',
                'greeting_customs': 'Handshakes are standard. Cheek kisses vary by country (one, two, or three). Always greet shopkeepers when entering.',
            },
            'americas': {
                'language_tips': 'English in North America; Spanish or Portuguese in Central and South America. Basic Spanish is very helpful throughout Latin America.',
                'bargaining_culture': 'Not common in the US/Canada except at flea markets. Expected at markets throughout Latin America.',
                'safety_customs': 'Varies by area. Use common sense, avoid displaying expensive items, and stay in well-lit areas at night.',
                'transport_customs': 'Car culture dominates in the US. Public transit is strong in major cities. In Latin America, buses are the main transport.',
                'greeting_customs': 'Firm handshake in North America. In Latin America, a light hug or cheek kiss is standard among acquaintances.',
            },
        }

        template = templates.get(region, {
            'language_tips': f'English may be spoken in tourist areas of {destination}. Learning basic local phrases is always appreciated.',
            'bargaining_culture': 'Check locally whether bargaining is customary at markets and with transport providers.',
            'safety_customs': f'Exercise standard travel safety precautions in {destination}. Keep valuables secure and stay aware.',
            'transport_customs': 'Research local transport options in advance. Ride-hailing apps are available in many destinations.',
            'greeting_customs': f'A friendly smile and polite greeting are universally appreciated in {destination}.',
        })

        return template
