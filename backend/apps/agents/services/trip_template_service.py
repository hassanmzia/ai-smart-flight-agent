"""
Trip Template Service
AI-powered trip template creation, browsing, cloning, and community features.
"""
import json
import logging
import os
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db.models import F

logger = logging.getLogger(__name__)


class TripTemplateService:
    """Manage cloneable trip templates with AI generation and community features."""

    # ------------------------------------------------------------------ #
    #  1. Create template from user data
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_template(user, data: dict) -> Dict[str, Any]:
        """
        Create a TripTemplate from user-supplied data.

        Required fields: title, destination, duration_days.
        Optional: description, style, estimated_budget, itinerary_data, tags,
                  highlights, cover_image_url, country.

        Returns
        -------
        dict with 'success' key and template data or error.
        """
        from apps.agents.models import TripTemplate

        try:
            required_fields = ['title', 'destination', 'duration_days']
            missing = [f for f in required_fields if not data.get(f)]
            if missing:
                return {
                    'success': False,
                    'error': f"Missing required fields: {', '.join(missing)}",
                }

            template = TripTemplate.objects.create(
                creator=user,
                title=data['title'],
                description=data.get('description', ''),
                destination=data['destination'],
                country=data.get('country', ''),
                duration_days=int(data['duration_days']),
                style=data.get('style', 'adventure'),
                estimated_budget=Decimal(str(data.get('estimated_budget', 0))),
                currency=data.get('currency', 'USD'),
                cover_image_url=data.get('cover_image_url', ''),
                itinerary_data=data.get('itinerary_data', []),
                tags=data.get('tags', []),
                highlights=data.get('highlights', []),
            )

            logger.info(
                "Created trip template '%s' for user %s (id=%s)",
                template.title, user, template.id,
            )

            return {
                'success': True,
                'template': TripTemplateService._template_to_dict(template),
            }
        except Exception as e:
            logger.error("Failed to create trip template: %s", e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  2. AI-generated template
    # ------------------------------------------------------------------ #

    @staticmethod
    def generate_template_from_ai(
        user,
        destination: str,
        duration_days: int,
        style: str = 'adventure',
        budget: float = 0,
    ) -> Dict[str, Any]:
        """
        Use AI to generate a complete trip template with itinerary data.

        Each day receives 3-5 activities with time, title, description,
        category, and cost. On AI failure a deterministic fallback is used.

        Returns
        -------
        dict with 'success' key and the created template data or error.
        """
        from apps.agents.models import TripTemplate

        try:
            ai_data = TripTemplateService._generate_itinerary_ai(
                destination, duration_days, style, budget,
            )

            itinerary_data = ai_data.get('itinerary_data', [])
            description = ai_data.get(
                'description',
                f"A {duration_days}-day {style} trip to {destination}.",
            )
            tags = ai_data.get('tags', [style, destination.lower(), 'ai-generated'])
            highlights = ai_data.get('highlights', [
                f"Explore the best of {destination}",
                f"{style.title()} experiences curated by AI",
                f"{duration_days} days of adventure",
            ])
            estimated_budget = Decimal(str(
                ai_data.get('estimated_budget', budget or 0)
            ))
            country = ai_data.get('country', '')

            template = TripTemplate.objects.create(
                creator=user,
                title=ai_data.get('title', f"{style.title()} Trip to {destination}"),
                description=description,
                destination=destination,
                country=country,
                duration_days=duration_days,
                style=style,
                estimated_budget=estimated_budget,
                currency=ai_data.get('currency', 'USD'),
                itinerary_data=itinerary_data,
                tags=tags,
                highlights=highlights,
            )

            logger.info(
                "AI-generated trip template '%s' for user %s (id=%s)",
                template.title, user, template.id,
            )

            return {
                'success': True,
                'template': TripTemplateService._template_to_dict(template),
            }
        except Exception as e:
            logger.error("Failed to generate AI trip template: %s", e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _generate_itinerary_ai(
        destination: str,
        duration_days: int,
        style: str,
        budget: float,
    ) -> Dict[str, Any]:
        """Generate itinerary via AI with deterministic fallback."""
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            logger.info("No OpenAI API key available, using fallback for %s", destination)
            return TripTemplateService._itinerary_fallback(
                destination, duration_days, style, budget,
            )

        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model='gpt-4o-mini',
                temperature=0.3,
                api_key=api_key,
                request_timeout=45,
            )

            prompt = (
                f"Create a detailed {duration_days}-day {style} trip itinerary for "
                f"{destination}"
                f"{' with budget ~$' + str(int(budget)) if budget else ''}.\n\n"
                "Return JSON only, no markdown fences:\n"
                '{\n'
                '  "title": "<catchy trip title>",\n'
                '  "description": "<2-3 sentence trip overview>",\n'
                '  "country": "<country name>",\n'
                '  "currency": "<3-letter currency code>",\n'
                '  "estimated_budget": <total numeric budget>,\n'
                '  "tags": ["<tag1>", "<tag2>", "<tag3>"],\n'
                '  "highlights": ["<highlight1>", "<highlight2>", "<highlight3>"],\n'
                '  "itinerary_data": [\n'
                '    {\n'
                '      "day": 1,\n'
                '      "activities": [\n'
                '        {\n'
                '          "time": "09:00",\n'
                '          "title": "<activity title>",\n'
                '          "description": "<1-2 sentence description>",\n'
                '          "category": "<sightseeing|food|adventure|culture|relaxation|transport|shopping>",\n'
                '          "cost": <numeric cost>\n'
                '        }\n'
                '      ]\n'
                '    }\n'
                '  ]\n'
                '}\n\n'
                f"Each day should have 3-5 activities. Style: {style}."
            )

            response = llm.invoke(prompt)
            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            data = json.loads(content)
            if isinstance(data, dict) and 'itinerary_data' in data:
                logger.info("AI-generated itinerary for %s (%d days)", destination, duration_days)
                return data
            logger.warning("AI returned unexpected format for %s, using fallback", destination)
            return TripTemplateService._itinerary_fallback(
                destination, duration_days, style, budget,
            )

        except Exception as e:
            logger.warning(
                "OpenAI itinerary generation failed for %s: %s", destination, e,
            )
            return TripTemplateService._itinerary_fallback(
                destination, duration_days, style, budget,
            )

    @staticmethod
    def _itinerary_fallback(
        destination: str,
        duration_days: int,
        style: str,
        budget: float,
    ) -> Dict[str, Any]:
        """Deterministic fallback itinerary with generic activities."""
        daily_budget = round(budget / duration_days, 2) if budget and duration_days else 0

        itinerary_data = []
        for day_num in range(1, duration_days + 1):
            activities = [
                {
                    'time': '09:00',
                    'title': f'Explore local landmarks - Day {day_num}',
                    'description': (
                        f'Morning exploration of popular landmarks and attractions '
                        f'in {destination}.'
                    ),
                    'category': 'sightseeing',
                    'cost': round(daily_budget * 0.3, 2) if daily_budget else 0,
                },
                {
                    'time': '12:30',
                    'title': f'Local cuisine experience - Day {day_num}',
                    'description': (
                        f'Afternoon lunch featuring local dishes and regional '
                        f'specialties of {destination}.'
                    ),
                    'category': 'food',
                    'cost': round(daily_budget * 0.3, 2) if daily_budget else 0,
                },
                {
                    'time': '18:00',
                    'title': f'Cultural experience - Day {day_num}',
                    'description': (
                        f'Evening cultural activity such as traditional performances, '
                        f'night markets, or local entertainment in {destination}.'
                    ),
                    'category': 'culture',
                    'cost': round(daily_budget * 0.4, 2) if daily_budget else 0,
                },
            ]
            itinerary_data.append({
                'day': day_num,
                'activities': activities,
            })

        return {
            'title': f"{style.title()} Trip to {destination}",
            'description': (
                f"A {duration_days}-day {style} trip to {destination}. "
                f"Explore landmarks, savor local cuisine, and immerse yourself "
                f"in the culture."
            ),
            'country': '',
            'currency': 'USD',
            'estimated_budget': budget or 0,
            'tags': [style, destination.lower(), 'ai-generated'],
            'highlights': [
                f"Explore the best of {destination}",
                f"{style.title()} experiences curated for you",
                f"{duration_days} days of unforgettable travel",
            ],
            'itinerary_data': itinerary_data,
        }

    # ------------------------------------------------------------------ #
    #  3. Browse / search templates
    # ------------------------------------------------------------------ #

    @staticmethod
    def browse_templates(
        destination: str = None,
        style: str = None,
        min_budget: float = None,
        max_budget: float = None,
        sort_by: str = 'popular',
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Browse and search trip templates with filters and sorting.

        Sort options: popular, newest, rating, budget_low.

        Returns
        -------
        dict with 'success' key and list of template dicts with creator name.
        """
        from apps.agents.models import TripTemplate

        try:
            qs = TripTemplate.objects.select_related('creator').all()

            # Filters
            if destination:
                qs = qs.filter(destination__icontains=destination)

            if style:
                qs = qs.filter(style=style)

            if min_budget is not None:
                qs = qs.filter(estimated_budget__gte=Decimal(str(min_budget)))

            if max_budget is not None:
                qs = qs.filter(estimated_budget__lte=Decimal(str(max_budget)))

            # Sorting
            sort_map = {
                'popular': '-clone_count',
                'newest': '-created_at',
                'rating': '-rating',
                'budget_low': 'estimated_budget',
            }
            order_field = sort_map.get(sort_by, '-clone_count')
            qs = qs.order_by(order_field)

            templates = []
            for t in qs[:limit]:
                template_dict = TripTemplateService._template_to_dict(t)
                template_dict['creator_name'] = TripTemplateService._get_display_name(t.creator)
                templates.append(template_dict)

            logger.info(
                "Browse templates: destination=%s, style=%s, sort=%s — returned %d results",
                destination, style, sort_by, len(templates),
            )

            return {
                'success': True,
                'templates': templates,
                'count': len(templates),
            }
        except Exception as e:
            logger.error("Failed to browse templates: %s", e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  4. Get template details
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_template(template_id: int) -> Dict[str, Any]:
        """
        Get full template details and increment views_count atomically.

        Returns
        -------
        dict with 'success' key and template data including creator info.
        """
        from apps.agents.models import TripTemplate

        try:
            try:
                template = TripTemplate.objects.select_related('creator').get(id=template_id)
            except TripTemplate.DoesNotExist:
                return {'success': False, 'error': f'Template with id {template_id} not found'}

            # Increment views atomically
            TripTemplate.objects.filter(pk=template.pk).update(
                views_count=F('views_count') + 1,
            )
            template.refresh_from_db()

            template_data = TripTemplateService._template_to_dict(template)
            template_data['creator_name'] = TripTemplateService._get_display_name(template.creator)

            logger.info("Retrieved template '%s' (id=%s)", template.title, template_id)

            return {
                'success': True,
                'template': template_data,
            }
        except Exception as e:
            logger.error("Failed to get template %s: %s", template_id, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  5. Clone template
    # ------------------------------------------------------------------ #

    @staticmethod
    def clone_template(user, template_id: int, customizations: dict = None) -> Dict[str, Any]:
        """
        Clone a trip template for the user.

        Increments the original template's clone_count atomically and creates
        a TemplateClone record.

        Returns
        -------
        dict with 'success' key and clone data or error.
        """
        from apps.agents.models import TemplateClone, TripTemplate

        try:
            try:
                template = TripTemplate.objects.get(id=template_id)
            except TripTemplate.DoesNotExist:
                return {'success': False, 'error': f'Template with id {template_id} not found'}

            # Increment clone count atomically
            TripTemplate.objects.filter(pk=template.pk).update(
                clone_count=F('clone_count') + 1,
            )
            template.refresh_from_db()

            clone = TemplateClone.objects.create(
                user=user,
                template=template,
                customizations=customizations or {},
            )

            logger.info(
                "User %s cloned template '%s' (id=%s, clone_id=%s)",
                user, template.title, template_id, clone.id,
            )

            return {
                'success': True,
                'clone': {
                    'id': clone.id,
                    'template_id': template.id,
                    'template_title': template.title,
                    'destination': template.destination,
                    'duration_days': template.duration_days,
                    'style': template.style,
                    'itinerary_data': template.itinerary_data,
                    'customizations': clone.customizations,
                    'clone_count': template.clone_count,
                    'created_at': clone.created_at.isoformat() if clone.created_at else None,
                },
            }
        except Exception as e:
            logger.error("Failed to clone template %s: %s", template_id, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  6. Like template
    # ------------------------------------------------------------------ #

    @staticmethod
    def like_template(user, template_id: int) -> Dict[str, Any]:
        """
        Increment likes_count atomically for a template.

        Returns
        -------
        dict with 'success' key and updated likes count.
        """
        from apps.agents.models import TripTemplate

        try:
            try:
                template = TripTemplate.objects.get(id=template_id)
            except TripTemplate.DoesNotExist:
                return {'success': False, 'error': f'Template with id {template_id} not found'}

            TripTemplate.objects.filter(pk=template.pk).update(
                likes_count=F('likes_count') + 1,
            )
            template.refresh_from_db()

            logger.info(
                "User %s liked template '%s' (id=%s, likes=%d)",
                user, template.title, template_id, template.likes_count,
            )

            return {
                'success': True,
                'template_id': template.id,
                'likes_count': template.likes_count,
            }
        except Exception as e:
            logger.error("Failed to like template %s: %s", template_id, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  7. Rate template
    # ------------------------------------------------------------------ #

    @staticmethod
    def rate_template(user, template_id: int, rating: float) -> Dict[str, Any]:
        """
        Update template rating using weighted average.

        Formula: new_avg = (old_avg * count + new_rating) / (count + 1)

        Returns
        -------
        dict with 'success' key and updated rating info.
        """
        from apps.agents.models import TripTemplate

        try:
            if not (0 <= rating <= 5):
                return {
                    'success': False,
                    'error': 'Rating must be between 0 and 5',
                }

            try:
                template = TripTemplate.objects.get(id=template_id)
            except TripTemplate.DoesNotExist:
                return {'success': False, 'error': f'Template with id {template_id} not found'}

            old_avg = float(template.rating)
            old_count = template.rating_count
            new_avg = (old_avg * old_count + rating) / (old_count + 1)
            new_avg = round(new_avg, 1)

            template.rating = Decimal(str(new_avg))
            template.rating_count = old_count + 1
            template.save(update_fields=['rating', 'rating_count', 'updated_at'])

            logger.info(
                "User %s rated template '%s' (id=%s): %.1f -> avg %.1f (%d ratings)",
                user, template.title, template_id, rating, new_avg, template.rating_count,
            )

            return {
                'success': True,
                'template_id': template.id,
                'rating': float(template.rating),
                'rating_count': template.rating_count,
            }
        except Exception as e:
            logger.error("Failed to rate template %s: %s", template_id, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  8. Featured templates
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_featured_templates(limit: int = 6) -> Dict[str, Any]:
        """
        Return featured and verified templates.

        Returns
        -------
        dict with 'success' key and list of featured template dicts.
        """
        from apps.agents.models import TripTemplate

        try:
            qs = TripTemplate.objects.select_related('creator').filter(
                is_featured=True,
                is_verified=True,
            ).order_by('-clone_count', '-rating')[:limit]

            templates = []
            for t in qs:
                template_dict = TripTemplateService._template_to_dict(t)
                template_dict['creator_name'] = TripTemplateService._get_display_name(t.creator)
                templates.append(template_dict)

            logger.info("Retrieved %d featured templates", len(templates))

            return {
                'success': True,
                'templates': templates,
                'count': len(templates),
            }
        except Exception as e:
            logger.error("Failed to get featured templates: %s", e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  9. Creator's templates
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_creator_templates(user) -> Dict[str, Any]:
        """
        Return all templates created by a given user.

        Returns
        -------
        dict with 'success' key and list of template dicts.
        """
        from apps.agents.models import TripTemplate

        try:
            qs = TripTemplate.objects.filter(creator=user).order_by('-created_at')

            templates = [
                TripTemplateService._template_to_dict(t) for t in qs
            ]

            logger.info("Retrieved %d templates for creator %s", len(templates), user)

            return {
                'success': True,
                'templates': templates,
                'count': len(templates),
            }
        except Exception as e:
            logger.error("Failed to get templates for creator %s: %s", user, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  Private helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _template_to_dict(template) -> Dict[str, Any]:
        """Serialize a TripTemplate instance to a dict."""
        return {
            'id': template.id,
            'title': template.title,
            'description': template.description,
            'destination': template.destination,
            'country': template.country,
            'duration_days': template.duration_days,
            'style': template.style,
            'estimated_budget': float(template.estimated_budget),
            'currency': template.currency,
            'cover_image_url': template.cover_image_url,
            'itinerary_data': template.itinerary_data,
            'tags': template.tags,
            'highlights': template.highlights,
            'is_featured': template.is_featured,
            'is_verified': template.is_verified,
            'clone_count': template.clone_count,
            'likes_count': template.likes_count,
            'views_count': template.views_count,
            'rating': float(template.rating),
            'rating_count': template.rating_count,
            'creator_id': template.creator_id,
            'created_at': template.created_at.isoformat() if template.created_at else None,
            'updated_at': template.updated_at.isoformat() if template.updated_at else None,
        }

    @staticmethod
    def _get_display_name(user) -> str:
        """Return a human-readable display name for a user."""
        full_name = getattr(user, 'get_full_name', lambda: '')()
        if full_name and full_name.strip():
            return full_name.strip()
        return getattr(user, 'username', '') or getattr(user, 'email', '') or str(user)
