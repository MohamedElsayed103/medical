import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, ScanLine, AlertTriangle, FileText, CheckCircle, XCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { radiologyService } from '@/services/api'
import { RADIOLOGY_MODALITIES } from '@/types'
import { safeFormat } from '@/lib/utils'

const STATUS_COLORS: Record<string, string> = {
  ordered: 'bg-blue-100 text-blue-800',
  scheduled: 'bg-yellow-100 text-yellow-800',
  in_progress: 'bg-orange-100 text-orange-800',
  awaiting_report: 'bg-purple-100 text-purple-800',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
}

const NEXT_STATUS: Record<string, { status: string; label: string }> = {
  ordered: { status: 'scheduled', label: 'Schedule' },
  scheduled: { status: 'in_progress', label: 'Start Acquisition' },
  in_progress: { status: 'awaiting_report', label: 'Mark Awaiting Report' },
  awaiting_report: { status: 'completed', label: 'Finalize & Complete' },
}

const modalityLabel = (v: string) => RADIOLOGY_MODALITIES.find(m => m.value === v)?.label ?? v

export default function RadiologyOrderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()
  const [reportingStudy, setReportingStudy] = useState<string | null>(null)
  const [reportForm, setReportForm] = useState({ findings: '', impression: '', is_critical: false })

  const { data: order, isLoading } = useQuery({
    queryKey: ['radiology-order', id],
    queryFn: () => radiologyService.getOrder(id!),
    enabled: !!id,
  })

  const transitionMut = useMutation({
    mutationFn: (status: string) => radiologyService.transition(id!, status),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['radiology-order', id] }); toast.success('Status updated') },
    onError: (e: any) => toast.error(e?.response?.data?.error?.message || e?.response?.data?.detail || 'Failed to update status'),
  })

  const reportMut = useMutation({
    mutationFn: (studyId: string) => radiologyService.recordReport(id!, { study_id: studyId, ...reportForm }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['radiology-order', id] })
      toast.success('Report recorded')
      setReportingStudy(null)
      setReportForm({ findings: '', impression: '', is_critical: false })
    },
    onError: (e: any) => toast.error(e?.response?.data?.error?.message || e?.response?.data?.detail || 'Failed to record report'),
  })

  if (isLoading) return (
    <div className="p-6 space-y-4">{[...Array(3)].map((_, i) => <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />)}</div>
  )
  if (!order) return <div className="p-6 text-center text-gray-500">Radiology order not found.</div>

  const next = NEXT_STATUS[order.status]
  const canReport = ['in_progress', 'awaiting_report'].includes(order.status)

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Header */}
      <div className="flex items-start gap-4">
        <Link to="/radiology" className="p-2 hover:bg-gray-100 rounded-lg mt-1"><ArrowLeft className="w-4 h-4" /></Link>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <ScanLine className="w-6 h-6 text-cyan-600" /> {order.order_number}
            </h1>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[order.status] ?? 'bg-gray-100'}`}>
              {order.status.replace(/_/g, ' ')}
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600 uppercase">{order.priority}</span>
          </div>
          <p className="text-gray-500 text-sm mt-1">Ordered {safeFormat(order.ordered_at, 'MMM d, yyyy HH:mm')}</p>
        </div>
        <div className="flex gap-2 shrink-0 flex-wrap">
          {next && (
            <button onClick={() => transitionMut.mutate(next.status)} disabled={transitionMut.isPending}
              className="btn-primary flex items-center gap-1.5 text-sm">
              <CheckCircle className="w-4 h-4" /> {next.label}
            </button>
          )}
          {!['completed', 'cancelled'].includes(order.status) && (
            <button onClick={() => { if (confirm('Cancel this radiology order?')) transitionMut.mutate('cancelled') }}
              className="btn-ghost text-red-600 border border-red-200 text-sm flex items-center gap-1.5">
              <XCircle className="w-4 h-4" /> Cancel
            </button>
          )}
        </div>
      </div>

      {/* Orderer */}
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 p-5">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-xs text-gray-500 uppercase font-medium mb-0.5">Orderer</p>
            <p className="font-medium text-gray-900">{order.orderer_name}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase font-medium mb-0.5">Type</p>
            <p className="font-medium text-gray-900 capitalize">{order.orderer_type}</p>
          </div>
          {order.clinical_notes && (
            <div className="col-span-2">
              <p className="text-xs text-gray-500 uppercase font-medium mb-0.5">Clinical Notes</p>
              <p className="text-gray-700">{order.clinical_notes}</p>
            </div>
          )}
          {order.invoice_id && (
            <div>
              <p className="text-xs text-gray-500 uppercase font-medium mb-0.5">Invoice</p>
              <Link to={`/billing/${order.invoice_id}`} className="font-medium text-primary-600 hover:underline">View invoice</Link>
            </div>
          )}
        </div>
      </div>

      {/* Studies */}
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100"><h2 className="font-semibold text-gray-900">Studies &amp; Reports</h2></div>
        <div className="divide-y divide-gray-50">
          {order.studies?.map((study) => {
            const isReporting = reportingStudy === study.id
            return (
              <div key={study.id} className="px-5 py-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-gray-900">{modalityLabel(study.modality)} — {study.body_part}</p>
                    {study.description && <p className="text-sm text-gray-500">{study.description}</p>}
                  </div>
                  {!study.report && canReport && (
                    <button onClick={() => { setReportingStudy(isReporting ? null : study.id); setReportForm({ findings: '', impression: '', is_critical: false }) }}
                      className="text-xs px-2 py-1 bg-primary-50 text-primary-700 rounded hover:bg-primary-100 inline-flex items-center gap-1 shrink-0">
                      <FileText className="w-3 h-3" /> Record Report
                    </button>
                  )}
                </div>

                {study.report && (
                  <div className="mt-3 p-3 rounded-xl bg-gray-50 border border-gray-100">
                    {study.report.is_critical && (
                      <span className="inline-flex items-center gap-1 bg-red-100 text-red-700 px-2 py-0.5 rounded text-xs font-bold mb-2">
                        <AlertTriangle className="w-3 h-3" /> CRITICAL FINDING
                      </span>
                    )}
                    <p className="text-xs text-gray-400 uppercase font-medium">Findings</p>
                    <p className="text-sm text-gray-800 whitespace-pre-line">{study.report.findings}</p>
                    {study.report.impression && (
                      <>
                        <p className="text-xs text-gray-400 uppercase font-medium mt-2">Impression</p>
                        <p className="text-sm text-gray-800 whitespace-pre-line">{study.report.impression}</p>
                      </>
                    )}
                    <p className="text-xs text-gray-400 mt-2">Reported {safeFormat(study.report.reported_at, 'MMM d, yyyy HH:mm')}</p>
                  </div>
                )}

                {isReporting && (
                  <div className="mt-3 p-3 bg-gray-50 rounded-xl space-y-2">
                    <textarea value={reportForm.findings} onChange={e => setReportForm(f => ({ ...f, findings: e.target.value }))} rows={3} placeholder="Findings *" className="input-field text-sm" />
                    <textarea value={reportForm.impression} onChange={e => setReportForm(f => ({ ...f, impression: e.target.value }))} rows={2} placeholder="Impression (optional)" className="input-field text-sm" />
                    <label className="flex items-center gap-2 text-sm text-gray-700">
                      <input type="checkbox" checked={reportForm.is_critical} onChange={e => setReportForm(f => ({ ...f, is_critical: e.target.checked }))} />
                      Mark as critical finding (notifies the referring doctor)
                    </label>
                    <div className="flex justify-end gap-2">
                      <button onClick={() => setReportingStudy(null)} className="btn-ghost text-sm">Cancel</button>
                      <button onClick={() => { if (!reportForm.findings.trim()) return toast.error('Enter findings'); reportMut.mutate(study.id) }}
                        disabled={reportMut.isPending} className="btn-primary text-sm">
                        {reportMut.isPending ? 'Saving...' : 'Save Report'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
