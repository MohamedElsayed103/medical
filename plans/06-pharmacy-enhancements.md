# 06 — Pharmacy Enhancements

Covers **#10** (pharmacy ordering: internal/external customer, OTC or prescription-linked, purchase),
**#12** (bulk upload medications), **#14** (low-stock restock notification), and integrates **#13**
(out-of-stock label, defined in file 01).

Depends on `05` (Customer, `validate_orderer`, `BillingService.create_from_source`) and `02`
(`pharmacy_orders:*`, `pharmacy:*`, `customers:*`).

---

## Current state (verified)
- `PharmacyInventory` (medication, batch, qty, reorder_level/qty, unit_cost, location, `is_low_stock`).
- `StockTransaction` (immutable ledger: RECEIVED/DISPENSED/ADJUSTED/EXPIRED/RETURNED, balance_after,
  performed_by_id).
- `DispenseRecord` / `DispenseItem` (prescription-linked dispensing; FEFO via
  `PharmacyService.dispense_prescription`).
- `PharmacyService`: `receive_stock`, `adjust_stock`, `dispense_prescription` (FEFO),
  `get_low_stock_items`, `get_expiring_stock`. Endpoints under `/api/v1/pharmacy/`.
- After file 04: `enqueue_for_dispense` + `_notify_pharmacists` exist; dispense-queue returns
  `DispenseRecord`s.

---

## #10 — Pharmacy ordering / point-of-sale

A pharmacist creates an **order** for either an internal patient or an external walk-in, with line
items chosen from inventory (OTC) and/or pulled from a prescription, then **completes the purchase**
(records payment via auto-invoice, deducts stock).

### New model — `apps/pharmacy/models.py`
```python
class PharmacyOrderStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    AWAITING_PAYMENT = "awaiting_payment", "Awaiting Payment"
    PAID = "paid", "Paid"
    FULFILLED = "fulfilled", "Fulfilled"      # stock handed over
    CANCELLED = "cancelled", "Cancelled"

class PharmacyOrder(BaseModel):
    # orderer (exactly one — see file 05 Part B)
    patient = models.ForeignKey("patients.Patient", null=True, blank=True,
                                on_delete=models.PROTECT, related_name="pharmacy_orders")
    customer = models.ForeignKey("patients.Customer", null=True, blank=True,
                                 on_delete=models.PROTECT, related_name="pharmacy_orders")
    prescription = models.ForeignKey("prescriptions.Prescription", null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name="pharmacy_orders",
                                     help_text="Set when the order originates from a prescription.")
    order_number = models.CharField(max_length=30, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=PharmacyOrderStatus.choices,
                              default=PharmacyOrderStatus.DRAFT)
    invoice = models.ForeignKey("billing.Invoice", null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="pharmacy_orders")
    created_by_id = models.UUIDField(help_text="Pharmacist user id")
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "pharmacy_order"
        ordering = ["-created_at"]
    AUDITED = True

class PharmacyOrderItem(BaseModel):
    order = models.ForeignKey(PharmacyOrder, on_delete=models.CASCADE, related_name="items")
    medication = models.ForeignKey("prescriptions.Medication", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # batch chosen at fulfillment (FEFO); recorded for traceability
    inventory = models.ForeignKey(PharmacyInventory, null=True, blank=True,
                                  on_delete=models.SET_NULL)

    class Meta:
        db_table = "pharmacy_order_item"

    @property
    def line_total(self):
        return self.quantity * self.unit_price
```
Add `orderer_name`/`orderer_type` properties (file 05 Part B). Migration: `makemigrations pharmacy`
→ `migrate_schemas`.

