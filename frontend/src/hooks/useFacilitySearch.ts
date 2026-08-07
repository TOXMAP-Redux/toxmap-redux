/**
 * Hook: debounced facility search autocomplete (ADR-010).
 * Calls GET /api/v1/facilities/search?q= on each keystroke (300ms debounce).
 * Returns ranked results with match_type (id/name) and relevance_score.
 */
import { useEffect, useRef, useState } from 'react'
import { searchFacilities } from '../api/facilities'
import type { FacilitySearchResult } from '../api/types'

export interface UseFacilitySearchResult {
  results: FacilitySearchResult[]
  loading: boolean
  error: Error | null
}

/**
 * Returns facility search results for the given query string.
 * Empty array when query < 2 chars or on error.
 *
 * @param query - Search query (TRI ID or facility name)
 * @param state - Optional 2-letter state code filter
 * @param limit - Max results (default 10)
 */
export function useFacilitySearch(
  query: string,
  state?: string,
  limit = 10,
): UseFacilitySearchResult {
  const [results, setResults] = useState<FacilitySearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const latestQuery = useRef(query)
  latestQuery.current = query

  useEffect(() => {
    // Clear any pending debounce
    if (debounceRef.current) clearTimeout(debounceRef.current)
    // Abort any in-flight request
    if (abortRef.current) abortRef.current.abort()

    // API requires min 2 chars
    if (query.length < 2) {
      setResults([])
      setLoading(false)
      setError(null)
      return
    }

    setLoading(true)
    setError(null)

    debounceRef.current = setTimeout(() => {
      const q = latestQuery.current
      const controller = new AbortController()
      abortRef.current = controller

      searchFacilities(q, state, limit, controller.signal)
        .then((data) => {
          if (latestQuery.current === q && !controller.signal.aborted) {
            setResults(data)
            setError(null)
          }
        })
        .catch((err) => {
          if (latestQuery.current === q && !controller.signal.aborted) {
            // Don't set error for abort
            if (err instanceof Error && err.name !== 'AbortError') {
              setError(err)
            }
            setResults([])
          }
        })
        .finally(() => {
          if (latestQuery.current === q && !controller.signal.aborted) {
            setLoading(false)
          }
        })
    }, 300)

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
      if (abortRef.current) abortRef.current.abort()
    }
  }, [query, state, limit])

  return { results, loading, error }
}
