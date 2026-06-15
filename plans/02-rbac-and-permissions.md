# 02 — RBAC & Permissions (foundational)

Covers items **#8** (RBAC enforced everywhere; vitals by Nurse **and** Doctor) and **#18** (a logged-in
user only sees/does what their role allows). **Implement this file first** — later files reference the
new permission strings defined here.

---

## Current state (verified)

There IS a working RBAC engine:
- Models: `Role`, `Permission(name="resource:action", resource=...)`, `RolePermission` (M2M),
  `TenantUser.role` (one role per user). `apps/rbac/models.py`.
- Seeding: `RBACService.seed_roles_and_permissions()` (`apps/rbac/services.py`) runs on tenant
  creation and defines 7 system roles (Admin, Doctor, Nurse, Receptionist, Lab Technician,
  Pharmacist, Billing Staff) with permission sets.
- Enforcement: `apps/rbac/permissions.py` provides `IsActiveTenantUser`, `HasPermission('x:y')`,
  `require_permission('x:y')`, `@check_permission('x:y')`, plus **legacy aliases**
  (`IsDoctor`, `IsNurseOrAbove`, `IsReceptionistOrAbove`, `IsBillingStaff`, `IsLabTech`,
  `CanReadPatients`, …).
- Frontend: `authStore.permissions: string[]`, `hasPermission()`, and `Sidebar.tsx` hides nav items
  the user lacks.

### Three problems to fix
1. **Semantic mismatch in legacy aliases.** `IsDoctor` is literally `HasPermission('medical_records:write')`,
   `IsNurseOrAbove` is `patients:write`, `IsReceptionistOrAbove` is `appointments:write`. These
   "work" by coincidence and make intent unreadable. We replace per-endpoint usage with explicit
   `require_permission('<correct resource:action>')`.
2. **Unenforced endpoints (gaps):**
   - `apps/rbac/views.py` — Role/TenantUser/Invitation viewsets only check `IsActiveTenantUser`
     (any active user can edit roles/users). Must require `roles:*` / `users:*` / `invitations:*`.
   - `apps/insurance/views.py` — only `IsAuthenticated`. Must require `insurance:read|write`.
   - `apps/rbac/views.py` seed endpoint — weak `is_staff` check.
