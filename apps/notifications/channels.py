"""
Notification channel adapters.

Each adapter implements ``send(recipient_id, title, body, data)``
returning a bool indicating success.
"""
import structlog

logger = structlog.get_logger(__name__)


class EmailChannel:
    """Sends notification via email (integration placeholder)."""

    @staticmethod
    def send(*, recipient_email: str, title: str, body: str, **kwargs) -> bool:
        # TODO: Integrate with email backend (SendGrid / SES / SMTP)
        logger.info("email_notification_sent", to=recipient_email, title=title)
        return True


class SMSChannel:
    """Sends notification via SMS (integration placeholder)."""

    @staticmethod
    def send(*, phone_number: str, body: str, **kwargs) -> bool:
        # TODO: Integrate with Twilio / AWS SNS
        logger.info("sms_notification_sent", to=phone_number)
        return True


class PushChannel:
    """Sends push notification (integration placeholder)."""

    @staticmethod
    def send(*, device_token: str, title: str, body: str, data: dict | None = None, **kwargs) -> bool:
        # TODO: Integrate with FCM / APNs
        logger.info("push_notification_sent", token=device_token[:10], title=title)
        return True


class InAppChannel:
    """In-app notification — simply marks notification as sent (already persisted)."""

    @staticmethod
    def send(**kwargs) -> bool:
        return True
