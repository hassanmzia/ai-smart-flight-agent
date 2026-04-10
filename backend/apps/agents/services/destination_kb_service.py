"""
Destination Knowledge Base Service
AI-powered destination knowledge generation, cultural info, user tips, and search.
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db.models import F, Q

logger = logging.getLogger(__name__)


class DestinationKBService:
    """Manage destination knowledge base with AI generation and deterministic fallbacks."""

    # ------------------------------------------------------------------ #
    #  1. Get or generate destination knowledge
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_or_generate_destination(destination_name: str, country: str = '') -> Dict[str, Any]:
        """
        Look up existing DestinationKnowledge or generate new one using AI.

        Increments views_count on every access.
        Returns the destination data as a dict including cultural_info and
        approved user_tips.
        """
        from apps.agents.models import DestinationKnowledge

        normalized = destination_name.strip().title()

        try:
            destination = DestinationKnowledge.objects.filter(
                destination__iexact=normalized,
            ).first()

            if destination:
                # Increment views atomically
                DestinationKnowledge.objects.filter(pk=destination.pk).update(
                    views_count=F('views_count') + 1,
                )
                destination.refresh_from_db()
                logger.info("Returning existing destination: %s", normalized)
                return DestinationKBService._destination_to_dict(destination)

            # Generate new destination via AI
            logger.info("Generating new destination knowledge for: %s", normalized)
            data = DestinationKBService._generate_destination_ai(normalized, country)

            destination = DestinationKnowledge.objects.create(
                destination=normalized,
                country=data.get('country', country or 'Unknown'),
                continent=data.get('continent', ''),
                summary=data.get('summary', ''),
                history=data.get('history', ''),
                culture=data.get('culture', ''),
                heritage_sites=data.get('heritage_sites', []),
                festivals=data.get('festivals', []),
                customs=data.get('customs', []),
                best_months=data.get('best_months', []),
                languages_spoken=data.get('languages_spoken', []),
                currency=data.get('currency', ''),
                timezone_info=data.get('timezone_info', ''),
                official_tourism_url=data.get('official_tourism_url', ''),
                emergency_numbers=data.get('emergency_numbers', {}),
                visa_info=data.get('visa_info', ''),
                ai_generated=True,
                views_count=1,
            )

            logger.info("Created destination knowledge for: %s (id=%s)", normalized, destination.pk)
            return DestinationKBService._destination_to_dict(destination)

        except Exception as e:
            logger.error("Error in get_or_generate_destination for %s: %s", normalized, e)
            return {
                'destination': normalized,
                'country': country or 'Unknown',
                'error': str(e),
            }

    @staticmethod
    def _generate_destination_ai(destination_name: str, country: str) -> Dict[str, Any]:
        """Generate structured destination data via AI with deterministic fallback."""
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            logger.info("No OpenAI API key available, using fallback for %s", destination_name)
            return DestinationKBService._destination_fallback(destination_name, country)

        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model='gpt-4o-mini',
                temperature=0.3,
                api_key=api_key,
                request_timeout=45,
            )

            prompt = (
                f"Generate comprehensive travel knowledge for {destination_name}"
                f"{', ' + country if country else ''}.\n\n"
                "Return JSON only, no markdown fences:\n"
                '{\n'
                '  "country": "<country name>",\n'
                '  "continent": "<continent>",\n'
                '  "summary": "<2-3 sentence overview>",\n'
                '  "history": "<brief history paragraph>",\n'
                '  "culture": "<cultural overview paragraph>",\n'
                '  "heritage_sites": [{"name": "<site>", "description": "<desc>", "type": "<UNESCO/National/Local>"}],\n'
                '  "festivals": [{"name": "<festival>", "month": "<month>", "description": "<desc>"}],\n'
                '  "customs": ["<custom1>", "<custom2>", "<custom3>"],\n'
                '  "best_months": ["<month1>", "<month2>"],\n'
                '  "languages_spoken": ["<lang1>", "<lang2>"],\n'
                '  "currency": "<currency code>",\n'
                '  "timezone_info": "<timezone>",\n'
                '  "official_tourism_url": "<url or empty>",\n'
                '  "emergency_numbers": {"police": "<number>", "ambulance": "<number>", "fire": "<number>"},\n'
                '  "visa_info": "<brief visa info for common nationalities>"\n'
                '}'
            )

            response = llm.invoke(prompt)
            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            data = json.loads(content)
            if isinstance(data, dict):
                logger.info("AI-generated destination data for %s", destination_name)
                return data
            logger.warning("AI returned non-dict for %s, using fallback", destination_name)
            return DestinationKBService._destination_fallback(destination_name, country)

        except Exception as e:
            logger.warning("OpenAI destination generation failed for %s: %s", destination_name, e)
            return DestinationKBService._destination_fallback(destination_name, country)

    @staticmethod
    def _destination_fallback(destination_name: str, country: str) -> Dict[str, Any]:
        """Create reasonable default content based on the destination name."""
        return {
            'country': country or 'Unknown',
            'continent': '',
            'summary': (
                f"{destination_name} is a fascinating destination known for its unique blend "
                f"of history, culture, and modern attractions. Visitors can explore local "
                f"landmarks, sample regional cuisine, and immerse themselves in the local way of life."
            ),
            'history': (
                f"{destination_name} is a historic city with rich cultural heritage spanning "
                f"centuries. Its storied past has shaped the architecture, traditions, and "
                f"character that travelers experience today."
            ),
            'culture': (
                f"The culture of {destination_name} reflects a vibrant mix of traditions, arts, "
                f"and community life. Locals take pride in their customs, cuisine, and hospitality."
            ),
            'heritage_sites': [
                {
                    'name': f'{destination_name} Historic Center',
                    'description': f'The preserved historic core of {destination_name} with traditional architecture.',
                    'type': 'Local',
                },
            ],
            'festivals': [
                {
                    'name': 'Local Festival',
                    'month': 'Various',
                    'description': f'Traditional celebration showcasing the culture and heritage of {destination_name}.',
                },
                {
                    'name': 'New Year Celebration',
                    'month': 'January',
                    'description': f'Annual new year festivities in {destination_name} with fireworks and cultural performances.',
                },
            ],
            'customs': [
                'Respect local customs and traditions',
                'Learn basic greetings in the local language',
                'Dress modestly when visiting religious sites',
                'Ask permission before photographing locals',
            ],
            'best_months': ['March', 'April', 'May', 'September', 'October'],
            'languages_spoken': ['Local language', 'English (tourist areas)'],
            'currency': '',
            'timezone_info': '',
            'official_tourism_url': '',
            'emergency_numbers': {
                'police': '112',
                'ambulance': '112',
                'fire': '112',
            },
            'visa_info': (
                f'Visa requirements for {destination_name} vary by nationality. '
                f'Check with the local embassy or consulate for the most up-to-date information.'
            ),
        }

    @staticmethod
    def _destination_to_dict(destination) -> Dict[str, Any]:
        """Serialize a DestinationKnowledge instance to dict with related data."""
        cultural_info = [
            {
                'id': ci.pk,
                'category': ci.category,
                'title': ci.title,
                'content': ci.content,
                'severity': ci.severity,
                'ai_generated': ci.ai_generated,
            }
            for ci in destination.cultural_info.all()
        ]

        user_tips = [
            {
                'id': tip.pk,
                'title': tip.title,
                'content': tip.content,
                'category': tip.category,
                'upvotes': tip.upvotes,
                'downvotes': tip.downvotes,
                'created_at': tip.created_at.isoformat() if tip.created_at else None,
            }
            for tip in destination.user_tips.filter(status='approved')
        ]

        return {
            'id': destination.pk,
            'destination': destination.destination,
            'country': destination.country,
            'continent': destination.continent,
            'summary': destination.summary,
            'history': destination.history,
            'culture': destination.culture,
            'heritage_sites': destination.heritage_sites,
            'festivals': destination.festivals,
            'customs': destination.customs,
            'best_months': destination.best_months,
            'languages_spoken': destination.languages_spoken,
            'currency': destination.currency,
            'timezone_info': destination.timezone_info,
            'official_tourism_url': destination.official_tourism_url,
            'emergency_numbers': destination.emergency_numbers,
            'visa_info': destination.visa_info,
            'ai_generated': destination.ai_generated,
            'views_count': destination.views_count,
            'created_at': destination.created_at.isoformat() if destination.created_at else None,
            'updated_at': destination.updated_at.isoformat() if destination.updated_at else None,
            'cultural_info': cultural_info,
            'user_tips': user_tips,
        }

    # ------------------------------------------------------------------ #
    #  2. Generate cultural info
    # ------------------------------------------------------------------ #

    @staticmethod
    def generate_cultural_info(destination_id: int) -> List[Dict[str, Any]]:
        """
        Generate cultural info entries for a destination using AI.

        Creates CulturalInfo records for categories: dress_code, tipping,
        greetings, dining, religious, photography, laws, taboos.
        Returns list of cultural info dicts.
        """
        from apps.agents.models import CulturalInfo, DestinationKnowledge

        try:
            destination = DestinationKnowledge.objects.get(pk=destination_id)
        except DestinationKnowledge.DoesNotExist:
            logger.error("Destination with id %s not found", destination_id)
            return []

        # If cultural info already exists, return it
        existing = destination.cultural_info.all()
        if existing.count() >= 8:
            logger.info("Cultural info already exists for %s", destination.destination)
            return [
                {
                    'id': ci.pk,
                    'category': ci.category,
                    'title': ci.title,
                    'content': ci.content,
                    'severity': ci.severity,
                    'ai_generated': ci.ai_generated,
                }
                for ci in existing
            ]

        categories = [
            'dress_code', 'tipping', 'greetings', 'dining',
            'religious', 'photography', 'laws', 'taboos',
        ]

        cultural_data = DestinationKBService._generate_cultural_info_ai(
            destination.destination, categories,
        )

        results = []
        for category in categories:
            entry = cultural_data.get(category, {})
            title = entry.get('title', f'{category.replace("_", " ").title()} in {destination.destination}')
            content = entry.get('content', f'General {category.replace("_", " ")} guidelines for {destination.destination}.')
            severity = entry.get('severity', 'advisory')
            if severity not in ('info', 'advisory', 'important', 'critical'):
                severity = 'advisory'

            try:
                ci = CulturalInfo.objects.create(
                    destination=destination,
                    category=category,
                    title=title,
                    content=content,
                    severity=severity,
                    ai_generated=True,
                )
                results.append({
                    'id': ci.pk,
                    'category': ci.category,
                    'title': ci.title,
                    'content': ci.content,
                    'severity': ci.severity,
                    'ai_generated': ci.ai_generated,
                })
            except Exception as e:
                logger.error("Failed to create CulturalInfo for %s/%s: %s", destination.destination, category, e)

        logger.info("Generated %d cultural info entries for %s", len(results), destination.destination)
        return results

    @staticmethod
    def _generate_cultural_info_ai(destination_name: str, categories: List[str]) -> Dict[str, Any]:
        """Generate cultural info via AI with deterministic fallback."""
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return DestinationKBService._cultural_info_fallback(destination_name)

        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model='gpt-4o-mini',
                temperature=0.3,
                api_key=api_key,
                request_timeout=45,
            )

            categories_str = ', '.join(categories)
            prompt = (
                f"Generate cultural etiquette info for {destination_name} "
                f"covering these categories: {categories_str}.\n\n"
                "Return JSON only, no markdown fences. Each category key maps to an object:\n"
                '{\n'
                '  "<category>": {\n'
                '    "title": "<descriptive title>",\n'
                '    "content": "<detailed 2-3 sentence guidance>",\n'
                '    "severity": "<one of: info, advisory, important, critical>"\n'
                '  }\n'
                '}\n\n'
                'Use "info" for general knowledge, "advisory" for standard guidance, '
                '"important" for things that could cause offense, "critical" for '
                'things that could lead to legal trouble or safety issues.'
            )

            response = llm.invoke(prompt)
            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            data = json.loads(content)
            if isinstance(data, dict):
                logger.info("AI-generated cultural info for %s", destination_name)
                return data
            return DestinationKBService._cultural_info_fallback(destination_name)

        except Exception as e:
            logger.warning("OpenAI cultural info generation failed for %s: %s", destination_name, e)
            return DestinationKBService._cultural_info_fallback(destination_name)

    @staticmethod
    def _cultural_info_fallback(destination_name: str) -> Dict[str, Any]:
        """Deterministic fallback cultural info for any destination."""
        return {
            'dress_code': {
                'title': f'Dress Code in {destination_name}',
                'content': (
                    f'Dress modestly when visiting religious sites and traditional areas in {destination_name}. '
                    f'Cover shoulders and knees in places of worship. Smart casual is appropriate for most restaurants and attractions.'
                ),
                'severity': 'advisory',
            },
            'tipping': {
                'title': f'Tipping Etiquette in {destination_name}',
                'content': (
                    f'Tipping customs vary in {destination_name}. A 10-15% tip is generally appreciated in restaurants '
                    f'if service charge is not included. Rounding up taxi fares is a common courtesy.'
                ),
                'severity': 'info',
            },
            'greetings': {
                'title': f'Greetings and Gestures in {destination_name}',
                'content': (
                    f'A warm smile and polite greeting go a long way in {destination_name}. '
                    f'Learn the local word for "hello" and "thank you." A handshake is generally acceptable '
                    f'in formal settings.'
                ),
                'severity': 'info',
            },
            'dining': {
                'title': f'Dining Etiquette in {destination_name}',
                'content': (
                    f'Follow the lead of locals when dining in {destination_name}. Wait to be seated at restaurants, '
                    f'and do not begin eating until the host or eldest person starts. Complimenting the food is appreciated.'
                ),
                'severity': 'info',
            },
            'religious': {
                'title': f'Religious Customs in {destination_name}',
                'content': (
                    f'Respect religious practices in {destination_name}. Remove shoes before entering places of worship. '
                    f'Dress modestly and speak softly in sacred spaces. Ask before participating in religious ceremonies.'
                ),
                'severity': 'important',
            },
            'photography': {
                'title': f'Photography Rules in {destination_name}',
                'content': (
                    f'Always ask permission before photographing people in {destination_name}. '
                    f'Photography may be prohibited in religious sites, military areas, and some government buildings. '
                    f'Respect "no photography" signs.'
                ),
                'severity': 'advisory',
            },
            'laws': {
                'title': f'Local Laws in {destination_name}',
                'content': (
                    f'Familiarize yourself with local laws before visiting {destination_name}. '
                    f'Drug offenses are treated severely in most countries. Carry identification at all times '
                    f'and respect local regulations on alcohol consumption and public behavior.'
                ),
                'severity': 'critical',
            },
            'taboos': {
                'title': f'Cultural Taboos in {destination_name}',
                'content': (
                    f'Avoid discussing sensitive political or religious topics with strangers in {destination_name}. '
                    f'Public displays of affection may be frowned upon in conservative areas. '
                    f'Do not point at people or religious objects with your finger.'
                ),
                'severity': 'important',
            },
        }

    # ------------------------------------------------------------------ #
    #  3. Submit user tip
    # ------------------------------------------------------------------ #

    @staticmethod
    def submit_user_tip(user, destination_id: int, data: dict) -> Dict[str, Any]:
        """
        Submit a user tip with AI moderation.

        AI scores the tip 0-1:
        - score > 0.7 -> auto-approved
        - score < 0.3 -> auto-rejected
        - otherwise   -> pending manual review

        On AI failure, score defaults to 0.5 with pending status.
        Returns the tip data as a dict.
        """
        from apps.agents.models import DestinationKnowledge, UserDestinationTip

        try:
            destination = DestinationKnowledge.objects.get(pk=destination_id)
        except DestinationKnowledge.DoesNotExist:
            logger.error("Destination with id %s not found for tip submission", destination_id)
            return {'error': 'Destination not found'}

        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        category = data.get('category', '').strip()

        if not title or not content:
            return {'error': 'Title and content are required'}

        # AI moderation
        moderation = DestinationKBService._moderate_tip_ai(title, content, destination.destination)
        score = moderation.get('score', 0.5)
        notes = moderation.get('notes', '')

        if score > 0.7:
            status = 'approved'
        elif score < 0.3:
            status = 'rejected'
        else:
            status = 'pending'

        try:
            tip = UserDestinationTip.objects.create(
                user=user,
                destination=destination,
                title=title,
                content=content,
                category=category,
                status=status,
                ai_moderation_score=score,
                ai_moderation_notes=notes,
            )

            logger.info(
                "User tip submitted for %s: status=%s, score=%.2f",
                destination.destination, status, score,
            )

            return {
                'id': tip.pk,
                'title': tip.title,
                'content': tip.content,
                'category': tip.category,
                'status': tip.status,
                'ai_moderation_score': tip.ai_moderation_score,
                'ai_moderation_notes': tip.ai_moderation_notes,
                'created_at': tip.created_at.isoformat() if tip.created_at else None,
            }

        except Exception as e:
            logger.error("Failed to create user tip: %s", e)
            return {'error': str(e)}

    @staticmethod
    def _moderate_tip_ai(title: str, content: str, destination_name: str) -> Dict[str, Any]:
        """Use AI to moderate a user tip. Falls back to neutral score on failure."""
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return {'score': 0.5, 'notes': 'AI moderation unavailable; queued for manual review.'}

        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model='gpt-4o-mini',
                temperature=0.1,
                api_key=api_key,
                request_timeout=30,
            )

            prompt = (
                f'Moderate this user-submitted travel tip for {destination_name}.\n\n'
                f'Title: {title}\n'
                f'Content: {content}\n\n'
                'Evaluate for: relevance to the destination, helpfulness, accuracy, '
                'absence of spam/offensive content, and overall quality.\n\n'
                'Return JSON only, no markdown fences:\n'
                '{"score": <float 0-1>, "notes": "<brief moderation notes>"}\n\n'
                'Score guide: 0.0 = spam/offensive, 0.5 = mediocre, 1.0 = excellent and helpful.'
            )

            response = llm.invoke(prompt)
            response_content = response.content.strip()
            if response_content.startswith('```'):
                response_content = response_content.split('\n', 1)[1].rsplit('```', 1)[0]
            data = json.loads(response_content)

            score = float(data.get('score', 0.5))
            score = max(0.0, min(1.0, score))
            notes = str(data.get('notes', ''))

            logger.info("AI moderation for tip '%s': score=%.2f", title, score)
            return {'score': score, 'notes': notes}

        except Exception as e:
            logger.warning("AI moderation failed for tip '%s': %s", title, e)
            return {'score': 0.5, 'notes': 'AI moderation failed; queued for manual review.'}

    # ------------------------------------------------------------------ #
    #  4. Vote on a tip
    # ------------------------------------------------------------------ #

    @staticmethod
    def vote_tip(user, tip_id: int, vote: str) -> Dict[str, Any]:
        """
        Upvote or downvote a user tip.

        Args:
            user: The user casting the vote.
            tip_id: The UserDestinationTip primary key.
            vote: Either 'upvote' or 'downvote'.

        Returns updated vote counts.
        """
        from apps.agents.models import UserDestinationTip

        if vote not in ('upvote', 'downvote'):
            return {'error': 'Vote must be "upvote" or "downvote"'}

        try:
            tip = UserDestinationTip.objects.get(pk=tip_id)
        except UserDestinationTip.DoesNotExist:
            logger.error("Tip with id %s not found for voting", tip_id)
            return {'error': 'Tip not found'}

        if vote == 'upvote':
            UserDestinationTip.objects.filter(pk=tip.pk).update(
                upvotes=F('upvotes') + 1,
            )
        else:
            UserDestinationTip.objects.filter(pk=tip.pk).update(
                downvotes=F('downvotes') + 1,
            )

        tip.refresh_from_db()

        logger.info("User voted '%s' on tip %s", vote, tip_id)
        return {
            'id': tip.pk,
            'title': tip.title,
            'upvotes': tip.upvotes,
            'downvotes': tip.downvotes,
        }

    # ------------------------------------------------------------------ #
    #  5. Search destinations
    # ------------------------------------------------------------------ #

    @staticmethod
    def search_destinations(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search destinations by name, country, or continent.

        Returns list of matching destinations with basic info.
        """
        from apps.agents.models import DestinationKnowledge

        if not query or not query.strip():
            return []

        query = query.strip()

        try:
            results = DestinationKnowledge.objects.filter(
                Q(destination__icontains=query)
                | Q(country__icontains=query)
                | Q(continent__icontains=query)
            ).order_by('-views_count')[:limit]

            destinations = [
                {
                    'id': dest.pk,
                    'destination': dest.destination,
                    'country': dest.country,
                    'continent': dest.continent,
                    'summary': dest.summary,
                    'views_count': dest.views_count,
                    'best_months': dest.best_months,
                    'currency': dest.currency,
                }
                for dest in results
            ]

            logger.info("Search for '%s' returned %d results", query, len(destinations))
            return destinations

        except Exception as e:
            logger.error("Search failed for query '%s': %s", query, e)
            return []

    # ------------------------------------------------------------------ #
    #  6. Get festivals
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_festivals(destination_name: str) -> List[Dict[str, Any]]:
        """
        Get festivals for a destination.

        If destination exists in the knowledge base, return its festivals.
        Otherwise generate via AI with fallback.
        """
        from apps.agents.models import DestinationKnowledge

        normalized = destination_name.strip().title()

        try:
            destination = DestinationKnowledge.objects.filter(
                destination__iexact=normalized,
            ).first()

            if destination and destination.festivals:
                logger.info("Returning existing festivals for %s", normalized)
                return destination.festivals

        except Exception as e:
            logger.warning("DB lookup failed for festivals in %s: %s", normalized, e)

        # Generate festivals via AI with fallback
        logger.info("Generating festivals for %s", normalized)
        return DestinationKBService._generate_festivals_ai(normalized)

    @staticmethod
    def _generate_festivals_ai(destination_name: str) -> List[Dict[str, Any]]:
        """Generate festival data via AI with deterministic fallback."""
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return DestinationKBService._festivals_fallback(destination_name)

        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model='gpt-4o-mini',
                temperature=0.3,
                api_key=api_key,
                request_timeout=30,
            )

            prompt = (
                f"List the major festivals and celebrations in {destination_name}.\n\n"
                "Return JSON only, no markdown fences. Return an array of objects:\n"
                '[{"name": "<festival name>", "month": "<month or date range>", '
                '"description": "<1-2 sentence description>"}]\n\n'
                "Include at least 5 festivals."
            )

            response = llm.invoke(prompt)
            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            data = json.loads(content)
            if isinstance(data, list):
                logger.info("AI-generated %d festivals for %s", len(data), destination_name)
                return data
            return DestinationKBService._festivals_fallback(destination_name)

        except Exception as e:
            logger.warning("OpenAI festivals generation failed for %s: %s", destination_name, e)
            return DestinationKBService._festivals_fallback(destination_name)

    @staticmethod
    def _festivals_fallback(destination_name: str) -> List[Dict[str, Any]]:
        """Deterministic fallback festival data."""
        return [
            {
                'name': 'Local Festival',
                'month': 'Various',
                'description': f'Traditional celebration showcasing the culture and heritage of {destination_name}.',
            },
            {
                'name': 'New Year Celebration',
                'month': 'January',
                'description': f'Annual new year festivities in {destination_name} with fireworks and cultural performances.',
            },
            {
                'name': 'Harvest Festival',
                'month': 'September',
                'description': f'A seasonal celebration of the local harvest with food, music, and community gatherings in {destination_name}.',
            },
            {
                'name': 'Music and Arts Festival',
                'month': 'June',
                'description': f'A vibrant festival celebrating local and international music, dance, and visual arts in {destination_name}.',
            },
            {
                'name': 'National Day Celebration',
                'month': 'Various',
                'description': f'Patriotic celebration with parades, concerts, and public festivities in {destination_name}.',
            },
        ]

    # ------------------------------------------------------------------ #
    #  7. Get etiquette summary
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_etiquette_summary(destination_name: str) -> Dict[str, Any]:
        """
        Get a quick etiquette summary combining key cultural info.

        Returns structured dict with do's and don'ts.
        """
        from apps.agents.models import DestinationKnowledge

        normalized = destination_name.strip().title()

        # Try to build from existing cultural info
        try:
            destination = DestinationKnowledge.objects.filter(
                destination__iexact=normalized,
            ).first()

            if destination:
                cultural_entries = destination.cultural_info.all()
                if cultural_entries.exists():
                    logger.info("Building etiquette summary from DB for %s", normalized)
                    return DestinationKBService._build_etiquette_from_cultural_info(
                        normalized, cultural_entries,
                    )
        except Exception as e:
            logger.warning("DB lookup failed for etiquette summary for %s: %s", normalized, e)

        # Generate via AI with fallback
        logger.info("Generating etiquette summary for %s via AI", normalized)
        return DestinationKBService._generate_etiquette_ai(normalized)

    @staticmethod
    def _build_etiquette_from_cultural_info(destination_name: str, cultural_entries) -> Dict[str, Any]:
        """Build an etiquette summary from existing CulturalInfo records."""
        dos = []
        donts = []
        key_info = {}

        for entry in cultural_entries:
            key_info[entry.category] = entry.content

            # Extract actionable items from content
            if entry.category == 'greetings':
                dos.append(f'Learn local greetings: {entry.content[:100]}')
            elif entry.category == 'dress_code':
                dos.append('Follow local dress code guidelines')
            elif entry.category == 'tipping':
                dos.append(f'Follow tipping customs: {entry.content[:100]}')
            elif entry.category == 'dining':
                dos.append('Observe local dining etiquette')
            elif entry.category == 'religious':
                dos.append('Respect religious customs and sites')
            elif entry.category == 'taboos':
                donts.append(f'Avoid cultural taboos: {entry.content[:100]}')
            elif entry.category == 'photography':
                donts.append('Do not photograph without permission where restricted')
            elif entry.category == 'laws':
                donts.append('Do not violate local laws and regulations')

        return {
            'destination': destination_name,
            'dos': dos or ['Respect local customs', 'Learn basic greetings', 'Dress modestly at religious sites'],
            'donts': donts or ['Do not photograph without permission', 'Avoid discussing sensitive topics'],
            'key_info': key_info,
        }

    @staticmethod
    def _generate_etiquette_ai(destination_name: str) -> Dict[str, Any]:
        """Generate etiquette summary via AI with deterministic fallback."""
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            return DestinationKBService._etiquette_fallback(destination_name)

        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model='gpt-4o-mini',
                temperature=0.3,
                api_key=api_key,
                request_timeout=30,
            )

            prompt = (
                f"Provide a quick etiquette summary for visitors to {destination_name}.\n\n"
                "Return JSON only, no markdown fences:\n"
                '{\n'
                '  "destination": "<destination>",\n'
                '  "dos": ["<do 1>", "<do 2>", "<do 3>", "<do 4>", "<do 5>"],\n'
                '  "donts": ["<dont 1>", "<dont 2>", "<dont 3>", "<dont 4>", "<dont 5>"],\n'
                '  "key_info": {\n'
                '    "greeting": "<how to greet>",\n'
                '    "tipping": "<tipping guidance>",\n'
                '    "dress_code": "<dress guidance>",\n'
                '    "dining": "<dining tips>"\n'
                '  }\n'
                '}'
            )

            response = llm.invoke(prompt)
            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            data = json.loads(content)
            if isinstance(data, dict):
                logger.info("AI-generated etiquette summary for %s", destination_name)
                return data
            return DestinationKBService._etiquette_fallback(destination_name)

        except Exception as e:
            logger.warning("OpenAI etiquette summary failed for %s: %s", destination_name, e)
            return DestinationKBService._etiquette_fallback(destination_name)

    @staticmethod
    def _etiquette_fallback(destination_name: str) -> Dict[str, Any]:
        """Deterministic fallback etiquette summary."""
        return {
            'destination': destination_name,
            'dos': [
                f'Learn basic greetings in the local language of {destination_name}',
                'Dress modestly when visiting religious or traditional sites',
                'Respect local customs and traditions',
                'Tip appropriately based on local conventions',
                'Ask permission before photographing locals',
            ],
            'donts': [
                'Do not disrespect local religious practices or sacred sites',
                'Avoid discussing sensitive political topics with strangers',
                'Do not photograph military, police, or government buildings',
                'Avoid public displays of affection in conservative areas',
                'Do not litter or damage natural or cultural sites',
            ],
            'key_info': {
                'greeting': f'A polite smile and local greeting go a long way in {destination_name}.',
                'tipping': 'Check local customs; 10-15% is a safe default in most restaurants.',
                'dress_code': 'Dress modestly at religious sites. Smart casual is usually appropriate elsewhere.',
                'dining': 'Follow the lead of locals. Wait for the host to begin eating.',
            },
        }
