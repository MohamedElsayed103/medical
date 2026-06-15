import { useState } from 'react'
import { motion } from 'framer-motion'
import { Pill, Plus, Search, Package, AlertTriangle, TrendingDown, CheckCircle, Upload } from 'lucide-react'
import { safeFormat } from '@/lib/utils'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { pharmacyService } from '@/services/api'
import toast from 'react-hot-toast'

export default function PharmacyPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'low_stock' | 'expired'>('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showDispenseModal, setShowDispenseModal] = useState(false)
  const [showBulkModal, setShowBulkModal] = useState(false)
  const [selectedItem, setSelectedItem] = useState<any>(null)

  const params: Record<string, any> = { page_size: 20 }
  if (search) params.search = search
  if (filter === 'low_stock') params.low_stock = true
  if (filter === 'expired') params.expired = true

  const { data: inventory, isLoading } = useQuery({
    queryKey: ['pharmacy', params],
    queryFn: () => pharmacyService.getInventory(params),
  })

  const createItem = useMutation({
    mutationFn: (data: any) => pharmacyService.createInventory(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pharmacy'] })
      toast.success('Item added to inventory')
      setShowCreateModal(false)
    },
    onError: (error: any) => toast.error(error?.response?.data?.detail || 'Failed to add item'),
  })

  const dispenseItem = useMutation({
    mutationFn: ({ id, quantity }: { id: string; quantity: number }) =>
      pharmacyService.dispense({ inventory_id: id, quantity }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pharmacy'] })
      toast.success('Item dispensed successfully')
      setShowDispenseModal(false)
      setSelectedItem(null)
    },
    onError: (error: any) => toast.error(error?.response?.data?.detail || 'Failed to dispense'),
  })

  const bulkUpload = useMutation({
    mutationFn: (file: File) => pharmacyService.bulkUpload(file),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['pharmacy'] })
      toast.success(`Bulk upload: ${data.created} created, ${data.updated} updated${data.errors?.length ? `, ${data.errors.length} errors` : ''}`)
      setShowBulkModal(false)
    },
    onError: (error: any) => toast.error(error?.response?.data?.detail || 'Upload failed'),
  })

  const lowStockCount = inventory?.results?.filter((i: any) => (i.quantity_on_hand ?? i.quantity) <= (i.reorder_level ?? 10)).length || 0
  const totalItems = inventory?.count || 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Pill className="w-7 h-7 text-green-600" /> Pharmacy
          </h1>
          <p className="text-gray-500 text-sm mt-1">Manage medication inventory and dispensing</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowBulkModal(true)} className="btn-ghost flex items-center gap-2 border border-gray-200">
            <Upload className="w-4 h-4" /> Bulk Upload
          </button>
          <button onClick={() => setShowCreateModal(true)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Add Item
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-gray-100 shadow-soft p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
            <Package className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">Total Items</p>
            <p className="text-xl font-bold text-gray-900">{totalItems}</p>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 shadow-soft p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-yellow-50 flex items-center justify-center">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">Low Stock</p>
            <p className="text-xl font-bold text-yellow-600">{lowStockCount}</p>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 shadow-soft p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
            <CheckCircle className="w-5 h-5 text-green-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">In Stock</p>
            <p className="text-xl font-bold text-gray-900">{totalItems - lowStockCount}</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search medications..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input-field pl-9"
          />
        </div>
        <div className="flex gap-2">
          {(['all', 'low_stock', 'expired'] as const).map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filter === f ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
            >{f === 'all' ? 'All' : f === 'low_stock' ? 'Low Stock' : 'Expired'}</button>
          ))}
        </div>
      </div>

      {/* Inventory Table */}
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="p-8 space-y-3">{[...Array(5)].map((_, i) => <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />)}</div>
        ) : !inventory?.results?.length ? (
          <div className="text-center py-12">
            <Package className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No items found</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Medication</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Category</th>
                <th className="text-center px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Quantity</th>
                <th className="text-center px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Reorder Level</th>
                <th className="text-center px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Unit Price</th>
                <th className="text-center px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Expiry</th>
                <th className="text-center px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Status</th>
                <th className="text-right px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {inventory.results.map((item: any) => {
                const qty = item.quantity_on_hand ?? item.quantity ?? 0
                const reorder = item.reorder_level ?? 10
                const isLow = qty <= reorder
                const isExpired = item.expiry_date && new Date(item.expiry_date) < new Date()
                return (
                  <motion.tr key={item.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="hover:bg-gray-50">
                    <td className="px-5 py-3">
                      <p className="font-medium text-gray-900">{item.medication_name || item.name || '—'}</p>
                      <p className="text-xs text-gray-500">{item.medication_generic || item.generic_name || ''}</p>
                    </td>
                    <td className="px-5 py-3 text-sm text-gray-600">{item.location || '-'}</td>
                    <td className="px-5 py-3 text-center">
                      <span className={`font-semibold ${isLow ? 'text-red-600' : 'text-gray-900'}`}>{qty}</span>
                    </td>
                    <td className="px-5 py-3 text-center text-sm text-gray-600">{reorder}</td>
                    <td className="px-5 py-3 text-center text-sm text-gray-600">${item.unit_cost || item.unit_price || '0.00'}</td>
                    <td className="px-5 py-3 text-center text-sm text-gray-600">
                      {safeFormat(item.expiry_date, 'MMM d, yyyy', '-')}
                    </td>
                    <td className="px-5 py-3 text-center">
                      {qty === 0 ? (
                        <span className="px-2 py-0.5 text-xs rounded-full bg-red-100 text-red-700 font-semibold">Out of Stock</span>
                      ) : isExpired ? (
                        <span className="px-2 py-0.5 text-xs rounded-full bg-red-100 text-red-700">Expired</span>
                      ) : isLow ? (
                        <span className="px-2 py-0.5 text-xs rounded-full bg-yellow-100 text-yellow-700 flex items-center gap-1 justify-center">
                          <TrendingDown className="w-3 h-3" /> Low Stock
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-700">In Stock</span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-right">
                      <button
                        onClick={() => { setSelectedItem(item); setShowDispenseModal(true) }}
                        className="text-xs font-medium text-green-600 hover:text-green-700"
                      >Dispense</button>
                    </td>
                  </motion.tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-2xl p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Add Inventory Item</h2>
            <form onSubmit={(e) => {
              e.preventDefault()
              const fd = new FormData(e.currentTarget)
              createItem.mutate({
                name: fd.get('name'),
                generic_name: fd.get('generic_name'),
                category: fd.get('category'),
                manufacturer: fd.get('manufacturer'),
                quantity: Number(fd.get('quantity')),
                unit: fd.get('unit'),
                unit_price: fd.get('unit_price'),
                reorder_level: Number(fd.get('reorder_level')),
                expiry_date: fd.get('expiry_date') || null,
                batch_number: fd.get('batch_number'),
              })
            }} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div><label className="text-xs font-medium text-gray-600">Name *</label><input name="name" required className="input-field" /></div>
                <div><label className="text-xs font-medium text-gray-600">Generic Name</label><input name="generic_name" className="input-field" /></div>
                <div><label className="text-xs font-medium text-gray-600">Category</label><input name="category" className="input-field" /></div>
                <div><label className="text-xs font-medium text-gray-600">Manufacturer</label><input name="manufacturer" className="input-field" /></div>
                <div><label className="text-xs font-medium text-gray-600">Quantity *</label><input name="quantity" type="number" required className="input-field" /></div>
                <div><label className="text-xs font-medium text-gray-600">Unit</label><input name="unit" defaultValue="tablets" className="input-field" /></div>
                <div><label className="text-xs font-medium text-gray-600">Unit Price</label><input name="unit_price" type="number" step="0.01" className="input-field" /></div>
                <div><label className="text-xs font-medium text-gray-600">Reorder Level</label><input name="reorder_level" type="number" defaultValue="10" className="input-field" /></div>
                <div><label className="text-xs font-medium text-gray-600">Expiry Date</label><input name="expiry_date" type="date" className="input-field" /></div>
                <div><label className="text-xs font-medium text-gray-600">Batch #</label><input name="batch_number" className="input-field" /></div>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button type="button" onClick={() => setShowCreateModal(false)} className="btn-secondary">Cancel</button>
                <button type="submit" disabled={createItem.isPending} className="btn-primary">
                  {createItem.isPending ? 'Adding...' : 'Add Item'}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}

      {/* Dispense Modal */}
      {showDispenseModal && selectedItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-2xl p-6 w-full max-w-md mx-4">
            <h2 className="text-lg font-bold text-gray-900 mb-2">Dispense Medication</h2>
            <p className="text-sm text-gray-500 mb-4">{selectedItem.medication_name || selectedItem.name} — Available: {selectedItem.quantity_on_hand ?? selectedItem.quantity} units</p>
            <form onSubmit={(e) => {
              e.preventDefault()
              const fd = new FormData(e.currentTarget)
              dispenseItem.mutate({ id: selectedItem.id, quantity: Number(fd.get('quantity')) })
            }}>
              <div className="mb-4">
                <label className="text-sm font-medium text-gray-700 mb-1 block">Quantity to Dispense</label>
                <input name="quantity" type="number" min="1" max={selectedItem.quantity_on_hand ?? selectedItem.quantity} required className="input-field" />
              </div>
              <div className="flex justify-end gap-3">
                <button type="button" onClick={() => { setShowDispenseModal(false); setSelectedItem(null) }} className="btn-secondary">Cancel</button>
                <button type="submit" disabled={dispenseItem.isPending} className="btn-primary">
                  {dispenseItem.isPending ? 'Dispensing...' : 'Dispense'}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
      {/* Bulk Upload Modal */}
      {showBulkModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-2xl p-6 w-full max-w-md mx-4">
            <h2 className="text-lg font-bold text-gray-900 mb-2">Bulk Upload Medications</h2>
            <p className="text-sm text-gray-500 mb-4">Upload a CSV file to create or update medications and inventory in bulk.</p>
            <div className="bg-gray-50 rounded-lg p-3 mb-4 text-xs text-gray-600 font-mono">
              medication_name, generic_name, strength, form, quantity,<br />
              unit_cost, batch_number, expiry_date, reorder_level
            </div>
            <input
              type="file"
              accept=".csv"
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-green-50 file:text-green-700 hover:file:bg-green-100 mb-4"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) bulkUpload.mutate(file)
              }}
            />
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowBulkModal(false)} className="btn-ghost">Cancel</button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
