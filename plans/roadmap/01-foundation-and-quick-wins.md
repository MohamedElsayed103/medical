# Plan 01 — Foundation & Quick Wins  (Tier P0)

Goal: make the product *feel finished* and stop the class of bugs we just fixed (clickability,
field-name drift, silent serializer errors). Low risk, high perceived value. Do this first.

Track status in [`PROGRESS.md`](./PROGRESS.md).

---

## 1.1 — Make ALL list rows clickable to a detail view  ·  P0

**Why:** Inconsistent clickability reads as "unfinished." Invoices/labs/prescriptions/radiology are
done; finish the rest.

**Frontend**
- Audit every list page under `frontend/src/pages/**`. For each row that has a meaningful detail:
  wrap it in `useNavigate()` → `/<resource>/:id` (or a `<Link>`), add `cursor-pointer`, and put
  `onClick={(e)=>e.stopPropagation()}` on any inline action buttons (same pattern as `BillingPage`).
- Pages to address: `pharmacy/PharmacyPage.tsx` (inventory item → detail), `insurance/InsurancePage.tsx`
  (policy/claim → detail), `appointments/AppointmentsPage.tsx` (row → appointment detail), `visits/VisitsPage.tsx`
  (confirm already links).
- Build missing detail pages where none exists yet: **AppointmentDetailPage**, **PharmacyItemDetailPage**,
  **InsurancePolicyDetailPage / InsuranceClaimDetailPage**. Add routes in `App.tsx`.

**Acceptance:** every list row navigates to a populated detail page; no dead `/x/:id` routes; action
buttons don't trigger row navigation.

---

## 1.2 — Reusable detail-page scaffold + StatusTimeline + StatusChip  ·  P0

**Why:** We're repeating the same detail layout (back link → header w/ chips → cards → related
sections). Standardize to cut build time and unify look.

**Frontend (`frontend/src/components/`)**
- `DetailPage.tsx` — props: `backTo`, `title`, `icon`, `chips: {label,color}[]`, `actions`, `children`.
- `StatusChip.tsx` — maps a status string → colored pill (centralize the per-domain color maps that
  are currently copy-pasted in each page).
- `StatusTimeline.tsx` — horizontal stepper for FSM-driven entities (lab order, radiology order,
  invoice, appointment). Pass `steps` + `current`.
- Refactor existing detail pages (`InvoiceDetailPage`, `LabOrderDetailPage`, `RadiologyOrderDetailPage`,
  `PrescriptionDetailPage`, `MedicationDetailPage`) to use them.

**Acceptance:** one scaffold powers all detail pages; status colors defined once.

---

## 1.3 — Patient 360 timeline  ·  P0 (highest value in this plan)

**Why:** The chart clinicians live in. Single biggest "this is real software" signal.

**Backend (`apps/patients/`)**
- `PatientService.timeline(patient, *, since=None, kinds=None)` → merged, reverse-chron list of events:
  visits, prescriptions, lab orders, radiology orders, invoices, (later) problems/allergies. Each
  event: `{type, id, occurred_at, title, subtitle, status, link}`. Pull from the existing
  per-resource querysets filtered by `patient_id`.
- Endpoint: `GET /api/v1/patients/{id}/timeline/?kinds=visit,lab&since=...` → `patients:read`.
- Also expose summary blocks the page needs: active medications (from latest non-dispensed Rx items),
  open orders, outstanding balance (sum of invoice balances). Add `GET /patients/{id}/summary/`.

