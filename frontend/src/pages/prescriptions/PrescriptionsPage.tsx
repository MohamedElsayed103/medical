import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Search, Pill } from 'lucide-react'
import { safeFormat } from '@/lib/utils'
import { usePrescriptions, useCreatePrescription, useMedications } from '@/hooks/usePrescriptions'
import { usePatients } from '@/hooks/usePatients'
import { useDoctors } from '@/hooks/useAppointments'
import { motion, AnimatePresence } from 'framer-motion'
import { useForm, useFieldArray } from 'react-hook-form'
import { X } from 'lucide-react'

export default function PrescriptionsPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [showCreate, setShowCreate] = useState(false)

  const params: Record<string, string | number> = { page, page_size: 15, ordering: '-created_at' }
  if (search) params.search = search

  const { data, isLoading } = usePrescriptions(params)

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Prescriptions</h1>
          <p className="text-gray-500 text-sm mt-1">{data?.count ?? 0} prescriptions</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Prescription
        </button>
      </div>

      <div className="relative">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input type="text" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1) }} placeholder="Search prescriptions..." className="input-field pl-10" />
      </div>

      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="p-8 space-y-4">{[...Array(5)].map((_, i) => <div key={i} className="animate-pulse h-16 bg-gray-100 rounded" />)}</div>
        ) : data?.results?.length ? (
          <div className="divide-y divide-gray-50">
            {data.results.map(rx => (
              <Link key={rx.id} to={`/prescriptions/${rx.id}`} className="flex items-center gap-4 p-5 hover:bg-gray-50/50 transition-colors">
                <div className="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
                  <Pill className="w-5 h-5 text-purple-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900">{rx.patient_name}</p>
                  <p className="text-sm text-gray-500">
                    Dr. {rx.doctor_name} • {rx.items?.length || 0} medication(s) • {safeFormat(rx.created_at, 'MMM d, yyyy')}
                  </p>
                  {rx.items?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {rx.items.slice(0, 3).map((item, i) => (
                        <span key={i} className="text-xs px-2 py-0.5 bg-purple-50 text-purple-700 rounded">{item.medication?.name || item.dosage}</span>
                      ))}
                      {rx.items.length > 3 && <span className="text-xs text-gray-400">+{rx.items.length - 3} more</span>}
                    </div>
                  )}
                </div>
                <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                  rx.status === 'active' ? 'bg-green-100 text-green-700' :
                  rx.status === 'dispensed' ? 'bg-blue-100 text-blue-700' :
                  'bg-gray-100 text-gray-700'
                }`}>{rx.status}</span>
              </Link>
            ))}
          </div>
        ) : (
          <div className="text-center py-16"><Pill className="w-12 h-12 text-gray-300 mx-auto mb-3" /><p className="text-gray-500">No prescriptions found</p></div>
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

      <CreatePrescriptionModal isOpen={showCreate} onClose={() => setShowCreate(false)} />
    </div>
  )
}

function CreatePrescriptionModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [patientSearch, setPatientSearch] = useState('')
  const createRx = useCreatePrescription()
  const { data: patients } = usePatients(patientSearch ? { search: patientSearch, page_size: 10 } : { page_size: 10 })
  const { data: doctors } = useDoctors({ page_size: 50 })
  const { data: medications } = useMedications({ page_size: 100 })

  const { register, handleSubmit, setValue, watch, control, reset, formState: { isSubmitting } } = useForm({
    defaultValues: {
      patient_id: '',
      doctor_id: '',
      notes: '',
      items: [{ medication_id: '', dosage: '', frequency: '', duration: '', quantity: 1, route: 'oral', instructions: '' }],
    },
  })

  const { fields, append, remove } = useFieldArray({ control, name: 'items' })
  const selectedPatientId = watch('patient_id')

  const onSubmit = async (data: any) => {
    await createRx.mutateAsync(data)
    reset()
    onClose()
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} className="relative bg-white rounded-2xl shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 rounded-t-2xl flex items-center justify-between z-10">
              <h2 className="text-lg font-semibold">New Prescription</h2>
              <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg"><X className="w-4 h-4" /></button>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-5">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Patient *</label>
                  <input type="text" value={patientSearch} onChange={(e) => setPatientSearch(e.target.value)} placeholder="Search..." className="input-field mb-1" />
                  <div className="max-h-24 overflow-y-auto border rounded-lg divide-y">
                    {patients?.results?.map(p => (
                      <button key={p.id} type="button" onClick={() => setValue('patient_id', p.id)} className={`w-full text-left px-3 py-1.5 text-sm hover:bg-gray-50 ${selectedPatientId === p.id ? 'bg-primary-50' : ''}`}>
                        {p.first_name} {p.last_name}
                      </button>
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
                </div>
              </div>

              {/* Medication Items */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-semibold text-gray-700">Medications *</label>
                  <button type="button" onClick={() => append({ medication_id: '', dosage: '', frequency: '', duration: '', quantity: 1, route: 'oral', instructions: '' })} className="text-sm text-primary-600 hover:text-primary-700">+ Add Item</button>
                </div>
                <div className="space-y-3">
                  {fields.map((field, index) => (
                    <div key={field.id} className="p-3 bg-gray-50 rounded-xl space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-gray-500">Item {index + 1}</span>
                        {fields.length > 1 && <button type="button" onClick={() => remove(index)} className="text-xs text-red-500">Remove</button>}
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <select {...register(`items.${index}.medication_id`)} className="input-field text-sm">
                          <option value="">Select medication...</option>
                          {medications?.results?.map(m => <option key={m.id} value={m.id}>{m.name} ({m.strength})</option>)}
                        </select>
                        <input {...register(`items.${index}.dosage`)} placeholder="Dosage (e.g., 500mg)" className="input-field text-sm" />
                        <input {...register(`items.${index}.frequency`)} placeholder="Frequency (e.g., 3x/day)" className="input-field text-sm" />
                        <input {...register(`items.${index}.duration`)} placeholder="Duration (e.g., 7 days)" className="input-field text-sm" />
                        <input type="number" {...register(`items.${index}.quantity`, { valueAsNumber: true })} placeholder="Qty" className="input-field text-sm" min={1} />
                        <select {...register(`items.${index}.route`)} className="input-field text-sm">
                          <option value="oral">Oral</option>
                          <option value="topical">Topical</option>
                          <option value="injection">Injection</option>
                          <option value="inhalation">Inhalation</option>
                          <option value="sublingual">Sublingual</option>
                        </select>
                      </div>
                      <input {...register(`items.${index}.instructions`)} placeholder="Special instructions..." className="input-field text-sm" />
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea {...register('notes')} className="input-field" rows={2} />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <button type="button" onClick={onClose} className="btn-ghost">Cancel</button>
                <button type="submit" disabled={isSubmitting} className="btn-primary">{isSubmitting ? 'Creating...' : 'Create Prescription'}</button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
