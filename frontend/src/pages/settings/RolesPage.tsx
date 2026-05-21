import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Shield, Trash2 } from 'lucide-react'
import { useRoles, useCreateRole, useDeleteRole } from '@/hooks/useRbac'
import { useForm } from 'react-hook-form'

export default function RolesPage() {
  const { data: rolesData, isLoading } = useRoles()
  const createRole = useCreateRole()
  const deleteRole = useDeleteRole()
  const [showCreate, setShowCreate] = useState(false)

  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm<{ name: string; description: string }>()

  const onCreateSubmit = async (data: { name: string; description: string }) => {
    await createRole.mutateAsync(data)
    reset()
    setShowCreate(false)
  }

  const handleDelete = (id: string) => {
    if (confirm('Delete this role? Users with this role will need to be reassigned.')) {
      deleteRole.mutate(id)
    }
  }

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
            <form onSubmit={handleSubmit(onCreateSubmit)} className="flex items-end gap-4">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-1">Role Name</label>
                <input {...register('name')} className="input-field" placeholder="e.g., Nurse" />
              </div>
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <input {...register('description')} className="input-field" placeholder="What this role does..." />
              </div>
              <button type="submit" disabled={isSubmitting} className="btn-primary">{isSubmitting ? 'Creating...' : 'Create'}</button>
              <button type="button" onClick={() => setShowCreate(false)} className="btn-ghost">Cancel</button>
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
                {!role.is_system_role && (
                  <div className="flex gap-1">
                    <button onClick={() => handleDelete(role.id)} className="p-1.5 hover:bg-red-50 rounded text-red-400 hover:text-red-600">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </div>
              <div className="flex flex-wrap gap-1 mt-3">
                {role.permissions?.slice(0, 8).map(perm => (
                  <span key={perm.id} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">{perm.codename}</span>
                ))}
                {role.permissions?.length > 8 && <span className="text-xs text-gray-400">+{role.permissions.length - 8} more</span>}
              </div>
              {role.is_system_role && <p className="text-xs text-amber-600 mt-2">System role (cannot be modified)</p>}
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
