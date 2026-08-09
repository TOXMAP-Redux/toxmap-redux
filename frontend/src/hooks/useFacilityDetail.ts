/**
 * Hook: fetch single facility detail (story 3.4.1).
 * Used by FacilityDrawer.
 * 
 * @param facilityId - TRI facility ID
 * @param year - If provided, filters top chemicals and totals to this reporting year.
 *               If null/undefined, returns all-years aggregation.
 */
import { useEffect, useState } from 'react'
import { fetchFacilityDetail } from '../api/facilities'
import type { FacilityDetail } from '../api/types'

export interface UseFacilityDetailResult {
  detail: FacilityDetail | null
  loading: boolean
  error: string | null
}

export function useFacilityDetail(facilityId: string | null, year?: number | null): UseFacilityDetailResult {
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
    fetchFacilityDetail(facilityId, year ?? undefined)
      .then((d) => {
        setDetail(d)
        setError(null)
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load facility detail')
      })
      .finally(() => setLoading(false))
  }, [facilityId, year])

  return { detail, loading, error }
}
