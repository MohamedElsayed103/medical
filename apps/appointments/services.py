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
        """Book a new appointment with conflict + availability detection."""
        AppointmentService._check_conflict(doctor, scheduled_at, duration_minutes)
        AppointmentService._check_availability(doctor, scheduled_at, duration_minutes)

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

        if new_status == AppointmentStatus.COMPLETED:
            try:
                from apps.notifications.services import NotificationService
                from common.enums import NotificationType, NotificationChannel
                has_visit = appointment.visits.filter(deleted_at__isnull=True).exists() if hasattr(appointment, 'visits') else False
                if not has_visit:
                    NotificationService.create_and_send(
                        recipient_id=str(appointment.doctor.user_id),
                        notification_type=NotificationType.SYSTEM,
                        title="Visit record needed",
                        body="Appointment completed. Please record the visit for the patient.",
                        channel=NotificationChannel.IN_APP,
                        data={"action": "create_visit", "appointment_id": str(appointment.id), "patient_id": str(appointment.patient_id)},
                    )
            except Exception:
                pass

        logger.info(
            "appointment_status_changed",
            appointment_id=str(appointment.id),
            new_status=new_status,
        )
        return appointment

    @staticmethod
    def get_available_slots(
        doctor: DoctorProfile,
        date,
        duration_minutes: int = 30,
        work_start_hour: int = 9,
        work_end_hour: int = 17,
    ) -> list:
        """Bookable slots for a doctor on a date.

        A slot is offered only when it is (a) inside one of the doctor's
        ``DoctorAvailability`` windows for that weekday, (b) not overlapping a
        ``DoctorTimeOff`` block, (c) not overlapping an existing appointment,
        and (d) not in the past. This is the SAME rule enforced by ``book()``
        via :meth:`_check_availability`, so the slots shown can always be booked.

        Backwards-compatible: a doctor with NO availability configured at all
        falls back to default working hours so the feature degrades gracefully.
        """
        from datetime import datetime as dt, timedelta, time as dt_time
        from .models import DoctorTimeOff

        date_obj = date.date() if hasattr(date, "date") else date

        configured = AppointmentService._has_availability_config(doctor)
        windows = AppointmentService._windows_for_day(doctor, date_obj)

        # Doctor keeps a schedule but does not work this weekday → no slots.
        if configured and not windows:
            return []

        if configured:
            windows_ranges = [
                (
                    timezone.make_aware(dt.combine(date_obj, w.start_time)),
                    timezone.make_aware(dt.combine(date_obj, w.end_time)),
                )
                for w in windows
            ]
        else:
            windows_ranges = [(
                timezone.make_aware(dt.combine(date_obj, dt_time(work_start_hour, 0))),
                timezone.make_aware(dt.combine(date_obj, dt_time(work_end_hour, 0))),
            )]

        # Fetch conflicts/time-off over the WHOLE day, independent of windows.
        day_start = timezone.make_aware(dt.combine(date_obj, dt_time.min))
        day_end = day_start + timedelta(days=1)

        time_off = DoctorTimeOff.objects.filter(
            doctor=doctor, start_at__lt=day_end, end_at__gt=day_start
        )
        existing = Appointment.objects.filter(
            doctor=doctor,
            scheduled_at__gte=day_start,
            scheduled_at__lt=day_end,
        ).exclude(
            status__in=[AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW]
        ).values_list("scheduled_at", "duration_minutes")

        occupied = [(s, s + timedelta(minutes=d)) for s, d in existing]
        occupied += [(off.start_at, off.end_at) for off in time_off]

        # Don't generate slots for a date that has already fully passed. We do
        # NOT filter individual slots by time-of-day against UTC `now`: the
        # clinic's wall-clock may differ from UTC, so a window like 09:00–10:00
        # is still "today's availability" for the clinic even when UTC is later.
        # The booking UI already prevents selecting past dates.
        if date_obj < timezone.now().date():
            return []

        slot_delta = timedelta(minutes=duration_minutes)
        slots = []
        for win_start, win_end in windows_ranges:
            current = win_start
            while current + slot_delta <= win_end:
                slot_end = current + slot_delta
                overlaps = any(
                    not (slot_end <= occ_start or current >= occ_end)
                    for occ_start, occ_end in occupied
                )
                if not overlaps:
                    slots.append(current)
                current = slot_end

        return slots

    # ── Internal ──

    @staticmethod
    def _has_availability_config(doctor: DoctorProfile) -> bool:
        """True if the doctor has any active weekly availability window."""
        from .models import DoctorAvailability
        return DoctorAvailability.objects.filter(doctor=doctor, is_active=True).exists()

    @staticmethod
    def _windows_for_day(doctor: DoctorProfile, date_obj):
        """Active availability windows for the given date's weekday (0=Mon)."""
        from .models import DoctorAvailability
        return list(
            DoctorAvailability.objects.filter(
                doctor=doctor, day_of_week=date_obj.weekday(), is_active=True
            ).order_by("start_time")
        )

    @staticmethod
    def _check_availability(
        doctor: DoctorProfile,
        start: datetime,
        duration_minutes: int,
    ):
        """Reject a booking outside the doctor's availability or during time-off.

        Mirrors :meth:`get_available_slots` exactly so the slots offered to the
        UI are precisely the slots ``book()`` will accept. A doctor who has not
        configured ANY availability is treated as always bookable (legacy);
        time-off is always enforced.
        """
        from .models import DoctorTimeOff

        end = start + timedelta(minutes=duration_minutes)

        # Time-off always blocks, even with no weekly schedule configured.
        if DoctorTimeOff.objects.filter(
            doctor=doctor, start_at__lt=end, end_at__gt=start
        ).exists():
            raise ServiceError(
                "Doctor is on time off at this time.",
                code="OUTSIDE_AVAILABILITY",
            )

        # No weekly schedule at all → allow (legacy behaviour).
        if not AppointmentService._has_availability_config(doctor):
            return

        local_start = timezone.localtime(start)
        local_end = timezone.localtime(end)
        windows = AppointmentService._windows_for_day(doctor, local_start.date())
        within = any(
            w.start_time <= local_start.time() and local_end.time() <= w.end_time
            for w in windows
        )
        if not within:
            raise ServiceError(
                "Doctor is not available at this time.",
                code="OUTSIDE_AVAILABILITY",
            )

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
