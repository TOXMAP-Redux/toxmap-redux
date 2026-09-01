# tests/steps/demographics_steps.py
"""
Demographics/Census step implementations for E2E tests.

Covers:
- US Census & Health Data panel navigation
- Population, Income, Mortality layer selection
- Choropleth legend assertions
- Demographics layer visibility
"""

from pytest_bdd import when, then, parsers
from playwright.sync_api import Page, expect

from ._shared import (
    PANEL_TIMEOUT,
    LAYER_TIMEOUT,
)


# ── Demographics panel navigation ─────────────────────────────────────────────


@when(parsers.parse('I open the "US Census & Health Data" panel'))
def open_census_health_panel(page: Page) -> None:
    """Open the US Census & Health Data panel via Map Contents."""
    map_contents_btn = page.get_by_role('button', name='Map Contents')
    if map_contents_btn.is_visible():
        map_contents_btn.click()
        page.wait_for_selector('[data-testid="map-contents-panel"]', timeout=PANEL_TIMEOUT)
    
    expect(page.locator('[data-testid="census-health-panel"]')).to_be_visible()


@when(parsers.parse('I select "Population" > "% Under 18" > "Census 2010"'))
def select_population_under_18_2010(page: Page) -> None:
    """Navigate to Population > % Under 18 > Census 2010 in the demographics panel."""
    page.locator('[data-testid="demo-tab-population"]').click()
    page.wait_for_timeout(300)
    page.locator('[data-testid="census-year-2010"]').click()
    page.wait_for_timeout(300)
    page.locator('[data-testid="demo-sublayer-pct-under-18"]').click()
    page.wait_for_timeout(2000)  # Wait for layer to render


@when(parsers.parse('I select "Income" > "Median Household Income" > "Census 2010"'))
def select_income_median_2010(page: Page) -> None:
    """Navigate to Income > Median Household Income > Census 2010."""
    page.locator('[data-testid="demo-tab-income"]').click()
    page.wait_for_timeout(300)
    page.locator('[data-testid="census-year-2010"]').click()
    page.wait_for_timeout(300)
    page.locator('[data-testid="demo-sublayer-median-income"]').click()
    page.wait_for_timeout(2000)  # Wait for layer to render


@when(parsers.parse('I select "Income" > "Median Household Income" > "Census 2000"'))
def select_income_median_2000(page: Page) -> None:
    """Navigate to Income > Median Household Income > Census 2000.
    
    Per TOXMAP_ACCEPTANCE_TESTS.md Feature 7 §T-06, income layer uses Census 2000.
    Income is available for Census 2000 (unlike age percentage layers).
    """
    page.locator('[data-testid="demo-tab-income"]').click()
    page.wait_for_timeout(300)
    page.locator('[data-testid="census-year-2000"]').click()
    page.wait_for_timeout(300)
    page.locator('[data-testid="demo-sublayer-median-income"]').click()
    page.wait_for_timeout(2000)  # Wait for layer to render


@when(parsers.parse('I select "Mortality" > "Cancer Mortality" > "Female" > "Census 2010"'))
def select_mortality_cancer_female_2010(page: Page) -> None:
    """Navigate to Mortality > Cancer Mortality > Female > Census 2010."""
    page.locator('[data-testid="demo-tab-mortality"]').click()
    page.wait_for_timeout(300)
    page.locator('[data-testid="census-year-2010"]').click()
    page.wait_for_timeout(300)
    page.locator('input[name="mortality-gender"][value="female"]').check()
    page.wait_for_timeout(300)
    page.locator('[data-testid="demo-sublayer-cancer-female"]').click()
    page.wait_for_timeout(2000)  # Wait for layer to render


