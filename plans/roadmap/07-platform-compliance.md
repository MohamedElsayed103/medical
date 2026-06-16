# Plan 07 — Platform, Trust & Compliance  (Tier P2)

What unlocks enterprise/hospital deals and keeps the platform operable at scale. Mostly backend +
ops, with a few admin UIs.

Track status in [`PROGRESS.md`](./PROGRESS.md).

---

## 7.1 — Compliance posture  ·  P2

**Deliverables (docs + config, not just code)**
- HIPAA (US) / GDPR (EU) readiness write-up: data flows, PHI inventory, encryption at rest/in transit
  (PII already Fernet-encrypted via `common/utils.py`), retention, sub-processors (Anthropic, Twilio,
  Stripe, clearinghouse, storage), BAA/DPA list, data-residency options per tenant.
- Configurable data retention + a patient data export/erasure (GDPR DSAR) job.
- A `SECURITY.md` / `COMPLIANCE.md` at repo root; surface a public trust page later.

**Acceptance:** a sales/security questionnaire can be answered from documented posture; DSAR export works.

---

## 7.2 — Audit-log UI + break-the-glass access logging  ·  P2

**Why:** You have an immutable `AuditLog` (`apps/audit/`); compliance officers need to *use* it.

**Backend:** searchable/filterable audit API (`/audit-logs/?actor=&resource_type=&resource_id=&from=&to=`)
with pagination + CSV export (`/audit-logs/export/`). Add **access logging**: record every *read* of a
patient chart (who viewed whom, when) — "break-the-glass" visibility, not just writes.

**Frontend:** enrich `pages/audit/AuditLogPage.tsx` with filters, detail drill-down, export; a
"who accessed this patient" view on the patient chart for admins.

**Acceptance:** an admin can search/export the audit trail and see who viewed a given patient.

---

## 7.3 — Observability: Sentry, Prometheus SLOs, tracing  ·  P2

**Backend:** Sentry + `django-prometheus` are installed — finish wiring: Sentry DSN per env, release
tagging, performance traces across the service layer; Prometheus metrics for request latency, Celery
queue depth, external-API latency (drug DB, clearinghouse, AI). Define SLOs (API p95, task success
rate) + alerting.

**Acceptance:** dashboards + alerts exist for API latency, error rate, Celery health, and external deps.

---

## 7.4 — Background-job hardening  ·  P2

**Backend:** make every async task (notifications, reminders, AI, claims, ERA, scans) idempotent with
bounded retries + dead-letter handling + visibility. Use a single Celery task conventions module;
ensure tenant schema context is set inside tasks (django-tenants). Add a small ops view/queue metrics.

**Acceptance:** tasks retry safely, never double-apply effects, and failures are observable + replayable.

---

## 7.5 — FHIR R4 read API  ·  P2 (interoperability — the enterprise key)

**Backend (new `apps/fhir/`)**
- Map core resources to FHIR R4: `Patient`, `Practitioner`, `Encounter` (Visit), `Observation`
  (Vitals + lab results), `MedicationRequest` (Prescription), `DiagnosticReport` (lab/radiology),
  `Condition` (Problem), `AllergyIntolerance`, `Coverage` (insurance), `Invoice`.
- Read + search endpoints under `/fhir/R4/<Resource>` with standard search params; OAuth2/SMART-on-FHIR
  scopes layered on the existing auth. Write support is a later phase.

**Acceptance:** a FHIR client can read a patient and their encounters/observations/medications in valid R4.

---

## 7.6 — HL7 v2 inbound feeds  ·  P2

**Backend:** an ingestion endpoint/worker for HL7 v2 messages (MLLP or file/HTTP): **ORU** (lab
results) → create/update lab results; **ADT** (admit/discharge/transfer) → patient demographics sync.
Parse with `hl7apy`; map to tenant; idempotent on message control id; quarantine/log unmappable messages.

**Acceptance:** an inbound ORU result message creates the corresponding lab result in the right tenant.

---

## Cross-cutting engineering quality (also see Plan 01.8–1.11)

- Contract tests + OpenAPI-generated client (1.10) prevent FE/BE drift.
- API smoke tests (1.9) per viewset in CI.
- Shared UI primitives (1.2) reduce duplication and bugs.
- Normalized error surfacing (1.8) so business-rule codes reach users.
