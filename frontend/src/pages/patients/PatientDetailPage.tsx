import { useState, useRef } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { format, parseISO, isValid } from 'date-fns'
import toast from 'react-hot-toast'
import {
  ArrowLeft, Edit2, Phone, Mail, MapPin, Heart, AlertTriangle,
  FileText, Pill, FlaskConical, DollarSign, User, Clock, ScanLine, Receipt, Stethoscope,
  FolderOpen, Upload, Trash2, Download,
} from 'lucide-react'
import { usePatient, usePatientVisits, usePatientPrescriptions, usePatientLabResults, usePatientInvoices, useDeletePatient } from '@/hooks/usePatients'
import { patientsService } from '@/services/api'
import { getApiErrorMessage } from '@/lib/api'
import { DOCUMENT_CATEGORIES } from '@/types'
import StatusChip from '@/components/ui/StatusChip'
import { formatClinicDateTime } from '@/lib/utils'
import PatientFormModal from './PatientFormModal'

const TIMELINE_ICONS: Record<string, any> = {
  visit: Stethoscope, prescription: Pill, lab_order: FlaskConical, radiology_order: ScanLine, invoice: Receipt,
}

function formatBytes(n: number): string {
  if (!n) return '0 B'
  const k = 1024, units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(n) / Math.log(k))
  return `${(n / Math.pow(k, i)).toFixed(i ? 1 : 0)} ${units[i]}`
}

