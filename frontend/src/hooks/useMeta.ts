/**
 * Hook: fetch data vintage metadata from GET /api/v1/meta.
 * Used by the DataVintageLabel component (story 3.1.5, UX invariant 7).
 */
import { useEffect, useState } from 'react'
import { fetchMeta } from '../api/meta'
import type { MetaResponse } from '../api/types'

export interface UseMetaResult {
  meta: MetaResponse | null
  loading: boolean
  error: string | null
}

/** Fetches metadata once on mount. Returns vintage label and available years. */
export function useMeta(): UseMetaResult {
  const [meta, setMeta] = useState<MetaResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    fetchMeta()
      .then((data) => {
        setMeta(data)
        setError(null)
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load metadata')
      })
      .finally(() => setLoading(false))
  }, [])

  return { meta, loading, error }
}
