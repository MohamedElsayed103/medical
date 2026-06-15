"""
Pharmacy models — tenant-scoped.

PharmacyInventory    Tracks stock levels per medication per location.
StockTransaction     Immutable ledger of all inventory changes.
DispenseRecord       Prescription dispensing record.
DispenseItem         Individual item in a dispense record.
"""
import uuid

from django.db import models

from common.enums import MedicationForm, PharmacyOrderStatus
from common.models import BaseModel


class StockTransactionType(models.TextChoices):
    RECEIVED = "received", "Received"
    DISPENSED = "dispensed", "Dispensed"
    ADJUSTED = "adjusted", "Adjusted"
    EXPIRED = "expired", "Expired"
    RETURNED = "returned", "Returned"


class DispenseStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PREPARING = "preparing", "Preparing"
    READY = "ready", "Ready"
    DISPENSED = "dispensed", "Dispensed"
    CANCELLED = "cancelled", "Cancelled"


class PharmacyInventory(BaseModel):
    """Tracks stock levels for a medication in a specific location."""

    medication = models.ForeignKey(
        "prescriptions.Medication",
        on_delete=models.PROTECT,
        related_name="inventory_items",
    )
    batch_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    quantity_on_hand = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(
        default=10, help_text="Alert when stock falls below this level"
    )
    reorder_quantity = models.PositiveIntegerField(
        default=50, help_text="Suggested reorder quantity"
    )
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    location = models.CharField(
        max_length=200, blank=True, help_text="Shelf/room location"
    )
    is_active = models.BooleanField(default=True)

    AUDITED = True

    class Meta:
        db_table = "pharmacy_inventory"
        ordering = ["medication__name", "expiry_date"]
        indexes = [
            models.Index(fields=["medication", "batch_number"]),
            models.Index(fields=["expiry_date"]),
        ]

    def __str__(self):
        return f"{self.medication.name} — Batch {self.batch_number} ({self.quantity_on_hand})"

    @property
    def is_low_stock(self) -> bool:
        return self.quantity_on_hand <= self.reorder_level

    @property
    def is_out_of_stock(self) -> bool:
        return self.quantity_on_hand == 0

    @property
    def stock_status(self) -> str:
        if self.quantity_on_hand == 0:
            return "out_of_stock"
        if self.quantity_on_hand <= self.reorder_level:
            return "low_stock"
        return "in_stock"

    @property
    def total_value(self):
        return self.quantity_on_hand * self.unit_cost


class StockTransaction(BaseModel):
    """Immutable ledger entry for inventory changes."""

    inventory = models.ForeignKey(
        PharmacyInventory, on_delete=models.CASCADE, related_name="transactions"
    )
    transaction_type = models.CharField(
        max_length=20, choices=StockTransactionType.choices
    )
    quantity = models.IntegerField(help_text="Positive for additions, negative for removals")
    balance_after = models.PositiveIntegerField(help_text="Stock level after transaction")
    reference = models.CharField(
        max_length=255, blank=True, help_text="Reference (e.g., PO number, prescription ID)"
    )
    reason = models.TextField(blank=True)
    performed_by_id = models.UUIDField(help_text="User who performed the transaction")

    class Meta:
        db_table = "pharmacy_stock_transaction"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} — {self.inventory.medication.name}"


class DispenseRecord(BaseModel):
    """Record of a prescription being dispensed."""

    prescription = models.ForeignKey(
        "prescriptions.Prescription",
        on_delete=models.PROTECT,
        related_name="dispense_records",
    )
    status = models.CharField(
        max_length=20, choices=DispenseStatus.choices, default=DispenseStatus.PENDING
    )
    dispensed_by_id = models.UUIDField(null=True, blank=True)
    dispensed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    AUDITED = True

    class Meta:
        db_table = "pharmacy_dispense_record"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Dispense({self.prescription_id}) — {self.status}"


class DispenseItem(BaseModel):
    """Individual medication item in a dispense record."""

    dispense_record = models.ForeignKey(
        DispenseRecord, on_delete=models.CASCADE, related_name="items"
    )
    medication = models.ForeignKey(
        "prescriptions.Medication", on_delete=models.PROTECT
    )
    inventory = models.ForeignKey(
        PharmacyInventory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Inventory batch dispensed from",
    )
    quantity_dispensed = models.PositiveIntegerField()
    batch_number = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "pharmacy_dispense_item"

    def __str__(self):
        return f"{self.medication.name} x{self.quantity_dispensed}"


class PharmacyOrder(BaseModel):
    """A pharmacy sale order (OTC or prescription-linked, internal patient or walk-in)."""

    AUDITED = True

    patient = models.ForeignKey(
        "patients.Patient", null=True, blank=True,
        on_delete=models.PROTECT, related_name="pharmacy_orders"
    )
    customer = models.ForeignKey(
        "patients.Customer", null=True, blank=True,
        on_delete=models.PROTECT, related_name="pharmacy_orders"
    )
    prescription = models.ForeignKey(
        "prescriptions.Prescription", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="pharmacy_orders",
        help_text="Set when the order originates from a prescription.",
    )
    order_number = models.CharField(max_length=30, unique=True, db_index=True)
    status = models.CharField(
        max_length=20, choices=PharmacyOrderStatus.choices,
        default=PharmacyOrderStatus.DRAFT,
    )
    invoice = models.ForeignKey(
        "billing.Invoice", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="pharmacy_orders"
    )
    created_by_id = models.UUIDField(help_text="Pharmacist user id")
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "pharmacy_order"
        ordering = ["-created_at"]

    @property
    def orderer_name(self) -> str:
        if self.patient_id:
            return getattr(self.patient, "full_name", "")
        return getattr(self.customer, "full_name", "") if self.customer_id else ""

    @property
    def orderer_type(self) -> str:
        return "patient" if self.patient_id else "customer"

    def __str__(self):
        return f"PharmacyOrder({self.order_number})"


class PharmacyOrderItem(BaseModel):
    """Line item in a pharmacy order."""

    order = models.ForeignKey(PharmacyOrder, on_delete=models.CASCADE, related_name="items")
    medication = models.ForeignKey(
        "prescriptions.Medication", on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    inventory = models.ForeignKey(
        PharmacyInventory, null=True, blank=True, on_delete=models.SET_NULL,
        help_text="Inventory batch fulfilled from (set at fulfillment)",
    )

    class Meta:
        db_table = "pharmacy_order_item"

    @property
    def line_total(self):
        from decimal import Decimal
        return Decimal(str(self.quantity)) * self.unit_price

    def __str__(self):
        return f"{self.medication.name} x{self.quantity}"
