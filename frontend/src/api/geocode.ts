/**
 * Typed API client — Geocoding (story 3.2.5).
 *
 * Uses Photon (photon.komoot.io) — a free geocoder backed by OpenStreetMap data,
 * operated by Komoot GmbH. Called directly from the browser (CORS-enabled).
 *
 * Fair-use mitigations:
 *  1. In-memory cache — repeated queries return cached results; zero network calls.
 *  2. 1-second throttle between distinct requests — enforced client-side.
 *  3. Attribution — `PHOTON_ATTRIBUTION` is rendered in the map UI footer.
 *
 * For high-traffic production: self-host Photon or switch to a hosted geocoding
 * service with a rate-limit tier. See docs/deployment/DEPLOYMENT_GUIDE.md.
 *
 * API: GET https://photon.komoot.io/api/?q=<location>&limit=1&lang=en
 * Response: GeoJSON FeatureCollection — coordinates [lon, lat] (GeoJSON order).
 */

const _PHOTON_URL = 'https://photon.komoot.io/api/'
const _CACHE_MAX = 200

export interface GeocodeResult {
  lat: number
  lon: number
  displayName: string
  /** US state code (e.g., "VA") if returned by Photon, undefined otherwise */
  state?: string
}

// ── In-memory result cache ────────────────────────────────────────────────────
// Keyed on normalised query string (lowercase, trimmed). Evicts oldest entry
// when _CACHE_MAX is reached.
const _cache = new Map<string, GeocodeResult>()

function _cacheGet(key: string): GeocodeResult | undefined {
  return _cache.get(key)
}

function _cacheSet(key: string, value: GeocodeResult): void {
  if (_cache.size >= _CACHE_MAX) {
    // Evict the oldest entry (Map preserves insertion order)
    const oldest = _cache.keys().next().value
    if (oldest !== undefined) _cache.delete(oldest)
  }
  _cache.set(key, value)
}

// ── 1-second throttle ────────────────────────────────────────────────────────
let _lastRequestTime = 0
const _MIN_INTERVAL_MS = 1000

async function _throttledFetch(url: string): Promise<Response> {
  const now = Date.now()
  const elapsed = now - _lastRequestTime
  if (elapsed < _MIN_INTERVAL_MS) {
    await new Promise((resolve) => setTimeout(resolve, _MIN_INTERVAL_MS - elapsed))
  }
  _lastRequestTime = Date.now()
  return fetch(url)
}

// ── US State name to code mapping ───────────────────────────────────────────
const US_STATE_CODES: Record<string, string> = {
  'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
  'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
  'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
  'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
  'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
  'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
  'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
  'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
  'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
  'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
  'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
  'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
  'Wisconsin': 'WI', 'Wyoming': 'WY', 'District of Columbia': 'DC',
}

function stateNameToCode(stateName: string): string | undefined {
  return US_STATE_CODES[stateName]
}

// ── US Zip Code Detection ───────────────────────────────────────────────────
// US zip codes are 5 digits, optionally followed by -XXXX (ZIP+4)
const US_ZIP_REGEX = /^\d{5}(-\d{4})?$/

/**
 * Returns true if the query looks like a US zip code.
 * Appending ", USA" to the Photon query biases results towards the US.
 */
function looksLikeUSZipCode(query: string): boolean {
  return US_ZIP_REGEX.test(query.trim())
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Geocodes a free-text location string using Photon (OpenStreetMap-backed).
 *
 * Returns a cached result instantly for repeated queries. Throttles to ≤ 1 req/s
 * for distinct queries. Returns null when the query is empty, unreachable, or
 * produces no results.
 *
 * US zip code handling: Appends ", USA" to 5-digit queries to bias Photon
 * towards US results (avoids geocoding to international locations like Mexico).
 */
export async function geocodeLocation(location: string): Promise<GeocodeResult | null> {
  const trimmed = location.trim()
  if (!trimmed) return null

  const cacheKey = trimmed.toLowerCase()
  const cached = _cacheGet(cacheKey)
  if (cached) return cached

  // Bias US zip codes towards USA to avoid international matches (e.g., Mexico)
  const queryString = looksLikeUSZipCode(trimmed) ? `${trimmed}, USA` : trimmed

  try {
    const params = new URLSearchParams({ q: queryString, limit: '1', lang: 'en' })
    const res = await _throttledFetch(`${_PHOTON_URL}?${params.toString()}`)
    if (!res.ok) return null

    const data = (await res.json()) as {
      type: string
      features: Array<{
        geometry: { type: string; coordinates: [number, number] }
        properties: {
          name?: string
          city?: string
          state?: string
          country?: string
        }
      }>
    }

    const feature = data.features?.[0]
    if (!feature) return null

    const [lon, lat] = feature.geometry.coordinates
    const p = feature.properties
    const displayName = [p.name, p.city, p.state, p.country]
      .filter(Boolean)
      .join(', ') || trimmed

    // Extract US state code from Photon state name
    const stateCode = p.state ? stateNameToCode(p.state) : undefined

    const result: GeocodeResult = { lat, lon, displayName, state: stateCode }
    _cacheSet(cacheKey, result)
    return result
  } catch {
    return null
  }
}


