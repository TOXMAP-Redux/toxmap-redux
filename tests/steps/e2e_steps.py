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


@then('the state filter dropdown is present with label "Filter to state (optional)"')
def state_filter_dropdown_present(page: Page) -> None:
    """UX Invariant 3 (Option C): State dropdown is present with filter label."""
    # Check the dropdown exists
    expect(page.locator('[data-testid="state-select"]')).to_be_visible()
    # Check the label text
    label = page.locator('label[for="state-select"]')
    expect(label).to_contain_text('Filter to state')


@when(parsers.parse('I search for "{chemical}" with state filter "{state}"'))
def search_with_state_filter(page: Page, chemical: str, state: str) -> None:
    """Search for a chemical with state filter applied (Option C)."""
    if not page.locator('[data-testid="search-panel"]').is_visible():
        page.get_by_role('button', name='Search').click()
        page.wait_for_selector('[data-testid="search-panel"]', timeout=5_000)

    page.locator('[data-testid="chemical-input"]').fill(chemical)
    page.locator('[data-testid="state-select"]').select_option(state)
    page.locator('[data-testid="search-submit-btn"]').click()
    page.wait_for_selector('[data-testid="results-table"]', timeout=15_000)


@when('I clear the state filter')
def clear_state_filter(page: Page) -> None:
    """Clear the state filter by selecting 'All' (no filter)."""
    page.locator('[data-testid="state-select"]').select_option('')


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
    """Select the TRI, Superfund, or Both dataset radio button in SearchPanel."""
    if not page.locator('[data-testid="search-panel"]').is_visible():
        page.get_by_role('button', name='Search').click()
        page.wait_for_selector('[data-testid="search-panel"]', timeout=5_000)
    ds = dataset.lower()
    if ds == 'tri':
        testid = 'dataset-radio-tri'
    elif ds == 'superfund':
        testid = 'dataset-radio-superfund'
    else:  # 'both'
        testid = 'dataset-radio-both'
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


# ══════════════════════════════════════════════════════════════════════════════
# Regression Tests: "Both" Dataset Option (Fig 2015-4)
# ══════════════════════════════════════════════════════════════════════════════


@when('I click on the Search tab')
def click_search_tab(page: Page) -> None:
    """Click the Search tab in the sidebar header to open the search panel."""
    page.get_by_role('button', name='Search').click()
    page.wait_for_selector('[data-testid="search-panel"]', timeout=5_000)


@then('the "Both" dataset radio button is selected by default')
def both_dataset_selected_by_default(page: Page) -> None:
    """Assert that the 'Both' dataset radio button is checked by default."""
    both_radio = page.locator('[data-testid="dataset-radio-both"]')
    expect(both_radio).to_be_visible()
    expect(both_radio).to_be_checked()


@then('the "TRI" dataset radio button is present')
def tri_dataset_radio_present(page: Page) -> None:
    """Assert that the 'TRI' dataset radio button exists."""
    expect(page.locator('[data-testid="dataset-radio-tri"]')).to_be_visible()


@then('the "Superfund" dataset radio button is present')
def superfund_dataset_radio_present(page: Page) -> None:
    """Assert that the 'Superfund' dataset radio button exists."""
    expect(page.locator('[data-testid="dataset-radio-superfund"]')).to_be_visible()


@then('the results sidebar shows TRI and Superfund sections')
def results_shows_both_sections(page: Page) -> None:
    """Assert that the results table shows both TRI and Superfund sections."""
    results_table = page.locator('[data-testid="results-table"]')
    expect(results_table).to_be_visible()
    # Check for section count text pattern: "X TRI facilities · Y Superfund sites"
    expect(results_table).to_contain_text('TRI facilities')
    expect(results_table).to_contain_text('Superfund sites')


@then('the TRI section header is visible')
def tri_section_header_visible(page: Page) -> None:
    """Assert that the TRI section header is visible in the combined results."""
    results_table = page.locator('[data-testid="results-table"]')
    expect(results_table).to_contain_text('TRI Facilities')


@then('the Superfund section header is visible')
def superfund_section_header_visible(page: Page) -> None:
    """Assert that the Superfund section header is visible in the combined results."""
    results_table = page.locator('[data-testid="results-table"]')
    expect(results_table).to_contain_text('Superfund Sites')


# ══════════════════════════════════════════════════════════════════════════════
# Regression Tests: "Both" Mode Drawer Selection
# ══════════════════════════════════════════════════════════════════════════════
# These steps catch the bug where clicking a Superfund result in "Both" mode
# opened the TRI drawer instead of the Superfund drawer. Root cause was that
# handleOpenDetail checked `dataset === 'superfund'` instead of the result type.


