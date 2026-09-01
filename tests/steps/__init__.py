# tests/steps/__init__.py
"""
E2E step implementations for pytest-bdd.

This package provides all step definitions for Gherkin scenarios.
Step modules are organized by domain:

- navigation_steps: Given steps, page load, navigation
- search_steps: Search form, filters, autocomplete
- results_steps: Results table interactions
- facility_steps: TRI facility detail drawer
- superfund_steps: Superfund site detail drawer
- demographics_steps: Demographics/choropleth layer
- map_layer_steps: MapLibre layer verification
- export_steps: CSV download, screenshots
- regression_steps: Bug regression tests (7.BUG.*, UCD-17, T-07, etc.)

Test files should use:
    from tests.steps import *
"""

# Re-export all constants from shared module
from ._shared import (
    # Configuration
    BASE_URL,
    # Timeout constants
    MAP_TIMEOUT,
    SEARCH_TIMEOUT,
    AUTOCOMPLETE_TIMEOUT,
    PANEL_TIMEOUT,
    DETAIL_TIMEOUT,
    LAYER_TIMEOUT,
    DOWNLOAD_TIMEOUT,
    HEAVY_LOAD_TIMEOUT,
    ANIMATION_DELAY,
    MAP_SETTLE_DELAY,
    BANNER_TIMEOUT,
    # Helper functions
    ensure_search_panel_open,
    dismiss_banner_if_present,
    get_bounding_box_safe,
    inject_map_helpers,
)

# Import all step modules to register steps with pytest-bdd
from . import navigation_steps
from . import search_steps
from . import results_steps
from . import facility_steps
from . import superfund_steps
from . import demographics_steps
from . import map_layer_steps
from . import export_steps
from . import regression_steps
from . import stubs_steps

# Public API for `from tests.steps import *`
__all__ = [
    # Constants (useful for external test modules)
    'BASE_URL',
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
    # Step modules (for explicit imports)
    'navigation_steps',
    'search_steps',
    'results_steps',
    'facility_steps',
    'superfund_steps',
    'demographics_steps',
    'map_layer_steps',
    'export_steps',
    'regression_steps',
    'stubs_steps',
]
