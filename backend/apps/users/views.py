import os
import uuid

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import update_session_auth_hash
from django.conf import settings

from .models import User, UserProfile, TravelHistory
from .serializers import (
    UserSerializer,
    UserDetailSerializer,
    UserRegistrationSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    UserProfileSerializer,
    TravelHistorySerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model.
    Provides CRUD operations for users.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    filterset_fields = ['is_active', 'is_verified', 'date_joined']
    ordering_fields = ['date_joined', 'email', 'last_login']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filter queryset to only show authenticated user's data unless staff."""
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['get', 'put', 'patch'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get or update current user's profile."""
        user = request.user

        if request.method == 'GET':
            serializer = UserDetailSerializer(user)
            return Response(serializer.data)

        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = UserUpdateSerializer(user, data=request.data, partial=partial)
            if serializer.is_valid():
                serializer.save()
                return Response(UserDetailSerializer(user).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Change user's password."""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            # Update session to prevent logout
            update_session_auth_hash(request, user)
            return Response({'message': 'Password updated successfully.'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def deactivate(self, request, pk=None):
        """Deactivate a user account."""
        user = self.get_object()

        # Only allow users to deactivate their own account or staff to deactivate any
        if user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to deactivate this account.'},
                status=status.HTTP_403_FORBIDDEN
            )

        user.is_active = False
        user.save()
        return Response({'message': 'Account deactivated successfully.'}, status=status.HTTP_200_OK)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserProfile model.
    Provides CRUD operations for user profiles.
    """

    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['preferred_currency', 'preferred_language', 'preferred_travel_class']
    ordering_fields = ['created_at', 'total_trips', 'total_flights']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter queryset to only show authenticated user's profile unless staff."""
        if self.request.user.is_staff:
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get', 'put', 'patch'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get or update current user's profile."""
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist
            profile = UserProfile.objects.create(user=request.user)

        if request.method == 'GET':
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)

        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = UserProfileSerializer(profile, data=request.data, partial=partial)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated],
            parser_classes=[MultiPartParser, FormParser])
    def upload_avatar(self, request):
        """Upload a profile picture. Saves to media/avatars/ and returns the URL."""
        avatar_file = request.FILES.get('avatar')
        if not avatar_file:
            return Response({'error': 'No avatar file provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if avatar_file.content_type not in allowed_types:
            return Response({'error': 'Invalid file type. Use JPEG, PNG, GIF, or WebP.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Validate file size (max 5MB)
        if avatar_file.size > 5 * 1024 * 1024:
            return Response({'error': 'File too large. Maximum size is 5MB.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Save to media/avatars/
        avatars_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
        os.makedirs(avatars_dir, exist_ok=True)

        ext = os.path.splitext(avatar_file.name)[1] or '.jpg'
        filename = f"{request.user.id}_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(avatars_dir, filename)

        with open(filepath, 'wb+') as dest:
            for chunk in avatar_file.chunks():
                dest.write(chunk)

        avatar_url = f"{settings.MEDIA_URL}avatars/{filename}"

        # Update profile
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)

        profile.avatar = avatar_url
        profile.save(update_fields=['avatar'])

        return Response({'success': True, 'avatar_url': avatar_url}, status=status.HTTP_200_OK)


class TravelHistoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TravelHistory model.
    Provides CRUD operations for travel history.
    """

    queryset = TravelHistory.objects.all()
    serializer_class = TravelHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['destination_city', 'destination_country', 'origin_city', 'origin_country']
    filterset_fields = ['trip_type', 'destination_country', 'departure_date']
    ordering_fields = ['departure_date', 'return_date', 'created_at']
    ordering = ['-departure_date']

    def get_queryset(self):
        """Filter queryset to only show authenticated user's travel history unless staff."""
        if self.request.user.is_staff:
            return TravelHistory.objects.all()
        return TravelHistory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the user when creating travel history."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def destinations(self, request):
        """Get list of unique destinations visited."""
        travel_history = self.get_queryset()
        destinations = travel_history.values('destination_city', 'destination_country').distinct()
        return Response(destinations)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def stats(self, request):
        """Get travel statistics for the user."""
        travel_history = self.get_queryset()
        total_trips = travel_history.count()
        countries = travel_history.values('destination_country').distinct().count()
        cities = travel_history.values('destination_city').distinct().count()

        return Response({
            'total_trips': total_trips,
            'countries_visited': countries,
            'cities_visited': cities,
        })
