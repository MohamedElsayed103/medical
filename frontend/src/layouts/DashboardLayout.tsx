import { Outlet, useLocation } from 'react-router-dom'
import { useEffect, Suspense } from 'react'
import Sidebar from '@/components/navigation/Sidebar'
import TopBar from '@/components/navigation/TopBar'
import { useUIStore } from '@/stores/uiStore'
import { useAuthStore } from '@/stores/authStore'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { rbacService } from '@/services/api'

export default function DashboardLayout() {
  const { sidebarOpen } = useUIStore()
  const { setUser, setRbacContext, currentTenant } = useAuthStore()
  const location = useLocation()

  // Fetch user data on mount (to get tenant_context with permissions)
  const { data: userData } = useQuery({
    queryKey: ['me', currentTenant?.tenant_slug],
    queryFn: async () => {
      const response = await api.get('/auth/me/')
      return response.data
    },
    enabled: !!currentTenant,
  })

  // Fetch RBAC context
  const { data: rbacData } = useQuery({
    queryKey: ['rbac-me'],
    queryFn: () => rbacService.getMe(),
  })

  useEffect(() => {
    if (userData) {
      setUser(userData)
    }
  }, [userData, setUser])

  useEffect(() => {
    if (rbacData) {
      setRbacContext(rbacData)
    }
  }, [rbacData, setRbacContext])

  // Close mobile sidebar on route change
  const { setSidebarOpen } = useUIStore()
  useEffect(() => {
    if (window.innerWidth < 1024) {
      setSidebarOpen(false)
    }
  }, [location.pathname, setSidebarOpen])

  // Handle window resize — close sidebar when resizing to mobile
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        setSidebarOpen(false)
      }
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [setSidebarOpen])

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <TopBar />
        
        <main className="flex-1 overflow-y-auto p-6 lg:p-8">
          <Suspense fallback={
            <div className="flex items-center justify-center h-64">
              <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
            </div>
          }>
            <Outlet />
          </Suspense>
        </main>
      </div>
    </div>
  )
}
