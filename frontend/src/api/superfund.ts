/**
 * Superfund API client — wraps GET /api/v1/superfund/browse, /api/v1/superfund, and /api/v1/superfund/{epa_id}.
 * Stories: 4.1.1, 4.2.1–4.2.3
 */
import type { SuperfundCollection, SuperfundDetail } from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export interface SuperfundSearchParams {
  lat: number
  lon: number
  radiusMiles: number
  chemical?: string
  state?: string
  restrictToState?: boolean
  status?: string
}

/**
 * Fetch ALL Superfund sites without radius constraint (browse mode).
 * Used for the always-on diamond layer. Fetched once on app load.
 */
export async function fetchAllSuperfundBrowse(
  signal?: AbortSignal,
): Promise<SuperfundCollection> {
  const res = await fetch(`${API_BASE}/api/v1/superfund/browse`, signal ? { signal } : {})
  if (!res.ok) throw new Error(`Superfund browse failed: ${res.status}`)
  return res.json() as Promise<SuperfundCollection>
}

/**
 * Fetch Superfund/NPL sites within the given radius.
 * Used for search results table in dataset=superfund mode.
 */
export async function fetchSuperfundSites(
  params: SuperfundSearchParams,
  signal?: AbortSignal,
): Promise<SuperfundCollection> {
  const p = new URLSearchParams({
    lat: String(params.lat),
    lon: String(params.lon),
    radius_miles: String(params.radiusMiles),
  })
  if (params.chemical) p.set('chemical', params.chemical)
  if (params.state) p.set('state', params.state)
  if (params.restrictToState) p.set('restrict_to_state', 'true')
  if (params.status) p.set('status', params.status)

  const res = await fetch(`${API_BASE}/api/v1/superfund?${p.toString()}`, signal ? { signal } : {})
  if (!res.ok) throw new Error(`Superfund search failed: ${res.status}`)
  return res.json() as Promise<SuperfundCollection>
}

/**
 * Fetch full Superfund site detail by EPA ID.
 * Used for the SuperfundDrawer (story 4.2.1).
 */
export async function fetchSuperfundDetail(epaId: string): Promise<SuperfundDetail> {
  const res = await fetch(`${API_BASE}/api/v1/superfund/${encodeURIComponent(epaId)}`)
  if (!res.ok) throw new Error(`Superfund detail failed: ${res.status}`)
  return res.json() as Promise<SuperfundDetail>
}
