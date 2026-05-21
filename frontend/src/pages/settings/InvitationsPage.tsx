import { useState } from 'react'
import { format } from 'date-fns'
import { Mail, Plus, Copy, XCircle } from 'lucide-react'
import { useInvitations, useCreateInvitation, useCancelInvitation, useRoles } from '@/hooks/useRbac'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'

export default function InvitationsPage() {
  const { data, isLoading } = useInvitations()
  const { data: rolesData } = useRoles()
  const createInvitation = useCreateInvitation()
  const cancelInvitation = useCancelInvitation()
  const [showForm, setShowForm] = useState(false)

  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm<{ email: string; role_id: string }>()

  const onSubmit = async (data: { email: string; role_id: string }) => {
    await createInvitation.mutateAsync(data)
    reset()
    setShowForm(false)
  }

  const copyLink = (token: string) => {
    navigator.clipboard.writeText(`${window.location.origin}/invitation/${token}`)
    toast.success('Invitation link copied!')
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Invitations</h1>
          <p className="text-gray-500 text-sm mt-1">Invite team members to your organization</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Invite Member
        </button>
      </div>

      {/* Invite Form */}
      {showForm && (
        <div className="bg-white rounded-xl p-6 shadow-soft border border-gray-100">
          <form onSubmit={handleSubmit(onSubmit)} className="flex items-end gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
              <input type="email" {...register('email')} className="input-field" placeholder="colleague@example.com" />
            </div>
            <div className="w-48">
              <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
              <select {...register('role_id')} className="input-field">
                <option value="">Select role...</option>
                {rolesData?.results?.map(role => <option key={role.id} value={role.id}>{role.name}</option>)}
              </select>
            </div>
            <button type="submit" disabled={isSubmitting} className="btn-primary">{isSubmitting ? 'Sending...' : 'Send Invite'}</button>
            <button type="button" onClick={() => setShowForm(false)} className="btn-ghost">Cancel</button>
          </form>
        </div>
      )}

      {/* Invitations List */}
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="p-8 space-y-4">{[...Array(3)].map((_, i) => <div key={i} className="animate-pulse h-16 bg-gray-100 rounded" />)}</div>
        ) : data?.results?.length ? (
          <div className="divide-y divide-gray-50">
            {data.results.map(inv => (
              <div key={inv.id} className="flex items-center gap-4 p-5">
                <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center">
                  <Mail className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{inv.email}</p>
                  <p className="text-sm text-gray-500">Role: {inv.role_name} • By: {inv.invited_by_name}</p>
                  <p className="text-xs text-gray-400">Expires: {format(new Date(inv.expires_at), 'MMM d, yyyy')}</p>
                </div>
                <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                  inv.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                  inv.status === 'accepted' ? 'bg-green-100 text-green-700' :
                  'bg-red-100 text-red-700'
                }`}>{inv.status}</span>
                {inv.status === 'pending' && (
                  <div className="flex gap-1">
                    <button onClick={() => copyLink(inv.token)} className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-400" title="Copy link">
                      <Copy className="w-4 h-4" />
                    </button>
                    <button onClick={() => cancelInvitation.mutate(inv.id)} className="p-1.5 hover:bg-red-50 rounded-lg text-red-400" title="Cancel">
                      <XCircle className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16"><Mail className="w-12 h-12 text-gray-300 mx-auto mb-3" /><p className="text-gray-500">No invitations yet</p></div>
        )}
      </div>
    </div>
  )
}
