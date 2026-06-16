# Implementation Progress Tracker

**This is the single source of truth for what is done and what is not.** Update it as you work.
Do not track status inside the individual plan files.

**Legend:** ✅ done · 🟡 in progress / partial · ⬜ not started · ⛔ blocked

Last updated: 2026-06-16 (Plan 01 + Plan 02 batches)

---

## Already shipped (baseline before this roadmap)

These landed in the bug/feature batch and the 2026-06-15 fixes — listed so we don't re-plan them.

- ✅ Multi-tenant + RBAC, core modules (patients, appointments, visits, prescriptions, labs, pharmacy, billing, insurance, radiology backend)
- ✅ Doctor availability model + CRUD UI; `doctor_id` writable serializer fix
- ✅ Appointment "filter by doctor" fixed; `doctor_name` in serializers; doctor select in list view
- ✅ Clickable rows + detail pages: invoices, lab orders, prescriptions
- ✅ Lab order detail: nested results display + per-test "record result"
- ✅ Medication model with image + clinical fields; Medications list + detail page (upload/edit); media storage in dev
- ✅ Radiology: create-order modal (modality/body-part/studies + internal/external orderer), detail page (status FSM + report recording); `is_deleted` filter bug fixed
- ✅ **Appointment ↔ availability alignment**: bookable slots == availability windows − time-off − existing appts − past; `book()` enforces the identical rule

---

## P0 — Plan 01: Foundation & Quick Wins   (mostly complete — 9/11)

- 🟡 1.1 Clickable rows + detail pages — DONE: appointments (new `AppointmentDetailPage` + clickable
  list & calendar rows), pharmacy inventory → medication detail links, visits already link.
  REMAINING: dedicated Insurance policy/claim detail pages.
- ✅ 1.2 Shared components — `StatusChip` (+ `statusColor`), `StatusTimeline`, `DetailHeader`
  (`components/ui/`). New detail pages use them.
- ✅ 1.3 Patient 360 — backend `PatientService.timeline()`/`summary()` + `/patients/{id}/timeline/`
  & `/summary/`; enriched Overview tab (KPI cards, active meds, allergies, vertical timeline with deep links).
- ✅ 1.4 Provider profile — `/providers/:id` (`ProviderDetailPage`): profile, weekly availability,
  time-off, upcoming schedule. Doctor names across the app link to it.
- 🟡 1.5 Visit enrichment — DONE: "Orders from this Visit" (linked prescriptions/labs/radiology)
  via `/visits/{id}/related/`. Cross-visit vitals **trend** charts deferred to 3.10 (a single visit
  has one reading; trends belong on the patient chart).
- ⬜ 1.6 Print/PDF for invoices, prescriptions, lab & radiology reports — NOT STARTED (needs
  weasyprint/reportlab; deferred).
- ✅ 1.7 Global search — backend `apps/search/` (`/api/v1/search/?q=`) across patients/invoices/
  lab/radiology; grouped command-palette results in `TopBar`.
- ✅ 1.8 Error normalization — `getApiErrorMessage()` + axios interceptor populates
  `error.response.data.detail` from `{error:{code,message}}` / DRF field errors so existing toasts show real messages.
- 🟡 1.9 API smoke tests — DONE: runnable `scripts/smoke_test.py` (21 checks: lists, doctor filter,
  available-slots, timeline/summary, search, visit-related, detail retrieves, radiology create→transition);
  all pass. REMAINING: port to a pytest-django harness for CI (pytest-django not yet installed).
- ⬜ 1.10 OpenAPI-generated TypeScript client — NOT STARTED (deferred; needs codegen tooling).
- ✅ 1.11 Seed/demo data — idempotent `manage.py seed_demo --schema <name>` (formulary, Mon–Fri
  availability for unscheduled doctors only, one demo visit + linked Rx + lab). One-command bootstrap script still pending.

## P0→P1 — Plan 02: Notifications & File Pipeline   (5/8 done or substantial)

> Note: most of the notification *backend* was already built (preferences model,
> channel adapters, WebSocket consumer + `group_send`, ASGI/routing). This pass
> finished the **frontend** + the **file pipeline** + provider wiring.

- 🟡 2.1 SMS (Twilio) — `SMSChannel` now sends via Twilio when `TWILIO_*` settings + the `twilio`
  package are present; logs + no-ops cleanly otherwise (verified no-op path). SMS toggle already in
  the preferences UI. REMAINING: real send needs Twilio credentials.
- 🟡 2.2 Push — `PushDevice` model + `register-device`/`unregister-device` endpoints; `PushChannel`
  resolves a user's active device tokens and sends via FCM when `FCM_SERVER_KEY` is set (guarded,
  no-op otherwise). Frontend `notificationsService.registerDevice/unregisterDevice` added. REMAINING:
  browser service-worker + VAPID token acquisition (web-push) to actually obtain a token.
- ✅ 2.3 Real-time bell — frontend `useNotificationSocket()` hook connects to `/ws/notifications/?token=`,
  live-updates the bell + toasts, reconnects with backoff, and **falls back to polling** if WS is down.
  Added `daphne` (ASGI runserver), dev `InMemoryChannelLayer`, and a `/ws` Vite proxy. **Restart the
  backend** to serve live WS (the consumer + `group_send` were already implemented).
- ✅ 2.4 Notification preferences UI — per-channel toggles (existing) + **editable quiet hours**
  (start/end time + clear) wired to `/notifications/preferences/`.
- ⬜ 2.5 Presigned uploads to MinIO/S3 — NOT STARTED. Dev uses direct multipart (used by 2.6);
  presign endpoint for prod still to do.
