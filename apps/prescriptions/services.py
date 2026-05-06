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
