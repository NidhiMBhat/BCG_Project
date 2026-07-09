import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Users, Activity, BarChart3,
  ClipboardList, Download, Settings, LogOut, Heart
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useLive } from '../hooks/useLive'

const ICON_MAP = {
  LayoutDashboard, Users, Activity, BarChart3, ClipboardList, Download, Settings,
}

const LINKS = [
  { path: '/',          label: 'Dashboard',       icon: 'LayoutDashboard' },
  { path: '/patients',  label: 'Patients',        icon: 'Users' },
  { path: '/live',      label: 'Live Monitoring', icon: 'Activity' },
  { path: '/analytics', label: 'Analytics',       icon: 'BarChart3' },
  { path: '/history',   label: 'Scan History',    icon: 'ClipboardList' },
  { path: '/exports',   label: 'Exports',         icon: 'Download' },
  { path: '/settings',  label: 'Settings',        icon: 'Settings' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const { liveData, connected } = useLive()
  const navigate = useNavigate()

  const isMonitoring = liveData?.session?.active

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col h-screen bg-surface-800 border-r border-brand-900/10">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-brand-900/10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-accent-cyan flex items-center justify-center shadow-lg shadow-brand-500/30">
            <Heart className="w-5 h-5 text-brand-900" />
          </div>
          <div>
            <p className="font-bold text-brand-900 text-sm leading-tight">BCG Healthcare</p>
            <p className="text-xs text-brand-700/60">Platform v1.0</p>
          </div>
        </div>
      </div>

      {/* Live monitoring indicator */}
      {isMonitoring && (
        <div className="mx-3 mt-3 px-3 py-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 animate-fade-in">
          <div className="flex items-center gap-2">
            <span className="dot-online" />
            <div className="min-w-0">
              <p className="text-xs font-semibold text-emerald-400">Monitoring Active</p>
              <p className="text-xs text-brand-700/80 truncate">Patient ID: {liveData?.session?.patient_id}</p>
            </div>
          </div>
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {LINKS.map(({ path, label, icon }) => {
          const Icon = ICON_MAP[icon]
          return (
            <NavLink
              key={path}
              to={path}
              end={path === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 group ${
                  isActive
                    ? 'bg-brand-600/20 text-brand-400 border border-brand-500/20'
                    : 'text-brand-700/80 hover:text-brand-900 hover:bg-surface-600'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-brand-400' : 'text-brand-700/60 group-hover:text-brand-800'}`} />
                  {label}
                  {icon === 'Activity' && isMonitoring && (
                    <span className="ml-auto w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  )}
                </>
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* User info + logout */}
      <div className="px-3 pb-4 border-t border-brand-900/10 pt-4">
        {/* Backend status */}
        <div className="flex items-center gap-2 px-3 py-2 mb-2">
          <span className={connected ? 'dot-online' : 'dot-offline'} />
          <span className="text-xs text-brand-700/60">{connected ? 'Backend Connected' : 'Backend Offline'}</span>
        </div>

        <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-surface-600 mb-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-500 to-violet-500 flex items-center justify-center flex-shrink-0">
            <span className="text-xs font-bold text-brand-900">{user?.username?.[0]?.toUpperCase()}</span>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-brand-900 truncate">{user?.username}</p>
            <p className="text-xs text-brand-700/60 capitalize">{user?.role}</p>
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-brand-700/80 hover:text-rose-400 hover:bg-rose-500/10 transition-all duration-150 w-full group"
        >
          <LogOut className="w-4 h-4 text-brand-700/60 group-hover:text-rose-400" />
          Logout
        </button>
      </div>
    </aside>
  )
}
