# 07 — Lab Ordering (internal/external) & Radiology (Rays) App

Covers **#10** (lab orders for internal patients AND external walk-ins) and **#11** (new Radiology
"rays" app, full feature set). Depends on `05` (Customer, `validate_orderer`,
`BillingService.create_from_source`) and `02` (`lab_results:*`, `radiology:*`, `customers:*`).

---

## Part 1 — Lab ordering: internal & external (#10)

### Current state (verified)
`LabOrder` (tenant): **non-null** `patient` FK, **non-null** `doctor` FK, `order_number` (unique),
`status` FSM (ORDERED→SAMPLE_COLLECTED→PROCESSING→COMPLETED→CANCELLED), `priority`, `visit` (nullable).
`LabTest` (order, test_name, code, specimen_type). `TestResult` (1:1 test, value, unit, ranges, flag,
`auto_flag()`, resulted_by_id). Endpoints under `/api/v1/lab-orders/`.

### Schema changes — `apps/lab_results/models.py`
Apply the file-05 orderer pattern:
- Make `patient` **nullable**: `null=True, blank=True` (keep `on_delete=PROTECT`).
- Add `customer = models.ForeignKey("patients.Customer", null=True, blank=True,
  on_delete=models.PROTECT, related_name="lab_orders")`.
- Make `doctor` **nullable** too: external walk-in lab orders may have no ordering doctor
  (`null=True, blank=True`). Document: clinical/internal orders still set doctor.
- Add `orderer_name` / `orderer_type` properties (file 05 Part B).
- Add `invoice = models.ForeignKey("billing.Invoice", null=True, blank=True, on_delete=SET_NULL,
  related_name="lab_orders")` for the auto-bill link.

Migration: existing rows keep their `patient`/`doctor`; new nullables are safe.
`makemigrations lab_results` → `migrate_schemas`.

### Service — `apps/lab_results/services.py`
- In the create-order method, resolve orderer with the file-05 convention (patient_id OR customer_id
  OR inline customer_name+phone → `CustomerService.get_or_create_by_phone`), then
  `validate_orderer(...)`. Allow `doctor=None` for external orders.
