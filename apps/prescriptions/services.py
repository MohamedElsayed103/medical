"""
Prescription service layer.
"""
import structlog
from django.db import transaction
from django.utils import timezone

from common.exceptions import ServiceError

from .models import Medication, Prescription, PrescriptionItem

logger = structlog.get_logger(__name__)


class PrescriptionService:

    @staticmethod
    @transaction.atomic
    def create_prescription(
        *,
        patient,
        doctor,
        visit=None,
        notes: str = "",
        items: list[dict],
    ) -> Prescription:
        """
        Create a prescription with its items atomically.

        ``items`` is a list of dicts: {medication_id, dosage, frequency, duration, route, quantity, ...}
        """
        prescription = Prescription.objects.create(
            patient=patient,
            doctor=doctor,
            visit=visit,
            notes=notes,
        )

        for item_data in items:
            medication = Medication.objects.get(pk=item_data["medication_id"])
            PrescriptionItem.objects.create(
                prescription=prescription,
                medication=medication,
                dosage=item_data["dosage"],
                frequency=item_data["frequency"],
                duration=item_data["duration"],
                route=item_data.get("route", "oral"),
                quantity=item_data["quantity"],
                instructions=item_data.get("instructions", ""),
                is_prn=item_data.get("is_prn", False),
            )

        logger.info(
            "prescription_created",
            prescription_id=str(prescription.id),
            patient_id=str(patient.id),
            item_count=len(items),
        )

        try:
            PrescriptionService.enqueue_for_dispense(prescription=prescription)
        except Exception as e:
            logger.warning("enqueue_for_dispense_failed_on_create prescription=%s err=%s", prescription.id, e)

        return prescription

    @staticmethod
    def dispense(prescription: Prescription) -> Prescription:
        if prescription.is_dispensed:
            raise ServiceError("Prescription is already dispensed.", code="ALREADY_DISPENSED")

        prescription.is_dispensed = True
        prescription.dispensed_at = timezone.now()
        prescription.save(update_fields=["is_dispensed", "dispensed_at", "updated_at"])
        logger.info("prescription_dispensed", prescription_id=str(prescription.id))
        return prescription

    @staticmethod
    def update_prescription(prescription: Prescription, **fields) -> Prescription:
        if prescription.is_dispensed:
            raise ServiceError(
                "Cannot modify a dispensed prescription.",
                code="PRESCRIPTION_DISPENSED",
            )

        update_fields = []
        for key, value in fields.items():
            if hasattr(prescription, key) and key not in ("is_dispensed", "dispensed_at"):
                setattr(prescription, key, value)
                update_fields.append(key)

        if update_fields:
            prescription.save(update_fields=update_fields + ["updated_at"])
        return prescription

    @staticmethod
    @transaction.atomic
    def enqueue_for_dispense(*, prescription: Prescription) -> None:
        """
        When a prescription is finalized, create a pharmacy order draft for it.
        Called from finalize_prescription or visit signing.
        """
        try:
            from apps.pharmacy.services import PharmacyOrderService

            # Only enqueue prescriptions that have not yet been dispensed.
            if prescription.is_dispensed:
                return

            items = [
                {
                    "medication_id": str(item.medication_id),
                    "quantity": item.quantity,
                }
                for item in prescription.items.select_related("medication").all()
            ]

            if not items:
                return

            order = PharmacyOrderService.create_order(
                created_by_id=str(prescription.doctor_id) if prescription.doctor_id else "",
                patient_id=str(prescription.patient_id) if prescription.patient_id else None,
                prescription_id=str(prescription.id),
                items=items,
                notes=f"Auto-created from prescription {prescription.id}",
            )
            logger.info(
                "prescription_enqueued_for_dispense",
                prescription_id=str(prescription.id),
                order_id=str(order.id),
            )
        except Exception as e:
            import logging as _logging
            _logging.getLogger(__name__).warning(
                "enqueue_for_dispense_failed prescription=%s err=%s", prescription.id, e
            )
