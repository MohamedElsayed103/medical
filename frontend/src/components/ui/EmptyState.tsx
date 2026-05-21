import { AlertTriangle } from 'lucide-react'
import Button from './Button'

interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
}

export default function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
        {icon || <AlertTriangle className="w-7 h-7 text-slate-400" />}
      </div>
      <h3 className="text-lg font-semibold text-slate-700">{title}</h3>
      {description && (
        <p className="mt-2 text-sm text-slate-500 max-w-sm">{description}</p>
      )}
      {action && (
        <div className="mt-6">
          <Button onClick={action.onClick}>{action.label}</Button>
        </div>
      )}
    </div>
  )
}
