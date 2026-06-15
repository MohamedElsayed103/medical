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


def _notify_pharmacists(*, title: str, body: str, data: dict = None):
    """Notify all active pharmacists via in-app notification."""
    import logging as _logging
    _logger = _logging.getLogger(__name__)
    try:
        from apps.rbac.models import TenantUser, TenantUserStatus
        from apps.notifications.services import NotificationService
        from common.enums import NotificationType, NotificationChannel

        pharmacist_ids = (
            TenantUser.objects.filter(
                status=TenantUserStatus.ACTIVE,
                is_deleted=False,
                role__role_permissions__permission__name="pharmacy:write",
                role__role_permissions__is_deleted=False,
            )
            .values_list("user_id", flat=True)
            .distinct()
        )
        for uid in pharmacist_ids:
            try:
                NotificationService.create_and_send(
                    recipient_id=str(uid),
                    notification_type=NotificationType.SYSTEM,
                    title=title,
                    body=body,
                    channel=NotificationChannel.IN_APP,
                    data=data or {},
                )
            except Exception as e:
                _logger.warning("pharmacist_notify_failed uid=%s err=%s", uid, e)
    except Exception as e:
        _logger.warning("_notify_pharmacists_failed: %s", e)


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
    @transaction.atomic
    def _deduct_fefo(*, medication, quantity: int, performed_by_id: str, reference: str = ""):
        """FEFO stock deduction with low-stock notifications."""
        from django.db.models import Sum

        before_total = (
            PharmacyInventory.objects.filter(medication=medication, is_active=True)
            .aggregate(s=Sum("quantity_on_hand"))["s"] or 0
        )

        remaining = quantity
        batches = (
            PharmacyInventory.objects.filter(
                medication=medication, is_active=True, quantity_on_hand__gt=0
            )
            .order_by("expiry_date")
            .select_for_update()
        )

        for batch in batches:
            if remaining <= 0:
                break
            take = min(batch.quantity_on_hand, remaining)
            batch.quantity_on_hand -= take
            batch.save(update_fields=["quantity_on_hand", "updated_at"])

            StockTransaction.objects.create(
                inventory=batch,
                transaction_type=StockTransactionType.DISPENSED,
                quantity=-take,
                balance_after=batch.quantity_on_hand,
                reference=reference,
                performed_by_id=performed_by_id,
            )
            remaining -= take

        if remaining > 0:
            raise ServiceError(
                f"Insufficient stock for {medication.name}. Need {quantity} more.",
                code="INSUFFICIENT_STOCK",
            )

        after_total = (
            PharmacyInventory.objects.filter(medication=medication, is_active=True)
            .aggregate(s=Sum("quantity_on_hand"))["s"] or 0
        )

        reorder_level = (
            PharmacyInventory.objects.filter(medication=medication, is_active=True)
            .values_list("reorder_level", flat=True)
            .first() or 10
        )

        if after_total == 0:
            _notify_pharmacists(
                title="Out of stock",
                body=f"{medication.name} is OUT OF STOCK.",
                data={"medication_id": str(medication.id)},
            )
        elif before_total > reorder_level >= after_total:
            _notify_pharmacists(
                title="Low stock — restock needed",
                body=f"{medication.name} is low ({after_total} left). Reorder suggested.",
                data={"medication_id": str(medication.id)},
            )

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


