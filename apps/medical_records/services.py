"""
Medical records service layer — visit lifecycle and signing.
"""
import structlog
from django.utils import timezone

from common.exceptions import ServiceError

from .models import Diagnosis, Visit, Vitals

logger = structlog.get_logger(__name__)


class VisitService:

    @staticmethod
    def create_visit(
        *,
        patient,
        doctor,
        visit_date,
        chief_complaint: str,
        appointment=None,
        **kwargs,
    ) -> Visit:
        visit = Visit.objects.create(
            patient=patient,
            doctor=doctor,
            visit_date=visit_date,
            chief_complaint=chief_complaint,
            appointment=appointment,
            **kwargs,
        )
        logger.info("visit_created", visit_id=str(visit.id), patient_id=str(patient.id))
        return visit

    @staticmethod
    def update_visit(visit: Visit, **fields) -> Visit:
        """Update a visit. Raises if already signed."""
        if visit.is_signed:
            raise ServiceError(
                "Cannot modify a signed visit record.",
                code="VISIT_SIGNED",
            )

        update_fields = []
        for key, value in fields.items():
            if hasattr(visit, key) and key not in ("is_signed", "signed_at", "id"):
                setattr(visit, key, value)
                update_fields.append(key)

        if update_fields:
            visit.save(update_fields=update_fields + ["updated_at"])
        return visit

    @staticmethod
    def sign_visit(visit: Visit) -> Visit:
        """Sign and lock the visit record. Irreversible."""
        if visit.is_signed:
            raise ServiceError("Visit is already signed.", code="ALREADY_SIGNED")

        visit.is_signed = True
        visit.signed_at = timezone.now()
        visit.save(update_fields=["is_signed", "signed_at", "updated_at"])
        logger.info("visit_signed", visit_id=str(visit.id))
        return visit

    @staticmethod
    def record_vitals(visit: Visit, recorded_by_id: str, **vital_data) -> Vitals:
        if visit.is_signed:
            raise ServiceError("Cannot add vitals to a signed visit.", code="VISIT_SIGNED")

        return Vitals.objects.create(
            visit=visit,
            recorded_by_id=recorded_by_id,
            **vital_data,
        )

    @staticmethod
    def add_diagnosis(visit: Visit, *, icd_code: str, description: str, **kwargs) -> Diagnosis:
        if visit.is_signed:
            raise ServiceError("Cannot add diagnosis to a signed visit.", code="VISIT_SIGNED")

        return Diagnosis.objects.create(
            visit=visit,
            icd_code=icd_code,
            description=description,
            **kwargs,
        )
