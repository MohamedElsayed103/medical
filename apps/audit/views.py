"""
Audit views — read-only access to audit logs.
"""
from rest_framework.viewsets import GenericViewSet, mixins

from apps.accounts.permissions import IsOwnerOrAdmin

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    """
    /api/v1/audit-logs/

    Read-only. Only org admins can access.
    Supports filtering by action, resource_type, user_id, date range.
    """

    serializer_class = AuditLogSerializer
    permission_classes = [IsOwnerOrAdmin]
    ordering = ["-timestamp"]
    filterset_fields = ["action", "resource_type", "user_id", "tenant_schema"]

    def get_queryset(self):
        return AuditLog.objects.all()
