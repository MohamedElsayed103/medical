import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Plus, Search, FileText, CheckCircle } from 'lucide-react'
import { safeFormat } from '@/lib/utils'
import { useVisits } from '@/hooks/useVisits'
import CreateVisitModal from './CreateVisitModal'

export default function VisitsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [showCreateModal, setShowCreateModal] = useState(searchParams.get('new') === '1')

  const params: Record<string, string | number> = { page, page_size: 15, ordering: '-visit_date' }
  if (search) params.search = search

  const { data, isLoading } = useVisits(params)

  useEffect(() => {
    if (searchParams.get('new') === '1') {
      setShowCreateModal(true)
      setSearchParams({})
    }
  }, [searchParams, setSearchParams])

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Medical Records</h1>
          <p className="text-gray-500 text-sm mt-1">{data?.count ?? 0} visit records</p>
        </div>
        <button onClick={() => setShowCreateModal(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Visit
        </button>
      </div>

      <div className="relative">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          placeholder="Search by patient, doctor, complaint..."
          className="input-field pl-10"
        />
      </div>

      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="p-8 space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse flex gap-4 py-3">
                <div className="w-10 h-10 rounded-lg bg-gray-200" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-1/3" />
                  <div className="h-3 bg-gray-100 rounded w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : data?.results?.length ? (
          <div className="divide-y divide-gray-50">
            {data.results.map((visit) => (
              <Link
                key={visit.id}
                to={`/visits/${visit.id}`}
                className="flex items-center gap-4 p-5 hover:bg-gray-50/50 transition-colors"
              >
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${visit.is_signed ? 'bg-green-50' : 'bg-primary-50'}`}>
                  {visit.is_signed ? <CheckCircle className="w-5 h-5 text-green-600" /> : <FileText className="w-5 h-5 text-primary-600" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900">{visit.chief_complaint}</p>
                  <p className="text-sm text-gray-500">
                    {visit.patient_name} • Dr. {visit.doctor_name} • {safeFormat(visit.visit_date, 'MMM d, yyyy')}
                  </p>
                  {visit.assessment && (
                    <p className="text-xs text-gray-400 mt-0.5 truncate">{visit.assessment}</p>
                  )}
                </div>
                <div className="text-right">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${visit.is_signed ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                    {visit.is_signed ? 'Signed' : 'Draft'}
                  </span>
                  {visit.diagnoses?.length > 0 && (
                    <p className="text-xs text-gray-400 mt-1">{visit.diagnoses.length} diagnosis</p>
                  )}
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No visit records found</p>
          </div>
        )}

        {data && data.count > 15 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100">
            <p className="text-sm text-gray-500">Page {page}</p>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={!data.previous} className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-50">Previous</button>
              <button onClick={() => setPage(p => p + 1)} disabled={!data.next} className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-50">Next</button>
            </div>
          </div>
        )}
      </div>

      <CreateVisitModal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} />
    </div>
  )
}
