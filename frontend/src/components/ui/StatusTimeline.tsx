import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Props {
  /** Ordered list of FSM steps (use human labels). */
  steps: string[]
  /** The current status (must be one of `steps`, else nothing is marked done). */
  current?: string | null
  /** If the entity is in a terminal/aborted state (e.g. cancelled), show it muted. */
  aborted?: boolean
  abortedLabel?: string
}

/**
 * Horizontal stepper for FSM-driven entities (lab order, radiology order,
 * invoice, appointment). Steps up to and including `current` are marked done.
 */
export default function StatusTimeline({ steps, current, aborted, abortedLabel = 'Cancelled' }: Props) {
  if (aborted) {
    return (
      <div className="flex items-center gap-2 text-sm text-red-600">
        <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
        {abortedLabel}
      </div>
    )
  }
  const currentIdx = current ? steps.findIndex(s => s.toLowerCase().replace(/\s+/g, '_') === current.toLowerCase().replace(/\s+/g, '_')) : -1

  return (
    <div className="flex items-center w-full">
      {steps.map((step, i) => {
        const done = i < currentIdx
        const active = i === currentIdx
        return (
          <div key={step} className="flex items-center flex-1 last:flex-none">
            <div className="flex flex-col items-center">
              <div className={cn(
                'w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold border-2',
                done && 'bg-primary-600 border-primary-600 text-white',
                active && 'bg-primary-100 border-primary-600 text-primary-700',
                !done && !active && 'bg-white border-gray-200 text-gray-400',
              )}>
                {done ? <Check className="w-3.5 h-3.5" /> : i + 1}
              </div>
              <span className={cn('mt-1 text-[11px] whitespace-nowrap', active ? 'text-primary-700 font-medium' : 'text-gray-400')}>
                {step}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div className={cn('flex-1 h-0.5 mx-1 -mt-5', i < currentIdx ? 'bg-primary-600' : 'bg-gray-200')} />
            )}
          </div>
        )
      })}
    </div>
  )
}
