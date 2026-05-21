import axios from 'axios'
import { useAuthStore } from '@/stores/authStore'

const API_BASE_URL = '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

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
    
    return Promise.reject(error)
  }
)

export default api
