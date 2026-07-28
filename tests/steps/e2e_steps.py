# tests/steps/e2e_steps.py
#
# Phase 3 E2E step implementations — T-01, T-03, T-08, UX Invariants 1–4, 7–9.
# Uses pytest-playwright (page fixture) + pytest-bdd.
#
# data-testid values: docs/testing/TEST_ID_REGISTRY.md
# Gherkin source:    docs/testing/TOXMAP_ACCEPTANCE_TESTS.md Features 7 & 8
#
# Playwright tests connect to http://localhost:3000 (Vite dev server).
# Backend and database must be running (docker compose up) before running E2E tests.
# seed_db fixture provides seeded TRI + Superfund data from tests/fixtures/seed.sql.

import re
import pytest
from pytest_bdd import given, when, then, parsers, scenarios
from playwright.sync_api import Page, expect

# ── Register feature files ────────────────────────────────────────────────────

scenarios('../features/e2e/ucd_task_scenarios.feature')
scenarios('../features/e2e/ux_invariants.feature')

# ── Constants ─────────────────────────────────────────────────────────────────

_BASE_URL = 'http://localhost:3000'
_MAP_TIMEOUT = 20_000    # ms — map tile load can take a few seconds
_SEARCH_TIMEOUT = 15_000  # ms — geocoding + API call
_AUTOCOMPLETE_TIMEOUT = 3_000  # ms — debounced autocomplete

# ── Background steps ──────────────────────────────────────────────────────────


@given('the application is running at "http://localhost:3000"')
def app_running() -> None:
    """No-op: the running app is a precondition, not something we start in tests."""


@given('the seed database is loaded', target_fixture='seed_db_loaded')
def seed_database_loaded(seed_db) -> None:  # noqa: ARG001
    """Triggers the session-scoped seed_db fixture to ensure data is seeded."""


# ── Map page navigation ───────────────────────────────────────────────────────


@given('I am on the map page')
def i_am_on_map_page(page: Page) -> None:
    """Navigate to the TOXMAP app and wait for the map container to be ready."""
    page.goto(_BASE_URL)
    page.wait_for_selector('[data-testid="map-container"]', timeout=_MAP_TIMEOUT)


@given('I am on the map page in browse mode')
def i_am_on_map_page_browse(page: Page) -> None:
    """Navigate to the map page (default state shows MapContentsPanel)."""
    page.goto(_BASE_URL)
    page.wait_for_selector('[data-testid="map-container"]', timeout=_MAP_TIMEOUT)


# ── Search form interactions ───────────────────────────────────────────────────


@when(parsers.parse('I type "{text}" into the location field'))
def type_location(page: Page, text: str) -> None:
    """Fill the location text input. Opens Search panel if not already active."""
    if not page.locator('[data-testid="search-panel"]').is_visible():
        page.get_by_role('button', name='Search').click()
        page.wait_for_selector('[data-testid="search-panel"]', timeout=5_000)
    page.locator('[data-testid="location-input"]').fill(text)


@when(parsers.parse('I type "{text}" into the chemical field'))
def type_chemical(page: Page, text: str) -> None:
    """Type into the chemical input. Opens Search panel if not already active."""
    if not page.locator('[data-testid="search-panel"]').is_visible():
        page.get_by_role('button', name='Search').click()
        page.wait_for_selector('[data-testid="search-panel"]', timeout=5_000)
    chem_input = page.locator('[data-testid="chemical-input"]')
    chem_input.fill(text)


@when(parsers.parse('I select the chemical "{chemical}" from autocomplete'))
def select_chemical_from_autocomplete(page: Page, chemical: str) -> None:
    """Wait for autocomplete options and click the one matching the chemical name."""
    options = page.locator('[data-testid="chemical-autocomplete-option"]')
    options.first.wait_for(timeout=_AUTOCOMPLETE_TIMEOUT)
    # Click the option whose text matches (case-insensitive)
    matching = options.filter(has_text=re.compile(re.escape(chemical), re.IGNORECASE))
    matching.first.click()


@when(parsers.parse('I select year "{year}"'))
def select_year(page: Page, year: str) -> None:
    """Select a year from the year dropdown."""
    page.locator('[data-testid="year-select"]').select_option(year)


