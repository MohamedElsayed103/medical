import { useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Pill, ImageIcon, Upload, Edit2, AlertTriangle, Thermometer, Info } from 'lucide-react'
import toast from 'react-hot-toast'
import { prescriptionsService } from '@/services/api'

const FORMS = ['tablet', 'capsule', 'syrup', 'injection', 'cream', 'drops', 'inhaler']

export default function MedicationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState<any>(null)

  const { data: med, isLoading } = useQuery({
    queryKey: ['medication', id],
    queryFn: () => prescriptionsService.getMedicationById(id!),
    enabled: !!id,
  })

  const updateMut = useMutation({
    mutationFn: (data: FormData | Record<string, any>) => prescriptionsService.updateMedication(id!, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['medication', id] })
      qc.invalidateQueries({ queryKey: ['medications'] })
      toast.success('Medication updated')
      setEditing(false)
    },
    onError: (e: any) => toast.error(e?.response?.data?.error?.message || 'Update failed'),
  })

  if (isLoading) return (
    <div className="p-6 space-y-4">
      {[...Array(3)].map((_, i) => <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />)}
    </div>
  )
  if (!med) return <div className="p-6 text-center text-gray-500">Medication not found.</div>

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const fd = new FormData()
    fd.append('image', file)
    updateMut.mutate(fd)
  }

  const startEdit = () => {
    setForm({
      name: med.name, generic_name: med.generic_name, form: med.form, strength: med.strength,
      manufacturer: med.manufacturer || '', description: med.description || '',
      side_effects: med.side_effects || '', contraindications: med.contraindications || '',
      storage_instructions: med.storage_instructions || '',
    })
    setEditing(true)
  }

  const saveEdit = () => updateMut.mutate(form)

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-start gap-4">
        <Link to="/medications" className="p-2 hover:bg-gray-100 rounded-lg mt-1"><ArrowLeft className="w-4 h-4" /></Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Pill className="w-6 h-6 text-purple-600" /> {med.name}
          </h1>
          <p className="text-gray-500 text-sm mt-1 capitalize">{med.generic_name} • {med.form} • {med.strength}</p>
        </div>
        {!editing && (
          <button onClick={startEdit} className="btn-ghost border border-gray-200 flex items-center gap-2 text-sm">
            <Edit2 className="w-4 h-4" /> Edit
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Image */}
        <div className="md:col-span-1">
          <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
            <div className="aspect-square bg-gray-50 flex items-center justify-center overflow-hidden">
              {med.image_url ? (
                <img src={med.image_url} alt={med.name} className="w-full h-full object-cover" />
              ) : (
                <ImageIcon className="w-16 h-16 text-gray-300" />
              )}
            </div>
            <div className="p-3">
              <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleImageUpload} />
              <button onClick={() => fileRef.current?.click()} disabled={updateMut.isPending}
                className="w-full btn-ghost border border-gray-200 flex items-center justify-center gap-2 text-sm">
                <Upload className="w-4 h-4" /> {med.image_url ? 'Replace Image' : 'Upload Image'}
              </button>
            </div>
          </div>
        </div>

        {/* Details */}
        <div className="md:col-span-2 space-y-4">
          {editing ? (
            <div className="bg-white rounded-2xl shadow-soft border border-gray-100 p-5 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <Field label="Name"><input value={form.name} onChange={e => setForm((f: any) => ({ ...f, name: e.target.value }))} className="input-field" /></Field>
                <Field label="Generic Name"><input value={form.generic_name} onChange={e => setForm((f: any) => ({ ...f, generic_name: e.target.value }))} className="input-field" /></Field>
                <Field label="Form">
                  <select value={form.form} onChange={e => setForm((f: any) => ({ ...f, form: e.target.value }))} className="input-field capitalize">
                    {FORMS.map(fm => <option key={fm} value={fm}>{fm}</option>)}
                  </select>
                </Field>
                <Field label="Strength"><input value={form.strength} onChange={e => setForm((f: any) => ({ ...f, strength: e.target.value }))} className="input-field" /></Field>
                <div className="col-span-2"><Field label="Manufacturer"><input value={form.manufacturer} onChange={e => setForm((f: any) => ({ ...f, manufacturer: e.target.value }))} className="input-field" /></Field></div>
                <div className="col-span-2"><Field label="Description"><textarea value={form.description} onChange={e => setForm((f: any) => ({ ...f, description: e.target.value }))} rows={2} className="input-field" /></Field></div>
                <div className="col-span-2"><Field label="Side Effects"><textarea value={form.side_effects} onChange={e => setForm((f: any) => ({ ...f, side_effects: e.target.value }))} rows={2} className="input-field" /></Field></div>
                <div className="col-span-2"><Field label="Contraindications"><textarea value={form.contraindications} onChange={e => setForm((f: any) => ({ ...f, contraindications: e.target.value }))} rows={2} className="input-field" /></Field></div>
                <div className="col-span-2"><Field label="Storage Instructions"><input value={form.storage_instructions} onChange={e => setForm((f: any) => ({ ...f, storage_instructions: e.target.value }))} className="input-field" /></Field></div>
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t">
                <button onClick={() => setEditing(false)} className="btn-ghost">Cancel</button>
                <button onClick={saveEdit} disabled={updateMut.isPending} className="btn-primary">{updateMut.isPending ? 'Saving...' : 'Save Changes'}</button>
              </div>
            </div>
          ) : (
            <>
              <div className="bg-white rounded-2xl shadow-soft border border-gray-100 p-5">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <Meta label="Form" value={med.form} capitalize />
                  <Meta label="Strength" value={med.strength} />
                  <Meta label="Generic Name" value={med.generic_name} />
                  <Meta label="Manufacturer" value={med.manufacturer || '—'} />
                </div>
              </div>
              {med.description && <InfoCard icon={<Info className="w-4 h-4 text-blue-500" />} title="Description" text={med.description} />}
              {med.side_effects && <InfoCard icon={<AlertTriangle className="w-4 h-4 text-amber-500" />} title="Side Effects" text={med.side_effects} />}
              {med.contraindications && <InfoCard icon={<AlertTriangle className="w-4 h-4 text-red-500" />} title="Contraindications" text={med.contraindications} />}
              {med.storage_instructions && <InfoCard icon={<Thermometer className="w-4 h-4 text-cyan-500" />} title="Storage" text={med.storage_instructions} />}
              {!med.description && !med.side_effects && !med.contraindications && !med.storage_instructions && (
                <div className="bg-white rounded-2xl border border-gray-100 p-5 text-sm text-gray-400">
                  No clinical details recorded yet. Click <span className="font-medium">Edit</span> to add a description, side effects, contraindications and storage instructions.
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
      {children}
    </div>
  )
}

function Meta({ label, value, capitalize }: { label: string; value: string; capitalize?: boolean }) {
  return (
    <div>
      <p className="text-xs text-gray-500 uppercase font-medium mb-0.5">{label}</p>
      <p className={`font-medium text-gray-900 ${capitalize ? 'capitalize' : ''}`}>{value}</p>
    </div>
  )
}

function InfoCard({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return (
    <div className="bg-white rounded-2xl shadow-soft border border-gray-100 p-5">
      <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">{icon} {title}</h3>
      <p className="text-sm text-gray-700 whitespace-pre-line">{text}</p>
    </div>
  )
}
