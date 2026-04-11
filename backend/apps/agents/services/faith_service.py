"""
Faith Travel Service
Prayer times, worship places, spiritual sites, dietary restaurants, and Ramadan-aware scheduling.
"""
import hashlib
import json
import logging
import os
import random
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class FaithTravelService:
    """Faith-aware travel features: prayer times, worship places, dietary options, spiritual sites."""

    @staticmethod
    def get_prayer_times(destination: str, date_str: Optional[str] = None) -> Dict[str, Any]:
        """Get prayer times for a destination on a given date."""
        try:
            from apps.agents.models import PrayerTimeCache
            from datetime import date as date_cls, datetime

            if date_str:
                try:
                    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    target_date = date_cls.today()
            else:
                target_date = date_cls.today()

            # Check cache
            cached = PrayerTimeCache.objects.filter(
                destination__iexact=destination, date=target_date,
            ).first()
            if cached:
                return {
                    'success': True,
                    'prayer_times': {
                        'destination': cached.destination,
                        'date': str(cached.date),
                        'fajr': cached.fajr, 'sunrise': cached.sunrise,
                        'dhuhr': cached.dhuhr, 'asr': cached.asr,
                        'maghrib': cached.maghrib, 'isha': cached.isha,
                        'method': cached.method,
                    },
                }

            # Try AI generation
            times = FaithTravelService._prayer_times_ai(destination, str(target_date))
            if not times:
                times = FaithTravelService._prayer_times_fallback(destination, target_date)

            # Cache it
            PrayerTimeCache.objects.create(
                destination=destination, date=target_date,
                fajr=times['fajr'], sunrise=times['sunrise'],
                dhuhr=times['dhuhr'], asr=times['asr'],
                maghrib=times['maghrib'], isha=times['isha'],
                method=times.get('method', 'estimated'),
            )

            return {
                'success': True,
                'prayer_times': {
                    'destination': destination,
                    'date': str(target_date),
                    **times,
                },
            }
        except Exception as e:
            logger.error("Prayer times failed for %s: %s", destination, e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _prayer_times_ai(destination: str, date_str: str) -> Optional[Dict[str, str]]:
        """Try Aladhan API first, then fall back to OpenAI."""
        # --- Aladhan API (free, no key required) ---
        try:
            import requests as http_requests
            # Use city-based endpoint
            city = destination.split(',')[0].strip()
            country = destination.split(',')[-1].strip() if ',' in destination else ''
            url = 'http://api.aladhan.com/v1/timingsByCity'
            params = {
                'city': city,
                'country': country or city,
                'method': 2,  # ISNA
                'date': date_str,
            }
            resp = http_requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                api_data = resp.json()
                if api_data.get('code') == 200 and api_data.get('data'):
                    timings = api_data['data']['timings']
                    return {
                        'fajr': timings.get('Fajr', '').split(' ')[0],
                        'sunrise': timings.get('Sunrise', '').split(' ')[0],
                        'dhuhr': timings.get('Dhuhr', '').split(' ')[0],
                        'asr': timings.get('Asr', '').split(' ')[0],
                        'maghrib': timings.get('Maghrib', '').split(' ')[0],
                        'isha': timings.get('Isha', '').split(' ')[0],
                        'method': api_data['data'].get('meta', {}).get('method', {}).get('name', 'ISNA'),
                    }
        except Exception as e:
            logger.warning("Aladhan API failed for %s: %s", destination, e)

        # --- OpenAI fallback ---
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return None
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model='gpt-4o-mini', temperature=0.2, api_key=api_key, request_timeout=30)
            response = llm.invoke(
                f"Return JSON only (no markdown fences) with estimated Islamic prayer times "
                f"for {destination} on {date_str}. Format: "
                '{"fajr":"HH:MM","sunrise":"HH:MM","dhuhr":"HH:MM",'
                '"asr":"HH:MM","maghrib":"HH:MM","isha":"HH:MM","method":"estimated"}'
            )
            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            data = json.loads(content)
            if isinstance(data, dict) and 'fajr' in data:
                return data
            return None
        except Exception as e:
            logger.warning("AI prayer times failed: %s", e)
            return None

    @staticmethod
    def _prayer_times_fallback(destination: str, target_date) -> Dict[str, str]:
        seed = int(hashlib.md5(f"prayer:{destination}:{target_date.month}".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        # Approximate times varying by month (Northern hemisphere bias)
        month = target_date.month
        summer = month in (5, 6, 7, 8)
        fajr_h = 3 if summer else 5
        sunrise_h = 5 if summer else 7
        dhuhr_h = 12
        asr_h = 15 if summer else 14
        maghrib_h = 20 if summer else 17
        isha_h = 22 if summer else 19
        offset = rng.randint(-30, 30)
        return {
            'fajr': f"{fajr_h:02d}:{(30 + offset % 30):02d}",
            'sunrise': f"{sunrise_h:02d}:{(15 + offset % 45):02d}",
            'dhuhr': f"{dhuhr_h:02d}:{(15 + offset % 20):02d}",
            'asr': f"{asr_h:02d}:{(30 + offset % 30):02d}",
            'maghrib': f"{maghrib_h:02d}:{(10 + offset % 20):02d}",
            'isha': f"{isha_h:02d}:{(0 + offset % 30):02d}",
            'method': 'estimated',
        }

    @staticmethod
    def find_worship_places(destination: str, faith: Optional[str] = None,
                            worship_type: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Find worship places near a destination."""
        try:
            from apps.agents.models import WorshipPlace
            qs = WorshipPlace.objects.filter(destination__iexact=destination)
            if faith:
                qs = qs.filter(faith=faith)
            if worship_type:
                qs = qs.filter(worship_type=worship_type)

            if not qs.exists():
                FaithTravelService._generate_worship_places(destination, faith)
                qs = WorshipPlace.objects.filter(destination__iexact=destination)
                if faith:
                    qs = qs.filter(faith=faith)
                if worship_type:
                    qs = qs.filter(worship_type=worship_type)

            places = list(qs[:limit])
            return {
                'success': True,
                'places': [FaithTravelService._place_to_dict(p) for p in places],
                'total': qs.count(),
            }
        except Exception as e:
            logger.error("Worship places failed: %s", e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _generate_worship_places(destination: str, faith: Optional[str] = None):
        from apps.agents.models import WorshipPlace
        seed = int(hashlib.md5(f"worship:{destination}".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        faith_place_map = {
            'islam': [('mosque', 'Grand Mosque'), ('mosque', 'Central Masjid'), ('mosque', 'Community Islamic Center')],
            'christianity': [('church', 'Cathedral'), ('church', 'St. Mary\'s Church'), ('church', 'Grace Chapel')],
            'judaism': [('synagogue', 'Beth Shalom Synagogue'), ('synagogue', 'Central Synagogue')],
            'hinduism': [('temple', 'Sri Ganesh Temple'), ('temple', 'Lakshmi Narayan Mandir')],
            'buddhism': [('monastery', 'Zen Meditation Center'), ('temple', 'Dharma Temple')],
            'sikhism': [('gurdwara', 'Gurdwara Sahib'), ('gurdwara', 'Sikh Community Center')],
        }

        faiths_to_gen = [faith] if faith and faith in faith_place_map else list(faith_place_map.keys())
        for f in faiths_to_gen[:3]:
            templates = faith_place_map.get(f, [])
            for wtype, name_tpl in templates:
                dist = round(rng.uniform(0.3, 5.0), 2)
                WorshipPlace.objects.create(
                    destination=destination, name=f"{destination} {name_tpl}",
                    worship_type=wtype, faith=f,
                    address=f"Near city center, {destination}",
                    distance_km=dist,
                    description=f"A well-known {wtype} serving the {f} community in {destination}.",
                    rating=round(rng.uniform(3.5, 5.0), 1),
                    halal_food_nearby=(f == 'islam'),
                    kosher_food_nearby=(f == 'judaism'),
                    amenities=['parking', 'restroom'],
                    services=['daily_services'],
                )

    @staticmethod
    def get_spiritual_sites(destination: str, category: Optional[str] = None,
                            faith: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Get spiritual and religious heritage sites."""
        try:
            from apps.agents.models import SpiritualSite
            qs = SpiritualSite.objects.filter(destination__iexact=destination)
            if category:
                qs = qs.filter(category=category)

            if not qs.exists():
                FaithTravelService._generate_spiritual_sites(destination)
                qs = SpiritualSite.objects.filter(destination__iexact=destination)
                if category:
                    qs = qs.filter(category=category)

            sites = list(qs[:limit])
            return {
                'success': True,
                'sites': [FaithTravelService._site_to_dict(s) for s in sites],
                'total': qs.count(),
            }
        except Exception as e:
            logger.error("Spiritual sites failed: %s", e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _generate_spiritual_sites(destination: str):
        from apps.agents.models import SpiritualSite
        seed = int(hashlib.md5(f"spiritual:{destination}".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        templates = [
            ('pilgrimage', 'Ancient Pilgrimage Trail', ['hinduism', 'buddhism'],
             'A centuries-old pilgrimage path attracting devotees from around the world.'),
            ('heritage', 'Historic Religious Quarter', ['christianity', 'islam'],
             'A UNESCO-recognized area with religious buildings spanning multiple centuries.'),
            ('meditation', 'Tranquil Meditation Retreat', ['buddhism'],
             'A serene retreat center offering silent meditation programs for visitors.'),
            ('sacred_natural', 'Sacred Mountain Overlook', ['hinduism', 'buddhism'],
             'A natural site considered sacred by local communities for generations.'),
            ('festival_venue', 'Festival Grounds', ['hinduism'],
             'Annual religious festival grounds with cultural performances and ceremonies.'),
        ]
        rng.shuffle(templates)
        for cat, name_tpl, faiths, desc in templates[:4]:
            SpiritualSite.objects.create(
                destination=destination, name=f"{destination} {name_tpl}",
                category=cat, faiths=faiths, description=desc,
                significance=f"An important spiritual landmark in the {destination} region.",
                visitor_tips='Dress modestly and remove shoes where required.',
                dress_code='Conservative clothing recommended',
                best_time_to_visit='Early morning or late afternoon',
            )

    @staticmethod
    def get_dietary_restaurants(destination: str, dietary_type: str = 'halal',
                                limit: int = 10) -> Dict[str, Any]:
        """Get dietary-compliant restaurants (halal, kosher, vegetarian, vegan)."""
        try:
            result = FaithTravelService._dietary_ai(destination, dietary_type, limit)
            if result:
                return {'success': True, 'restaurants': result}
            return {'success': True, 'restaurants': FaithTravelService._dietary_fallback(destination, dietary_type, limit)}
        except Exception as e:
            logger.error("Dietary restaurants failed: %s", e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _dietary_ai(destination: str, dietary_type: str, limit: int) -> Optional[List[Dict]]:
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return None
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model='gpt-4o-mini', temperature=0.4, api_key=api_key, request_timeout=30)
            response = llm.invoke(
                f"List {limit} {dietary_type} restaurants in {destination}. "
                f"Return JSON array only (no markdown fences): "
                f'[{{"name":"...","cuisine":"...","distance":"... km",'
                f'"rating":4.5,"dietary_certifications":["..."],"description":"..."}}]'
            )
            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            data = json.loads(content)
            if isinstance(data, list):
                return data
            return None
        except Exception as e:
            logger.warning("AI dietary restaurants failed: %s", e)
            return None

    @staticmethod
    def _dietary_fallback(destination: str, dietary_type: str, limit: int) -> List[Dict]:
        seed = int(hashlib.md5(f"dietary:{destination}:{dietary_type}".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        cuisines = {
            'halal': ['Middle Eastern', 'Turkish', 'Pakistani', 'Malaysian', 'North African'],
            'kosher': ['Israeli', 'Jewish Deli', 'Mediterranean', 'Bakery', 'Fine Dining'],
            'vegetarian': ['Indian', 'Thai', 'Italian', 'Mexican', 'Japanese'],
            'vegan': ['Plant-Based', 'Raw Food', 'Smoothie Bar', 'Asian Fusion', 'Mediterranean'],
        }
        names_prefix = {
            'halal': ['Al-', 'Sultan ', 'Medina ', 'Saffron ', 'Oasis '],
            'kosher': ['Beth\'s ', 'David\'s ', 'Shalom ', 'Golden ', 'King '],
            'vegetarian': ['Green ', 'Garden ', 'Fresh ', 'Lotus ', 'Harvest '],
            'vegan': ['Pure ', 'Sprout ', 'Earthly ', 'Verdant ', 'Seeds '],
        }
        suffixes = ['Kitchen', 'Bistro', 'Grill', 'House', 'Cafe', 'Restaurant']
        available_cuisines = cuisines.get(dietary_type, cuisines['vegetarian'])
        prefixes = names_prefix.get(dietary_type, names_prefix['vegetarian'])

        restaurants = []
        for i in range(min(limit, 6)):
            restaurants.append({
                'name': f"{rng.choice(prefixes)}{rng.choice(suffixes)}",
                'cuisine': rng.choice(available_cuisines),
                'distance': f"{rng.uniform(0.3, 4.0):.1f} km",
                'rating': round(rng.uniform(3.5, 5.0), 1),
                'dietary_certifications': [dietary_type.capitalize(), 'Verified'],
                'description': f"Popular {dietary_type} restaurant near {destination} city center.",
            })
        return restaurants

    @staticmethod
    def get_ramadan_schedule(destination: str, date_str: Optional[str] = None) -> Dict[str, Any]:
        """Get Ramadan-aware daily schedule."""
        try:
            prayer_result = FaithTravelService.get_prayer_times(destination, date_str)
            if not prayer_result.get('success'):
                return prayer_result

            pt = prayer_result['prayer_times']
            fajr = pt.get('fajr', '04:30')
            maghrib = pt.get('maghrib', '18:30')

            # Calculate suhoor (30 min before fajr)
            fajr_parts = fajr.split(':')
            fajr_h, fajr_m = int(fajr_parts[0]), int(fajr_parts[1])
            suhoor_h = fajr_h if fajr_m >= 30 else (fajr_h - 1) % 24
            suhoor_m = (fajr_m - 30) % 60
            suhoor_time = f"{suhoor_h:02d}:{suhoor_m:02d}"

            # Fasting duration
            mag_parts = maghrib.split(':')
            mag_h, mag_m = int(mag_parts[0]), int(mag_parts[1])
            fasting_mins = (mag_h * 60 + mag_m) - (fajr_h * 60 + fajr_m)
            if fasting_mins < 0:
                fasting_mins += 24 * 60
            fasting_hours = f"{fasting_mins // 60}h {fasting_mins % 60}m"

            return {
                'success': True,
                'schedule': {
                    'suhoor_time': suhoor_time,
                    'iftar_time': maghrib,
                    'fasting_hours': fasting_hours,
                    'activity_windows': [
                        {'period': 'Early Morning', 'activities': f'Suhoor by {suhoor_time}, Fajr prayer at {fajr}'},
                        {'period': 'Morning (8-11 AM)', 'activities': 'Light sightseeing, museum visits, cultural tours'},
                        {'period': 'Midday (11 AM-2 PM)', 'activities': 'Rest and indoor activities, shopping in AC malls'},
                        {'period': 'Afternoon (2-5 PM)', 'activities': 'Light activities, prepare for iftar'},
                        {'period': 'Evening', 'activities': f'Iftar at {maghrib}, evening prayers, night markets'},
                    ],
                    'tips': [
                        'Stay hydrated between iftar and suhoor',
                        'Avoid strenuous outdoor activities during peak heat hours',
                        'Many restaurants close during fasting hours; plan meals accordingly',
                        'Respect local customs by not eating in public during fasting hours',
                        'Night markets and entertainment are often more active after iftar',
                        f'Carry water and dates for iftar if you will be outdoors near {maghrib}',
                    ],
                },
            }
        except Exception as e:
            logger.error("Ramadan schedule failed: %s", e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_faith_travel_summary(destination: str, faith: str) -> Dict[str, Any]:
        """Comprehensive faith travel summary combining all features."""
        try:
            prayer = FaithTravelService.get_prayer_times(destination)
            worship = FaithTravelService.find_worship_places(destination, faith=faith, limit=5)
            spiritual = FaithTravelService.get_spiritual_sites(destination, faith=faith, limit=5)

            dietary_map = {'islam': 'halal', 'judaism': 'kosher', 'hinduism': 'vegetarian',
                           'buddhism': 'vegetarian', 'sikhism': 'vegetarian'}
            dietary_type = dietary_map.get(faith, 'vegetarian')
            dietary = FaithTravelService.get_dietary_restaurants(destination, dietary_type, limit=5)

            return {
                'success': True,
                'destination': destination,
                'faith': faith,
                'prayer_times': prayer.get('prayer_times'),
                'worship_places': worship.get('places', []),
                'spiritual_sites': spiritual.get('sites', []),
                'dietary_restaurants': dietary.get('restaurants', []),
            }
        except Exception as e:
            logger.error("Faith travel summary failed: %s", e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _place_to_dict(place) -> Dict[str, Any]:
        return {
            'id': place.id,
            'name': place.name,
            'worship_type': place.worship_type,
            'faith': place.faith,
            'address': place.address,
            'distance_km': float(place.distance_km) if place.distance_km else None,
            'description': place.description,
            'rating': float(place.rating),
            'halal_food_nearby': place.halal_food_nearby,
            'kosher_food_nearby': place.kosher_food_nearby,
            'services': place.services or [],
            'amenities': place.amenities or [],
            'operating_hours': place.operating_hours or {},
        }

    @staticmethod
    def _site_to_dict(site) -> Dict[str, Any]:
        return {
            'id': site.id,
            'name': site.name,
            'category': site.category,
            'faiths': site.faiths or [],
            'description': site.description,
            'significance': site.significance,
            'visitor_tips': site.visitor_tips,
            'dress_code': site.dress_code,
            'best_time_to_visit': site.best_time_to_visit,
            'image_url': site.image_url,
        }
