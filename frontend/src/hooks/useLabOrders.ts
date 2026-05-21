import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { labOrdersService } from '@/services/api'
import type { LabOrderCreateRequest, TestResultInput } from '@/types'
import toast from 'react-hot-toast'

export const labOrderKeys = {
  all: ['lab-orders'] as const,
  lists: () => [...labOrderKeys.all, 'list'] as const,
  list: (params: Record<string, string | number>) => [...labOrderKeys.lists(), params] as const,
  details: () => [...labOrderKeys.all, 'detail'] as const,
  detail: (id: string) => [...labOrderKeys.details(), id] as const,
}

export function useLabOrders(params: Record<string, string | number> = {}) {
  return useQuery({
    queryKey: labOrderKeys.list(params),
    queryFn: () => labOrdersService.getAll(params),
  })
}

export function useLabOrder(id: string) {
  return useQuery({
    queryKey: labOrderKeys.detail(id),
    queryFn: () => labOrdersService.getById(id),
    enabled: !!id,
  })
}

export function useCreateLabOrder() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: LabOrderCreateRequest) => labOrdersService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: labOrderKeys.lists() })
      toast.success('Lab order created')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to create lab order')
    },
  })
}

export function useLabOrderAction() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, action }: { id: string; action: 'collect' | 'in_progress' | 'complete' | 'cancel' }) => {
      switch (action) {
        case 'collect': return labOrdersService.collect(id)
        case 'in_progress': return labOrdersService.inProgress(id)
        case 'complete': return labOrdersService.complete(id)
        case 'cancel': return labOrdersService.cancel(id)
      }
    },
    onSuccess: (_, { id, action }) => {
      queryClient.invalidateQueries({ queryKey: labOrderKeys.lists() })
      queryClient.invalidateQueries({ queryKey: labOrderKeys.detail(id) })
      const messages: Record<string, string> = {
        collect: 'Sample collected',
        in_progress: 'Processing started',
        complete: 'Order completed',
        cancel: 'Order cancelled',
      }
      toast.success(messages[action])
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Action failed')
    },
  })
}

export function useRecordTestResult() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ orderId, testId, data }: { orderId: string; testId: string; data: TestResultInput }) =>
      labOrdersService.recordResult(orderId, testId, data),
    onSuccess: (_, { orderId }) => {
      queryClient.invalidateQueries({ queryKey: labOrderKeys.detail(orderId) })
      toast.success('Result recorded')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to record result')
    },
  })
}

export function useVerifyTestResult() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ orderId, testId }: { orderId: string; testId: string }) =>
      labOrdersService.verifyResult(orderId, testId),
    onSuccess: (_, { orderId }) => {
      queryClient.invalidateQueries({ queryKey: labOrderKeys.detail(orderId) })
      toast.success('Result verified')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to verify result')
    },
  })
}
