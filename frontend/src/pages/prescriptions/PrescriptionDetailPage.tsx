import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Pill, User, Stethoscope, Calendar, FileText } from 'lucide-react'
import { safeFormat } from '@/lib/utils'
import { prescriptionsService } from '@/services/api'

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-green-100 text-green-700',
  dispensed: 'bg-blue-100 text-blue-700',
}

export default function PrescriptionDetailPage() {
  const { id } = useParams<{ id: string }>()

  const { data: rx, isLoading } = useQuery({
    queryKey: ['prescription', id],
    queryFn: () => prescriptionsService.getById(id!),
    enabled: !!id,
  })

  if (isLoading) return (
    <div className="p-6 space-y-4">
      {[...Array(4)].map((_, i) => <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />)}
    </div>
  )

  if (!rx) return <div className="p-6 text-center text-gray-500">Prescription not found.</div>

  const visitId = (rx as any).visit || rx.visit_id

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Header */}
      <div className="flex items-start gap-4">
        <Link to="/prescriptions" className="p-2 hover:bg-gray-100 rounded-lg mt-1"><ArrowLeft className="w-4 h-4" /></Link>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Pill className="w-6 h-6 text-purple-600" />
              Prescription #{id?.slice(0, 8)}
            </h1>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[rx.status] ?? 'bg-gray-100 text-gray-700'}`}>
              {rx.status}
            </span>
          </div>
          <p className="text-gray-500 text-sm mt-1">
            Prescribed {safeFormat((rx as any).prescribed_at || rx.created_at, 'MMM d, yyyy HH:mm')}
          </p>
        </div>
      </div>

      {/* Meta card */}
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 p-5">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-xs text-gray-500 uppercase font-medium mb-0.5 flex items-center gap-1"><User className="w-3 h-3" /> Patient</p>
            {typeof rx.patient === 'string' ? (
              <Link to={`/patients/${rx.patient}`} className="font-medium text-primary-600 hover:underline">{rx.patient_name || 'View patient'}</Link>
            ) : (
              <p className="font-medium text-gray-900">{rx.patient_name || '—'}</p>
            )}
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase font-medium mb-0.5 flex items-center gap-1"><Stethoscope className="w-3 h-3" /> Prescriber</p>
            <p className="font-medium text-gray-900">Dr. {rx.doctor_name || '—'}</p>
          </div>
          {visitId && (
            <div>
              <p className="text-xs text-gray-500 uppercase font-medium mb-0.5 flex items-center gap-1"><Calendar className="w-3 h-3" /> Visit</p>
              <Link to={`/visits/${visitId}`} className="font-medium text-primary-600 hover:underline">View visit</Link>
            </div>
          )}
        </div>
        {rx.notes && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <p className="text-xs text-gray-500 uppercase font-medium mb-1 flex items-center gap-1"><FileText className="w-3 h-3" /> Notes</p>
            <p className="text-sm text-gray-700">{rx.notes}</p>
          </div>
        )}
      </div>

      {/* Medications */}
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Medications ({rx.items?.length || 0})</h2>
        </div>
        {rx.items?.length ? (
          <div className="divide-y divide-gray-50">
            {rx.items.map((item: any) => (
              <div key={item.id} className="px-5 py-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      {item.medication ? (
                        <Link to={`/medications/${item.medication}`} className="font-semibold text-gray-900 hover:text-primary-600 hover:underline">
                          {item.medication_name || item.medication?.name || 'Medication'}
                        </Link>
                      ) : (
                        <span className="font-semibold text-gray-900">{item.medication_name || 'Medication'}</span>
                      )}
                      {item.is_prn && <span className="text-xs px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded">PRN</span>}
                    </div>
                    {item.instructions && <p className="text-sm text-gray-500 mt-0.5">{item.instructions}</p>}
                  </div>
                  <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded capitalize shrink-0">{item.route}</span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3 text-sm">
                  <div>
                    <p className="text-xs text-gray-400">Dosage</p>
                    <p className="font-medium text-gray-800">{item.dosage || '—'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400">Frequency</p>
                    <p className="font-medium text-gray-800">{item.frequency || '—'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400">Duration</p>
                    <p className="font-medium text-gray-800">{item.duration || '—'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400">Quantity</p>
                    <p className="font-medium text-gray-800">{item.quantity}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400 text-sm">No medications</div>
        )}
      </div>
    </div>
  )
}
