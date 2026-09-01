# tests/steps/results_steps.py
"""
Results table step implementations for E2E tests.

Covers:
- Results table visibility and content assertions
- Row content verification (names, amounts)
- Number formatting validation (UX Invariant 8)
"""

import re
from pytest_bdd import then, parsers
from playwright.sync_api import Page, expect

from ._shared import HEAVY_LOAD_TIMEOUT


# ── Results table visibility ──────────────────────────────────────────────────


@then('the search results panel is visible')
def search_results_visible(page: Page) -> None:
    """UX Invariant 1: results table visible after search."""
    expect(page.locator('[data-testid="results-table"]')).to_be_visible()


@then('the search results panel is NOT visible')
def search_results_not_visible(page: Page) -> None:
    """UX Invariant 1: results table not visible in browse mode."""
    results = page.locator('[data-testid="results-table"]')
    if results.count() > 0:
        expect(results).not_to_be_visible()


@then('the map contents panel is visible')
def map_contents_visible(page: Page) -> None:
    """UX Invariant 1: MapContentsPanel is visible in default (non-search) state."""
    expect(page.locator('[data-testid="map-contents-panel"]')).to_be_visible()


@then('the map contents panel is NOT visible')
def map_contents_not_visible(page: Page) -> None:
    """UX Invariant 1: MapContentsPanel is hidden when search is active."""
    panel = page.locator('[data-testid="map-contents-panel"]')
    if panel.count() > 0:
        expect(panel).not_to_be_visible()


# ── Results content assertions ────────────────────────────────────────────────


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
    release_locator = page.locator('[data-testid="results-row-release"]')
    release_locator.first.wait_for(state='visible', timeout=HEAVY_LOAD_TIMEOUT)
    
    cell_texts = release_locator.all_inner_texts()
    assert len(cell_texts) > 0, 'No release amount cells found in results'
    for text in cell_texts:
        text = text.strip()
        assert text, 'Empty release cell found'
        if text != '—' and text != '':
            # UX Invariant 8: numbers ≥ 1,000 must be comma-formatted
            if re.search(r'\d{4}', text):  # 4-digit number present
                assert ',' in text, f'Release amount "{text}" ≥ 1000 is not comma-formatted'


# ── Latest year label ─────────────────────────────────────────────────────────


@then('the latest year toggle label contains "(latest year)"')
def latest_year_label(page: Page) -> None:
    """UX Invariant 7: the most-recent year label must include '(latest year)'."""
    label = page.locator('[data-testid="year-toggle-latest"]')
    expect(label).to_be_visible()
    expect(label).to_contain_text('(latest year)')
