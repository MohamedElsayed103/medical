import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Stethoscope, Clock, CalendarOff, Mail, Award } from 'lucide-react'
import { appointmentsService, availabilityService } from '@/services/api'
import { formatClinicDateTime } from '@/lib/utils'
import DetailHeader from '@/components/ui/DetailHeader'
import StatusChip from '@/components/ui/StatusChip'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

export default function ProviderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: doctor, isLoading } = useQuery({
    queryKey: ['doctor', id],
    queryFn: () => appointmentsService.getDoctor(id!),
    enabled: !!id,
  })
  const { data: windows } = useQuery({
    queryKey: ['availability-windows', id],
    queryFn: () => availabilityService.getWindows({ doctor_id: id! }),
    enabled: !!id,
  })
  const { data: timeOff } = useQuery({
    queryKey: ['time-off', id],
    queryFn: () => availabilityService.getTimeOff({ doctor_id: id! }),
    enabled: !!id,
  })
  const { data: appts } = useQuery({
    queryKey: ['provider-appts', id],
    queryFn: () => appointmentsService.getAll({ doctor_id: id!, ordering: 'scheduled_at', page_size: 10 }),
    enabled: !!id,
  })

  if (isLoading) return <div className="p-6 space-y-4">{[...Array(3)].map((_, i) => <div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse" />)}</div>
  if (!doctor) return <div className="p-6 text-center text-gray-500">Provider not found.</div>

  const windowList: any[] = (windows as any)?.results ?? (windows as any) ?? []
  const timeOffList: any[] = (timeOff as any)?.results ?? (timeOff as any) ?? []

  return (
    <div className="space-y-6 max-w-4xl">
      <DetailHeader
        backTo="/appointments"
        icon={<Stethoscope className="w-6 h-6 text-primary-600" />}
        title={`Dr. ${doctor.user_name || ''}`.trim()}
        subtitle={doctor.specialization}
        chips={[{ label: doctor.is_available ? 'Available' : 'Unavailable' }]}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile */}
        <div className="bg-white rounded-2xl shadow-soft border border-gray-100 p-5 space-y-3">
          <h2 className="font-semibold text-gray-900">Profile</h2>
          <div className="text-sm space-y-2">
            {doctor.specialization && <p className="flex items-center gap-2 text-gray-700"><Award className="w-4 h-4 text-gray-400" /> {doctor.specialization}</p>}
            {doctor.qualification && <p className="text-gray-600">{doctor.qualification}</p>}
            {typeof doctor.years_of_experience === 'number' && <p className="text-gray-600">{doctor.years_of_experience} yrs experience</p>}
            {doctor.consultation_fee && <p className="text-gray-600">Fee: ${Number(doctor.consultation_fee).toFixed(2)}</p>}
            {doctor.user_id && <p className="flex items-center gap-2 text-gray-500 text-xs"><Mail className="w-3 h-3" /> {doctor.user_name}</p>}
          </div>
          {doctor.bio && <p className="text-sm text-gray-600 pt-2 border-t border-gray-100">{doctor.bio}</p>}
        </div>

        {/* Weekly availability */}
        <div className="bg-white rounded-2xl shadow-soft border border-gray-100 p-5">
          <h2 className="font-semibold text-gray-900 mb-3 flex items-center gap-2"><Clock className="w-4 h-4 text-blue-600" /> Weekly Availability</h2>
          {windowList.length ? (
            <div className="space-y-2">
              {DAYS.map((day, idx) => {
                const dayWindows = windowList.filter(w => w.day_of_week === idx)
                if (!dayWindows.length) return null
                return (
                  <div key={day} className="text-sm">
                    <span className="text-gray-500 w-24 inline-block">{day}</span>
                    {dayWindows.map((w: any) => (
                      <span key={w.id} className="inline-block mr-2 px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs">
                        {w.start_time?.slice(0, 5)}–{w.end_time?.slice(0, 5)}
                      </span>
                    ))}
                  </div>
                )
              })}
            </div>
          ) : <p className="text-sm text-gray-400">No availability configured</p>}
          <Link to="/appointments/availability" className="text-xs text-primary-600 hover:underline mt-3 inline-block">Manage availability →</Link>
        </div>

        {/* Time off */}
        <div className="bg-white rounded-2xl shadow-soft border border-gray-100 p-5">
          <h2 className="font-semibold text-gray-900 mb-3 flex items-center gap-2"><CalendarOff className="w-4 h-4 text-red-500" /> Time Off</h2>
          {timeOffList.length ? (
            <div className="space-y-2 text-sm">
              {timeOffList.map((t: any) => (
                <div key={t.id}>
                  <p className="text-gray-700">{formatClinicDateTime(t.start_at)} → {formatClinicDateTime(t.end_at)}</p>
                  {t.reason && <p className="text-xs text-gray-400">{t.reason}</p>}
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-gray-400">No time-off scheduled</p>}
        </div>
      </div>

      {/* Upcoming appointments */}
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100"><h2 className="font-semibold text-gray-900">Upcoming Schedule</h2></div>
        {appts?.results?.length ? (
          <div className="divide-y divide-gray-50">
            {appts.results.map(a => (
              <div key={a.id} onClick={() => navigate(`/appointments/${a.id}`)}
                className="flex items-center justify-between px-5 py-3 hover:bg-gray-50 cursor-pointer">
                <div>
                  <p className="font-medium text-gray-900">{a.patient_name || 'Patient'}</p>
                  <p className="text-xs text-gray-500">{formatClinicDateTime(a.scheduled_at)}</p>
                </div>
                <StatusChip status={a.status} />
              </div>
            ))}
          </div>
        ) : <div className="text-center py-8 text-gray-400 text-sm">No appointments</div>}
      </div>
    </div>
  )
}
