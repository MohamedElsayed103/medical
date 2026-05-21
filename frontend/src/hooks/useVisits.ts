import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { visitsService } from '@/services/api'
import type { VisitCreateRequest, VitalsCreateRequest, DiagnosisCreateRequest } from '@/types'
import toast from 'react-hot-toast'

export const visitKeys = {
  all: ['visits'] as const,
  lists: () => [...visitKeys.all, 'list'] as const,
  list: (params: Record<string, string | number>) => [...visitKeys.lists(), params] as const,
  details: () => [...visitKeys.all, 'detail'] as const,
  detail: (id: string) => [...visitKeys.details(), id] as const,
}

export function useVisits(params: Record<string, string | number> = {}) {
  return useQuery({
    queryKey: visitKeys.list(params),
    queryFn: () => visitsService.getAll(params),
  })
}

export function useVisit(id: string) {
  return useQuery({
    queryKey: visitKeys.detail(id),
    queryFn: () => visitsService.getById(id),
    enabled: !!id,
  })
}

export function useCreateVisit() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: VisitCreateRequest) => visitsService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: visitKeys.lists() })
      toast.success('Visit record created')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to create visit')
    },
  })
}

export function useUpdateVisit() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<VisitCreateRequest> }) =>
      visitsService.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: visitKeys.lists() })
      queryClient.invalidateQueries({ queryKey: visitKeys.detail(id) })
      toast.success('Visit updated')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to update visit')
    },
  })
}

export function useSignVisit() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => visitsService.sign(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: visitKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: visitKeys.lists() })
      toast.success('Visit signed and finalized')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to sign visit')
    },
  })
}

export function useAddVitals() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ visitId, data }: { visitId: string; data: VitalsCreateRequest }) =>
      visitsService.addVitals(visitId, data),
    onSuccess: (_, { visitId }) => {
      queryClient.invalidateQueries({ queryKey: visitKeys.detail(visitId) })
      toast.success('Vitals recorded')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to record vitals')
    },
  })
}

export function useAddDiagnosis() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ visitId, data }: { visitId: string; data: DiagnosisCreateRequest }) =>
      visitsService.addDiagnosis(visitId, data),
    onSuccess: (_, { visitId }) => {
      queryClient.invalidateQueries({ queryKey: visitKeys.detail(visitId) })
      toast.success('Diagnosis added')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to add diagnosis')
    },
  })
}
