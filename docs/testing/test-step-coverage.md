# TOXMAP Test Step Coverage Tracker

**Last updated:** 2026-07-21  
**Purpose:** Tracks which Gherkin step definitions are implemented, which are stubs, and which development phase each is
targeted for. Prevents agents from over-generating all steps at once (violating the phase schedule) or under-generating
(only the documented stubs).

> **Source of truth for scenario text:** `TOXMAP_ACCEPTANCE_TESTS.md`  
> **Step files:** `tests/steps/api_steps.py` · `tests/steps/e2e_steps.py`

---

## Status Legend

| Symbol | Meaning                              |
|--------|--------------------------------------|
| ✅      | Implemented and passing in CI        |
| 🔧     | Stub exists (function body = `pass`) |
| ❌      | Not yet written — target phase shown |

---

## Feature 1: TRI Facility Search (`facility_search.feature`) — Phase 2

| Step Text                                                                                 | Status | Phase   | Notes                                 |
|-------------------------------------------------------------------------------------------|--------|---------|---------------------------------------|
| `Given the seed database is loaded`                                                       | 🔧     | Phase 0 | `seed_db` fixture in conftest.py      |
| `Given the API is running at base URL "{base_url}"`                                       | 🔧     | Phase 0 | `api_client` fixture                  |

**E2E Phase 0 fixtures** (tracked here alongside API Phase 0 for completeness):

| Step Text                                                             | Status | Phase   | Notes                                                              |
|-----------------------------------------------------------------------|--------|---------|--------------------------------------------------------------------|
| `Given the application is running at "{url}"` (E2E Background)       | 🔧     | Phase 0 | No-op; `page` fixture + `--base-url` in pyproject.toml sets URL   |
| `Given the seed database is loaded` (E2E Background)                 | 🔧     | Phase 0 | Same `seed_db` fixture — reused from API conftest.py              |
| `Given I am on the map page`                                          | 🔧     | Phase 0 | `page.goto("/")` + `wait_for_selector("[data-testid='map-container']")` |

---
| `When I GET "{path}"`                                                                     | 🔧     | Phase 2 | httpx client call                     |
| `Then the response status is {code:d}`                                                    | 🔧     | Phase 2 | `assert response.status_code == code` |
| `Then the response is a GeoJSON FeatureCollection`                                        | 🔧     | Phase 2 | check `type == "FeatureCollection"`   |
| `Then the FeatureCollection contains a feature with property "{key}" = "{value}"`         | ❌      | Phase 2 | iterate features                      |
| `Then every feature has a "{field}" property that is a number`                            | ❌      | Phase 2 | type check loop                       |
| `Then every feature has a "color_band" property in {list}`                                | ❌      | Phase 2 | enum check                            |
| `Then the FeatureCollection does not contain a feature with property "{key}" = "{value}"` | ❌      | Phase 2 | negative check                        |
| `Then the response meta has "{key}" = {value}`                                            | ❌      | Phase 2 | dict path check                       |
| `Then every feature has coordinates within bbox {bbox}`                                   | 🔧     | Phase 2 | coordinate bounds check               |
| `Then every feature in the FeatureCollection has a non-null "{field}" property`           | ❌      | Phase 2 | null check                            |
| `Then every feature has property "{key}" = "{value}"`                                     | ❌      | Phase 2 | property equality check               |
| `Then the FeatureCollection may contain features with "{key}" != "{value}"`               | ❌      | Phase 2 | informational — no assertion needed   |
| `Then the response has "{key}" = "{value}"`                                               | ❌      | Phase 2 | top-level dict check                  |
| `Then the response has "{key}" containing "{substr}"`                                     | ❌      | Phase 2 | substring check                       |
| `Then the response status is 422`                                                         | ❌      | Phase 2 | same as status check                  |
| `Then the response status is 400`                                                         | ❌      | Phase 2 | same as status check                  |

---

## Feature 2: Release Time Series (`release_trends.feature`) — Phase 2

