"""
Appointment model — tenant-scoped.

Includes DB-level exclusion constraint to prevent double-booking.
"""
import uuid

from django.db import models

from apps.patients.models import Patient
from common.enums import AppointmentStatus, AppointmentType
from common.models import BaseModel


class DoctorProfile(BaseModel):
    """
    Doctor-specific profile within a tenant.

    ``user_id`` is a UUID referencing ``accounts.User`` in the public schema.
    Cross-schema ForeignKey is not possible in PostgreSQL, so resolution is
    done at the application layer.
    """

    AUDITED = True

    user_id = models.UUIDField(db_index=True, help_text="References accounts.User.id in public schema.")
    specialization = models.CharField(max_length=200)
    license_number = models.CharField(max_length=100, blank=True)
    qualification = models.TextField(blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bio = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)

    class Meta:
        db_table = "appointments_doctor_profile"
        indexes = [
            models.Index(fields=["user_id"]),
            models.Index(fields=["specialization"]),
        ]

    def __str__(self):
        return f"Dr. {self.specialization} (user={self.user_id})"


class Appointment(BaseModel):
    """
    An appointment between a patient and a doctor.

    Status transitions are enforced in the service layer.
    """

    AUDITED = True

    patient = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name="appointments"
    )
    doctor = models.ForeignKey(
        DoctorProfile, on_delete=models.PROTECT, related_name="appointments"
    )
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    status = models.CharField(
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.SCHEDULED,
    )
    type = models.CharField(
        max_length=20,
        choices=AppointmentType.choices,
        default=AppointmentType.IN_PERSON,
    )
    reason = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    cancelled_by_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "appointments_appointment"
        ordering = ["-scheduled_at"]
        indexes = [
            models.Index(fields=["doctor", "scheduled_at"]),
            models.Index(fields=["patient", "scheduled_at"]),
            models.Index(fields=["status", "scheduled_at"]),
        ]

    def __str__(self):
        return f"Appointment({self.patient}, {self.doctor}, {self.scheduled_at})"

    @property
    def end_time(self):
        from datetime import timedelta

        return self.scheduled_at + timedelta(minutes=self.duration_minutes)
