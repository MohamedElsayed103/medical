"""
Patient service layer.
"""
import structlog

from common.exceptions import ServiceError
from common.utils import encrypt_field, generate_mrn

from .models import Document, Patient

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

    @staticmethod
    def timeline(patient: Patient, *, kinds: list[str] | None = None, limit: int = 100) -> list[dict]:
        """Merged, reverse-chronological clinical timeline across all modules.

        Each event: {type, id, occurred_at(iso), title, subtitle, status, link}.
        `kinds` optionally filters to a subset of
        {visit, prescription, lab_order, radiology_order, invoice}.
        """
        from apps.medical_records.models import Visit
        from apps.prescriptions.models import Prescription
        from apps.lab_results.models import LabOrder
        from apps.billing.models import Invoice
        try:
            from apps.radiology.models import RadiologyOrder
        except Exception:  # app may be absent in some deployments
            RadiologyOrder = None

        want = set(kinds) if kinds else None
        events: list[dict] = []

        def included(kind: str) -> bool:
            return want is None or kind in want

        if included("visit"):
            for v in Visit.objects.filter(patient=patient).only(
                "id", "visit_date", "chief_complaint", "is_signed"
            )[:limit]:
                events.append({
                    "type": "visit", "id": str(v.id), "occurred_at": v.visit_date.isoformat(),
                    "title": v.chief_complaint or "Visit",
                    "subtitle": "Signed" if v.is_signed else "Unsigned",
                    "status": "completed" if v.is_signed else "active",
                    "link": f"/visits/{v.id}",
                })

        if included("prescription"):
            for rx in Prescription.objects.filter(patient=patient).prefetch_related("items__medication")[:limit]:
                meds = ", ".join(i.medication.name for i in rx.items.all()[:3]) or "Prescription"
                events.append({
                    "type": "prescription", "id": str(rx.id), "occurred_at": rx.prescribed_at.isoformat(),
                    "title": meds, "subtitle": f"{rx.items.count()} medication(s)",
                    "status": "dispensed" if rx.is_dispensed else "active",
                    "link": f"/prescriptions/{rx.id}",
                })

        if included("lab_order"):
            for o in LabOrder.objects.filter(patient=patient)[:limit]:
                events.append({
                    "type": "lab_order", "id": str(o.id), "occurred_at": o.ordered_at.isoformat(),
                    "title": f"Lab order {o.order_number}", "subtitle": f"{o.tests.count()} test(s)",
                    "status": o.status, "link": f"/lab-orders/{o.id}",
                })

        if RadiologyOrder and included("radiology_order"):
            for o in RadiologyOrder.objects.filter(patient=patient)[:limit]:
                events.append({
                    "type": "radiology_order", "id": str(o.id), "occurred_at": o.ordered_at.isoformat(),
                    "title": f"Imaging {o.order_number}", "subtitle": f"{o.studies.count()} study(ies)",
                    "status": o.status, "link": f"/radiology/{o.id}",
                })

        if included("invoice"):
            for inv in Invoice.objects.filter(patient=patient)[:limit]:
                events.append({
                    "type": "invoice", "id": str(inv.id), "occurred_at": inv.issued_at.isoformat(),
                    "title": f"Invoice {inv.invoice_number}",
                    "subtitle": f"${inv.total} • balance ${inv.balance_due}",
                    "status": inv.status, "link": f"/billing/{inv.id}",
                })

        events.sort(key=lambda e: e["occurred_at"], reverse=True)
        return events[:limit]

    @staticmethod
    def summary(patient: Patient) -> dict:
        """Chart summary blocks: active meds, open orders, outstanding balance, counts."""
        from decimal import Decimal
        from apps.medical_records.models import Visit
        from apps.prescriptions.models import Prescription
        from apps.lab_results.models import LabOrder
        from apps.billing.models import Invoice
        from common.enums import LabOrderStatus

        active_meds: list[str] = []
        for rx in Prescription.objects.filter(
            patient=patient, is_dispensed=False
        ).prefetch_related("items__medication")[:10]:
            for item in rx.items.all():
                if item.medication.name not in active_meds:
                    active_meds.append(item.medication.name)

        open_labs = LabOrder.objects.filter(patient=patient).exclude(
            status__in=[LabOrderStatus.COMPLETED, LabOrderStatus.CANCELLED]
        ).count()

        outstanding = Decimal("0.00")
        for inv in Invoice.objects.filter(patient=patient):
            bal = inv.balance_due
            if bal > 0:
                outstanding += bal

        return {
            "active_medications": active_meds,
            "open_lab_orders": open_labs,
            "outstanding_balance": str(outstanding),
            "visit_count": Visit.objects.filter(patient=patient).count(),
        }


# Allowed upload types + max size (10 MB) — basic content validation (Plan 02 #2.7).
ALLOWED_DOC_TYPES = {
    "application/pdf", "image/jpeg", "image/png", "image/gif", "image/webp",
    "text/plain", "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_DOC_SIZE = 10 * 1024 * 1024


class DocumentService:

    @staticmethod
    def create_from_upload(*, patient, uploaded_file, category: str, description: str = "",
                           uploaded_by_id: str | None = None) -> Document:
        if uploaded_file is None:
            raise ServiceError("No file provided.", code="NO_FILE")
        if uploaded_file.size > MAX_DOC_SIZE:
            raise ServiceError("File exceeds the 10 MB limit.", code="FILE_TOO_LARGE")
        content_type = getattr(uploaded_file, "content_type", "") or ""
        if content_type and content_type not in ALLOWED_DOC_TYPES:
            raise ServiceError(f"Unsupported file type: {content_type}", code="UNSUPPORTED_TYPE")

        doc = Document.objects.create(
            patient=patient,
            category=category or "other",
            file=uploaded_file,
            filename=getattr(uploaded_file, "name", "")[:255],
            content_type=content_type,
            size=uploaded_file.size,
            description=description,
            uploaded_by_id=uploaded_by_id,
        )
        logger.info("document_uploaded", document_id=str(doc.id), patient_id=str(patient.id),
                    category=doc.category, size=doc.size)
        return doc