| Step Text                                                                        | Status | Phase   | Notes                    |
|----------------------------------------------------------------------------------|--------|---------|--------------------------|
| `Then the response is a JSON array`                                              | ❌      | Phase 2 | `isinstance(body, list)` |
| `Then every item has "{fields}"`                                                 | ❌      | Phase 2 | field presence check     |
| `Then the array contains an item with "{key}" = {value} and "{key2}" = {value2}` | ❌      | Phase 2 | filter + assert          |
| `Then the array length is greater than 0`                                        | ❌      | Phase 2 | `len(body) > 0`          |
| `Then no item has "{key}" = null`                                                | ❌      | Phase 2 | null filter              |
| `Then the response has "total_release_lbs" >= {value}`                           | ❌      | Phase 2 | numeric comparison       |

---

## Feature 3: Chemical Search (`chemicals.feature`) — Phase 2

| Step Text                                                                           | Status | Phase   | Notes                                 |
|-------------------------------------------------------------------------------------|--------|---------|---------------------------------------|
| `Then the array contains an item with "cas_number" = "{cas}" and "name" = "{name}"` | ❌      | Phase 2 | filter + assert                       |
| `Then every item has "atsdr_url" as a string or null`                               | ❌      | Phase 2 | type check                            |
| `Then the array length is <= {n:d}`                                                 | ❌      | Phase 2 | length bound                          |
| `Then the response is an empty JSON array`                                          | ❌      | Phase 2 | `body == []`                          |
| `Then the response time is less than {ms:d} milliseconds`                           | 🔧     | Phase 2 | `elapsed.total_seconds() * 1000 < ms` |

---

## Feature 4: Superfund Search (`superfund.feature`) — Phase 4

| Step Text                                                       | Status | Phase   | Notes                 |
|-----------------------------------------------------------------|--------|---------|-----------------------|
| `Then every feature has "{fields}" properties`                  | ❌      | Phase 4 | field presence check  |
| `Then every feature has a geometry of type "Point"`             | ❌      | Phase 4 | geometry type check   |
| `Then the response has "contaminants" as a non-empty array`     | ❌      | Phase 4 | length > 0            |
| `Then the response has "epa_progress_url" as a non-null string` | ❌      | Phase 4 | not None + isinstance |
| `Then the FeatureCollection contains 0 features`                | ❌      | Phase 4 | `len(features) == 0`  |

---

## Feature 5: Demographics (`demographics.feature`) — Phase 5

| Step Text                                                              | Status | Phase   | Notes                      |
|------------------------------------------------------------------------|--------|---------|----------------------------|
| `Then every feature has geometry of type "MultiPolygon" or "Polygon"`  | ❌      | Phase 5 | geometry type check        |
| `Then that feature has "{field}" as a number between {low} and {high}` | ❌      | Phase 5 | numeric range check        |
| `Then that feature has units metadata "{key}" = "{value}"`             | ❌      | Phase 5 | meta.units path check      |
| `Then the response meta has "units" object containing keys {keys}`     | ❌      | Phase 5 | key presence in meta.units |
| `Then every feature has "fips_code" starting with "{prefix}"`          | ❌      | Phase 5 | string prefix check        |

---

## Feature 6: CSV Export (`export.feature`) — Phase 3

| Step Text                                                                           | Status | Phase   | Notes                 |
|-------------------------------------------------------------------------------------|--------|---------|-----------------------|
| `Then the response Content-Type is "text/csv"`                                      | ❌      | Phase 3 | header check          |
| `Then the response Content-Disposition contains "attachment"`                       | ❌      | Phase 3 | header substring      |
| `Then the CSV has headers: "{header_line}"`                                         | ❌      | Phase 3 | first row parse       |
| `Then the CSV contains a row with "{col}" = "{value}"`                              | ❌      | Phase 3 | csv.DictReader filter |
| `Then the response uses Transfer-Encoding "chunked" or has a Content-Length header` | ❌      | Phase 3 | header presence       |

---

## Feature 9: Data Vintage Metadata (`metadata.feature`) — Phase 2

> Covers `GET /api/v1/meta`. Implemented in Phase 2 alongside the other API endpoints because it requires the same `seed_db` fixture and FastAPI test client. See [TOXMAP_API_CONTRACT.md §17](../api/TOXMAP_API_CONTRACT.md).

