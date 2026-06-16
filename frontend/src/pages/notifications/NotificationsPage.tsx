import { useState } from 'react'
import { motion } from 'framer-motion'
import { Bell, Check, CheckCheck, Settings, Mail, MessageSquare, Smartphone } from 'lucide-react'
import { safeFormat } from '@/lib/utils'
import { useNotifications, useMarkAsRead, useMarkAllAsRead, useNotificationPreferences, useUpdateNotificationPreferences } from '@/hooks/useNotifications'

export default function NotificationsPage() {
  const [page, setPage] = useState(1)
  const [filter, setFilter] = useState<string>('')

  const params: Record<string, string | number> = { page, page_size: 20 }
  if (filter) params.is_read = filter

  const { data, isLoading } = useNotifications(params)
  const markAsRead = useMarkAsRead()
  const markAllAsRead = useMarkAllAsRead()
  const { data: prefs } = useNotificationPreferences()
  const updatePrefs = useUpdateNotificationPreferences()
  const [showPrefs, setShowPrefs] = useState(false)

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'email': return <Mail className="w-4 h-4 text-blue-500" />
      case 'sms': return <Smartphone className="w-4 h-4 text-green-500" />
      default: return <Bell className="w-4 h-4 text-primary-500" />
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
          <p className="text-gray-500 text-sm mt-1">{data?.count ?? 0} notifications</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => markAllAsRead.mutate()} className="btn-ghost flex items-center gap-2 text-sm">
            <CheckCheck className="w-4 h-4" /> Mark All Read
          </button>
          <button onClick={() => setShowPrefs(!showPrefs)} className="btn-ghost flex items-center gap-2 text-sm">
            <Settings className="w-4 h-4" /> Preferences
          </button>
        </div>
      </div>

      {/* Preferences Panel */}
      {showPrefs && prefs && (
        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="bg-white rounded-xl p-6 shadow-soft border border-gray-100">
          <h3 className="font-semibold text-gray-900 mb-4">Notification Preferences</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { key: 'email_enabled', label: 'Email', icon: Mail },
              { key: 'sms_enabled', label: 'SMS', icon: Smartphone },
              { key: 'push_enabled', label: 'Push', icon: Bell },
              { key: 'in_app_enabled', label: 'In-App', icon: MessageSquare },
            ].map(({ key, label, icon: Icon }) => (
              <label key={key} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100">
                <input
                  type="checkbox"
                  checked={(prefs as any)[key]}
                  onChange={(e) => updatePrefs.mutate({ [key]: e.target.checked })}
                  className="w-4 h-4 text-primary-600 rounded"
                />
                <Icon className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-medium">{label}</span>
              </label>
            ))}
          </div>
          <div className="mt-5 pt-4 border-t border-gray-100">
            <p className="text-sm font-medium text-gray-700 mb-2">Quiet Hours</p>
            <p className="text-xs text-gray-400 mb-3">During these hours, only in-app notifications are delivered (SMS/push/email are held).</p>
            <div className="flex items-center gap-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">From</label>
                <input type="time" value={prefs.quiet_hours_start?.slice(0, 5) || ''}
                  onChange={(e) => updatePrefs.mutate({ quiet_hours_start: e.target.value || null })}
                  className="input-field w-auto text-sm" />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">To</label>
                <input type="time" value={prefs.quiet_hours_end?.slice(0, 5) || ''}
                  onChange={(e) => updatePrefs.mutate({ quiet_hours_end: e.target.value || null })}
                  className="input-field w-auto text-sm" />
              </div>
              {(prefs.quiet_hours_start || prefs.quiet_hours_end) && (
                <button onClick={() => updatePrefs.mutate({ quiet_hours_start: null, quiet_hours_end: null })}
                  className="text-xs text-gray-500 hover:text-red-500 mt-5">Clear</button>
              )}
            </div>
          </div>
        </motion.div>
      )}

      {/* Filter */}
      <div className="flex gap-2">
        <button onClick={() => setFilter('')} className={`px-3 py-1.5 rounded-lg text-sm font-medium ${!filter ? 'bg-primary-100 text-primary-700' : 'text-gray-500 hover:bg-gray-100'}`}>All</button>
        <button onClick={() => setFilter('false')} className={`px-3 py-1.5 rounded-lg text-sm font-medium ${filter === 'false' ? 'bg-primary-100 text-primary-700' : 'text-gray-500 hover:bg-gray-100'}`}>Unread</button>
        <button onClick={() => setFilter('true')} className={`px-3 py-1.5 rounded-lg text-sm font-medium ${filter === 'true' ? 'bg-primary-100 text-primary-700' : 'text-gray-500 hover:bg-gray-100'}`}>Read</button>
      </div>

      {/* Notification List */}
      <div className="bg-white rounded-2xl shadow-soft border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="p-8 space-y-4">{[...Array(5)].map((_, i) => <div key={i} className="animate-pulse h-16 bg-gray-100 rounded" />)}</div>
        ) : data?.results?.length ? (
          <div className="divide-y divide-gray-50">
            {data.results.map(notif => (
              <motion.div
                key={notif.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className={`flex items-start gap-4 p-5 transition-colors ${!notif.is_read ? 'bg-primary-50/30' : 'hover:bg-gray-50/50'}`}
              >
                <div className="mt-1">{getTypeIcon(notif.channel)}</div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm ${!notif.is_read ? 'font-semibold text-gray-900' : 'text-gray-700'}`}>{notif.title}</p>
                  <p className="text-sm text-gray-500 mt-0.5">{notif.body}</p>
                  <p className="text-xs text-gray-400 mt-1">{safeFormat(notif.created_at, 'MMM d, yyyy h:mm a')}</p>
                </div>
                {!notif.is_read && (
                  <button onClick={() => markAsRead.mutate(notif.id)} className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-400 hover:text-primary-600" title="Mark as read">
                    <Check className="w-4 h-4" />
                  </button>
                )}
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16"><Bell className="w-12 h-12 text-gray-300 mx-auto mb-3" /><p className="text-gray-500">No notifications</p></div>
        )}

        {data && data.count > 20 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100">
            <p className="text-sm text-gray-500">Page {page}</p>
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
