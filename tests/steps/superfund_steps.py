# tests/steps/superfund_steps.py
"""
Superfund site step implementations for E2E tests.

Covers:
- Superfund site selection from results
- Superfund detail panel assertions
- EPA progress profile link
- Superfund layer visibility
- Superfund drawer resize
"""

import re
from pytest_bdd import when, then, parsers
from playwright.sync_api import Page, expect

from ._shared import (
    DETAIL_TIMEOUT,
    LAYER_TIMEOUT,
    DOWNLOAD_TIMEOUT,
    get_bounding_box_safe,
)


# ── Superfund result selection ────────────────────────────────────────────────


@when(parsers.parse('I click on "{site_name}" in the Superfund results'))
def click_superfund_result(page: Page, site_name: str) -> None:
    """Click on a Superfund result row and wait for the detail panel."""
    page.locator('[data-testid="results-row"]').filter(has_text=site_name).click()
    page.wait_for_selector('[data-testid="superfund-detail-panel"]', timeout=DETAIL_TIMEOUT)


# ── Detail panel assertions ───────────────────────────────────────────────────


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


@then('the TRI facility detail panel is not shown')
def tri_facility_detail_not_shown(page: Page) -> None:
    """Invariant 6: clicking a Superfund result opens the Superfund panel, not the TRI panel."""
    tri_panel = page.locator('[data-testid="facility-detail-panel"]')
    if tri_panel.count() > 0:
        expect(tri_panel).not_to_be_visible()


# ── Superfund layer toggle ────────────────────────────────────────────────────


@then('the Superfund layer toggle is present')
def superfund_layer_toggle_present(page: Page) -> None:
    """Invariant 6: the Superfund layer toggle checkbox exists in MapContentsPanel."""
    expect(page.locator('[data-testid="layer-toggle-superfund"]')).to_be_visible()


# ── Superfund layer visibility ────────────────────────────────────────────────


@then('the Superfund layer is visible on the map')
def superfund_layer_visible_on_map(page: Page) -> None:
    """
    Regression test: Superfund MapLibre layer exists and has data.

    This catches the bug where useSuperfundViewport's hasFetchedRef was set
    before the fetch completed, causing React StrictMode to skip the retry.
    """
    page.wait_for_function(
        "() => { const m = window.__DEBUG_MAP__; return m && !!m.getSource('superfund-source'); }",
        timeout=LAYER_TIMEOUT,
    )

    layer_info = page.evaluate('''() => {
        const map = window.__DEBUG_MAP__;
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
    }''')

    assert layer_info.get('hasSource'), (
        'Superfund GeoJSON source not found — useSuperfundViewport likely failed to fetch data.'
    )
    assert layer_info.get('hasLayer'), (
        'Superfund symbol layer not found — MapContainer did not create the layer.'
    )
    assert layer_info.get('hasNplFinal'), 'superfund-npl-final sprite not registered'
    assert layer_info.get('hasProposed'), 'superfund-proposed sprite not registered'
    visibility = layer_info.get('layerVisibility')
    assert visibility in (None, 'visible'), f'Superfund layer visibility is {visibility}, expected visible'


# ── Superfund in-view count ───────────────────────────────────────────────────


@then('the Superfund in-view count is greater than zero')
def superfund_in_view_count_positive(page: Page) -> None:
    """
    Regression test: Superfund sidebar count shows sites in view.

    If useSuperfundViewport fails to fetch data (StrictMode bug), the sidebar
    will show no count or "0 in view".
    """
    page.wait_for_function(
        """() => {
            const t = document.querySelector('[data-testid="layer-toggle-superfund"]');
            if (!t) return false;
            const label = t.closest('label');
            return label && /\\d+\\s*in\\s*view/i.test(label.innerText);
        }""",
        timeout=LAYER_TIMEOUT,
    )

    superfund_toggle = page.locator('[data-testid="layer-toggle-superfund"]')
    toggle_container = superfund_toggle.locator('xpath=..')
    container_text = toggle_container.inner_text()

    match = re.search(r'(\d+)\s*in\s*view', container_text, re.IGNORECASE)
    assert match, (
        f'Could not find "X in view" count in Superfund toggle. Text: "{container_text}".'
    )

    count = int(match.group(1))
    assert count > 0, (
        f'Superfund in-view count is {count}, expected > 0.'
    )


@then(parsers.parse('the Superfund in-view count is greater than or equal to {min_count:d}'))
def superfund_in_view_count_at_least(page: Page, min_count: int) -> None:
    """
    UCD-17 regression test: verify seed data contains all 3 Superfund status types.
    """
    page.wait_for_function(
        """() => {
            const t = document.querySelector('[data-testid="layer-toggle-superfund"]');
            if (!t) return false;
            const label = t.closest('label');
            return label && /\\d+\\s*in\\s*view/i.test(label.innerText);
        }""",
        timeout=LAYER_TIMEOUT,
    )

    superfund_toggle = page.locator('[data-testid="layer-toggle-superfund"]')
    expect(superfund_toggle).to_be_visible()

    toggle_container = superfund_toggle.locator('xpath=..')
    expect(toggle_container).to_contain_text('in view', timeout=DOWNLOAD_TIMEOUT)
    container_text = toggle_container.inner_text()

    match = re.search(r'(\d+)\s*in\s*view', container_text, re.IGNORECASE)
    assert match, f'Could not find "X in view" count. Text: "{container_text}".'

    count = int(match.group(1))
    assert count >= min_count, (
        f'Superfund in-view count is {count}, expected >= {min_count}.'
    )


# ── Superfund drawer resize ───────────────────────────────────────────────────


@then('the superfund drawer resize handle is present')
def superfund_drawer_resize_handle_present(page: Page) -> None:
    """Regression test for 7.BUG.31: SuperfundDrawer should have a resize handle."""
    handle = page.locator('[data-testid="superfund-drawer-resize-handle"]')
    expect(handle).to_be_visible()


@when(parsers.parse('I drag the superfund drawer resize handle {pixels:d} pixels to the left'))
def drag_superfund_drawer_resize(page: Page, pixels: int, step_context) -> None:
    """Regression test for 7.BUG.31: Simulate dragging the resize handle."""
    handle = page.locator('[data-testid="superfund-drawer-resize-handle"]')
    expect(handle).to_be_visible()
    
    drawer = page.locator('[data-testid="superfund-detail-panel"]')
    box = get_bounding_box_safe(drawer, 'Superfund drawer not visible')
    step_context['initial_superfund_drawer_width'] = box['width']
    
    handle.drag_to(handle, target_position={'x': -pixels, 'y': 0})


@then('the superfund drawer width has increased')
def superfund_drawer_width_increased(page: Page, step_context) -> None:
    """Regression test for 7.BUG.31: Verify drawer width increased after drag."""
    drawer = page.locator('[data-testid="superfund-detail-panel"]')
    box = get_bounding_box_safe(drawer, 'Superfund drawer not visible after drag')
    current_width = box['width']
    initial_width = step_context.get('initial_superfund_drawer_width', 0)
    
    assert current_width > initial_width, (
        f'REGRESSION 7.BUG.31: Superfund drawer width did not increase. '
        f'Initial: {initial_width}px, Current: {current_width}px'
    )
