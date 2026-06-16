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

        sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
        token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
        from_number = getattr(settings, "TWILIO_FROM_NUMBER", "")
        if not (sid and token and from_number):
            logger.info("sms_not_configured", to=phone, body=body[:50])
            return False

        try:
            from twilio.rest import Client  # optional dependency
        except ImportError:
            logger.warning("sms_twilio_not_installed")
            return False

        try:
            Client(sid, token).messages.create(
                to=phone, from_=from_number, body=f"{title}\n{body}"[:1500]
            )
            logger.info("sms_notification_sent", to=phone)
            return True
        except Exception as exc:
            logger.error("sms_notification_failed", to=phone, error=str(exc))
            return False


class PushChannel:
    """Sends push notifications to a user's registered devices via FCM.

    No-ops cleanly when FCM is unconfigured or the user has no devices.
    """

    @staticmethod
    def send(*, recipient_id: str, title: str, body: str, data: dict | None = None, **kwargs) -> bool:
        from .models import PushDevice

        tokens = list(
            PushDevice.objects.filter(user_id=recipient_id, is_active=True)
            .values_list("token", flat=True)
        )
        if not tokens:
            logger.info("push_no_devices", recipient_id=recipient_id)
            return False

        server_key = getattr(settings, "FCM_SERVER_KEY", "")
        if not server_key:
            logger.info("push_not_configured", recipient_id=recipient_id, devices=len(tokens))
            return False

        try:
            import httpx
            resp = httpx.post(
                "https://fcm.googleapis.com/fcm/send",
                headers={"Authorization": f"key={server_key}", "Content-Type": "application/json"},
                json={"registration_ids": tokens, "notification": {"title": title, "body": body}, "data": data or {}},
                timeout=10,
            )
            ok = resp.status_code == 200
            logger.info("push_notification_sent", recipient_id=recipient_id, devices=len(tokens), ok=ok)
            return ok
        except Exception as exc:
            logger.error("push_notification_failed", recipient_id=recipient_id, error=str(exc))
            return False


class InAppChannel:
    """In-app notification — simply marks notification as sent (already persisted)."""

    @staticmethod
    def send(**kwargs) -> bool:
        return True
