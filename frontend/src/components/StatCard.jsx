export default function StatCard({ label, value, unit, icon: Icon, color = 'text-slate-100', subtext, pulse = false }) {
  return (
    <div className="glass-card p-4 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-brand-700/80 uppercase tracking-wider">{label}</p>
        {Icon && (
          <div className={`w-7 h-7 rounded-lg flex items-center justify-center bg-white/5`}>
            <Icon className={`w-3.5 h-3.5 ${color}`} />
          </div>
        )}
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className={`stat-value ${color} ${pulse ? 'animate-pulse-slow' : ''}`}>{value ?? '—'}</span>
        {unit && <span className="text-sm text-brand-700/60">{unit}</span>}
      </div>
      {subtext && <p className="text-xs text-brand-700/60">{subtext}</p>}
    </div>
  )
}
