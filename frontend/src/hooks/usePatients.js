import { useState, useEffect, useCallback } from 'react'
import api from '../utils/api'

export function usePatients() {
  const [patients, setPatients] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.patients.list()
      setPatients(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetch() }, [fetch])

  return { patients, loading, error, refetch: fetch }
}

export function usePatient(id) {
  const [patient, setPatient] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    api.patients.get(id)
      .then(setPatient)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  return { patient, loading, error }
}
