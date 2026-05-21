import { cn } from '@/lib/utils'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'success' | 'warning' | 'danger' | 'info' | 'neutral'
  className?: string
}

export default function Badge({ children, variant = 'neutral', className }: BadgeProps) {
  const variants = {
    success: 'badge-success',
    warning: 'badge-warning',
    danger: 'badge-danger',
    info: 'badge-info',
    neutral: 'badge-neutral',
  }

  return (
    <span className={cn(variants[variant], className)}>
      {children}
    </span>
  )
}

export function StatusBadge({ status }: { status: string }) {
  const statusMap: Record<string, { variant: BadgeProps['variant']; label: string }> = {
    active: { variant: 'success', label: 'Active' },
    ACTIVE: { variant: 'success', label: 'Active' },
    completed: { variant: 'success', label: 'Completed' },
    COMPLETED: { variant: 'success', label: 'Completed' },
    confirmed: { variant: 'success', label: 'Confirmed' },
    CONFIRMED: { variant: 'success', label: 'Confirmed' },
    paid: { variant: 'success', label: 'Paid' },
    PAID: { variant: 'success', label: 'Paid' },
    pending: { variant: 'warning', label: 'Pending' },
    PENDING: { variant: 'warning', label: 'Pending' },
    scheduled: { variant: 'info', label: 'Scheduled' },
    SCHEDULED: { variant: 'info', label: 'Scheduled' },
    in_progress: { variant: 'info', label: 'In Progress' },
    IN_PROGRESS: { variant: 'info', label: 'In Progress' },
    cancelled: { variant: 'danger', label: 'Cancelled' },
    CANCELLED: { variant: 'danger', label: 'Cancelled' },
    overdue: { variant: 'danger', label: 'Overdue' },
    OVERDUE: { variant: 'danger', label: 'Overdue' },
    expired: { variant: 'danger', label: 'Expired' },
    EXPIRED: { variant: 'danger', label: 'Expired' },
    inactive: { variant: 'neutral', label: 'Inactive' },
    INACTIVE: { variant: 'neutral', label: 'Inactive' },
    accepted: { variant: 'success', label: 'Accepted' },
    ACCEPTED: { variant: 'success', label: 'Accepted' },
  }

  const config = statusMap[status] || { variant: 'neutral' as const, label: status }
  
  return <Badge variant={config.variant}>{config.label}</Badge>
}