@when('I click "Search"')
def click_search(page: Page) -> None:
    """Submit the search form and wait for the results table to appear."""
    page.locator('[data-testid="search-submit-btn"]').click()
    page.wait_for_selector('[data-testid="results-table"]', timeout=_SEARCH_TIMEOUT)


@when('I click the search panel tab')
def click_search_panel_tab(page: Page) -> None:
    """Click the Search tab in the sidebar header."""
    page.get_by_role('button', name='Search').click()
    page.wait_for_selector('[data-testid="search-panel"]', timeout=5_000)


# ── Compound step: perform a full search ──────────────────────────────────────


@when(parsers.parse('I perform a search for "{chemical}" near "{location}"'))
def perform_search(page: Page, chemical: str, location: str) -> None:
    """Fills in chemical + location and submits search. Opens search panel if needed."""
    # Ensure search panel is open
    search_btn = page.get_by_role('button', name='Search')
    if search_btn.is_visible():
        search_btn.click()
    page.wait_for_selector('[data-testid="search-panel"]', timeout=5_000)

    page.locator('[data-testid="chemical-input"]').fill(chemical)
    page.locator('[data-testid="location-input"]').fill(location)
    page.locator('[data-testid="search-submit-btn"]').click()
    page.wait_for_selector('[data-testid="results-table"]', timeout=_SEARCH_TIMEOUT)


# ── Results table assertions ───────────────────────────────────────────────────


@then(parsers.parse('the results sidebar shows "{facility_name}"'))
def results_shows_facility(page: Page, facility_name: str) -> None:
    """Assert that a result row containing the facility name is visible."""
    expect(
        page.locator('[data-testid="results-row-name"]').filter(has_text=facility_name)
    ).to_be_visible()


@then('every row in the results table has a facility name')
def every_row_has_name(page: Page) -> None:
    """UX Invariant 2: no placeholder/empty rows."""
    rows = page.locator('[data-testid="results-row"]').all()
    assert len(rows) > 0, 'Results table has no rows'
    for row in rows:
        name_cell = row.locator('[data-testid="results-row-name"]')
        assert name_cell.inner_text().strip() != '', 'Found a row with an empty facility name'


@then('every row in the results table has a release amount')
def every_row_has_amount(page: Page) -> None:
    """UX Invariant 2: every row has a numeric release amount (not blank)."""
    rows = page.locator('[data-testid="results-row"]').all()
    for row in rows:
        amount_cell = row.locator('[data-testid="results-row-release"]')
        text = amount_cell.inner_text().strip()
        assert text != '', 'Found a row with an empty release amount'


@then('all visible release amounts contain a comma or dash')
def release_amounts_formatted(page: Page) -> None:
    """UX Invariant 8: comma-formatted or '—' for null values."""
    cells = page.locator('[data-testid="results-row-release"]').all()
    assert len(cells) > 0, 'No release amount cells found in results'
    for cell in cells:
        text = cell.inner_text().strip()
        # Valid formats: "12,485 lbs", "—", "0 lbs" (zero is a meaningful value per Data Integrity Rule 3)
        assert text, f'Empty release cell found'
        if text != '—' and text != '':
            # Should contain either a comma (for numbers ≥ 1,000) or be a small plain number
            # The invariant applies to numbers ≥ 1,000 specifically
            if re.search(r'\d{4}', text):  # 4-digit number present
                assert ',' in text, f'Release amount "{text}" ≥ 1000 is not comma-formatted'


# ── Facility click + detail ────────────────────────────────────────────────────


@when(parsers.parse('I click on "{facility_name}" in the results'))
def click_on_result(page: Page, facility_name: str) -> None:
    """Click on a specific facility row in the results table."""
    page.locator('[data-testid="results-row"]').filter(has_text=facility_name).click()
    page.wait_for_selector('[data-testid="facility-detail-panel"]', timeout=8_000)


@when('I click on the first result in the results table')
def click_first_result(page: Page) -> None:
    """Click the first result row — used for generic popup tests."""
    page.locator('[data-testid="results-row"]').first.click()
    page.wait_for_selector('[data-testid="facility-detail-panel"]', timeout=8_000)


@then('the facility detail panel opens')
def detail_panel_opens(page: Page) -> None:
    """Assert the facility detail panel is visible."""
    expect(page.locator('[data-testid="facility-detail-panel"]')).to_be_visible()


