import { useState } from 'react'
import { Download, FileText } from 'lucide-react'
import { usePatients } from '../hooks/usePatients'
import api from '../utils/api'

export default function ExportsPage() {
  const { patients } = usePatients()
  const [patientId, setPatientId] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleExport = async () => {
    if (!patientId) { setError('Please select a patient'); return }
    setError('')
    setSuccess('')
    setLoading(true)
    try {
      const { blob, filename } = await api.export.csv(patientId, startDate || null, endDate || null)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
      setSuccess(`Downloaded: ${filename}`)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-brand-900">CSV Export</h1>
        <p className="text-brand-700/80 text-sm">Download patient scan data for MATLAB, Python, or Excel</p>
      </div>

      <div className="glass-card p-6 max-w-xl space-y-4">
        <p className="section-title">Export Configuration</p>

        <div>
          <label className="block text-xs text-brand-700/80 mb-1">Patient *</label>
          <select className="input-field" value={patientId} onChange={e => setPatientId(e.target.value)}>
            <option value="">Select patient…</option>
            {patients.map(p => <option key={p.id} value={p.id}>{p.name} ({p.patient_code})</option>)}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-brand-700/80 mb-1">From Date (optional)</label>
            <input type="date" className="input-field" value={startDate} onChange={e => setStartDate(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs text-brand-700/80 mb-1">To Date (optional)</label>
            <input type="date" className="input-field" value={endDate} onChange={e => setEndDate(e.target.value)} />
          </div>
        </div>

        {error && <p className="text-rose-400 text-sm">{error}</p>}
        {success && <p className="text-emerald-400 text-sm">{success}</p>}

        <button onClick={handleExport} disabled={loading} className="btn-primary flex items-center gap-2 w-full justify-center py-3">
          <Download className="w-4 h-4" />
          {loading ? 'Preparing export…' : 'Download CSV'}
        </button>
      </div>

      {/* Format notes */}
      <div className="glass-card p-5 max-w-xl">
        <p className="section-title">CSV Format</p>
        <div className="space-y-2 text-sm text-brand-700/80">
          <div className="flex items-start gap-2">
            <FileText className="w-4 h-4 text-brand-400 flex-shrink-0 mt-0.5" />
            <p>Headers: scan_id, patient_id, patient_code, patient_name, timestamp, heart_rate_bpm, respiration_rate_brpm, sdnn_ms, rmssd_ms, motion_detected, signal_quality, ai_health_score, ai_confidence, risk_level, notes</p>
          </div>
          <p className="text-xs text-brand-700/60">Compatible with MATLAB <code>readtable()</code>, Python pandas, and Excel.</p>
        </div>
      </div>
    </div>
  )
}
