import { Menu, Search, Bell, ChevronDown } from 'lucide-react'
import { useUIStore } from '@/stores/uiStore'
import { useAuthStore } from '@/stores/authStore'
import { useState } from 'react'
import { cn, getInitials, generateAvatarColor } from '@/lib/utils'
import TenantSwitcher from './TenantSwitcher'

export default function TopBar() {
  const { toggleSidebar } = useUIStore()
  const { user } = useAuthStore()
  const [searchOpen, setSearchOpen] = useState(false)

  const userName = user ? `${user.first_name} ${user.last_name}` : 'User'
  const avatarColor = generateAvatarColor(userName)

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
        <div className={cn(
          'relative transition-all duration-300',
          searchOpen ? 'w-80' : 'w-64'
        )}>
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search patients, records..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-sm focus:bg-white focus:border-primary-300 focus:ring-2 focus:ring-primary-500/10 outline-none transition-all"
            onFocus={() => setSearchOpen(true)}
            onBlur={() => setSearchOpen(false)}
          />
          <kbd className="absolute right-3 top-1/2 -translate-y-1/2 hidden sm:inline-flex h-5 items-center gap-1 rounded border border-slate-200 bg-slate-50 px-1.5 text-[10px] font-medium text-slate-400">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Right */}
      <div className="flex items-center gap-3">
        {/* Tenant Switcher */}
        <TenantSwitcher />
        
        {/* Notifications */}
        <button className="relative w-10 h-10 flex items-center justify-center rounded-xl hover:bg-slate-100 text-slate-600 transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-rose-500 rounded-full animate-pulse-soft" />
        </button>

        {/* User Menu */}
        <button className="flex items-center gap-3 pl-3 pr-2 py-1.5 rounded-xl hover:bg-slate-50 transition-colors">
          <div className={cn('w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-semibold', avatarColor)}>
            {getInitials(userName)}
          </div>
          <div className="hidden md:block text-left">
            <p className="text-sm font-medium text-slate-700">{userName}</p>
            <p className="text-xs text-slate-400">{user?.tenant_context?.role_name}</p>
          </div>
          <ChevronDown className="w-4 h-4 text-slate-400" />
        </button>
      </div>
    </header>
  )
}
