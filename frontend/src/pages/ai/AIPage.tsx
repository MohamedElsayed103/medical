import { useState } from 'react'
import { motion } from 'framer-motion'
import { format } from 'date-fns'
import { Brain, Send, Sparkles, Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { aiService } from '@/services/api'
import { usePatients } from '@/hooks/usePatients'
import toast from 'react-hot-toast'

export default function AIPage() {
  const queryClient = useQueryClient()
  const [requestType, setRequestType] = useState('symptom_analysis')
  const [inputText, setInputText] = useState('')
  const [patientId, setPatientId] = useState('')
  const [patientSearch, setPatientSearch] = useState('')

  const { data: requests, isLoading } = useQuery({
    queryKey: ['ai-requests'],
    queryFn: () => aiService.getAll({ page_size: 20, ordering: '-created_at' }),
  })

  const { data: patients } = usePatients(patientSearch ? { search: patientSearch, page_size: 5 } : { page_size: 5 })

  const createRequest = useMutation({
    mutationFn: () => aiService.create({
      request_type: requestType,
      input_data: { text: inputText, type: requestType },
      patient_id: patientId || undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-requests'] })
      toast.success('AI request submitted')
      setInputText('')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to submit request')
    },
  })

  const requestTypes = [
    { value: 'symptom_analysis', label: 'Symptom Analysis', description: 'Analyze patient symptoms and suggest possible conditions' },
    { value: 'drug_interaction', label: 'Drug Interaction Check', description: 'Check for potential drug interactions' },
    { value: 'treatment_suggestion', label: 'Treatment Suggestion', description: 'AI-powered treatment recommendations' },
    { value: 'medical_summary', label: 'Medical Summary', description: 'Generate a summary of patient records' },
    { value: 'differential_diagnosis', label: 'Differential Diagnosis', description: 'Suggest differential diagnoses based on symptoms' },
    { value: 'lab_interpretation', label: 'Lab Result Interpretation', description: 'Interpret lab results in clinical context' },
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'processing': return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
      case 'failed': return <XCircle className="w-4 h-4 text-red-500" />
      default: return <Clock className="w-4 h-4 text-yellow-500" />
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Brain className="w-7 h-7 text-purple-600" /> AI Assistant
        </h1>
        <p className="text-gray-500 text-sm mt-1">AI-powered medical insights and analysis</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Panel */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white rounded-2xl shadow-soft border border-gray-100 p-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-500" /> New Request
            </h3>

            {/* Request Type */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
              <div className="space-y-2">
                {requestTypes.map(type => (
                  <label
                    key={type.value}
                    className={`flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                      requestType === type.value ? 'bg-purple-50 border border-purple-200' : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                  >
                    <input
                      type="radio"
                      name="requestType"
                      value={type.value}
                      checked={requestType === type.value}
                      onChange={(e) => setRequestType(e.target.value)}
                      className="mt-1"
                    />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{type.label}</p>
                      <p className="text-xs text-gray-500">{type.description}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Patient (optional) */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Patient (optional)</label>
              <input
                type="text"
                value={patientSearch}
                onChange={(e) => setPatientSearch(e.target.value)}
                placeholder="Search patient..."
                className="input-field text-sm mb-1"
              />
              {patients?.results?.length ? (
                <div className="max-h-24 overflow-y-auto border rounded-lg divide-y">
                  {patients.results.map(p => (
                    <button key={p.id} type="button" onClick={() => { setPatientId(p.id); setPatientSearch(p.first_name + ' ' + p.last_name) }}
                      className={`w-full text-left px-3 py-1.5 text-xs hover:bg-gray-50 ${patientId === p.id ? 'bg-purple-50' : ''}`}
                    >{p.first_name} {p.last_name}</button>
                  ))}
                </div>
              ) : null}
            </div>

            {/* Input */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Describe the case / query</label>
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                className="input-field"
                rows={5}
                placeholder="Enter symptoms, medications, or clinical question..."
              />
            </div>

            <button
              onClick={() => createRequest.mutate()}
              disabled={!inputText || createRequest.isPending}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {createRequest.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              {createRequest.isPending ? 'Processing...' : 'Submit to AI'}
            </button>
          </div>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-2xl shadow-soft border border-gray-100 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Recent Requests</h3>

            {isLoading ? (
              <div className="space-y-4">{[...Array(3)].map((_, i) => <div key={i} className="animate-pulse h-24 bg-gray-100 rounded-xl" />)}</div>
            ) : requests?.results?.length ? (
              <div className="space-y-4 max-h-[600px] overflow-y-auto">
                {requests.results.map(req => (
                  <motion.div
                    key={req.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-4 rounded-xl border border-gray-100 hover:border-purple-200 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(req.status)}
                        <span className="text-sm font-medium text-gray-900 capitalize">{req.request_type?.replace('_', ' ')}</span>
                      </div>
                      <span className="text-xs text-gray-400">{format(new Date(req.created_at), 'MMM d, h:mm a')}</span>
                    </div>

                    {/* Input */}
                    <div className="text-sm text-gray-600 mb-2 bg-gray-50 p-2 rounded">
                      <p className="font-medium text-xs text-gray-500 mb-1">Input:</p>
                      <p className="truncate">{typeof req.input_data === 'object' ? (req.input_data as any)?.text || JSON.stringify(req.input_data) : String(req.input_data)}</p>
                    </div>

                    {/* Output */}
                    {req.output_data && (
                      <div className="text-sm bg-purple-50 p-3 rounded-lg border border-purple-100">
                        <p className="font-medium text-xs text-purple-700 mb-1">AI Response:</p>
                        <p className="text-gray-800 whitespace-pre-wrap text-sm">
                          {typeof req.output_data === 'object'
                            ? (req.output_data as any)?.response || (req.output_data as any)?.text || JSON.stringify(req.output_data, null, 2)
                            : String(req.output_data)}
                        </p>
                      </div>
                    )}

                    {req.error_message && (
                      <p className="text-sm text-red-600 mt-2">Error: {req.error_message}</p>
                    )}

                    {/* Metadata */}
                    {(req.model_name || req.latency_ms) && (
                      <div className="flex gap-3 mt-2 text-xs text-gray-400">
                        {req.model_name && <span>Model: {req.model_name}</span>}
                        {req.latency_ms && <span>{req.latency_ms}ms</span>}
                        {req.total_tokens && <span>{req.total_tokens} tokens</span>}
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Brain className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No AI requests yet</p>
                <p className="text-sm text-gray-400">Submit your first query to get AI-powered insights</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
