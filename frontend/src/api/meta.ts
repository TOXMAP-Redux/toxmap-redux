/**
 * Typed API client — Meta endpoint (story 2.7.3).
 * Used by the data vintage label in the map footer (story 3.1.5).
 */
import type { MetaResponse } from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

/** GET /api/v1/meta — TRI data vintage info */
export async function fetchMeta(): Promise<MetaResponse> {
  const res = await fetch(`${API_BASE}/api/v1/meta`)
  if (!res.ok) throw new Error(`Meta fetch failed: ${res.status}`)
  return res.json() as Promise<MetaResponse>
}