@when(parsers.parse('I click on "{facility_name}" in the TRI results'))
def click_tri_result_in_both_mode(page: Page, facility_name: str) -> None:
    """Click on a TRI result row in the combined 'Both' mode results table."""
    # Find the TRI section by looking for the green header
    tri_section = page.locator('text=TRI Facilities').locator('xpath=following-sibling::table[1]')
    tri_row = tri_section.locator('[data-testid="results-row"]').filter(has_text=facility_name)
    tri_row.click()
    # Wait for the TRI drawer to open (drawer has class 'toxmap-drawer', popup has 'toxmap-popup')
    page.wait_for_selector('.toxmap-drawer[data-testid="facility-detail-panel"]', timeout=8_000)


@then('the TRI facility detail drawer opens')
def tri_facility_detail_drawer_opens(page: Page) -> None:
    """Assert the TRI facility detail drawer (not popup) is visible."""
    # Use class selector to distinguish drawer from popup
    expect(page.locator('.toxmap-drawer[data-testid="facility-detail-panel"]')).to_be_visible()


@then('the Superfund detail panel is not shown')
def superfund_detail_panel_not_shown(page: Page) -> None:
    """Assert the Superfund detail panel is NOT visible (when TRI drawer should be shown)."""
    superfund_panel = page.locator('[data-testid="superfund-detail-panel"]')
    if superfund_panel.count() > 0:
        expect(superfund_panel).not_to_be_visible()


# ══════════════════════════════════════════════════════════════════════════════
# Regression Tests: US Zip Code Geocoding
# ══════════════════════════════════════════════════════════════════════════════
# These steps catch the bug where US zip codes (e.g., "22630") were geocoded to
# Mexico instead of the US because Photon is a global geocoder.
# Fix: Append ", USA" to 5-digit zip code queries.


@then('the map is centered in the United States')
def map_centered_in_usa(page: Page) -> None:
    """
    Assert the map center is within continental US bounds.

    Continental US bounds (approximate):
    - Latitude: 24.5 (Key West) to 49.5 (northern border)
    - Longitude: -125 (west coast) to -66 (Maine)
    """
    page.wait_for_timeout(2000)  # Allow time for map to pan after geocoding

    center = page.evaluate('''() => {
        const map = window.__DEBUG_MAP__;
        if (!map) return { error: 'Map not found' };
        const c = map.getCenter();
        return { lat: c.lat, lon: c.lng };
    }''')

    assert 'error' not in center, center.get('error', 'Unknown error')

    lat, lon = center['lat'], center['lon']

    # Continental US bounds
    assert 24.5 <= lat <= 49.5, (
        f'Map latitude {lat} is outside continental US bounds (24.5 to 49.5). '
        f'This may indicate the US zip code geocoding fix has regressed.'
    )
    assert -125 <= lon <= -66, (
        f'Map longitude {lon} is outside continental US bounds (-125 to -66). '
        f'This may indicate the US zip code geocoding fix has regressed.'
    )


@then('the map is NOT centered in Mexico')
def map_not_centered_in_mexico(page: Page) -> None:
    """
    Assert the map center is NOT in Mexico (specifically not near Tijuana).

    Tijuana is at approximately (32.5, -117). The bug caused "22630" to geocode
    there instead of Front Royal, VA (38.9, -78.2).

    We check that the longitude is NOT in the Baja California / western Mexico
    region (-118 to -105) while latitude is in the border region (28 to 35).
    """
    page.wait_for_timeout(1000)  # Allow time for map to settle

    center = page.evaluate('''() => {
        const map = window.__DEBUG_MAP__;
        if (!map) return { error: 'Map not found' };
        const c = map.getCenter();
        return { lat: c.lat, lon: c.lng };
    }''')

    assert 'error' not in center, center.get('error', 'Unknown error')

    lat, lon = center['lat'], center['lon']

    # Tijuana / Baja California region check
    # If in this region, the geocoding likely returned Mexico instead of USA
    in_tijuana_region = (28 <= lat <= 35) and (-118 <= lon <= -105)

    assert not in_tijuana_region, (
        f'Map is centered at ({lat}, {lon}), which is in the Tijuana/Baja California region. '
        f'US zip code "22630" should geocode to Front Royal, VA (~38.9, ~-78.2), not Mexico. '
        f'This indicates the US zip code geocoding fix has regressed.'
    )


# ══════════════════════════════════════════════════════════════════════════════
# Phase 5: Demographics Step Implementations — T-05, T-06, T-09, Invariants 5, 10
# ══════════════════════════════════════════════════════════════════════════════


