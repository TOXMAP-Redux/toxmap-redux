# TOXMAP Acceptance Tests — Gherkin Feature Specifications

**Date:** 2026-07-15  
**Last Updated:** 2026-08-17 — Updated test directory layout to reflect modular E2E step structure  
**Format:** Gherkin BDD (pytest-bdd / behave)  
**Test Runner:** `pytest` + `pytest-bdd` (API layer) · `pytest-playwright` (E2E layer)  
**Seed Data:** [TOXMAP_TEST_SEED_DATA.md](TOXMAP_TEST_SEED_DATA.md)  
**API Contract:** [TOXMAP_API_CONTRACT.md](../api/TOXMAP_API_CONTRACT.md)  
**Source Requirements:** [ADR-001](../adr/ADR-001-fastapi-postgis-react.md) · [ADR-008](../adr/ADR-008-geocoding-confidence-scoring.md) · [Tech Stack Analysis §3](../adr/TOXMAP_TECH_STACK_ANALYSIS.md)

---

## Test Directory Layout

```
tests/
├── features/
│   ├── api/
│   │   ├── facility_search.feature
│   │   ├── superfund.feature
│   │   ├── chemicals.feature
│   │   ├── demographics.feature
│   │   ├── release_trends.feature
│   │   ├── export.feature
│   │   └── metadata.feature
│   └── e2e/
│       ├── ucd_task_scenarios.feature
│       └── ux_invariants.feature
├── conftest.py          # seed DB + FastAPI test client
├── steps/
│   ├── __init__.py             # Re-exports all E2E steps
│   ├── _shared.py              # Constants and helper functions
│   ├── api_steps.py            # API test steps (@given/@when/@then for F1–F6)
│   ├── navigation_steps.py     # E2E navigation and page load
│   ├── search_steps.py         # Search form, filters, autocomplete
│   ├── results_steps.py        # Results table interactions
│   ├── facility_steps.py       # TRI facility detail drawer
│   ├── superfund_steps.py      # Superfund site detail drawer
│   ├── demographics_steps.py   # Demographics layer steps
│   ├── map_layer_steps.py      # MapLibre layer verification
│   ├── export_steps.py         # CSV download, screenshots
│   ├── regression_steps.py     # Bug regression tests (7.BUG.*, UCD-17, T-07)
│   └── stubs_steps.py          # Placeholder stub steps
└── fixtures/
    └── seed.sql         # see TOXMAP_TEST_SEED_DATA.md
```

> **Feature numbering scheme:** Features 1–6 and 9 are API layer features; Features 7 and 8 are E2E layer features.
> Feature 9 (Data Vintage Metadata) was added after the initial 1–8 numbering and assigned to Phase 2 alongside
> the other API features. In this file it appears after Feature 6 (the last API feature before E2E) to keep API
> features together, then Features 7 and 8 (E2E) follow. Feature numbers map directly to their `.feature` filenames:
> `facility_search.feature` = Feature 1, `metadata.feature` = Feature 9, `ucd_task_scenarios.feature` = Feature 7, etc.

---

## Feature 1: TRI Facility Search (API Layer)