### Service — `apps/pharmacy/services.py`
```python
class PharmacyOrderService:
    @staticmethod
    @transaction.atomic
    def create_order(*, created_by_id, patient_id=None, customer_id=None,
                     customer_name=None, customer_phone=None,
                     prescription_id=None, items: list[dict], notes="") -> PharmacyOrder:
        # resolve orderer (file 05 convention)
        customer = None
        if not patient_id:
            if customer_id:
                customer = Customer.objects.get(id=customer_id)
            elif customer_name and customer_phone:
                customer = CustomerService.get_or_create_by_phone(full_name=customer_name, phone=customer_phone)
        validate_orderer(patient_id, customer.id if customer else None)

        order = PharmacyOrder.objects.create(
            order_number=generate_order_number("PH"),    # reuse/extend common util
            patient_id=patient_id, customer=customer,
            prescription_id=prescription_id, created_by_id=created_by_id, notes=notes,
        )
        for it in items:
            med = Medication.objects.get(id=it["medication_id"])
            # default price: latest inventory unit_cost * markup, or explicit unit_price
            unit_price = Decimal(str(it.get("unit_price") or PharmacyOrderService._default_price(med)))
            PharmacyOrderItem.objects.create(order=order, medication=med,
                                             quantity=it["quantity"], unit_price=unit_price)
        # validate stock availability (sum across batches) — warn/raise if insufficient
        PharmacyOrderService._assert_stock_available(order)
        return order

    @staticmethod
    @transaction.atomic
    def checkout(*, order: PharmacyOrder, created_by_id) -> PharmacyOrder:
        """Generate the invoice (auto-bill) and move to AWAITING_PAYMENT."""
        if order.status != PharmacyOrderStatus.DRAFT:
            raise ServiceError("Order is not in draft.", code="NOT_DRAFT")
        invoice = BillingService.create_from_source(
            source_type="pharmacy_order", source_id=str(order.id),
            patient=order.patient, customer=order.customer,
            items=[{"item_type": "medication", "description": f"{i.medication.name} x{i.quantity}",
                    "quantity": i.quantity, "unit_price": i.unit_price} for i in order.items.all()],
            created_by_id=created_by_id,
        )
        order.invoice = invoice
        order.status = PharmacyOrderStatus.AWAITING_PAYMENT
        order.save(update_fields=["invoice", "status", "updated_at"])
        return order

    @staticmethod
    @transaction.atomic
    def fulfill(*, order: PharmacyOrder, performed_by_id) -> PharmacyOrder:
        """Deduct stock (FEFO) once paid, mark fulfilled. Triggers low-stock checks."""
        if order.status not in (PharmacyOrderStatus.PAID, PharmacyOrderStatus.AWAITING_PAYMENT):
            raise ServiceError("Order not ready to fulfill.", code="NOT_PAYABLE")
        for item in order.items.select_related("medication"):
            PharmacyService._deduct_fefo(medication=item.medication, quantity=item.quantity,
                                         performed_by_id=performed_by_id,
                                         reference=order.order_number)
        order.status = PharmacyOrderStatus.FULFILLED
        order.save(update_fields=["status", "updated_at"])
        return order
```
Notes:
- Refactor the FEFO deduction loop out of `dispense_prescription` into a reusable
  `PharmacyService._deduct_fefo(*, medication, quantity, performed_by_id, reference)` that creates
  `StockTransaction` rows and updates `quantity_on_hand`, then calls the low-stock check (#14).
  `dispense_prescription` should call the same helper to avoid two stock-mutation code paths.
- `order.status == PAID` is set when the linked invoice becomes PAID (file 08 can call back, or
  `fulfill` accepts AWAITING_PAYMENT for cash-at-counter where payment + fulfill happen together —
  support both; for a simple counter sale, checkout→record payment→fulfill can be one combined
  endpoint `POST /pharmacy/orders/{id}/complete-sale/`).
- `generate_order_number("PH")`: add a small helper in `common/utils.py` (there's already an invoice
  number generator pattern — mirror it with a prefix arg).

### API — `apps/pharmacy/views.py` + `urls.py`
- `GET/POST /api/v1/pharmacy/orders/` → list/create (`pharmacy_orders:read`/`write`).
- `GET /api/v1/pharmacy/orders/{id}/` → detail.
- `POST /api/v1/pharmacy/orders/{id}/checkout/` → create invoice.
- `POST /api/v1/pharmacy/orders/{id}/fulfill/` → deduct stock.
- `POST /api/v1/pharmacy/orders/{id}/complete-sale/` → combined checkout+pay+fulfill for counter
  sales (body: payment method/amount); records payment through `BillingService.record_payment`.
- `POST /api/v1/pharmacy/orders/{id}/cancel/`.
Serializers in `apps/pharmacy/serializers.py` (order + items + orderer fields per file 05).

### Frontend — new "Pharmacy Orders" UI
- Add a tab/section on `PharmacyPage.tsx` (or a new `pages/pharmacy/PharmacyOrdersPage.tsx` + route
  `/pharmacy/orders` gated `pharmacy_orders:read`).
- New order flow:
  1. Choose orderer: **Internal** (patient search → patient_id) or **External** (name + phone →
     resolved to a Customer).
  2. Optionally pick a prescription (for internal patients with a pending Rx) to prefill items;
     or add OTC items by searching `medications`.
  3. Add line items (medication, qty; price auto-filled, editable).
  4. Checkout → shows invoice/total → take payment (method) → fulfill.
- `pharmacyService` additions: `getOrders`, `createOrder`, `getOrder`, `checkout`, `fulfill`,
  `completeSale`, `cancelOrder`. Types in `src/types/`.

### Acceptance
- Pharmacist creates an order for a **walk-in** (name+phone) → Customer is created/reused → items
  added → sale completed → stock deducted → a paid invoice exists linked to the order.
- Same for an **internal patient**, including prefilling from a prescription.
- Insufficient stock blocks fulfillment with a clear error.

---

## #12 — Bulk upload medications / inventory

Let a pharmacist upload a CSV to create `Medication` references and/or `PharmacyInventory` batches in
one shot.

### Backend
- New endpoint `POST /api/v1/pharmacy/inventory/bulk-upload/` (multipart file) →
  `pharmacy:write`.
- Service `PharmacyService.bulk_upload(*, file, performed_by_id) -> dict`:
  - Parse CSV with Python stdlib `csv` (no new dependency). Expected columns (document in UI + a
    downloadable template):
    `medication_name, generic_name, form, strength, manufacturer, batch_number, expiry_date,
     quantity, reorder_level, reorder_quantity, unit_cost, location`.
  - For each row: `get_or_create` `Medication` by (name, strength, form); create or top-up
    `PharmacyInventory` (if same medication+batch exists, `receive_stock`; else create then
    `receive_stock`). All within `@transaction.atomic`; collect per-row errors.
  - Return `{ "created": n, "updated": m, "errors": [{row, message}] }`. **Do not abort the whole
    file on one bad row** — skip it, report it (use a savepoint per row).
  - Validate `form` against `MedicationForm` choices; validate dates; coerce numerics; on invalid →
    row error.

### Frontend
- "Bulk upload" button on the pharmacy inventory view → file picker + a "Download CSV template" link
  (static template matching the columns). After upload, show a result summary (created/updated/errors
  table). `pharmacyService.bulkUpload(file)` using `FormData`.

### Acceptance
- Uploading a valid CSV creates medications + inventory; a file with some bad rows imports the good
  rows and reports the bad ones with row numbers.

---

## #14 — Low-stock → notify pharmacists to restock

### Backend
- In `PharmacyService._deduct_fefo(...)` (the shared deduction helper), after updating
  `quantity_on_hand`, check the medication's **aggregate** stock across active batches:
  ```python
  total = PharmacyInventory.objects.filter(medication=medication, is_active=True)\
            .aggregate(s=Sum("quantity_on_hand"))["s"] or 0
  # use the batch's reorder_level (or a per-medication threshold); compare aggregate
  if total == 0:
      PharmacyService._notify_pharmacists(title="Out of stock",
          body=f"{medication.name} is OUT OF STOCK.", data={"medication_id": str(medication.id)})
  elif crossed_into_low:   # was above reorder_level before this deduction, now <=
      PharmacyService._notify_pharmacists(title="Low stock — restock needed",
          body=f"{medication.name} is low ({total} left). Reorder suggested.",
          data={"medication_id": str(medication.id)})
  ```
  - **Only notify on the crossing** (compute the pre-deduction total; notify when it transitions from
    above-threshold to at/below, or to zero) to avoid spamming on every subsequent dispense while
    already low. Keep it simple: compare `before > reorder_level >= after` for "entered low", and
    `after == 0` for out-of-stock.
- `_notify_pharmacists(*, title, body, data=None)` (shared with file 04):
  ```python
  # resolve all active pharmacists: TenantUsers whose role grants pharmacy:write
  pharmacist_ids = TenantUser.objects.filter(
      status=TenantUserStatus.ACTIVE, is_deleted=False,
      role__role_permissions__permission__name="pharmacy:write",
      role__role_permissions__is_deleted=False,
  ).values_list("user_id", flat=True).distinct()
  for uid in pharmacist_ids:
      try:
          NotificationService.create_and_send(
              recipient_id=str(uid), notification_type=NotificationType.SYSTEM,
              title=title, body=body, channel=NotificationChannel.IN_APP, data=data or {})
      except Exception:
          logger.warning("pharmacist_notify_failed", user_id=str(uid))
  ```
  (Import `TenantUser`, `NotificationService`, enums at top or lazily to avoid cycles.)

### Frontend
- No new screen required — notifications land in the bell. Optionally add a "Low / Out of stock"
  filter chip on the inventory list (uses `stock_status` from file 01).

### Acceptance
- Dispensing/fulfilling that pushes a medication's total stock to ≤ reorder_level fires **one**
  low-stock notification to all pharmacists; hitting 0 fires an out-of-stock notification.
- No duplicate notifications on every subsequent dispense while it stays low.