@then(parsers.parse('the detail panel shows "{amount}"'))
def detail_shows_amount(page: Page, amount: str) -> None:
    """Assert the release amount text is visible in the facility detail panel."""
    panel = page.locator('[data-testid="facility-detail-panel"]')
    expect(panel).to_contain_text(amount)


@then(parsers.parse('the detail panel shows "{amount}" for the year {year:d}'))
def detail_shows_amount_year(page: Page, amount: str, year: int) -> None:
    """Assert the release amount and year appear in the facility detail panel."""
    panel = page.locator('[data-testid="facility-detail-panel"]')
    expect(panel).to_contain_text(amount)
    expect(panel).to_contain_text(str(year))


@then('the release quantities are formatted with commas')
def release_quantities_formatted(page: Page) -> None:
    """UX Invariant 8: comma-formatting in the detail panel."""
    cells = page.locator('[data-testid="facility-release-amount"]').all()
    assert len(cells) > 0, 'No facility-release-amount elements found'
    for cell in cells:
        text = cell.inner_text().strip()
        if text != '—' and re.search(r'\d{4}', text):
            assert ',' in text, f'Amount "{text}" is not comma-formatted'


# ── Sidebar panel state (UX Invariants 1, 4) ──────────────────────────────────


@then('the map contents panel is visible')
def map_contents_visible(page: Page) -> None:
    """UX Invariant 1: MapContentsPanel is visible in default (non-search) state."""
    expect(page.locator('[data-testid="map-contents-panel"]')).to_be_visible()


@then('the search results panel is NOT visible')
def search_results_not_visible(page: Page) -> None:
    """UX Invariant 1: results table not visible in browse mode."""
    results = page.locator('[data-testid="results-table"]')
    # results-table is only rendered after a search
    expect(results).not_to_be_visible() if results.count() > 0 else None


@then('the search results panel is visible')
def search_results_visible(page: Page) -> None:
    """UX Invariant 1: results table visible after search."""
    expect(page.locator('[data-testid="results-table"]')).to_be_visible()


@then('the map contents panel is NOT visible')
def map_contents_not_visible(page: Page) -> None:
    """UX Invariant 1: MapContentsPanel is hidden when search is active."""
    panel = page.locator('[data-testid="map-contents-panel"]')
    # Panel is conditionally rendered — either hidden or not in DOM
    if panel.count() > 0:
        expect(panel).not_to_be_visible()


# ── Label assertions (UX Invariant 4) ─────────────────────────────────────────


@then('no element with text "Quick Search" exists in the DOM')
def no_quick_search_label(page: Page) -> None:
    """UX Invariant 4: 'Quick Search' must never appear as a label."""
    count = page.get_by_text('Quick Search', exact=True).count()
    assert count == 0, f'Found {count} element(s) with text "Quick Search" — must be zero'


@then('the search panel label is "Search Chemical Releases by Location"')
def search_panel_label_correct(page: Page) -> None:
    """UX Invariant 4: search panel must use the correct label."""
    # Click search tab to make it visible first
    search_btn = page.get_by_role('button', name='Search')
    if search_btn.is_visible():
        search_btn.click()
    expect(
        page.get_by_text('Search Chemical Releases by Location', exact=True)
    ).to_be_visible()


# ── State filter (UX Invariant 3) ─────────────────────────────────────────────


@then('the restrict-to-state checkbox is present')
def restrict_to_state_checkbox_present(page: Page) -> None:
    """UX Invariant 3: 'Limit to state' checkbox must be in the search panel."""
    expect(page.locator('[data-testid="restrict-to-state-checkbox"]')).to_be_visible()


# ── Latest year label (UX Invariant 7) ────────────────────────────────────────


@then('the latest year toggle label contains "(latest year)"')
def latest_year_label(page: Page) -> None:
    """UX Invariant 7: the most-recent year label must include '(latest year)'."""
    label = page.locator('[data-testid="year-toggle-latest"]')
    expect(label).to_be_visible()
    expect(label).to_contain_text('(latest year)')


# ── Close link at bottom (UX Invariant 9) ─────────────────────────────────────


@then('the close link at the bottom of the popup is present')
def popup_close_bottom_present(page: Page) -> None:
    """UX Invariant 9: the popup/drawer must have a close link at the bottom."""
    expect(page.locator('[data-testid="popup-close-bottom"]').first).to_be_visible()


# ── ATSDR link (T-08) ─────────────────────────────────────────────────────────


