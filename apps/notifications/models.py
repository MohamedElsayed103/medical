"""
Notification models — tenant-scoped.

Notification            Notification record for a user.
NotificationPreference  Per-user channel preferences.
"""
from django.db import models

from common.enums import NotificationChannel, NotificationType
from common.models import BaseModel


class Notification(BaseModel):
    """A notification addressed to a specific user within a tenant."""

    recipient_id = models.UUIDField(db_index=True, help_text="User ID of the recipient")
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices)
    channel = models.CharField(max_length=10, choices=NotificationChannel.choices)
    title = models.CharField(max_length=255)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True, help_text="Arbitrary payload (e.g., deeplink info)")
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)

    class Meta:
        db_table = "notifications_notification"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient_id", "is_read"]),
            models.Index(fields=["notification_type"]),
        ]

    def __str__(self):
        return f"Notification({self.title[:30]})"


class NotificationPreference(BaseModel):
    """Per-user notification channel preferences."""

    user_id = models.UUIDField(unique=True, help_text="User ID from public schema")
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications_preference"

    def __str__(self):
        return f"Prefs({self.user_id})"

    def is_channel_enabled(self, channel: str) -> bool:
        mapping = {
            NotificationChannel.EMAIL: self.email_enabled,
            NotificationChannel.SMS: self.sms_enabled,
            NotificationChannel.PUSH: self.push_enabled,
            NotificationChannel.IN_APP: self.in_app_enabled,
        }
        return mapping.get(channel, True)