3. **Frontend only gates the sidebar.** Direct navigation to `/billing` (etc.) and action buttons are
   NOT gated (#18).

---

## Step 1 — Define the full permission matrix

Update `RBACService.seed_roles_and_permissions()` (and the demo seeder
`apps/tenants/management/commands/seed_data.py` if it independently defines perms) to this matrix.
**Add new resources** introduced by later files so they exist before those features ship:
`doctor_availability`, `customers`, `pharmacy_orders`, `radiology`, plus a granular
`medical_records:write_vitals`.

### Resources & actions (canonical list)
```
patients:           read, write, delete
appointments:       read, write, delete
doctor_availability:read, write
medical_records:    read, write, write_vitals          # write_vitals is the new granular perm (#8)
prescriptions:      read, write
lab_results:        read, write, result
radiology:          read, write, result                # new app (file 07)
pharmacy:           read, write                         # inventory
pharmacy_orders:    read, write                         # ordering/POS (file 06)
customers:          read, write                         # walk-in customers (file 05)
billing:            read, write, export
insurance:          read, write
notifications:      read, write
ai:                 read, write
reports:            read, export
users:              read, write
roles:              read, write
invitations:        read, write
settings:           read, write
audit:              read
```

### Role → permission grid
Legend: R=read, W=write, D=delete, and explicit extras named.

| Resource | Admin | Doctor | Nurse | Receptionist | Lab Tech | Pharmacist | Billing |
|---|---|---|---|---|---|---|---|
| patients | R W D | R W | R W | R W | R | R | R |
| appointments | R W D | R W | R W | R W D | – | – | R |
| doctor_availability | R W | R W (own) | R | R W | – | – | – |
| medical_records | R W | R W | R | – | R | – | – |
| medical_records:write_vitals | ✅ | ✅ | ✅ | – | – | – | – |
| prescriptions | R W | R W | R | – | – | R | – |
| lab_results | R W result | R W | R | – | R W result | – | – |
| radiology | R W result | R W | R | – | R (or W result if radiographer) | – | – |
| pharmacy (inventory) | R W | R | R | – | – | R W | – |
| pharmacy_orders | R W | – | – | R | – | R W | R |
| customers | R W | – | R | R W | R W | R W | R |
| billing | R W export | R | – | R W | – | R | R W export |
| insurance | R W | R | – | R | – | – | R W |
| notifications | R W | R W | R W | R W | R W | R W | R W |
| ai | R W | R W | R | – | R | – | – |
| reports | R export | R | – | – | R | R | R export |
| users | R W | – | – | – | – | – | – |
| roles | R W | – | – | – | – | – | – |
| invitations | R W | – | – | – | – | – | – |
| settings | R W | – | – | – | – | – | – |
| audit | R | – | – | – | – | – | – |

> Notes:
> - **#8 vitals:** `medical_records:write_vitals` is granted to Admin, Doctor, **and Nurse**. The
>   vitals endpoint will require exactly this permission (not the coincidental `patients:write`).
> - "Doctor … (own)" for availability means the API restricts a doctor to editing their own
>   `DoctorAvailability` rows (enforced in the service by matching `DoctorProfile.user_id`), while
>   Admin/Receptionist manage anyone's.
> - Adjust the lab-tech/radiographer split to the clinic's reality; the grid is the default.

### Seeding requirements
- Use `get_or_create` for every Permission and Role (idempotent — safe to re-run).
- After editing the matrix, re-seed existing tenants. Provide/run a management command, e.g.
  `python manage.py reseed_permissions` that loops tenants and calls
  `RBACService.seed_roles_and_permissions()` inside each `schema_context`. (If `seed_data`/`seed`
  endpoints already do this, reuse them.) **System roles must stay `is_system=True` and keep their
  existing permissions plus the new ones — do not drop custom permissions admins may have added.**

---

## Step 2 — Make permission classes explicit & add the vitals permission

In `apps/rbac/permissions.py`:
- Keep `HasPermission`, `IsActiveTenantUser`, `require_permission`, `@check_permission`.
- Add a class for the new granular vitals permission for readability:
  ```python
  class CanRecordVitals(HasPermission):
      def __init__(self):
          super().__init__('medical_records:write_vitals')
  ```
- Leave legacy aliases in place (don't break imports) but **stop using them in new/edited code**;
  prefer `require_permission('resource:action')` inside each viewset's `get_permissions()`.

### #8 — vitals by Nurse and Doctor
**File:** `apps/medical_records/views.py` — in `get_permissions()`, change the `record_vitals` action
from `IsNurseOrAbove()` to `require_permission('medical_records:write_vitals')` (or `CanRecordVitals()`).
Doctor and Nurse both have it; Receptionist/Lab/Pharmacist/Billing do not. The other visit actions
(create/update/sign/add_diagnosis) require `medical_records:write` (Doctor only, per matrix — Nurse
is read on medical_records but has the separate vitals perm).

---

## Step 3 — Close the backend enforcement gaps

### `apps/rbac/views.py`
Add `get_permissions()` to each management viewset (compose with `IsAuthenticated, IsActiveTenantUser`):
- `RoleViewSet`: list/retrieve → `roles:read`; create/update/partial_update/destroy → `roles:write`.
- `PermissionViewSet`: list/retrieve → `roles:read`.
- `TenantUserViewSet`: list/retrieve → `users:read`; mutations + `remove` → `users:write`.
- `InvitationViewSet`: list/retrieve → `invitations:read`; create/cancel/resend → `invitations:write`.
- **Seed endpoint:** require platform staff **OR** `roles:write` in the current tenant; once any
  `TenantUser` exists, require `roles:write` (drop the bare `is_staff` bypass).

### `apps/insurance/views.py`
Add `get_permissions()`:
- read actions → `insurance:read`; write actions (create/update/approve/reject) → `insurance:write`.

### Audit the rest
Quick pass over `apps/notifications/views.py`, `apps/audit/views.py`, `apps/ai_integration/views.py`,
`apps/referrals/views.py`:
- notifications: a user manages **their own** notifications — keep `IsActiveTenantUser` but ensure
  the queryset is filtered to `recipient_id == request.user.id` (don't leak others' notifications).
- audit: list/retrieve → `audit:read`.
- ai: read → `ai:read`, create → `ai:write`.

---

## Step 4 — Frontend: only show/allow permitted features (#18)

### 4a. Route-level guard
**New file:** `src/components/auth/RequirePermission.tsx`
```tsx
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

export function RequirePermission({ permission, children }: { permission?: string; children: JSX.Element }) {
  const hasPermission = useAuthStore(s => s.hasPermission)
  if (permission && !hasPermission(permission)) {
    return <Navigate to="/dashboard" replace />   // or a dedicated <NoAccess/> page
  }
  return children
}
```

**File:** `src/App.tsx` — wrap each protected route element with the matching permission (same
mapping the Sidebar already uses). Example:
```tsx
<Route path="/billing" element={<RequirePermission permission="billing:read"><BillingPage/></RequirePermission>} />
<Route path="/billing/:id" element={<RequirePermission permission="billing:read"><InvoiceDetailPage/></RequirePermission>} />
<Route path="/pharmacy" element={<RequirePermission permission="pharmacy:read"><PharmacyPage/></RequirePermission>} />
<Route path="/settings/roles" element={<RequirePermission permission="roles:read"><RolesPage/></RequirePermission>} />
```
Apply to: patients, appointments, visits, prescriptions, lab-orders, billing, pharmacy, insurance,
notifications, audit-log, settings/*, and the new radiology/pharmacy-orders routes from later files.
Leave `/dashboard` and `/profile` open to all authenticated users. Gate `/ai` behind `ai:read`
(the Sidebar currently leaves AI ungated — fix that too: add `permission: 'ai:read'` to the AI nav item).

### 4b. Action-level gating
Within pages, wrap mutating controls so a read-only user can view but not act:
- Pattern: `{hasPermission('patients:write') && <button>Add Patient</button>}`.
- Apply to the primary create/edit/delete/finalize/pay/dispense buttons on every page:
  - Patients: Add/Edit/Delete → `patients:write` / `patients:delete`.
  - Appointments: Book/Reschedule/Cancel → `appointments:write` (Cancel/delete → `appointments:delete`).
  - Visits: Create/Edit/Sign/Add diagnosis → `medical_records:write`; Record vitals →
    `medical_records:write_vitals`.
  - Prescriptions: Create/Edit → `prescriptions:write`.
  - Lab orders: Create → `lab_results:write`; Record result/verify → `lab_results:result`.
  - Billing: Create/Finalize/Pay/Cancel → `billing:write`; Export → `billing:export`.
  - Pharmacy: inventory CRUD → `pharmacy:write`; orders → `pharmacy_orders:write`.
  - Settings (users/roles/invitations): mutations → `users:write`/`roles:write`/`invitations:write`.

### 4c. Optional helper
Add a tiny `<Can permission="x:y">…</Can>` wrapper component (renders children only if permitted) to
reduce repetition; use it for buttons.

---

## Step 5 — Verification

Backend:
```bash
DJANGO_SETTINGS_MODULE=config.settings.development venv_new/bin/python manage.py reseed_permissions   # if added
# Log in as admin (admin@clinic.com / SecurePass123!) → GET /api/v1/rbac/me/ shows the full permission set.
```
- Create a test Nurse and a test Receptionist (via invitations) and confirm:
  - Nurse CAN `POST /visits/{id}/vitals/` but CANNOT `POST /visits/` (create visit) — 403.
  - Receptionist CANNOT `GET /rbac/roles/` mutations — 403; CAN book appointments.
  - A non-billing user gets 403 on `POST /invoices/` and is redirected away from `/billing` in the UI.
- Insurance endpoints now 403 for users without `insurance:*`.

### Acceptance
- Every list/detail/mutation endpoint enforces a specific `resource:action`.
- Vitals recordable by Doctor **and** Nurse only.
- A user logging in sees only permitted sidebar items, cannot deep-link to forbidden pages, and
  cannot see action buttons they can't use.