@then('the ATSDR link is visible for the selected chemical')
def atsdr_link_visible(page: Page) -> None:
    """T-08: ATSDR ToxFAQ link is visible after selecting a chemical."""
    expect(page.locator('[data-testid="atsdr-link"]').first).to_be_visible()


@then('the ATSDR link opens in a new tab')
def atsdr_link_new_tab(page: Page) -> None:
    """T-08: ATSDR link must open in a new tab (target=_blank + rel=noopener)."""
    link = page.locator('[data-testid="atsdr-link"]').first
    expect(link).to_have_attribute('target', '_blank')
    expect(link).to_have_attribute('rel', re.compile(r'noopener'))


# ── Stub steps for @skip-tagged Phase 5+ scenarios ───────────────────────────


@given('I open the TOXMAP application')
def open_app_stub() -> None:
    """Stub step for @skip-tagged future-phase scenarios."""
    pytest.skip('Scenario not yet implemented in this phase')


@then('a demographics scenario stub exists')
def demographics_stub() -> None:
    pytest.skip('Phase 5 scenario — not yet implemented')


@then('a chlorine scenario stub exists')
def chlorine_stub() -> None:
    pytest.skip('Phase 3 E2E — T-07 covered by API tests; E2E pending')


@then('a demographics invariant stub exists')
def demographics_invariant_stub() -> None:
    pytest.skip('Phase 5 invariant — not yet implemented')


# ── Phase 4: Superfund step implementations ──────────────────────────────────


@when(parsers.parse('I select the "{dataset}" dataset'))
def select_dataset(page: Page, dataset: str) -> None:
    """Select the TRI or Superfund dataset radio button in SearchPanel."""
    if not page.locator('[data-testid="search-panel"]').is_visible():
        page.get_by_role('button', name='Search').click()
        page.wait_for_selector('[data-testid="search-panel"]', timeout=5_000)
    testid = 'dataset-radio-tri' if dataset.lower() == 'tri' else 'dataset-radio-superfund'
    page.locator(f'[data-testid="{testid}"]').click()


@when(parsers.parse('I click on "{site_name}" in the Superfund results'))
def click_superfund_result(page: Page, site_name: str) -> None:
    """Click on a Superfund result row and wait for the detail panel."""
    page.locator('[data-testid="results-row"]').filter(has_text=site_name).click()
    page.wait_for_selector('[data-testid="superfund-detail-panel"]', timeout=8_000)


@then('the Superfund detail panel opens')
def superfund_detail_panel_opens(page: Page) -> None:
    """Assert the Superfund site detail panel is visible."""
    expect(page.locator('[data-testid="superfund-detail-panel"]')).to_be_visible()


@then('the contaminants list is visible')
def contaminants_list_visible(page: Page) -> None:
    """T-02: the contaminants list is visible within the detail panel."""
    expect(page.locator('[data-testid="superfund-contaminants-list"]')).to_be_visible()


@then(parsers.parse('the contaminants list contains "{contaminant}"'))
def contaminants_list_contains(page: Page, contaminant: str) -> None:
    """T-04: the contaminants list includes the named substance."""
    contaminants = page.locator('[data-testid="superfund-contaminants-list"]')
    expect(contaminants).to_be_visible()
    expect(contaminants).to_contain_text(contaminant)


@then('the EPA site progress profile link is present')
def epa_progress_link_present(page: Page) -> None:
    """T-04: the EPA site progress profile link is visible."""
    link = page.locator('[data-testid="superfund-epa-progress-link"]')
    expect(link).to_be_visible()
    expect(link).to_have_attribute('target', '_blank')
    expect(link).to_have_attribute('rel', re.compile(r'noopener'))


# ── Phase 4: UX Invariant 6 step implementations ─────────────────────────────


@then('the Superfund layer toggle is present')
def superfund_layer_toggle_present(page: Page) -> None:
    """Invariant 6: the Superfund layer toggle checkbox exists in MapContentsPanel."""
    expect(page.locator('[data-testid="layer-toggle-superfund"]')).to_be_visible()


@then('the TRI layer toggle is present')
def tri_layer_toggle_present(page: Page) -> None:
    """Invariant 6: the TRI latest-year toggle exists in MapContentsPanel."""
    expect(page.locator('[data-testid="year-toggle-latest"]')).to_be_visible()


