import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, FlaskConical, CheckCircle, Clock, AlertTriangle } from 'lucide-react'
import { safeFormat } from '@/lib/utils'
import { labOrdersService } from '@/services/api'
import toast from 'react-hot-toast'

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  collected: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-purple-100 text-purple-800',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
}

const PRIORITY_COLORS: Record<string, string> = {
  routine: 'bg-gray-100 text-gray-700',
  urgent: 'bg-orange-100 text-orange-700',
  stat: 'bg-red-100 text-red-700',
}

export default function LabOrderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()

  const { data: order, isLoading } = useQuery({
    queryKey: ['lab-order', id],
    queryFn: () => labOrdersService.getById(id!),
    enabled: !!id,
  })

  const transitionMut = useMutation({
    mutationFn: (action: string) => {
      if (action === 'collect') return labOrdersService.collect(id!)
      if (action === 'start') return labOrdersService.inProgress(id!)
      return labOrdersService.complete(id!)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['lab-order', id] })
      toast.success('Status updated')
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed to update status'),
  })

  if (isLoading) return (
    <div className="p-6 space-y-4">
      {[...Array(4)].map((_, i) => <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />)}
    </div>
  )

  if (!order) return (
    <div className="p-6 text-center text-gray-500">Lab order not found.</div>
  )

  const NEXT_ACTION: Record<string, { action: string; label: string }> = {
    pending: { action: 'collect', label: 'Mark Collected' },
    collected: { action: 'start', label: 'Start Processing' },
    in_progress: { action: 'complete', label: 'Mark Completed' },
  }
  const next = NEXT_ACTION[order.status]

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Back + Header */}
      <div className="flex items-start gap-4">
        <Link to="/lab-orders" className="p-2 hover:bg-gray-100 rounded-lg mt-1">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <FlaskConical className="w-6 h-6 text-purple-600" />
              {order.order_number || `Lab Order #${id?.slice(0, 8)}`}
            </h1>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[order.status] ?? 'bg-gray-100 text-gray-700'}`}>
              {order.status?.replace(/_/g, ' ')}
            </span>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${PRIORITY_COLORS[order.priority] ?? 'bg-gray-100'}`}>
              {order.priority}
            </span>
          </div>
          <p className="text-gray-500 text-sm mt-1">
            Ordered {safeFormat(order.created_at || order.ordered_at, 'MMM d, yyyy HH:mm')}
          </p>
        </div>
        {next && (
          <button onClick={() => transitionMut.mutate(next.action)}
            disabled={transitionMut.isPending}
            className="btn-primary flex items-center gap-2 shrink-0">
            <CheckCircle className="w-4 h-4" /> {next.label}
          </button>
        )}
      </div>

      {/* Patient / Orderer */}
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 p-5">
        <h2 className="font-semibold text-gray-900 mb-3">Patient / Orderer</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-500 text-xs uppercase font-medium mb-0.5">Name</p>
            <p className="font-medium text-gray-900">
              {order.patient_name || (order as any).orderer_name || '—'}
            </p>
          </div>
          <div>
            <p className="text-gray-500 text-xs uppercase font-medium mb-0.5">Type</p>
            <p className="font-medium text-gray-900 capitalize">{(order as any).orderer_type || 'patient'}</p>
          </div>
          {order.doctor_name && (
            <div>
              <p className="text-gray-500 text-xs uppercase font-medium mb-0.5">Ordering Doctor</p>
              <p className="font-medium text-gray-900">{order.doctor_name}</p>
            </div>
          )}
          {order.visit_id && (
            <div>
              <p className="text-gray-500 text-xs uppercase font-medium mb-0.5">Visit</p>
              <Link to={`/visits/${order.visit_id}`} className="font-medium text-primary-600 hover:underline">
                View Visit
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Tests */}
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Tests Ordered</h2>
        </div>
        {order.tests?.length ? (
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-5 py-2 text-xs font-semibold text-gray-500 uppercase">Test</th>
                <th className="text-left px-5 py-2 text-xs font-semibold text-gray-500 uppercase">Result</th>
                <th className="text-center px-5 py-2 text-xs font-semibold text-gray-500 uppercase">Flag</th>
                <th className="text-left px-5 py-2 text-xs font-semibold text-gray-500 uppercase">Reference</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {order.tests.map((test: any) => (
                <tr key={test.id} className="hover:bg-gray-50">
                  <td className="px-5 py-3 font-medium text-gray-900">{test.test_name || test.name}</td>
                  <td className="px-5 py-3 text-gray-700">
                    {test.result_value ? `${test.result_value} ${test.unit || ''}`.trim() : <span className="text-gray-400">Pending</span>}
                  </td>
                  <td className="px-5 py-3 text-center">
                    {test.is_flagged && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-red-100 text-red-700">
                        <AlertTriangle className="w-3 h-3" /> Flagged
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-sm text-gray-500">{test.reference_range || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="text-center py-8 text-gray-400 text-sm">No tests recorded</div>
        )}
      </div>

      {/* Invoice link */}
      {(order as any).invoice_id && (
        <div className="bg-white rounded-xl border border-gray-100 shadow-soft p-4 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-700">
            <Clock className="w-4 h-4 text-gray-400" />
            Invoice linked to this order
          </div>
          <Link to={`/billing/${(order as any).invoice_id}`} className="text-sm font-medium text-primary-600 hover:underline">
            View Invoice →
          </Link>
        </div>
      )}
    </div>
  )
}
