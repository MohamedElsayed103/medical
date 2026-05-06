"""
Lab models — tenant-scoped.

LabOrder     An order for lab tests placed by a doctor.
LabTest      A specific test within an order.
TestResult   The result of a completed test with automatic flagging.
"""
from decimal import Decimal

from django.db import models

from apps.appointments.models import DoctorProfile
from apps.medical_records.models import Visit
from apps.patients.models import Patient
from common.enums import LabOrderStatus, LabPriority, ResultFlag
from common.models import BaseModel


class LabOrder(BaseModel):
    """Lab order placed by a doctor for a patient."""

    AUDITED = True

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="lab_orders")
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.PROTECT, related_name="lab_orders")
    visit = models.ForeignKey(
        Visit, null=True, blank=True, on_delete=models.SET_NULL, related_name="lab_orders"
    )
    order_number = models.CharField(max_length=30, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=LabOrderStatus.choices, default=LabOrderStatus.ORDERED)
    priority = models.CharField(max_length=10, choices=LabPriority.choices, default=LabPriority.ROUTINE)
    clinical_notes = models.TextField(blank=True)
    ordered_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "lab_results_lab_order"
        ordering = ["-ordered_at"]
        indexes = [
            models.Index(fields=["patient", "ordered_at"]),
            models.Index(fields=["status", "priority"]),
        ]

    def __str__(self):
        return f"Lab({self.order_number})"


class LabTest(BaseModel):
    """A specific test within a lab order (e.g., CBC, TSH, Lipid Panel)."""

    order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name="tests")
    test_name = models.CharField(max_length=200)
    test_code = models.CharField(max_length=50, blank=True)
    specimen_type = models.CharField(max_length=100, blank=True, help_text="e.g., Blood, Urine, Serum")
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "lab_results_lab_test"

    def __str__(self):
        return f"{self.test_name} ({self.order.order_number})"


class TestResult(BaseModel):
    """
    Result for a lab test — supports automatic flagging based on reference range.
    """

    test = models.OneToOneField(LabTest, on_delete=models.CASCADE, related_name="result")
    value = models.CharField(max_length=200, help_text="Observed value")
    unit = models.CharField(max_length=50, blank=True, help_text="e.g., mg/dL, mmol/L")
    reference_range_low = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    reference_range_high = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    flag = models.CharField(max_length=20, choices=ResultFlag.choices, default=ResultFlag.NORMAL)
    resulted_at = models.DateTimeField(auto_now_add=True)
    resulted_by_id = models.UUIDField(help_text="User ID of the lab tech who entered the result")
    interpretation = models.TextField(blank=True, help_text="Lab tech interpretation notes")

    class Meta:
        db_table = "lab_results_test_result"

    def __str__(self):
        return f"Result({self.test.test_name}={self.value})"

    def auto_flag(self) -> str:
        """
        Automatically determine flag based on numeric value and reference range.
        Returns the computed flag string.
        """
        try:
            numeric_value = Decimal(self.value)
        except Exception:
            return ResultFlag.NORMAL

        if self.reference_range_low is not None and numeric_value < self.reference_range_low:
            critical_low = self.reference_range_low * Decimal("0.5")
            return ResultFlag.CRITICAL if numeric_value <= critical_low else ResultFlag.LOW

        if self.reference_range_high is not None and numeric_value > self.reference_range_high:
            critical_high = self.reference_range_high * Decimal("1.5")
            return ResultFlag.CRITICAL if numeric_value >= critical_high else ResultFlag.HIGH

        return ResultFlag.NORMAL
