"""
WebSocket consumers for real-time notifications.
"""
import json
import structlog
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

logger = structlog.get_logger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.

    Connect: ws://host/ws/notifications/?token=<jwt_token>
    Messages sent to client:
        - {"type": "new_notification", "notification": {...}}
        - {"type": "unread_count", "count": 5}
    """

    async def connect(self):
        user = self.scope.get("user")

        # Attempt token-based auth from query string if user is anonymous
        if not user or user.is_anonymous:
            user = await self._authenticate_from_token()
            if not user:
                await self.close(code=4001)
                return
            self.scope["user"] = user

        self.user_id = str(user.id)
        self.group_name = f"user_{self.user_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send initial unread count
        count = await self._get_unread_count()
        await self.send_json({"type": "unread_count", "count": count})

        logger.info("ws_connected", user_id=self.user_id)

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            logger.info("ws_disconnected", user_id=self.user_id)

    async def receive_json(self, content, **kwargs):
        """Handle incoming messages from the client."""
        msg_type = content.get("type")

        if msg_type == "mark_read":
            notification_id = content.get("notification_id")
            if notification_id:
                await self._mark_notification_read(notification_id)
                count = await self._get_unread_count()
                await self.send_json({"type": "unread_count", "count": count})

        elif msg_type == "mark_all_read":
            await self._mark_all_read()
            await self.send_json({"type": "unread_count", "count": 0})

    # ── Channel layer handlers (called via group_send) ──

    async def new_notification(self, event):
        """Forward new notification to WebSocket client."""
        await self.send_json({
            "type": "new_notification",
            "notification": event["notification"],
        })

    async def unread_count_update(self, event):
        """Forward unread count update to WebSocket client."""
        await self.send_json({
            "type": "unread_count",
            "count": event["count"],
        })

    # ── Helper methods ──

    async def _authenticate_from_token(self):
        """Authenticate via JWT token in query string."""
        query_string = self.scope.get("query_string", b"").decode()
        params = dict(p.split("=", 1) for p in query_string.split("&") if "=" in p)
        token = params.get("token")

        if not token:
            return None

        return await self._validate_token(token)

    @database_sync_to_async
    def _validate_token(self, token):
        """Validate JWT token and return User."""
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            access = AccessToken(token)
            from apps.accounts.models import User
            return User.objects.get(pk=access["user_id"])
        except Exception:
            pass

        try:
            from django.contrib.auth import authenticate
            user = authenticate(token=token)
            return user
        except Exception:
            return None

    @database_sync_to_async
    def _get_unread_count(self):
        from apps.notifications.models import Notification
        return Notification.objects.filter(
            recipient_id=self.user_id, is_read=False
        ).count()

    @database_sync_to_async
    def _mark_notification_read(self, notification_id):
        from apps.notifications.models import Notification
        from django.utils import timezone
        Notification.objects.filter(
            pk=notification_id, recipient_id=self.user_id, is_read=False
        ).update(is_read=True, read_at=timezone.now())

    @database_sync_to_async
    def _mark_all_read(self):
        from apps.notifications.models import Notification
        from django.utils import timezone
        Notification.objects.filter(
            recipient_id=self.user_id, is_read=False
        ).update(is_read=True, read_at=timezone.now())
