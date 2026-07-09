import { useState, useEffect, useCallback } from 'react'
import api from '../utils/api'

export function useAnalytics(patientId) {
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetch = useCallback(async () => {
    if (!patientId) return
    setLoading(true)
    setError(null)
    try {
      const data = await api.analytics.get(patientId)
      setAnalytics(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [patientId])

  useEffect(() => { fetch() }, [fetch])

  return { analytics, loading, error, refetch: fetch }
}
