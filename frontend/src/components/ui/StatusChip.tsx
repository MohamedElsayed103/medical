import { cn } from '@/lib/utils'

/**
 * Centralized status → color mapping for every domain status in the app.
 * Replaces the per-page copy-pasted color maps.
 */
const STATUS_COLORS: Record<string, string> = {
  // generic
  active: 'bg-green-100 text-green-700',
  inactive: 'bg-gray-100 text-gray-600',
  pending: 'bg-yellow-100 text-yellow-800',
  in_progress: 'bg-purple-100 text-purple-700',
  completed: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-700',
  // appointments
  scheduled: 'bg-blue-100 text-blue-700',
  confirmed: 'bg-green-100 text-green-700',
  no_show: 'bg-amber-100 text-amber-700',
  // lab
  collected: 'bg-blue-100 text-blue-700',
  // radiology
  ordered: 'bg-blue-100 text-blue-800',
  awaiting_report: 'bg-purple-100 text-purple-800',
  // billing
  draft: 'bg-gray-100 text-gray-700',
  issued: 'bg-blue-100 text-blue-800',
  sent: 'bg-indigo-100 text-indigo-800',
  paid: 'bg-green-100 text-green-700',
  partially_paid: 'bg-yellow-100 text-yellow-800',
  overdue: 'bg-red-100 text-red-700',
  voided: 'bg-gray-200 text-gray-500',
  // prescriptions / pharmacy
  dispensed: 'bg-blue-100 text-blue-700',
  in_stock: 'bg-green-100 text-green-700',
  low_stock: 'bg-amber-100 text-amber-700',
  out_of_stock: 'bg-red-100 text-red-700',
  // flags / severity
  normal: 'bg-green-100 text-green-700',
  low: 'bg-blue-100 text-blue-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
  // claims
  denied: 'bg-red-100 text-red-700',
  appealed: 'bg-amber-100 text-amber-700',
  accepted: 'bg-green-100 text-green-700',
  submitted: 'bg-blue-100 text-blue-700',
}

export function statusColor(status?: string | null): string {
  if (!status) return 'bg-gray-100 text-gray-600'
  return STATUS_COLORS[status] ?? 'bg-gray-100 text-gray-700'
}

interface Props {
  status?: string | null
  className?: string
}

export default function StatusChip({ status, className }: Props) {
  if (!status) return null
  return (
    <span className={cn('px-2.5 py-0.5 rounded-full text-xs font-medium capitalize', statusColor(status), className)}>
      {status.replace(/_/g, ' ')}
    </span>
  )
}
