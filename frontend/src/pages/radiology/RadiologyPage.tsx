import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

type RadiologyOrder = {
  id: string
  order_number: string
  status: string
  priority: string
  orderer_name: string
  orderer_type: string
  clinical_notes: string
  ordered_at: string
  completed_at: string | null
  studies: Array<{
    id: string
    modality: string
    body_part: string
    description: string
    report?: { findings: string; impression: string; is_critical: boolean }
  }>
}

const STATUS_COLORS: Record<string, string> = {
  ordered: 'bg-blue-100 text-blue-800',
  scheduled: 'bg-yellow-100 text-yellow-800',
  in_progress: 'bg-orange-100 text-orange-800',
  awaiting_report: 'bg-purple-100 text-purple-800',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
}

const NEXT_STATUS: Record<string, string> = {
  ordered: 'scheduled',
  scheduled: 'in_progress',
  in_progress: 'awaiting_report',
  awaiting_report: 'completed',
}

export default function RadiologyPage() {
  const qc = useQueryClient()
  const [statusFilter, setStatusFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['radiology-orders', statusFilter],
    queryFn: () =>
      api.get('/radiology/orders/', { params: statusFilter ? { status: statusFilter } : {} }).then((r) => r.data),
  })

  const transitionMut = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api.post(`/radiology/orders/${id}/transition/`, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['radiology-orders'] }),
  })

  const orders: RadiologyOrder[] = data?.results ?? data ?? []

  if (isLoading) return <div className="p-6 text-gray-500">Loading radiology orders...</div>

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Radiology Orders</h1>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
        >
          <option value="">All Statuses</option>
          {Object.keys(STATUS_COLORS).map((s) => (
            <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
          ))}
        </select>
      </div>

      {orders.length === 0 ? (
        <div className="text-center py-12 text-gray-500">No radiology orders found.</div>
      ) : (
        <div className="space-y-4">
          {orders.map((order) => (
            <div key={order.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-sm font-medium text-gray-600">{order.order_number}</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[order.status] ?? 'bg-gray-100 text-gray-700'}`}>
                    {order.status.replace(/_/g, ' ')}
                  </span>
                  <span className="text-xs text-gray-400 uppercase">{order.priority}</span>
                </div>
                {NEXT_STATUS[order.status] && (
                  <button
                    onClick={() => transitionMut.mutate({ id: order.id, status: NEXT_STATUS[order.status] })}
                    disabled={transitionMut.isPending}
                    className="text-sm px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    Move to {NEXT_STATUS[order.status].replace(/_/g, ' ')}
                  </button>
                )}
              </div>
              <div className="text-sm text-gray-700 mb-2">
                <span className="font-medium">{order.orderer_name}</span>
                <span className="text-gray-400 ml-1">({order.orderer_type})</span>
              </div>
              {order.clinical_notes && (
                <p className="text-sm text-gray-500 mb-3 italic">{order.clinical_notes}</p>
              )}
              <div className="flex flex-wrap gap-2">
                {order.studies.map((s) => (
                  <div key={s.id} className="bg-gray-50 rounded-lg px-3 py-2 text-xs">
                    <span className="font-medium uppercase">{s.modality}</span>
                    <span className="text-gray-500 ml-1">— {s.body_part}</span>
                    {s.report?.is_critical && (
                      <span className="ml-2 bg-red-100 text-red-700 px-1.5 py-0.5 rounded font-bold">CRITICAL</span>
                    )}
                    {s.report && (
                      <div className="mt-1 text-gray-600">{s.report.impression || s.report.findings}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
