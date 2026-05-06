from django.contrib import admin

from .models import AIRequest


@admin.register(AIRequest)
class AIRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "request_type", "status", "requested_by_id", "latency_ms", "requested_at"]
    list_filter = ["request_type", "status"]
    readonly_fields = ["input_data", "output_data"]