@then('the TRI facility detail panel is not shown')
def tri_facility_detail_not_shown(page: Page) -> None:
    """Invariant 6: clicking a Superfund result opens the Superfund panel, not the TRI panel."""
    tri_panel = page.locator('[data-testid="facility-detail-panel"]')
    if tri_panel.count() > 0:
        expect(tri_panel).not_to_be_visible()


# ── Superfund Layer Visibility Regression Tests ──────────────────────────────
# These steps catch the React StrictMode bug in useSuperfundViewport where
# hasFetchedRef was set before fetch completion, causing the second mount to
# skip fetching entirely.


@then('the Superfund layer is visible on the map')
def superfund_layer_visible_on_map(page: Page) -> None:
    """
    Regression test: Superfund MapLibre layer exists and has data.

    This catches the bug where useSuperfundViewport's hasFetchedRef was set
    before the fetch completed, causing React StrictMode to skip the retry.
    Result: superfund-source and superfund-sites layer never created.
    """
    # Wait for map to fully load and data to arrive
    page.wait_for_timeout(2000)  # Allow time for API response and layer creation

    # Check MapLibre internals via page.evaluate
    layer_info = page.evaluate('''() => {
        const map = window.__DEBUG_MAP__;
        if (!map) return { error: 'Map not found' };

        return {
            hasSource: !!map.getSource('superfund-source'),
            hasLayer: !!map.getLayer('superfund-sites'),
            hasDiamondFilled: map.hasImage('superfund-diamond-filled'),
            hasDiamondOutline: map.hasImage('superfund-diamond-outline'),
            layerVisibility: map.getLayer('superfund-sites')
                ? map.getLayoutProperty('superfund-sites', 'visibility')
                : null,
        };
    }''')

    assert layer_info.get('hasSource'), (
        'Superfund GeoJSON source not found — useSuperfundViewport likely failed to fetch data. '
        'This may indicate the React StrictMode hasFetchedRef bug has regressed.'
    )
    assert layer_info.get('hasLayer'), (
        'Superfund symbol layer not found — MapContainer did not create the layer.'
    )
    assert layer_info.get('hasDiamondFilled'), 'superfund-diamond-filled sprite not registered'
    assert layer_info.get('hasDiamondOutline'), 'superfund-diamond-outline sprite not registered'
    # Visibility should be 'visible' or undefined (defaults to visible)
    visibility = layer_info.get('layerVisibility')
    assert visibility in (None, 'visible'), f'Superfund layer visibility is {visibility}, expected visible'


@then('the Superfund in-view count is greater than zero')
def superfund_in_view_count_positive(page: Page) -> None:
    """
    Regression test: Superfund sidebar count shows sites in view.

    If useSuperfundViewport fails to fetch data (StrictMode bug), the sidebar
    will show no count or "0 in view". This test ensures data was fetched.
    """
    # Wait for count to appear in the sidebar
    page.wait_for_timeout(2000)  # Allow time for data fetch and render

    # The MapContentsPanel shows "X in view" for Superfund sites
    superfund_toggle = page.locator('[data-testid="layer-toggle-superfund"]')
    expect(superfund_toggle).to_be_visible()

    # Get the text content of the toggle's parent or sibling that shows the count
    # The label structure is: "Superfund / NPL Sites X in view"
    toggle_container = superfund_toggle.locator('xpath=..')
    container_text = toggle_container.inner_text()

    # Extract the "X in view" number
    import re
    match = re.search(r'(\d+)\s*in\s*view', container_text, re.IGNORECASE)
    assert match, (
        f'Could not find "X in view" count in Superfund toggle. Text: "{container_text}". '
        'This may indicate useSuperfundViewport failed to fetch data (StrictMode bug).'
    )

    count = int(match.group(1))
    assert count > 0, (
        f'Superfund in-view count is {count}, expected > 0. '
        'The seed database has 2 Superfund sites; both should be visible at continental zoom. '
        'This may indicate useSuperfundViewport failed to fetch data.'
    )


# ── TRI Circle Layer Visibility Regression Tests ─────────────────────────────
# These steps catch the TRI browse mode 500-mile radius bug where browse mode
# called /api/v1/facilities with radius_miles=500 instead of /facilities/browse.
# They also catch the React StrictMode bug in useMapFacilities.


