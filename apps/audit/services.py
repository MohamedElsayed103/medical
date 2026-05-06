"""
Audit service.
"""
import structlog
from django.db import connection

from .models import AuditLog

logger = structlog.get_logger(__name__)


class AuditService:

    @staticmethod
    def log(
        *,
        action: str,
        resource_type: str,
        resource_id: str = "",
        user_id: str | None = None,
        user_email: str = "",
        ip_address: str | None = None,
        user_agent: str = "",
        description: str = "",
        changes: dict | None = None,
        request_id: str = "",
    ) -> AuditLog:
        tenant_schema = getattr(connection, "schema_name", "public")

        entry = AuditLog.objects.create(
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            description=description,
            tenant_schema=tenant_schema,
            changes=changes or {},
            request_id=request_id,
        )
        logger.info(
            "audit_logged",
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
        )
        return entry
