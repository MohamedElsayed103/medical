import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { format, parseISO, isValid } from 'date-fns'
import { Plus, Search, DollarSign, CreditCard, TrendingUp, AlertTriangle } from 'lucide-react'
import { useInvoices, useBillingSummary, useCreateInvoice, useInvoiceAction, useRecordPayment } from '@/hooks/useBilling'
import { usePatients } from '@/hooks/usePatients'
import { motion, AnimatePresence } from 'framer-motion'
import { useForm, useFieldArray } from 'react-hook-form'
import { X } from 'lucide-react'

export default function BillingPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const [showCreate, setShowCreate] = useState(searchParams.get('new') === '1')
  const [payingInvoice, setPayingInvoice] = useState<string | null>(null)

  const params: Record<string, string | number> = { page, page_size: 15, ordering: '-created_at' }
  if (search) params.search = search
  if (statusFilter) params.status = statusFilter

  const { data, isLoading } = useInvoices(params)
  const { data: summary } = useBillingSummary()
  const invoiceAction = useInvoiceAction()

  useEffect(() => {
    if (searchParams.get('new') === '1') { setShowCreate(true); setSearchParams({}) }
  }, [searchParams, setSearchParams])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'bg-gray-100 text-gray-700'
      case 'sent': return 'bg-blue-100 text-blue-700'
      case 'paid': return 'bg-green-100 text-green-700'
      case 'partially_paid': return 'bg-yellow-100 text-yellow-700'
      case 'overdue': return 'bg-red-100 text-red-700'
      case 'cancelled': return 'bg-red-100 text-red-700'
      case 'voided': return 'bg-gray-100 text-gray-500'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Billing & Invoices</h1>
          <p className="text-gray-500 text-sm mt-1">{data?.count ?? 0} invoices</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Create Invoice
        </button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl p-4 shadow-soft border border-gray-100">
            <div className="flex items-center gap-2 mb-2"><TrendingUp className="w-4 h-4 text-green-500" /><span className="text-xs text-gray-500">Total Revenue</span></div>
            <p className="text-xl font-bold text-gray-900">${Number(summary.total_invoiced || summary.total_revenue || 0).toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-soft border border-gray-100">
            <div className="flex items-center gap-2 mb-2"><DollarSign className="w-4 h-4 text-blue-500" /><span className="text-xs text-gray-500">Outstanding</span></div>
            <p className="text-xl font-bold text-gray-900">${Number(summary.total_outstanding || 0).toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-soft border border-gray-100">
            <div className="flex items-center gap-2 mb-2"><AlertTriangle className="w-4 h-4 text-red-500" /><span className="text-xs text-gray-500">Overdue</span></div>
            <p className="text-xl font-bold text-red-600">${Number(summary.total_outstanding || 0).toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-soft border border-gray-100">
            <div className="flex items-center gap-2 mb-2"><CreditCard className="w-4 h-4 text-purple-500" /><span className="text-xs text-gray-500">Paid</span></div>
            <p className="text-xl font-bold text-gray-900">{summary.paid_count || 0} / {summary.invoice_count || 0}</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input type="text" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1) }} placeholder="Search invoices..." className="input-field pl-10" />
        </div>
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }} className="input-field w-auto">
          <option value="">All Status</option>
          <option value="draft">Draft</option>
          <option value="sent">Sent</option>
          <option value="paid">Paid</option>
          <option value="partially_paid">Partially Paid</option>
          <option value="overdue">Overdue</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {/* Invoice List */}
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="p-8 space-y-4">{[...Array(5)].map((_, i) => <div key={i} className="animate-pulse h-16 bg-gray-100 rounded" />)}</div>
        ) : data?.results?.length ? (
          <div className="divide-y divide-gray-50">
            {data.results.map(invoice => (
              <div
                key={invoice.id}
                onClick={() => navigate(`/billing/${invoice.id}`)}
                className="flex items-center gap-4 p-5 hover:bg-gray-50/50 transition-colors cursor-pointer"
              >
                <div className="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center">
                  <DollarSign className="w-5 h-5 text-emerald-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-gray-900">#{invoice.invoice_number}</p>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(invoice.status)}`}>{invoice.status?.replace('_', ' ')}</span>
                  </div>
                  <p className="text-sm text-gray-500">{invoice.patient_name} • {(() => { const d = parseISO(invoice.issued_at || invoice.created_at || ''); return isValid(d) ? format(d, 'MMM d, yyyy') : '—' })()}</p>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-gray-900">${Number(invoice.total || 0).toFixed(2)}</p>
                  {invoice.balance_due && Number(invoice.balance_due) > 0 && (
                    <p className="text-xs text-red-600">Due: ${Number(invoice.balance_due).toFixed(2)}</p>
                  )}
                </div>
                <div className="flex flex-col gap-1" onClick={(e) => e.stopPropagation()}>
                  {invoice.status === 'draft' && (
                    <button onClick={() => invoiceAction.mutate({ id: invoice.id, action: 'finalize' })} className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded hover:bg-blue-100">Finalize</button>
                  )}
                  {['sent', 'partially_paid', 'overdue'].includes(invoice.status) && (
                    <button onClick={() => setPayingInvoice(invoice.id)} className="text-xs px-2 py-1 bg-green-50 text-green-700 rounded hover:bg-green-100">Record Payment</button>
                  )}
                  {['draft', 'sent'].includes(invoice.status) && (
                    <button onClick={() => invoiceAction.mutate({ id: invoice.id, action: 'cancel' })} className="text-xs px-2 py-1 bg-red-50 text-red-700 rounded hover:bg-red-100">Cancel</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16"><DollarSign className="w-12 h-12 text-gray-300 mx-auto mb-3" /><p className="text-gray-500">No invoices found</p></div>
        )}

        {data && data.count > 15 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100">
            <p className="text-sm text-gray-500">Page {page}</p>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={!data.previous} className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-50">Previous</button>
              <button onClick={() => setPage(p => p + 1)} disabled={!data.next} className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-50">Next</button>
            </div>
          </div>
        )}
      </div>

      <CreateInvoiceModal isOpen={showCreate} onClose={() => setShowCreate(false)} />
      <PaymentModal invoiceId={payingInvoice} onClose={() => setPayingInvoice(null)} />
    </div>
  )
}

function CreateInvoiceModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [patientSearch, setPatientSearch] = useState('')
  const createInvoice = useCreateInvoice()
  const { data: patients } = usePatients(patientSearch ? { search: patientSearch, page_size: 10 } : { page_size: 10 })

  const { register, handleSubmit, setValue, watch, control, reset, formState: { isSubmitting } } = useForm({
    defaultValues: {
      patient_id: '', due_date: '', tax_rate: '0', discount_amount: '0', notes: '',
      items: [{ item_type: 'consultation', description: '', quantity: 1, unit_price: '' }],
    },
  })
  const { fields, append, remove } = useFieldArray({ control, name: 'items' })
  const selectedPatientId = watch('patient_id')

  const onSubmit = async (data: any) => {
    await createInvoice.mutateAsync({
      ...data,
      items: data.items.map((i: any) => ({ ...i, quantity: Number(i.quantity) || 1 })),
    })
    reset()
    onClose()
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} className="relative bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 rounded-t-2xl flex items-center justify-between z-10">
              <h2 className="text-lg font-semibold">Create Invoice</h2>
              <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg"><X className="w-4 h-4" /></button>
            </div>
            <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Patient *</label>
                <input type="text" value={patientSearch} onChange={(e) => setPatientSearch(e.target.value)} placeholder="Search..." className="input-field mb-1" />
                <div className="max-h-24 overflow-y-auto border rounded-lg divide-y">
                  {patients?.results?.map(p => (
                    <button key={p.id} type="button" onClick={() => setValue('patient_id', p.id)} className={`w-full text-left px-3 py-1.5 text-sm hover:bg-gray-50 ${selectedPatientId === p.id ? 'bg-primary-50' : ''}`}>{p.first_name} {p.last_name}</button>
                  ))}
                </div>
                <input type="hidden" {...register('patient_id')} />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
                  <input type="date" {...register('due_date')} className="input-field" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tax Rate (%)</label>
                  <input type="text" {...register('tax_rate')} className="input-field" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Discount ($)</label>
                  <input type="text" {...register('discount_amount')} className="input-field" />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-semibold text-gray-700">Line Items *</label>
                  <button type="button" onClick={() => append({ item_type: 'consultation', description: '', quantity: 1, unit_price: '' })} className="text-sm text-primary-600">+ Add Item</button>
                </div>
                <div className="space-y-2">
                  {fields.map((field, i) => (
                    <div key={field.id} className="p-3 bg-gray-50 rounded-xl grid grid-cols-5 gap-2 items-end">
                      <select {...register(`items.${i}.item_type`)} className="input-field text-sm">
                        <option value="consultation">Consultation</option>
                        <option value="procedure">Procedure</option>
                        <option value="medication">Medication</option>
                        <option value="lab_test">Lab Test</option>
                        <option value="other">Other</option>
                      </select>
                      <input {...register(`items.${i}.description`)} placeholder="Description *" className="input-field text-sm col-span-2" />
                      <input type="number" {...register(`items.${i}.quantity`)} placeholder="Qty" className="input-field text-sm" min={1} />
                      <div className="flex gap-1">
                        <input {...register(`items.${i}.unit_price`)} placeholder="Price *" className="input-field text-sm" />
                        {fields.length > 1 && <button type="button" onClick={() => remove(i)} className="text-red-500 text-xs">×</button>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea {...register('notes')} className="input-field" rows={2} />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <button type="button" onClick={onClose} className="btn-ghost">Cancel</button>
                <button type="submit" disabled={isSubmitting} className="btn-primary">{isSubmitting ? 'Creating...' : 'Create Invoice'}</button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}

function PaymentModal({ invoiceId, onClose }: { invoiceId: string | null; onClose: () => void }) {
  const recordPayment = useRecordPayment()
  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm({
    defaultValues: { amount: '', method: 'cash', reference_number: '', notes: '' },
  })

  const onSubmit = async (data: any) => {
    if (!invoiceId) return
    await recordPayment.mutateAsync({ id: invoiceId, data })
    reset()
    onClose()
  }

  if (!invoiceId) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold mb-4">Record Payment</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Amount *</label>
            <input type="text" {...register('amount')} className="input-field" placeholder="0.00" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Method *</label>
            <select {...register('method')} className="input-field">
              <option value="cash">Cash</option>
              <option value="credit_card">Credit Card</option>
              <option value="debit_card">Debit Card</option>
              <option value="bank_transfer">Bank Transfer</option>
              <option value="insurance">Insurance</option>
              <option value="check">Check</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Reference #</label>
            <input {...register('reference_number')} className="input-field" />
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button type="button" onClick={onClose} className="btn-ghost">Cancel</button>
            <button type="submit" disabled={isSubmitting} className="btn-primary">{isSubmitting ? 'Recording...' : 'Record Payment'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}
