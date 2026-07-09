import { useState } from 'react'
import { X, Save, Clock, Heart, Wind, Activity, Zap } from 'lucide-react'
import { formatDateTime, formatHR, formatRR, formatHRV, formatPct, signalQualityColor, riskColor, scoreColor } from '../utils/formatters'
import api from '../utils/api'

export default function ScanModal({ scan, onClose, onSaved }) {
  const [notes, setNotes] = useState(scan?.notes || '')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  if (!scan) return null

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.scans.updateNotes(scan.id, notes)
      setSaved(true)
      onSaved?.()
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      alert('Failed to save notes: ' + e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative glass-card w-full max-w-2xl max-h-[90vh] overflow-y-auto animate-slide-in">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-brand-900/10">
          <div>
            <h2 className="text-lg font-bold text-brand-900">Scan Details</h2>
            <p className="text-sm text-brand-700/80 mt-0.5">
              <Clock className="w-3 h-3 inline mr-1" />
              {formatDateTime(scan.timestamp)}
            </p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-brand-900/5 transition-colors">
            <X className="w-5 h-5 text-brand-700/80" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Vitals grid */}
          <div>
            <p className="section-title">Physiological Metrics</p>
            <div className="grid grid-cols-2 gap-3">
              <MetricRow icon={Heart} label="Heart Rate" value={formatHR(scan.heart_rate)} color="text-rose-400" />
              <MetricRow icon={Wind} label="Respiration" value={formatRR(scan.respiration_rate)} color="text-cyan-400" />
              <MetricRow icon={Activity} label="SDNN" value={formatHRV(scan.sdnn)} color="text-violet-400" />
              <MetricRow icon={Zap} label="RMSSD" value={formatHRV(scan.rmssd)} color="text-amber-400" />
            </div>
          </div>

          {/* Signal & AI */}
          <div>
            <p className="section-title">Signal Quality & AI Analysis</p>
            <div className="glass-card p-4 space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-brand-700/80">Signal Quality</span>
                <span className={`font-semibold text-sm ${signalQualityColor(scan.signal_quality)}`}>{scan.signal_quality || '—'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-brand-700/80">Motion Detected</span>
                <span className={`font-semibold text-sm ${scan.motion_detected ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {scan.motion_detected ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-brand-700/80">AI Health Score</span>
                <span className={`font-bold text-lg font-mono ${scoreColor(scan.ai_health_score)}`}>
                  {scan.ai_health_score?.toFixed(1) ?? '—'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-brand-700/80">AI Confidence</span>
                <span className="font-semibold text-sm text-brand-900">{formatPct(scan.ai_confidence)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-brand-700/80">Risk Level</span>
                <span className={`badge ${riskColor(scan.risk_level)}`}>{scan.risk_level || '—'}</span>
              </div>
            </div>
            <p className="text-xs text-brand-700/60 mt-2">
              ⚠️ AI scores are heuristic demonstrations only — not medical diagnoses.
            </p>
          </div>

          {/* Notes */}
          <div>
            <p className="section-title">Research & Doctor Notes</p>
            <textarea
              className="input-field resize-none h-28 text-sm font-mono"
              placeholder="Add research notes, clinical observations, calibration notes…"
              value={notes}
              onChange={e => setNotes(e.target.value)}
            />
            <div className="flex justify-end mt-2 gap-2">
              <button onClick={onClose} className="btn-secondary text-sm">Cancel</button>
              <button onClick={handleSave} disabled={saving} className="btn-primary text-sm flex items-center gap-2">
                <Save className="w-3.5 h-3.5" />
                {saving ? 'Saving…' : saved ? 'Saved ✓' : 'Save Notes'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function MetricRow({ icon: Icon, label, value, color }) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-xl bg-surface-600">
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center bg-white/5`}>
        <Icon className={`w-4 h-4 ${color}`} />
      </div>
      <div>
        <p className="text-xs text-brand-700/60">{label}</p>
        <p className={`font-bold font-mono text-sm ${color}`}>{value}</p>
      </div>
    </div>
  )
}
