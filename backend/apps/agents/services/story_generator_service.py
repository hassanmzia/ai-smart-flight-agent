"""
Story Generator Service
AI-powered travel story generation, social cards, sharing, likes, and comments.
"""
import json
import logging
import os
import uuid
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db.models import F

logger = logging.getLogger(__name__)

# Mood palette used by the deterministic fallback for story cards
_FALLBACK_MOODS = [
    'adventurous', 'relaxed', 'excited', 'inspired',
    'curious', 'grateful', 'joyful', 'reflective',
]

# Default hashtag sets per format
_FORMAT_HASHTAGS = {
    'journal': ['#traveljournal', '#wanderlust', '#traveldiaries'],
    'instagram': ['#instatravel', '#travelgram', '#explore'],
    'blog': ['#travelblog', '#traveltips', '#bucketlist'],
    'social': ['#travel', '#adventure', '#vacation'],
    'thread': ['#travelthread', '#storytelling', '#traveler'],
}


class StoryGeneratorService:
    """Generate, share, and interact with AI-powered travel stories."""

    # ------------------------------------------------------------------ #
    #  1. Generate Story
    # ------------------------------------------------------------------ #

    @staticmethod
    def generate_story(user, data: dict) -> Dict[str, Any]:
        """
        Generate an AI travel story from trip data.

        Parameters
        ----------
        data : dict
            Required: destination, trip_days (int), highlights (list[str]), format.
            Optional: itinerary_id (int).

        Returns
        -------
        dict with 'success' key and story data or error.
        """
        from apps.agents.models import TravelStoryGenerated

        try:
            destination = data.get('destination', '')
            trip_days = int(data.get('trip_days', 1))
            highlights = data.get('highlights', [])
            story_format = data.get('format', 'journal')
            itinerary_id = data.get('itinerary_id')

            if not destination:
                return {'success': False, 'error': 'destination is required'}

            share_token = uuid.uuid4().hex[:32]

            # Attempt AI generation
            ai_result = StoryGeneratorService._generate_story_ai(
                destination, trip_days, highlights, story_format,
            )

            title = ai_result.get('title', f'My {trip_days}-Day Adventure in {destination}')
            content = ai_result.get('content', '')
            story_cards = ai_result.get('story_cards', [])
            tags = ai_result.get('tags', [destination.lower(), 'travel', story_format])

            story = TravelStoryGenerated.objects.create(
                user=user,
                itinerary_id=itinerary_id,
                title=title,
                content=content,
                format=story_format,
                status='draft',
                destination=destination,
                tags=tags,
                story_cards=story_cards,
                share_token=share_token,
            )

            logger.info(
                "Generated travel story '%s' for user %s (id=%s, format=%s)",
                title, user, story.id, story_format,
            )

            return {
                'success': True,
                'story': StoryGeneratorService._serialize_story(story),
            }
        except Exception as e:
            logger.error("Failed to generate story for user %s: %s", user, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  2. Generate Social Cards
    # ------------------------------------------------------------------ #

    @staticmethod
    def generate_social_cards(story_id: int) -> Dict[str, Any]:
        """
        Generate Instagram-ready story cards from an existing story.

        Each card: {day, title, caption, hashtags, mood_emoji}.
        Updates the story's story_cards field.

        Returns
        -------
        dict with 'success' key and list of cards.
        """
        from apps.agents.models import TravelStoryGenerated

        try:
            try:
                story = TravelStoryGenerated.objects.get(id=story_id)
            except TravelStoryGenerated.DoesNotExist:
                return {'success': False, 'error': f'Story with id {story_id} not found'}

            cards = StoryGeneratorService._generate_social_cards_ai(story)

            story.story_cards = cards
            story.save(update_fields=['story_cards', 'updated_at'])

            logger.info(
                "Generated %d social cards for story %s ('%s')",
                len(cards), story_id, story.title,
            )

            return {'success': True, 'cards': cards, 'story_id': story_id}
        except Exception as e:
            logger.error("Failed to generate social cards for story %s: %s", story_id, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  3. Get Story (public, by share_token)
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_story(share_token: str, user=None) -> Dict[str, Any]:
        """
        Retrieve a published story by its share_token.

        Increments views_count atomically. Returns story data with
        comments and like count.

        Returns
        -------
        dict with 'success' key and story data or error.
        """
        from apps.agents.models import TravelStoryGenerated

        try:
            try:
                story = TravelStoryGenerated.objects.get(share_token=share_token)
            except TravelStoryGenerated.DoesNotExist:
                return {'success': False, 'error': 'Story not found'}

            # Non-published stories are only visible to their author
            if story.status != 'published':
                is_owner = user is not None and getattr(user, 'is_authenticated', False) and story.user_id == user.id
                if not is_owner:
                    return {'success': False, 'error': 'Story not found or not published'}

            # Increment views atomically
            TravelStoryGenerated.objects.filter(pk=story.pk).update(
                views_count=F('views_count') + 1,
            )
            story.refresh_from_db()

            # Fetch comments
            comments = [
                {
                    'id': c.id,
                    'user': str(c.user),
                    'user_id': c.user_id,
                    'content': c.content,
                    'created_at': c.created_at.isoformat() if c.created_at else None,
                }
                for c in story.comments.select_related('user').order_by('-created_at')
            ]

            story_data = StoryGeneratorService._serialize_story(story, user=user)
            story_data['comments'] = comments

            logger.info("Retrieved story '%s' via share_token (views=%d)", story.title, story.views_count)

            return {'success': True, 'story': story_data}
        except Exception as e:
            logger.error("Failed to get story by token %s: %s", share_token, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  4. List User Stories
    # ------------------------------------------------------------------ #

    @staticmethod
    def list_user_stories(user) -> Dict[str, Any]:
        """
        Return all stories created by a user, newest first.

        Returns
        -------
        dict with 'success' key and list of story dicts.
        """
        from apps.agents.models import TravelStoryGenerated

        try:
            stories = TravelStoryGenerated.objects.filter(
                user=user,
            ).order_by('-created_at')

            results = [
                StoryGeneratorService._serialize_story(s, user=user) for s in stories
            ]

            logger.info("Listed %d stories for user %s", len(results), user)

            return {'success': True, 'stories': results, 'count': len(results)}
        except Exception as e:
            logger.error("Failed to list stories for user %s: %s", user, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  5. List Public Stories
    # ------------------------------------------------------------------ #

    @staticmethod
    def list_public_stories(
        destination: str = None,
        format: str = None,
        limit: int = 20,
        user=None,
    ) -> Dict[str, Any]:
        """
        List public published stories with optional filters.

        Parameters
        ----------
        destination : str, optional
            Filter by destination (case-insensitive contains).
        format : str, optional
            Filter by story format.
        limit : int
            Max results (default 20).

        Returns
        -------
        dict with 'success' key and list of story dicts.
        """
        from apps.agents.models import TravelStoryGenerated

        try:
            qs = TravelStoryGenerated.objects.filter(
                status='published',
                is_public=True,
            ).order_by('-created_at')

            if destination:
                qs = qs.filter(destination__icontains=destination)

            if format:
                qs = qs.filter(format=format)

            stories = qs[:limit]

            results = [
                StoryGeneratorService._serialize_story(s, user=user) for s in stories
            ]

            logger.info(
                "Listed %d public stories (destination=%s, format=%s, limit=%d)",
                len(results), destination, format, limit,
            )

            return {'success': True, 'stories': results, 'count': len(results)}
        except Exception as e:
            logger.error("Failed to list public stories: %s", e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  6. Toggle Like (legacy wrapper) / Set Reaction
    # ------------------------------------------------------------------ #

    @staticmethod
    def toggle_like(user, story_id: int) -> Dict[str, Any]:
        """Backward-compatible wrapper around set_reaction('like')."""
        return StoryGeneratorService.set_reaction(user, story_id, 'like')

    @staticmethod
    def set_reaction(user, story_id: int, reaction: str) -> Dict[str, Any]:
        """
        Toggle a like or dislike on a story.

        ``reaction`` is one of 'like' or 'dislike'. If the user already has that
        same reaction, it is cleared. If the user has the opposite reaction, it
        is switched. Counters are maintained atomically with F() updates.

        Returns dict with success, my_reaction ('like'|'dislike'|None),
        likes_count, dislikes_count.
        """
        from apps.agents.models import StoryLike, StoryDislike, TravelStoryGenerated

        if reaction not in ('like', 'dislike'):
            return {'success': False, 'error': "reaction must be 'like' or 'dislike'"}

        try:
            try:
                story = TravelStoryGenerated.objects.get(id=story_id)
            except TravelStoryGenerated.DoesNotExist:
                return {'success': False, 'error': f'Story with id {story_id} not found'}

            has_like = StoryLike.objects.filter(user=user, story=story).exists()
            has_dislike = StoryDislike.objects.filter(user=user, story=story).exists()

            likes_delta = 0
            dislikes_delta = 0
            new_reaction = reaction

            if reaction == 'like':
                if has_like:
                    StoryLike.objects.filter(user=user, story=story).delete()
                    likes_delta -= 1
                    new_reaction = None
                else:
                    if has_dislike:
                        StoryDislike.objects.filter(user=user, story=story).delete()
                        dislikes_delta -= 1
                    StoryLike.objects.create(user=user, story=story)
                    likes_delta += 1
            else:  # dislike
                if has_dislike:
                    StoryDislike.objects.filter(user=user, story=story).delete()
                    dislikes_delta -= 1
                    new_reaction = None
                else:
                    if has_like:
                        StoryLike.objects.filter(user=user, story=story).delete()
                        likes_delta -= 1
                    StoryDislike.objects.create(user=user, story=story)
                    dislikes_delta += 1

            if likes_delta or dislikes_delta:
                TravelStoryGenerated.objects.filter(pk=story.pk).update(
                    likes_count=F('likes_count') + likes_delta,
                    dislikes_count=F('dislikes_count') + dislikes_delta,
                )
                story.refresh_from_db()

            return {
                'success': True,
                'my_reaction': new_reaction,
                'liked': new_reaction == 'like',
                'likes_count': story.likes_count,
                'dislikes_count': story.dislikes_count,
            }
        except Exception as e:
            logger.error("Failed to set reaction for story %s: %s", story_id, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  7. Add Comment
    # ------------------------------------------------------------------ #

    @staticmethod
    def add_comment(user, story_id: int, content: str) -> Dict[str, Any]:
        """
        Add a comment to a story.

        Parameters
        ----------
        content : str
            Comment text (max 1000 characters).

        Returns
        -------
        dict with 'success' key and comment data.
        """
        from apps.agents.models import StoryComment, TravelStoryGenerated

        try:
            try:
                story = TravelStoryGenerated.objects.get(id=story_id)
            except TravelStoryGenerated.DoesNotExist:
                return {'success': False, 'error': f'Story with id {story_id} not found'}

            if not content or not content.strip():
                return {'success': False, 'error': 'Comment content cannot be empty'}

            if len(content) > 1000:
                return {'success': False, 'error': 'Comment exceeds 1000 character limit'}

            comment = StoryComment.objects.create(
                user=user,
                story=story,
                content=content.strip(),
            )
            TravelStoryGenerated.objects.filter(pk=story.pk).update(
                comments_count=F('comments_count') + 1,
            )
            story.refresh_from_db()

            logger.info("User %s commented on story %s", user, story_id)

            return {
                'success': True,
                'comments_count': story.comments_count,
                'comment': {
                    'id': comment.id,
                    'user': str(user),
                    'user_id': getattr(user, 'id', None),
                    'story_id': story_id,
                    'content': comment.content,
                    'created_at': comment.created_at.isoformat() if comment.created_at else None,
                },
            }
        except Exception as e:
            logger.error("Failed to add comment to story %s: %s", story_id, e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def delete_comment(user, comment_id: int) -> Dict[str, Any]:
        """Delete a comment (only its author can delete). Decrements comments_count."""
        from apps.agents.models import StoryComment, TravelStoryGenerated

        try:
            try:
                comment = StoryComment.objects.select_related('story').get(id=comment_id)
            except StoryComment.DoesNotExist:
                return {'success': False, 'error': 'Comment not found'}

            if comment.user_id != getattr(user, 'id', None):
                return {'success': False, 'error': 'Not authorized to delete this comment'}

            story_pk = comment.story_id
            comment.delete()
            TravelStoryGenerated.objects.filter(pk=story_pk).update(
                comments_count=F('comments_count') - 1,
            )
            story = TravelStoryGenerated.objects.filter(pk=story_pk).first()
            return {
                'success': True,
                'comments_count': story.comments_count if story else 0,
            }
        except Exception as e:
            logger.error("Failed to delete story comment %s: %s", comment_id, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  8. Publish Story
    # ------------------------------------------------------------------ #

    @staticmethod
    def publish_story(user, story_id: int) -> Dict[str, Any]:
        """
        Publish a story (set status='published', is_public=True).

        Only the story owner may publish.

        Returns
        -------
        dict with 'success' key and updated story data.
        """
        from apps.agents.models import TravelStoryGenerated

        try:
            try:
                story = TravelStoryGenerated.objects.get(id=story_id)
            except TravelStoryGenerated.DoesNotExist:
                return {'success': False, 'error': f'Story with id {story_id} not found'}

            if story.user != user:
                return {'success': False, 'error': 'Only the story owner can publish this story'}

            story.status = 'published'
            story.is_public = True
            story.save(update_fields=['status', 'is_public', 'updated_at'])

            logger.info("Story %s published by user %s", story_id, user)

            return {
                'success': True,
                'story': StoryGeneratorService._serialize_story(story),
            }
        except Exception as e:
            logger.error("Failed to publish story %s: %s", story_id, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  9. Share Story
    # ------------------------------------------------------------------ #

    @staticmethod
    def share_story(story_id: int) -> Dict[str, Any]:
        """
        Record a share action on a story: increment shares_count and
        return the shareable URL.

        Returns
        -------
        dict with 'success' key, share_url, and updated shares_count.
        """
        from apps.agents.models import TravelStoryGenerated

        try:
            try:
                story = TravelStoryGenerated.objects.get(id=story_id)
            except TravelStoryGenerated.DoesNotExist:
                return {'success': False, 'error': f'Story with id {story_id} not found'}

            TravelStoryGenerated.objects.filter(pk=story.pk).update(
                shares_count=F('shares_count') + 1,
            )
            story.refresh_from_db()

            share_url = f"/stories/{story.share_token}"

            logger.info("Story %s shared (shares=%d)", story_id, story.shares_count)

            return {
                'success': True,
                'share_url': share_url,
                'share_token': story.share_token,
                'shares_count': story.shares_count,
            }
        except Exception as e:
            logger.error("Failed to share story %s: %s", story_id, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  Internal: AI story generation
    # ------------------------------------------------------------------ #

    @staticmethod
    def _generate_story_ai(
        destination: str,
        trip_days: int,
        highlights: List[str],
        story_format: str,
    ) -> Dict[str, Any]:
        """Generate story content via LangChain GPT-4o-mini with deterministic fallback."""
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            logger.info("No OpenAI API key available, using fallback story generation")
            return StoryGeneratorService._story_fallback(
                destination, trip_days, highlights, story_format,
            )

        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model='gpt-4o-mini',
                temperature=0.7,
                api_key=api_key,
                request_timeout=25,
            )

            highlights_text = ', '.join(highlights) if highlights else 'local sights and culture'

            prompt = (
                f"Generate a travel story for a {trip_days}-day trip to {destination}.\n"
                f"Highlights: {highlights_text}\n"
                f"Format: {story_format}\n\n"
                "Return JSON only, no markdown fences:\n"
                '{\n'
                '  "title": "<catchy story title>",\n'
                '  "content": "<full narrative, multiple paragraphs>",\n'
                '  "tags": ["<tag1>", "<tag2>", "<tag3>", "<tag4>", "<tag5>"],\n'
                '  "story_cards": [\n'
                '    {\n'
                '      "day": 1,\n'
                '      "title": "<day title>",\n'
                '      "content": "<day narrative, 2-3 sentences>",\n'
                '      "mood": "<mood word>",\n'
                '      "image_url": ""\n'
                '    }\n'
                '  ]\n'
                '}\n\n'
                f"Generate exactly {trip_days} story_cards, one per day."
            )

            response = llm.invoke(prompt)
            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            data = json.loads(content)

            if isinstance(data, dict) and 'title' in data:
                logger.info("AI-generated story for %s (%d days)", destination, trip_days)
                return data

            logger.warning("AI returned unexpected structure for %s, using fallback", destination)
            return StoryGeneratorService._story_fallback(
                destination, trip_days, highlights, story_format,
            )

        except Exception as e:
            logger.warning("AI story generation failed for %s: %s", destination, e)
            return StoryGeneratorService._story_fallback(
                destination, trip_days, highlights, story_format,
            )

    @staticmethod
    def _story_fallback(
        destination: str,
        trip_days: int,
        highlights: List[str],
        story_format: str,
    ) -> Dict[str, Any]:
        """Deterministic fallback: build day-by-day journal entries from highlights."""
        title = f'My {trip_days}-Day Adventure in {destination}'

        # Distribute highlights across days
        story_cards = []
        for day in range(1, trip_days + 1):
            highlight_idx = (day - 1) % len(highlights) if highlights else -1
            day_highlight = highlights[highlight_idx] if highlights else 'exploring the city'
            mood = _FALLBACK_MOODS[(day - 1) % len(_FALLBACK_MOODS)]

            story_cards.append({
                'day': day,
                'title': f'Day {day}: {day_highlight.title()}',
                'content': (
                    f'On day {day} in {destination}, the journey continued with '
                    f'{day_highlight}. The experience was truly {mood} and left '
                    f'a lasting impression.'
                ),
                'mood': mood,
                'image_url': '',
            })

        # Build full narrative from cards
        paragraphs = [
            f"# {title}\n",
            f"A {trip_days}-day journey through {destination} filled with unforgettable moments.\n",
        ]
        for card in story_cards:
            paragraphs.append(f"## {card['title']}\n{card['content']}\n")

        content = '\n'.join(paragraphs)
        tags = [destination.lower(), 'travel', story_format]
        if highlights:
            tags.extend([h.lower().replace(' ', '') for h in highlights[:3]])

        return {
            'title': title,
            'content': content,
            'tags': tags,
            'story_cards': story_cards,
        }

    # ------------------------------------------------------------------ #
    #  Internal: AI social card generation
    # ------------------------------------------------------------------ #

    @staticmethod
    def _generate_social_cards_ai(story) -> List[Dict[str, Any]]:
        """Generate Instagram-ready social cards from a story via AI with fallback."""
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            logger.info("No OpenAI API key, using fallback social cards for story %s", story.id)
            return StoryGeneratorService._social_cards_fallback(story)

        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model='gpt-4o-mini',
                temperature=0.7,
                api_key=api_key,
                request_timeout=30,
            )

            prompt = (
                f"Create Instagram-ready story cards for this travel story.\n"
                f"Title: {story.title}\n"
                f"Destination: {story.destination}\n"
                f"Content summary: {story.content[:500]}\n\n"
                "Return JSON only, no markdown fences. Array of cards:\n"
                '[\n'
                '  {\n'
                '    "day": 1,\n'
                '    "title": "<short punchy title>",\n'
                '    "caption": "<Instagram caption, 1-2 sentences>",\n'
                '    "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],\n'
                '    "mood_emoji": "<single emoji>"\n'
                '  }\n'
                ']\n\n'
                "Create one card per story card/day."
            )

            response = llm.invoke(prompt)
            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            cards = json.loads(content)

            if isinstance(cards, list) and len(cards) > 0:
                logger.info("AI-generated %d social cards for story %s", len(cards), story.id)
                return cards

            logger.warning("AI returned unexpected social cards for story %s, using fallback", story.id)
            return StoryGeneratorService._social_cards_fallback(story)

        except Exception as e:
            logger.warning("AI social card generation failed for story %s: %s", story.id, e)
            return StoryGeneratorService._social_cards_fallback(story)

    @staticmethod
    def _social_cards_fallback(story) -> List[Dict[str, Any]]:
        """Deterministic fallback for social cards using existing story_cards data."""
        base_hashtags = _FORMAT_HASHTAGS.get(story.format, _FORMAT_HASHTAGS['social'])
        destination_tag = f'#{story.destination.lower().replace(" ", "")}'

        mood_emojis = {
            'adventurous': '\u2728',
            'relaxed': '\U0001f334',
            'excited': '\U0001f525',
            'inspired': '\U0001f4ab',
            'curious': '\U0001f50d',
            'grateful': '\u2764\ufe0f',
            'joyful': '\u2600\ufe0f',
            'reflective': '\U0001f319',
        }

        cards = []
        existing_cards = story.story_cards if isinstance(story.story_cards, list) else []

        if existing_cards:
            for card in existing_cards:
                mood = card.get('mood', 'adventurous')
                cards.append({
                    'day': card.get('day', len(cards) + 1),
                    'title': card.get('title', f'Day {card.get("day", len(cards) + 1)}'),
                    'caption': card.get('content', f'Exploring {story.destination}!'),
                    'hashtags': base_hashtags + [destination_tag, '#travel'],
                    'mood_emoji': mood_emojis.get(mood, '\u2728'),
                })
        else:
            # Create a single card from the story itself
            cards.append({
                'day': 1,
                'title': story.title,
                'caption': story.content[:150] + '...' if len(story.content) > 150 else story.content,
                'hashtags': base_hashtags + [destination_tag, '#travel'],
                'mood_emoji': '\u2728',
            })

        return cards

    # ------------------------------------------------------------------ #
    #  Internal: serialization
    # ------------------------------------------------------------------ #

    @staticmethod
    def _serialize_story(story, user=None) -> Dict[str, Any]:
        """Convert a TravelStoryGenerated instance to a dict.

        If ``user`` is given and authenticated, includes per-user reaction state.
        """
        from apps.agents.models import StoryLike, StoryDislike

        my_reaction = None
        if user is not None and getattr(user, 'is_authenticated', False):
            if StoryLike.objects.filter(user=user, story=story).exists():
                my_reaction = 'like'
            elif StoryDislike.objects.filter(user=user, story=story).exists():
                my_reaction = 'dislike'

        return {
            'id': story.id,
            'user': str(story.user),
            'itinerary_id': story.itinerary_id,
            'title': story.title,
            'content': story.content,
            'format': story.format,
            'status': story.status,
            'destination': story.destination,
            'cover_image_url': story.cover_image_url,
            'tags': story.tags,
            'story_cards': story.story_cards,
            'share_token': story.share_token,
            'views_count': story.views_count,
            'likes_count': story.likes_count,
            'dislikes_count': getattr(story, 'dislikes_count', 0),
            'comments_count': getattr(story, 'comments_count', 0),
            'shares_count': story.shares_count,
            'is_public': story.is_public,
            'my_reaction': my_reaction,
            'created_at': story.created_at.isoformat() if story.created_at else None,
            'updated_at': story.updated_at.isoformat() if story.updated_at else None,
        }