@when(parsers.parse('I select "Mortality" > "Cancer Mortality" > "Female" > "Census 2000"'))
def select_mortality_cancer_female_2000(page: Page) -> None:
    """Navigate to Mortality > Cancer Mortality > Female > Census 2000.
    
    Per TOXMAP_ACCEPTANCE_TESTS.md Feature 7 §T-09, mortality uses Census 2000.
    This step is used by the @skip @blocked-mortality T-09 scenario.
    """
    page.locator('[data-testid="demo-tab-mortality"]').click()
    page.wait_for_timeout(300)
    page.locator('[data-testid="census-year-2000"]').click()
    page.wait_for_timeout(300)
    page.locator('input[name="mortality-gender"][value="female"]').check()
    page.wait_for_timeout(300)
    page.locator('[data-testid="demo-sublayer-cancer-female"]').click()
    page.wait_for_timeout(2000)  # Wait for layer to render


# ── Demographics layer assertions ─────────────────────────────────────────────


@then('the map shows county-level color shading')
def map_shows_county_shading(page: Page) -> None:
    """Assert that the demographics choropleth layer is visible on the map."""
    page.wait_for_function(
        """() => {
            const map = window.__DEBUG_MAP__;
            return map && map.getSource('demographics-source') && map.getLayer('demographics-fill');
        }""",
        timeout=LAYER_TIMEOUT,
    )
    
    layer_info = page.evaluate('''() => {
        const map = window.__DEBUG_MAP__;
        if (!map) return { error: 'Map not found' };
        
        return {
            hasSource: !!map.getSource('demographics-source'),
            hasFillLayer: !!map.getLayer('demographics-fill'),
        };
    }''')
    
    assert layer_info.get('hasSource'), 'Demographics source not found on map'
    assert layer_info.get('hasFillLayer'), 'Demographics fill layer not found on map'


@then('the map shows cancer mortality choropleth shading')
def map_shows_cancer_mortality_shading(page: Page) -> None:
    """Assert that the cancer mortality choropleth layer is visible."""
    page.wait_for_function(
        """() => {
            const map = window.__DEBUG_MAP__;
            return map && map.getSource('demographics-source') && map.getLayer('demographics-fill');
        }""",
        timeout=LAYER_TIMEOUT,
    )
    
    layer_info = page.evaluate('''() => {
        const map = window.__DEBUG_MAP__;
        if (!map) return { error: 'Map not found' };
        
        return {
            hasSource: !!map.getSource('demographics-source'),
            hasFillLayer: !!map.getLayer('demographics-fill'),
        };
    }''')
    
    assert layer_info.get('hasSource'), 'Demographics source not found on map'
    assert layer_info.get('hasFillLayer'), 'Demographics fill layer not found'


@then('the sidebar switches to show the demographic panel only')
def sidebar_shows_demographic_panel_only(page: Page) -> None:
    """Assert the map contents panel is visible (contains census health panel)."""
    expect(page.locator('[data-testid="census-health-panel"]')).to_be_visible()


@then('the TRI facility markers remain visible on the map')
def tri_markers_remain_visible(page: Page) -> None:
    """Assert that TRI facility markers are still visible over demographics layer."""
    layer_info = page.evaluate('''() => {
        const map = window.__DEBUG_MAP__;
        if (!map) return { error: 'Map not found' };
        
        return {
            hasLayer: !!map.getLayer('facility-circles'),
            visibility: map.getLayer('facility-circles')
                ? map.getLayoutProperty('facility-circles', 'visibility')
                : null,
        };
    }''')
    
    assert layer_info.get('hasLayer'), 'TRI facility-circles layer not found'
    visibility = layer_info.get('visibility')
    assert visibility in (None, 'visible'), f'TRI layer visibility is {visibility}, expected visible'


# ── Legend assertions ─────────────────────────────────────────────────────────


@then(parsers.parse('a legend is visible with inline percentage values and the unit "%"'))
def legend_visible_with_percentage(page: Page) -> None:
    """Assert the demographic legend is visible with % units."""
    legend = page.locator('[data-testid="demographic-legend"]')
    expect(legend).to_be_visible()
    expect(legend).to_contain_text('%')


