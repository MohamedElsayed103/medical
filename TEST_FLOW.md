# MedFlow Pro — Frontend Testing Flow

## Prerequisites

```bash
# Terminal 1: Backend
cd "/media/mohamed/New Volume/medical/medical"
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Frontend
cd "/media/mohamed/New Volume/medical/medical/frontend"
npm run dev
```

Open browser at: **http://localhost:5173** (or whatever port Vite shows)

---

## 1. Authentication

### 1.1 Register a New User
1. Go to `/register`
2. Fill in: First Name, Last Name, Email, Password, Confirm Password
3. Click "Create Account"
4. **Expected**: Redirect to `/dashboard` with the new user logged in

### 1.2 Logout
1. Click user avatar/name in the top-right corner
2. Click "Logout"
3. **Expected**: Redirect to `/login`

### 1.3 Login
1. Go to `/login`
2. Enter credentials: `admin@clinic.com` / `SecurePass123!`
3. Click "Sign In"
4. **Expected**: Redirect to `/dashboard`

### 1.4 Token Refresh (automatic)
- The app auto-refreshes tokens. If access token expires, the next API call should still work seamlessly.

---

## 2. Dashboard (`/dashboard`)

1. Verify stats cards load (Patients, Appointments, Revenue, etc.)
2. Verify the revenue/analytics chart renders
3. Verify "Today's Schedule" or recent activity section loads
4. **Expected**: All cards show numbers, chart renders, no errors in console

---

## 3. Patients

### 3.1 Patients List (`/patients`)
1. Navigate to Patients from sidebar
2. Verify patient list loads with names, dates, status
3. Test search/filter bar (type a name)
4. **Expected**: List renders, filtering works

### 3.2 Add New Patient
1. Click "Add Patient" button
2. Fill in patient form (name, DOB, gender, phone, email, address)
3. Submit
4. **Expected**: Patient created, appears in list

### 3.3 Patient Detail (`/patients/:id`)
1. Click on a patient from the list
2. Verify tabs load: Overview, Visits, Prescriptions, Lab Results, Billing
3. Check each tab renders data
4. **Expected**: All sections render without "Invalid time value" errors

---

## 4. Appointments (`/appointments`)

1. Navigate to Appointments
2. Verify appointment list/calendar view loads
3. Click "New Appointment"
4. Select patient, doctor, date/time, type
5. Submit
6. **Expected**: Appointment created, appears in list

---

## 5. Visits (`/visits`)

1. Navigate to Visits
2. Verify visit list loads
3. Click a visit to view detail (`/visits/:id`)
4. **Expected**: Visit detail page shows patient info, notes, vitals

---

## 6. Prescriptions (`/prescriptions`)

1. Navigate to Prescriptions
2. View list of prescriptions
3. Create new prescription (select patient, add medication items)
4. **Expected**: Prescription created with medication details

---

## 7. Lab Orders (`/lab-orders`)

1. Navigate to Lab Orders
2. View existing orders
3. Create new lab order (select patient, tests)
4. **Expected**: Lab order created, status shows correctly

---

## 8. Billing (`/billing`)

1. Navigate to Billing
2. Verify invoices list loads with amounts, dates, status
3. Check date columns render properly (no "Invalid time value")
4. Create new invoice if supported
5. **Expected**: All financial data renders cleanly

---

## 9. Pharmacy (`/pharmacy`)

1. Navigate to Pharmacy
2. View medication inventory
3. Check dispensing functionality
4. **Expected**: Pharmacy data loads

---

## 10. Insurance (`/insurance`)

1. Navigate to Insurance
2. View providers and policies
3. View claims
4. **Expected**: Insurance data renders

---

## 11. AI Integration (`/ai`)

1. Navigate to AI page
2. Test AI assistant / clinical decision support
3. **Expected**: AI interface loads (may show "no API key configured" if not set up)

---

## 12. Notifications (`/notifications`)

1. Navigate to Notifications page
2. Verify notification list loads
3. Click the bell icon in TopBar — verify dropdown shows recent notifications
4. Mark notifications as read
5. **Expected**: Notifications display, mark-as-read works

---

## 13. Audit Log (`/audit-log`)

1. Navigate to Audit Log
2. Verify log entries show user actions with timestamps
3. **Expected**: Audit trail renders chronologically

---

## 14. Settings

### 14.1 General Settings (`/settings`)
1. Navigate to Settings
2. Verify settings page loads

### 14.2 Users Management (`/settings/users`)
1. View list of users with names, emails, roles, status
2. Verify user data displays correctly (no blank names)
3. **Expected**: User list shows display names and roles

### 14.3 Roles & Permissions (`/settings/roles`)
1. View list of roles
2. Click "Create Role"
3. Enter name, description, select permissions (grouped by resource)
4. Save
5. Edit an existing role, toggle permissions
6. **Expected**: Permissions picker shows all available permissions grouped by module

### 14.4 Invitations (`/settings/invitations`)
1. View sent invitations
2. Send new invitation (email, role)
3. Check terminal/console for email output (email content with invitation link)
4. **Expected**: Invitation sent, email printed to terminal

---

## 15. User Profile (`/profile`)

1. Click user menu → Profile
2. Update profile fields (name, phone)
3. Save
4. **Expected**: Profile updated successfully

---

## 16. Navigation & UI

### 16.1 Sidebar
1. Verify all menu items are clickable and route correctly
2. Collapse sidebar (click collapse button)
3. **Expected**: Sidebar collapses to icons, content area expands

### 16.2 TopBar
1. Verify search input works (type patient name → see results dropdown)
2. Verify notification bell shows count badge
3. Verify user menu dropdown (Profile, Settings, Logout)

### 16.3 Responsive
1. Resize browser to mobile width
2. **Expected**: Sidebar becomes overlay/hamburger, layout adjusts

---

## 17. Email Verification

Emails are sent to the console (printed in the backend terminal).

1. Send an invitation from `/settings/invitations`
2. Check the **backend terminal** output — you'll see the email content with the invitation link
3. Copy the invitation link and open it in browser
4. **Expected**: Accept invitation page loads with tenant/role info

---

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| White screen after login | Clear localStorage, reload |
| "Invalid time value" | Already fixed with safeFormat utility |
| Sidebar shifts content | Already fixed with flex layout |
| No emails appearing | Check backend terminal output (console backend) |
| Wrong frontend loaded | Make sure you're in `medical/medical/frontend/`, not `medical/frontend/` |

---

## Test Credentials

| Email | Password | Role |
|-------|----------|------|
| `admin@clinic.com` | `SecurePass123!` | Admin |

You can also register new users via `/register`.
