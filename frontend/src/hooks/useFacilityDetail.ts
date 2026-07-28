/**
 * Hook: fetch single facility detail (story 3.4.1).
 * Used by FacilityDrawer.
 */
import { useEffect, useState } from 'react'
import { fetchFacilityDetail } from '../api/facilities'
import type { FacilityDetail } from '../api/types'

export interface UseFacilityDetailResult {
  detail: FacilityDetail | null
  loading: boolean
  error: string | null
}

export function useFacilityDetail(facilityId: string | null): UseFacilityDetailResult {
  const [detail, setDetail] = useState<FacilityDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!facilityId) {
      setDetail(null)
      return
    }
    setLoading(true)
    setError(null)
    fetchFacilityDetail(facilityId)
      .then((d) => {
        setDetail(d)
        setError(null)
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load facility detail')
      })
      .finally(() => setLoading(false))
  }, [facilityId])

  return { detail, loading, error }
}
