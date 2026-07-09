import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function DailyAvgChart({ data = [], label = 'Avg HR', color = '#f43f5e' }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#374151' }} tickLine={{ stroke: '#374151' }} axisLine={{ stroke: '#374151' }} />
        <YAxis tick={{ fontSize: 10, fill: '#374151' }} tickLine={{ stroke: '#374151' }} axisLine={{ stroke: '#374151' }} />
        <Tooltip
          contentStyle={{ background: '#141829', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px', fontSize: '11px' }}
          formatter={(v) => [`${v?.toFixed(1)}`, label]}
        />
        <Bar dataKey="value" name={label} fill={color} radius={[4, 4, 0, 0]} opacity={0.8} />
      </BarChart>
    </ResponsiveContainer>
  )
}
