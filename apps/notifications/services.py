"""
Notification service layer.
"""
import structlog
from django.utils import timezone

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
            sent = adapter.send(title=title, body=body, data=data)
            if sent:
                notification.is_sent = True
                notification.sent_at = timezone.now()
                notification.save(update_fields=["is_sent", "sent_at", "updated_at"])

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
