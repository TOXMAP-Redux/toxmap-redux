/**
 * Hook: fetch Superfund site detail by EPA ID.
 * Story 4.2.1 — powers the SuperfundDrawer.
 */
import { useEffect, useState } from 'react'
import { fetchSuperfundDetail } from '../api/superfund'
import type { SuperfundDetail } from '../api/types'

export interface UseSuperfundDetailResult {
  data: SuperfundDetail | null
  loading: boolean
  error: string | null
}

/** Fetches the full detail for one Superfund site. Pass null to suppress. */
export function useSuperfundDetail(epaId: string | null): UseSuperfundDetailResult {
  const [data, setData] = useState<SuperfundDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!epaId) {
      setData(null)
      return
    }
    setLoading(true)
    setError(null)
    fetchSuperfundDetail(epaId)
      .then((result) => {
        setData(result)
        setError(null)
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load site detail')
      })
      .finally(() => setLoading(false))
  }, [epaId])

  return { data, loading, error }
}
