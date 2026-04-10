from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend

from .models import Review, Rating, AIRating
from .serializers import ReviewSerializer, RatingSerializer, AIRatingSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for Review model."""
    queryset = Review.objects.filter(status='approved')
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['content_type', 'object_id', 'rating', 'is_verified_purchase']
    ordering = ['-created_at']

    def get_queryset(self):
        if self.request.user.is_staff:
            return Review.objects.all()
        if self.request.user.is_authenticated and self.action in ['list', 'retrieve']:
            return Review.objects.filter(status='approved')
        return Review.objects.filter(status='approved')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_helpful(self, request, pk=None):
        """Mark review as helpful."""
        review = self.get_object()
        review.helpful_count += 1
        review.save()
        return Response({'helpful_count': review.helpful_count})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_not_helpful(self, request, pk=None):
        """Mark review as not helpful."""
        review = self.get_object()
        review.not_helpful_count += 1
        review.save()
        return Response({'not_helpful_count': review.not_helpful_count})


class RatingViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Rating model."""
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['review', 'aspect']


class AIRatingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for AI-generated quality ratings.

    list / retrieve — browse existing AI ratings.
    rate (POST)     — request a new AI rating for an entity.
    predict (GET)   — get a personalized enjoyment prediction.
    """

    queryset = AIRating.objects.all()
    serializer_class = AIRatingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['entity_type', 'destination']
    search_fields = ['entity_name', 'destination']
    ordering_fields = ['overall_score', 'created_at']
    ordering = ['-overall_score']

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def rate(self, request):
        """
        Generate an AI quality rating for an entity.

        Expects: entity_type, entity_name, destination
        """
        entity_type = request.data.get('entity_type')
        entity_name = request.data.get('entity_name')
        destination = request.data.get('destination')

        if not all([entity_type, entity_name, destination]):
            return Response(
                {'error': 'entity_type, entity_name, and destination are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_types = [choice[0] for choice in AIRating.ENTITY_TYPE_CHOICES]
        if entity_type not in valid_types:
            return Response(
                {'error': f'entity_type must be one of: {", ".join(valid_types)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from apps.agents.services.rating_agent import RatingAgent
            agent = RatingAgent()
            ai_rating = agent.rate_entity(entity_type, entity_name, destination)
            serializer = self.get_serializer(ai_rating)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Rating generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def predict(self, request):
        """
        Predict how much the authenticated user would enjoy an entity.

        Query params: entity_type, entity_name, destination
        """
        entity_type = request.query_params.get('entity_type')
        entity_name = request.query_params.get('entity_name')
        destination = request.query_params.get('destination')

        if not all([entity_type, entity_name, destination]):
            return Response(
                {'error': 'entity_type, entity_name, and destination query params are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_types = [choice[0] for choice in AIRating.ENTITY_TYPE_CHOICES]
        if entity_type not in valid_types:
            return Response(
                {'error': f'entity_type must be one of: {", ".join(valid_types)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from apps.agents.services.rating_agent import RatingAgent
            agent = RatingAgent()
            prediction = agent.predict_enjoyment(
                request.user, entity_type, entity_name, destination,
            )
            return Response(prediction, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Prediction failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
