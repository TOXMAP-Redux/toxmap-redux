/**
 * MapContainer — MapLibre GL JS map via react-map-gl.
 * Stories: 3.1.2 (map component), 3.3.1 (colored circles).
 *
 * Basemap: OpenFreeMap Liberty (ADR-005). No PMTiles, no R2 upload required.
 * Style URL: VITE_MAPLIBRE_STYLE env var.
 *
 * ARCHITECTURE (2026-07-28):
 * TRI facility circles are created ONCE in handleLoad, then updated via setData()
 * when facilities data changes. Circles are colored by release tier (color_band).
 *
 * NOTE: Clustering is disabled due to a MapLibre/Supercluster bug where the
 * spatial index is not built when source is created imperatively after map load.
 * Circle size scales by zoom level to approximate clustering visual behavior.
 *
 * Layer structure:
 *   facility-circles — individual TRI facilities (green/yellow/orange/red by color_band)
 */
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import Map, {
  Source,
  Layer,
  NavigationControl,
  AttributionControl,
  Popup,
  type MapRef,
  type ViewState,
  type MapLayerMouseEvent,
} from 'react-map-gl/maplibre'
import 'maplibre-gl/dist/maplibre-gl.css'
import maplibregl from 'maplibre-gl'
import type { FacilityCollection, FacilityFeature, SuperfundCollection, SuperfundFeature, DemographicCollection, DemographicLayer } from '../../api/types'
import { getColorScale } from '../Demographics/InlineLegend'

/**
 * Generate color stops for MapLibre interpolate expression.
 * Returns [value1, color1, value2, color2, ...] array.
 */
function getDemographicColorStops(layer: DemographicLayer): (number | string)[] {
  const colors = getColorScale(layer)
  
  // Define breakpoints based on layer type
  let breaks: number[]
  switch (layer) {
    case 'pct_under_18':
      breaks = [0, 15, 20, 25, 30]
      break
    case 'pct_over_65':
      breaks = [0, 10, 15, 20, 25]
      break
    case 'pct_nonwhite':
      breaks = [0, 10, 25, 40, 60]
      break
    case 'median_income':
      breaks = [0, 30000, 45000, 60000, 80000]
      break
    case 'cancer_mortality_male_per_100k':
    case 'cancer_mortality_female_per_100k':
      breaks = [0, 100, 150, 200, 250]
      break
    case 'heart_disease_mortality_per_100k':
      breaks = [0, 100, 150, 200, 300]
      break
    case 'total_pop':
      breaks = [0, 10000, 50000, 100000, 500000]
      break
    default:
      breaks = [0, 25, 50, 75, 100]
  }
  
  // Interleave breaks and colors: [break1, color1, break2, color2, ...]
  const stops: (number | string)[] = []
  for (let i = 0; i < colors.length; i++) {
    stops.push(breaks[i], colors[i])
  }
  return stops
}

/**
 * Always-visible attribution appended to the tile source's own attribution.
 *
 * The OpenFreeMap Liberty tile source already provides (via TileJSON):
 *   "OpenFreeMap | © OpenMapTiles | Data from OpenStreetMap" (all linked to
 *   openstreetmap.org/copyright) — satisfying OSM ODbL requirements.
 *
 * We add only the Photon geocoding credit here; the OSM attribution comes
 * from the source itself. compact={false} ensures everything is always visible
 * without a user click (required by OSM fair-use policy).
 *
 * This HTML string is handled by MapLibre's internal control, not React's
 * dangerouslySetInnerHTML (standard practice for map libraries).
 */
const CUSTOM_ATTRIBUTION =
  'Geocoding: <a href="https://photon.komoot.io" target="_blank" rel="noopener noreferrer">Photon/Komoot</a>'

const MAP_STYLE = import.meta.env.VITE_MAPLIBRE_STYLE || 'https://tiles.openfreemap.org/styles/liberty'

