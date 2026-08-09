/**
 * Export API functions for CSV and map image downloads.
 * 
 * Story 6.EXPORT.1–6.EXPORT.10 — Data export UI.
 * Uses existing backend endpoints: GET /api/v1/export/csv, GET /api/v1/export/map-metadata.
 * 
 * SECURITY (SEC story 6.EXPORT.14): CSV injection prevention.
 * All user-controlled text fields are escaped using escapeCsvField() which:
 * - Prefixes formula-trigger characters (=+-@\t\r) with single quote
 * - Double-quotes fields containing commas, newlines, or quotes
 * - Escapes embedded double-quotes by doubling them
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

/**
 * Escape a single CSV field value to prevent formula injection.
 * SEC story 6.EXPORT.14: Prevents Excel/Sheets from interpreting formulas.
 * 
 * @param value The raw field value
 * @returns Properly escaped CSV field
 */
function escapeCsvField(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return ''
  
  const str = String(value)
  
  // Check for formula injection characters at start of field
  // These trigger formula evaluation in Excel, Google Sheets, LibreOffice
  const formulaChars = /^[=+\-@\t\r]/
  const needsQuote = formulaChars.test(str) || str.includes(',') || str.includes('\n') || str.includes('"')
  
  if (needsQuote) {
    // Prefix formula-trigger chars with single quote (standard CSV injection defense)
    // Then wrap in double quotes with internal quotes escaped
    const prefixed = formulaChars.test(str) ? `'${str}` : str
    return `"${prefixed.replace(/"/g, '""')}"`
  }
  
  return str
}

export interface ExportParams {
  lat?: number | null
  lon?: number | null
  radius_miles?: number
  chemical?: string | null
  year?: number | null
  state?: string | null
  medium?: string | null
  bbox?: string | null
}

/**
 * Generate a safe filename for export.
 * Pattern: toxmap-{chemical}-{year}-{date}.csv
 */
function generateFilename(params: ExportParams, prefix = 'toxmap'): string {
  const parts: string[] = [prefix]
  
  if (params.chemical) {
    // Sanitize chemical name: lowercase, replace non-alphanumeric with dashes
    parts.push(params.chemical.toLowerCase().replace(/[^\w]+/g, '-').slice(0, 30))
  }
  
  if (params.year) {
    parts.push(String(params.year))
  }
  
  // Add ISO date (YYYYMMDD format)
  const date = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  parts.push(date)
  
  return `${parts.join('-')}.csv`
}

/**
 * Export TRI facility data as CSV using the backend streaming endpoint.
 * Triggers a browser download of the CSV file.
 * 
 * @param params Search parameters to filter the export
 * @returns Promise resolving when download is triggered
 * @throws Error if export fails (network error, 4xx/5xx response)
 */
export async function exportFacilitiesCsv(params: ExportParams): Promise<void> {
  const searchParams = new URLSearchParams()
  
  // Determine if this is a nationwide search (no lat/lon)
  const isNationwideSearch = params.lat == null || params.lon == null
  
  // Use browse endpoint for nationwide searches (no spatial constraint)
  if (isNationwideSearch) {
    // Optional filters only
    if (params.chemical) {
      searchParams.set('chemical', params.chemical)
    }
    if (params.year) {
      searchParams.set('year', String(params.year))
    }
    if (params.state) {
      searchParams.set('state', params.state)
    }
    if (params.medium) {
      searchParams.set('medium', params.medium)
    }
    
    const url = `${API_BASE_URL}/api/v1/export/csv/browse?${searchParams.toString()}`
    
    const response = await fetch(url)
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      throw new Error(`Export failed: ${response.status} ${response.statusText}. ${errorText}`)
    }
    
    // Get blob from response
    const blob = await response.blob()
    
    // Create download link and trigger click
    const filename = generateFilename(params)
    const downloadUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(downloadUrl)
    return
  }
  
  // Location-based search: use spatial endpoint
  searchParams.set('lat', String(params.lat))
  searchParams.set('lon', String(params.lon))
  searchParams.set('radius_miles', String(params.radius_miles ?? 500))
  
  // Optional filters
  if (params.chemical) {
    searchParams.set('chemical', params.chemical)
  }
  if (params.year) {
    searchParams.set('year', String(params.year))
  }
  if (params.state) {
    searchParams.set('state', params.state)
    searchParams.set('restrict_to_state', 'true')
  }
  if (params.medium) {
    searchParams.set('medium', params.medium)
  }
  if (params.bbox) {
    searchParams.set('bbox', params.bbox)
  }
  
  const url = `${API_BASE_URL}/api/v1/export/csv?${searchParams.toString()}`
  
  const response = await fetch(url)
  
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error')
    throw new Error(`Export failed: ${response.status} ${response.statusText}. ${errorText}`)
  }
  
  // Get blob from response
  const blob = await response.blob()
  
  // Create download link and trigger click
  const filename = generateFilename(params)
  const downloadUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(downloadUrl)
}

