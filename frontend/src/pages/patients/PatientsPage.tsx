import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Search, Users, Phone, Mail } from 'lucide-react'
import { usePatients } from '@/hooks/usePatients'
import { safeFormat } from '@/lib/utils'
import PatientFormModal from './PatientFormModal'

export default function PatientsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [page, setPage] = useState(1)
  const [showCreateModal, setShowCreateModal] = useState(searchParams.get('new') === '1')
  const [statusFilter, setStatusFilter] = useState<string>('')

  const params: Record<string, string | number> = { page, page_size: 15 }
  if (search) params.search = search
  if (statusFilter) params.is_active = statusFilter

  const { data, isLoading } = usePatients(params)

  useEffect(() => {
    if (searchParams.get('new') === '1') {
      setShowCreateModal(true)
      setSearchParams({})
    }
  }, [searchParams, setSearchParams])

  const handleSearch = (value: string) => {
    setSearch(value)
    setPage(1)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Patients</h1>
          <p className="text-gray-500 text-sm mt-1">
            {data?.count !== undefined ? `${data.count} patients registered` : 'Manage patient records'}
          </p>
        </div>
        <button onClick={() => setShowCreateModal(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Patient
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search by name, phone, MRN..."
            className="input-field pl-10"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
          className="input-field w-auto"
        >
          <option value="">All Status</option>
          <option value="true">Active</option>
          <option value="false">Inactive</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="p-8">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse flex items-center gap-4 py-4 border-b border-gray-50">
                <div className="w-10 h-10 rounded-full bg-gray-200" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-1/3" />
                  <div className="h-3 bg-gray-100 rounded w-1/4" />
                </div>
              </div>
            ))}
          </div>
        ) : data?.results?.length ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100">
                  <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Patient</th>
                  <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">MRN</th>
                  <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Contact</th>
                  <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Gender</th>
                  <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">DOB</th>
                  <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Status</th>
                  <th className="text-right px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody>
                <AnimatePresence>
                  {data.results.map((patient) => (
                    <motion.tr
                      key={patient.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors"
                    >
                      <td className="px-6 py-4">
                        <Link to={`/patients/${patient.id}`} className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center text-sm font-semibold text-primary-700">
                            {patient.first_name?.[0]}{patient.last_name?.[0]}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900 hover:text-primary-600">
                              {patient.first_name} {patient.last_name}
                            </p>
                            {patient.blood_type && (
                              <span className="text-xs text-gray-500">Blood: {patient.blood_type}</span>
                            )}
                          </div>
                        </Link>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600 font-mono">
                        {patient.medical_record_number || '—'}
                      </td>
                      <td className="px-6 py-4">
                        <div className="space-y-1">
                          {patient.phone && (
                            <div className="flex items-center gap-1 text-sm text-gray-600">
                              <Phone className="w-3 h-3" /> {patient.phone}
                            </div>
                          )}
                          {patient.email && (
                            <div className="flex items-center gap-1 text-sm text-gray-600">
                              <Mail className="w-3 h-3" /> {patient.email}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600 capitalize">{patient.gender || '—'}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {safeFormat(patient.date_of_birth, 'MMM d, yyyy')}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          patient.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {patient.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link
                          to={`/patients/${patient.id}`}
                          className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                        >
                          View
                        </Link>
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-16">
            <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <h3 className="text-lg font-medium text-gray-700 mb-1">No patients found</h3>
            <p className="text-gray-500 text-sm mb-4">
              {search ? 'Try a different search term' : 'Get started by adding your first patient'}
            </p>
            {!search && (
              <button onClick={() => setShowCreateModal(true)} className="btn-primary">
                <Plus className="w-4 h-4 mr-2" /> Add First Patient
              </button>
            )}
          </div>
        )}

        {/* Pagination */}
        {data && data.count > 15 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100">
            <p className="text-sm text-gray-500">
              Showing {(page - 1) * 15 + 1}–{Math.min(page * 15, data.count)} of {data.count}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={!data.previous}
                className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-50 hover:bg-gray-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={!data.next}
                className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-50 hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create Modal */}
      <PatientFormModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
      />
    </div>
  )
}