interface MapContainerProps {
  viewState: ViewState
  onViewStateChange: (vs: ViewState) => void
  onBoundsChange: (bbox: [number, number, number, number]) => void
  /** Ref callback to expose flyTo function for programmatic camera moves */
  onMapReady?: (flyTo: (lat: number, lon: number, zoom: number) => void) => void
  facilities: FacilityCollection | null
  selectedFacilityId: string | null
  highlightedFacilityId: string | null
  onFacilityClick: (facility: FacilityFeature) => void
  /** Controls TRI cluster + individual circle layer visibility */
  showTRILayer?: boolean
  /** Superfund sites for the always-on diamond layer (story 4.1.1) */
  superfundSites: SuperfundCollection | null
  /** Controls diamond layer visibility (story 4.1.2) */
  showSuperfundLayer: boolean
  /** Called when the user clicks a Superfund diamond (story 4.2.1) */
  onSuperfundSiteClick: (site: SuperfundFeature) => void
  /** EPA ID of currently selected Superfund site (for drawer) */
  selectedSuperfundEpaId?: string | null
  /** Sidebar width in pixels. MapLibre camera padding is set to this value so
   * easeTo/flyTo and popup auto-pan target the usable viewport area. */
  sidebarWidth?: number
  /** Demographics GeoJSON for choropleth layer (story 5.2.1) */
  demographics: DemographicCollection | null
  /** Currently selected demographic layer (null = no overlay) */
  demographicLayer: DemographicLayer | null
  children?: ReactNode
}

/**
 * Full-viewport map with TRI facility markers.
 * Emits onBoundsChange whenever the viewport moves/zooms.
 */

/**
 * Build square SVG as an Image object for MapLibre sprite registration.
 * Used for NPL Final sites per UCD-17.
 */
function makeSquareImage(fill: string, stroke: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const svgStr = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">
      <rect x="2" y="2" width="12" height="12" rx="1"
            fill="${fill}" stroke="${stroke}" stroke-width="1.5"/>
    </svg>`
    const blob = new Blob([svgStr], { type: 'image/svg+xml' })
    const url = URL.createObjectURL(blob)
    const img = new Image(16, 16)
    img.onload = () => { URL.revokeObjectURL(url); resolve(img) }
    img.onerror = reject
    img.src = url
  })
}

/**
 * Build half-shaded square SVG for Proposed sites.
 * Same shape as Final but with diagonal half-fill to indicate pending status.
 */
function makeHalfSquareImage(fill: string, stroke: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const svgStr = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">
      <defs>
        <clipPath id="halfClip">
          <polygon points="2,2 14,2 14,14"/>
        </clipPath>
      </defs>
      <rect x="2" y="2" width="12" height="12" rx="1"
            fill="transparent" stroke="${stroke}" stroke-width="1.5"/>
      <rect x="2" y="2" width="12" height="12" rx="1"
            fill="${fill}" clip-path="url(#halfClip)"/>
    </svg>`
    const blob = new Blob([svgStr], { type: 'image/svg+xml' })
    const url = URL.createObjectURL(blob)
    const img = new Image(16, 16)
    img.onload = () => { URL.revokeObjectURL(url); resolve(img) }
    img.onerror = reject
    img.src = url
  })
}

/**
 * Build square-with-X SVG as an Image object for MapLibre sprite registration.
 * Used for Deleted NPL sites per UCD-17 (original TOXMAP used crossed-out squares).
 * Same color scheme as other Superfund icons for consistency.
 */
