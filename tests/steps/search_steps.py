# tests/steps/search_steps.py
"""
Search form step implementations for E2E tests.

Covers:
- Location and chemical input
- Autocomplete interactions
- Year and state filter selection
- Search submission
- Dataset selection (TRI/Superfund/Both)
"""

import re
from pytest_bdd import when, then, parsers
from playwright.sync_api import Page, expect

from ._shared import (
    SEARCH_TIMEOUT,
    AUTOCOMPLETE_TIMEOUT,
    PANEL_TIMEOUT,
    ensure_search_panel_open,
)


# ── Input field steps ─────────────────────────────────────────────────────────


@when(parsers.parse('I type "{text}" into the location field'))
def type_location(page: Page, text: str) -> None:
    """Fill the location text input. Opens Search panel if not already active."""
    ensure_search_panel_open(page)
    page.locator('[data-testid="location-input"]').fill(text)


@when(parsers.parse('I type "{text}" into the chemical field'))
def type_chemical(page: Page, text: str) -> None:
    """Type into the chemical input. Opens Search panel if not already active."""
    ensure_search_panel_open(page)
    page.locator('[data-testid="chemical-input"]').fill(text)


@when('I leave the location field empty')
def leave_location_empty(page: Page) -> None:
    """Explicitly leave the location field empty (for nationwide search)."""
    ensure_search_panel_open(page)
    page.locator('[data-testid="location-input"]').fill('')


# ── Autocomplete steps ────────────────────────────────────────────────────────


@when(parsers.parse('I select the chemical "{chemical}" from autocomplete'))
def select_chemical_from_autocomplete(page: Page, chemical: str) -> None:
    """Wait for autocomplete options and click the one matching the chemical name."""
    options = page.locator('[data-testid="chemical-autocomplete-option"]')
    options.first.wait_for(timeout=AUTOCOMPLETE_TIMEOUT)
    # Click the option whose text matches (case-insensitive)
    matching = options.filter(has_text=re.compile(re.escape(chemical), re.IGNORECASE))
    matching.first.click()


# ── Filter steps ──────────────────────────────────────────────────────────────


@when(parsers.parse('I select year "{year}"'))
def select_year(page: Page, year: str) -> None:
    """Select a year from the year dropdown."""
    page.locator('[data-testid="year-select"]').select_option(year)


@when(parsers.parse('I search for "{chemical}" with state filter "{state}"'))
def search_with_state_filter(page: Page, chemical: str, state: str) -> None:
    """Search for a chemical with state filter applied (Option C)."""
    ensure_search_panel_open(page)
    page.locator('[data-testid="chemical-input"]').fill(chemical)
    page.locator('[data-testid="state-select"]').select_option(state)
    page.locator('[data-testid="search-submit-btn"]').click()
    page.wait_for_selector('[data-testid="results-table"]', timeout=SEARCH_TIMEOUT)


@when('I clear the state filter')
def clear_state_filter(page: Page) -> None:
    """Clear the state filter by selecting 'All' (no filter)."""
    page.locator('[data-testid="state-select"]').select_option('')


# ── Dataset selection ─────────────────────────────────────────────────────────


@when(parsers.parse('I select the "{dataset}" dataset'))
def select_dataset(page: Page, dataset: str) -> None:
    """Select the TRI, Superfund, or Both dataset radio button in SearchPanel."""
    ensure_search_panel_open(page)
    ds = dataset.lower()
    if ds == 'tri':
        testid = 'dataset-radio-tri'
    elif ds == 'superfund':
        testid = 'dataset-radio-superfund'
    else:  # 'both'
        testid = 'dataset-radio-both'
    page.locator(f'[data-testid="{testid}"]').click()


# ── Search submission ─────────────────────────────────────────────────────────


@when('I click "Search"')
@when('I click Search')
def click_search(page: Page) -> None:
    """Submit the search form and wait for the results table to appear."""
    page.locator('[data-testid="search-submit-btn"]').click()
    page.wait_for_selector('[data-testid="results-table"]', timeout=SEARCH_TIMEOUT)


@when('I click the search panel tab')
def click_search_panel_tab(page: Page) -> None:
    """Click the Search tab in the sidebar header."""
    ensure_search_panel_open(page)


@when(parsers.parse('I perform a search for "{chemical}" near "{location}"'))
def perform_search(page: Page, chemical: str, location: str) -> None:
    """Fills in chemical + location and submits search. Opens search panel if needed."""
    ensure_search_panel_open(page)
    page.locator('[data-testid="chemical-input"]').fill(chemical)
    page.locator('[data-testid="location-input"]').fill(location)
    page.locator('[data-testid="search-submit-btn"]').click()
    page.wait_for_selector('[data-testid="results-table"]', timeout=SEARCH_TIMEOUT)


# ── State filter assertions ───────────────────────────────────────────────────


@then('the state filter dropdown is present with label "Filter to state (optional)"')
def state_filter_dropdown_present(page: Page) -> None:
    """UX Invariant 3 (Option C): State dropdown is present with filter label."""
    expect(page.locator('[data-testid="state-select"]')).to_be_visible()
    label = page.locator('label[for="state-select"]')
    expect(label).to_contain_text('Filter to state')


# ── Label assertions (UX Invariant 4) ─────────────────────────────────────────


@then('no element with text "Quick Search" exists in the DOM')
def no_quick_search_label(page: Page) -> None:
    """UX Invariant 4: 'Quick Search' must never appear as a label."""
    count = page.get_by_text('Quick Search', exact=True).count()
    assert count == 0, f'Found {count} element(s) with text "Quick Search" — must be zero'


@then('the search panel label is "Search Chemical Releases by Location"')
def search_panel_label_correct(page: Page) -> None:
    """UX Invariant 4: search panel must use the correct label."""
    search_btn = page.get_by_role('button', name='Search')
    if search_btn.is_visible():
        search_btn.click()
    expect(
        page.get_by_text('Search Chemical Releases by Location', exact=True)
    ).to_be_visible()


# ── Extended search steps ─────────────────────────────────────────────────────


@when(parsers.parse('I search for TRI facilities releasing "{chemical}" near "{location}" in year "{year}"'))
def search_tri_facilities_near_location_year(page: Page, chemical: str, location: str, year: str) -> None:
    """Search for TRI facilities with chemical, location, and year filter."""
    ensure_search_panel_open(page)
    page.locator('[data-testid="dataset-radio-tri"]').click()
    page.locator('[data-testid="chemical-input"]').fill(chemical)
    page.locator('[data-testid="location-input"]').fill(location)
    page.locator('[data-testid="year-select"]').select_option(year)
    page.locator('[data-testid="search-submit-btn"]').click()
    page.wait_for_selector('[data-testid="results-table"]', timeout=SEARCH_TIMEOUT)


@when(parsers.parse('I search for "{chemical}" near "{location}" in year "{year}"'))
def search_chemical_near_location_year(page: Page, chemical: str, location: str, year: str) -> None:
    """Search with chemical, location, and year filter."""
    ensure_search_panel_open(page)
    page.locator('[data-testid="chemical-input"]').fill(chemical)
    page.locator('[data-testid="location-input"]').fill(location)
    page.locator('[data-testid="year-select"]').select_option(year)
    page.locator('[data-testid="search-submit-btn"]').click()
    page.wait_for_selector('[data-testid="results-table"]', timeout=SEARCH_TIMEOUT)
