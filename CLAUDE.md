# MedFlow Pro — Claude Code Guide

## Project Overview

**MedFlow Pro** is a multi-tenant Healthcare SaaS platform for clinics, hospitals, and laboratories.

- **Backend**: Django 5.x + DRF + PostgreSQL (schema-per-tenant via `django-tenants`)
- **Frontend**: React 19 + Vite + TypeScript + Tailwind CSS
- **Architecture**: Modular Monolith with Service Layer pattern

---

## Running the Project

### Prerequisites

The original venv at `venv/` was created on a different machine path and is broken. Use `venv_new/` instead:

```bash
# The working venv
cd /home/mohamed/Projects/medical/medical
```

### Start the Backend

```bash
# Terminal 1 — Django dev server
DJANGO_SETTINGS_MODULE=config.settings.development venv_new/bin/python manage.py runserver 0.0.0.0:8000
```

### Start the Frontend

```bash
# Terminal 2 — Vite dev server
cd frontend
npm run dev
```

Frontend: http://localhost:5173  
Backend API: http://localhost:8000/api/v1/  
Swagger docs: http://localhost:8000/api/docs/

### Infrastructure (Docker)

The PostgreSQL database runs in Docker. Only the DB container needs to be running for local dev:

```bash
docker compose up db -d     # Start only the database (port 5433)
docker compose up -d        # Full stack (PG + Redis + RabbitMQ + MinIO + Keycloak)
```

The DB listens on **port 5433** (not the default 5432) to avoid conflicts.

### Test Credentials

| Email | Password | Role |
|-------|----------|------|
| `admin@clinic.com` | `SecurePass123!` | Admin (Demo Clinic tenant) |

---

## Project Structure

```
medical/                          ← project root
├── config/
│   ├── settings/
│   │   ├── base.py               ← All core settings (tenants, DRF, Celery, MinIO)
│   │   ├── development.py        ← DEBUG=True, SimpleJWT auth, console email
│   │   ├── production.py         ← SSL, HSTS, secure cookies
│   │   └── testing.py            ← Eager Celery, fast hashers
│   ├── urls.py                   ← All API routes (/api/v1/...)
│   └── celery.py
├── apps/
│   ├── accounts/                 ← User, UserSecrets, JWT auth, Keycloak OIDC
│   ├── tenants/                  ← Organization model, schema provisioning
│   ├── rbac/                     ← Roles, Permissions, TenantUser
│   ├── patients/                 ← Patient records, MRN, soft-delete
│   ├── appointments/             ← DoctorProfile, Appointment scheduling
│   ├── medical_records/          ← Visit (SOAP), Vitals, Diagnosis
│   ├── prescriptions/            ← Prescription, PrescriptionItem, Medication
│   ├── lab_results/              ← LabOrder, TestResult, auto-flagging
│   ├── billing/                  ← Invoice, Payment, partial payments
│   ├── pharmacy/                 ← Inventory, StockTransaction, Dispensing
│   ├── insurance/                ← Provider, Policy, Claim
│   ├── ai_integration/           ← AIRequest, async OCR/lab analysis
│   ├── notifications/            ← Multi-channel (email/SMS/push/in-app)
│   ├── audit/                    ← Immutable AuditLog, middleware, signals
│   └── referrals/                ← Inter-facility patient referrals
├── common/
│   ├── models.py                 ← BaseModel (UUID PK), SoftDeleteModel
│   ├── enums.py                  ← All TextChoices enums
│   ├── utils.py                  ← MRN gen, Fernet encryption, IP extraction
│   ├── exceptions.py             ← Normalized error format: {"error": {"code","message"}}
│   └── health/                   ← /health/, /health/db/, /health/redis/
├── frontend/
│   └── src/
│       ├── pages/                ← Lazy-loaded page components
│       ├── components/           ← Sidebar, TopBar
│       ├── services/api.ts       ← All API calls (Axios)
│       ├── stores/               ← Zustand (authStore, uiStore)
│       ├── types/                ← TypeScript type definitions
│       └── lib/                  ← Utilities (safeFormat for dates, etc.)
├── venv_new/                     ← Working Python venv (use this one)
├── venv/                         ← Broken venv — wrong path hardcoded, do not use
├── .env                          ← Local environment variables
├── docker-compose.yml
└── manage.py
```

---

## Architecture Patterns

### Multi-Tenancy (Schema-per-Tenant)