- When the order transitions to **COMPLETED**, auto-bill:
  ```python
  BillingService.create_from_source(
      source_type="lab_order", source_id=str(order.id),
      patient=order.patient, customer=order.customer,
      items=[{"item_type": "lab_test", "description": t.test_name,
              "quantity": 1, "unit_price": _price_for_test(t)} for t in order.tests.all()],
      created_by_id=acting_user_id)
  ```
  (`_price_for_test` can read a per-test price; if no pricing table exists yet, default to a
  configurable flat fee or 0 with a TODO — keep it explicit, don't silently bill 0 without logging.)

### API / Frontend
- Lab order create endpoint + form accept the orderer choice (internal patient vs external
  name+phone), mirroring the pharmacy order UI from file 06. Reuse an "OrdererPicker" component
  (build once, share across pharmacy/lab/rays).
- `labOrdersService.create` payload includes orderer fields. Detail page (built in file 01) shows
  `orderer_name`/`orderer_type`.

### Acceptance
- A walk-in (name+phone) can have a lab order with tests, no patient record, billed to a Customer on
  completion; internal patient flow unchanged.

---

## Part 2 — Radiology (Rays) app (#11)

New tenant-schema Django app `apps/radiology/`, structured exactly like `lab_results` (the closest
analog). Mirrors its patterns: order → studies/exams → report/result, status FSM, auto-flag-style
report, internal/external orderer, auto-bill on completion. AI hooks into the existing
`AIRequestType.RADIOLOGY`.

### 2a. Create the app skeleton
```
apps/radiology/
  __init__.py
  apps.py            # RadiologyConfig, name="apps.radiology"
  models.py
  services.py
  serializers.py
  views.py
  urls.py
  admin.py
  migrations/__init__.py
  tests/__init__.py
```
Register in `config/settings/base.py` → add `"apps.radiology"` to **`TENANT_APPS`** (tenant-scoped).
Add to `config/urls.py`: `path("api/v1/radiology/", include("apps.radiology.urls", namespace="radiology"))`.

### 2b. Enums — `common/enums.py`
```python
class RadiologyModality(models.TextChoices):
    XRAY = "xray", "X-Ray"
    CT = "ct", "CT Scan"
    MRI = "mri", "MRI"
    ULTRASOUND = "ultrasound", "Ultrasound"
    MAMMOGRAPHY = "mammography", "Mammography"
    FLUOROSCOPY = "fluoroscopy", "Fluoroscopy"
    PET = "pet", "PET Scan"

class RadiologyOrderStatus(models.TextChoices):
    ORDERED = "ordered", "Ordered"
    SCHEDULED = "scheduled", "Scheduled"
    IN_PROGRESS = "in_progress", "In Progress"     # acquisition
    AWAITING_REPORT = "awaiting_report", "Awaiting Report"
    COMPLETED = "completed", "Completed"           # report finalized
    CANCELLED = "cancelled", "Cancelled"
```
(`LabPriority` already exists — reuse routine/urgent/stat.)

### 2c. Models — `apps/radiology/models.py`
```python
class RadiologyOrder(BaseModel):
    patient = models.ForeignKey("patients.Patient", null=True, blank=True,
                                on_delete=models.PROTECT, related_name="radiology_orders")
    customer = models.ForeignKey("patients.Customer", null=True, blank=True,
                                 on_delete=models.PROTECT, related_name="radiology_orders")
    doctor = models.ForeignKey("appointments.DoctorProfile", null=True, blank=True,
                               on_delete=models.PROTECT, related_name="radiology_orders")
    visit = models.ForeignKey("medical_records.Visit", null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="radiology_orders")
    order_number = models.CharField(max_length=30, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=RadiologyOrderStatus.choices,
                              default=RadiologyOrderStatus.ORDERED)
    priority = models.CharField(max_length=10, choices=LabPriority.choices, default=LabPriority.ROUTINE)
    clinical_notes = models.TextField(blank=True)
    invoice = models.ForeignKey("billing.Invoice", null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="radiology_orders")
    ordered_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "radiology_order"
        ordering = ["-ordered_at"]
        indexes = [models.Index(fields=["status", "priority"])]
    AUDITED = True
    # + orderer_name / orderer_type properties (file 05 Part B)

class RadiologyStudy(BaseModel):
    """One imaging study within an order (e.g. 'Chest X-Ray PA view')."""
    order = models.ForeignKey(RadiologyOrder, on_delete=models.CASCADE, related_name="studies")
    modality = models.CharField(max_length=20, choices=RadiologyModality.choices)
    body_part = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    performed_by_id = models.UUIDField(null=True, blank=True, help_text="Radiographer user id")
    performed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "radiology_study"

class RadiologyReport(BaseModel):
    """Radiologist's findings for a study (1:1)."""
    study = models.OneToOneField(RadiologyStudy, on_delete=models.CASCADE, related_name="report")
    findings = models.TextField()
    impression = models.TextField(blank=True)
    is_critical = models.BooleanField(default=False, help_text="Critical/urgent finding flag")
    reported_by_id = models.UUIDField(help_text="Radiologist user id")
    reported_at = models.DateTimeField(auto_now_add=True)
    # optional image storage (MinIO is configured): store object key, not the blob
    image_object_key = models.CharField(max_length=500, blank=True,
                                         help_text="MinIO object key for the DICOM/image, if uploaded")

    class Meta:
        db_table = "radiology_report"
```

### 2d. Service — `apps/radiology/services.py`
Mirror `lab_results` service patterns:
- `create_order(*, created_by_id, patient_id/customer..., doctor_id=None, priority, clinical_notes,
  studies: list[dict])` → resolve orderer (file 05), `validate_orderer`, create order + studies,
  `generate_order_number("RX")` (or "RAD").
- `transition_status(order, new_status, ...)` with an FSM dict mirroring lab's transitions.
- `record_report(*, study, reported_by_id, findings, impression, is_critical, image_object_key="")`
  → create `RadiologyReport`; if `is_critical`, notify the ordering doctor (if any) via
  `NotificationService` (like lab critical values).
- On order → COMPLETED: `BillingService.create_from_source(source_type="radiology_order", ...,
  items=[{item_type:"procedure", description: f"{study.modality} {study.body_part}", quantity:1,
  unit_price:_price(study)}])` and set `completed_at`.

### 2e. Serializers / Views / URLs
- Serializers for order (+ nested studies + report), study, report; orderer fields per file 05.
- `RadiologyOrderViewSet` (CRUD + status actions + `record_report` action), permissions:
  - list/retrieve → `radiology:read`; create → `radiology:write`; record report / acquisition →
    `radiology:result`. (Match the grid in file 02.)
- URLs under `/api/v1/radiology/orders/...` (router). Add `record-report` and status-transition
  actions analogous to lab-orders.

### 2f. AI integration (optional, wire if time permits)
`AIRequestType.RADIOLOGY` already exists. A `record_report` flow can attach an AI pre-read by creating
an `AIRequest` (existing app) referencing the study's `image_object_key`. Keep this optional — the
core report entry must work without the AI service.

### 2g. Migration
`makemigrations radiology` → `migrate_schemas` (tenant). Because it's a brand-new app, also ensure it
migrates into existing tenants (`migrate_schemas` iterates all tenant schemas).

### 2h. Frontend
- New `pages/radiology/RadiologyPage.tsx` (list) + `RadiologyOrderDetailPage.tsx`, routes
  `/radiology` and `/radiology/:id`, both gated `radiology:read`.
- `radiologyService` in `src/services/api.ts`: `getAll`, `getById`, `create`, status transitions,
  `recordReport`. Types in `src/types/`.
- Sidebar: add a "Radiology" nav item (icon e.g. `Scan`/`Radiation` from lucide) with
  `permission: 'radiology:read'`.
- Order create form: OrdererPicker (shared, internal/external) + add studies (modality + body part).
  Report entry form on the detail page (findings, impression, critical flag, optional image upload to
  MinIO via a presigned URL if file upload is wired; otherwise skip image for v1).

### Acceptance
- Create a radiology order (internal or external orderer) with one or more studies; radiologist
  records a report; a critical finding notifies the ordering doctor; completing the order auto-creates
  a DRAFT invoice with one line per study.
- Sidebar shows Radiology only for users with `radiology:read`.