**Frontend**
- Enrich `pages/patients/PatientDetailPage.tsx`: add an **Overview** tab with a vertical timeline
  (icon per event type, colored status chip, deep-link to the event's detail page) + summary cards
  (active meds, allergies, problems, balance, next appointment).
- `patientsService.getTimeline(id, params)` and `getSummary(id)` in `api.ts`; types in `types/index.ts`.

**Acceptance:** opening a patient shows a chronological chart spanning all modules; each item links out.

---

## 1.4 — Provider profile detail page  ·  P1

**Backend:** `GET /api/v1/appointments/doctors/{id}/` already serializes `DoctorProfile`; add
`@action` `schedule/` returning this week's appointments + availability windows + time-off, and
lightweight productivity counts (appointments completed last 30d).

**Frontend:** `pages/providers/ProviderDetailPage.tsx` + route `/providers/:id`: bio, specialization,
availability grid (reuse from `DoctorAvailabilityPage`), today's schedule, patient panel. Link doctor
names (in appointments/visits/orders) to it.

**Acceptance:** clicking a doctor anywhere opens their profile with live schedule.

---

## 1.5 — Visit detail enrichment  ·  P1

**Backend:** ensure `GET /visits/{id}/` nests vitals, diagnoses, and links to prescriptions
(`/visits/{id}/prescriptions/`), lab orders, radiology orders filtered by `visit_id`. Add those
filters to the respective viewsets if missing.

**Frontend:** `pages/visits/VisitDetailPage.tsx`: vitals **sparklines** (recharts) for repeated
measures, SOAP sections, linked-orders sections with deep links, "Sign & lock" affordance (disabled
once `is_signed`), and an "Add prescription/lab/imaging from this visit" action that pre-fills `visit_id`.

**Acceptance:** a visit is a true encounter hub; signing locks edits; orders link back to the visit.

---

## 1.6 — Print / PDF artifacts  ·  P0

**Why:** Billing/clinical trust = printable documents.

**Backend (recommended: server-side PDF for fidelity)**
- Add `weasyprint` (or `reportlab`) to requirements. Create `common/pdf.py::render_pdf(template, ctx)`.
- Endpoints returning `application/pdf`:
  - `GET /invoices/{id}/pdf/` (invoice/receipt), `GET /prescriptions/{id}/pdf/`,
    `GET /lab-orders/{id}/pdf/`, `GET /radiology/orders/{id}/pdf/`.
  - HTML templates under `templates/pdf/` with clinic letterhead (tenant name/logo).

**Frontend:** a "Print / Download PDF" button on each detail page (`window.open` the pdf URL, or fetch
as blob with auth header and open). Add `*.getPdf(id)` helpers in `api.ts`.

**Acceptance:** each detail page can produce a clean, branded PDF.

---

## 1.7 — Global search  ·  P1

**Backend:** `GET /api/v1/search/?q=` → cross-resource search (patients by name/MRN/phone, invoices by
number, orders by number). Implement as a small `apps/search/` view or a `common` view aggregating
existing querysets; cap results per type. Permission: union of read perms (filter results by what the
user may see).

**Frontend:** command-palette style search in `components/navigation/TopBar.tsx` (⌘K), grouped
results, each linking to its detail page.

**Acceptance:** typing a patient name/MRN or an order number jumps straight to it.

---

## 1.8 — Normalize API error surfacing  ·  P0 (quick, prevents silent failures)

**Why:** Backend returns `{"error":{"code","message"}}` (see `common/exceptions.py`) but many toasts
read `error.detail`, so users see "An unexpected error occurred" or nothing.

**Frontend (`src/lib/api.ts`)**
- In the response interceptor, attach a normalized `err.message` derived from
  `data?.error?.message ?? data?.detail ?? <field errors> ?? 'Something went wrong'`.
- Replace ad-hoc `e?.response?.data?.detail` reads in mutations with the normalized message helper.

**Acceptance:** business-rule errors (e.g. `OUTSIDE_AVAILABILITY`, `VISIT_SIGNED`) show their real
message in a toast.

---

## 1.9 — API smoke tests per viewset  ·  P0 (stops the bugs we just fixed)

**Why:** The radiology `is_deleted` 500 and the availability `doctor_id` drop were invisible to unit
tests because nothing exercised the request path.

**Backend (`apps/<app>/tests/`)**
- pytest + DRF `APIClient`, authenticated as the seeded admin in a `demo_clinic` test tenant.
- For each viewset: happy-path **create → retrieve → list → (transition/action)**, asserting 2xx and
  key response fields. Prioritize: radiology, lab orders, prescriptions, appointments+availability,
  billing, medications (incl. multipart image upload).
- Run in CI: `DJANGO_SETTINGS_MODULE=config.settings.testing … pytest`.

**Acceptance:** `pytest` covers the create/transition path of every clinical viewset; CI gate added.

---

## 1.10 — OpenAPI-generated TypeScript client  ·  P0

**Why:** Frontend/backend disagreed on field names (`doctor_name` vs `doctor`, `visit_id` vs `visit`,
`test.result_value` vs `test.result.value`). Generating types from the schema makes drift impossible.

- `drf-spectacular` is installed and serves `/api/schema/`. Add a frontend script:
  `npm run gen:api` → `openapi-typescript /api/schema/ -o src/types/api.gen.ts` (or `orval` for a full
  client). Replace hand-written interfaces in `src/types/index.ts` incrementally with generated ones.
- Add response serializers to actions that return ad-hoc dicts (e.g. `available-slots`, `timeline`)
  with `@extend_schema` so they appear in the schema.

**Acceptance:** types regenerate from the backend; a renamed serializer field breaks the FE build, not prod.

---

## 1.11 — Seed/demo data + one-command bootstrap  ·  P1

**Backend:** `manage.py seed_demo` (idempotent) creating a tenant with doctors (+ availability),
patients, a few visits/rx/lab/rays/invoices/medications-with-images, so demos and tests start populated.

**Dev DX:** a `make dev` / `scripts/dev.sh` that brings up the DB (docker), runs migrations + seed,
and starts backend + frontend. Fix the broken `venv/` reference in docs; keep `requirements/*.txt`
authoritative (Pillow already added).

**Acceptance:** a fresh clone reaches a populated, running app in one command.
