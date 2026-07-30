/**
 * Demographics API client — stories 5.2.1, 5.3.1.
 * Fetches county-level demographic data from GET /api/v1/demographics/county.
 *
 * Units come from `meta.units` in the response — never hardcoded.
 */
import { resolveDataSource } from '../lib/duckdbCompat'
import type { DemographicCollection } from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

export interface DemographicParams {
  /** Two-letter state code to filter (optional) */
  state?: string
}

/**
 * Fetch county demographic data.
 * Returns GeoJSON FeatureCollection with polygon geometries and demographic properties.
 *
 * @param params - Optional filter params (state code)
 * @param signal - AbortSignal for request cancellation
 */
export async function fetchDemographics(
  params?: DemographicParams,
  signal?: AbortSignal,
): Promise<DemographicCollection> {
  const source = resolveDataSource()

  if (source === 'duckdb') {
    // Production mode: DuckDB WASM path (Phase 7)
    // TODO: Implement Parquet-based query when Phase 7 is complete
    throw new Error('DuckDB WASM demographics not yet implemented')
  }

  // Dev mode: FastAPI backend
  const url = new URL(`${API_BASE}/api/v1/demographics/county`, window.location.origin)
  if (params?.state) {
    url.searchParams.set('state', params.state)
  }

  const res = await fetch(url.toString(), { signal })
  if (!res.ok) {
    throw new Error(`Demographics fetch failed: ${res.status} ${res.statusText}`)
  }

  return res.json() as Promise<DemographicCollection>
}
