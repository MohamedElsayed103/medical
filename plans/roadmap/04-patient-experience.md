# Plan 04 — Patient Experience  (Tier P1)

The patient-facing surface competitors monetize heavily and your platform doesn't have yet. Biggest
untapped growth lever. Depends on Plan 02 (reminders/notifications) and the availability engine
(already aligned) for scheduling.

Track status in [`PROGRESS.md`](./PROGRESS.md).

---

## 4.1 — Patient portal auth scope  ·  P1 (foundation for the rest)

**Why:** Patients need to log in without being staff. Must be strictly scoped to *their own* records.

**Backend (`apps/accounts/` + `apps/patients/`)**
- Introduce a `patient` principal: either a `User` with a `is_patient` flag linked to a `Patient`
  (via `patient_user_id` UUID on `Patient`, honoring the no-cross-schema-FK rule), or a dedicated
  portal auth. Issue JWTs with a `scope=patient` claim.
- A `PatientScopedPermission` that restricts every portal endpoint to `request.user`'s linked patient.
- Portal endpoints live under `/api/v1/portal/...` and ONLY ever return the caller's data.
- Invitation flow: staff invites a patient (email) → patient sets a password → linked to their record.

**Frontend:** a separate portal entry (route group `/portal/*` or a distinct subdomain/app) with its
own minimal layout; reuse the design system.

**Acceptance:** a patient logs in and can read ONLY their own data; staff RBAC is unaffected.

---

## 4.2 — Portal: records, results, appointments, statements  ·  P1

**Backend:** read-only portal endpoints: `/portal/me/`, `/portal/visits/`, `/portal/results/`
(labs + radiology reports, only finalized/released), `/portal/appointments/`, `/portal/invoices/`.
Add a "released to patient" gate on results so unreviewed/critical results aren't auto-shown.

**Frontend:** portal pages: summary, upcoming appointments, results (with the plain-language summary
from Plan 06 when available), statements/balances.

**Acceptance:** a patient sees their visits, released results, appointments, and balances.

---

## 4.3 — Online self-scheduling  ·  P1 (uses the now-aligned availability engine)

**Backend:** `/portal/book/` flow reusing `AppointmentService.get_available_slots` (already honors
windows + time-off) and `book()` (already validates). Add booking rules: which specialties/visit types
patients may self-book, min lead time, max horizon. New appts default to `SCHEDULED` and notify staff.

**Frontend:** portal scheduling wizard: pick specialty → provider → date → slot (the same slot grid as
`BookAppointmentModal`, reused as a shared component). Confirmation + reminder opt-in.

**Acceptance:** a patient books only into real available slots; double-booking is impossible; staff is notified.

---

## 4.4 — Appointment reminders  ·  P1 (depends on Plan 02 SMS/push)

**Backend:** Celery beat job scans upcoming appointments and sends reminders at configurable lead
times (e.g. 24h + 2h) via the patient's preferred channels; idempotent (don't double-send); respects
preferences (2.4). Record reminder sends on the appointment.

**Frontend:** clinic setting for reminder lead times + channels; per-appointment "reminders sent" indicator.

**Acceptance:** upcoming appointments trigger reminders on schedule; no duplicates.

---

## 4.5 — Telehealth video visits  ·  P1

**Backend:** `Appointment.type` already supports `telehealth`. On booking a telehealth appt, create a
video room (Twilio Video / Daily / Zoom SDK) and store `room_url`/`room_sid`; mint short-lived access
tokens via `GET /appointments/{id}/video-token/` for both provider and patient (scoped).

**Frontend:** a "Join visit" button (staff appointment detail + patient portal) opening the video room;
a virtual waiting room state until the provider admits the patient.

**Acceptance:** provider and patient join a working video room from their respective apps at visit time.

---

## 4.6 — Digital intake forms + e-signature consent  ·  P1

**Backend:** `IntakeForm` (template, JSON schema of questions) + `IntakeSubmission` (patient, answers,
signed_at, signature blob/hash, linked appointment/visit). Endpoints under `/portal/intake/` and staff
review under `/intake/`. Consent docs stored via Plan 02 documents.

**Frontend:** portal renders the form pre-visit; e-signature pad; staff sees submissions on the patient
chart / pre-visit.

**Acceptance:** a patient completes intake + signs consent before the visit; staff reviews it on the chart.

---

## 4.7 — Online bill pay  ·  P1 (revenue, and you already track balances)

**Backend:** integrate Stripe (or Adyen). `POST /portal/invoices/{id}/checkout/` → PaymentIntent /
Checkout Session for the balance; Stripe **webhook** → `BillingService.record_payment(...)` (reuse the
existing payment recording so the invoice/ledger updates exactly like a manual payment). Idempotent on
event id. Keep secrets in env.

**Frontend:** "Pay now" on portal statements → Stripe Checkout → success returns to a receipt
(Plan 01 PDF).

**Acceptance:** a patient pays an invoice online; the webhook posts the payment and the balance updates;
no double-posting on webhook retries.
