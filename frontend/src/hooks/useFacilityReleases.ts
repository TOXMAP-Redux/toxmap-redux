/**
 * Hook: fetch facility release time series (story 3.4.3).
 * Used by the 3-tab chart in FacilityDrawer.
 */
import { useEffect, useState } from 'react'
import { fetchFacilityReleases } from '../api/facilities'
import type { ReleaseEvent } from '../api/types'

export interface UseFacilityReleasesResult {
  releases: ReleaseEvent[]
  loading: boolean
  error: string | null
}

export function useFacilityReleases(
  facilityId: string | null,
  fromYear?: number,
  toYear?: number,
): UseFacilityReleasesResult {
  const [releases, setReleases] = useState<ReleaseEvent[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!facilityId) {
      setReleases([])
      return
    }
    setLoading(true)
    setError(null)
    fetchFacilityReleases(facilityId, fromYear, toYear)
      .then((data) => {
        setReleases(data)
        setError(null)
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load releases')
      })
      .finally(() => setLoading(false))
  }, [facilityId, fromYear, toYear])

  return { releases, loading, error }
}
