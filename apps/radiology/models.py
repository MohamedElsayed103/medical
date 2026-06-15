"""
Radiology models — tenant-scoped.
"""
from django.db import models

from common.enums import LabPriority, RadiologyModality, RadiologyOrderStatus
from common.models import BaseModel


class RadiologyOrder(BaseModel):
    """A radiology imaging order."""

    AUDITED = True

    patient = models.ForeignKey(
        "patients.Patient", null=True, blank=True,
        on_delete=models.PROTECT, related_name="radiology_orders"
    )
    customer = models.ForeignKey(
        "patients.Customer", null=True, blank=True,
        on_delete=models.PROTECT, related_name="radiology_orders"
    )
    doctor = models.ForeignKey(
        "appointments.DoctorProfile", null=True, blank=True,
        on_delete=models.PROTECT, related_name="radiology_orders"
    )
    visit = models.ForeignKey(
        "medical_records.Visit", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="radiology_orders"
    )
    order_number = models.CharField(max_length=30, unique=True, db_index=True)
    status = models.CharField(
        max_length=30, choices=RadiologyOrderStatus.choices,
        default=RadiologyOrderStatus.ORDERED
    )
    priority = models.CharField(
        max_length=10, choices=LabPriority.choices, default=LabPriority.ROUTINE
    )
    clinical_notes = models.TextField(blank=True)
    invoice = models.ForeignKey(
        "billing.Invoice", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="radiology_orders"
    )
    ordered_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "radiology_order"
        ordering = ["-ordered_at"]
        indexes = [models.Index(fields=["status", "priority"])]

    @property
    def orderer_name(self) -> str:
        if self.patient_id:
            return getattr(self.patient, "full_name", "")
        return getattr(self.customer, "full_name", "") if self.customer_id else ""

    @property
    def orderer_type(self) -> str:
        return "patient" if self.patient_id else "customer"

    def __str__(self):
        return f"RadOrder({self.order_number})"


class RadiologyStudy(BaseModel):
    """One imaging study within an order (e.g., Chest X-Ray PA view)."""

    order = models.ForeignKey(RadiologyOrder, on_delete=models.CASCADE, related_name="studies")
    modality = models.CharField(max_length=20, choices=RadiologyModality.choices)
    body_part = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    performed_by_id = models.UUIDField(null=True, blank=True, help_text="Radiographer user id")
    performed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "radiology_study"

    def __str__(self):
        return f"{self.modality} {self.body_part}"


class RadiologyReport(BaseModel):
    """Radiologist findings for a study (1:1)."""

    study = models.OneToOneField(RadiologyStudy, on_delete=models.CASCADE, related_name="report")
    findings = models.TextField()
    impression = models.TextField(blank=True)
    is_critical = models.BooleanField(default=False, help_text="Critical/urgent finding flag")
    reported_by_id = models.UUIDField(help_text="Radiologist user id")
    reported_at = models.DateTimeField(auto_now_add=True)
    image_object_key = models.CharField(
        max_length=500, blank=True,
        help_text="MinIO object key for the image, if uploaded",
    )

    class Meta:
        db_table = "radiology_report"

    def __str__(self):
        return f"Report({self.study})"
