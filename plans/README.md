# MedFlow Pro — Implementation Plan Index

This directory contains the full implementation plan for the 18 requested items, split into
self-contained files. Each file is written so it can be implemented **independently and in order**
with no ambiguity. Read this index first, then implement files in the recommended sequence.

> **Audience:** the implementing engineer (Sonnet). Every file gives exact file paths, exact model
> fields, migration commands, serializer/view/URL diffs, frontend changes, and acceptance criteria.

---

## Locked architectural decisions (do not re-litigate)

These were decided up front because they fork the data model:

1. **External/walk-in orderers** → a dedicated `Customer` model (tenant schema). Order models
   (pharmacy/lab/rays) get a **nullable `patient` FK AND a nullable `customer` FK**; exactly one is
   set per order. `Patient` stays clinical-only. See `05-ordering-system-foundation.md`.
2. **Pharmacy OTC** → a pharmacy order may be **free-standing (OTC)** OR linked to a prescription.
3. **Auto-billing** → completing a visit, dispensing a pharmacy order, or completing a lab/rays
   order **auto-creates a DRAFT invoice** linked to the source. Billing staff finalizes. See
   `08-billing-and-invoicing.md`.
4. **Doctor availability** → **weekly recurring schedule + date-specific exceptions** (time off).

---

## Item → file mapping

| # | Request | File |
|---|---------|------|
| 1 | Patient page: visits/lab/invoices navigation | `01-quick-fixes.md` |
| 2 | Dashboard Revenue Overview fix | `01-quick-fixes.md` |
| 3 | Remove "other" gender option | `01-quick-fixes.md` |
| 9 | Wrong required fields | `01-quick-fixes.md` |
| 13 | "Out of stock" vs "low stock" label | `01-quick-fixes.md` |
| 8 | RBAC enforced everywhere; vitals by Nurse+Doctor | `02-rbac-and-permissions.md` |
| 18 | Login shows only permitted features | `02-rbac-and-permissions.md` |
| 4 | Doctor availability schedule | `03-appointments-and-availability.md` |
| 5 | Search by specialization → choose doctor | `03-appointments-and-availability.md` |
| 6 | Calendar view: doctor name + filters | `03-appointments-and-availability.md` |
| 7 | Completed appointment → record visit (notify) | `03-appointments-and-availability.md` |
| 15 | Finalized prescription auto-flows to pharmacy | `04-prescriptions-and-visits.md` |
| 16 | Prescription as part of the visit | `04-prescriptions-and-visits.md` |
| 10a | Shared customer + ordering foundation | `05-ordering-system-foundation.md` |
| 10b | Pharmacy ordering (internal/external, OTC) | `06-pharmacy-enhancements.md` |
| 12 | Bulk upload meds to pharmacy | `06-pharmacy-enhancements.md` |
| 14 | Low-stock → notify to restock | `06-pharmacy-enhancements.md` |
| 10c | Lab ordering (internal/external) | `07-lab-and-radiology.md` |
| 11 | New Radiology (rays) app | `07-lab-and-radiology.md` |
| 17 | Invoice logic review + auto-generation | `08-billing-and-invoicing.md` |

---

## Recommended implementation order (by dependency)

```
02-rbac-and-permissions       ← foundational; new resources/permissions used by everything
01-quick-fixes                ← independent, low risk; ship early for momentum
05-ordering-system-foundation ← Customer model + billing-source hook; blocks 06 & 07
03-appointments-and-availability
04-prescriptions-and-visits
06-pharmacy-enhancements      ← depends on 05
07-lab-and-radiology          ← depends on 05
08-billing-and-invoicing      ← depends on 05; integrates 04/06/07 sources
```

**Why this order:** `02` adds the permission strings every later view references, so doing it first
avoids re-touching viewsets. `05` defines the `Customer` model and the `BillingService.create_from_source`
hook that `06`, `07`, and `08` all call. `01` is parallelizable any time.

---

## Conventions every file assumes

### Backend (Django)
- **Python entry point:** use `venv_new/`, not `venv/` (the old one is broken). Always set
  `DJANGO_SETTINGS_MODULE=config.settings.development`.
- **Service layer:** business logic goes in `apps/<app>/services.py` as `@staticmethod` on a
  `*Service` class, wrapped in `@transaction.atomic` for writes. Views stay thin (validate →
  call service → serialize). Raise `common.exceptions.ServiceError(message, code="UPPER_SNAKE")`
  for business-rule violations.
- **Base models:** inherit `common.models.BaseModel` (UUID pk, timestamps) or `SoftDeleteModel`
  (adds `is_active`, `deleted_at`, `soft_delete()`, `objects`/`all_objects`).
- **Cross-schema rule:** NEVER add a FK from a tenant-schema model to a public-schema model
  (User, Organization). Reference users by `UUIDField` named `<role>_id` (e.g. `recorded_by_id`),
  matching the existing `DoctorProfile.user_id` pattern.
- **Enums:** add new `TextChoices` to `common/enums.py` (shared) unless app-local (e.g. pharmacy
  has local enums in its `models.py`). Follow existing style.
- **Migrations (django-tenants):** after model changes run:
  ```bash
  DJANGO_SETTINGS_MODULE=config.settings.development venv_new/bin/python manage.py makemigrations <app>
  DJANGO_SETTINGS_MODULE=config.settings.development venv_new/bin/python manage.py migrate_schemas --shared   # public-schema apps
  DJANGO_SETTINGS_MODULE=config.settings.development venv_new/bin/python manage.py migrate_schemas            # tenant-schema apps
  ```
  New tenant-schema apps must be added to `TENANT_APPS` in `config/settings/base.py`; public apps to
  `SHARED_APPS`. (All clinical/ordering apps are **tenant** apps.)
- **Audit:** set `AUDITED = True` on a model class to auto-log CRUD (existing signal mechanism).
- **Permissions:** import permission classes from `apps/rbac/permissions.py`. After `02` is done,
  prefer the explicit `HasPermission('<resource>:<action>')` (via the `require_permission` helper in
  `get_permissions()`) over the legacy `IsDoctor`/`IsNurseOrAbove` aliases.

### Frontend (React + TS)
- **API calls:** add a method to the relevant service object in `src/services/api.ts`. Never call
  axios from a component.
- **Types:** add/extend interfaces in `src/types/` (see `src/types/index.ts`).
- **Routing:** routes are declared in `src/App.tsx`. Detail routes follow `/<resource>/:id`.
- **Permission gating:** `useAuthStore().hasPermission('resource:action')`. After `02`, also wrap
  protected routes in the new `<RequirePermission>` component and gate action buttons.
- **Dates:** always format with the existing `safeFormat()` util — never raw `format(parseISO(...))`
  without a validity guard (this is the source of past "Invalid time value" crashes).
- **Forms:** React Hook Form + Zod. The Zod schema is the source of truth for "required"; the `*`
  in the label must match it.

### Definition of done (every item)
- Backend: migration created + applied to `public` and `demo_clinic`; endpoint returns 2xx with the
  test admin token; RBAC enforced; service raises `ServiceError` on bad input.
- Frontend: no console errors; loading + empty states present; action buttons gated by permission.
- Manual check against `TEST_FLOW.md` for the affected screen.
