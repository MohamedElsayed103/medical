import { NavLink, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Activity, LayoutDashboard, Users, Calendar,
  Pill, FlaskConical, CreditCard, Bell, Settings,
  Shield, UserPlus, ClipboardList, ChevronLeft,
  LogOut, User, Brain, Package, ShieldCheck, Stethoscope
} from 'lucide-react'
import { useUIStore } from '@/stores/uiStore'
import { useAuthStore } from '@/stores/authStore'
import { cn, getInitials, generateAvatarColor } from '@/lib/utils'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/patients', icon: Users, label: 'Patients', permission: 'patients:read' },
  { to: '/appointments', icon: Calendar, label: 'Appointments', permission: 'appointments:read' },
  { to: '/visits', icon: Stethoscope, label: 'Visits', permission: 'medical_records:read' },
  { to: '/prescriptions', icon: Pill, label: 'Prescriptions', permission: 'prescriptions:read' },
  { to: '/lab-orders', icon: FlaskConical, label: 'Lab Orders', permission: 'lab_results:read' },
  { to: '/billing', icon: CreditCard, label: 'Billing', permission: 'billing:read' },
  { to: '/pharmacy', icon: Package, label: 'Pharmacy', permission: 'pharmacy:read' },
  { to: '/insurance', icon: ShieldCheck, label: 'Insurance', permission: 'insurance:read' },
  { to: '/ai', icon: Brain, label: 'AI Assistant' },
  { to: '/notifications', icon: Bell, label: 'Notifications', permission: 'notifications:read' },
  { to: '/audit-log', icon: ClipboardList, label: 'Audit Log', permission: 'audit:read' },
]

const settingsItems = [
  { to: '/settings/users', icon: Users, label: 'Users', permission: 'users:read' },
  { to: '/settings/roles', icon: Shield, label: 'Roles', permission: 'roles:read' },
  { to: '/settings/invitations', icon: UserPlus, label: 'Invitations', permission: 'invitations:read' },
  { to: '/settings', icon: Settings, label: 'General', permission: 'settings:read' },
]

export default function Sidebar() {
  const { sidebarOpen, sidebarCollapsed, toggleCollapsed } = useUIStore()
  const { user, hasPermission, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const userName = user ? `${user.first_name} ${user.last_name}` : 'User'
  const avatarColor = generateAvatarColor(userName)

  return (
    <motion.aside
      initial={false}
      animate={{
        width: sidebarCollapsed ? 80 : 288,
        x: sidebarOpen || window.innerWidth >= 1024 ? 0 : -288,
      }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className={cn(
        'fixed inset-y-0 left-0 z-40 flex flex-col bg-white border-r border-slate-100',
        'lg:relative lg:z-0'
      )}
      style={{ flexShrink: 0 }}
    >
      {/* Logo */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 gradient-primary rounded-xl flex items-center justify-center shadow-glow">
            <Activity className="w-5 h-5 text-white" />
          </div>
          {!sidebarCollapsed && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="font-bold text-lg text-slate-800"
            >
              MedFlow
            </motion.span>
          )}
        </div>
        <button
          onClick={toggleCollapsed}
          className="hidden lg:flex w-8 h-8 items-center justify-center rounded-lg hover:bg-slate-100 text-slate-400"
        >
          <ChevronLeft className={cn('w-4 h-4 transition-transform', sidebarCollapsed && 'rotate-180')} />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {/* Main Navigation */}
        <div className="space-y-1">
          {!sidebarCollapsed && (
            <p className="px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
              Main Menu
            </p>
          )}
          {navItems.map((item) => {
            if (item.permission && !hasPermission(item.permission)) return null
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    isActive ? 'sidebar-link-active' : 'sidebar-link',
                    sidebarCollapsed && 'justify-center px-3'
                  )
                }
                title={sidebarCollapsed ? item.label : undefined}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {!sidebarCollapsed && <span>{item.label}</span>}
              </NavLink>
            )
          })}
        </div>

        {/* Settings */}
        <div className="pt-6 space-y-1">
          {!sidebarCollapsed && (
            <p className="px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
              Administration
            </p>
          )}
          {settingsItems.map((item) => {
            if (item.permission && !hasPermission(item.permission)) return null
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    isActive ? 'sidebar-link-active' : 'sidebar-link',
                    sidebarCollapsed && 'justify-center px-3'
                  )
                }
                title={sidebarCollapsed ? item.label : undefined}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {!sidebarCollapsed && <span>{item.label}</span>}
              </NavLink>
            )
          })}
        </div>
      </nav>

      {/* User Section */}
      <div className="border-t border-slate-100 p-3">
        <div className={cn(
          'flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 transition-colors cursor-pointer',
          sidebarCollapsed && 'justify-center p-2'
        )}>
          <div className={cn('w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-semibold', avatarColor)}>
            {getInitials(userName)}
          </div>
          {!sidebarCollapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-700 truncate">{userName}</p>
              <p className="text-xs text-slate-400 truncate">{user?.tenant_context?.role_name}</p>
            </div>
          )}
        </div>
        
        <div className={cn('flex gap-1 mt-2', sidebarCollapsed && 'flex-col')}>
          <button
            onClick={() => navigate('/profile')}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-500 hover:bg-slate-100 transition-colors"
            title="Profile"
          >
            <User className="w-4 h-4" />
            {!sidebarCollapsed && <span>Profile</span>}
          </button>
          <button
            onClick={handleLogout}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm text-rose-500 hover:bg-rose-50 transition-colors"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
            {!sidebarCollapsed && <span>Logout</span>}
          </button>
        </div>
      </div>
    </motion.aside>
  )
}
