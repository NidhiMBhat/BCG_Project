import { useEffect, useState } from 'react'
import { Server, Database, Radio, Activity, Monitor } from 'lucide-react'
import api from '../utils/api'
import { useLive } from '../hooks/useLive'

export default function SettingsPage() {
  const [settings, setSettings] = useState(null)
  const [loading, setLoading] = useState(true)
  const { connected } = useLive()

  useEffect(() => {
    api.settings.get().then(setSettings).catch(() => {}).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-6 text-brand-700/80">Loading settings…</div>

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-brand-900">Settings</h1>
        <p className="text-brand-700/80 text-sm">Application configuration and status</p>
      </div>

      {/* Version info */}
      <div className="glass-card p-5">
        <p className="section-title">Application Info</p>
        <div className="space-y-3">
          {[
            ['App Name', settings?.app_name],
            ['Version', settings?.app_version],
            ['Backend Port', settings?.backend_port],
          ].map(([k, v]) => (
            <Row key={k} label={k} value={v} />
          ))}
        </div>
      </div>

      {/* Connection status */}
      <div className="glass-card p-5">
        <p className="section-title">Connection Status</p>
        <div className="space-y-3">
          <StatusRow icon={Server} label="Backend API" status={connected} text={connected ? 'Online' : 'Offline'} />
          <StatusRow icon={Database} label="SQLite Database" status={!!settings?.database_exists} text={settings?.database_exists ? `OK (${settings.database_size_mb} MB)` : 'Missing'} />
          <StatusRow icon={Radio} label="TCP Interface" status={true} text={`${settings?.tcp_host}:${settings?.tcp_port}`} />
          <StatusRow icon={Activity} label="Monitoring Session" status={settings?.monitoring_active} text={settings?.monitoring_active ? `Active (Patient #${settings.active_patient_id})` : 'Idle'} />
        </div>
      </div>

      {/* Live stats */}
      <div className="glass-card p-5">
        <p className="section-title">Live Statistics</p>
        <div className="space-y-3">
          {[
            ['Packets Received', settings?.packet_count ?? 0],
            ['Packets Per Second', settings?.packets_per_second ?? 0],
            ['Sampling Interval', `${settings?.sampling_interval_seconds ?? 10}s per scan`],
            ['Database Path', settings?.database_path],
          ].map(([k, v]) => <Row key={k} label={k} value={v} />)}
        </div>
      </div>

      {/* Notes */}
      <div className="glass-card p-5">
        <p className="section-title">Notes</p>
        <ul className="space-y-2 text-sm text-brand-700/80">
          <li>• The original <code className="text-brand-400">bcg_live.py</code> matplotlib dashboard is unmodified and always available.</li>
          <li>• To revert to matplotlib only: simply stop this frontend and backend — <code className="text-brand-400">python bcg_live.py</code> continues working.</li>
          <li>• This platform is an independent layer over the existing TCP pipeline.</li>
          <li>• AI Health Scores are heuristic demonstrations only — <strong>not medical diagnoses</strong>.</li>
        </ul>
      </div>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-brand-900/10 last:border-0">
      <span className="text-sm text-brand-700/80">{label}</span>
      <span className="text-sm font-mono text-brand-900">{value ?? '—'}</span>
    </div>
  )
}

function StatusRow({ icon: Icon, label, status, text }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-brand-900/10 last:border-0">
      <div className="flex items-center gap-2">
        <Icon className={`w-4 h-4 ${status ? 'text-emerald-400' : 'text-brand-700/60'}`} />
        <span className="text-sm text-brand-700/80">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${status ? 'bg-emerald-400' : 'bg-slate-600'}`} />
        <span className={`text-sm font-medium ${status ? 'text-emerald-400' : 'text-brand-700/60'}`}>{text}</span>
      </div>
    </div>
  )
}
