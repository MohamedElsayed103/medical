import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

type PharmacyOrder = {
  id: string
  order_number: string
  status: string
  orderer_name: string
  orderer_type: string
  created_at: string
  items: Array<{
    id: string
    medication_name: string
    quantity: number
    unit_price: string
    line_total: string
  }>
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  awaiting_payment: 'bg-yellow-100 text-yellow-800',
  paid: 'bg-blue-100 text-blue-800',
  fulfilled: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
}

export default function PharmacyOrdersPage() {
  const qc = useQueryClient()
  const [statusFilter, setStatusFilter] = useState('')
  const [showFulfillModal, setShowFulfillModal] = useState<string | null>(null)
  const [paymentAmount, setPaymentAmount] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['pharmacy-orders', statusFilter],
    queryFn: () =>
      api.get('/pharmacy/orders/', { params: statusFilter ? { status: statusFilter } : {} }).then((r) => r.data),
  })

  const completeSaleMut = useMutation({
    mutationFn: ({ id, amount }: { id: string; amount: string }) =>
      api.post(`/pharmacy/orders/${id}/complete-sale/`, { amount, method: 'cash' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pharmacy-orders'] })
      setShowFulfillModal(null)
      setPaymentAmount('')
    },
  })

  const cancelMut = useMutation({
    mutationFn: (id: string) => api.post(`/pharmacy/orders/${id}/cancel/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pharmacy-orders'] }),
  })

  const orders: PharmacyOrder[] = data?.results ?? data ?? []

  if (isLoading) return <div className="p-6 text-gray-500">Loading pharmacy orders...</div>

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Pharmacy Orders</h1>
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
        <div className="text-center py-12 text-gray-500">No pharmacy orders found.</div>
      ) : (
        <div className="space-y-4">
          {orders.map((order) => {
            const total = order.items.reduce((sum, i) => sum + parseFloat(i.line_total || '0'), 0)
            return (
              <div key={order.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm font-medium text-gray-600">{order.order_number}</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[order.status] ?? 'bg-gray-100'}`}>
                      {order.status.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    {order.status === 'draft' && (
                      <button
                        onClick={() => setShowFulfillModal(order.id)}
                        className="text-sm px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700"
                      >
                        Complete Sale
                      </button>
                    )}
                    {order.status !== 'fulfilled' && order.status !== 'cancelled' && (
                      <button
                        onClick={() => cancelMut.mutate(order.id)}
                        className="text-sm px-3 py-1.5 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                </div>
                <div className="text-sm text-gray-700 mb-3">
                  <span className="font-medium">{order.orderer_name}</span>
                  <span className="text-gray-400 ml-1">({order.orderer_type})</span>
                </div>
                <div className="space-y-1">
                  {order.items.map((item) => (
                    <div key={item.id} className="flex justify-between text-sm text-gray-600">
                      <span>{item.medication_name} × {item.quantity}</span>
                      <span className="font-medium">${item.line_total}</span>
                    </div>
                  ))}
                  <div className="border-t pt-1 flex justify-between text-sm font-bold">
                    <span>Total</span>
                    <span>${total.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {showFulfillModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-80">
            <h2 className="text-lg font-semibold mb-4">Complete Sale</h2>
            <label className="block text-sm text-gray-700 mb-1">Amount received</label>
            <input
              type="number"
              step="0.01"
              value={paymentAmount}
              onChange={(e) => setPaymentAmount(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 mb-4"
              placeholder="0.00"
            />
            <div className="flex gap-2">
              <button
                onClick={() => completeSaleMut.mutate({ id: showFulfillModal, amount: paymentAmount })}
                disabled={!paymentAmount || completeSaleMut.isPending}
                className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                Confirm
              </button>
              <button
                onClick={() => setShowFulfillModal(null)}
                className="flex-1 border border-gray-300 py-2 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
