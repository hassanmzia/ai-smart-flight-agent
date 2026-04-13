from rest_framework import serializers
from .models import Itinerary, ItineraryDay, ItineraryItem, Weather, TripFeedback


class ItineraryItemSerializer(serializers.ModelSerializer):
    """Serializer for ItineraryItem model."""
    item_type_display = serializers.CharField(source='get_item_type_display', read_only=True)
    # Collaboration tallies derived from the JSON ``votes`` field.
    vote_summary = serializers.SerializerMethodField()

    class Meta:
        model = ItineraryItem
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'vote_summary']

    def get_vote_summary(self, obj):
        votes = obj.votes or {}
        up, down = 0, 0
        for v in votes.values():
            if v == 1 or v == '1':
                up += 1
            elif v == -1 or v == '-1':
                down += 1
        request = self.context.get('request') if hasattr(self, 'context') else None
        my_vote = 0
        if request and request.user and request.user.is_authenticated:
            my_vote = int(votes.get((request.user.email or '').lower(), 0) or 0)
        return {'up': up, 'down': down, 'my_vote': my_vote}


class ItineraryDaySerializer(serializers.ModelSerializer):
    """Serializer for ItineraryDay model."""
    items = ItineraryItemSerializer(many=True, read_only=True)

    class Meta:
        model = ItineraryDay
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ItinerarySerializer(serializers.ModelSerializer):
    """Serializer for Itinerary model."""
    days = ItineraryDaySerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_days = serializers.IntegerField(read_only=True)
    # Trip-level "I'm in / I'm out" tallies derived from the ``confirmations`` JSON.
    confirmation_summary = serializers.SerializerMethodField()

    class Meta:
        model = Itinerary
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'confirmation_summary']

    def get_confirmation_summary(self, obj):
        confs = obj.confirmations or {}
        # Pool of expected confirmers: owner + every email in shared_with.
        pool = set()
        try:
            owner_email = (obj.user.email or '').lower()
            if owner_email:
                pool.add(owner_email)
        except Exception:
            owner_email = ''
        for e in (obj.shared_with or []):
            if isinstance(e, str) and e:
                pool.add(e.lower())
        in_count = sum(1 for v in confs.values() if v == 'in')
        out_count = sum(1 for v in confs.values() if v == 'out')
        responded = {k.lower() for k in confs.keys()}
        pending = max(0, len(pool) - len(responded.intersection(pool)))
        request = self.context.get('request') if hasattr(self, 'context') else None
        my_status = 'pending'
        if request and request.user and request.user.is_authenticated:
            email = (request.user.email or '').lower()
            my_status = confs.get(email, 'pending')
        return {
            'in': in_count,
            'out': out_count,
            'pending': pending,
            'total': len(pool),
            'my_status': my_status,
            'all_in': bool(pool) and in_count == len(pool),
        }


class TripFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for TripFeedback model."""
    sentiment_display = serializers.CharField(source='get_sentiment_display', read_only=True)

    class Meta:
        model = TripFeedback
        fields = '__all__'
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at',
            # NLP fields are computed by the backend
            'sentiment', 'sentiment_score', 'emotions',
            'is_toxic', 'toxicity_score', 'extracted_topics',
            'learned_preferences',
        ]


class WeatherSerializer(serializers.ModelSerializer):
    """Serializer for Weather model."""

    class Meta:
        model = Weather
        fields = '__all__'
        read_only_fields = ['id', 'fetched_at']
