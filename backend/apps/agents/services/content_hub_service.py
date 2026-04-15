"""
Content Hub Service
Community-driven content platform for destinations -- submit, moderate, vote, and browse
photos, stories, tips, videos, and audio contributed by travelers.
"""
import json
import logging
import os
from datetime import timedelta
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db.models import Count, F, Q
from django.utils import timezone

logger = logging.getLogger(__name__)


class ContentHubService:
    """Handles community content submission, AI moderation, voting, and discovery."""

    # ------------------------------------------------------------------ #
    #  1. Submit Content
    # ------------------------------------------------------------------ #

    @staticmethod
    def submit_content(user, data: dict) -> Dict[str, Any]:
        """
        Submit new community content with AI-powered moderation.

        Parameters
        ----------
        user : User
            The authenticated user submitting the content.
        data : dict
            Must include: destination, content_type, title.
            Optional: description, media_url, body, tags.

        Returns
        -------
        dict with 'success' key and content data or error.
        """
        from apps.agents.models import ContentItem

        try:
            required_fields = ['destination', 'content_type', 'title']
            missing = [f for f in required_fields if not data.get(f)]
            if missing:
                return {
                    'success': False,
                    'error': f"Missing required fields: {', '.join(missing)}",
                }

            valid_types = ['photo', 'story', 'tip', 'video', 'audio']
            if data['content_type'] not in valid_types:
                return {
                    'success': False,
                    'error': f"Invalid content_type. Must be one of: {', '.join(valid_types)}",
                }

            # Run AI moderation to score content quality
            moderation = ContentHubService._moderate_with_ai(
                title=data['title'],
                description=data.get('description', ''),
                body=data.get('body', ''),
                content_type=data['content_type'],
                destination=data['destination'],
            )

            score = moderation['score']
            if score > 0.7:
                status = 'approved'
            elif score < 0.2:
                status = 'rejected'
            else:
                status = 'pending'

            content = ContentItem.objects.create(
                user=user,
                destination=data['destination'].strip().title(),
                content_type=data['content_type'],
                title=data['title'],
                description=data.get('description', ''),
                media_url=data.get('media_url', ''),
                body=data.get('body', ''),
                tags=data.get('tags', []),
                status=status,
                ai_moderation_score=score,
            )

            logger.info(
                "Content submitted: id=%s, type=%s, destination=%s, status=%s, score=%.2f, user=%s",
                content.id, content.content_type, content.destination,
                content.status, content.ai_moderation_score, user,
            )

            return {
                'success': True,
                'content': ContentHubService._content_to_dict(content),
                'moderation': {
                    'score': score,
                    'status': status,
                    'reason': moderation.get('reason', ''),
                },
            }
        except Exception as e:
            logger.error("Failed to submit content for user %s: %s", user, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  2. Get Destination Content
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_destination_content(
        destination: str,
        content_type: str = None,
        sort_by: str = 'popular',
        limit: int = 20,
        user=None,
    ) -> Dict[str, Any]:
        """
        Retrieve approved content for a destination.

        Parameters
        ----------
        destination : str
            Destination name (case-insensitive match).
        content_type : str or None
            Filter by content type (photo/story/tip/video/audio).
        sort_by : str
            Sorting strategy: 'popular', 'newest', or 'most_viewed'.
        limit : int
            Maximum number of items to return.

        Returns
        -------
        dict with 'success' key and list of content dicts.
        """
        from apps.agents.models import ContentItem

        try:
            qs = ContentItem.objects.filter(
                destination__icontains=destination.strip(),
                status='approved',
            ).select_related('user')

            if content_type:
                qs = qs.filter(content_type=content_type)

            sort_map = {
                'popular': '-upvotes',
                'newest': '-created_at',
                'most_viewed': '-views_count',
            }
            ordering = sort_map.get(sort_by, '-upvotes')
            qs = qs.order_by(ordering)[:limit]

            items = []
            for item in qs:
                item_dict = ContentHubService._content_to_dict(item, user=user)
                item_dict['user_name'] = (
                    item.user.get_full_name() or item.user.username
                    if item.user else 'Anonymous'
                )
                items.append(item_dict)

            logger.info(
                "Retrieved %d content items for destination=%s, type=%s, sort=%s",
                len(items), destination, content_type, sort_by,
            )

            return {
                'success': True,
                'content': items,
                'count': len(items),
                'destination': destination,
                'sort_by': sort_by,
            }
        except Exception as e:
            logger.error("Failed to get destination content for %s: %s", destination, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  3. Vote Content
    # ------------------------------------------------------------------ #

    @staticmethod
    def vote_content(user, content_id: int, vote: str) -> Dict[str, Any]:
        """
        Cast or toggle a per-user vote on a content item.

        Accepts 'up'/'down' (UI style) or 'upvote'/'downvote' (legacy).
        If the user has already cast the same vote, it is cleared. If they have
        the opposite vote, it is switched. Counters are maintained atomically.
        """
        from apps.agents.models import ContentItem, ContentVote

        # Normalize vote alias
        vote_map = {'up': 'up', 'down': 'down', 'upvote': 'up', 'downvote': 'down'}
        vote_norm = vote_map.get(vote)
        if vote_norm is None:
            return {
                'success': False,
                'error': "Vote must be 'up'/'down' (or 'upvote'/'downvote').",
            }

        try:
            try:
                content = ContentItem.objects.get(id=content_id)
            except ContentItem.DoesNotExist:
                return {
                    'success': False,
                    'error': f'Content item with id {content_id} not found.',
                }

            existing = ContentVote.objects.filter(user=user, content_item=content).first()

            upvotes_delta = 0
            downvotes_delta = 0
            new_vote = vote_norm

            if existing and existing.vote == vote_norm:
                # Same vote pressed again → clear
                existing.delete()
                if vote_norm == 'up':
                    upvotes_delta -= 1
                else:
                    downvotes_delta -= 1
                new_vote = None
            elif existing and existing.vote != vote_norm:
                # Switching sides
                if existing.vote == 'up':
                    upvotes_delta -= 1
                else:
                    downvotes_delta -= 1
                existing.vote = vote_norm
                existing.save(update_fields=['vote'])
                if vote_norm == 'up':
                    upvotes_delta += 1
                else:
                    downvotes_delta += 1
            else:
                # New vote
                ContentVote.objects.create(user=user, content_item=content, vote=vote_norm)
                if vote_norm == 'up':
                    upvotes_delta += 1
                else:
                    downvotes_delta += 1

            if upvotes_delta or downvotes_delta:
                ContentItem.objects.filter(id=content_id).update(
                    upvotes=F('upvotes') + upvotes_delta,
                    downvotes=F('downvotes') + downvotes_delta,
                )
                content.refresh_from_db()

            my_reaction = 'like' if new_vote == 'up' else ('dislike' if new_vote == 'down' else None)

            logger.info(
                "User %s set vote=%s on content id=%s", user, new_vote, content_id,
            )

            return {
                'success': True,
                'content_id': content_id,
                'vote': new_vote,
                'my_reaction': my_reaction,
                'upvotes': content.upvotes,
                'downvotes': content.downvotes,
            }
        except Exception as e:
            logger.error("Failed to vote on content %s: %s", content_id, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  3b. Comments
    # ------------------------------------------------------------------ #

    @staticmethod
    def add_comment(user, content_id: int, content: str) -> Dict[str, Any]:
        """Add a comment to a content item (max 1000 chars)."""
        from apps.agents.models import ContentItem, ContentComment

        if not content or not content.strip():
            return {'success': False, 'error': 'Comment cannot be empty'}
        if len(content) > 1000:
            return {'success': False, 'error': 'Comment exceeds 1000 character limit'}

        try:
            try:
                item = ContentItem.objects.get(id=content_id)
            except ContentItem.DoesNotExist:
                return {
                    'success': False,
                    'error': f'Content item with id {content_id} not found.',
                }

            comment = ContentComment.objects.create(
                user=user, content_item=item, content=content.strip(),
            )
            ContentItem.objects.filter(id=content_id).update(
                comments_count=F('comments_count') + 1,
            )
            item.refresh_from_db()

            user_name = (
                user.get_full_name() or getattr(user, 'username', '') or 'Anonymous'
            )
            return {
                'success': True,
                'comments_count': item.comments_count,
                'comment': {
                    'id': comment.id,
                    'user': user_name,
                    'user_id': getattr(user, 'id', None),
                    'content_id': content_id,
                    'content': comment.content,
                    'created_at': comment.created_at.isoformat() if comment.created_at else None,
                },
            }
        except Exception as e:
            logger.error("Failed to add comment to content %s: %s", content_id, e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def list_comments(content_id: int) -> Dict[str, Any]:
        """List comments for a content item, newest first."""
        from apps.agents.models import ContentItem

        try:
            try:
                item = ContentItem.objects.get(id=content_id)
            except ContentItem.DoesNotExist:
                return {
                    'success': False,
                    'error': f'Content item with id {content_id} not found.',
                }

            comments = [
                {
                    'id': c.id,
                    'user': (c.user.get_full_name() or c.user.username) if c.user else 'Anonymous',
                    'user_id': c.user_id,
                    'content': c.content,
                    'created_at': c.created_at.isoformat() if c.created_at else None,
                }
                for c in item.comments.select_related('user').order_by('-created_at')
            ]
            return {'success': True, 'comments': comments, 'count': len(comments)}
        except Exception as e:
            logger.error("Failed to list comments for content %s: %s", content_id, e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def delete_comment(user, comment_id: int) -> Dict[str, Any]:
        """Delete a content comment (author only)."""
        from apps.agents.models import ContentComment, ContentItem

        try:
            try:
                comment = ContentComment.objects.select_related('content_item').get(id=comment_id)
            except ContentComment.DoesNotExist:
                return {'success': False, 'error': 'Comment not found'}

            if comment.user_id != getattr(user, 'id', None):
                return {'success': False, 'error': 'Not authorized to delete this comment'}

            item_pk = comment.content_item_id
            comment.delete()
            ContentItem.objects.filter(pk=item_pk).update(
                comments_count=F('comments_count') - 1,
            )
            item = ContentItem.objects.filter(pk=item_pk).first()
            return {
                'success': True,
                'comments_count': item.comments_count if item else 0,
            }
        except Exception as e:
            logger.error("Failed to delete content comment %s: %s", comment_id, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  4. Get Content Detail
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_content_detail(content_id: int, user=None) -> Dict[str, Any]:
        """
        Retrieve a single content item and increment its view count atomically.

        Parameters
        ----------
        content_id : int
            ID of the ContentItem.

        Returns
        -------
        dict with 'success' key and content data.
        """
        from apps.agents.models import ContentItem

        try:
            try:
                content = ContentItem.objects.select_related('user').get(id=content_id)
            except ContentItem.DoesNotExist:
                return {
                    'success': False,
                    'error': f'Content item with id {content_id} not found.',
                }

            # Increment views atomically
            ContentItem.objects.filter(id=content_id).update(
                views_count=F('views_count') + 1,
            )
            content.refresh_from_db()

            content_dict = ContentHubService._content_to_dict(content, user=user)
            content_dict['user_name'] = (
                content.user.get_full_name() or content.user.username
                if content.user else 'Anonymous'
            )

            logger.info("Content detail retrieved: id=%s, views=%s", content_id, content.views_count)

            return {
                'success': True,
                'content': content_dict,
            }
        except Exception as e:
            logger.error("Failed to get content detail for id %s: %s", content_id, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  5. Get User Content
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_user_content(user, status: str = None) -> Dict[str, Any]:
        """
        Retrieve all content submitted by a user, optionally filtered by status.

        Parameters
        ----------
        user : User
            The content author.
        status : str or None
            Filter by status (pending/approved/rejected/flagged).

        Returns
        -------
        dict with 'success' key and list of content dicts.
        """
        from apps.agents.models import ContentItem

        try:
            qs = ContentItem.objects.filter(user=user).order_by('-created_at')

            if status:
                qs = qs.filter(status=status)

            items = [ContentHubService._content_to_dict(item, user=user) for item in qs]

            logger.info(
                "Retrieved %d content items for user %s (status=%s)",
                len(items), user, status,
            )

            return {
                'success': True,
                'content': items,
                'count': len(items),
            }
        except Exception as e:
            logger.error("Failed to get content for user %s: %s", user, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  6. Get Trending Content
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_trending_content(limit: int = 10, user=None) -> Dict[str, Any]:
        """
        Retrieve trending content ranked by upvotes + views.

        Prefers content from the last 7 days; falls back to all-time
        trending if the recent window is empty so the tab is never blank.
        """
        from apps.agents.models import ContentItem

        try:
            cutoff = timezone.now() - timedelta(days=7)

            base_qs = ContentItem.objects.filter(
                status='approved',
            ).select_related('user')

            recent_qs = base_qs.filter(created_at__gte=cutoff).order_by(
                '-upvotes', '-views_count', '-created_at',
            )[:limit]

            qs = list(recent_qs)
            period_days: int | None = 7

            # Fall back to all-time trending so the tab isn't empty when
            # there's no activity this week.
            if not qs:
                qs = list(base_qs.order_by('-upvotes', '-views_count', '-created_at')[:limit])
                period_days = None

            items = []
            for item in qs:
                item_dict = ContentHubService._content_to_dict(item, user=user)
                item_dict['user_name'] = (
                    item.user.get_full_name() or item.user.username
                    if item.user else 'Anonymous'
                )
                items.append(item_dict)

            logger.info("Retrieved %d trending content items (period=%s)", len(items), period_days)

            return {
                'success': True,
                'content': items,
                'count': len(items),
                'period_days': period_days,
            }
        except Exception as e:
            logger.error("Failed to get trending content: %s", e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  7. Moderate Content (Admin)
    # ------------------------------------------------------------------ #

    @staticmethod
    def moderate_content(content_id: int, action: str) -> Dict[str, Any]:
        """
        Admin moderation action on a content item.

        Parameters
        ----------
        content_id : int
            ID of the ContentItem.
        action : str
            One of: 'approve', 'reject', 'flag'.

        Returns
        -------
        dict with 'success' key and updated content data.
        """
        from apps.agents.models import ContentItem

        try:
            action_map = {
                'approve': 'approved',
                'reject': 'rejected',
                'flag': 'flagged',
            }

            if action not in action_map:
                return {
                    'success': False,
                    'error': f"Invalid action. Must be one of: {', '.join(action_map.keys())}",
                }

            try:
                content = ContentItem.objects.get(id=content_id)
            except ContentItem.DoesNotExist:
                return {
                    'success': False,
                    'error': f'Content item with id {content_id} not found.',
                }

            previous_status = content.status
            content.status = action_map[action]
            content.save(update_fields=['status', 'updated_at'])

            logger.info(
                "Content id=%s moderated: %s -> %s (action=%s)",
                content_id, previous_status, content.status, action,
            )

            return {
                'success': True,
                'content': ContentHubService._content_to_dict(content),
                'previous_status': previous_status,
                'action': action,
            }
        except Exception as e:
            logger.error("Failed to moderate content id %s: %s", content_id, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  8. Get Destination Stats
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_destination_stats(destination: str) -> Dict[str, Any]:
        """
        Aggregate statistics for a destination's community content.

        Returns total content count, breakdown by type, top contributors,
        and count of recent content (last 7 days).

        Parameters
        ----------
        destination : str
            Destination name (case-insensitive match).

        Returns
        -------
        dict with 'success' key and stats data.
        """
        from apps.agents.models import ContentItem

        try:
            qs = ContentItem.objects.filter(
                destination__iexact=destination.strip(),
                status='approved',
            )

            total_content = qs.count()

            # Breakdown by content type
            by_type = dict(
                qs.values_list('content_type')
                .annotate(count=Count('id'))
                .values_list('content_type', 'count')
            )

            # Top contributors (by number of approved items)
            top_contributors_qs = (
                qs.values('user__username', 'user__first_name', 'user__last_name')
                .annotate(contributions=Count('id'))
                .order_by('-contributions')[:5]
            )
            top_contributors = [
                {
                    'username': c['user__username'],
                    'name': (
                        f"{c['user__first_name']} {c['user__last_name']}".strip()
                        or c['user__username']
                    ),
                    'contributions': c['contributions'],
                }
                for c in top_contributors_qs
            ]

            # Recent content count (last 7 days)
            cutoff = timezone.now() - timedelta(days=7)
            recent_count = qs.filter(created_at__gte=cutoff).count()

            logger.info(
                "Destination stats for %s: total=%d, recent=%d",
                destination, total_content, recent_count,
            )

            return {
                'success': True,
                'destination': destination,
                'total_content': total_content,
                'by_type': by_type,
                'top_contributors': top_contributors,
                'recent_content_count': recent_count,
            }
        except Exception as e:
            logger.error("Failed to get destination stats for %s: %s", destination, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  AI Moderation (private)
    # ------------------------------------------------------------------ #

    @staticmethod
    def _moderate_with_ai(
        title: str,
        description: str,
        body: str,
        content_type: str,
        destination: str,
    ) -> Dict[str, Any]:
        """
        Score content quality 0-1 using GPT-4o-mini.

        Falls back to deterministic score of 0.5 on any failure.
        """
        api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        if not api_key or api_key in ('your_openai_api_key_here', ''):
            logger.info("No OpenAI API key configured; using fallback moderation score.")
            return ContentHubService._moderate_fallback(title, description, body)

        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage

            model = ChatOpenAI(
                model='gpt-4o-mini',
                temperature=0.1,
                api_key=api_key,
                request_timeout=30,
            )

            text_content = f"Title: {title}"
            if description:
                text_content += f"\nDescription: {description}"
            if body:
                text_content += f"\nBody: {body}"

            response = model.invoke([
                SystemMessage(content=(
                    "You are a content moderation engine for a travel community platform. "
                    "Return JSON only, no markdown fences."
                )),
                HumanMessage(content=f"""Score the following user-submitted {content_type} content for "{destination}".

{text_content}

Evaluate on: relevance to the destination, quality of writing, helpfulness,
appropriateness (no spam, hate speech, or misleading info), and overall value
to fellow travelers.

Return a single JSON object:
{{
  "score": <float 0.0 to 1.0, where 1.0 is excellent quality>,
  "reason": "<1-2 sentence explanation of the score>"
}}"""),
            ])

            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            data = json.loads(content)

            score = max(0.0, min(1.0, float(data.get('score', 0.5))))
            reason = data.get('reason', '')

            logger.info("AI moderation score: %.2f for title='%s'", score, title)

            return {'score': score, 'reason': reason}

        except Exception as e:
            logger.warning("AI moderation failed, using fallback: %s", e)
            return ContentHubService._moderate_fallback(title, description, body)

    @staticmethod
    def _moderate_fallback(title: str, description: str, body: str) -> Dict[str, Any]:
        """
        Deterministic fallback moderation when AI is unavailable.

        Assigns a default score of 0.5 (pending review) with basic heuristics.
        """
        score = 0.5
        reasons = []

        combined_text = f"{title} {description} {body}".lower()

        # Slightly boost content that has reasonable length
        text_length = len(combined_text.strip())
        if text_length > 100:
            score += 0.1
            reasons.append("Reasonable content length")
        if text_length < 10:
            score -= 0.15
            reasons.append("Very short content")

        # Basic spam indicators
        spam_words = ['buy now', 'click here', 'free money', 'casino', 'viagra']
        if any(word in combined_text for word in spam_words):
            score -= 0.3
            reasons.append("Potential spam detected")

        # Clamp
        score = max(0.0, min(1.0, round(score, 2)))

        reason = '; '.join(reasons) if reasons else 'Fallback moderation applied'
        return {'score': score, 'reason': reason}

    # ------------------------------------------------------------------ #
    #  Serialisation helper
    # ------------------------------------------------------------------ #

    @staticmethod
    def _content_to_dict(item, user=None) -> Dict[str, Any]:
        """Serialise a ContentItem model instance to a plain dict.

        If ``user`` is authenticated, includes per-user vote/reaction state.
        """
        from apps.agents.models import ContentVote

        my_vote = None
        my_reaction = None
        if user is not None and getattr(user, 'is_authenticated', False):
            vote = ContentVote.objects.filter(user=user, content_item=item).first()
            if vote:
                my_vote = vote.vote  # 'up' | 'down'
                my_reaction = 'like' if vote.vote == 'up' else 'dislike'

        return {
            'id': item.id,
            'destination': item.destination,
            'content_type': item.content_type,
            'title': item.title,
            'description': item.description,
            'media_url': item.media_url,
            'body': item.body,
            'tags': item.tags,
            'status': item.status,
            'ai_moderation_score': item.ai_moderation_score,
            'upvotes': item.upvotes,
            'downvotes': item.downvotes,
            'likes_count': item.upvotes,
            'dislikes_count': item.downvotes,
            'comments_count': getattr(item, 'comments_count', 0),
            'views_count': item.views_count,
            'my_vote': my_vote,
            'my_reaction': my_reaction,
            'created_at': item.created_at.isoformat() if item.created_at else None,
            'updated_at': item.updated_at.isoformat() if item.updated_at else None,
            'user_id': item.user_id,
        }
