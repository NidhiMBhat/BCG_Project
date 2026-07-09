import { useState } from 'react'
import { Search, SortAsc, SortDesc, ChevronLeft, ChevronRight } from 'lucide-react'
import { usePatients } from '../hooks/usePatients'
import { useScans } from '../hooks/useScans'
import ScanModal from '../components/ScanModal'
import { formatDateTime, formatHR, formatRR, formatHRV, signalQualityColor, riskColor } from '../utils/formatters'

const PAGE_SIZE = 15

export default function HistoryPage() {
  const { patients } = usePatients()
  const [patientId, setPatientId] = useState('')
  const [search, setSearch] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [sort, setSort] = useState('desc')
  const [page, setPage] = useState(1)
  const [selectedScan, setSelectedScan] = useState(null)

  const { scans, loading, refetch } = useScans(patientId, {
    search, startDate, endDate, sort, page, pageSize: PAGE_SIZE,
  })

  return (
    <div className="p-6 space-y-5 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-brand-900">Scan History</h1>
        <p className="text-brand-700/80 text-sm">Sortable, searchable, filterable scan archive</p>
      </div>

      {/* Filters */}
      <div className="glass-card p-4 flex flex-wrap gap-3 items-end">
        <div className="min-w-[160px] flex-1">
          <label className="block text-xs text-brand-700/80 mb-1">Patient</label>
          <select className="input-field" value={patientId} onChange={e => { setPatientId(e.target.value); setPage(1) }}>
            <option value="">All patients</option>
            {patients.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </div>
        <div className="min-w-[160px] flex-1">
          <label className="block text-xs text-brand-700/80 mb-1">Search Notes</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-brand-700/60" />
            <input className="input-field pl-9" placeholder="Search…" value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} />
          </div>
        </div>
        <div>
          <label className="block text-xs text-brand-700/80 mb-1">From</label>
          <input type="date" className="input-field" value={startDate} onChange={e => setStartDate(e.target.value)} />
        </div>
        <div>
          <label className="block text-xs text-brand-700/80 mb-1">To</label>
          <input type="date" className="input-field" value={endDate} onChange={e => setEndDate(e.target.value)} />
        </div>
        <button
          className="btn-secondary flex items-center gap-1.5"
          onClick={() => setSort(s => s === 'desc' ? 'asc' : 'desc')}
        >
          {sort === 'desc' ? <SortDesc className="w-4 h-4" /> : <SortAsc className="w-4 h-4" />}
          {sort === 'desc' ? 'Newest First' : 'Oldest First'}
        </button>
      </div>

      {/* Table */}
      {loading ? (
        <div className="text-brand-700/80 text-sm">Loading scans…</div>
      ) : !patientId ? (
        <div className="glass-card p-8 text-center text-brand-700/60">Select a patient to view their scan history.</div>
      ) : scans.length === 0 ? (
        <div className="glass-card p-8 text-center text-brand-700/60">No scans found.</div>
      ) : (
        <>
          <div className="glass-card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-brand-900/10 text-xs text-brand-700/60 uppercase tracking-wider">
                  {['Timestamp', 'HR', 'RR', 'SDNN', 'RMSSD', 'Signal', 'Motion', 'AI Score', 'Risk', 'Notes'].map(h => (
                    <th key={h} className="px-4 py-3 text-left font-semibold">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {scans.map(s => (
                  <tr
                    key={s.id}
                    className="border-b border-brand-900/10 hover:bg-brand-900/5 cursor-pointer transition-colors"
                    onClick={() => setSelectedScan(s)}
                  >
                    <td className="px-4 py-3 text-brand-700/80 font-mono text-xs whitespace-nowrap">{formatDateTime(s.timestamp)}</td>
                    <td className="px-4 py-3 text-rose-400 font-mono font-semibold">{formatHR(s.heart_rate)}</td>
                    <td className="px-4 py-3 text-cyan-400 font-mono">{formatRR(s.respiration_rate)}</td>
                    <td className="px-4 py-3 text-violet-400 font-mono">{formatHRV(s.sdnn)}</td>
                    <td className="px-4 py-3 text-amber-400 font-mono">{formatHRV(s.rmssd)}</td>
                    <td className={`px-4 py-3 font-medium ${signalQualityColor(s.signal_quality)}`}>{s.signal_quality || '—'}</td>
                    <td className={`px-4 py-3 ${s.motion_detected ? 'text-amber-400' : 'text-emerald-400'}`}>{s.motion_detected ? 'Yes' : 'No'}</td>
                    <td className="px-4 py-3 font-mono font-bold text-brand-400">{s.ai_health_score?.toFixed(1) ?? '—'}</td>
                    <td className="px-4 py-3"><span className={`badge ${riskColor(s.risk_level)}`}>{s.risk_level || '—'}</span></td>
                    <td className="px-4 py-3 text-brand-700/60 max-w-xs truncate">{s.notes || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between">
            <p className="text-sm text-brand-700/60">Page {page} · {scans.length} results</p>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary p-2">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button onClick={() => setPage(p => p + 1)} disabled={scans.length < PAGE_SIZE} className="btn-secondary p-2">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </>
      )}

      {selectedScan && <ScanModal scan={selectedScan} onClose={() => setSelectedScan(null)} onSaved={refetch} />}
    </div>
  )
}
