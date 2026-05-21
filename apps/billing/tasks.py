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
    """
    from .models import Invoice

    today = timezone.now().date()
    updated = Invoice.objects.filter(
        due_date__lt=today,
        status__in=[InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID],
    ).update(status=InvoiceStatus.OVERDUE, updated_at=timezone.now())

    logger.info("overdue_invoices_marked", count=updated)
    return updated