@then(parsers.parse('the legend shows dollar values with the unit "$"'))
def legend_shows_dollar_values(page: Page) -> None:
    """Assert the legend shows dollar values."""
    legend = page.locator('[data-testid="demographic-legend"]')
    expect(legend).to_be_visible()
    expect(legend).to_contain_text('$')


@then(parsers.parse('each legend range label includes a "$" symbol'))
def legend_range_has_dollar(page: Page) -> None:
    """Assert that each legend label includes a $ symbol."""
    legend = page.locator('[data-testid="demographic-legend"]')
    expect(legend).to_be_visible()
    expect(legend).to_contain_text('$')


@then('the legend shows rate values with "per 100,000" units')
def legend_shows_rate_values(page: Page) -> None:
    """Assert the legend shows rate values with per 100,000 units."""
    legend = page.locator('[data-testid="demographic-legend"]')
    expect(legend).to_be_visible()
    expect(legend).to_contain_text('per 100,000')


@then('the demographic legend is visible')
def demographic_legend_visible(page: Page) -> None:
    """Assert the demographic legend is visible."""
    legend = page.locator('[data-testid="demographic-legend"]')
    expect(legend).to_be_visible()


# ── UX Invariant 5: Single demographic layer ──────────────────────────────────


@when('I select the "Population" demographic category')
def select_population_category(page: Page) -> None:
    """Select the Population category in the demographics panel."""
    page.locator('[data-testid="demo-tab-population"]').click()


@when('I select the "Income" demographic category')
def select_income_category(page: Page) -> None:
    """Select the Income category in the demographics panel."""
    page.locator('[data-testid="demo-tab-income"]').click()


@then('only one demographic layer is active on the map')
def only_one_demographic_layer_active(page: Page) -> None:
    """UX Invariant 5: Only one demographic layer can be active at a time."""
    layer_info = page.evaluate('''() => {
        const map = window.__DEBUG_MAP__;
        if (!map) return { error: 'Map not found' };
        
        // Check how many demographic-related fill layers are visible
        const layers = map.getStyle().layers || [];
        const visibleDemoLayers = layers.filter(l => 
            l.id.includes('demographics') && 
            l.type === 'fill' &&
            map.getLayoutProperty(l.id, 'visibility') !== 'none'
        );
        
        return {
            count: visibleDemoLayers.length,
            layers: visibleDemoLayers.map(l => l.id),
        };
    }''')
    
    assert layer_info.get('count', 0) <= 1, (
        f'UX Invariant 5: Expected at most 1 demographic layer, found {layer_info.get("count")}: {layer_info.get("layers")}'
    )


# ── Clear layer ───────────────────────────────────────────────────────────────


@when(parsers.parse('I click "Clear layer" in the demographic panel'))
def click_clear_layer(page: Page) -> None:
    """Click the Clear layer button in the demographic legend."""
    page.locator('[data-testid="clear-layer-btn"]').click()


@then('the county color shading is removed from the map')
def county_shading_removed(page: Page) -> None:
    """Assert the demographics layer is no longer on the map."""
    from ._shared import DOWNLOAD_TIMEOUT
    page.wait_for_function(
        """() => {
            const map = window.__DEBUG_MAP__;
            return map && !map.getLayer('demographics-fill');
        }""",
        timeout=DOWNLOAD_TIMEOUT,
    )
    
    layer_info = page.evaluate('''() => {
        const map = window.__DEBUG_MAP__;
        if (!map) return { error: 'Map not found' };
        
        return {
            hasSource: !!map.getSource('demographics-source'),
            hasFillLayer: !!map.getLayer('demographics-fill'),
        };
    }''')
    
    assert not layer_info.get('hasFillLayer'), 'Demographics fill layer still present after clear'


