# Healthcare SaaS — Complete API Testing Guide

> **Swagger UI** → [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
> **OpenAPI JSON** → [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)
>
> **162 endpoints** across **16 modules** — this guide walks through every API in logical order.

---

## Table of Contents

1. [Prerequisites & Setup](#1-prerequisites--setup)
2. [Phase 1 — Authentication](#2-phase-1--authentication)
3. [Phase 2 — Tenant / Organization Setup](#3-phase-2--tenant--organization-setup)
4. [Phase 3 — Team Members (Roles)](#4-phase-3--team-members-roles)
5. [Phase 4 — Patient Registration](#5-phase-4--patient-registration)
6. [Phase 5 — Doctor Profiles & Appointments](#6-phase-5--doctor-profiles--appointments)
7. [Phase 6 — Clinical Visit (EMR)](#7-phase-6--clinical-visit-emr)
8. [Phase 7 — Prescriptions & Medications](#8-phase-7--prescriptions--medications)
9. [Phase 8 — Lab Orders & Results](#9-phase-8--lab-orders--results)
10. [Phase 9 — Billing & Invoices](#10-phase-9--billing--invoices)
11. [Phase 10 — Pharmacy](#11-phase-10--pharmacy)
12. [Phase 11 — Insurance Claims](#12-phase-11--insurance-claims)
13. [Phase 12 — Referrals (Cross-Tenant)](#13-phase-12--referrals-cross-tenant)
14. [Phase 13 — Notifications](#14-phase-13--notifications)
15. [Phase 14 — AI Integration](#15-phase-14--ai-integration)
16. [Phase 15 — Audit Logs](#16-phase-15--audit-logs)
17. [Phase 16 — Health Checks & Monitoring](#17-phase-16--health-checks--monitoring)
18. [Quick Reference — All Endpoints](#18-quick-reference--all-endpoints)

---

## 1. Prerequisites & Setup

### Start the dev server

```bash
cd /media/mohamed/New\ Volume/medical/medical
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

### Open Swagger UI

Navigate to **http://localhost:8000/api/docs/**

### How to Authenticate in Swagger

1. Call `POST /api/v1/auth/login/` (or register first)
2. Copy the `access` token from the response
3. Click the **🔒 Authorize** button (top-right of Swagger UI)
4. Enter: `Bearer <your_access_token>`
5. Click **Authorize** → all subsequent requests include the JWT

### Tenant Header (Multi-Tenancy)

This app uses **schema-per-tenant** with domain-based routing. For local dev:
- The **public** tenant is used by default on `localhost`
- After creating an org, you access it via its domain (e.g., `acme.localhost:8000`)
- If using Swagger, all tenant-scoped API calls go through the primary domain

---

## 2. Phase 1 — Authentication

Test the full auth lifecycle first.

### 2.1 Register a User (Owner)

```
POST /api/v1/auth/register/
```
```json
{
  "email": "admin@clinic.com",
  "password": "SecurePass123!",
  "first_name": "Ahmed",
  "last_name": "Hassan"
}
```
**Expected:** `201` — returns `user` object + `tokens.access` / `tokens.refresh`
**Save:** Copy `access` token → use in Authorize button.

### 2.2 Login

```
POST /api/v1/auth/login/
```
```json
{
  "email": "admin@clinic.com",
  "password": "SecurePass123!"
}
```
**Expected:** `200` — returns `user`, `memberships` (empty initially), `tokens`

### 2.3 Refresh Token

```
POST /api/v1/auth/token/refresh/
```
```json
{
  "refresh": "<refresh_token_from_login>"
}
```
**Expected:** `200` — returns new `access` token

### 2.4 Get Profile

```
GET /api/v1/auth/me/
```
**Expected:** `200` — user profile with `memberships` array

### 2.5 Update Profile

```
PATCH /api/v1/auth/me/
```
```json
{
  "first_name": "Ahmed",
  "phone": "+201001234567"
}
```
**Expected:** `200` — updated profile

### 2.6 Generate API Key

```
POST /api/v1/auth/api-keys/
```
**Expected:** `201` — returns `api_key` (shown once) + message

### 2.7 Revoke API Key

```
DELETE /api/v1/auth/api-keys/
```
**Expected:** `200` — `"API key revoked successfully."`

---

## 3. Phase 2 — Tenant / Organization Setup

### 3.1 Create Organization

```
POST /api/v1/tenants/
```
```json
{
  "name": "Cairo Medical Center",
  "type": "clinic",
  "license_number": "LIC-2024-001",
  "phone": "+20212345678",
  "email": "info@cairomedical.com",
  "address": "123 Tahrir Square, Cairo",
  "domain_url": "cairo-medical"
}
```
**Expected:** `201` — creates org + tenant schema + domain. The creator automatically becomes `owner`.

> **Type options:** `clinic`, `hospital`, `lab`

### 3.2 List My Organizations

```
GET /api/v1/tenants/
```
**Expected:** `200` — array of orgs the current user belongs to

### 3.3 Get Organization Detail

```
GET /api/v1/tenants/{org_id}/
```
**Expected:** `200` — full org details

### 3.4 Update Organization

```
PATCH /api/v1/tenants/{org_id}/
```
```json
{
  "phone": "+20211111111",
  "subscription_plan": "pro"
}
```
**Expected:** `200` — updated org (owner/admin only)

---

## 4. Phase 3 — Team Members (Roles)

### 4.1 Register Additional Users

Register users for each role you want to test:

```
POST /api/v1/auth/register/
```
Create users with emails like:
- `doctor@clinic.com` (will become doctor)
- `nurse@clinic.com` (will become nurse)
- `reception@clinic.com` (will become receptionist)
- `lab@clinic.com` (will become lab_tech)
- `billing@clinic.com` (will become billing_staff)

### 4.2 Invite Members to Organization

Using the **owner** token:

```
POST /api/v1/tenants/{org_id}/invite/
```
```json
{
  "email": "doctor@clinic.com",
  "role": "doctor"
}
```

Repeat for each role:
| Email | Role |
|---|---|
| `doctor@clinic.com` | `doctor` |
| `nurse@clinic.com` | `nurse` |
| `reception@clinic.com` | `receptionist` |
| `lab@clinic.com` | `lab_tech` |
| `billing@clinic.com` | `billing_staff` |

> **Role options:** `owner`, `admin`, `doctor`, `nurse`, `receptionist`, `lab_tech`, `billing_staff`

### 4.3 List Members

```
GET /api/v1/tenants/{org_id}/members/
```
**Expected:** `200` — array of membership objects with roles

### 4.4 Update Member Role

```
PATCH /api/v1/tenants/{org_id}/members/{member_id}/
```
```json
{
  "role": "admin"
}
```

### 4.5 Remove Member

```
DELETE /api/v1/tenants/{org_id}/members/{member_id}/
```
**Expected:** `200` (cannot remove last owner)

---

## 5. Phase 4 — Patient Registration

> **Required role:** `receptionist` or above. Login as the receptionist user.

### 5.1 Register a Patient

```
POST /api/v1/patients/
```
```json
{
  "first_name": "Mohamed",
  "last_name": "Ali",
  "date_of_birth": "1990-05-15",
  "gender": "male",
  "phone": "+201501234567",
  "email": "mohamed.ali@email.com",
  "address": "45 Nile Street, Cairo",
  "emergency_contact_name": "Fatma Ali",
  "emergency_contact_phone": "+201509876543",
  "blood_type": "A+",
  "allergies": "Penicillin"
}
```
**Expected:** `201` — returns patient with auto-generated `medical_record_number`
**Save:** the `id` for subsequent steps

> **Gender options:** `male`, `female`, `other`

### 5.2 List Patients

```
GET /api/v1/patients/
```
**Supports:** search (`?search=Mohamed`), ordering (`?ordering=-registered_at`), filtering

### 5.3 Get Patient Detail

```
GET /api/v1/patients/{patient_id}/
```

### 5.4 Update Patient

```
PATCH /api/v1/patients/{patient_id}/
```
```json
{
  "phone": "+201501111111"
}
```

### 5.5 Get Patient Sub-Resources

> **Required role:** `doctor` for visits/prescriptions/lab-results, `billing_staff` for invoices

```
GET /api/v1/patients/{patient_id}/visits/
GET /api/v1/patients/{patient_id}/prescriptions/
GET /api/v1/patients/{patient_id}/lab-results/
GET /api/v1/patients/{patient_id}/invoices/
```
**Expected:** `200` — paginated lists (empty initially, populated after later steps)

### 5.6 Soft-Delete Patient

```
DELETE /api/v1/patients/{patient_id}/
```
**Expected:** `204` — soft delete (sets `is_active=False`)

---

## 6. Phase 5 — Doctor Profiles & Appointments

### 6.1 Create Doctor Profile

> **Required role:** `receptionist` or above

```
POST /api/v1/appointments/doctors/
```
```json
{
  "user": "<doctor_user_id>",
  "specialization": "Cardiology",
  "consultation_fee": "250.00",
  "available_days": ["sunday", "monday", "tuesday", "wednesday", "thursday"],
  "working_hours_start": "09:00:00",
  "working_hours_end": "17:00:00",
  "slot_duration_minutes": 30
}
```
**Save:** the doctor profile `id`

### 6.2 List Doctors

```
GET /api/v1/appointments/doctors/
GET /api/v1/appointments/doctors/?search=Cardiology
```

### 6.3 Check Available Slots

```
GET /api/v1/appointments/available-slots/?doctor_id={doctor_user_id}&date=2026-05-13&duration_minutes=30
```
**Expected:** `200` — array of available ISO time slots

### 6.4 Book Appointment

```
POST /api/v1/appointments/
```
```json
{
  "patient_id": "<patient_id>",
  "doctor_id": "<doctor_user_id>",
  "scheduled_at": "2026-05-13T10:00:00Z",
  "duration_minutes": 30,
  "type": "in_person",
  "reason": "Chest pain evaluation"
}
```
**Expected:** `201` — appointment with status `scheduled`
**Save:** the appointment `id`

> **Type options:** `in_person`, `telehealth`

### 6.5 Appointment Lifecycle

Execute these in order:

```
POST /api/v1/appointments/{id}/confirm/     → status: confirmed
POST /api/v1/appointments/{id}/start/        → status: in_progress
POST /api/v1/appointments/{id}/complete/     → status: completed
```

### 6.6 Reschedule (instead of complete)

```
PATCH /api/v1/appointments/{id}/
```
```json
{
  "scheduled_at": "2026-05-14T14:00:00Z",
  "duration_minutes": 30
}
```

### 6.7 Cancel Appointment

```
POST /api/v1/appointments/{id}/cancel/
```
```json
{
  "reason": "Patient requested cancellation"
}
```

### 6.8 Mark No-Show

```
POST /api/v1/appointments/{id}/no-show/
```

### 6.9 List All Appointments

```
GET /api/v1/appointments/
GET /api/v1/appointments/?status=scheduled
GET /api/v1/appointments/?doctor={doctor_id}
GET /api/v1/appointments/?date_from=2026-05-13&date_to=2026-05-14
```

---

## 7. Phase 6 — Clinical Visit (EMR)

> **Required role:** `doctor`

### 7.1 Create a Visit

```
POST /api/v1/visits/
```
```json
{
  "patient_id": "<patient_id>",
  "doctor_id": "<doctor_user_id>",
  "visit_date": "2026-05-13T10:00:00Z",
  "chief_complaint": "Chest pain for 3 days, worse on exertion",
  "appointment_id": "<appointment_id>",
  "history_of_present_illness": "Patient reports substernal chest pain radiating to left arm. Started 3 days ago. Gets worse with physical activity. No shortness of breath.",
  "examination_notes": "BP: 140/90, HR: 88, RR: 18. Heart sounds normal, no murmurs.",
  "assessment": "Suspected angina pectoris. Rule out ACS.",
  "plan": "ECG, cardiac enzymes, chest X-ray. Start aspirin 81mg daily.",
  "follow_up_date": "2026-05-20"
}
```
**Expected:** `201` — visit record
**Save:** the visit `id`

### 7.2 Record Vitals

> **Required role:** `nurse` or above

```
POST /api/v1/visits/{visit_id}/vitals/
```
```json
{
  "blood_pressure_systolic": 140,
  "blood_pressure_diastolic": 90,
  "heart_rate": 88,
  "respiratory_rate": 18,
  "temperature": 37.0,
  "oxygen_saturation": 98,
  "weight": 82.5,
  "height": 175,
  "notes": "Patient slightly anxious"
}
```

### 7.3 Get Vitals

```
GET /api/v1/visits/{visit_id}/vitals/
```

### 7.4 Add Diagnosis

> **Required role:** `doctor`

```
POST /api/v1/visits/{visit_id}/diagnoses/
```
```json
{
  "icd_code": "I20.0",
  "description": "Unstable angina",
  "type": "primary",
  "notes": "Pending cardiac workup"
}
```

Add a secondary diagnosis:
```json
{
  "icd_code": "I10",
  "description": "Essential hypertension",
  "type": "secondary"
}
```

> **Diagnosis types:** `primary`, `secondary`, `rule_out`

### 7.5 Get Diagnoses

```
GET /api/v1/visits/{visit_id}/diagnoses/
```

### 7.6 Sign Visit (lock as final)

```
POST /api/v1/visits/{visit_id}/sign/
```
**Expected:** `200` — visit is now signed and locked

### 7.7 List All Visits

```
GET /api/v1/visits/
GET /api/v1/visits/?ordering=-visit_date
```

---

## 8. Phase 7 — Prescriptions & Medications

### 8.1 Create Medications (Catalog)

> **Required role:** `receptionist` or above

```
POST /api/v1/prescriptions/medications/
```
```json
{
  "name": "Aspirin",
  "generic_name": "Acetylsalicylic acid",
  "form": "tablet",
  "strength": "81mg",
  "route": "oral",
  "manufacturer": "Bayer"
}
```

Create a few more:
```json
{"name": "Atorvastatin", "generic_name": "Atorvastatin calcium", "form": "tablet", "strength": "20mg", "route": "oral", "manufacturer": "Pfizer"}
```
```json
{"name": "Metoprolol", "generic_name": "Metoprolol tartrate", "form": "tablet", "strength": "50mg", "route": "oral", "manufacturer": "AstraZeneca"}
```

> **Form options:** `tablet`, `capsule`, `syrup`, `injection`, `cream`, `drops`, `inhaler`
> **Route options:** `oral`, `iv`, `im`, `topical`, `sublingual`, `inhalation`

**Save:** each medication `id`

### 8.2 List / Search Medications

```
GET /api/v1/prescriptions/medications/
GET /api/v1/prescriptions/medications/?search=aspirin
```

### 8.3 Create Prescription

> **Required role:** `doctor`

```
POST /api/v1/prescriptions/
```
```json
{
  "patient_id": "<patient_id>",
  "doctor_id": "<doctor_user_id>",
  "visit_id": "<visit_id>",
  "notes": "Start cardiac medications immediately",
  "items": [
    {
      "medication_id": "<aspirin_id>",
      "dosage": "81mg",
      "frequency": "Once daily",
      "duration": "30 days",
      "quantity": 30,
      "instructions": "Take with food in the morning"
    },
    {
      "medication_id": "<atorvastatin_id>",
      "dosage": "20mg",
      "frequency": "Once daily at bedtime",
      "duration": "30 days",
      "quantity": 30,
      "instructions": "Take at night"
    },
    {
      "medication_id": "<metoprolol_id>",
      "dosage": "50mg",
      "frequency": "Twice daily",
      "duration": "30 days",
      "quantity": 60,
      "instructions": "Take morning and evening. Do not stop suddenly."
    }
  ]
}
```
**Expected:** `201` — prescription with items
**Save:** the prescription `id`

### 8.4 Update Prescription

> Only works if NOT yet dispensed.

```
PATCH /api/v1/prescriptions/{id}/
```
```json
{
  "notes": "Updated: added dietary advice"
}
```

### 8.5 Dispense Prescription

> **Required role:** `receptionist` or above

```
POST /api/v1/prescriptions/{id}/dispense/
```
**Expected:** `200` — marks `is_dispensed=True`, sets `dispensed_at`

### 8.6 List Prescriptions

```
GET /api/v1/prescriptions/
GET /api/v1/prescriptions/?ordering=-prescribed_at
```

---

## 9. Phase 8 — Lab Orders & Results

### 9.1 Create Lab Order

> **Required role:** `doctor`

```
POST /api/v1/lab-orders/
```
```json
{
  "patient_id": "<patient_id>",
  "doctor_id": "<doctor_user_id>",
  "visit_id": "<visit_id>",
  "priority": "urgent",
  "clinical_notes": "R/O ACS. Check cardiac enzymes and CBC",
  "tests": [
    {"test_name": "Troponin I", "test_code": "TROP"},
    {"test_name": "CK-MB", "test_code": "CKMB"},
    {"test_name": "Complete Blood Count", "test_code": "CBC"},
    {"test_name": "Lipid Panel", "test_code": "LIPID"}
  ]
}
```
**Expected:** `201` — lab order with status `ordered`
**Save:** the order `id` and individual `test` IDs from the response

> **Priority options:** `routine`, `urgent`, `stat`

### 9.2 Lab Order Lifecycle

> **Required role:** `lab_tech`

Execute in order:

```
POST /api/v1/lab-orders/{id}/collect/       → status: sample_collected
POST /api/v1/lab-orders/{id}/in_progress/   → status: processing
```

### 9.3 Record Test Results

> **Required role:** `lab_tech`

```
POST /api/v1/lab-orders/{order_id}/tests/{test_id}/result/
```
```json
{
  "value": "0.04",
  "unit": "ng/mL",
  "reference_range": "0.00 - 0.10",
  "flag": "normal",
  "notes": "Within normal limits"
}
```

Record another result (abnormal):
```json
{
  "value": "280",
  "unit": "mg/dL",
  "reference_range": "0 - 200",
  "flag": "high",
  "notes": "Elevated total cholesterol"
}
```

> **Flag options:** `normal`, `low`, `high`, `critical`

### 9.4 Verify Test Result

> **Required role:** `doctor`

```
POST /api/v1/lab-orders/{order_id}/tests/{test_id}/result/verify/
```
**Expected:** `200` — sets `verified_by_id` and `verified_at`

### 9.5 Complete Lab Order

> **Required role:** `lab_tech`

```
POST /api/v1/lab-orders/{id}/complete/      → status: completed
```

### 9.6 Cancel Lab Order

```
POST /api/v1/lab-orders/{id}/cancel/        → status: cancelled
```

### 9.7 List Lab Orders

```
GET /api/v1/lab-orders/
GET /api/v1/lab-orders/?status=ordered
GET /api/v1/lab-orders/?priority=urgent
```

---

## 10. Phase 9 — Billing & Invoices

> **Required role:** `billing_staff`

### 10.1 Create Invoice

```
POST /api/v1/invoices/
```
```json
{
  "patient_id": "<patient_id>",
  "items": [
    {
      "description": "Cardiology Consultation",
      "item_type": "consultation",
      "quantity": 1,
      "unit_price": "250.00"
    },
    {
      "description": "ECG",
      "item_type": "procedure",
      "quantity": 1,
      "unit_price": "150.00"
    },
    {
      "description": "Troponin I Test",
      "item_type": "lab_test",
      "quantity": 1,
      "unit_price": "120.00"
    },
    {
      "description": "Lipid Panel",
      "item_type": "lab_test",
      "quantity": 1,
      "unit_price": "100.00"
    }
  ],
  "tax_rate": "14.00",
  "discount_amount": "50.00",
  "due_date": "2026-06-13",
  "notes": "Visit on 2026-05-13"
}
```
**Expected:** `201` — invoice with status `draft`, auto-calculated `subtotal`, `tax_amount`, `total`
**Save:** the invoice `id`

> **Item types:** `consultation`, `procedure`, `lab_test`, `medication`, `other`

### 10.2 Invoice Lifecycle

```
POST /api/v1/invoices/{id}/finalize/         → status: issued
```

### 10.3 Record Payment (partial)

```
POST /api/v1/invoices/{id}/pay/
```
```json
{
  "amount": "300.00",
  "method": "cash",
  "reference": "RCPT-001",
  "notes": "Partial payment"
}
```
**Expected:** `201` — invoice moves to `partially_paid` if amount < total

> **Payment methods:** `cash`, `card`, `insurance`, `bank_transfer`, `online`

### 10.4 Record Full Payment

```
POST /api/v1/invoices/{id}/pay/
```
```json
{
  "amount": "<remaining_balance>",
  "method": "card",
  "reference": "TXN-12345"
}
```
**Expected:** `201` — invoice moves to `paid`

### 10.5 View Payments

```
GET /api/v1/invoices/{id}/payments/
```

### 10.6 Void / Cancel Invoice

```
POST /api/v1/invoices/{id}/void/
POST /api/v1/invoices/{id}/cancel/
```

### 10.7 Billing Summary Dashboard

> **Required role:** `owner` or `admin`

```
GET /api/v1/invoices/summary/
GET /api/v1/invoices/summary/?date_from=2026-05-01&date_to=2026-05-31
```
**Expected:** `200` — aggregated revenue data with `total_invoiced`, `total_paid`, `total_outstanding`, `by_payment_method`

### 10.8 List / Filter Invoices

```
GET /api/v1/invoices/
GET /api/v1/invoices/?status=issued
GET /api/v1/invoices/?ordering=-total
```

---

## 11. Phase 10 — Pharmacy

> **Required role:** `nurse` or above

### 11.1 Create Inventory Items

```
POST /api/v1/pharmacy/inventory/
```
```json
{
  "medication_id": "<aspirin_medication_id>",
  "batch_number": "BATCH-2026-001",
  "quantity_on_hand": 500,
  "reorder_level": 100,
  "unit_cost": "0.50",
  "expiry_date": "2027-12-31"
}
```

Repeat for other medications. **Save:** the inventory item `id`.

### 11.2 Receive Stock

```
POST /api/v1/pharmacy/inventory/{id}/receive/
```
```json
{
  "quantity": 200,
  "notes": "Received from supplier ABC"
}
```
**Expected:** `201` — stock transaction created, `quantity_on_hand` increased

### 11.3 Adjust Stock (correction)

```
POST /api/v1/pharmacy/inventory/{id}/adjust/
```
```json
{
  "quantity": -5,
  "reason": "Damaged units removed"
}
```

### 11.4 View Stock Transactions

```
GET /api/v1/pharmacy/inventory/{id}/transactions/
```

### 11.5 Check Low Stock

```
GET /api/v1/pharmacy/low-stock/
```
**Expected:** `200` — items where `quantity_on_hand <= reorder_level`

### 11.6 Dispense Queue

```
GET /api/v1/pharmacy/dispense-queue/
```
**Expected:** `200` — undispensed prescriptions

### 11.7 Dispense a Prescription

```
POST /api/v1/pharmacy/dispense/
```
```json
{
  "prescription_id": "<prescription_id>",
  "notes": "All items dispensed. Patient counseled on medication use."
}
```
**Expected:** `201` — dispense record with items, inventory deducted (FEFO)

### 11.8 List / Search Inventory

```
GET /api/v1/pharmacy/inventory/
GET /api/v1/pharmacy/inventory/?search=aspirin
GET /api/v1/pharmacy/inventory/?ordering=expiry_date
```

---

## 12. Phase 11 — Insurance Claims

### 12.1 Create Insurance Provider

```
POST /api/v1/insurance/providers/
```
```json
{
  "name": "National Health Insurance",
  "code": "NHI-001",
  "contact_email": "claims@nhi.gov",
  "contact_phone": "+20221234567",
  "address": "Ministry of Health, Cairo"
}
```
**Save:** the provider `id`

### 12.2 List / Search Providers

```
GET /api/v1/insurance/providers/
GET /api/v1/insurance/providers/?search=National
GET /api/v1/insurance/providers/?is_active=true
```

### 12.3 Add Patient Insurance Policy

```
POST /api/v1/insurance/policies/
```
```json
{
  "patient": "<patient_id>",
  "provider": "<provider_id>",
  "policy_number": "POL-2026-12345",
  "group_number": "GRP-100",
  "subscriber_name": "Mohamed Ali",
  "subscriber_relationship": "self",
  "effective_date": "2026-01-01",
  "expiration_date": "2026-12-31",
  "is_primary": true
}
```
**Save:** the policy `id`

> **Subscriber relationships:** `self`, `spouse`, `child`, `other`

### 12.4 List Patient Policies

```
GET /api/v1/insurance/policies/
```

### 12.5 File an Insurance Claim

```
POST /api/v1/insurance/claims/
```
```json
{
  "invoice": "<invoice_id>",
  "patient_insurance": "<policy_id>",
  "amount_claimed": "620.00",
  "notes": "Claim for cardiac evaluation visit"
}
```
**Expected:** `201` — claim with auto-generated `claim_number`, status `draft`
**Save:** the claim `id`

### 12.6 Insurance Claim Lifecycle

```
POST /api/v1/insurance/claims/{id}/submit/       → status: submitted
POST /api/v1/insurance/claims/{id}/review/        → status: in_review
```

**Approve:**
```
POST /api/v1/insurance/claims/{id}/approve/
```
```json
{
  "amount_approved": "620.00"
}
```

**OR Partially Approve:**
```
POST /api/v1/insurance/claims/{id}/partial-approve/
```
```json
{
  "amount_approved": "400.00"
}
```

**OR Deny:**
```
POST /api/v1/insurance/claims/{id}/deny/
```
```json
{
  "denial_reason": "Pre-authorization not obtained"
}
```

**Appeal (after denial or partial approval):**
```
POST /api/v1/insurance/claims/{id}/appeal/       → status: appealed → goes back to in_review
```

**Mark Paid (after approval):**
```
POST /api/v1/insurance/claims/{id}/mark-paid/    → status: paid
```

### 12.7 Upload Claim Documents

```
POST /api/v1/insurance/claims/{id}/documents/
```
```json
{
  "file_name": "medical_report.pdf",
  "file_path": "claims/2026/CLM-ABC123/medical_report.pdf",
  "content_type": "application/pdf",
  "description": "Attending physician's medical report"
}
```

### 12.8 Get Claim Documents

```
GET /api/v1/insurance/claims/{id}/documents/
```

### 12.9 Claims Summary

```
GET /api/v1/insurance/claims/summary/
```
**Expected:** `200` — `total_claims`, `total_claimed`, `total_approved`

### 12.10 Filter Claims

```
GET /api/v1/insurance/claims/?status=submitted
GET /api/v1/insurance/claims/?patient_insurance=<policy_id>
```

---

## 13. Phase 12 — Referrals (Cross-Tenant)

> Referrals work across tenants. You need **two organizations** to test fully.

### 13.1 Setup: Create Second Organization

Register another user and create a second org:

```
POST /api/v1/auth/register/
→ {"email": "admin@hospital.com", "password": "SecurePass123!", ...}

POST /api/v1/tenants/
→ {"name": "Nile Hospital", "type": "hospital", "domain_url": "nile-hospital", ...}
```

### 13.2 Request Connection

From Org A (Cairo Medical Center):

```
POST /api/v1/referrals/connections/request/
```
```json
{
  "to_tenant": "<nile_hospital_org_id>",
  "notes": "Requesting referral partnership for cardiology cases"
}
```
**Expected:** `201` — connection with status `pending`
**Save:** the connection `id`

### 13.3 Accept Connection

From Org B (Nile Hospital) — login as `admin@hospital.com`:

```
POST /api/v1/referrals/connections/{connection_id}/accept/
```
**Expected:** `200` — status changes to `active`, `established_at` set

### 13.4 List Connections

```
GET /api/v1/referrals/connections/
```

### 13.5 Create Referral

From Org A (as doctor):

```
POST /api/v1/referrals/
```
```json
{
  "to_tenant": "<nile_hospital_org_id>",
  "patient_summary": {
    "age": 35,
    "gender": "male",
    "chief_complaint": "Chest pain",
    "diagnosis": "Suspected ACS",
    "relevant_history": "Hypertension, elevated cholesterol",
    "current_medications": ["Aspirin 81mg", "Atorvastatin 20mg", "Metoprolol 50mg"]
  },
  "reason": "Patient needs cardiac catheterization not available at our facility",
  "priority": "urgent",
  "clinical_notes": "ECG shows ST depression in leads V4-V6. Troponin mildly elevated."
}
```
**Expected:** `201` — referral with status `draft`
**Save:** the referral `id`

> **Priority options:** `routine`, `urgent`, `stat`

### 13.6 Referral Lifecycle

```
POST /api/v1/referrals/{id}/submit/       → status: submitted
```

From Org B:
```
POST /api/v1/referrals/{id}/accept/        → status: accepted
POST /api/v1/referrals/{id}/start/         → status: in_progress
POST /api/v1/referrals/{id}/complete/      → status: completed
```

**OR Decline:**
```
POST /api/v1/referrals/{id}/decline/
```
```json
{
  "reason": "Cath lab under maintenance until next week"
}
```

**Cancel (by referring facility):**
```
POST /api/v1/referrals/{id}/cancel/
```

### 13.7 Add Notes (Communication)

```
POST /api/v1/referrals/{id}/notes/
```
```json
{
  "content": "Patient arrived, admission processed. Catheterization scheduled for tomorrow."
}
```

### 13.8 Get Notes

```
GET /api/v1/referrals/{id}/notes/
```

### 13.9 List Referrals

```
GET /api/v1/referrals/
```
Shows both sent and received referrals for the current tenant.

### 13.10 Suspend Connection

```
POST /api/v1/referrals/connections/{id}/suspend/
```

---

## 14. Phase 13 — Notifications

### 14.1 List Notifications

```
GET /api/v1/notifications/
```
**Expected:** `200` — notifications triggered by previous actions (appointments, lab results, etc.)

### 14.2 Get Single Notification

```
GET /api/v1/notifications/{id}/
```

### 14.3 Mark as Read

```
POST /api/v1/notifications/{id}/mark_read/
```

### 14.4 Mark All as Read

```
POST /api/v1/notifications/mark_all_read/
```
**Expected:** `200` — `{"marked_read": <count>}`

### 14.5 Get Unread Count

```
GET /api/v1/notifications/unread_count/
```
**Expected:** `200` — `{"unread_count": <number>}`

### 14.6 Get Notification Preferences

```
GET /api/v1/notifications/preferences/
```
**Expected:** `200` — user's channel preferences + quiet hours

### 14.7 Update Preferences

```
PATCH /api/v1/notifications/preferences/
```
```json
{
  "email_enabled": true,
  "sms_enabled": false,
  "push_enabled": false,
  "in_app_enabled": true,
  "quiet_hours_start": "22:00:00",
  "quiet_hours_end": "07:00:00"
}
```

### 14.8 WebSocket (Real-Time)

Connect via WebSocket for real-time notifications:

```
ws://localhost:8000/ws/notifications/?token=<jwt_access_token>
```

Events received:
- `new_notification` — when a new notification is created
- `unread_count_update` — when count changes

Send from client:
```json
{"type": "mark_read", "notification_id": "<uuid>"}
{"type": "mark_all_read"}
```

---

## 15. Phase 14 — AI Integration

> **Required role:** `doctor`
> Note: Requires an external AI service running. Requests will be queued via Celery.

### 15.1 Submit AI Request

```
POST /api/v1/ai/
```
```json
{
  "request_type": "lab_analysis",
  "input_data": {
    "test_results": [
      {"test": "Troponin I", "value": "0.04", "unit": "ng/mL", "flag": "normal"},
      {"test": "Total Cholesterol", "value": "280", "unit": "mg/dL", "flag": "high"},
      {"test": "LDL", "value": "180", "unit": "mg/dL", "flag": "high"}
    ]
  },
  "patient_id": "<patient_id>"
}
```
**Expected:** `202 Accepted` — task queued for processing  
**Save:** the request `id`

> **Request types:** `prescription_ocr`, `lab_analysis`, `radiology`

### 15.2 Check AI Request Status (Poll)

```
GET /api/v1/ai/{request_id}/
```
**Expected:** Status progresses from `pending` → `processing` → `completed` (or `failed`)

### 15.3 List AI Requests

```
GET /api/v1/ai/
```
Returns all AI requests made by the current user.

---

## 16. Phase 15 — Audit Logs

> **Required role:** `owner` or `admin`

### 16.1 List Audit Logs

```
GET /api/v1/audit-logs/
```
**Expected:** `200` — chronological log of all CRUD actions performed

### 16.2 Filter Audit Logs

```
GET /api/v1/audit-logs/?action=create
GET /api/v1/audit-logs/?resource_type=Patient
GET /api/v1/audit-logs/?user_id=<uuid>
```

### 16.3 Get Audit Log Detail

```
GET /api/v1/audit-logs/{id}/
```
**Expected:** `200` — includes `changes` diff, `ip_address`, `user_agent`

---

## 17. Phase 16 — Health Checks & Monitoring

These are **unauthenticated** endpoints.

### 17.1 Application Health

```
GET /health/
```
**Expected:** `200` — `{"status": "ok"}`

### 17.2 Database Health

```
GET /health/db/
```
**Expected:** `200` — `{"status": "ok", "database": "connected"}`

### 17.3 Redis Health

```
GET /health/redis/
```
**Expected:** `200` — `{"status": "ok", "redis": "connected"}`

### 17.4 Prometheus Metrics

```
GET /metrics
```
**Expected:** `200` — Prometheus-format metrics

---

## 18. Quick Reference — All Endpoints

### Auth (8 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register/` | Register new user |
| POST | `/api/v1/auth/login/` | Login → get JWT |
| POST | `/api/v1/auth/token/refresh/` | Refresh access token |
| GET | `/api/v1/auth/me/` | Get current profile |
| PATCH | `/api/v1/auth/me/` | Update profile |
| POST | `/api/v1/auth/verify-pin/` | Verify clinical PIN |
| POST | `/api/v1/auth/api-keys/` | Generate API key |
| DELETE | `/api/v1/auth/api-keys/` | Revoke API key |

### Tenants (8 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tenants/` | List my orgs |
| POST | `/api/v1/tenants/` | Create org |
| GET | `/api/v1/tenants/{id}/` | Get org detail |
| PATCH | `/api/v1/tenants/{id}/` | Update org |
| POST | `/api/v1/tenants/{id}/invite/` | Invite member |
| GET | `/api/v1/tenants/{id}/members/` | List members |
| PATCH | `/api/v1/tenants/{id}/members/{mid}/` | Update role |
| DELETE | `/api/v1/tenants/{id}/members/{mid}/` | Remove member |

### Patients (10 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/patients/` | List patients |
| POST | `/api/v1/patients/` | Register patient |
| GET | `/api/v1/patients/{id}/` | Patient detail |
| PUT | `/api/v1/patients/{id}/` | Full update |
| PATCH | `/api/v1/patients/{id}/` | Partial update |
| DELETE | `/api/v1/patients/{id}/` | Soft delete |
| GET | `/api/v1/patients/{id}/visits/` | Patient visits |
| GET | `/api/v1/patients/{id}/prescriptions/` | Patient prescriptions |
| GET | `/api/v1/patients/{id}/lab-results/` | Patient lab results |
| GET | `/api/v1/patients/{id}/invoices/` | Patient invoices |

### Appointments (18 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/appointments/doctors/` | List doctors |
| POST | `/api/v1/appointments/doctors/` | Create doctor profile |
| GET | `/api/v1/appointments/doctors/{id}/` | Doctor detail |
| PUT | `/api/v1/appointments/doctors/{id}/` | Update doctor |
| PATCH | `/api/v1/appointments/doctors/{id}/` | Partial update doctor |
| DELETE | `/api/v1/appointments/doctors/{id}/` | Delete doctor |
| GET | `/api/v1/appointments/` | List appointments |
| POST | `/api/v1/appointments/` | Book appointment |
| GET | `/api/v1/appointments/{id}/` | Appointment detail |
| PATCH | `/api/v1/appointments/{id}/` | Reschedule |
| POST | `/api/v1/appointments/{id}/confirm/` | Confirm |
| POST | `/api/v1/appointments/{id}/start/` | Start |
| POST | `/api/v1/appointments/{id}/complete/` | Complete |
| POST | `/api/v1/appointments/{id}/cancel/` | Cancel |
| POST | `/api/v1/appointments/{id}/no-show/` | Mark no-show |
| GET | `/api/v1/appointments/available-slots/` | Check available slots |

### Visits / EMR (11 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/visits/` | List visits |
| POST | `/api/v1/visits/` | Create visit |
| GET | `/api/v1/visits/{id}/` | Visit detail |
| PUT | `/api/v1/visits/{id}/` | Full update |
| PATCH | `/api/v1/visits/{id}/` | Partial update |
| DELETE | `/api/v1/visits/{id}/` | Delete visit |
| POST | `/api/v1/visits/{id}/sign/` | Sign (lock) visit |
| GET | `/api/v1/visits/{id}/vitals/` | Get vitals |
| POST | `/api/v1/visits/{id}/vitals/` | Record vitals |
| GET | `/api/v1/visits/{id}/diagnoses/` | Get diagnoses |
| POST | `/api/v1/visits/{id}/diagnoses/` | Add diagnosis |

### Prescriptions (13 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/prescriptions/medications/` | List medications |
| POST | `/api/v1/prescriptions/medications/` | Create medication |
| GET | `/api/v1/prescriptions/medications/{id}/` | Medication detail |
| PUT | `/api/v1/prescriptions/medications/{id}/` | Update medication |
| PATCH | `/api/v1/prescriptions/medications/{id}/` | Partial update |
| DELETE | `/api/v1/prescriptions/medications/{id}/` | Delete medication |
| GET | `/api/v1/prescriptions/` | List prescriptions |
| POST | `/api/v1/prescriptions/` | Create prescription |
| GET | `/api/v1/prescriptions/{id}/` | Prescription detail |
| PUT | `/api/v1/prescriptions/{id}/` | Update prescription |
| PATCH | `/api/v1/prescriptions/{id}/` | Partial update |
| DELETE | `/api/v1/prescriptions/{id}/` | Delete prescription |
| POST | `/api/v1/prescriptions/{id}/dispense/` | Dispense |

### Lab Orders (12 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/lab-orders/` | List lab orders |
| POST | `/api/v1/lab-orders/` | Create lab order |
| GET | `/api/v1/lab-orders/{id}/` | Lab order detail |
| PUT | `/api/v1/lab-orders/{id}/` | Update lab order |
| PATCH | `/api/v1/lab-orders/{id}/` | Partial update |
| DELETE | `/api/v1/lab-orders/{id}/` | Delete lab order |
| POST | `/api/v1/lab-orders/{id}/collect/` | Collect sample |
| POST | `/api/v1/lab-orders/{id}/in_progress/` | Start processing |
| POST | `/api/v1/lab-orders/{id}/complete/` | Complete order |
| POST | `/api/v1/lab-orders/{id}/cancel/` | Cancel order |
| POST | `/api/v1/lab-orders/{id}/tests/{tid}/result/` | Record result |
| POST | `/api/v1/lab-orders/{id}/tests/{tid}/result/verify/` | Verify result |

### Billing (12 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/invoices/summary/` | Revenue dashboard |
| GET | `/api/v1/invoices/` | List invoices |
| POST | `/api/v1/invoices/` | Create invoice |
| GET | `/api/v1/invoices/{id}/` | Invoice detail |
| PUT | `/api/v1/invoices/{id}/` | Update invoice |
| PATCH | `/api/v1/invoices/{id}/` | Partial update |
| DELETE | `/api/v1/invoices/{id}/` | Delete invoice |
| POST | `/api/v1/invoices/{id}/finalize/` | Finalize (issue) |
| POST | `/api/v1/invoices/{id}/pay/` | Record payment |
| POST | `/api/v1/invoices/{id}/cancel/` | Cancel invoice |
| POST | `/api/v1/invoices/{id}/void/` | Void invoice |
| GET | `/api/v1/invoices/{id}/payments/` | List payments |

### Notifications (7 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/notifications/` | List notifications |
| GET | `/api/v1/notifications/{id}/` | Notification detail |
| POST | `/api/v1/notifications/{id}/mark_read/` | Mark as read |
| POST | `/api/v1/notifications/mark_all_read/` | Mark all read |
| GET | `/api/v1/notifications/unread_count/` | Unread count |
| GET | `/api/v1/notifications/preferences/` | Get preferences |
| PATCH | `/api/v1/notifications/preferences/` | Update preferences |

### AI Integration (3 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/ai/` | List AI requests |
| POST | `/api/v1/ai/` | Submit AI request |
| GET | `/api/v1/ai/{id}/` | Check request status |

### Pharmacy (12 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/pharmacy/low-stock/` | Low stock items |
| GET | `/api/v1/pharmacy/dispense-queue/` | Dispense queue |
| POST | `/api/v1/pharmacy/dispense/` | Dispense prescription |
| GET | `/api/v1/pharmacy/inventory/` | List inventory |
| POST | `/api/v1/pharmacy/inventory/` | Create inventory item |
| GET | `/api/v1/pharmacy/inventory/{id}/` | Inventory detail |
| PUT | `/api/v1/pharmacy/inventory/{id}/` | Update inventory |
| PATCH | `/api/v1/pharmacy/inventory/{id}/` | Partial update |
| DELETE | `/api/v1/pharmacy/inventory/{id}/` | Delete inventory |
| POST | `/api/v1/pharmacy/inventory/{id}/receive/` | Receive stock |
| POST | `/api/v1/pharmacy/inventory/{id}/adjust/` | Adjust stock |
| GET | `/api/v1/pharmacy/inventory/{id}/transactions/` | Transaction history |

### Referrals (17 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/referrals/connections/` | List connections |
| GET | `/api/v1/referrals/connections/{id}/` | Connection detail |
| POST | `/api/v1/referrals/connections/request/` | Request connection |
| POST | `/api/v1/referrals/connections/{id}/accept/` | Accept connection |
| POST | `/api/v1/referrals/connections/{id}/suspend/` | Suspend connection |
| GET | `/api/v1/referrals/` | List referrals |
| POST | `/api/v1/referrals/` | Create referral |
| GET | `/api/v1/referrals/{id}/` | Referral detail |
| PATCH | `/api/v1/referrals/{id}/` | Update referral |
| POST | `/api/v1/referrals/{id}/submit/` | Submit referral |
| POST | `/api/v1/referrals/{id}/accept/` | Accept referral |
| POST | `/api/v1/referrals/{id}/decline/` | Decline referral |
| POST | `/api/v1/referrals/{id}/start/` | Start progress |
| POST | `/api/v1/referrals/{id}/complete/` | Complete referral |
| POST | `/api/v1/referrals/{id}/cancel/` | Cancel referral |
| GET | `/api/v1/referrals/{id}/notes/` | Get notes |
| POST | `/api/v1/referrals/{id}/notes/` | Add note |

### Insurance (26 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/insurance/providers/` | List providers |
| POST | `/api/v1/insurance/providers/` | Create provider |
| GET | `/api/v1/insurance/providers/{id}/` | Provider detail |
| PUT | `/api/v1/insurance/providers/{id}/` | Update provider |
| PATCH | `/api/v1/insurance/providers/{id}/` | Partial update |
| DELETE | `/api/v1/insurance/providers/{id}/` | Delete provider |
| GET | `/api/v1/insurance/policies/` | List policies |
| POST | `/api/v1/insurance/policies/` | Create policy |
| GET | `/api/v1/insurance/policies/{id}/` | Policy detail |
| PUT | `/api/v1/insurance/policies/{id}/` | Update policy |
| PATCH | `/api/v1/insurance/policies/{id}/` | Partial update |
| DELETE | `/api/v1/insurance/policies/{id}/` | Delete policy |
| GET | `/api/v1/insurance/claims/` | List claims |
| POST | `/api/v1/insurance/claims/` | File claim |
| GET | `/api/v1/insurance/claims/{id}/` | Claim detail |
| PATCH | `/api/v1/insurance/claims/{id}/` | Update claim |
| POST | `/api/v1/insurance/claims/{id}/submit/` | Submit claim |
| POST | `/api/v1/insurance/claims/{id}/review/` | Start review |
| POST | `/api/v1/insurance/claims/{id}/approve/` | Approve claim |
| POST | `/api/v1/insurance/claims/{id}/partial-approve/` | Partially approve |
| POST | `/api/v1/insurance/claims/{id}/deny/` | Deny claim |
| POST | `/api/v1/insurance/claims/{id}/appeal/` | Appeal denial |
| POST | `/api/v1/insurance/claims/{id}/mark-paid/` | Mark as paid |
| GET | `/api/v1/insurance/claims/{id}/documents/` | List documents |
| POST | `/api/v1/insurance/claims/{id}/documents/` | Upload document |
| GET | `/api/v1/insurance/claims/summary/` | Claims summary |

### Audit Logs (2 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/audit-logs/` | List audit logs |
| GET | `/api/v1/audit-logs/{id}/` | Audit log detail |

### Health & Monitoring (4 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health/` | App health |
| GET | `/health/db/` | Database health |
| GET | `/health/redis/` | Redis health |
| GET | `/metrics` | Prometheus metrics |

---

## Status Workflow Diagrams

### Appointment States
```
scheduled → confirmed → in_progress → completed
    ↓           ↓           ↓
 cancelled   cancelled   cancelled
    ↓
 no_show
```

### Lab Order States
```
ordered → sample_collected → processing → completed
   ↓                                         
cancelled                                    
```

### Invoice States
```
draft → issued → partially_paid → paid
          ↓
       overdue
          ↓
       cancelled
```

### Insurance Claim States
```
draft → submitted → in_review → approved → paid
                        ↓         
                      denied → appealed → in_review (loop)
                        ↓
                   partially_approved → paid
                        ↓
                     appealed
```

### Referral States
```
draft → submitted → accepted → in_progress → completed
           ↓
        declined
           ↓
       cancelled (any state except completed/declined)
```

---

## Role Permissions Summary

| Role | What They Can Do |
|------|-----------------|
| **owner** | Everything + billing summary + audit logs + member management |
| **admin** | Everything + billing summary + audit logs + member management |
| **doctor** | Visits, prescriptions, lab orders, AI requests, verify lab results, patient sub-resources |
| **nurse** | Record vitals, pharmacy operations, view labs |
| **receptionist** | Patient CRUD, appointments, doctor profiles, medications, dispense prescriptions |
| **lab_tech** | Lab order status transitions, record test results |
| **billing_staff** | Invoice CRUD, payments, patient invoices |

---

## Tips for Testing

1. **Follow the phases in order** — each phase builds on data created in previous phases
2. **Switch users** when testing role-based access — login as different role users
3. **Test negative cases** — try invalid transitions (e.g., complete before start), unauthorized access
4. **Use Swagger "Try it out"** — every endpoint has an interactive form
5. **Check paginated responses** — list endpoints return `{count, next, previous, results}`
6. **Use query params** — `?search=`, `?ordering=`, `?status=` on list endpoints