@then('the TRI layer is visible on the map')
def tri_layer_visible_on_map(page: Page) -> None:
    """
    Regression test: TRI facility circles MapLibre layer exists and has data.

    This catches the bug where browse mode used /api/v1/facilities with
    radius_miles=500 (only Kansas-area facilities) instead of /facilities/browse
    (all US facilities).
    """
    # Wait for map to fully load and data to arrive
    page.wait_for_timeout(2000)  # Allow time for API response and layer creation

    # Check MapLibre internals via page.evaluate
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
        'TRI facilities GeoJSON source not found — useMapFacilities likely failed to fetch data. '
        'This may indicate the browse mode 500-mile radius bug or React StrictMode issue has regressed.'
    )
    assert layer_info.get('hasLayer'), (
        'TRI facility-circles layer not found — MapContainer did not create the layer.'
    )
    # Visibility should be 'visible' or undefined (defaults to visible)
    visibility = layer_info.get('layerVisibility')
    assert visibility in (None, 'visible'), f'TRI layer visibility is {visibility}, expected visible'


@then('the TRI layer is hidden on the map')
def tri_layer_hidden_on_map(page: Page) -> None:
    """Assert that the TRI facility-circles layer visibility is 'none'."""
    page.wait_for_timeout(500)  # Allow time for toggle to take effect

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


@then('the TRI in-view count is greater than zero')
def tri_in_view_count_positive(page: Page) -> None:
    """
    Regression test: TRI sidebar count shows facilities in view.

    If useMapFacilities fails to fetch data or uses the old 500-mile radius,
    the sidebar will show 0 or a much smaller count than expected.
    """
    # Wait for count to appear in the sidebar
    page.wait_for_timeout(2000)  # Allow time for data fetch and render

    # The MapContentsPanel shows "X in view" for TRI facilities
    tri_toggle = page.locator('[data-testid="year-toggle-latest"]')
    expect(tri_toggle).to_be_visible()

    # Get the text content of the toggle's parent or sibling that shows the count
    toggle_container = tri_toggle.locator('xpath=..')
    container_text = toggle_container.inner_text()

    # Extract the "X in view" number
    match = re.search(r'(\d+)\s*in\s*view', container_text, re.IGNORECASE)
    assert match, (
        f'Could not find "X in view" count in TRI toggle. Text: "{container_text}". '
        'This may indicate useMapFacilities failed to fetch data.'
    )

    count = int(match.group(1))
    assert count > 0, (
        f'TRI in-view count is {count}, expected > 0. '
        'The seed database has facilities that should be visible at continental zoom. '
        'This may indicate useMapFacilities failed to fetch data or used wrong endpoint.'
    )


@then('the results sidebar shows at least one facility')
def results_sidebar_shows_facility(page: Page) -> None:
    """Assert that at least one facility row is visible in the results table."""
    rows = page.locator('[data-testid="results-row"]')
    expect(rows.first).to_be_visible()
    count = rows.count()
    assert count > 0, 'Expected at least one facility in results table'


@when('I toggle the TRI layer off')
def toggle_tri_layer_off(page: Page) -> None:
    """Toggle off the TRI facilities layer via the MapContentsPanel checkbox."""
    # Navigate to Map Contents panel if not already there
    map_contents_btn = page.get_by_role('button', name='Map Contents')
    if map_contents_btn.is_visible():
        map_contents_btn.click()
        page.wait_for_selector('[data-testid="map-contents-panel"]', timeout=5_000)

    tri_toggle = page.locator('[data-testid="year-toggle-latest"]')
    expect(tri_toggle).to_be_visible()
    # Click to toggle off (assumes it's currently checked)
    tri_toggle.click()


@when('I toggle the TRI layer on')
def toggle_tri_layer_on(page: Page) -> None:
    """Toggle on the TRI facilities layer via the MapContentsPanel checkbox."""
    # Navigate to Map Contents panel if not already there
    map_contents_btn = page.get_by_role('button', name='Map Contents')
    if map_contents_btn.is_visible() and not page.locator('[data-testid="map-contents-panel"]').is_visible():
        map_contents_btn.click()
        page.wait_for_selector('[data-testid="map-contents-panel"]', timeout=5_000)

    tri_toggle = page.locator('[data-testid="year-toggle-latest"]')
    expect(tri_toggle).to_be_visible()
    # Click to toggle on (assumes it's currently unchecked)
    tri_toggle.click()