```gherkin
# tests/features/api/facility_search.feature

Feature: TRI Facility Search
  As a user or API consumer
  I want to search for TRI facilities by location, chemical, year, and medium
  So that I can explore toxic release data programmatically

  Background:
    Given the seed database is loaded
    And the API is running at base URL "http://localhost:8000"

  # ── Happy path: radius search ───────────────────────────────────────────────

  Scenario: Radius search returns facilities within the specified distance
    When I GET "/api/v1/facilities?lat=39.2197&lon=-76.4785&radius_miles=10"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And the FeatureCollection contains a feature with property "tri_facility_id" = "21219BTHLS3RD"
    And every feature has a "total_release_lbs" property that is a number
    And every feature has a "color_band" property in ["green", "yellow", "orange", "red"]
    And every feature has a "unit_of_measure" property in ["Pounds", "Grams"]

  Scenario: Radius search excludes facilities outside the radius
    When I GET "/api/v1/facilities?lat=39.2197&lon=-76.4785&radius_miles=1"
    Then the response status is 200
    And the FeatureCollection does not contain a feature with property "tri_facility_id" = "89319BHPCP7MILE"

  # ── Chemical filter ──────────────────────────────────────────────────────────

  Scenario: Chemical filter returns only facilities releasing that chemical
    When I GET "/api/v1/facilities?lat=39.2197&lon=-76.4785&radius_miles=10&chemical=LEAD+COMPOUNDS&year=2008"
    Then the response status is 200
    And the FeatureCollection contains a feature with property "tri_facility_id" = "21219BTHLS3RD"
    And the response meta has "chemical" = "LEAD COMPOUNDS"
    And the response meta has "year" = 2008

  Scenario: Chemical filter with no matches returns empty FeatureCollection
    When I GET "/api/v1/facilities?lat=39.2197&lon=-76.4785&radius_miles=10&chemical=DIOXANE&year=2008"
    Then the response status is 200
    And the FeatureCollection contains 0 features

  # ── Medium filter ────────────────────────────────────────────────────────────

  Scenario: Medium filter restricts results to the specified release medium
    When I GET "/api/v1/facilities?lat=39.2919&lon=-115.0319&radius_miles=30&chemical=COPPER&year=2008&medium=land"
    Then the response status is 200
    And the FeatureCollection contains a feature with property "tri_facility_id" = "89319BHPCP7MILE"

  Scenario: Medium filter air excludes land-only releases
    When I GET "/api/v1/facilities?lat=39.2919&lon=-115.0319&radius_miles=30&chemical=COPPER&year=2008&medium=air"
    Then the response status is 200
    And the FeatureCollection does not contain a feature with property "tri_facility_id" = "89319BHPCP7MILE"

  # ── Viewport (bbox) scoping ──────────────────────────────────────────────────

  Scenario: Results are scoped to the viewport bounding box
    When I GET "/api/v1/facilities?lat=39.2197&lon=-76.4785&radius_miles=50&bbox=-76.6,39.1,-76.3,39.4"
    Then the response status is 200
    And every feature has coordinates within bbox [-76.6, 39.1, -76.3, 39.4]
    And the response meta has "bbox" = [-76.6, 39.1, -76.3, 39.4]

  Scenario: No empty placeholder rows in results
    When I GET "/api/v1/facilities?lat=39.2197&lon=-76.4785&radius_miles=50&bbox=-76.6,39.1,-76.3,39.4"
    Then the response status is 200
    And every feature in the FeatureCollection has a non-null "name" property
    And every feature in the FeatureCollection has a non-null geometry

  # ── State restriction ────────────────────────────────────────────────────────

  Scenario: State filter with restrict_to_state=true excludes out-of-state facilities
    When I GET "/api/v1/facilities?lat=38.9179&lon=-78.1942&radius_miles=100&state=VA&restrict_to_state=true"
    Then the response status is 200
    And every feature has property "state_code" = "VA"

  Scenario: State filter with restrict_to_state=false includes nearby out-of-state facilities
    When I GET "/api/v1/facilities?lat=38.9179&lon=-78.1942&radius_miles=100&state=VA&restrict_to_state=false"
    Then the response status is 200
    And the FeatureCollection may contain features with "state_code" != "VA"

  # ── Facility detail ──────────────────────────────────────────────────────────

  Scenario: Facility detail returns full record for a known facility
    When I GET "/api/v1/facilities/21219BTHLS3RD"
    Then the response status is 200
    And the response has "tri_facility_id" = "21219BTHLS3RD"
    And the response has "name" = "BETHLEHEM STEEL CORP - SPARROWS POINT"
    And the response has "state_code" = "MD"
    And the response has "naics_code" = "331110"
    And the response has a "location" object with "lat" and "lon" numbers

  Scenario: Facility detail for unknown ID returns 404
    When I GET "/api/v1/facilities/DOESNOTEXIST000"
    Then the response status is 404
    And the response has "detail" containing "not found"

  # ── Error cases ──────────────────────────────────────────────────────────────

  Scenario: Missing required lat/lon returns 422
    When I GET "/api/v1/facilities?radius_miles=25"
    Then the response status is 422

  Scenario: radius_miles exceeding 500 returns 400
    When I GET "/api/v1/facilities?lat=39.2&lon=-76.5&radius_miles=999"
    Then the response status is 400
    And the response has "detail" containing "radius"

  # ── Browse mode (no radius constraint) — added 2026-07-28 ────────────────────

  Scenario: Browse endpoint returns all facilities without radius
    When I GET "/api/v1/facilities/browse"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And the response meta has "browse_all" = true
    And the FeatureCollection contains more than 100 features

  Scenario: Browse endpoint with year filter
    When I GET "/api/v1/facilities/browse?year=2008"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And the FeatureCollection contains a feature with property "tri_facility_id" = "21219BTHLS3RD"
    And the FeatureCollection contains a feature with property "tri_facility_id" = "89319BHPCP7MILE"

  Scenario: Browse endpoint with state filter
    When I GET "/api/v1/facilities/browse?state=MD"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And every feature has property "state_code" = "MD"

  Scenario: Browse endpoint with chemical filter
    When I GET "/api/v1/facilities/browse?chemical=copper"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And the FeatureCollection contains a feature with property "tri_facility_id" = "89319BHPCP7MILE"
```

---

## Feature 2: Release Time Series (API Layer)

