import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { prescriptionsService } from '@/services/api'
import type { PrescriptionCreateRequest } from '@/types'
import toast from 'react-hot-toast'

export const prescriptionKeys = {
  all: ['prescriptions'] as const,
  lists: () => [...prescriptionKeys.all, 'list'] as const,
  list: (params: Record<string, string | number>) => [...prescriptionKeys.lists(), params] as const,
  details: () => [...prescriptionKeys.all, 'detail'] as const,
  detail: (id: string) => [...prescriptionKeys.details(), id] as const,
  medications: () => ['medications'] as const,
}

export function usePrescriptions(params: Record<string, string | number> = {}) {
  return useQuery({
    queryKey: prescriptionKeys.list(params),
    queryFn: () => prescriptionsService.getAll(params),
  })
}

export function usePrescription(id: string) {
  return useQuery({
    queryKey: prescriptionKeys.detail(id),
    queryFn: () => prescriptionsService.getById(id),
    enabled: !!id,
  })
}

export function useMedications(params: Record<string, string | number> = {}) {
  return useQuery({
    queryKey: [...prescriptionKeys.medications(), params],
    queryFn: () => prescriptionsService.getMedications(params),
  })
}

export function useCreatePrescription() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: PrescriptionCreateRequest) => prescriptionsService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: prescriptionKeys.lists() })
      toast.success('Prescription created')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to create prescription')
    },
  })
}

export function useDeletePrescription() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => prescriptionsService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: prescriptionKeys.lists() })
      toast.success('Prescription deleted')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to delete prescription')
    },
  })
}
