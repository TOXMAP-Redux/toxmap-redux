/**
 * Hook: fetch TRI facilities for map display.
 *
 * Two modes:
 * 1. Browse mode (params=null): fetch ALL facilities via /api/v1/facilities/browse
 * 2. Search mode (params set): fetch within radius via /api/v1/facilities
 *
 * Story: 3.3.2 (clustering), 3.2.8 (viewport count)
 */
import { useEffect, useRef, useState } from 'react'
import { fetchFacilities, fetchAllFacilitiesBrowse } from '../api/facilities'
import type { FacilityCollection } from '../api/types'

export interface MapSearchParams {
  /** Latitude of search center. Null for nationwide browse with filters. */
  lat: number | null
  /** Longitude of search center. Null for nationwide browse with filters. */
  lon: number | null
  radiusMiles: number
  chemical?: string
  year?: string
  state?: string
  restrictToState?: boolean
  /** ADR-007: Skip chemical family expansion (search exact term only) */
  exactMatch?: boolean
}

export interface UseMapFacilitiesResult {
  data: FacilityCollection | null
  loading: boolean
  error: string | null
}

/**
 * Generate a stable key for the search parameters.
 * null means browse mode (all facilities, no filters).
 * params with lat=null means browse mode with filters (nationwide chemical search).
 */
function searchKey(p: MapSearchParams | null): string {
  if (!p) return 'browse-all'
  if (p.lat === null || p.lon === null) return `browse-filtered|${p.chemical ?? ''}|${p.year ?? ''}|${p.state ?? ''}|${p.exactMatch ?? false}`
  return `search|${p.lat.toFixed(4)}|${p.lon.toFixed(4)}|${p.radiusMiles}|${p.chemical ?? ''}|${p.year ?? ''}|${p.state ?? ''}|${p.restrictToState ?? false}|${p.exactMatch ?? false}`
}

/**
 * Fetch facilities for map display.
 * Pass null for browse mode (all facilities), or search params for radius search.
 */
export function useMapFacilities(params: MapSearchParams | null): UseMapFacilitiesResult {
  const [data, setData] = useState<FacilityCollection | null>(null)
  const [fetching, setFetching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  // Track which key has been SUCCESSFULLY fetched (not just attempted).
  // This prevents StrictMode from breaking: first mount aborts before success,
  // second mount should retry since lastSuccessfulKeyRef is still null.
  const lastSuccessfulKeyRef = useRef<string | null>(null)

  // Compute current search key
  const currentKey = searchKey(params)
  
  // CRITICAL: loading is true if:
  // 1. We're actively fetching (fetching=true), OR
  // 2. The current key doesn't match the last successful fetch (new search pending)
  // This ensures loading=true SYNCHRONOUSLY when params change, before useEffect runs.
  const loading = fetching || currentKey !== lastSuccessfulKeyRef.current

  useEffect(() => {
    const key = currentKey
    
    // Skip if same search already succeeded
    if (key === lastSuccessfulKeyRef.current) return

    // Abort any in-flight request
    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setFetching(true)
    setError(null)

    const fetchData = params
      ? params.lat !== null && params.lon !== null
        ? // Search mode: radius-based search
          fetchFacilities({
            lat: params.lat,
            lon: params.lon,
            radiusMiles: params.radiusMiles,
            chemical: params.chemical ?? '',
            year: params.year ?? '',
            medium: '',
            state: params.state ?? '',
            restrictToState: params.restrictToState ?? false,
            bbox: null, // No bbox — we want all data for the search radius
            exactMatch: params.exactMatch,
          }, controller.signal)
        : // Browse mode with filters (nationwide chemical search)
          fetchAllFacilitiesBrowse({
            chemical: params.chemical,
            year: params.year,
            state: params.state,
            exactMatch: params.exactMatch,
          }, controller.signal)
      : // Browse mode: all facilities, no filters
        fetchAllFacilitiesBrowse({}, controller.signal)

    fetchData
      .then((result) => {
        lastSuccessfulKeyRef.current = key
        setData(result)
        setError(null)
      })
      .catch((err: unknown) => {
        if (err instanceof Error && err.name === 'AbortError') {
          return
        }
        setError(err instanceof Error ? err.message : 'Search failed')
      })
      .finally(() => {
        setFetching(false)
      })

    return () => {
      controller.abort()
    }
  }, [currentKey, params])

  return { data, loading, error }
}

/**
 * Filter a FacilityCollection to features within a bounding box.
 * Used for sidebar "X facilities in view" count without refetching.
 */
export function filterByBbox(
  collection: FacilityCollection | null,
  bbox: [number, number, number, number] | null,
): FacilityCollection | null {
  if (!collection) return null
  if (!bbox) return collection

  const [minLon, minLat, maxLon, maxLat] = bbox
  const filtered = collection.features.filter((f) => {
    const [lon, lat] = f.geometry.coordinates
    return lon >= minLon && lon <= maxLon && lat >= minLat && lat <= maxLat
  })

  return {
    type: 'FeatureCollection',
    features: filtered,
    meta: {
      ...collection.meta,
      total_count: filtered.length,
    },
  }
}
