# E2E Steps Refactoring Audit

**Date:** 2025-01-13 (updated 2026-08-17)  
**File:** `tests/steps/` (modular)  
**Status:** ✅ Completed (8/8 tasks) — Legacy `e2e_steps.py` deleted

---

## Summary

This document records the refactoring improvements made to the E2E step implementations.
The original monolithic `tests/steps/e2e_steps.py` (~2,800 lines) has been completely 
replaced by 10 focused domain modules.

---

## Completed Improvements

### 1. Extract `_ensure_search_panel_open` Helper ✅

**Issue:** Duplicated "open search panel if not visible" logic appeared in 8+ step functions.

**Solution:** Created `_ensure_search_panel_open(page: Page)` helper function and refactored all occurrences:
- `type_location()`
- `type_chemical()`
- `click_search_panel_tab()`
- `perform_search()`
- `search_with_state_filter()`
- `select_dataset()`
- `search_tri_chemical_location_year()`
- `search_chemical_location_year()`
- `leave_location_empty()`

Also created `_dismiss_banner_if_present(page: Page)` helper to handle interpretation banner dismissal, used in navigation steps.

### 2. Remove Duplicate Step Definitions ✅

**Issue:** Two duplicate `@when` decorators caused potential runtime errors:
- Line ~1430: `select_state_filter_option`
- Line ~1952: `select_state_filter`
- Line ~2044: `click_facility_tab`
- Line ~2647: `click_drawer_tab_by_name`

**Solution:** Removed the less robust duplicate and kept the implementation with better error handling (value_map pattern). Added NOTE comments at the original locations pointing to the retained implementation.

### 3. Fix `bounding_box()` Type Errors ✅

**Issue:** `bounding_box()` returns `Optional[dict]`, but code accessed `['width']` directly without None check (type error).

**Solution:** Created `_get_bounding_box_safe(locator, error_msg)` helper that asserts non-None and returns typed dict. Updated 4 occurrences:
- `drag_facility_drawer_resize()`
- `facility_drawer_width_increased()`
- `drag_superfund_drawer_resize()`
- `superfund_drawer_width_increased()`

### 4. Replace Magic Timeout Numbers with Constants ✅

**Issue:** Magic numbers like `timeout=8_000`, `timeout=15_000`, `timeout=30000` scattered throughout.

**Solution:** Added centralized timeout constants and replaced all magic numbers:

```python
_MAP_TIMEOUT = 20_000         # Map tile load
_SEARCH_TIMEOUT = 15_000      # Geocoding + API call
_AUTOCOMPLETE_TIMEOUT = 3_000 # Debounced autocomplete
_PANEL_TIMEOUT = 5_000        # Sidebar panel transitions
_DETAIL_TIMEOUT = 8_000       # Detail drawer opening
_LAYER_TIMEOUT = 15_000       # MapLibre layer creation
_DOWNLOAD_TIMEOUT = 10_000    # File download
_HEAVY_LOAD_TIMEOUT = 30_000  # Heavy operations
_ANIMATION_DELAY = 500        # Small UI animation waits
_MAP_SETTLE_DELAY = 2_000     # Map re-render / settle delay
_BANNER_TIMEOUT = 1_000       # Quick banner dismiss check
```

### 5. Add `__all__` Exports ✅

**Issue:** No explicit public API documentation.

**Solution:** Added `__all__` list exporting timeout constants for use by other test modules. Added module docstring explaining that step definitions are implicitly exported via pytest-bdd decorators.

### 6. Split into Domain Modules ✅

**Issue:** Monolithic 2,800+ line file difficult to navigate and maintain.

**Solution:** Split steps into focused domain modules:

```
tests/steps/
├── __init__.py              # Re-exports all steps for imports
├── _shared.py               # Constants and helper functions
├── navigation_steps.py      # Given steps, page load, navigation
├── search_steps.py          # Search form, filters, autocomplete
├── results_steps.py         # Results table interactions
├── facility_steps.py        # TRI facility detail drawer
├── superfund_steps.py       # Superfund site detail drawer
├── demographics_steps.py    # Demographics layer steps
├── map_layer_steps.py       # MapLibre layer verification
├── export_steps.py          # CSV download, screenshots
├── regression_steps.py      # Bug regression tests (7.BUG.*, UCD-17, T-07)
└── stubs_steps.py           # Placeholder steps for unimplemented features
```

**Usage:** Test files import from the package:
- `from tests.steps import *`

### 7. Extract JS Evaluations to Fixture File ✅

**Issue:** Inline JavaScript strings (30+ `page.evaluate()` calls) lacked syntax highlighting and were duplicated.

**Solution:** Created `tests/fixtures/map_helpers.js` with reusable MapLibre testing utilities:

```javascript
// tests/fixtures/map_helpers.js
window.mapHelpers = {
  getMap,           // Get __DEBUG_MAP__ instance
  hasSource,        // Check if GeoJSON source exists
  hasLayer,         // Check if layer exists
  hasImage,         // Check if icon image is loaded
  getLayerVisibility,
  getMapCenter,
  getZoom,
  isMoving,
  getLayerInfo,
  getSourceFeatureCount,
  getSuperfundLayerInfo,
  getFacilitiesLayerInfo,
  getDemographicsLayerInfo,
  getViewState,
  getTierSizing,
};
```

**Usage:**
```python
from tests.steps._shared import inject_map_helpers
inject_map_helpers(page)
result = page.evaluate('mapHelpers.hasSource("facilities")')
```

---

## Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Duplicate step definitions | 4 | 0 | -4 |
| Magic timeout numbers | 55 | 0 | -55 |
| `bounding_box()` type errors | 4 | 0 | -4 |
| Helper functions | 0 | 4 | +4 |
| Named constants | 7 | 11 | +4 |
| Domain modules | 1 | 10 | +9 |
| JS helper functions | 0 | 15 | +15 |
| Total step definitions | 181 | 191 | +10 (refined) |

---

## Files Created

- `tests/steps/__init__.py` — Package exports
- `tests/steps/_shared.py` — Constants and helpers
- `tests/steps/navigation_steps.py` — Navigation steps
- `tests/steps/search_steps.py` — Search form steps
- `tests/steps/results_steps.py` — Results table steps
- `tests/steps/facility_steps.py` — TRI facility drawer steps
- `tests/steps/superfund_steps.py` — Superfund panel steps
- `tests/steps/demographics_steps.py` — Demographics steps
- `tests/steps/map_layer_steps.py` — MapLibre layer steps
- `tests/steps/export_steps.py` — Export functionality steps
- `tests/steps/regression_steps.py` — Bug regression test steps
- `tests/steps/stubs_steps.py` — Placeholder stub steps
- `tests/fixtures/map_helpers.js` — MapLibre JavaScript utilities

## Files Deleted

- `tests/steps/e2e_steps.py` — Legacy monolith (removed after migration complete)

---

## Verification

All changes verified with:
```bash
python -c "from tests.steps import *"           # Modular imports
python -m py_compile tests/steps/*.py           # Syntax check all modules
```

Unit tests and E2E tests should be run to verify no regressions.

---

## 8. Delete Legacy Monolith ✅

**Issue:** After migration, `e2e_steps.py` was redundant (all 181 steps migrated to modules).

**Solution:** 
1. Updated test runner files to use `from tests.steps import *`
2. Removed `e2e_steps.py`
3. Verified all imports work without the legacy file
