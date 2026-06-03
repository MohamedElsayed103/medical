import { Menu, Search, Bell, ChevronDown, LogOut, User, Settings, X } from 'lucide-react'
import { useUIStore } from '@/stores/uiStore'
import { useAuthStore } from '@/stores/authStore'
import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { cn, getInitials, generateAvatarColor } from '@/lib/utils'
import { useQuery } from '@tanstack/react-query'
import { notificationsService, patientsService } from '@/services/api'
import TenantSwitcher from './TenantSwitcher'

export default function TopBar() {
  const { toggleSidebar } = useUIStore()
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [searchOpen, setSearchOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [showNotifications, setShowNotifications] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const notifRef = useRef<HTMLDivElement>(null)
  const userMenuRef = useRef<HTMLDivElement>(null)
  const searchRef = useRef<HTMLDivElement>(null)

  const userName = user ? `${user.first_name} ${user.last_name}` : 'User'
  const avatarColor = generateAvatarColor(userName)

  // Notifications
  const { data: notifications } = useQuery({
    queryKey: ['notifications', { page_size: 5 }],
    queryFn: () => notificationsService.getAll({ page_size: 5 }),
    retry: false,
  })

  // Search patients
  const { data: searchResults } = useQuery({
    queryKey: ['search', searchQuery],
    queryFn: () => patientsService.getAll({ search: searchQuery, page_size: 5 }),
    enabled: searchQuery.length >= 2,
  })

  // Close dropdowns on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) setShowNotifications(false)
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) setShowUserMenu(false)
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) { setSearchOpen(false); setSearchQuery('') }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Use dedicated unread count query
  const { data: unreadCountData } = useQuery({
    queryKey: ['notifications-unread-count'],
    queryFn: () => notificationsService.getAll({ is_read: 'false', page_size: 1 }),
    retry: false,
  })
  const unreadCount = unreadCountData?.count ?? 0

  return (
    <header className="h-16 bg-white/80 backdrop-blur-xl border-b border-slate-100 flex items-center justify-between px-4 lg:px-8 sticky top-0 z-20">
      {/* Left */}
      <div className="flex items-center gap-4">
        <button
          onClick={toggleSidebar}
          className="lg:hidden w-10 h-10 flex items-center justify-center rounded-xl hover:bg-slate-100 text-slate-600"
        >
          <Menu className="w-5 h-5" />
        </button>
        
        {/* Search */}
        <div ref={searchRef} className="relative">
          <div className={cn(
            'relative transition-all duration-300',
            searchOpen ? 'w-80' : 'w-64'
          )}>
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search patients, records..."
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setSearchOpen(true) }}
              onFocus={() => setSearchOpen(true)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-sm focus:bg-white focus:border-primary-300 focus:ring-2 focus:ring-primary-500/10 outline-none transition-all"
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2">
                <X className="w-3.5 h-3.5 text-slate-400" />
              </button>
            )}
          </div>

          {/* Search Results Dropdown */}
          {searchOpen && searchQuery.length >= 2 && (
            <div className="absolute top-full mt-2 left-0 w-80 bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden z-50">
              {searchResults?.results?.length ? (
                <div className="divide-y divide-slate-50 max-h-64 overflow-y-auto">
                  {searchResults.results.map((patient: any) => (
                    <button
                      key={patient.id}
                      onClick={() => { navigate(`/patients/${patient.id}`); setSearchQuery(''); setSearchOpen(false) }}
                      className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-50 text-left"
                    >
                      <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-xs font-semibold text-primary-700">
                        {patient.first_name?.[0]}{patient.last_name?.[0]}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-slate-800">{patient.first_name} {patient.last_name}</p>
                        <p className="text-xs text-slate-400">{patient.medical_record_number || patient.email || patient.phone || ''}</p>
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="px-4 py-6 text-center text-sm text-slate-400">No patients found</div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Right */}
      <div className="flex items-center gap-3">
        {/* Tenant Switcher */}
        <TenantSwitcher />
        
        {/* Notifications */}
        <div ref={notifRef} className="relative">
          <button
            onClick={() => { setShowNotifications(!showNotifications); setShowUserMenu(false) }}
            className="relative w-10 h-10 flex items-center justify-center rounded-xl hover:bg-slate-100 text-slate-600 transition-colors"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-4 h-4 bg-rose-500 rounded-full text-[10px] text-white flex items-center justify-center font-medium">
                {unreadCount}
              </span>
            )}
          </button>

          {/* Notifications Dropdown */}
          {showNotifications && (
            <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden z-50">
              <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
                <h3 className="font-semibold text-sm text-slate-800">Notifications</h3>
                <button onClick={() => { navigate('/notifications'); setShowNotifications(false) }} className="text-xs text-primary-600 hover:text-primary-700">View All</button>
              </div>
              <div className="max-h-72 overflow-y-auto divide-y divide-slate-50">
                {notifications?.results?.length ? (
                  notifications.results.map((notif: any) => (
                    <div key={notif.id} className={cn('px-4 py-3 text-sm', !notif.is_read && 'bg-primary-50/30')}>
                      <p className="font-medium text-slate-800 truncate">{notif.title}</p>
                      <p className="text-xs text-slate-500 mt-0.5 truncate">{notif.message}</p>
                    </div>
                  ))
                ) : (
                  <div className="px-4 py-8 text-center text-sm text-slate-400">No notifications</div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Menu */}
        <div ref={userMenuRef} className="relative">
          <button
            onClick={() => { setShowUserMenu(!showUserMenu); setShowNotifications(false) }}
            className="flex items-center gap-3 pl-3 pr-2 py-1.5 rounded-xl hover:bg-slate-50 transition-colors"
          >
            <div className={cn('w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-semibold', avatarColor)}>
              {getInitials(userName)}
            </div>
            <div className="hidden md:block text-left">
              <p className="text-sm font-medium text-slate-700">{userName}</p>
              <p className="text-xs text-slate-400">{user?.tenant_context?.role_name}</p>
            </div>
            <ChevronDown className={cn('w-4 h-4 text-slate-400 transition-transform', showUserMenu && 'rotate-180')} />
          </button>

          {/* User Menu Dropdown */}
          {showUserMenu && (
            <div className="absolute right-0 top-full mt-2 w-56 bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden z-50">
              <div className="px-4 py-3 border-b border-slate-100">
                <p className="text-sm font-semibold text-slate-800">{userName}</p>
                <p className="text-xs text-slate-400">{user?.email}</p>
              </div>
              <div className="py-1">
                <button onClick={() => { navigate('/profile'); setShowUserMenu(false) }} className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50">
                  <User className="w-4 h-4 text-slate-400" /> Profile
                </button>
                <button onClick={() => { navigate('/settings'); setShowUserMenu(false) }} className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50">
                  <Settings className="w-4 h-4 text-slate-400" /> Settings
                </button>
                <div className="border-t border-slate-100 mt-1 pt-1">
                  <button onClick={handleLogout} className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-rose-600 hover:bg-rose-50">
                    <LogOut className="w-4 h-4" /> Logout
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
