import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { patientsService } from '@/services/api'
import type { PatientCreateRequest } from '@/types'
import toast from 'react-hot-toast'

export const patientKeys = {
  all: ['patients'] as const,
  lists: () => [...patientKeys.all, 'list'] as const,
  list: (params: Record<string, string | number>) => [...patientKeys.lists(), params] as const,
  details: () => [...patientKeys.all, 'detail'] as const,
  detail: (id: string) => [...patientKeys.details(), id] as const,
  visits: (id: string) => [...patientKeys.detail(id), 'visits'] as const,
  prescriptions: (id: string) => [...patientKeys.detail(id), 'prescriptions'] as const,
  labResults: (id: string) => [...patientKeys.detail(id), 'lab-results'] as const,
  invoices: (id: string) => [...patientKeys.detail(id), 'invoices'] as const,
}

export function usePatients(params: Record<string, string | number> = {}) {
  return useQuery({
    queryKey: patientKeys.list(params),
    queryFn: () => patientsService.getAll(params),
  })
}

export function usePatient(id: string) {
  return useQuery({
    queryKey: patientKeys.detail(id),
    queryFn: () => patientsService.getById(id),
    enabled: !!id,
  })
}

export function usePatientVisits(id: string, params: Record<string, string | number> = {}) {
  return useQuery({
    queryKey: [...patientKeys.visits(id), params],
    queryFn: () => patientsService.getVisits(id, params),
    enabled: !!id,
  })
}

export function usePatientPrescriptions(id: string, params: Record<string, string | number> = {}) {
  return useQuery({
    queryKey: [...patientKeys.prescriptions(id), params],
    queryFn: () => patientsService.getPrescriptions(id, params),
    enabled: !!id,
  })
}

export function usePatientLabResults(id: string, params: Record<string, string | number> = {}) {
  return useQuery({
    queryKey: [...patientKeys.labResults(id), params],
    queryFn: () => patientsService.getLabResults(id, params),
    enabled: !!id,
  })
}

export function usePatientInvoices(id: string, params: Record<string, string | number> = {}) {
  return useQuery({
    queryKey: [...patientKeys.invoices(id), params],
    queryFn: () => patientsService.getInvoices(id, params),
    enabled: !!id,
  })
}

export function useCreatePatient() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: PatientCreateRequest) => patientsService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: patientKeys.lists() })
      toast.success('Patient created successfully')
    },
    onError: (error: any) => {
      const msg = error?.response?.data?.detail || error?.response?.data?.message || 'Failed to create patient'
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
    },
  })
}

export function useUpdatePatient() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<PatientCreateRequest> }) =>
      patientsService.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: patientKeys.lists() })
      queryClient.invalidateQueries({ queryKey: patientKeys.detail(id) })
      toast.success('Patient updated successfully')
    },
    onError: (error: any) => {
      const msg = error?.response?.data?.detail || 'Failed to update patient'
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
    },
  })
}

export function useDeletePatient() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => patientsService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: patientKeys.lists() })
      toast.success('Patient deleted successfully')
    },
    onError: (error: any) => {
      const msg = error?.response?.data?.detail || 'Failed to delete patient'
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
    },
  })
}
