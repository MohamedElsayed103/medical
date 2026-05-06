"""
Audit serializers.
"""
from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "timestamp",
            "user_id",
            "user_email",
            "ip_address",
            "action",
            "resource_type",
            "resource_id",
            "description",
            "tenant_schema",
            "changes",
            "request_id",
        ]
