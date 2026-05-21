import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, AuthTokens, TenantMapping, MeResponse } from '@/types'

interface AuthState {
  user: User | null
  tokens: AuthTokens | null
  currentTenant: TenantMapping | null
  permissions: string[]
  roleName: string | null
  isAuthenticated: boolean
  
  setUser: (user: User) => void
  setTokens: (tokens: AuthTokens) => void
  setCurrentTenant: (tenant: TenantMapping) => void
  setRbacContext: (me: MeResponse) => void
  login: (user: User, tokens: AuthTokens, tenants?: TenantMapping[]) => void
  logout: () => void
  hasPermission: (permission: string) => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      tokens: null,
      currentTenant: null,
      permissions: [],
      roleName: null,
      isAuthenticated: false,

      setUser: (user) => set({ user }),
      
      setTokens: (tokens) => set({ tokens }),
      
      setCurrentTenant: (tenant) => set({ currentTenant: tenant }),

      setRbacContext: (me: any) => {
        set({
          permissions: me.permissions || [],
          roleName: me.role_name || me.role?.name || null,
        })
      },
      
      login: (user, tokens, tenants?) => {
        const currentTenant = tenants?.[0] || user.tenant_mappings?.[0] || user.tenants?.[0] || null
        set({ user, tokens, currentTenant, isAuthenticated: true })
      },
      
      logout: () => {
        set({ user: null, tokens: null, currentTenant: null, permissions: [], roleName: null, isAuthenticated: false })
      },
      
      hasPermission: (permission: string) => {
        const { permissions } = get()
        return permissions.includes(permission)
      },
    }),
    {
      name: 'medflow-auth',
      partialize: (state) => ({
        user: state.user,
        tokens: state.tokens,
        currentTenant: state.currentTenant,
        isAuthenticated: state.isAuthenticated,
        permissions: state.permissions,
        roleName: state.roleName,
      }),
    }
  )
)
