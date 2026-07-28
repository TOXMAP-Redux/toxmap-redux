/**
 * Typed API client — Chemicals (stories 2.3.x).
 */
import type { Chemical } from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

/** GET /api/v1/chemicals — full list */
export async function fetchChemicals(): Promise<Chemical[]> {
  const res = await fetch(`${API_BASE}/api/v1/chemicals`)
  if (!res.ok) throw new Error(`Chemicals list failed: ${res.status}`)
  return res.json() as Promise<Chemical[]>
}

/**
 * GET /api/v1/chemicals/search?q= — autocomplete.
 * Returns empty array for queries < 2 chars (matches API 422 behavior).
 */
export async function searchChemicals(q: string): Promise<Chemical[]> {
  if (q.length < 2) return []
  const res = await fetch(`${API_BASE}/api/v1/chemicals/search?q=${encodeURIComponent(q)}`)
  if (!res.ok) return []
  return res.json() as Promise<Chemical[]>
}
