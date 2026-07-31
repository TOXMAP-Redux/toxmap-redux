# tests/visual/test_visual_regression.py
#
# Visual regression tests for TOXMAP.
# Uses Playwright screenshots + Pillow/numpy for pixel diff comparison.
#
# CC-02: Visual regression: map initial load
# CC-03: Visual regression: facility detail panel (T-01)
# CC-04: Visual regression: choropleth overlay (T-05)
#
# Baselines are stored in tests/visual/snapshots/
# Run: pytest tests/visual/ -v --browser chromium
#
# To update baselines: pytest tests/visual/ --update-snapshots
#

import os
import pytest
from pathlib import Path
from playwright.sync_api import Page

# Snapshot directory
SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
DIFF_DIR = Path(__file__).parent / "diffs"

# Pixel diff threshold (percentage of pixels that can differ)
DIFF_THRESHOLD = 0.02  # 2%


def _ensure_dirs():
    """Ensure snapshot and diff directories exist."""
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    DIFF_DIR.mkdir(exist_ok=True)


def _calculate_diff(img1_path: Path, img2_path: Path, diff_path: Path) -> float:
    """
    Calculate pixel difference between two images.
    
    Returns:
        Percentage of pixels that differ (0.0 to 1.0)
    """
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        pytest.skip("Pillow and numpy required for visual regression tests")
    
    img1 = np.array(Image.open(img1_path).convert('RGB'))
    img2 = np.array(Image.open(img2_path).convert('RGB'))
    
    # Handle size mismatch by padding the smaller image
    if img1.shape != img2.shape:
        max_height = max(img1.shape[0], img2.shape[0])
        max_width = max(img1.shape[1], img2.shape[1])
        
        padded1 = np.zeros((max_height, max_width, 3), dtype=np.uint8)
        padded2 = np.zeros((max_height, max_width, 3), dtype=np.uint8)
        
        padded1[:img1.shape[0], :img1.shape[1]] = img1
        padded2[:img2.shape[0], :img2.shape[1]] = img2
        
        img1, img2 = padded1, padded2
    
    # Calculate diff
    diff = np.abs(img1.astype(int) - img2.astype(int))
    diff_mask = np.any(diff > 10, axis=2)  # Pixel differs if any channel > 10
    
    # Save diff image (highlight differences in red)
    diff_img = img2.copy()
    diff_img[diff_mask] = [255, 0, 0]  # Red for differences
    Image.fromarray(diff_img).save(diff_path)
    
    # Return percentage of differing pixels
    total_pixels = diff_mask.size
    diff_pixels = np.sum(diff_mask)
    
    return diff_pixels / total_pixels


class TestVisualRegressionMapLoad:
    """CC-02: Visual regression tests for initial map load."""
    
    def test_map_initial_load(self, page: Page, seed_db, request) -> None:
        """
        CC-02: Map initial load visual baseline.
        
        Captures the map after initial page load with all layers visible.
        """
        _ensure_dirs()
        snapshot_name = "map_initial_load.png"
        snapshot_path = SNAPSHOT_DIR / snapshot_name
        actual_path = DIFF_DIR / f"actual_{snapshot_name}"
        diff_path = DIFF_DIR / f"diff_{snapshot_name}"
        
        # Navigate and wait for map to be fully loaded
        page.goto("http://localhost:3000")
        page.wait_for_selector('[data-testid="map-container"]', timeout=20_000)
        
        # Wait for map style to load and all layers to render
        page.wait_for_function(
            """() => {
                const map = window.__DEBUG_MAP__;
                return map && map.isStyleLoaded() && !map.isMoving();
            }""",
            timeout=15_000,
        )
        
        # Additional wait for tile rendering
        page.wait_for_timeout(2000)
        
        # Take screenshot of map container only
        map_container = page.locator('[data-testid="map-container"]')
        map_container.screenshot(path=str(actual_path))
        
        # Check if we should update baseline
        if request.config.getoption("--update-snapshots", default=False):
            actual_path.rename(snapshot_path)
            pytest.skip("Baseline updated")
            return
        
        # Compare against baseline
        if not snapshot_path.exists():
            actual_path.rename(snapshot_path)
            pytest.skip("Baseline created (first run)")
            return
        
        diff_pct = _calculate_diff(snapshot_path, actual_path, diff_path)
        
        assert diff_pct <= DIFF_THRESHOLD, (
            f"Visual regression failed: {diff_pct*100:.2f}% pixels differ "
            f"(threshold: {DIFF_THRESHOLD*100:.1f}%)\n"
            f"Baseline: {snapshot_path}\n"
            f"Actual: {actual_path}\n"
            f"Diff: {diff_path}"
        )


