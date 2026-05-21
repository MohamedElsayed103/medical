import { useQuery } from '@tanstack/react-query'
import { auditService } from '@/services/api'

export const auditKeys = {
  all: ['audit-logs'] as const,
  lists: () => [...auditKeys.all, 'list'] as const,
  list: (params: Record<string, string | number>) => [...auditKeys.lists(), params] as const,
}

export function useAuditLogs(params: Record<string, string | number> = {}) {
  return useQuery({
    queryKey: auditKeys.list(params),
    queryFn: () => auditService.getAll(params),
  })
}
