"""
Billing service layer.
"""
from decimal import Decimal

import structlog
from django.db import transaction

from common.enums import InvoiceSourceType, InvoiceStatus
from common.exceptions import ServiceError
from common.utils import generate_invoice_number

from .models import Invoice, InvoiceItem, Payment

logger = structlog.get_logger(__name__)


class BillingService:

    @staticmethod
    @transaction.atomic
    def create_invoice(
        *,
        patient,
        items: list[dict],
        tax_rate: Decimal = Decimal("0.00"),
        discount_amount: Decimal = Decimal("0.00"),
        due_date=None,
        notes: str = "",
    ) -> Invoice:
        """
        Create an invoice with line items. Calculates subtotal, tax, total.

        ``items``: list of {item_type, description, quantity, unit_price}
        ``tax_rate``: percentage (e.g. 10 for 10%)
        """
        invoice = Invoice(
            invoice_number=generate_invoice_number(),
            patient=patient,
            due_date=due_date,
            discount_amount=discount_amount,
            notes=notes,
        )

        subtotal = Decimal("0.00")
        item_objects = []
        for item_data in items:
            item = InvoiceItem(
                invoice=invoice,
                item_type=item_data["item_type"],
                description=item_data["description"],
                quantity=item_data.get("quantity", 1),
                unit_price=Decimal(str(item_data["unit_price"])),
            )
            item.total_price = item.unit_price * item.quantity
            subtotal += item.total_price
            item_objects.append(item)

        if not (Decimal("0") <= tax_rate <= Decimal("1")):
            from common.exceptions import ServiceError
            raise ServiceError("tax_rate must be a decimal fraction in [0, 1]. E.g. 0.10 for 10%.", code="INVALID_TAX_RATE")
        tax_multiplier = tax_rate
        invoice.subtotal = subtotal
        invoice.tax_amount = subtotal * tax_multiplier
        invoice.total = subtotal + invoice.tax_amount - discount_amount
        invoice.save()

        for item in item_objects:
            item.invoice = invoice
            item.save()

        logger.info(
            "invoice_created",
            invoice_id=str(invoice.id),
            invoice_number=invoice.invoice_number,
            total=str(invoice.total),
        )
        return invoice

    @staticmethod
    def finalize_invoice(invoice: Invoice) -> Invoice:
        if invoice.status != InvoiceStatus.DRAFT:
            raise ServiceError("Only draft invoices can be finalized.", code="NOT_DRAFT")
        invoice.status = InvoiceStatus.ISSUED
        invoice.save(update_fields=["status", "updated_at"])
        logger.info("invoice_finalized", invoice_id=str(invoice.id))
        return invoice

    @staticmethod
    @transaction.atomic
    def record_payment(
        *,
        invoice: Invoice,
        amount: Decimal,
        method: str,
        received_by_id: str,
        reference_number: str = "",
        notes: str = "",
    ) -> Payment:
        if invoice.status in (InvoiceStatus.DRAFT, InvoiceStatus.CANCELLED):
            raise ServiceError(
                f"Cannot record payment on {invoice.status} invoice.",
                code="INVALID_INVOICE_STATUS",
            )

        if amount > invoice.balance_due:
            raise ServiceError(
                f"Payment amount ({amount}) exceeds balance due ({invoice.balance_due}).",
                code="OVERPAYMENT",
            )

        payment = Payment.objects.create(
            invoice=invoice,
            amount=amount,
            method=method,
            reference_number=reference_number,
            received_by_id=received_by_id,
            notes=notes,
        )

        invoice.amount_paid += amount
        if invoice.amount_paid >= invoice.total:
            invoice.status = InvoiceStatus.PAID
        elif invoice.amount_paid > Decimal("0.00"):
            invoice.status = InvoiceStatus.PARTIALLY_PAID

        invoice.save(update_fields=["amount_paid", "status", "updated_at"])

        # Sync pharmacy order status when invoice becomes PAID
        if invoice.status == InvoiceStatus.PAID and invoice.source_type == "pharmacy_order" and invoice.source_id:
            try:
                from apps.pharmacy.models import PharmacyOrder, PharmacyOrderStatus
                po = PharmacyOrder.objects.filter(id=invoice.source_id).first()
                if po and po.status == PharmacyOrderStatus.AWAITING_PAYMENT:
                    po.status = PharmacyOrderStatus.PAID
                    po.save(update_fields=["status", "updated_at"])
            except Exception:
                logger.warning("pharmacy_order_status_sync_failed", source_id=str(invoice.source_id))

        logger.info(
            "payment_recorded",
            payment_id=str(payment.id),
            invoice_id=str(invoice.id),
            amount=str(amount),
            new_status=invoice.status,
        )
        return payment

    @staticmethod
    def cancel_invoice(invoice: Invoice) -> Invoice:
        if invoice.status == InvoiceStatus.PAID:
            raise ServiceError("Cannot cancel a fully paid invoice.", code="INVOICE_PAID")
        if invoice.amount_paid > Decimal("0.00"):
            raise ServiceError(
                "Cannot cancel invoice with existing payments. Refund first.",
                code="HAS_PAYMENTS",
            )
        invoice.status = InvoiceStatus.CANCELLED
        invoice.save(update_fields=["status", "updated_at"])
        logger.info("invoice_cancelled", invoice_id=str(invoice.id))
        return invoice

    @staticmethod
    def void_invoice(invoice: Invoice) -> Invoice:
        if invoice.status == InvoiceStatus.CANCELLED:
            raise ServiceError("Invoice already cancelled.", code="ALREADY_CANCELLED")
        invoice.status = InvoiceStatus.CANCELLED
        invoice.save(update_fields=["status", "updated_at"])
        logger.info("invoice_voided", invoice_id=str(invoice.id))
        return invoice

    @staticmethod
    @transaction.atomic
    def create_from_source(
        *,
        source_type: str,
        source_id: str,
        patient=None,
        customer=None,
        items: list[dict],
        created_by_id: str = "",
        tax_rate: Decimal = Decimal("0.00"),
        discount_amount: Decimal = Decimal("0.00"),
        notes: str = "",
    ) -> "Invoice":
        """
        Create a DRAFT invoice linked to a source event.
        Idempotent per (source_type, source_id): returns existing non-cancelled invoice.
        """
        existing = Invoice.objects.filter(
            source_type=source_type, source_id=source_id
        ).exclude(status=InvoiceStatus.CANCELLED).first()
        if existing:
            return existing

        invoice = Invoice(
            invoice_number=generate_invoice_number(),
            patient=patient,
            customer=customer,
            source_type=source_type,
            source_id=source_id,
            discount_amount=discount_amount,
            notes=notes,
            status=InvoiceStatus.DRAFT,
        )

        subtotal = Decimal("0.00")
        item_objects = []
        for item_data in items:
            item = InvoiceItem(
                invoice=invoice,
                item_type=item_data.get("item_type", "other"),
                description=item_data["description"],
                quantity=item_data.get("quantity", 1),
                unit_price=Decimal(str(item_data.get("unit_price", "0.00"))),
            )
            item.total_price = item.unit_price * item.quantity
            subtotal += item.total_price
            item_objects.append(item)

        invoice.subtotal = subtotal
        invoice.tax_amount = subtotal * tax_rate
        invoice.total = subtotal + invoice.tax_amount - discount_amount
        invoice.save()

        for item in item_objects:
            item.invoice = invoice
            item.save()

        logger.info(
            "invoice_created_from_source",
            invoice_id=str(invoice.id),
            source_type=source_type,
            source_id=source_id,
        )
        return invoice
