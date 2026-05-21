import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { appointmentsService } from '@/services/api'
import type { BookAppointmentRequest } from '@/types'
import toast from 'react-hot-toast'

export const appointmentKeys = {
  all: ['appointments'] as const,
  lists: () => [...appointmentKeys.all, 'list'] as const,
  list: (params: Record<string, string | number>) => [...appointmentKeys.lists(), params] as const,
  details: () => [...appointmentKeys.all, 'detail'] as const,
  detail: (id: string) => [...appointmentKeys.details(), id] as const,
  slots: (params: { doctor_id: string; date: string }) => [...appointmentKeys.all, 'slots', params] as const,
  doctors: () => [...appointmentKeys.all, 'doctors'] as const,
}

export function useAppointments(params: Record<string, string | number> = {}) {
  return useQuery({
    queryKey: appointmentKeys.list(params),
    queryFn: () => appointmentsService.getAll(params),
  })
}

export function useAppointment(id: string) {
  return useQuery({
    queryKey: appointmentKeys.detail(id),
    queryFn: () => appointmentsService.getById(id),
    enabled: !!id,
  })
}

export function useDoctors(params: Record<string, string | number> = {}) {
  return useQuery({
    queryKey: [...appointmentKeys.doctors(), params],
    queryFn: () => appointmentsService.getDoctors(params),
  })
}

export function useAvailableSlots(params: { doctor_id: string; date: string; duration_minutes?: number }) {
  return useQuery({
    queryKey: appointmentKeys.slots(params),
    queryFn: () => appointmentsService.getAvailableSlots(params),
    enabled: !!params.doctor_id && !!params.date,
  })
}

export function useBookAppointment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: BookAppointmentRequest) => appointmentsService.book(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: appointmentKeys.lists() })
      toast.success('Appointment booked successfully')
    },
    onError: (error: any) => {
      const msg = error?.response?.data?.detail || error?.response?.data?.non_field_errors?.[0] || 'Failed to book appointment'
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
    },
  })
}

export function useRescheduleAppointment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { scheduled_at: string; duration_minutes?: number } }) =>
      appointmentsService.reschedule(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: appointmentKeys.lists() })
      queryClient.invalidateQueries({ queryKey: appointmentKeys.detail(id) })
      toast.success('Appointment rescheduled')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to reschedule')
    },
  })
}

export function useAppointmentAction() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, action, reason }: { id: string; action: 'confirm' | 'start' | 'complete' | 'cancel' | 'no-show'; reason?: string }) => {
      switch (action) {
        case 'confirm': return appointmentsService.confirm(id)
        case 'start': return appointmentsService.start(id)
        case 'complete': return appointmentsService.complete(id)
        case 'cancel': return appointmentsService.cancel(id, reason)
        case 'no-show': return appointmentsService.noShow(id)
      }
    },
    onSuccess: (_, { action }) => {
      queryClient.invalidateQueries({ queryKey: appointmentKeys.lists() })
      toast.success(`Appointment ${action === 'no-show' ? 'marked as no-show' : action + 'ed'}`)
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Action failed')
    },
  })
}