- Uses `django-tenants` — each org gets its own PostgreSQL schema
- **Public schema**: `accounts`, `tenants`, `audit`, `referrals`
- **Tenant schemas**: everything else (patients, appointments, billing, etc.)
- **No cross-schema FK** — `DoctorProfile.user_id` is a `UUIDField`, not a ForeignKey
- `TENANT_MODEL = "tenants.Organization"`, `TENANT_DOMAIN_MODEL = "tenants.Domain"`

### Service Layer Pattern

Each app has a `services.py` containing all business logic. Views are thin:

```
View → Service → Model → DB
```

Never put business logic in views or serializers. Add it to `services.py`.

### Authentication

- **Development**: SimpleJWT (`rest_framework_simplejwt`)
- **Production**: Keycloak OIDC (`mozilla-django-oidc`)
- Both are configured in `config/settings/development.py`
- Token header: `Authorization: Bearer <access_token>`

### Data Safety Rules

- **Soft-delete only** — never `instance.delete()` on medical records; use `is_active=False`
- **Visit signing** — once `visit.is_signed = True`, the record is immutable
- **Audit log** — no UPDATE or DELETE on `AuditLog` records, ever
- **PII encryption** — `national_id` uses Fernet encryption via `common/utils.py`

---

## API Routes

All routes are prefixed with `/api/v1/`:

| Prefix | App |
|--------|-----|
| `/auth/` | accounts |
| `/rbac/` | rbac |
| `/tenants/` | tenants |
| `/patients/` | patients |
| `/appointments/` | appointments |
| `/visits/` | medical_records |
| `/prescriptions/` | prescriptions |
| `/lab-orders/` | lab_results |
| `/invoices/` | billing |
| `/notifications/` | notifications |
| `/ai/` | ai_integration |
| `/audit-logs/` | audit |
| `/pharmacy/` | pharmacy |
| `/referrals/` | referrals |
| `/insurance/` | insurance |

OpenAPI/Swagger: http://localhost:8000/api/docs/

---

## Database

- PostgreSQL 16 running in Docker on **port 5433**
- Credentials: `healthcare_user` / `healthcare_pass` / db `healthcare`
- Migrations: `manage.py migrate_schemas --shared` (public) + `migrate_schemas` (tenant)
- Demo tenant schema: `demo_clinic`

---

## Frontend Notes

- Vite proxies `/api/*` to `http://localhost:8000` (see `vite.config.ts`)
- Path alias `@` → `src/` (e.g. `import X from '@/components/X'`)
- All API calls go through `frontend/src/services/api.ts`
- Use `safeFormat()` from `src/lib/` for all date formatting (avoids "Invalid time value" errors)
- State: Zustand for auth/UI, TanStack Query for server state

---

## Key Environment Variables (`.env`)

| Variable | Default | Notes |
|----------|---------|-------|
| `SECRET_KEY` | dev key | Change in production |
| `DB_HOST` | `localhost` | `db` when using docker compose |
| `DB_PORT` | `5433` | Non-standard to avoid conflicts |
| `FIELD_ENCRYPTION_KEY` | set | Fernet key for national_id encryption |
| `DJANGO_SETTINGS_MODULE` | — | Must be set: `config.settings.development` |

---

## Common Tasks

### Run migrations

```bash
DJANGO_SETTINGS_MODULE=config.settings.development venv_new/bin/python manage.py migrate_schemas --shared
DJANGO_SETTINGS_MODULE=config.settings.development venv_new/bin/python manage.py migrate_schemas
```

### Create a new migration

```bash
DJANGO_SETTINGS_MODULE=config.settings.development venv_new/bin/python manage.py makemigrations <app_name>
```

### Django shell

```bash
DJANGO_SETTINGS_MODULE=config.settings.development venv_new/bin/python manage.py shell_plus
```

### Run tests

```bash
DJANGO_SETTINGS_MODULE=config.settings.testing venv_new/bin/python -m pytest
```

---

## Known Issues & Limitations

1. **Old `venv/`** — broken (was created at `/media/mohamed/New Volume/...`). Use `venv_new/` for everything.
2. **SMS/Push channels** — placeholders only; email and in-app notifications actually send.
3. **No file uploads wired** — MinIO is configured but no frontend upload UI exists yet.
4. **No WebSocket** — notifications use polling; Channels is installed but not connected.
5. **Keycloak optional in dev** — SimpleJWT is used by default; Keycloak requires Docker stack.
6. **AI integration** — requires external AI service (`AI_SERVICE_BASE_URL`); not functional out-of-box.
7. **No ICD-10 autocomplete** — diagnosis codes are entered manually.
