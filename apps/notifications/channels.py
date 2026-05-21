"""
Notification channel adapters.

Each adapter implements ``send(recipient_id, title, body, data)``
returning a bool indicating success.  The adapter is responsible for
resolving any channel-specific recipient info (email, phone, etc.).
"""
import structlog
from django.core.mail import send_mail
from django.conf import settings

logger = structlog.get_logger(__name__)


def _get_user_model():
    from django.contrib.auth import get_user_model
    return get_user_model()


class EmailChannel:
    """Sends notification via Django email backend."""

    @staticmethod
    def send(*, recipient_id: str, title: str, body: str, data: dict | None = None, **kwargs) -> bool:
        User = _get_user_model()
        try:
            user = User.objects.get(pk=recipient_id)
        except User.DoesNotExist:
            logger.warning("email_recipient_not_found", recipient_id=recipient_id)
            return False

        if not user.email:
            logger.warning("email_recipient_no_email", recipient_id=recipient_id)
            return False

        try:
            send_mail(
                subject=title,
                message=body,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@healthsaas.com"),
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info("email_notification_sent", to=user.email, title=title)
            return True
        except Exception as exc:
            logger.error("email_notification_failed", to=user.email, error=str(exc))
            return False


class SMSChannel:
    """Sends notification via SMS (integration placeholder)."""

    @staticmethod
    def send(*, recipient_id: str, title: str, body: str, data: dict | None = None, **kwargs) -> bool:
        User = _get_user_model()
        try:
            user = User.objects.get(pk=recipient_id)
        except User.DoesNotExist:
            logger.warning("sms_recipient_not_found", recipient_id=recipient_id)
            return False

        phone = getattr(user, "phone", None)
        if not phone:
            logger.warning("sms_recipient_no_phone", recipient_id=recipient_id)
            return False

        # TODO: Integrate with Twilio / AWS SNS
        logger.info("sms_notification_sent", to=phone, body=body[:50])
        return True


class PushChannel:
    """Sends push notification (integration placeholder)."""

    @staticmethod
    def send(*, recipient_id: str, title: str, body: str, data: dict | None = None, **kwargs) -> bool:
        # TODO: Integrate with FCM / APNs — requires device_token storage
        logger.info("push_notification_queued", recipient_id=recipient_id, title=title)
        return True


class InAppChannel:
    """In-app notification — simply marks notification as sent (already persisted)."""

    @staticmethod
    def send(**kwargs) -> bool:
        return True
