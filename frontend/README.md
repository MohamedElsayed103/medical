# MedFlow Pro - Frontend

A premium healthcare management dashboard built with React, TypeScript, and Tailwind CSS.

## Tech Stack

- **React 19** + TypeScript
- **Vite 6** - Lightning-fast build tool
- **TailwindCSS 3** - Utility-first styling
- **Framer Motion** - Smooth animations
- **TanStack Query** - Server state management
- **Zustand** - Client state management
- **React Hook Form + Zod** - Form handling & validation
- **Recharts** - Dashboard charts
- **Lucide React** - Beautiful icons

## Getting Started

```bash
# Due to the path containing spaces, use symlink:
ln -sf "/media/mohamed/New Volume/medical/medical/frontend" /tmp/med-frontend
cd /tmp/med-frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Or use the helper script:
```bash
bash frontend/start-dev.sh
```

## Features

- **Authentication** - Login, invitation acceptance
- **Dashboard** - Stats cards, patient growth charts, revenue overview
- **Patient Management** - CRUD, search, detail views
- **Appointments** - List & calendar views
- **Medical Records** - Clinical documentation
- **Prescriptions** - Medication management
- **Lab Results** - Test results with critical flags
- **Billing** - Invoices & payments
- **RBAC** - Roles, permissions, invitations management
- **Notifications** - Real-time alerts
- **Audit Log** - Action tracking
- **Multi-tenant** - Organization switching
- **Responsive** - Mobile-first design

## Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Primary (Teal) | `#0d9488` | Main actions, navigation |
| Secondary (Indigo) | `#4f46e5` | Accents, charts |
| Emerald | `#059669` | Success, health |
| Amber | `#d97706` | Warnings |
| Rose | `#e11d48` | Errors, critical |
| Slate | `#1e293b` | Text, borders |

## Project Structure

```
src/
├── components/
│   ├── navigation/     # Sidebar, TopBar, TenantSwitcher
│   └── ui/             # Button, Card, Modal, DataTable, etc.
├── layouts/            # AuthLayout, DashboardLayout
├── lib/                # API client, utilities
├── pages/
│   ├── auth/           # Login, AcceptInvitation
│   ├── dashboard/      # Main dashboard
│   ├── patients/       # Patient CRUD
│   ├── appointments/   # Appointment management
│   ├── medical-records/
│   ├── prescriptions/
│   ├── lab-results/
│   ├── billing/
│   ├── notifications/
│   ├── settings/       # Users, Roles, Invitations
│   ├── audit/          # Audit log
│   └── profile/        # User profile
├── stores/             # Zustand state (auth, UI)
└── types/              # TypeScript interfaces
```
