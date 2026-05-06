"""
Notification views.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet, mixins

from apps.accounts.permissions import IsTenantMember

from .models import Notification, NotificationPreference
from .serializers import NotificationPreferenceSerializer, NotificationSerializer
from .services import NotificationService


class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    """
    /api/v1/notifications/

    Lists the authenticated user's notifications.
    Custom actions: mark_read, mark_all_read, unread_count
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsTenantMember]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Notification.objects.filter(recipient_id=self.request.user.id)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification = NotificationService.mark_read(notification)
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        count = NotificationService.mark_all_read(str(request.user.id))
        return Response({"marked_read": count})

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = NotificationService.get_unread_count(str(request.user.id))
        return Response({"unread_count": count})


class NotificationPreferenceViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    """
    /api/v1/notification-preferences/

    Singleton per user — retrieve and update their notification preferences.
    """

    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsTenantMember]

    def get_object(self):
        obj, _ = NotificationPreference.objects.get_or_create(user_id=self.request.user.id)
        return obj

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response(NotificationPreferenceSerializer(instance).data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = NotificationPreferenceSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