class PharmacyOrderService:

    @staticmethod
    @transaction.atomic
    def create_order(
        *,
        created_by_id: str,
        patient_id=None,
        customer_id=None,
        customer_name: str = "",
        customer_phone: str = "",
        prescription_id=None,
        items: list[dict],
        notes: str = "",
    ):
        from decimal import Decimal
        from apps.patients.models import Customer
        from apps.patients.services_customers import CustomerService
        from apps.prescriptions.models import Medication
        from common.validators import validate_orderer
        from common.utils import generate_order_number
        from .models import PharmacyOrder, PharmacyOrderItem

        customer = None
        if not patient_id:
            if customer_id:
                customer = Customer.objects.get(id=customer_id)
            elif customer_name and customer_phone:
                customer = CustomerService.get_or_create_by_phone(
                    full_name=customer_name, phone=customer_phone
                )
        validate_orderer(patient_id, customer.id if customer else None)

        order = PharmacyOrder.objects.create(
            order_number=generate_order_number("PH"),
            patient_id=patient_id,
            customer=customer,
            prescription_id=prescription_id,
            created_by_id=created_by_id,
            notes=notes,
        )

        for it in items:
            med = Medication.objects.get(id=it["medication_id"])
            inv_qs = PharmacyInventory.objects.filter(
                medication=med, is_active=True, quantity_on_hand__gt=0
            )
            default_price = inv_qs.order_by("expiry_date").values_list("unit_cost", flat=True).first() or Decimal("0")
            unit_price = Decimal(str(it.get("unit_price") or default_price))
            PharmacyOrderItem.objects.create(
                order=order, medication=med,
                quantity=it["quantity"], unit_price=unit_price,
            )

        return order

    @staticmethod
    @transaction.atomic
    def checkout(*, order, created_by_id: str):
        from .models import PharmacyOrderStatus
        from apps.billing.services import BillingService
        if order.status != PharmacyOrderStatus.DRAFT:
            raise ServiceError("Order is not in draft.", code="NOT_DRAFT")

        items = [
            {
                "item_type": "medication",
                "description": f"{i.medication.name} x{i.quantity}",
                "quantity": i.quantity,
                "unit_price": i.unit_price,
            }
            for i in order.items.select_related("medication")
        ]
        invoice = BillingService.create_from_source(
            source_type="pharmacy_order",
            source_id=str(order.id),
            patient=order.patient,
            customer=order.customer,
            items=items,
            created_by_id=created_by_id,
        )
        order.invoice = invoice
        order.status = PharmacyOrderStatus.AWAITING_PAYMENT
        order.save(update_fields=["invoice", "status", "updated_at"])
        return order

    @staticmethod
    @transaction.atomic
    def fulfill(*, order, performed_by_id: str):
        from .models import PharmacyOrderStatus
        if order.status not in (PharmacyOrderStatus.PAID, PharmacyOrderStatus.AWAITING_PAYMENT):
            raise ServiceError("Order not ready to fulfill.", code="NOT_PAYABLE")

        for item in order.items.select_related("medication"):
            PharmacyService._deduct_fefo(
                medication=item.medication,
                quantity=item.quantity,
                performed_by_id=performed_by_id,
                reference=order.order_number,
            )

        order.status = PharmacyOrderStatus.FULFILLED
        order.save(update_fields=["status", "updated_at"])
        return order

    @staticmethod
    @transaction.atomic
    def complete_sale(*, order, amount, method: str, received_by_id: str):
        """Checkout + record payment + fulfill in one step (counter sale)."""
        from apps.billing.services import BillingService
        from decimal import Decimal
        order = PharmacyOrderService.checkout(order=order, created_by_id=received_by_id)
        invoice = order.invoice
        BillingService.finalize_invoice(invoice=invoice)
        invoice.refresh_from_db()
        BillingService.record_payment(
            invoice=invoice,
            amount=Decimal(str(amount)),
            method=method,
            received_by_id=received_by_id,
        )
        order.refresh_from_db()
        order = PharmacyOrderService.fulfill(order=order, performed_by_id=received_by_id)
        return order

    @staticmethod
    @transaction.atomic
    def cancel(*, order):
        from .models import PharmacyOrderStatus
        if order.status == PharmacyOrderStatus.FULFILLED:
            raise ServiceError("Cannot cancel a fulfilled order.", code="ALREADY_FULFILLED")
        order.status = PharmacyOrderStatus.CANCELLED
        order.save(update_fields=["status", "updated_at"])
        return order

    @staticmethod
    def bulk_upload(*, file, performed_by_id: str) -> dict:
        """Parse CSV and create/update medications and inventory."""
        import csv
        import io
        from datetime import datetime
        from decimal import Decimal, InvalidOperation
        from django.db import transaction as db_transaction
        from apps.prescriptions.models import Medication, MedicationForm

        created = 0
        updated = 0
        errors = []

        content = file.read().decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(content))
        form_choices = [c[0] for c in MedicationForm.choices]

        for row_num, row in enumerate(reader, start=2):
            try:
                with db_transaction.atomic():
                    med_name = (row.get("medication_name") or "").strip()
                    strength = (row.get("strength") or "").strip()
                    form_raw = (row.get("form") or "tablet").strip().lower()
                    form = form_raw if form_raw in form_choices else "tablet"

                    if not med_name:
                        errors.append({"row": row_num, "message": "medication_name is required"})
                        continue

                    med, med_created = Medication.objects.get_or_create(
                        name=med_name,
                        strength=strength,
                        form=form,
                        defaults={
                            "generic_name": (row.get("generic_name") or med_name).strip(),
                            "manufacturer": (row.get("manufacturer") or "").strip(),
                        },
                    )

                    qty_raw = row.get("quantity", "0")
                    try:
                        qty = int(qty_raw)
                    except (ValueError, TypeError):
                        errors.append({"row": row_num, "message": f"Invalid quantity: {qty_raw}"})
                        continue

                    try:
                        unit_cost = Decimal(str(row.get("unit_cost") or "0"))
                    except InvalidOperation:
                        unit_cost = Decimal("0")

                    batch = (row.get("batch_number") or "").strip()
                    expiry_raw = (row.get("expiry_date") or "").strip()
                    expiry = None
                    if expiry_raw:
                        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                            try:
                                expiry = datetime.strptime(expiry_raw, fmt).date()
                                break
                            except ValueError:
                                pass

                    inv, inv_created = PharmacyInventory.objects.get_or_create(
                        medication=med,
                        batch_number=batch,
                        defaults={
                            "expiry_date": expiry,
                            "quantity_on_hand": 0,
                            "reorder_level": int(row.get("reorder_level") or 10),
                            "reorder_quantity": int(row.get("reorder_quantity") or 50),
                            "unit_cost": unit_cost,
                            "location": (row.get("location") or "").strip(),
                        },
                    )

                    if qty > 0:
                        PharmacyService.receive_stock(
                            inventory=inv,
                            quantity=qty,
                            performed_by_id=performed_by_id,
                            reference="bulk_upload",
                        )

                    if inv_created or med_created:
                        created += 1
                    else:
                        updated += 1

            except Exception as e:
                errors.append({"row": row_num, "message": str(e)})

        return {"created": created, "updated": updated, "errors": errors}
