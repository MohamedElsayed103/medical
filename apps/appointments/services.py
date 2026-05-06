"""
Appointment service layer — scheduling, conflict detection, status transitions.
"""
from datetime import datetime, timedelta

import structlog
from django.db import models
from django.utils import timezone

from common.enums import AppointmentStatus
from common.exceptions import ServiceError

from .models import Appointment, DoctorProfile

logger = structlog.get_logger(__name__)

# Valid status transitions
_TRANSITIONS: dict[str, set[str]] = {
    AppointmentStatus.SCHEDULED: {AppointmentStatus.CONFIRMED, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW},
    AppointmentStatus.CONFIRMED: {AppointmentStatus.IN_PROGRESS, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW},
    AppointmentStatus.IN_PROGRESS: {AppointmentStatus.COMPLETED},
    AppointmentStatus.COMPLETED: set(),
    AppointmentStatus.CANCELLED: set(),
    AppointmentStatus.NO_SHOW: set(),
}


class AppointmentService:

    @staticmethod
    def book(
        *,
        patient,
        doctor: DoctorProfile,
        scheduled_at: datetime,
        duration_minutes: int = 30,
        appointment_type: str = AppointmentStatus.SCHEDULED,
        reason: str = "",
    ) -> Appointment:
        """Book a new appointment with conflict detection."""
        AppointmentService._check_conflict(doctor, scheduled_at, duration_minutes)

        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            type=appointment_type,
            reason=reason,
        )
        logger.info(
            "appointment_booked",
            appointment_id=str(appointment.id),
            doctor_id=str(doctor.id),
            patient_id=str(patient.id),
            scheduled_at=str(scheduled_at),
        )
        return appointment

    @staticmethod
    def reschedule(
        appointment: Appointment,
        new_scheduled_at: datetime,
        new_duration: int | None = None,
    ) -> Appointment:
        """Reschedule an existing appointment."""
        if appointment.status in (AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED):
            raise ServiceError(
                f"Cannot reschedule a {appointment.status} appointment.",
                code="APPOINTMENT_NOT_RESCHEDULABLE",
            )

        duration = new_duration or appointment.duration_minutes
        AppointmentService._check_conflict(
            appointment.doctor, new_scheduled_at, duration, exclude_id=appointment.id
        )

        appointment.scheduled_at = new_scheduled_at
        if new_duration:
            appointment.duration_minutes = new_duration
        appointment.save(update_fields=["scheduled_at", "duration_minutes", "updated_at"])

        logger.info("appointment_rescheduled", appointment_id=str(appointment.id))
        return appointment

    @staticmethod
    def transition_status(
        appointment: Appointment,
        new_status: str,
        cancelled_by_id: str | None = None,
        cancellation_reason: str = "",
    ) -> Appointment:
        """Enforce valid status transitions."""
        allowed = _TRANSITIONS.get(appointment.status, set())
        if new_status not in allowed:
            raise ServiceError(
                f"Cannot transition from '{appointment.status}' to '{new_status}'.",
                code="INVALID_STATUS_TRANSITION",
            )

        appointment.status = new_status

        if new_status == AppointmentStatus.CANCELLED:
            appointment.cancellation_reason = cancellation_reason
            if cancelled_by_id:
                appointment.cancelled_by_id = cancelled_by_id

        appointment.save()
        logger.info(
            "appointment_status_changed",
            appointment_id=str(appointment.id),
            new_status=new_status,
        )
        return appointment

    @staticmethod
    def get_available_slots(
        doctor: DoctorProfile,
        date: datetime.date,
        duration_minutes: int = 30,
        work_start_hour: int = 9,
        work_end_hour: int = 17,
    ) -> list[datetime]:
        """Return available time slots for a doctor on a given date."""
        start_of_day = timezone.make_aware(
            datetime.combine(date, datetime.min.time().replace(hour=work_start_hour))
        )
        end_of_day = timezone.make_aware(
            datetime.combine(date, datetime.min.time().replace(hour=work_end_hour))
        )

        # Fetch existing appointments (non-cancelled) for the day
        existing = Appointment.objects.filter(
            doctor=doctor,
            scheduled_at__gte=start_of_day,
            scheduled_at__lt=end_of_day,
        ).exclude(
            status__in=[AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW]
        ).values_list("scheduled_at", "duration_minutes")

        # Build set of occupied ranges
        occupied = []
        for appt_start, appt_duration in existing:
            appt_end = appt_start + timedelta(minutes=appt_duration)
            occupied.append((appt_start, appt_end))

        # Generate slots
        slots = []
        current = start_of_day
        slot_delta = timedelta(minutes=duration_minutes)

        while current + slot_delta <= end_of_day:
            slot_end = current + slot_delta
            conflict = any(
                not (slot_end <= occ_start or current >= occ_end)
                for occ_start, occ_end in occupied
            )
            if not conflict:
                slots.append(current)
            current += slot_delta

        return slots

    # ── Internal ──

    @staticmethod
    def _check_conflict(
        doctor: DoctorProfile,
        start: datetime,
        duration_minutes: int,
        exclude_id=None,
    ):
        """Raise if the proposed slot overlaps an existing appointment."""
        end = start + timedelta(minutes=duration_minutes)

        conflicts = Appointment.objects.filter(
            doctor=doctor,
            status__in=[
                AppointmentStatus.SCHEDULED,
                AppointmentStatus.CONFIRMED,
                AppointmentStatus.IN_PROGRESS,
            ],
        ).exclude(
            # Exclude cancelled / no-show
        ).filter(
            # Overlap condition: existing.start < new.end AND existing.end > new.start
            scheduled_at__lt=end,
        ).annotate(
            end_time=models.ExpressionWrapper(
                models.F("scheduled_at") + timedelta(minutes=1) * models.F("duration_minutes"),
                output_field=models.DateTimeField(),
            )
        ).filter(end_time__gt=start)

        if exclude_id:
            conflicts = conflicts.exclude(pk=exclude_id)

        if conflicts.exists():
            raise ServiceError(
                "Doctor already has an appointment at this time.",
                code="APPOINTMENT_CONFLICT",
            )
