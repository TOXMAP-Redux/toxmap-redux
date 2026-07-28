/**
 * TOXMAP Application Root — Phase 4: Superfund Overlay
 *
 * Stories: 4.1.1–4.3.1 (Epics 4.1–4.3)
 * New in Phase 4:
 *   - Superfund diamond markers on map (always-on layer) — story 4.1.1
 *   - Superfund layer toggle in MapContentsPanel — story 4.1.2
 *   - Superfund search results in dataset=superfund mode — story 4.1.3
 *   - SuperfundDrawer: EPA ID, HRS score, contaminants, EPA progress link — 4.2.1–4.2.3
 *   - Unified TRI + Superfund legend — story 4.3.1
 *   - UX Invariant 6: distinct TRI circles vs Superfund diamonds
 *
 * DATA FLOW (2026-07-28):
 * TRI circles: useMapFacilities fetches ALL facilities once via /browse endpoint.
 * Superfund diamonds: useSuperfundViewport fetches ALL sites once via /browse endpoint.
 *   → Both layers: MapLibre handles viewport rendering, toggle via setLayoutProperty.
 * Sidebar count: filterByBbox filters map data client-side by current viewport.
 *   → "X in view" updates without refetching.
 */
import { useCallback, useMemo, useState } from 'react'
import type { ViewState } from 'react-map-gl/maplibre'
import { MapContainer } from './components/Map/MapContainer'
import { Sidebar, type ActivePanel } from './components/Sidebar/Sidebar'
import { FacilityPopup } from './components/FacilityDetail/FacilityPopup'
import { FacilityDrawer } from './components/FacilityDetail/FacilityDrawer'
import { SuperfundDrawer } from './components/FacilityDetail/SuperfundDrawer'
import { DataVintageLabel } from './components/DataVintageLabel'
import { InterpretationBanner } from './components/Onboarding/InterpretationBanner'
import { useMapFacilities, filterByBbox, type MapSearchParams } from './hooks/useMapFacilities'
import { useSuperfundViewport } from './hooks/useSuperfundViewport'
import { useSuperfundSearch } from './hooks/useSuperfundSearch'
import { useMeta } from './hooks/useMeta'
import { geocodeLocation } from './api/geocode'
import type { FacilityFeature, SubmittedSearch, SuperfundFeature } from './api/types'
import type { SuperfundSearchParams } from './api/superfund'
import type { SearchFormValues } from './components/Sidebar/SearchPanel'

/** Default US overview viewport */
const INITIAL_VIEW: ViewState = {
  latitude: 38.5,
  longitude: -96,
  zoom: 4,
  bearing: 0,
  pitch: 0,
  padding: { top: 0, bottom: 0, left: 0, right: 0 },
}

/**
 * Root application component.
 * Manages all global state: map viewport, search, facility selection.
 */
