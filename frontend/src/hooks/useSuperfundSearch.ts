/**
 * Hook: fetch Superfund search results when the user submits a Superfund-mode search.
 * Story 4.1.3 — powers the results table in Superfund dataset mode.
 */
import { useEffect, useRef, useState } from 'react'
import { fetchSuperfundSites, type SuperfundSearchParams } from '../api/superfund'
import type { SuperfundCollection } from '../api/types'

export interface UseSuperfundSearchResult {
  data: SuperfundCollection | null
  loading: boolean
  error: string | null
}

/**
 * Fetches Superfund sites for the submitted search location.
 * Pass `null` params to suppress fetching (TRI mode or no search).
 */
export function useSuperfundSearch(
  params: SuperfundSearchParams | null,
): UseSuperfundSearchResult {
  const [data, setData] = useState<SuperfundCollection | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    if (!params) {
      setData(null)
      return
    }

    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setLoading(true)
    setError(null)

    fetchSuperfundSites(params, controller.signal)
      .then((result) => {
        setData(result)
        setError(null)
      })
      .catch((err: unknown) => {
        if (err instanceof Error && err.name === 'AbortError') return
        setError(err instanceof Error ? err.message : 'Superfund search failed')
      })
      .finally(() => setLoading(false))
  }, [params])

  return { data, loading, error }
}
