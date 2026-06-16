"""
Patient model — tenant-scoped.

Each tenant (clinic/hospital) maintains its own patient records.
No cross-tenant sharing.
"""
from django.db import models

from common.enums import DocumentCategory, Gender
from common.models import SoftDeleteModel


class Patient(SoftDeleteModel):
    """
    A patient registered within a specific tenant.

    Supports soft delete — medical records must never be hard-deleted.
    Sensitive fields (national_id) are encrypted at the application layer
    before being stored.
    """

    AUDITED = True  # Flag for audit signal auto-logging

    medical_record_number = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=Gender.choices)
    national_id_encrypted = models.TextField(
        blank=True,
        default="",
        help_text="Fernet-encrypted national ID.",
    )
    blood_type = models.CharField(max_length=5, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    allergies = models.JSONField(default=list, blank=True)
    chronic_conditions = models.JSONField(default=list, blank=True)
    insurance_provider = models.CharField(max_length=200, blank=True)
    insurance_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patients_patient"
        ordering = ["-registered_at"]
        indexes = [
            models.Index(fields=["phone"]),
            models.Index(fields=["last_name", "first_name", "date_of_birth"]),
            models.Index(fields=["medical_record_number"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.medical_record_number})"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class Customer(SoftDeleteModel):
    """Non-patient orderer (walk-in) for pharmacy/lab/rays. Minimal PII; not a clinical record."""

    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "patients_customer"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone"]),
            models.Index(fields=["full_name"]),
        ]

    AUDITED = True

    def __str__(self):
        return f"{self.full_name} ({self.phone})"


class Document(SoftDeleteModel):
    """A file attached to a patient (lab report, ID, consent, imaging, etc.).

    Stored via the configured storage backend (filesystem in dev, S3/MinIO in
    prod). Medical documents are soft-deleted, never hard-deleted.
    """

    patient = models.ForeignKey(
        Patient, null=True, blank=True, on_delete=models.PROTECT, related_name="documents"
    )
    customer = models.ForeignKey(
        Customer, null=True, blank=True, on_delete=models.PROTECT, related_name="documents"
    )
    category = models.CharField(
        max_length=20, choices=DocumentCategory.choices, default=DocumentCategory.OTHER
    )
    file = models.FileField(upload_to="documents/")
    filename = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    size = models.PositiveIntegerField(default=0)
    description = models.CharField(max_length=255, blank=True)
    uploaded_by_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "patients_document"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["patient", "category"])]

    AUDITED = True

    def __str__(self):
        return self.filename or str(self.file)
