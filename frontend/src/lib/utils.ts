import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { format, parseISO, isValid } from 'date-fns'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Safely format a date string. Returns fallback if date is invalid.
 */
export function safeFormat(dateStr: string | null | undefined, fmt: string, fallback = '—'): string {
  if (!dateStr) return fallback
  try {
    const d = parseISO(dateStr)
    return isValid(d) ? format(d, fmt) : fallback
  } catch {
    return fallback
  }
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function formatDateTime(date: string | Date): string {
  return new Date(date).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatTime(date: string | Date): string {
  return new Date(date).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * Format a time in the CLINIC clock (UTC), not the browser's timezone.
 *
 * Appointment/availability times are stored and authored as UTC wall-clock
 * (the backend runs with TIME_ZONE="UTC" and doctor availability is naive
 * UTC). Displaying them with the browser's local timezone would shift e.g.
 * a 09:00 window to "2:00 PM" for a UTC+5 user. These helpers keep the
 * displayed time identical to what the doctor configured.
 */
export function formatClinicTime(dateStr: string | null | undefined, fallback = '—'): string {
  if (!dateStr) return fallback
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return fallback
  return new Intl.DateTimeFormat('en-US', {
    timeZone: 'UTC', hour: 'numeric', minute: '2-digit', hour12: true,
  }).format(d)
}

export function formatClinicDateTime(dateStr: string | null | undefined, fallback = '—'): string {
  if (!dateStr) return fallback
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return fallback
  return new Intl.DateTimeFormat('en-US', {
    timeZone: 'UTC', month: 'short', day: 'numeric', year: 'numeric',
    hour: 'numeric', minute: '2-digit', hour12: true,
  }).format(d)
}

/** UTC calendar day (yyyy-mm-dd) for an ISO datetime — for date bucketing. */
export function clinicDayKey(dateStr: string | null | undefined): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return ''
  return d.toISOString().slice(0, 10)
}

export function getInitials(name: string): string {
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str
  return str.slice(0, length) + '...'
}

export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
}

export function generateAvatarColor(name: string): string {
  const colors = [
    'bg-primary-500',
    'bg-secondary-500',
    'bg-emerald-500',
    'bg-sky-500',
    'bg-amber-500',
    'bg-rose-500',
    'bg-violet-500',
    'bg-cyan-500',
  ]
  const index = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return colors[index % colors.length]
}