export default function App(): JSX.Element {
  // ── Map viewport ──────────────────────────────────────────────────────────
  const [viewState, setViewState] = useState<ViewState>(INITIAL_VIEW)
  const [mapBbox, setMapBbox] = useState<[number, number, number, number] | null>(null)

  // ── Sidebar + search state ────────────────────────────────────────────────
  const [activePanel, setActivePanel] = useState<ActivePanel>('map-contents')
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const [submittedSearch, setSubmittedSearch] = useState<SubmittedSearch | null>(null)
  const [geocodeError, setGeocodeError] = useState<string | null>(null)

  // ── Facility selection (TRI) ──────────────────────────────────────────────
  const [selectedFacility, setSelectedFacility] = useState<FacilityFeature | null>(null)
  const [detailFacilityId, setDetailFacilityId] = useState<string | null>(null)
  const [highlightedFacilityId, setHighlightedFacilityId] = useState<string | null>(null)

  // ── Superfund site selection ──────────────────────────────────────────────
  const [selectedSuperfundEpaId, setSelectedSuperfundEpaId] = useState<string | null>(null)
  const [showSuperfundLayer, setShowSuperfundLayer] = useState(true)
  const [showTRILayer, setShowTRILayer] = useState(true)

  // ── Data ──────────────────────────────────────────────────────────────────
  const { meta } = useMeta()

  // TRI map params:
  // - Browse mode (no search): null → hook fetches ALL facilities via /browse endpoint
  // - Search mode: search location + radius + filters
  // MapLibre handles viewport subsetting client-side from the fetched data.
  const triMapParams = useMemo<MapSearchParams | null>(() => {
    if (submittedSearch?.dataset === 'tri') {
      return {
        lat: submittedSearch.lat,
        lon: submittedSearch.lon,
        radiusMiles: submittedSearch.radiusMiles,
        chemical: submittedSearch.chemical || undefined,
        year: submittedSearch.year || undefined,
        state: submittedSearch.state || undefined,
        restrictToState: submittedSearch.restrictToState,
      }
    }
    // Browse mode: null → fetch ALL facilities without radius constraint
    return null
  }, [submittedSearch])

  // Build Superfund search params when dataset=superfund and a search was submitted.
  const superfundSearchParams = useMemo<SuperfundSearchParams | null>(() => {
    if (!submittedSearch || submittedSearch.dataset !== 'superfund') return null
    return {
      lat: submittedSearch.lat,
      lon: submittedSearch.lon,
      radiusMiles: submittedSearch.radiusMiles,
      chemical: submittedSearch.chemical || undefined,
      state: submittedSearch.state || undefined,
      restrictToState: submittedSearch.restrictToState,
    }
  }, [submittedSearch])

  // TRI facilities for the MAP (all data, no bbox filtering)
  // This data is passed to MapContainer and should be stable per search.
  const { data: triMapFacilities, loading, error } = useMapFacilities(triMapParams)

  // TRI facilities filtered by current viewport (for sidebar "X in view" count)
  const triViewportFacilities = useMemo(
    () => filterByBbox(triMapFacilities, mapBbox),
    [triMapFacilities, mapBbox],
  )

  // Results table only gets data when a TRI search has been submitted (not in browse mode)
  const triSearchResults = submittedSearch?.dataset === 'tri' ? triViewportFacilities : null

  // Always-on Superfund layer: fetches ALL sites once (no bbox/radius constraint)
  const { data: superfundViewportSites } = useSuperfundViewport()

  // Superfund search results (only active in superfund dataset mode)
  const { data: superfundSearchResults, loading: superfundLoading, error: superfundError } = useSuperfundSearch(superfundSearchParams)

  // Determine which results to show and loading/error state
  const activeLoading = submittedSearch?.dataset === 'superfund' ? superfundLoading : loading
  const activeError = submittedSearch?.dataset === 'superfund' ? superfundError : error

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleSearchSubmit = useCallback(async (values: SearchFormValues) => {
    setGeocodeError(null)
    const geocoded = await geocodeLocation(values.location)
    if (!geocoded) {
      setGeocodeError(`Could not geocode "${values.location}". Try a different location.`)
      return
    }

    // Reset bbox before setting new search so the first request has no stale viewport constraint.
    // The map will zoom to the new location, fire onMoveEnd, and update bbox for subsequent requests.
    setMapBbox(null)

    setSubmittedSearch({
      lat: geocoded.lat,
      lon: geocoded.lon,
      chemical: values.chemical,
      chemicalObj: values.chemicalObj,
      year: values.year,
      state: values.state,
      restrictToState: values.restrictToState,
      radiusMiles: 25,
      dataset: values.dataset,
    })

    // Zoom map to the geocoded location
    setViewState((prev) => ({
      ...prev,
      latitude: geocoded.lat,
      longitude: geocoded.lon,
      zoom: 10,
    }))

    // Switch sidebar to search results (UX Invariant 1)
    setActivePanel('search')
    setSelectedFacility(null)
    setDetailFacilityId(null)
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

  const handleOpenDetail = useCallback((id: string) => {
    if (submittedSearch?.dataset === 'superfund') {
      setSelectedSuperfundEpaId(id)
      setDetailFacilityId(null)
    } else {
      setDetailFacilityId(id)
      setSelectedSuperfundEpaId(null)
    }
    setSelectedFacility(null)
  }, [submittedSearch?.dataset])

  const handleClosePopup = useCallback(() => {
    setSelectedFacility(null)
  }, [])

  const handleCloseDrawer = useCallback(() => {
    setDetailFacilityId(null)
  }, [])

  const handleCloseSuperfundDrawer = useCallback(() => {
    setSelectedSuperfundEpaId(null)
  }, [])

  const handleBoundsChange = useCallback((bbox: [number, number, number, number]) => {
    setMapBbox(bbox)
  }, [])

  const combinedError = geocodeError ?? activeError

  // Sidebar expanded = 20rem = 320px; collapsed = 2.5rem = 40px.
  // Passed to MapContainer so camera padding and popup pan guard use the correct offset.
  const sidebarWidth = isSidebarCollapsed ? 40 : 320

  return (
    <div
      className="toxmap-root relative h-screen w-screen overflow-hidden"
      style={{ position: 'relative', height: '100vh', width: '100vw', overflow: 'hidden' }}
    >      {/* Full-viewport map (background layer) */}
      <MapContainer
        viewState={viewState}
        onViewStateChange={setViewState}
        onBoundsChange={handleBoundsChange}
        facilities={triMapFacilities}
        selectedFacilityId={selectedFacility?.properties.tri_facility_id ?? null}
        highlightedFacilityId={highlightedFacilityId}
        onFacilityClick={handleFacilityClick}
        showTRILayer={showTRILayer}
        superfundSites={superfundViewportSites}
        showSuperfundLayer={showSuperfundLayer}
        onSuperfundSiteClick={handleSuperfundSiteClick}
        sidebarWidth={sidebarWidth}      >
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
        facilities={triSearchResults}
        superfundResults={superfundSearchResults}
        loading={activeLoading}
        error={combinedError}
        highlightedFacilityId={highlightedFacilityId}
        onHighlight={setHighlightedFacilityId}
        onFacilitySelect={handleOpenDetail}
        latestYear={meta?.latest_year ?? null}
        showTRILayer={showTRILayer}
        onToggleTRILayer={() => setShowTRILayer((v) => !v)}
        showSuperfundLayer={showSuperfundLayer}
        onToggleSuperfundLayer={() => setShowSuperfundLayer((v) => !v)}
        triViewportCount={triViewportFacilities?.meta.total_count ?? null}
        triViewportLoading={loading}
        superfundViewportCount={superfundViewportSites?.meta.total_count ?? null}
        superfundViewportLoading={false}
      />

      {/* Facility detail drawer (right panel — TRI mode) */}
      {detailFacilityId && (
        <FacilityDrawer
          facilityId={detailFacilityId}
          onClose={handleCloseDrawer}
        />
      )}

      {/* Superfund detail drawer (right panel — Superfund mode, story 4.2.1) */}
      {selectedSuperfundEpaId && (
        <SuperfundDrawer
          epaId={selectedSuperfundEpaId}
          onClose={handleCloseSuperfundDrawer}
        />
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
