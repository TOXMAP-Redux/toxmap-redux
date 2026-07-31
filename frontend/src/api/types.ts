/**
 * Shared TypeScript types matching the TOXMAP API contract.
 * These types mirror the Pydantic schemas in backend/app/schemas/.
 */

// ── Facilities ─────────────────────────────────────────────────────────────

export interface FacilityProperties {
  tri_facility_id: string
  name: string
  address: string
  city: string
  state_code: string
  naics_code: string | null
  total_release_lbs: number | null
  color_band: 'green' | 'yellow' | 'orange' | 'red'
  chemical_name: string | null
  reporting_year: number | null
  unit_of_measure: string | null
  marker_shape: 'circle'
}

export interface FacilityFeature {
  type: 'Feature'
  geometry: {
    type: 'Point'
    coordinates: [number, number] // [lon, lat]
  }
  properties: FacilityProperties
}

export interface FacilityCollection {
  type: 'FeatureCollection'
  features: FacilityFeature[]
  meta: {
    total_count: number
    lat: number
    lon: number
    radius_miles: number
    chemical: string | null
    year: number | null
    medium: string | null
    bbox: [number, number, number, number] | null
  }
}

export interface FacilityDetail {
  tri_facility_id: string
  name: string
  address: string
  city: string
  state_code: string
  zip_code: string | null
  naics_code: string | null
  primary_sic: string | null
  location: { lat: number; lon: number }
  top_chemicals: Array<{
    chemical_name: string
    total_release_lbs: number
  }>
}

// ── Releases ───────────────────────────────────────────────────────────────

export interface ReleaseEvent {
  reporting_year: number
  total_release_lbs: number | null
  air_release_lbs: number | null
  water_release_lbs: number | null
  land_release_lbs: number | null
  underground_release_lbs: number | null
  unit_of_measure: string
  form_type: string
}

// ── Chemicals ──────────────────────────────────────────────────────────────

export interface Chemical {
  id: number
  cas_number: string | null
  name: string
  category: string | null
  atsdr_url: string | null
  pubchem_url: string | null
}

// ── Superfund ──────────────────────────────────────────────────────────────

/** Properties on a GeoJSON Feature from GET /api/v1/superfund */
export interface SuperfundProperties {
  id: number
  epa_id: string
  name: string
  city: string
  state_code: string
  status: 'NPL' | 'Proposed' | 'Deleted'
  hrs_score: number | null
  npl_date: string | null
  /** Summary contaminant names array (for list display in non-detail context) */
  contaminants: string[]
  marker_shape: 'diamond'
}

export interface SuperfundFeature {
  type: 'Feature'
  geometry: { type: 'Point'; coordinates: [number, number] }
  properties: SuperfundProperties
}

export interface SuperfundCollection {
  type: 'FeatureCollection'
  features: SuperfundFeature[]
  meta: {
    total_count: number
    query: {
      lat: number
      lon: number
      radius_miles: number
      chemical: string | null
      state: string | null
      restrict_to_state: boolean
      status: string | null
    }
  }
}

/** One contaminant in a Superfund detail response */
export interface SuperfundContaminant {
  name: string
  cas_number: string | null
  atsdr_url: string | null
}

/** Full site detail from GET /api/v1/superfund/{epa_id} */
export interface SuperfundDetail {
  id: number
  epa_id: string
  name: string
  address: string | null
  city: string
  state_code: string
  zip_code: string | null
  county: string | null
  status: 'NPL' | 'Proposed' | 'Deleted'
  hrs_score: number | null
  npl_date: string | null
  contaminants: SuperfundContaminant[]
  epa_progress_url: string | null
  location: { lat: number; lon: number }
}

// ── Demographics / Census ──────────────────────────────────────────────────

/** Properties on a county GeoJSON Feature from GET /api/v1/demographics/county */
export interface DemographicProperties {
  fips_code: string
  name: string
  state_code: string
  total_pop: number | null
  median_income: number | null
  pct_under_18: number | null
  pct_over_65: number | null
  pct_nonwhite: number | null
  cancer_mortality_male_per_100k: number | null
  cancer_mortality_female_per_100k: number | null
  heart_disease_mortality_per_100k: number | null
}

export interface DemographicFeature {
  type: 'Feature'
  geometry: GeoJSON.Polygon | GeoJSON.MultiPolygon
  properties: DemographicProperties
}

/** Units metadata for rendering legend with proper labels */
export interface DemographicUnits {
  total_pop: string
  median_income: string
  pct_under_18: string
  pct_over_65: string
  pct_nonwhite: string
  cancer_mortality_male_per_100k: string
  cancer_mortality_female_per_100k: string
  heart_disease_mortality_per_100k: string
}

export interface DemographicCollection {
  type: 'FeatureCollection'
  features: DemographicFeature[]
  meta: {
    units: DemographicUnits
  }
}

/** Demographic sub-layer type — determines color scale and property to render */
export type DemographicLayer =
  | 'total_pop'
  | 'pct_under_18'
  | 'pct_over_65'
  | 'pct_nonwhite'
  | 'median_income'
  | 'cancer_mortality_male_per_100k'
  | 'cancer_mortality_female_per_100k'
  | 'heart_disease_mortality_per_100k'

// ── Meta ───────────────────────────────────────────────────────────────────

export interface MetaResponse {
  source: string
  vintage_label: string
  available_years: number[]
  latest_year: number
  total_facility_count: number
  total_release_event_count: number
}

// ── Search ─────────────────────────────────────────────────────────────────

/** Parameters passed to useViewportFacilities. All from user search + map state. */
export interface SearchParams {
  lat: number
  lon: number
  radiusMiles: number
  chemical: string
  year: string
  medium: string
  state: string
  restrictToState: boolean
  bbox: [number, number, number, number] | null
}

/** State holding the geocoded, submitted search. Null before first search. */
export interface SubmittedSearch {
  /** Latitude of search center. Null for nationwide search (no location). */
  lat: number | null
  /** Longitude of search center. Null for nationwide search (no location). */
  lon: number | null
  chemical: string
  chemicalObj: Chemical | null // full object for ATSDR/PubChem links
  year: string
  /** If set, results are filtered to this state only (state dropdown = filter) */
  state: string
  radiusMiles: number
  /** Which dataset the search targets — controls results table mode */
  dataset: 'tri' | 'superfund' | 'both'
}
