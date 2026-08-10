/**
 * TOXMAP Application Root — Phase 5: Demographics Overlay
 *
 * Stories: 5.1.1–5.4.2 (Epics 5.1–5.4)
 * New in Phase 5:
 *   - CensusHealthPanel: "US Census & Health Data" (UX Invariant 4) — story 5.1.1
 *   - Year/Category/Sub-layer tabs — stories 5.1.2–5.1.5
 *   - County choropleth fill layer — story 5.2.1
 *   - Zoom notice for zoomed-in views — story 5.2.2
 *   - InlineLegend with always-visible values (UX Invariant 5) — story 5.3.1
 *   - Clear layer button — story 5.3.3
 *   - Co-occurrence disclaimer on mortality tabs only (UX Invariant 10) — story 5.4.1
 *   - Male/Female breakdown for mortality — story 5.4.2
 *
 * DATA FLOW (2026-07-28):
 * TRI circles: useMapFacilities fetches ALL facilities once via /browse endpoint.
 * Superfund diamonds: useSuperfundViewport fetches ALL sites once via /browse endpoint.
 * Demographics: useDemographics fetches county polygons for choropleth layer.
 *   → All layers: MapLibre handles viewport rendering, toggle via setLayoutProperty.
 * Sidebar count: filterByBbox filters map data client-side by current viewport.
 *   → "X in view" updates without refetching.
 */
import { useCallback, useMemo, useState, useRef, useEffect } from 'react'
import type { ViewState } from 'react-map-gl/maplibre'
import { MapContainer } from './components/Map/MapContainer'
import { Sidebar, type ActivePanel } from './components/Sidebar/Sidebar'
import { FacilityPopup } from './components/FacilityDetail/FacilityPopup'
import { FacilityDrawer } from './components/FacilityDetail/FacilityDrawer'
import { SuperfundDrawer } from './components/FacilityDetail/SuperfundDrawer'
import { DataVintageLabel } from './components/DataVintageLabel'
import { InterpretationBanner } from './components/Onboarding/InterpretationBanner'
import { InlineLegend } from './components/Demographics'
import type { CensusYearValue } from './components/Demographics/CensusHealthPanel'
import { useMapFacilities, filterByBbox, type MapSearchParams } from './hooks/useMapFacilities'
import { useSuperfundViewport } from './hooks/useSuperfundViewport'
import { useSuperfundSearch } from './hooks/useSuperfundSearch'
import { useDemographics } from './hooks/useDemographics'
import { useMeta } from './hooks/useMeta'
import { geocodeLocation, type GeocodeResult } from './api/geocode'
import { exportFacilitiesCsv } from './api/export'
import type { FacilityFeature, SubmittedSearch, SuperfundFeature, SuperfundCollection, DemographicLayer } from './api/types'
import type { SuperfundSearchParams } from './api/superfund'
import type { SearchFormValues } from './components/Sidebar/SearchPanel'
import { isContinentalUS, CONUS_FILTER } from './components/Sidebar/SearchPanel'

/** Default US overview viewport */
const INITIAL_VIEW: ViewState = {
  latitude: 38.5,
  longitude: -96,
  zoom: 4,
  bearing: 0,
  pitch: 0,
  padding: { top: 0, bottom: 0, left: 0, right: 0 },
}

