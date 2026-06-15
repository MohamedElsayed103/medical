# 04 — Prescriptions ↔ Visits ↔ Pharmacy

Covers **#15** (finalized prescription auto-flows to pharmacy) and **#16** (prescription is part of
the visit). Depends on `02` (permissions). Touches `06` (pharmacy dispense queue) — keep consistent.

---

## Current state (verified)
- `Prescription` (tenant): `patient`, `doctor`, optional `visit` FK (already exists!), `notes`,
  `is_dispensed`, `dispensed_at`. `PrescriptionItem`: medication, dosage, frequency, duration, route,
  quantity, is_prn.
- `PrescriptionService.create_prescription(patient, doctor, visit=None, notes, items)` exists and
  accepts `visit`.
- TWO dispense flows exist:
  - `PrescriptionService.dispense(prescription)` — just sets `is_dispensed=True` (no inventory).
  - `PharmacyService.dispense_prescription(prescription, dispensed_by_id, notes)` — FEFO inventory
    deduction, creates `DispenseRecord` + `DispenseItem` + `StockTransaction`, sets `is_dispensed`.
- `GET /api/v1/pharmacy/dispense-queue/` currently lists prescriptions where `not is_dispensed`.
- Frontend: `PrescriptionsPage.tsx` (standalone create). `VisitDetailPage.tsx` shows visit info.
  `visitsService` has no prescription methods; `prescriptionsService.create` takes a `visit` field
  only if the create payload includes it (verify the serializer exposes `visit_id`).

---

## #16 — Prescription as part of the visit

Goal: a doctor creates the prescription **from within the visit**, and it's linked to that visit.

### Backend
- Confirm the prescription create serializer (`apps/prescriptions/serializers.py`) exposes a writable
  `visit_id` (or `visit`) field mapping to `Prescription.visit`. If missing, add it (write-only,
  `required=False`, `allow_null=True`).
- Add a convenience nested read on the visit: `GET /api/v1/visits/{id}/prescriptions/` listing
  prescriptions where `visit_id == id`. Implement as an `@action(detail=True)` on the visit viewset
  (`apps/medical_records/views.py`) → permission `prescriptions:read`. (Patient-level list already
  exists via `/patients/{id}/prescriptions/`.)
- Guard: do not allow creating/editing a prescription against a **signed** visit's clinical content,
  but prescribing itself is fine post-sign? Decision: **allow prescriptions to be added even after the
  visit is signed** is risky for immutability. Default: **block adding new prescriptions to a signed
  visit** (raise `ServiceError(code="VISIT_SIGNED")`), matching the visit-immutability rule. Document
  this; if the clinic wants post-sign prescribing, relax later.

### Frontend
- In `VisitDetailPage.tsx`, add a **Prescriptions** section listing this visit's prescriptions
  (`visitsService.getPrescriptions(visitId)` → new service method hitting `/visits/{id}/prescriptions/`).
- Add a "Add Prescription" button (gated `prescriptions:write`, hidden when visit `is_signed`) that
  opens a prescription form modal pre-filled with `patient_id`, `doctor_id`, and `visit_id` from the
  visit. Reuse the existing prescription create form from `PrescriptionsPage` — extract it into a
  shared `PrescriptionFormModal.tsx` taking optional `visitId`/`patientId` props so both the
  standalone page and the visit page use it.
- `prescriptionsService.create` payload includes `visit_id` when launched from a visit.

### Acceptance
- From a visit, a doctor adds a prescription; it appears in the visit's Prescriptions section and in
  the patient's Prescriptions tab, with `visit` populated.
- Standalone prescription creation (no visit) still works.

---

## #15 — Finalized prescription auto-flows to pharmacy

Goal: when a doctor finalizes a prescription, it shows up in the pharmacy's work queue and a
pharmacist is notified — no manual hand-off.

### Design decision (resolves the two-dispense-flow ambiguity)
- A prescription becoming "ready for pharmacy" must **create a `DispenseRecord` with
  `status=PENDING`** (this is the canonical pharmacy work item), rather than relying only on the
  `is_dispensed=False` filter. This makes the queue explicit, statusful (PENDING→PREPARING→READY→
  DISPENSED), and notifiable.
- `is_dispensed` stays as the final completion flag set when the dispense is actually handed over
  (by `PharmacyService.dispense_prescription`).

### Backend changes

**`apps/prescriptions/services.py`** — at the end of `create_prescription(...)` (after items are
created), and/or in a new explicit `finalize(prescription)`:
```python
from apps.pharmacy.services import PharmacyService   # import inside function to avoid cycles
PharmacyService.enqueue_for_dispense(prescription)
```
> If you want create != finalize, add a `finalized` boolean or a `finalize` action; simplest given
> the current model (no draft state on Prescription) is to enqueue **on create**. Default: **enqueue
> on create**. Document this; if a draft phase is wanted later, add a status field.

**`apps/pharmacy/services.py`** — add:
```python
@staticmethod
@transaction.atomic
def enqueue_for_dispense(prescription) -> "DispenseRecord":
    # idempotent: don't double-enqueue
    existing = DispenseRecord.objects.filter(
        prescription=prescription, status__in=[DispenseStatus.PENDING, DispenseStatus.PREPARING, DispenseStatus.READY]
    ).first()
    if existing:
        return existing
    record = DispenseRecord.objects.create(prescription=prescription, status=DispenseStatus.PENDING)
    PharmacyService._notify_pharmacists(
        title="New prescription to dispense",
        body=f"Rx for {prescription.patient.full_name} is ready for dispensing.",
        data={"action": "dispense", "prescription_id": str(prescription.id),
              "dispense_record_id": str(record.id)},
    )
    return record
```
- Add `_notify_pharmacists(...)` helper (shared with file 06 #14): resolves all `TenantUser`s whose
  role has `pharmacy:write` (or role name "Pharmacist") and calls
  `NotificationService.create_and_send` for each `user_id`. See file 06 for the exact resolver.
- Update `GET /pharmacy/dispense-queue/` to return **`DispenseRecord`s with status in
  (PENDING, PREPARING, READY)** (joined to prescription + patient + items), instead of raw
  prescriptions. Keep response shape backward-compatible for the frontend (include prescription +
  patient + items). Update `apps/pharmacy/serializers.py` accordingly.

**Avoid import cycles:** import `PharmacyService` lazily inside the prescription service function
(as shown), since pharmacy already imports prescription models.

### Frontend
- Pharmacy "Dispense Queue" (in `PharmacyPage.tsx` or a dedicated Orders page from file 06) now lists
  pending `DispenseRecord`s with patient, Rx items, and status; pharmacist advances status and
  dispenses (calls existing `pharmacyService.dispense`).
- The pharmacist receives an in-app notification when a new prescription is enqueued.

### Acceptance
- Doctor creates a prescription → a PENDING `DispenseRecord` appears in the pharmacy dispense queue
  and pharmacists get a notification.
- Enqueue is idempotent (editing/re-saving doesn't create duplicate queue items).
- Completing the dispense deducts inventory (existing FEFO logic) and sets `is_dispensed=True`.