```gherkin
# tests/features/api/release_trends.feature

Feature: Release Time Series
  As a researcher
  I want to retrieve historical release data for a specific facility and chemical
  So that I can visualize 15-year trends

  Background:
    Given the seed database is loaded
    And the API is running at base URL "http://localhost:8000"

  Scenario: Time series returns 15 years of data for a seeded facility
    When I GET "/api/v1/facilities/21219BTHLS3RD/releases?from_year=2000&to_year=2008"
    Then the response status is 200
    And the response is a JSON array
    And every item has "reporting_year", "total_release_lbs", "air_release_lbs", "water_release_lbs", "land_release_lbs", "underground_release_lbs", "unit_of_measure", "form_type"
    And the array contains an item with "reporting_year" = 2008 and "total_release_lbs" = 12485.0

  Scenario: Time series with medium filter returns only that medium's totals
    When I GET "/api/v1/facilities/89319BHPCP7MILE/releases?from_year=2008&to_year=2008&medium=land"
    Then the response status is 200
    And the array contains an item with "reporting_year" = 2008 and "land_release_lbs" = 8205.0
    And the array contains an item with "reporting_year" = 2008 and "unit_of_measure" = "Pounds"
    And the array contains an item with "reporting_year" = 2008 and "form_type" = "R"

  Scenario: Time series for facility with sparse years returns only years with data
    When I GET "/api/v1/facilities/22630FRTRY0001/releases?from_year=2000&to_year=2008"
    Then the response status is 200
    And the response is a JSON array
    And the array length is greater than 0
    And no item has "total_release_lbs" = null

  Scenario: Largest release query returns top facility in a state
    When I GET "/api/v1/releases/largest?chemical=CHLORINE&state=SC"
    Then the response status is 200
    And the response has "state_code" = "SC"
    And the response has "chemical_name" = "CHLORINE"
    And the response has "total_release_lbs" = 85000.0
    And the response has "tri_facility_id" = "29801DSTLR0001"

  Scenario: Largest release query without state returns nationwide top facility
    When I GET "/api/v1/releases/largest?chemical=CHLORINE"
    Then the response status is 200
    And the response has "total_release_lbs" >= 85000.0
    And the response has "tri_facility_id" = "70663ENTGR0001"

  # ── Arithmetic invariant guard (C-1 regression) ──────────────────────────────

  Scenario: On-site release total equals sum of all medium breakdowns
    When I GET "/api/v1/facilities/21219BTHLS3RD/releases?from_year=2008&to_year=2008"
    Then the response status is 200
    And for every item in the array, "total_release_lbs" equals the sum of "air_release_lbs", "water_release_lbs", "land_release_lbs", "underground_release_lbs"

  # ── T-03 full breakdown at API level ─────────────────────────────────────────
  # (The E2E browser version is in Feature 7 T-03; this asserts raw API values.)

  Scenario: Robinson NV copper 2008 releases are entirely to land with zero other mediums
    When I GET "/api/v1/facilities/89319BHPCP7MILE/releases?from_year=2008&to_year=2008"
    Then the response status is 200
    And the array contains an item with "reporting_year" = 2008 and "total_release_lbs" = 8205.0
    And the array contains an item with "reporting_year" = 2008 and "air_release_lbs" = 0.0
    And the array contains an item with "reporting_year" = 2008 and "water_release_lbs" = 0.0
    And the array contains an item with "reporting_year" = 2008 and "land_release_lbs" = 8205.0
    And the array contains an item with "reporting_year" = 2008 and "underground_release_lbs" = 0.0

  # ── Form A coverage note ──────────────────────────────────────────────────────
  # Form A Certification records (form_type = 'A') have all-zero quantities as
  # certification artifacts, not measured zero releases. The seed data contains
  # only Form R records. Form A behavior is verified at Layer 1 (test_tri_parser.py
  # CF-05) and in the conftest.py Data Integrity Rule 3 comment. A separate
  # pytest fixture (outside seed.sql) is required to test Form A API behavior.
```

---

## Feature 3: Chemical Search & Auto-Complete (API Layer)

```gherkin
# tests/features/api/chemicals.feature

Feature: Chemical Search and Lookup
  As a user
  I want to search for chemicals by name with auto-complete
  So that I can quickly find the chemical I'm looking for

  Background:
    Given the seed database is loaded
    And the API is running at base URL "http://localhost:8000"

  Scenario: Chemical list returns all seeded chemicals
    When I GET "/api/v1/chemicals"
    Then the response status is 200
    And the response is a JSON array
    And the array contains an item with "cas_number" = "71-43-2" and "name" = "BENZENE"
    And the array contains an item with "cas_number" = "7664-41-7" and "name" = "AMMONIA"
    And the array contains an item with "name" = "LEAD COMPOUNDS" and "cas_number" = null
    And every item has "cas_number" as a string or null
    And every item has "atsdr_url" as a string or null
    And every item has "pubchem_url" as a string or null

  Scenario: Chemical auto-complete returns partial name matches
    When I GET "/api/v1/chemicals/search?q=benz"
    Then the response status is 200
    And the response is a JSON array
    And the array contains an item with "name" = "BENZENE"
    And the array length is <= 10

  Scenario: Chemical auto-complete for 1-character query returns 422
    When I GET "/api/v1/chemicals/search?q=b"
    Then the response status is 422

  Scenario: Chemical auto-complete with no matches returns empty array
    When I GET "/api/v1/chemicals/search?q=ZZZNOTACHEMICAL"
    Then the response status is 200
    And the response is an empty JSON array

  Scenario: Auto-complete response time is within SLA
    When I GET "/api/v1/chemicals/search?q=lead"
    Then the response status is 200
    And the response time is less than 100 milliseconds

  # ── Compound category null CAS (M-4 regression) ──────────────────────────────

  Scenario: Auto-complete for TRI compound category returns null cas_number
    When I GET "/api/v1/chemicals/search?q=lead"
    Then the response status is 200
    And the array contains an item with "name" = "LEAD COMPOUNDS" and "cas_number" = null
```

---

## Feature 4: Superfund Search (API Layer)

