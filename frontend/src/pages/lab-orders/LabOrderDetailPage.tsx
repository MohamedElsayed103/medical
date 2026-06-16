import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, FlaskConical, CheckCircle, Clock, AlertTriangle, Plus } from 'lucide-react'
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

const FLAG_COLORS: Record<string, string> = {
  normal: 'bg-green-100 text-green-700',
  low: 'bg-blue-100 text-blue-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
}

function formatReference(result: any): string {
  if (!result) return '—'
  const lo = result.reference_range_low
  const hi = result.reference_range_high
  if (lo != null && hi != null) return `${lo} – ${hi}`
  if (lo != null) return `> ${lo}`
  if (hi != null) return `< ${hi}`
  return '—'
}

export default function LabOrderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()
  const [editingTest, setEditingTest] = useState<string | null>(null)
  const [resultForm, setResultForm] = useState({ value: '', unit: '', reference_range_low: '', reference_range_high: '', interpretation: '' })

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
    onError: (e: any) => toast.error(e?.response?.data?.error?.message || e?.response?.data?.detail || 'Failed to update status'),
  })

  const recordMut = useMutation({
    mutationFn: ({ testId, data }: { testId: string; data: any }) => labOrdersService.recordResult(id!, testId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['lab-order', id] })
      toast.success('Result recorded')
      setEditingTest(null)
      setResultForm({ value: '', unit: '', reference_range_low: '', reference_range_high: '', interpretation: '' })
    },
    onError: (e: any) => toast.error(e?.response?.data?.error?.message || e?.response?.data?.detail || 'Failed to record result'),
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
  // Results can be entered once the sample is collected / processing.
  const canRecord = ['collected', 'in_progress'].includes(order.status)

  const submitResult = (testId: string) => {
    if (!resultForm.value.trim()) return toast.error('Enter a result value')
    recordMut.mutate({
      testId,
      data: {
        value: resultForm.value,
        unit: resultForm.unit || '',
        reference_range_low: resultForm.reference_range_low ? Number(resultForm.reference_range_low) : null,
        reference_range_high: resultForm.reference_range_high ? Number(resultForm.reference_range_high) : null,
        interpretation: resultForm.interpretation || '',
      },
    })
  }

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
            <p className="text-gray-500 text-xs uppercase font-medium mb-0.5">Patient</p>
            <p className="font-medium text-gray-900">{order.patient_name || '—'}</p>
          </div>
          <div>
            <p className="text-gray-500 text-xs uppercase font-medium mb-0.5">Ordering Doctor</p>
            <p className="font-medium text-gray-900">{order.doctor_name || '—'}</p>
          </div>
          {order.visit && (
            <div>
              <p className="text-gray-500 text-xs uppercase font-medium mb-0.5">Visit</p>
              <Link to={`/visits/${order.visit}`} className="font-medium text-primary-600 hover:underline">
                View Visit
              </Link>
            </div>
          )}
          {order.clinical_notes && (
            <div className="col-span-2">
              <p className="text-gray-500 text-xs uppercase font-medium mb-0.5">Clinical Notes</p>
              <p className="text-gray-700">{order.clinical_notes}</p>
            </div>
          )}
        </div>
      </div>

      {/* Tests */}
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Tests &amp; Results</h2>
        </div>
        {order.tests?.length ? (
          <div className="divide-y divide-gray-50">
            {order.tests.map((test: any) => {
              const result = test.result
              const isEditing = editingTest === test.id
              return (
                <div key={test.id} className="px-5 py-3">
                  <div className="flex items-center gap-4">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900">{test.test_name}</p>
                      {test.specimen_type && <p className="text-xs text-gray-400">{test.specimen_type}</p>}
                    </div>
                    <div className="text-right">
                      {result ? (
                        <>
                          <p className="font-semibold text-gray-900">{`${result.value} ${result.unit || ''}`.trim()}</p>
                          <p className="text-xs text-gray-400">Ref: {formatReference(result)}</p>
                        </>
                      ) : (
                        <span className="text-sm text-gray-400">Pending</span>
                      )}
                    </div>
                    <div className="w-24 text-center">
                      {result?.flag && result.flag !== 'normal' && (
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full ${FLAG_COLORS[result.flag] ?? 'bg-gray-100 text-gray-700'}`}>
                          <AlertTriangle className="w-3 h-3" /> {result.flag}
                        </span>
                      )}
                      {result?.flag === 'normal' && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-700">Normal</span>
                      )}
                    </div>
                    <div className="w-28 text-right">
                      {!result && canRecord && (
                        <button
                          onClick={() => { setEditingTest(isEditing ? null : test.id); setResultForm({ value: '', unit: '', reference_range_low: '', reference_range_high: '', interpretation: '' }) }}
                          className="text-xs px-2 py-1 bg-primary-50 text-primary-700 rounded hover:bg-primary-100 inline-flex items-center gap-1"
                        >
                          <Plus className="w-3 h-3" /> Result
                        </button>
                      )}
                    </div>
                  </div>
                  {isEditing && (
                    <div className="mt-3 p-3 bg-gray-50 rounded-xl grid grid-cols-2 gap-2">
                      <input value={resultForm.value} onChange={e => setResultForm(f => ({ ...f, value: e.target.value }))} placeholder="Value *" className="input-field text-sm" />
                      <input value={resultForm.unit} onChange={e => setResultForm(f => ({ ...f, unit: e.target.value }))} placeholder="Unit (e.g. mg/dL)" className="input-field text-sm" />
                      <input type="number" value={resultForm.reference_range_low} onChange={e => setResultForm(f => ({ ...f, reference_range_low: e.target.value }))} placeholder="Ref low" className="input-field text-sm" />
                      <input type="number" value={resultForm.reference_range_high} onChange={e => setResultForm(f => ({ ...f, reference_range_high: e.target.value }))} placeholder="Ref high" className="input-field text-sm" />
                      <input value={resultForm.interpretation} onChange={e => setResultForm(f => ({ ...f, interpretation: e.target.value }))} placeholder="Interpretation (optional)" className="input-field text-sm col-span-2" />
                      <div className="col-span-2 flex justify-end gap-2">
                        <button onClick={() => setEditingTest(null)} className="btn-ghost text-sm">Cancel</button>
                        <button onClick={() => submitResult(test.id)} disabled={recordMut.isPending} className="btn-primary text-sm">
                          {recordMut.isPending ? 'Saving...' : 'Save Result'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400 text-sm">No tests recorded</div>
        )}
      </div>

      {/* Invoice link */}
      {(order as any).invoice && (
        <div className="bg-white rounded-xl border border-gray-100 shadow-soft p-4 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-700">
            <Clock className="w-4 h-4 text-gray-400" />
            Invoice linked to this order
          </div>
          <Link to={`/billing/${(order as any).invoice}`} className="text-sm font-medium text-primary-600 hover:underline">
            View Invoice →
          </Link>
        </div>
      )}
    </div>
  )
}
