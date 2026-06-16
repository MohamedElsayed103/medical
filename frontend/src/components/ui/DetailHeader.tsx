import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import StatusChip from './StatusChip'

interface Chip { label?: string; status?: string | null }

interface Props {
  backTo: string
  title: ReactNode
  icon?: ReactNode
  subtitle?: ReactNode
  chips?: Chip[]
  actions?: ReactNode
}

/**
 * Standard detail-page header: back link → title (+ icon) + status chips,
 * subtitle line, and right-aligned actions. Used across all detail pages.
 */
export default function DetailHeader({ backTo, title, icon, subtitle, chips, actions }: Props) {
  return (
    <div className="flex items-start gap-4">
      <Link to={backTo} className="p-2 hover:bg-gray-100 rounded-lg mt-1 shrink-0">
        <ArrowLeft className="w-4 h-4" />
      </Link>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            {icon}
            {title}
          </h1>
          {chips?.map((c, i) =>
            c.status ? <StatusChip key={i} status={c.status} /> :
            c.label ? <span key={i} className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600 capitalize">{c.label}</span> : null
          )}
        </div>
        {subtitle && <p className="text-gray-500 text-sm mt-1">{subtitle}</p>}
      </div>
      {actions && <div className="flex gap-2 shrink-0 flex-wrap">{actions}</div>}
    </div>
  )
}
