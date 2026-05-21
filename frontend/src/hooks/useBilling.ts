import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { billingService } from '@/services/api'
import type { InvoiceCreateRequest, PaymentInput } from '@/types'
import toast from 'react-hot-toast'

export const billingKeys = {
  all: ['billing'] as const,
  lists: () => [...billingKeys.all, 'list'] as const,
  list: (params: Record<string, string | number>) => [...billingKeys.lists(), params] as const,
  details: () => [...billingKeys.all, 'detail'] as const,
  detail: (id: string) => [...billingKeys.details(), id] as const,
  summary: () => [...billingKeys.all, 'summary'] as const,
}

export function useInvoices(params: Record<string, string | number> = {}) {
  return useQuery({
    queryKey: billingKeys.list(params),
    queryFn: () => billingService.getAll(params),
  })
}

export function useInvoice(id: string) {
  return useQuery({
    queryKey: billingKeys.detail(id),
    queryFn: () => billingService.getById(id),
    enabled: !!id,
  })
}

export function useBillingSummary() {
  return useQuery({
    queryKey: billingKeys.summary(),
    queryFn: () => billingService.getSummary(),
  })
}

export function useCreateInvoice() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: InvoiceCreateRequest) => billingService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: billingKeys.lists() })
      queryClient.invalidateQueries({ queryKey: billingKeys.summary() })
      toast.success('Invoice created')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to create invoice')
    },
  })
}

export function useInvoiceAction() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, action }: { id: string; action: 'finalize' | 'cancel' | 'void' }) => {
      switch (action) {
        case 'finalize': return billingService.finalize(id)
        case 'cancel': return billingService.cancel(id)
        case 'void': return billingService.void(id)
      }
    },
    onSuccess: (_, { id, action }) => {
      queryClient.invalidateQueries({ queryKey: billingKeys.lists() })
      queryClient.invalidateQueries({ queryKey: billingKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: billingKeys.summary() })
      toast.success(`Invoice ${action === 'void' ? 'voided' : action + 'ed'}`)
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Action failed')
    },
  })
}

export function useRecordPayment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: PaymentInput }) =>
      billingService.pay(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: billingKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: billingKeys.lists() })
      queryClient.invalidateQueries({ queryKey: billingKeys.summary() })
      toast.success('Payment recorded')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to record payment')
    },
  })
}
