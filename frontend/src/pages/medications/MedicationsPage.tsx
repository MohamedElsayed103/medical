import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Search, Pill, X, ImageIcon } from 'lucide-react'
import toast from 'react-hot-toast'
import { prescriptionsService } from '@/services/api'

const FORMS = ['tablet', 'capsule', 'syrup', 'injection', 'cream', 'drops', 'inhaler']

export default function MedicationsPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [showCreate, setShowCreate] = useState(false)

  const params: Record<string, string | number> = { page, page_size: 20, ordering: 'name' }
  if (search) params.search = search

  const { data, isLoading } = useQuery({
    queryKey: ['medications', params],
    queryFn: () => prescriptionsService.getMedications(params),
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Medications</h1>
          <p className="text-gray-500 text-sm mt-1">{data?.count ?? 0} medications in the formulary</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Add Medication
        </button>
      </div>

      <div className="relative">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input type="text" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1) }} placeholder="Search by name or generic name..." className="input-field pl-10" />
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => <div key={i} className="h-40 bg-gray-100 rounded-2xl animate-pulse" />)}
        </div>
      ) : data?.results?.length ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.results.map(med => (
            <Link key={med.id} to={`/medications/${med.id}`}
              className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden hover:shadow-md transition-shadow">
              <div className="h-32 bg-gray-50 flex items-center justify-center overflow-hidden">
                {med.image_url ? (
                  <img src={med.image_url} alt={med.name} className="w-full h-full object-cover" />
                ) : (
                  <ImageIcon className="w-10 h-10 text-gray-300" />
                )}
              </div>
              <div className="p-4">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-semibold text-gray-900 truncate">{med.name}</p>
                  <span className="text-xs px-2 py-0.5 bg-purple-50 text-purple-700 rounded capitalize shrink-0">{med.form}</span>
                </div>
                <p className="text-sm text-gray-500 truncate">{med.generic_name}</p>
                <p className="text-xs text-gray-400 mt-1">{med.strength}{med.manufacturer ? ` • ${med.manufacturer}` : ''}</p>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-100 text-center py-16">
          <Pill className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No medications found</p>
        </div>
      )}

      {data && data.count > 20 && (
        <div className="flex items-center justify-end gap-2">
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={!data.previous} className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-50">Previous</button>
          <button onClick={() => setPage(p => p + 1)} disabled={!data.next} className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-50">Next</button>
        </div>
      )}

      <CreateMedicationModal isOpen={showCreate} onClose={() => setShowCreate(false)} />
    </div>
  )
}

function CreateMedicationModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({ name: '', generic_name: '', form: 'tablet', strength: '', manufacturer: '', description: '' })
  const [imageFile, setImageFile] = useState<File | null>(null)

  const createMut = useMutation({
    mutationFn: () => {
      const fd = new FormData()
      Object.entries(form).forEach(([k, v]) => fd.append(k, v))
      if (imageFile) fd.append('image', imageFile)
      return prescriptionsService.createMedication(fd)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['medications'] })
      toast.success('Medication added')
      onClose()
      setForm({ name: '', generic_name: '', form: 'tablet', strength: '', manufacturer: '', description: '' })
      setImageFile(null)
    },
    onError: (e: any) => toast.error(e?.response?.data?.error?.message || 'Failed to add medication'),
  })

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name || !form.generic_name || !form.strength) return toast.error('Name, generic name and strength are required')
    createMut.mutate()
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} className="relative bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 rounded-t-2xl flex items-center justify-between z-10">
              <h2 className="text-lg font-semibold">Add Medication</h2>
              <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg"><X className="w-4 h-4" /></button>
            </div>
            <form onSubmit={submit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                  <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className="input-field" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Generic Name *</label>
                  <input value={form.generic_name} onChange={e => setForm(f => ({ ...f, generic_name: e.target.value }))} className="input-field" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Form</label>
                  <select value={form.form} onChange={e => setForm(f => ({ ...f, form: e.target.value }))} className="input-field capitalize">
                    {FORMS.map(fm => <option key={fm} value={fm}>{fm}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Strength *</label>
                  <input value={form.strength} onChange={e => setForm(f => ({ ...f, strength: e.target.value }))} placeholder="e.g. 500mg" className="input-field" />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Manufacturer</label>
                  <input value={form.manufacturer} onChange={e => setForm(f => ({ ...f, manufacturer: e.target.value }))} className="input-field" />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} rows={2} className="input-field" />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Image</label>
                  <input type="file" accept="image/*" onChange={e => setImageFile(e.target.files?.[0] || null)} className="text-sm" />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t">
                <button type="button" onClick={onClose} className="btn-ghost">Cancel</button>
                <button type="submit" disabled={createMut.isPending} className="btn-primary">{createMut.isPending ? 'Saving...' : 'Add Medication'}</button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
