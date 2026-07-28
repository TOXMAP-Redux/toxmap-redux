/**
 * Hook: fetch ALL Superfund sites once for the always-on diamond layer (story 4.1.1).
 *
 * ARCHITECTURE (2026-07-28 — matches TRI pattern):
 * - Fetches all ~1,700 sites once via /api/v1/superfund/browse
 * - No bbox dependency, no re-fetch on pan/zoom
 * - MapLibre handles viewport subsetting client-side
 * - Toggle on/off via setLayoutProperty('superfund-sites', 'visibility', ...)
 */
import { useEffect, useRef, useState } from 'react'
import { fetchAllSuperfundBrowse } from '../api/superfund'
import type { SuperfundCollection } from '../api/types'

export interface UseSuperfundViewportResult {
  data: SuperfundCollection | null
  loading: boolean
  error: string | null
}

/**
 * Fetches ALL Superfund sites once on mount.
 * Returns stable data for the always-on diamond layer.
 */
export function useSuperfundViewport(): UseSuperfundViewportResult {
  const [data, setData] = useState<SuperfundCollection | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  // Track successful fetch completion — prevents StrictMode from breaking:
  // first mount aborts before success, second mount retries since ref is null.
  const hasSucceededRef = useRef(false)

  useEffect(() => {
    // Skip if already successfully fetched
    if (hasSucceededRef.current) return

    // Abort any in-flight request
    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setLoading(true)

    fetchAllSuperfundBrowse(controller.signal)
      .then((result) => {
        hasSucceededRef.current = true
        setData(result)
        setError(null)
      })
      .catch((err: unknown) => {
        if (err instanceof Error && err.name === 'AbortError') return
        setError(err instanceof Error ? err.message : 'Superfund fetch failed')
      })
      .finally(() => setLoading(false))

    return () => controller.abort()
  }, [])

  return { data, loading, error }
}
