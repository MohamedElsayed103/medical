# Plan 03 — Clinical Depth  (Tier P1)

The features that appear on competitor comparison pages and that clinicians expect from a "real" EMR.
Depends on Plan 02 (for any document/imaging bits) but most items are independent.

Track status in [`PROGRESS.md`](./PROGRESS.md).

---

## 3.1 — Drug database integration + medication autocomplete  ·  P1

**Why:** `Medication` is free-text today. A coded drug DB enables interaction checking (3.2),
standardized strengths/forms, and clean prescribing.

**Backend (`apps/prescriptions/`)**
- Add coding fields to `Medication`: `rxnorm_cui`, `ndc`, `atc_code` (all `blank=True`, indexed).
- `services_drugdb.py` — adapter interface `DrugDBProvider` with a concrete `RxNormProvider`
  (NLM RxNorm REST) and/or `OpenFDAProvider`. Methods: `search(term)`, `get(rxcui)`,
  `interactions(rxcui_list)`. Cache responses (Redis) — external APIs are slow/rate-limited.
- Endpoint: `GET /prescriptions/drug-search/?q=` → normalized `{name, rxcui, strength, form}` list.

**Frontend:** in the prescription item form, replace the local medication `<select>` with an async
autocomplete hitting `drug-search`; selecting one upserts a local `Medication` row (so inventory/Rx
still reference a tenant `Medication`).

**Acceptance:** prescribing searches a real drug DB; chosen drugs carry RxNorm codes.

---

## 3.2 — Drug–drug & drug–allergy interaction checking  ·  P1 (flagship safety feature)

**Backend**
- `PrescriptionService.check_interactions(patient, new_items)` → calls the drug-DB provider with the
  patient's active meds + the new items, and cross-checks the patient allergy list (3.4). Returns
  `[{severity, a, b, description}]`.
- Run it inside `create_prescription` (non-blocking: return warnings in the response, do NOT hard-fail
  — clinician overrides with a reason, matching the human-in-the-loop philosophy). Persist overrides
  on the prescription for audit.
- Endpoint to pre-check before save: `POST /prescriptions/check-interactions/`.

**Frontend:** prescription modal calls the pre-check on item change; show a severity-colored banner
(`contraindicated/major/moderate/minor`); require an override note to proceed on major+.

**Acceptance:** prescribing two interacting drugs (or one the patient is allergic to) warns the
prescriber and records the override.

---

## 3.3 — Problem list  ·  P1

**Backend (`apps/medical_records/`)**
- `Problem(BaseModel)`: `patient`, `icd_code`, `description`, `status` (`active|resolved|chronic`),
  `onset_date`, `resolved_date`, `noted_by_id`, `visit` (nullable). `AUDITED = True`.
- `ProblemService` CRUD + resolve; endpoints `GET/POST /patients/{id}/problems/`,
  `PATCH /problems/{id}/`. Permission `medical_records:write`.

**Frontend:** Problems card on Patient 360 (1.3) + a manage modal (add/resolve, ICD picker from 3.5).

**Acceptance:** problems persist as structured, coded records and surface on the patient chart.

---

## 3.4 — Allergy list  ·  P1

**Backend:** `Allergy(BaseModel)`: `patient`, `substance` (+ optional `rxnorm_cui`), `reaction`,
`severity` (`mild|moderate|severe|anaphylaxis`), `noted_by_id`, `is_active`. `AUDITED = True`.
Endpoints `GET/POST /patients/{id}/allergies/`, `PATCH /allergies/{id}/`. Feeds 3.2.

**Frontend:** Allergies card on Patient 360 with a prominent banner for severe/anaphylaxis; manage modal.

**Acceptance:** allergies are structured + drive interaction checks; severe allergies are visually loud.

---

## 3.5 / 3.6 / 3.7 — Coded pickers: ICD-10, CPT, LOINC  ·  P1

**Why:** Manual code entry is a known gap (`CLAUDE.md`). Coded data unlocks billing, analytics, interop.

**Backend (new `apps/terminology/` tenant or shared app)**
- Reference tables `ICD10Code`, `CPTCode`, `LOINCCode` (`code`, `description`, `category`, search index).
  Load via management commands from public datasets (`manage.py load_icd10 <file>`, etc.).
- Search endpoints: `GET /terminology/icd10/?q=`, `/cpt/?q=`, `/loinc/?q=` (typeahead, capped).
- For LOINC, attach default reference ranges (by age/sex where available) used by lab result flagging.

**Frontend:** a reusable `<CodePicker kind="icd10|cpt|loinc">` async-search component. Wire into:
diagnosis entry (ICD), invoice line items / superbill (CPT), lab test definition (LOINC).

**Acceptance:** diagnoses/procedures/lab tests are chosen from coded, searchable pickers.

---

## 3.8 — Note templates  ·  P1

**Backend:** `NoteTemplate(BaseModel)`: `name`, `specialty`, `body` (structured SOAP scaffold / JSON),
`owner_id` (nullable = shared), `is_active`. Endpoints under `/visits/templates/`.

**Frontend:** in `CreateVisitModal` / `VisitDetailPage`, a "Use template" dropdown pre-fills SOAP fields.

**Acceptance:** a doctor applies a specialty template and edits from a scaffold instead of blank fields.

---

## 3.9 — Order sets  ·  P1

**Backend:** `OrderSet(BaseModel)`: `name`, `specialty`, `items` (JSON: bundled lab tests, imaging
studies, prescription items). `OrderSetService.apply(order_set, patient, visit, created_by_id)` fans
out into the existing lab/radiology/prescription create services. Endpoints under `/order-sets/`.

**Frontend:** "Apply order set" on the visit page → creates the bundled orders in one click.

**Acceptance:** applying "URI workup" creates the predefined labs + imaging + Rx for the patient/visit.

---

## 3.10 — Vitals trends & pediatric growth charts  ·  P1

**Backend:** `GET /patients/{id}/vitals-series/?metric=weight_kg&...` returning dense time series from
existing `Vitals`. Include patient `date_of_birth`/`gender` for percentile lookup.

**Frontend:** recharts line charts per metric on Patient 360 / Visit detail; for pediatric patients
overlay WHO/CDC percentile curves (ship the percentile tables as static JSON).

**Acceptance:** repeated vitals render as trends; child patients show growth percentiles.

---

## 3.11 — Care plans & care-gap reminders  ·  P2

**Backend:** `CarePlan(BaseModel)` + `CarePlanItem` (goal, due/interval, status); a Celery beat job
computes overdue items (e.g. annual screenings, chronic follow-ups) and emits notifications + a
care-gaps queue. Endpoints under `/care-plans/`.

**Frontend:** care-plan section on the patient chart + a clinic-wide "care gaps" worklist page.

**Acceptance:** overdue care items generate reminders and appear on a worklist.

---

## 3.12 — Referrals loop closure  ·  P1 (you already have an `apps/referrals/` app)

**Backend:** ensure `Referral` has a status FSM (`requested→accepted→scheduled→completed→declined`)
and a result/return-note field; `ReferralService.transition_status` + notify the referring provider on
completion. Endpoints/actions to advance status and attach the consult result.

**Frontend:** a Referrals page + detail with the status timeline (reuse 1.2) and the returned result;
notify + deep-link the referring doctor when the loop closes.

**Acceptance:** a referral can be tracked end-to-end and the referring doctor sees the returned result.
