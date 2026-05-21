import api from '@/lib/api'
import type {
  PaginatedResponse,
  Patient,
  PatientCreateRequest,
  Appointment,
  BookAppointmentRequest,
  AvailableSlot,
  DoctorProfile,
  Visit,
  VisitCreateRequest,
  VitalsCreateRequest,
  DiagnosisCreateRequest,
  Vitals,
  Diagnosis,
  Prescription,
  PrescriptionCreateRequest,
  Medication,
  LabOrder,
  LabOrderCreateRequest,
  TestResultInput,
  Invoice,
  InvoiceCreateRequest,
  PaymentInput,
  BillingSummary,
  Notification,
  NotificationPreferences,
  AIRequest,
  AIRequestCreate,
  AuditLog,
  Role,
  TenantUser,
  Invitation,
  Permission,
  MeResponse,
  User,
  LoginRequest,
  LoginResponse,
  InvitationInfo,
  PharmacyItem,
  InsuranceProvider,
  InsurancePolicy,
  InsuranceClaim,
} from '@/types'

// ============================================
// AUTH SERVICE
// ============================================
export const authService = {
  login: (data: LoginRequest) =>
    api.post<LoginResponse>('/auth/login/', data).then(r => r.data),

  register: (data: { email: string; password: string; first_name: string; last_name: string }) =>
    api.post('/auth/register/', data).then(r => r.data),

  refreshToken: (refresh: string) =>
    api.post<{ access: string }>('/auth/token/refresh/', { refresh }).then(r => r.data),

  getMe: () =>
    api.get<User>('/auth/me/').then(r => r.data),

  updateProfile: (data: Partial<User>) =>
    api.patch<User>('/auth/me/', data).then(r => r.data),

  verifyPin: (pin: string) =>
    api.post('/auth/verify-pin/', { pin }).then(r => r.data),

  getInvitationInfo: (token: string) =>
    api.get<InvitationInfo>(`/auth/invitation/${token}/`).then(r => r.data),

  acceptInvitation: (token: string, data: { password: string; first_name: string; last_name: string }) =>
    api.post(`/auth/invitation/${token}/accept/`, data).then(r => r.data),
}

// ============================================
// RBAC SERVICE
// ============================================
export const rbacService = {
  getMe: () =>
    api.get<MeResponse>('/rbac/me/').then(r => r.data),

  // Roles
  getRoles: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<Role>>('/rbac/roles/', { params }).then(r => r.data),

  getRole: (id: string) =>
    api.get<Role>(`/rbac/roles/${id}/`).then(r => r.data),

  createRole: (data: { name: string; description?: string; permissions?: string[] }) =>
    api.post<Role>('/rbac/roles/', data).then(r => r.data),

  updateRole: (id: string, data: Partial<{ name: string; description: string; permissions: string[] }>) =>
    api.patch<Role>(`/rbac/roles/${id}/`, data).then(r => r.data),

  deleteRole: (id: string) =>
    api.delete(`/rbac/roles/${id}/`).then(r => r.data),

  // Permissions
  getPermissions: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<Permission>>('/rbac/permissions/', { params }).then(r => r.data),

  // Users
  getUsers: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<TenantUser>>('/rbac/users/', { params }).then(r => r.data),

  getUser: (id: string) =>
    api.get<TenantUser>(`/rbac/users/${id}/`).then(r => r.data),

  updateUser: (id: string, data: Partial<TenantUser>) =>
    api.patch<TenantUser>(`/rbac/users/${id}/`, data).then(r => r.data),

  deleteUser: (id: string) =>
    api.delete(`/rbac/users/${id}/`).then(r => r.data),

  // Invitations
  getInvitations: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<Invitation>>('/rbac/invitations/', { params }).then(r => r.data),

  createInvitation: (data: { email: string; role_id: string; metadata?: Record<string, unknown> }) =>
    api.post<Invitation>('/rbac/invitations/', data).then(r => r.data),

  cancelInvitation: (id: string) =>
    api.post(`/rbac/invitations/${id}/cancel/`).then(r => r.data),

  resendInvitation: (id: string) =>
    api.post(`/rbac/invitations/${id}/resend/`).then(r => r.data),

  seedRoles: () =>
    api.post('/rbac/seed/').then(r => r.data),
}

