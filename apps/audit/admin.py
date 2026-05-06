from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["id", "timestamp", "action", "resource_type", "resource_id", "user_email", "tenant_schema"]
    list_filter = ["action", "resource_type", "tenant_schema"]
    search_fields = ["resource_id", "user_email", "description"]
    date_hierarchy = "timestamp"
    readonly_fields = [
        "id", "timestamp", "user_id", "user_email", "ip_address", "user_agent",
        "action", "resource_type", "resource_id", "description", "tenant_schema",
        "changes", "request_id",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
