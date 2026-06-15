"""
Billing Celery tasks.
"""
import structlog
from celery import shared_task
from django.utils import timezone

from common.enums import InvoiceStatus

logger = structlog.get_logger(__name__)


@shared_task(name="apps.billing.tasks.mark_overdue_invoices")
def mark_overdue_invoices():
    """
    Daily task: marks invoices as OVERDUE when due_date < today
    and status is ISSUED or PARTIALLY_PAID.
    Works across all tenant schemas when django-tenants is installed.
    """
    try:
        from django_tenants.utils import get_tenant_model, schema_context

        TenantModel = get_tenant_model()
        tenants = TenantModel.objects.exclude(schema_name="public")
        for tenant in tenants:
            with schema_context(tenant.schema_name):
                _mark_overdue_for_current_schema()
    except ImportError:
        _mark_overdue_for_current_schema()


def _mark_overdue_for_current_schema():
    from .models import Invoice

    today = timezone.now().date()
    updated = Invoice.objects.filter(
        due_date__lt=today,
        status__in=[InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID],
        is_deleted=False,
    ).update(status=InvoiceStatus.OVERDUE, updated_at=timezone.now())

    if updated:
        logger.info("invoices_marked_overdue", count=updated)
    return updated
