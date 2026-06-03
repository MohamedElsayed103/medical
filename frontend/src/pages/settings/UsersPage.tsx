import { useState } from 'react'
import { Users, MoreVertical } from 'lucide-react'
import { useTenantUsers, useUpdateTenantUser, useDeleteTenantUser } from '@/hooks/useRbac'
import { useRoles } from '@/hooks/useRbac'

export default function UsersPage() {
  const { data, isLoading } = useTenantUsers()
  const { data: rolesData } = useRoles()
  const updateUser = useUpdateTenantUser()
  const deleteUser = useDeleteTenantUser()
  const [editingUser, setEditingUser] = useState<string | null>(null)

  const handleRoleChange = (userId: string, roleId: string) => {
    updateUser.mutate({ id: userId, data: { role_id: roleId } })
    setEditingUser(null)
  }

  const handleRemove = (userId: string) => {
    if (confirm('Remove this user from the organization?')) {
      deleteUser.mutate(userId)
    }
  }

  const getUserDisplayName = (user: any) => {
    if (user.display_name) return user.display_name
    if (user.first_name || user.last_name) return `${user.first_name || ''} ${user.last_name || ''}`.trim()
    if (user.user_name) return user.user_name
    return user.email || user.user_email || 'Unknown'
  }

  const getUserEmail = (user: any) => {
    return user.email || user.user_email || ''
  }

  const getUserInitials = (user: any) => {
    const name = getUserDisplayName(user)
    return name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()
  }

  const getUserRoleId = (user: any) => {
    return user.role || user.role_id || ''
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Team Members</h1>
        <p className="text-gray-500 text-sm mt-1">{data?.count ?? 0} members in your organization</p>
      </div>

      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="p-8 space-y-4">{[...Array(5)].map((_, i) => <div key={i} className="animate-pulse h-16 bg-gray-100 rounded" />)}</div>
        ) : data?.results?.length ? (
          <div className="divide-y divide-gray-50">
            {data.results.map(user => (
              <div key={user.id} className="flex items-center gap-4 p-5">
                <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center text-sm font-semibold text-primary-700">
                  {getUserInitials(user)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900">{getUserDisplayName(user)}</p>
                  <p className="text-sm text-gray-500">{getUserEmail(user)}</p>
                  {user.specialty && <p className="text-xs text-gray-400">{user.specialty}</p>}
                </div>
                <div className="flex items-center gap-3">
                  {editingUser === user.id ? (
                    <select
                      defaultValue={getUserRoleId(user)}
                      onChange={(e) => handleRoleChange(user.id, e.target.value)}
                      onBlur={() => setEditingUser(null)}
                      className="input-field text-sm w-auto"
                      autoFocus
                    >
                      {rolesData?.results?.map(role => (
                        <option key={role.id} value={role.id}>{role.name}</option>
                      ))}
                    </select>
                  ) : (
                    <span className="px-2.5 py-1 bg-primary-50 text-primary-700 rounded-full text-xs font-medium">
                      {user.role_name || 'No role'}
                    </span>
                  )}
                  <span className={`px-2 py-0.5 rounded-full text-xs ${
                    user.status === 'ACTIVE' || user.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                  }`}>{(user.status || 'active').toLowerCase()}</span>
                  <div className="relative">
                    <button onClick={() => setEditingUser(editingUser === user.id ? null : user.id)} className="p-1.5 hover:bg-gray-100 rounded-lg" title="Change role">
                      <MoreVertical className="w-4 h-4 text-gray-400" />
                    </button>
                  </div>
                  <button onClick={() => handleRemove(user.id)} className="text-xs text-red-500 hover:text-red-700">Remove</button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16"><Users className="w-12 h-12 text-gray-300 mx-auto mb-3" /><p className="text-gray-500">No team members</p></div>
        )}
      </div>
    </div>
  )
}
