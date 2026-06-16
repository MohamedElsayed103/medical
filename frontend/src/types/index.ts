// ============================================
// Auth & User Types
// ============================================
export interface User {
  id: string
  email: string
  username: string | null
  first_name: string
  last_name: string
  full_name: string
  display_name: string
  phone: string | null
  is_active: boolean
  last_login: string | null
  created_at: string
  tenant_mappings: TenantMapping[]
  tenants?: TenantMapping[]
  tenant_context?: {
    tenant_id: string
    tenant_name: string
    tenant_slug: string
    role_name: string
    permissions: string[]
  }
}

export interface TenantMapping {
  id: string
  tenant_id: string
  tenant_name: string
  tenant_slug: string
  role_name: string
  status: string
}

export interface AuthTokens {
  access: string
  refresh: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  user: User
  tokens: AuthTokens
}

export interface RegisterRequest {
  email: string
  password: string
  first_name: string
  last_name: string
  username?: string
}

// ============================================
// RBAC Types
// ============================================
export interface Permission {
  id: string
  codename: string
  name: string
  description: string
  category: string
}

export interface Role {
  id: string
  name: string
  description: string
  is_system_role?: boolean
  is_system?: boolean
  permissions: Permission[]
  user_count?: number
  created_at: string
  updated_at?: string
}

export interface TenantUser {
  id: string
  user_id: string
  user_email: string
  user_name: string
  role: Role | string
  role_id: string
  role_name: string
  status: string
  specialty: string | null
  license_number: string | null
  qualification: string | null
  joined_at: string
  created_at: string
}

export interface Invitation {
  id: string
  email: string
  role: string
  role_id: string
  role_name: string
  invited_by: string
  invited_by_name: string
  token: string
  expires_at: string
  status: string
  accepted_at: string | null
  cancelled_at: string | null
  metadata: Record<string, unknown> | null
  created_at: string
}

export interface InvitationInfo {
  email: string
  role_name: string
  tenant_name: string
  expires_at: string
}

export interface MeResponse {
  user: TenantUser
  role: Role
  permissions: string[]
}

// ============================================
// Tenant Types
// ============================================
export interface Tenant {
  id: string
  name: string
  slug: string
  domain: string | null
  is_active: boolean
  settings: Record<string, unknown>
  created_at: string
  updated_at: string
}

// ============================================
// Patient Types
// ============================================
export interface Patient {
  id: string
  medical_record_number: string
  first_name: string
  last_name: string
  full_name: string
  date_of_birth: string
  gender: string
  email: string | null
  phone: string
  national_id: string | null
  blood_type: string | null
  address: string | null
  emergency_contact_name: string | null
  emergency_contact_phone: string | null
  allergies: string[]
  chronic_conditions: string[]
  insurance_provider: string | null
  insurance_number: string | null
  notes: string | null
  is_active: boolean
  registered_at: string
  created_at: string
  updated_at: string
}

export interface PatientCreateRequest {
  first_name: string
  last_name: string
  date_of_birth: string
  gender: string
  phone: string
  national_id?: string
  blood_type?: string
  email?: string
  address?: string
  emergency_contact_name?: string
  emergency_contact_phone?: string
  allergies?: string[]
  chronic_conditions?: string[]
  insurance_provider?: string
  insurance_number?: string
  notes?: string
}

// ============================================
// Appointment Types
// ============================================
export interface DoctorProfile {
  id: string
  user_id: string
  user_name: string
  user_email: string
  specialization: string
  license_number: string
  qualification: string
  years_of_experience: number
  consultation_fee: string
  bio: string | null
  is_available: boolean
  created_at: string
  updated_at: string
}