```gherkin
# tests/features/api/superfund.feature

Feature: Superfund NPL Site Search
  As an environmental health professional
  I want to search for Superfund/NPL sites by location and chemical
  So that I can explore hazardous waste sites near a given area

  Background:
    Given the seed database is loaded
    And the API is running at base URL "http://localhost:8000"

  # ── Browse mode (no radius constraint) — added 2026-07-28 ────────────────────

  Scenario: Browse endpoint returns all Superfund sites without radius
    When I GET "/api/v1/superfund/browse"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And the FeatureCollection contains a feature with property "epa_id" = "VAD070358684"

  Scenario: Browse endpoint with state filter
    When I GET "/api/v1/superfund/browse?state=VA"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And every feature has property "state_code" = "VA"

  Scenario: Browse endpoint with NPL status filter
    When I GET "/api/v1/superfund/browse?status=NPL"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And every feature has property "status" = "NPL"

  # ── Radius search ────────────────────────────────────────────────────────────

  Scenario: Superfund radius search returns sites within distance
    When I GET "/api/v1/superfund?lat=38.9179&lon=-78.1942&radius_miles=10"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And the FeatureCollection contains a feature with property "epa_id" = "VAD070358684"

  Scenario: Superfund feature has required properties
    When I GET "/api/v1/superfund?lat=38.9179&lon=-78.1942&radius_miles=10"
    Then the response status is 200
    And every feature has "epa_id", "name", "hrs_score", "status", "contaminants" properties
    And every feature has a geometry of type "Point"
    And every feature has "marker_shape" = "diamond"

  Scenario: Superfund site detail returns full record
    When I GET "/api/v1/superfund/VAD070358684"
    Then the response status is 200
    And the response has "epa_id" = "VAD070358684"
    And the response has "name" = "AVTEX FIBERS INC"
    And the response has "city" = "FRONT ROYAL"
    And the response has "state_code" = "VA"
    And the response has "hrs_score" as a number
    And the response has "contaminants" as a non-empty array
    And the response has "epa_progress_url" as a non-null string

  Scenario: Superfund search with chemical filter returns matching sites
    When I GET "/api/v1/superfund?lat=38.9179&lon=-78.1942&radius_miles=25&chemical=STYRENE"
    Then the response status is 200
    And the FeatureCollection contains a feature with property "epa_id" = "VAD070358684"

  Scenario: Superfund search outside radius returns empty collection
    When I GET "/api/v1/superfund?lat=29.7604&lon=-95.3698&radius_miles=5"
    Then the response status is 200
    And the FeatureCollection contains 0 features
```

---

## Feature 5: Demographics Overlay (API Layer)

```gherkin
# tests/features/api/demographics.feature

Feature: US Census & Health Demographics
  As a public health professional
  I want to retrieve demographic data by county and census tract
  So that I can overlay population health context on the map

  Background:
    Given the seed database is loaded
    And the API is running at base URL "http://localhost:8000"

  Scenario: County demographics returns GeoJSON polygons for a state
    When I GET "/api/v1/demographics/county?state=VA"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And every feature has geometry of type "MultiPolygon" or "Polygon"
    And every feature has "fips_code", "name", "census_year", "total_pop" properties

  Scenario: County demographics includes Warren County VA with under-18 data
    When I GET "/api/v1/demographics/county?state=VA"
    Then the response status is 200
    And the FeatureCollection contains a feature with property "fips_code" = "51187"
    And that feature has "pct_under_18" as a number between 0 and 100
    And that feature has units metadata "pct_under_18_unit" = "%"

  Scenario: County demographics for Harris County TX includes income data
    When I GET "/api/v1/demographics/county?state=TX"
    Then the response status is 200
    And the FeatureCollection contains a feature with property "fips_code" = "48201"
    And that feature has "median_income" as a positive number
    And that feature has units metadata "median_income_unit" = "$"

  Scenario: Census tract demographics returns sub-county features
    When I GET "/api/v1/demographics/tract?county_fips=51187"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And every feature has "fips_code" starting with "51187"

  Scenario: Demographics response includes units metadata for all numeric fields
    When I GET "/api/v1/demographics/county?state=VA"
    Then the response status is 200
    And the response meta has "units" object containing keys "pct_under_18", "median_income", "pct_over_65", "pct_nonwhite"
    And meta "units"."pct_under_18" = "%"
    And meta "units"."median_income" = "$"
    And meta "units"."pct_over_65" = "%"
    And meta "units"."pct_nonwhite" = "%"
    And meta "units"."cancer_mortality_female_per_100k" = "per 100,000"
```

---

## Feature 6: Data Export (API Layer)

