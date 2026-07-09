import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { formatDateTime } from '../../utils/formatters'

export default function RMSSDChart({ scans = [] }) {
  const data = scans.filter(s => s.rmssd != null).slice(-50).map(s => ({
    time: formatDateTime(s.timestamp).split(' ')[1] || '',
    RMSSD: parseFloat(s.rmssd?.toFixed(1)),
  }))
  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#374151' }} tickLine={{ stroke: '#374151' }} axisLine={{ stroke: '#374151' }} />
        <YAxis tick={{ fontSize: 10, fill: '#374151' }} tickLine={{ stroke: '#374151' }} axisLine={{ stroke: '#374151' }} />
        <Tooltip formatter={(v) => [`${v?.toFixed(1)} ms`, 'RMSSD']} contentStyle={{ background: '#141829', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px', fontSize: '11px' }} />
        <Line type="linear" dataKey="RMSSD" stroke="#1f77b4" strokeWidth={1.5} dot={{ r: 3, fill: '#1f77b4', strokeWidth: 0 }} activeDot={{ r: 4 }} />
      </LineChart>
    </ResponsiveContainer>
  )
}
