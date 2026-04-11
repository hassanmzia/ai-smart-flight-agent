"""
Collaborative Filtering Service
Finds similar users based on Travel DNA profiles, generates
"people like you" recommendations, social proof, and enjoyment predictions.
"""
import hashlib
import json
import logging
import os
import random

from django.conf import settings

logger = logging.getLogger(__name__)

# Weights for similarity dimensions
SIMILARITY_WEIGHTS = {
    'trip_style': 0.20,
    'budget_range': 0.15,
    'pace': 0.15,
    'preferred_cuisines': 0.15,
    'faith': 0.10,
    'dietary_preference': 0.10,
    'mobility': 0.10,
    'languages_spoken': 0.05,
}


class CollaborativeFilterService:
    """Collaborative filtering for travel recommendations based on user similarity."""

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_similar_users(user, limit=5):
        """
        Find users with the most similar Travel DNA profiles.

        Calculates a weighted similarity score (0-1) across trip_style,
        budget_range, pace, preferred_cuisines, faith, dietary_preference,
        mobility, and languages_spoken.

        Returns
        -------
        dict with 'success' key and list of similar user dicts.
        """
        from apps.agents.models import UserPreference

        try:
            try:
                user_pref = UserPreference.objects.get(user=user)
            except UserPreference.DoesNotExist:
                return {
                    'success': True,
                    'similar_users': [],
                    'message': 'No preferences found for this user. '
                               'Complete your Travel DNA profile first.',
                }

            # Fetch all other users' preferences
            other_prefs = (
                UserPreference.objects
                .exclude(user=user)
                .select_related('user')
            )

            if not other_prefs.exists():
                return {
                    'success': True,
                    'similar_users': [],
                    'message': 'No other users found for comparison.',
                }

            scored_users = []
            for other_pref in other_prefs:
                similarity = CollaborativeFilterService._calculate_similarity(
                    user_pref, other_pref,
                )
                common_traits = CollaborativeFilterService._find_common_traits(
                    user_pref, other_pref,
                )
                scored_users.append({
                    'user_id': other_pref.user.id,
                    'username': getattr(other_pref.user, 'username', '')
                                or getattr(other_pref.user, 'email', ''),
                    'similarity_score': round(similarity, 4),
                    'common_traits': common_traits,
                })

            # Sort by similarity descending
            scored_users.sort(key=lambda x: x['similarity_score'], reverse=True)

            return {
                'success': True,
                'similar_users': scored_users[:limit],
            }
        except Exception as e:
            logger.error("Failed to get similar users for user %s: %s", user, e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_people_like_you_recommendations(user, limit=10):
        """
        Get destinations that similar users loved but the current user hasn't visited.

        Finds similar users, collects their highly-rated TripMemory destinations
        (rating >= 4), excludes already-visited destinations, and ranks by
        weighted score (similarity * rating).

        Returns
        -------
        dict with 'success' key and list of recommendation dicts.
        """
        from apps.agents.models import TripMemory

        try:
            # Get similar users
            similar_result = CollaborativeFilterService.get_similar_users(user, limit=10)
            if not similar_result.get('success'):
                return similar_result

            similar_users = similar_result.get('similar_users', [])
            if not similar_users:
                return {
                    'success': True,
                    'recommendations': [],
                    'message': 'No similar users found to base recommendations on.',
                }

            # Get destinations the current user has already visited
            visited_destinations = set(
                TripMemory.objects.filter(user=user)
                .values_list('destination', flat=True)
            )

            # Collect highly-rated destinations from similar users
            similar_user_ids = [su['user_id'] for su in similar_users]
            similarity_map = {su['user_id']: su['similarity_score'] for su in similar_users}

            high_rated_memories = (
                TripMemory.objects
                .filter(user_id__in=similar_user_ids, rating__gte=4)
                .select_related('user')
            )

            # Aggregate destination scores
            destination_data = {}
            for memory in high_rated_memories:
                dest = memory.destination
                if dest in visited_destinations:
                    continue

                sim_score = similarity_map.get(memory.user_id, 0)
                weighted_score = sim_score * memory.rating

                if dest not in destination_data:
                    destination_data[dest] = {
                        'destination': dest,
                        'total_weighted_score': 0.0,
                        'recommended_by_count': 0,
                        'ratings': [],
                        'recommenders': [],
                    }

                destination_data[dest]['total_weighted_score'] += weighted_score
                destination_data[dest]['recommended_by_count'] += 1
                destination_data[dest]['ratings'].append(memory.rating)
                username = getattr(memory.user, 'username', '')
                if username:
                    destination_data[dest]['recommenders'].append(username)

            # Build recommendation list
            recommendations = []
            for dest, data in destination_data.items():
                avg_rating = sum(data['ratings']) / len(data['ratings'])
                score = data['total_weighted_score'] / data['recommended_by_count']
                recommendations.append({
                    'destination': dest,
                    'score': round(score, 2),
                    'recommended_by_count': data['recommended_by_count'],
                    'avg_rating': round(avg_rating, 2),
                    'why': f"Recommended by {data['recommended_by_count']} traveler(s) "
                           f"similar to you with an average rating of {avg_rating:.1f}/5.",
                })

            # Sort by score descending
            recommendations.sort(key=lambda x: x['score'], reverse=True)

            return {
                'success': True,
                'recommendations': recommendations[:limit],
            }
        except Exception as e:
            logger.error(
                "Failed to get people-like-you recommendations for user %s: %s",
                user, e,
            )
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_social_proof(destination):
        """
        Get community stats for a destination.

        Returns total visits, average rating, percentage who loved it
        (rating >= 4), and common traveler profiles (most common trip_style,
        budget_range, pace among visitors).

        Returns
        -------
        dict with 'success' key and social proof stats.
        """
        from apps.agents.models import TripMemory, UserPreference

        try:
            memories = TripMemory.objects.filter(destination__iexact=destination)
            total_visits = memories.count()

            if total_visits == 0:
                return {
                    'success': True,
                    'destination': destination,
                    'total_visits': 0,
                    'avg_rating': 0,
                    'loved_percentage': 0,
                    'common_profiles': {},
                    'message': 'No visit data available for this destination.',
                }

            # Calculate average rating (only for memories with ratings > 0)
            rated_memories = memories.filter(rating__gt=0)
            if rated_memories.exists():
                from django.db.models import Avg
                avg_rating = rated_memories.aggregate(avg=Avg('rating'))['avg'] or 0
            else:
                avg_rating = 0

            # Percentage who loved it (rating >= 4)
            loved_count = memories.filter(rating__gte=4).count()
            loved_percentage = round((loved_count / total_visits) * 100, 1)

            # Common traveler profiles among visitors
            visitor_user_ids = list(
                memories.values_list('user_id', flat=True).distinct()
            )
            visitor_prefs = UserPreference.objects.filter(user_id__in=visitor_user_ids)

            trip_styles = []
            budget_ranges = []
            paces = []
            for pref in visitor_prefs:
                if pref.trip_style:
                    trip_styles.append(pref.trip_style)
                if pref.budget_range:
                    budget_ranges.append(pref.budget_range)
                if pref.pace:
                    paces.append(pref.pace)

            from collections import Counter

            common_profiles = {}
            if trip_styles:
                common_profiles['most_common_trip_style'] = Counter(trip_styles).most_common(1)[0][0]
            if budget_ranges:
                common_profiles['most_common_budget_range'] = Counter(budget_ranges).most_common(1)[0][0]
            if paces:
                common_profiles['most_common_pace'] = Counter(paces).most_common(1)[0][0]

            return {
                'success': True,
                'destination': destination,
                'total_visits': total_visits,
                'avg_rating': round(float(avg_rating), 2),
                'loved_percentage': loved_percentage,
                'common_profiles': common_profiles,
            }
        except Exception as e:
            logger.error("Failed to get social proof for %s: %s", destination, e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_enjoyment_prediction(user, destination):
        """
        Predict how much a user will enjoy a destination.

        Combines:
        (a) Similar users' ratings at the destination
        (b) Match against the destination's top visitor profile
        (c) AI rating breakdown vs user preferences

        Returns
        -------
        dict with 'success' key, predicted_score (1-10), confidence, and factors.
        """
        from apps.agents.models import TripMemory, UserPreference

        try:
            try:
                user_pref = UserPreference.objects.get(user=user)
            except UserPreference.DoesNotExist:
                return {
                    'success': True,
                    'predicted_score': 5.0,
                    'confidence': 'low',
                    'factors': [
                        'No Travel DNA profile found. Prediction based on general data.',
                    ],
                }

            factors = []
            scores = []
            weights = []

            # (a) Similar users' ratings at this destination
            similar_result = CollaborativeFilterService.get_similar_users(user, limit=10)
            similar_users = similar_result.get('similar_users', []) if similar_result.get('success') else []

            if similar_users:
                similar_user_ids = [su['user_id'] for su in similar_users]
                similar_memories = TripMemory.objects.filter(
                    user_id__in=similar_user_ids,
                    destination__iexact=destination,
                    rating__gt=0,
                )

                if similar_memories.exists():
                    similarity_map = {
                        su['user_id']: su['similarity_score'] for su in similar_users
                    }
                    weighted_sum = 0.0
                    weight_sum = 0.0
                    for mem in similar_memories:
                        sim = similarity_map.get(mem.user_id, 0.5)
                        weighted_sum += mem.rating * sim
                        weight_sum += sim

                    if weight_sum > 0:
                        collaborative_score = (weighted_sum / weight_sum) * 2  # Scale 1-5 to 1-10
                        scores.append(collaborative_score)
                        weights.append(0.4)
                        factors.append(
                            f"Similar travelers rated {destination} "
                            f"{weighted_sum / weight_sum:.1f}/5 on average."
                        )

            # (b) Match against destination's top visitor profile
            social_result = CollaborativeFilterService.get_social_proof(destination)
            if social_result.get('success') and social_result.get('total_visits', 0) > 0:
                common_profiles = social_result.get('common_profiles', {})
                profile_match_score = 0.0
                profile_checks = 0

                if common_profiles.get('most_common_trip_style'):
                    profile_checks += 1
                    if user_pref.trip_style == common_profiles['most_common_trip_style']:
                        profile_match_score += 1.0
                        factors.append(
                            f"Your trip style ({user_pref.trip_style}) matches "
                            f"most visitors to {destination}."
                        )

                if common_profiles.get('most_common_budget_range'):
                    profile_checks += 1
                    if user_pref.budget_range == common_profiles['most_common_budget_range']:
                        profile_match_score += 1.0
                        factors.append(
                            f"Your budget range ({user_pref.budget_range}) matches "
                            f"most visitors to {destination}."
                        )

                if common_profiles.get('most_common_pace'):
                    profile_checks += 1
                    if user_pref.pace == common_profiles['most_common_pace']:
                        profile_match_score += 1.0
                        factors.append(
                            f"Your travel pace ({user_pref.pace}) matches "
                            f"most visitors to {destination}."
                        )

                if profile_checks > 0:
                    profile_score = (profile_match_score / profile_checks) * 10
                    scores.append(profile_score)
                    weights.append(0.25)

                # Use loved percentage as a signal
                loved_pct = social_result.get('loved_percentage', 0)
                if loved_pct > 0:
                    community_score = min(loved_pct / 10, 10)
                    scores.append(community_score)
                    weights.append(0.1)
                    factors.append(
                        f"{loved_pct}% of visitors loved {destination}."
                    )

            # (c) AI rating breakdown vs user preferences
            try:
                from apps.reviews.models import AIRating

                ai_rating = AIRating.objects.filter(
                    destination__iexact=destination,
                    entity_type='destination',
                ).first()

                if ai_rating:
                    ai_scores = []
                    if ai_rating.overall_score:
                        ai_scores.append(float(ai_rating.overall_score))
                    if ai_rating.safety_score:
                        ai_scores.append(float(ai_rating.safety_score))
                    if ai_rating.value_score:
                        ai_scores.append(float(ai_rating.value_score))

                    # Weight food score higher for food-oriented travelers
                    if ai_rating.food_score:
                        cuisines = user_pref.preferred_cuisines or []
                        if cuisines:
                            ai_scores.append(float(ai_rating.food_score))
                            factors.append(
                                f"Food score: {ai_rating.food_score}/10 "
                                f"(important given your cuisine preferences)."
                            )
                        else:
                            ai_scores.append(float(ai_rating.food_score))

                    if ai_rating.culture_score:
                        ai_scores.append(float(ai_rating.culture_score))
                        if user_pref.trip_style == 'cultural':
                            factors.append(
                                f"Culture score: {ai_rating.culture_score}/10 "
                                f"(great match for your cultural travel style)."
                            )

                    if ai_rating.accessibility_score:
                        ai_scores.append(float(ai_rating.accessibility_score))
                        if user_pref.mobility != 'full':
                            factors.append(
                                f"Accessibility score: {ai_rating.accessibility_score}/10 "
                                f"(relevant for your mobility needs)."
                            )

                    if ai_scores:
                        ai_avg = sum(ai_scores) / len(ai_scores)
                        scores.append(ai_avg)
                        weights.append(0.25)
                        factors.append(
                            f"AI quality rating: {ai_rating.overall_score}/10."
                        )
            except Exception as exc:
                logger.warning("AI rating lookup failed for %s: %s", destination, exc)

            # Combine scores
            if scores and weights:
                total_weight = sum(weights)
                predicted_score = sum(
                    s * w for s, w in zip(scores, weights)
                ) / total_weight
                predicted_score = max(1.0, min(10.0, round(predicted_score, 1)))
            else:
                predicted_score = 5.0
                factors.append(
                    'Limited data available. Prediction based on general popularity.'
                )

            # Determine confidence
            data_points = len(scores)
            if data_points >= 3:
                confidence = 'high'
            elif data_points >= 2:
                confidence = 'medium'
            else:
                confidence = 'low'

            return {
                'success': True,
                'destination': destination,
                'predicted_score': predicted_score,
                'confidence': confidence,
                'factors': factors,
            }
        except Exception as e:
            logger.error(
                "Failed to predict enjoyment for user %s at %s: %s",
                user, destination, e,
            )
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  Private helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _calculate_similarity(pref_a, pref_b):
        """
        Compute weighted similarity between two UserPreference objects.

        Weights:
            trip_style       0.20
            budget_range     0.15
            pace             0.15
            preferred_cuisines 0.15
            faith            0.10
            dietary_preference 0.10
            mobility         0.10
            languages_spoken 0.05

        Returns
        -------
        float between 0 and 1.
        """
        score = 0.0

        # Exact-match dimensions
        if pref_a.trip_style == pref_b.trip_style:
            score += SIMILARITY_WEIGHTS['trip_style']

        if pref_a.budget_range == pref_b.budget_range:
            score += SIMILARITY_WEIGHTS['budget_range']

        if pref_a.pace == pref_b.pace:
            score += SIMILARITY_WEIGHTS['pace']

        if pref_a.faith == pref_b.faith:
            score += SIMILARITY_WEIGHTS['faith']

        if pref_a.dietary_preference == pref_b.dietary_preference:
            score += SIMILARITY_WEIGHTS['dietary_preference']

        if pref_a.mobility == pref_b.mobility:
            score += SIMILARITY_WEIGHTS['mobility']

        # Set-overlap dimensions (Jaccard similarity)
        cuisines_sim = CollaborativeFilterService._jaccard_similarity(
            pref_a.preferred_cuisines or [],
            pref_b.preferred_cuisines or [],
        )
        score += cuisines_sim * SIMILARITY_WEIGHTS['preferred_cuisines']

        languages_sim = CollaborativeFilterService._jaccard_similarity(
            pref_a.languages_spoken or [],
            pref_b.languages_spoken or [],
        )
        score += languages_sim * SIMILARITY_WEIGHTS['languages_spoken']

        return score

    @staticmethod
    def _jaccard_similarity(list_a, list_b):
        """
        Compute Jaccard similarity between two lists.

        Jaccard = |A ∩ B| / |A ∪ B|

        Returns
        -------
        float between 0 and 1.  Returns 0 if both lists are empty.
        """
        set_a = set(list_a) if list_a else set()
        set_b = set(list_b) if list_b else set()

        if not set_a and not set_b:
            return 0.0

        intersection = set_a & set_b
        union = set_a | set_b

        return len(intersection) / len(union)

    @staticmethod
    def _find_common_traits(pref_a, pref_b):
        """
        Identify common traits between two UserPreference objects.

        Returns
        -------
        list of descriptive strings for matching traits.
        """
        common = []

        if pref_a.trip_style == pref_b.trip_style:
            common.append(f"Same trip style: {pref_a.trip_style}")

        if pref_a.budget_range == pref_b.budget_range:
            common.append(f"Same budget range: {pref_a.budget_range}")

        if pref_a.pace == pref_b.pace:
            common.append(f"Same pace: {pref_a.pace}")

        if pref_a.faith == pref_b.faith and pref_a.faith != 'none':
            common.append(f"Same faith: {pref_a.faith}")

        if pref_a.dietary_preference == pref_b.dietary_preference and pref_a.dietary_preference != 'none':
            common.append(f"Same dietary preference: {pref_a.dietary_preference}")

        if pref_a.mobility == pref_b.mobility and pref_a.mobility != 'full':
            common.append(f"Same mobility: {pref_a.mobility}")

        # Overlapping cuisines
        shared_cuisines = set(pref_a.preferred_cuisines or []) & set(pref_b.preferred_cuisines or [])
        if shared_cuisines:
            common.append(f"Shared cuisines: {', '.join(sorted(shared_cuisines))}")

        # Overlapping languages
        shared_languages = set(pref_a.languages_spoken or []) & set(pref_b.languages_spoken or [])
        if shared_languages:
            common.append(f"Shared languages: {', '.join(sorted(shared_languages))}")

        return common