@when(parsers.parse('I search for TRI facilities releasing "{chemical}" near "{location}" in year "{year}"'))
def search_tri_chemical_location_year(page: Page, chemical: str, location: str, year: str) -> None:
    """Search for TRI facilities with chemical, location, and year filters."""
    # Open search panel if not visible
    if not page.locator('[data-testid="search-panel"]').is_visible():
        page.get_by_role('button', name='Search').click()
        page.wait_for_selector('[data-testid="search-panel"]', timeout=5_000)

    # Select TRI dataset
    page.locator('[data-testid="dataset-radio-tri"]').click()

    # Fill chemical
    page.locator('[data-testid="chemical-input"]').fill(chemical)

    # Fill location
    page.locator('[data-testid="location-input"]').fill(location)

    # Select year
    page.locator('[data-testid="year-select"]').select_option(year)

    # Submit search
    page.locator('[data-testid="search-submit-btn"]').click()
    page.wait_for_selector('[data-testid="results-table"]', timeout=_SEARCH_TIMEOUT)


@when(parsers.parse('I search for "{chemical}" near "{location}" in year "{year}"'))
def search_chemical_location_year(page: Page, chemical: str, location: str, year: str) -> None:
    """Search for chemical near a location in a specific year."""
    # Open search panel if not visible
    if not page.locator('[data-testid="search-panel"]').is_visible():
        page.get_by_role('button', name='Search').click()
        page.wait_for_selector('[data-testid="search-panel"]', timeout=5_000)

    # Fill chemical
    page.locator('[data-testid="chemical-input"]').fill(chemical)

    # Fill location
    page.locator('[data-testid="location-input"]').fill(location)

    # Select year
    page.locator('[data-testid="year-select"]').select_option(year)

    # Submit search
    page.locator('[data-testid="search-submit-btn"]').click()
    page.wait_for_selector('[data-testid="results-table"]', timeout=_SEARCH_TIMEOUT)


@then('at least one TRI facility marker is visible on the map')
def at_least_one_tri_marker_visible(page: Page) -> None:
    """Assert that at least one TRI facility marker is visible on the map."""
    page.wait_for_timeout(2000)  # Allow time for map render
    
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
    # The results table should show at least 2 facilities
    rows = page.locator('[data-testid="results-row"]')
    expect(rows.first).to_be_visible()
    count = rows.count()
    assert count >= 2, f'Expected at least 2 benzene facilities near Houston, found {count}'


@then('the results sidebar shows TRI results without a simultaneous Map Contents panel')
def results_sidebar_no_map_contents(page: Page) -> None:
    """UX Invariant 1: results visible, map contents hidden."""
    expect(page.locator('[data-testid="results-table"]')).to_be_visible()
    map_contents = page.locator('[data-testid="map-contents-panel"]')
    if map_contents.count() > 0:
        expect(map_contents).not_to_be_visible()


@when(parsers.parse('I open the "US Census & Health Data" panel'))
def open_census_health_panel(page: Page) -> None:
    """Open the US Census & Health Data panel via Map Contents."""
    # Navigate to Map Contents panel
    map_contents_btn = page.get_by_role('button', name='Map Contents')
    if map_contents_btn.is_visible():
        map_contents_btn.click()
        page.wait_for_selector('[data-testid="map-contents-panel"]', timeout=5_000)
    
    # The census health panel is part of map contents
    expect(page.locator('[data-testid="census-health-panel"]')).to_be_visible()


@when(parsers.parse('I select "Population" > "% Under 18" > "Census 2000"'))
def select_population_under_18(page: Page) -> None:
    """Navigate to Population > % Under 18 > Census 2000 in the demographics panel."""
    # Census 2000 is default, so just ensure population tab + sub-layer
    page.locator('[data-testid="demo-tab-population"]').click()
    page.locator('[data-testid="demo-sublayer-pct-under-18"]').click()


@when(parsers.parse('I select "Income" > "Median Household Income" > "Census 2000"'))
def select_income_median(page: Page) -> None:
    """Navigate to Income > Median Household Income > Census 2000."""
    page.locator('[data-testid="demo-tab-income"]').click()
    page.locator('[data-testid="demo-sublayer-median-income"]').click()


@when(parsers.parse('I select "Mortality" > "Cancer Mortality" > "Female" > "Census 2000"'))
def select_mortality_cancer_female(page: Page) -> None:
    """Navigate to Mortality > Cancer Mortality > Female > Census 2000."""
    page.locator('[data-testid="demo-tab-mortality"]').click()
    # Ensure Female radio is selected (default)
    page.locator('input[name="mortality-gender"][value="female"]').check()
    page.locator('[data-testid="demo-sublayer-cancer-female"]').click()


