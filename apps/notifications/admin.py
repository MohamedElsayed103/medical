from django.contrib import admin

from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["id", "recipient_id", "notification_type", "channel", "is_read", "is_sent", "created_at"]
    list_filter = ["notification_type", "channel", "is_read", "is_sent"]


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ["user_id", "email_enabled", "sms_enabled", "push_enabled", "in_app_enabled"]
