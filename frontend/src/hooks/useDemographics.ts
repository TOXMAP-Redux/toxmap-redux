/**
 * useDemographics hook — stories 5.2.1, 5.3.1.
 * Fetches county-level demographic data for the choropleth layer.
 *
 * Returns GeoJSON FeatureCollection with units metadata from `meta.units`.
 */
import { useEffect, useState } from 'react'
import { fetchDemographics, type DemographicParams } from '../api/demographics'
import type { DemographicCollection } from '../api/types'

interface UseDemographicsResult {
  data: DemographicCollection | null
  loading: boolean
  error: string | null
}

/**
 * Fetch demographics data for the choropleth layer.
 *
 * @param params - Pass an object (even empty) to trigger fetch, undefined to skip
 * @returns Demographics data, loading state, and error
 */
export function useDemographics(params?: DemographicParams): UseDemographicsResult {
  const [data, setData] = useState<DemographicCollection | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Track if params were provided (even empty object means "fetch")
  const shouldFetch = params !== undefined
  const stateParam = params?.state

  useEffect(() => {
    // Don't fetch if params is undefined
    if (!shouldFetch) {
      setData(null)
      return
    }

    const abortController = new AbortController()

    async function load() {
      setLoading(true)
      setError(null)

      try {
        const result = await fetchDemographics(stateParam ? { state: stateParam } : undefined, abortController.signal)
        if (!abortController.signal.aborted) {
          setData(result)
        }
      } catch (err) {
        if (!abortController.signal.aborted) {
          setError(err instanceof Error ? err.message : 'Failed to fetch demographics')
        }
      } finally {
        if (!abortController.signal.aborted) {
          setLoading(false)
        }
      }
    }

    load()

    return () => {
      abortController.abort()
    }
  }, [shouldFetch, stateParam])

  return { data, loading, error }
}
