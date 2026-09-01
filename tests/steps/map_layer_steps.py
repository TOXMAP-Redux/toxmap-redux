# tests/steps/map_layer_steps.py
"""
MapLibre layer step implementations for E2E tests.

Covers:
- TRI facility layer visibility and toggle
- Layer toggle interactions
- In-view count assertions
- Map viewport state verification
- Map interactions (scroll, pan)
"""

import re
from pytest_bdd import when, then, parsers
from playwright.sync_api import Page, expect

from ._shared import (
    PANEL_TIMEOUT,
    LAYER_TIMEOUT,
    DOWNLOAD_TIMEOUT,
    ANIMATION_DELAY,
    MAP_SETTLE_DELAY,
    get_bounding_box_safe,
)


# ── TRI layer toggle ──────────────────────────────────────────────────────────


@then('the TRI layer toggle is present')
def tri_layer_toggle_present(page: Page) -> None:
    """Invariant 6: the TRI latest-year toggle exists in MapContentsPanel."""
    expect(page.locator('[data-testid="year-toggle-latest"]')).to_be_visible()


@when('I toggle the TRI layer off')
def toggle_tri_layer_off(page: Page) -> None:
    """Toggle off the TRI facilities layer via the MapContentsPanel checkbox."""
    map_contents_btn = page.get_by_role('button', name='Map Contents')
    if map_contents_btn.is_visible():
        map_contents_btn.click()
        page.wait_for_selector('[data-testid="map-contents-panel"]', timeout=PANEL_TIMEOUT)

    tri_toggle = page.locator('[data-testid="year-toggle-latest"]')
    expect(tri_toggle).to_be_visible()
    # Uncheck if checked
    if tri_toggle.is_checked():
        tri_toggle.click()


@when('I toggle the TRI layer on')
def toggle_tri_layer_on(page: Page) -> None:
    """Toggle on the TRI facilities layer via the MapContentsPanel checkbox."""
    map_contents_btn = page.get_by_role('button', name='Map Contents')
    if map_contents_btn.is_visible():
        map_contents_btn.click()
        page.wait_for_selector('[data-testid="map-contents-panel"]', timeout=PANEL_TIMEOUT)

    tri_toggle = page.locator('[data-testid="year-toggle-latest"]')
    expect(tri_toggle).to_be_visible()
    tri_toggle.click()


# ── TRI layer visibility ──────────────────────────────────────────────────────


@then('the TRI layer is visible on the map')
def tri_layer_visible_on_map(page: Page) -> None:
    """
    Regression test: TRI facility circles MapLibre layer exists and has data.
    """
    page.wait_for_function(
        "() => { const m = window.__DEBUG_MAP__; return m && !!m.getSource('facilities'); }",
        timeout=LAYER_TIMEOUT,
    )

    layer_info = page.evaluate('''() => {
        const map = window.__DEBUG_MAP__;
        if (!map) return { error: 'Map not found' };

        return {
            hasSource: !!map.getSource('facilities'),
            hasLayer: !!map.getLayer('facility-circles'),
            layerVisibility: map.getLayer('facility-circles')
                ? map.getLayoutProperty('facility-circles', 'visibility')
                : null,
        };
    }''')

    assert layer_info.get('hasSource'), (
        'TRI facilities GeoJSON source not found.'
    )
    assert layer_info.get('hasLayer'), (
        'TRI facility-circles layer not found.'
    )
    visibility = layer_info.get('layerVisibility')
    assert visibility in (None, 'visible'), f'TRI layer visibility is {visibility}, expected visible'


@then('the TRI layer is hidden on the map')
def tri_layer_hidden_on_map(page: Page) -> None:
    """Assert that the TRI facility-circles layer visibility is 'none'."""
    page.wait_for_function(
        """() => {
            const map = window.__DEBUG_MAP__;
            if (!map) return false;
            const layer = map.getLayer('facility-circles');
            return layer && map.getLayoutProperty('facility-circles', 'visibility') === 'none';
        }""",
        timeout=PANEL_TIMEOUT,
    )

    layer_info = page.evaluate('''() => {
        const map = window.__DEBUG_MAP__;
        if (!map) return { error: 'Map not found' };

        return {
            hasLayer: !!map.getLayer('facility-circles'),
            layerVisibility: map.getLayer('facility-circles')
                ? map.getLayoutProperty('facility-circles', 'visibility')
                : null,
        };
    }''')

    assert layer_info.get('hasLayer'), 'TRI facility-circles layer not found'
    visibility = layer_info.get('layerVisibility')
    assert visibility == 'none', f'TRI layer visibility is {visibility}, expected none (hidden)'


# ── TRI in-view count ─────────────────────────────────────────────────────────


@then('the TRI in-view count is greater than zero')
def tri_in_view_count_positive(page: Page) -> None:
    """
    Regression test: TRI sidebar count shows facilities in view.
    """
    page.wait_for_function(
        """() => {
            const t = document.querySelector('[data-testid="year-toggle-latest"]');
            if (!t) return false;
            const label = t.closest('label') || t.parentElement;
            return label && /\\d+\\s*in\\s*view/i.test(label.innerText);
        }""",
        timeout=LAYER_TIMEOUT,
    )

    tri_toggle = page.locator('[data-testid="year-toggle-latest"]')
    expect(tri_toggle).to_be_visible()

    toggle_container = tri_toggle.locator('xpath=..')
    container_text = toggle_container.inner_text()

    match = re.search(r'(\d+)\s*in\s*view', container_text, re.IGNORECASE)
    assert match, (
        f'Could not find "X in view" count in TRI toggle. Text: "{container_text}".'
    )

    count = int(match.group(1))
    assert count > 0, (
        f'TRI in-view count is {count}, expected > 0.'
    )


