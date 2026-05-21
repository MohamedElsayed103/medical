import { useState } from 'react'
import { motion } from 'framer-motion'
import { format } from 'date-fns'
import { Shield, Plus, Search, Building2, FileCheck, Users, CheckCircle, XCircle } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { insuranceService } from '@/services/api'
import { usePatients } from '@/hooks/usePatients'
import toast from 'react-hot-toast'

type Tab = 'providers' | 'policies' | 'claims'

export default function InsurancePage() {
  const [tab, setTab] = useState<Tab>('providers')
  const [search, setSearch] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Shield className="w-7 h-7 text-indigo-600" /> Insurance
          </h1>
          <p className="text-gray-500 text-sm mt-1">Manage providers, policies, and claims</p>
        </div>
        <button onClick={() => setShowCreateModal(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Add {tab === 'providers' ? 'Provider' : tab === 'policies' ? 'Policy' : 'Claim'}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1">
        {([
          { key: 'providers', label: 'Providers', icon: Building2 },
          { key: 'policies', label: 'Policies', icon: Users },
          { key: 'claims', label: 'Claims', icon: FileCheck },
        ] as const).map(t => (
          <button key={t.key} onClick={() => { setTab(t.key); setSearch('') }}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              tab === t.key ? 'bg-white shadow text-indigo-600' : 'text-gray-600 hover:text-gray-800'
            }`}>
            <t.icon className="w-4 h-4" /> {t.label}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input type="text" placeholder={`Search ${tab}...`} value={search} onChange={e => setSearch(e.target.value)} className="input-field pl-9" />
      </div>

      {/* Tab Content */}
      {tab === 'providers' && <ProvidersTab search={search} showCreate={showCreateModal} setShowCreate={setShowCreateModal} />}
      {tab === 'policies' && <PoliciesTab search={search} showCreate={showCreateModal} setShowCreate={setShowCreateModal} />}
      {tab === 'claims' && <ClaimsTab search={search} showCreate={showCreateModal} setShowCreate={setShowCreateModal} />}
    </div>
  )
}

function ProvidersTab({ search, showCreate, setShowCreate }: { search: string; showCreate: boolean; setShowCreate: (v: boolean) => void }) {
  const queryClient = useQueryClient()
  const params: Record<string, any> = { page_size: 20 }
  if (search) params.search = search

  const { data, isLoading } = useQuery({
    queryKey: ['insurance-providers', params],
    queryFn: () => insuranceService.getProviders(params),
  })

  const createProvider = useMutation({
    mutationFn: (d: any) => insuranceService.createProvider(d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['insurance-providers'] }); toast.success('Provider added'); setShowCreate(false) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed'),
  })

  return (
    <>
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="p-8 space-y-3">{[...Array(4)].map((_, i) => <div key={i} className="h-16 bg-gray-100 rounded animate-pulse" />)}</div>
        ) : !data?.results?.length ? (
          <div className="text-center py-12"><Building2 className="w-12 h-12 text-gray-300 mx-auto mb-3" /><p className="text-gray-500">No providers found</p></div>
        ) : (
          <div className="divide-y">
            {data.results.map((p: any) => (
              <motion.div key={p.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-4 hover:bg-gray-50 flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">{p.name}</p>
                  <p className="text-sm text-gray-500">{p.contact_email} • {p.phone}</p>
                </div>
                <div className="text-right">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${p.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {p.is_active ? 'Active' : 'Inactive'}
                  </span>
                  <p className="text-xs text-gray-400 mt-1">{p.provider_type || 'Standard'}</p>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-2xl p-6 w-full max-w-lg mx-4">
            <h2 className="text-lg font-bold mb-4">Add Insurance Provider</h2>
            <form onSubmit={(e) => { e.preventDefault(); const fd = new FormData(e.currentTarget); createProvider.mutate({ name: fd.get('name'), contact_email: fd.get('email'), phone: fd.get('phone'), address: fd.get('address'), provider_type: fd.get('type') }) }} className="space-y-3">
              <div><label className="text-xs font-medium text-gray-600">Name *</label><input name="name" required className="input-field" /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="text-xs font-medium text-gray-600">Email</label><input name="email" type="email" className="input-field" /></div>
                <div><label className="text-xs font-medium text-gray-600">Phone</label><input name="phone" className="input-field" /></div>
              </div>
              <div><label className="text-xs font-medium text-gray-600">Address</label><input name="address" className="input-field" /></div>
              <div><label className="text-xs font-medium text-gray-600">Type</label><select name="type" className="input-field"><option value="health">Health</option><option value="dental">Dental</option><option value="vision">Vision</option><option value="life">Life</option></select></div>
              <div className="flex justify-end gap-3 pt-3">
                <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
                <button type="submit" disabled={createProvider.isPending} className="btn-primary">{createProvider.isPending ? 'Adding...' : 'Add Provider'}</button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </>
  )
}

function PoliciesTab({ search, showCreate, setShowCreate }: { search: string; showCreate: boolean; setShowCreate: (v: boolean) => void }) {
  const queryClient = useQueryClient()
  const params: Record<string, any> = { page_size: 20 }
  if (search) params.search = search

  const { data, isLoading } = useQuery({
    queryKey: ['insurance-policies', params],
    queryFn: () => insuranceService.getPolicies(params),
  })

  const { data: patients } = usePatients({ page_size: 50 })
  const { data: providers } = useQuery({ queryKey: ['insurance-providers', {}], queryFn: () => insuranceService.getProviders({}) })

  const createPolicy = useMutation({
    mutationFn: (d: any) => insuranceService.createPolicy(d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['insurance-policies'] }); toast.success('Policy created'); setShowCreate(false) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed'),
  })

  return (
    <>
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="p-8 space-y-3">{[...Array(4)].map((_, i) => <div key={i} className="h-16 bg-gray-100 rounded animate-pulse" />)}</div>
        ) : !data?.results?.length ? (
          <div className="text-center py-12"><Users className="w-12 h-12 text-gray-300 mx-auto mb-3" /><p className="text-gray-500">No policies found</p></div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b"><tr>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Policy #</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Patient</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Provider</th>
              <th className="text-center px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Coverage</th>
              <th className="text-center px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Valid Until</th>
              <th className="text-center px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Status</th>
            </tr></thead>
            <tbody className="divide-y">{data.results.map((p: any) => (
              <tr key={p.id} className="hover:bg-gray-50">
                <td className="px-5 py-3 font-mono text-sm">{p.policy_number}</td>
                <td className="px-5 py-3 text-sm">{p.patient_name || '-'}</td>
                <td className="px-5 py-3 text-sm">{p.provider_name || '-'}</td>
                <td className="px-5 py-3 text-center text-sm">${Number(p.coverage_amount || 0).toLocaleString()}</td>
                <td className="px-5 py-3 text-center text-sm">{p.end_date ? format(new Date(p.end_date), 'MMM d, yyyy') : '-'}</td>
                <td className="px-5 py-3 text-center">
                  <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${p.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>{p.status}</span>
                </td>
              </tr>
            ))}</tbody>
          </table>
        )}
      </div>

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-2xl p-6 w-full max-w-lg mx-4">
            <h2 className="text-lg font-bold mb-4">Create Policy</h2>
            <form onSubmit={(e) => { e.preventDefault(); const fd = new FormData(e.currentTarget); createPolicy.mutate({ patient: fd.get('patient'), provider: fd.get('provider'), policy_number: fd.get('policy_number'), coverage_amount: fd.get('coverage_amount'), start_date: fd.get('start_date'), end_date: fd.get('end_date') }) }} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div><label className="text-xs font-medium text-gray-600">Patient *</label><select name="patient" required className="input-field">{patients?.results?.map(p => <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>)}</select></div>
                <div><label className="text-xs font-medium text-gray-600">Provider *</label><select name="provider" required className="input-field">{providers?.results?.map((p: any) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></div>
              </div>
              <div><label className="text-xs font-medium text-gray-600">Policy Number *</label><input name="policy_number" required className="input-field" /></div>
              <div className="grid grid-cols-3 gap-3">
                <div><label className="text-xs font-medium text-gray-600">Coverage $</label><input name="coverage_amount" type="number" className="input-field" /></div>
                <div><label className="text-xs font-medium text-gray-600">Start</label><input name="start_date" type="date" className="input-field" /></div>
                <div><label className="text-xs font-medium text-gray-600">End</label><input name="end_date" type="date" className="input-field" /></div>
              </div>
              <div className="flex justify-end gap-3 pt-3">
                <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
                <button type="submit" disabled={createPolicy.isPending} className="btn-primary">{createPolicy.isPending ? 'Creating...' : 'Create Policy'}</button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </>
  )
}

function ClaimsTab({ search, showCreate, setShowCreate }: { search: string; showCreate: boolean; setShowCreate: (v: boolean) => void }) {
  const queryClient = useQueryClient()
  const params: Record<string, any> = { page_size: 20 }
  if (search) params.search = search

  const { data, isLoading } = useQuery({
    queryKey: ['insurance-claims', params],
    queryFn: () => insuranceService.getClaims(params),
  })

  const { data: policies } = useQuery({ queryKey: ['insurance-policies', {}], queryFn: () => insuranceService.getPolicies({}) })

  const createClaim = useMutation({
    mutationFn: (d: any) => insuranceService.createClaim(d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['insurance-claims'] }); toast.success('Claim submitted'); setShowCreate(false) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed'),
  })

  const approveClaim = useMutation({
    mutationFn: (id: string) => insuranceService.approveClaim(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['insurance-claims'] }); toast.success('Claim approved') },
  })

  const rejectClaim = useMutation({
    mutationFn: (id: string) => insuranceService.rejectClaim(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['insurance-claims'] }); toast.success('Claim rejected') },
  })

  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-700',
    approved: 'bg-green-100 text-green-700',
    rejected: 'bg-red-100 text-red-700',
    paid: 'bg-blue-100 text-blue-700',
  }

  return (
    <>
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="p-8 space-y-3">{[...Array(4)].map((_, i) => <div key={i} className="h-16 bg-gray-100 rounded animate-pulse" />)}</div>
        ) : !data?.results?.length ? (
          <div className="text-center py-12"><FileCheck className="w-12 h-12 text-gray-300 mx-auto mb-3" /><p className="text-gray-500">No claims found</p></div>
        ) : (
          <div className="divide-y">
            {data.results.map((c: any) => (
              <motion.div key={c.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">Claim #{c.claim_number || c.id.slice(0, 8)}</p>
                    <p className="text-sm text-gray-500">{c.diagnosis || c.description || 'No description'}</p>
                    <p className="text-xs text-gray-400 mt-1">Submitted: {format(new Date(c.created_at), 'MMM d, yyyy')}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900">${Number(c.amount || 0).toLocaleString()}</p>
                    <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${statusColors[c.status] || 'bg-gray-100 text-gray-600'}`}>{c.status}</span>
                    {c.status === 'pending' && (
                      <div className="flex gap-2 mt-2 justify-end">
                        <button onClick={() => approveClaim.mutate(c.id)} className="text-xs text-green-600 hover:underline flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Approve</button>
                        <button onClick={() => rejectClaim.mutate(c.id)} className="text-xs text-red-600 hover:underline flex items-center gap-1"><XCircle className="w-3 h-3" /> Reject</button>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-2xl p-6 w-full max-w-lg mx-4">
            <h2 className="text-lg font-bold mb-4">Submit Claim</h2>
            <form onSubmit={(e) => { e.preventDefault(); const fd = new FormData(e.currentTarget); createClaim.mutate({ policy: fd.get('policy'), amount: fd.get('amount'), diagnosis: fd.get('diagnosis'), description: fd.get('description'), service_date: fd.get('service_date') }) }} className="space-y-3">
              <div><label className="text-xs font-medium text-gray-600">Policy *</label><select name="policy" required className="input-field"><option value="">Select...</option>{policies?.results?.map((p: any) => <option key={p.id} value={p.id}>{p.policy_number} - {p.patient_name}</option>)}</select></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="text-xs font-medium text-gray-600">Amount *</label><input name="amount" type="number" step="0.01" required className="input-field" /></div>
                <div><label className="text-xs font-medium text-gray-600">Service Date *</label><input name="service_date" type="date" required className="input-field" /></div>
              </div>
              <div><label className="text-xs font-medium text-gray-600">Diagnosis</label><input name="diagnosis" className="input-field" /></div>
              <div><label className="text-xs font-medium text-gray-600">Description</label><textarea name="description" className="input-field" rows={3} /></div>
              <div className="flex justify-end gap-3 pt-3">
                <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
                <button type="submit" disabled={createClaim.isPending} className="btn-primary">{createClaim.isPending ? 'Submitting...' : 'Submit Claim'}</button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </>
  )
}
