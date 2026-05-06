"""
Medical Record models — tenant-scoped.

Visit        A clinical encounter (SOAP format). Immutable once signed.
Vitals       Vital signs recorded during a visit.
Diagnosis    ICD-coded diagnoses associated with a visit.
"""
import uuid

from django.db import models

from apps.appointments.models import Appointment, DoctorProfile
from apps.patients.models import Patient
from common.enums import DiagnosisType
from common.models import BaseModel


class Visit(BaseModel):
    """
    A clinical visit / encounter.

    Follows SOAP format:
      S – chief_complaint, history_of_present_illness
      O – vitals (separate model), examination_notes
      A – assessment, diagnoses (separate model)
      P – plan, prescriptions (prescriptions app), follow_up_date

    Once ``is_signed`` is True, the record is immutable.
    """

    AUDITED = True

    appointment = models.ForeignKey(
        Appointment,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="visits",
    )
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="visits")
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.PROTECT, related_name="visits")
    visit_date = models.DateTimeField()
    chief_complaint = models.TextField()
    history_of_present_illness = models.TextField(blank=True)
    examination_notes = models.TextField(blank=True)
    assessment = models.TextField(blank=True)
    plan = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    is_signed = models.BooleanField(default=False)
    signed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "medical_records_visit"
        ordering = ["-visit_date"]
        indexes = [
            models.Index(fields=["patient", "visit_date"]),
            models.Index(fields=["doctor", "visit_date"]),
        ]

    def __str__(self):
        return f"Visit({self.patient}, {self.visit_date.date()})"


class Vitals(BaseModel):
    """Vital signs recorded during a visit."""

    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="vitals")
    blood_pressure_systolic = models.PositiveIntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.PositiveIntegerField(null=True, blank=True)
    heart_rate = models.PositiveIntegerField(null=True, blank=True)
    temperature = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True, help_text="Celsius"
    )
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True)
    oxygen_saturation = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True, help_text="Percentage"
    )
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by_id = models.UUIDField(help_text="References accounts.User.id")

    class Meta:
        db_table = "medical_records_vitals"
        verbose_name_plural = "vitals"

    def __str__(self):
        return f"Vitals(visit={self.visit_id})"


class Diagnosis(BaseModel):
    """An ICD-coded diagnosis associated with a visit."""

    AUDITED = True

    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="diagnoses")
    icd_code = models.CharField(max_length=20, db_index=True, help_text="ICD-10/11 code")
    description = models.TextField()
    type = models.CharField(max_length=20, choices=DiagnosisType.choices, default=DiagnosisType.PRIMARY)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "medical_records_diagnosis"
        verbose_name_plural = "diagnoses"
        indexes = [
            models.Index(fields=["visit"]),
            models.Index(fields=["icd_code"]),
        ]

    def __str__(self):
        return f"{self.icd_code}: {self.description[:60]}"