```gherkin
# tests/features/api/export.feature

Feature: CSV and Map Data Export
  As a researcher or citizen
  I want to download search results as a CSV file
  So that I can use the data in my own analysis tools

  Background:
    Given the seed database is loaded
    And the API is running at base URL "http://localhost:8000"

  Scenario: CSV export returns valid CSV with correct headers
    When I GET "/api/v1/export/csv?lat=39.2197&lon=-76.4785&radius_miles=10&year=2008"
    Then the response status is 200
    And the response Content-Type is "text/csv"
    And the response Content-Disposition contains "attachment"
    And the CSV has headers: "tri_facility_id,name,address,city,state_code,chemical_name,reporting_year,total_release_lbs,air_release_lbs,water_release_lbs,land_release_lbs,underground_release_lbs,unit_of_measure,form_type"

  Scenario: CSV export contains only facilities within radius
    When I GET "/api/v1/export/csv?lat=39.2197&lon=-76.4785&radius_miles=10&year=2008&chemical=LEAD+COMPOUNDS"
    Then the response status is 200
    And the CSV contains a row with "tri_facility_id" = "21219BTHLS3RD"
    And the CSV contains a row with "total_release_lbs" = "12485.0"
    And the CSV contains a row with "unit_of_measure" = "Pounds"
    And the CSV contains a row with "form_type" = "R"
    And release quantity values in the CSV are comma-formatted when rendered

  Scenario: CSV export streams (does not buffer full response)
    When I GET "/api/v1/export/csv?lat=39.2197&lon=-76.4785&radius_miles=500"
    Then the response status is 200
    And the response uses Transfer-Encoding "chunked" or has a Content-Length header
```

---

## Feature 9: Data Vintage Metadata (API Layer)

> Tests for `GET /api/v1/meta` — the dev-mode endpoint that tells the React app what TRI data is loaded and its EPA vintage. See [TOXMAP_API_CONTRACT.md §17](../api/TOXMAP_API_CONTRACT.md) and [TOXMAP_TEST_SEED_DATA.md §10](TOXMAP_TEST_SEED_DATA.md) for seed behavior.

```gherkin
# tests/features/api/metadata.feature

Feature: Data Vintage Metadata Endpoint
  As the React frontend
  I want to query the server for the currently loaded TRI data vintage
  So that I can display data currency to users and populate the year-picker

  Background:
    Given the seed database is loaded
    And the API is running at base URL "http://localhost:8000"

  Scenario: Meta endpoint returns 200 with valid schema
    When I GET "/api/v1/meta"
    Then the response status is 200
    And the response has "source" = "fastapi-dev"
    And the response has "vintage_label" as a non-null string
    And the response has "available_years" as a non-empty array
    And the response has "latest_year" as a positive integer
    And the response has "total_facility_count" as a positive integer
    And the response has "total_release_event_count" as a positive integer

  Scenario: Meta endpoint available_years reflects seeded release events
    When I GET "/api/v1/meta"
    Then the response status is 200
    And the response "available_years" contains 2006
    And the response "available_years" contains 2007
    And the response "available_years" contains 2008

  Scenario: Meta endpoint latest_year is the max year in seeded release events
    When I GET "/api/v1/meta"
    Then the response status is 200
    And the response has "latest_year" = 2008

  Scenario: Meta endpoint vintage_label falls back to "unknown" when no ingestion metadata exists
    When I GET "/api/v1/meta"
    Then the response status is 200
    And the response has "vintage_label" = "unknown"
```

---

## Feature 7: UCD 2011 Task Scenarios — E2E (Playwright Layer)

> These are the 9 original usability study task scenarios. Each must pass against a seeded database with the Playwright browser driver. See [TOXMAP_TEST_SEED_DATA.md](TOXMAP_TEST_SEED_DATA.md) for fixture values.

