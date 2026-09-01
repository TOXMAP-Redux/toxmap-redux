# tests/steps/_shared.py
"""
Shared constants, utilities, and helpers for E2E step implementations.

This module provides:
- Timeout constants for consistent wait durations
- Helper functions used across multiple step modules
- Base URL configuration

All step modules import from here to avoid duplication.
"""

import os
from playwright.sync_api import Page

# ── Public API ────────────────────────────────────────────────────────────────

__all__ = [
    # Configuration
    'BASE_URL',
    # Timeout constants
    'MAP_TIMEOUT',
    'SEARCH_TIMEOUT',
    'AUTOCOMPLETE_TIMEOUT',
    'PANEL_TIMEOUT',
    'DETAIL_TIMEOUT',
    'LAYER_TIMEOUT',
    'DOWNLOAD_TIMEOUT',
    'HEAVY_LOAD_TIMEOUT',
    'ANIMATION_DELAY',
    'MAP_SETTLE_DELAY',
    'BANNER_TIMEOUT',
    # Helper functions
    'ensure_search_panel_open',
    'dismiss_banner_if_present',
    'get_bounding_box_safe',
    'inject_map_helpers',
]

# ── Configuration ─────────────────────────────────────────────────────────────

# Allow override via TEST_BASE_URL for Docker container networking
BASE_URL = os.getenv('TEST_BASE_URL', 'http://localhost:3000')

# ── Timeouts (ms) ─────────────────────────────────────────────────────────────

MAP_TIMEOUT = 20_000         # Map tile load can take a few seconds
SEARCH_TIMEOUT = 15_000      # Geocoding + API call
AUTOCOMPLETE_TIMEOUT = 3_000 # Debounced autocomplete
PANEL_TIMEOUT = 5_000        # Sidebar panel transitions
DETAIL_TIMEOUT = 8_000       # Detail drawer opening
LAYER_TIMEOUT = 15_000       # MapLibre layer creation
DOWNLOAD_TIMEOUT = 10_000    # File download
HEAVY_LOAD_TIMEOUT = 30_000  # Heavy operations (large result sets)
ANIMATION_DELAY = 500        # Small UI animation waits
MAP_SETTLE_DELAY = 2_000     # Map re-render / settle delay
BANNER_TIMEOUT = 3_000       # Banner dismiss + animation wait

# ── Path to JS helpers ────────────────────────────────────────────────────────

_MAP_HELPERS_PATH = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'map_helpers.js')


# ── Helper Functions ──────────────────────────────────────────────────────────


def ensure_search_panel_open(page: Page) -> None:
    """Open the search panel if not already visible.
    
    This helper is used by multiple steps that interact with the search form.
    It handles both the sidebar tab button and the fallback role-based button.
    """
    if page.locator('[data-testid="search-panel"]').is_visible():
        return
    search_tab = page.locator('button.toxmap-sidebar-tab:has-text("Search")')
    if search_tab.count() > 0:
        search_tab.click()
    else:
        page.get_by_role('button', name='Search').first.click()
    page.wait_for_selector('[data-testid="search-panel"]', timeout=PANEL_TIMEOUT)


def dismiss_banner_if_present(page: Page) -> None:
    """Dismiss the interpretation banner if visible (blocks UI interactions)."""
    banner_dismiss = page.get_by_label('Dismiss disclaimer')
    if banner_dismiss.is_visible():
        banner_dismiss.click()
        page.wait_for_selector('[data-testid="interpretation-banner"]', state='hidden', timeout=BANNER_TIMEOUT)


def get_bounding_box_safe(locator, error_msg: str = 'Element not visible') -> dict:
    """Get bounding box with type-safe None check.
    
    Args:
        locator: Playwright locator
        error_msg: Error message if bounding_box returns None
        
    Returns:
        Bounding box dict with x, y, width, height
        
    Raises:
        AssertionError if element is not visible
    """
    box = locator.bounding_box()
    assert box is not None, error_msg
    return box


def inject_map_helpers(page: Page) -> None:
    """Inject map_helpers.js into the page for MapLibre testing utilities.
    
    After calling this, you can use page.evaluate('mapHelpers.hasSource("facilities")').
    Only needs to be called once per page load.
    """
    if os.path.exists(_MAP_HELPERS_PATH):
        with open(_MAP_HELPERS_PATH, 'r') as f:
            page.evaluate(f.read())
