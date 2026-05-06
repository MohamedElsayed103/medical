# Healthcare SaaS — Handoff Document

## What's Been Done

### Architecture & Design
- Full architecture documented in `ARCHITECTURE.md`
- Modular monolith pattern with Django 5.x + DRF
- Schema-per-tenant multi-tenancy via `django-tenants`
- Service layer pattern: views are thin, business logic lives in `services.py`

### Project Structure
```
config/
├── settings/
│   ├── base.py           # Full settings (tenants, Keycloak, Celery, MinIO, DRF, structlog)
│   ├── development.py    # DEBUG=True, relaxed throttling
│   ├── production.py     # SSL, HSTS, secure cookies
│   └── testing.py        # Eager Celery, locmem cache, fast hashers
├── celery.py             # Celery app with autodiscover
├── urls.py               # All API v1 routes
├── wsgi.py / asgi.py
common/
├── models.py             # BaseModel (UUID PK), SoftDeleteModel
├── enums.py              # All TextChoices enums
├── exceptions.py         # Normalized error response format
├── utils.py              # MRN gen, encryption, hashing, IP extraction
├── pagination.py         # Page-number + Cursor pagination
├── validators.py         # Phone, file size, medical file type
└── health/               # /health/, /health/db/, /health/redis/
apps/
├── accounts/             # User, UserSecrets, TenantMembership, Keycloak OIDC, RBAC
├── tenants/              # Organization (TenantMixin), Domain, provisioning
├── patients/             # Patient (soft-delete, encrypted national_id, MRN)
├── appointments/         # DoctorProfile, Appointment (status machine, conflict detection)
├── medical_records/      # Visit (SOAP), Vitals, Diagnosis
├── prescriptions/        # Prescription, PrescriptionItem, Medication
├── lab_results/          # LabOrder, LabTest, TestResult (auto-flagging)
├── billing/              # Invoice, InvoiceItem, Payment (partial payments)
├── notifications/        # Notification, Preferences, channel adapters, Celery task
├── ai_integration/       # AIRequest, httpx client, Celery task with backoff
└── audit/                # Immutable AuditLog, middleware, signals (auto-log AUDITED models)
```

### Infrastructure Files
| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage, Python 3.12-slim, gunicorn, non-root user |
| `docker-compose.yml` | Full dev stack: PG16, Redis, RabbitMQ, MinIO, Keycloak, Nginx |
| `nginx/nginx.conf` | Reverse proxy with security headers |
| `.env.example` | All required env vars documented |
| `pyproject.toml` | pytest + coverage config |
| `.pre-commit-config.yaml` | black, isort, flake8, mypy, migration-linter |
| `.gitignore` | Standard Python/Django ignores |
| `requirements/` | base, development, production, testing splits |

### Key Design Decisions
- **No cross-tenant patient sharing** — simplifies HIPAA compliance
- **DoctorProfile.user_id is a UUID field** (not FK) — PostgreSQL can't do cross-schema FKs
- **Keycloak for auth** — JWKS validation, auto-provisioning users on first login
- **MinIO for file storage** — pre-signed URLs with 15-min expiry
- **Audit via signals** — any model with `AUDITED = True` gets auto-logged on save/delete

---

## What's Left (Next Steps)

### 1. Migrations
```bash
python manage.py makemigrations
python manage.py migrate_schemas --shared
```
- Generate initial migrations for all apps
- Validate with `django-migration-linter`

### 2. Keycloak Realm Setup
- Create `healthcare-saas` realm in Keycloak admin
- Create `web-app` client (confidential, OIDC)
- Configure redirect URIs, token lifetimes
- Map user roles to token claims

### 3. MinIO Bucket Initialization
- Create `medical-documents` and `ai-inputs` buckets
- Set bucket policies (private by default)
- Can be automated with an entrypoint script or management command

### 4. Tests
- Unit tests for each service layer (most critical)
- Integration tests for API endpoints (with `django-tenants` test utilities)
- Test fixtures / factories (recommend `factory_boy`)
- Target: 80%+ coverage (configured in `pyproject.toml`)

### 5. Missing Functional Pieces
| Item | Notes |
|------|-------|
| Email/SMS/Push integration | Channel adapters are placeholder stubs — wire up SendGrid/Twilio/FCM |
| File upload endpoints | MinIO storage is configured but no upload views exist yet |
| Appointment reminders | Celery beat periodic task to send reminders N hours before |
| Patient document management | Upload/list/download medical documents per patient |
| Reporting / analytics endpoints | Aggregate queries for dashboards |
| Webhook for AI results | Currently poll-based; consider WebSocket or callback URL |

### 6. Security Hardening
- [ ] Rate limiting per-endpoint (currently global throttle only)
- [ ] CORS allowed origins — tighten for production
- [ ] CSP headers in Nginx
- [ ] Rotate `FIELD_ENCRYPTION_KEY` strategy
- [ ] Add `django-axes` for brute-force protection on any local auth
- [ ] Penetration testing

### 7. CI/CD Pipeline
- GitHub Actions workflow: lint → test → build Docker image → push to registry
- Database migration check in CI (`migrate --check`)
- Deploy to staging on merge to `develop`, production on `main` tag

### 8. Observability
- [ ] Grafana dashboards (import Prometheus django/celery metrics)
- [ ] Alerting rules (error rate, latency P95, queue depth)
- [ ] Structured log shipping to ELK/Loki
- [ ] Sentry release tracking + source maps

### 9. Production Deployment
- `docker-compose.prod.yml` with resource limits, replicas, named networks
- TLS termination (Let's Encrypt or cloud LB)
- Database backups (pg_dump cron or managed PG)
- Secrets management (Vault, AWS Secrets Manager, or K8s secrets)

### 10. Documentation
- [ ] API docs auto-generated at `/api/docs/` (already wired via drf-spectacular)
- [ ] Developer onboarding guide
- [ ] Runbook for common ops tasks

---

## Quick Start (for the next developer)

```bash
# 1. Clone & configure
cp .env.example .env
# Edit .env with real values (especially FIELD_ENCRYPTION_KEY, SECRET_KEY)

# 2. Start infrastructure
docker compose up -d db redis rabbitmq minio keycloak

# 3. Install deps
pip install -r requirements/development.txt

# 4. Run migrations
python manage.py migrate_schemas --shared

# 5. Create a public tenant
python manage.py shell
# >>> from apps.tenants.services import TenantService
# >>> TenantService.create_organization(name="Demo Clinic", slug="demo", ...)

# 6. Run server
python manage.py runserver

# 7. Or run everything via Docker
docker compose up
```
