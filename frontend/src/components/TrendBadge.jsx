import { trendArrowColor } from '../utils/formatters'

export default function TrendBadge({ badge, metric }) {
  if (!badge) return null
  const { label, arrow, direction } = badge
  const arrowColor = trendArrowColor(direction)
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-white/5 border border-brand-900/20">
      <span className={`font-bold ${arrowColor}`}>{arrow}</span>
      <span className="text-brand-800">{label}</span>
    </span>
  )
}