function makeXSquareImage(color: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const svgStr = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">
      <rect x="2" y="2" width="12" height="12" rx="1"
            fill="transparent" stroke="${color}" stroke-width="1.5"/>
      <line x1="4" y1="4" x2="12" y2="12" stroke="${color}" stroke-width="2"/>
      <line x1="12" y1="4" x2="4" y2="12" stroke="${color}" stroke-width="2"/>
    </svg>`
    const blob = new Blob([svgStr], { type: 'image/svg+xml' })
    const url = URL.createObjectURL(blob)
    const img = new Image(16, 16)
    img.onload = () => { URL.revokeObjectURL(url); resolve(img) }
    img.onerror = reject
    img.src = url
  })
}

export function MapContainer({
  viewState,
  onViewStateChange,
  onBoundsChange,
  onMapReady,
  facilities,
  selectedFacilityId,
  highlightedFacilityId,
  onFacilityClick,
  showTRILayer = true,
  superfundSites,
  showSuperfundLayer,
  onSuperfundSiteClick,
  selectedSuperfundEpaId = null,
  sidebarWidth = 0,
  demographics,
  demographicLayer,
  children,
}: MapContainerProps): JSX.Element {
  const mapRef = useRef<MapRef>(null)
  const [cursor, setCursor] = useState('grab')
  const [mapLoaded, setMapLoaded] = useState(false)
  /** True once TRI source/layers are created — gates setData updates */
  const [triLayersReady, setTriLayersReady] = useState(false)
  /** True once all Superfund SVG sprites are registered — gates the superfund-sites layer */
  const [spritesReady, setSpritesReady] = useState(false)

  // PERFORMANCE: Don't update React state on every animation frame!
  // Only sync viewState on moveEnd to prevent 80+ re-renders during flyTo.
  const handleMoveEndWithViewSync = useCallback(() => {
    const map = mapRef.current?.getMap()
    if (!map) return
    const b = map.getBounds()
    onBoundsChange([b.getWest(), b.getSouth(), b.getEast(), b.getNorth()])
    // Sync viewState to React for legend zoom display
    const center = map.getCenter()
    onViewStateChange({
      latitude: center.lat,
      longitude: center.lng,
      zoom: map.getZoom(),
      bearing: map.getBearing(),
      pitch: map.getPitch(),
      padding: map.getPadding(),
    })
  }, [onViewStateChange, onBoundsChange])

  // Register diamond SVG sprites on map load (story 4.1.1)
  const handleLoad = useCallback(() => {
    setMapLoaded(true)
    handleMoveEndWithViewSync()
    const map = mapRef.current?.getMap()
    if (!map) return

    // Expose flyTo function for programmatic camera moves
    // PERFORMANCE: Use jumpTo instead of flyTo to avoid CPU spike from
    // basemap tile processing during animation. The flyTo animation
    // triggers MapLibre to load many tiles at intermediate zoom levels,
    // causing CPU-intensive style expression evaluation.
    if (onMapReady) {
      onMapReady((lat: number, lon: number, zoom: number) => {
        map.jumpTo({ center: [lon, lat], zoom })
      })
    }

    // DEBUG: Expose map instance globally (can be removed in production)
    ;(window as unknown as { __DEBUG_MAP__: maplibregl.Map }).__DEBUG_MAP__ = map

    // TRI source/layers are created in the data effect when facilities data arrives.
    // CRITICAL: MapLibre's clustered GeoJSON source does NOT rebuild its spatial
    // index when setData() is called on a source created with empty data. The source
    // must be created with actual data present.

    // ── Superfund status sprites (UCD-17: 3-way distinction) ─────────────────
    // NPL Final → solid dark red square (no stroke)
    // Proposed → half-shaded dark red square (diagonal fill)
    // Deleted → dark red outline square with dark red X
    const SUPERFUND_COLOR = '#b91c1c' // red-700 for better contrast
    Promise.all([
      makeSquareImage(SUPERFUND_COLOR, SUPERFUND_COLOR), // NPL Final: solid square
      makeHalfSquareImage(SUPERFUND_COLOR, SUPERFUND_COLOR), // Proposed: half-shaded
      makeXSquareImage(SUPERFUND_COLOR),              // Deleted: outline + X
    ]).then(([nplSquare, proposedDiamond, deletedXSquare]) => {
      if (!map.hasImage('superfund-npl-final')) map.addImage('superfund-npl-final', nplSquare)
      if (!map.hasImage('superfund-proposed')) map.addImage('superfund-proposed', proposedDiamond)
      if (!map.hasImage('superfund-deleted')) map.addImage('superfund-deleted', deletedXSquare)
      setSpritesReady(true)
    }).catch(() => { /* sprite registration failure is non-fatal */ })
  }, [handleMoveEndWithViewSync, onMapReady])

  const handleMouseEnter = useCallback(() => setCursor('pointer'), [])
  const handleMouseLeave = useCallback(() => setCursor('grab'), [])

  // Click on a facility circle → emit onFacilityClick
  const handleMapClick = useCallback((evt: MapLayerMouseEvent) => {
    const feature = evt.features?.[0]
    if (!feature || !feature.properties) return

    if (feature.layer.id === 'facility-circles') {
      // Reconstruct the FacilityFeature from the clicked GeoJSON feature
      const coords = (feature.geometry as GeoJSON.Point).coordinates as [number, number]
      const facilityFeature: FacilityFeature = {
        type: 'Feature',
        geometry: { type: 'Point', coordinates: coords },
        properties: feature.properties as FacilityFeature['properties'],
      }
      onFacilityClick(facilityFeature)
    }

    if (feature.layer.id === 'superfund-sites') {
      const coords = (feature.geometry as GeoJSON.Point).coordinates as [number, number]
      const superfundFeature: SuperfundFeature = {
        type: 'Feature',
        geometry: { type: 'Point', coordinates: coords },
        properties: feature.properties as SuperfundFeature['properties'],
      }
      onSuperfundSiteClick(superfundFeature)
    }
  }, [onFacilityClick, onSuperfundSiteClick])

  // Update Superfund layer visibility imperatively when toggle changes
  useEffect(() => {
    if (!mapLoaded) return
    const map = mapRef.current?.getMap()
    if (!map || !map.getLayer('superfund-sites')) return
    map.setLayoutProperty('superfund-sites', 'visibility', showSuperfundLayer ? 'visible' : 'none')
  }, [showSuperfundLayer, mapLoaded])

  // Create/update TRI source + layers when facilities data changes.
  // NOTE: Clustering is disabled due to a MapLibre/Supercluster bug where the
  // spatial index is not built when source is created imperatively after map load.
  // Individual circles render correctly at all zoom levels.
  //
  // PERFORMANCE FIX: Only create source/layer once. Use setData() for updates.
  // Removing/re-adding 22K features took ~10 seconds and caused CPU spike.
  useEffect(() => {
    if (!mapLoaded) return
    const map = mapRef.current?.getMap()
    if (!map) return

    // If no data, just update to empty FeatureCollection (don't destroy layers)
    if (!facilities || facilities.features.length === 0) {
      const existingSource = map.getSource('facilities') as maplibregl.GeoJSONSource | undefined
      if (existingSource) {
        existingSource.setData({ type: 'FeatureCollection', features: [] })
      }
      return
    }

    const newData: GeoJSON.FeatureCollection = {
      type: 'FeatureCollection',
      features: facilities.features,
    }

    // If source already exists, just update the data (FAST)
    const existingSource = map.getSource('facilities') as maplibregl.GeoJSONSource | undefined
    if (existingSource) {
      existingSource.setData(newData)
      return
    }

    // First time: create source and layer.
    // buffer=0: no tile buffer for point data — circles don't bleed across tile edges.
    // This halves worker processing time for the initial 30K browse load.
    map.addSource('facilities', {
      type: 'geojson',
      data: newData,
      buffer: 0,
    })

    // Individual facility circles (colored by release tier)
    map.addLayer({
      id: 'facility-circles',
      type: 'circle',
      source: 'facilities',
      paint: {
        'circle-color': [
          'match', ['get', 'color_band'],
          'green', '#1B5E20',  // green-900 (deep forest green)
          'yellow', '#FBC02D', // yellow-700 (true yellow)
          'orange', '#E65100', // orange-900 (deep burnt orange)
          'red', '#7F0000',    // dark maroon (very dark red)
          '#424242',           // gray-800 (fallback)
        ],
        'circle-radius': [
          'interpolate', ['linear'], ['zoom'],
          // At each zoom level, radius varies by tier: red=full, green=smallest
          3, ['match', ['get', 'color_band'],
            'red', 3, 'orange', 2.5, 'yellow', 2, 'green', 1.5, 2],
          5, ['match', ['get', 'color_band'],
            'red', 4, 'orange', 3.3, 'yellow', 2.7, 'green', 2, 2.7],
          8, ['match', ['get', 'color_band'],
            'red', 6, 'orange', 5, 'yellow', 4, 'green', 3, 4],
          12, ['match', ['get', 'color_band'],
            'red', 9, 'orange', 7.5, 'yellow', 6, 'green', 4.5, 6],
          16, ['match', ['get', 'color_band'],
            'red', 12, 'orange', 10, 'yellow', 8, 'green', 6, 8],
        ],
        'circle-opacity': 0.8,
      },
    })

    setTriLayersReady(true)
  }, [facilities, mapLoaded])

  // Toggle TRI layer visibility
  useEffect(() => {
    if (!triLayersReady) return
    const map = mapRef.current?.getMap()
    if (!map || !map.getLayer('facility-circles')) return
    map.setLayoutProperty('facility-circles', 'visibility', showTRILayer ? 'visible' : 'none')
  }, [showTRILayer, triLayersReady])

  // Update selected/highlighted facility stroke imperatively
  useEffect(() => {
    if (!triLayersReady) return
    const map = mapRef.current?.getMap()
    if (!map || !map.getLayer('facility-circles')) return
    // Show white stroke only on selected/highlighted facilities
    const strokeWidth = (selectedFacilityId || highlightedFacilityId)
      ? ['case',
          ['any',
            ['==', ['get', 'tri_facility_id'], selectedFacilityId ?? ''],
            ['==', ['get', 'tri_facility_id'], highlightedFacilityId ?? ''],
          ],
          3, 0,
        ]
      : 0
    map.setPaintProperty('facility-circles', 'circle-stroke-width', strokeWidth)
    map.setPaintProperty('facility-circles', 'circle-stroke-color', '#ffffff')
  }, [selectedFacilityId, highlightedFacilityId, triLayersReady])

  // When a popup is about to open, pan the map so the popup is fully visible.
  // MapLibre does not auto-pan for declarative react-map-gl Popups, so we
  // handle it explicitly here. Checks all edges: left (sidebar), right, top.
  useEffect(() => {
    if (!selectedFacilityId || !facilities || !mapLoaded) return
    const map = mapRef.current?.getMap()
    if (!map) return

    const feature = facilities.features.find(
      (f) => f.properties.tri_facility_id === selectedFacilityId,
    )
    if (!feature) return

    const [lon, lat] = feature.geometry.coordinates
    const screenPt = map.project([lon, lat])
    const gutter = 16
    // Popup maxWidth is 300px; anchor is bottom-center
    const popupHalfWidth = 150
    const popupHeight = 160 // Approximate height including content + tip
    const popupTipOffset = 15

    const popupLeftEdge = screenPt.x - popupHalfWidth
    const popupRightEdge = screenPt.x + popupHalfWidth
    const popupTopEdge = screenPt.y - popupHeight - popupTipOffset

    const canvas = map.getCanvas()
    const viewportWidth = canvas.clientWidth

    const minLeft = sidebarWidth + gutter
    const maxRight = viewportWidth - gutter
    const minTop = gutter

    let panX = 0
    let panY = 0

    // Left edge check (popup overlaps sidebar)
    if (popupLeftEdge < minLeft) {
      panX = minLeft - popupLeftEdge
    }
    // Right edge check (popup extends past right edge)
    if (popupRightEdge > maxRight) {
      panX = maxRight - popupRightEdge // Negative value to pan left
    }
    // Top edge check (popup extends above viewport)
    if (popupTopEdge < minTop) {
      panY = minTop - popupTopEdge // Negative value to pan down
    }

    if (panX !== 0 || panY !== 0) {
      map.panBy([-panX, -panY], { animate: true, duration: 250 })
    }
  }, [selectedFacilityId, facilities, sidebarWidth, mapLoaded])

  // Scroll map to center on highlighted TRI facility from results table.
  // With camera padding set, easeTo centers on the usable viewport automatically.
  useEffect(() => {
    if (!highlightedFacilityId || !facilities) return
    const feature = facilities.features.find(
      (f) => f.properties.tri_facility_id === highlightedFacilityId,
    )
    if (!feature) return
    const [lon, lat] = feature.geometry.coordinates
    mapRef.current?.getMap()?.easeTo({ center: [lon, lat], zoom: 12, duration: 500 })
  }, [highlightedFacilityId, facilities])

  // Scroll map to center on highlighted Superfund site from results table.
  // Uses the same highlightedFacilityId state (can be TRI ID or Superfund EPA ID).
  useEffect(() => {
    if (!highlightedFacilityId || !superfundSites) return
    // Check if the highlighted ID matches a Superfund site (by EPA ID)
    const feature = superfundSites.features.find(
      (f) => f.properties.epa_id === highlightedFacilityId,
    )
    if (!feature) return
    const [lon, lat] = feature.geometry.coordinates
    mapRef.current?.getMap()?.easeTo({ center: [lon, lat], zoom: 12, duration: 500 })
  }, [highlightedFacilityId, superfundSites])

  // Get the highlighted TRI facility feature for showing the hover tooltip
  // Don't show hover tooltip if the facility is already selected (has its own popup)
  const highlightedFeature = highlightedFacilityId && highlightedFacilityId !== selectedFacilityId && facilities
    ? facilities.features.find((f) => f.properties.tri_facility_id === highlightedFacilityId)
    : null

  // Get the highlighted Superfund site feature for showing the hover tooltip
  // Don't show hover tooltip if the site is already selected (has its own drawer)
  const highlightedSuperfundFeature = highlightedFacilityId && highlightedFacilityId !== selectedSuperfundEpaId && superfundSites
    ? superfundSites.features.find((f) => f.properties.epa_id === highlightedFacilityId)
    : null

  return (
    <div
      data-testid="map-container"
      className="absolute inset-0"
      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
    >      <Map
        ref={mapRef}
        // PERFORMANCE: Use uncontrolled mode to prevent 80+ re-renders during flyTo animation.
        // For programmatic camera moves, use flyToLocation callback instead of setViewState.
        initialViewState={viewState}
        padding={{ top: 0, right: 0, bottom: 0, left: sidebarWidth }}
        onMoveEnd={handleMoveEndWithViewSync}
        onLoad={handleLoad}
        onClick={handleMapClick}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        interactiveLayerIds={['facility-circles', 'superfund-sites']}
        cursor={cursor}
        mapStyle={MAP_STYLE}
        style={{ width: '100%', height: '100%' }}
        attributionControl={false}
      >
        {/*
          Attribution control — compact=false ensures attribution is always visible
          without requiring user interaction (OSM ODbL fair-use requirement).
          The OpenFreeMap source provides "© OpenStreetMap contributors" text
          with a link to openstreetmap.org/copyright; CUSTOM_ATTRIBUTION appends
          the Photon geocoding credit.
        */}
        <AttributionControl
          compact={false}
          position="bottom-right"
          customAttribution={CUSTOM_ATTRIBUTION}
          style={{ fontSize: '11px', maxWidth: '480px' }}
        />
        <NavigationControl position="top-right" />

        {/* TRI facility layers are managed imperatively in handleLoad/useEffect
            to avoid react-map-gl Source calling setData on every render. */}

        {/* Demographics choropleth layer (story 5.2.1) — rendered BELOW point layers.
            TRI circles and Superfund diamonds remain visible above the fill layer. */}
        {demographics && demographicLayer && (
          <Source
            id="demographics-source"
            type="geojson"
            data={{ type: 'FeatureCollection', features: demographics.features }}
          >
            <Layer
              id="demographics-fill"
              type="fill"
              beforeId={mapLoaded && mapRef.current?.getMap()?.getLayer('facility-circles') ? 'facility-circles' : undefined}
              paint={{
                'fill-color': [
                  'interpolate',
                  ['linear'],
                  ['coalesce', ['get', demographicLayer], 0],
                  ...getDemographicColorStops(demographicLayer),
                ] as unknown as string,
                'fill-opacity': 0.6,
              }}
            />
            <Layer
              id="demographics-outline"
              type="line"
              beforeId={mapLoaded && mapRef.current?.getMap()?.getLayer('facility-circles') ? 'facility-circles' : undefined}
              paint={{
                'line-color': '#666',
                'line-width': 0.5,
                'line-opacity': 0.5,
              }}
            />
          </Source>
        )}

        {/* Superfund sites — separate, unclustered symbol layer (story 4.1.1).
            Only rendered after diamond sprites are registered (spritesReady),
            preventing a race condition where the layer mounts before addImage completes. */}
        {spritesReady && superfundSites && (
          <Source
            id="superfund-source"
            type="geojson"
            data={{ type: 'FeatureCollection', features: superfundSites.features }}
          >
            <Layer
              id="superfund-sites"
              type="symbol"
              layout={{
                // UCD-17: 3-way status distinction
                // NPL → filled red square
                // Proposed → red diamond outline
                // Deleted → gray X-square
                'icon-image': [
                  'match', ['get', 'status'],
                  'NPL', 'superfund-npl-final',
                  'Proposed', 'superfund-proposed',
                  'Deleted', 'superfund-deleted',
                  'superfund-proposed', // fallback
                ] as unknown as string,
                'icon-size': [
                  'interpolate', ['linear'], ['zoom'],
                  3, 0.5,  // Small at full country zoom
                  5, 0.7,  // Medium-small at continental zoom  
                  8, 0.9,  // Medium at regional zoom
                  12, 1.2, // Large at city zoom
                ],
                'icon-allow-overlap': true,
              }}
              paint={{
                'icon-opacity': 0.8,
              }}
            />
          </Source>
        )}

        {/* Hover tooltip for highlighted facility from results table */}
        {highlightedFeature && (
          <Popup
            longitude={highlightedFeature.geometry.coordinates[0]}
            latitude={highlightedFeature.geometry.coordinates[1]}
            anchor="bottom"
            closeButton={false}
            closeOnClick={false}
            offset={[0, -15]}
            style={{ zIndex: 10 }}
          >
            <div style={{
              padding: '6px 10px',
              fontSize: '12px',
              fontWeight: 600,
              color: '#1f2937',
              maxWidth: '200px',
              textAlign: 'center',
              lineHeight: 1.3,
            }}>
              {highlightedFeature.properties.name}
            </div>
          </Popup>
        )}

        {/* Hover tooltip for highlighted Superfund site from results table */}
        {highlightedSuperfundFeature && (
          <Popup
            longitude={highlightedSuperfundFeature.geometry.coordinates[0]}
            latitude={highlightedSuperfundFeature.geometry.coordinates[1]}
            anchor="bottom"
            closeButton={false}
            closeOnClick={false}
            offset={[0, -15]}
            style={{ zIndex: 10 }}
          >
            <div style={{
              padding: '6px 10px',
              fontSize: '12px',
              fontWeight: 600,
              color: '#991b1b',
              maxWidth: '200px',
              textAlign: 'center',
              lineHeight: 1.3,
            }}>
              {highlightedSuperfundFeature.properties.name}
            </div>
          </Popup>
        )}

        {children}
      </Map>
    </div>
  )
}
