import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameDay, isToday, startOfWeek, endOfWeek } from 'date-fns'
import { Plus, Search, Calendar as CalendarIcon, List, Clock, CheckCircle, XCircle, Play, AlertTriangle } from 'lucide-react'
import { safeFormat } from '@/lib/utils'
import { useAppointments, useAppointmentAction, useDoctors } from '@/hooks/useAppointments'
import BookAppointmentModal from './BookAppointmentModal'

export default function AppointmentsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [view, setView] = useState<'list' | 'calendar'>('list')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const [showBookModal, setShowBookModal] = useState(searchParams.get('new') === '1')
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [doctorFilter, setDoctorFilter] = useState('')

  const params: Record<string, string | number> = { page, page_size: 20, ordering: '-scheduled_at' }
  if (search) params.search = search
  if (statusFilter) params.status = statusFilter
  if (doctorFilter) params.doctor_id = doctorFilter

  const { data: doctors } = useDoctors({ page_size: 100 })

  const { data, isLoading } = useAppointments(params)
  const appointmentAction = useAppointmentAction()

  useEffect(() => {
    if (searchParams.get('new') === '1') {
      setShowBookModal(true)
      setSearchParams({})
    }
  }, [searchParams, setSearchParams])

  const handleAction = (id: string, action: 'confirm' | 'start' | 'complete' | 'cancel' | 'no-show') => {
    if (action === 'cancel' && !confirm('Cancel this appointment?')) return
    appointmentAction.mutate({ id, action })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'scheduled': return 'bg-blue-100 text-blue-700'
      case 'confirmed': return 'bg-green-100 text-green-700'
      case 'in_progress': return 'bg-purple-100 text-purple-700'
      case 'completed': return 'bg-gray-100 text-gray-700'
      case 'cancelled': return 'bg-red-100 text-red-700'
      case 'no_show': return 'bg-amber-100 text-amber-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  // Calendar helpers
  const monthStart = startOfMonth(currentMonth)
  const monthEnd = endOfMonth(currentMonth)
  const calendarStart = startOfWeek(monthStart)
  const calendarEnd = endOfWeek(monthEnd)
  const calendarDays = eachDayOfInterval({ start: calendarStart, end: calendarEnd })

  const getAppointmentsForDay = (day: Date) => {
    if (!data?.results) return []
    return data.results.filter(apt => {
      const aptDate = new Date(apt.scheduled_at)
      return isSameDay(aptDate, day)
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Appointments</h1>
          <p className="text-gray-500 text-sm mt-1">{data?.count ?? 0} total appointments</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setView('list')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${view === 'list' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500'}`}
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={() => setView('calendar')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${view === 'calendar' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500'}`}
            >
              <CalendarIcon className="w-4 h-4" />
            </button>
          </div>
          <button onClick={() => setShowBookModal(true)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Book Appointment
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            placeholder="Search patients, doctors..."
            className="input-field pl-10"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
          className="input-field w-auto"
        >
          <option value="">All Status</option>
          <option value="scheduled">Scheduled</option>
          <option value="confirmed">Confirmed</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
          <option value="no_show">No Show</option>
        </select>
      </div>

      {/* List View */}
      {view === 'list' && (
        <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
          {isLoading ? (
            <div className="p-8 space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="animate-pulse flex items-center gap-4 py-3">
                  <div className="w-12 h-12 rounded-xl bg-gray-200" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-200 rounded w-1/3" />
                    <div className="h-3 bg-gray-100 rounded w-1/4" />
                  </div>
                </div>
              ))}
            </div>
          ) : data?.results?.length ? (
            <div className="divide-y divide-gray-50">
              {data.results.map((apt) => (
                <motion.div
                  key={apt.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex items-center gap-4 p-5 hover:bg-gray-50/50 transition-colors"
                >
                  <div className="w-12 h-12 rounded-xl bg-primary-50 flex items-center justify-center">
                    <Clock className="w-5 h-5 text-primary-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900">{apt.patient_name || 'Patient'}</p>
                    <p className="text-sm text-gray-500">
                      Dr. {apt.doctor_name || 'Unknown'} • {safeFormat(apt.scheduled_at, 'MMM d, yyyy h:mm a')}
                      {apt.duration_minutes && ` • ${apt.duration_minutes} min`}
                    </p>
                    {apt.reason && <p className="text-xs text-gray-400 mt-0.5">{apt.reason}</p>}
                  </div>
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getStatusColor(apt.status)}`}>
                    {apt.status?.replace('_', ' ')}
                  </span>
                  {/* Action Buttons */}
                  <div className="flex items-center gap-1">
                    {apt.status === 'scheduled' && (
                      <button
                        onClick={() => handleAction(apt.id, 'confirm')}
                        className="p-1.5 rounded-lg hover:bg-green-50 text-green-600"
                        title="Confirm"
                      >
                        <CheckCircle className="w-4 h-4" />
                      </button>
                    )}
                    {apt.status === 'confirmed' && (
                      <button
                        onClick={() => handleAction(apt.id, 'start')}
                        className="p-1.5 rounded-lg hover:bg-purple-50 text-purple-600"
                        title="Start"
                      >
                        <Play className="w-4 h-4" />
                      </button>
                    )}
                    {apt.status === 'in_progress' && (
                      <button
                        onClick={() => handleAction(apt.id, 'complete')}
                        className="p-1.5 rounded-lg hover:bg-green-50 text-green-600"
                        title="Complete"
                      >
                        <CheckCircle className="w-4 h-4" />
                      </button>
                    )}
                    {['scheduled', 'confirmed'].includes(apt.status) && (
                      <>
                        <button
                          onClick={() => handleAction(apt.id, 'no-show')}
                          className="p-1.5 rounded-lg hover:bg-amber-50 text-amber-600"
                          title="No Show"
                        >
                          <AlertTriangle className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleAction(apt.id, 'cancel')}
                          className="p-1.5 rounded-lg hover:bg-red-50 text-red-600"
                          title="Cancel"
                        >
                          <XCircle className="w-4 h-4" />
                        </button>
                      </>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="text-center py-16">
              <CalendarIcon className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No appointments found</p>
            </div>
          )}

          {/* Pagination */}
          {data && data.count > 20 && (
            <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100">
              <p className="text-sm text-gray-500">Page {page} of {Math.ceil(data.count / 20)}</p>
              <div className="flex gap-2">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={!data.previous} className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-50 hover:bg-gray-50">Previous</button>
                <button onClick={() => setPage(p => p + 1)} disabled={!data.next} className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-50 hover:bg-gray-50">Next</button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Calendar View */}
      {view === 'calendar' && (
        <div className="bg-white rounded-2xl shadow-soft border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-6">
            <button onClick={() => setCurrentMonth(d => new Date(d.getFullYear(), d.getMonth() - 1))} className="p-2 hover:bg-gray-100 rounded-lg">&lt;</button>
            <h2 className="text-lg font-semibold text-gray-900">{format(currentMonth, 'MMMM yyyy')}</h2>
            <button onClick={() => setCurrentMonth(d => new Date(d.getFullYear(), d.getMonth() + 1))} className="p-2 hover:bg-gray-100 rounded-lg">&gt;</button>
            <select
              value={doctorFilter}
              onChange={e => setDoctorFilter(e.target.value)}
              className="input-field text-sm py-1.5 max-w-[200px]"
            >
              <option value="">All Doctors</option>
              {doctors?.results?.map(doc => (
                <option key={doc.id} value={doc.id}>{doc.user_name}</option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-7 gap-1">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => (
              <div key={d} className="text-center text-xs font-semibold text-gray-500 py-2">{d}</div>
            ))}
            {calendarDays.map((day) => {
              const dayAppointments = getAppointmentsForDay(day)
              const inMonth = day.getMonth() === currentMonth.getMonth()
              return (
                <div
                  key={day.toISOString()}
                  className={`min-h-[80px] p-1 rounded-lg border ${
                    isToday(day) ? 'border-primary-300 bg-primary-50/50' :
                    inMonth ? 'border-gray-100' : 'border-transparent'
                  } ${!inMonth ? 'opacity-30' : ''}`}
                >
                  <p className={`text-xs font-medium mb-1 ${isToday(day) ? 'text-primary-700' : 'text-gray-700'}`}>
                    {format(day, 'd')}
                  </p>
                  {dayAppointments.slice(0, 2).map(apt => (
                    <div key={apt.id} className={`text-[10px] px-1 py-0.5 rounded mb-0.5 truncate ${getStatusColor(apt.status)}`}>
                      {apt.patient_name?.split(' ')[0] || 'Apt'}
                      {apt.doctor_name && <span className="text-xs opacity-70"> · {apt.doctor_name}</span>}
                    </div>
                  ))}
                  {dayAppointments.length > 2 && (
                    <p className="text-[10px] text-gray-500">+{dayAppointments.length - 2} more</p>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Book Modal */}
      <BookAppointmentModal isOpen={showBookModal} onClose={() => setShowBookModal(false)} />
    </div>
  )
}
