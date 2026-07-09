import { AlertTriangle, Info, AlertOctagon, X } from 'lucide-react'
import { formatRelative } from '../utils/formatters'

const ICONS = {
  critical: AlertOctagon,
  warning: AlertTriangle,
  info: Info,
}
const STYLES = {
  critical: 'bg-rose-500/10 border-rose-500/30 text-rose-300',
  warning: 'bg-amber-500/10 border-amber-500/30 text-amber-300',
  info: 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300',
}

export default function AlertBanner({ alert, onDismiss }) {
  const sev = alert.severity || 'info'
  const Icon = ICONS[sev] || Info
  const style = STYLES[sev] || STYLES.info

  return (
    <div className={`flex items-start gap-3 px-4 py-3 rounded-xl border animate-slide-in ${style}`}>
      <Icon className="w-4 h-4 flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">{alert.message}</p>
        <p className="text-xs opacity-60 mt-0.5">{formatRelative(alert.created_at)}</p>
      </div>
      {onDismiss && (
        <button onClick={onDismiss} className="opacity-50 hover:opacity-100 transition-opacity">
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  )
}
