"""
Notification service layer.
"""
import structlog
from django.utils import timezone

from django.utils.timezone import localtime

from common.enums import NotificationChannel

from .channels import EmailChannel, InAppChannel, PushChannel, SMSChannel
from .models import Notification, NotificationPreference

logger = structlog.get_logger(__name__)

CHANNEL_ADAPTERS = {
    NotificationChannel.EMAIL: EmailChannel,
    NotificationChannel.SMS: SMSChannel,
    NotificationChannel.PUSH: PushChannel,
    NotificationChannel.IN_APP: InAppChannel,
}


class NotificationService:

    @staticmethod
    def create_and_send(
        *,
        recipient_id: str,
        notification_type: str,
        title: str,
        body: str,
        channel: str = NotificationChannel.IN_APP,
        data: dict | None = None,
    ) -> Notification:
        """
        Create a notification record and dispatch it through the appropriate channel.
        Respects user preferences.
        """
        prefs = NotificationPreference.objects.filter(user_id=recipient_id).first()
        if prefs and not prefs.is_channel_enabled(channel):
            logger.info(
                "notification_channel_disabled",
                recipient_id=recipient_id,
                channel=channel,
            )
            channel = NotificationChannel.IN_APP

        # Respect quiet hours — downgrade to in_app during quiet hours
        if prefs and prefs.quiet_hours_start and prefs.quiet_hours_end:
            now_time = localtime(timezone.now()).time()
            start = prefs.quiet_hours_start
            end = prefs.quiet_hours_end
            in_quiet = (
                (start <= now_time or now_time < end)
                if start > end  # overnight range (e.g., 22:00 - 07:00)
                else (start <= now_time < end)
            )
            if in_quiet and channel != NotificationChannel.IN_APP:
                logger.info(
                    "notification_quiet_hours",
                    recipient_id=recipient_id,
                    channel=channel,
                )
                channel = NotificationChannel.IN_APP

        notification = Notification.objects.create(
            recipient_id=recipient_id,
            notification_type=notification_type,
            channel=channel,
            title=title,
            body=body,
            data=data or {},
        )

        adapter = CHANNEL_ADAPTERS.get(channel)
        if adapter:
            sent = adapter.send(
                recipient_id=recipient_id,
                title=title,
                body=body,
                data=data,
            )
            if sent:
                notification.is_sent = True
                notification.sent_at = timezone.now()
                notification.save(update_fields=["is_sent", "sent_at", "updated_at"])

        # Push real-time WebSocket event
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"user_{recipient_id}",
                    {
                        "type": "new_notification",
                        "notification": {
                            "id": str(notification.id),
                            "title": title,
                            "body": body,
                            "notification_type": notification_type,
                            "channel": channel,
                            "is_read": False,
                            "created_at": notification.created_at.isoformat(),
                            "data": data or {},
                        },
                    },
                )
        except Exception as exc:
            logger.warning("ws_notification_failed", error=str(exc))

        return notification

    @staticmethod
    def mark_read(notification: Notification) -> Notification:
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at", "updated_at"])
        return notification

    @staticmethod
    def mark_all_read(recipient_id: str) -> int:
        return Notification.objects.filter(
            recipient_id=recipient_id, is_read=False
        ).update(is_read=True, read_at=timezone.now())

    @staticmethod
    def get_unread_count(recipient_id: str) -> int:
        return Notification.objects.filter(
            recipient_id=recipient_id, is_read=False
        ).count()
