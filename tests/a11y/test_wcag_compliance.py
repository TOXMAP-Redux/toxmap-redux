# tests/a11y/test_wcag_compliance.py
#
# WCAG 2.1 AA accessibility tests for TOXMAP.
# Uses axe-core via Playwright page.evaluate() injection.
#
# CC-01: Accessibility map page — 0 critical/serious violations
#
# Run: pytest tests/a11y/ -v --browser chromium
#

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="module")
def axe_script() -> str:
    """
    Load axe-core from CDN for injection into page.
    
    In CI, this is fetched once per module. For offline/air-gapped environments,
    consider vendoring axe.min.js into tests/a11y/vendor/.
    """
    return """
    (async () => {
        if (!window.axe) {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js';
            script.integrity = 'sha512-gYEv0lSO9FX0t0K21DK12FEXQGjb9C5M/c5K0Vs4h3B17jqjLuB5eL7C4FG0xmPYVf0PoWLMtmYPX/3oMJmg2w==';
            script.crossOrigin = 'anonymous';
            await new Promise((resolve, reject) => {
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            });
        }
        return true;
    })();
    """


def run_axe(page: Page, axe_script: str, context: str = None) -> dict:
    """
    Run axe-core accessibility scan on the page.
    
    Args:
        page: Playwright Page instance
        axe_script: Script to inject axe-core
        context: CSS selector to scope the scan (optional)
        
    Returns:
        axe-core results object with violations, passes, incomplete, inapplicable
    """
    # Inject axe-core
    page.evaluate(axe_script)
    
    # Wait for axe to be available
    page.wait_for_function("() => window.axe !== undefined", timeout=10_000)
    
    # Run axe scan
    if context:
        results = page.evaluate(f"""
            async () => {{
                return await axe.run('{context}', {{
                    runOnly: ['wcag2a', 'wcag2aa', 'wcag21aa'],
                }});
            }}
        """)
    else:
        results = page.evaluate("""
            async () => {
                return await axe.run({
                    runOnly: ['wcag2a', 'wcag2aa', 'wcag21aa'],
                });
            }
        """)
    
    return results


class TestMapPageAccessibility:
    """CC-01: Accessibility tests for the main map page."""
    
    def test_map_page_no_critical_violations(
        self, page: Page, seed_db, axe_script: str
    ) -> None:
        """
        WCAG 2.1 AA: No critical or serious axe-core violations on map page.
        
        Excludes the MapLibre <canvas> element which cannot be made accessible
        (WebGL canvas is inherently inaccessible; map data is available via
        results table and facility detail panels which ARE accessible).
        """
        page.goto("http://localhost:3000")
        page.wait_for_selector('[data-testid="map-container"]', timeout=20_000)
        
        # Run axe excluding the canvas element
        results = page.evaluate("""
            async () => {
                // Wait for axe to be available
                if (!window.axe) {
                    const script = document.createElement('script');
                    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js';
                    await new Promise((resolve, reject) => {
                        script.onload = resolve;
                        script.onerror = reject;
                        document.head.appendChild(script);
                    });
                }
                
                return await axe.run({
                    runOnly: ['wcag2a', 'wcag2aa', 'wcag21aa'],
                    rules: {
                        // Exclude canvas-specific rules (MapLibre GL canvas)
                        'canvas-has-accessible-name': { enabled: false },
                    },
                    exclude: [
                        // MapLibre GL canvas is inherently inaccessible
                        ['canvas.maplibregl-canvas'],
                    ],
                });
            }
        """)
        
        # Filter for critical and serious violations only
        violations = results.get('violations', [])
        critical_serious = [
            v for v in violations
            if v.get('impact') in ('critical', 'serious')
        ]
        
        if critical_serious:
            # Format violations for error message
            messages = []
            for v in critical_serious:
                nodes = v.get('nodes', [])
                for node in nodes:
                    messages.append(
                        f"[{v['impact']}] {v['id']}: {v['description']}\n"
                        f"  Element: {node.get('html', 'N/A')}\n"
                        f"  Fix: {v['help']}"
                    )
            
            pytest.fail(
                f"Found {len(critical_serious)} critical/serious a11y violations:\n\n"
                + "\n\n".join(messages)
            )
    
    def test_sidebar_is_keyboard_navigable(
        self, page: Page, seed_db
    ) -> None:
        """Sidebar tabs must be navigable via keyboard."""
        page.goto("http://localhost:3000")
        page.wait_for_selector('[data-testid="map-container"]', timeout=20_000)
        
        # Press Tab to move focus into sidebar
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")
        
        # Check that a sidebar element received focus
        focused = page.evaluate("() => document.activeElement.dataset.testid")
        # Should be on a button or focusable element in the sidebar area
        assert focused is not None, "Keyboard navigation did not reach any data-testid element"
    
    def test_results_table_has_proper_table_semantics(
        self, page: Page, seed_db
    ) -> None:
        """Results table must use proper <table> semantics for screen readers."""
        page.goto("http://localhost:3000")
        page.wait_for_selector('[data-testid="map-container"]', timeout=20_000)
        
        # Open search panel and perform a search
        page.get_by_role('button', name='Search').click()
        page.locator('[data-testid="chemical-input"]').fill("BENZENE")
        page.locator('[data-testid="location-input"]').fill("Houston, TX")
        page.locator('[data-testid="search-submit-btn"]').click()
        page.wait_for_selector('[data-testid="results-table"]', timeout=15_000)
        
        # Check table has proper structure
        results_table = page.locator('[data-testid="results-table"]')
        expect(results_table).to_be_visible()
        
        # Should have <table> or role="table"
        tag_name = results_table.evaluate("el => el.tagName")
        role = results_table.get_attribute("role")
        
        assert tag_name == "TABLE" or role == "table", (
            f"Results table must use <table> or role='table', got {tag_name} with role={role}"
        )


