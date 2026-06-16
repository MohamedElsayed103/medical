import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { X, Search, Clock, ChevronLeft, ChevronRight } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { format, addDays, parseISO } from 'date-fns'
import { useQuery } from '@tanstack/react-query'
import { useBookAppointment, useDoctors } from '@/hooks/useAppointments'
import { usePatients } from '@/hooks/usePatients'
import { appointmentsService } from '@/services/api'
import { formatClinicTime } from '@/lib/utils'

const bookSchema = z.object({
  patient_id: z.string().min(1, 'Select a patient'),
  doctor_id: z.string().min(1, 'Select a doctor'),
  scheduled_at: z.string().min(1, 'Select a time slot'),
  duration_minutes: z.number().min(10).max(240).optional(),
  type: z.string().optional(),
  reason: z.string().optional(),
})

type BookForm = z.infer<typeof bookSchema>

interface Props {
  isOpen: boolean
  onClose: () => void
}

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

export default function BookAppointmentModal({ isOpen, onClose }: Props) {
  const [patientSearch, setPatientSearch] = useState('')
  const [selectedDate, setSelectedDate] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [weekOffset, setWeekOffset] = useState(0)
  const bookAppointment = useBookAppointment()

  const { data: patients } = usePatients(patientSearch ? { search: patientSearch, page_size: 10 } : { page_size: 10 })
  const { data: doctors } = useDoctors({ page_size: 50 })

  const { register, handleSubmit, setValue, watch, reset, formState: { errors, isSubmitting } } = useForm<BookForm>({
    resolver: zodResolver(bookSchema),
    defaultValues: { duration_minutes: 30, type: 'in_person' },
  })

  const selectedPatientId = watch('patient_id')
  const selectedDoctorId = watch('doctor_id')
  const selectedSlot = watch('scheduled_at')
  const duration = watch('duration_minutes') || 30

  const { data: slotsData, isLoading: slotsLoading } = useQuery({
    queryKey: ['slots', selectedDoctorId, selectedDate, duration],
    queryFn: () => appointmentsService.getAvailableSlots({ doctor_id: selectedDoctorId, date: selectedDate, duration_minutes: duration }),
    enabled: !!selectedDoctorId && !!selectedDate,
  })

  const slots: string[] = (slotsData as any)?.slots ?? []

  // Build 7-day week strip
  const today = new Date()
  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(today, weekOffset * 7 + i))

  const onSubmit = async (data: BookForm) => {
    await bookAppointment.mutateAsync(data)
    reset()
    setSelectedDate(format(new Date(), 'yyyy-MM-dd'))
    onClose()
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
          <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="relative bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[92vh] overflow-y-auto">

            <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 rounded-t-2xl flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Book Appointment</h2>
              <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg"><X className="w-4 h-4" /></button>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-5">

              {/* Patient */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Patient *</label>
                <div className="relative mb-2">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input type="text" value={patientSearch} onChange={e => setPatientSearch(e.target.value)}
                    placeholder="Search patients..." className="input-field pl-10" />
                </div>
                <div className="max-h-32 overflow-y-auto border border-gray-200 rounded-lg divide-y divide-gray-50">
                  {patients?.results?.map(p => (
                    <button key={p.id} type="button" onClick={() => setValue('patient_id', p.id)}
                      className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-50 ${selectedPatientId === p.id ? 'bg-primary-50 text-primary-700' : ''}`}>
                      {p.first_name} {p.last_name} <span className="text-gray-400">• {p.phone}</span>
                    </button>
                  ))}
                  {!patients?.results?.length && <p className="px-3 py-2 text-sm text-gray-400">No patients found</p>}
                </div>
                <input type="hidden" {...register('patient_id')} />
                {errors.patient_id && <p className="mt-1 text-xs text-red-600">{errors.patient_id.message}</p>}
              </div>

              {/* Doctor + specialization search */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Doctor *</label>
                <select {...register('doctor_id')} className="input-field">
                  <option value="">Select a doctor...</option>
                  {doctors?.results?.map(doc => (
                    <option key={doc.id} value={doc.id}>{doc.user_name} — {doc.specialization}</option>
                  ))}
                </select>
                {errors.doctor_id && <p className="mt-1 text-xs text-red-600">{errors.doctor_id.message}</p>}
              </div>

              {/* Duration & Type */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Duration (min)</label>
                  <input type="number" {...register('duration_minutes', { valueAsNumber: true })}
                    className="input-field" min={10} max={240} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                  <select {...register('type')} className="input-field">
                    <option value="in_person">In Person</option>
                    <option value="telehealth">Telehealth</option>
                  </select>
                </div>
              </div>

              {/* Date selector (week strip) */}
              {selectedDoctorId && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Select Date *</label>
                  <div className="flex items-center gap-1 mb-2">
                    <button type="button" onClick={() => setWeekOffset(w => w - 1)} disabled={weekOffset === 0}
                      className="p-1 rounded hover:bg-gray-100 disabled:opacity-30"><ChevronLeft className="w-4 h-4" /></button>
                    <div className="flex flex-1 gap-1">
                      {weekDays.map(day => {
                        const iso = format(day, 'yyyy-MM-dd')
                        const isPast = day < today && iso !== format(today, 'yyyy-MM-dd')
                        return (
                          <button key={iso} type="button" disabled={isPast}
                            onClick={() => setSelectedDate(iso)}
                            className={`flex-1 py-2 rounded-lg text-center text-xs font-medium transition-colors disabled:opacity-30 disabled:cursor-not-allowed
                              ${selectedDate === iso ? 'bg-primary-600 text-white' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}>
                            <div>{DAY_NAMES[day.getDay()]}</div>
                            <div className="font-bold">{format(day, 'd')}</div>
                          </button>
                        )
                      })}
                    </div>
                    <button type="button" onClick={() => setWeekOffset(w => w + 1)}
                      className="p-1 rounded hover:bg-gray-100"><ChevronRight className="w-4 h-4" /></button>
                  </div>

                  {/* Time slots */}
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Available Slots — {format(parseISO(selectedDate), 'EEE, MMM d')}
                  </label>
                  {slotsLoading ? (
                    <div className="grid grid-cols-4 gap-2">
                      {[...Array(8)].map((_, i) => <div key={i} className="h-9 bg-gray-100 rounded-lg animate-pulse" />)}
                    </div>
                  ) : slots.length === 0 ? (
                    <p className="text-sm text-gray-400 py-3 text-center">No available slots for this day</p>
                  ) : (
                    <div className="grid grid-cols-4 gap-2 max-h-40 overflow-y-auto pr-1">
                      {slots.map(slot => {
                        const slotIso = new Date(slot).toISOString()
                        const label = formatClinicTime(slot)
                        return (
                          <button key={slot} type="button"
                            onClick={() => setValue('scheduled_at', slotIso)}
                            className={`py-2 px-1 rounded-lg text-xs font-medium border transition-colors flex items-center justify-center gap-1
                              ${selectedSlot === slotIso ? 'bg-primary-600 text-white border-primary-600' : 'border-gray-200 hover:border-primary-400 hover:bg-primary-50 text-gray-700'}`}>
                            <Clock className="w-3 h-3" />{label}
                          </button>
                        )
                      })}
                    </div>
                  )}
                  <input type="hidden" {...register('scheduled_at')} />
                  {errors.scheduled_at && <p className="mt-1 text-xs text-red-600">{errors.scheduled_at.message}</p>}
                </div>
              )}

              {/* Reason */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Reason</label>
                <textarea {...register('reason')} className="input-field" rows={2} placeholder="Reason for visit..." />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                <button type="button" onClick={onClose} className="btn-ghost">Cancel</button>
                <button type="submit" disabled={isSubmitting} className="btn-primary">
                  {isSubmitting ? 'Booking...' : 'Book Appointment'}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
