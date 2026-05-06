"""
Prescription models — tenant-scoped.

Medication          Reference table for drugs.
Prescription        A prescription issued by a doctor.
PrescriptionItem    Individual medication entries in a prescription.
"""
from django.db import models

from apps.appointments.models import DoctorProfile
from apps.medical_records.models import Visit
from apps.patients.models import Patient
from common.enums import MedicationForm, MedicationRoute
from common.models import BaseModel


class Medication(BaseModel):
    """Drug reference table — shared within a tenant."""

    name = models.CharField(max_length=255, db_index=True)
    generic_name = models.CharField(max_length=255, db_index=True)
    form = models.CharField(max_length=20, choices=MedicationForm.choices)
    strength = models.CharField(max_length=50)
    manufacturer = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "prescriptions_medication"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} {self.strength} ({self.form})"


class Prescription(BaseModel):
    """A prescription issued by a doctor for a patient."""

    AUDITED = True

    visit = models.ForeignKey(
        Visit, null=True, blank=True, on_delete=models.SET_NULL, related_name="prescriptions"
    )
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="prescriptions")
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.PROTECT, related_name="prescriptions")
    prescribed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    is_dispensed = models.BooleanField(default=False)
    dispensed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "prescriptions_prescription"
        ordering = ["-prescribed_at"]
        indexes = [
            models.Index(fields=["patient", "prescribed_at"]),
            models.Index(fields=["doctor", "prescribed_at"]),
        ]

    def __str__(self):
        return f"Rx({self.patient}, {self.prescribed_at.date()})"


class PrescriptionItem(BaseModel):
    """Individual medication entry in a prescription."""

    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name="items"
    )
    medication = models.ForeignKey(
        Medication, on_delete=models.PROTECT, related_name="prescription_items"
    )
    dosage = models.CharField(max_length=100, help_text='e.g., "500mg"')
    frequency = models.CharField(max_length=100, help_text='e.g., "twice daily"')
    duration = models.CharField(max_length=100, help_text='e.g., "7 days"')
    route = models.CharField(max_length=20, choices=MedicationRoute.choices, default=MedicationRoute.ORAL)
    quantity = models.PositiveIntegerField()
    instructions = models.TextField(blank=True, help_text='e.g., "after meals"')
    is_prn = models.BooleanField(default=False, help_text="As-needed basis")

    class Meta:
        db_table = "prescriptions_prescription_item"

    def __str__(self):
        return f"{self.medication.name} {self.dosage} — {self.frequency}"
