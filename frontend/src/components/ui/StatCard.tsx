import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import type { LucideIcon } from 'lucide-react'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  trend?: number
  trendLabel?: string
  color?: 'primary' | 'secondary' | 'emerald' | 'amber' | 'rose' | 'sky'
  delay?: number
}

const colorMap = {
  primary: {
    bg: 'bg-primary-50',
    icon: 'text-primary-600',
    border: 'border-primary-100',
  },
  secondary: {
    bg: 'bg-secondary-50',
    icon: 'text-secondary-600',
    border: 'border-secondary-100',
  },
  emerald: {
    bg: 'bg-emerald-50',
    icon: 'text-emerald-600',
    border: 'border-emerald-100',
  },
  amber: {
    bg: 'bg-amber-50',
    icon: 'text-amber-600',
    border: 'border-amber-100',
  },
  rose: {
    bg: 'bg-rose-50',
    icon: 'text-rose-600',
    border: 'border-rose-100',
  },
  sky: {
    bg: 'bg-sky-50',
    icon: 'text-sky-600',
    border: 'border-sky-100',
  },
}

export default function StatCard({ title, value, icon: Icon, trend, trendLabel, color = 'primary', delay = 0 }: StatCardProps) {
  const colors = colorMap[color]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className="stat-card group"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="mt-2 text-3xl font-bold text-slate-800">{value}</p>
          
          {trend !== undefined && (
            <div className="flex items-center gap-1.5 mt-3">
              {trend >= 0 ? (
                <TrendingUp className="w-4 h-4 text-emerald-500" />
              ) : (
                <TrendingDown className="w-4 h-4 text-rose-500" />
              )}
              <span className={cn(
                'text-sm font-medium',
                trend >= 0 ? 'text-emerald-600' : 'text-rose-600'
              )}>
                {trend >= 0 ? '+' : ''}{trend}%
              </span>
              {trendLabel && (
                <span className="text-xs text-slate-400">{trendLabel}</span>
              )}
            </div>
          )}
        </div>
        
        <div className={cn(
          'w-12 h-12 rounded-xl flex items-center justify-center border transition-transform group-hover:scale-110',
          colors.bg, colors.border
        )}>
          <Icon className={cn('w-6 h-6', colors.icon)} />
        </div>
      </div>
    </motion.div>
  )
}