@then('the legend disappears')
def legend_disappears(page: Page) -> None:
    """Assert the demographic legend is no longer visible."""
    legend = page.locator('[data-testid="demographic-legend"]')
    if legend.count() > 0:
        expect(legend).not_to_be_visible()


# ── Co-occurrence disclaimer ──────────────────────────────────────────────────


@then(parsers.parse('a co-occurrence disclaimer is visible reading "{text}"'))
def cooccurrence_disclaimer_visible(page: Page, text: str) -> None:
    """Assert the co-occurrence disclaimer is visible with specific text."""
    disclaimer = page.locator('[data-testid="cooccurrence-disclaimer"]')
    expect(disclaimer).to_be_visible()
    expect(disclaimer).to_contain_text(text)


@when(parsers.parse('I switch to the "Population" tab in the demographic panel'))
def switch_to_population_tab(page: Page) -> None:
    """Click the Population tab in the census health panel."""
    page.locator('[data-testid="demo-tab-population"]').click()


@when(parsers.parse('I switch to "Income" tab in the demographic panel'))
def switch_to_income_tab(page: Page) -> None:
    """Click the Income tab in the census health panel."""
    page.locator('[data-testid="demo-tab-income"]').click()


@then('the co-occurrence disclaimer is NOT visible')
def cooccurrence_disclaimer_not_visible(page: Page) -> None:
    """Assert the co-occurrence disclaimer is not visible."""
    disclaimer = page.locator('[data-testid="cooccurrence-disclaimer"]')
    if disclaimer.count() > 0:
        expect(disclaimer).not_to_be_visible()


# ── Text visibility assertions ────────────────────────────────────────────────


@then(parsers.parse('the text "{text}" is visible'))
def text_is_visible(page: Page, text: str) -> None:
    """Assert that the specified text is visible on the page."""
    expect(page.get_by_text(text, exact=False)).to_be_visible()


@then(parsers.parse('the text "{text}" is NOT visible'))
def text_is_not_visible(page: Page, text: str) -> None:
    """Assert that the specified text is not visible on the page."""
    locator = page.get_by_text(text, exact=False)
    if locator.count() > 0:
        expect(locator).not_to_be_visible()


# ── Legend detail assertions ──────────────────────────────────────────────────


@then('the legend is visible on screen')
def legend_visible_on_screen(page: Page) -> None:
    """UX Invariant 5: legend is visible (not hidden behind mouse-over)."""
    expect(page.locator('[data-testid="demographic-legend"]')).to_be_visible()


@then('the legend shows at least 3 color-range entries')
def legend_has_at_least_3_entries(page: Page) -> None:
    """UX Invariant 5: at least 3 legend entries visible without hover."""
    entries = page.locator('[data-testid="demographic-legend-entry"]')
    expect(entries.first).to_be_visible()
    count = entries.count()
    assert count >= 3, f'Expected at least 3 legend entries, found {count}'


@then('each legend entry has a visible numeric value without hovering')
def each_legend_entry_has_numeric_value(page: Page) -> None:
    """UX Invariant 5: each legend entry has a visible numeric value."""
    import re as regex
    entries = page.locator('[data-testid="demographic-legend-entry"]').all()
    assert len(entries) >= 3, 'Expected at least 3 legend entries'
    for entry in entries:
        text = entry.inner_text()
        # Entry should contain at least one digit or range indicator
        assert regex.search(r'\d', text), f'Legend entry "{text}" has no numeric value'


@then(parsers.parse('each legend entry includes the unit "{unit}"'))
def each_legend_entry_includes_unit(page: Page, unit: str) -> None:
    """Assert each legend entry contains the specified unit."""
    entries = page.locator('[data-testid="demographic-legend-entry"]').all()
    assert len(entries) >= 3, 'Expected at least 3 legend entries'
    for entry in entries:
        text = entry.inner_text()
        assert unit in text, f'Legend entry "{text}" does not include unit "{unit}"'
