# tests/e2e/helpers.py
#
# Shared E2E test helpers for TOXMAP Playwright tests.
# Abstracts common patterns like MapLibre map access and wait conditions.
#

from playwright.sync_api import Page


def wait_for_map_ready(page: Page, timeout: int = 20_000) -> None:
    """
    Wait for the MapLibre map to be fully loaded and ready.
    
    The frontend exposes window.__DEBUG_MAP__ for test access to the map instance.
    This is a contract requirement — if removed, E2E tests will fail.
    
    Args:
        page: Playwright Page instance
        timeout: Maximum wait time in milliseconds (default: 20s)
    """
    page.wait_for_function(
        """() => {
            const map = window.__DEBUG_MAP__;
            return map && map.isStyleLoaded() && !map.isMoving();
        }""",
        timeout=timeout,
    )


def wait_for_map_idle(page: Page, timeout: int = 10_000) -> None:
    """
    Wait for the map to stop moving and zooming.
    
    Use this after triggering map interactions (search, pan, zoom).
    
    Args:
        page: Playwright Page instance
        timeout: Maximum wait time in milliseconds (default: 10s)
    """
    page.wait_for_function(
        """() => {
            const map = window.__DEBUG_MAP__;
            return map && !map.isMoving() && !map.isZooming();
        }""",
        timeout=timeout,
    )


def wait_for_layer_source(page: Page, source_id: str, timeout: int = 15_000) -> None:
    """
    Wait for a MapLibre GeoJSON source to have features.
    
    Args:
        page: Playwright Page instance
        source_id: MapLibre source ID (e.g., 'facilities', 'superfund-source')
        timeout: Maximum wait time in milliseconds (default: 15s)
    """
    page.wait_for_function(
        f"""() => {{
            const map = window.__DEBUG_MAP__;
            if (!map) return false;
            const source = map.getSource('{source_id}');
            return source && source._data && source._data.features && source._data.features.length > 0;
        }}""",
        timeout=timeout,
    )


def wait_for_layer_visible(page: Page, layer_id: str, timeout: int = 15_000) -> None:
    """
    Wait for a MapLibre layer to be visible.
    
    Args:
        page: Playwright Page instance
        layer_id: MapLibre layer ID (e.g., 'facility-circles', 'superfund-sites')
        timeout: Maximum wait time in milliseconds (default: 15s)
    """
    page.wait_for_function(
        f"""() => {{
            const map = window.__DEBUG_MAP__;
            if (!map) return false;
            const layer = map.getLayer('{layer_id}');
            if (!layer) return false;
            const visibility = map.getLayoutProperty('{layer_id}', 'visibility');
            return visibility !== 'none';
        }}""",
        timeout=timeout,
    )


def wait_for_layer_hidden(page: Page, layer_id: str, timeout: int = 5_000) -> None:
    """
    Wait for a MapLibre layer visibility to be 'none'.
    
    Args:
        page: Playwright Page instance
        layer_id: MapLibre layer ID
        timeout: Maximum wait time in milliseconds (default: 5s)
    """
    page.wait_for_function(
        f"""() => {{
            const map = window.__DEBUG_MAP__;
            if (!map) return false;
            const layer = map.getLayer('{layer_id}');
            return layer && map.getLayoutProperty('{layer_id}', 'visibility') === 'none';
        }}""",
        timeout=timeout,
    )


def get_map_center(page: Page) -> dict:
    """
    Get the current map center coordinates.
    
    Returns:
        dict with 'lat' and 'lon' keys, or {'error': message} if map not found
    """
    return page.evaluate('''() => {
        const map = window.__DEBUG_MAP__;
        if (!map) return { error: 'Map not found - window.__DEBUG_MAP__ not available' };
        const c = map.getCenter();
        return { lat: c.lat, lon: c.lng };
    }''')


def get_map_zoom(page: Page) -> float:
    """
    Get the current map zoom level.
    
    Returns:
        Zoom level as float, or -1 if map not found
    """
    return page.evaluate('''() => {
        const map = window.__DEBUG_MAP__;
        return map ? map.getZoom() : -1;
    }''')


def get_layer_info(page: Page, source_id: str, layer_id: str) -> dict:
    """
    Get information about a MapLibre layer.
    
    Args:
        page: Playwright Page instance
        source_id: MapLibre source ID
        layer_id: MapLibre layer ID
        
    Returns:
        dict with 'hasSource', 'hasLayer', 'layerVisibility', 'featureCount' keys
    """
    return page.evaluate(f'''() => {{
        const map = window.__DEBUG_MAP__;
        if (!map) return {{ error: 'Map not found' }};
        
        const source = map.getSource('{source_id}');
        const layer = map.getLayer('{layer_id}');
        
        return {{
            hasSource: !!source,
            hasLayer: !!layer,
            layerVisibility: layer ? map.getLayoutProperty('{layer_id}', 'visibility') : null,
            featureCount: source && source._data && source._data.features 
                ? source._data.features.length 
                : 0,
        }};
    }}''')


# Contract documentation: window.__DEBUG_MAP__
#
# The TOXMAP frontend MUST expose window.__DEBUG_MAP__ containing the MapLibre GL
# map instance. This is required for E2E test automation. Removing this global
# will break all map-related E2E tests.
#
# Location: frontend/src/components/MapContainer.tsx
# Assignment: window.__DEBUG_MAP__ = map  (in useEffect after map creation)
#
# This is NOT a production leak - it contains no sensitive data and provides
# read-only access to map state for test assertions.
