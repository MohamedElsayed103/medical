# 01 — Quick Fixes

Covers items **#1, #2, #3, #9, #13**. These are independent, low-risk, and good to ship first.
No new models. Mostly frontend + small serializer additions.

---

## #1 — Patient detail: visits / lab results / invoices navigation

### Root cause (verified)
`src/pages/patients/PatientDetailPage.tsx` renders tab rows as links:
- Visits → `/visits/${visit.id}` ✅ route exists (`/visits/:id` → `VisitDetailPage`)
- Lab Results → `/lab-orders/${order.id}` ❌ **route does not exist** (only `/lab-orders` list)
- Invoices → `/billing/${inv.id}` ❌ **route does not exist** (only `/billing` list)

So lab/invoice rows navigate to a blank/unmatched route. The fix is to **build the two missing
detail pages and register their routes**.

### Backend — confirm detail endpoints exist
Both already exist (no change needed):
- `GET /api/v1/lab-orders/{id}/` → `labOrdersService.getById(id)`
- `GET /api/v1/invoices/{id}/` → `billingService.getById(id)`, plus `getPayments(id)`.

If `labOrdersService.getById` / `billingService.getById` are missing from `src/services/api.ts`,
add them mirroring the existing `getAll` patterns.

### Frontend — create two detail pages

**File:** `src/pages/lab-orders/LabOrderDetailPage.tsx` (new)
- Route param `id`; `useQuery(['lab-order', id], () => labOrdersService.getById(id))`.
- Render: order number, status badge, priority, ordered/completed dates (via `safeFormat`),
  ordering doctor name, patient link, clinical notes.
- List `tests[]` with each test's result (value, unit, reference range, flag badge colored by
  `normal/low/high/critical`). Use the existing flag color convention from `LabOrdersPage`.
- Lab-tech actions (gated — see file 02): `collect`, `inProgress`, `complete`, and per-test
  `recordResult`. Reuse mutations already defined for `LabOrdersPage` if present.

**File:** `src/pages/billing/InvoiceDetailPage.tsx` (new)
- `useQuery(['invoice', id], () => billingService.getById(id))` + `getPayments(id)`.
- Render: invoice number, status badge, patient, issued/due dates, line-item table
  (`items[]`: description, qty, unit_price, total_price), totals block (subtotal, tax, discount,
  total, amount_paid, **balance_due**), payments list.
- Billing-staff actions (gated): `finalize`, `pay` (payment modal), `cancel`/`void`.

### Frontend — register routes
**File:** `src/App.tsx` — add inside the protected `DashboardLayout` block, next to the existing list routes:
```tsx
<Route path="/lab-orders/:id" element={<LabOrderDetailPage />} />
<Route path="/billing/:id" element={<InvoiceDetailPage />} />
```
Add the matching `lazy(() => import(...))` declarations alongside the other lazy page imports.

### Acceptance
- From a patient with lab orders and invoices, clicking a Lab Results row and an Invoices row each
  opens a populated detail page (no blank screen, no console error).
- Visits row still works (already did).

---

## #2 — Dashboard "Revenue Overview" fix

### Root cause (verified)
`src/pages/dashboard/DashboardPage.tsx` builds the chart from only the **7 most recent invoices**
(`page_size: 7`, ordered `-created_at`), grouped by `created_at` day, summing `inv.total`
regardless of payment status. Problems:
1. 7 rows ≠ a time series → often collapses to **one bar**, looks broken.
2. Uses billed `total`, not actual **revenue collected** (`amount_paid`), so "revenue" is wrong.
3. Same-day invoices all merge into a single point.

### Fix — add a proper revenue time-series endpoint, consume it

**Backend** — `apps/billing/`:
- Add `BillingService.revenue_timeseries(*, days: int = 30) -> list[dict]` in `services.py`:
  - Aggregate `Payment` rows (real cash in) by day for the last `days` days:
    group by `paid_at::date`, `Sum('amount')`.
    Use `django.db.models.functions.TruncDate`. Return a **dense** series (fill missing days with
    `0.0`) so the chart is continuous: `[{ "date": "2026-06-01", "revenue": 1234.0 }, ...]`.
  - Rationale: payments = recognized revenue; this is the metric a clinic owner expects.
- Add view + route: `GET /api/v1/invoices/revenue-timeseries/?days=30` on `InvoiceViewSet`
  (`@action(detail=False, methods=['get'])`), permission `HasPermission('billing:read')`
  (or `reports:read`). Returns the list above.

**Frontend** — `src/services/api.ts`:
- `billingService.getRevenueTimeseries = (days = 30) => api.get('/invoices/revenue-timeseries/', { params: { days } }).then(r => r.data)`

**Frontend** — `DashboardPage.tsx`:
- Replace the local `revenueChartData` IIFE (the `recentInvoices`-based aggregation) with
  `useQuery(['revenue-ts', 30], () => billingService.getRevenueTimeseries(30))`.
- Map to `{ name: safeFormat(d.date, 'MMM dd'), revenue: Number(d.revenue) }`.
- Keep the existing `<AreaChart>`; keep the "No revenue data yet" empty state when the series is all-zero.

### Acceptance
- Chart shows a continuous 30-day line/area even when invoices cluster on few days.
- The number reflects **payments received**, not draft/issued totals.
- Recording a new payment (via invoice pay) moves the latest day's value up after refetch.