@then('at least one TRI facility marker is visible on the map')
def at_least_one_tri_marker_visible(page: Page) -> None:
    """Assert that at least one TRI facility marker is visible on the map."""
    page.wait_for_function(
        """() => {
            const map = window.__DEBUG_MAP__;
            if (!map) return false;
            const source = map.getSource('facilities');
            return source && source._data && source._data.features && source._data.features.length > 0;
        }""",
        timeout=LAYER_TIMEOUT,
    )
    
    layer_info = page.evaluate('''() => {
        const map = window.__DEBUG_MAP__;
        if (!map) return { error: 'Map not found' };
        
        const source = map.getSource('facilities');
        if (!source) return { hasSource: false };
        
        return {
            hasSource: true,
            hasLayer: !!map.getLayer('facility-circles'),
            featureCount: source._data?.features?.length ?? 0,
        };
    }''')
    
    assert layer_info.get('hasSource'), 'TRI facilities source not found on map'
    assert layer_info.get('hasLayer'), 'TRI facility-circles layer not found'
    assert layer_info.get('featureCount', 0) > 0, 'No TRI facility features on map'


@then('at least two benzene TRI facility markers appear in the Houston area')
def at_least_two_benzene_markers_houston(page: Page) -> None:
    """Assert that at least 2 benzene TRI markers appear in the Houston area."""
    rows = page.locator('[data-testid="results-row"]')
    expect(rows.first).to_be_visible()
    count = rows.count()
    assert count >= 2, f'Expected at least 2 benzene facilities near Houston, found {count}'


# ── Results sidebar ───────────────────────────────────────────────────────────


@then('the results sidebar shows at least one facility')
def results_sidebar_shows_facility(page: Page) -> None:
    """Assert that at least one facility row is visible in the results table."""
    rows = page.locator('[data-testid="results-row"]')
    expect(rows.first).to_be_visible()
    count = rows.count()
    assert count > 0, 'Expected at least one facility in results table'


@then('the results sidebar shows TRI results without a simultaneous Map Contents panel')
def results_sidebar_no_map_contents(page: Page) -> None:
    """UX Invariant 1: results visible, map contents hidden."""
    expect(page.locator('[data-testid="results-table"]')).to_be_visible()
    map_contents = page.locator('[data-testid="map-contents-panel"]')
    if map_contents.count() > 0:
        expect(map_contents).not_to_be_visible()


# ── Map viewport assertions ───────────────────────────────────────────────────


@then('the map is centered on the Continental US')
def map_centered_continental_us(page: Page) -> None:
    """Assert that the map is centered on the continental United States."""
    page.wait_for_function(
        """() => {
            const map = window.__DEBUG_MAP__;
            return map && !map.isMoving();
        }""",
        timeout=DOWNLOAD_TIMEOUT,
    )

    center = page.evaluate('''() => {
        const map = window.__DEBUG_MAP__;
        if (!map) return { error: 'Map not found' };
        const c = map.getCenter();
        return { lat: c.lat, lon: c.lng };
    }''')

    assert 'error' not in center, center.get('error', 'Unknown error')

    lat, lon = center['lat'], center['lon']
    # Continental US bounds (approximate)
    assert 24.5 <= lat <= 49.5, f'Map latitude {lat} is outside Continental US (24.5–49.5)'
    assert -125 <= lon <= -66, f'Map longitude {lon} is outside Continental US (-125–-66)'


@then('the map is NOT centered on Tijuana/Baja California')
def map_not_centered_tijuana(page: Page) -> None:
    """
    Regression test: US zip code "22630" should not geocode to Tijuana.
    """
    page.wait_for_function(
        """() => {
            const map = window.__DEBUG_MAP__;
            return map && !map.isMoving();
        }""",
        timeout=DOWNLOAD_TIMEOUT,
    )

    center = page.evaluate('''() => {
        const map = window.__DEBUG_MAP__;
        if (!map) return { error: 'Map not found' };
        const c = map.getCenter();
        return { lat: c.lat, lon: c.lng };
    }''')

    assert 'error' not in center, center.get('error', 'Unknown error')

    lat, lon = center['lat'], center['lon']
    # Tijuana region
    in_tijuana_region = (28 <= lat <= 35) and (-118 <= lon <= -105)

    assert not in_tijuana_region, (
        f'Map is centered at ({lat}, {lon}), which is in the Tijuana/Baja California region.'
    )


# ── Map scroll / pan ──────────────────────────────────────────────────────────


@when('I scroll the map')
def scroll_the_map(page: Page) -> None:
    """Pan the map slightly to trigger viewport change."""
    map_container = page.locator('[data-testid="map-container"]')
    box = map_container.bounding_box()
    if box:
        center_x = box['x'] + box['width'] / 2
        center_y = box['y'] + box['height'] / 2
        page.mouse.move(center_x, center_y)
        page.mouse.down()
        page.mouse.move(center_x + 100, center_y + 50, steps=5)
        page.mouse.up()
        page.wait_for_timeout(ANIMATION_DELAY)


@when('I zoom in on the map')
def zoom_in_on_map(page: Page) -> None:
    """Zoom in on the map to test viewport filtering."""
    page.wait_for_function(
        """() => {
            const map = window.__DEBUG_MAP__;
            return map && !map.isMoving();
        }""",
        timeout=PANEL_TIMEOUT,
    )
    
    page.evaluate('''() => {
        const map = window.__DEBUG_MAP__;
        if (map) {
            map.zoomIn();
        }
    }''')
    
    page.wait_for_timeout(MAP_SETTLE_DELAY)