/** Approximate center coordinates and zoom levels for US states (used for state-only browse) */
const STATE_CENTERS: Record<string, { lat: number; lon: number; zoom: number }> = {
  AL: { lat: 32.7, lon: -86.7, zoom: 6.5 },
  AK: { lat: 64.0, lon: -153.0, zoom: 4 },
  AZ: { lat: 34.2, lon: -111.6, zoom: 6 },
  AR: { lat: 34.8, lon: -92.2, zoom: 6.5 },
  CA: { lat: 37.2, lon: -119.4, zoom: 5.5 },
  CO: { lat: 39.0, lon: -105.5, zoom: 6 },
  CT: { lat: 41.6, lon: -72.7, zoom: 8 },
  DE: { lat: 39.0, lon: -75.5, zoom: 8 },
  FL: { lat: 28.1, lon: -81.6, zoom: 6 },
  GA: { lat: 32.6, lon: -83.4, zoom: 6.5 },
  HI: { lat: 20.8, lon: -156.3, zoom: 6.5 },
  ID: { lat: 44.4, lon: -114.7, zoom: 5.5 },
  IL: { lat: 40.0, lon: -89.2, zoom: 6 },
  IN: { lat: 40.0, lon: -86.3, zoom: 6.5 },
  IA: { lat: 42.0, lon: -93.5, zoom: 6.5 },
  KS: { lat: 38.5, lon: -98.4, zoom: 6 },
  KY: { lat: 37.8, lon: -85.3, zoom: 6.5 },
  LA: { lat: 31.0, lon: -91.9, zoom: 6.5 },
  ME: { lat: 45.4, lon: -69.0, zoom: 6 },
  MD: { lat: 39.0, lon: -76.8, zoom: 7 },
  MA: { lat: 42.2, lon: -71.5, zoom: 7.5 },
  MI: { lat: 44.3, lon: -85.4, zoom: 6 },
  MN: { lat: 46.3, lon: -94.3, zoom: 5.5 },
  MS: { lat: 32.7, lon: -89.7, zoom: 6.5 },
  MO: { lat: 38.4, lon: -92.5, zoom: 6.5 },
  MT: { lat: 47.0, lon: -109.6, zoom: 5.5 },
  NE: { lat: 41.5, lon: -99.8, zoom: 6 },
  NV: { lat: 39.3, lon: -116.6, zoom: 5.5 },
  NH: { lat: 43.6, lon: -71.5, zoom: 7 },
  NJ: { lat: 40.1, lon: -74.7, zoom: 7.5 },
  NM: { lat: 34.4, lon: -106.1, zoom: 6 },
  NY: { lat: 43.0, lon: -75.5, zoom: 6 },
  NC: { lat: 35.5, lon: -79.8, zoom: 6.5 },
  ND: { lat: 47.4, lon: -100.3, zoom: 6 },
  OH: { lat: 40.2, lon: -82.8, zoom: 6.5 },
  OK: { lat: 35.5, lon: -97.5, zoom: 6 },
  OR: { lat: 43.9, lon: -120.6, zoom: 6 },
  PA: { lat: 40.9, lon: -77.8, zoom: 6.5 },
  RI: { lat: 41.7, lon: -71.5, zoom: 9 },
  SC: { lat: 33.8, lon: -80.9, zoom: 7 },
  SD: { lat: 44.4, lon: -100.2, zoom: 6 },
  TN: { lat: 35.8, lon: -86.3, zoom: 6.5 },
  TX: { lat: 31.5, lon: -99.4, zoom: 5.5 },
  UT: { lat: 39.3, lon: -111.7, zoom: 6 },
  VT: { lat: 44.0, lon: -72.7, zoom: 7 },
  VA: { lat: 37.5, lon: -78.8, zoom: 6.5 },
  WA: { lat: 47.4, lon: -120.5, zoom: 6 },
  WV: { lat: 38.6, lon: -80.6, zoom: 7 },
  WI: { lat: 44.6, lon: -89.7, zoom: 6 },
  WY: { lat: 43.0, lon: -107.5, zoom: 6 },
  DC: { lat: 38.9, lon: -77.0, zoom: 11 },
  PR: { lat: 18.2, lon: -66.5, zoom: 8 },
  VI: { lat: 18.3, lon: -64.8, zoom: 9 },
  GU: { lat: 13.4, lon: 144.8, zoom: 10 },
  AS: { lat: -14.3, lon: -170.7, zoom: 10 },
  MP: { lat: 15.2, lon: 145.8, zoom: 8 },
}

