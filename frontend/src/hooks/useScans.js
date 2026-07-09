import { useState, useEffect, useCallback } from 'react'
import api from '../utils/api'

export function useScans(patientId, params = {}) {
  const [scans, setScans] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetch = useCallback(async () => {
    if (!patientId) return
    setLoading(true)
    setError(null)
    try {
      const data = await api.scans.list(patientId, params)
      setScans(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [patientId, JSON.stringify(params)])

  useEffect(() => { fetch() }, [fetch])

  return { scans, loading, error, refetch: fetch }
}

export function useScan(scanId) {
  const [scan, setScan] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!scanId) return
    setLoading(true)
    api.scans.get(scanId).then(setScan).finally(() => setLoading(false))
  }, [scanId])

  return { scan, loading }
}
