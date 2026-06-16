import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Calendar, CheckCircle, Play, XCircle, AlertTriangle, Stethoscope, User, FileText } from 'lucide-react'
import toast from 'react-hot-toast'
import { appointmentsService } from '@/services/api'
import { getApiErrorMessage } from '@/lib/api'
import { formatClinicDateTime } from '@/lib/utils'
import DetailHeader from '@/components/ui/DetailHeader'
import StatusTimeline from '@/components/ui/StatusTimeline'

const STEPS = ['Scheduled', 'Confirmed', 'In Progress', 'Completed']

export default function AppointmentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()
  const navigate = useNavigate()

  const { data: apt, isLoading } = useQuery({
    queryKey: ['appointment', id],
    queryFn: () => appointmentsService.getById(id!),
    enabled: !!id,
  })

  const action = useMutation({
    mutationFn: ({ a, reason }: { a: 'confirm' | 'start' | 'complete' | 'cancel' | 'no-show'; reason?: string }) => {
      if (a === 'confirm') return appointmentsService.confirm(id!)
      if (a === 'start') return appointmentsService.start(id!)
      if (a === 'complete') return appointmentsService.complete(id!)
      if (a === 'no-show') return appointmentsService.noShow(id!)
      return appointmentsService.cancel(id!, reason)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['appointment', id] })
      qc.invalidateQueries({ queryKey: ['appointments'] })
      toast.success('Appointment updated')
    },
    onError: (e) => toast.error(getApiErrorMessage(e)),
  })

  if (isLoading) return <div className="p-6 space-y-4">{[...Array(3)].map((_, i) => <div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse" />)}</div>
  if (!apt) return <div className="p-6 text-center text-gray-500">Appointment not found.</div>

  const aborted = ['cancelled', 'no_show'].includes(apt.status)
  const doctorId = typeof apt.doctor === 'string' ? apt.doctor : (apt as any).doctor?.id

  return (
    <div className="space-y-6 max-w-3xl">
      <DetailHeader
        backTo="/appointments"
        icon={<Calendar className="w-6 h-6 text-primary-600" />}
        title="Appointment"
        chips={[{ status: apt.status }, { label: apt.type?.replace('_', ' ') }]}
        subtitle={formatClinicDateTime(apt.scheduled_at) + (apt.duration_minutes ? ` • ${apt.duration_minutes} min` : '')}
        actions={
          <>
            {apt.status === 'scheduled' && <button onClick={() => action.mutate({ a: 'confirm' })} className="btn-primary text-sm flex items-center gap-1.5"><CheckCircle className="w-4 h-4" /> Confirm</button>}
            {apt.status === 'confirmed' && <button onClick={() => action.mutate({ a: 'start' })} className="btn-primary text-sm flex items-center gap-1.5"><Play className="w-4 h-4" /> Start</button>}
            {apt.status === 'in_progress' && <button onClick={() => action.mutate({ a: 'complete' })} className="btn-primary text-sm flex items-center gap-1.5"><CheckCircle className="w-4 h-4" /> Complete</button>}
            {['scheduled', 'confirmed'].includes(apt.status) && (
              <>
                <button onClick={() => action.mutate({ a: 'no-show' })} className="btn-ghost border border-amber-200 text-amber-600 text-sm flex items-center gap-1.5"><AlertTriangle className="w-4 h-4" /> No-show</button>
                <button onClick={() => { if (confirm('Cancel this appointment?')) action.mutate({ a: 'cancel' }) }} className="btn-ghost border border-red-200 text-red-600 text-sm flex items-center gap-1.5"><XCircle className="w-4 h-4" /> Cancel</button>
              </>
            )}
          </>
        }
      />

      {/* Status timeline */}
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 p-6">
        <StatusTimeline steps={STEPS} current={apt.status} aborted={aborted} abortedLabel={apt.status === 'no_show' ? 'No-show' : 'Cancelled'} />
      </div>

      {/* Details */}
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 p-5">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-xs text-gray-500 uppercase font-medium mb-0.5 flex items-center gap-1"><User className="w-3 h-3" /> Patient</p>
            {typeof apt.patient === 'string'
              ? <Link to={`/patients/${apt.patient}`} className="font-medium text-primary-600 hover:underline">{apt.patient_name || 'View patient'}</Link>
              : <p className="font-medium text-gray-900">{apt.patient_name || '—'}</p>}
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase font-medium mb-0.5 flex items-center gap-1"><Stethoscope className="w-3 h-3" /> Doctor</p>
            {doctorId
              ? <Link to={`/providers/${doctorId}`} className="font-medium text-primary-600 hover:underline">Dr. {apt.doctor_name || 'View provider'}</Link>
              : <p className="font-medium text-gray-900">Dr. {apt.doctor_name || '—'}</p>}
          </div>
          {apt.reason && (
            <div className="col-span-2">
              <p className="text-xs text-gray-500 uppercase font-medium mb-0.5">Reason</p>
              <p className="text-gray-700">{apt.reason}</p>
            </div>
          )}
          {(apt as any).cancellation_reason && (
            <div className="col-span-2">
              <p className="text-xs text-gray-500 uppercase font-medium mb-0.5">Cancellation reason</p>
              <p className="text-gray-700">{(apt as any).cancellation_reason}</p>
            </div>
          )}
        </div>
      </div>

      {/* Post-completion: record a visit */}
      {apt.status === 'completed' && typeof apt.patient === 'string' && (
        <div className="bg-white rounded-xl border border-gray-100 shadow-soft p-4 flex items-center justify-between">
          <span className="text-sm text-gray-700 flex items-center gap-2"><FileText className="w-4 h-4 text-gray-400" /> Appointment completed — record the visit.</span>
          <button onClick={() => navigate(`/visits?patient=${apt.patient}&appointment=${apt.id}`)} className="text-sm font-medium text-primary-600 hover:underline">Record visit →</button>
        </div>
      )}
    </div>
  )
}