/**
 * Root application component.
 * Manages all global state: map viewport, search, facility selection.
 */
export default function App(): JSX.Element {
  // ── Map viewport ──────────────────────────────────────────────────────────
  const [viewState, setViewState] = useState<ViewState>(INITIAL_VIEW)
  const viewStateRef = useRef(viewState)
  useEffect(() => { viewStateRef.current = viewState }, [viewState])
  const [mapBbox, setMapBbox] = useState<[number, number, number, number] | null>(null)
  
  // PERFORMANCE: Use uncontrolled map mode - store flyTo function from map
  const flyToRef = useRef<((lat: number, lon: number, zoom: number) => void) | null>(null)
  const handleMapReady = useCallback((flyTo: (lat: number, lon: number, zoom: number) => void) => {
    flyToRef.current = flyTo
  }, [])

  // ── Sidebar + search state ────────────────────────────────────────────────
  const [activePanel, setActivePanel] = useState<ActivePanel>('map-contents')
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const [sidebarWidthPx, setSidebarWidthPx] = useState(400)
  const [facilityDrawerWidthPx, setFacilityDrawerWidthPx] = useState(420)
  const [superfundDrawerWidthPx, setSuperfundDrawerWidthPx] = useState(340)
  const [submittedSearch, setSubmittedSearch] = useState<SubmittedSearch | null>(null)
  const [geocodeError, setGeocodeError] = useState<string | null>(null)
  const [resolvedGeocode, setResolvedGeocode] = useState<GeocodeResult | null>(null)
  const [exportLoading, setExportLoading] = useState(false)

  // ── Facility selection (TRI) ──────────────────────────────────────────────
  const [selectedFacility, setSelectedFacility] = useState<FacilityFeature | null>(null)
  const [detailFacilityId, setDetailFacilityId] = useState<string | null>(null)
  const [highlightedFacilityId, setHighlightedFacilityId] = useState<string | null>(null)

  // ── Superfund site selection ──────────────────────────────────────────────
  const [selectedSuperfundEpaId, setSelectedSuperfundEpaId] = useState<string | null>(null)
  const [showSuperfundLayer, setShowSuperfundLayer] = useState(true)
  const [showTRILayer, setShowTRILayer] = useState(true)

  // ── Demographics layer (Phase 5) ──────────────────────────────────────────
  const [selectedDemographicLayer, setSelectedDemographicLayer] = useState<DemographicLayer | null>(null)
  const [censusYear, setCensusYear] = useState<CensusYearValue>(2000)

  // ── Data ──────────────────────────────────────────────────────────────────
  const { meta } = useMeta()

  // TRI map params:
  // - Browse mode (no search): null → hook fetches ALL facilities via /browse endpoint
  // - Search mode: search location + radius + filters
  // MapLibre handles viewport subsetting client-side from the fetched data.
  const triMapParams = useMemo<MapSearchParams | null>(() => {
    if (submittedSearch?.dataset === 'tri' || submittedSearch?.dataset === 'both') {
      // CONUS filter is handled client-side; don't pass state to API
      const isConusFilter = submittedSearch.state === CONUS_FILTER
      const stateForApi = isConusFilter ? undefined : (submittedSearch.state || undefined)
      const hasStateFilter = Boolean(stateForApi)
      return {
        lat: submittedSearch.lat,
        lon: submittedSearch.lon,
        radiusMiles: submittedSearch.radiusMiles,
        chemical: submittedSearch.chemical || undefined,
        year: submittedSearch.year || undefined,
        state: stateForApi,
        // Option C: state dropdown = filter. Always restrict when state is selected.
        restrictToState: hasStateFilter,
        // ADR-007: Skip chemical family expansion if user clicked "Search exact term only"
        exactMatch: submittedSearch.exactMatch,
      }
    }
    // Browse mode: null → fetch ALL facilities without radius constraint
    return null
  }, [submittedSearch])

  // Build Superfund search params when dataset=superfund or both and a search was submitted.
  // Returns null for nationwide searches (lat/lon = null) — the always-on Superfund layer
  // will show all sites, and the results table will display filtered viewport sites.
  const superfundSearchParams = useMemo<SuperfundSearchParams | null>(() => {
    if (!submittedSearch || (submittedSearch.dataset !== 'superfund' && submittedSearch.dataset !== 'both')) return null
    // Nationwide mode: use the always-on layer instead of radius search
    if (submittedSearch.lat === null || submittedSearch.lon === null) return null
    // CONUS filter is handled client-side; don't pass state to API
    const isConusFilter = submittedSearch.state === CONUS_FILTER
    const stateForApi = isConusFilter ? undefined : (submittedSearch.state || undefined)
    const hasStateFilter = Boolean(stateForApi)
    return {
      lat: submittedSearch.lat,
      lon: submittedSearch.lon,
      radiusMiles: submittedSearch.radiusMiles,
      chemical: submittedSearch.chemical || undefined,
      state: stateForApi,
      // Option C: state dropdown = filter. Always restrict when state is selected.
      restrictToState: hasStateFilter,
    }
  }, [submittedSearch])

  // TRI facilities for the MAP (all data, no bbox filtering)
  // This data is passed to MapContainer and should be stable per search.
  const { data: triMapFacilities, loading, error } = useMapFacilities(triMapParams)

  // TRI facilities filtered by current viewport (for sidebar "X in view" count)
  // Also applies CONUS filter if selected (client-side filtering for Continental US)
  const triViewportFacilities = useMemo(() => {
    let filtered = filterByBbox(triMapFacilities, mapBbox)
    // Apply CONUS filter client-side
    if (filtered && submittedSearch?.state === CONUS_FILTER) {
      filtered = {
        ...filtered,
        features: filtered.features.filter((f) => isContinentalUS(f.properties.state_code)),
        meta: {
          ...filtered.meta,
          total_count: filtered.features.filter((f) => isContinentalUS(f.properties.state_code)).length,
        },
      }
    }
    return filtered
  }, [triMapFacilities, mapBbox, submittedSearch?.state])

  // For nationwide searches (no location), show ALL matching facilities, not just viewport
  // For location-based searches, continue showing viewport-filtered results
  const triAllResults = useMemo(() => {
    if (!triMapFacilities) return null
    // Apply CONUS filter if selected
    if (submittedSearch?.state === CONUS_FILTER) {
      const filtered = triMapFacilities.features.filter((f) => isContinentalUS(f.properties.state_code))
      return {
        ...triMapFacilities,
        features: filtered,
        meta: {
          ...triMapFacilities.meta,
          total_count: filtered.length,
        },
      }
    }
    return triMapFacilities
  }, [triMapFacilities, submittedSearch?.state])

  // Results table: 
  // - Nationwide search (lat/lon = null): show ALL results (not viewport-filtered)
  // - Location search: show ALL results within search radius (not viewport-filtered)
  //   The API already constrains by radius; we don't need additional viewport filtering.
  //   This prevents flickering when the map bbox changes during scroll or re-render.
  const triSearchResults = useMemo(() => {
    if (submittedSearch?.dataset !== 'tri' && submittedSearch?.dataset !== 'both') return null
    // Use all results from the search (already filtered by radius on server side)
    // Nationwide search returns all matching facilities; location search returns within radius.
    return triAllResults
  }, [submittedSearch, triAllResults])

  // Always-on Superfund layer: fetches ALL sites once (no bbox/radius constraint)
  const { data: superfundViewportSites } = useSuperfundViewport()

  // Superfund sites filtered by current viewport (for sidebar "X in view" count)
  const superfundInViewCount = useMemo(() => {
    if (!superfundViewportSites || !mapBbox) return superfundViewportSites?.meta.total_count ?? null
    const [minLon, minLat, maxLon, maxLat] = mapBbox
    const filtered = superfundViewportSites.features.filter((f) => {
      const [lon, lat] = f.geometry.coordinates
      return lon >= minLon && lon <= maxLon && lat >= minLat && lat <= maxLat
    })
    return filtered.length
  }, [superfundViewportSites, mapBbox])

  // Superfund search results (only active in superfund or both dataset mode)
  const { data: superfundSearchResults, loading: superfundLoading, error: superfundError } = useSuperfundSearch(superfundSearchParams)

  // For nationwide chemical searches, filter Superfund sites client-side by contaminant name
  // (since /api/v1/superfund/browse doesn't support chemical filtering)
  // Also applies CONUS filter if selected (client-side filtering for Continental US)
  const superfundResultsForDisplay = useMemo<SuperfundCollection | null>(() => {
    const isConusFilter = submittedSearch?.state === CONUS_FILTER
    
    // Helper to apply CONUS filter to a collection
    const applyConusFilter = (collection: SuperfundCollection): SuperfundCollection => {
      if (!isConusFilter) return collection
      const filtered = collection.features.filter((f) => isContinentalUS(f.properties.state_code))
      return {
        ...collection,
        features: filtered,
        meta: {
          ...collection.meta,
          total_count: filtered.length,
        },
      }
    }
    
    // If we have location-based search results, use those (with CONUS filter if applicable)
    if (superfundSearchResults) {
      return applyConusFilter(superfundSearchResults)
    }
    
    // If not in superfund or both mode, no results
    if (!submittedSearch || (submittedSearch.dataset !== 'superfund' && submittedSearch.dataset !== 'both')) {
      return null
    }
    
    // Nationwide mode: filter the always-on layer by chemical and/or state (and CONUS if applicable)
    if (submittedSearch.lat === null && superfundViewportSites) {
      const hasChemicalFilter = Boolean(submittedSearch.chemical?.trim())
      const hasStateFilter = submittedSearch.state && submittedSearch.state !== CONUS_FILTER && submittedSearch.state !== 'All'
      
      // At least one filter must be active (chemical or state)
      if (!hasChemicalFilter && !hasStateFilter && !isConusFilter) {
        return null
      }
      
      let filtered = superfundViewportSites.features
      
      // Apply chemical filter
      if (hasChemicalFilter) {
        const chemicalUpper = submittedSearch.chemical!.toUpperCase()
        filtered = filtered.filter((f) =>
          f.properties.contaminants.some((c) => c.toUpperCase().includes(chemicalUpper))
        )
      }
      
      // Apply state filter (non-CONUS)
      if (hasStateFilter) {
        const stateUpper = submittedSearch.state!.toUpperCase()
        filtered = filtered.filter((f) => f.properties.state_code === stateUpper)
      }
      
      // Apply CONUS filter
      if (isConusFilter) {
        filtered = filtered.filter((f) => isContinentalUS(f.properties.state_code))
      }
      return {
        type: 'FeatureCollection' as const,
        features: filtered,
        meta: {
          total_count: filtered.length,
          query: {
            lat: 0,
            lon: 0,
            radius_miles: 0,
            chemical: submittedSearch.chemical || null,
            state: submittedSearch.state || null,
            restrict_to_state: Boolean(hasStateFilter),
            status: null,
          },
        },
      }
    }
    
    return null
  }, [superfundSearchResults, submittedSearch, superfundViewportSites])

  // Superfund sites to show on the map:
  // - Browse mode (no search): all Superfund sites
  // - Search with dataset "both" or "superfund": filtered results only
  // - Search with dataset "tri" only: no Superfund (user only wants TRI)
  const superfundSitesForMap = useMemo<SuperfundCollection | null>(() => {
    // No search active: browse mode, show all sites
    if (!submittedSearch) {
      return superfundViewportSites
    }
    // Search active with TRI only: don't show Superfund markers
    if (submittedSearch.dataset === 'tri') {
      return null
    }
    // Search active with "both" or "superfund": show filtered results
    return superfundResultsForDisplay
  }, [submittedSearch, superfundViewportSites, superfundResultsForDisplay])

  // TRI facilities to show on the map:
  // - Browse mode (no search): all TRI facilities
  // - Search active but loading: null (prevents rendering 30K old features during flyTo)
  // - Search active: filtered results (includes CONUS filter)
  // - Search with dataset "superfund" only: no TRI (user only wants Superfund)
  const triFacilitiesForMap = useMemo(() => {
    // No search active: browse mode, show all facilities
    if (!submittedSearch) {
      return triMapFacilities
    }
    // Search active but still loading: don't show stale 30K browse data
    // This prevents CPU spike from rendering 30K GeoJSON features during flyTo animation
    if (loading) {
      return null
    }
    // Search active with Superfund only: don't show TRI markers
    if (submittedSearch.dataset === 'superfund') {
      return null
    }
    // Search active with "both" or "tri": show filtered results
    // triAllResults has CONUS filter applied when state=CONUS_FILTER
    return triAllResults
  }, [submittedSearch, triMapFacilities, triAllResults, loading])

  // Demographics data for choropleth layer (story 5.2.1)
  // Fetch all counties when demographic layer is selected
  // If a search has been performed, filter to the searched state
  // C-002: Pass selected census year to API
  const { data: demographicsData } = useDemographics(
    selectedDemographicLayer
      ? {
          ...(submittedSearch?.state ? { state: submittedSearch.state } : {}),
          censusYear,
        }
      : undefined
  )

  // Determine which results to show and loading/error state
  const activeLoading = submittedSearch?.dataset === 'superfund' ? superfundLoading
    : submittedSearch?.dataset === 'both' ? (loading || superfundLoading)
    : loading
  const activeError = submittedSearch?.dataset === 'superfund' ? superfundError
    : submittedSearch?.dataset === 'both' ? (error || superfundError)
    : error

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleSearchSubmit = useCallback(async (values: SearchFormValues) => {
    setGeocodeError(null)
    setResolvedGeocode(null)
    
    const locationTrimmed = values.location.trim()
    const chemicalTrimmed = values.chemical.trim()
    const hasStateFilter = values.state && values.state !== 'All'
    
    // Browse/search modes without location:
    // 1. State-only browse: just a state filter selected
    // 2. Nationwide chemical search: chemical specified (optionally with state filter)
    if (!locationTrimmed) {
      // Need at least a chemical OR a state filter
      if (!chemicalTrimmed && !hasStateFilter) {
        setGeocodeError('Please enter a chemical, location, or select a state to search.')
        return
      }
      
      // Reset bbox and set browse search (lat/lon = null)
      setMapBbox(null)
      
      setSubmittedSearch({
        lat: null,
        lon: null,
        chemical: values.chemical,
        chemicalObj: values.chemicalObj,
        year: values.year,
        state: values.state || '',
        radiusMiles: 25, // Not used for nationwide, but required by interface
        dataset: values.dataset,
        exactMatch: values.exactMatch,
      })

      // Zoom map: state-specific if state filter, otherwise US overview
      if (flyToRef.current) {
        if (hasStateFilter && STATE_CENTERS[values.state]) {
          const { lat, lon, zoom } = STATE_CENTERS[values.state]
          flyToRef.current(lat, lon, zoom)
        } else {
          flyToRef.current(38.5, -96, 4)
        }
      }

      // Switch sidebar to search results (UX Invariant 1)
      setActivePanel('search')
      setSelectedFacility(null)
      setDetailFacilityId(null)
      setHighlightedFacilityId(null)
      return
    }
    
    // Location-based search: geocode with viewport bias for better local results
    const geocoded = await geocodeLocation(values.location, {
      biasLat: viewStateRef.current.latitude,
      biasLon: viewStateRef.current.longitude,
    })
    if (!geocoded) {
      setGeocodeError(`Could not geocode "${values.location}". Try a different location.`)
      return
    }

    // Store resolved geocode for display with confidence info
    setResolvedGeocode(geocoded)

    // Reset bbox before setting new search so the first request has no stale viewport constraint.
    // The map will zoom to the new location, fire onMoveEnd, and update bbox for subsequent requests.
    setMapBbox(null)

    setSubmittedSearch({
      lat: geocoded.lat,
      lon: geocoded.lon,
      chemical: values.chemical,
      chemicalObj: values.chemicalObj,
      year: values.year,
      // Use explicit state filter if set, otherwise use geocoded state
      state: values.state || geocoded.state || '',
      radiusMiles: 25,
      dataset: values.dataset,
      exactMatch: values.exactMatch,
    })

    // Zoom map to the geocoded location
    if (flyToRef.current) {
      flyToRef.current(geocoded.lat, geocoded.lon, 10)
    }

    // Switch sidebar to search results (UX Invariant 1)
    setActivePanel('search')
    setSelectedFacility(null)
    setDetailFacilityId(null)
    setHighlightedFacilityId(null)
  }, [])

  const handleFacilityClick = useCallback((facility: FacilityFeature) => {
    setSelectedFacility(facility)
    setDetailFacilityId(null)
    setSelectedSuperfundEpaId(null)
  }, [])

  const handleSuperfundSiteClick = useCallback((site: SuperfundFeature) => {
    setSelectedSuperfundEpaId(site.properties.epa_id)
    setSelectedFacility(null)
    setDetailFacilityId(null)
  }, [])

  const handleOpenDetail = useCallback((id: string, type: 'tri' | 'superfund') => {
    if (type === 'superfund') {
      setSelectedSuperfundEpaId(id)
      setDetailFacilityId(null)
    } else {
      setDetailFacilityId(id)
      setSelectedSuperfundEpaId(null)
    }
    setSelectedFacility(null)
  }, [])

  const handleClosePopup = useCallback(() => {
    setSelectedFacility(null)
  }, [])

  const handleCloseDrawer = useCallback(() => {
    setDetailFacilityId(null)
  }, [])

  const handleCloseSuperfundDrawer = useCallback(() => {
    setSelectedSuperfundEpaId(null)
  }, [])

  /**
   * Handle CSV export (story 6.EXPORT.1–4).
   * Uses the current search parameters to fetch and download CSV.
   */
  const handleExport = useCallback(async () => {
    if (!submittedSearch) return
    
    setExportLoading(true)
    try {
      await exportFacilitiesCsv({
        lat: submittedSearch.lat,
        lon: submittedSearch.lon,
        radius_miles: submittedSearch.radiusMiles,
        chemical: submittedSearch.chemical || undefined,
        year: submittedSearch.year ? parseInt(submittedSearch.year, 10) : undefined,
        state: submittedSearch.state && submittedSearch.state !== CONUS_FILTER 
          ? submittedSearch.state 
          : undefined,
      })
    } catch (err) {
      console.error('Export failed:', err)
      // Could add toast notification here
      window.alert('Export failed. Please try again.')
    } finally {
      setExportLoading(false)
    }
  }, [submittedSearch])

  const handleBoundsChange = useCallback((bbox: [number, number, number, number]) => {
    setMapBbox(bbox)
  }, [])

  const combinedError = geocodeError ?? activeError

  // Sidebar expanded = 20rem = 320px; collapsed = 2.5rem = 40px.
  // Passed to MapContainer so camera padding and popup pan guard use the correct offset.
  const sidebarWidth = isSidebarCollapsed ? 40 : sidebarWidthPx

  return (
    <div
      className="toxmap-root relative h-screen w-screen overflow-hidden"
      style={{ position: 'relative', height: '100vh', width: '100vw', overflow: 'hidden' }}
    >      {/* Full-viewport map (background layer) */}
      <MapContainer
        viewState={viewState}
        onViewStateChange={setViewState}
        onBoundsChange={handleBoundsChange}
        onMapReady={handleMapReady}
        facilities={triFacilitiesForMap}
        selectedFacilityId={selectedFacility?.properties.tri_facility_id ?? null}
        highlightedFacilityId={highlightedFacilityId}
        onFacilityClick={handleFacilityClick}
        showTRILayer={showTRILayer}
        superfundSites={superfundSitesForMap}
        showSuperfundLayer={showSuperfundLayer}
        onSuperfundSiteClick={handleSuperfundSiteClick}
        selectedSuperfundEpaId={selectedSuperfundEpaId}
        sidebarWidth={sidebarWidth}
        demographics={demographicsData}
        demographicLayer={selectedDemographicLayer}
      >
        {/* Facility popup — shown on marker click */}
        {selectedFacility && (
          <FacilityPopup
            facility={selectedFacility}
            onClose={handleClosePopup}
            onOpenDetail={handleOpenDetail}
          />
        )}
      </MapContainer>

      {/* Sidebar overlay (left panel) */}
      <Sidebar
        activePanel={activePanel}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed((c) => !c)}
        onPanelChange={setActivePanel}
        onSearch={handleSearchSubmit}
        sidebarWidth={sidebarWidthPx}
        onSidebarWidthChange={setSidebarWidthPx}
        facilities={triSearchResults}
        superfundResults={superfundResultsForDisplay}
        loading={activeLoading}
        error={combinedError}
        highlightedFacilityId={highlightedFacilityId}
        onHighlight={setHighlightedFacilityId}
        onFacilitySelect={handleOpenDetail}
        resolvedGeocode={resolvedGeocode}
        latestYear={meta?.latest_year ?? null}
        showTRILayer={showTRILayer}
        onToggleTRILayer={() => setShowTRILayer((v) => !v)}
        showSuperfundLayer={showSuperfundLayer}
        onToggleSuperfundLayer={() => setShowSuperfundLayer((v) => !v)}
        triViewportCount={triViewportFacilities?.meta.total_count ?? null}
        triViewportLoading={loading}
        superfundViewportCount={superfundInViewCount}
        superfundViewportLoading={false}
        selectedDemographicLayer={selectedDemographicLayer}
        onDemographicLayerSelect={setSelectedDemographicLayer}
        censusYear={censusYear}
        onCensusYearChange={setCensusYear}
        onExport={handleExport}
        exportLoading={exportLoading}
      />

      {/* Facility detail drawer (right panel — TRI mode) */}
      {detailFacilityId && (
        <FacilityDrawer
          facilityId={detailFacilityId}
          onClose={handleCloseDrawer}
          selectedYear={submittedSearch?.year || null}
          width={facilityDrawerWidthPx}
          onWidthChange={setFacilityDrawerWidthPx}
        />
      )}

      {/* Superfund detail drawer (right panel — Superfund mode, story 4.2.1) */}
      {selectedSuperfundEpaId && (
        <SuperfundDrawer
          epaId={selectedSuperfundEpaId}
          onClose={handleCloseSuperfundDrawer}
          width={superfundDrawerWidthPx}
          onWidthChange={setSuperfundDrawerWidthPx}
        />
      )}

      {/* Demographic layer legend — bottom left overlay (stories 5.3.1–5.3.3) */}
      {selectedDemographicLayer && demographicsData && (
        <div
          style={{
            position: 'absolute',
            bottom: '40px',
            left: sidebarWidth + 16,
            zIndex: 20,
          }}
        >
          <InlineLegend
            layer={selectedDemographicLayer}
            units={demographicsData.meta.units}
            onClear={() => setSelectedDemographicLayer(null)}
          />
        </div>
      )}

      {/* Data vintage label — map footer (story 3.1.5) */}
      <DataVintageLabel
        vintageLabel={meta?.vintage_label ?? null}
      />

      {/* Interpretation banner (story 3.6.2) */}
      <InterpretationBanner />
    </div>
  )
}
