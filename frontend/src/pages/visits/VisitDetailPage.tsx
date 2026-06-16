import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { ArrowLeft, CheckCircle, Plus, Heart, Thermometer, Activity, Pill, FlaskConical, ScanLine } from 'lucide-react'
import { safeFormat } from '@/lib/utils'
import { useVisit, useSignVisit, useAddVitals, useAddDiagnosis } from '@/hooks/useVisits'
import { visitsService } from '@/services/api'
import StatusChip from '@/components/ui/StatusChip'
import { useForm } from 'react-hook-form'
import type { VitalsCreateRequest, DiagnosisCreateRequest } from '@/types'

export default function VisitDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: visit, isLoading } = useVisit(id!)
  const signVisit = useSignVisit()
  const addVitals = useAddVitals()
  const addDiagnosis = useAddDiagnosis()
  const [showVitalsForm, setShowVitalsForm] = useState(false)
  const [showDiagnosisForm, setShowDiagnosisForm] = useState(false)

  const vitalsForm = useForm<VitalsCreateRequest>()
  const diagnosisForm = useForm<DiagnosisCreateRequest>()
  const { data: related } = useQuery({
    queryKey: ['visit-related', id],
    queryFn: () => visitsService.getRelated(id!),
    enabled: !!id,
  })

  if (isLoading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-3 border-primary-200 border-t-primary-600 rounded-full animate-spin" /></div>
  if (!visit) return <div className="text-center py-16"><p className="text-gray-500">Visit not found</p></div>

  const handleSignVisit = () => {
    if (confirm('Sign and finalize this visit? This action cannot be undone.')) {
      signVisit.mutate(visit.id)
    }
  }

  const handleAddVitals = async (data: VitalsCreateRequest) => {
    await addVitals.mutateAsync({ visitId: visit.id, data })
    vitalsForm.reset()
    setShowVitalsForm(false)
  }

  const handleAddDiagnosis = async (data: DiagnosisCreateRequest) => {
    await addDiagnosis.mutateAsync({ visitId: visit.id, data })
    diagnosisForm.reset()
    setShowDiagnosisForm(false)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/visits" className="p-2 hover:bg-gray-100 rounded-lg"><ArrowLeft className="w-5 h-5" /></Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">{visit.chief_complaint}</h1>
          <p className="text-sm text-gray-500">
            {visit.patient_name} • Dr. {visit.doctor_name} • {safeFormat(visit.visit_date, 'MMM d, yyyy h:mm a')}
          </p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${visit.is_signed ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
          {visit.is_signed ? '✓ Signed' : 'Draft'}
        </span>
        {!visit.is_signed && (
          <button onClick={handleSignVisit} className="btn-primary flex items-center gap-2">
            <CheckCircle className="w-4 h-4" /> Sign & Finalize
          </button>
        )}
      </div>

      {/* Clinical Notes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl shadow-soft border border-gray-100 p-6 space-y-4">
          <h3 className="font-semibold text-gray-900">Clinical Notes</h3>
          {visit.history_of_present_illness && (
            <div><p className="text-xs font-semibold text-gray-500 uppercase mb-1">History of Present Illness</p><p className="text-sm text-gray-700 whitespace-pre-wrap">{visit.history_of_present_illness}</p></div>
          )}
          {visit.examination_notes && (
            <div><p className="text-xs font-semibold text-gray-500 uppercase mb-1">Examination</p><p className="text-sm text-gray-700 whitespace-pre-wrap">{visit.examination_notes}</p></div>
          )}
          {visit.assessment && (
            <div><p className="text-xs font-semibold text-gray-500 uppercase mb-1">Assessment</p><p className="text-sm text-gray-700 whitespace-pre-wrap">{visit.assessment}</p></div>
          )}
          {visit.plan && (
            <div><p className="text-xs font-semibold text-gray-500 uppercase mb-1">Plan</p><p className="text-sm text-gray-700 whitespace-pre-wrap">{visit.plan}</p></div>
          )}
          {visit.follow_up_date && (
            <div className="pt-3 border-t"><p className="text-sm"><span className="font-medium">Follow-up:</span> {safeFormat(visit.follow_up_date, 'MMM d, yyyy')}</p></div>
          )}
        </motion.div>

        {/* Vitals */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-white rounded-2xl shadow-soft border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Vitals</h3>
            {!visit.is_signed && (
              <button onClick={() => setShowVitalsForm(!showVitalsForm)} className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
                <Plus className="w-3 h-3" /> Add Vitals
              </button>
            )}
          </div>

          {visit.vitals?.length > 0 ? (
            <div className="grid grid-cols-2 gap-3">
              {visit.vitals.map((v, i) => (
                <div key={i} className="space-y-2">
                  <div className="flex items-center gap-2 p-2 bg-red-50 rounded-lg"><Heart className="w-4 h-4 text-red-500" /><span className="text-sm">{v.blood_pressure_systolic}/{v.blood_pressure_diastolic} mmHg</span></div>
                  <div className="flex items-center gap-2 p-2 bg-pink-50 rounded-lg"><Activity className="w-4 h-4 text-pink-500" /><span className="text-sm">{v.heart_rate} bpm</span></div>
                  <div className="flex items-center gap-2 p-2 bg-orange-50 rounded-lg"><Thermometer className="w-4 h-4 text-orange-500" /><span className="text-sm">{v.temperature}°C</span></div>
                  <div className="text-xs text-gray-500 space-y-1">
                    <p>RR: {v.respiratory_rate}/min • SpO2: {v.oxygen_saturation}%</p>
                    <p>Weight: {v.weight_kg}kg • Height: {v.height_cm}cm</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400">No vitals recorded</p>
          )}

          {showVitalsForm && (
            <form onSubmit={vitalsForm.handleSubmit(handleAddVitals)} className="mt-4 pt-4 border-t space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <input type="number" placeholder="Systolic" {...vitalsForm.register('blood_pressure_systolic', { valueAsNumber: true })} className="input-field text-sm" />
                <input type="number" placeholder="Diastolic" {...vitalsForm.register('blood_pressure_diastolic', { valueAsNumber: true })} className="input-field text-sm" />
                <input type="number" placeholder="Heart Rate" {...vitalsForm.register('heart_rate', { valueAsNumber: true })} className="input-field text-sm" />
                <input type="number" step="0.1" placeholder="Temperature" {...vitalsForm.register('temperature', { valueAsNumber: true })} className="input-field text-sm" />
                <input type="number" placeholder="Resp Rate" {...vitalsForm.register('respiratory_rate', { valueAsNumber: true })} className="input-field text-sm" />
                <input type="number" placeholder="SpO2 %" {...vitalsForm.register('oxygen_saturation', { valueAsNumber: true })} className="input-field text-sm" />
                <input type="text" placeholder="Weight (kg)" {...vitalsForm.register('weight_kg')} className="input-field text-sm" />
                <input type="text" placeholder="Height (cm)" {...vitalsForm.register('height_cm')} className="input-field text-sm" />
              </div>
              <button type="submit" className="btn-primary text-sm w-full">Save Vitals</button>
            </form>
          )}
        </motion.div>
      </div>

      {/* Diagnoses */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="bg-white rounded-2xl shadow-soft border border-gray-100 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">Diagnoses</h3>
          {!visit.is_signed && (
            <button onClick={() => setShowDiagnosisForm(!showDiagnosisForm)} className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
              <Plus className="w-3 h-3" /> Add Diagnosis
            </button>
          )}
        </div>

        {visit.diagnoses?.length > 0 ? (
          <div className="space-y-2">
            {visit.diagnoses.map((dx) => (
              <div key={dx.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-mono">{dx.icd_code}</span>
                <span className="text-sm font-medium text-gray-900">{dx.description}</span>
                <span className="text-xs text-gray-500 capitalize">{dx.type}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">No diagnoses recorded</p>
        )}

        {showDiagnosisForm && (
          <form onSubmit={diagnosisForm.handleSubmit(handleAddDiagnosis)} className="mt-4 pt-4 border-t space-y-3">
            <div className="grid grid-cols-3 gap-3">
              <input placeholder="ICD Code (e.g., J06.9)" {...diagnosisForm.register('icd_code')} className="input-field text-sm" />
              <input placeholder="Description" {...diagnosisForm.register('description')} className="input-field text-sm col-span-2" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <select {...diagnosisForm.register('type')} className="input-field text-sm">
                <option value="primary">Primary</option>
                <option value="secondary">Secondary</option>
                <option value="differential">Differential</option>
              </select>
              <input placeholder="Notes (optional)" {...diagnosisForm.register('notes')} className="input-field text-sm" />
            </div>
            <button type="submit" className="btn-primary text-sm">Add Diagnosis</button>
          </form>
        )}
      </motion.div>

      {/* Linked orders */}
      {related && (related.prescriptions.length + related.lab_orders.length + related.radiology_orders.length) > 0 && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="bg-white rounded-2xl shadow-soft border border-gray-100 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Orders from this Visit</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <LinkedGroup title="Prescriptions" icon={<Pill className="w-4 h-4 text-purple-500" />} items={related.prescriptions} />
            <LinkedGroup title="Lab Orders" icon={<FlaskConical className="w-4 h-4 text-amber-500" />} items={related.lab_orders} />
            <LinkedGroup title="Radiology" icon={<ScanLine className="w-4 h-4 text-cyan-500" />} items={related.radiology_orders} />
          </div>
        </motion.div>
      )}
    </div>
  )
}

function LinkedGroup({ title, icon, items }: { title: string; icon: React.ReactNode; items: { id: string; label: string; status: string; link: string }[] }) {
  return (
    <div>
      <p className="text-xs font-semibold text-gray-500 uppercase mb-2 flex items-center gap-1.5">{icon} {title}</p>
      {items.length ? (
        <div className="space-y-1.5">
          {items.map(it => (
            <Link key={it.id} to={it.link} className="flex items-center justify-between gap-2 px-3 py-2 bg-gray-50 rounded-lg hover:bg-gray-100">
              <span className="text-sm text-gray-800 truncate">{it.label}</span>
              <StatusChip status={it.status} />
            </Link>
          ))}
        </div>
      ) : <p className="text-sm text-gray-400">None</p>}
    </div>
  )
}
