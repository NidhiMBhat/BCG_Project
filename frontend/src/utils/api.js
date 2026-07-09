// API utility — all requests go to /api which Vite proxies to http://localhost:8001

const BASE = '/api'

function getToken() {
  return localStorage.getItem('bcg_token')
}

function authHeaders() {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request(method, path, body = null, signal = null) {
  const headers = { 'Content-Type': 'application/json', ...authHeaders() }
  const options = { method, headers, signal }
  if (body) options.body = JSON.stringify(body)

  const res = await fetch(`${BASE}${path}`, options)

  if (res.status === 401) {
    localStorage.removeItem('bcg_token')
    localStorage.removeItem('bcg_user')
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `Request failed: ${res.status}`)
  }

  if (res.status === 204) return null
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) return res.json()
  return res  // streaming (CSV)
}

// ── Auth ───────────────────────────────────────────────────────────────────
export const api = {
  auth: {
    login: (username, password) => request('POST', '/auth/login', { username, password }),
    me: () => request('GET', '/auth/me'),
    register: (data) => request('POST', '/auth/register', data),
  },

  // ── Patients ────────────────────────────────────────────────────────────
  patients: {
    list: () => request('GET', '/patients/'),
    get: (id) => request('GET', `/patients/${id}`),
    create: (data) => request('POST', '/patients/', data),
    update: (id, data) => request('PUT', `/patients/${id}`, data),
  },

  // ── Scans ───────────────────────────────────────────────────────────────
  scans: {
    list: (patientId, params = {}) => {
      const q = new URLSearchParams()
      if (params.startDate) q.set('start_date', params.startDate)
      if (params.endDate) q.set('end_date', params.endDate)
      if (params.search) q.set('search', params.search)
      if (params.sort) q.set('sort', params.sort)
      if (params.page) q.set('page', params.page)
      if (params.pageSize) q.set('page_size', params.pageSize)
      return request('GET', `/patients/${patientId}/scans?${q}`)
    },
    get: (scanId) => request('GET', `/scans/${scanId}`),
    updateNotes: (scanId, notes) => request('PUT', `/scans/${scanId}/notes`, { notes }),
    ingest: (data) => request('POST', '/scan', data),
  },

  // ── Session ─────────────────────────────────────────────────────────────
  session: {
    start: (patientId) => request('POST', `/session/start?patient_id=${patientId}`),
    stop: () => request('POST', '/session/stop'),
    status: () => request('GET', '/session/status'),
    listForPatient: (patientId) => request('GET', `/session/patients/${patientId}/sessions`),
  },

  // ── Analytics ───────────────────────────────────────────────────────────
  analytics: {
    get: (patientId) => request('GET', `/analytics/${patientId}`),
  },

  // ── Alerts ──────────────────────────────────────────────────────────────
  alerts: {
    list: (patientId) => {
      const q = patientId ? `?patient_id=${patientId}` : ''
      return request('GET', `/alerts/${q}`)
    },
    forPatient: (patientId) => request('GET', `/alerts/${patientId}`),
  },

  // ── Export ──────────────────────────────────────────────────────────────
  export: {
    csv: async (patientId, startDate, endDate) => {
      const q = new URLSearchParams()
      if (startDate) q.set('start_date', startDate)
      if (endDate) q.set('end_date', endDate)
      const res = await fetch(`${BASE}/export/csv/${patientId}?${q}`, {
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error('Export failed')
      const blob = await res.blob()
      const cd = res.headers.get('Content-Disposition') || ''
      const match = cd.match(/filename="([^"]+)"/)
      const filename = match ? match[1] : `BCG_${patientId}.csv`
      return { blob, filename }
    },
  },

  // ── Settings ─────────────────────────────────────────────────────────────
  settings: {
    get: () => request('GET', '/settings/'),
  },

  // ── Health ───────────────────────────────────────────────────────────────
  health: () => request('GET', '/health'),
}

export default api
