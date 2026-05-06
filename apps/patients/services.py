"""
Patient service layer.
"""
import structlog

from common.exceptions import ServiceError
from common.utils import encrypt_field, generate_mrn

from .models import Patient

logger = structlog.get_logger(__name__)


class PatientService:

    @staticmethod
    def register_patient(
        *,
        first_name: str,
        last_name: str,
        date_of_birth,
        gender: str,
        phone: str,
        national_id: str = "",
        **kwargs,
    ) -> Patient:
        """Register a new patient within the current tenant schema."""
        mrn = generate_mrn()

        # Encrypt sensitive field
        national_id_encrypted = encrypt_field(national_id) if national_id else ""

        patient = Patient.objects.create(
            medical_record_number=mrn,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            gender=gender,
            phone=phone,
            national_id_encrypted=national_id_encrypted,
            **kwargs,
        )
        logger.info("patient_registered", patient_id=str(patient.id), mrn=mrn)
        return patient

    @staticmethod
    def update_patient(patient: Patient, **fields) -> Patient:
        """Update mutable patient fields."""
        # Handle national_id encryption if provided
        national_id = fields.pop("national_id", None)
        if national_id is not None:
            patient.national_id_encrypted = encrypt_field(national_id)

        update_fields = []
        for key, value in fields.items():
            if hasattr(patient, key) and value is not None:
                setattr(patient, key, value)
                update_fields.append(key)

        if national_id is not None:
            update_fields.append("national_id_encrypted")

        if update_fields:
            patient.save(update_fields=update_fields + ["updated_at"])

        return patient

    @staticmethod
    def soft_delete_patient(patient: Patient) -> Patient:
        """Soft-delete a patient. Medical records must never be hard-deleted."""
        patient.soft_delete()
        logger.warning("patient_soft_deleted", patient_id=str(patient.id))
        return patient
