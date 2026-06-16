import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, X, ScanLine, AlertTriangle, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { radiologyService } from '@/services/api'
import { usePatients } from '@/hooks/usePatients'
import { useDoctors } from '@/hooks/useAppointments'
import { RADIOLOGY_MODALITIES, type RadiologyOrder } from '@/types'
import { safeFormat } from '@/lib/utils'

const STATUS_COLORS: Record<string, string> = {
  ordered: 'bg-blue-100 text-blue-800',
  scheduled: 'bg-yellow-100 text-yellow-800',
  in_progress: 'bg-orange-100 text-orange-800',
  awaiting_report: 'bg-purple-100 text-purple-800',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
}

export default function RadiologyPage() {
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState('')
  const [showCreate, setShowCreate] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['radiology-orders', statusFilter],
    queryFn: () => radiologyService.getOrders(statusFilter ? { status: statusFilter } : {}),
  })

  const orders: RadiologyOrder[] = data?.results ?? (data as any) ?? []

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <ScanLine className="w-6 h-6 text-cyan-600" /> Radiology
          </h1>
          <p className="text-gray-500 text-sm mt-1">{data?.count ?? orders.length} imaging orders</p>
        </div>
        <div className="flex items-center gap-3">
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="input-field w-auto">
            <option value="">All Statuses</option>
            {Object.keys(STATUS_COLORS).map((s) => (
              <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
            ))}
          </select>
          <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> New Imaging Request
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">{[...Array(4)].map((_, i) => <div key={i} className="h-24 bg-gray-100 rounded-2xl animate-pulse" />)}</div>
      ) : orders.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 text-center py-16">
          <ScanLine className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No radiology orders yet. Create an imaging request to get started.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {orders.map((order) => (
            <div key={order.id} onClick={() => navigate(`/radiology/${order.id}`)}
              className="bg-white rounded-2xl shadow-soft border border-gray-100 p-5 hover:bg-gray-50/50 cursor-pointer transition-colors">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="font-mono text-sm font-medium text-gray-700">{order.order_number}</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[order.status] ?? 'bg-gray-100 text-gray-700'}`}>
                    {order.status.replace(/_/g, ' ')}
                  </span>
                  <span className="text-xs text-gray-400 uppercase">{order.priority}</span>
                </div>
                <span className="text-xs text-gray-400">{safeFormat(order.ordered_at, 'MMM d, yyyy')}</span>
              </div>
              <div className="text-sm text-gray-700 mb-2">
                <span className="font-medium">{order.orderer_name}</span>
                <span className="text-gray-400 ml-1 capitalize">({order.orderer_type})</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {order.studies?.map((s) => (
                  <div key={s.id} className="bg-gray-50 rounded-lg px-3 py-1.5 text-xs">
                    <span className="font-medium uppercase">{s.modality}</span>
                    <span className="text-gray-500 ml-1">— {s.body_part}</span>
                    {s.report?.is_critical && (
                      <span className="ml-2 inline-flex items-center gap-1 bg-red-100 text-red-700 px-1.5 py-0.5 rounded font-bold">
                        <AlertTriangle className="w-3 h-3" /> CRITICAL
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <CreateRadiologyModal isOpen={showCreate} onClose={() => setShowCreate(false)} />
    </div>
  )
}

type StudyRow = { modality: string; body_part: string; description: string }

function CreateRadiologyModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const qc = useQueryClient()
  const [ordererType, setOrdererType] = useState<'patient' | 'external'>('patient')
  const [patientSearch, setPatientSearch] = useState('')
  const [patientId, setPatientId] = useState('')
  const [customer, setCustomer] = useState({ name: '', phone: '' })
  const [doctorId, setDoctorId] = useState('')
  const [priority, setPriority] = useState('routine')
  const [clinicalNotes, setClinicalNotes] = useState('')
  const [studies, setStudies] = useState<StudyRow[]>([{ modality: 'xray', body_part: '', description: '' }])

  const { data: patients } = usePatients(patientSearch ? { search: patientSearch, page_size: 10 } : { page_size: 10 })
  const { data: doctors } = useDoctors({ page_size: 50 })

  const createMut = useMutation({
    mutationFn: () => radiologyService.createOrder({
      ...(ordererType === 'patient' ? { patient_id: patientId } : { customer_name: customer.name, customer_phone: customer.phone }),
      doctor_id: doctorId || null,
      priority,
      clinical_notes: clinicalNotes,
      studies: studies.filter(s => s.body_part.trim()),
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['radiology-orders'] })
      toast.success('Radiology order created')
      reset()
      onClose()
    },
    onError: (e: any) => toast.error(e?.response?.data?.error?.message || e?.response?.data?.detail || 'Failed to create order'),
  })

  const reset = () => {
    setOrdererType('patient'); setPatientId(''); setPatientSearch(''); setCustomer({ name: '', phone: '' })
    setDoctorId(''); setPriority('routine'); setClinicalNotes(''); setStudies([{ modality: 'xray', body_part: '', description: '' }])
  }

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (ordererType === 'patient' && !patientId) return toast.error('Select a patient')
    if (ordererType === 'external' && (!customer.name || !customer.phone)) return toast.error('Enter walk-in name and phone')
    if (!studies.some(s => s.body_part.trim())) return toast.error('Add at least one study with a body part')
    createMut.mutate()
  }

  const updateStudy = (i: number, key: keyof StudyRow, value: string) =>
    setStudies(s => s.map((row, idx) => idx === i ? { ...row, [key]: value } : row))

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} className="relative bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 rounded-t-2xl flex items-center justify-between z-10">
              <h2 className="text-lg font-semibold">New Imaging Request</h2>
              <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg"><X className="w-4 h-4" /></button>
            </div>
            <form onSubmit={submit} className="p-6 space-y-5">
              {/* Orderer type toggle */}
              <div className="flex gap-2">
                <button type="button" onClick={() => setOrdererType('patient')}
                  className={`flex-1 py-2 rounded-lg text-sm font-medium border ${ordererType === 'patient' ? 'bg-primary-50 border-primary-300 text-primary-700' : 'border-gray-200 text-gray-500'}`}>
                  Registered Patient
                </button>
                <button type="button" onClick={() => setOrdererType('external')}
                  className={`flex-1 py-2 rounded-lg text-sm font-medium border ${ordererType === 'external' ? 'bg-primary-50 border-primary-300 text-primary-700' : 'border-gray-200 text-gray-500'}`}>
                  Walk-in / External
                </button>
              </div>

              {ordererType === 'patient' ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Patient *</label>
                  <input type="text" value={patientSearch} onChange={(e) => setPatientSearch(e.target.value)} placeholder="Search..." className="input-field mb-1" />
                  <div className="max-h-28 overflow-y-auto border rounded-lg divide-y">
                    {patients?.results?.map(p => (
                      <button key={p.id} type="button" onClick={() => setPatientId(p.id)}
                        className={`w-full text-left px-3 py-1.5 text-sm hover:bg-gray-50 ${patientId === p.id ? 'bg-primary-50' : ''}`}>
                        {p.first_name} {p.last_name}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
                    <input value={customer.name} onChange={e => setCustomer(c => ({ ...c, name: e.target.value }))} className="input-field" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Phone *</label>
                    <input value={customer.phone} onChange={e => setCustomer(c => ({ ...c, phone: e.target.value }))} className="input-field" />
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Referring Doctor</label>
                  <select value={doctorId} onChange={e => setDoctorId(e.target.value)} className="input-field">
                    <option value="">None</option>
                    {doctors?.results?.map(d => <option key={d.id} value={d.id}>{d.user_name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                  <select value={priority} onChange={e => setPriority(e.target.value)} className="input-field">
                    <option value="routine">Routine</option>
                    <option value="urgent">Urgent</option>
                    <option value="stat">STAT</option>
                  </select>
                </div>
              </div>

              {/* Studies builder */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-semibold text-gray-700">Studies (type of imaging) *</label>
                  <button type="button" onClick={() => setStudies(s => [...s, { modality: 'xray', body_part: '', description: '' }])} className="text-sm text-primary-600">+ Add Study</button>
                </div>
                <div className="space-y-2">
                  {studies.map((study, i) => (
                    <div key={i} className="p-3 bg-gray-50 rounded-xl grid grid-cols-12 gap-2 items-center">
                      <select value={study.modality} onChange={e => updateStudy(i, 'modality', e.target.value)} className="input-field text-sm col-span-3">
                        {RADIOLOGY_MODALITIES.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                      </select>
                      <input value={study.body_part} onChange={e => updateStudy(i, 'body_part', e.target.value)} placeholder="Body part (e.g. Chest) *" className="input-field text-sm col-span-4" />
                      <input value={study.description} onChange={e => updateStudy(i, 'description', e.target.value)} placeholder="Description / view (optional)" className="input-field text-sm col-span-4" />
                      <button type="button" onClick={() => setStudies(s => s.filter((_, idx) => idx !== i))} disabled={studies.length === 1}
                        className="col-span-1 flex justify-center text-gray-400 hover:text-red-500 disabled:opacity-30">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Clinical Notes</label>
                <textarea value={clinicalNotes} onChange={e => setClinicalNotes(e.target.value)} rows={2} className="input-field" placeholder="Reason for the imaging request..." />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <button type="button" onClick={onClose} className="btn-ghost">Cancel</button>
                <button type="submit" disabled={createMut.isPending} className="btn-primary">{createMut.isPending ? 'Creating...' : 'Create Request'}</button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
