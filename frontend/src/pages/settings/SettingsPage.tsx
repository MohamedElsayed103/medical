import { Link } from 'react-router-dom'
import { Users, Shield, Mail, Building2, Activity } from 'lucide-react'

export default function SettingsPage() {

  const sections = [
    { title: 'Team Members', description: 'Manage users and their roles', icon: Users, to: '/settings/users', permission: 'manage_users' },
    { title: 'Roles & Permissions', description: 'Configure access control', icon: Shield, to: '/settings/roles', permission: 'manage_roles' },
    { title: 'Invitations', description: 'Invite new team members', icon: Mail, to: '/settings/invitations', permission: 'manage_invitations' },
    { title: 'Organization', description: 'Clinic/Hospital settings', icon: Building2, to: '/settings/organization', permission: null },
    { title: 'Audit Log', description: 'View system activity', icon: Activity, to: '/audit', permission: 'view_audit_logs' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 text-sm mt-1">Manage your organization settings</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sections.map((section) => (
          <Link
            key={section.title}
            to={section.to}
            className="bg-white rounded-xl p-6 shadow-soft border border-gray-100 hover:shadow-card-hover hover:border-primary-200 transition-all group"
          >
            <div className="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center mb-4 group-hover:bg-primary-100 transition-colors">
              <section.icon className="w-5 h-5 text-primary-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-1">{section.title}</h3>
            <p className="text-sm text-gray-500">{section.description}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}
