"""
Patient model — tenant-scoped.

Each tenant (clinic/hospital) maintains its own patient records.
No cross-tenant sharing.
"""
from django.db import models

from common.enums import Gender
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
