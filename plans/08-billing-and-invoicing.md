# 08 — Billing & Invoicing Review + Auto-Generation

Covers **#17** (review the invoice logic, clarify it, and add automation). Depends on `05`
(`BillingService.create_from_source`, Invoice source/customer fields) and integrates the billing
triggers declared in `03` (visit), `06` (pharmacy order), `07` (lab & radiology).

---

## Current state (verified) and the problems

`Invoice` (tenant): `invoice_number`, `patient` (non-null), `status`
(DRAFT→ISSUED→PARTIALLY_PAID→PAID→OVERDUE→CANCELLED), `subtotal/tax_amount/discount_amount/total/
amount_paid`, `balance_due` property. `InvoiceItem` (item_type, qty, unit_price, total_price
auto-computed in `save`). `Payment` (amount, method, received_by_id).

`BillingService`:
- `create_invoice(patient, items, tax_rate, discount_amount, due_date, notes)` — computes
  subtotal/tax/total atomically. **Tax handling is ambiguous:** "if tax_rate > 1 divide by 100"
  guesses percent vs fraction. This is fragile.
- `finalize_invoice` (DRAFT→ISSUED), `record_payment` (rejects overpay, flips status to
  PARTIALLY_PAID/PAID), `cancel_invoice`, `void_invoice`.

### Why #17 says "logic is not clear" — concrete issues
1. **No source linking / no automation.** Invoices are 100% manual; nothing connects an invoice to
   the visit/lab/pharmacy event that justifies it. Staff must re-enter everything → errors, omissions.
2. **Ambiguous tax input** (`>1 ⇒ percent` heuristic) — a 1% tax and a 100%-as-fraction collide.
3. **`OVERDUE` is never set** — it's a status value with no transition logic (no job marks overdue
   invoices past `due_date`).
4. **No customer billing** — `patient` is required, so walk-in (Customer) sales can't be billed.
5. **Status semantics**: DRAFT vs ISSUED vs PARTIALLY_PAID is fine, but there's no single documented
   state machine, and payment can be recorded on ISSUED but the relationship to fulfillment (pharmacy)
   isn't defined.

---

## Target invoice model & state machine (documented)

```
            create_from_source / create_invoice
                        │
                      DRAFT ──cancel──► CANCELLED
                        │ finalize
                        ▼
                      ISSUED ──cancel(if no payments)──► CANCELLED
                    │      │
        record_payment  due_date passed & balance>0 (job)
            │      │              │
            ▼      ▼              ▼
   PARTIALLY_PAID  PAID        OVERDUE ──record_payment──► PARTIALLY_PAID/PAID
            │
       record_payment ──► PAID
```
Rules:
- Payments only allowed on `ISSUED`, `PARTIALLY_PAID`, `OVERDUE` (not DRAFT/CANCELLED/PAID).
- `PAID` when `amount_paid >= total`; `PARTIALLY_PAID` when `0 < amount_paid < total`.
- `OVERDUE` is `ISSUED`/`PARTIALLY_PAID` with `due_date < today` and `balance_due > 0`; set by a
  scheduled job (below), reverts via payment.

---

## Changes

### 1. Model — `apps/billing/models.py`
(Most added in file 05 Part C; consolidate here.)
- `patient` → nullable; add nullable `customer` FK (file 05).
- Add `source_type` (choices `visit|pharmacy_order|lab_order|radiology_order|manual`, default
  `manual`) and `source_id` (UUIDField, null=True, db_index=True).
- Add a `payer_name` read property: patient.full_name or customer.full_name.
- Keep `balance_due` property.
Migration: `makemigrations billing` → `migrate_schemas`.

### 2. Fix tax handling (unambiguous)
Change `create_invoice` / `create_from_source` to take an explicit **`tax_rate` as a decimal fraction
in [0,1]** (e.g. `0.10` = 10%). Remove the `>1 ⇒ /100` heuristic. Validate `0 <= tax_rate <= 1`,
raise `ServiceError(code="INVALID_TAX_RATE")` otherwise. Update the frontend invoice form to send a
fraction (or send a percent and divide by 100 in one clearly-named place on the client). Document the
contract in the serializer help_text.

