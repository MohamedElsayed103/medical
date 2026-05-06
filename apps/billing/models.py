"""
Billing models — tenant-scoped.

Invoice         Header: patient, date, totals, status.
InvoiceItem     Line items (consultation, lab, prescription, procedure, etc.).
Payment         Payment records against an invoice (supports partial payments).
"""
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.patients.models import Patient
from common.enums import InvoiceItemType, InvoiceStatus, PaymentMethod
from common.models import BaseModel
from common.utils import generate_invoice_number


class Invoice(BaseModel):
    """Invoice issued to a patient."""

    AUDITED = True

    invoice_number = models.CharField(max_length=30, unique=True, db_index=True)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="invoices")
    issued_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT
    )
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "billing_invoice"
        ordering = ["-issued_at"]
        indexes = [
            models.Index(fields=["patient", "issued_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Invoice({self.invoice_number})"

    @property
    def balance_due(self) -> Decimal:
        return self.total - self.amount_paid


class InvoiceItem(BaseModel):
    """Line item on an invoice."""

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    item_type = models.CharField(max_length=20, choices=InvoiceItemType.choices)
    description = models.CharField(max_length=500)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        db_table = "billing_invoice_item"

    def save(self, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(**kwargs)

    def __str__(self):
        return f"{self.description} x{self.quantity}"


class Payment(BaseModel):
    """Payment record against an invoice — supports partial payments."""

    AUDITED = True

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    reference_number = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(auto_now_add=True)
    received_by_id = models.UUIDField(help_text="User ID of staff who processed payment")
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "billing_payment"
        ordering = ["-paid_at"]

    def __str__(self):
        return f"Payment({self.amount} on {self.invoice.invoice_number})"
