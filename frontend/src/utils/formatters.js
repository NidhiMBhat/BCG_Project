import { format, formatDistanceToNow, parseISO } from 'date-fns'

export function formatDateTime(ts) {
  if (!ts) return '—'
  try {
    return format(parseISO(ts), 'MMM d, yyyy HH:mm')
  } catch { return ts }
}

export function formatDate(ts) {
  if (!ts) return '—'
  try {
    return format(parseISO(ts), 'MMM d, yyyy')
  } catch { return ts }
}

export function formatRelative(ts) {
  if (!ts) return '—'
  try {
    return formatDistanceToNow(parseISO(ts), { addSuffix: true })
  } catch { return ts }
}

export function formatHR(v) {
  if (v == null) return '—'
  return `${v.toFixed(1)} BPM`
}

export function formatRR(v) {
  if (v == null) return '—'
  return `${v.toFixed(1)} br/min`
}

export function formatHRV(v) {
  if (v == null) return '—'
  return `${v.toFixed(1)} ms`
}

export function formatScore(v) {
  if (v == null) return '—'
  return v.toFixed(1)
}

export function formatPct(v) {
  if (v == null) return '—'
  return `${v.toFixed(1)}%`
}

export function signalQualityColor(sq) {
  switch ((sq || '').toLowerCase()) {
    case 'excellent': return 'text-emerald-400'
    case 'good': return 'text-cyan-400'
    case 'moderate': return 'text-amber-400'
    case 'poor': return 'text-rose-400'
    default: return 'text-brand-700/80'
  }
}

export function riskColor(risk) {
  switch ((risk || '').toLowerCase()) {
    case 'low': return 'badge-green'
    case 'medium': return 'badge-amber'
    case 'high': return 'badge-red'
    default: return 'badge-gray'
  }
}

export function scoreColor(score) {
  if (score == null) return 'text-brand-700/80'
  if (score >= 80) return 'text-emerald-400'
  if (score >= 60) return 'text-amber-400'
  return 'text-rose-400'
}

export function severityColor(severity) {
  switch ((severity || '').toLowerCase()) {
    case 'critical': return 'badge-red'
    case 'warning': return 'badge-amber'
    case 'info': return 'badge-blue'
    default: return 'badge-gray'
  }
}

export function roleColor(role) {
  switch (role) {
    case 'admin': return 'badge-purple'
    case 'doctor': return 'badge-blue'
    case 'patient': return 'badge-green'
    default: return 'badge-gray'
  }
}

export function trendArrowColor(direction) {
  switch (direction) {
    case 'up': return 'text-rose-400'
    case 'down': return 'text-emerald-400'
    default: return 'text-brand-700/80'
  }
}
