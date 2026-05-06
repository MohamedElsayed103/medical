"""
Audit models — stored in the **public** schema for cross-tenant visibility.

AuditLog    Immutable, append-only log of all significant actions.
"""
import uuid

from django.db import models

from common.enums import AuditAction


class AuditLog(models.Model):
    """
    Immutable audit trail entry.

    No update/delete methods exposed. Records are append-only.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # Who
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    user_email = models.EmailField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # What
    action = models.CharField(max_length=20, choices=AuditAction.choices, db_index=True)
    resource_type = models.CharField(max_length=100, db_index=True, help_text="e.g., Patient, Invoice")
    resource_id = models.CharField(max_length=36, blank=True, db_index=True)
    description = models.TextField(blank=True)

    # Context
    tenant_schema = models.CharField(max_length=63, blank=True, db_index=True)
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text='{"field": {"old": ..., "new": ...}}',
    )
    request_id = models.CharField(max_length=36, blank=True, help_text="Correlation ID")

    class Meta:
        db_table = "audit_log"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user_id", "timestamp"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["tenant_schema", "timestamp"]),
        ]

    def __str__(self):
        return f"Audit({self.action} {self.resource_type} {self.resource_id})"

    def save(self, **kwargs):
        # Enforce immutability: only allow insert, never update
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise ValueError("AuditLog records are immutable. Updates are not allowed.")
        super().save(**kwargs)

    def delete(self, **kwargs):
        raise ValueError("AuditLog records cannot be deleted.")