class TestVisualRegressionFacilityDetail:
    """CC-03: Visual regression tests for facility detail panel."""
    
    def test_facility_detail_panel_t01(self, page: Page, seed_db, request) -> None:
        """
        CC-03: Facility detail panel visual baseline (T-01 Bethlehem Steel).
        """
        _ensure_dirs()
        snapshot_name = "facility_detail_t01.png"
        snapshot_path = SNAPSHOT_DIR / snapshot_name
        actual_path = DIFF_DIR / f"actual_{snapshot_name}"
        diff_path = DIFF_DIR / f"diff_{snapshot_name}"
        
        # Navigate and search for T-01 facility
        page.goto("http://localhost:3000")
        page.wait_for_selector('[data-testid="map-container"]', timeout=20_000)
        
        # Perform T-01 search
        page.get_by_role('button', name='Search').click()
        page.locator('[data-testid="chemical-input"]').fill("LEAD COMPOUNDS")
        page.locator('[data-testid="location-input"]').fill("Sparrows Point, MD")
        page.locator('[data-testid="year-select"]').select_option("2008")
        page.locator('[data-testid="search-submit-btn"]').click()
        
        # Wait for results and click first result
        page.wait_for_selector('[data-testid="results-table"]', timeout=15_000)
        page.locator('[data-testid="results-row"]').first.click()
        page.wait_for_selector('[data-testid="facility-detail-panel"]', timeout=8_000)
        
        # Wait for panel content to fully render
        page.wait_for_timeout(1000)
        
        # Screenshot the detail panel
        detail_panel = page.locator('[data-testid="facility-detail-panel"]')
        detail_panel.screenshot(path=str(actual_path))
        
        # Update or compare baseline
        if request.config.getoption("--update-snapshots", default=False):
            actual_path.rename(snapshot_path)
            pytest.skip("Baseline updated")
            return
        
        if not snapshot_path.exists():
            actual_path.rename(snapshot_path)
            pytest.skip("Baseline created (first run)")
            return
        
        diff_pct = _calculate_diff(snapshot_path, actual_path, diff_path)
        
        assert diff_pct <= DIFF_THRESHOLD, (
            f"Visual regression failed: {diff_pct*100:.2f}% pixels differ\n"
            f"Baseline: {snapshot_path}\n"
            f"Actual: {actual_path}\n"
            f"Diff: {diff_path}"
        )


class TestVisualRegressionChoropleth:
    """CC-04: Visual regression tests for demographic choropleth overlay."""
    
    @pytest.mark.skip(reason="Demographics UI not yet implemented in Phase 6")
    def test_choropleth_overlay_t05(self, page: Page, seed_db, request) -> None:
        """
        CC-04: Choropleth overlay visual baseline (T-05 demographics).
        
        Note: This test requires the Demographics panel UI to be implemented.
        It is marked skip until Phase 5+ demographics features are complete.
        """
        _ensure_dirs()
        snapshot_name = "choropleth_t05.png"
        snapshot_path = SNAPSHOT_DIR / snapshot_name
        actual_path = DIFF_DIR / f"actual_{snapshot_name}"
        diff_path = DIFF_DIR / f"diff_{snapshot_name}"
        
        # Navigate
        page.goto("http://localhost:3000")
        page.wait_for_selector('[data-testid="map-container"]', timeout=20_000)
        
        # Open demographics panel and select Population > % Under 18
        # (Implementation depends on Demographics UI)
        page.get_by_role('button', name='Map Contents').click()
        page.locator('[data-testid="census-health-panel"]').click()
        page.locator('[data-testid="demo-tab-population"]').click()
        page.locator('[data-testid="demo-sublayer-pct-under-18"]').click()
        
        # Wait for choropleth to render
        page.wait_for_function(
            """() => {
                const map = window.__DEBUG_MAP__;
                return map && map.getSource('demographics-source') && !map.isMoving();
            }""",
            timeout=15_000,
        )
        page.wait_for_timeout(2000)
        
        # Screenshot map with choropleth
        map_container = page.locator('[data-testid="map-container"]')
        map_container.screenshot(path=str(actual_path))
        
        # Update or compare baseline
        if request.config.getoption("--update-snapshots", default=False):
            actual_path.rename(snapshot_path)
            pytest.skip("Baseline updated")
            return
        
        if not snapshot_path.exists():
            actual_path.rename(snapshot_path)
            pytest.skip("Baseline created (first run)")
            return
        
        diff_pct = _calculate_diff(snapshot_path, actual_path, diff_path)
        
        assert diff_pct <= DIFF_THRESHOLD, (
            f"Visual regression failed: {diff_pct*100:.2f}% pixels differ\n"
            f"Baseline: {snapshot_path}\n"
            f"Actual: {actual_path}\n"
            f"Diff: {diff_path}"
        )


def pytest_addoption(parser):
    """Add --update-snapshots option for baseline updates."""
    try:
        parser.addoption(
            "--update-snapshots",
            action="store_true",
            default=False,
            help="Update visual regression baselines",
        )
    except ValueError:
        # Option already added by conftest.py
        pass