/**
 * Export a single facility's release data as CSV.
 * Fetches all years for the specified TRI facility.
 * 
 * @param triId TRI Facility ID (e.g., "89319BHPCP7MILE")
 * @returns Promise resolving when download is triggered
 */
export async function exportSingleFacilityCsv(triId: string): Promise<void> {
  // For single facility, we use the releases endpoint and format client-side
  const url = `${API_BASE_URL}/api/v1/facilities/${triId}/releases`
  
  const response = await fetch(url)
  
  if (!response.ok) {
    throw new Error(`Export failed: ${response.status} ${response.statusText}`)
  }
  
  const releases: Array<{
    reporting_year: number
    total_release_lbs: number | null
    air_release_lbs: number | null
    water_release_lbs: number | null
    land_release_lbs: number | null
    underground_release_lbs: number | null
  }> = await response.json()
  
  // Generate CSV content
  const headers = ['year', 'total_lbs', 'air_lbs', 'water_lbs', 'land_lbs', 'underground_lbs']
  const rows = releases.map(r => [
    r.reporting_year,
    r.total_release_lbs ?? '',
    r.air_release_lbs ?? '',
    r.water_release_lbs ?? '',
    r.land_release_lbs ?? '',
    r.underground_release_lbs ?? ''
  ].join(','))
  
  const csvContent = [headers.join(','), ...rows].join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' })
  
  // Generate filename with date
  const date = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  const filename = `toxmap-${triId}-${date}.csv`
  
  const downloadUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(downloadUrl)
}

/**
 * Export Superfund site contaminants as CSV.
 * 
 * @param epaId EPA Site ID (e.g., "VAD070358684")
 * @param siteName Site name for filename
 * @returns Promise resolving when download is triggered
 */
export async function exportSuperfundContaminantsCsv(
  epaId: string,
  siteName: string
): Promise<void> {
  const url = `${API_BASE_URL}/api/v1/superfund/${epaId}`
  
  const response = await fetch(url)
  
  if (!response.ok) {
    throw new Error(`Export failed: ${response.status} ${response.statusText}`)
  }
  
  const site = await response.json()
  const contaminants: Array<{
    name: string
    cas_number: string | null
    atsdr_url: string | null
    pubchem_url: string | null
  }> = site.contaminants || []
  
  // Generate CSV content (SEC 6.EXPORT.14: use escapeCsvField for all text)
  const headers = ['site_name', 'epa_id', 'contaminant', 'cas_number', 'atsdr_url', 'pubchem_url']
  const rows = contaminants.map(c => [
    escapeCsvField(siteName),
    escapeCsvField(epaId),
    escapeCsvField(c.name),
    escapeCsvField(c.cas_number),
    escapeCsvField(c.atsdr_url),
    escapeCsvField(c.pubchem_url)
  ].join(','))
  
  const csvContent = [headers.join(','), ...rows].join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' })
  
  const date = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  const filename = `superfund-${epaId}-contaminants-${date}.csv`
  
  const downloadUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(downloadUrl)
}

/**
 * Export current map view as PNG image.
 * Uses MapLibre's canvas toDataURL with attribution watermark.
 * 
 * @param mapCanvas The map's canvas element
 * @returns Promise resolving when download is triggered
 */
export async function exportMapImage(mapCanvas: HTMLCanvasElement): Promise<void> {
  // Create a new canvas to add attribution watermark
  const canvas = document.createElement('canvas')
  canvas.width = mapCanvas.width
  canvas.height = mapCanvas.height
  const ctx = canvas.getContext('2d')
  
  if (!ctx) {
    throw new Error('Could not create canvas context')
  }
  
  // Draw the map
  ctx.drawImage(mapCanvas, 0, 0)
  
  // Add attribution watermark (required by OpenStreetMap license)
  const attribution = '© OpenStreetMap contributors'
  ctx.font = '12px Arial'
  ctx.fillStyle = 'rgba(0, 0, 0, 0.7)'
  ctx.fillRect(10, canvas.height - 25, ctx.measureText(attribution).width + 10, 20)
  ctx.fillStyle = 'white'
  ctx.fillText(attribution, 15, canvas.height - 10)
  
  // Convert to PNG and trigger download
  const dataUrl = canvas.toDataURL('image/png')
  const timestamp = Date.now()
  const filename = `toxmap-map-${timestamp}.png`
  
  const link = document.createElement('a')
  link.href = dataUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