### 3. `create_from_source` (the automation core)
Implemented per file 05 Part C. Confirm:
- Idempotent per `(source_type, source_id)` (skip if a non-CANCELLED invoice already exists → return it).
- Accepts `patient=None`/`customer=None` (exactly one) and validates with `validate_orderer`.
- Produces a **DRAFT** invoice; never auto-finalizes or auto-pays (billing staff stays in control).

### 4. Wire the triggers (call sites live in their feature files; verify here)
- **Visit (file 03/04):** when a visit is **signed** (`VisitService.sign_visit`), call
  `create_from_source(source_type="visit", source_id=visit.id, patient=visit.patient,
  items=[{item_type:"consultation", description:f"Consultation — Dr …", quantity:1,
  unit_price: visit.doctor.consultation_fee}])`. Signing (not creation) is the bill-worthy event.
  Wrap in try/except + log; a billing failure must not block signing.
- **Pharmacy order (file 06):** `checkout`/`complete-sale` calls `create_from_source(
  source_type="pharmacy_order", …)`.
- **Lab order (file 07):** on COMPLETED.
- **Radiology order (file 07):** on COMPLETED.
Each feature stores the returned invoice on its `invoice` FK so the UI can deep-link order → invoice.

### 5. OVERDUE job (Celery beat — infra already present)
- Add a periodic task `apps/billing/tasks.py::mark_overdue_invoices` that, per tenant schema, sets
  `status=OVERDUE` for invoices where `status in (ISSUED, PARTIALLY_PAID)` and `due_date < today`
  and `balance_due > 0`. Schedule daily via `django_celery_beat` (already installed). Must iterate
  tenant schemas (use `tenant_context`/`schema_context` over `Organization` rows). If running Celery
  isn't desired in dev, also expose a management command `mark_overdue_invoices` doing the same, so it
  can be run manually/cron.

### 6. Payment ↔ fulfillment link (pharmacy)
When `record_payment` brings a pharmacy-order invoice to `PAID`, optionally flip the linked
`PharmacyOrder.status` to `PAID` (so `fulfill` is enabled). Implement as: after payment, if
`invoice.source_type == "pharmacy_order"` and now PAID, look up the order via `source_id` and update
its status. Keep this in `BillingService.record_payment` behind a small dispatch, or emit a signal —
prefer a direct, explicit call with a lazy import to avoid cycles. (For simple counter sales the
combined `complete-sale` endpoint already handles pay+fulfill together.)

### 7. Frontend
- **Invoice detail page** (built in file 01) shows `source_type` + a link to the source
  (visit/order), `payer_name` (patient or customer), the full state, and the OVERDUE badge.
- **Billing list**: add status filter incl. OVERDUE; show payer (patient/customer).
- **Auto-draft visibility:** DRAFT invoices generated by automation appear in the billing list for
  staff to review → finalize → collect. Make the "DRAFT" filter prominent so staff see the queue of
  auto-generated invoices awaiting issuance.
- Invoice create form: support selecting a patient **or** entering a walk-in customer (reuse the
  shared OrdererPicker from files 06/07); send `tax_rate` as a fraction (or convert percent→fraction
  in one labeled helper).

---

## Acceptance
- Signing a visit, completing a lab/radiology order, and completing a pharmacy sale each produce
  exactly one DRAFT invoice linked to its source (idempotent — repeating the event doesn't duplicate).
- Walk-in customers can be billed (invoice with `customer`, no patient).
- Tax is unambiguous (fraction); a 10% tax yields `tax_amount = subtotal * 0.10`.
- Invoices past `due_date` with a balance flip to OVERDUE via the job/command and revert on payment.
- Recording full payment on a pharmacy-order invoice enables fulfillment.
- Billing staff can see and finalize the queue of auto-generated DRAFT invoices.

---

## Note on scope / what NOT to do
- Do **not** auto-finalize or auto-charge — keep a human (billing staff) in the loop (matches the
  chosen "auto-draft" decision, not "auto-charge").
- Do **not** add a payment gateway here (it's a documented SRS limitation / future work). Payments
  remain manually recorded with a method + reference.
