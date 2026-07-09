import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { formatDateTime } from '../../utils/formatters'

export default function AIScoreChart({ scans = [] }) {
  const data = scans.filter(s => s.ai_health_score != null).slice(-50).map(s => ({
    time: formatDateTime(s.timestamp).split(' ')[1] || '',
    Score: parseFloat(s.ai_health_score?.toFixed(1)),
    Confidence: parseFloat(s.ai_confidence?.toFixed(1)),
  }))
  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data}>
        
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#374151' }} tickLine={{ stroke: '#374151' }} axisLine={{ stroke: '#374151' }} />
        <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#374151' }} tickLine={{ stroke: '#374151' }} axisLine={{ stroke: '#374151' }} />
        <Tooltip
          contentStyle={{ background: '#141829', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px', fontSize: '11px' }}
          formatter={(v, n) => [`${v?.toFixed(1)}`, n]}
        />
        <Line type="linear" dataKey="Score" name="AI Score" stroke="#6366f1" fill="url(#scoreGrad)" strokeWidth={1.5} dot={{ r: 3, fill: '#1f77b4', strokeWidth: 0 }} />
        <Line type="linear" dataKey="Confidence" name="Confidence" stroke="#14b8a6" fill="none" strokeWidth={1.5} strokeDasharray="4 4" dot={{ r: 3, fill: '#1f77b4', strokeWidth: 0 }} />
      </LineChart>
    </ResponsiveContainer>
  )
}
