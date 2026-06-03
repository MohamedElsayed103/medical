# Software Requirements Specification (SRS)
## MedFlow Pro — Healthcare SaaS Platform

| Field | Value |
|-------|-------|
| **Document Version** | 1.0 |
| **Date** | May 31, 2026 |
| **Product Name** | MedFlow Pro |
| **Platform** | Web (SaaS) |
| **Architecture** | Multi-tenant Modular Monolith (Schema-per-Tenant) |
| **Tech Stack** | Django 5.x + DRF + PostgreSQL + React 19 + Vite + Tailwind CSS |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Overview](#2-system-overview)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [System Architecture](#5-system-architecture)
6. [Data Models Summary](#6-data-models-summary)
7. [API Design](#7-api-design)
8. [Security & Compliance](#8-security--compliance)
9. [Current Limitations](#9-current-limitations)
10. [Future Work & Market Differentiation](#10-future-work--market-differentiation)

---

## 1. Introduction

### 1.1 Purpose

This SRS document describes the complete functional and non-functional requirements of **MedFlow Pro**, a multi-tenant Healthcare SaaS platform designed for clinics, hospitals, and laboratories. It serves as a reference for development, testing, and stakeholder communication.

### 1.2 Scope

MedFlow Pro provides:
- Electronic Medical Records (EMR)
- Patient management
- Appointment scheduling
- Prescription management
- Laboratory order tracking & result management
- Billing & invoicing
- Pharmacy inventory & dispensing
- Insurance claims management
- AI-powered clinical decision support
- Role-Based Access Control (RBAC)
- Multi-channel notification system
- Audit trail & compliance logging
- Inter-facility referrals

### 1.3 Target Users

| User Role | Description |
|-----------|-------------|
| **Clinic Owner/Admin** | Manages tenant configuration, users, roles, billing |
| **Doctor/Physician** | Manages patients, visits, prescriptions, lab orders |
| **Nurse** | Records vitals, assists with patient care |
| **Receptionist** | Schedules appointments, registers patients |
| **Lab Technician** | Processes lab orders, enters results |
| **Pharmacist** | Manages drug inventory, dispenses medications |
| **Billing Staff** | Creates invoices, processes payments |

### 1.4 Definitions & Acronyms

| Term | Definition |
|------|------------|
| **Tenant** | An organization (clinic/hospital/lab) with its own isolated data schema |
| **RBAC** | Role-Based Access Control |
| **SOAP** | Subjective, Objective, Assessment, Plan (clinical note format) |
| **ICD** | International Classification of Diseases |
| **EMR** | Electronic Medical Record |
| **HIPAA** | Health Insurance Portability and Accountability Act |
| **MRN** | Medical Record Number |

---

## 2. System Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React 19 + Vite)                │
│   Tailwind CSS │ Framer Motion │ Recharts │ TanStack Query       │
└───────────────────────────────┬─────────────────────────────────┘
                                │ REST API (JSON)
┌───────────────────────────────▼─────────────────────────────────┐
│                     BACKEND (Django 5.x + DRF)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Accounts │ │   RBAC   │ │ Patients │ │Appointmt │          │
│  ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤          │
│  │ Billing  │ │ Lab Res. │ │ Prescr.  │ │ Med.Rec. │          │
│  ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤          │
│  │ Pharmacy │ │Insurance │ │ AI Integ │ │ Notif.   │          │
│  ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤          │
│  │  Audit   │ │ Referral │ │ Tenants  │ │ Common   │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│              PostgreSQL (Schema-per-Tenant)                       │
│   ┌────────┐  ┌────────────┐  ┌────────────┐                    │
│   │ public │  │ tenant_abc │  │ tenant_xyz │   ...               │
│   └────────┘  └────────────┘  └────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Multi-Tenancy Model

- **Schema-per-tenant** via `django-tenants`
- Each organization gets its own PostgreSQL schema with full data isolation
- Public schema stores: users, audit logs, tenant metadata, referrals
- Tenant schemas store: patients, appointments, visits, prescriptions, labs, billing, pharmacy, insurance, notifications, RBAC

---

## 3. Functional Requirements

### 3.1 Authentication & User Management (FR-AUTH)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-AUTH-01 | User registration with email/password | High | ✅ Implemented |
| FR-AUTH-02 | User login with JWT token issuance | High | ✅ Implemented |
| FR-AUTH-03 | Token refresh (access + refresh tokens) | High | ✅ Implemented |
| FR-AUTH-04 | User profile view and update | Medium | ✅ Implemented |
| FR-AUTH-05 | PIN-based quick verification for clinical access | Medium | ✅ Implemented |
| FR-AUTH-06 | API key generation and management | Low | ✅ Implemented |
| FR-AUTH-07 | Rate limiting on auth endpoints (5/min) | High | ✅ Implemented |
| FR-AUTH-08 | Multi-tenant user mapping (user belongs to multiple orgs) | High | ✅ Implemented |
| FR-AUTH-09 | Keycloak OIDC integration (SSO) | Medium | ✅ Implemented |
| FR-AUTH-10 | Invitation-based onboarding for team members | Medium | ✅ Implemented |

### 3.2 Role-Based Access Control (FR-RBAC)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-RBAC-01 | Define custom roles per tenant | High | ✅ Implemented |
| FR-RBAC-02 | Granular resource:action permissions | High | ✅ Implemented |
| FR-RBAC-03 | Assign permissions to roles (M2M) | High | ✅ Implemented |
| FR-RBAC-04 | Assign roles to users within a tenant | High | ✅ Implemented |
| FR-RBAC-05 | System roles (non-deletable, seeded on creation) | Medium | ✅ Implemented |
| FR-RBAC-06 | Permission checking middleware | High | ✅ Implemented |
| FR-RBAC-07 | User invitation with pre-assigned role | Medium | ✅ Implemented |
| FR-RBAC-08 | Token-based invitation acceptance flow | Medium | ✅ Implemented |
| FR-RBAC-09 | Frontend permission-gated UI components | Medium | ✅ Implemented |

### 3.3 Patient Management (FR-PAT)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-PAT-01 | Patient registration with demographics | High | ✅ Implemented |
| FR-PAT-02 | Unique Medical Record Number (MRN) per patient | High | ✅ Implemented |
| FR-PAT-03 | Patient search and filtering | High | ✅ Implemented |
| FR-PAT-04 | Patient detail view (overview + history tabs) | High | ✅ Implemented |
| FR-PAT-05 | Encrypted national ID storage (Fernet encryption) | High | ✅ Implemented |
| FR-PAT-06 | Allergies and chronic conditions tracking (JSON) | Medium | ✅ Implemented |
| FR-PAT-07 | Emergency contact information | Medium | ✅ Implemented |
| FR-PAT-08 | Insurance information on patient record | Medium | ✅ Implemented |
| FR-PAT-09 | Soft-delete only (no hard deletion of medical data) | High | ✅ Implemented |
| FR-PAT-10 | Blood type recording | Low | ✅ Implemented |

### 3.4 Appointment Scheduling (FR-APPT)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-APPT-01 | Schedule appointment (patient + doctor + time) | High | ✅ Implemented |
| FR-APPT-02 | Appointment status lifecycle (scheduled → confirmed → in_progress → completed) | High | ✅ Implemented |
| FR-APPT-03 | Appointment type: In-Person / Telehealth | Medium | ✅ Implemented |
| FR-APPT-04 | Cancellation with reason tracking | Medium | ✅ Implemented |
| FR-APPT-05 | No-show marking | Medium | ✅ Implemented |
| FR-APPT-06 | Duration-based time slots (configurable) | Medium | ✅ Implemented |
| FR-APPT-07 | Doctor profile with specialization, fee, availability | High | ✅ Implemented |
| FR-APPT-08 | Appointment filtering by date, doctor, status | Medium | ✅ Implemented |

### 3.5 Medical Records / Visits (FR-MR)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-MR-01 | Create clinical visit in SOAP format | High | ✅ Implemented |
| FR-MR-02 | Record vitals (BP, HR, temp, resp. rate, O2 sat, weight, height) | High | ✅ Implemented |
| FR-MR-03 | ICD-coded diagnosis assignment (primary/secondary/rule-out) | High | ✅ Implemented |
| FR-MR-04 | Visit signing (immutable after sign-off) | High | ✅ Implemented |
| FR-MR-05 | Link visit to appointment | Medium | ✅ Implemented |
| FR-MR-06 | Follow-up date tracking | Medium | ✅ Implemented |
| FR-MR-07 | Clinical notes (chief complaint, HPI, examination, assessment, plan) | High | ✅ Implemented |
| FR-MR-08 | Visit history per patient | High | ✅ Implemented |

### 3.6 Prescriptions (FR-RX)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-RX-01 | Create prescription with multiple medication items | High | ✅ Implemented |
| FR-RX-02 | Medication reference table (name, generic, form, strength) | High | ✅ Implemented |
| FR-RX-03 | Dosage, frequency, duration, route per item | High | ✅ Implemented |
| FR-RX-04 | PRN (as-needed) flag for medications | Medium | ✅ Implemented |
| FR-RX-05 | Link prescription to visit | Medium | ✅ Implemented |
| FR-RX-06 | Dispensing status tracking | Medium | ✅ Implemented |
| FR-RX-07 | Multiple medication routes (oral, IV, IM, topical, sublingual, inhalation) | Medium | ✅ Implemented |
| FR-RX-08 | Multiple medication forms (tablet, capsule, syrup, injection, cream, drops, inhaler) | Medium | ✅ Implemented |

### 3.7 Laboratory (FR-LAB)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-LAB-01 | Create lab order with multiple tests | High | ✅ Implemented |
| FR-LAB-02 | Lab order status lifecycle (ordered → sample_collected → processing → completed) | High | ✅ Implemented |
| FR-LAB-03 | Priority levels (routine, urgent, stat) | Medium | ✅ Implemented |
| FR-LAB-04 | Test result entry with values, units, reference ranges | High | ✅ Implemented |
| FR-LAB-05 | Automatic result flagging (normal/low/high/critical) | High | ✅ Implemented |
| FR-LAB-06 | Critical value auto-detection (50% below low or 150% above high) | Medium | ✅ Implemented |
| FR-LAB-07 | Specimen type tracking per test | Medium | ✅ Implemented |
| FR-LAB-08 | Lab technician result attribution | Medium | ✅ Implemented |
| FR-LAB-09 | Link lab order to visit | Medium | ✅ Implemented |

### 3.8 Billing & Invoicing (FR-BILL)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-BILL-01 | Invoice creation with line items | High | ✅ Implemented |
| FR-BILL-02 | Auto-generated invoice numbers | High | ✅ Implemented |
| FR-BILL-03 | Invoice status lifecycle (draft → issued → partially_paid → paid) | High | ✅ Implemented |
| FR-BILL-04 | Multiple item types (consultation, lab, prescription, procedure) | Medium | ✅ Implemented |
| FR-BILL-05 | Tax and discount calculation | Medium | ✅ Implemented |
| FR-BILL-06 | Partial payment support | High | ✅ Implemented |
| FR-BILL-07 | Multiple payment methods (cash, card, insurance, bank, online) | Medium | ✅ Implemented |
| FR-BILL-08 | Balance due calculation | Medium | ✅ Implemented |
| FR-BILL-09 | Payment reference tracking | Medium | ✅ Implemented |
| FR-BILL-10 | Overdue invoice detection | Medium | ✅ Implemented |

### 3.9 Pharmacy (FR-PHARM)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-PHARM-01 | Medication inventory management | High | ✅ Implemented |
| FR-PHARM-02 | Stock level tracking (current quantity) | High | ✅ Implemented |
| FR-PHARM-03 | Reorder level alerts | Medium | ✅ Implemented |
| FR-PHARM-04 | Expiry date tracking | Medium | ✅ Implemented |
| FR-PHARM-05 | Stock transactions (in/out/adjustment/waste) | High | ✅ Implemented |
| FR-PHARM-06 | Dispense records linked to prescriptions | High | ✅ Implemented |
| FR-PHARM-07 | Dispense status tracking (pending → dispensed → returned) | Medium | ✅ Implemented |
| FR-PHARM-08 | Batch/lot number tracking | Medium | ✅ Implemented |

### 3.10 Insurance (FR-INS)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-INS-01 | Insurance provider management | High | ✅ Implemented |
| FR-INS-02 | Patient insurance policy records | High | ✅ Implemented |
| FR-INS-03 | Insurance claim creation and tracking | High | ✅ Implemented |
| FR-INS-04 | Claim status lifecycle (submitted → under_review → approved → paid / denied) | High | ✅ Implemented |
| FR-INS-05 | Claim document attachment | Medium | ✅ Implemented |
| FR-INS-06 | Coverage amount and co-pay tracking | Medium | ✅ Implemented |
| FR-INS-07 | Policy validity period tracking | Medium | ✅ Implemented |

### 3.11 AI Integration (FR-AI)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-AI-01 | Prescription OCR (image → structured data) | High | ✅ Implemented |
| FR-AI-02 | Lab result analysis and interpretation | High | ✅ Implemented |
| FR-AI-03 | Radiology report analysis | Medium | ✅ Implemented |
| FR-AI-04 | AI request tracking (status, tokens, latency, cost) | Medium | ✅ Implemented |
| FR-AI-05 | Async processing for heavy AI tasks (Celery) | Medium | ✅ Implemented |
| FR-AI-06 | Retry mechanism for failed AI requests | Medium | ✅ Implemented |
| FR-AI-07 | Sanitized input logging for auditability | High | ✅ Implemented |

### 3.12 Notifications (FR-NOTIF)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-NOTIF-01 | In-app notification creation and delivery | High | ✅ Implemented |
| FR-NOTIF-02 | Email notification channel | High | ✅ Implemented |
| FR-NOTIF-03 | SMS notification channel (integration ready) | Medium | ✅ Implemented |
| FR-NOTIF-04 | Push notification channel (integration ready) | Medium | ✅ Implemented |
| FR-NOTIF-05 | Per-user channel preferences | Medium | ✅ Implemented |
| FR-NOTIF-06 | Quiet hours respect | Medium | ✅ Implemented |
| FR-NOTIF-07 | Mark as read/unread | Medium | ✅ Implemented |
| FR-NOTIF-08 | Notification types (appointment, lab result, prescription, billing, system) | Medium | ✅ Implemented |
| FR-NOTIF-09 | Real-time notification bell in TopBar with count badge | Medium | ✅ Implemented |

### 3.13 Audit Trail (FR-AUDIT)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-AUDIT-01 | Immutable, append-only audit log | High | ✅ Implemented |
| FR-AUDIT-02 | Track all CRUD operations on critical resources | High | ✅ Implemented |
| FR-AUDIT-03 | Record user, IP address, user-agent | High | ✅ Implemented |
| FR-AUDIT-04 | Record field-level changes (old vs new values) | High | ✅ Implemented |
| FR-AUDIT-05 | Cross-tenant visibility (public schema) | Medium | ✅ Implemented |
| FR-AUDIT-06 | Login/logout/export event logging | Medium | ✅ Implemented |
| FR-AUDIT-07 | Correlation ID (request_id) for tracing | Medium | ✅ Implemented |
| FR-AUDIT-08 | No update or delete allowed on audit records | High | ✅ Implemented |

### 3.14 Referrals (FR-REF)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-REF-01 | Facility-to-facility connection management | Medium | ✅ Implemented |
| FR-REF-02 | Patient referral creation between facilities | Medium | ✅ Implemented |
| FR-REF-03 | Referral status tracking (pending → accepted → in_progress → completed) | Medium | ✅ Implemented |
| FR-REF-04 | Referral priority (routine, urgent, emergency) | Medium | ✅ Implemented |
| FR-REF-05 | Referral notes and communication | Medium | ✅ Implemented |
| FR-REF-06 | Connection request/approval flow | Medium | ✅ Implemented |

### 3.15 Tenant / Organization Management (FR-TENANT)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-TENANT-01 | Organization creation with auto schema provisioning | High | ✅ Implemented |
| FR-TENANT-02 | Organization types: clinic, hospital, lab | High | ✅ Implemented |
| FR-TENANT-03 | Subscription plans: free, pro, enterprise | Medium | ✅ Implemented |
| FR-TENANT-04 | Domain-based tenant routing | High | ✅ Implemented |
| FR-TENANT-05 | Tenant activation/deactivation | Medium | ✅ Implemented |

### 3.16 Frontend Dashboard & UI (FR-UI)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-UI-01 | Real-time stats dashboard (patients, appointments, revenue) | High | ✅ Implemented |
| FR-UI-02 | Revenue/analytics charts (Recharts) | Medium | ✅ Implemented |
| FR-UI-03 | Animated sidebar with collapse/expand | Medium | ✅ Implemented |
| FR-UI-04 | Global patient search in TopBar | Medium | ✅ Implemented |
| FR-UI-05 | Notification dropdown with count badge | Medium | ✅ Implemented |
| FR-UI-06 | User menu (profile, settings, logout) | Medium | ✅ Implemented |
| FR-UI-07 | Responsive layout (mobile hamburger menu) | Medium | ✅ Implemented |
| FR-UI-08 | Page-level lazy loading for performance | Medium | ✅ Implemented |
| FR-UI-09 | Error boundaries for graceful failure handling | Medium | ✅ Implemented |
| FR-UI-10 | Framer Motion page transitions | Low | ✅ Implemented |

---

## 4. Non-Functional Requirements

### 4.1 Security (NFR-SEC)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| NFR-SEC-01 | Schema-level data isolation between tenants | Critical | ✅ |
| NFR-SEC-02 | JWT-based stateless authentication | High | ✅ |
| NFR-SEC-03 | Fernet encryption for PII (national IDs) | High | ✅ |
| NFR-SEC-04 | Rate limiting on auth endpoints | High | ✅ |
| NFR-SEC-05 | CORS configuration (whitelist in production) | High | ✅ |
| NFR-SEC-06 | Password hashing (Django PBKDF2/Argon2) | High | ✅ |
| NFR-SEC-07 | Soft-delete only for medical data (no permanent loss) | High | ✅ |
| NFR-SEC-08 | Immutable audit trail (no update/delete) | High | ✅ |
| NFR-SEC-09 | Keycloak for centralized identity (MFA, brute-force protection) | Medium | ✅ |
| NFR-SEC-10 | Pre-signed URLs for file access (MinIO/S3) | Medium | ✅ |
| NFR-SEC-11 | API key hashing (never stored in plain text) | Medium | ✅ |
| NFR-SEC-12 | PIN hashing for quick clinical access | Medium | ✅ |
| NFR-SEC-13 | No cross-schema foreign keys (prevents data leaks) | High | ✅ |

### 4.2 Performance (NFR-PERF)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| NFR-PERF-01 | Database indexing on all frequently queried fields | High | ✅ |
| NFR-PERF-02 | Lazy-loaded frontend pages (code splitting) | Medium | ✅ |
| NFR-PERF-03 | Frontend bundle chunking (vendor, charts, UI, query) | Medium | ✅ |
| NFR-PERF-04 | Celery for async heavy tasks (AI, notifications) | Medium | ✅ |
| NFR-PERF-05 | Pagination on all list endpoints | High | ✅ |
| NFR-PERF-06 | Optimized queries with `select_related` | Medium | ✅ |
| NFR-PERF-07 | TanStack Query for frontend caching | Medium | ✅ |

### 4.3 Scalability (NFR-SCALE)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| NFR-SCALE-01 | Schema-per-tenant supports ~500 tenants per PostgreSQL instance | High | ✅ |
| NFR-SCALE-02 | Stateless backend (horizontally scalable) | High | ✅ |
| NFR-SCALE-03 | Celery workers scale independently | Medium | ✅ |
| NFR-SCALE-04 | Docker Compose for development, cloud-ready for production | Medium | ✅ |
| NFR-SCALE-05 | MinIO for object storage (scalable independently) | Medium | ✅ |

### 4.4 Reliability (NFR-REL)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| NFR-REL-01 | Service layer pattern (clean separation of concerns) | High | ✅ |
| NFR-REL-02 | Error handling with structured error responses | High | ✅ |
| NFR-REL-03 | Structured logging via `structlog` | Medium | ✅ |
| NFR-REL-04 | Prometheus metrics export | Medium | ✅ |
| NFR-REL-05 | Health check endpoints | Medium | ✅ |
| NFR-REL-06 | Retry mechanism for AI requests | Medium | ✅ |

### 4.5 Maintainability (NFR-MAIN)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| NFR-MAIN-01 | Modular app structure (each feature in its own Django app) | High | ✅ |
| NFR-MAIN-02 | Service layer (business logic isolated from views/models) | High | ✅ |
| NFR-MAIN-03 | TypeScript frontend with strict type checking | High | ✅ |
| NFR-MAIN-04 | OpenAPI/Swagger documentation (`drf-spectacular`) | Medium | ✅ |
| NFR-MAIN-05 | Zustand for predictable state management | Medium | ✅ |
| NFR-MAIN-06 | Environment-based configuration (django-environ) | Medium | ✅ |

### 4.6 Compliance (NFR-COMP)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| NFR-COMP-01 | HIPAA-ready architecture (data isolation, encryption, audit trail) | High | ✅ |
| NFR-COMP-02 | Immutable audit logs for regulatory inspection | High | ✅ |
| NFR-COMP-03 | Data sovereignty support (self-hosted MinIO) | Medium | ✅ |
| NFR-COMP-04 | No hard deletion of medical records | High | ✅ |
| NFR-COMP-05 | Field-level change tracking in audit | Medium | ✅ |
| NFR-COMP-06 | User consent tracking infrastructure | Medium | ✅ |

### 4.7 Usability (NFR-UX)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| NFR-UX-01 | Professional UI with Tailwind CSS design system | High | ✅ |
| NFR-UX-02 | Smooth animations (Framer Motion) | Medium | ✅ |
| NFR-UX-03 | Responsive design (mobile + desktop) | Medium | ✅ |
| NFR-UX-04 | Global search for quick patient lookup | Medium | ✅ |
| NFR-UX-05 | Accessible form validation with Zod | Medium | ✅ |
| NFR-UX-06 | Loading states and skeleton screens | Medium | ✅ |

---

## 5. System Architecture

### 5.1 Backend Architecture

```
config/settings/          → Environment-specific Django settings
apps/
  accounts/               → User identity (public schema)
  tenants/                → Organization management
  rbac/                   → Roles, permissions, tenant users (tenant schema)
  patients/               → Patient records
  appointments/           → Scheduling + doctor profiles
  medical_records/        → Visits, vitals, diagnoses (SOAP)
  prescriptions/          → Medications, prescriptions, items
  lab_results/            → Lab orders, tests, results
  billing/                → Invoices, items, payments
  pharmacy/               → Inventory, stock, dispensing
  insurance/              → Providers, policies, claims
  ai_integration/         → AI request tracking
  notifications/          → Multi-channel notifications
  audit/                  → Immutable audit trail
  referrals/              → Inter-facility referrals
common/                   → Shared utilities, base models, enums
```

### 5.2 Frontend Architecture

```
src/
  pages/                  → Page components (lazy-loaded)
    auth/                 → Login, Register, Accept Invitation
    dashboard/            → Main dashboard with stats
    patients/             → Patient list + detail
    appointments/         → Appointment management
    visits/               → Visit list + detail
    prescriptions/        → Prescription management
    lab-orders/           → Lab order tracking
    billing/              → Invoicing & payments
    pharmacy/             → Inventory management
    insurance/            → Claims management
    ai/                   → AI assistant interface
    notifications/        → Notification center
    audit/                → Audit log viewer
    settings/             → Users, Roles, Invitations
    profile/              → User profile
  components/
    navigation/           → Sidebar, TopBar
  layouts/                → DashboardLayout, AuthLayout
  stores/                 → Zustand state (auth, UI)
  services/               → API client (Axios)
  types/                  → TypeScript type definitions
  lib/                    → Utilities (safeFormat, etc.)
```

### 5.3 Data Flow Pattern

```
Frontend (React) → Axios → Vite Proxy → Django REST API
                                              │
                         ┌────────────────────┤
                         │                    │
                    Views (thin)         Middleware
                         │              (tenant routing,
                    Services             audit, RBAC)
                    (business logic)
                         │
                    Models (data integrity)
                         │
                    PostgreSQL (schema-per-tenant)
```

---

## 6. Data Models Summary

### Public Schema (Shared)
| Model | Purpose |
|-------|---------|
| User | Platform-wide user identity |
| UserSecrets | PIN hash, API key hash |
| UserTenantMapping | Links users to tenants |
| Organization | Tenant entity (clinic/hospital/lab) |
| Domain | Hostname → tenant routing |
| AuditLog | Immutable audit trail |
| FacilityConnection | Inter-facility links |
| Referral | Patient referrals between facilities |

### Tenant Schema (Per-Organization)
| Model | Purpose |
|-------|---------|
| Role | Named role with permissions |
| Permission | Resource:action pair |
| RolePermission | M2M role ↔ permission |
| TenantUser | User profile within tenant |
| UserInvitation | Invitation tokens |
| Patient | Patient demographics + medical info |
| DoctorProfile | Doctor specialization + fees |
| Appointment | Scheduled encounters |
| Visit | Clinical encounter (SOAP) |
| Vitals | Vital signs per visit |
| Diagnosis | ICD-coded diagnoses |
| Medication | Drug reference table |
| Prescription | Prescription header |
| PrescriptionItem | Medication line items |
| LabOrder | Lab order header |
| LabTest | Individual tests |
| TestResult | Result with auto-flagging |
| Invoice | Billing header |
| InvoiceItem | Billing line items |
| Payment | Payment records |
| PharmacyInventory | Drug stock levels |
| StockTransaction | Stock movements |
| DispenseRecord | Dispensing records |
| DispenseItem | Dispensed medication items |
| InsuranceProvider | Insurance companies |
| PatientInsurance | Patient policies |
| InsuranceClaim | Claims submissions |
| ClaimDocument | Claim attachments |
| AIRequest | AI service request log |
| Notification | User notifications |
| NotificationPreference | Channel preferences |

---

## 7. API Design

### 7.1 API Conventions
- Base URL: `/api/v1/`
- Format: JSON
- Authentication: Bearer JWT
- Pagination: Offset-based with configurable page size
- Filtering: Django-filter querystring params
- Error format: `{"error": {"code": "ERROR_CODE", "message": "Human-readable"}}`
- Versioned: `/api/v1/` prefix

### 7.2 Endpoint Groups

| Prefix | Module | Auth |
|--------|--------|------|
| `/api/v1/auth/` | Authentication, Registration, Profile | Public/Authenticated |
| `/api/v1/rbac/` | Roles, Permissions, Users, Invitations | Authenticated + RBAC |
| `/api/v1/patients/` | Patient CRUD + Search | Authenticated + RBAC |
| `/api/v1/appointments/` | Scheduling + Doctor Profiles | Authenticated + RBAC |
| `/api/v1/visits/` | Medical Records (SOAP) | Authenticated + RBAC |
| `/api/v1/prescriptions/` | Medications + Prescriptions | Authenticated + RBAC |
| `/api/v1/lab/` | Lab Orders + Results | Authenticated + RBAC |
| `/api/v1/billing/` | Invoices + Payments | Authenticated + RBAC |
| `/api/v1/pharmacy/` | Inventory + Dispensing | Authenticated + RBAC |
| `/api/v1/insurance/` | Providers + Claims | Authenticated + RBAC |
| `/api/v1/ai/` | AI Requests | Authenticated + RBAC |
| `/api/v1/notifications/` | Notifications | Authenticated |
| `/api/v1/audit/` | Audit Log (read-only) | Authenticated + Admin |

---

## 8. Security & Compliance

### 8.1 Authentication Flow
```
Register/Login → JWT (access + refresh) → Bearer header on every request
                                                    │
                                        Middleware validates token
                                        Resolves tenant from domain
                                        Loads RBAC permissions
                                                    │
                                        View checks permission decorators
```

### 8.2 Data Protection Layers

1. **Network**: HTTPS/TLS in production
2. **Authentication**: JWT with short-lived access tokens (1 day dev, 15 min prod)
3. **Authorization**: Granular RBAC (resource:action)
4. **Data Isolation**: PostgreSQL schema-per-tenant
5. **Encryption**: Fernet for PII fields
6. **Audit**: Every significant action logged immutably
7. **Soft Delete**: Medical records never permanently deleted

### 8.3 HIPAA Alignment

| HIPAA Requirement | Implementation |
|-------------------|----------------|
| Access Controls | RBAC with granular permissions |
| Audit Controls | Immutable audit log with field-level changes |
| Integrity Controls | Signed visits are immutable |
| Transmission Security | HTTPS + JWT |
| Unique User Identification | UUID-based, per-tenant profiles |
| Emergency Access | PIN-based quick verification |
| Automatic Logoff | Short-lived tokens |
| Encryption | Fernet for sensitive fields |

---

## 9. Current Limitations

| # | Limitation | Impact |
|---|-----------|--------|
| 1 | No real-time WebSocket updates | Polling for new notifications |
| 2 | SMS/Push channels are placeholders | Only email + in-app actually send |
| 3 | No file upload for documents (MinIO configured but not wired to frontend) | Can't attach images/documents |
| 4 | No appointment calendar view (list only) | Less intuitive scheduling |
| 5 | No drug interaction checking | Safety risk for prescriptions |
| 6 | No telehealth video integration | Appointment type exists but no video |
| 7 | No patient portal (patient-facing app) | Patients can't self-service |
| 8 | No automated appointment reminders | Manual notifications only |
| 9 | No report generation (PDF invoices, lab reports) | Can't print/download |
| 10 | No mobile app | Web-only |
| 11 | AI integration requires external service setup | Not functional out-of-box |
| 12 | No payment gateway integration | Manual payment recording only |
| 13 | No ICD-10 code lookup/autocomplete | Manual entry |
| 14 | No FHIR/HL7 interoperability | Can't exchange data with other systems |

---

## 10. Future Work & Market Differentiation

### 10.1 Phase 1 — Critical Enhancements (1-3 months)

| # | Feature | Business Impact | Differentiation |
|---|---------|----------------|-----------------|
| 1 | **Real-time WebSocket notifications** | Instant alerts for critical lab results, appointment changes | Table stakes for modern healthcare |
| 2 | **PDF report generation** | Print invoices, lab reports, prescriptions, visit summaries | Essential for paper workflows in clinics |
| 3 | **Patient Portal** | Patients view appointments, results, invoices, request refills | Reduces staff workload by 30-40% |
| 4 | **Appointment Calendar View** (drag-drop, week/day views) | Visual scheduling for receptionists | Major UX improvement |
| 5 | **Automated appointment reminders** (SMS/Email, 24h before) | Reduces no-shows by 30-50% | Direct revenue impact |
| 6 | **Drug interaction checker** (FDA database integration) | Patient safety, reduces adverse events | Liability protection |
| 7 | **ICD-10 autocomplete** with search | Faster diagnosis coding, billing accuracy | Workflow efficiency |

### 10.2 Phase 2 — Competitive Advantages (3-6 months)

| # | Feature | Business Impact | Differentiation |
|---|---------|----------------|-----------------|
| 8 | **Telehealth video integration** (WebRTC/Daily.co) | Remote consultations, pandemic-ready | 40% of consultations going virtual |
| 9 | **AI Clinical Decision Support** (symptom → diagnosis suggestions) | Assists doctors with differential diagnosis | Unique AI-powered feature |
| 10 | **AI Medical Transcription** (voice → SOAP notes) | Doctors dictate instead of type, saves 2-3 hours/day | Massive time savings, premium feature |
| 11 | **Smart Scheduling AI** (predict no-shows, auto-fill cancellations) | Optimize clinic utilization | Advanced ML differentiation |
| 12 | **Payment Gateway** (Stripe/PayPal/local gateways) | Online payments, automated invoicing | Revenue acceleration |
| 13 | **Multi-language support** (i18n) | Arabic, French, Spanish markets | Expand TAM significantly |
| 14 | **White-label support** (custom branding per tenant) | Clinics use their own brand | Premium tier feature |
| 15 | **Mobile app** (React Native) | On-the-go access for doctors | Expected by modern users |

### 10.3 Phase 3 — Market Disruption (6-12 months)

| # | Feature | Business Impact | Differentiation |
|---|---------|----------------|-----------------|
| 16 | **FHIR R4 / HL7 interoperability** | Exchange data with other EMRs, insurance, labs | Enterprise requirement, rare in SaaS |
| 17 | **AI Predictive Analytics** | Predict patient readmission, disease progression | Data-driven medicine, unique selling point |
| 18 | **Chronic Disease Management Programs** | Automated care plans, medication adherence tracking | Long-term patient engagement |
| 19 | **Population Health Dashboard** | Aggregate analytics across patient populations | Public health compliance, enterprise feature |
| 20 | **Automated Insurance Pre-Authorization** | Auto-submit prior auth, reduce denials | Saves staff 2-3 hours/day |
| 21 | **Blockchain-verified Medical Certificates** | Tamper-proof sick notes, prescriptions, vaccination records | Innovation differentiator |
| 22 | **IoT Device Integration** | Auto-capture vitals from connected devices (BP monitors, glucometers) | Reduces manual data entry |
| 23 | **AI Radiology Assistant** | Auto-detect anomalies in X-rays/CT scans | Premium AI feature, high value |
| 24 | **Multi-facility Analytics** | Cross-tenant reporting for hospital chains | Enterprise tier feature |
| 25 | **Clinical Trial Management** | Protocol adherence, patient matching, data collection | Niche but high-value vertical |

### 10.4 Unique Market Position Strategy

**What makes MedFlow Pro stand out:**

1. **True Multi-Tenancy with Full Isolation** — Most competitors use shared tables with `tenant_id` filtering (leak-prone). We use PostgreSQL schema isolation — same security as separate databases, with shared infrastructure cost efficiency.

2. **AI-First Clinical Workflows** — Not just AI as a feature, but AI deeply embedded in:
   - Prescription OCR (scan paper prescriptions)
   - Lab result interpretation (auto-highlight concerning values)
   - Clinical decision support (suggest diagnoses)
   - Voice-to-SOAP transcription (future)
   - Smart scheduling (future)

3. **Complete Vertical Integration** — One platform covers EMR + Pharmacy + Lab + Billing + Insurance + AI + Referrals. Competitors typically specialize in one area, forcing clinics to use 3-5 different systems.

4. **Developer-Friendly Architecture** — Modular monolith means:
   - Easy to add features (new Django app)
   - Easy to extract microservices when needed
   - Clean API (OpenAPI documented)
   - TypeScript frontend with strict types

5. **Compliance by Design** — HIPAA/regulatory compliance isn't an afterthought:
   - Immutable audit logs baked in
   - Encryption by default
   - Soft-delete everywhere
   - Schema isolation
   - Signed (immutable) clinical records

### 10.5 Revenue Model Recommendations

| Tier | Target | Features | Pricing |
|------|--------|----------|---------|
| **Free** | Solo practitioners | 1 user, 50 patients, basic EMR | $0/mo |
| **Pro** | Small clinics (2-10 staff) | Unlimited users, full features, email support | $49-99/mo |
| **Enterprise** | Hospitals, chains | Multi-facility, SSO, API access, SLA, priority support | $299-999/mo |
| **AI Add-on** | All tiers | Transcription, decision support, smart scheduling | $29-99/mo/user |

---

## Appendix A: Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 19 | UI framework |
| Frontend | Vite 6 | Build tool |
| Frontend | TypeScript | Type safety |
| Frontend | Tailwind CSS | Styling |
| Frontend | Framer Motion | Animations |
| Frontend | Recharts | Data visualization |
| Frontend | TanStack Query | Server state management |
| Frontend | Zustand | Client state management |
| Frontend | React Hook Form + Zod | Form handling + validation |
| Frontend | Axios | HTTP client |
| Backend | Django 5.x | Web framework |
| Backend | Django REST Framework | API layer |
| Backend | django-tenants | Multi-tenancy |
| Backend | django-filter | Queryset filtering |
| Backend | drf-spectacular | OpenAPI docs |
| Backend | SimpleJWT | Token authentication |
| Backend | Celery | Async task queue |
| Backend | structlog | Structured logging |
| Backend | django-prometheus | Metrics |
| Database | PostgreSQL | Primary data store |
| Storage | MinIO (S3-compatible) | File/document storage |
| Auth | Keycloak | Identity provider (optional) |
| Queue | RabbitMQ | Message broker for Celery |
| Infra | Docker + Docker Compose | Containerization |
| Infra | Nginx | Reverse proxy |

---

## Appendix B: Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Nginx (Reverse Proxy)                │
│                    SSL Termination + Static Files             │
└──────────────┬────────────────────────────┬─────────────────┘
               │                            │
    ┌──────────▼──────────┐     ┌──────────▼──────────┐
    │   Django (Gunicorn)  │     │   React (Static)    │
    │   Port 8000          │     │   Port 5173 (dev)   │
    └──────────┬───────────┘     └─────────────────────┘
               │
    ┌──────────▼──────────┐
    │     PostgreSQL       │
    │   (Schema/Tenant)    │
    └──────────────────────┘
               │
    ┌──────────▼──────────┐     ┌─────────────────────┐
    │   RabbitMQ (Queue)   │────▶│   Celery Workers    │
    └──────────────────────┘     └─────────────────────┘
               │
    ┌──────────▼──────────┐     ┌─────────────────────┐
    │   MinIO (S3)         │     │   Keycloak (SSO)    │
    └──────────────────────┘     └─────────────────────┘
```

---

*End of Document*
