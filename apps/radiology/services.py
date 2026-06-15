"""
Radiology service layer.
"""
import structlog
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from common.exceptions import ServiceError
from common.utils import generate_order_number
from .models import RadiologyOrder, RadiologyStudy, RadiologyReport
from common.enums import RadiologyOrderStatus

logger = structlog.get_logger(__name__)


class RadiologyService:

    VALID_TRANSITIONS = {
        RadiologyOrderStatus.ORDERED: [RadiologyOrderStatus.SCHEDULED, RadiologyOrderStatus.CANCELLED],
        RadiologyOrderStatus.SCHEDULED: [RadiologyOrderStatus.IN_PROGRESS, RadiologyOrderStatus.CANCELLED],
        RadiologyOrderStatus.IN_PROGRESS: [RadiologyOrderStatus.AWAITING_REPORT, RadiologyOrderStatus.CANCELLED],
        RadiologyOrderStatus.AWAITING_REPORT: [RadiologyOrderStatus.COMPLETED, RadiologyOrderStatus.CANCELLED],
        RadiologyOrderStatus.COMPLETED: [],
        RadiologyOrderStatus.CANCELLED: [],
    }

    @staticmethod
    @transaction.atomic
    def create_order(
        *,
        patient=None,
        customer=None,
        doctor=None,
        visit=None,
        studies: list[dict],
        priority: str = "routine",
        clinical_notes: str = "",
        created_by_id: str = "",
    ) -> RadiologyOrder:
        from common.validators import validate_orderer

        validate_orderer(
            patient.id if patient else None,
            customer.id if customer else None,
        )

        order = RadiologyOrder.objects.create(
            order_number=generate_order_number("RAD"),
            patient=patient,
            customer=customer,
            doctor=doctor,
            visit=visit,
            priority=priority,
            clinical_notes=clinical_notes,
            status=RadiologyOrderStatus.ORDERED,
        )

        for s in studies:
            RadiologyStudy.objects.create(
                order=order,
                modality=s["modality"],
                body_part=s.get("body_part", ""),
                description=s.get("description", ""),
            )

        logger.info("radiology_order_created", order_id=str(order.id), order_number=order.order_number)
        return order

    @staticmethod
    @transaction.atomic
    def transition_status(
        *,
        order: RadiologyOrder,
        new_status: str,
        performed_by_id: str = "",
    ) -> RadiologyOrder:
        allowed = RadiologyService.VALID_TRANSITIONS.get(order.status, [])
        if new_status not in allowed:
            raise ServiceError(
                f"Cannot transition from {order.status} to {new_status}.",
                code="INVALID_TRANSITION",
            )

        order.status = new_status
        if new_status == RadiologyOrderStatus.COMPLETED:
            order.completed_at = timezone.now()
            RadiologyService._auto_bill(order=order, created_by_id=performed_by_id)

        order.save(update_fields=["status", "completed_at", "updated_at"])
        logger.info("radiology_order_status_changed", order_id=str(order.id), new_status=new_status)
        return order

    @staticmethod
    def _auto_bill(*, order: RadiologyOrder, created_by_id: str = "") -> None:
        """Create draft invoice for completed radiology order."""
        try:
            from apps.billing.services import BillingService

            studies = list(order.studies.all())
            if not studies:
                return

            items = [
                {
                    "item_type": "radiology",
                    "description": f"{s.modality.upper()} - {s.body_part}",
                    "quantity": 1,
                    "unit_price": Decimal("50.00"),
                }
                for s in studies
            ]

            invoice = BillingService.create_from_source(
                source_type="radiology_order",
                source_id=str(order.id),
                patient=order.patient,
                customer=order.customer,
                items=items,
                created_by_id=created_by_id,
            )
            order.invoice = invoice
            order.save(update_fields=["invoice", "updated_at"])
        except Exception as e:
            logger.warning("radiology_auto_bill_failed order_id=%s err=%s", order.id, e)

    @staticmethod
    @transaction.atomic
    def record_report(
        *,
        study: RadiologyStudy,
        findings: str,
        impression: str = "",
        is_critical: bool = False,
        reported_by_id: str,
        image_object_key: str = "",
    ) -> RadiologyReport:
        if hasattr(study, "report") and study.report:
            raise ServiceError("Report already exists for this study.", code="DUPLICATE_REPORT")

        report = RadiologyReport.objects.create(
            study=study,
            findings=findings,
            impression=impression,
            is_critical=is_critical,
            reported_by_id=reported_by_id,
            image_object_key=image_object_key,
        )

        if is_critical:
            RadiologyService._notify_critical(report=report)

        logger.info("radiology_report_created", study_id=str(study.id), is_critical=is_critical)
        return report

    @staticmethod
    def _notify_critical(*, report: RadiologyReport) -> None:
        try:
            from apps.notifications.services import NotificationService
            from common.enums import NotificationType, NotificationChannel

            order = report.study.order
            recipient_id = str(order.doctor.user_id) if order.doctor_id else None
            if not recipient_id:
                return

            NotificationService.create_and_send(
                recipient_id=recipient_id,
                notification_type=NotificationType.SYSTEM,
                title="CRITICAL radiology finding",
                body=f"Critical finding on {report.study.modality} - {report.study.body_part}: {report.impression[:100]}",
                channel=NotificationChannel.IN_APP,
                data={"report_id": str(report.id), "order_id": str(report.study.order_id)},
            )
        except Exception as e:
            logger.warning("critical_notify_failed: %s", e)
