/**
 * Typed API client — Facilities (stories 2.1.x, 2.2.x, ADR-010).
 * All requests go through the Vite proxy (/api → http://backend:8000) in dev/Docker.
 * When VITE_API_BASE_URL is set (outside Docker), requests are direct.
 */
import type {
  FacilityCollection,
  FacilityDetail,
  FacilitySearchResult,
  ReleaseEvent,
  SearchParams,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

/**
 * Builds the query URL for GET /api/v1/facilities.
 * Security: all params are passed via URLSearchParams — no string interpolation with user input.
 */
function buildFacilitySearchUrl(params: SearchParams): string {
  const p = new URLSearchParams({
    lat: String(params.lat),
    lon: String(params.lon),
    radius_miles: String(params.radiusMiles),
  })
  if (params.chemical) p.set('chemical', params.chemical)
  if (params.year) p.set('year', params.year)
  if (params.medium) p.set('medium', params.medium)
  if (params.state) p.set('state', params.state)
  if (params.restrictToState) p.set('restrict_to_state', 'true')
  if (params.bbox) p.set('bbox', params.bbox.join(','))
  if (params.exactMatch) p.set('exact_match', 'true')
  return `${API_BASE}/api/v1/facilities?${p.toString()}`
}

/** GET /api/v1/facilities — radius + filter search */
export async function fetchFacilities(
  params: SearchParams,
  signal?: AbortSignal,
): Promise<FacilityCollection> {
  const url = buildFacilitySearchUrl(params)
  const res = await fetch(url, signal ? { signal } : {})
  if (!res.ok) throw new Error(`Facility search failed: ${res.status}`)
  const data = await res.json() as FacilityCollection
  return data
}

/** GET /api/v1/facilities/{id} — single facility detail */
export async function fetchFacilityDetail(id: string): Promise<FacilityDetail> {
  const res = await fetch(`${API_BASE}/api/v1/facilities/${encodeURIComponent(id)}`)
  if (!res.ok) throw new Error(`Facility detail failed: ${res.status}`)
  return res.json() as Promise<FacilityDetail>
}

/** GET /api/v1/facilities/{id}/releases — 15-year time series */
export async function fetchFacilityReleases(
  id: string,
  fromYear?: number,
  toYear?: number,
): Promise<ReleaseEvent[]> {
  const p = new URLSearchParams()
  if (fromYear != null) p.set('from_year', String(fromYear))
  if (toYear != null) p.set('to_year', String(toYear))
  const qs = p.toString() ? `?${p.toString()}` : ''
  const res = await fetch(`${API_BASE}/api/v1/facilities/${encodeURIComponent(id)}/releases${qs}`)
  if (!res.ok) throw new Error(`Facility releases failed: ${res.status}`)
  return res.json() as Promise<ReleaseEvent[]>
}

export interface BrowseParams {
  year?: string
  chemical?: string
  medium?: string
  state?: string
  /** ADR-007: Skip chemical family expansion (search exact term only) */
  exactMatch?: boolean
}

/** GET /api/v1/facilities/browse — all facilities without radius constraint (browse mode) */
export async function fetchAllFacilitiesBrowse(
  params: BrowseParams = {},
  signal?: AbortSignal,
): Promise<FacilityCollection> {
  const p = new URLSearchParams()
  if (params.year) p.set('year', params.year)
  if (params.chemical) p.set('chemical', params.chemical)
  if (params.medium) p.set('medium', params.medium)
  if (params.state) p.set('state', params.state)
  if (params.exactMatch) p.set('exact_match', 'true')
  const qs = p.toString() ? `?${p.toString()}` : ''
  const url = `${API_BASE}/api/v1/facilities/browse${qs}`
  const res = await fetch(url, signal ? { signal } : {})
  if (!res.ok) throw new Error(`Browse facilities failed: ${res.status}`)
  const data = await res.json() as FacilityCollection
  return data
}

/**
 * GET /api/v1/facilities/search — autocomplete by TRI ID or name (ADR-010).
 *
 * Returns ranked results with:
 * - Exact TRI ID match: score 1.0
 * - TRI ID prefix: score 0.95
 * - Exact name match: score 0.90
 * - Name prefix: score 0.80
 * - Name contains: score 0.60
 * - TRI ID contains: score 0.50
 */
export async function searchFacilities(
  q: string,
  state?: string,
  limit = 10,
  signal?: AbortSignal,
): Promise<FacilitySearchResult[]> {
  const p = new URLSearchParams({ q })
  if (state) p.set('state', state)
  if (limit !== 10) p.set('limit', String(limit))
  const res = await fetch(
    `${API_BASE}/api/v1/facilities/search?${p.toString()}`,
    signal ? { signal } : {},
  )
  if (!res.ok) throw new Error(`Facility search failed: ${res.status}`)
  return res.json() as Promise<FacilitySearchResult[]>
}
