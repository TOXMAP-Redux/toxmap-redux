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
 * API: GET https://photon.komoot.io/api/?q=<location>&limit=5&lang=en&lat=X&lon=Y
 * Response: GeoJSON FeatureCollection — coordinates [lon, lat] (GeoJSON order).
 */

const _PHOTON_URL = 'https://photon.komoot.io/api/'
const _CACHE_MAX = 200

/** Confidence level for geocoding results */
export type GeocodeConfidence = 'exact' | 'high' | 'approximate' | 'low'

export interface GeocodeResult {
  lat: number
  lon: number
  displayName: string
  /** US state code (e.g., "VA") if returned by Photon, undefined otherwise */
  state?: string
  /** Confidence score 0-1 */
  confidence: number
  /** Human-readable confidence level */
  confidenceLevel: GeocodeConfidence
  /** House number if extracted from result */
  houseNumber?: string
  /** Street name if available */
  street?: string
  /** City name if available */
  city?: string
  /** Postal code if available */
  postcode?: string
  /** OSM type (house, street, city, etc.) */
  osmType?: string
}

/** Options for geocoding request */
export interface GeocodeOptions {
  /** Current map center latitude for proximity bias */
  biasLat?: number
  /** Current map center longitude for proximity bias */
  biasLon?: number
  /** Return multiple candidates instead of auto-selecting best */
  returnCandidates?: boolean
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

// ── Query parsing ───────────────────────────────────────────────────────────
interface ParsedQuery {
  houseNumber?: string
  streetName?: string
  city?: string
  stateCode?: string
  postcode?: string
  originalQuery: string
}

/**
 * Parse a free-text address query to extract components for scoring.
 * Example: "100 Mill Rd, Port Townsend, WA 98368"
 */
function parseAddressQuery(query: string): ParsedQuery {
  const result: ParsedQuery = { originalQuery: query }
  
  // Extract house number (leading digits)
  const houseMatch = query.match(/^(\d+)\s+/)
  if (houseMatch) {
    result.houseNumber = houseMatch[1]
  }
  
  // Extract postal code (5 digits, optionally +4)
  const zipMatch = query.match(/\b(\d{5})(-\d{4})?\b/)
  if (zipMatch) {
    result.postcode = zipMatch[1]
  }
  
  // Extract US state code (2 uppercase letters, typically after comma)
  const stateMatch = query.match(/,\s*([A-Z]{2})(?:\s|,|$)/)
  if (stateMatch && US_STATE_CODES[Object.keys(US_STATE_CODES).find(k => US_STATE_CODES[k] === stateMatch[1]) || '']) {
    result.stateCode = stateMatch[1]
  }
  // Also check for state names
  for (const [name, code] of Object.entries(US_STATE_CODES)) {
    if (query.toLowerCase().includes(name.toLowerCase())) {
      result.stateCode = code
      break
    }
  }
  
  // Extract street name (text after house number, before first comma)
  if (houseMatch) {
    const afterHouse = query.substring(houseMatch[0].length)
    const streetMatch = afterHouse.match(/^([^,]+)/)
    if (streetMatch) {
      result.streetName = streetMatch[1].trim()
    }
  }
  
  // Extract city (text after first comma, before state)
  const parts = query.split(',').map(p => p.trim())
  if (parts.length >= 2) {
    // City is typically the second part (after street address)
    const potentialCity = parts[1].replace(/\s*[A-Z]{2}\s*\d{5}.*$/, '').trim()
    if (potentialCity && !potentialCity.match(/^\d+$/)) {
      result.city = potentialCity
    }
  }
  
  return result
}

// ── Street name normalization ───────────────────────────────────────────────
const STREET_ABBREVIATIONS: Record<string, string[]> = {
  'road': ['rd', 'road'],
  'street': ['st', 'str', 'street'],
  'avenue': ['ave', 'av', 'avenue'],
  'boulevard': ['blvd', 'boulevard'],
  'drive': ['dr', 'drive'],
  'lane': ['ln', 'lane'],
  'court': ['ct', 'court'],
  'circle': ['cir', 'circle'],
  'place': ['pl', 'place'],
  'way': ['wy', 'way'],
  'highway': ['hwy', 'highway'],
  'parkway': ['pkwy', 'parkway'],
}

function normalizeStreetName(name: string): string {
  let normalized = name.toLowerCase().trim()
  for (const [canonical, variants] of Object.entries(STREET_ABBREVIATIONS)) {
    for (const variant of variants) {
      // Replace at word boundary at end of string
      const regex = new RegExp(`\\b${variant}\\b$`, 'i')
      if (regex.test(normalized)) {
        normalized = normalized.replace(regex, canonical)
        break
      }
    }
  }
  return normalized
}

function streetNameSimilarity(query: string, result: string): number {
  const q = normalizeStreetName(query)
  const r = normalizeStreetName(result)
  
  if (q === r) return 1.0
  if (r.includes(q) || q.includes(r)) return 0.8
  
  // Check word overlap
  const qWords = new Set(q.split(/\s+/))
  const rWords = new Set(r.split(/\s+/))
  const intersection = [...qWords].filter(w => rWords.has(w))
  const union = new Set([...qWords, ...rWords])
  
  return intersection.length / union.size
}

// ── Haversine distance ──────────────────────────────────────────────────────
function haversineDistanceKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371 // Earth's radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon/2) * Math.sin(dLon/2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
  return R * c
}

