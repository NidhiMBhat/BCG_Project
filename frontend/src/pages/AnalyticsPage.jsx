import { useState } from 'react'
import { usePatients } from '../hooks/usePatients'
import { useAnalytics } from '../hooks/useAnalytics'
import TrendBadge from '../components/TrendBadge'
import DailyAvgChart from '../components/charts/DailyAvgChart'
import { useScans } from '../hooks/useScans'
import { formatHR } from '../utils/formatters'

export default function AnalyticsPage() {
  const { patients } = usePatients()
  const [selectedId, setSelectedId] = useState('')
  const { analytics, loading } = useAnalytics(selectedId)
  const { scans: rawScans } = useScans(selectedId, { sort: 'desc', pageSize: 100 })
  const scans = [...rawScans].reverse()

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-brand-900">Analytics</h1>
        <p className="text-brand-700/80 text-sm">7-day physiological analysis per patient</p>
      </div>

      {/* Patient selector */}
      <div className="flex items-center gap-3 max-w-sm">
        <select
          className="input-field"
          value={selectedId}
          onChange={e => setSelectedId(e.target.value)}
        >
          <option value="">Select patient…</option>
          {patients.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </div>

      {loading && <div className="text-brand-700/80 text-sm">Computing analytics…</div>}

      {analytics && analytics.scan_count > 0 && (
        <>
          {/* Summary sentence */}
          <div className="glass-card p-4">
            <p className="text-sm text-brand-800">{analytics.summary}</p>
          </div>

          {/* Averages grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              ['Avg HR', formatHR(analytics.averages?.heart_rate), 'text-rose-400'],
              ['Highest HR', formatHR(analytics.highest_hr), 'text-rose-300'],
              ['Lowest HR', formatHR(analytics.lowest_hr), 'text-emerald-400'],
              ['Weekly HR', formatHR(analytics.weekly_hr), 'text-brand-800'],
              ['Scan Count', analytics.scan_count, 'text-brand-400'],
            ].map(([k, v, c]) => (
              <div key={k} className="glass-card p-4">
                <p className="text-xs text-brand-700/60">{k}</p>
                <p className={`font-bold font-mono text-lg mt-1 ${c}`}>{v}</p>
              </div>
            ))}
          </div>

          {/* Trend badges + summaries */}
          <div className="glass-card p-5 space-y-4">
            <p className="section-title">Trend Analysis</p>
            <div className="space-y-3">
              {[
                ['Heart Rate', analytics.trends?.hr, analytics.hr_summary],
              ].map(([label, badge, summary]) => (
                <div key={label} className="flex items-start gap-4 py-3 border-b border-brand-900/10 last:border-0">
                  <div className="w-28 flex-shrink-0">
                    <p className="text-sm font-medium text-brand-800">{label}</p>
                    <TrendBadge badge={badge} />
                  </div>
                  <p className="text-sm text-brand-700/80">{summary}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="glass-card p-5">
              <p className="section-title">Daily Average HR</p>
              <DailyAvgChart data={analytics.daily_hr} label="Avg HR (BPM)" color="#f43f5e" />
            </div>
          </div>
        </>
      )}

      {analytics && analytics.scan_count === 0 && (
        <div className="glass-card p-8 text-center text-brand-700/60">
          No scan data found for this patient in the last 7 days.
        </div>
      )}
    </div>
  )
}
