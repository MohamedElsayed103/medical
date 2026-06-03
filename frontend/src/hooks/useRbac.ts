import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { rbacService } from '@/services/api'
import toast from 'react-hot-toast'

export const rbacKeys = {
  me: () => ['rbac', 'me'] as const,
  roles: () => ['rbac', 'roles'] as const,
  role: (id: string) => ['rbac', 'roles', id] as const,
  permissions: () => ['rbac', 'permissions'] as const,
  users: () => ['rbac', 'users'] as const,
  user: (id: string) => ['rbac', 'users', id] as const,
  invitations: () => ['rbac', 'invitations'] as const,
}

export function useRbacMe() {
  return useQuery({
    queryKey: rbacKeys.me(),
    queryFn: () => rbacService.getMe(),
  })
}

export function useRoles(params?: Record<string, string>) {
  return useQuery({
    queryKey: [...rbacKeys.roles(), params],
    queryFn: () => rbacService.getRoles(params),
  })
}

export function usePermissions(params?: Record<string, string>) {
  return useQuery({
    queryKey: [...rbacKeys.permissions(), params],
    queryFn: () => rbacService.getPermissions(params),
  })
}

export function useCreateRole() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; description?: string; permission_ids?: string[] }) =>
      rbacService.createRole(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rbacKeys.roles() })
      toast.success('Role created')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to create role')
    },
  })
}

export function useUpdateRole() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<{ name: string; description: string; permission_ids: string[] }> }) =>
      rbacService.updateRole(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: rbacKeys.roles() })
      queryClient.invalidateQueries({ queryKey: rbacKeys.role(id) })
      toast.success('Role updated')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to update role')
    },
  })
}

export function useDeleteRole() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => rbacService.deleteRole(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rbacKeys.roles() })
      toast.success('Role deleted')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to delete role')
    },
  })
}

export function useTenantUsers(params?: Record<string, string>) {
  return useQuery({
    queryKey: [...rbacKeys.users(), params],
    queryFn: () => rbacService.getUsers(params),
  })
}

export function useUpdateTenantUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<{ role_id: string; status: string }> }) =>
      rbacService.updateUser(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rbacKeys.users() })
      toast.success('User updated')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to update user')
    },
  })
}

export function useDeleteTenantUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => rbacService.deleteUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rbacKeys.users() })
      toast.success('User removed')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to remove user')
    },
  })
}

export function useInvitations(params?: Record<string, string>) {
  return useQuery({
    queryKey: [...rbacKeys.invitations(), params],
    queryFn: () => rbacService.getInvitations(params),
  })
}

export function useCreateInvitation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { email: string; role_id: string }) =>
      rbacService.createInvitation(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rbacKeys.invitations() })
      toast.success('Invitation sent')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || error?.response?.data?.email?.[0] || 'Failed to send invitation')
    },
  })
}

export function useCancelInvitation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => rbacService.cancelInvitation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rbacKeys.invitations() })
      toast.success('Invitation cancelled')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to cancel invitation')
    },
  })
}