// ── Confidence scoring ──────────────────────────────────────────────────────
interface PhotonFeature {
  geometry: { type: string; coordinates: [number, number] }
  properties: {
    name?: string
    housenumber?: string
    street?: string
    city?: string
    state?: string
    country?: string
    postcode?: string
    osm_key?: string
    osm_value?: string
    type?: string
  }
}

function scoreCandidate(
  feature: PhotonFeature,
  parsedQuery: ParsedQuery,
  biasLat?: number,
  biasLon?: number
): number {
  const p = feature.properties
  let score = 0
  
  // House number match: +0.35
  if (parsedQuery.houseNumber && p.housenumber) {
    if (p.housenumber === parsedQuery.houseNumber) {
      score += 0.35
    } else {
      // Partial credit for close house numbers
      const queryNum = parseInt(parsedQuery.houseNumber, 10)
      const resultNum = parseInt(p.housenumber, 10)
      if (!isNaN(queryNum) && !isNaN(resultNum)) {
        const diff = Math.abs(queryNum - resultNum)
        if (diff <= 10) score += 0.2
        else if (diff <= 50) score += 0.1
      }
    }
  } else if (!parsedQuery.houseNumber && !p.housenumber) {
    // No house number in query, none in result — neutral
    score += 0.15
  }
  
  // Street name similarity: +0.25
  if (parsedQuery.streetName && p.street) {
    score += 0.25 * streetNameSimilarity(parsedQuery.streetName, p.street)
  } else if (parsedQuery.streetName && p.name) {
    // Sometimes street is in name field
    score += 0.20 * streetNameSimilarity(parsedQuery.streetName, p.name)
  }
  
  // City match: +0.10
  if (parsedQuery.city && p.city) {
    if (p.city.toLowerCase() === parsedQuery.city.toLowerCase()) {
      score += 0.10
    } else if (p.city.toLowerCase().includes(parsedQuery.city.toLowerCase()) ||
               parsedQuery.city.toLowerCase().includes(p.city.toLowerCase())) {
      score += 0.05
    }
  }
  
  // State match: +0.10
  if (parsedQuery.stateCode && p.state) {
    const resultStateCode = stateNameToCode(p.state)
    if (resultStateCode === parsedQuery.stateCode) {
      score += 0.10
    }
  }
  
  // Postal code match: +0.10
  if (parsedQuery.postcode && p.postcode) {
    if (p.postcode === parsedQuery.postcode) {
      score += 0.10
    } else if (p.postcode.startsWith(parsedQuery.postcode.substring(0, 3))) {
      score += 0.05 // Same ZIP prefix
    }
  }
  
  // Proximity bonus: +0.10 (if within 50km of bias point)
  if (biasLat !== undefined && biasLon !== undefined) {
    const [lon, lat] = feature.geometry.coordinates
    const distKm = haversineDistanceKm(lat, lon, biasLat, biasLon)
    if (distKm <= 10) score += 0.10
    else if (distKm <= 50) score += 0.07
    else if (distKm <= 100) score += 0.04
    else if (distKm <= 500) score += 0.02
  }
  
  // OSM type bonus: prefer address-level matches
  const osmType = p.type || p.osm_value
  if (osmType === 'house' || osmType === 'building') score += 0.05
  else if (osmType === 'street') score += 0.02
  
  return Math.min(score, 1.0) // Cap at 1.0
}

