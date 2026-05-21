import { useState } from 'react'
import { Building2, ChevronDown, Check } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { cn } from '@/lib/utils'
import { motion, AnimatePresence } from 'framer-motion'

export default function TenantSwitcher() {
  const { user, currentTenant, setCurrentTenant } = useAuthStore()
  const [open, setOpen] = useState(false)

  if (!user?.tenants || user.tenants.length <= 1) return null

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 rounded-xl border border-slate-200 hover:border-primary-300 hover:bg-primary-50/50 transition-all text-sm"
      >
        <Building2 className="w-4 h-4 text-primary-600" />
        <span className="font-medium text-slate-700 max-w-[120px] truncate">
          {currentTenant?.tenant_name || 'Select Tenant'}
        </span>
        <ChevronDown className={cn('w-4 h-4 text-slate-400 transition-transform', open && 'rotate-180')} />
      </button>

      <AnimatePresence>
        {open && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
            <motion.div
              initial={{ opacity: 0, y: -5, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -5, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="absolute right-0 top-full mt-2 w-64 bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden z-50"
            >
              <div className="p-2">
                <p className="px-3 py-2 text-xs font-semibold text-slate-400 uppercase">
                  Switch Organization
                </p>
                {user.tenants.map((tenant) => (
                  <button
                    key={tenant.tenant_id}
                    onClick={() => {
                      setCurrentTenant(tenant)
                      setOpen(false)
                    }}
                    className={cn(
                      'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-left',
                      currentTenant?.tenant_id === tenant.tenant_id
                        ? 'bg-primary-50 text-primary-700'
                        : 'hover:bg-slate-50 text-slate-700'
                    )}
                  >
                    <div className="w-8 h-8 rounded-lg bg-primary-100 flex items-center justify-center">
                      <Building2 className="w-4 h-4 text-primary-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{tenant.tenant_name}</p>
                      <p className="text-xs text-slate-400 truncate">{tenant.tenant_slug}</p>
                    </div>
                    {currentTenant?.tenant_id === tenant.tenant_id && (
                      <Check className="w-4 h-4 text-primary-600" />
                    )}
                  </button>
                ))}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
