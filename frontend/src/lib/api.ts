import axios from 'axios'
import { useAuthStore } from '@/stores/authStore'

const API_BASE_URL = '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Derive a human-readable message from any API error. The backend returns
 * `{ "error": { "code", "message" } }` for business-rule failures and DRF's
 * `{ "detail": ... }` / `{ field: [msg] }` for validation. This normalizes all
 * of them so toasts show the real message instead of "An unexpected error…".
 */
export function getApiErrorMessage(error: any, fallback = 'Something went wrong'): string {
  const data = error?.response?.data
  if (data) {
    if (typeof data === 'string') return data
    if (data.error?.message) return data.error.message
    if (typeof data.error === 'string') return data.error
    if (data.detail) return typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
    if (data.message) return data.message
    // DRF field errors: { field: ["msg", ...] }
    const firstField = Object.values(data).find(v => Array.isArray(v) && v.length > 0)
    if (firstField) return String((firstField as any[])[0])
  }
  if (error?.message && !/^request failed/i.test(error.message)) return error.message
  return fallback
}

// Request interceptor - add auth token and tenant header
api.interceptors.request.use((config) => {
  const { tokens, currentTenant } = useAuthStore.getState()
  
  if (tokens?.access) {
    config.headers.Authorization = `Bearer ${tokens.access}`
  }
  
  if (currentTenant) {
    config.headers['X-Tenant-Slug'] = currentTenant.tenant_slug
  }
  
  return config
})

// Response interceptor - handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      const { tokens, setTokens, logout } = useAuthStore.getState()
      
      if (tokens?.refresh) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: tokens.refresh,
          })
          
          const newTokens = {
            access: response.data.access,
            refresh: tokens.refresh,
          }
          setTokens(newTokens)
          originalRequest.headers.Authorization = `Bearer ${newTokens.access}`
          return api(originalRequest)
        } catch {
          logout()
          window.location.href = '/login'
        }
      } else {
        logout()
        window.location.href = '/login'
      }
    }

    // Normalize the error message so any consumer gets a real message.
    const msg = getApiErrorMessage(error)
    error.apiMessage = msg
    // Back-compat: many components read `error.response.data.detail` directly.
    if (error.response?.data && typeof error.response.data === 'object' && !error.response.data.detail) {
      error.response.data.detail = msg
    }

    return Promise.reject(error)
  }
)

export default api
