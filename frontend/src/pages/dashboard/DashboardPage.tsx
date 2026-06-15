import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import {
  Users, Calendar, FlaskConical, DollarSign,
  TrendingUp, Clock, ArrowRight, Activity,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import api from '@/lib/api'
import { patientsService, appointmentsService, labOrdersService, billingService } from '@/services/api'
import { useAuthStore } from '@/stores/authStore'
import { isValid, parseISO } from 'date-fns'

function safeFormat(dateStr: string | null | undefined, fmt: string): string {
  if (!dateStr) return '—'
  const d = typeof dateStr === 'string' ? parseISO(dateStr) : new Date(dateStr)
  return isValid(d) ? format(d, fmt) : '—'
}

export default function DashboardPage() {
  const { user, roleName } = useAuthStore()
  const today = format(new Date(), 'yyyy-MM-dd')

  // Parallel data queries
  const { data: patientsData } = useQuery({
    queryKey: ['dashboard', 'patients'],
    queryFn: () => patientsService.getAll({ page_size: 5, ordering: '-created_at' }),
  })

  const { data: appointmentsData } = useQuery({
    queryKey: ['dashboard', 'appointments-today'],
    queryFn: () => appointmentsService.getAll({ date: today, page_size: 10 }),
  })

  const { data: labData } = useQuery({
    queryKey: ['dashboard', 'lab-pending'],
    queryFn: () => labOrdersService.getAll({ status: 'pending', page_size: 1 }),
  })

  const { data: billingSummary } = useQuery({
    queryKey: ['dashboard', 'billing-summary'],
    queryFn: () => billingService.getSummary(),
    retry: false,
  })

  const { data: revenueData } = useQuery({
    queryKey: ['revenue-timeseries'],
    queryFn: () => api.get('/invoices/revenue-timeseries/').then(r => r.data),
    retry: false,
  })

  const stats = [
    {
      label: 'Total Patients',
      value: patientsData?.count ?? '—',
      icon: Users,
      color: 'from-primary-500 to-primary-600',
      bgColor: 'bg-primary-50',
      textColor: 'text-primary-700',
    },
    {
      label: "Today's Appointments",
      value: appointmentsData?.count ?? '—',
      icon: Calendar,
      color: 'from-secondary-500 to-secondary-600',
      bgColor: 'bg-secondary-50',
      textColor: 'text-secondary-700',
    },
    {
      label: 'Pending Lab Orders',
      value: labData?.count ?? '—',
      icon: FlaskConical,
      color: 'from-amber-500 to-orange-500',
      bgColor: 'bg-amber-50',
      textColor: 'text-amber-700',
    },
    {
      label: 'Revenue',
      value: billingSummary ? `$${Number(billingSummary.total_invoiced || 0).toLocaleString()}` : '—',
      icon: DollarSign,
      color: 'from-emerald-500 to-green-600',
      bgColor: 'bg-emerald-50',
      textColor: 'text-emerald-700',
    },
  ]

  // Map revenue timeseries data to chart format
  const revenueChartData = (revenueData?.results ?? []).map(
    (entry: { date: string; revenue: number }) => ({
      name: safeFormat(entry.date, 'MMM dd'),
      revenue: entry.revenue,
    })
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 18 ? 'afternoon' : 'evening'},{' '}
            {user?.first_name || 'Doctor'}
          </h1>
          <p className="text-gray-500 mt-1">
            {roleName && <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800 mr-2">{roleName}</span>}
            Here's what's happening today — {format(new Date(), 'EEEE, MMMM d, yyyy')}
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="bg-white rounded-2xl p-5 shadow-soft border border-gray-100 hover:shadow-card-hover transition-all"
          >
            <div className="flex items-center justify-between mb-3">
              <div className={`w-10 h-10 rounded-xl ${stat.bgColor} flex items-center justify-center`}>
                <stat.icon className={`w-5 h-5 ${stat.textColor}`} />
              </div>
              <TrendingUp className="w-4 h-4 text-green-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
            <p className="text-sm text-gray-500 mt-1">{stat.label}</p>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="lg:col-span-2 bg-white rounded-2xl p-6 shadow-soft border border-gray-100"
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Revenue Overview</h3>
              <p className="text-sm text-gray-500">Recent invoice totals</p>
            </div>
            <Link to="/billing" className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
              View All <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          {revenueChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={revenueChartData}>
                <defs>
                  <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0d9488" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#0d9488" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} />
                <Tooltip />
                <Area type="monotone" dataKey="revenue" stroke="#0d9488" fill="url(#colorRevenue)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-60 flex items-center justify-center text-gray-400">
              <p>No revenue data yet</p>
            </div>
          )}
        </motion.div>

        {/* Today's Schedule */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white rounded-2xl p-6 shadow-soft border border-gray-100"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Today's Schedule</h3>
            <Link to="/appointments" className="text-sm text-primary-600 hover:text-primary-700 font-medium">
              View All
            </Link>
          </div>
          <div className="space-y-3 max-h-[280px] overflow-y-auto">
            {appointmentsData?.results?.length ? (
              appointmentsData.results.map((apt) => (
                <div key={apt.id} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors">
                  <div className="w-2 h-2 rounded-full bg-primary-500 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {apt.patient_name || 'Patient'}
                    </p>
                    <p className="text-xs text-gray-500">
                      {apt.scheduled_at ? safeFormat(apt.scheduled_at, 'h:mm a') : apt.reason || 'Appointment'}
                    </p>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    apt.status === 'confirmed' ? 'bg-green-100 text-green-700' :
                    apt.status === 'scheduled' ? 'bg-blue-100 text-blue-700' :
                    apt.status === 'completed' ? 'bg-gray-100 text-gray-700' :
                    'bg-yellow-100 text-yellow-700'
                  }`}>
                    {apt.status}
                  </span>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-400">
                <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No appointments today</p>
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* Bottom Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Patients */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white rounded-2xl p-6 shadow-soft border border-gray-100"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Recent Patients</h3>
            <Link to="/patients" className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
              View All <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="space-y-3">
            {patientsData?.results?.length ? (
              patientsData.results.map((patient) => (
                <Link
                  key={patient.id}
                  to={`/patients/${patient.id}`}
                  className="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors"
                >
                  <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center text-sm font-semibold text-primary-700">
                    {patient.first_name[0]}{patient.last_name[0]}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900">
                      {patient.first_name} {patient.last_name}
                    </p>
                    <p className="text-xs text-gray-500">
                      MRN: {patient.medical_record_number || '—'} • {patient.phone || patient.email || '—'}
                    </p>
                  </div>
                  <span className="text-xs text-gray-400">
                    {safeFormat(patient.created_at, 'MMM d')}
                  </span>
                </Link>
              ))
            ) : (
              <div className="text-center py-8 text-gray-400">
                <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No patients yet</p>
              </div>
            )}
          </div>
        </motion.div>

        {/* Quick Actions / Appointments by Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-white rounded-2xl p-6 shadow-soft border border-gray-100"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'New Patient', to: '/patients?new=1', icon: Users, color: 'bg-primary-50 text-primary-700 hover:bg-primary-100' },
              { label: 'Book Appointment', to: '/appointments?new=1', icon: Calendar, color: 'bg-secondary-50 text-secondary-700 hover:bg-secondary-100' },
              { label: 'Create Invoice', to: '/billing?new=1', icon: DollarSign, color: 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100' },
              { label: 'New Lab Order', to: '/lab-orders?new=1', icon: FlaskConical, color: 'bg-amber-50 text-amber-700 hover:bg-amber-100' },
              { label: 'New Visit', to: '/visits?new=1', icon: Activity, color: 'bg-rose-50 text-rose-700 hover:bg-rose-100' },
              { label: 'AI Assistant', to: '/ai', icon: Activity, color: 'bg-purple-50 text-purple-700 hover:bg-purple-100' },
            ].map((action) => (
              <Link
                key={action.label}
                to={action.to}
                className={`flex items-center gap-3 p-4 rounded-xl transition-colors ${action.color}`}
              >
                <action.icon className="w-5 h-5" />
                <span className="text-sm font-medium">{action.label}</span>
              </Link>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
