"""
Pharmacy service layer.
"""
import structlog
from django.db import transaction
from django.utils import timezone

from common.exceptions import ServiceError

from .models import (
    DispenseItem,
    DispenseRecord,
    DispenseStatus,
    PharmacyInventory,
    StockTransaction,
    StockTransactionType,
)

logger = structlog.get_logger(__name__)


class PharmacyService:

    @staticmethod
    @transaction.atomic
    def receive_stock(
        *,
        inventory: PharmacyInventory,
        quantity: int,
        performed_by_id: str,
        reference: str = "",
        reason: str = "",
    ) -> StockTransaction:
        """Add stock to inventory."""
        if quantity <= 0:
            raise ServiceError("Quantity must be positive.", code="INVALID_QUANTITY")

        inventory.quantity_on_hand += quantity
        inventory.save(update_fields=["quantity_on_hand", "updated_at"])

        txn = StockTransaction.objects.create(
            inventory=inventory,
            transaction_type=StockTransactionType.RECEIVED,
            quantity=quantity,
            balance_after=inventory.quantity_on_hand,
            reference=reference,
            reason=reason,
            performed_by_id=performed_by_id,
        )

        logger.info(
            "stock_received",
            inventory_id=str(inventory.id),
            medication=inventory.medication.name,
            quantity=quantity,
            new_balance=inventory.quantity_on_hand,
        )
        return txn

    @staticmethod
    @transaction.atomic
    def adjust_stock(
        *,
        inventory: PharmacyInventory,
        quantity: int,
        performed_by_id: str,
        reason: str,
    ) -> StockTransaction:
        """Manual stock adjustment (positive or negative)."""
        new_balance = inventory.quantity_on_hand + quantity
        if new_balance < 0:
            raise ServiceError(
                f"Adjustment would result in negative stock ({new_balance}).",
                code="NEGATIVE_STOCK",
            )

        inventory.quantity_on_hand = new_balance
        inventory.save(update_fields=["quantity_on_hand", "updated_at"])

        txn = StockTransaction.objects.create(
            inventory=inventory,
            transaction_type=StockTransactionType.ADJUSTED,
            quantity=quantity,
            balance_after=new_balance,
            reason=reason,
            performed_by_id=performed_by_id,
        )

        logger.info(
            "stock_adjusted",
            inventory_id=str(inventory.id),
            adjustment=quantity,
            new_balance=new_balance,
        )
        return txn

    @staticmethod
    @transaction.atomic
    def dispense_prescription(
        *,
        prescription,
        dispensed_by_id: str,
        notes: str = "",
    ) -> DispenseRecord:
        """
        Dispense a prescription — deducts inventory and creates records.
        Also marks the prescription as dispensed.
        """
        if prescription.is_dispensed:
            raise ServiceError(
                "Prescription already dispensed.", code="ALREADY_DISPENSED"
            )

        record = DispenseRecord.objects.create(
            prescription=prescription,
            status=DispenseStatus.DISPENSED,
            dispensed_by_id=dispensed_by_id,
            dispensed_at=timezone.now(),
            notes=notes,
        )

        for item in prescription.items.select_related("medication"):
            # Find available inventory (FEFO — First Expiry, First Out)
            inv = (
                PharmacyInventory.objects.filter(
                    medication=item.medication,
                    is_active=True,
                    quantity_on_hand__gte=item.quantity,
                )
                .order_by("expiry_date")
                .select_for_update()
                .first()
            )

            if not inv:
                raise ServiceError(
                    f"Insufficient stock for {item.medication.name} "
                    f"(need {item.quantity}).",
                    code="INSUFFICIENT_STOCK",
                )

            # Deduct inventory
            inv.quantity_on_hand -= item.quantity
            inv.save(update_fields=["quantity_on_hand", "updated_at"])

            # Create dispense item
            DispenseItem.objects.create(
                dispense_record=record,
                medication=item.medication,
                inventory=inv,
                quantity_dispensed=item.quantity,
                batch_number=inv.batch_number,
            )

            # Stock transaction
            StockTransaction.objects.create(
                inventory=inv,
                transaction_type=StockTransactionType.DISPENSED,
                quantity=-item.quantity,
                balance_after=inv.quantity_on_hand,
                reference=str(prescription.id),
                performed_by_id=dispensed_by_id,
            )

        # Mark prescription as dispensed
        prescription.is_dispensed = True
        prescription.dispensed_at = timezone.now()
        prescription.save(update_fields=["is_dispensed", "dispensed_at", "updated_at"])

        logger.info(
            "prescription_dispensed_via_pharmacy",
            prescription_id=str(prescription.id),
            dispense_record_id=str(record.id),
            item_count=record.items.count(),
        )
        return record

    @staticmethod
    def get_low_stock_items():
        """Return inventory items at or below reorder level."""
        from django.db.models import F
        return PharmacyInventory.objects.filter(
            is_active=True,
            quantity_on_hand__lte=F("reorder_level"),
        ).select_related("medication")

    @staticmethod
    def get_expiring_stock(days: int = 30):
        """Return inventory expiring within given days."""
        from datetime import timedelta
        cutoff = timezone.now().date() + timedelta(days=days)
        return PharmacyInventory.objects.filter(
            is_active=True,
            expiry_date__lte=cutoff,
            quantity_on_hand__gt=0,
        ).select_related("medication")
