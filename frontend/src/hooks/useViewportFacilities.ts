/**
 * Hook: fetch viewport-scoped TRI facilities (story 3.2.8, UX invariant 2).
 *
 * Re-fetches when params change (new search or bbox update after map move).
 * Returns null data before the first successful fetch.
 *
 * In browse mode, shows old data silently during map-pan re-fetches (no flicker).
 * On a new search (chemical/location change), clears old data and shows loading.
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchFacilities } from '../api/facilities'
import type { FacilityCollection, SearchParams } from '../api/types'

export interface UseViewportFacilitiesResult {
  data: FacilityCollection | null
  loading: boolean
  error: string | null
}

/** A key that identifies the "search identity" — changes when chemical or location changes. */
function searchKey(p: SearchParams): string {
  return `${p.chemical}|${p.lat.toFixed(2)}|${p.lon.toFixed(2)}|${p.radiusMiles}|${p.year}|${p.state}`
}

export function useViewportFacilities(params: SearchParams | null): UseViewportFacilitiesResult {
  const [data, setData] = useState<FacilityCollection | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const lastSearchKeyRef = useRef<string | null>(null)

  const run = useCallback((p: SearchParams) => {
    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller

    const key = searchKey(p)
    const isNewSearch = key !== lastSearchKeyRef.current
    lastSearchKeyRef.current = key

    // Show loading and clear data on new search (chemical/location change).
    // Silent re-fetch for map-pan bbox updates.
    if (isNewSearch) {
      setData(null)
      setLoading(true)
    }
    setError(null)

    fetchFacilities(p, controller.signal)
      .then((result) => {
        setData(result)
        setError(null)
      })
      .catch((err: unknown) => {
        if (err instanceof Error && err.name === 'AbortError') return
        setError(err instanceof Error ? err.message : 'Search failed')
      })
      .finally(() => {
        setLoading(false)
      })
  }, [])

  useEffect(() => {
    if (!params) return
    run(params)
    return () => {
      abortRef.current?.abort()
    }
  }, [params, run])

  return { data, loading, error }
}