```gherkin
# tests/features/e2e/ucd_task_scenarios.feature

Feature: UCD 2011 Task Scenarios
  As a real user performing realistic tasks
  I want the application to return accurate results and navigate smoothly
  So that the clone faithfully reproduces the original ToxMap's core value

  Background:
    Given the application is running at "http://localhost:3000"
    And the seed database is loaded

  # ── T-01: Lead compounds near Sparrows Point, MD ─────────────────────────────

  Scenario: T-01 Parent finds lead-compound TRI facility near Sparrows Point MD
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I type "LEAD COMPOUNDS" into the chemical field
    And I select year "2008"
    And I click "Search"
    Then the map shows at least one facility marker near coordinates 39.2197, -76.4785
    And the results sidebar shows "BETHLEHEM STEEL CORP - SPARROWS POINT"
    When I click on "BETHLEHEM STEEL CORP - SPARROWS POINT" in the results
    Then the facility detail panel opens
    And the detail panel shows "12,485 lbs" for the year 2008
    And the release quantities are formatted with commas

  # ── T-02: Superfund chemical list accessible ─────────────────────────────────

  Scenario: T-02 Superfund-reportable chemical list accessible within 2 clicks
    Given I am on the map page
    When I click the "Search Chemical Releases by Location" panel trigger
    Then the search panel is visible
    When I click the "Superfund" dataset option
    Then a list or searchable dropdown of Superfund-reportable chemicals is visible
    And the chemical list contains "STYRENE"
    And the total number of clicks from map page to chemical list is <= 2

  # ── T-03: Copper > 8,000 lbs in eastern Nevada ───────────────────────────────

  Scenario: T-03 Copper releases over 8000 lbs found near Ely Nevada
    Given I am on the map page
    When I type "Ruth, NV" into the location field
    And I type "COPPER" into the chemical field
    And I select year "2008"
    And I click "Search"
    Then the results sidebar shows "ROBINSON NEVADA MINING CO"
    When I click on "ROBINSON NEVADA MINING CO"
    Then the facility detail panel opens
    And the detail panel shows "8,205 lbs" total release
    And the release distribution chart shows the "Land" medium as the largest bar
    And the "Air" medium bar is absent or zero

  # ── T-04: Styrene Superfund near Front Royal VA ───────────────────────────────

  Scenario: T-04 Styrene Superfund site found near Front Royal VA
    Given I am on the map page
    When I type "Front Royal, VA" into the location field
    And I select dataset "Superfund"
    And I type "STYRENE" into the chemical field
    And I click "Search"
    Then the map shows a Superfund diamond marker near coordinates 38.9179, -78.1942
    And the results sidebar shows "AVTEX FIBERS INC"
    When I click on the "AVTEX FIBERS INC" Superfund marker
    Then the Superfund detail panel opens
    And the detail panel shows EPA ID "VAD070358684"
    And the detail panel shows a contaminants list containing "STYRENE"
    And the detail panel shows a link to the EPA site progress profile

  # ── T-05: TRI styrene sites near Front Royal + under-18 overlay ──────────────

  Scenario: T-05 TRI styrene sites and under-18 demographic overlay work together
    Given I am on the map page
    When I search for TRI facilities releasing "STYRENE" near "Front Royal, VA" in year "2008"
    Then at least one TRI facility marker is visible on the map
    And the results sidebar shows TRI results without a simultaneous Map Contents panel
    When I open the "US Census & Health Data" panel
    And I select "Population" > "% Under 18" > "Census 2000"
    Then the map shows county-level color shading
    And the sidebar switches to show the demographic panel only
    And the TRI facility markers remain visible on the map
    And a legend is visible with inline percentage values and the unit "%"

  # ── T-06: Income demographic layer ──────────────────────────────────────────

  Scenario: T-06 Income range overlay applied units shown and layer removable
    Given I am on the map page
    When I open the "US Census & Health Data" panel
    And I select "Income" > "Median Household Income" > "Census 2000"
    Then the map shows county-level color shading
    And the legend shows dollar values with the unit "$"
    And each legend range label includes a "$" symbol
    When I click "Clear layer" in the demographic panel
    Then the county color shading is removed from the map
    And the legend disappears

  # ── T-07: Largest chlorine release SC vs. nationwide ────────────────────��───

  Scenario: T-07 Largest chlorine release in SC and nationwide are both queryable
    Given I am on the map page
    When I search for "CHLORINE" with state "SC" and "Limit to state" checked
    Then the results show only SC facilities
    And the top result has "85,000 lbs" total release
    And the top result facility is "BORDEN CHEMICALS AND PLASTICS INC"
    When I uncheck "Limit to state"
    And I click "Search"
    Then the top result has total release greater than "85,000 lbs"
    And the top result facility is "ENTERPRISE GAS PROCESSING LLC"

  # ── T-08: CDC ToxFAQ link for ammonia ───────────────────────────────────────

  Scenario: T-08 CDC ToxFAQ for ammonia opens without losing map state
    Given I am on the map page at coordinates lat=29.7604 lon=-95.3698 zoom=10
    When I open the "Search Chemical Releases by Location" panel
    And I click "Chemical Information" for "AMMONIA"
    Then a new browser tab opens with a URL containing "atsdr.cdc.gov" or "ammonia"
    And the original map tab remains open at the same coordinates and zoom level
    And the search state is preserved in the original tab

  # ── T-09: Benzene + cancer mortality co-occurrence ───────────────────────────

  Scenario: T-09 Benzene releases and cancer mortality overlay with disclaimer
    Given I am on the map page
    When I search for "BENZENE" near "Houston, TX" in year "2008"
    Then at least two benzene TRI facility markers appear in the Houston area
    When I open the "US Census & Health Data" panel
    And I select "Mortality" > "Cancer Mortality" > "Female" > "Census 2000"
    Then the map shows cancer mortality choropleth shading
    And a co-occurrence disclaimer is visible reading "Correlation does not imply causation"
    When I switch to the "Population" tab in the demographic panel
    Then the co-occurrence disclaimer is NOT visible
```

---

## Feature 8: UX Design Invariants — E2E (Playwright Layer)

