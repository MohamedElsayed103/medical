"""
Appointment Celery tasks.
"""
import structlog
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from common.enums import AppointmentStatus, NotificationType

logger = structlog.get_logger(__name__)


@shared_task(name="apps.appointments.tasks.send_appointment_reminders")
def send_appointment_reminders():
    """
    Hourly task: sends reminder notifications for appointments
    scheduled within the next 24-25 hours.
    """
    from .models import Appointment

    now = timezone.now()
    window_start = now + timedelta(hours=24)
    window_end = now + timedelta(hours=25)

    appointments = Appointment.objects.filter(
        scheduled_at__gte=window_start,
        scheduled_at__lt=window_end,
        status__in=[
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.CONFIRMED,
        ],
    ).select_related("patient", "doctor")

    count = 0
    for appt in appointments:
        try:
            from apps.notifications.services import NotificationService

            # Notify the doctor
            NotificationService.create_and_send(
                recipient_id=str(appt.doctor.user_id),
                notification_type=NotificationType.APPOINTMENT_REMINDER,
                title="Appointment Reminder",
                body=(
                    f"You have an appointment with "
                    f"{appt.patient.first_name} {appt.patient.last_name} "
                    f"at {appt.scheduled_at.strftime('%H:%M on %b %d')}."
                ),
                data={
                    "appointment_id": str(appt.id),
                    "patient_id": str(appt.patient_id),
                },
            )
            count += 1
        except Exception as exc:
            logger.error(
                "appointment_reminder_failed",
                appointment_id=str(appt.id),
                error=str(exc),
            )

    logger.info("appointment_reminders_sent", count=count)
    return count