---

## #3 — Remove "Other" gender option

Keep the backend enum value `Gender.OTHER` (existing patient rows may use it; removing the enum
value would break historical data and migrations). **Only remove it from the UI selector.**

**File:** `src/pages/patients/PatientFormModal.tsx` — delete this line from the gender `<select>`:
```tsx
<option value="other">Other</option>
```
Leave `male`/`female` and the empty "Select..." placeholder.

> If a frontend type union exists (e.g. `type Gender = 'male' | 'female' | 'other'` in
> `src/types/`), you may narrow it to `'male' | 'female'` for new input, but keep read paths tolerant
> of `'other'` so existing patients still render.

### Acceptance
- New/edit patient form shows only Male / Female. Existing "other" patients still display without error.

---

## #9 — Required-field corrections

**Method:** the backend model is the source of truth. A field is truly required only if the model has
**no** `null=True`/`blank=True` and no default. Align each frontend Zod schema + `*` label to the model.

### Verified backend reality (from models) vs current frontend

**Patient** (`apps/patients/models.py`): required at DB = `first_name`, `last_name`, `date_of_birth`,
`gender`, `phone`. Everything else (`email`, `national_id`, `blood_type`, `address`, emergency
contacts, insurance, `notes`) is `blank=True` → **optional**.
- `PatientFormModal.tsx` Zod already matches this. ✅ No change unless a `*` is shown on an optional
  field — audit the labels and remove stray `*` from optional fields.

**Appointment** (`apps/appointments/models.py`): required = `patient`, `doctor`, `scheduled_at`.
`duration_minutes` has default 30, `type` has default → **optional**. `reason` is `blank=True`.
- `BookAppointmentModal.tsx` Zod matches. ✅ Verify no `*` on duration/type/reason.

### The actual offenders to fix (audit these forms)
Go through each create/edit form and make the Zod schema + `*` labels match the model. Known
likely-wrong spots to check and correct:

| Form file | Field | Model truth | Action |
|-----------|-------|-------------|--------|
| `pages/visits/CreateVisitModal.tsx` | only `chief_complaint` is required on `Visit`; `hpi`, `examination_notes`, `assessment`, `plan`, `follow_up_date` are `blank=True` | optional | Ensure only `patient`, `doctor`, `visit_date`, `chief_complaint` are required; drop `*`/`.min(1)` from the SOAP narrative fields |
| `pages/prescriptions/PrescriptionsPage.tsx` (create form) | `PrescriptionItem` requires `dosage`, `frequency`, `duration`, `quantity`; `route` has default, `instructions`/`is_prn` optional | as listed | Make `instructions` optional; `route` defaults to `oral` |
| Lab order create | `LabOrder` requires `patient`, `doctor`; `priority` defaults; `clinical_notes` `blank=True`; each `LabTest` needs `test_name` only | as listed | `specimen_type`, `test_code`, `notes`, `clinical_notes` optional |
| Doctor profile create (`appointmentsService.createDoctor`) | `DoctorProfile` requires `user_id`, `specialization`; fee defaults 0; `license_number`,`qualification`,`bio` `blank=True` | as listed | Only `specialization` (+ user) required |

**Process for each form:**
1. Open the form, find its Zod schema.
2. For every field, cross-check the model field's `null/blank/default`.
3. If the model allows blank/has a default → make Zod `.optional()` (and `.or(z.literal(''))` for
   strings) and remove the `*` from the label.
4. If the model requires it but Zod doesn't → add `.min(1)` and a `*`.

### Acceptance
- Submitting each form with only the genuinely-required fields succeeds (no 400 from backend, no
  client-side block on optional fields).
- No `*` appears on a field the backend accepts as blank.

---

## #13 — "Out of stock" instead of "low stock" when quantity is 0

### Backend — `apps/pharmacy/models.py`
`PharmacyInventory` already has `is_low_stock` (`quantity_on_hand <= reorder_level`). Add a sibling:
```python
@property
def is_out_of_stock(self) -> bool:
    return self.quantity_on_hand == 0

@property
def stock_status(self) -> str:
    if self.quantity_on_hand == 0:
        return "out_of_stock"
    if self.quantity_on_hand <= self.reorder_level:
        return "low_stock"
    return "in_stock"
```

### Backend — serializer
In `apps/pharmacy/serializers.py`, expose `is_out_of_stock` and `stock_status` as read-only fields
on the inventory serializer (add to `fields` and as `serializers.ReadOnlyField()` /
`SerializerMethodField`). Keep `is_low_stock` for back-compat.

### Frontend — `src/pages/pharmacy/PharmacyPage.tsx`
Where the badge currently renders low/normal, switch on `stock_status` (or compute from quantity):
- `out_of_stock` → red badge "Out of stock"
- `low_stock` → amber badge "Low stock"
- `in_stock` → green/neutral badge "In stock"

Extend the `PharmacyItem` type in `src/types/` with `is_out_of_stock: boolean` and
`stock_status: 'in_stock' | 'low_stock' | 'out_of_stock'`.

### Acceptance
- An inventory row with `quantity_on_hand === 0` shows **Out of stock** (red), not "Low stock".
- `0 < qty <= reorder_level` shows **Low stock**; above shows **In stock**.

> Related: file 06 (#14) adds the restock notification when crossing into low/out states.