```gherkin
# tests/features/e2e/ux_invariants.feature

Feature: UX Design Invariants
  These invariants must hold across ALL application states
  They are derived from the UCD Inc. 2011 usability study critical findings

  Background:
    Given the application is running at "http://localhost:3000"
    And the seed database is loaded

  # ── Invariant 1: Single sidebar ──────────────────────────────────────────────

  Scenario: Map Contents and Search Results are never visible simultaneously
    Given I am on the map page in browse mode
    Then the Map Contents panel is visible
    And the Search Results panel is NOT visible
    When I perform a search for "BENZENE" near "Houston, TX"
    Then the Search Results panel is visible
    And the Map Contents panel is NOT visible
    And there is exactly 1 active sidebar panel on screen

  # ── Invariant 2: No empty table rows ────────────────────────────────────────

  Scenario: Search results table never contains empty placeholder rows
    When I perform a search for "LEAD COMPOUNDS" near "Sparrows Point, MD"
    Then every row in the results table has a facility name
    And every row in the results table has a numeric release amount
    And no row is visually empty or grayed out

  # ── Invariant 3: State restriction actually filters ──────────────────────────

  Scenario: State restriction checkbox filters results to selected state only
    Given I search for "BENZENE" with state "TX" and "Limit to state" unchecked
    Then results may include facilities outside TX
    When I check "Limit to state"
    And I click "Search"
    Then all facility markers on the map are in Texas
    And the results table shows no facilities with state other than "TX"

  # ── Invariant 4: Correct panel labels ───────────────────────────────────────

  Scenario: Search panel is labeled correctly per UCD 2011 recommendation
    Given I am on the map page
    Then no element with text "Quick Search" is visible
    And an element with text "Search Chemical Releases by Location" is visible

  Scenario: Demographics panel is labeled correctly per UCD 2011 recommendation
    Given I am on the map page
    Then no element with text "Demographics" is visible as a primary navigation label
    And an element with text "US Census & Health Data" is visible

  # ── Invariant 5: Demographic legend inline ───────────────────────────────────

  Scenario: Demographic legend values are visible without mouse interaction
    Given I apply the "% Under 18" demographic layer
    Then the legend is visible on screen
    And the legend shows at least 3 color-range entries
    And each legend entry has a visible numeric value without hovering
    And each legend entry includes the unit "%"

  # ── Invariant 6: Distinct site type icons ───────────────────────────────────

  Scenario: TRI and Superfund icons are visually distinct
    Given I have both TRI and Superfund layers active
    Then TRI facility markers use a circle shape
    And Superfund NPL markers use a diamond shape
    And no TRI marker uses the same shape and color as a Superfund marker

  # ── Invariant 7: Latest year label ──────────────────────────────────────────

  Scenario: Most recent data year is labeled as latest year in layer toggles
    Given I am on the map page in browse mode
    Then the layer toggle for the most recent TRI year includes the text "(latest year)"

  # ── Invariant 8: Comma-formatted numbers ────────────────────────────────────

  Scenario: All release quantities are displayed with comma formatting
    When I search for "COPPER" near "Ruth, NV" in year "2008"
    And I click on "ROBINSON NEVADA MINING CO"
    Then the detail panel shows "8,205" not "8205"
    And no numeric release quantity anywhere on screen is unformatted (no 4+ digit number without commas)

  # ── Invariant 9: Facility popup close link ───────────────────────────────────

  Scenario: Facility popup always has an accessible close link at the bottom
    When I click on any TRI facility marker on the map
    Then a facility popup or detail panel opens
    And the popup contains a close control at the BOTTOM of the panel
    And clicking the bottom close control dismisses the popup

  # ── Invariant 10: Co-occurrence disclaimer scope ─────────────────────────────

  Scenario: Co-occurrence disclaimer appears only on mortality demographic tabs
    Given I apply the "Cancer Mortality" demographic layer
    Then the text "Correlation does not imply causation" is visible

    When I switch to the "% Under 18" demographic layer
    Then the text "Correlation does not imply causation" is NOT visible

    When I switch to "Median Household Income"
    Then the text "Correlation does not imply causation" is NOT visible

  # ── Invariant 11: Data vintage indicator ──────────────────────────────────────

  Scenario: Data vintage label is visible in the map footer on load
    Given I am on the map page
    Then an element with data-testid "data-vintage-label" is visible
    And the text content of "data-vintage-label" is not empty
    And the text content of "data-vintage-label" does not contain "null" or "undefined"

  # ── Invariant 12: Release unit labels match unit_of_measure ──────────────────

  Scenario: Release quantity display shows "lbs" unit label for Pounds records
    When I search for "COPPER" near "Ruth, NV" in year "2008"
    And I click on "ROBINSON NEVADA MINING CO"
    Then the detail panel shows the text "8,205 lbs" or a "lbs" label adjacent to "8,205"
    And each medium breakdown value in the detail panel has a unit label matching the facility's unit_of_measure

  Scenario: Facility search results list displays unit labels next to release quantities
    When I search for "LEAD COMPOUNDS" near "Sparrows Point, MD" in year "2008"
    Then every row in the results table that shows a release quantity also shows a unit label
    And no release quantity appears without an adjacent unit label

  # ── Invariant 13: Geocoding confidence feedback (ADR-008) ────────────────────
  # Users must see the resolved canonical address and a confidence indicator
  # to set appropriate expectations for address-level geocoding accuracy.

  Scenario: Resolved geocode location is displayed with confidence badge
    Given I am on the map page
    When I type "100 Mill Rd, Port Townsend, WA" into the location field
    And I click "Search"
    Then the resolved location panel is visible
    And the resolved location panel shows a canonical address
    And a geocode confidence badge is visible (Exact, High, Approximate, or Low)

  Scenario: Low-confidence geocodes show a warning message
    Given I am on the map page
    When I type "100 Mill Rd" into the location field (ambiguous query)
    And I click "Search"
    Then the resolved location panel shows "Approximate" or "Low" confidence
    And a warning message is visible suggesting to add city/state

  # ── Regression: Geocoding Confidence Scoring (7.BUG.25) ───────────────────────
  # Full address → high confidence; partial address → approximate + warning.
  # See ADR-008 for scoring algorithm and confidence thresholds.

  Scenario: Regression — Full address geocodes with high confidence
    Given I am on the map page
    When I type "100 Mill Rd, Port Townsend, WA" into the location field
    And I click "Search"
    Then the geocode confidence badge shows "High" or "Exact"
    And the resolved address contains "Port Townsend"

  Scenario: Regression — Partial address shows approximate confidence warning
    Given I am on the map page
    When I type "100 Mill Rd" into the location field
    And I click "Search"
    Then the geocode confidence badge shows "Approximate" or "Low"
    And the approximate location warning is visible

  Scenario: Regression — Resolved location shows canonical address from Photon
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    Then the resolved location panel shows a different address than "Sparrows Point, MD"
    And the resolved address contains "MD" or "Maryland"
```

