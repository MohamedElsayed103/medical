"""
Audit signals — auto-log model changes for models with AUDITED = True.
"""
import structlog
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from common.enums import AuditAction

from .middleware import get_audit_context
from .services import AuditService

logger = structlog.get_logger(__name__)


def _is_audited(instance) -> bool:
    return getattr(instance.__class__, "AUDITED", False)


def _get_changes(instance) -> dict:
    """
    Build a changes dict from the instance's dirty fields.
    Falls back to empty if the model doesn't track dirty fields.
    """
    if hasattr(instance, "get_dirty_fields"):
        dirty = instance.get_dirty_fields()
        return {
            field: {"old": str(old_val), "new": str(getattr(instance, field, ""))}
            for field, old_val in dirty.items()
        }
    return {}


@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    if not _is_audited(instance):
        return

    ctx = get_audit_context()
    action = AuditAction.CREATE if created else AuditAction.UPDATE

    AuditService.log(
        action=action,
        resource_type=sender.__name__,
        resource_id=str(instance.pk),
        user_id=ctx.get("user_id"),
        user_email=ctx.get("user_email", ""),
        ip_address=ctx.get("ip_address"),
        user_agent=ctx.get("user_agent", ""),
        description=f"{'Created' if created else 'Updated'} {sender.__name__} {instance.pk}",
        changes=_get_changes(instance) if not created else {},
        request_id=ctx.get("request_id", ""),
    )


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    if not _is_audited(instance):
        return

    ctx = get_audit_context()

    AuditService.log(
        action=AuditAction.DELETE,
        resource_type=sender.__name__,
        resource_id=str(instance.pk),
        user_id=ctx.get("user_id"),
        user_email=ctx.get("user_email", ""),
        ip_address=ctx.get("ip_address"),
        user_agent=ctx.get("user_agent", ""),
        description=f"Deleted {sender.__name__} {instance.pk}",
        request_id=ctx.get("request_id", ""),
    )