- ✅ 2.6 Documents — `Document` model (patient/customer, category, file, size, type) + migration;
  `DocumentService.create_from_upload` (type + 10 MB validation); `/patients/{id}/documents/`
  (GET/POST multipart) + `/documents/{id}/` (soft-delete); **Documents tab** on the patient chart
  (category-tagged upload, list, download, delete). Verified upload→list→delete.
- 🟡 2.7 Validation/scanning — content-type allowlist + 10 MB size limit enforced in
  `DocumentService`. REMAINING: ClamAV virus-scan hook.
- ⬜ 2.8 DICOM/image handling for radiology — NOT STARTED.

## P1 — Plan 03: Clinical Depth

- ⬜ 3.1 Drug database integration (RxNorm/OpenFDA) + medication autocomplete
- ⬜ 3.2 Drug–drug & drug–allergy interaction checking at prescribe time
- ⬜ 3.3 Problem list (structured, coded) per patient
- ⬜ 3.4 Allergy list (structured, severity, reaction) per patient
- ⬜ 3.5 ICD-10 coded picker (diagnoses)
- ⬜ 3.6 CPT coded picker (procedures/billing)
- ⬜ 3.7 LOINC coded picker (lab tests) + reference ranges by age/sex
- ⬜ 3.8 Note templates (specialty SOAP templates)
- ⬜ 3.9 Order sets (favorite Rx/lab/imaging bundles)
- ⬜ 3.10 Vitals trends + pediatric growth percentile charts
- ⬜ 3.11 Care plans & care-gap reminders
- ⬜ 3.12 Referrals loop closure (status + result return)

## P1 — Plan 04: Patient Experience

- ⬜ 4.1 Patient portal auth scope (separate login + tenant-scoped patient user)
- ⬜ 4.2 Portal: view records, results, appointments, statements
- ⬜ 4.3 Online self-scheduling (book into availability slots)
- ⬜ 4.4 Appointment reminders (email/SMS/push, configurable lead time)
- ⬜ 4.5 Telehealth video visits (room + virtual waiting room)
- ⬜ 4.6 Digital intake forms + e-signature consent
- ⬜ 4.7 Online bill pay (Stripe checkout against invoices)

## P2 — Plan 05: Revenue Cycle Management

- ⬜ 5.1 Real-time insurance eligibility (270/271)
- ⬜ 5.2 Claim model + lifecycle + scrubbing
- ⬜ 5.3 Claims submission (837) via clearinghouse
- ⬜ 5.4 ERA/EOB ingestion (835) + auto-posting
- ⬜ 5.5 Superbill generation + coding assist linkage
- ⬜ 5.6 Patient payment plans + automated statements/dunning
- ⬜ 5.7 RCM analytics dashboard (A/R aging, denial rate, days-in-A/R, payer mix)

## P1→P2 — Plan 06: AI & Intelligence

- ⬜ 6.1 Ambient scribe: audio → transcript → drafted SOAP note (human-in-loop)
- ⬜ 6.2 Lab/radiology result summarization & plain-language explanations
- ⬜ 6.3 Coding suggestions (ICD/CPT) from the note
- ⬜ 6.4 Smart inbox / triage (prioritize results, refills, messages)
- ⬜ 6.5 No-show prediction scoring
- ⬜ 6.6 AI safety scaffolding (audit, confidence, always-confirm, PII guardrails)

## P2 — Plan 07: Platform, Trust & Compliance

- ⬜ 7.1 Compliance posture docs (HIPAA/GDPR, BAA/DPA, data residency)
- ⬜ 7.2 Audit-log UI (searchable, exportable) + break-the-glass access logging
- ⬜ 7.3 Observability: Sentry dashboards, Prometheus SLOs, request tracing
- ⬜ 7.4 Background-job hardening (retries, dead-letter, idempotency) for Celery
- ⬜ 7.5 FHIR R4 read API (Patient, Encounter, Observation, MedicationRequest…)
- ⬜ 7.6 HL7 v2 inbound feeds (lab results, ADT)

---

## Change log

- 2026-06-15 — Roadmap created; baseline section reflects shipped bug-fixes/features.
- 2026-06-16 — Plan 01 implemented (9/11): 1.2, 1.3, 1.4, 1.7, 1.8, 1.11 done; 1.1, 1.5, 1.9 partial
  (notes above); 1.6 (PDF) and 1.10 (OpenAPI client) deferred. New backend: `apps/search/`,
  patient timeline/summary, visit `related`, `seed_demo`. New frontend: `StatusChip`,
  `StatusTimeline`, `DetailHeader`, `AppointmentDetailPage`, `ProviderDetailPage`, enriched Patient-360
  Overview + Visit linked-orders, global search in TopBar, error normalization. Frontend builds clean;
  `scripts/smoke_test.py` → 21/21 pass.
- 2026-06-16 — Plan 02 batch: 2.3, 2.4, 2.6 done; 2.1, 2.2, 2.7 partial; 2.5, 2.8 deferred. New
  backend: `Document` model + endpoints + `DocumentService`, `PushDevice` + register/unregister,
  guarded Twilio SMS + FCM push, `daphne` ASGI runserver + dev in-memory channel layer. New frontend:
  patient **Documents tab** (upload/list/download/delete), editable **quiet hours**, real-time
  **WebSocket bell** (`useNotificationSocket`) with polling fallback, `/ws` + `/media` Vite proxies.
  Migrations: `patients.0003_document`, `notifications.0002_pushdevice`. `scripts/smoke_test.py` → 25/25 pass.
  ACTION: restart the backend (now ASGI/daphne) to enable live WebSocket delivery.
