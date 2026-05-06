"""
Notification serializers.
"""
from rest_framework import serializers

from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "channel",
            "title",
            "body",
            "data",
            "is_read",
            "read_at",
            "is_sent",
            "sent_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "notification_type",
            "channel",
            "title",
            "body",
            "data",
            "is_sent",
            "sent_at",
            "created_at",
        ]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "id",
            "email_enabled",
            "sms_enabled",
            "push_enabled",
            "in_app_enabled",
            "quiet_hours_start",
            "quiet_hours_end",
        ]
        read_only_fields = ["id"]
