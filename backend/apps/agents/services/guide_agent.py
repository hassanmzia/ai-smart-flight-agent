"""
Guide Agent Service
AI-powered curated guide generation for must-visit/eat/see/do lists per destination.
"""
import hashlib
import json
import logging
import os
import random
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class GuideAgent:
    """Generates AI-curated must-visit/eat/see lists for destinations."""

    GUIDE_TITLES = {
        'must_visit': 'Must-Visit Places in {destination}',
        'must_eat': 'Must-Eat Food & Restaurants in {destination}',
        'must_see': 'Must-See Sights in {destination}',
        'must_do': 'Must-Do Activities in {destination}',
        'hidden_gem': 'Hidden Gems of {destination}',
    }

    GUIDE_DESCRIPTIONS = {
        'must_visit': (
            'A curated list of the top places you absolutely must visit '
            'when traveling to {destination}. From iconic landmarks to '
            'beloved local spots, these are the essential stops for any trip.'
        ),
        'must_eat': (
            'The definitive food guide for {destination}. Discover the best '
            'restaurants, street food, and local delicacies that make this '
            'destination a culinary delight.'
        ),
        'must_see': (
            'The most spectacular sights and views in {destination}. '
            'These are the visual highlights you cannot miss, from '
            'breathtaking panoramas to architectural wonders.'
        ),
        'must_do': (
            'The top experiences and activities in {destination}. '
            'From thrilling adventures to relaxing pastimes, these '
            'are the things every visitor should try.'
        ),
        'hidden_gem': (
            'Off-the-beaten-path treasures in {destination}. These '
            'lesser-known spots offer authentic experiences away from '
            'the tourist crowds.'
        ),
    }

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def generate_guide(self, destination: str, guide_type: str):
        """
        Generate (or retrieve cached) a curated guide for a destination.

        Returns the saved CuratedGuide model instance.
        """
        from apps.community.models import CuratedGuide
        from django.utils import timezone
        from datetime import timedelta

        # Return existing guide if fresh (updated within last 7 days)
        existing = CuratedGuide.objects.filter(
            destination__iexact=destination,
            guide_type=guide_type,
        ).first()

        if existing and existing.last_updated > timezone.now() - timedelta(days=7):
            return existing

        # Try OpenAI-powered generation, fall back to template-based
        guide_data = self._generate_openai(destination, guide_type)
        if guide_data is None:
            guide_data = self._generate_fallback(destination, guide_type)

        title = self.GUIDE_TITLES.get(
            guide_type, 'Travel Guide for {destination}'
        ).format(destination=destination)

        description = self.GUIDE_DESCRIPTIONS.get(
            guide_type, 'A curated travel guide for {destination}.'
        ).format(destination=destination)

        # Persist using case-normalized destination
        guide, _ = CuratedGuide.objects.update_or_create(
            destination=destination,
            guide_type=guide_type,
            defaults={
                'title': title,
                'description': description,
                'items': guide_data,
                'ai_generated': True,
            },
        )
        return guide

    # ------------------------------------------------------------------ #
    #  OpenAI-powered generation
    # ------------------------------------------------------------------ #

    def _generate_openai(
        self, destination: str, guide_type: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Generate a curated guide using OpenAI. Returns None on failure."""
        api_key = getattr(
            settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''),
        )
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return None

        guide_type_label = dict([
            ('must_visit', 'must-visit places'),
            ('must_eat', 'must-eat food and restaurants'),
            ('must_see', 'must-see sights and views'),
            ('must_do', 'must-do activities and experiences'),
            ('hidden_gem', 'hidden gems and off-the-beaten-path spots'),
        ]).get(guide_type, 'notable places')

        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(
                model='gpt-4o-mini',
                temperature=0.6,
                api_key=api_key,
                request_timeout=45,
            )

            response = model.invoke([
                SystemMessage(content=(
                    "You are a world-class travel curator. "
                    "Return JSON only, no markdown fences."
                )),
                HumanMessage(content=f"""Create a curated list of top 10 {guide_type_label} in {destination}.

Return a JSON array of exactly 10 objects. Each object must have these exact keys:
[
  {{
    "name": "<place/item name>",
    "description": "<2-3 sentence description>",
    "rating": <float 1-10>,
    "price_range": "<one of: $, $$, $$$, $$$$>",
    "best_time": "<best time to visit/try, e.g. 'Morning', 'Evening', 'Year-round'>",
    "address": "<approximate address or area>",
    "website_url": "",
    "image_url": "",
    "tags": ["tag1", "tag2", "tag3"]
  }}
]

Be specific to {destination}. Use real, well-known places and items that actually exist there."""),
            ])

            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            data = json.loads(content)

            if not isinstance(data, list):
                return None

            # Validate and normalize each item
            items = []
            for item in data[:10]:
                items.append({
                    'name': str(item.get('name', '')),
                    'description': str(item.get('description', '')),
                    'rating': float(item.get('rating', 7.5)),
                    'price_range': str(item.get('price_range', '$$')),
                    'best_time': str(item.get('best_time', 'Year-round')),
                    'address': str(item.get('address', '')),
                    'website_url': str(item.get('website_url', '')),
                    'image_url': str(item.get('image_url', '')),
                    'tags': list(item.get('tags', [])),
                })
            return items

        except Exception as e:
            logger.warning(
                "OpenAI guide generation failed for %s (%s): %s",
                destination, guide_type, e,
            )
            return None

    # ------------------------------------------------------------------ #
    #  Template-based fallback
    # ------------------------------------------------------------------ #

    def _generate_fallback(
        self, destination: str, guide_type: str,
    ) -> List[Dict[str, Any]]:
        """Generate a plausible template-based guide when OpenAI is unavailable."""
        seed = int(
            hashlib.md5(
                f"{destination}:{guide_type}".encode()
            ).hexdigest()[:8],
            16,
        )
        rng = random.Random(seed)

        templates = self._get_templates(guide_type, destination)
        items = []

        for template in templates:
            rating = round(rng.uniform(7.0, 9.5), 1)
            price_range = rng.choice(['$', '$$', '$$$', '$$$$'])
            items.append({
                'name': template['name'],
                'description': template['description'].format(
                    destination=destination,
                ),
                'rating': rating,
                'price_range': price_range,
                'best_time': template.get('best_time', 'Year-round'),
                'address': template.get(
                    'address', f'Central {destination}',
                ),
                'website_url': '',
                'image_url': '',
                'tags': template.get('tags', []),
            })

        return items

    def _get_templates(
        self, guide_type: str, destination: str,
    ) -> List[Dict[str, Any]]:
        """Return template items based on guide type."""
        templates = {
            'must_visit': [
                {
                    'name': 'Historic Old Town',
                    'description': (
                        'The charming historic center of {destination} '
                        'with cobblestone streets, historic architecture, '
                        'and vibrant local culture. A must for any first-time visitor.'
                    ),
                    'best_time': 'Morning',
                    'tags': ['historic', 'walking', 'architecture'],
                },
                {
                    'name': 'Central Market',
                    'description': (
                        'The bustling main market of {destination} where locals '
                        'shop for fresh produce, spices, and handmade goods. '
                        'A sensory overload in the best way.'
                    ),
                    'best_time': 'Early morning',
                    'tags': ['market', 'food', 'local culture'],
                },
                {
                    'name': 'National Museum',
                    'description': (
                        'The premier museum in {destination} showcasing the '
                        'rich history and cultural heritage of the region. '
                        'Plan at least half a day to explore.'
                    ),
                    'best_time': 'Afternoon',
                    'tags': ['museum', 'culture', 'history'],
                },
                {
                    'name': 'Royal Palace',
                    'description': (
                        'An iconic landmark of {destination}, the royal palace '
                        'offers stunning architecture and beautifully maintained '
                        'gardens open to the public.'
                    ),
                    'best_time': 'Morning',
                    'tags': ['landmark', 'architecture', 'royalty'],
                },
                {
                    'name': 'Waterfront Promenade',
                    'description': (
                        'A scenic walkway along the water in {destination}, '
                        'perfect for a leisurely stroll with views of the '
                        'skyline and local boat traffic.'
                    ),
                    'best_time': 'Evening',
                    'tags': ['scenic', 'walking', 'waterfront'],
                },
                {
                    'name': 'Botanical Gardens',
                    'description': (
                        'Lush tropical and exotic gardens in {destination} '
                        'featuring hundreds of plant species and peaceful '
                        'walking paths. A green oasis in the city.'
                    ),
                    'best_time': 'Morning',
                    'tags': ['nature', 'gardens', 'peaceful'],
                },
                {
                    'name': 'Grand Cathedral',
                    'description': (
                        'A magnificent religious landmark in {destination} '
                        'known for its awe-inspiring architecture and '
                        'centuries of history.'
                    ),
                    'best_time': 'Afternoon',
                    'tags': ['religious', 'architecture', 'historic'],
                },
                {
                    'name': 'Arts District',
                    'description': (
                        'The creative heart of {destination}, filled with '
                        'galleries, street art, independent shops, and '
                        'trendy cafes.'
                    ),
                    'best_time': 'Afternoon',
                    'tags': ['art', 'culture', 'shopping'],
                },
                {
                    'name': 'City Viewpoint',
                    'description': (
                        'The best panoramic viewpoint in {destination}, '
                        'offering sweeping views of the entire city. '
                        'Spectacular at any time of day.'
                    ),
                    'best_time': 'Sunset',
                    'tags': ['viewpoint', 'photography', 'scenic'],
                },
                {
                    'name': 'Local Neighborhood Quarter',
                    'description': (
                        'An authentic residential neighborhood in {destination} '
                        'where you can experience daily life, local eateries, '
                        'and genuine hospitality.'
                    ),
                    'best_time': 'Any time',
                    'tags': ['local life', 'authentic', 'neighborhood'],
                },
            ],
            'must_eat': [
                {
                    'name': 'Local Street Food Market',
                    'description': (
                        'The most popular street food destination in '
                        '{destination}, serving authentic local dishes at '
                        'affordable prices. Come hungry.'
                    ),
                    'best_time': 'Lunch',
                    'tags': ['street food', 'local cuisine', 'budget'],
                },
                {
                    'name': 'Traditional Heritage Restaurant',
                    'description': (
                        'A beloved family-run restaurant in {destination} '
                        'that has been serving traditional recipes for '
                        'generations. Reservations recommended.'
                    ),
                    'best_time': 'Dinner',
                    'tags': ['traditional', 'fine dining', 'heritage'],
                },
                {
                    'name': 'Waterfront Seafood House',
                    'description': (
                        'Fresh seafood with a view in {destination}. '
                        'Known for the catch of the day and generous '
                        'portions at reasonable prices.'
                    ),
                    'best_time': 'Lunch or dinner',
                    'tags': ['seafood', 'waterfront', 'fresh'],
                },
                {
                    'name': 'Rooftop Bar & Grill',
                    'description': (
                        'A stylish rooftop dining spot in {destination} '
                        'with panoramic city views, craft cocktails, and '
                        'grilled specialties.'
                    ),
                    'best_time': 'Evening',
                    'tags': ['rooftop', 'cocktails', 'views'],
                },
                {
                    'name': 'Morning Pastry & Coffee House',
                    'description': (
                        'The go-to breakfast spot in {destination} for '
                        'flaky pastries, strong coffee, and a warm '
                        'atmosphere to start your day.'
                    ),
                    'best_time': 'Breakfast',
                    'tags': ['breakfast', 'coffee', 'pastries'],
                },
                {
                    'name': 'Night Market Food Stalls',
                    'description': (
                        'An electric atmosphere of sizzling woks and '
                        'aromatic spices at the {destination} night market. '
                        'Dozens of vendors offer local favorites.'
                    ),
                    'best_time': 'Night',
                    'tags': ['night market', 'street food', 'atmosphere'],
                },
                {
                    'name': 'Vegetarian & Vegan Bistro',
                    'description': (
                        'A creative plant-based restaurant in {destination} '
                        'proving that local cuisine can be reinvented with '
                        'fresh, sustainable ingredients.'
                    ),
                    'best_time': 'Lunch',
                    'tags': ['vegetarian', 'vegan', 'healthy'],
                },
                {
                    'name': 'Artisan Ice Cream Parlor',
                    'description': (
                        'Handmade ice cream using local flavors and '
                        'seasonal fruits in {destination}. A sweet treat '
                        'on a warm afternoon.'
                    ),
                    'best_time': 'Afternoon',
                    'tags': ['dessert', 'artisan', 'sweet'],
                },
                {
                    'name': 'Historic Tea & Spice House',
                    'description': (
                        'A centuries-old tea house in {destination} '
                        'offering rare blends, local spices, and '
                        'traditional tasting ceremonies.'
                    ),
                    'best_time': 'Afternoon',
                    'tags': ['tea', 'spices', 'traditional'],
                },
                {
                    'name': 'Farm-to-Table Country Kitchen',
                    'description': (
                        'A rustic dining experience just outside '
                        '{destination} featuring seasonal menus sourced '
                        'from nearby farms and vineyards.'
                    ),
                    'best_time': 'Lunch',
                    'tags': ['farm-to-table', 'organic', 'countryside'],
                },
            ],
            'must_see': [
                {
                    'name': 'Sunset Viewpoint',
                    'description': (
                        'The most breathtaking sunset spot in {destination}. '
                        'Arrive early to secure a prime position and watch '
                        'the sky transform in vivid colors.'
                    ),
                    'best_time': 'Sunset',
                    'tags': ['sunset', 'photography', 'romantic'],
                },
                {
                    'name': 'Famous Bridge',
                    'description': (
                        'An iconic bridge in {destination} that is both '
                        'a feat of engineering and a beloved symbol of '
                        'the city, especially stunning when lit at night.'
                    ),
                    'best_time': 'Evening',
                    'tags': ['landmark', 'architecture', 'iconic'],
                },
                {
                    'name': 'Ancient Temple Complex',
                    'description': (
                        'A sprawling temple complex in {destination} '
                        'with intricate carvings, serene courtyards, '
                        'and centuries of spiritual significance.'
                    ),
                    'best_time': 'Morning',
                    'tags': ['temple', 'historic', 'spiritual'],
                },
                {
                    'name': 'Mountain Panorama Trail',
                    'description': (
                        'A moderate hiking trail near {destination} '
                        'rewarding you with spectacular mountain and '
                        'valley views at the summit.'
                    ),
                    'best_time': 'Morning',
                    'tags': ['hiking', 'nature', 'panorama'],
                },
                {
                    'name': 'Crystal Blue Lagoon',
                    'description': (
                        'A natural lagoon near {destination} with '
                        'impossibly clear turquoise water, perfect '
                        'for swimming and photography.'
                    ),
                    'best_time': 'Midday',
                    'tags': ['nature', 'swimming', 'scenic'],
                },
                {
                    'name': 'Colonial Architecture Walk',
                    'description': (
                        'A self-guided walk through the colonial-era '
                        'buildings of {destination}, showcasing ornate '
                        'facades, grand courtyards, and living history.'
                    ),
                    'best_time': 'Morning',
                    'tags': ['architecture', 'colonial', 'walking tour'],
                },
                {
                    'name': 'City Skyline at Night',
                    'description': (
                        'The glittering skyline of {destination} as seen '
                        'from across the river or a hilltop. A magical '
                        'sight after dark.'
                    ),
                    'best_time': 'Night',
                    'tags': ['skyline', 'night', 'photography'],
                },
                {
                    'name': 'Dramatic Coastline Cliffs',
                    'description': (
                        'Rugged sea cliffs near {destination} offering '
                        'dramatic ocean views and crashing waves. '
                        'A powerful reminder of nature at its finest.'
                    ),
                    'best_time': 'Afternoon',
                    'tags': ['coastline', 'nature', 'dramatic'],
                },
                {
                    'name': 'Flower & Garden Festival Grounds',
                    'description': (
                        'Beautifully landscaped grounds in {destination} '
                        'that host seasonal flower displays and garden '
                        'festivals throughout the year.'
                    ),
                    'best_time': 'Spring',
                    'tags': ['gardens', 'flowers', 'seasonal'],
                },
                {
                    'name': 'Stargazing Overlook',
                    'description': (
                        'A dark-sky location just outside {destination} '
                        'ideal for stargazing. On clear nights, the '
                        'Milky Way is visible to the naked eye.'
                    ),
                    'best_time': 'Night',
                    'tags': ['stargazing', 'nature', 'night sky'],
                },
            ],
            'must_do': [
                {
                    'name': 'Guided Walking Tour',
                    'description': (
                        'A comprehensive walking tour through the heart '
                        'of {destination} led by a knowledgeable local guide '
                        'covering history, culture, and hidden stories.'
                    ),
                    'best_time': 'Morning',
                    'tags': ['tour', 'walking', 'cultural'],
                },
                {
                    'name': 'Local Cooking Class',
                    'description': (
                        'Learn to prepare traditional dishes of {destination} '
                        'with a hands-on cooking class. Includes a market '
                        'visit and full meal.'
                    ),
                    'best_time': 'Morning',
                    'tags': ['cooking', 'food', 'experience'],
                },
                {
                    'name': 'River or Harbor Cruise',
                    'description': (
                        'See {destination} from the water on a scenic '
                        'boat cruise. Options range from budget ferries '
                        'to luxury sunset cruises.'
                    ),
                    'best_time': 'Sunset',
                    'tags': ['cruise', 'scenic', 'water'],
                },
                {
                    'name': 'Hot Air Balloon Ride',
                    'description': (
                        'Float above the landscapes surrounding '
                        '{destination} for an unforgettable bird-eye '
                        'perspective at dawn.'
                    ),
                    'best_time': 'Early morning',
                    'tags': ['adventure', 'aerial', 'bucket list'],
                },
                {
                    'name': 'Traditional Dance or Music Show',
                    'description': (
                        'An evening of traditional performance art in '
                        '{destination}, featuring authentic costumes, '
                        'music, and storytelling.'
                    ),
                    'best_time': 'Evening',
                    'tags': ['performance', 'culture', 'entertainment'],
                },
                {
                    'name': 'Cycling Tour of the Countryside',
                    'description': (
                        'Explore the scenic countryside around {destination} '
                        'on two wheels. Routes cater to all fitness levels '
                        'and include village stops.'
                    ),
                    'best_time': 'Morning',
                    'tags': ['cycling', 'countryside', 'active'],
                },
                {
                    'name': 'Spa & Wellness Retreat',
                    'description': (
                        'Relax and recharge at one of {destination}\'s '
                        'top spa facilities offering traditional and '
                        'modern wellness treatments.'
                    ),
                    'best_time': 'Any time',
                    'tags': ['spa', 'wellness', 'relaxation'],
                },
                {
                    'name': 'Local Craft Workshop',
                    'description': (
                        'Try your hand at a traditional craft of '
                        '{destination}, from pottery to textile weaving, '
                        'guided by skilled local artisans.'
                    ),
                    'best_time': 'Afternoon',
                    'tags': ['crafts', 'workshop', 'artisan'],
                },
                {
                    'name': 'Snorkeling or Diving Excursion',
                    'description': (
                        'Explore the underwater world near {destination} '
                        'with guided snorkeling or diving trips to vibrant '
                        'reefs and marine life.'
                    ),
                    'best_time': 'Morning',
                    'tags': ['snorkeling', 'diving', 'marine life'],
                },
                {
                    'name': 'Sunrise Yoga Session',
                    'description': (
                        'Start your day with a peaceful outdoor yoga '
                        'session at a scenic location in {destination}. '
                        'Open to all levels.'
                    ),
                    'best_time': 'Sunrise',
                    'tags': ['yoga', 'wellness', 'sunrise'],
                },
            ],
            'hidden_gem': [
                {
                    'name': 'Secret Garden Courtyard',
                    'description': (
                        'A hidden courtyard tucked behind a nondescript '
                        'doorway in {destination}, filled with flowers, '
                        'fountains, and absolute tranquility.'
                    ),
                    'best_time': 'Afternoon',
                    'tags': ['hidden', 'garden', 'peaceful'],
                },
                {
                    'name': 'Underground Jazz Bar',
                    'description': (
                        'A speakeasy-style jazz bar beneath the streets '
                        'of {destination}. Live music every night and '
                        'expertly crafted cocktails.'
                    ),
                    'best_time': 'Night',
                    'tags': ['jazz', 'nightlife', 'speakeasy'],
                },
                {
                    'name': 'Abandoned Railway Trail',
                    'description': (
                        'A converted railway line near {destination} '
                        'that is now a peaceful walking and cycling path '
                        'through wildflowers and old tunnels.'
                    ),
                    'best_time': 'Morning',
                    'tags': ['trail', 'nature', 'off-beaten-path'],
                },
                {
                    'name': 'Family-Run Hole-in-the-Wall Eatery',
                    'description': (
                        'A tiny, unmarked restaurant in {destination} '
                        'beloved by locals for its homestyle cooking '
                        'and incredibly low prices.'
                    ),
                    'best_time': 'Lunch',
                    'tags': ['local food', 'budget', 'authentic'],
                },
                {
                    'name': 'Quiet Hilltop Chapel',
                    'description': (
                        'A small chapel perched on a hill above '
                        '{destination} with stunning views and a '
                        'contemplative atmosphere.'
                    ),
                    'best_time': 'Morning',
                    'tags': ['chapel', 'views', 'quiet'],
                },
                {
                    'name': 'Artisan Bookshop & Cafe',
                    'description': (
                        'A quirky independent bookshop in {destination} '
                        'doubling as a cafe, hosting poetry readings '
                        'and cultural events.'
                    ),
                    'best_time': 'Afternoon',
                    'tags': ['bookshop', 'cafe', 'culture'],
                },
                {
                    'name': 'Hidden Waterfall',
                    'description': (
                        'A little-known waterfall a short hike from '
                        '{destination}. Rarely crowded, it offers a '
                        'refreshing natural swimming hole.'
                    ),
                    'best_time': 'Midday',
                    'tags': ['waterfall', 'nature', 'swimming'],
                },
                {
                    'name': 'Vintage Flea Market',
                    'description': (
                        'A weekend flea market in a side street of '
                        '{destination} where vendors sell antiques, '
                        'vinyl records, and handmade jewelry.'
                    ),
                    'best_time': 'Weekend morning',
                    'tags': ['market', 'vintage', 'shopping'],
                },
                {
                    'name': 'Rooftop Community Garden',
                    'description': (
                        'An urban community garden on a rooftop in '
                        '{destination} where locals grow herbs and '
                        'vegetables, with skyline views as a bonus.'
                    ),
                    'best_time': 'Afternoon',
                    'tags': ['rooftop', 'garden', 'community'],
                },
                {
                    'name': 'Sunset Fishing Pier',
                    'description': (
                        'A weathered wooden pier on the outskirts of '
                        '{destination} where local fishermen cast their '
                        'lines and the sunsets are unforgettable.'
                    ),
                    'best_time': 'Sunset',
                    'tags': ['pier', 'sunset', 'local life'],
                },
            ],
        }

        return templates.get(guide_type, templates['must_visit'])
