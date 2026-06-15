# 05 — Ordering System Foundation (shared)

This file defines the **shared building blocks** used by pharmacy (file 06), lab & radiology
(file 07), and billing (file 08). Implement it **before** 06/07/08. Items it directly enables:
**#10** (internal vs external orderer across pharmacy/lab/rays) and the auto-billing hook for **#17**.

Depends on `02` (uses `customers:*`).

---

## Locked decisions recap
- **External/walk-in orderer** → dedicated `Customer` model. Each order has a **nullable `patient` FK
  AND a nullable `customer` FK**; exactly one is set.
- **Auto-billing** → a single `BillingService.create_from_source(...)` helper that every order/visit
  calls to spin up a DRAFT invoice linked to its source.

---

## Part A — The `Customer` model (walk-in / external)

New tenant-schema model. Put it in a small shared place so pharmacy/lab/rays can all import it.
**Recommended location:** `apps/patients/models.py` (same app as Patient, conceptually "people we
serve") — OR a new `apps/customers/` app. Default: **add to `apps/patients/`** to avoid a new app +
settings wiring. Document the choice.

```python
class Customer(SoftDeleteModel):
    """Non-patient orderer (walk-in) for pharmacy/lab/rays. Minimal PII; not a clinical record."""
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "patients_customer"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["phone"]), models.Index(fields=["full_name"])]
    AUDITED = True

    def __str__(self):
        return f"{self.full_name} ({self.phone})"
```

### Service — `apps/patients/services.py` (or customers service)
```python
class CustomerService:
    @staticmethod
    def get_or_create_by_phone(*, full_name: str, phone: str, email: str = "") -> Customer:
        """Reuse a walk-in by phone so repeat customers accumulate history."""
        customer, created = Customer.objects.get_or_create(
            phone=phone, defaults={"full_name": full_name, "email": email})
        if not created and full_name and customer.full_name != full_name:
            # keep most recent name; don't clobber silently if blank
            customer.full_name = full_name
            customer.save(update_fields=["full_name", "updated_at"])
        return customer
```

### API — endpoints (new `CustomerViewSet`)
- `GET /api/v1/customers/?search=<name|phone>` → `customers:read`
- `POST /api/v1/customers/` → `customers:write`
- `GET /api/v1/customers/{id}/` → `customers:read`
- `PATCH /api/v1/customers/{id}/` → `customers:write`
Register under `/api/v1/customers/` in `config/urls.py` (and the app's `urls.py`). Add serializer.

### Migration
`makemigrations patients` (or new app) → `migrate_schemas` (tenant).

---

## Part B — The orderer mixin pattern (how orders reference patient OR customer)

Every order model (PharmacyOrder, LabOrder updates, RadiologyOrder) gains these two nullable FKs and a
validation rule. **Do not** create an abstract base with FKs (django-tenants + abstract FK
`related_name` clashes are painful); instead add the two fields directly to each order model and reuse
a shared validator function.

Fields to add to each order model:
```python
patient = models.ForeignKey("patients.Patient", null=True, blank=True,
                            on_delete=models.PROTECT, related_name="%(class)s_orders")
customer = models.ForeignKey("patients.Customer", null=True, blank=True,
                             on_delete=models.PROTECT, related_name="%(class)s_orders")
```

Shared validator — `common/validators.py`:
```python
def validate_orderer(patient_id, customer_id):
    """Exactly one of patient/customer must be set."""
    if bool(patient_id) == bool(customer_id):
        from common.exceptions import ServiceError
        raise ServiceError("An order must reference exactly one of patient or customer.",
                           code="INVALID_ORDERER")
```
Call `validate_orderer(...)` at the top of each order-creating service method.

Convenience read property on each order model:
```python
@property
def orderer_name(self) -> str:
    if self.patient_id:
        return self.patient.full_name
    return self.customer.full_name if self.customer_id else ""

@property
def orderer_type(self) -> str:
    return "patient" if self.patient_id else "customer"
```

> **Existing `LabOrder` has a non-null `patient` FK today.** File 07 covers the migration to make it
> nullable and add `customer`. Existing rows keep their patient — safe.

### Serializer convention
Order serializers accept **one of**: `patient_id` OR (`customer_id` OR inline
`{customer_name, customer_phone}`). On create, the service resolves: if `customer_id` given use it;
elif `customer_name`+`customer_phone` given call `CustomerService.get_or_create_by_phone`; else use
`patient_id`. Expose read-only `orderer_name` and `orderer_type` in responses.

---

## Part C — Auto-billing hook (`BillingService.create_from_source`)

A single entry point so visits, pharmacy orders, and lab/rays orders all bill consistently. Full
status/flow details are in file 08; this is the **interface contract** the other files call.

Add to `apps/billing/services.py`:
```python
@staticmethod
@transaction.atomic
def create_from_source(*, source_type: str, source_id: str,
                       patient=None, customer=None,
                       items: list[dict], created_by_id: str,
                       tax_rate=Decimal("0.00"), discount_amount=Decimal("0.00"),
                       notes: str = "") -> Invoice:
    """
    Create a DRAFT invoice linked to a source event. Idempotent per (source_type, source_id):
    if a non-cancelled invoice already exists for this source, return it instead of duplicating.
    items: [{item_type, description, quantity, unit_price}]
    """
```
Requirements:
- Add `source_type` (CharField, choices: `visit|pharmacy_order|lab_order|radiology_order|manual`,
  default `manual`) and `source_id` (UUIDField, null=True) to the `Invoice` model so invoices link
  back to what generated them. Also add nullable `customer` FK to `Invoice` (today it only has
  `patient`) so walk-in sales can be billed. Make `Invoice.patient` nullable (mirror Part B).
- Idempotency: unique-ish guard — before creating, check
  `Invoice.objects.filter(source_type=..., source_id=..., status__ne=CANCELLED).first()`.
- Reuse the existing total math from `BillingService.create_invoice` (subtotal/tax/discount/total).
- Returns the invoice in `DRAFT`; billing staff finalizes/collects later (file 08).

Migration for the new Invoice fields: `makemigrations billing` → `migrate_schemas`.

### Who calls it (wired in their own files)
- **Visit completed/signed** (file 08 + 03): consultation line from `doctor.consultation_fee`.
- **Pharmacy order purchased** (file 06): one line per dispensed med (qty × unit price).
- **Lab order completed** (file 07): one line per test.
- **Radiology order completed** (file 07): one line per study/exam.

---

## Acceptance for this file
- `Customer` CRUD works and `get_or_create_by_phone` dedupes repeat walk-ins by phone.
- `validate_orderer` rejects orders with both/neither patient and customer (`INVALID_ORDERER`).
- `BillingService.create_from_source` creates exactly one DRAFT invoice per source event (idempotent),
  linked via `source_type`/`source_id`, billable to either a patient or a customer.
