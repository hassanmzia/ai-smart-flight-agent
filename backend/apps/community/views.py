from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import DestinationMedia, TravelStory, TravelTip, DestinationInfo, CuratedGuide
from .serializers import (
    DestinationMediaSerializer,
    TravelStorySerializer,
    TravelTipSerializer,
    DestinationInfoSerializer,
    CuratedGuideSerializer,
)


class DestinationMediaViewSet(viewsets.ModelViewSet):
    """
    CRUD viewset for user-uploaded destination media.
    Supports multipart file upload for photos, audio, videos, PDFs, and documents.
    """

    queryset = DestinationMedia.objects.filter(is_approved=True)
    serializer_class = DestinationMediaSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['destination', 'media_type']
    search_fields = ['title', 'description', 'destination']
    ordering_fields = ['created_at', 'upvotes']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = DestinationMedia.objects.all()
        if self.request.user.is_staff:
            return qs
        if self.request.user.is_authenticated:
            if self.action in ['update', 'partial_update', 'destroy']:
                return qs.filter(user=self.request.user)
            # Signed-in users see approved content PLUS their own uploads
            # (even if still pending moderation) so they can see what they
            # just submitted.
            return qs.filter(Q(is_approved=True) | Q(user=self.request.user))
        return qs.filter(is_approved=True)

    def perform_create(self, serializer):
        # Auto-approve the user's own upload so they can see it immediately.
        # Admins can still unapprove/flag content later; the default-approved
        # behavior keeps the UX usable without a moderation queue.
        serializer.save(user=self.request.user, is_approved=True)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def upvote(self, request, pk=None):
        """Increment the upvote count for a media item."""
        media = self.get_object()
        media.upvotes += 1
        media.save(update_fields=['upvotes'])
        return Response({'upvotes': media.upvotes}, status=status.HTTP_200_OK)


class TravelStoryViewSet(viewsets.ModelViewSet):
    """
    CRUD viewset for user travel stories.
    Supports filtering by destination and language.
    """

    queryset = TravelStory.objects.filter(is_approved=True)
    serializer_class = TravelStorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['destination', 'language']
    search_fields = ['title', 'content', 'destination']
    ordering_fields = ['created_at', 'upvotes', 'rating']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = TravelStory.objects.all()
        if self.request.user.is_staff:
            return qs
        if self.request.user.is_authenticated:
            if self.action in ['update', 'partial_update', 'destroy']:
                return qs.filter(user=self.request.user)
            return qs.filter(Q(is_approved=True) | Q(user=self.request.user))
        return qs.filter(is_approved=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, is_approved=True)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def upvote(self, request, pk=None):
        """Increment the upvote count for a travel story."""
        story = self.get_object()
        story.upvotes += 1
        story.save(update_fields=['upvotes'])
        return Response({'upvotes': story.upvotes}, status=status.HTTP_200_OK)


class TravelTipViewSet(viewsets.ModelViewSet):
    """
    CRUD viewset for travel tips.
    Supports filtering by destination and category.
    """

    queryset = TravelTip.objects.filter(is_approved=True)
    serializer_class = TravelTipSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['destination', 'category']
    search_fields = ['title', 'content', 'destination']
    ordering_fields = ['created_at', 'upvotes']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = TravelTip.objects.all()
        if self.request.user.is_staff:
            return qs
        if self.request.user.is_authenticated:
            if self.action in ['update', 'partial_update', 'destroy']:
                return qs.filter(user=self.request.user)
            return qs.filter(Q(is_approved=True) | Q(user=self.request.user))
        return qs.filter(is_approved=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, is_approved=True)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def upvote(self, request, pk=None):
        """Increment the upvote count for a travel tip."""
        tip = self.get_object()
        tip.upvotes += 1
        tip.save(update_fields=['upvotes'])
        return Response({'upvotes': tip.upvotes}, status=status.HTTP_200_OK)


class DestinationInfoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for curated destination information.
    """

    queryset = DestinationInfo.objects.all()
    serializer_class = DestinationInfoSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['destination', 'country']
    search_fields = ['destination', 'country', 'summary']


class CuratedGuideViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for AI-curated must-visit/eat/see guides.
    Supports generating new guides and filtering by destination.
    """

    queryset = CuratedGuide.objects.all()
    serializer_class = CuratedGuideSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['destination', 'guide_type']
    search_fields = ['destination', 'title', 'description']

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def generate(self, request):
        """
        Generate a curated guide for a destination.

        POST body: {"destination": "Paris", "guide_type": "must_eat"}
        """
        destination = request.data.get('destination')
        guide_type = request.data.get('guide_type')

        if not destination:
            return Response(
                {'error': 'destination is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_types = [choice[0] for choice in CuratedGuide.GUIDE_TYPE_CHOICES]
        if not guide_type:
            return Response(
                {'error': f'guide_type is required. Valid types: {valid_types}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if guide_type not in valid_types:
            return Response(
                {'error': f'Invalid guide_type. Must be one of: {valid_types}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from apps.agents.services.guide_agent import GuideAgent
            agent = GuideAgent()
            guide = agent.generate_guide(destination, guide_type)
            serializer = self.get_serializer(guide)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Guide generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def by_destination(self, request):
        """
        Return all curated guides for a given destination.

        GET /curated-guides/by_destination/?destination=Paris
        """
        destination = request.query_params.get('destination')
        if not destination:
            return Response(
                {'error': 'destination query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        guides = CuratedGuide.objects.filter(destination__iexact=destination)
        serializer = self.get_serializer(guides, many=True)
        return Response({
            'destination': destination,
            'guides': serializer.data,
            'count': guides.count(),
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def destination_content(request, destination):
    """
    Aggregated view returning all community content for a destination:
    media, stories, tips, and destination info.
    """
    media = DestinationMedia.objects.filter(
        destination__iexact=destination, is_approved=True,
    )
    stories = TravelStory.objects.filter(
        destination__iexact=destination, is_approved=True,
    )
    tips = TravelTip.objects.filter(
        destination__iexact=destination, is_approved=True,
    )
    info = DestinationInfo.objects.filter(
        destination__iexact=destination,
    ).first()
    guides = CuratedGuide.objects.filter(
        destination__iexact=destination,
    )

    return Response({
        'destination': destination,
        'info': DestinationInfoSerializer(info).data if info else None,
        'media': DestinationMediaSerializer(media, many=True).data,
        'stories': TravelStorySerializer(stories, many=True).data,
        'tips': TravelTipSerializer(tips, many=True).data,
        'guides': CuratedGuideSerializer(guides, many=True).data,
        'counts': {
            'media': media.count(),
            'stories': stories.count(),
            'tips': tips.count(),
            'guides': guides.count(),
        },
    })
