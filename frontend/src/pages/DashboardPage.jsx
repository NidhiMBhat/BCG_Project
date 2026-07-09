import { useEffect, useState } from 'react'
import { Users, Heart, Activity, Zap, AlertTriangle, TrendingUp } from 'lucide-react'
import { usePatients } from '../hooks/usePatients'
import { useLive } from '../hooks/useLive'
import StatCard from '../components/StatCard'
import PatientCard from '../components/PatientCard'
import AlertBanner from '../components/AlertBanner'
import api from '../utils/api'
import { formatHR, formatDateTime } from '../utils/formatters'

export default function DashboardPage() {
  const { patients } = usePatients()
  const { liveData, connected } = useLive()
  const [alerts, setAlerts] = useState([])
  const [stats, setStats] = useState(null)

  useEffect(() => {
    api.alerts.list().then(setAlerts).catch(() => {})
  }, [])

  const scan = liveData?.latest_scan
  const session = liveData?.session

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-brand-900">Dashboard</h1>
          <p className="text-brand-700/80 text-sm mt-0.5">BCG Healthcare Platform overview</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-700 border border-brand-900/10">
          <span className={connected ? 'dot-online' : 'dot-offline'} />
          <span className="text-xs text-brand-700/80">{connected ? 'Live Connected' : 'Backend Offline'}</span>
        </div>
      </div>

      {/* Top stat row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Patients"
          value={patients.length}
          icon={Users}
          color="text-brand-400"
          subtext="Registered in system"
        />
        <StatCard
          label="Live HR"
          value={scan?.heart_rate?.toFixed(1) ?? '—'}
          unit="BPM"
          icon={Heart}
          color="text-rose-400"
          pulse={!!scan}
          subtext={session?.active ? `Patient #${session.patient_id}` : 'No active session'}
        />
        <StatCard
          label="AI Health Score"
          value={scan?.ai_health_score?.toFixed(1) ?? '—'}
          unit="/100"
          icon={TrendingUp}
          color="text-brand-400"
          subtext={scan?.risk_level ? `Risk: ${scan.risk_level}` : 'Awaiting data'}
        />
        <StatCard
          label="Active Alerts"
          value={alerts.slice(0, 50).length}
          icon={AlertTriangle}
          color="text-amber-400"
          subtext="Last 7 days"
        />
      </div>

      {/* Session banner */}
      {session?.active && (
        <div className="glass-card p-4 border-l-4 border-emerald-500 animate-slide-in">
          <div className="flex items-center gap-3">
            <span className="dot-online" />
            <div>
              <p className="font-semibold text-emerald-400">Monitoring Session Active</p>
              <p className="text-sm text-brand-700/80">
                Patient ID {session.patient_id} · {session.packet_count} packets · {session.packets_per_second} PPS · {Math.round(session.elapsed_seconds)}s elapsed
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent alerts */}
        <div className="lg:col-span-1 space-y-3">
          <div className="flex items-center justify-between">
            <p className="section-title">Recent Alerts</p>
            <span className="badge badge-amber">{alerts.length}</span>
          </div>
          {alerts.length === 0 ? (
            <div className="glass-card p-4 text-center text-brand-700/60 text-sm">No alerts</div>
          ) : (
            alerts.slice(0, 6).map(a => <AlertBanner key={a.id} alert={a} />)
          )}
        </div>

        {/* Patient list */}
        <div className="lg:col-span-2 space-y-3">
          <p className="section-title">Patients</p>
          {patients.slice(0, 6).map(p => <PatientCard key={p.id} patient={p} />)}
        </div>
      </div>
    </div>
  )
}