@then('the map shows county-level color shading')
def map_shows_county_shading(page: Page) -> None:
    """Assert that the demographics choropleth layer is visible on the map."""
    page.wait_for_timeout(2000)  # Allow time for API and render
    
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
    # Same as county shading — the layer is the same, just different data property
    page.wait_for_timeout(2000)
    
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
def each_legend_label_has_dollar(page: Page) -> None:
    """Assert each legend entry contains a $ symbol."""
    entries = page.locator('[data-testid="demographic-legend-entry"]').all()
    assert len(entries) >= 3, f'Expected at least 3 legend entries, found {len(entries)}'
    for entry in entries:
        text = entry.inner_text()
        assert '$' in text, f'Legend entry "{text}" does not contain $ symbol'


@when(parsers.parse('I click "Clear layer" in the demographic panel'))
def click_clear_layer(page: Page) -> None:
    """Click the Clear layer button in the demographic legend."""
    page.locator('[data-testid="clear-layer-btn"]').click()


@then('the county color shading is removed from the map')
def county_shading_removed(page: Page) -> None:
    """Assert the demographics layer is no longer on the map."""
    page.wait_for_timeout(500)  # Allow time for layer removal
    
    layer_info = page.evaluate('''() => {
        const map = window.__DEBUG_MAP__;
        if (!map) return { error: 'Map not found' };
        
        return {
            hasSource: !!map.getSource('demographics-source'),
            hasFillLayer: !!map.getLayer('demographics-fill'),
        };
    }''')
    
    # Source and layer should be gone after clearing
    assert not layer_info.get('hasFillLayer'), 'Demographics fill layer still present after clear'


@then('the legend disappears')
def legend_disappears(page: Page) -> None:
    """Assert the demographic legend is no longer visible."""
    legend = page.locator('[data-testid="demographic-legend"]')
    if legend.count() > 0:
        expect(legend).not_to_be_visible()


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
    entries = page.locator('[data-testid="demographic-legend-entry"]').all()
    assert len(entries) >= 3, 'Expected at least 3 legend entries'
    for entry in entries:
        text = entry.inner_text()
        # Entry should contain at least one digit or range indicator
        assert re.search(r'\d', text), f'Legend entry "{text}" has no numeric value'


@then(parsers.parse('each legend entry includes the unit "{unit}"'))
def each_legend_entry_includes_unit(page: Page, unit: str) -> None:
    """Assert each legend entry contains the specified unit."""
    entries = page.locator('[data-testid="demographic-legend-entry"]').all()
    assert len(entries) >= 3, 'Expected at least 3 legend entries'
    for entry in entries:
        text = entry.inner_text()
        assert unit in text, f'Legend entry "{text}" does not include unit "{unit}"'


# ── Nationwide Chemical Search Regression Tests ──────────────────────────────
# These steps test the nationwide search feature where users can search by
# chemical without entering a location. Both TRI and Superfund results should
# be filtered by the chemical name (client-side filtering for Superfund).


@when('I leave the location field empty')
def leave_location_empty(page: Page) -> None:
    """Ensure the location field is empty for a nationwide search."""
    if not page.locator('[data-testid="search-panel"]').is_visible():
        page.get_by_role('button', name='Search').click()
        page.wait_for_selector('[data-testid="search-panel"]', timeout=5_000)
    # Clear the location field
    page.locator('[data-testid="location-input"]').fill('')


@then(parsers.parse('the results summary shows "{expected_text}"'))
def results_summary_shows(page: Page, expected_text: str) -> None:
    """
    Assert the results summary contains the expected text.
    
    The results summary shows counts like "1 TRI facilities · 1 Superfund sites".
    """
    summary = page.locator('[data-testid="results-summary"]')
    expect(summary).to_be_visible()
    expect(summary).to_contain_text(expected_text)


@then(parsers.parse('the results summary does not show "{text}"'))
def results_summary_does_not_show(page: Page, text: str) -> None:
    """Assert the results summary does not contain the specified text."""
    summary = page.locator('[data-testid="results-summary"]')
    expect(summary).to_be_visible()
    actual_text = summary.inner_text()
    assert text not in actual_text, f'Results summary "{actual_text}" unexpectedly contains "{text}"'


