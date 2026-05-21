import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { format } from 'date-fns'
import { Plus, Search, FlaskConical, AlertCircle } from 'lucide-react'
import { useLabOrders, useCreateLabOrder, useLabOrderAction } from '@/hooks/useLabOrders'
import { usePatients } from '@/hooks/usePatients'
import { useDoctors } from '@/hooks/useAppointments'
import { motion, AnimatePresence } from 'framer-motion'
import { useForm, useFieldArray } from 'react-hook-form'
import { X } from 'lucide-react'

export default function LabOrdersPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const [showCreate, setShowCreate] = useState(searchParams.get('new') === '1')

  const params: Record<string, string | number> = { page, page_size: 15, ordering: '-created_at' }
  if (search) params.search = search
  if (statusFilter) params.status = statusFilter

  const { data, isLoading } = useLabOrders(params)
  const labAction = useLabOrderAction()

  useEffect(() => {
    if (searchParams.get('new') === '1') { setShowCreate(true); setSearchParams({}) }
  }, [searchParams, setSearchParams])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-700'
      case 'collected': return 'bg-blue-100 text-blue-700'
      case 'in_progress': return 'bg-purple-100 text-purple-700'
      case 'completed': return 'bg-green-100 text-green-700'
      case 'cancelled': return 'bg-red-100 text-red-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Lab Orders</h1>
          <p className="text-gray-500 text-sm mt-1">{data?.count ?? 0} orders</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Lab Order
        </button>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input type="text" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1) }} placeholder="Search lab orders..." className="input-field pl-10" />
        </div>
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }} className="input-field w-auto">
          <option value="">All Status</option>
          <option value="pending">Pending</option>
          <option value="collected">Collected</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="p-8 space-y-4">{[...Array(5)].map((_, i) => <div key={i} className="animate-pulse h-16 bg-gray-100 rounded" />)}</div>
        ) : data?.results?.length ? (
          <div className="divide-y divide-gray-50">
            {data.results.map(order => (
              <div key={order.id} className="flex items-center gap-4 p-5 hover:bg-gray-50/50 transition-colors">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${order.priority === 'urgent' ? 'bg-red-50' : 'bg-amber-50'}`}>
                  {order.priority === 'urgent' ? <AlertCircle className="w-5 h-5 text-red-600" /> : <FlaskConical className="w-5 h-5 text-amber-600" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-gray-900">#{order.order_number}</p>
                    {order.priority === 'urgent' && <span className="text-xs px-1.5 py-0.5 bg-red-100 text-red-700 rounded">Urgent</span>}
                  </div>
                  <p className="text-sm text-gray-500">
                    {order.patient_name} • Dr. {order.doctor_name} • {order.tests?.length || 0} test(s)
                  </p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {order.tests?.slice(0, 3).map((t, i) => (
                      <span key={i} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">{t.test_name}</span>
                    ))}
                  </div>
                </div>
                <div className="text-right space-y-1">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getStatusColor(order.status)}`}>
                    {order.status?.replace('_', ' ')}
                  </span>
                  <p className="text-xs text-gray-400">{format(new Date(order.created_at), 'MMM d')}</p>
                </div>
                {/* Workflow Actions */}
                <div className="flex flex-col gap-1">
                  {order.status === 'pending' && (
                    <button onClick={() => labAction.mutate({ id: order.id, action: 'collect' })} className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded hover:bg-blue-100">Collect</button>
                  )}
                  {order.status === 'collected' && (
                    <button onClick={() => labAction.mutate({ id: order.id, action: 'in_progress' })} className="text-xs px-2 py-1 bg-purple-50 text-purple-700 rounded hover:bg-purple-100">Process</button>
                  )}
                  {order.status === 'in_progress' && (
                    <button onClick={() => labAction.mutate({ id: order.id, action: 'complete' })} className="text-xs px-2 py-1 bg-green-50 text-green-700 rounded hover:bg-green-100">Complete</button>
                  )}
                  {['pending', 'collected'].includes(order.status) && (
                    <button onClick={() => labAction.mutate({ id: order.id, action: 'cancel' })} className="text-xs px-2 py-1 bg-red-50 text-red-700 rounded hover:bg-red-100">Cancel</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16"><FlaskConical className="w-12 h-12 text-gray-300 mx-auto mb-3" /><p className="text-gray-500">No lab orders found</p></div>
        )}

        {data && data.count > 15 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100">
            <p className="text-sm text-gray-500">Page {page}</p>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={!data.previous} className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-50">Previous</button>
              <button onClick={() => setPage(p => p + 1)} disabled={!data.next} className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-50">Next</button>
            </div>
          </div>
        )}
      </div>

      <CreateLabOrderModal isOpen={showCreate} onClose={() => setShowCreate(false)} />
    </div>
  )
}

function CreateLabOrderModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [patientSearch, setPatientSearch] = useState('')
  const createOrder = useCreateLabOrder()
  const { data: patients } = usePatients(patientSearch ? { search: patientSearch, page_size: 10 } : { page_size: 10 })
  const { data: doctors } = useDoctors({ page_size: 50 })

  const { register, handleSubmit, setValue, watch, control, reset, formState: { isSubmitting } } = useForm({
    defaultValues: {
      patient_id: '', doctor_id: '', priority: 'routine', clinical_notes: '',
      tests: [{ test_name: '', test_code: '', specimen_type: '', notes: '' }],
    },
  })
  const { fields, append, remove } = useFieldArray({ control, name: 'tests' })
  const selectedPatientId = watch('patient_id')

  const onSubmit = async (data: any) => {
    await createOrder.mutateAsync(data)
    reset()
    onClose()
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} className="relative bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 rounded-t-2xl flex items-center justify-between z-10">
              <h2 className="text-lg font-semibold">New Lab Order</h2>
              <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg"><X className="w-4 h-4" /></button>
            </div>
            <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-5">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Patient *</label>
                  <input type="text" value={patientSearch} onChange={(e) => setPatientSearch(e.target.value)} placeholder="Search..." className="input-field mb-1" />
                  <div className="max-h-24 overflow-y-auto border rounded-lg divide-y">
                    {patients?.results?.map(p => (
                      <button key={p.id} type="button" onClick={() => setValue('patient_id', p.id)} className={`w-full text-left px-3 py-1.5 text-sm hover:bg-gray-50 ${selectedPatientId === p.id ? 'bg-primary-50' : ''}`}>{p.first_name} {p.last_name}</button>
                    ))}
                  </div>
                  <input type="hidden" {...register('patient_id')} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Doctor *</label>
                  <select {...register('doctor_id')} className="input-field">
                    <option value="">Select...</option>
                    {doctors?.results?.map(d => <option key={d.id} value={d.id}>{d.user_name}</option>)}
                  </select>
                  <label className="block text-sm font-medium text-gray-700 mb-1 mt-3">Priority</label>
                  <select {...register('priority')} className="input-field">
                    <option value="routine">Routine</option>
                    <option value="urgent">Urgent</option>
                    <option value="stat">STAT</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Clinical Notes</label>
                <textarea {...register('clinical_notes')} className="input-field" rows={2} />
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-semibold text-gray-700">Tests *</label>
                  <button type="button" onClick={() => append({ test_name: '', test_code: '', specimen_type: '', notes: '' })} className="text-sm text-primary-600">+ Add Test</button>
                </div>
                <div className="space-y-2">
                  {fields.map((field, i) => (
                    <div key={field.id} className="p-3 bg-gray-50 rounded-xl">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-semibold text-gray-500">Test {i + 1}</span>
                        {fields.length > 1 && <button type="button" onClick={() => remove(i)} className="text-xs text-red-500">Remove</button>}
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <input {...register(`tests.${i}.test_name`)} placeholder="Test name *" className="input-field text-sm" />
                        <input {...register(`tests.${i}.test_code`)} placeholder="Code (optional)" className="input-field text-sm" />
                        <input {...register(`tests.${i}.specimen_type`)} placeholder="Specimen type" className="input-field text-sm" />
                        <input {...register(`tests.${i}.notes`)} placeholder="Notes" className="input-field text-sm" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <button type="button" onClick={onClose} className="btn-ghost">Cancel</button>
                <button type="submit" disabled={isSubmitting} className="btn-primary">{isSubmitting ? 'Creating...' : 'Create Lab Order'}</button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
