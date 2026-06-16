# Plan 05 — Revenue Cycle Management (RCM)  (Tier P2)

Where clinics decide to buy. Builds on the existing `apps/billing/` (Invoice/Payment, auto-billing via
`BillingService.create_from_source`) and `apps/insurance/` (Provider/Policy/Claim). US-centric X12
transactions are referenced; adapt to local payers as needed.

Track status in [`PROGRESS.md`](./PROGRESS.md).

---

## 5.1 — Real-time insurance eligibility (270/271)  ·  P2

**Backend (`apps/insurance/`)**
- `EligibilityService.check(policy, *, service_type, as_of)` → calls a clearinghouse (Change
  Healthcare / Availity / Stedi) via an adapter; persist an `EligibilityCheck` record (coverage
  active?, copay, deductible remaining, response blob). Cache for the day.
- Endpoint `POST /insurance/policies/{id}/eligibility/`. Async (Celery) with a synchronous "quick
  check" fallback. Secrets in env.

**Frontend:** "Check eligibility" on the insurance policy detail + a coverage summary banner on the
patient chart / before billing.

**Acceptance:** staff runs eligibility and sees active/copay/deductible before the visit.

---

## 5.2 — Claim model + lifecycle + scrubbing  ·  P2

**Backend**
- Extend `Claim`: status FSM (`draft→scrubbed→submitted→accepted→paid→denied→appealed`), linked
  invoice, service lines (CPT from Plan 03.6 + ICD pointers from 3.5 + charge), payer, subscriber.
- `ClaimService.build_from_invoice(invoice)` mapping invoice line items → claim service lines.
- `ClaimService.scrub(claim)` — local validation (required fields, code validity, payer rules) → list
  of issues before submission.

**Frontend:** Claims worklist + claim detail (status timeline, service lines, scrub issues). Build a
claim from an invoice in one click.

**Acceptance:** an invoice generates a scrubbable claim; scrub errors are shown before submission.

---

## 5.3 — Claims submission (837)  ·  P2

**Backend:** `ClaimService.submit(claim)` → render X12 837P (use a library or a clearinghouse API) and
send via the clearinghouse adapter; store the control number; transition to `submitted`. Poll/receive
277 status updates (Celery) → update claim status.

**Acceptance:** a scrubbed claim submits and its acknowledgment/status updates flow back automatically.

---

## 5.4 — ERA/EOB ingestion (835) + auto-posting  ·  P2

**Backend:** ingest 835 remittances (clearinghouse webhook or SFTP poll) → parse payments/adjustments
per claim line → `BillingService.record_payment(...)` against the invoice + write-offs/adjustments;
flag denials with reason codes. Reuse existing payment posting so ledgers stay consistent.

**Frontend:** remittance/EOB view; denial worklist with reason codes feeding appeals.

**Acceptance:** an 835 auto-posts insurer payments and adjustments and surfaces denials for follow-up.

---

## 5.5 — Superbill generation + coding assist  ·  P2

**Backend:** `GET /visits/{id}/superbill/` assembling diagnoses (ICD) + procedures (CPT) + charges
from the encounter; optional AI coding suggestions (Plan 06.3). PDF via Plan 01.6.

**Frontend:** "Generate superbill" on the visit; review/edit codes → create invoice/claim.

**Acceptance:** a completed visit produces an editable, coded superbill that flows to billing.

---

## 5.6 — Patient payment plans + statements/dunning  ·  P2

**Backend:** `PaymentPlan(invoice/patient, total, installment, cadence, status)` + a Celery beat job
that charges due installments (via Plan 04.7 Stripe) and sends statements/reminders for overdue A/R
(escalating dunning). Idempotent.

**Frontend:** set up a plan on an invoice; patient sees the plan + auto-pay in the portal.

**Acceptance:** an invoice can be split into a plan; installments auto-charge; overdue balances dun automatically.

---

## 5.7 — RCM analytics dashboard  ·  P2

**Backend:** aggregation endpoints: A/R aging buckets, denial rate, days-in-A/R, clean-claim rate,
collection rate, payer mix, charges vs collections. Build on the existing billing summary + payments
time series (extend `BillingService`).

**Frontend:** an RCM dashboard page (recharts) with the KPIs above and drill-downs to worklists.

**Acceptance:** a clinic owner sees A/R aging, denial rate, and collections trends with drill-down.