class TestSearchPanelAccessibility:
    """Accessibility tests for the search panel."""
    
    def test_search_inputs_have_labels(
        self, page: Page, seed_db
    ) -> None:
        """All form inputs must have associated labels."""
        page.goto("http://localhost:3000")
        page.wait_for_selector('[data-testid="map-container"]', timeout=20_000)
        
        # Open search panel
        page.get_by_role('button', name='Search').click()
        page.wait_for_selector('[data-testid="search-panel"]', timeout=5_000)
        
        # Check each input has a label
        inputs = [
            'location-input',
            'chemical-input',
            'year-select',
            'state-select',
        ]
        
        for input_id in inputs:
            input_el = page.locator(f'[data-testid="{input_id}"]')
            if input_el.count() == 0:
                continue
            
            # Check for aria-label, aria-labelledby, or associated <label>
            aria_label = input_el.get_attribute("aria-label")
            aria_labelledby = input_el.get_attribute("aria-labelledby")
            input_html_id = input_el.get_attribute("id")
            
            has_label = (
                aria_label or
                aria_labelledby or
                (input_html_id and page.locator(f'label[for="{input_html_id}"]').count() > 0)
            )
            
            assert has_label, f"Input {input_id} is missing an accessible label"


class TestFacilityDetailAccessibility:
    """Accessibility tests for facility detail panel."""
    
    def test_detail_panel_has_heading(
        self, page: Page, seed_db
    ) -> None:
        """Facility detail panel must have a heading for screen reader navigation."""
        page.goto("http://localhost:3000")
        page.wait_for_selector('[data-testid="map-container"]', timeout=20_000)
        
        # Perform a search and click a result
        page.get_by_role('button', name='Search').click()
        page.locator('[data-testid="chemical-input"]').fill("LEAD COMPOUNDS")
        page.locator('[data-testid="location-input"]').fill("Sparrows Point, MD")
        page.locator('[data-testid="search-submit-btn"]').click()
        page.wait_for_selector('[data-testid="results-table"]', timeout=15_000)
        
        # Click first result
        page.locator('[data-testid="results-row"]').first.click()
        page.wait_for_selector('[data-testid="facility-detail-panel"]', timeout=8_000)
        
        # Check for heading
        detail_panel = page.locator('[data-testid="facility-detail-panel"]')
        headings = detail_panel.locator('h1, h2, h3, [role="heading"]')
        
        assert headings.count() > 0, (
            "Facility detail panel must have at least one heading element"
        )
    
    def test_external_links_have_rel_noopener(
        self, page: Page, seed_db
    ) -> None:
        """External links (ATSDR, EPA) must have rel='noopener' for security."""
        page.goto("http://localhost:3000")
        page.wait_for_selector('[data-testid="map-container"]', timeout=20_000)
        
        # Find ATSDR link after search
        page.get_by_role('button', name='Search').click()
        page.locator('[data-testid="chemical-input"]').fill("AMMONIA")
        page.wait_for_selector('[data-testid="atsdr-link"]', timeout=5_000)
        
        atsdr_link = page.locator('[data-testid="atsdr-link"]').first
        rel = atsdr_link.get_attribute("rel")
        
        assert rel and "noopener" in rel, (
            f"ATSDR link must have rel='noopener', got rel='{rel}'"
        )
