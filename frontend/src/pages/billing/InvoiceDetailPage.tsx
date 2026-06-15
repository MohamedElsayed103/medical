import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { ArrowLeft, Receipt, CheckCircle, XCircle, CreditCard } from 'lucide-react'
import { safeFormat } from '@/lib/utils'
import { billingService } from '@/services/api'
import toast from 'react-hot-toast'
import { useState } from 'react'

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  issued: 'bg-blue-100 text-blue-800',
  sent: 'bg-indigo-100 text-indigo-800',
  paid: 'bg-green-100 text-green-800',
  partially_paid: 'bg-yellow-100 text-yellow-800',
  overdue: 'bg-red-100 text-red-800',
  cancelled: 'bg-gray-200 text-gray-500',
  voided: 'bg-gray-200 text-gray-500',
}

export default function InvoiceDetailPage() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()
  const [showPayModal, setShowPayModal] = useState(false)
  const [payAmount, setPayAmount] = useState('')
  const [payMethod, setPayMethod] = useState('cash')

  const { data: invoice, isLoading } = useQuery({
    queryKey: ['invoice', id],
    queryFn: () => billingService.getById(id!),
    enabled: !!id,
  })

  const { data: payments } = useQuery({
    queryKey: ['invoice-payments', id],
    queryFn: () => billingService.getPayments(id!),
    enabled: !!id,
  })

  const finalizeMut = useMutation({
    mutationFn: () => billingService.finalize(id!),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['invoice', id] }); toast.success('Invoice finalized') },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed'),
  })

  const payMut = useMutation({
    mutationFn: (data: any) => billingService.pay(id!, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invoice', id] })
      qc.invalidateQueries({ queryKey: ['invoice-payments', id] })
      toast.success('Payment recorded')
      setShowPayModal(false)
      setPayAmount('')
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Payment failed'),
  })

  const cancelMut = useMutation({
    mutationFn: () => billingService.cancel(id!),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['invoice', id] }); toast.success('Invoice cancelled') },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed'),
  })

  if (isLoading) return (
    <div className="p-6 space-y-4">
      {[...Array(4)].map((_, i) => <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />)}
    </div>
  )

  if (!invoice) return <div className="p-6 text-center text-gray-500">Invoice not found.</div>

  const balance = parseFloat(invoice.total || '0') - parseFloat(invoice.amount_paid || '0')

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Header */}
      <div className="flex items-start gap-4">
        <Link to="/billing" className="p-2 hover:bg-gray-100 rounded-lg mt-1"><ArrowLeft className="w-4 h-4" /></Link>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Receipt className="w-6 h-6 text-indigo-600" />
              {invoice.invoice_number || `Invoice #${id?.slice(0, 8)}`}
            </h1>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[invoice.status] ?? 'bg-gray-100'}`}>
              {invoice.status?.replace(/_/g, ' ')}
            </span>
          </div>
          <p className="text-gray-500 text-sm mt-1">Issued {safeFormat(invoice.issued_at || invoice.created_at, 'MMM d, yyyy')}</p>
        </div>
        <div className="flex gap-2 shrink-0 flex-wrap">
          {invoice.status === 'draft' && (
            <button onClick={() => finalizeMut.mutate()} disabled={finalizeMut.isPending}
              className="btn-primary flex items-center gap-1.5 text-sm">
              <CheckCircle className="w-4 h-4" /> Finalize
            </button>
          )}
          {['issued', 'sent', 'partially_paid', 'overdue'].includes(invoice.status) && (
            <button onClick={() => setShowPayModal(true)}
              className="btn-primary flex items-center gap-1.5 text-sm">
              <CreditCard className="w-4 h-4" /> Record Payment
            </button>
          )}
          {['draft', 'issued', 'sent'].includes(invoice.status) && (
            <button onClick={() => { if (confirm('Cancel this invoice?')) cancelMut.mutate() }}
              disabled={cancelMut.isPending}
              className="btn-ghost text-red-600 border border-red-200 text-sm flex items-center gap-1.5">
              <XCircle className="w-4 h-4" /> Cancel
            </button>
          )}
        </div>
      </div>

      {/* Summary card */}
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 p-5">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-xs text-gray-500 uppercase font-medium mb-0.5">Patient / Payer</p>
            <p className="font-medium text-gray-900">{invoice.patient_name || (invoice as any).payer_name || '—'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase font-medium mb-0.5">Total</p>
            <p className="font-bold text-gray-900 text-lg">${parseFloat(invoice.total || '0').toFixed(2)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase font-medium mb-0.5">Paid</p>
            <p className="font-medium text-green-700">${parseFloat(invoice.amount_paid || '0').toFixed(2)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase font-medium mb-0.5">Balance</p>
            <p className={`font-bold text-lg ${balance > 0 ? 'text-red-600' : 'text-green-600'}`}>${balance.toFixed(2)}</p>
          </div>
        </div>
        {invoice.due_date && (
          <p className="mt-3 text-xs text-gray-400">Due: {safeFormat(invoice.due_date, 'MMM d, yyyy')}</p>
        )}
      </div>

      {/* Line Items */}
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Line Items</h2>
        </div>
        {invoice.items?.length ? (
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-5 py-2 text-xs font-semibold text-gray-500 uppercase">Description</th>
                <th className="text-center px-5 py-2 text-xs font-semibold text-gray-500 uppercase">Qty</th>
                <th className="text-right px-5 py-2 text-xs font-semibold text-gray-500 uppercase">Unit</th>
                <th className="text-right px-5 py-2 text-xs font-semibold text-gray-500 uppercase">Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {invoice.items.map((item: any) => (
                <tr key={item.id}>
                  <td className="px-5 py-3 text-sm text-gray-800">{item.description}</td>
                  <td className="px-5 py-3 text-center text-sm text-gray-600">{item.quantity}</td>
                  <td className="px-5 py-3 text-right text-sm text-gray-600">${parseFloat(item.unit_price || '0').toFixed(2)}</td>
                  <td className="px-5 py-3 text-right text-sm font-medium text-gray-900">${parseFloat(item.total_price || item.line_total || '0').toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot className="border-t border-gray-200 bg-gray-50">
              {invoice.tax_amount && parseFloat(invoice.tax_amount) > 0 && (
                <tr>
                  <td colSpan={3} className="px-5 py-2 text-right text-sm text-gray-500">Tax</td>
                  <td className="px-5 py-2 text-right text-sm text-gray-700">${parseFloat(invoice.tax_amount).toFixed(2)}</td>
                </tr>
              )}
              {invoice.discount_amount && parseFloat(invoice.discount_amount) > 0 && (
                <tr>
                  <td colSpan={3} className="px-5 py-2 text-right text-sm text-gray-500">Discount</td>
                  <td className="px-5 py-2 text-right text-sm text-red-600">-${parseFloat(invoice.discount_amount).toFixed(2)}</td>
                </tr>
              )}
              <tr>
                <td colSpan={3} className="px-5 py-2 text-right font-semibold text-gray-900">Total</td>
                <td className="px-5 py-2 text-right font-bold text-gray-900">${parseFloat(invoice.total || '0').toFixed(2)}</td>
              </tr>
            </tfoot>
          </table>
        ) : (
          <div className="text-center py-8 text-gray-400 text-sm">No line items</div>
        )}
      </div>

      {/* Payments */}
      {payments && (Array.isArray(payments) ? payments : payments?.results ?? []).length > 0 && (
        <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100"><h2 className="font-semibold text-gray-900">Payment History</h2></div>
          <div className="divide-y divide-gray-50">
            {(Array.isArray(payments) ? payments : payments?.results ?? []).map((p: any) => (
              <div key={p.id} className="flex items-center justify-between px-5 py-3">
                <div>
                  <p className="text-sm font-medium text-gray-800">{safeFormat(p.payment_date || p.created_at, 'MMM d, yyyy HH:mm')}</p>
                  <p className="text-xs text-gray-500 capitalize">{p.method || p.payment_method}</p>
                </div>
                <p className="text-sm font-bold text-green-700">${parseFloat(p.amount).toFixed(2)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pay Modal */}
      {showPayModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-2xl p-6 w-full max-w-sm mx-4">
            <h2 className="text-lg font-bold mb-4">Record Payment</h2>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount *</label>
                <input type="number" step="0.01" value={payAmount} onChange={e => setPayAmount(e.target.value)}
                  placeholder={`Balance: $${balance.toFixed(2)}`} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Method</label>
                <select value={payMethod} onChange={e => setPayMethod(e.target.value)} className="input-field">
                  <option value="cash">Cash</option>
                  <option value="card">Card</option>
                  <option value="bank_transfer">Bank Transfer</option>
                  <option value="insurance">Insurance</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <button onClick={() => setShowPayModal(false)} className="btn-ghost">Cancel</button>
              <button onClick={() => payMut.mutate({ amount: payAmount, method: payMethod })}
                disabled={!payAmount || payMut.isPending} className="btn-primary">
                {payMut.isPending ? 'Saving...' : 'Record'}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
