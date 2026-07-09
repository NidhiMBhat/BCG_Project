import { useState, useEffect, useCallback } from 'react'
import api from '../utils/api'

export function useSessions(patientId) {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchSessions = useCallback(async () => {
    if (!patientId) return
    setLoading(true)
    setError(null)
    try {
      // In api.js we'll add api.session.listForPatient
      const res = await api.session.listForPatient(patientId)
      setSessions(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [patientId])

  useEffect(() => {
    fetchSessions()
  }, [fetchSessions])

  return { sessions, loading, error, refetch: fetchSessions }
}
