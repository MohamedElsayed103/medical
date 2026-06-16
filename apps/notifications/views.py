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
    filterset_fields = ["is_read"]

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

    @action(detail=False, methods=["post"], url_path="register-device")
    def register_device(self, request):
        """POST /api/v1/notifications/register-device/ — store a push token for this user."""
        from .models import PushDevice
        token = request.data.get("token")
        if not token:
            return Response({"error": {"code": "NO_TOKEN", "message": "token is required"}},
                            status=status.HTTP_400_BAD_REQUEST)
        device, _ = PushDevice.objects.update_or_create(
            user_id=request.user.id, token=token,
            defaults={"platform": request.data.get("platform", "web"), "is_active": True},
        )
        return Response({"id": str(device.id), "platform": device.platform}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="unregister-device")
    def unregister_device(self, request):
        """POST /api/v1/notifications/unregister-device/ — deactivate a push token."""
        from .models import PushDevice
        token = request.data.get("token")
        PushDevice.objects.filter(user_id=request.user.id, token=token).update(is_active=False)
        return Response(status=status.HTTP_204_NO_CONTENT)


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
