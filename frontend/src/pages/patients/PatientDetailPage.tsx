import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { format, parseISO, isValid } from 'date-fns'
import {
  ArrowLeft, Edit2, Phone, Mail, MapPin, Heart, AlertTriangle,
  FileText, Pill, FlaskConical, DollarSign, User,
} from 'lucide-react'
import { usePatient, usePatientVisits, usePatientPrescriptions, usePatientLabResults, usePatientInvoices, useDeletePatient } from '@/hooks/usePatients'
import PatientFormModal from './PatientFormModal'

type Tab = 'overview' | 'visits' | 'prescriptions' | 'lab-results' | 'invoices'

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
  const deletePatient = useDeletePatient()

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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {patient.chronic_conditions?.length > 0 && (
              <div className="bg-white rounded-xl p-5 shadow-soft border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-3">Chronic Conditions</h3>
                <div className="flex flex-wrap gap-2">
                  {patient.chronic_conditions.map((c, i) => (
                    <span key={i} className="px-3 py-1 bg-red-50 text-red-700 rounded-lg text-sm">{c}</span>
                  ))}
                </div>
              </div>
            )}
            {patient.notes && (
              <div className="bg-white rounded-xl p-5 shadow-soft border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-3">Notes</h3>
                <p className="text-sm text-gray-600 whitespace-pre-wrap">{patient.notes}</p>
              </div>
            )}
            <div className="bg-white rounded-xl p-5 shadow-soft border border-gray-100">
              <h3 className="font-semibold text-gray-900 mb-3">Summary</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><span className="text-gray-500">Total Visits:</span> <span className="font-medium">{visits?.count ?? 0}</span></div>
                <div><span className="text-gray-500">Prescriptions:</span> <span className="font-medium">{prescriptions?.count ?? 0}</span></div>
                <div><span className="text-gray-500">Lab Orders:</span> <span className="font-medium">{labResults?.count ?? 0}</span></div>
                <div><span className="text-gray-500">Invoices:</span> <span className="font-medium">{invoices?.count ?? 0}</span></div>
              </div>
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
                  <div key={rx.id} className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900">{rx.items?.length || 0} medication(s)</p>
                        <p className="text-sm text-gray-500">Dr. {rx.doctor_name} • {rx.created_at && isValid(parseISO(rx.created_at)) ? format(parseISO(rx.created_at), 'MMM d, yyyy') : '—'}</p>
                      </div>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        rx.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                      }`}>{rx.status}</span>
                    </div>
                  </div>
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
