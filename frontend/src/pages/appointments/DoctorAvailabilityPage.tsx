import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Plus, Trash2, Clock, CalendarOff, CalendarCheck } from 'lucide-react'
import toast from 'react-hot-toast'
import { availabilityService, appointmentsService } from '@/services/api'
import { safeFormat } from '@/lib/utils'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

export default function DoctorAvailabilityPage() {
  const qc = useQueryClient()
  const [selectedDoctorId, setSelectedDoctorId] = useState('')
  const [showWindowModal, setShowWindowModal] = useState(false)
  const [showTimeOffModal, setShowTimeOffModal] = useState(false)

  // Window form state
  const [wForm, setWForm] = useState({ day_of_week: 0, start_time: '09:00', end_time: '17:00' })
  // Time-off form state
  const [tForm, setTForm] = useState({ start_at: '', end_at: '', reason: '' })

  const { data: doctors } = useQuery({
    queryKey: ['doctors'],
    queryFn: () => appointmentsService.getDoctors({ page_size: 100 }),
  })

  const { data: windows } = useQuery({
    queryKey: ['availability-windows', selectedDoctorId],
    queryFn: () => availabilityService.getWindows(selectedDoctorId ? { doctor_id: selectedDoctorId } : {}),
    enabled: true,
  })

  const { data: timeOffs } = useQuery({
    queryKey: ['time-off', selectedDoctorId],
    queryFn: () => availabilityService.getTimeOff(selectedDoctorId ? { doctor_id: selectedDoctorId } : {}),
    enabled: true,
  })

  const createWindow = useMutation({
    mutationFn: (data: any) => availabilityService.createWindow(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['availability-windows'] })
      toast.success('Availability window created')
      setShowWindowModal(false)
      setWForm({ day_of_week: 0, start_time: '09:00', end_time: '17:00' })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed to create window'),
  })

  const deleteWindow = useMutation({
    mutationFn: (id: string) => availabilityService.deleteWindow(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['availability-windows'] })
      toast.success('Window removed')
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed to remove'),
  })

  const createTimeOff = useMutation({
    mutationFn: (data: any) => availabilityService.createTimeOff(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['time-off'] })
      toast.success('Time-off block created')
      setShowTimeOffModal(false)
      setTForm({ start_at: '', end_at: '', reason: '' })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed to create time-off'),
  })

  const deleteTimeOff = useMutation({
    mutationFn: (id: string) => availabilityService.deleteTimeOff(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['time-off'] })
      toast.success('Time-off removed')
    },
  })

  const windowList: any[] = windows?.results ?? windows ?? []
  const timeOffList: any[] = timeOffs?.results ?? timeOffs ?? []

  const doctorList: any[] = doctors?.results ?? []

  const filteredWindows = selectedDoctorId
    ? windowList.filter(w => w.doctor_id === selectedDoctorId)
    : windowList

  const filteredTimeOffs = selectedDoctorId
    ? timeOffList.filter(t => t.doctor_id === selectedDoctorId)
    : timeOffList

  const handleCreateWindow = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedDoctorId) return toast.error('Select a doctor first')
    createWindow.mutate({ ...wForm, doctor_id: selectedDoctorId })
  }

  const handleCreateTimeOff = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedDoctorId) return toast.error('Select a doctor first')
    createTimeOff.mutate({ ...tForm, doctor_id: selectedDoctorId })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <CalendarCheck className="w-6 h-6 text-blue-600" /> Doctor Availability
          </h1>
          <p className="text-gray-500 text-sm mt-1">Manage recurring availability windows and time-off blocks</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowTimeOffModal(true)}
            className="btn-ghost flex items-center gap-2 border border-gray-200">
            <CalendarOff className="w-4 h-4" /> Add Time-Off
          </button>
          <button onClick={() => setShowWindowModal(true)}
            className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Add Window
          </button>
        </div>
      </div>

      {/* Doctor filter */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-soft p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Doctor</label>
        <select value={selectedDoctorId} onChange={e => setSelectedDoctorId(e.target.value)} className="input-field max-w-sm">
          <option value="">All Doctors</option>
          {doctorList.map(d => (
            <option key={d.id} value={d.id}>{d.user_name} — {d.specialization}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Availability Windows */}
        <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
            <Clock className="w-4 h-4 text-blue-600" />
            <h2 className="font-semibold text-gray-900">Weekly Windows</h2>
            <span className="ml-auto text-sm text-gray-400">{filteredWindows.length} windows</span>
          </div>
          {filteredWindows.length === 0 ? (
            <div className="text-center py-10 text-gray-400 text-sm">No availability windows configured</div>
          ) : (
            <div className="divide-y divide-gray-50">
              {DAYS.map((day, idx) => {
                const dayWindows = filteredWindows.filter(w => w.day_of_week === idx)
                if (!dayWindows.length) return null
                return (
                  <div key={day} className="px-5 py-3">
                    <p className="text-xs font-semibold text-gray-500 uppercase mb-2">{day}</p>
                    {dayWindows.map((w: any) => (
                      <motion.div key={w.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
                        className="flex items-center justify-between bg-blue-50 rounded-lg px-3 py-2 mb-1">
                        <div className="flex items-center gap-2">
                          <Clock className="w-3.5 h-3.5 text-blue-600" />
                          <span className="text-sm font-medium text-blue-800">
                            {w.start_time?.slice(0, 5)} – {w.end_time?.slice(0, 5)}
                          </span>
                          {!w.is_active && (
                            <span className="text-xs bg-gray-200 text-gray-500 px-1.5 py-0.5 rounded">Inactive</span>
                          )}
                        </div>
                        <button onClick={() => { if (confirm('Remove this window?')) deleteWindow.mutate(w.id) }}
                          className="p-1 hover:bg-blue-100 rounded text-blue-400 hover:text-red-500">
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </motion.div>
                    ))}
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Time Off */}
        <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
            <CalendarOff className="w-4 h-4 text-red-500" />
            <h2 className="font-semibold text-gray-900">Time-Off Blocks</h2>
            <span className="ml-auto text-sm text-gray-400">{filteredTimeOffs.length} blocks</span>
          </div>
          {filteredTimeOffs.length === 0 ? (
            <div className="text-center py-10 text-gray-400 text-sm">No time-off blocks scheduled</div>
          ) : (
            <div className="divide-y divide-gray-50">
              {filteredTimeOffs.map((t: any) => (
                <motion.div key={t.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  className="flex items-center justify-between px-5 py-3">
                  <div>
                    <p className="text-sm font-medium text-gray-800">
                      {safeFormat(t.start_at, 'MMM d, HH:mm')} → {safeFormat(t.end_at, 'MMM d, HH:mm')}
                    </p>
                    {t.reason && <p className="text-xs text-gray-500 mt-0.5">{t.reason}</p>}
                  </div>
                  <button onClick={() => { if (confirm('Remove this time-off block?')) deleteTimeOff.mutate(t.id) }}
                    className="p-1.5 hover:bg-red-50 rounded text-gray-400 hover:text-red-500">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Add Window Modal */}
      {showWindowModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-2xl p-6 w-full max-w-md mx-4">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Add Availability Window</h2>
            <form onSubmit={handleCreateWindow} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Doctor *</label>
                <select value={selectedDoctorId} onChange={e => setSelectedDoctorId(e.target.value)} className="input-field" required>
                  <option value="">Select doctor...</option>
                  {doctorList.map(d => (
                    <option key={d.id} value={d.id}>{d.user_name} — {d.specialization}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Day of Week *</label>
                <select value={wForm.day_of_week} onChange={e => setWForm(f => ({ ...f, day_of_week: Number(e.target.value) }))} className="input-field">
                  {DAYS.map((d, i) => <option key={i} value={i}>{d}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Start Time *</label>
                  <input type="time" value={wForm.start_time}
                    onChange={e => setWForm(f => ({ ...f, start_time: e.target.value }))}
                    className="input-field" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">End Time *</label>
                  <input type="time" value={wForm.end_time}
                    onChange={e => setWForm(f => ({ ...f, end_time: e.target.value }))}
                    className="input-field" required />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowWindowModal(false)} className="btn-ghost">Cancel</button>
                <button type="submit" disabled={createWindow.isPending} className="btn-primary">
                  {createWindow.isPending ? 'Saving...' : 'Add Window'}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}

      {/* Add Time-Off Modal */}
      {showTimeOffModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-2xl p-6 w-full max-w-md mx-4">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Block Time-Off</h2>
            <form onSubmit={handleCreateTimeOff} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Doctor *</label>
                <select value={selectedDoctorId} onChange={e => setSelectedDoctorId(e.target.value)} className="input-field" required>
                  <option value="">Select doctor...</option>
                  {doctorList.map(d => (
                    <option key={d.id} value={d.id}>{d.user_name} — {d.specialization}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">From *</label>
                  <input type="datetime-local" value={tForm.start_at}
                    onChange={e => setTForm(f => ({ ...f, start_at: e.target.value }))}
                    className="input-field" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Until *</label>
                  <input type="datetime-local" value={tForm.end_at}
                    onChange={e => setTForm(f => ({ ...f, end_at: e.target.value }))}
                    className="input-field" required />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Reason</label>
                <input type="text" value={tForm.reason}
                  onChange={e => setTForm(f => ({ ...f, reason: e.target.value }))}
                  placeholder="e.g. Conference, Annual leave..."
                  className="input-field" />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowTimeOffModal(false)} className="btn-ghost">Cancel</button>
                <button type="submit" disabled={createTimeOff.isPending} className="btn-primary">
                  {createTimeOff.isPending ? 'Saving...' : 'Block Time'}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  )
}