| Step Text                                                                 | Status | Phase   | Notes                                                              |
|---------------------------------------------------------------------------|--------|---------|--------------------------------------------------------------------|
| `Then the response has "available_years" as a non-empty array`            | ❌      | Phase 2 | `isinstance(body["available_years"], list) and len(...) > 0`       |
| `Then the response has "latest_year" as a positive integer`               | ❌      | Phase 2 | `isinstance(body["latest_year"], int) and body["latest_year"] > 0` |
| `Then the response has "total_facility_count" as a positive integer`      | ❌      | Phase 2 | same pattern                                                       |
| `Then the response has "total_release_event_count" as a positive integer` | ❌      | Phase 2 | same pattern                                                       |
| `Then the response "available_years" contains {year:d}`                   | ❌      | Phase 2 | `year in body["available_years"]`                                  |
| `Then the response has "vintage_label" as a non-null string`              | ❌      | Phase 2 | `isinstance(body["vintage_label"], str)`                           |

---

## Feature 7: UCD 2011 E2E Task Scenarios (`ucd_task_scenarios.feature`) — Phase 3–5

| Scenario                         | Status | Phase   | Key Steps Needing Implementation                                       |
|----------------------------------|--------|---------|------------------------------------------------------------------------|
| T-01: Lead near Sparrows Point   | ❌      | Phase 3 | `type "Sparrows Point, MD"`, `shows "12,485 lbs"`, comma formatting    |
| T-02: Superfund chemical list    | ❌      | Phase 4 | `click "Superfund"`, `chemical list contains "STYRENE"`, `<= 2 clicks` |
| T-03: Copper > 8,000 lbs NV      | ❌      | Phase 3 | `shows "8,205 lbs"`, `"Land" medium as largest bar`                    |
| T-04: AVTEX FIBERS Superfund     | ❌      | Phase 4 | Superfund diamond marker, contaminants list, EPA progress link         |
| T-05: TRI + under-18 overlay     | ❌      | Phase 5 | Demographics panel, inline legend, simultaneous TRI + choropleth       |
| T-06: Income demographic layer   | ❌      | Phase 5 | "$" units, "Clear layer" button                                        |
| T-07: SC vs nationwide chlorine  | ❌      | Phase 5 | "Limit to state" checkbox, uncheck + re-search                         |
| T-08: ToxFAQ link                | ❌      | Phase 3 | new tab opens, original tab unchanged, `data-testid="atsdr-link"`      |
| T-09: Benzene + cancer mortality | ❌      | Phase 5 | mortality tab, co-occurrence disclaimer visible                        |

---

## Feature 8: UX Invariants (`ux_invariants.feature`) — Phase 3–5

> **Scope note:** This feature implements Playwright assertions for **10 of the 10 canonical UX
> invariants** as follows — 5 invariants are tested directly here; the other 5 are covered by the
> UCD 2011 E2E task scenarios in Feature 7. Item 11 below is a **Phase 3 gate DoD item**, not a
> standing UX invariant; it still requires a step implementation.
>
> | CONTEXT_SUMMARY invariant # | Tested in Feature 8? | If not, tested in |
> |------------------------------|----------------------|-------------------|
> | 1 — Default view (US centered, all TRI visible) | No | Feature 7 (T-01/T-03 E2E) |
> | 2 — Search re-centers map without page reload | No | Feature 7 (T-01/T-03 E2E) |
> | 3 — Facility detail panel without page navigation | No | Feature 7 (T-01/T-03 E2E) |
> | 4 — No "Quick Search" / "Demographics" labels | **Yes** — item 4 below | — |
> | 5 — Inline legend visible without hover | **Yes** — item 5 below | — |
> | 6 — TRI circles; Superfund diamonds | **Yes** — item 6 below | — |
> | 7 — Facility count in results panel | No | Feature 7 (T-01/T-03 E2E) |
> | 8 — Release ≥1,000 formatted with commas | **Yes** — item 8 below | — |
> | 9 — Map state preserved on back/forward | No | Feature 7 (T-08 E2E) |
> | 10 — Co-occurrence disclaimer on mortality tab only | **Yes** — item 10 below | — |