function getConfidenceLevel(score: number): GeocodeConfidence {
  if (score >= 0.85) return 'exact'
  if (score >= 0.65) return 'high'
  if (score >= 0.40) return 'approximate'
  return 'low'
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
 *
 * @param location - Free-text location query
 * @param options - Optional bias and candidate settings
 */
export async function geocodeLocation(
  location: string,
  options: GeocodeOptions = {}
): Promise<GeocodeResult | null> {
  const trimmed = location.trim()
  if (!trimmed) return null

  // Cache key includes bias coordinates for proximity-aware caching
  const biasKey = options.biasLat !== undefined && options.biasLon !== undefined
    ? `_${options.biasLat.toFixed(2)}_${options.biasLon.toFixed(2)}`
    : ''
  const cacheKey = trimmed.toLowerCase() + biasKey
  const cached = _cacheGet(cacheKey)
  if (cached) return cached

  // Parse query for scoring
  const parsedQuery = parseAddressQuery(trimmed)

  // Build query string with US bias for zip codes
  let queryString = trimmed
  if (looksLikeUSZipCode(trimmed)) {
    queryString = `${trimmed}, USA`
  } else if (!trimmed.toLowerCase().includes('usa') && !trimmed.toLowerCase().includes('united states')) {
    // Append USA if not already present and this looks like a US address
    if (parsedQuery.stateCode || parsedQuery.postcode) {
      queryString = `${trimmed}, USA`
    }
  }

  try {
    // Request multiple candidates for scoring
    const params = new URLSearchParams({ q: queryString, limit: '5', lang: 'en' })
    
    // Add location bias if provided
    if (options.biasLat !== undefined && options.biasLon !== undefined) {
      params.set('lat', options.biasLat.toFixed(6))
      params.set('lon', options.biasLon.toFixed(6))
    }
    
    const res = await _throttledFetch(`${_PHOTON_URL}?${params.toString()}`)
    if (!res.ok) return null

    const data = (await res.json()) as {
      type: string
      features: PhotonFeature[]
    }

    if (!data.features?.length) return null

    // Score all candidates
    const scored = data.features.map((feature) => ({
      feature,
      score: scoreCandidate(feature, parsedQuery, options.biasLat, options.biasLon),
    }))

    // Sort by score descending
    scored.sort((a, b) => b.score - a.score)

    // Select best candidate
    const best = scored[0]
    const [lon, lat] = best.feature.geometry.coordinates
    const p = best.feature.properties

    // Build display name from structured components
    const displayParts: string[] = []
    if (p.housenumber && p.street) {
      displayParts.push(`${p.housenumber} ${p.street}`)
    } else if (p.name) {
      displayParts.push(p.name)
    } else if (p.street) {
      displayParts.push(p.street)
    }
    if (p.city) displayParts.push(p.city)
    if (p.state) {
      const stateCode = stateNameToCode(p.state)
      displayParts.push(stateCode || p.state)
    }
    if (p.postcode) displayParts.push(p.postcode)
    
    const displayName = displayParts.length > 0 ? displayParts.join(', ') : trimmed

    const result: GeocodeResult = {
      lat,
      lon,
      displayName,
      state: p.state ? stateNameToCode(p.state) : undefined,
      confidence: best.score,
      confidenceLevel: getConfidenceLevel(best.score),
      houseNumber: p.housenumber,
      street: p.street,
      city: p.city,
      postcode: p.postcode,
      osmType: p.type || p.osm_value,
    }

    _cacheSet(cacheKey, result)
    return result
  } catch {
    return null
  }
}

/**
 * Geocodes a location and returns multiple scored candidates for disambiguation.
 * Use this when you want to show the user alternative matches.
 */
export async function geocodeLocationWithCandidates(
  location: string,
  options: GeocodeOptions = {}
): Promise<GeocodeResult[]> {
  const trimmed = location.trim()
  if (!trimmed) return []

  const parsedQuery = parseAddressQuery(trimmed)

  let queryString = trimmed
  if (looksLikeUSZipCode(trimmed)) {
    queryString = `${trimmed}, USA`
  } else if (!trimmed.toLowerCase().includes('usa') && !trimmed.toLowerCase().includes('united states')) {
    if (parsedQuery.stateCode || parsedQuery.postcode) {
      queryString = `${trimmed}, USA`
    }
  }

  try {
    const params = new URLSearchParams({ q: queryString, limit: '5', lang: 'en' })
    
    if (options.biasLat !== undefined && options.biasLon !== undefined) {
      params.set('lat', options.biasLat.toFixed(6))
      params.set('lon', options.biasLon.toFixed(6))
    }
    
    const res = await _throttledFetch(`${_PHOTON_URL}?${params.toString()}`)
    if (!res.ok) return []

    const data = (await res.json()) as {
      type: string
      features: PhotonFeature[]
    }

    if (!data.features?.length) return []

    // Score and sort all candidates
    const results: GeocodeResult[] = data.features.map((feature) => {
      const score = scoreCandidate(feature, parsedQuery, options.biasLat, options.biasLon)
      const [lon, lat] = feature.geometry.coordinates
      const p = feature.properties

      const displayParts: string[] = []
      if (p.housenumber && p.street) {
        displayParts.push(`${p.housenumber} ${p.street}`)
      } else if (p.name) {
        displayParts.push(p.name)
      } else if (p.street) {
        displayParts.push(p.street)
      }
      if (p.city) displayParts.push(p.city)
      if (p.state) {
        const stateCode = stateNameToCode(p.state)
        displayParts.push(stateCode || p.state)
      }
      if (p.postcode) displayParts.push(p.postcode)

      return {
        lat,
        lon,
        displayName: displayParts.length > 0 ? displayParts.join(', ') : trimmed,
        state: p.state ? stateNameToCode(p.state) : undefined,
        confidence: score,
        confidenceLevel: getConfidenceLevel(score),
        houseNumber: p.housenumber,
        street: p.street,
        city: p.city,
        postcode: p.postcode,
        osmType: p.type || p.osm_value,
      }
    })

    results.sort((a, b) => b.confidence - a.confidence)
    return results
  } catch {
    return []
  }
}


