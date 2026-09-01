/**
 * Hook: Chemical family expansion for DuckDB WASM mode (ADR-007, Algorithms Handbook Phase 2b).
 *
 * In production mode (DuckDB WASM + Parquet on R2), this hook loads
 * chemical_families.json and provides family expansion for chemical searches.
 *
 * This mirrors the backend's in-memory family cache, ensuring consistent
 * behavior between API mode and DuckDB WASM mode.
 *
 * Story context: ADR-007 (Chemical families for transparent right-to-know search)
 */
import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Map of chemical names (uppercase) to their family members.
 * Example: { "LEAD": ["LEAD", "LEAD COMPOUNDS"], ... }
 */
type FamilyMap = Record<string, string[]>

export interface UseChemicalFamiliesResult {
  /** Whether the family data is still loading */
  loading: boolean
  /** Error message if loading failed (non-fatal — search falls back to exact match) */
  error: string | null
  /**
   * Expand a chemical name to all family members.
   * Returns [chemical] if no family found or still loading.
   */
  expandChemical: (chemical: string) => string[]
  /** Check if a chemical belongs to a family */
  hasFamily: (chemical: string) => boolean
}

// Module-level cache (shared across all hook instances)
let _familyCache: FamilyMap | null = null
let _loadPromise: Promise<FamilyMap | null> | null = null

/**
 * Get the R2 base URL for Parquet data.
 * Falls back to development proxy if not configured.
 */
function getR2BaseUrl(): string {
  // In production, this comes from VITE_R2_PUBLIC_URL
  // In dev, we proxy through Vite to avoid CORS issues
  return import.meta.env.VITE_R2_PUBLIC_URL || '/data'
}

/**
 * Load chemical families from R2/CDN.
 * Returns null if the file doesn't exist (graceful degradation).
 */
async function loadFamilies(): Promise<FamilyMap | null> {
  const url = `${getR2BaseUrl()}/chemical_families.json`

  try {
    const response = await fetch(url)
    if (!response.ok) {
      if (response.status === 404) {
        // File doesn't exist — graceful fallback to no expansion
        console.debug('[useChemicalFamilies] chemical_families.json not found, using exact match')
        return null
      }
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    const data = (await response.json()) as FamilyMap
    console.debug('[useChemicalFamilies] Loaded', Object.keys(data).length, 'chemicals')
    return data
  } catch (err) {
    console.warn('[useChemicalFamilies] Failed to load chemical families:', err)
    return null
  }
}

/**
 * Hook to access chemical family expansion.
 *
 * Loads chemical_families.json once on first use (module-level cache).
 * Safe to call from multiple components — only one fetch will occur.
 */
export function useChemicalFamilies(): UseChemicalFamiliesResult {
  const [loading, setLoading] = useState(_familyCache === null)
  const [error, setError] = useState<string | null>(null)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true

    // Already cached — nothing to do
    if (_familyCache !== null) {
      setLoading(false)
      return
    }

    // Already loading — wait for existing promise
    if (_loadPromise !== null) {
      _loadPromise.then((data) => {
        if (mountedRef.current) {
          setLoading(false)
          if (!data) setError('Chemical families not available')
        }
      })
      return
    }

    // First caller — start the load
    _loadPromise = loadFamilies()
    _loadPromise.then((data) => {
      _familyCache = data
      if (mountedRef.current) {
        setLoading(false)
        if (!data) setError('Chemical families not available')
      }
    })

    return () => {
      mountedRef.current = false
    }
  }, [])

  const expandChemical = useCallback((chemical: string): string[] => {
    if (!chemical) return []
    const key = chemical.trim().toUpperCase()
    if (!_familyCache) return [chemical] // Fallback to exact match
    return _familyCache[key] ?? [chemical]
  }, [])

  const hasFamily = useCallback((chemical: string): boolean => {
    if (!chemical || !_familyCache) return false
    const key = chemical.trim().toUpperCase()
    const family = _familyCache[key]
    // A chemical "has a family" if its family has more than just itself
    return family !== undefined && family.length > 1
  }, [])

  return { loading, error, expandChemical, hasFamily }
}

/**
 * Prefetch chemical families early (call from app initialization).
 * This ensures the cache is warm before the user performs a search.
 */
export function prefetchChemicalFamilies(): void {
  if (_familyCache !== null || _loadPromise !== null) return
  _loadPromise = loadFamilies().then((data) => {
    _familyCache = data
    return data
  })
}
