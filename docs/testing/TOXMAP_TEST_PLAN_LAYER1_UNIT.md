# Test Plan
## Service: `toxmap`

- **Author(s):** Victor Cannestro
- **Maintained By:** Quality Engineering Team
- **Version:** 1.0  
- **Last Updated:** 2026-08-03 — Added 4.11 Superfund CAS Lookup tests (7.BUG.17–7.BUG.21): ATSDR toxid correctness, PubChem URL validation for petroleum mixtures
- **Test Type:** Unit Test (pure logic — zero I/O, zero infrastructure)

---

## Table of Contents
1. [Scope & Objectives](#1-scope--objectives)
2. [Test Architecture](#2-test-architecture)
3. [Test Data](#3-test-data)
4. [Test Scenarios](#4-test-scenarios)
5. [Entry & Exit Criteria](#5-entry--exit-criteria)
6. [Out of Scope](#6-out-of-scope)
7. [Appendix A — Automation Traceability](#appendix-a--automation-traceability)

---

## 1. Scope & Objectives

### Scope
This plan covers unit-level testing of all pure-logic modules in the TOXMAP backend (`app/domain/`, `app/services/` utilities) and frontend (`src/utils/`, `src/state/`). No database, network, filesystem, or browser interaction is permitted. Tests run offline and complete in under 30 seconds total.

### Functionality Under Test

| Module | Language | File | Purpose |
|--------|----------|------|---------|
| Color band classification | Python | `app/domain/color_band.py` | Assigns `"green"/"yellow"/"orange"/"red"` based on release quantity thresholds |
| Geo utilities | Python | `app/domain/geo_utils.py` | Miles→meters conversion, bbox string parsing, radius validation |
| GeoJSON builder | Python | `app/domain/geojson_builder.py` | Constructs RFC 7946-compliant `Feature` and `FeatureCollection` objects |
| Query param validation | Python | `app/schemas/query_params.py` | Pydantic models for all endpoint parameters |
| CSV row formatter | Python | `app/domain/csv_formatter.py` | Formats facility + release data into CSV row dicts |
| Meta response builder | Python | `app/domain/meta_builder.py` | Constructs `/api/v1/meta` response with vintage fallback logic |
| Superfund CAS lookup | Python | `app/services/superfund_cas_lookup.py` | Provides CAS numbers, ATSDR ToxFAQs URLs, and PubChem URLs for Superfund contaminants not in TRI chemicals table |
| Number formatters | TypeScript | `src/utils/formatters.ts` | Comma-formats release quantities; appends units (`%`, `$`) |
| Color band CSS mapping | TypeScript | `src/utils/colorBand.ts` | Maps `color_band` string to hex color for MapLibre GL |
| Sidebar state machine | TypeScript | `src/state/sidebarState.ts` | Enforces mutual exclusion of Map Contents and Search Results panels |
| BBox utilities | TypeScript | `src/utils/bboxUtils.ts` | Parses bbox string; validates point-in-bbox; serializes MapLibre bounds |
| Year picker logic | TypeScript | `src/state/yearPicker.ts` | Derives `latestYear`, generates `"(latest year)"` label |

### Two-Phase Test Flow

```
Phase 1: Input              Phase 2: Assert
┌─────────────────┐        ┌──────────────────────┐
│  Parametrized   │        │  Return value /      │
│  input values   │───────▶│  raised exception    │
│  (no mocking)   │        │  matches expected    │
└─────────────────┘        └──────────────────────┘
```

---

## 2. Test Architecture

### Approach
Each test module imports the production function directly. No fixtures, no mocking. Parametrized test cases drive boundary-value analysis.

```
[ @pytest.mark.parametrize / test.each() ]
│
│  (call production function directly)
▼
[ Pure function: assign_color_band(lbs) ]
│
│  (return value)
▼
[ assert return == expected ]
```

### Test Infrastructure

| Component         | Strategy                                              |
|-------------------|-------------------------------------------------------|
| Python runner     | `pytest` with `@pytest.mark.parametrize`              |
| TypeScript runner | `Vitest` with `test.each()`                           |
| No mocking needed | Functions have no side effects or dependencies        |
| Negative testing  | `pytest.raises(ValueError)` / `expect(...).toThrow()` |

### Test Execution Lifecycle

```
BEFORE_ALL  (none)
TEST
├─ Call function with parametrized input
└─ Assert return value OR raised exception
AFTER_ALL   (none)
```

### Key Assertion Values

All boundary values are derived from the [TOXMAP API Contract §Color Band Logic](../api/TOXMAP_API_CONTRACT.md) and [TOXMAP_TEST_SEED_DATA.md §9 Known Good Assertion Values](TOXMAP_TEST_SEED_DATA.md).

| Value                         | Source                            | What it tests                          |
|-------------------------------|-----------------------------------|----------------------------------------|
| `12485.0` → `"orange"`        | T-01 Bethlehem Steel              | Color band boundary (10k–99,999)       |
| `8205.0` → `"8,205"`          | T-03 Robinson NV (UCD 2011 exact) | Comma formatting invariant             |
| `342500.0` → `"red"`          | T-07 Enterprise Gas               | Color band ≥ 100k boundary             |
| `[lon, lat]` coordinate order | RFC 7946                          | GeoJSON coordinate convention          |
| `vintage_label == "unknown"`  | Seed data design                  | Meta fallback when no ingestion record |

---

## 3. Test Data

Unit tests use **inline parametrize values only**. No SQL files, no fixtures, no seed data are loaded. All inputs and expected outputs are defined directly in each `@pytest.mark.parametrize` or `test.each()` call.

> ⚠️ **Date Maintenance:** Not applicable — unit tests contain no date-sensitive data.

---

## 4. Test Scenarios

### 4.1 Color Band Classification

**File:** `tests/unit/backend/test_color_band.py`  
**Prefix:** `CB` (Color Band)

| ID    | Input `lbs` | Expected `color_band`     | Notes                             |
|-------|-------------|---------------------------|-----------------------------------|
| CB-01 | `0.0`       | `"green"`                 | Zero release                      |
| CB-02 | `999.0`     | `"green"`                 | Upper boundary of green band      |
| CB-03 | `1000.0`    | `"yellow"`                | Lower boundary of yellow band     |
| CB-04 | `9999.0`    | `"yellow"`                | Upper boundary of yellow band     |
| CB-05 | `10000.0`   | `"orange"`                | Lower boundary of orange band     |
| CB-06 | `12485.0`   | `"orange"`                | T-01 Bethlehem Steel (seed value) |
| CB-07 | `99999.0`   | `"orange"`                | Upper boundary of orange band     |
| CB-08 | `100000.0`  | `"red"`                   | Lower boundary of red band        |
| CB-09 | `342500.0`  | `"red"`                   | T-07 Enterprise Gas (seed value)  |
| CB-10 | `-1.0`      | `ValueError`              | Negative release quantity is invalid; function must raise before returning a band |
| CB-11 | `8.5` with `unit="Grams"` | `"green"` (equivalent to 8.5 × 453.592 ≈ 3855 lbs) | Gram-unit inputs must be scaled to lbs-equivalent before band assignment. The color-band function must accept an optional `unit` parameter; dioxin-like facilities (TRI N150) report in grams — failing to scale produces a ~453× underestimate of the hazard tier. See A-048 in TOXMAP_DESIGN_ASSUMPTIONS.md. |

> **Implementation note for agents:** `assign_color_band` must accept a `unit: str = "Pounds"` parameter. When `unit == "Grams"`, convert input by multiplying by 453.592 before applying pound-based thresholds. CB-11 uses 8.5 g → 3855 lbs → green band (below 1,000 lbs threshold). A meaningful dioxin real-world case: `25.0 g` → 11,340 lbs-equivalent → orange band.

### 4.2 Geo Utilities

**File:** `tests/unit/backend/test_geo_utils.py`  
**Prefix:** `GU` (Geo Utilities)

| ID    | Function           | Input                     | Expected                     | Notes                      |
|-------|--------------------|---------------------------|------------------------------|----------------------------|
| GU-01 | `miles_to_meters`  | `10`                      | `16093.44` (±1 m)            | Standard conversion        |
| GU-02 | `miles_to_meters`  | `0`                       | `0.0`                        | Zero radius                |
| GU-03 | `miles_to_meters`  | `500`                     | valid result                 | Max allowed — no exception |
| GU-04 | `miles_to_meters`  | `501`                     | `ValueError`                 | Exceeds max radius         |
| GU-05 | `bbox_from_string` | `"-76.6,39.1,-76.3,39.4"` | `(-76.6, 39.1, -76.3, 39.4)` | Standard bbox              |
| GU-06 | `bbox_from_string` | `"invalid"`               | `ValueError`                 | Malformed string           |
| GU-07 | `bbox_from_string` | `"-76.3,39.1,-76.6,39.4"` | `ValueError`                 | Swapped min/max lon        |

### 4.3 GeoJSON Builder

**File:** `tests/unit/backend/test_geojson_builder.py`  
**Prefix:** `GB` (GeoJSON Builder)

| ID    | Scenario                                        | Assertion                                                                                                        |
|-------|-------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| GB-01 | `build_facility_feature(db_row)` with valid row | `geometry.type == "Point"`                                                                                       |
| GB-02 | Coordinate order                                | `coordinates == [lon, lat]` not `[lat, lon]` (RFC 7946)                                                          |
| GB-03 | Properties completeness                         | `tri_facility_id`, `name`, `city`, `state_code`, `total_release_lbs`, `color_band`, `reporting_year`, `unit_of_measure` all present |
| GB-04 | `build_feature_collection(features, meta)`      | `type == "FeatureCollection"`, `meta.total_count == len(features)`                                                                   |
| GB-05 | Row with `NULL` location                        | Feature excluded from output (no null geometry)                                                                                      |
| GB-06 | Row with `unit_of_measure = "Grams"`            | `properties.unit_of_measure == "Grams"` — GeoJSON serializer must propagate the column from `release_events`; frontend reads this to display "g" label (see A-048) |

### 4.4 Query Parameter Validation

**File:** `tests/unit/backend/test_query_params.py`  
**Prefix:** `QP` (Query Params)

| ID    | Input                                                         | Expected                                |
|-------|---------------------------------------------------------------|-----------------------------------------|
| QP-01 | `FacilitySearchParams(lat=39.2, lon=-76.5, radius_miles=10)`  | Valid — no exception                    |
| QP-02 | `FacilitySearchParams(radius_miles=10)`                       | `ValidationError` — missing `lat`/`lon` |
| QP-03 | `FacilitySearchParams(lat=39.2, lon=-76.5, radius_miles=999)` | `ValidationError` — radius > 500        |
| QP-04 | `FacilitySearchParams(lat=91.0, lon=-76.5, radius_miles=10)`  | `ValidationError` — lat out of range    |
| QP-05 | `FacilitySearchParams(..., year=1986)`                        | `ValidationError` — TRI began 1987      |
| QP-06 | `FacilitySearchParams(..., medium="fog")`                     | `ValidationError` — invalid enum value  |
| QP-07 | `ChemicalSearchParams(q="b")`                                 | `ValidationError` — min length 2        |
| QP-08 | `ChemicalSearchParams(q="be")`                                | Valid                                   |

### 4.5 CSV Row Formatter

**File:** `tests/unit/backend/test_csv_formatter.py`  
**Prefix:** `CF` (CSV Formatter)

| ID    | Scenario                                | Assertion                                                                            |
|-------|-----------------------------------------|--------------------------------------------------------------------------------------|
| CF-01 | `format_release_row(facility, release)` | Column order matches [TOXMAP_API_CONTRACT.md §15](../api/TOXMAP_API_CONTRACT.md)     |
| CF-02 | Float values                            | Written as floats (`12485.0`), not comma-formatted — that is frontend responsibility |
| CF-03 | `None` medium fields                    | Written as `"0.0"`, not empty string                                                 |
| CF-04 | `release.unit_of_measure = "Pounds"`    | Row contains `unit_of_measure` column with value `"Pounds"` — required per C-2 fix  |
| CF-05 | `release.form_type = "A"` (Form A)      | Row contains `form_type` column with value `"A"`; distinguishable from Form R zero-release records — required per H-4 fix |

### 4.6 Meta Response Builder

**File:** `tests/unit/backend/test_meta_builder.py`  
**Prefix:** `MB` (Meta Builder)

| ID    | Input                                                                | Assertion                                               |
|-------|----------------------------------------------------------------------|---------------------------------------------------------|
| MB-01 | `build_meta_response(ingestion_record=None)`                         | `vintage_label == "unknown"`, `build_date == "unknown"` |
| MB-02 | `build_meta_response(ingestion_record={"vintage": "Oct 2024", ...})` | Values propagated correctly                             |
| MB-03 | `available_years` from `[2008, 2006, 2007]` (unsorted input)         | Sorted ascending: `[2006, 2007, 2008]`                  |
| MB-04 | `latest_year`                                                        | `max(available_years)`                                  |

### 4.7 Frontend Number Formatters

**File:** `src/__tests__/unit/formatters.test.ts`  
**Prefix:** `FF` (Frontend Formatters)

| ID    | Input                           | Expected         | Notes                    |
|-------|---------------------------------|------------------|--------------------------|
| FF-01 | `formatReleaseQuantity(8205)`   | `"8,205"`        | UCD 2011 comma invariant |
| FF-02 | `formatReleaseQuantity(12485)`  | `"12,485"`       | T-01 Bethlehem           |
| FF-03 | `formatReleaseQuantity(342500)` | `"342,500"`      | T-07 Enterprise          |
| FF-04 | `formatReleaseQuantity(0)`      | `"0"`            | Zero                     |
| FF-05 | `formatReleaseQuantity(null)`   | `"—"` or `"N/A"` | Never render `"null"`    |
| FF-06 | `formatReleaseQuantity(999)`    | `"999"`          | No commas under 1,000    |
| FF-07 | `formatWithUnit(24.7, "%")`     | `"24.7%"`        | Demographics unit        |
| FF-08 | `formatWithUnit(41246, "$")`    | `"$41,246"`      | Income unit              |
| FF-09 | `formatReleaseQuantity(8205, "Pounds")`  | `"8,205 lbs"`   | Explicit Pounds unit label; all seed records use Pounds |
| FF-10 | `formatReleaseQuantity(8.5, "Grams")`   | `"8.5 g"` or `"8.5 grams"` | Gram unit label for dioxin facilities; must NOT display "lbs" when unit is Grams |

### 4.8 Color Band CSS Mapping

**File:** `src/__tests__/unit/colorBand.test.ts`  
**Prefix:** `BC` (Band CSS)

> **Implementation note for agents:** The expected hex values for BC-01 through BC-04 are defined in the design system constants in `src/utils/colorBand.ts` (or the project's Tailwind/token config). Read the production source to obtain the canonical hex before writing assertions — do NOT hard-code assumed hex values. BC-05 only asserts no crash and a non-null/non-undefined return value.

| ID    | Input                                             | Expected                                                                         |
|-------|---------------------------------------------------|----------------------------------------------------------------------------------|
| BC-01 | `colorBandToHex("green")`                         | Hex string matching design system constant (read from `colorBand.ts`)            |
| BC-02 | `colorBandToHex("yellow")`                        | Hex string matching design system constant                                       |
| BC-03 | `colorBandToHex("orange")`                        | Hex string matching design system constant                                       |
| BC-04 | `colorBandToHex("red")`                           | Hex string matching design system constant                                       |
| BC-05 | `colorBandToHex("unknown")`                       | Fallback color — non-null, non-undefined string; no exception thrown             |

### 4.9 Sidebar State Machine

**File:** `src/__tests__/unit/sidebarState.test.ts`  
**Prefix:** `SS` (Sidebar State)

| ID    | Scenario                                            | Assertion                                                        |
|-------|-----------------------------------------------------|------------------------------------------------------------------|
| SS-01 | Initial state                                       | `activePanel == "map-contents"`, `searchResultsVisible == false` |
| SS-02 | `showSearchResults()`                               | `activePanel == "search-results"`, `mapContentsVisible == false` |
| SS-03 | `showMapContents()`                                 | `activePanel == "map-contents"`, `searchResultsVisible == false` |
| SS-04 | `activePanelCount()` across any transition sequence | Always returns `1`                                               |
| SS-05 | Both panels                                         | Never both `visible == true` simultaneously                      |

### 4.10 BBox Utilities / Year Picker

**Files:** `src/__tests__/unit/bboxUtils.test.ts` · `src/__tests__/unit/yearPicker.test.ts`  
**Prefix:** `BX` (BBox / year piXer)

| ID    | Function                              | Input                     | Assertion                                          |
|-------|---------------------------------------|---------------------------|----------------------------------------------------|
| BX-01 | `parseBbox`                           | `"-76.6,39.1,-76.3,39.4"` | Returns `[-76.6, 39.1, -76.3, 39.4]`               |
| BX-02 | `isPointInBbox`                       | boundary coordinates      | `true`/`false` at exact edges                      |
| BX-03 | `toBboxString`                        | MapLibre bounds object    | Correct comma-separated serialization              |
| BX-04 | `getAvailableYears([2006,2007,2008])` | —                         | `latestYear == 2008`                               |
| BX-05 | Latest year option text               | —                         | Includes `"(latest year)"` suffix (UX Invariant 7) |
| BX-06 | Year not in `available_years`         | —                         | Treated as invalid selection                       |

### 4.11 Superfund CAS Lookup

**File:** `tests/unit/test_superfund_cas_lookup.py`  
**Prefix:** `SL` (Superfund Lookup)

Regression tests for bug fixes 7.BUG.17, 7.BUG.18, 7.BUG.19, 7.BUG.21. Validates CAS numbers, ATSDR ToxFAQs URLs (correct toxid mappings), and PubChem URLs (correct patterns for petroleum mixtures).

| ID    | Class                    | Test                                      | Assertion                                                                 |
|-------|--------------------------|-------------------------------------------|---------------------------------------------------------------------------|
| SL-01 | `TestATSDRToxidCorrectness` | `test_atsdr_toxid_is_correct`           | 30+ chemicals have correct ATSDR toxid (e.g., MANGANESE=23, not 42)       |
| SL-02 | `TestATSDRToxidCorrectness` | `test_manganese_not_methylene_chloride` | MANGANESE links to toxid=23, NOT toxid=42 (7.BUG.18 regression)           |
| SL-03 | `TestATSDRUrlFormat`     | `test_all_atsdr_urls_use_toxfaqs_format`  | All ATSDR URLs use `ToxFAQsDetails.aspx`, not `ToxSubstance.aspx`         |
| SL-04 | `TestCASNumberCoverage`  | `test_cas_number_correct`                 | 30+ key chemicals have verified CAS numbers                               |
| SL-05 | `TestCASNumberCoverage`  | `test_lookup_has_minimum_coverage`        | Lookup has ≥200 entries                                                   |
| SL-06 | `TestChemicalNameVariants` | `test_all_variants_present`             | Chemical name variants (TCE, PERC, DCE, DDT, xylenes) all present         |
| SL-07 | `TestPubChemUrlValidation` | `test_petroleum_mixture_pubchem_urls`   | TPH, JP-5, JP-8 use `/substance/` URLs; Fuel Oils use `/compound/Fuel-Oils` (7.BUG.21) |
| SL-08 | `TestPubChemUrlValidation` | `test_tph_not_compound_url`             | TPH does NOT use `/compound/` URL (returns 404)                           |
| SL-09 | `TestPubChemUrlValidation` | `test_jp5_not_compound_url`             | JP-5 does NOT use `/compound/JP-5` URL (redirects to wrong compound)     |
| SL-10 | `TestPubChemUrlValidation` | `test_all_pubchem_urls_are_valid_format`| All explicit PubChem URLs match `/compound/` or `/substance/` patterns    |

---

## 5. Entry & Exit Criteria

### Entry Criteria

| # | Criterion                             | Verification                                              |
|---|---------------------------------------|-----------------------------------------------------------|
| 1 | Target module compiled without errors | `pytest --collect-only` succeeds; `tsc --noEmit` succeeds |
| 2 | `pytest` ≥ 8.0 and `Vitest` installed | `pytest --version`; `npx vitest --version`                |
| 3 | No external services required         | Tests run without Docker or network                       |

### Exit Criteria

| # | Criterion                                            | Evidence                                                       |
|---|------------------------------------------------------|----------------------------------------------------------------|
| 1 | All parametrized cases passing                       | `pytest tests/unit/` and `npm run test:unit` report 0 failures |
| 2 | `app/domain/` line + branch coverage = **100%**      | `pytest-cov` report                                            |
| 3 | `src/utils/` + `src/state/` line coverage = **100%** | Vitest coverage report                                         |
| 4 | No `pytest.skip()` without justification             | Code review                                                    |
| 5 | Mutation score ≥ 85% on `app/domain/`                | `mutmut` results                                               |

---

## 6. Out of Scope

| Area                                 | Reason                                                    |
|--------------------------------------|-----------------------------------------------------------|
| Database queries                     | Covered by Layer 3 Integration Tests                      |
| HTTP request/response                | Covered by Layer 3 and Layer 4                            |
| React component rendering            | Covered by Layer 2 Component Tests                        |
| Browser behavior                     | Covered by Layer 5 E2E Tests                              |
| `app/repositories/` (SQL generation) | Covered by Layer 3 Integration Tests against real PostGIS |

---

## Appendix A — Automation Traceability

| Test ID | Scenario ID   | Description                                 | File                      | Status     |
|---------|---------------|---------------------------------------------|---------------------------|------------|
| UT-01   | CB-01–CB-09   | Color band boundary values                  | `test_color_band.py`      | ⚠️ Planned |
| UT-02   | CB-10         | Color band negative guard                   | `test_color_band.py`      | ⚠️ Planned |
| UT-03   | GU-01–GU-03   | `miles_to_meters` conversion                | `test_geo_utils.py`       | ⚠️ Planned |
| UT-04   | GU-04         | `miles_to_meters` max guard                 | `test_geo_utils.py`       | ⚠️ Planned |
| UT-05   | GU-05         | `bbox_from_string` happy path               | `test_geo_utils.py`       | ⚠️ Planned |
| UT-06   | GU-06–GU-07   | `bbox_from_string` error cases              | `test_geo_utils.py`       | ⚠️ Planned |
| UT-07   | GB-01–GB-04   | `build_facility_feature` + coordinate order | `test_geojson_builder.py` | ⚠️ Planned |
| UT-08   | GB-05         | Null geometry exclusion                     | `test_geojson_builder.py` | ⚠️ Planned |
| UT-09   | QP-01–QP-08   | Pydantic model validation                   | `test_query_params.py`    | ⚠️ Planned |
| UT-10   | CF-01–CF-03   | CSV formatter                               | `test_csv_formatter.py`   | ⚠️ Planned |
| UT-10a  | CF-04         | CSV `unit_of_measure` column (C-2 fix)      | `test_csv_formatter.py`   | ⚠️ Planned |
| UT-10b  | CF-05         | CSV `form_type` column (H-4 fix)            | `test_csv_formatter.py`   | ⚠️ Planned |
| UT-11   | MB-01–MB-04   | Meta response builder + fallback            | `test_meta_builder.py`    | ⚠️ Planned |
| UT-11a  | CB-11         | Color band gram-unit scaling (A-048)        | `test_color_band.py`      | ⚠️ Planned |
| UT-11b  | GB-06         | GeoJSON `unit_of_measure` property          | `test_geojson_builder.py` | ⚠️ Planned |
| UT-12   | FF-01–FF-08   | `formatReleaseQuantity` + `formatWithUnit`  | `formatters.test.ts`      | ⚠️ Planned |
| UT-12a  | FF-09–FF-10   | Unit label display for Pounds and Grams     | `formatters.test.ts`      | ⚠️ Planned |
| UT-13   | BC-01–BC-05   | `colorBandToHex` mapping                    | `colorBand.test.ts`       | ⚠️ Planned |
| UT-14   | SS-01–SS-05   | Sidebar state machine                       | `sidebarState.test.ts`    | ⚠️ Planned |
| UT-15   | BX-01–BX-03   | BBox utilities                              | `bboxUtils.test.ts`       | ⚠️ Planned |
| UT-16   | BX-04–BX-06   | Year picker logic                           | `yearPicker.test.ts`      | ⚠️ Planned |
| UT-17   | SL-01–SL-02   | ATSDR toxid correctness (7.BUG.18)          | `test_superfund_cas_lookup.py` | ✅ Implemented |
| UT-18   | SL-03         | ATSDR URL format validation (7.BUG.19)      | `test_superfund_cas_lookup.py` | ✅ Implemented |
| UT-19   | SL-04–SL-05   | CAS number coverage (7.BUG.17)              | `test_superfund_cas_lookup.py` | ✅ Implemented |
| UT-20   | SL-06         | Chemical name variants                      | `test_superfund_cas_lookup.py` | ✅ Implemented |
| UT-21   | SL-07–SL-10   | PubChem URL validation (7.BUG.21)           | `test_superfund_cas_lookup.py` | ✅ Implemented |

### Automation Status Key

| Symbol | Meaning                       |
|--------|-------------------------------|
| ✅      | Implemented and passing in CI |
| ⚠️     | Planned — not yet automated   |
| ⏸️     | Deferred to future iteration  |

