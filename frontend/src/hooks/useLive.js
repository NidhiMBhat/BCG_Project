import { useState, useEffect, useRef, useCallback } from 'react'

const SSE_URL = '/api/live'

export function useLive() {
  const [liveData, setLiveData] = useState(null)
  const [connected, setConnected] = useState(false)
  const esRef = useRef(null)

  const connect = useCallback(() => {
    if (esRef.current) esRef.current.close()
    const es = new EventSource(SSE_URL)
    esRef.current = es

    es.onopen = () => setConnected(true)
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        setLiveData(data)
      } catch {}
    }
    es.onerror = () => {
      setConnected(false)
      es.close()
      setTimeout(connect, 3000)
    }
  }, [])

  useEffect(() => {
    connect()
    return () => esRef.current?.close()
  }, [connect])

  return { liveData, connected }
}