| Invariant                | Status | Phase   | Key Selector                                                                   |
|--------------------------|--------|---------|--------------------------------------------------------------------------------|
| 1: Single sidebar        | ❌      | Phase 3 | `[data-testid="sidebar-panel"][data-active="true"]` count == 1                 |
| 2: No empty rows         | ❌      | Phase 3 | `[data-testid="results-row"]` all have non-empty text                          |
| 3: State restriction     | ❌      | Phase 3 | `[data-testid="restrict-to-state-checkbox"]`                                   |
| 4: Panel labels          | ❌      | Phase 3 | text "Quick Search" absent, "Search Chemical Releases" present                 |
| 5: Inline legend         | ❌      | Phase 5 | `[data-testid="demographic-legend-entry"]` visible without hover               |
| 6: Distinct icons        | ❌      | Phase 4 | TRI circle != Superfund diamond (check SVG shape attributes)                   |
| 7: Latest year label     | ❌      | Phase 3 | `[data-testid="layer-toggle-tri-latest"]` contains "(latest year)"             |
| 8: Comma formatting      | ❌      | Phase 3 | `/\d{1,3}(,\d{3})+/` in `[data-testid="facility-release-amount"]`              |
| 9: Close link at bottom  | ❌      | Phase 3 | `[data-testid="popup-close-bottom"]` visible and clickable                     |
| 10: Disclaimer scope     | ❌      | Phase 5 | `[data-testid="cooccurrence-disclaimer"]` only on mortality tab                |
| ~~11: Data vintage visible~~ → **Gate DoD item (Phase 3, not a UX invariant)** | ❌ | Phase 3 | `[data-testid="data-vintage-label"]` visible, non-empty, no "null"/"undefined" — verified in Gate 3→4 checklist |

---

## Step Count Summary

| Phase     | Feature                                        | Total Steps | Implemented | Stubs | Not Started |
|-----------|------------------------------------------------|-------------|-------------|-------|-------------|
| Phase 0   | API Fixtures + E2E Fixtures                    | 5           | 0           | 5     | 0           |
| Phase 2   | F1–F3, F9                                      | 41          | 0           | 6     | 35          |
| Phase 3   | F6, T-01/03/08, F8-rows 1–4/7–9/11¹           | 23          | 0           | 0     | 23          |
| Phase 4   | F4, T-02/04, F8-row 6¹                         | 10          | 0           | 0     | 10          |
| Phase 5   | F5, T-05–07/09, F8-rows 5/10¹                  | 20          | 0           | 0     | 20          |
| **Total** |                                                | **99**      | **0**       | **11**| **88**      |

> ¹ **Feature 8 numbering note:** "F8-row N" refers to Feature 8's **local row numbers** (1–10+11),
> which are NOT the same as `CONTEXT_SUMMARY.md` UX invariant numbers. See the cross-reference table
> at the top of §Feature 8 for the mapping between CONTEXT_SUMMARY invariant IDs (1–10) and which
> Feature (7 or 8) covers each one. In brief: CONTEXT_SUMMARY invariants #4, #5, #6, #8, #10 are
> directly tested in Feature 8; invariants #1, #2, #3, #7, #9 are covered by Feature 7 (UCD E2E).

> All step definitions need implementation during their respective phases. Agents implementing steps in Phase 2 must NOT pre-implement Phase 3+ steps — doing so violates the phased delivery schedule and may produce untestable code before the required UI components exist.

> **Future layer stubs (Phase 4/5):** When the nuclear, NPRI, and congressional-districts endpoints are implemented, create the corresponding feature files before writing step definitions:
> - `tests/features/api/nuclear.feature` (Phase 4)
> - `tests/features/api/npri.feature` (Phase 5)
> - `tests/features/api/congressional_districts.feature` (Phase 5)
> Each stub should follow the same Background + Scenario pattern as `superfund.feature` and be registered in this tracker before agent implementation begins.

