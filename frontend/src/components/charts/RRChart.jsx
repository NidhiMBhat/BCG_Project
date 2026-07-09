import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { formatDateTime } from '../../utils/formatters'

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-card px-3 py-2 text-xs">
      {payload.map(p => (
        <p key={p.dataKey} style={{ color: p.color }}>{p.name}: <strong>{p.value?.toFixed(1)}</strong> br/min</p>
      ))}
    </div>
  )
}

export default function RRChart({ scans = [] }) {
  const data = scans.filter(s => s.respiration_rate != null).slice(-50).map(s => ({
    time: formatDateTime(s.timestamp).split(' ')[1] || '',
    RR: parseFloat(s.respiration_rate?.toFixed(1)),
  }))

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#374151' }} tickLine={{ stroke: '#374151' }} axisLine={{ stroke: '#374151' }} />
        <YAxis domain={[8, 25]} tick={{ fontSize: 10, fill: '#374151' }} tickLine={{ stroke: '#374151' }} axisLine={{ stroke: '#374151' }} />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={12} stroke="rgba(6,182,212,0.3)" strokeDasharray="4 4" />
        <ReferenceLine y={20} stroke="rgba(6,182,212,0.3)" strokeDasharray="4 4" />
        <Line type="linear" dataKey="RR" name="Respiration" stroke="#1f77b4" strokeWidth={1.5} dot={{ r: 3, fill: '#1f77b4', strokeWidth: 0 }} activeDot={{ r: 4 }} />
      </LineChart>
    </ResponsiveContainer>
  )
}
