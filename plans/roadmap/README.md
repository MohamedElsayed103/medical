# MedFlow Pro — Product Roadmap & Implementation Plans

This directory turns [`SAAS_RECOMMENDATIONS.md`](../../SAAS_RECOMMENDATIONS.md) into **detailed,
buildable plans**. Every plan file covers **both backend and frontend**, with exact file paths,
models, endpoints, components, and acceptance criteria, so any engineer can pick up a task and ship it.

> These plans are NEW (post-2026-06-15) and supersede the original `plans/01..08` files, which were
> the bug/feature batch that is now largely shipped. Track live status in **[`PROGRESS.md`](./PROGRESS.md)**.

---

## How to use this directory

1. **Read this README** for the priority order and conventions.
2. **Open [`PROGRESS.md`](./PROGRESS.md)** — it is the single source of truth for *what is done and
   what is not*. Update it (check the box, set the status) as you complete each task. Do not track
   status inside the plan files themselves.
3. **Pick the lowest-priority-number plan with unfinished tasks** and implement top-to-bottom.

---

## Priority model

| Tier | Meaning | When |
|------|---------|------|
| **P0** | Makes the product *feel finished* and stops regressions. Low risk, high perceived value. | Now |
| **P1** | Clinical depth + patient experience that wins deals and drives daily usage. | Next |
| **P2** | Enterprise scale: revenue cycle, interoperability, compliance, deep AI. | Then |

Within a plan, tasks are ordered by impact-to-effort. Each task has its own priority tag in case
you want to cherry-pick across plans.

---

## The plans

| # | Plan | Tier | Theme |
|---|------|------|-------|
| 01 | [Foundation & Quick Wins](./01-foundation-and-quick-wins.md) | **P0** | Rich detail pages, clickable rows, print/PDF, global search, status timelines, error normalization, API smoke tests, OpenAPI-typed client, seed data |
| 02 | [Notifications & File Pipeline](./02-notifications-and-files.md) | **P0→P1** | SMS/push providers, real-time WebSocket bell, production file storage (uploads, DICOM, document categories) |
| 03 | [Clinical Depth](./03-clinical-depth.md) | **P1** | Drug DB + interaction checking, problem/allergy lists, ICD-10/CPT/LOINC coded pickers, note templates & order sets, vitals/growth charts, care plans, referrals loop |
| 04 | [Patient Experience](./04-patient-experience.md) | **P1** | Patient portal, online self-scheduling, reminders, telehealth, digital intake/consent, online bill pay |
| 05 | [Revenue Cycle Management](./05-revenue-cycle.md) | **P2** | Eligibility (270/271), claims & ERA (837/835), superbills, payment plans, RCM analytics |
| 06 | [AI & Intelligence](./06-ai-intelligence.md) | **P1→P2** | Ambient scribe (note generation), result summarization, coding suggestions, smart inbox, no-show prediction |
| 07 | [Platform, Trust & Compliance](./07-platform-compliance.md) | **P2** | HIPAA/GDPR posture, audit/access-log UI, observability/SLOs, background-job hardening, FHIR R4 / HL7 v2 |

**Recommended build order:** 01 → 02 → (03 ‖ 04 ‖ 06 in parallel) → 05 → 07.

---

## Conventions every plan assumes

### Backend (Django 5 + DRF, schema-per-tenant)
- Use `venv_new/`, always `DJANGO_SETTINGS_MODULE=config.settings.development`.
- **Service layer:** business logic in `apps/<app>/services.py` as `@staticmethod` on a `*Service`
  class; writes wrapped in `@transaction.atomic`. Views stay thin. Raise
  `common.exceptions.ServiceError(message, code="UPPER_SNAKE")` for business-rule violations.
- **Base models:** inherit `common.models.BaseModel` (UUID pk, timestamps) or `SoftDeleteModel`
  (`is_active`, `deleted_at`, `soft_delete()`; default manager already hides soft-deleted rows —
  never filter on the `is_deleted` *property*, it is not a DB column).
- **Cross-schema rule:** NEVER FK from a tenant model to a public model (User, Organization).
  Reference users by `UUIDField` named `<role>_id` (e.g. `recorded_by_id`).
- **Enums:** shared `TextChoices` go in `common/enums.py`.
- **Permissions:** `apps/rbac/permissions.py::HasPermission('<resource>:<action>')`. Add new
  permission strings to the RBAC seed in `apps/rbac/services.py` and grant them to roles.
- **Migrations:** `makemigrations <app>` → `migrate_schemas --shared` (public apps) +
  `migrate_schemas` (tenant apps). New tenant apps go in `TENANT_APPS` (config/settings/base.py),
  public apps in `SHARED_APPS`. New apps also need a `config/urls.py` include.
- **Audit:** set `AUDITED = True` on a model to auto-log CRUD.

### Frontend (React 19 + Vite + TS + Tailwind)
- **API calls** only via a service object in `src/services/api.ts` (never axios in a component).
  FormData uploads must pass `multipartConfig(data)` (already added) so the JSON content-type is cleared.
- **Types** in `src/types/index.ts`.
- **Routing** in `src/App.tsx` (lazy import + `<Route>`); detail routes are `/<resource>/:id`.
- **Nav** in `src/components/navigation/Sidebar.tsx`, gated by `permission`.
- **Server state:** TanStack Query; **app state:** Zustand (`authStore`, `uiStore`).
- **Forms:** React Hook Form + Zod (Zod schema is the source of truth for "required").
- **Dates:** always `safeFormat()` from `src/lib/utils`.
- **Permission gating:** `useAuthStore().hasPermission('resource:action')`.

### Definition of done (every task)
- Migration created + applied to `public` and `demo_clinic`; endpoint returns 2xx with the test
  admin token; RBAC enforced; service raises `ServiceError` on bad input.
- Frontend: no console errors; loading + empty states; action buttons permission-gated; row → detail
  navigation where a list exists.
- A happy-path API smoke test exists for any new endpoint (see Plan 01).
- `PROGRESS.md` updated.

### Test credentials / run
- `admin@clinic.com` / `SecurePass123!` (tenant `demo_clinic`), DB on port 5433.
- Backend: `… manage.py runserver 0.0.0.0:8000`; Frontend: `cd frontend && npm run dev`.
