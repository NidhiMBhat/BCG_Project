import { useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { ArrowLeft, User, Heart, Wind, Activity, Zap, FileText } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { usePatient } from '../hooks/usePatients'
import { useScans } from '../hooks/useScans'
import { useAnalytics } from '../hooks/useAnalytics'
import ScanModal from '../components/ScanModal'
import TrendBadge from '../components/TrendBadge'
import HRChart from '../components/charts/HRChart'
import RRChart from '../components/charts/RRChart'
import AIScoreChart from '../components/charts/AIScoreChart'
import { formatDateTime, formatHR, formatRR, formatHRV, riskColor, signalQualityColor } from '../utils/formatters'

export default function PatientDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { patient } = usePatient(id)
  const { scans } = useScans(id, { sort: 'asc', pageSize: 100 })
  const { analytics } = useAnalytics(id)
  const [selectedScan, setSelectedScan] = useState(null)

  const latest = scans[scans.length - 1]

  if (!patient) return <div className="p-6 text-brand-700/80">Loading patient…</div>

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/patients')} className="p-2 rounded-lg hover:bg-brand-900/5 transition-colors">
          <ArrowLeft className="w-5 h-5 text-brand-700/80" />
        </button>
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-brand-600 to-accent-violet flex items-center justify-center">
            <User className="w-6 h-6 text-brand-900" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-brand-900">{patient.name}</h1>
            <p className="text-brand-700/80 text-sm">{patient.patient_code} · {patient.age}y · {patient.gender}</p>
          </div>
        </div>
      </div>

      {/* Demographics */}
      <div className="glass-card p-5">
        <p className="section-title">Demographics</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            ['Height', patient.height ? `${patient.height} cm` : '—'],
            ['Weight', patient.weight ? `${patient.weight} kg` : '—'],
            ['Blood Group', patient.blood_group || '—'],
            ['Total Scans', analytics?.total_scan_count ?? scans.length],
          ].map(([k, v]) => (
            <div key={k}>
              <p className="text-xs text-brand-700/60">{k}</p>
              <p className="font-semibold text-brand-900 mt-0.5">{v}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Analytics summary */}
      {analytics && analytics.scan_count > 0 && (
        <div className="glass-card p-5">
          <p className="section-title">7-Day Analytics</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            {[
              ['Avg HR', formatHR(analytics.averages?.heart_rate), 'text-rose-400'],
              ['Avg RR', formatRR(analytics.averages?.respiration_rate), 'text-cyan-400'],
              ['Avg SDNN', formatHRV(analytics.averages?.sdnn), 'text-violet-400'],
              ['Avg RMSSD', formatHRV(analytics.averages?.rmssd), 'text-amber-400'],
            ].map(([k, v, c]) => (
              <div key={k}>
                <p className="text-xs text-brand-700/60">{k}</p>
                <p className={`font-bold font-mono text-lg mt-0.5 ${c}`}>{v}</p>
              </div>
            ))}
          </div>
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-2 text-sm text-brand-700/80">
              <span>HR Trend:</span> <TrendBadge badge={analytics.trends?.hr} />
            </div>
            <div className="flex items-center gap-2 text-sm text-brand-700/80">
              <span>RR Trend:</span> <TrendBadge badge={analytics.trends?.rr} />
            </div>
            <div className="flex items-center gap-2 text-sm text-brand-700/80">
              <span>HRV Trend:</span> <TrendBadge badge={analytics.trends?.hrv} />
            </div>
          </div>
          {analytics.hr_summary && (
            <div className="mt-4 space-y-1">
              {[analytics.hr_summary, analytics.rr_summary, analytics.hrv_summary].filter(Boolean).map((s, i) => (
                <p key={i} className="text-sm text-brand-700/80">• {s}</p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Latest scan */}
      {latest && (
        <div className="glass-card p-5">
          <div className="flex justify-between items-start">
            <p className="section-title">Latest Scan</p>
            <button onClick={() => setSelectedScan(latest)} className="text-xs text-brand-400 hover:text-brand-300">
              View Details →
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatItem icon={Heart} label="Heart Rate" value={formatHR(latest.heart_rate)} color="text-rose-400" />
            <StatItem icon={Wind} label="Respiration" value={formatRR(latest.respiration_rate)} color="text-cyan-400" />
            <StatItem icon={Activity} label="SDNN" value={formatHRV(latest.sdnn)} color="text-violet-400" />
            <StatItem icon={Zap} label="RMSSD" value={formatHRV(latest.rmssd)} color="text-amber-400" />
          </div>
          <div className="mt-3 flex flex-wrap gap-3">
            <span className={`text-sm ${signalQualityColor(latest.signal_quality)}`}>⬤ {latest.signal_quality}</span>
            <span className={`badge ${riskColor(latest.risk_level)}`}>{latest.risk_level} Risk</span>
            <span className="text-sm text-brand-700/60">{formatDateTime(latest.timestamp)}</span>
          </div>
          {latest.notes && (
            <div className="mt-3 p-3 rounded-xl bg-surface-600 flex gap-2">
              <FileText className="w-4 h-4 text-brand-700/80 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-brand-800">{latest.notes}</p>
            </div>
          )}
        </div>
      )}

      {/* Charts */}
      {scans.length > 1 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="glass-card p-5">
            <p className="section-title">Heart Rate History</p>
            <HRChart scans={scans} />
          </div>
          <div className="glass-card p-5">
            <p className="section-title">Respiration History</p>
            <RRChart scans={scans} />
          </div>
          <div className="glass-card p-5 lg:col-span-2">
            <p className="section-title">AI Health Score History</p>
            <AIScoreChart scans={scans} />
          </div>
        </div>
      )}

      {selectedScan && <ScanModal scan={selectedScan} onClose={() => setSelectedScan(null)} />}
    </div>
  )
}

function StatItem({ icon: Icon, label, value, color }) {
  return (
    <div className="flex items-center gap-3">
      <Icon className={`w-5 h-5 ${color} flex-shrink-0`} />
      <div>
        <p className="text-xs text-brand-700/60">{label}</p>
        <p className={`font-bold font-mono ${color}`}>{value}</p>
      </div>
    </div>
  )
}
