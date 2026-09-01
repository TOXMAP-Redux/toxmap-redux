/**
 * MapLibre helper functions for E2E tests.
 * 
 * These functions are injected into the page context and used by Playwright
 * step implementations to verify map state, layer visibility, and data.
 * 
 * Usage in Python:
 *   page.evaluate(open('tests/fixtures/map_helpers.js').read())
 *   result = page.evaluate('window.mapHelpers.hasSource("facilities")')
 */

(function() {
  'use strict';

  /**
   * Get the MapLibre map instance from the debug global.
   * @returns {Object|null} MapLibre map instance or null
   */
  function getMap() {
    return window.__DEBUG_MAP__ || null;
  }

  /**
   * Check if a GeoJSON source exists on the map.
   * @param {string} sourceName - Name of the source (e.g., 'facilities', 'superfund-source')
   * @returns {boolean}
   */
  function hasSource(sourceName) {
    const map = getMap();
    return map && !!map.getSource(sourceName);
  }

  /**
   * Check if a layer exists on the map.
   * @param {string} layerName - Name of the layer (e.g., 'facility-circles', 'superfund-sites')
   * @returns {boolean}
   */
  function hasLayer(layerName) {
    const map = getMap();
    return map && !!map.getLayer(layerName);
  }

  /**
   * Get layer visibility property.
   * @param {string} layerName - Name of the layer
   * @returns {string|null} 'visible', 'none', or null if layer doesn't exist
   */
  function getLayerVisibility(layerName) {
    const map = getMap();
    if (!map) return null;
    const layer = map.getLayer(layerName);
    return layer ? map.getLayoutProperty(layerName, 'visibility') : null;
  }

  /**
   * Check if an icon image is loaded on the map.
   * @param {string} imageName - Name of the image (e.g., 'superfund-npl-final')
   * @returns {boolean}
   */
  function hasImage(imageName) {
    const map = getMap();
    return map && map.hasImage(imageName);
  }

  /**
   * Get the current map center coordinates.
   * @returns {{lat: number, lon: number}|{error: string}}
   */
  function getMapCenter() {
    const map = getMap();
    if (!map) return { error: 'Map not found' };
    const c = map.getCenter();
    return { lat: c.lat, lon: c.lng };
  }

  /**
   * Get the current map zoom level.
   * @returns {number|null}
   */
  function getZoom() {
    const map = getMap();
    return map ? map.getZoom() : null;
  }

  /**
   * Check if the map is currently moving/animating.
   * @returns {boolean}
   */
  function isMoving() {
    const map = getMap();
    return map ? map.isMoving() : false;
  }

  /**
   * Get comprehensive layer information for a specific layer.
   * @param {string} layerName - Name of the layer
   * @returns {Object}
   */
  function getLayerInfo(layerName) {
    const map = getMap();
    if (!map) return { error: 'Map not found' };

    const layer = map.getLayer(layerName);
    return {
      hasLayer: !!layer,
      layerVisibility: layer ? map.getLayoutProperty(layerName, 'visibility') : null,
    };
  }

  /**
   * Get feature count from a GeoJSON source.
   * @param {string} sourceName - Name of the source
   * @returns {number|null}
   */
  function getSourceFeatureCount(sourceName) {
    const map = getMap();
    if (!map) return null;
    
    const source = map.getSource(sourceName);
    if (!source || !source._data || !source._data.features) return null;
    
    return source._data.features.length;
  }

  /**
   * Get Superfund layer information including icon status.
   * @returns {Object}
   */
  function getSuperfundLayerInfo() {
    const map = getMap();
    if (!map) return { error: 'Map not found' };

    return {
      hasSource: !!map.getSource('superfund-source'),
      hasLayer: !!map.getLayer('superfund-sites'),
      hasNplFinal: map.hasImage('superfund-npl-final'),
      hasProposed: map.hasImage('superfund-proposed'),
      hasDeleted: map.hasImage('superfund-deleted'),
      layerVisibility: map.getLayer('superfund-sites')
        ? map.getLayoutProperty('superfund-sites', 'visibility')
        : null,
    };
  }

  /**
   * Get TRI facilities layer information.
   * @returns {Object}
   */
  function getFacilitiesLayerInfo() {
    const map = getMap();
    if (!map) return { error: 'Map not found' };

    return {
      hasSource: !!map.getSource('facilities'),
      hasLayer: !!map.getLayer('facility-circles'),
      layerVisibility: map.getLayer('facility-circles')
        ? map.getLayoutProperty('facility-circles', 'visibility')
        : null,
    };
  }

  /**
   * Get demographics layer information.
   * @returns {Object}
   */
  function getDemographicsLayerInfo() {
    const map = getMap();
    if (!map) return { error: 'Map not found' };

    return {
      hasSource: !!map.getSource('demographics-source'),
      hasFillLayer: !!map.getLayer('demographics-fill'),
    };
  }

  /**
   * Get current view state (center, zoom, bounds).
   * @returns {Object}
   */
  function getViewState() {
    const map = getMap();
    if (!map) return { error: 'Map not found' };
    
    const center = map.getCenter();
    const bounds = map.getBounds();
    
    return {
      lat: center.lat,
      lng: center.lng,
      zoom: map.getZoom(),
      north: bounds.getNorth(),
      south: bounds.getSouth(),
      east: bounds.getEast(),
      west: bounds.getWest(),
    };
  }

  /**
   * Get circle size at a specific tier from the facility-circles layer.
   * @param {number} tierValue - Tier value (1-4)
   * @returns {number|null}
   */
  function getCircleSizeForTier(tierValue) {
    const map = getMap();
    if (!map) return null;
    
    const layer = map.getLayer('facility-circles');
    if (!layer) return null;
    
    const paint = map.getPaintProperty('facility-circles', 'circle-radius');
    if (!paint || !Array.isArray(paint)) return null;
    
    // Paint is a data-driven style like:
    // ['interpolate', ['linear'], ['get', 'tier'], 1, 4, 2, 6, 3, 8, 4, 10]
    const tierIndex = paint.indexOf(tierValue);
    if (tierIndex > 0 && tierIndex < paint.length - 1) {
      return paint[tierIndex + 1];
    }
    return null;
  }

  /**
   * Get all tier sizes for facility circles.
   * @returns {Object}
   */
  function getTierSizing() {
    const map = getMap();
    if (!map) return { error: 'Map not found' };
    
    return {
      tier1: getCircleSizeForTier(1),
      tier2: getCircleSizeForTier(2),
      tier3: getCircleSizeForTier(3),
      tier4: getCircleSizeForTier(4),
    };
  }

  // Expose helpers on window for page.evaluate access
  window.mapHelpers = {
    getMap,
    hasSource,
    hasLayer,
    hasImage,
    getLayerVisibility,
    getMapCenter,
    getZoom,
    isMoving,
    getLayerInfo,
    getSourceFeatureCount,
    getSuperfundLayerInfo,
    getFacilitiesLayerInfo,
    getDemographicsLayerInfo,
    getViewState,
    getCircleSizeForTier,
    getTierSizing,
  };
})();
