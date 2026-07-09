import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Play, Square, Heart, Wind, Activity, Zap, Wifi, WifiOff, Database, Radio, ActivitySquare, Monitor } from 'lucide-react'
import { useLive } from '../hooks/useLive'
import { usePatients } from '../hooks/usePatients'
import StatCard from '../components/StatCard'
import MatplotlibStream from '../components/MatplotlibStream'
import api from '../utils/api'
import { formatDateTime, formatHR, formatRR, formatHRV, signalQualityColor, riskColor, scoreColor } from '../utils/formatters'

export default function LiveMonitorPage() {
  const { liveData, connected } = useLive()
  const { patients } = usePatients()
  const [selectedPatientId, setSelectedPatientId] = useState('')
  const [sessionLoading, setSessionLoading] = useState(false)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('clinical') // 'clinical' or 'signal'

  const session = liveData?.session
  const scan = liveData?.latest_scan
  const isActive = session?.active

  const handleStart = async () => {
    if (!selectedPatientId) { setError('Please select a patient first'); return }
    setError('')
    setSessionLoading(true)
    try {
      await api.session.start(parseInt(selectedPatientId))
    } catch (e) {
      setError(e.message)
    } finally {
      setSessionLoading(false)
    }
  }

  const handleStop = async () => {
    setSessionLoading(true)
    try {
      await api.session.stop()
    } catch (e) {
      setError(e.message)
    } finally {
      setSessionLoading(false)
    }
  }

  const activePatient = patients.find(p => p.id === session?.patient_id)

  return (
    <div className="p-6 space-y-6 animate-fade-in flex flex-col h-[calc(100vh-2rem)]">
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-brand-900">Live Monitoring</h1>
          <p className="text-brand-700/80 text-sm mt-0.5">Real-time BCG session dashboard</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white border border-brand-900/10 shadow-sm">
          {connected ? <Wifi className="w-4 h-4 text-emerald-400" /> : <WifiOff className="w-4 h-4 text-brand-700/60" />}
          <span className="text-xs text-brand-700/80">{connected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-brand-900/10 shrink-0">
        <button
          onClick={() => setActiveTab('clinical')}
          className={`flex items-center gap-2 px-4 py-2 font-medium text-sm transition-colors border-b-2 ${
            activeTab === 'clinical' 
              ? 'border-brand-700 text-brand-700' 
              : 'border-transparent text-brand-700/60 hover:text-brand-900'
          }`}
        >
          <ActivitySquare className="w-4 h-4" />
          Clinical View
        </button>
        <button
          onClick={() => setActiveTab('signal')}
          className={`flex items-center gap-2 px-4 py-2 font-medium text-sm transition-colors border-b-2 ${
            activeTab === 'signal' 
              ? 'border-brand-700 text-brand-700' 
              : 'border-transparent text-brand-700/60 hover:text-brand-900'
          }`}
        >
          <Monitor className="w-4 h-4" />
          Signal Analysis
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto pr-2 pb-10">
        {activeTab === 'clinical' ? (
          <div className="space-y-6">
            {/* Session control */}
            <div className="glass-card p-5">
              <p className="section-title">Session Control</p>

              {isActive ? (
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <div className="flex items-center gap-3">
                    <span className="dot-online" />
                    <div>
                      <p className="font-bold text-emerald-500">Session Active</p>
                      <p className="text-sm text-brand-700/80">
                        {activePatient?.name || `Patient #${session.patient_id}`} · {session.packet_count} packets · {session.packets_per_second} PPS
                      </p>
                    </div>
                  </div>
                  <button onClick={handleStop} disabled={sessionLoading} className="btn-danger flex items-center gap-2">
                    <Square className="w-4 h-4" />
                    {sessionLoading ? 'Stopping…' : 'Stop Monitoring'}
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-3 flex-wrap">
                  <select
                    className="input-field max-w-xs"
                    value={selectedPatientId}
                    onChange={e => setSelectedPatientId(e.target.value)}
                  >
                    <option value="">Select patient…</option>
                    {patients.map(p => (
                      <option key={p.id} value={p.id}>{p.name} ({p.patient_code})</option>
                    ))}
                  </select>
                  <button onClick={handleStart} disabled={sessionLoading || !selectedPatientId} className="btn-success flex items-center gap-2">
                    <Play className="w-4 h-4" />
                    {sessionLoading ? 'Starting…' : 'Start Monitoring'}
                  </button>
                  {error && <p className="text-rose-500 text-sm">{error}</p>}
                </div>
              )}
            </div>

            {/* Live vitals */}
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
              <StatCard label="Heart Rate" value={scan?.heart_rate?.toFixed(1) ?? '—'} unit="BPM" icon={Heart} color="text-rose-500" pulse={!!scan} />
              <StatCard label="Lowest HR (session)" value={session?.lowest_heart_rate?.toFixed(1) ?? '—'} unit="BPM" icon={Activity} color="text-cyan-500" />
              <StatCard label="Highest HR (session)" value={session?.highest_heart_rate?.toFixed(1) ?? '—'} unit="BPM" icon={Zap} color="text-amber-500" />
            </div>

            {/* AI & Signal */}
            {scan && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* AI panel */}
                <div className="glass-card p-5 space-y-4">
                  <p className="section-title">AI Analysis</p>
                  <div className="text-center py-2">
                    <p className={`text-6xl font-black font-mono ${scoreColor(scan.ai_health_score)}`}>
                      {scan.ai_health_score?.toFixed(0) ?? '—'}
                    </p>
                    <p className="text-brand-700/80 text-sm mt-1">AI Health Score</p>
                  </div>
                  <p className="text-xs text-brand-700/60 text-center">⚠️ Heuristic demo — not a medical diagnosis</p>
                </div>

                {/* Signal quality */}
                <div className="glass-card p-5 space-y-3">
                  <p className="section-title">Signal & Status</p>
                  <div className="space-y-2">
                    {[
                      ['Signal Quality', <span className={signalQualityColor(scan.signal_quality)}>{scan.signal_quality || '—'}</span>],
                      ['Timestamp', <span className="text-brand-800 text-xs font-mono">{formatDateTime(scan.timestamp)}</span>],
                    ].map(([k, v]) => (
                      <div key={k} className="flex items-center justify-between py-2 border-b border-brand-900/10 last:border-0">
                        <span className="text-sm text-brand-700/80">{k}</span>
                        <span className="text-sm font-medium">{v}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Status bar */}
            <div className="glass-card p-4">
              <p className="section-title">System Status</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { icon: Radio, label: 'TCP Status', value: connected ? 'Connected' : 'Offline', ok: connected },
                  { icon: Database, label: 'Database', value: 'SQLite', ok: true },
                  { icon: Heart, label: 'Monitoring', value: isActive ? 'Active' : 'Idle', ok: isActive },
                  { icon: Activity, label: 'Packets/sec', value: session?.packets_per_second ?? 0, ok: true },
                ].map(({ icon: Icon, label, value, ok }) => (
                  <div key={label} className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${ok ? 'bg-emerald-500/10' : 'bg-brand-900/5'}`}>
                      <Icon className={`w-4 h-4 ${ok ? 'text-emerald-500' : 'text-brand-700/60'}`} />
                    </div>
                    <div>
                      <p className="text-xs text-brand-700/60">{label}</p>
                      <p className={`text-sm font-medium ${ok ? 'text-emerald-500' : 'text-brand-700/80'}`}>{value}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="w-full h-full pb-4">
            <MatplotlibStream />
          </div>
        )}
      </div>
    </div>
  )
}