type Tab = 'overview' | 'visits' | 'prescriptions' | 'lab-results' | 'invoices' | 'documents'

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [showEditModal, setShowEditModal] = useState(false)

  const { data: patient, isLoading } = usePatient(id!)
  const { data: visits } = usePatientVisits(id!, {})
  const { data: prescriptions } = usePatientPrescriptions(id!, {})
  const { data: labResults } = usePatientLabResults(id!, {})
  const { data: invoices } = usePatientInvoices(id!, {})
  const { data: timeline } = useQuery({
    queryKey: ['patient-timeline', id],
    queryFn: () => patientsService.getTimeline(id!),
    enabled: !!id,
  })
  const { data: summary } = useQuery({
    queryKey: ['patient-summary', id],
    queryFn: () => patientsService.getSummary(id!),
    enabled: !!id,
  })
  const { data: documents } = useQuery({
    queryKey: ['patient-documents', id],
    queryFn: () => patientsService.getDocuments(id!),
    enabled: !!id,
  })
  const deletePatient = useDeletePatient()
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [docCategory, setDocCategory] = useState('other')

  const uploadDoc = useMutation({
    mutationFn: (file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('category', docCategory)
      return patientsService.uploadDocument(id!, fd)
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['patient-documents', id] }); qc.invalidateQueries({ queryKey: ['patient-timeline', id] }); toast.success('Document uploaded') },
    onError: (e) => toast.error(getApiErrorMessage(e)),
  })
  const deleteDoc = useMutation({
    mutationFn: (docId: string) => patientsService.deleteDocument(docId),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['patient-documents', id] }); toast.success('Document removed') },
    onError: (e) => toast.error(getApiErrorMessage(e)),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-3 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
      </div>
    )
  }

  if (!patient) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-500">Patient not found</p>
        <Link to="/patients" className="text-primary-600 mt-2 inline-block">Back to patients</Link>
      </div>
    )
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this patient?')) return
    await deletePatient.mutateAsync(patient.id)
    navigate('/patients')
  }

  const tabs: { id: string; label: string; icon: any; count?: number }[] = [
    { id: 'overview', label: 'Overview', icon: User },
    { id: 'visits', label: 'Visits', icon: FileText, count: visits?.count },
    { id: 'prescriptions', label: 'Prescriptions', icon: Pill, count: prescriptions?.count },
    { id: 'lab-results', label: 'Lab Results', icon: FlaskConical, count: labResults?.count },
    { id: 'invoices', label: 'Invoices', icon: DollarSign, count: invoices?.count },
    { id: 'documents', label: 'Documents', icon: FolderOpen, count: documents?.count },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/patients" className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft className="w-5 h-5 text-gray-600" />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">
            {patient.first_name} {patient.last_name}
          </h1>
          <p className="text-sm text-gray-500">MRN: {patient.medical_record_number || 'N/A'}</p>
        </div>
        <button onClick={() => setShowEditModal(true)} className="btn-ghost flex items-center gap-2">
          <Edit2 className="w-4 h-4" /> Edit
        </button>
        <button onClick={handleDelete} className="btn-ghost text-red-600 hover:bg-red-50">Delete</button>
      </div>

      {/* Patient Info Card */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl shadow-soft border border-gray-100 p-6"
      >
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-primary-100 flex items-center justify-center text-xl font-bold text-primary-700">
              {patient.first_name[0]}{patient.last_name[0]}
            </div>
            <div>
              <p className="font-semibold text-gray-900">{patient.first_name} {patient.last_name}</p>
              <p className="text-sm text-gray-500 capitalize">{patient.gender} • {patient.date_of_birth && isValid(parseISO(patient.date_of_birth)) ? format(parseISO(patient.date_of_birth), 'MMM d, yyyy') : 'N/A'}</p>
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium mt-1 ${
                patient.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>{patient.is_active ? 'Active' : 'Inactive'}</span>
            </div>
          </div>

          <div className="space-y-2">
            {patient.phone && <div className="flex items-center gap-2 text-sm text-gray-600"><Phone className="w-4 h-4 text-gray-400" />{patient.phone}</div>}
            {patient.email && <div className="flex items-center gap-2 text-sm text-gray-600"><Mail className="w-4 h-4 text-gray-400" />{patient.email}</div>}
            {patient.address && <div className="flex items-center gap-2 text-sm text-gray-600"><MapPin className="w-4 h-4 text-gray-400" />{patient.address}</div>}
          </div>

          <div className="space-y-2">
            {patient.blood_type && <div className="flex items-center gap-2 text-sm"><Heart className="w-4 h-4 text-red-400" /><span className="font-medium">Blood:</span> {patient.blood_type}</div>}
            {patient.allergies?.length > 0 && (
              <div className="flex items-start gap-2 text-sm">
                <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5" />
                <div>
                  <span className="font-medium">Allergies:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {patient.allergies.map((a, i) => (
                      <span key={i} className="px-2 py-0.5 bg-amber-50 text-amber-700 rounded text-xs">{a}</span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="space-y-2">
            {patient.insurance_provider && (
              <div className="text-sm"><span className="font-medium text-gray-700">Insurance:</span> {patient.insurance_provider}</div>
            )}
            {patient.insurance_number && (
              <div className="text-sm text-gray-600">Policy: {patient.insurance_number}</div>
            )}
            {patient.emergency_contact_name && (
              <div className="text-sm"><span className="font-medium text-gray-700">Emergency:</span> {patient.emergency_contact_name} ({patient.emergency_contact_phone})</div>
            )}
          </div>
        </div>
      </motion.div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as Tab)}
              className={`flex items-center gap-2 pb-3 px-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
              {tab.count !== undefined && (
                <span className="ml-1 px-1.5 py-0.5 bg-gray-100 rounded-full text-xs">{tab.count}</span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left column: summary blocks */}
            <div className="space-y-6">
              {/* KPI cards */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white rounded-xl p-4 shadow-soft border border-gray-100">
                  <p className="text-xs text-gray-500">Outstanding</p>
                  <p className={`text-xl font-bold ${Number(summary?.outstanding_balance ?? 0) > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    ${Number(summary?.outstanding_balance ?? 0).toFixed(2)}
                  </p>
                </div>
                <div className="bg-white rounded-xl p-4 shadow-soft border border-gray-100">
                  <p className="text-xs text-gray-500">Open Lab Orders</p>
                  <p className="text-xl font-bold text-gray-900">{summary?.open_lab_orders ?? 0}</p>
                </div>
                <div className="bg-white rounded-xl p-4 shadow-soft border border-gray-100">
                  <p className="text-xs text-gray-500">Total Visits</p>
                  <p className="text-xl font-bold text-gray-900">{summary?.visit_count ?? visits?.count ?? 0}</p>
                </div>
                <div className="bg-white rounded-xl p-4 shadow-soft border border-gray-100">
                  <p className="text-xs text-gray-500">Prescriptions</p>
                  <p className="text-xl font-bold text-gray-900">{prescriptions?.count ?? 0}</p>
                </div>
              </div>

              {/* Active medications */}
              <div className="bg-white rounded-xl p-5 shadow-soft border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2"><Pill className="w-4 h-4 text-purple-500" /> Active Medications</h3>
                {summary?.active_medications?.length ? (
                  <div className="flex flex-wrap gap-1.5">
                    {summary.active_medications.map((m, i) => (
                      <span key={i} className="px-2 py-0.5 bg-purple-50 text-purple-700 rounded text-xs">{m}</span>
                    ))}
                  </div>
                ) : <p className="text-sm text-gray-400">None on record</p>}
              </div>

              {/* Allergies */}
              <div className="bg-white rounded-xl p-5 shadow-soft border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-amber-500" /> Allergies</h3>
                {patient.allergies?.length ? (
                  <div className="flex flex-wrap gap-1.5">
                    {patient.allergies.map((a, i) => <span key={i} className="px-2 py-0.5 bg-amber-50 text-amber-700 rounded text-xs">{a}</span>)}
                  </div>
                ) : <p className="text-sm text-gray-400">No known allergies</p>}
              </div>

              {patient.chronic_conditions?.length > 0 && (
                <div className="bg-white rounded-xl p-5 shadow-soft border border-gray-100">
                  <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2"><Heart className="w-4 h-4 text-red-500" /> Chronic Conditions</h3>
                  <div className="flex flex-wrap gap-1.5">
                    {patient.chronic_conditions.map((c, i) => <span key={i} className="px-2 py-0.5 bg-red-50 text-red-700 rounded text-xs">{c}</span>)}
                  </div>
                </div>
              )}
              {patient.notes && (
                <div className="bg-white rounded-xl p-5 shadow-soft border border-gray-100">
                  <h3 className="font-semibold text-gray-900 mb-3">Notes</h3>
                  <p className="text-sm text-gray-600 whitespace-pre-wrap">{patient.notes}</p>
                </div>
              )}
            </div>

            {/* Right column: timeline */}
            <div className="lg:col-span-2 bg-white rounded-xl p-5 shadow-soft border border-gray-100">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2"><Clock className="w-4 h-4 text-primary-500" /> Patient Timeline</h3>
              {timeline?.length ? (
                <div className="relative pl-6">
                  <div className="absolute left-2 top-1 bottom-1 w-px bg-gray-200" />
                  <div className="space-y-4">
                    {timeline.map(ev => {
                      const Icon = TIMELINE_ICONS[ev.type] || FileText
                      return (
                        <Link key={`${ev.type}-${ev.id}`} to={ev.link} className="relative block group">
                          <span className="absolute -left-[1.35rem] top-1 w-4 h-4 rounded-full bg-white border-2 border-primary-400 group-hover:border-primary-600" />
                          <div className="flex items-start justify-between gap-3 rounded-lg px-3 py-2 -mx-3 group-hover:bg-gray-50">
                            <div className="min-w-0">
                              <div className="flex items-center gap-2">
                                <Icon className="w-4 h-4 text-gray-400 shrink-0" />
                                <p className="font-medium text-gray-900 truncate">{ev.title}</p>
                                <StatusChip status={ev.status} />
                              </div>
                              <p className="text-xs text-gray-500 mt-0.5">{ev.subtitle}</p>
                            </div>
                            <p className="text-xs text-gray-400 whitespace-nowrap shrink-0">{formatClinicDateTime(ev.occurred_at)}</p>
                          </div>
                        </Link>
                      )
                    })}
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-400 text-sm">No activity recorded yet</div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'visits' && (
          <div className="bg-white rounded-xl shadow-soft border border-gray-100 overflow-hidden">
            {visits?.results?.length ? (
              <div className="divide-y divide-gray-50">
                {visits.results.map(visit => (
                  <Link key={visit.id} to={`/visits/${visit.id}`} className="flex items-center gap-4 p-4 hover:bg-gray-50 transition-colors">
                    <div className="w-10 h-10 rounded-lg bg-primary-50 flex items-center justify-center">
                      <FileText className="w-5 h-5 text-primary-600" />
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{visit.chief_complaint}</p>
                      <p className="text-sm text-gray-500">Dr. {visit.doctor_name} • {visit.visit_date && isValid(parseISO(visit.visit_date)) ? format(parseISO(visit.visit_date), 'MMM d, yyyy') : '—'}</p>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${visit.is_signed ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                      {visit.is_signed ? 'Signed' : 'Draft'}
                    </span>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-400">No visits recorded</div>
            )}
          </div>
        )}

        {activeTab === 'prescriptions' && (
          <div className="bg-white rounded-xl shadow-soft border border-gray-100 overflow-hidden">
            {prescriptions?.results?.length ? (
              <div className="divide-y divide-gray-50">
                {prescriptions.results.map(rx => (
                  <Link key={rx.id} to={`/prescriptions/${rx.id}`} className="block p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="min-w-0">
                        <p className="font-medium text-gray-900 truncate">
                          {rx.items?.length
                            ? rx.items.map((it: any) => it.medication_name || it.medication?.name).filter(Boolean).join(', ')
                            : `${rx.items?.length || 0} medication(s)`}
                        </p>
                        <p className="text-sm text-gray-500">Dr. {rx.doctor_name} • {rx.created_at && isValid(parseISO(rx.created_at)) ? format(parseISO(rx.created_at), 'MMM d, yyyy') : '—'}</p>
                      </div>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium shrink-0 ${
                        rx.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                      }`}>{rx.status}</span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-400">No prescriptions</div>
            )}
          </div>
        )}

        {activeTab === 'lab-results' && (
          <div className="bg-white rounded-xl shadow-soft border border-gray-100 overflow-hidden">
            {labResults?.results?.length ? (
              <div className="divide-y divide-gray-50">
                {labResults.results.map(order => (
                  <Link key={order.id} to={`/lab-orders/${order.id}`} className="flex items-center gap-4 p-4 hover:bg-gray-50">
                    <div className="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center">
                      <FlaskConical className="w-5 h-5 text-amber-600" />
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">Order #{order.order_number}</p>
                      <p className="text-sm text-gray-500">{order.tests?.length || 0} test(s) • {order.created_at && isValid(parseISO(order.created_at)) ? format(parseISO(order.created_at), 'MMM d, yyyy') : '—'}</p>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      order.status === 'completed' ? 'bg-green-100 text-green-700' :
                      order.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-blue-100 text-blue-700'
                    }`}>{order.status}</span>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-400">No lab orders</div>
            )}
          </div>
        )}

        {activeTab === 'invoices' && (
          <div className="bg-white rounded-xl shadow-soft border border-gray-100 overflow-hidden">
            {invoices?.results?.length ? (
              <div className="divide-y divide-gray-50">
                {invoices.results.map(inv => (
                  <Link key={inv.id} to={`/billing/${inv.id}`} className="flex items-center gap-4 p-4 hover:bg-gray-50">
                    <div className="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center">
                      <DollarSign className="w-5 h-5 text-emerald-600" />
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">#{inv.invoice_number}</p>
                      <p className="text-sm text-gray-500">${inv.total} • {(inv.issued_at || inv.created_at) && isValid(parseISO(inv.issued_at || inv.created_at || '')) ? format(parseISO(inv.issued_at || inv.created_at || ''), 'MMM d, yyyy') : '—'}</p>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      inv.status === 'paid' ? 'bg-green-100 text-green-700' :
                      inv.status === 'overdue' ? 'bg-red-100 text-red-700' :
                      'bg-yellow-100 text-yellow-700'
                    }`}>{inv.status}</span>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-400">No invoices</div>
            )}
          </div>
        )}

        {activeTab === 'documents' && (
          <div className="bg-white rounded-xl shadow-soft border border-gray-100 overflow-hidden">
            {/* Upload bar */}
            <div className="flex items-center gap-3 p-4 border-b border-gray-100 bg-gray-50/50">
              <select value={docCategory} onChange={e => setDocCategory(e.target.value)} className="input-field w-auto text-sm">
                {DOCUMENT_CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
              <input ref={fileRef} type="file" className="hidden"
                onChange={e => { const f = e.target.files?.[0]; if (f) uploadDoc.mutate(f); if (fileRef.current) fileRef.current.value = '' }} />
              <button onClick={() => fileRef.current?.click()} disabled={uploadDoc.isPending}
                className="btn-primary text-sm flex items-center gap-2">
                <Upload className="w-4 h-4" /> {uploadDoc.isPending ? 'Uploading...' : 'Upload Document'}
              </button>
              <span className="text-xs text-gray-400 ml-auto">PDF, images, or docs up to 10 MB</span>
            </div>

            {documents?.results?.length ? (
              <div className="divide-y divide-gray-50">
                {documents.results.map(doc => (
                  <div key={doc.id} className="flex items-center gap-4 p-4 hover:bg-gray-50/50">
                    <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                      <FileText className="w-5 h-5 text-blue-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">{doc.filename || 'Document'}</p>
                      <p className="text-xs text-gray-500">
                        <span className="capitalize">{doc.category}</span> • {formatBytes(doc.size)} • {formatClinicDateTime(doc.created_at)}
                      </p>
                    </div>
                    {doc.file_url && (
                      <a href={doc.file_url} target="_blank" rel="noopener noreferrer"
                        className="p-2 rounded-lg hover:bg-gray-100 text-gray-500" title="Download / view">
                        <Download className="w-4 h-4" />
                      </a>
                    )}
                    <button onClick={() => { if (confirm('Remove this document?')) deleteDoc.mutate(doc.id) }}
                      className="p-2 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500" title="Delete">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-400">No documents uploaded</div>
            )}
          </div>
        )}
      </div>

      {/* Edit Modal */}
      <PatientFormModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        patient={patient}
      />
    </div>
  )
}
