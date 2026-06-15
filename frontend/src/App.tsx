import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import AuthLayout from '@/layouts/AuthLayout'
import DashboardLayout from '@/layouts/DashboardLayout'

// Lazy load pages for performance
const LoginPage = lazy(() => import('@/pages/auth/LoginPage'))
const AcceptInvitationPage = lazy(() => import('@/pages/auth/AcceptInvitationPage'))
const DashboardPage = lazy(() => import('@/pages/dashboard/DashboardPage'))
const PatientsPage = lazy(() => import('@/pages/patients/PatientsPage'))
const PatientDetailPage = lazy(() => import('@/pages/patients/PatientDetailPage'))
const AppointmentsPage = lazy(() => import('@/pages/appointments/AppointmentsPage'))
const VisitsPage = lazy(() => import('@/pages/visits/VisitsPage'))
const VisitDetailPage = lazy(() => import('@/pages/visits/VisitDetailPage'))
const PrescriptionsPage = lazy(() => import('@/pages/prescriptions/PrescriptionsPage'))
const LabOrdersPage = lazy(() => import('@/pages/lab-orders/LabOrdersPage'))
const BillingPage = lazy(() => import('@/pages/billing/BillingPage'))
const NotificationsPage = lazy(() => import('@/pages/notifications/NotificationsPage'))
const AIPage = lazy(() => import('@/pages/ai/AIPage'))
const PharmacyPage = lazy(() => import('@/pages/pharmacy/PharmacyPage'))
const RadiologyPage = lazy(() => import('@/pages/radiology/RadiologyPage'))
const PharmacyOrdersPage = lazy(() => import('@/pages/pharmacy/PharmacyOrdersPage'))
const InsurancePage = lazy(() => import('@/pages/insurance/InsurancePage'))
const SettingsPage = lazy(() => import('@/pages/settings/SettingsPage'))
const UsersPage = lazy(() => import('@/pages/settings/UsersPage'))
const RolesPage = lazy(() => import('@/pages/settings/RolesPage'))
const InvitationsPage = lazy(() => import('@/pages/settings/InvitationsPage'))
const ProfilePage = lazy(() => import('@/pages/profile/ProfilePage'))
const AuditLogPage = lazy(() => import('@/pages/audit/AuditLogPage'))
const DoctorAvailabilityPage = lazy(() => import('@/pages/appointments/DoctorAvailabilityPage'))
const LabOrderDetailPage = lazy(() => import('@/pages/lab-orders/LabOrderDetailPage'))
const InvoiceDetailPage = lazy(() => import('@/pages/billing/InvoiceDetailPage'))

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
    </div>
  )
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, tokens } = useAuthStore()
  if (!isAuthenticated || !tokens?.access) return <Navigate to="/login" replace />
  return <>{children}</>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
        <Route element={<AuthLayout />}>
          <Route path="/invitation/:token" element={<AcceptInvitationPage />} />
        </Route>

        {/* Protected Routes */}
        <Route element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/patients" element={<PatientsPage />} />
          <Route path="/patients/:id" element={<PatientDetailPage />} />
          <Route path="/appointments" element={<AppointmentsPage />} />
          <Route path="/visits" element={<VisitsPage />} />
          <Route path="/visits/:id" element={<VisitDetailPage />} />
          <Route path="/prescriptions" element={<PrescriptionsPage />} />
          <Route path="/lab-orders" element={<LabOrdersPage />} />
          <Route path="/lab-orders/:id" element={<LabOrderDetailPage />} />
          <Route path="/billing" element={<BillingPage />} />
          <Route path="/billing/:id" element={<InvoiceDetailPage />} />
          <Route path="/appointments/availability" element={<DoctorAvailabilityPage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/ai" element={<AIPage />} />
          <Route path="/pharmacy" element={<PharmacyPage />} />
          <Route path="/radiology" element={<RadiologyPage />} />
          <Route path="/pharmacy/orders" element={<PharmacyOrdersPage />} />
          <Route path="/insurance" element={<InsurancePage />} />
          <Route path="/audit-log" element={<AuditLogPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/settings/users" element={<UsersPage />} />
          <Route path="/settings/roles" element={<RolesPage />} />
          <Route path="/settings/invitations" element={<InvitationsPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Route>

        {/* Redirects */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Suspense>
  )
}
