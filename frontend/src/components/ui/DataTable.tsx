import { cn } from '@/lib/utils'
import { motion } from 'framer-motion'

interface DataTableProps<T> {
  columns: {
    key: string
    label: string
    render?: (item: T) => React.ReactNode
    className?: string
  }[]
  data: T[]
  onRowClick?: (item: T) => void
  loading?: boolean
  emptyMessage?: string
}

export default function DataTable<T extends { id: string }>({
  columns,
  data,
  onRowClick,
  loading = false,
  emptyMessage = 'No data found',
}: DataTableProps<T>) {
  if (loading) {
    return (
      <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
        <div className="animate-pulse">
          <div className="h-12 bg-slate-50 border-b" />
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-16 border-b border-slate-50 flex items-center px-6 gap-4">
              <div className="h-4 bg-slate-100 rounded w-1/4" />
              <div className="h-4 bg-slate-100 rounded w-1/3" />
              <div className="h-4 bg-slate-100 rounded w-1/5" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-slate-100 p-12 text-center">
        <p className="text-slate-400 text-sm">{emptyMessage}</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-slate-50/80">
              {columns.map((col) => (
                <th key={col.key} className={cn('table-header', col.className)}>
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data.map((item, index) => (
              <motion.tr
                key={item.id}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.03 }}
                onClick={() => onRowClick?.(item)}
                className={cn(
                  'transition-colors',
                  onRowClick && 'cursor-pointer hover:bg-primary-50/50'
                )}
              >
                {columns.map((col) => (
                  <td key={col.key} className={cn('table-cell', col.className)}>
                    {col.render
                      ? col.render(item)
                      : String((item as Record<string, unknown>)[col.key] ?? '')
                    }
                  </td>
                ))}
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
