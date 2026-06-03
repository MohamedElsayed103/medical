import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Shield, Trash2, Edit2, Check } from 'lucide-react'
import { useRoles, useCreateRole, useDeleteRole, useUpdateRole, usePermissions } from '@/hooks/useRbac'
import { useForm } from 'react-hook-form'

export default function RolesPage() {
  const { data: rolesData, isLoading } = useRoles()
  const { data: permsData } = usePermissions({ page_size: '100' } as any)
  const createRole = useCreateRole()
  const deleteRole = useDeleteRole()
  const updateRole = useUpdateRole()
  const [showCreate, setShowCreate] = useState(false)
  const [editingRole, setEditingRole] = useState<string | null>(null)
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([])
  const [editPermissions, setEditPermissions] = useState<string[]>([])

  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm<{ name: string; description: string }>()

  const onCreateSubmit = async (data: { name: string; description: string }) => {
    await createRole.mutateAsync({ ...data, permission_ids: selectedPermissions })
    reset()
    setSelectedPermissions([])
    setShowCreate(false)
  }

  const handleDelete = (id: string) => {
    if (confirm('Delete this role? Users with this role will need to be reassigned.')) {
      deleteRole.mutate(id)
    }
  }

  const togglePermission = (permId: string, forEdit = false) => {
    if (forEdit) {
      setEditPermissions(prev => prev.includes(permId) ? prev.filter(p => p !== permId) : [...prev, permId])
    } else {
      setSelectedPermissions(prev => prev.includes(permId) ? prev.filter(p => p !== permId) : [...prev, permId])
    }
  }

  const startEditing = (role: any) => {
    setEditingRole(role.id)
    setEditPermissions(role.permissions?.map((p: any) => p.id) || [])
  }

  const savePermissions = (roleId: string) => {
    updateRole.mutate({ id: roleId, data: { permission_ids: editPermissions } })
    setEditingRole(null)
  }

  // Group permissions by resource
  const permissionsByResource = permsData?.results?.reduce((acc: Record<string, any[]>, perm: any) => {
    const resource = perm.resource || 'other'
    if (!acc[resource]) acc[resource] = []
    acc[resource].push(perm)
    return acc
  }, {} as Record<string, any[]>) || {}

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Roles & Permissions</h1>
          <p className="text-gray-500 text-sm mt-1">{rolesData?.results?.length ?? 0} roles configured</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Create Role
        </button>
      </div>

      {/* Create Role Form */}
      <AnimatePresence>
        {showCreate && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="bg-white rounded-xl p-6 shadow-soft border border-gray-100">
            <form onSubmit={handleSubmit(onCreateSubmit)} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Role Name *</label>
                  <input {...register('name')} className="input-field" placeholder="e.g., Nurse" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <input {...register('description')} className="input-field" placeholder="What this role does..." />
                </div>
              </div>
              
              {/* Permissions Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Permissions</label>
                <div className="border border-gray-200 rounded-lg p-4 max-h-64 overflow-y-auto space-y-3">
                  {Object.entries(permissionsByResource).map(([resource, perms]) => (
                    <div key={resource}>
                      <p className="text-xs font-semibold text-gray-500 uppercase mb-1">{resource.replace('_', ' ')}</p>
                      <div className="flex flex-wrap gap-2">
                        {(perms as any[]).map((perm: any) => (
                          <button
                            key={perm.id}
                            type="button"
                            onClick={() => togglePermission(perm.id)}
                            className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                              selectedPermissions.includes(perm.id)
                                ? 'bg-primary-100 text-primary-700 border border-primary-300'
                                : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200'
                            }`}
                          >
                            {perm.name}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-gray-400 mt-1">{selectedPermissions.length} permissions selected</p>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button type="button" onClick={() => { setShowCreate(false); setSelectedPermissions([]) }} className="btn-ghost">Cancel</button>
                <button type="submit" disabled={isSubmitting} className="btn-primary">{isSubmitting ? 'Creating...' : 'Create Role'}</button>
              </div>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Roles Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="animate-pulse h-40 bg-gray-100 rounded-xl" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {rolesData?.results?.map(role => (
            <motion.div
              key={role.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-xl p-6 shadow-soft border border-gray-100"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-secondary-50 flex items-center justify-center">
                    <Shield className="w-5 h-5 text-secondary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{role.name}</h3>
                    <p className="text-xs text-gray-500">{role.description || 'No description'}</p>
                  </div>
                </div>
                {!(role.is_system || role.is_system_role) && (
                  <div className="flex gap-1">
                    {editingRole === role.id ? (
                      <button onClick={() => savePermissions(role.id)} className="p-1.5 hover:bg-green-50 rounded text-green-600 hover:text-green-700">
                        <Check className="w-3.5 h-3.5" />
                      </button>
                    ) : (
                      <button onClick={() => startEditing(role)} className="p-1.5 hover:bg-blue-50 rounded text-blue-400 hover:text-blue-600">
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                    <button onClick={() => handleDelete(role.id)} className="p-1.5 hover:bg-red-50 rounded text-red-400 hover:text-red-600">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </div>

              {/* Permissions display / edit */}
              {editingRole === role.id ? (
                <div className="border border-gray-200 rounded-lg p-3 max-h-48 overflow-y-auto space-y-2 mt-2">
                  {Object.entries(permissionsByResource).map(([resource, perms]) => (
                    <div key={resource}>
                      <p className="text-xs font-semibold text-gray-500 uppercase mb-1">{resource.replace('_', ' ')}</p>
                      <div className="flex flex-wrap gap-1">
                        {(perms as any[]).map((perm: any) => (
                          <button
                            key={perm.id}
                            type="button"
                            onClick={() => togglePermission(perm.id, true)}
                            className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                              editPermissions.includes(perm.id)
                                ? 'bg-primary-100 text-primary-700'
                                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                            }`}
                          >
                            {perm.name}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-wrap gap-1 mt-3">
                  {role.permissions?.slice(0, 8).map((perm: any) => (
                    <span key={perm.id} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">{perm.name || perm.codename}</span>
                  ))}
                  {role.permissions?.length > 8 && <span className="text-xs text-gray-400">+{role.permissions.length - 8} more</span>}
                </div>
              )}
              {(role.is_system || role.is_system_role) && <p className="text-xs text-amber-600 mt-2">System role (cannot be modified)</p>}
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
