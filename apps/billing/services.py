"""
Billing service layer.
"""
from decimal import Decimal

import structlog
from django.db import transaction

from common.enums import InvoiceStatus
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

        invoice.subtotal = subtotal
        invoice.tax_amount = subtotal * tax_rate
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
