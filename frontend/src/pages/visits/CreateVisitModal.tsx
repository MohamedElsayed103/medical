import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useCreateVisit } from '@/hooks/useVisits'
import { usePatients } from '@/hooks/usePatients'
import { useDoctors } from '@/hooks/useAppointments'

const visitSchema = z.object({
  patient_id: z.string().min(1, 'Select a patient'),
  doctor_id: z.string().min(1, 'Select a doctor'),
  visit_date: z.string().min(1, 'Required'),
  chief_complaint: z.string().min(1, 'Required'),
  history_of_present_illness: z.string().optional(),
  examination_notes: z.string().optional(),
  assessment: z.string().optional(),
  plan: z.string().optional(),
  follow_up_date: z.string().optional(),
})

type VisitForm = z.infer<typeof visitSchema>

interface Props { isOpen: boolean; onClose: () => void }

export default function CreateVisitModal({ isOpen, onClose }: Props) {
  const [patientSearch, setPatientSearch] = useState('')
  const createVisit = useCreateVisit()

  const { data: patients } = usePatients(patientSearch ? { search: patientSearch, page_size: 10 } : { page_size: 10 })
  const { data: doctors } = useDoctors({ page_size: 50 })

  const { register, handleSubmit, setValue, watch, reset, formState: { errors, isSubmitting } } = useForm<VisitForm>({
    resolver: zodResolver(visitSchema),
  })

  const selectedPatientId = watch('patient_id')

  const onSubmit = async (data: VisitForm) => {
    await createVisit.mutateAsync({
      ...data,
      visit_date: new Date(data.visit_date).toISOString(),
      follow_up_date: data.follow_up_date || undefined,
    })
    reset()
    onClose()
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} className="relative bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 rounded-t-2xl flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">New Visit Record</h2>
              <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg"><X className="w-4 h-4" /></button>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-5">
              {/* Patient */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Patient *</label>
                <input type="text" value={patientSearch} onChange={(e) => setPatientSearch(e.target.value)} placeholder="Search patients..." className="input-field mb-2" />
                <div className="max-h-28 overflow-y-auto border border-gray-200 rounded-lg divide-y divide-gray-50">
                  {patients?.results?.map(p => (
                    <button key={p.id} type="button" onClick={() => setValue('patient_id', p.id)} className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-50 ${selectedPatientId === p.id ? 'bg-primary-50 text-primary-700' : ''}`}>
                      {p.first_name} {p.last_name}
                    </button>
                  ))}
                </div>
                <input type="hidden" {...register('patient_id')} />
                {errors.patient_id && <p className="mt-1 text-xs text-red-600">{errors.patient_id.message}</p>}
              </div>

              {/* Doctor & Date */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Doctor *</label>
                  <select {...register('doctor_id')} className="input-field">
                    <option value="">Select doctor...</option>
                    {doctors?.results?.map(d => <option key={d.id} value={d.id}>{d.user_name} — {d.specialization}</option>)}
                  </select>
                  {errors.doctor_id && <p className="mt-1 text-xs text-red-600">{errors.doctor_id.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Visit Date *</label>
                  <input type="datetime-local" {...register('visit_date')} className="input-field" />
                  {errors.visit_date && <p className="mt-1 text-xs text-red-600">{errors.visit_date.message}</p>}
                </div>
              </div>

              {/* Chief Complaint */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Chief Complaint *</label>
                <input {...register('chief_complaint')} className="input-field" placeholder="Patient's main concern..." />
                {errors.chief_complaint && <p className="mt-1 text-xs text-red-600">{errors.chief_complaint.message}</p>}
              </div>

              {/* Clinical Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">History of Present Illness</label>
                <textarea {...register('history_of_present_illness')} className="input-field" rows={3} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Examination Notes</label>
                <textarea {...register('examination_notes')} className="input-field" rows={3} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Assessment</label>
                <textarea {...register('assessment')} className="input-field" rows={2} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Plan</label>
                <textarea {...register('plan')} className="input-field" rows={2} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Follow-up Date</label>
                <input type="date" {...register('follow_up_date')} className="input-field" />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                <button type="button" onClick={onClose} className="btn-ghost">Cancel</button>
                <button type="submit" disabled={isSubmitting} className="btn-primary">
                  {isSubmitting ? 'Creating...' : 'Create Visit Record'}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
