import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsService } from '@/services/api'
import toast from 'react-hot-toast'
import type { NotificationPreferences } from '@/types'

export const notificationKeys = {
  all: ['notifications'] as const,
  lists: () => [...notificationKeys.all, 'list'] as const,
  list: (params: Record<string, string | number>) => [...notificationKeys.lists(), params] as const,
  preferences: () => [...notificationKeys.all, 'preferences'] as const,
  unreadCount: () => [...notificationKeys.all, 'unread-count'] as const,
}

export function useNotifications(params: Record<string, string | number> = {}) {
  return useQuery({
    queryKey: notificationKeys.list(params),
    queryFn: () => notificationsService.getAll(params),
    refetchInterval: 30000, // Poll every 30s
  })
}

export function useUnreadCount() {
  return useQuery({
    queryKey: notificationKeys.unreadCount(),
    queryFn: async () => {
      const data = await notificationsService.getAll({ is_read: 'false', page_size: 1 })
      return data.count
    },
    refetchInterval: 15000,
  })
}

export function useMarkAsRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => notificationsService.markAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.lists() })
      queryClient.invalidateQueries({ queryKey: notificationKeys.unreadCount() })
    },
  })
}

export function useMarkAllAsRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => notificationsService.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.lists() })
      queryClient.invalidateQueries({ queryKey: notificationKeys.unreadCount() })
      toast.success('All notifications marked as read')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to mark all as read')
    },
  })
}

export function useNotificationPreferences() {
  return useQuery({
    queryKey: notificationKeys.preferences(),
    queryFn: () => notificationsService.getPreferences(),
  })
}

export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<NotificationPreferences>) =>
      notificationsService.updatePreferences(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.preferences() })
      toast.success('Preferences updated')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to update preferences')
    },
  })
}