// ============================================
// PATIENTS SERVICE
// ============================================
export const patientsService = {
  getAll: (params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<Patient>>('/patients/', { params }).then(r => r.data),

  getById: (id: string) =>
    api.get<Patient>(`/patients/${id}/`).then(r => r.data),

  create: (data: PatientCreateRequest) =>
    api.post<Patient>('/patients/', data).then(r => r.data),

  update: (id: string, data: Partial<PatientCreateRequest>) =>
    api.patch<Patient>(`/patients/${id}/`, data).then(r => r.data),

  delete: (id: string) =>
    api.delete(`/patients/${id}/`).then(r => r.data),

  getVisits: (id: string, params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<Visit>>(`/patients/${id}/visits/`, { params }).then(r => r.data),

  getPrescriptions: (id: string, params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<Prescription>>(`/patients/${id}/prescriptions/`, { params }).then(r => r.data),

  getLabResults: (id: string, params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<LabOrder>>(`/patients/${id}/lab-results/`, { params }).then(r => r.data),

  getInvoices: (id: string, params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<Invoice>>(`/patients/${id}/invoices/`, { params }).then(r => r.data),
}

// ============================================
// APPOINTMENTS SERVICE
// ============================================
export const appointmentsService = {
  getAll: (params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<Appointment>>('/appointments/', { params }).then(r => r.data),

  getById: (id: string) =>
    api.get<Appointment>(`/appointments/${id}/`).then(r => r.data),

  book: (data: BookAppointmentRequest) =>
    api.post<Appointment>('/appointments/', data).then(r => r.data),

  reschedule: (id: string, data: { scheduled_at: string; duration_minutes?: number }) =>
    api.patch<Appointment>(`/appointments/${id}/`, data).then(r => r.data),

  confirm: (id: string) =>
    api.post<Appointment>(`/appointments/${id}/confirm/`).then(r => r.data),

  start: (id: string) =>
    api.post<Appointment>(`/appointments/${id}/start/`).then(r => r.data),

  complete: (id: string) =>
    api.post<Appointment>(`/appointments/${id}/complete/`).then(r => r.data),

  cancel: (id: string, reason?: string) =>
    api.post<Appointment>(`/appointments/${id}/cancel/`, { reason }).then(r => r.data),

  noShow: (id: string) =>
    api.post<Appointment>(`/appointments/${id}/no-show/`).then(r => r.data),

  getAvailableSlots: (params: { doctor_id: string; date: string; duration_minutes?: number }) =>
    api.get<AvailableSlot[]>('/appointments/available-slots/', { params }).then(r => r.data),

  // Doctor profiles
  getDoctors: (params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<DoctorProfile>>('/appointments/doctors/', { params }).then(r => r.data),

  getDoctor: (id: string) =>
    api.get<DoctorProfile>(`/appointments/doctors/${id}/`).then(r => r.data),

  createDoctor: (data: Partial<DoctorProfile>) =>
    api.post<DoctorProfile>('/appointments/doctors/', data).then(r => r.data),

  updateDoctor: (id: string, data: Partial<DoctorProfile>) =>
    api.patch<DoctorProfile>(`/appointments/doctors/${id}/`, data).then(r => r.data),
}

// ============================================
// VISITS (MEDICAL RECORDS) SERVICE
// ============================================
export const visitsService = {
  getAll: (params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<Visit>>('/visits/', { params }).then(r => r.data),

  getById: (id: string) =>
    api.get<Visit>(`/visits/${id}/`).then(r => r.data),

  create: (data: VisitCreateRequest) =>
    api.post<Visit>('/visits/', data).then(r => r.data),

  update: (id: string, data: Partial<VisitCreateRequest>) =>
    api.patch<Visit>(`/visits/${id}/`, data).then(r => r.data),

  delete: (id: string) =>
    api.delete(`/visits/${id}/`).then(r => r.data),

  sign: (id: string) =>
    api.post<Visit>(`/visits/${id}/sign/`).then(r => r.data),

  // Vitals
  getVitals: (visitId: string) =>
    api.get<Vitals[]>(`/visits/${visitId}/vitals/`).then(r => r.data),

  addVitals: (visitId: string, data: VitalsCreateRequest) =>
    api.post<Vitals>(`/visits/${visitId}/vitals/`, data).then(r => r.data),

  // Diagnoses
  getDiagnoses: (visitId: string) =>
    api.get<Diagnosis[]>(`/visits/${visitId}/diagnoses/`).then(r => r.data),

  addDiagnosis: (visitId: string, data: DiagnosisCreateRequest) =>
    api.post<Diagnosis>(`/visits/${visitId}/diagnoses/`, data).then(r => r.data),
}

// ============================================
// PRESCRIPTIONS SERVICE
// ============================================
export const prescriptionsService = {
  getAll: (params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<Prescription>>('/prescriptions/', { params }).then(r => r.data),

  getById: (id: string) =>
    api.get<Prescription>(`/prescriptions/${id}/`).then(r => r.data),

  create: (data: PrescriptionCreateRequest) =>
    api.post<Prescription>('/prescriptions/', data).then(r => r.data),

  update: (id: string, data: Partial<PrescriptionCreateRequest>) =>
    api.patch<Prescription>(`/prescriptions/${id}/`, data).then(r => r.data),

  delete: (id: string) =>
    api.delete(`/prescriptions/${id}/`).then(r => r.data),

  // Medications
  getMedications: (params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<Medication>>('/prescriptions/medications/', { params }).then(r => r.data),

  createMedication: (data: Partial<Medication>) =>
    api.post<Medication>('/prescriptions/medications/', data).then(r => r.data),

  updateMedication: (id: string, data: Partial<Medication>) =>
    api.patch<Medication>(`/prescriptions/medications/${id}/`, data).then(r => r.data),
}

// ============================================
// LAB ORDERS SERVICE
// ============================================
export const labOrdersService = {
  getAll: (params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<LabOrder>>('/lab-orders/', { params }).then(r => r.data),

  getById: (id: string) =>
    api.get<LabOrder>(`/lab-orders/${id}/`).then(r => r.data),

  create: (data: LabOrderCreateRequest) =>
    api.post<LabOrder>('/lab-orders/', data).then(r => r.data),

  collect: (id: string) =>
    api.post<LabOrder>(`/lab-orders/${id}/collect/`).then(r => r.data),

  inProgress: (id: string) =>
    api.post<LabOrder>(`/lab-orders/${id}/in_progress/`).then(r => r.data),

  complete: (id: string) =>
    api.post<LabOrder>(`/lab-orders/${id}/complete/`).then(r => r.data),

  cancel: (id: string) =>
    api.post<LabOrder>(`/lab-orders/${id}/cancel/`).then(r => r.data),

  recordResult: (orderId: string, testId: string, data: TestResultInput) =>
    api.post(`/lab-orders/${orderId}/tests/${testId}/result/`, data).then(r => r.data),

  verifyResult: (orderId: string, testId: string) =>
    api.post(`/lab-orders/${orderId}/tests/${testId}/result/verify/`).then(r => r.data),
}

// ============================================
// BILLING SERVICE
// ============================================
export const billingService = {
  getAll: (params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<Invoice>>('/invoices/', { params }).then(r => r.data),

  getById: (id: string) =>
    api.get<Invoice>(`/invoices/${id}/`).then(r => r.data),

  create: (data: InvoiceCreateRequest) =>
    api.post<Invoice>('/invoices/', data).then(r => r.data),

  update: (id: string, data: Partial<InvoiceCreateRequest>) =>
    api.patch<Invoice>(`/invoices/${id}/`, data).then(r => r.data),

  finalize: (id: string) =>
    api.post<Invoice>(`/invoices/${id}/finalize/`).then(r => r.data),

  pay: (id: string, data: PaymentInput) =>
    api.post(`/invoices/${id}/pay/`, data).then(r => r.data),

  cancel: (id: string) =>
    api.post<Invoice>(`/invoices/${id}/cancel/`).then(r => r.data),

  void: (id: string) =>
    api.post<Invoice>(`/invoices/${id}/void/`).then(r => r.data),

  getPayments: (id: string) =>
    api.get(`/invoices/${id}/payments/`).then(r => r.data),

  getSummary: () =>
    api.get<BillingSummary>('/invoices/summary/').then(r => r.data),
}

// ============================================
// NOTIFICATIONS SERVICE
// ============================================
export const notificationsService = {
  getAll: (params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<Notification>>('/notifications/', { params }).then(r => r.data),

  markAsRead: (id: string) =>
    api.patch<Notification>(`/notifications/${id}/`, { is_read: true }).then(r => r.data),

  markAllAsRead: () =>
    api.post('/notifications/mark-all-read/').then(r => r.data),

  getPreferences: () =>
    api.get<NotificationPreferences>('/notifications/preferences/').then(r => r.data),

  updatePreferences: (data: Partial<NotificationPreferences>) =>
    api.patch<NotificationPreferences>('/notifications/preferences/', data).then(r => r.data),
}

// ============================================
// AI SERVICE
// ============================================
export const aiService = {
  getAll: (params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<AIRequest>>('/ai/', { params }).then(r => r.data),

  getById: (id: string) =>
    api.get<AIRequest>(`/ai/${id}/`).then(r => r.data),

  create: (data: AIRequestCreate) =>
    api.post<AIRequest>('/ai/', data).then(r => r.data),
}

// ============================================
// PHARMACY SERVICE
// ============================================
export const pharmacyService = {
  getInventory: (params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<PharmacyItem>>('/pharmacy/inventory/', { params }).then(r => r.data),

  getLowStock: () =>
    api.get<PharmacyItem[]>('/pharmacy/low-stock/').then(r => r.data),

  getDispenseQueue: () =>
    api.get('/pharmacy/dispense-queue/').then(r => r.data),

  dispense: (data: { prescription_item_id: string; quantity: number; notes?: string }) =>
    api.post('/pharmacy/dispense/', data).then(r => r.data),

  updateInventory: (id: string, data: Partial<PharmacyItem>) =>
    api.patch(`/pharmacy/inventory/${id}/`, data).then(r => r.data),

  createInventory: (data: { medication_id: string; quantity_in_stock: number; reorder_level: number; unit_cost: string; selling_price: string; batch_number?: string; expiry_date?: string }) =>
    api.post('/pharmacy/inventory/', data).then(r => r.data),
}

// ============================================
// INSURANCE SERVICE
// ============================================
export const insuranceService = {
  // Providers
  getProviders: (params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<InsuranceProvider>>('/insurance/providers/', { params }).then(r => r.data),

  createProvider: (data: Partial<InsuranceProvider>) =>
    api.post<InsuranceProvider>('/insurance/providers/', data).then(r => r.data),

  updateProvider: (id: string, data: Partial<InsuranceProvider>) =>
    api.patch<InsuranceProvider>(`/insurance/providers/${id}/`, data).then(r => r.data),

  // Policies
  getPolicies: (params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<InsurancePolicy>>('/insurance/policies/', { params }).then(r => r.data),

  createPolicy: (data: Partial<InsurancePolicy>) =>
    api.post<InsurancePolicy>('/insurance/policies/', data).then(r => r.data),

  updatePolicy: (id: string, data: Partial<InsurancePolicy>) =>
    api.patch<InsurancePolicy>(`/insurance/policies/${id}/`, data).then(r => r.data),

  // Claims
  getClaims: (params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<InsuranceClaim>>('/insurance/claims/', { params }).then(r => r.data),

  createClaim: (data: Partial<InsuranceClaim>) =>
    api.post<InsuranceClaim>('/insurance/claims/', data).then(r => r.data),

  updateClaim: (id: string, data: Partial<InsuranceClaim>) =>
    api.patch<InsuranceClaim>(`/insurance/claims/${id}/`, data).then(r => r.data),

  approveClaim: (id: string) =>
    api.post<InsuranceClaim>(`/insurance/claims/${id}/approve/`).then(r => r.data),

  rejectClaim: (id: string) =>
    api.post<InsuranceClaim>(`/insurance/claims/${id}/reject/`).then(r => r.data),
}

// ============================================
// AUDIT SERVICE
// ============================================
export const auditService = {
  getAll: (params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<AuditLog>>('/audit-logs/', { params }).then(r => r.data),

  getById: (id: string) =>
    api.get<AuditLog>(`/audit-logs/${id}/`).then(r => r.data),
}
