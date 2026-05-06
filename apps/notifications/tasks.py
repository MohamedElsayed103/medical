"""
Celery tasks for async notification dispatch.
"""
from celery import shared_task

from .services import NotificationService


@shared_task(
    name="notifications.send_notification",
    queue="notifications",
    max_retries=3,
    default_retry_delay=60,
)
def send_notification_task(
    *,
    recipient_id: str,
    notification_type: str,
    title: str,
    body: str,
    channel: str = "in_app",
    data: dict | None = None,
):
    """Async notification dispatch — called from other services."""
    NotificationService.create_and_send(
        recipient_id=recipient_id,
        notification_type=notification_type,
        title=title,
        body=body,
        channel=channel,
        data=data,
    )
