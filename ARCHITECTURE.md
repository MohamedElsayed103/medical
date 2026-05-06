# Healthcare SaaS Backend — Architecture Plan

> **Version**: 1.0  
> **Date**: 2026-05-05  
> **Stack**: Django 5.x + Django REST Framework + PostgreSQL + Keycloak + Celery + RabbitMQ + MinIO  
> **Architecture**: Modular Monolith (Schema-per-Tenant)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Decisions & Rationale](#architecture-decisions--rationale)
3. [Project Structure](#project-structure)
4. [Database Design](#database-design)
5. [Authentication & Authorization (Keycloak)](#authentication--authorization-keycloak)
6. [API Design](#api-design)
7. [AI Integration Layer](#ai-integration-layer)
8. [Security & Compliance](#security--compliance)
9. [Monitoring & Observability](#monitoring--observability)
10. [Migration Management](#migration-management)
11. [Infrastructure (Docker)](#infrastructure-docker)
12. [Dependencies](#dependencies)
13. [Verification & Testing Strategy](#verification--testing-strategy)

---

## Executive Summary

This document defines the production-ready backend architecture for a Healthcare SaaS platform serving clinics, hospitals, and laboratories. The system manages patient records (EMR), appointments, prescriptions, billing, lab results, and integrates with an external AI service for prescription OCR, lab analysis, and radiology processing.

### Key Architectural Choices

| Concern | Decision |
|---------|----------|
| Multi-tenancy | Schema-per-tenant via `django-tenants` |
| Patient ownership | Per-tenant only (no cross-tenant sharing) |
| Authentication | Keycloak (OIDC) + `UserSecrets` table |
| Business logic | Service layer pattern (`services.py`) |
| File storage | MinIO (S3-compatible, self-hosted) |
| Async processing | Celery + RabbitMQ |
| AI communication | REST for sync + RabbitMQ for heavy tasks |
| Monitoring | Sentry + Prometheus + Grafana + structlog |
| Migrations | Django migrations + `django-migration-linter` + squashing |
| Deployment | Docker Compose → cloud (AWS/GCP/Azure) |

---

## Architecture Decisions & Rationale

### Why Schema-per-Tenant (not shared DB with FK)?

- **True data isolation** at database level — eliminates entire class of data-leak bugs
- Each tenant's schema is independently queryable; no `WHERE tenant_id = X` on every query
- Regulatory compliance: some health authorities require physical data separation
- `django-tenants` handles schema routing transparently
- **Practical limit**: ~500 tenants per PostgreSQL instance. Beyond that, shard by DB instance.

### Why Patients Are Tenant-Scoped Only?

- Cross-tenant patient sharing introduces:
  - Cross-schema queries (PostgreSQL doesn't JOIN across schemas natively)
  - HIPAA consent management (which tenant can see what data)
  - Complex patient identity resolution
- **Eliminated complexity**: no `PatientIdentity` in public schema, no `PatientConsent` table, no cross-schema joins
- **Future path**: If needed, add "patient referral" feature — explicit opt-in data sharing between specific tenants via API, not shared tables.

### Why Service Layer (not Fat Models)?

- **Models** own data integrity: constraints, validation, computed properties
- **Services** own business logic: workflows spanning multiple models, external calls, side effects
- **Views/ViewSets** are thin: validate input → call service → return response
- Benefits:
  - Models testable in isolation (no mocking external services)
  - Services mockable for fast unit tests
  - Clear dependency graph
  - Easy to extract into microservice later (service = natural boundary)

### Why Keycloak (not SimpleJWT)?

- Externalizes all auth complexity: password policies, MFA, brute-force protection, SSO
- Supports OIDC/OAuth2 — industry standard for healthcare
- Scales independently from Django
- One identity provider for future mobile apps, internal tools, partner integrations
- Django never stores passwords — reduced attack surface

### Why MinIO (not cloud S3 directly)?

- Local development parity with production (same S3 API)
- Cost control for staging/dev environments
- Self-hosted = data sovereignty compliance
- Production can swap to AWS S3 / GCP Cloud Storage without code changes (same `boto3` interface)
- Pre-signed URLs work identically

### Why Django Migrations (not Alembic)?

- `django-tenants` **requires** Django's migration framework — it hooks into `migrate_schemas` to run migrations per-schema
- Alembic is SQLAlchemy's tool; using both creates an unmaintainable dual-migration system
- Better tooling achieves the same goals: `django-migration-linter` catches unsafe migrations, squashing reduces file count, CI detects conflicts

### Why UUIDs as Primary Keys?

- No information leakage (sequential IDs reveal record count/creation rate)
- Safe for distributed systems / future microservice extraction
- Merge-safe across environments (dev → staging → prod)
- Slight index performance cost — acceptable tradeoff for healthcare security requirements

---

## Project Structure

```
medical/
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                 # Shared settings (installed apps, middleware, DB, etc.)
│   │   ├── development.py         # DEBUG=True, local MinIO, Keycloak dev realm
│   │   ├── staging.py            # Staging-specific overrides
│   │   └── production.py         # Production hardening (no DEBUG, strict CORS, etc.)
│   ├── urls.py                    # Root URL configuration
│   ├── wsgi.py                    # WSGI entry point
│   ├── asgi.py                    # ASGI entry point (future WebSocket support)
│   └── celery.py                  # Celery app configuration + task autodiscovery
│
├── apps/
│   ├── __init__.py
│   │
│   ├── accounts/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py             # CustomUser, UserSecrets, TenantMembership
│   │   ├── managers.py           # CustomUserManager
│   │   ├── backends.py           # KeycloakOIDCAuthenticationBackend
│   │   ├── serializers.py        # User, membership serializers
│   │   ├── views.py              # Auth views, user profile, membership management
│   │   ├── urls.py
│   │   ├── services.py           # User provisioning, role assignment logic
│   │   ├── permissions.py        # IsOwner, IsAdmin, IsDoctor, IsNurse, etc.
│   │   ├── signals.py            # Post-login hooks (update last_login, audit)
│   │   ├── admin.py
│   │   ├── migrations/
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_models.py
│   │       ├── test_services.py
│   │       ├── test_views.py
│   │       └── factories.py      # factory_boy factories
│   │
│   ├── tenants/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py             # Organization, TenantDomain
│   │   ├── serializers.py
│   │   ├── views.py              # Tenant CRUD, member invitation
│   │   ├── urls.py
│   │   ├── services.py           # Tenant provisioning (schema creation, defaults)
│   │   ├── middleware.py         # TenantResolutionMiddleware (subdomain/header)
│   │   ├── migrations/
│   │   └── tests/
│   │
│   ├── patients/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py             # Patient (tenant-scoped, single model)
│   │   ├── serializers.py
│   │   ├── views.py              # PatientViewSet (CRUD + search)
│   │   ├── urls.py
│   │   ├── services.py           # Registration, MRN generation, soft delete
│   │   ├── filters.py            # django-filter FilterSet
│   │   ├── migrations/
│   │   └── tests/
│   │
│   ├── appointments/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py             # Appointment
│   │   ├── serializers.py
│   │   ├── views.py              # AppointmentViewSet + available slots endpoint
│   │   ├── urls.py
│   │   ├── services.py           # Scheduling, conflict detection, status transitions
│   │   ├── filters.py            # By doctor, date range, status
│   │   ├── migrations/
│   │   └── tests/
│   │
│   ├── prescriptions/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py             # Prescription, PrescriptionItem, Medication
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── services.py           # Creation, dispensing, drug interaction check hook
│   │   ├── migrations/
│   │   └── tests/
│   │
│   ├── medical_records/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py             # Visit, Vitals, Diagnosis
│   │   ├── serializers.py
│   │   ├── views.py              # VisitViewSet + nested vitals/diagnoses
│   │   ├── urls.py
│   │   ├── services.py           # Visit creation, signing (locks record)
│   │   ├── migrations/
│   │   └── tests/
│   │
│   ├── lab_results/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py             # LabOrder, LabTest, TestResult
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── services.py           # Order creation, result entry, abnormal flagging
│   │   ├── migrations/
│   │   └── tests/
│   │
│   ├── billing/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py             # Invoice, InvoiceItem, Payment
│   │   ├── serializers.py
│   │   ├── views.py              # InvoiceViewSet, PaymentViewSet, summary endpoint
│   │   ├── urls.py
│   │   ├── services.py           # Invoice generation, payment recording, status calc
│   │   ├── migrations/
│   │   └── tests/
│   │
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py             # Notification, NotificationPreference
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── services.py           # Dispatch orchestration
│   │   ├── channels.py           # SMSChannel, EmailChannel, PushChannel adapters
│   │   ├── tasks.py              # Celery tasks for async delivery
│   │   ├── migrations/
│   │   └── tests/
│   │
│   ├── ai_integration/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py             # AIRequest
│   │   ├── serializers.py
│   │   ├── views.py              # Upload endpoints, status polling
│   │   ├── urls.py
│   │   ├── services.py           # Orchestration: upload → dispatch → save results
│   │   ├── clients.py            # AIServiceRESTClient, AIServiceMessagePublisher
│   │   ├── tasks.py              # Celery tasks: process_ai_request, handle_ai_result
│   │   ├── consumers.py          # RabbitMQ result queue consumer
│   │   ├── migrations/
│   │   └── tests/
│   │
│   └── audit/
│       ├── __init__.py
│       ├── apps.py
│       ├── models.py              # AuditLog (immutable, append-only)
│       ├── middleware.py          # RequestAuditMiddleware (captures context)
│       ├── signals.py             # post_save/post_delete → auto-log
│       ├── services.py            # AuditService.log() — single entry point
│       ├── migrations/
│       └── tests/
│
├── common/
│   ├── __init__.py
│   ├── models.py                  # BaseModel (created_at, updated_at, soft delete)
│   ├── mixins.py                  # SerializerMixins, ViewSetMixins
│   ├── pagination.py             # StandardResultsPagination (cursor + page-number)
│   ├── exceptions.py             # Custom DRF exception handler
│   ├── validators.py             # Phone, national ID, file size validators
│   ├── enums.py                  # Shared TextChoices/IntegerChoices
│   └── utils.py                  # generate_mrn(), encrypt_field(), etc.
│
├── docker/
│   ├── Dockerfile                 # Multi-stage build for Django app
│   ├── Dockerfile.celery          # Celery worker image
│   └── nginx/
│       └── nginx.conf             # Reverse proxy config
│
├── docker-compose.yml             # Development stack
├── docker-compose.prod.yml        # Production overrides
├── requirements/
│   ├── base.txt                   # Core dependencies
│   ├── development.txt            # Debug toolbar, ipdb, etc.
│   ├── production.txt             # gunicorn, gevent, etc.
│   └── testing.txt                # pytest, factory_boy, coverage
├── manage.py
├── pytest.ini
├── setup.cfg                      # flake8, isort, mypy config
├── .env.example                   # Template for environment variables
├── .pre-commit-config.yaml        # Pre-commit hooks
└── README.md
```

---

## Database Design

### Entity Relationship Overview

```
┌──────────────────────────── PUBLIC SCHEMA ────────────────────────────────┐
│                                                                           │
│  Organization ←──┐                                                        │
│       ↑          │                                                        │
│       │     TenantMembership ──→ User ←── UserSecrets                    │
│       │          │                ↑                                        │
│       │          └────────────────┘                                        │
│       │                                                                   │
│  AuditLog (references Organization + User)                               │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────── TENANT SCHEMA ────────────────────────────────┐
│                                                                           │
│  DoctorProfile (→ User in public)                                        │
│       │                                                                   │
│       ├──→ Appointment ←── Patient                                        │
│       │         │              │                                           │
│       │         ↓              ├──→ Prescription ──→ PrescriptionItem     │
│       │       Visit            │         │              │                  │
│       │         │              │         └──────── Medication              │
│       │         ├── Vitals     │                                           │
│       │         ├── Diagnosis  ├──→ LabOrder ──→ LabTest ──→ TestResult   │
│       │         │              │                                           │
│       │         └──────────────├──→ Invoice ──→ InvoiceItem               │
│       │                        │         │                                 │
│       │                        │      Payment                              │
│       │                        │                                           │
│       └────────────────────────├──→ AIRequest                             │
│                                │                                           │
│                             Notification                                   │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

### Public Schema Models

#### Organization (Tenant)

```python
# apps/tenants/models.py
class Organization(TenantMixin):
    """
    Each clinic/hospital/lab is an Organization with its own PostgreSQL schema.
    TenantMixin from django-tenants provides schema_name and domain handling.
    """
    id = UUIDField(primary_key=True, default=uuid4)
    name = CharField(max_length=255)
    slug = SlugField(max_length=100, unique=True)
    type = CharField(choices=OrganizationType.choices)  # clinic, hospital, lab
    license_number = CharField(max_length=100)
    address = TextField(blank=True)
    phone = CharField(max_length=20)
    email = EmailField()
    is_active = BooleanField(default=True)
    subscription_plan = CharField(choices=SubscriptionPlan.choices, default='free')
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    # django-tenants required
    auto_create_schema = True
```

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| name | varchar(255) | NOT NULL | |
| slug | varchar(100) | UNIQUE, NOT NULL | ✓ |
| schema_name | varchar(63) | UNIQUE, NOT NULL | ✓ (django-tenants) |
| type | varchar(20) | enum: clinic, hospital, lab | |
| license_number | varchar(100) | NOT NULL | |
| address | text | | |
| phone | varchar(20) | NOT NULL | |
| email | varchar(255) | NOT NULL | |
| is_active | boolean | DEFAULT true | |
| subscription_plan | varchar(20) | DEFAULT 'free' | |
| created_at | timestamptz | auto | |
| updated_at | timestamptz | auto | |

---

#### User (CustomUser)

```python
# apps/accounts/models.py
class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model. Authentication handled by Keycloak.
    This model stores identity + maps to Keycloak subject.
    Django never stores/validates passwords directly.
    """
    id = UUIDField(primary_key=True, default=uuid4)
    keycloak_id = UUIDField(unique=True, db_index=True)
    email = EmailField(unique=True)
    phone = CharField(max_length=20, unique=True, null=True, blank=True)
    first_name = CharField(max_length=150)
    last_name = CharField(max_length=150)
    national_id = EncryptedCharField(max_length=50, null=True, blank=True)
    is_active = BooleanField(default=True)
    is_staff = BooleanField(default=False)
    date_joined = DateTimeField(auto_now_add=True)
    last_login = DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    objects = CustomUserManager()
```

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| keycloak_id | UUID | UNIQUE, NOT NULL | ✓ |
| email | varchar(255) | UNIQUE, NOT NULL | ✓ |
| phone | varchar(20) | UNIQUE, NULLABLE | ✓ |
| first_name | varchar(150) | NOT NULL | |
| last_name | varchar(150) | NOT NULL | |
| national_id | encrypted varchar(50) | NULLABLE | |
| is_active | boolean | DEFAULT true | |
| is_staff | boolean | DEFAULT false | |
| date_joined | timestamptz | auto | |
| last_login | timestamptz | NULLABLE | |

---

#### UserSecrets

```python
# apps/accounts/models.py
class UserSecrets(models.Model):
    """
    Application-level secrets for a user. NOT Keycloak credentials.
    - api_key_hash: service-to-service auth (non-OIDC clients)
    - pin_hash: quick-access PIN for clinical workflows
    - mfa_backup_codes: encrypted backup codes
    - refresh_token: encrypted, for background jobs acting on behalf of user
    """
    id = UUIDField(primary_key=True, default=uuid4)
    user = OneToOneField(User, on_delete=CASCADE, related_name='secrets')
    api_key_hash = CharField(max_length=128, null=True, blank=True)
    refresh_token_encrypted = TextField(null=True, blank=True)
    mfa_backup_codes_encrypted = TextField(null=True, blank=True)
    pin_hash = CharField(max_length=128, null=True, blank=True)
    last_rotated_at = DateTimeField(null=True, blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| user_id | UUID FK → User | UNIQUE (OneToOne) | ✓ |
| api_key_hash | varchar(128) | NULLABLE | |
| refresh_token_encrypted | text | NULLABLE | |
| mfa_backup_codes_encrypted | text | NULLABLE | |
| pin_hash | varchar(128) | NULLABLE | |
| last_rotated_at | timestamptz | NULLABLE | |
| created_at | timestamptz | auto | |
| updated_at | timestamptz | auto | |

---

#### TenantMembership

```python
# apps/accounts/models.py
class TenantMembership(models.Model):
    """Maps a user to a tenant with a specific role."""
    id = UUIDField(primary_key=True, default=uuid4)
    user = ForeignKey(User, on_delete=CASCADE, related_name='memberships')
    tenant = ForeignKey(Organization, on_delete=CASCADE, related_name='memberships')
    role = CharField(max_length=20, choices=UserRole.choices)
    is_active = BooleanField(default=True)
    joined_at = DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'tenant')
```

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| user_id | UUID FK → User | NOT NULL | ✓ (composite) |
| tenant_id | UUID FK → Organization | NOT NULL | ✓ (composite) |
| role | varchar(20) | enum: owner, admin, doctor, nurse, receptionist, lab_tech, billing_staff | |
| is_active | boolean | DEFAULT true | |
| joined_at | timestamptz | auto | |
| | | UNIQUE(user_id, tenant_id) | ✓ |

---

#### AuditLog

```python
# apps/audit/models.py
class AuditLog(models.Model):
    """
    Immutable, append-only audit trail. Partitioned by month.
    No update or delete operations are ever exposed.
    """
    id = BigAutoField(primary_key=True)
    tenant_id = UUIDField(null=True, db_index=True)
    user_id = UUIDField(null=True, db_index=True)
    action = CharField(max_length=20, choices=AuditAction.choices)
    resource_type = CharField(max_length=100)
    resource_id = CharField(max_length=100)
    changes = JSONField(null=True, blank=True)  # {"before": {...}, "after": {...}}
    ip_address = GenericIPAddressField(null=True)
    user_agent = TextField(null=True, blank=True)
    timestamp = DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            Index(fields=['tenant_id', 'timestamp']),
            Index(fields=['user_id', 'timestamp']),
            Index(fields=['resource_type', 'resource_id']),
        ]
        # Partition by range on timestamp (configured via raw SQL migration)
```

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | BIGINT | PK, auto-increment | ✓ (PK) |
| tenant_id | UUID | NULLABLE | ✓ (composite with timestamp) |
| user_id | UUID | NULLABLE | ✓ (composite with timestamp) |
| action | varchar(20) | enum: create, read, update, delete, login, logout, export | |
| resource_type | varchar(100) | NOT NULL | ✓ (composite with resource_id) |
| resource_id | varchar(100) | NOT NULL | ✓ (composite with resource_type) |
| changes | jsonb | NULLABLE | |
| ip_address | inet | NULLABLE | |
| user_agent | text | NULLABLE | |
| timestamp | timestamptz | auto | |
| | | **PARTITION BY RANGE (timestamp)** — monthly partitions | |

---

### Tenant Schema Models

#### DoctorProfile

```python
# apps/accounts/models.py (tenant app)
class DoctorProfile(BaseModel):
    """Doctor-specific profile within a tenant. Links to User in public schema."""
    user_id = UUIDField(db_index=True)  # References User.id in public schema
    specialization = CharField(max_length=200)
    license_number = CharField(max_length=100)
    qualification = TextField()
    years_of_experience = PositiveIntegerField()
    consultation_fee = DecimalField(max_digits=10, decimal_places=2)
    bio = TextField(null=True, blank=True)
    is_available = BooleanField(default=True)
```

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| user_id | UUID | NOT NULL (logical FK to public.User) | ✓ |
| specialization | varchar(200) | NOT NULL | ✓ |
| license_number | varchar(100) | NOT NULL | |
| qualification | text | NOT NULL | |
| years_of_experience | int | NOT NULL, >= 0 | |
| consultation_fee | decimal(10,2) | NOT NULL | |
| bio | text | NULLABLE | |
| is_available | boolean | DEFAULT true | |
| created_at | timestamptz | auto (from BaseModel) | |
| updated_at | timestamptz | auto (from BaseModel) | |

> **Note**: `user_id` is a UUID field, not a Django ForeignKey, because it references the public schema. Cross-schema FKs are not supported by PostgreSQL. Resolution is done at the application/service layer.

---

#### Patient

```python
# apps/patients/models.py
class Patient(BaseModel):
    """
    Patient record scoped entirely to this tenant.
    Contains both identity and clinical profile information.
    Supports soft delete via deleted_at field.
    """
    medical_record_number = CharField(max_length=50, unique=True)
    first_name = CharField(max_length=150)
    last_name = CharField(max_length=150)
    date_of_birth = DateField()
    gender = CharField(max_length=10, choices=Gender.choices)
    national_id = EncryptedCharField(max_length=50, null=True, blank=True)
    blood_type = CharField(max_length=5, null=True, blank=True)
    phone = CharField(max_length=20)
    email = EmailField(null=True, blank=True)
    address = TextField(null=True, blank=True)
    emergency_contact_name = CharField(max_length=255, blank=True)
    emergency_contact_phone = CharField(max_length=20, blank=True)
    allergies = JSONField(default=list)
    chronic_conditions = JSONField(default=list)
    insurance_provider = CharField(max_length=200, null=True, blank=True)
    insurance_number = CharField(max_length=100, null=True, blank=True)
    notes = TextField(null=True, blank=True)
    registered_at = DateTimeField(auto_now_add=True)
    is_active = BooleanField(default=True)
    deleted_at = DateTimeField(null=True, blank=True)  # Soft delete

    class Meta:
        indexes = [
            Index(fields=['national_id']),
            Index(fields=['phone']),
            Index(fields=['last_name', 'first_name', 'date_of_birth']),
            Index(fields=['medical_record_number']),
        ]
```

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| medical_record_number | varchar(50) | UNIQUE, NOT NULL | ✓ |
| first_name | varchar(150) | NOT NULL | ✓ (composite) |
| last_name | varchar(150) | NOT NULL | ✓ (composite) |
| date_of_birth | date | NOT NULL | ✓ (composite) |
| gender | varchar(10) | enum: male, female, other | |
| national_id | encrypted varchar(50) | NULLABLE | ✓ |
| blood_type | varchar(5) | NULLABLE | |
| phone | varchar(20) | NOT NULL | ✓ |
| email | varchar(255) | NULLABLE | |
| address | text | NULLABLE | |
| emergency_contact_name | varchar(255) | | |
| emergency_contact_phone | varchar(20) | | |
| allergies | jsonb | DEFAULT [] | GIN index |
| chronic_conditions | jsonb | DEFAULT [] | GIN index |
| insurance_provider | varchar(200) | NULLABLE | |
| insurance_number | varchar(100) | NULLABLE | |
| notes | text | NULLABLE | |
| registered_at | timestamptz | auto | |
| is_active | boolean | DEFAULT true | |
| deleted_at | timestamptz | NULLABLE (soft delete) | |
| created_at | timestamptz | auto | |
| updated_at | timestamptz | auto | |

---

#### Appointment

```python
# apps/appointments/models.py
class Appointment(BaseModel):
    """
    Appointment between a patient and doctor.
    Uses PostgreSQL exclusion constraint to prevent double-booking.
    """
    patient = ForeignKey(Patient, on_delete=PROTECT, related_name='appointments')
    doctor = ForeignKey(DoctorProfile, on_delete=PROTECT, related_name='appointments')
    scheduled_at = DateTimeField()
    duration_minutes = PositiveIntegerField(default=30)
    status = CharField(max_length=20, choices=AppointmentStatus.choices, default='scheduled')
    type = CharField(max_length=20, choices=AppointmentType.choices, default='in_person')
    reason = TextField(null=True, blank=True)
    cancellation_reason = TextField(null=True, blank=True)
    cancelled_by_id = UUIDField(null=True, blank=True)  # User who cancelled

    class Meta:
        indexes = [
            Index(fields=['doctor', 'scheduled_at']),
            Index(fields=['patient', 'scheduled_at']),
            Index(fields=['status', 'scheduled_at']),
        ]
        # Exclusion constraint added via migration (prevents overlapping appointments per doctor)
```

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| patient_id | UUID FK → Patient | NOT NULL, PROTECT | |
| doctor_id | UUID FK → DoctorProfile | NOT NULL, PROTECT | ✓ (composite with scheduled_at) |
| scheduled_at | timestamptz | NOT NULL | ✓ |
| duration_minutes | int | NOT NULL, DEFAULT 30 | |
| status | varchar(20) | enum: scheduled, confirmed, in_progress, completed, cancelled, no_show | ✓ (composite with scheduled_at) |
| type | varchar(20) | enum: in_person, telehealth | |
| reason | text | NULLABLE | |
| cancellation_reason | text | NULLABLE | |
| cancelled_by_id | UUID | NULLABLE | |
| created_at | timestamptz | auto | |
| updated_at | timestamptz | auto | |
| | | **EXCLUSION CONSTRAINT**: no overlapping per doctor | |

**Exclusion Constraint** (raw SQL in migration):
```sql
ALTER TABLE appointments_appointment
ADD CONSTRAINT no_overlapping_appointments
EXCLUDE USING gist (
    doctor_id WITH =,
    tstzrange(scheduled_at, scheduled_at + (duration_minutes || ' minutes')::interval) WITH &&
) WHERE (status NOT IN ('cancelled', 'no_show'));
```

---

#### Visit (Medical Record)

```python
# apps/medical_records/models.py
class Visit(BaseModel):
    """
    A clinical visit/encounter. Becomes immutable once signed by doctor.
    SOAP format: Subjective (chief_complaint, HPI), Objective (vitals, exam),
    Assessment (diagnoses), Plan (prescriptions, follow-up).
    """
    appointment = ForeignKey('appointments.Appointment', null=True, blank=True,
                            on_delete=SET_NULL, related_name='visits')
    patient = ForeignKey(Patient, on_delete=PROTECT, related_name='visits')
    doctor = ForeignKey(DoctorProfile, on_delete=PROTECT, related_name='visits')
    visit_date = DateTimeField()
    chief_complaint = TextField()
    history_of_present_illness = TextField(null=True, blank=True)
    examination_notes = TextField(null=True, blank=True)
    assessment = TextField(null=True, blank=True)
    plan = TextField(null=True, blank=True)
    follow_up_date = DateField(null=True, blank=True)
    is_signed = BooleanField(default=False)
    signed_at = DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            Index(fields=['patient', 'visit_date']),
            Index(fields=['doctor', 'visit_date']),
        ]
```

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| appointment_id | UUID FK → Appointment | NULLABLE, SET_NULL | |
| patient_id | UUID FK → Patient | NOT NULL, PROTECT | ✓ (composite) |
| doctor_id | UUID FK → DoctorProfile | NOT NULL, PROTECT | ✓ (composite) |
| visit_date | timestamptz | NOT NULL | ✓ (in composites) |
| chief_complaint | text | NOT NULL | |
| history_of_present_illness | text | NULLABLE | |
| examination_notes | text | NULLABLE | |
| assessment | text | NULLABLE | |
| plan | text | NULLABLE | |
| follow_up_date | date | NULLABLE | |
| is_signed | boolean | DEFAULT false | |
| signed_at | timestamptz | NULLABLE | |
| created_at | timestamptz | auto | |
| updated_at | timestamptz | auto | |

---

#### Vitals

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| visit_id | UUID FK → Visit | NOT NULL, CASCADE | |
| blood_pressure_systolic | int | NULLABLE | |
| blood_pressure_diastolic | int | NULLABLE | |
| heart_rate | int | NULLABLE | |
| temperature | decimal(4,1) | NULLABLE (°C) | |
| respiratory_rate | int | NULLABLE | |
| oxygen_saturation | decimal(4,1) | NULLABLE (%) | |
| weight_kg | decimal(5,2) | NULLABLE | |
| height_cm | decimal(5,1) | NULLABLE | |
| recorded_at | timestamptz | NOT NULL | |
| recorded_by_id | UUID | NOT NULL (User ref) | |

---

#### Diagnosis

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| visit_id | UUID FK → Visit | NOT NULL, CASCADE | ✓ |
| icd_code | varchar(20) | NOT NULL (ICD-10/11) | ✓ |
| description | text | NOT NULL | |
| type | varchar(20) | enum: primary, secondary, rule_out | |
| notes | text | NULLABLE | |
| created_at | timestamptz | auto | |

---

#### Medication (Reference Table)

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| name | varchar(255) | NOT NULL | ✓ |
| generic_name | varchar(255) | NOT NULL | ✓ |
| form | varchar(20) | enum: tablet, capsule, syrup, injection, cream, drops, inhaler | |
| strength | varchar(50) | NOT NULL | |
| manufacturer | varchar(200) | NULLABLE | |
| is_active | boolean | DEFAULT true | |

---

#### Prescription

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| visit_id | UUID FK → Visit | NULLABLE | |
| patient_id | UUID FK → Patient | NOT NULL | ✓ (composite) |
| doctor_id | UUID FK → DoctorProfile | NOT NULL | |
| prescribed_at | timestamptz | NOT NULL | ✓ (in composite) |
| notes | text | NULLABLE | |
| is_dispensed | boolean | DEFAULT false | |
| dispensed_at | timestamptz | NULLABLE | |
| created_at | timestamptz | auto | |
| updated_at | timestamptz | auto | |

---

#### PrescriptionItem

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| prescription_id | UUID FK → Prescription | NOT NULL, CASCADE | |
| medication_id | UUID FK → Medication | NOT NULL, PROTECT | |
| dosage | varchar(100) | NOT NULL (e.g., "500mg") | |
| frequency | varchar(100) | NOT NULL (e.g., "twice daily") | |
| duration | varchar(100) | NOT NULL (e.g., "7 days") | |
| route | varchar(20) | enum: oral, iv, im, topical, sublingual, inhalation | |
| quantity | int | NOT NULL | |
| instructions | text | NULLABLE (e.g., "after meals") | |
| is_prn | boolean | DEFAULT false (as-needed basis) | |

---

#### LabOrder

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| visit_id | UUID FK → Visit | NULLABLE | |
| patient_id | UUID FK → Patient | NOT NULL | ✓ (composite) |
| ordered_by_id | UUID FK → DoctorProfile | NOT NULL | |
| ordered_at | timestamptz | NOT NULL | ✓ (in composite) |
| status | varchar(20) | enum: ordered, sample_collected, processing, completed, cancelled | ✓ |
| priority | varchar(10) | enum: routine, urgent, stat | |
| notes | text | NULLABLE | |
| created_at | timestamptz | auto | |
| updated_at | timestamptz | auto | |

---

#### LabTest

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| lab_order_id | UUID FK → LabOrder | NOT NULL, CASCADE | |
| test_name | varchar(255) | NOT NULL | |
| test_code | varchar(50) | NOT NULL (LOINC code) | ✓ |
| category | varchar(100) | NOT NULL (e.g., "hematology") | |

---

#### TestResult

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| lab_test_id | UUID FK → LabTest | NOT NULL, CASCADE | |
| value | varchar(100) | NOT NULL | |
| unit | varchar(50) | NOT NULL | |
| reference_range_low | decimal(10,4) | NULLABLE | |
| reference_range_high | decimal(10,4) | NULLABLE | |
| is_abnormal | boolean | DEFAULT false | ✓ |
| flag | varchar(10) | enum: normal, low, high, critical | |
| performed_by_id | UUID | NULLABLE (User ref) | |
| resulted_at | timestamptz | NOT NULL | |
| verified_by_id | UUID | NULLABLE (User ref) | |
| verified_at | timestamptz | NULLABLE | |
| notes | text | NULLABLE | |

---

#### Invoice

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| invoice_number | varchar(50) | UNIQUE, NOT NULL | ✓ |
| patient_id | UUID FK → Patient | NOT NULL | ✓ (composite) |
| visit_id | UUID FK → Visit | NULLABLE | |
| issued_at | timestamptz | NOT NULL | |
| due_date | date | NOT NULL | ✓ (composite with status) |
| subtotal | decimal(12,2) | NOT NULL | |
| tax_amount | decimal(12,2) | DEFAULT 0 | |
| discount_amount | decimal(12,2) | DEFAULT 0 | |
| total_amount | decimal(12,2) | NOT NULL | |
| paid_amount | decimal(12,2) | DEFAULT 0 | |
| status | varchar(20) | enum: draft, issued, partially_paid, paid, overdue, cancelled | ✓ |
| notes | text | NULLABLE | |
| created_at | timestamptz | auto | |
| updated_at | timestamptz | auto | |

---

#### InvoiceItem

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| invoice_id | UUID FK → Invoice | NOT NULL, CASCADE | |
| description | varchar(500) | NOT NULL | |
| item_type | varchar(20) | enum: consultation, procedure, lab_test, medication, other | |
| quantity | int | DEFAULT 1 | |
| unit_price | decimal(10,2) | NOT NULL | |
| total_price | decimal(10,2) | NOT NULL | |
| reference_id | UUID | NULLABLE (polymorphic link) | |
| reference_type | varchar(50) | NULLABLE (e.g., "appointment", "lab_order") | |

---

#### Payment

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| invoice_id | UUID FK → Invoice | NOT NULL | ✓ |
| amount | decimal(12,2) | NOT NULL | |
| method | varchar(20) | enum: cash, card, insurance, bank_transfer, online | |
| transaction_ref | varchar(200) | NULLABLE | |
| paid_at | timestamptz | NOT NULL | ✓ |
| received_by_id | UUID | NOT NULL (User ref) | |
| notes | text | NULLABLE | |
| created_at | timestamptz | auto | |

---

#### AIRequest

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| request_type | varchar(20) | enum: prescription_ocr, lab_analysis, radiology | ✓ (composite) |
| patient_id | UUID FK → Patient | NULLABLE | ✓ |
| requested_by_id | UUID | NOT NULL (User ref) | |
| input_file | varchar(500) | NOT NULL (MinIO object path) | |
| input_metadata | jsonb | DEFAULT {} | |
| status | varchar(20) | enum: pending, processing, completed, failed, retrying | ✓ |
| result | jsonb | NULLABLE | |
| error_message | text | NULLABLE | |
| retry_count | int | DEFAULT 0 | |
| max_retries | int | DEFAULT 3 | |
| celery_task_id | varchar(255) | NULLABLE | |
| started_at | timestamptz | NULLABLE | |
| completed_at | timestamptz | NULLABLE | |
| created_at | timestamptz | auto | |
| updated_at | timestamptz | auto | |

---

#### Notification

| Field | Type | Constraints | Index |
|-------|------|-------------|-------|
| id | UUID | PK | ✓ (PK) |
| user_id | UUID | NOT NULL (User ref) | ✓ (composite) |
| title | varchar(255) | NOT NULL | |
| message | text | NOT NULL | |
| type | varchar(30) | enum: appointment_reminder, lab_result, prescription, billing, system | |
| channel | varchar(10) | enum: in_app, sms, email, push | |
| is_read | boolean | DEFAULT false | ✓ (composite) |
| read_at | timestamptz | NULLABLE | |
| metadata | jsonb | DEFAULT {} | |
| created_at | timestamptz | auto | ✓ (composite) |

**Composite Index**: `(user_id, is_read, created_at DESC)` — optimizes "unread notifications" query.

---

### Base Model (inherited by all tenant models)

```python
# common/models.py
class BaseModel(models.Model):
    """Abstract base providing timestamps and soft delete."""
    id = UUIDField(primary_key=True, default=uuid4, editable=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModel(BaseModel):
    """Extends BaseModel with soft delete support."""
    is_active = BooleanField(default=True)
    deleted_at = DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_active', 'deleted_at', 'updated_at'])
```

---

## Authentication & Authorization (Keycloak)

### Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Client    │────→│   Keycloak   │────→│   Django API    │
│ (Frontend/  │     │   (OIDC)     │     │   (Validates    │
│  Mobile)    │←────│              │     │    JWT token)   │
└─────────────┘     └──────────────┘     └─────────────────┘
      │                                          │
      │  Authorization: Bearer <access_token>    │
      └──────────────────────────────────────────┘
```

### Flow

1. **User authenticates** against Keycloak (login page, API, or social login)
2. **Keycloak issues** `access_token` (JWT, 15-min TTL) + `refresh_token` (7-day TTL)
3. **Client sends** `Authorization: Bearer <access_token>` with every API request
4. **Django middleware** validates token:
   - Verifies signature against Keycloak's JWKS endpoint (public keys cached in Redis)
   - Checks `exp`, `iss`, `aud` claims
   - Extracts `sub` (Keycloak user ID)
5. **Maps `keycloak_id` → `User`** record in public schema
6. **Auto-provisioning**: If `keycloak_id` not found, creates `User` record from token claims
7. **Tenant context**: Request header `X-Tenant-Slug` or subdomain resolves active tenant
8. **RBAC**: `TenantMembership` determines role within tenant → permission classes enforce access

### Keycloak Configuration

```
Realm: healthcare-saas
Clients:
  - web-app (public, PKCE flow)
  - mobile-app (public, PKCE flow)
  - service-account (confidential, client_credentials for Celery/background jobs)

Roles (Keycloak realm roles — mapped to TenantMembership):
  - Not used for RBAC (kept in Django for flexibility)
  - Keycloak handles: authentication, MFA, password policy, session management

Custom Token Claims (via mapper):
  - email, first_name, last_name, phone (for auto-provisioning)
```

### Django Authentication Backend

```python
# apps/accounts/backends.py
class KeycloakOIDCBackend:
    """
    Validates Keycloak JWT tokens and maps to Django User.
    Uses cached JWKS for signature verification (no round-trip per request).
    """
    def authenticate(self, request, token=None):
        # 1. Decode + verify token signature (cached JWKS from Redis)
        # 2. Validate claims (exp, iss, aud)
        # 3. Extract keycloak_id from 'sub' claim
        # 4. Lookup User by keycloak_id
        # 5. If not found: auto-provision from token claims
        # 6. Return User instance
        pass
```

### UserSecrets Usage

| Secret | Purpose | When Used |
|--------|---------|-----------|
| `api_key_hash` | Service-to-service auth | External systems calling Django API without OIDC |
| `pin_hash` | Quick-access clinical PIN | Doctor confirming prescription (4-6 digit PIN instead of full re-auth) |
| `mfa_backup_codes_encrypted` | MFA recovery | Stored encrypted, decrypted only during MFA recovery flow |
| `refresh_token_encrypted` | Background job delegation | Celery tasks acting on behalf of user (e.g., sending notifications) |

### Permission Classes

```python
# apps/accounts/permissions.py
class IsTenantMember(BasePermission):
    """User must be an active member of the current tenant."""

class HasRole(BasePermission):
    """User must have one of the specified roles in current tenant."""
    def __init__(self, *allowed_roles):
        self.allowed_roles = allowed_roles

class IsDoctor(HasRole('doctor', 'owner', 'admin')):
    """Access restricted to doctors (and admins)."""

class IsNurse(HasRole('nurse', 'doctor', 'owner', 'admin')):
    """Access for nursing staff and above."""

class IsReceptionist(HasRole('receptionist', 'nurse', 'doctor', 'owner', 'admin')):
    """Access for reception and above."""

class IsLabTech(HasRole('lab_tech', 'doctor', 'owner', 'admin')):
    """Access for lab technicians and above."""

class IsBillingStaff(HasRole('billing_staff', 'owner', 'admin')):
    """Access for billing department."""

class IsOwnerOrAdmin(HasRole('owner', 'admin')):
    """Full tenant management access."""
```

---

## API Design

### Base URL Pattern

```
https://{tenant-slug}.api.healthsaas.com/api/v1/
```

Or with header-based tenant resolution:
```
https://api.healthsaas.com/api/v1/
Header: X-Tenant-Slug: clinic-abc
```

### Pagination (all list endpoints)

```json
{
  "count": 142,
  "next": "https://api.healthsaas.com/api/v1/patients/?cursor=cD0yMDI0",
  "previous": null,
  "results": [...]
}
```

Default: 25 items per page. Max: 100. Supports cursor-based and page-number pagination.

---

### Authentication Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/token/` | None | Exchange Keycloak token for session (optional — for cookie-based sessions) |
| GET | `/api/v1/auth/me/` | Required | Current user profile + tenant memberships |
| POST | `/api/v1/auth/verify-pin/` | Required | Verify clinical PIN for sensitive actions |
| POST | `/api/v1/auth/api-keys/` | Admin | Generate API key (stored hashed in UserSecrets) |
| DELETE | `/api/v1/auth/api-keys/{id}/` | Admin | Revoke API key |

---

### Tenant Management

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/tenants/` | Any authenticated | Create new organization (creator becomes owner) |
| GET | `/api/v1/tenants/` | Any authenticated | List user's organizations |
| GET | `/api/v1/tenants/{slug}/` | Member | Organization detail |
| PATCH | `/api/v1/tenants/{slug}/` | Owner/Admin | Update organization settings |
| POST | `/api/v1/tenants/{slug}/invite/` | Owner/Admin | Invite user by email (assigns role) |
| GET | `/api/v1/tenants/{slug}/members/` | Owner/Admin | List members |
| PATCH | `/api/v1/tenants/{slug}/members/{id}/` | Owner/Admin | Update member role |
| DELETE | `/api/v1/tenants/{slug}/members/{id}/` | Owner | Remove member |

---

### Patients (Tenant-Scoped)

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/patients/` | Receptionist+ | List patients (paginated) |
| POST | `/api/v1/patients/` | Receptionist+ | Register new patient |
| GET | `/api/v1/patients/{id}/` | Nurse+ | Patient detail |
| PATCH | `/api/v1/patients/{id}/` | Receptionist+ | Update patient info |
| DELETE | `/api/v1/patients/{id}/` | Admin | Soft delete patient |
| GET | `/api/v1/patients/{id}/visits/` | Doctor | Full visit history |
| GET | `/api/v1/patients/{id}/prescriptions/` | Doctor | All prescriptions |
| GET | `/api/v1/patients/{id}/lab-results/` | Doctor/LabTech | Lab result history |
| GET | `/api/v1/patients/{id}/invoices/` | Billing+ | Billing history |

**Filters**: `?search=<name/phone/mrn>`, `?blood_type=A+`, `?gender=male`, `?registered_after=2024-01-01`, `?is_active=true`

**Ordering**: `?ordering=-registered_at`, `?ordering=last_name`

---

### Appointments

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/appointments/` | Receptionist+ | List appointments |
| POST | `/api/v1/appointments/` | Receptionist+ | Book appointment |
| GET | `/api/v1/appointments/{id}/` | Receptionist+ | Appointment detail |
| PATCH | `/api/v1/appointments/{id}/` | Receptionist+ | Reschedule (change time/doctor) |
| POST | `/api/v1/appointments/{id}/confirm/` | Receptionist+ | Confirm appointment |
| POST | `/api/v1/appointments/{id}/start/` | Doctor/Nurse | Mark in-progress |
| POST | `/api/v1/appointments/{id}/complete/` | Doctor | Mark completed |
| POST | `/api/v1/appointments/{id}/cancel/` | Receptionist+ | Cancel with reason |
| POST | `/api/v1/appointments/{id}/no-show/` | Receptionist+ | Mark no-show |
| GET | `/api/v1/appointments/available-slots/` | Receptionist+ | Get available time slots |

**Filters**: `?doctor={id}`, `?patient={id}`, `?date=2024-06-01`, `?date_from=...&date_to=...`, `?status=scheduled`

**Available Slots Query Params**: `?doctor={id}&date=2024-06-01&duration=30`

**Status Transitions** (enforced in service layer):
```
scheduled → confirmed → in_progress → completed
scheduled → cancelled
confirmed → cancelled
scheduled → no_show
confirmed → no_show
```

---

### Medical Records (Visits)

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/visits/` | Doctor | List visits |
| POST | `/api/v1/visits/` | Doctor | Create visit record |
| GET | `/api/v1/visits/{id}/` | Doctor | Full visit detail (includes vitals, diagnoses) |
| PATCH | `/api/v1/visits/{id}/` | Doctor | Update visit (only if unsigned) |
| POST | `/api/v1/visits/{id}/sign/` | Doctor | Sign and lock record |
| POST | `/api/v1/visits/{id}/vitals/` | Nurse/Doctor | Record vitals |
| GET | `/api/v1/visits/{id}/vitals/` | Nurse/Doctor | Get vitals |
| POST | `/api/v1/visits/{id}/diagnoses/` | Doctor | Add diagnosis |
| GET | `/api/v1/visits/{id}/diagnoses/` | Doctor | List diagnoses |

**Business Rule**: Once `is_signed = true`, the visit record is immutable. No updates allowed. An addendum mechanism can be added later.

---

### Prescriptions

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/prescriptions/` | Doctor | List prescriptions |
| POST | `/api/v1/prescriptions/` | Doctor | Create prescription with items |
| GET | `/api/v1/prescriptions/{id}/` | Doctor | Detail with medication list |
| PATCH | `/api/v1/prescriptions/{id}/` | Doctor | Update (only if not dispensed) |
| POST | `/api/v1/prescriptions/{id}/dispense/` | Nurse/Receptionist | Mark as dispensed |

**Request Body (Create)**:
```json
{
  "patient_id": "uuid",
  "visit_id": "uuid (optional)",
  "notes": "Take with plenty of water",
  "items": [
    {
      "medication_id": "uuid",
      "dosage": "500mg",
      "frequency": "twice daily",
      "duration": "7 days",
      "route": "oral",
      "quantity": 14,
      "instructions": "after meals",
      "is_prn": false
    }
  ]
}
```

---

### Lab Results

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/lab-orders/` | Doctor/LabTech | List lab orders |
| POST | `/api/v1/lab-orders/` | Doctor | Create lab order with tests |
| GET | `/api/v1/lab-orders/{id}/` | Doctor/LabTech | Order detail + results |
| PATCH | `/api/v1/lab-orders/{id}/status/` | LabTech | Update status (sample_collected → processing → completed) |
| POST | `/api/v1/lab-orders/{id}/results/` | LabTech | Submit test results |
| GET | `/api/v1/lab-orders/{id}/results/` | Doctor/LabTech | Get test results |
| POST | `/api/v1/lab-orders/{id}/results/{result_id}/verify/` | Doctor | Verify/approve result |

**Auto-flagging**: When `TestResult.value` is outside `reference_range_low`/`reference_range_high`, `is_abnormal` is set to `true` and `flag` is computed automatically in the service layer.

---

### Billing

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/invoices/` | Billing+ | List invoices |
| POST | `/api/v1/invoices/` | Billing+ | Create invoice |
| GET | `/api/v1/invoices/{id}/` | Billing+ | Invoice detail with items + payments |
| PATCH | `/api/v1/invoices/{id}/` | Billing+ | Update draft invoice |
| POST | `/api/v1/invoices/{id}/issue/` | Billing+ | Issue invoice (draft → issued) |
| POST | `/api/v1/invoices/{id}/payments/` | Billing+ | Record payment |
| GET | `/api/v1/billing/summary/` | Admin | Revenue dashboard (date range, totals) |

**Filters**: `?status=overdue`, `?patient={id}`, `?date_from=...&date_to=...`

**Auto-status**: When `paid_amount >= total_amount` → status becomes `paid`. When `paid_amount > 0` but less → `partially_paid`. Cron job marks `overdue` when `due_date < today` and not fully paid.

---

### AI Integration

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/ai/prescription-scan/` | Doctor/Nurse | Upload prescription image for OCR |
| POST | `/api/v1/ai/lab-analysis/` | Doctor/LabTech | Submit lab results for AI analysis |
| GET | `/api/v1/ai/requests/` | Doctor+ | List AI processing requests |
| GET | `/api/v1/ai/requests/{id}/` | Doctor+ | Get processing status + results |
| POST | `/api/v1/ai/requests/{id}/retry/` | Doctor+ | Retry failed request |
| POST | `/api/v1/ai/requests/{id}/accept/` | Doctor | Accept AI results (creates records) |

---

### Notifications

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/notifications/` | Any | User's notifications (paginated, newest first) |
| PATCH | `/api/v1/notifications/{id}/read/` | Any | Mark single as read |
| POST | `/api/v1/notifications/mark-all-read/` | Any | Mark all as read |
| GET | `/api/v1/notifications/unread-count/` | Any | Get unread count |
| GET | `/api/v1/notifications/preferences/` | Any | Get notification preferences |
| PATCH | `/api/v1/notifications/preferences/` | Any | Update preferences |

---

### Common Response Formats

**Success (single resource)**:
```json
{
  "id": "uuid",
  "field": "value",
  "created_at": "2024-06-01T10:30:00Z",
  "updated_at": "2024-06-01T10:30:00Z"
}
```

**Success (list)**:
```json
{
  "count": 42,
  "next": "...?cursor=abc",
  "previous": null,
  "results": [...]
}
```

**Error**:
```json
{
  "error": {
    "code": "APPOINTMENT_CONFLICT",
    "message": "Doctor already has an appointment at this time.",
    "details": {
      "conflicting_appointment_id": "uuid",
      "scheduled_at": "2024-06-01T10:00:00Z"
    }
  }
}
```

**Validation Error**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input.",
    "fields": {
      "email": ["Enter a valid email address."],
      "date_of_birth": ["Date cannot be in the future."]
    }
  }
}
```

---

## AI Integration Layer

### Architecture Overview

```
┌─────────┐     ┌─────────────┐     ┌───────────┐     ┌─────────────┐
│  Client  │───→│  Django API  │───→│   MinIO   │     │  AI Service  │
│          │    │              │    │ (storage)  │     │  (external)  │
└─────────┘    │              │    └───────────┘     │              │
               │  services.py  │                      │              │
               │  ┌──────────┐ │    ┌───────────┐    │              │
               │  │  Light   │─┼──→│ REST call  │───→│              │
               │  │  tasks   │ │    └───────────┘    │              │
               │  ├──────────┤ │                      │              │
               │  │  Heavy   │─┼──→┌───────────┐───→│              │
               │  │  tasks   │ │   │ RabbitMQ  │    │              │
               │  └──────────┘ │   │  queue    │    │              │
               │              │    └───────────┘    │              │
               │  ┌──────────┐ │                      │              │
               │  │  Celery  │←┼──────────────────────│  Result     │
               │  │  worker  │ │    ┌───────────┐    │  callback   │
               │  └──────────┘ │←──│ RabbitMQ  │←───│              │
               │              │    │  results  │    │              │
               └──────────────┘    └───────────┘    └─────────────┘
```

### Processing Flow: Prescription OCR

```
Step 1: Upload
─────────────────────────────────────────────────────────────
POST /api/v1/ai/prescription-scan/
Content-Type: multipart/form-data
Body: { file: <image>, patient_id: "uuid" (optional) }

→ Validate file (allowed types: image/jpeg, image/png, application/pdf)
→ Validate file size (max 10MB)
→ Upload to MinIO: bucket=ai-inputs, key={tenant_schema}/{uuid}.{ext}
→ Create AIRequest(status=pending, input_file=minio_path)
→ Return 202 Accepted { request_id, status: "pending", poll_url: "/api/v1/ai/requests/{id}/" }

Step 2: Dispatch
─────────────────────────────────────────────────────────────
Service layer decides routing based on request_type:

LIGHT TASKS (expected < 5s):
  → Celery task with short timeout
  → Task makes REST call to AI service
  → AI service processes synchronously and returns result

HEAVY TASKS (expected > 5s):
  → Publish message to RabbitMQ exchange: "ai.tasks"
  → Routing key: "ai.tasks.prescription_ocr"
  → Message payload: { request_id, file_url (pre-signed), metadata }
  → Update AIRequest(status=processing)

Step 3: AI Service Processing (external)
─────────────────────────────────────────────────────────────
AI service (separate Python service):
  1. Downloads file from MinIO via pre-signed URL
  2. Runs OCR → extracts text
  3. Runs NLP → structures data (medications, dosages, etc.)
  4. Publishes result to RabbitMQ exchange: "ai.results"
  5. Routing key: "ai.results.prescription_ocr"

Step 4: Result Handling (Django/Celery)
─────────────────────────────────────────────────────────────
Celery worker consumes from "ai.results" queue:
  1. Deserialize result payload
  2. Update AIRequest:
     - status = "completed"
     - result = structured JSON
     - completed_at = now()
  3. If patient_id was provided:
     - Create draft PrescriptionItems from extracted data
     - Flag items with confidence < 0.8 for manual review
  4. Send notification to requesting user:
     "AI analysis complete. Review results."

Step 5: User Review
─────────────────────────────────────────────────────────────
Doctor reviews AI results via:
  GET /api/v1/ai/requests/{id}/
  → Returns structured data + confidence scores

If accepted:
  POST /api/v1/ai/requests/{id}/accept/
  → Creates actual Prescription + PrescriptionItems from AI output
```

### AI Service Contract

**Request (via RabbitMQ message)**:
```json
{
  "request_id": "uuid",
  "type": "prescription_ocr",
  "file_url": "https://minio:9000/ai-inputs/tenant_abc/uuid.jpg?X-Amz-Signature=...",
  "metadata": {
    "tenant_id": "uuid",
    "patient_id": "uuid",
    "requested_by": "uuid"
  },
  "callback": {
    "exchange": "ai.results",
    "routing_key": "ai.results.prescription_ocr"
  }
}
```

**Response (via RabbitMQ message)**:
```json
{
  "request_id": "uuid",
  "status": "success",
  "data": {
    "medications": [
      {
        "name": "Amoxicillin",
        "generic_name": "amoxicillin",
        "dosage": "500mg",
        "frequency": "3 times daily",
        "duration": "7 days",
        "route": "oral",
        "instructions": "after meals",
        "confidence": 0.95
      },
      {
        "name": "Ibuprofen",
        "generic_name": "ibuprofen",
        "dosage": "400mg",
        "frequency": "as needed",
        "duration": "5 days",
        "route": "oral",
        "instructions": "with food, max 3/day",
        "confidence": 0.72
      }
    ],
    "doctor_name": "Dr. Ahmed Hassan",
    "date_written": "2024-06-01",
    "raw_text": "Rx: Amoxicillin 500mg TDS x 7/7\nIbuprofen 400mg PRN x 5/7",
    "warnings": ["Low confidence on Ibuprofen instructions - manual review recommended"]
  },
  "processing_time_ms": 2340,
  "model_version": "prescription-ocr-v2.1"
}
```

### Error Handling & Retry Strategy

```python
# apps/ai_integration/tasks.py
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,  # 30s initial
    retry_backoff=True,      # Exponential: 30s → 60s → 120s
    retry_backoff_max=600,   # Cap at 10 minutes
    acks_late=True,          # Re-queue if worker dies mid-processing
)
def process_ai_request(self, request_id: str):
    try:
        # ... processing logic ...
    except AIServiceUnavailable as exc:
        ai_request.status = 'retrying'
        ai_request.retry_count += 1
        ai_request.save()
        raise self.retry(exc=exc)
    except AIServiceError as exc:
        ai_request.status = 'failed'
        ai_request.error_message = str(exc)
        ai_request.save()
        notify_user_failure(ai_request)
    except MaxRetriesExceededError:
        ai_request.status = 'failed'
        ai_request.error_message = 'Max retries exceeded'
        ai_request.save()
        # Move to dead letter queue
        publish_to_dlq(ai_request)
        notify_admin_dlq(ai_request)
```

### Circuit Breaker

```python
# apps/ai_integration/clients.py
class AIServiceClient:
    """
    REST client with circuit breaker pattern.
    States: CLOSED (normal) → OPEN (rejecting) → HALF_OPEN (testing)
    """
    FAILURE_THRESHOLD = 5       # Failures before opening circuit
    RECOVERY_TIMEOUT = 300      # 5 minutes before trying again
    SUCCESS_THRESHOLD = 3       # Successes in half-open before closing

    # Implementation uses Redis to track failure counts across workers
    # When circuit is OPEN: return 503 immediately, don't call AI service
```

---

## Security & Compliance

### Data Protection Layers

| Layer | Mechanism | Scope |
|-------|-----------|-------|
| At rest (DB) | PostgreSQL TDE or cloud-provider encryption | Entire database |
| At rest (files) | MinIO server-side encryption (SSE-S3) | All uploaded files |
| In transit | TLS 1.3 (nginx termination) | All network traffic |
| Application-level | Fernet symmetric encryption | national_id, PIN, backup codes |
| Access control | Schema isolation + RBAC | Per-tenant + per-role |

### Field-Level Encryption

```python
# common/utils.py
from cryptography.fernet import Fernet

class FieldEncryptor:
    """
    Encrypts/decrypts sensitive fields at application level.
    Key rotation: store key version with ciphertext, support multiple active keys.
    """
    def encrypt(self, plaintext: str) -> str: ...
    def decrypt(self, ciphertext: str) -> str: ...
```

Encrypted fields:
- `User.national_id`
- `Patient.national_id`
- `UserSecrets.refresh_token_encrypted`
- `UserSecrets.mfa_backup_codes_encrypted`

### Audit Logging

Every access to patient data generates an audit entry:

```python
# apps/audit/middleware.py
class AuditMiddleware:
    """
    Captures request context for audit logging.
    Works with signals to log who accessed/modified what.
    """
    def process_request(self, request):
        request._audit_context = {
            'user_id': request.user.id,
            'tenant_id': request.tenant.id,
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
        }

# apps/audit/signals.py
@receiver(post_save)
def log_model_change(sender, instance, created, **kwargs):
    """Auto-log create/update for audited models."""
    if hasattr(sender, 'AUDITED') and sender.AUDITED:
        AuditService.log(
            action='create' if created else 'update',
            resource_type=sender.__name__,
            resource_id=str(instance.pk),
            changes=get_changes(instance),
        )
```

### Rate Limiting

| Scope | Limit | Endpoint |
|-------|-------|----------|
| Anonymous | 20 req/min | All |
| Authenticated | 100 req/min | General API |
| AI upload | 10 req/min | `/api/v1/ai/*` |
| Auth endpoints | 5 req/min | `/api/v1/auth/*` |
| Bulk operations | 5 req/min | Any bulk endpoint |

### Additional Security Measures

- **CORS**: Strict origin whitelist per environment
- **Security headers**: HSTS, X-Content-Type-Options, X-Frame-Options (via Django middleware)
- **Input validation**: Serializer-level + model-level (defense in depth)
- **SQL injection**: Protected by Django ORM (parameterized queries)
- **File upload validation**: Type checking (magic bytes, not just extension), size limits, antivirus scan hook
- **Pre-signed URLs**: 15-minute expiry for medical document access
- **Secret management**: Environment variables via `django-environ`, never committed to VCS
- **Dependency scanning**: `safety` + `pip-audit` in CI pipeline
- **GDPR/Data retention**: Configurable per-tenant, anonymization procedure for "right to erasure"

---

## Monitoring & Observability

### Stack

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **Sentry** | Exception tracking + performance monitoring | Django SDK with tracing, release tracking |
| **Prometheus** | Metrics collection | `django-prometheus` exports at `/metrics/` |
| **Grafana** | Metrics visualization + alerting | Dashboards for API, DB, Celery, AI, tenants |
| **structlog** | Structured JSON logging | Request correlation IDs, tenant context |

### Structured Logging (structlog)

```python
# config/settings/base.py
import structlog

LOGGING = {
    'version': 1,
    'handlers': {
        'json': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'formatters': {
        'json': {
            '()': structlog.stdlib.ProcessorFormatter,
            'processor': structlog.dev.JSONRenderer(),
        },
    },
}

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,     # Request correlation
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)
```

**Log output example**:
```json
{
  "timestamp": "2024-06-01T10:30:00.123Z",
  "level": "info",
  "event": "appointment_created",
  "request_id": "req-abc-123",
  "tenant_id": "uuid",
  "user_id": "uuid",
  "patient_id": "uuid",
  "doctor_id": "uuid",
  "appointment_id": "uuid",
  "duration_ms": 45
}
```

### Prometheus Metrics

Key metrics exported:

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total requests by method, endpoint, status |
| `http_request_duration_seconds` | Histogram | Request latency by endpoint |
| `db_query_duration_seconds` | Histogram | Database query latency |
| `celery_tasks_total` | Counter | Tasks by name, state (success/failure) |
| `celery_task_duration_seconds` | Histogram | Task execution time |
| `ai_requests_total` | Counter | AI requests by type, status |
| `ai_processing_duration_seconds` | Histogram | AI processing time |
| `active_tenants` | Gauge | Number of active tenant schemas |
| `minio_upload_size_bytes` | Histogram | File upload sizes |

### Grafana Dashboards

1. **API Health**: Request rate, error rate (5xx), latency P50/P95/P99
2. **Database**: Query rate, slow queries, connection pool utilization
3. **Celery**: Queue depth, task success rate, processing time
4. **AI Service**: Request volume, success rate, processing time, circuit breaker state
5. **Tenant Usage**: Active tenants, requests per tenant, storage per tenant
6. **Business**: Appointments/day, patients registered, prescriptions issued

### Alerting Rules (Prometheus Alertmanager)

| Alert | Condition | Severity |
|-------|-----------|----------|
| High Error Rate | 5xx rate > 5% for 5 min | Critical |
| API Latency | P95 > 2s for 10 min | Warning |
| Celery Queue Backlog | Queue depth > 1000 for 5 min | Warning |
| AI Circuit Open | Circuit breaker in OPEN state | Critical |
| DB Connection Exhaustion | Available connections < 5 | Critical |
| MinIO Disk Usage | > 85% capacity | Warning |
| Failed AI Requests | > 10 failures in 5 min | Warning |

---

## Migration Management

### Strategy

Since `django-tenants` requires Django's migration framework (it hooks into `migrate_schemas` to run migrations per-schema), we use Django migrations with enhanced tooling:

### Tooling

| Tool | Purpose |
|------|---------|
| `django-migration-linter` | CI check: blocks unsafe migrations (e.g., NOT NULL without default on large tables, full table locks) |
| Migration squashing | Reduce file count when > 20 migrations per app |
| CI conflict detection | Detect merge conflicts between parallel branches |
| Git tags | Tag migrations for rollback reference: `migration/v1.2.0` |

### Commands

```bash
# Create migrations (standard Django)
python manage.py makemigrations

# Apply to all tenant schemas
python manage.py migrate_schemas --shared      # Public schema only
python manage.py migrate_schemas --tenant      # All tenant schemas
python manage.py migrate_schemas              # Both

# Lint migrations in CI
django-migration-linter apps/

# Squash when needed
python manage.py squashmigrations patients 0001 0020
```

### CI Pipeline Migration Checks

```yaml
# In CI/CD pipeline:
- name: Check migration conflicts
  run: python manage.py makemigrations --check --dry-run

- name: Lint migrations
  run: django-migration-linter apps/ --exclude-migration-tests

- name: Verify migration ordering
  run: python manage.py showmigrations --plan | grep "CONFLICT" && exit 1 || true
```

### Migration Safety Rules

1. **Never** add NOT NULL column without a default on tables with > 100k rows
2. **Never** run data migrations in the same transaction as schema migrations
3. **Always** make migrations backward-compatible (deploy new code → run migration → verify)
4. **Always** test migrations on a staging environment with production-like data volume
5. **Tag** every release with its migration state for rollback capability

---

## Infrastructure (Docker)

### docker-compose.yml (Development)

```yaml
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: docker/Dockerfile
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
      minio:
        condition: service_healthy
      keycloak:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: healthcare
      POSTGRES_USER: healthcare_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U healthcare_user -d healthcare"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  rabbitmq:
    image: rabbitmq:3-management-alpine
    environment:
      RABBITMQ_DEFAULT_USER: healthcare
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
    ports:
      - "5672:5672"
      - "15672:15672"  # Management UI
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "-q", "check_running"]
      interval: 10s
      timeout: 10s
      retries: 5

  celery_worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.celery
    command: celery -A config worker -l info -Q default,ai_tasks,notifications
    volumes:
      - .:/app
    env_file: .env
    depends_on:
      - db
      - redis
      - rabbitmq

  celery_beat:
    build:
      context: .
      dockerfile: docker/Dockerfile.celery
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    volumes:
      - .:/app
    env_file: .env
    depends_on:
      - db
      - redis
      - rabbitmq

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    ports:
      - "9000:9000"   # API
      - "9001:9001"   # Console
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 10s
      retries: 5

  keycloak:
    image: quay.io/keycloak/keycloak:24.0
    command: start-dev
    environment:
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://db:5432/keycloak
      KC_DB_USERNAME: healthcare_user
      KC_DB_PASSWORD: ${DB_PASSWORD}
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD}
    ports:
      - "8080:8080"
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "exec 3<>/dev/tcp/localhost/8080 && echo -e 'GET /health/ready HTTP/1.1\\r\\nHost: localhost\\r\\n\\r\\n' >&3 && cat <&3 | grep -q '200'"]
      interval: 10s
      timeout: 10s
      retries: 10

volumes:
  postgres_data:
  minio_data:
```

### MinIO Buckets (created on first deploy)

| Bucket | Purpose | Access |
|--------|---------|--------|
| `ai-inputs` | Files uploaded for AI processing | Private, pre-signed URLs |
| `medical-documents` | Patient documents, reports | Private, pre-signed URLs |
| `prescriptions` | Scanned prescriptions | Private, pre-signed URLs |
| `exports` | Generated reports, bulk exports | Private, time-limited access |

### .env.example

```bash
# Django
DJANGO_SETTINGS_MODULE=config.settings.development
SECRET_KEY=change-me-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=healthcare
DB_USER=healthcare_user
DB_PASSWORD=change-me
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# RabbitMQ
RABBITMQ_URL=amqp://healthcare:change-me@rabbitmq:5672/
RABBITMQ_PASSWORD=change-me

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=change-me
MINIO_USE_SSL=False
MINIO_BUCKET_AI_INPUTS=ai-inputs
MINIO_BUCKET_DOCUMENTS=medical-documents

# Keycloak
KEYCLOAK_URL=http://keycloak:8080
KEYCLOAK_REALM=healthcare-saas
KEYCLOAK_CLIENT_ID=web-app
KEYCLOAK_ADMIN_PASSWORD=change-me
OIDC_RP_CLIENT_ID=web-app
OIDC_RP_CLIENT_SECRET=change-me
OIDC_OP_JWKS_ENDPOINT=http://keycloak:8080/realms/healthcare-saas/protocol/openid-connect/certs

# Sentry
SENTRY_DSN=
SENTRY_ENVIRONMENT=development

# AI Service
AI_SERVICE_BASE_URL=http://ai-service:5000
AI_SERVICE_TIMEOUT=30

# Encryption
FIELD_ENCRYPTION_KEY=base64-encoded-fernet-key
```

---

## Dependencies

### requirements/base.txt

```
# Core
Django>=5.0,<5.1
djangorestframework>=3.14,<4.0
django-tenants>=3.6,<4.0

# Authentication (Keycloak/OIDC)
mozilla-django-oidc>=4.0,<5.0
PyJWT>=2.8,<3.0
cryptography>=42.0,<43.0

# Async / Task Queue
celery[redis]>=5.3,<6.0
django-celery-beat>=2.5,<3.0
kombu>=5.3,<6.0

# Database
psycopg[binary]>=3.1,<4.0

# API
django-filter>=23.0,<24.0
django-cors-headers>=4.3,<5.0
drf-spectacular>=0.27,<1.0          # OpenAPI schema generation

# Storage (MinIO)
django-storages>=1.14,<2.0
boto3>=1.34,<2.0

# Monitoring
sentry-sdk[django]>=1.40,<2.0
django-prometheus>=2.3,<3.0
structlog>=24.0,<25.0

# Security
django-ratelimit>=4.1,<5.0

# Migrations
django-migration-linter>=5.0,<6.0

# Utilities
django-environ>=0.11,<1.0
python-dateutil>=2.8,<3.0
```

### requirements/development.txt

```
-r base.txt

# Debug
django-debug-toolbar>=4.2,<5.0
ipdb>=0.13,<1.0
django-extensions>=3.2,<4.0

# Code Quality
ruff>=0.3,<1.0
mypy>=1.8,<2.0
django-stubs>=4.2,<5.0
```

### requirements/testing.txt

```
-r base.txt

# Testing
pytest>=8.0,<9.0
pytest-django>=4.8,<5.0
pytest-cov>=4.1,<5.0
pytest-asyncio>=0.23,<1.0
factory-boy>=3.3,<4.0
faker>=23.0,<24.0
responses>=0.25,<1.0          # Mock HTTP requests
freezegun>=1.4,<2.0           # Time mocking
```

### requirements/production.txt

```
-r base.txt

# WSGI Server
gunicorn>=21.0,<22.0
gevent>=24.0,<25.0

# Production Utilities
whitenoise>=6.6,<7.0
```

---

## Verification & Testing Strategy

### Test Pyramid

```
         ╱╲
        ╱  ╲        E2E Tests (few)
       ╱────╲       - Full API flow tests
      ╱      ╲      - Multi-tenant isolation
     ╱────────╲     Integration Tests (moderate)
    ╱          ╲    - API endpoint tests
   ╱────────────╲   - Database queries
  ╱              ╲  - Celery task execution
 ╱────────────────╲ Unit Tests (many)
╱                  ╲ - Service functions
╱────────────────────╲ - Model methods, validators
```

### Test Categories

| Category | What | Tools |
|----------|------|-------|
| Unit | Service functions, model methods, validators | pytest, factory_boy, unittest.mock |
| Integration | API endpoints, DB operations, Celery tasks | pytest-django, DRF test client |
| Security | Cross-tenant access, permission enforcement | Custom test mixins |
| Performance | Appointment conflict detection under concurrency | locust, pytest-benchmark |
| Migration | Migration linting, fresh DB setup | django-migration-linter |

### Critical Test Cases

1. **Multi-tenant isolation**: Create patient in Tenant A → query from Tenant B → must return empty/404
2. **Appointment conflict**: Two concurrent requests for same doctor/time → one succeeds, one fails (DB exclusion constraint)
3. **RBAC enforcement**: Receptionist cannot access visit details. Doctor cannot access billing admin.
4. **Visit immutability**: After `is_signed=true`, PATCH request returns 403
5. **AI retry logic**: Mock AI service failure → verify 3 retries with backoff → final failure notification
6. **Audit completeness**: CRUD on patient → verify 4 audit entries created
7. **Soft delete**: Deleted patient excluded from list queries, accessible via admin endpoint
8. **Keycloak token validation**: Expired token → 401. Invalid signature → 401. Valid token → authenticated.
9. **MinIO pre-signed URL**: URL expires after 15 minutes → returns 403 from MinIO
10. **Invoice status machine**: Payment recorded → status auto-updates to paid/partially_paid

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=apps --cov-report=html

# Specific app
pytest apps/appointments/tests/

# Only unit tests (fast)
pytest -m unit

# Integration tests (requires DB + Redis)
pytest -m integration

# Migration linting
django-migration-linter apps/
```

---

## Appendix: Enum Definitions

```python
# common/enums.py
from django.db.models import TextChoices

class OrganizationType(TextChoices):
    CLINIC = 'clinic', 'Clinic'
    HOSPITAL = 'hospital', 'Hospital'
    LAB = 'lab', 'Laboratory'

class SubscriptionPlan(TextChoices):
    FREE = 'free', 'Free'
    PRO = 'pro', 'Professional'
    ENTERPRISE = 'enterprise', 'Enterprise'

class UserRole(TextChoices):
    OWNER = 'owner', 'Owner'
    ADMIN = 'admin', 'Administrator'
    DOCTOR = 'doctor', 'Doctor'
    NURSE = 'nurse', 'Nurse'
    RECEPTIONIST = 'receptionist', 'Receptionist'
    LAB_TECH = 'lab_tech', 'Lab Technician'
    BILLING_STAFF = 'billing_staff', 'Billing Staff'

class Gender(TextChoices):
    MALE = 'male', 'Male'
    FEMALE = 'female', 'Female'
    OTHER = 'other', 'Other'

class AppointmentStatus(TextChoices):
    SCHEDULED = 'scheduled', 'Scheduled'
    CONFIRMED = 'confirmed', 'Confirmed'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'
    NO_SHOW = 'no_show', 'No Show'

class AppointmentType(TextChoices):
    IN_PERSON = 'in_person', 'In Person'
    TELEHEALTH = 'telehealth', 'Telehealth'

class LabOrderStatus(TextChoices):
    ORDERED = 'ordered', 'Ordered'
    SAMPLE_COLLECTED = 'sample_collected', 'Sample Collected'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'

class LabPriority(TextChoices):
    ROUTINE = 'routine', 'Routine'
    URGENT = 'urgent', 'Urgent'
    STAT = 'stat', 'Stat'

class ResultFlag(TextChoices):
    NORMAL = 'normal', 'Normal'
    LOW = 'low', 'Low'
    HIGH = 'high', 'High'
    CRITICAL = 'critical', 'Critical'

class InvoiceStatus(TextChoices):
    DRAFT = 'draft', 'Draft'
    ISSUED = 'issued', 'Issued'
    PARTIALLY_PAID = 'partially_paid', 'Partially Paid'
    PAID = 'paid', 'Paid'
    OVERDUE = 'overdue', 'Overdue'
    CANCELLED = 'cancelled', 'Cancelled'

class PaymentMethod(TextChoices):
    CASH = 'cash', 'Cash'
    CARD = 'card', 'Card'
    INSURANCE = 'insurance', 'Insurance'
    BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
    ONLINE = 'online', 'Online'

class MedicationForm(TextChoices):
    TABLET = 'tablet', 'Tablet'
    CAPSULE = 'capsule', 'Capsule'
    SYRUP = 'syrup', 'Syrup'
    INJECTION = 'injection', 'Injection'
    CREAM = 'cream', 'Cream'
    DROPS = 'drops', 'Drops'
    INHALER = 'inhaler', 'Inhaler'

class MedicationRoute(TextChoices):
    ORAL = 'oral', 'Oral'
    IV = 'iv', 'Intravenous'
    IM = 'im', 'Intramuscular'
    TOPICAL = 'topical', 'Topical'
    SUBLINGUAL = 'sublingual', 'Sublingual'
    INHALATION = 'inhalation', 'Inhalation'

class DiagnosisType(TextChoices):
    PRIMARY = 'primary', 'Primary'
    SECONDARY = 'secondary', 'Secondary'
    RULE_OUT = 'rule_out', 'Rule Out'

class AIRequestType(TextChoices):
    PRESCRIPTION_OCR = 'prescription_ocr', 'Prescription OCR'
    LAB_ANALYSIS = 'lab_analysis', 'Lab Analysis'
    RADIOLOGY = 'radiology', 'Radiology'

class AIRequestStatus(TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    RETRYING = 'retrying', 'Retrying'

class AuditAction(TextChoices):
    CREATE = 'create', 'Create'
    READ = 'read', 'Read'
    UPDATE = 'update', 'Update'
    DELETE = 'delete', 'Delete'
    LOGIN = 'login', 'Login'
    LOGOUT = 'logout', 'Logout'
    EXPORT = 'export', 'Export'

class NotificationType(TextChoices):
    APPOINTMENT_REMINDER = 'appointment_reminder', 'Appointment Reminder'
    LAB_RESULT = 'lab_result', 'Lab Result Ready'
    PRESCRIPTION = 'prescription', 'Prescription'
    BILLING = 'billing', 'Billing'
    SYSTEM = 'system', 'System'

class NotificationChannel(TextChoices):
    IN_APP = 'in_app', 'In-App'
    SMS = 'sms', 'SMS'
    EMAIL = 'email', 'Email'
    PUSH = 'push', 'Push Notification'

class InvoiceItemType(TextChoices):
    CONSULTATION = 'consultation', 'Consultation'
    PROCEDURE = 'procedure', 'Procedure'
    LAB_TEST = 'lab_test', 'Lab Test'
    MEDICATION = 'medication', 'Medication'
    OTHER = 'other', 'Other'
```

---

## Summary of Key Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Architecture | Modular Monolith | Simpler ops than microservices, natural extraction boundaries via apps |
| Multi-tenancy | Schema-per-tenant | True isolation, regulatory compliance, no accidental data leaks |
| Patient scope | Per-tenant only | Eliminates cross-schema complexity and consent management |
| Auth | Keycloak (external) | Externalizes auth complexity, supports MFA/SSO/OIDC natively |
| Business logic | Service layer | Testable, mockable, extractable. Models stay focused on data integrity |
| File storage | MinIO | S3-compatible, self-hosted, dev/prod parity, swappable for cloud S3 |
| Async | Celery + RabbitMQ | Proven stack, supports priority queues, dead letter, routing |
| AI comms | REST + Message broker | REST for quick lookups, broker for heavy processing (best of both) |
| Monitoring | Sentry + Prometheus + Grafana + structlog | Full observability: errors, metrics, logs, traces |
| Migrations | Django migrations + linter | Required by django-tenants, enhanced with CI safety checks |
| PKs | UUID | Security (no enumeration), merge-safe, microservice-ready |
| Soft delete | Where appropriate | Patient, records — never lose medical data |
