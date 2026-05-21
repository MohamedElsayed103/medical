"""
Pharmacy Celery tasks.
"""
import structlog
from celery import shared_task
from django.utils import timezone

logger = structlog.get_logger(__name__)


@shared_task(name="apps.pharmacy.tasks.check_low_stock_alerts")
def check_low_stock_alerts():
    """Daily task: send notifications for items below reorder level."""
    from django.db.models import F
    from .models import PharmacyInventory

    low_items = PharmacyInventory.objects.filter(
        is_active=True,
        quantity_on_hand__lte=F("reorder_level"),
    ).select_related("medication")

    count = low_items.count()
    if count > 0:
        logger.warning("low_stock_alert", item_count=count)
        # In future: send notification to pharmacy staff
    return count


@shared_task(name="apps.pharmacy.tasks.check_expiring_stock")
def check_expiring_stock():
    """Daily task: alert on items expiring within 30 days."""
    from datetime import timedelta
    from .models import PharmacyInventory

    cutoff = timezone.now().date() + timedelta(days=30)
    expiring = PharmacyInventory.objects.filter(
        is_active=True,
        expiry_date__lte=cutoff,
        quantity_on_hand__gt=0,
    ).select_related("medication")

    count = expiring.count()
    if count > 0:
        logger.warning("expiring_stock_alert", item_count=count, cutoff=str(cutoff))
    return count
