import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import { Shield, Building2, Save } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { authService } from '@/services/api'
import toast from 'react-hot-toast'

export default function ProfilePage() {
  const { user, roleName, permissions, currentTenant, setUser } = useAuthStore()
  const [isEditing, setIsEditing] = useState(false)

  const { register, handleSubmit, formState: { isSubmitting } } = useForm({
    defaultValues: {
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      phone: user?.phone || '',
      display_name: user?.display_name || '',
    },
  })

  const onSubmit = async (data: any) => {
    try {
      const updated = await authService.updateProfile(data)
      setUser(updated)
      toast.success('Profile updated')
      setIsEditing(false)
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to update profile')
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>

      {/* Personal Info */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl shadow-soft border border-gray-100 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center text-lg font-bold text-primary-700">
              {user?.first_name?.[0]}{user?.last_name?.[0]}
            </div>
            <div>
              <h2 className="font-semibold text-gray-900">{user?.first_name} {user?.last_name}</h2>
              <p className="text-sm text-gray-500">{user?.email}</p>
            </div>
          </div>
          <button onClick={() => setIsEditing(!isEditing)} className="btn-ghost text-sm">
            {isEditing ? 'Cancel' : 'Edit'}
          </button>
        </div>

        {isEditing ? (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                <input {...register('first_name')} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                <input {...register('last_name')} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
                <input {...register('display_name')} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <input {...register('phone')} className="input-field" />
              </div>
            </div>
            <button type="submit" disabled={isSubmitting} className="btn-primary flex items-center gap-2">
              <Save className="w-4 h-4" /> {isSubmitting ? 'Saving...' : 'Save Changes'}
            </button>
          </form>
        ) : (
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><span className="text-gray-500">Email:</span> <span className="font-medium">{user?.email}</span></div>
            <div><span className="text-gray-500">Phone:</span> <span className="font-medium">{user?.phone || 'Not set'}</span></div>
            <div><span className="text-gray-500">Username:</span> <span className="font-medium">{user?.username || 'Not set'}</span></div>
            <div><span className="text-gray-500">Last Login:</span> <span className="font-medium">{user?.last_login ? new Date(user.last_login).toLocaleDateString() : 'N/A'}</span></div>
          </div>
        )}
      </motion.div>

      {/* Organization & Role */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-white rounded-2xl shadow-soft border border-gray-100 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Building2 className="w-5 h-5 text-primary-600" />
          <h3 className="font-semibold text-gray-900">Organization</h3>
        </div>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div><span className="text-gray-500">Organization:</span> <span className="font-medium">{currentTenant?.tenant_name || 'N/A'}</span></div>
          <div><span className="text-gray-500">Role:</span> <span className="font-medium">{roleName || currentTenant?.role_name || 'N/A'}</span></div>
        </div>
      </motion.div>

      {/* Permissions */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="bg-white rounded-2xl shadow-soft border border-gray-100 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Shield className="w-5 h-5 text-secondary-600" />
          <h3 className="font-semibold text-gray-900">Permissions ({permissions.length})</h3>
        </div>
        {permissions.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {permissions.map(perm => (
              <span key={perm} className="px-2.5 py-1 bg-gray-100 text-gray-700 rounded-lg text-xs font-mono">{perm}</span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">No permissions loaded</p>
        )}
      </motion.div>
    </div>
  )
}