@then('the map is zoomed to US continental view')
def map_zoomed_to_us_view(page: Page) -> None:
    """
    Assert the map is zoomed out to show the continental US.
    
    For nationwide searches, the map should zoom to approximately:
    - Center: lat ~38.5, lon ~-96
    - Zoom: ~4
    """
    page.wait_for_timeout(1000)  # Allow time for zoom animation
    
    view_state = page.evaluate('''() => {
        const map = window.__DEBUG_MAP__;
        if (!map) return { error: 'Map not found' };
        
        return {
            center: map.getCenter(),
            zoom: map.getZoom(),
        };
    }''')
    
    assert 'error' not in view_state, f'Map error: {view_state.get("error")}'
    
    center = view_state.get('center', {})
    zoom = view_state.get('zoom', 0)
    
    # US continental view is approximately:
    # - Latitude: 35-42 (center around 38.5)
    # - Longitude: -105 to -85 (center around -96)
    # - Zoom: 3-5
    lat = center.get('lat', 0)
    lon = center.get('lng', 0)
    
    assert 30 <= lat <= 45, f'Map center latitude {lat} is not in US continental range (30-45)'
    assert -120 <= lon <= -70, f'Map center longitude {lon} is not in US continental range (-120 to -70)'
    assert 3 <= zoom <= 6, f'Map zoom {zoom} is not at US overview level (3-6)'


# ── State Filter Regression Tests ─────────────────────────────────────────────
# These steps test the state filter dropdown including the "Continental US" option.

# Continental US = 48 contiguous states + DC (excludes AK, HI, and territories)
CONTINENTAL_US_STATES = {
    'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', 'IA', 'ID', 'IL', 'IN',
    'KS', 'KY', 'LA', 'MA', 'MD', 'ME', 'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE',
    'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX',
    'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY',
}


@then(parsers.parse('the state filter dropdown shows "{option}" as the selected option'))
def state_filter_shows_selected(page: Page, option: str) -> None:
    """Assert the state filter dropdown has the specified option selected."""
    select = page.locator('[data-testid="state-select"]')
    expect(select).to_be_visible()
    # Get the selected option text
    selected_text = select.locator('option:checked').inner_text()
    assert selected_text == option, f'State filter shows "{selected_text}", expected "{option}"'


@then(parsers.parse('the state filter dropdown contains "{option}" option'))
def state_filter_contains_option(page: Page, option: str) -> None:
    """Assert the state filter dropdown contains the specified option."""
    select = page.locator('[data-testid="state-select"]')
    expect(select).to_be_visible()
    options = select.locator('option').all_inner_texts()
    assert option in options, f'State filter does not contain "{option}". Options: {options}'


@when(parsers.parse('I select "{option}" from the state filter'))
def select_state_filter_option(page: Page, option: str) -> None:
    """Select an option from the state filter dropdown."""
    select = page.locator('[data-testid="state-select"]')
    # Map display text to value
    if option == 'All':
        select.select_option('')
    elif option == 'Continental US':
        select.select_option('CONUS')
    else:
        select.select_option(option)


@then('all results are from continental US states')
def all_results_are_conus(page: Page) -> None:
    """
    Assert all facilities in the results are from continental US states.
    
    Continental US = 48 contiguous states + DC.
    Excludes: AK, HI, and territories (AS, GU, MP, PR, VI).
    """
    # Get all result rows and their state info
    rows = page.locator('[data-testid="results-row"]').all()
    assert len(rows) > 0, 'No results to verify'
    
    for row in rows:
        # Each row has a city/state like "HOUSTON, TX" or "SPARROWS POINT, MD"
        # The state code is the last 2 chars before any status text
        row_text = row.inner_text()
        # Extract state code - look for 2-letter code pattern
        match = re.search(r'\b([A-Z]{2})\b', row_text)
        if match:
            state = match.group(1)
            # Skip if it's a status like "NPL"
            if state in ('NPL', 'HRS'):
                # Try to find another match
                matches = re.findall(r'\b([A-Z]{2})\b', row_text)
                for m in matches:
                    if m in CONTINENTAL_US_STATES or m in ('AK', 'HI', 'AS', 'GU', 'MP', 'PR', 'VI'):
                        state = m
                        break
            if state in CONTINENTAL_US_STATES:
                continue
            if state in ('AK', 'HI', 'AS', 'GU', 'MP', 'PR', 'VI'):
                raise AssertionError(
                    f'Found non-CONUS result with state "{state}" in row: {row_text}. '
                    'Continental US filter should exclude AK, HI, and territories.'
                )


@then(parsers.parse('no result shows "{text}" in the facility name'))
def no_result_shows_facility_text(page: Page, text: str) -> None:
    """Assert that no results row contains the specified text in its facility name."""
    rows = page.locator('[data-testid="results-row"]').all()
    for row in rows:
        row_text = row.inner_text()
        assert text not in row_text, (
            f'Found excluded facility text "{text}" in results row: {row_text}'
        )

