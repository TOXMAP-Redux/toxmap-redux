# tests/steps/facility_steps.py
"""
TRI Facility detail drawer step implementations for E2E tests.

Covers:
- Clicking on facility results
- Facility detail panel assertions
- Release amount formatting
- ATSDR link verification
- Close button (UX Invariant 9)
"""

import re
from pytest_bdd import when, then, parsers
from playwright.sync_api import Page, expect

from ._shared import (
    DETAIL_TIMEOUT,
    ANIMATION_DELAY,
    get_bounding_box_safe,
)


# ── Facility selection ────────────────────────────────────────────────────────


@when(parsers.parse('I click on "{facility_name}" in the results'))
def click_on_result(page: Page, facility_name: str) -> None:
    """Click on a specific facility row in the results table."""
    page.locator('[data-testid="results-row"]').filter(has_text=facility_name).click()
    page.wait_for_selector('[data-testid="facility-detail-panel"]', timeout=DETAIL_TIMEOUT)


@when('I click on the first result in the results table')
def click_first_result(page: Page) -> None:
    """Click the first result row — used for generic popup tests."""
    page.locator('[data-testid="results-row"]').first.click()
    page.wait_for_selector('[data-testid="facility-detail-panel"]', timeout=DETAIL_TIMEOUT)


@when('I click on the first TRI result row')
def click_first_tri_result(page: Page) -> None:
    """Click the first TRI result row to select it."""
    first_row = page.locator('[data-testid="results-row"]').first
    first_row.click()
    page.wait_for_selector('[data-testid="facility-detail-panel"]', timeout=DETAIL_TIMEOUT)


@when(parsers.parse('I click on "{facility_name}" in the TRI results'))
def click_tri_result_in_both_mode(page: Page, facility_name: str) -> None:
    """Click on a TRI result row in the combined 'Both' mode results table."""
    tri_section = page.locator('text=TRI Facilities').locator('xpath=following-sibling::table[1]')
    tri_row = tri_section.locator('[data-testid="results-row"]').filter(has_text=facility_name)
    tri_row.click()
    page.wait_for_selector('.toxmap-drawer[data-testid="facility-detail-panel"]', timeout=DETAIL_TIMEOUT)


# ── Detail panel assertions ───────────────────────────────────────────────────


@then('the facility detail panel opens')
def detail_panel_opens(page: Page) -> None:
    """Assert the facility detail panel is visible."""
    expect(page.locator('[data-testid="facility-detail-panel"]')).to_be_visible()


@then('the TRI facility detail drawer opens')
def tri_facility_detail_drawer_opens(page: Page) -> None:
    """Assert the TRI facility detail drawer (not popup) is visible."""
    expect(page.locator('.toxmap-drawer[data-testid="facility-detail-panel"]')).to_be_visible()


@then('the Superfund detail panel is not shown')
def superfund_detail_panel_not_shown(page: Page) -> None:
    """Assert the Superfund detail panel is NOT visible (when TRI drawer should be shown)."""
    superfund_panel = page.locator('[data-testid="superfund-detail-panel"]')
    if superfund_panel.count() > 0:
        expect(superfund_panel).not_to_be_visible()


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


# ── Close link (UX Invariant 9) ───────────────────────────────────────────────


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


# ── Facility drawer tab steps ─────────────────────────────────────────────────


@when(parsers.parse('I click the "{tab_name}" tab'))
def click_drawer_tab_by_name(page: Page, tab_name: str) -> None:
    """Click a tab by its visible label text."""
    tab_map = {
        'Top Chemicals': 'facility-chart-tab-1',
        'By Medium': 'facility-chart-tab-2',
        'Release Trend': 'facility-chart-tab-3',
        '15-Year Trend': 'facility-chart-tab-3',  # Legacy name
    }
    testid = tab_map.get(tab_name, 'facility-chart-tab-3')
    tab = page.locator(f'[data-testid="{testid}"]')
    expect(tab).to_be_visible()
    tab.click()


# ── Drawer resize steps ───────────────────────────────────────────────────────


@then('the facility drawer resize handle is present')
def facility_drawer_resize_handle_present(page: Page) -> None:
    """Regression test for 7.BUG.30: FacilityDrawer should have a resize handle."""
    handle = page.locator('[data-testid="facility-drawer-resize-handle"]')
    expect(handle).to_be_visible()


@when(parsers.parse('I drag the facility drawer resize handle {pixels:d} pixels to the left'))
def drag_facility_drawer_resize(page: Page, pixels: int, step_context) -> None:
    """Regression test for 7.BUG.30: Simulate dragging the resize handle."""
    handle = page.locator('[data-testid="facility-drawer-resize-handle"]')
    expect(handle).to_be_visible()
    
    drawer = page.locator('[data-testid="facility-detail-panel"]')
    box = get_bounding_box_safe(drawer, 'Facility drawer not visible')
    step_context['initial_facility_drawer_width'] = box['width']
    
    handle.drag_to(handle, target_position={'x': -pixels, 'y': 0})


@then('the facility drawer width has increased')
def facility_drawer_width_increased(page: Page, step_context) -> None:
    """Regression test for 7.BUG.30: Verify drawer width increased after drag."""
    drawer = page.locator('[data-testid="facility-detail-panel"]')
    box = get_bounding_box_safe(drawer, 'Facility drawer not visible after drag')
    current_width = box['width']
    initial_width = step_context.get('initial_facility_drawer_width', 0)
    
    assert current_width > initial_width, (
        f'REGRESSION 7.BUG.30: Drawer width did not increase. '
        f'Initial: {initial_width}px, Current: {current_width}px'
    )


# ── EPA TRI Facility Report link ──────────────────────────────────────────────


@then('the EPA TRI Facility Report link is visible')
def epa_tri_facility_report_link_visible(page: Page) -> None:
    """ADR-010: EPA TRI Facility Report link should be visible at bottom of drawer."""
    link = page.locator('[data-testid="facility-epa-report-link"]')
    expect(link).to_be_visible()


@then('the EPA TRI Facility Report link is above the close button')
def epa_tri_report_link_above_close(page: Page) -> None:
    """ADR-010: EPA TRI Facility Report link should appear before close button."""
    report_link = page.locator('[data-testid="facility-epa-report-link"]')
    close_button = page.locator('[data-testid="popup-close-bottom"]')
    expect(report_link).to_be_visible()
    expect(close_button).to_be_visible()
    
    report_box = report_link.bounding_box()
    close_box = close_button.bounding_box()
    assert report_box and close_box, 'ADR-010: Could not get bounding boxes for layout check'
    assert report_box['y'] < close_box['y'], (
        f'ADR-010: EPA TRI Report link (y={report_box["y"]}) should be above close button (y={close_box["y"]})'
    )
