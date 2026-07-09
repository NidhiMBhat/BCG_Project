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
import AIScoreChart from '../components/charts/AIScoreChart'
import { useSessions } from '../hooks/useSessions'
import { formatDateTime, formatHR, signalQualityColor } from '../utils/formatters'

export default function PatientDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { patient } = usePatient(id)
  const { scans: rawScans } = useScans(id, { sort: 'desc', pageSize: 100 })
  const { analytics } = useAnalytics(id)
  const { sessions } = useSessions(id)
  const [selectedScan, setSelectedScan] = useState(null)

  // Sort scans ascending for charts (they come back descending from the API)
  const scans = [...rawScans].reverse()
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
          </div>
          {analytics.hr_summary && (
            <div className="mt-4 space-y-1">
              {[analytics.hr_summary].filter(Boolean).map((s, i) => (
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
          <div className="grid grid-cols-2 gap-4">
            <StatItem icon={Heart} label="Heart Rate" value={formatHR(latest.heart_rate)} color="text-rose-400" />
            <StatItem icon={Heart} label="Lowest HR" value={formatHR(latest.lowest_heart_rate)} color="text-cyan-400" />
            <StatItem icon={Heart} label="Highest HR" value={formatHR(latest.highest_heart_rate)} color="text-amber-400" />
          </div>
          <div className="mt-3 flex flex-wrap gap-3">
            <span className={`text-sm ${signalQualityColor(latest.signal_quality)}`}>⬤ {latest.signal_quality}</span>
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

      {/* Session History */}
      {sessions && sessions.length > 0 && (
        <div className="glass-card p-5">
          <p className="section-title">Session History</p>
          <div className="mt-4 overflow-hidden rounded-xl border border-brand-900/10">
            <table className="w-full text-sm text-left">
              <thead className="bg-brand-900/5">
                <tr className="text-xs text-brand-700/60 uppercase tracking-wider">
                  <th className="px-4 py-3 font-semibold">Start Time</th>
                  <th className="px-4 py-3 font-semibold">End Time</th>
                  <th className="px-4 py-3 font-semibold">HR Range</th>
                  <th className="px-4 py-3 font-semibold">Packets</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-900/10">
                {sessions.map(s => (
                  <tr key={s.id} className="hover:bg-brand-900/5 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs">{formatDateTime(s.start_time)}</td>
                    <td className="px-4 py-3 font-mono text-xs">{s.end_time ? formatDateTime(s.end_time) : 'Active'}</td>
                    <td className="px-4 py-3 font-mono text-rose-400">
                      {s.lowest_heart_rate ? formatHR(s.lowest_heart_rate) : '—'} - {s.highest_heart_rate ? formatHR(s.highest_heart_rate) : '—'}
                    </td>
                    <td className="px-4 py-3 font-mono text-brand-700/80">{s.packet_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
