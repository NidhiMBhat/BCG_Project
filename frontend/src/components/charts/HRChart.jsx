import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { formatDateTime } from '../../utils/formatters'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-card px-3 py-2 text-xs">
      <p className="text-brand-700/80 mb-1">{label}</p>
      {payload.map(p => (
        <p key={p.dataKey} style={{ color: p.color }}>{p.name}: <strong>{p.value?.toFixed(1)}</strong></p>
      ))}
    </div>
  )
}

export default function HRChart({ scans = [] }) {
  const data = scans
    .filter(s => s.heart_rate != null)
    .slice(-50)
    .map(s => ({
      time: formatDateTime(s.timestamp).split(' ')[1] || '',
      HR: parseFloat(s.heart_rate?.toFixed(1)),
    }))

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#374151' }} tickLine={{ stroke: '#374151' }} axisLine={{ stroke: '#374151' }} />
        <YAxis domain={[45, 110]} tick={{ fontSize: 10, fill: '#374151' }} tickLine={{ stroke: '#374151' }} axisLine={{ stroke: '#374151' }} />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={60} stroke="rgba(244,63,94,0.3)" strokeDasharray="4 4" />
        <ReferenceLine y={100} stroke="rgba(244,63,94,0.3)" strokeDasharray="4 4" />
        <Line type="linear" dataKey="HR" name="Heart Rate" stroke="#1f77b4" strokeWidth={1.5} dot={{ r: 3, fill: '#1f77b4', strokeWidth: 0 }} activeDot={{ r: 4 }} />
      </LineChart>
    </ResponsiveContainer>
  )
}
