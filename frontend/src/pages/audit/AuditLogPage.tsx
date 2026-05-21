import { useState } from 'react'
import { format } from 'date-fns'
import { Activity, Search } from 'lucide-react'
import { useAuditLogs } from '@/hooks/useAudit'

export default function AuditLogPage() {
  const [search, setSearch] = useState('')
  const [actionFilter, setActionFilter] = useState('')
  const [page, setPage] = useState(1)

  const params: Record<string, string | number> = { page, page_size: 25, ordering: '-created_at' }
  if (search) params.search = search
  if (actionFilter) params.action = actionFilter

  const { data, isLoading } = useAuditLogs(params)

  const getActionColor = (action: string) => {
    if (action.includes('create') || action.includes('add')) return 'bg-green-100 text-green-700'
    if (action.includes('update') || action.includes('edit')) return 'bg-blue-100 text-blue-700'
    if (action.includes('delete') || action.includes('remove')) return 'bg-red-100 text-red-700'
    if (action.includes('login') || action.includes('auth')) return 'bg-purple-100 text-purple-700'
    return 'bg-gray-100 text-gray-700'
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Audit Log</h1>
        <p className="text-gray-500 text-sm mt-1">Track all system activity and changes</p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input type="text" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1) }} placeholder="Search by user, action, resource..." className="input-field pl-10" />
        </div>
        <select value={actionFilter} onChange={(e) => { setActionFilter(e.target.value); setPage(1) }} className="input-field w-auto">
          <option value="">All Actions</option>
          <option value="create">Create</option>
          <option value="update">Update</option>
          <option value="delete">Delete</option>
          <option value="login">Login</option>
        </select>
      </div>

      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="p-8 space-y-3">{[...Array(10)].map((_, i) => <div key={i} className="animate-pulse h-12 bg-gray-100 rounded" />)}</div>
        ) : data?.results?.length ? (
          <div className="divide-y divide-gray-50">
            {data.results.map(log => (
              <div key={log.id} className="flex items-center gap-4 px-5 py-3 hover:bg-gray-50/50">
                <div className="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center flex-shrink-0">
                  <Activity className="w-4 h-4 text-gray-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900">
                    <span className="font-medium">{log.user_email || 'System'}</span>
                    {' '}<span className={`px-1.5 py-0.5 rounded text-xs font-medium ${getActionColor(log.action)}`}>{log.action}</span>
                    {' '}<span className="text-gray-600">{log.resource_type}</span>
                    {log.resource_id && <span className="text-gray-400 text-xs ml-1">({log.resource_id.slice(0, 8)}...)</span>}
                  </p>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="text-xs text-gray-500">{format(new Date(log.created_at || log.timestamp), 'MMM d, h:mm a')}</p>
                  {log.ip_address && <p className="text-xs text-gray-400">{log.ip_address}</p>}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16"><Activity className="w-12 h-12 text-gray-300 mx-auto mb-3" /><p className="text-gray-500">No audit logs</p></div>
        )}

        {data && data.count > 25 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100">
            <p className="text-sm text-gray-500">Showing {(page-1)*25 + 1}–{Math.min(page*25, data.count)} of {data.count}</p>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={!data.previous} className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-50">Previous</button>
              <button onClick={() => setPage(p => p + 1)} disabled={!data.next} className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-50">Next</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