export interface Appointment {
  id: string
  patient: Patient | string
  patient_id: string
  patient_name: string
  doctor: DoctorProfile | string
  doctor_id: string
  doctor_name: string
  scheduled_at: string
  duration_minutes: number
  end_time?: string
  status: string
  type: string
  reason: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface BookAppointmentRequest {
  patient_id: string
  doctor_id: string
  scheduled_at: string
  duration_minutes?: number
  type?: string
  reason?: string
}

export interface AvailableSlot {
  start: string
  end: string
}

// ============================================
// Medical Records (Visits) Types
// ============================================
export interface Vitals {
  id: string
  blood_pressure_systolic: number
  blood_pressure_diastolic: number
  heart_rate: number
  temperature: number
  respiratory_rate: number
  oxygen_saturation: number
  weight_kg: string
  height_cm: string
  recorded_at: string
  recorded_by_id: string | null
}

export interface Diagnosis {
  id: string
  icd_code: string
  description: string
  type: string
  notes: string | null
  created_at: string
}

export interface Visit {
  id: string
  patient: Patient | string
  patient_id: string
  patient_name: string
  doctor: DoctorProfile | string
  doctor_id: string
  doctor_name: string
  appointment_id: string | null
  visit_date: string
  chief_complaint: string
  history_of_present_illness: string | null
  examination_notes: string | null
  assessment: string | null
  plan: string | null
  follow_up_date: string | null
  is_signed: boolean
  signed_at: string | null
  vitals: Vitals[]
  diagnoses: Diagnosis[]
  created_at: string
  updated_at: string
}

export interface VisitCreateRequest {
  patient_id: string
  doctor_id: string
  visit_date: string
  chief_complaint: string
  appointment_id?: string
  history_of_present_illness?: string
  examination_notes?: string
  assessment?: string
  plan?: string
  follow_up_date?: string
}

export interface VitalsCreateRequest {
  blood_pressure_systolic: number
  blood_pressure_diastolic: number
  heart_rate: number
  temperature: number
  respiratory_rate: number
  oxygen_saturation: number
  weight_kg: string
  height_cm: string
}

export interface DiagnosisCreateRequest {
  icd_code: string
  description: string
  type: string
  notes?: string
}

// ============================================
// Prescription Types
// ============================================
export interface Medication {
  id: string
  name: string
  generic_name: string
  form: string
  strength: string
  manufacturer: string | null
  is_active: boolean
  image?: string | null
  image_url?: string | null
  description?: string | null
  side_effects?: string | null
  contraindications?: string | null
  storage_instructions?: string | null
}

export interface PrescriptionItem {
  id: string
  medication: Medication
  medication_id: string
  dosage: string
  frequency: string
  duration: string
  quantity: number
  route: string
  instructions: string | null
  is_prn: boolean
}

export interface Prescription {
  id: string
  patient: Patient | string
  patient_id: string
  patient_name: string
  doctor: DoctorProfile | string
  doctor_id: string
  doctor_name: string
  visit_id: string | null
  status: string
  notes: string | null
  items: PrescriptionItem[]
  prescribed_at: string
  created_at: string
  updated_at: string
}

export interface PrescriptionItemInput {
  medication_id: string
  dosage: string
  frequency: string
  duration: string
  quantity: number
  route?: string
  instructions?: string
  is_prn?: boolean
}

export interface PrescriptionCreateRequest {
  patient_id: string
  doctor_id: string
  visit_id?: string
  notes?: string
  items: PrescriptionItemInput[]
}

// ============================================
// Lab Results Types
// ============================================
export interface TestResult {
  id: string
  value: string
  unit: string | null
  reference_range_low: string | null
  reference_range_high: string | null
  interpretation: string | null
  flag?: string | null
  recorded_at: string
  resulted_at?: string | null
  verified_at: string | null
  verified_by: string | null
}

export interface LabTest {
  id: string
  test_name: string
  test_code: string | null
  specimen_type: string | null
  notes: string | null
  result: TestResult | null
}

export interface LabOrder {
  id: string
  order_number: string
  patient: Patient | string
  patient_id: string
  patient_name: string
  doctor: DoctorProfile | string
  doctor_id: string
  doctor_name: string
  visit_id: string | null
  visit?: string | null
  invoice?: string | null
  status: string
  priority: string
  clinical_notes: string | null
  tests: LabTest[]
  test_count?: number
  ordered_at: string
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface LabOrderCreateRequest {
  patient_id: string
  doctor_id: string
  visit_id?: string
  priority?: string
  clinical_notes?: string
  tests: LabTestInput[]
}

export interface LabTestInput {
  test_name: string
  test_code?: string
  specimen_type?: string
  notes?: string
}

export interface TestResultInput {
  value: string
  unit?: string
  reference_range_low?: string
  reference_range_high?: string
  interpretation?: string
}

// ============================================
// Billing Types
// ============================================
export interface InvoiceItem {
  id: string
  item_type: string
  description: string
  quantity: number
  unit_price: string
  total: string
}

export interface Payment {
  id: string
  amount: string
  method: string
  reference_number: string | null
  notes: string | null
  paid_at: string
  created_at: string
}

export interface Invoice {
  id: string
  invoice_number: string
  patient: Patient | string
  patient_id: string
  patient_name: string
  status: string
  due_date: string | null
  issued_at: string
  tax_rate: string
  discount_amount: string
  subtotal: string
  tax_amount: string
  total: string
  amount_paid: string
  balance_due: string
  notes: string | null
  items: InvoiceItem[]
  payments: Payment[]
  created_at: string
  updated_at: string
}

export interface InvoiceCreateRequest {
  patient_id: string
  due_date?: string
  tax_rate?: string
  discount_amount?: string
  notes?: string
  items: InvoiceItemInput[]
}

export interface InvoiceItemInput {
  item_type: string
  description: string
  quantity?: number
  unit_price: string
}

export interface PaymentInput {
  amount: string
  method: string
  reference_number?: string
  notes?: string
}

export interface BillingSummary {
  total_invoiced: number
  total_paid: number
  total_outstanding: number
  total_revenue?: number
  invoice_count: number
  paid_count: number
  overdue_count: number
  draft_count: number
  by_payment_method: Array<{ method: string; total: number }>
}

// ============================================
// Notification Types
// ============================================
export interface Notification {
  id: string
  notification_type: string
  channel: string
  title: string
  body: string
  data: Record<string, unknown> | null
  is_read: boolean
  is_sent: boolean
  sent_at: string | null
  created_at: string
}

export interface NotificationPreferences {
  id: string
  email_enabled: boolean
  sms_enabled: boolean
  push_enabled: boolean
  in_app_enabled: boolean
  quiet_hours_start: string | null
  quiet_hours_end: string | null
}

// ============================================
// AI Integration Types
// ============================================
export interface AIRequest {
  id: string
  request_type: string
  status: string
  input_data: Record<string, unknown>
  output_data: Record<string, unknown> | null
  patient_id: string | null
  model_name: string | null
  prompt_tokens: number | null
  completion_tokens: number | null
  total_tokens: number | null
  latency_ms: number | null
  error_message: string | null
  requested_at: string
  completed_at: string | null
  created_at: string
}

export interface AIRequestCreate {
  request_type: string
  input_data: Record<string, unknown>
  patient_id?: string
}

// ============================================
// Pharmacy Types
// ============================================
export interface PharmacyItem {
  id: string
  medication: Medication
  medication_id: string
  quantity_in_stock: number
  reorder_level: number
  unit_cost: string
  selling_price: string
  batch_number: string | null
  expiry_date: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface DispenseRecord {
  id: string
  prescription_item: PrescriptionItem
  quantity_dispensed: number
  dispensed_by: string
  dispensed_at: string
  notes: string | null
}

// ============================================
// Insurance Types
// ============================================
export interface InsuranceProvider {
  id: string
  name: string
  contact_email: string | null
  contact_phone: string | null
  address: string | null
  is_active: boolean
  created_at: string
}

export interface InsurancePolicy {
  id: string
  patient_id: string
  patient_name: string
  provider: InsuranceProvider
  provider_id: string
  policy_number: string
  group_number: string | null
  coverage_start: string
  coverage_end: string | null
  copay_amount: string | null
  deductible: string | null
  is_active: boolean
  created_at: string
}

export interface InsuranceClaim {
  id: string
  invoice_id: string
  invoice_number: string
  policy_id: string
  policy_number: string
  claim_number: string | null
  amount_claimed: string
  amount_approved: string | null
  status: string
  submitted_at: string | null
  processed_at: string | null
  notes: string | null
  created_at: string
}

// ============================================
// Audit Types
// ============================================
export interface AuditLog {
  id: string
  user: string | null
  user_email: string | null
  action: string
  resource_type: string
  resource_id: string | null
  changes: Record<string, unknown> | null
  ip_address: string | null
  user_agent: string | null
  timestamp: string
  created_at: string
}

// ============================================
// Common Types
// ============================================
export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface DashboardStats {
  total_patients: number
  total_appointments_today: number
  pending_lab_results: number
  revenue_this_month: number
  patients_trend: number
  appointments_trend: number
  recent_patients: Patient[]
  upcoming_appointments: Appointment[]
}

export interface SelectOption {
  value: string
  label: string
}

// ============================================
// Patient 360 Types
// ============================================
export interface TimelineEvent {
  type: 'visit' | 'prescription' | 'lab_order' | 'radiology_order' | 'invoice'
  id: string
  occurred_at: string
  title: string
  subtitle: string
  status: string
  link: string
}

export interface PatientSummary {
  active_medications: string[]
  open_lab_orders: number
  outstanding_balance: string
  visit_count: number
}

export const DOCUMENT_CATEGORIES: { value: string; label: string }[] = [
  { value: 'lab', label: 'Lab Report' },
  { value: 'imaging', label: 'Imaging' },
  { value: 'id', label: 'ID Document' },
  { value: 'insurance', label: 'Insurance' },
  { value: 'consent', label: 'Consent Form' },
  { value: 'referral', label: 'Referral' },
  { value: 'other', label: 'Other' },
]

export interface PatientDocument {
  id: string
  patient: string
  category: string
  filename: string
  content_type: string
  size: number
  description: string
  file_url: string | null
  uploaded_by_id: string | null
  created_at: string
}

// ============================================
// Radiology Types
// ============================================
export const RADIOLOGY_MODALITIES: { value: string; label: string }[] = [
  { value: 'xray', label: 'X-Ray' },
  { value: 'ct', label: 'CT Scan' },
  { value: 'mri', label: 'MRI' },
  { value: 'ultrasound', label: 'Ultrasound' },
  { value: 'mammography', label: 'Mammography' },
  { value: 'fluoroscopy', label: 'Fluoroscopy' },
  { value: 'pet', label: 'PET Scan' },
]

export interface RadiologyReport {
  id: string
  findings: string
  impression: string
  is_critical: boolean
  reported_by_id: string | null
  reported_at: string
  image_object_key: string | null
}

export interface RadiologyStudy {
  id: string
  modality: string
  body_part: string
  description: string
  performed_by_id: string | null
  performed_at: string | null
  report?: RadiologyReport | null
}

export interface RadiologyOrder {
  id: string
  order_number: string
  status: string
  priority: string
  patient_id: string | null
  customer_id: string | null
  doctor_id: string | null
  visit_id: string | null
  orderer_name: string
  orderer_type: string
  clinical_notes: string
  invoice_id: string | null
  ordered_at: string
  completed_at: string | null
  studies: RadiologyStudy[]
}

export interface RadiologyStudyInput {
  modality: string
  body_part: string
  description?: string
}

export interface RadiologyOrderCreateRequest {
  patient_id?: string | null
  customer_name?: string
  customer_phone?: string
  doctor_id?: string | null
  priority?: string
  clinical_notes?: string
  studies: RadiologyStudyInput[]
}
