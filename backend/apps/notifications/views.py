from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend

from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationPreferenceSerializer


class IsAuthenticatedOrEmpty(IsAuthenticatedOrReadOnly):
    """
    Permission class that returns empty results for unauthenticated users
    instead of 401 error. This allows the frontend to load gracefully.
    """
    def has_permission(self, request, view):
        # Allow all GET requests (will return empty queryset for anonymous users)
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        # Require authentication for modifications
        return request.user and request.user.is_authenticated


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for Notification model."""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticatedOrEmpty]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['notification_type', 'priority', 'is_read']
    ordering = ['-created_at']

    def get_queryset(self):
        # Return empty queryset for anonymous users instead of error
        if not self.request.user.is_authenticated:
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        return Response(self.get_serializer(notification).data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        from django.utils import timezone
        self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({'status': 'success'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications. Returns 0 for anonymous users."""
        if not request.user.is_authenticated:
            return Response({'unread_count': 0})
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """ViewSet for NotificationPreference model."""
    queryset = NotificationPreference.objects.all()
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get', 'put'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get or update current user's notification preferences."""
        preference, created = NotificationPreference.objects.get_or_create(user=request.user)

        if request.method == 'GET':
            serializer = self.get_serializer(preference)
            return Response(serializer.data)

        elif request.method == 'PUT':
            serializer = self.get_serializer(preference, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
