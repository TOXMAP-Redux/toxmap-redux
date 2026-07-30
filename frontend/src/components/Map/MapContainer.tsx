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
  type MapRef,
  type ViewState,
  type ViewStateChangeEvent,
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
/** Build diamond SVG as an Image object for MapLibre sprite registration */
function makeDiamondImage(fill: string, stroke: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const svgStr = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">
      <rect x="2" y="2" width="12" height="12" rx="1"
            fill="${fill}" stroke="${stroke}" stroke-width="1.5"
            transform="rotate(45 8 8)"/>
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
  facilities,
  selectedFacilityId,
  highlightedFacilityId,
  onFacilityClick,
  showTRILayer = true,
  superfundSites,
  showSuperfundLayer,
  onSuperfundSiteClick,
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
  /** True once both SVG diamond sprites are registered — gates the superfund-sites layer */
  const [spritesReady, setSpritesReady] = useState(false)

  // Emit bbox whenever the map stops moving
  const handleMoveEnd = useCallback(() => {
    const map = mapRef.current?.getMap()
    if (!map) return
    const b = map.getBounds()
    onBoundsChange([b.getWest(), b.getSouth(), b.getEast(), b.getNorth()])
  }, [onBoundsChange])

  // Register diamond SVG sprites on map load (story 4.1.1)
  const handleLoad = useCallback(() => {
    setMapLoaded(true)
    handleMoveEnd()
    const map = mapRef.current?.getMap()
    if (!map) return

    // DEBUG: Expose map instance globally (can be removed in production)
    ;(window as unknown as { __DEBUG_MAP__: maplibregl.Map }).__DEBUG_MAP__ = map

    // TRI source/layers are created in the data effect when facilities data arrives.
    // CRITICAL: MapLibre's clustered GeoJSON source does NOT rebuild its spatial
    // index when setData() is called on a source created with empty data. The source
    // must be created with actual data present.

    // ── Superfund diamond sprites ──────────────────────────────────────────
    Promise.all([
      makeDiamondImage('#ef4444', 'white'),   // filled — NPL sites
      makeDiamondImage('transparent', '#ef4444'), // outline — CERCLIS/Deleted
    ]).then(([filled, outline]) => {
      if (!map.hasImage('superfund-diamond-filled')) map.addImage('superfund-diamond-filled', filled)
      if (!map.hasImage('superfund-diamond-outline')) map.addImage('superfund-diamond-outline', outline)
      setSpritesReady(true)
    }).catch(() => { /* sprite registration failure is non-fatal */ })
  }, [handleMoveEnd])

  const handleMove = useCallback((evt: ViewStateChangeEvent) => {
    onViewStateChange(evt.viewState)
  }, [onViewStateChange])

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
  useEffect(() => {
    if (!mapLoaded) return
    if (!facilities || facilities.features.length === 0) {
      // No data — remove existing layers/source if present
      const map = mapRef.current?.getMap()
      if (map) {
        if (map.getLayer('facility-circles')) map.removeLayer('facility-circles')
        if (map.getSource('facilities')) map.removeSource('facilities')
      }
      setTriLayersReady(false)
      return
    }

    const map = mapRef.current?.getMap()
    if (!map) return

    // Remove existing source/layers (for HMR or data change)
    if (map.getLayer('facility-circles')) map.removeLayer('facility-circles')
    if (map.getSource('facilities')) map.removeSource('facilities')

    // Create source WITHOUT clustering (clustering is broken in this context)
    map.addSource('facilities', {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features: facilities.features,
      },
    })

    // Individual facility circles (colored by release tier)
    map.addLayer({
      id: 'facility-circles',
      type: 'circle',
      source: 'facilities',
      paint: {
        'circle-color': [
          'match', ['get', 'color_band'],
          'green', '#4CAF50',
          'yellow', '#FFEB3B',
          'orange', '#FF9800',
          'red', '#F44336',
          '#9E9E9E',
        ],
        'circle-radius': [
          'interpolate', ['linear'], ['zoom'],
          4, 4,   // Small at continental zoom
          8, 6,   // Medium at regional zoom
          12, 8,  // Larger at city zoom
          16, 10, // Full size at street zoom
        ],
        'circle-stroke-width': 1.5,
        'circle-stroke-color': '#ffffff',
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
    const strokeWidth = (selectedFacilityId || highlightedFacilityId)
      ? ['case',
          ['any',
            ['==', ['get', 'tri_facility_id'], selectedFacilityId ?? ''],
            ['==', ['get', 'tri_facility_id'], highlightedFacilityId ?? ''],
          ],
          4, 2,
        ]
      : 2
    map.setPaintProperty('facility-circles', 'circle-stroke-width', strokeWidth)
  }, [selectedFacilityId, highlightedFacilityId, triLayersReady])

  // When a popup is about to open, pan right if the marker falls within the
  // sidebar+gutter zone so the popup card is fully readable.
  // MapLibre does not auto-pan for declarative react-map-gl Popups, so we
  // handle it explicitly here.
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
    const gutter = 12
    // Popup maxWidth is 300px; anchor is bottom-center, so left edge ≈ markerX - 150
    const popupLeftEdge = screenPt.x - 150
    const minLeft = sidebarWidth + gutter

    if (popupLeftEdge < minLeft) {
      map.panBy([minLeft - popupLeftEdge, 0], { animate: true, duration: 250 })
    }
  }, [selectedFacilityId, facilities, sidebarWidth, mapLoaded])

  // Scroll map to center on selected facility from results table.
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

  return (
    <div
      data-testid="map-container"
      className="absolute inset-0"
      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
    >      <Map
        ref={mapRef}
        {...viewState}
        // sidebarWidth passed as explicit padding prop AFTER the viewState spread so
        // it always wins — avoids the imperative setPadding vs. controlled-viewState
        // conflict where each camera move would reset padding to 0.
        padding={{ top: 0, right: 0, bottom: 0, left: sidebarWidth }}
        onMove={handleMove}
        onMoveEnd={handleMoveEnd}
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
                'icon-image': [
                  'match', ['get', 'status'],
                  'NPL', 'superfund-diamond-filled',
                  'superfund-diamond-outline',
                ] as unknown as string,
                'icon-size': 1,
                'icon-allow-overlap': true,
              }}
              paint={{}}
            />
          </Source>
        )}

        {children}
      </Map>
    </div>
  )
}