---

## Step Implementation Hints

### API Step Stubs (`tests/steps/api_steps.py`)

```python
# pytest-bdd step implementations sketch
#
# IMPORTANT: The `context` fixture (a plain dict) is defined in conftest.py.
# It is function-scoped and provides a shared mutable namespace between step
# functions within a single scenario. Never use module-level state here.
#
# IMPORTANT: The `api_client` fixture (FastAPI TestClient) is defined in conftest.py.
# Step functions below that accept `api_client` as a parameter receive that fixture.
# The "the API is running at base URL" step is a no-op — it documents the Gherkin
# Background but the actual client comes from conftest.py's TestClient fixture.

import json
import pytest
from pytest_bdd import given, when, then, parsers

@given("the seed database is loaded")
def given_seed_db_loaded(seed_db):
    """Delegates to the seed_db fixture in conftest.py.
    The fixture handles INSERT and teardown TRUNCATE automatically."""
    pass  # seed_db fixture runs before this step; nothing extra needed

@given(parsers.parse('the API is running at base URL "{base_url}"'))
def given_api_base_url(base_url):
    """No-op: the api_client fixture (TestClient) is already configured in conftest.py.
    This step exists only to make the Gherkin Background self-documenting."""
    pass

@when(parsers.parse('I GET "{path}"'))
def get_request(api_client, path, context):
    context["response"] = api_client.get(path)

@then(parsers.parse("the response status is {code:d}"))
def check_status(context, code):
    assert context["response"].status_code == code

@then("the response is a GeoJSON FeatureCollection")
def check_geojson(context):
    body = context["response"].json()
    assert body["type"] == "FeatureCollection"
    assert isinstance(body["features"], list)

@then(parsers.parse('the response time is less than {ms:d} milliseconds'))
def check_response_time(context, ms):
    assert context["response"].elapsed.total_seconds() * 1000 < ms

@then(parsers.parse('every feature has coordinates within bbox {bbox}'))
def check_bbox(context, bbox):
    min_lon, min_lat, max_lon, max_lat = json.loads(bbox)
    for feature in context["response"].json()["features"]:
        lon, lat = feature["geometry"]["coordinates"]
        assert min_lon <= lon <= max_lon
        assert min_lat <= lat <= max_lat
```

### E2E Step Implementations (`tests/steps/`)

E2E steps are organized into domain-specific modules. Import all steps via:
```python
from tests.steps import *
```

Modules:
- `navigation_steps.py` — Given steps, page load, navigation
- `search_steps.py` — Search form, filters, autocomplete
- `results_steps.py` — Results table interactions
- `facility_steps.py` — TRI facility detail drawer
- `superfund_steps.py` — Superfund site detail drawer
- `demographics_steps.py` — Demographics layer steps
- `map_layer_steps.py` — MapLibre layer verification
- `export_steps.py` — CSV download, screenshots
- `regression_steps.py` — Bug regression tests
- `stubs_steps.py` — Placeholder stub steps

```python
# Example step implementations sketch
#
# IMPORTANT: The `page` fixture is provided by pytest-playwright automatically.
# Configuration lives entirely in pyproject.toml — no playwright.config.ts is used.
#   [tool.pytest.ini_options]
#   addopts = "--base-url http://localhost:3000 --screenshot only-on-failure"
#
# To run against a different environment:
#   pytest tests/features/e2e/ --base-url http://staging.example.com
# Browser matrix:
#   pytest tests/features/e2e/ --browser chromium --browser firefox --browser webkit

from pytest_bdd import given, when, then, parsers
from playwright.sync_api import Page

@given("I am on the map page")
def navigate_to_map(page: Page):
    # pytest-playwright sets the base URL via --base-url (configured in pyproject.toml addopts).
    # Use page.goto("/") to navigate to root — do NOT use a separate browser_base_url fixture,
    # which would conflict with pytest-playwright's own base_url injection and duplicate the URL.
    page.goto("/")
    page.wait_for_selector("[data-testid='map-container']")

@when(parsers.parse('I type "{text}" into the location field'))
def type_location(page: Page, text: str):
    page.fill("[data-testid='location-input']", text)

@when(parsers.parse('I type "{text}" into the chemical field'))
def type_chemical(page: Page, text: str):
    page.fill("[data-testid='chemical-input']", text)
    # Wait for autocomplete
    page.wait_for_selector("[data-testid='chemical-autocomplete-option']", timeout=1000)
    page.click(f"[data-testid='chemical-autocomplete-option']:has-text('{text}')")

@then("the Map Contents panel is NOT visible")
def map_contents_hidden(page: Page):
    assert not page.is_visible("[data-testid='map-contents-panel']")

@then("there is exactly 1 active sidebar panel on screen")
def single_sidebar(page: Page):
    panels = page.query_selector_all("[data-testid='sidebar-panel'][data-active='true']")
    assert len(panels) == 1
```

