"""
User-specific RAG (Retrieval-Augmented Generation) for the AI Travel Assistant chat.

Instead of dumping ALL user data into the system prompt (context stuffing),
this module embeds user bookings, itineraries, trip feedback, and agent sessions
into a ChromaDB vector store and retrieves only the most relevant chunks per query.

Architecture:
  - Single ChromaDB collection `user_travel_data` with user_id metadata filtering
  - Lazy indexing: user data is indexed on first chat request, then refreshed
    periodically (controlled by cache TTL)
  - Each user record (booking, itinerary, feedback, session) is converted to
    a descriptive text chunk and embedded
"""

import os
import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Cache TTL for user index freshness (seconds)
USER_INDEX_TTL = 300  # 5 minutes

# Collection name
COLLECTION_NAME = "user_travel_data"


def _get_embedding_function():
    """Get the best available embedding function."""
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if openai_api_key:
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=openai_api_key,
            model_name="text-embedding-3-small"
        )
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )


class UserDataRAG:
    """
    RAG system for user-specific travel data.

    Uses a single ChromaDB collection with user_id metadata filtering
    so each user's data is isolated during retrieval.
    """

    def __init__(self, persist_directory: Optional[str] = None):
        if persist_directory is None:
            persist_directory = str(Path(settings.BASE_DIR) / 'data' / 'chromadb_user')

        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        self.embedding_fn = _get_embedding_function()
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_fn,
            metadata={"description": "User-specific travel data for chat RAG"}
        )

        logger.info(f"UserDataRAG initialized (collection: {COLLECTION_NAME})")

    # ─── Indexing ────────────────────────────────────────────────────────

    def index_user_data(self, user) -> int:
        """
        Index (or re-index) all travel data for a given user.
        Deletes existing user documents first, then re-inserts fresh ones.

        Returns the number of chunks indexed.
        """
        user_id = str(user.id)

        # Delete existing user documents
        try:
            existing = self.collection.get(where={"user_id": user_id})
            if existing and existing['ids']:
                self.collection.delete(ids=existing['ids'])
                logger.info(f"Deleted {len(existing['ids'])} old chunks for user {user_id}")
        except Exception as e:
            logger.warning(f"Could not delete old user data: {e}")

        # Gather all text chunks + metadata
        chunks: List[Dict[str, Any]] = []
        chunks.extend(self._chunks_from_bookings(user))
        chunks.extend(self._chunks_from_itineraries(user))
        chunks.extend(self._chunks_from_feedback(user))
        chunks.extend(self._chunks_from_sessions(user))
        chunks.extend(self._chunks_from_profile(user))

        if not chunks:
            logger.info(f"No data to index for user {user_id}")
            return 0

        # Prepare for ChromaDB upsert
        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            doc_id = hashlib.md5(
                f"{user_id}_{chunk['data_type']}_{chunk['record_id']}_{chunk.get('sub_id', '')}".encode()
            ).hexdigest()
            ids.append(doc_id)
            documents.append(chunk['text'])
            metadatas.append({
                'user_id': user_id,
                'data_type': chunk['data_type'],
                'record_id': str(chunk['record_id']),
                'indexed_at': datetime.utcnow().isoformat(),
            })

        # Add in batches of 100 (ChromaDB limit)
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self.collection.add(
                ids=ids[i:i + batch_size],
                documents=documents[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size],
            )

        logger.info(f"Indexed {len(ids)} chunks for user {user_id}")

        # Mark user index as fresh in cache
        cache.set(f"user_rag_indexed_{user_id}", True, USER_INDEX_TTL)

        return len(ids)

    def _chunks_from_bookings(self, user) -> List[Dict[str, Any]]:
        """Convert user bookings to text chunks."""
        chunks = []
        try:
            from apps.bookings.models import Booking
            bookings = (
                Booking.objects.filter(user=user)
                .prefetch_related('items')
                .order_by('-booking_date')[:30]
            )

            for b in bookings:
                items_parts = []
                for item in b.items.all():
                    date_str = ''
                    if item.start_date:
                        date_str = f" on {item.start_date.strftime('%Y-%m-%d')}"
                        if item.end_date:
                            date_str += f" to {item.end_date.strftime('%Y-%m-%d')}"
                    items_parts.append(
                        f"{item.item_type}: {item.item_name}{date_str} (${item.total_price})"
                    )

                items_text = '; '.join(items_parts) if items_parts else 'no items yet'
                special = f" Special requests: {b.special_requests}" if b.special_requests else ''
                notes = f" Notes: {b.notes}" if b.notes else ''

                text = (
                    f"Booking #{b.booking_number} — status: {b.status}, "
                    f"total: ${b.total_amount} {b.currency}, "
                    f"traveler: {b.primary_traveler_name}, "
                    f"booked on: {b.booking_date.strftime('%Y-%m-%d')}. "
                    f"Items: {items_text}.{special}{notes}"
                )
                chunks.append({
                    'text': text,
                    'data_type': 'booking',
                    'record_id': b.id,
                })
        except Exception as e:
            logger.warning(f"Error indexing bookings: {e}")
        return chunks

    def _chunks_from_itineraries(self, user) -> List[Dict[str, Any]]:
        """Convert user itineraries (with days and items) to text chunks."""
        chunks = []
        try:
            from apps.itineraries.models import Itinerary
            itineraries = (
                Itinerary.objects.filter(user=user)
                .prefetch_related('days__items')
                .order_by('-created_at')[:20]
            )

            for it in itineraries:
                origin = it.origin_city or 'unknown origin'
                budget_str = f"${it.estimated_budget}" if it.estimated_budget else 'not set'
                spent_str = f"${it.actual_spent}" if it.actual_spent else '$0'
                desc = f" Description: {it.description[:500]}" if it.description else ''

                # Main itinerary chunk
                text = (
                    f"Trip plan: \"{it.title}\" — {origin} to {it.destination}, "
                    f"{it.start_date} to {it.end_date}, "
                    f"{it.number_of_travelers} traveler(s), status: {it.status}, "
                    f"budget: {budget_str}, spent: {spent_str}.{desc}"
                )
                chunks.append({
                    'text': text,
                    'data_type': 'itinerary',
                    'record_id': it.id,
                })

                # AI narrative chunk (often the richest text)
                if it.ai_narrative and len(it.ai_narrative.strip()) > 50:
                    narrative_text = (
                        f"AI narrative for trip \"{it.title}\" "
                        f"({origin} to {it.destination}, {it.start_date}): "
                        f"{it.ai_narrative[:2000]}"
                    )
                    chunks.append({
                        'text': narrative_text,
                        'data_type': 'itinerary_narrative',
                        'record_id': it.id,
                        'sub_id': 'narrative',
                    })

                # Day-level chunks (combine day + items into one chunk per day)
                for day in it.days.all():
                    day_parts = [
                        f"Day {day.day_number} ({day.date}) of \"{it.title}\" trip to {it.destination}"
                    ]
                    if day.title:
                        day_parts.append(f"— {day.title}")
                    if day.description:
                        day_parts.append(f". {day.description[:300]}")
                    if day.weather_condition:
                        day_parts.append(
                            f" Weather: {day.weather_condition}, "
                            f"{day.weather_temp_low}°–{day.weather_temp_high}°."
                        )

                    for item in day.items.all():
                        cost_str = f" (${item.estimated_cost})" if item.estimated_cost else ''
                        loc_str = f" at {item.location_name}" if item.location_name else ''
                        time_str = f" {item.start_time.strftime('%H:%M')}" if item.start_time else ''
                        day_parts.append(
                            f" • {item.item_type}: {item.title}{loc_str}{time_str}{cost_str}"
                        )

                    if day.notes:
                        day_parts.append(f" Notes: {day.notes[:200]}")

                    day_text = ''.join(day_parts)
                    if len(day_text) > 80:  # Only index if there's meaningful content
                        chunks.append({
                            'text': day_text,
                            'data_type': 'itinerary_day',
                            'record_id': it.id,
                            'sub_id': f'day_{day.day_number}',
                        })

        except Exception as e:
            logger.warning(f"Error indexing itineraries: {e}")
        return chunks

    def _chunks_from_feedback(self, user) -> List[Dict[str, Any]]:
        """Convert trip feedback to text chunks."""
        chunks = []
        try:
            from apps.itineraries.models import TripFeedback
            feedbacks = (
                TripFeedback.objects.filter(user=user)
                .select_related('itinerary')
                .order_by('-created_at')[:20]
            )

            for fb in feedbacks:
                trip_title = fb.itinerary.title if fb.itinerary else 'Unknown trip'
                dest = fb.itinerary.destination if fb.itinerary else ''
                parts = [
                    f"Trip feedback for \"{trip_title}\" to {dest}: "
                    f"overall rating {fb.overall_rating}/5."
                ]
                if fb.flight_rating:
                    parts.append(f" Flights: {fb.flight_rating}/5.")
                if fb.hotel_rating:
                    parts.append(f" Hotels: {fb.hotel_rating}/5.")
                if fb.activities_rating:
                    parts.append(f" Activities: {fb.activities_rating}/5.")
                if fb.food_rating:
                    parts.append(f" Food: {fb.food_rating}/5.")
                if fb.loved_most:
                    parts.append(f" Loved most: {fb.loved_most[:300]}")
                if fb.would_change:
                    parts.append(f" Would change: {fb.would_change[:300]}")
                if fb.additional_comments:
                    parts.append(f" Comments: {fb.additional_comments[:300]}")
                if fb.would_visit_again is not None:
                    parts.append(f" Would visit again: {'Yes' if fb.would_visit_again else 'No'}.")
                if fb.would_recommend is not None:
                    parts.append(f" Would recommend: {'Yes' if fb.would_recommend else 'No'}.")
                if fb.tags:
                    parts.append(f" Tags: {', '.join(fb.tags)}.")
                if fb.sentiment:
                    parts.append(f" Sentiment: {fb.sentiment}.")

                text = ''.join(parts)
                chunks.append({
                    'text': text,
                    'data_type': 'trip_feedback',
                    'record_id': fb.id,
                })
        except Exception as e:
            logger.warning(f"Error indexing feedback: {e}")
        return chunks

    def _chunks_from_sessions(self, user) -> List[Dict[str, Any]]:
        """Convert past AI agent sessions to text chunks."""
        chunks = []
        try:
            from apps.agents.models import AgentSession
            sessions = (
                AgentSession.objects.filter(user=user, status='completed')
                .order_by('-completed_at')[:10]
            )

            for s in sessions:
                intent = s.user_intent[:300] if s.user_intent else 'trip planning'
                entities = s.detected_entities or {}
                dest = entities.get('destination', '')
                origin = entities.get('origin', '')
                completed = s.completed_at.strftime('%Y-%m-%d') if s.completed_at else 'N/A'

                text = (
                    f"AI planning session (completed {completed}): "
                    f"\"{intent}\""
                    f"{' from ' + origin if origin else ''}"
                    f"{' to ' + dest if dest else ''}. "
                    f"Entities: {', '.join(f'{k}={v}' for k, v in entities.items() if v)}."
                )
                chunks.append({
                    'text': text,
                    'data_type': 'agent_session',
                    'record_id': s.id,
                })
        except Exception as e:
            logger.warning(f"Error indexing sessions: {e}")
        return chunks

    def _chunks_from_profile(self, user) -> List[Dict[str, Any]]:
        """Create a profile summary chunk."""
        chunks = []
        try:
            name = f"{user.first_name or ''} {user.last_name or ''}".strip() or 'Traveler'
            text = f"User profile: {name} ({user.email}). Member since {user.date_joined.strftime('%Y-%m-%d')}."
            chunks.append({
                'text': text,
                'data_type': 'profile',
                'record_id': user.id,
            })
        except Exception as e:
            logger.warning(f"Error indexing profile: {e}")
        return chunks

    # ─── Retrieval ───────────────────────────────────────────────────────

    def retrieve(
        self,
        user,
        query: str,
        n_results: int = 8,
        data_types: Optional[List[str]] = None,
    ) -> str:
        """
        Retrieve the most relevant user data chunks for a given query.

        Args:
            user: Django user object
            query: The user's chat message
            n_results: Number of chunks to retrieve
            data_types: Optional filter to specific data types

        Returns:
            A formatted string of relevant context to inject into the LLM prompt
        """
        user_id = str(user.id)

        # Ensure user data is indexed (lazy indexing with cache check)
        self._ensure_indexed(user)

        # Build filter
        where_filter: Dict[str, Any] = {"user_id": user_id}
        if data_types:
            where_filter = {
                "$and": [
                    {"user_id": user_id},
                    {"data_type": {"$in": data_types}},
                ]
            }

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
            )

            documents = results['documents'][0] if results['documents'] else []
            distances = results['distances'][0] if results['distances'] else []
            metadatas = results['metadatas'][0] if results['metadatas'] else []

            if not documents:
                return ''

            # Format retrieved context with relevance info
            context_parts = []
            for doc, dist, meta in zip(documents, distances, metadatas):
                data_type = meta.get('data_type', 'unknown')
                # ChromaDB distance: lower = more similar
                relevance = 'high' if dist < 0.5 else 'medium' if dist < 1.0 else 'low'
                context_parts.append(f"[{data_type}] {doc}")

            return '\n\n'.join(context_parts)

        except Exception as e:
            logger.error(f"RAG retrieval error for user {user_id}: {e}")
            return ''

    def _ensure_indexed(self, user):
        """Ensure user data is indexed. Uses cache to avoid re-indexing on every request."""
        user_id = str(user.id)
        cache_key = f"user_rag_indexed_{user_id}"

        if cache.get(cache_key):
            return  # Already indexed and fresh

        # Check if user has any documents in the collection
        try:
            existing = self.collection.get(
                where={"user_id": user_id},
                limit=1,
            )
            has_docs = bool(existing and existing['ids'])
        except Exception:
            has_docs = False

        if not has_docs:
            # First time — index everything
            self.index_user_data(user)
        else:
            # Re-index to pick up changes (in background would be ideal,
            # but for now we do it inline with a short TTL)
            self.index_user_data(user)

    # ─── Stats ───────────────────────────────────────────────────────────

    def get_user_stats(self, user) -> Dict[str, Any]:
        """Get indexing stats for a user."""
        user_id = str(user.id)
        try:
            existing = self.collection.get(where={"user_id": user_id})
            doc_count = len(existing['ids']) if existing and existing['ids'] else 0
            data_types = {}
            if existing and existing['metadatas']:
                for meta in existing['metadatas']:
                    dt = meta.get('data_type', 'unknown')
                    data_types[dt] = data_types.get(dt, 0) + 1
            return {
                'user_id': user_id,
                'total_chunks': doc_count,
                'data_types': data_types,
                'is_fresh': bool(cache.get(f"user_rag_indexed_{user_id}")),
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {'user_id': user_id, 'total_chunks': 0, 'error': str(e)}

    def delete_user_data(self, user) -> int:
        """Delete all indexed data for a user. Returns count of deleted chunks."""
        user_id = str(user.id)
        try:
            existing = self.collection.get(where={"user_id": user_id})
            if existing and existing['ids']:
                count = len(existing['ids'])
                self.collection.delete(ids=existing['ids'])
                cache.delete(f"user_rag_indexed_{user_id}")
                logger.info(f"Deleted {count} chunks for user {user_id}")
                return count
            return 0
        except Exception as e:
            logger.error(f"Error deleting user data: {e}")
            return 0


# ─── Global singleton ────────────────────────────────────────────────────

_user_data_rag: Optional[UserDataRAG] = None


def get_user_data_rag() -> UserDataRAG:
    """Get or create the global UserDataRAG instance."""
    global _user_data_rag
    if _user_data_rag is None:
        _user_data_rag = UserDataRAG()
    return _user_data_rag
