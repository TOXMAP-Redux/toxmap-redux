# Test Plan
## Service: `toxmap`

- **Author(s):** Victor Cannestro
- **Maintained By:** Quality Engineering Team
- **Version:** 1.0
- **Last Updated:** 2026-07-17
- **Test Type:** Integration Test (with real PostGIS database and FastAPI request-response interactions)

---

## Table of Contents
1. [Scope & Objectives](#1-scope--objectives)
2. [Test Architecture](#2-test-architecture)
3. [Test Data](#3-test-data)
4. [Test Scenarios](#4-test-scenarios)
5. [Entry & Exit Criteria](#5-entry--exit-criteria)
6. [Out of Scope](#6-out-of-scope)
7. [Appendix A — Automation Traceability](#appendix-a--automation-traceability)
8. [Appendix B — Seed Data Reference](#appendix-b--seed-data-reference)

---

## 1. Scope & Objectives

### Scope
This plan covers integration-level testing of the TOXMAP FastAPI backend against a real PostgreSQL 16 + PostGIS 3.4 database loaded with deterministic seed data. Tests exercise the full request-response stack: query parameter validation → repository SQL execution → service-layer transformation → serialized HTTP response. No browser is involved.

### Functionality Under Test

| Endpoint Group | Endpoints | Purpose |
|---------------|-----------|---------|
| Facility search | `GET /api/v1/facilities` | Radius search, chemical/medium/bbox/state filters, color band, null-geometry exclusion |
| Facility detail | `GET /api/v1/facilities/{id}` | Single facility record with complete field set |
| Release time series | `GET /api/v1/facilities/{id}/releases`, `GET /api/v1/releases/largest` | Multi-year trend data, medium filter, state vs. nationwide largest |
| Chemicals | `GET /api/v1/chemicals`, `GET /api/v1/chemicals/search` | Full list, autocomplete, SLA |
| Superfund | `GET /api/v1/superfund`, `GET /api/v1/superfund/{epa_id}` | NPL radius search, chemical filter, site detail |
| Demographics | `GET /api/v1/demographics/county`, `GET /api/v1/demographics/tract` | GeoJSON polygons, units metadata |
| CSV export | `GET /api/v1/export/csv` | Streaming CSV, headers, row content |
| Data vintage metadata | `GET /api/v1/meta` | Source, vintage fallback, available years, counts |

### Three-Phase Data Flow

```
Phase 1: Read                Phase 2: Process              Phase 3: Emit
┌──────────────────┐        ┌─────────────────────┐       ┌──────────────────┐
│  HTTP Request    │        │  PostGIS spatial    │       │  HTTP Response   │
│  (FastAPI        │───────▶│  query execution    │──────▶│  (GeoJSON /      │
│   TestClient)    │        │  + service logic    │       │   CSV / JSON)    │
└──────────────────┘        └─────────────────────┘       └──────────────────┘
     │                              │                              │
  Query params              ST_DWithin, ST_Within          Response body
  validation                color_band, filtering          + status code
                            coordinate serialization       + headers
```

---

## 2. Test Architecture

### Approach
Tests use `FastAPI TestClient` (synchronous HTTPX) against an app instance wired to the `toxmap_test` PostGIS database. The `seed_db` pytest fixture loads `tests/fixtures/seed.sql` before each test and TRUNCATEs all tables after. Tests MUST run single-threaded (`-p no:xdist`).

```
[ FastAPI TestClient ]
│
│  GET "/api/v1/facilities?lat=39.2197&lon=-76.4785&radius_miles=10&chemical=LEAD+COMPOUNDS&year=2008"
▼
[ FastAPI Router → FacilityService → FacilityRepository ]
│
│  SELECT ... FROM facilities JOIN release_events
│  WHERE ST_DWithin(location, ST_MakePoint(-76.4785, 39.2197)::geography, 16093.44)
│    AND chemical_name ILIKE '%LEAD COMPOUNDS%'
│    AND reporting_year = 2008
▼
[ PostgreSQL 16 + PostGIS 3.4 — toxmap_test database ]
│
│  Returns rows including:  tri_facility_id="21219BTHLS3RD", total_release_lbs=12485.0
▼
[ FacilityService.search() ]
│  color_band = "orange"  (12485 is in 10k–99,999 range)
│  geometry = {"type":"Point","coordinates":[-76.4785, 39.2197]}
▼
[ HTTP 200 — GeoJSON FeatureCollection ]
│  assert features[0].properties["tri_facility_id"] == "21219BTHLS3RD"
│  assert features[0].properties["color_band"] == "orange"
```

### Test Infrastructure

| Component | Strategy |
|-----------|----------|
| PostgreSQL + PostGIS | `postgis/postgis:16-3.4` Docker container (`docker compose up -d postgres`) |
| Test database | `toxmap_test` — separate from dev DB; created fresh per CI run |
| Seed data | `tests/fixtures/seed.sql` — loaded by `seed_db` fixture before each test |
| FastAPI client | `fastapi.testclient.TestClient` (wraps `httpx.Client`) |
| DB fixture driver | `psycopg2-binary` (sync) — distinct from app's `asyncpg` driver |
| Parallel execution | **Disabled** (`addopts = "-p no:xdist"`) — TRUNCATE races corrupt state |

### Test Execution Lifecycle

```
BEFORE_EACH
├─ TRUNCATE all tables (FK order)
└─ Load tests/fixtures/seed.sql

TEST
├─ Setup: optionally manipulate seed data via direct SQL
├─ Trigger: api_client.get("/api/v1/...")
└─ Verify: assert response.status_code, response.json()

AFTER_EACH
└─ TRUNCATE all tables (FK order)
```

### Key DB Columns Asserted

| Table | Asserted Fields |
|-------|----------------|
| `facilities` | `tri_facility_id`, `name`, `city`, `state_code`, `naics_code`, `location` (WKT) |
| `release_events` | `reporting_year`, `total_release_lbs`, `air_release_lbs`, `water_release_lbs`, `land_release_lbs`, `underground_release_lbs` |
| `chemicals` | `cas_number`, `name`, `atsdr_url`, `pubchem_url` |
| `superfund_sites` | `epa_id`, `name`, `hrs_score`, `status`, `contaminants`, `epa_progress_url` |
| `census_county` | `fips_code`, `name`, `pct_under_18`, `median_income`, `boundary` (polygon) |

---

## 3. Test Data

All integration tests use the **7 seeded facilities, 14 release events, 2 Superfund sites, and 3 census counties** defined in `tests/fixtures/seed.sql`. For complete fixture values, entity IDs, and known-good assertion values, see [TOXMAP_TEST_SEED_DATA.md](TOXMAP_TEST_SEED_DATA.md).

| Seed Set | Records | Key Scenarios |
|----------|---------|---------------|
| Facilities | 7 | T-01 (Bethlehem MD), T-03 (Robinson NV), T-05 (Front Royal VA), T-07 (Borden SC + Enterprise LA), T-09 (ExxonMobil + LyondellBasell TX) |
| Release events | 14 | Multi-year trends (2006–2008); UCD 2011 exact values for T-01 and T-03 |
| Superfund sites | 2 | T-04 AVTEX FIBERS `VAD070358684` (UCD 2011 exact) |
| Census counties | 3 | T-05 Warren County VA `51187`; T-09 Harris County TX `48201`; T-07 Aiken County SC `45003` |

> ⚠️ **Date Maintenance:** The seed SQL contains no date-sensitive fields. However, if `reportingYear`-based filters are added to future queries, review seed years before test cycles.

---

## 4. Test Scenarios

### 4.1 Facility Search — Radius, Filters, Color Band

**File:** `tests/integration/test_facility_search.py`
**Prefix:** `FSR` (Facility Search Results)

| ID     | Scenario                              | Request                                              | Assertion                                                             |
|--------|---------------------------------------|------------------------------------------------------|-----------------------------------------------------------------------|
| FSR-01 | Radius includes known facility        | `?lat=39.2197&lon=-76.4785&radius_miles=10`          | `tri_facility_id="21219BTHLS3RD"` in features                        |
| FSR-02 | Radius excludes distant facility      | `?lat=39.2197&lon=-76.4785&radius_miles=1`           | `tri_facility_id="89319BHPCP7MILE"` NOT in features                  |
| FSR-03 | Max radius 500 allowed                | `radius_miles=500`                                   | HTTP 200                                                              |
| FSR-04 | Chemical filter narrows results       | `&chemical=LEAD+COMPOUNDS&year=2008`                 | Only facilities releasing lead compounds                             |
| FSR-05 | Chemical filter with no matches       | `&chemical=DIOXANE&year=2008`                        | HTTP 200; `features == []`                                           |
| FSR-06 | Medium filter land includes Robinson  | `&chemical=COPPER&year=2008&medium=land`             | `tri_facility_id="89319BHPCP7MILE"` in features                      |
| FSR-07 | Medium filter air excludes Robinson   | `&medium=air` (Robinson has zero air release)        | `tri_facility_id="89319BHPCP7MILE"` NOT in features                  |
| FSR-08 | BBox scoping filters to viewport      | `&bbox=-76.6,39.1,-76.3,39.4`                       | All features have coordinates within bbox                            |
| FSR-09 | State restrict=true                   | `&state=VA&restrict_to_state=true`                   | All features have `state_code=="VA"`                                 |
| FSR-10 | State restrict=false                  | `&state=VA&restrict_to_state=false`                  | Features from multiple states possible                               |
| FSR-11 | Color band applied                    | Bethlehem Steel `total_release_lbs=12485.0`          | `color_band=="orange"` in response                                   |
| FSR-12 | No null geometry in response          | Any search with results                              | Zero features with `geometry==null`                                  |
| FSR-13 | No null name in response              | Any search with results                              | Zero features with `properties.name==null`                           |

### 4.2 Facility Search — Validation Errors

**File:** `tests/integration/test_facility_search.py`
**Prefix:** `FSE` (Facility Search Errors)

| ID     | Scenario              | Request                                    | Assertion                             |
|--------|-----------------------|--------------------------------------------|---------------------------------------|
| FSE-01 | Missing `lat`         | `?radius_miles=25`                         | HTTP 422                              |
| FSE-02 | `radius_miles` > 500  | `?lat=39.2&lon=-76.5&radius_miles=501`     | HTTP 400; `"radius"` in `detail`      |

### 4.3 Facility Detail

**File:** `tests/integration/test_facility_detail.py`
**Prefix:** `FDT` (Facility DeTail)

| ID     | Scenario                      | Request                                     | Assertion                                                                                         |
|--------|-------------------------------|---------------------------------------------|---------------------------------------------------------------------------------------------------|
| FDT-01 | Known facility returns 200    | `GET /api/v1/facilities/21219BTHLS3RD`      | HTTP 200; all required fields present                                                             |
| FDT-02 | All fields complete           | Same                                        | `tri_facility_id`, `name`, `state_code`, `naics_code`, `location.lat`, `location.lon` present    |
| FDT-03 | Unknown facility returns 404  | `GET /api/v1/facilities/DOESNOTEXIST000`    | HTTP 404; `"not found"` in `detail`                                                               |

### 4.4 Release Time Series

**File:** `tests/integration/test_release_trends.py`
**Prefix:** `RLS` (ReLease Series)

| ID     | Scenario                          | Request                                                                     | Assertion                                                                                                                                  |
|--------|-----------------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| RLS-01 | Returns array                     | `GET /api/v1/facilities/21219BTHLS3RD/releases`                             | Response is JSON array                                                                                                                     |
| RLS-02 | All required fields present       | Same                                                                        | Each item has all 6 release medium fields                                                                                                  |
| RLS-03 | T-01 exact value                  | `?from_year=2008&to_year=2008`                                              | Item with `reporting_year=2008` has `total_release_lbs=12485.0`                                                                            |
| RLS-04 | T-03 land medium filter           | `/89319BHPCP7MILE/releases?medium=land`                                     | `land_release_lbs=8205.0` in 2008 item                                                                                                     |
| RLS-05 | Sparse years — no nulls           | Any multi-year request                                                      | No item has `total_release_lbs==null`                                                                                                      |
| RLS-06 | Largest in state                  | `GET /api/v1/releases/largest?chemical=CHLORINE&state=SC`                   | `total_release_lbs=85000.0`, `state_code="SC"`                                                                                             |
| RLS-07 | Largest nationwide                | `GET /api/v1/releases/largest?chemical=CHLORINE`                            | `total_release_lbs>=85000.0`, `tri_facility_id="70663ENTGR0001"`                                                                           |

### 4.5 Chemicals

**File:** `tests/integration/test_chemicals.py`
**Prefix:** `CHM` (CHeMicals)

| ID     | Scenario                         | Request                                      | Assertion                                                                                |
|--------|----------------------------------|----------------------------------------------|------------------------------------------------------------------------------------------|
| CHM-01 | Full list returns all seeded     | `GET /api/v1/chemicals`                      | All 6 seeded chemicals present                                                           |
| CHM-02 | List includes CAS numbers + URLs | Same                                         | Each item has `cas_number`, `atsdr_url` (string or null), `pubchem_url` (string or null) |
| CHM-03 | Autocomplete partial match       | `GET /api/v1/chemicals/search?q=benz`        | Response contains item with `name="BENZENE"`                                             |
| CHM-04 | Autocomplete max 10 results      | `?q=lead`                                    | Result count ≤ 10                                                                        |
| CHM-05 | Autocomplete no match            | `?q=ZZZNOTACHEMICAL`                         | Response is `[]`                                                                         |
| CHM-06 | Autocomplete SLA                 | `?q=lead`                                    | Response time < 100ms (soft — logged, not failed)                                        |
| CHM-07 | Autocomplete 1-char query        | `?q=b`                                       | HTTP 422                                                                                 |

### 4.6 Superfund

**File:** `tests/integration/test_superfund.py`
**Prefix:** `SUP` (SUPerfund)

| ID     | Scenario                            | Request                                                | Assertion                                                                       |
|--------|-------------------------------------|--------------------------------------------------------|---------------------------------------------------------------------------------|
| SUP-01 | Radius includes AVTEX               | `?lat=38.9179&lon=-78.1942&radius_miles=10`            | Feature with `epa_id="VAD070358684"`                                            |
| SUP-02 | Required properties present         | Same                                                   | Every feature has `epa_id`, `name`, `hrs_score`, `status`, `contaminants`       |
| SUP-03 | Geometry type                       | Same                                                   | Every feature has `geometry.type=="Point"`                                      |
| SUP-04 | Site detail — all fields            | `GET /api/v1/superfund/VAD070358684`                   | All fields; `contaminants` non-empty; `epa_progress_url` non-null string        |
| SUP-05 | Chemical filter match               | `?chemical=STYRENE`                                    | AVTEX included (has STYRENE as contaminant)                                     |
| SUP-06 | Outside radius — empty              | Remote coordinates                                     | `features == []`                                                                |

### 4.7 Demographics

**File:** `tests/integration/test_demographics.py`
**Prefix:** `DEM` (DEMographics)

| ID     | Scenario                           | Request                                              | Assertion                                                                       |
|--------|------------------------------------|------------------------------------------------------|---------------------------------------------------------------------------------|
| DEM-01 | County returns GeoJSON             | `GET /api/v1/demographics/county?state=VA`           | GeoJSON FeatureCollection                                                       |
| DEM-02 | Geometry type                      | Same                                                 | All features are `Polygon` or `MultiPolygon`                                    |
| DEM-03 | Warren County pct_under_18         | Same, FIPS `51187`                                   | `pct_under_18==24.7`                                                            |
| DEM-04 | Warren County units                | Same                                                 | `meta.units.pct_under_18=="%"`                                                  |
| DEM-05 | Harris County income               | `?state=TX`, FIPS `48201`                            | `median_income > 0`                                                             |
| DEM-06 | Income units                       | Same                                                 | `meta.units.median_income=="$"`                                                 |
| DEM-07 | All units keys present             | `?state=VA`                                          | `meta.units` has `pct_under_18`, `median_income`, `pct_over_65`, `pct_nonwhite`, `cancer_mortality_female_per_100k` |
| DEM-08 | Census tract sub-county            | `GET /api/v1/demographics/tract?county_fips=51187`   | All FIPS codes start with `"51187"`                                             |

### 4.8 CSV Export

**File:** `tests/integration/test_export.py`
**Prefix:** `EXP` (EXPort)

| ID     | Scenario                    | Request                                                | Assertion                                                                    |
|--------|-----------------------------|--------------------------------------------------------|------------------------------------------------------------------------------|
| EXP-01 | Content-Type header         | `GET /api/v1/export/csv?lat=...&radius_miles=10`       | `Content-Type: text/csv`                                                     |
| EXP-02 | Content-Disposition header  | Same                                                   | Contains `attachment`                                                        |
| EXP-03 | CSV headers                 | Same                                                   | First row matches column order from [API Contract §15](../api/TOXMAP_API_CONTRACT.md) |
| EXP-04 | Data row present            | `&chemical=LEAD+COMPOUNDS&year=2008`                   | Row with `tri_facility_id="21219BTHLS3RD"` and `total_release_lbs=12485.0`   |
| EXP-05 | Streaming                   | `radius_miles=500`                                     | Uses `Transfer-Encoding: chunked` OR has `Content-Length`                    |

### 4.9 Data Vintage Metadata

**File:** `tests/integration/test_meta.py`
**Prefix:** `META` (METAdata)

| ID      | Scenario                        | Request                  | Assertion                                                                                                                     |
|---------|---------------------------------|--------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| META-01 | Returns 200                     | `GET /api/v1/meta`       | HTTP 200                                                                                                                      |
| META-02 | Complete schema                 | Same                     | All 6 fields: `source`, `vintage_label`, `available_years`, `latest_year`, `total_facility_count`, `total_release_event_count` |
| META-03 | Source field                    | Same                     | `source=="fastapi-dev"`                                                                                                       |
| META-04 | Available years from seed       | Same                     | `available_years` contains `2006`, `2007`, `2008`                                                                             |
| META-05 | Latest year from seed           | Same                     | `latest_year==2008`                                                                                                           |
| META-06 | Facility count from seed        | Same                     | `total_facility_count==7`                                                                                                     |
| META-07 | Vintage fallback                | Same                     | `vintage_label=="unknown"` (no ingestion metadata in seed)                                                                    |

---

## 5. Entry & Exit Criteria

### Entry Criteria

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | Layer 2 component tests passing | CI green |
| 2 | `docker compose up -d postgres` succeeds | Container health check passes |
| 3 | `toxmap_test` database exists and migrations applied | `alembic upgrade head` succeeds |
| 4 | `tests/fixtures/seed.sql` executes without error | `psql -f seed.sql` returns 0 |
| 5 | `DATABASE_URL_SYNC` env var set | `echo $DATABASE_URL_SYNC` returns valid DSN |

### Exit Criteria

| # | Criterion | Evidence |
|---|-----------|---------|
| 1 | All FSR-*, FSE-*, FDT-*, RLS-*, CHM-*, SUP-*, DEM-*, EXP-*, META-* scenarios passing (58 tests) | `pytest tests/integration/` — 0 failures |
| 2 | FSE-* (validation error) scenarios emphasized — HTTP 422 / 400 with correct `detail` bodies | Same report |
| 3 | PostGIS spatial correctness: radius includes/excludes correct seeded facilities | FSR-01, FSR-02 in `test_facility_search.py` passing |
| 4 | GeoJSON coordinate order correct for all spatial endpoints | `test_geojson_rfc7946.py` (Layer 4) green |
| 5 | `app/routers/` line coverage ≥ 85% | `pytest-cov` report |
| 6 | Tests deterministic across 3 consecutive runs | CI evidence |

### Deferred Scenarios

| Scenario | Reason | Target |
|----------|--------|--------|
| Nuclear plant layer (`/api/v1/layers/nuclear`) | Layer not yet implemented | Phase 4 |
| Congressional districts layer | Layer not yet implemented | Phase 5 |
| NPRI Canadian facilities | Layer not yet implemented | Phase 5 |

---

## 6. Out of Scope

| Area | Reason |
|------|--------|
| Browser rendering | Covered by Layer 5 E2E Tests |
| OpenAPI schema conformance fuzzing | Covered by Layer 4 API Contract Tests |
| Performance SLA under load | Covered by Layer 4 performance contract tests |
| Production DuckDB WASM mode | Covered by Layer 5 production smoke suite |
| Application log assertions | DB state + HTTP response are sufficient signal |

---

## Appendix A — Automation Traceability

| Test ID  | Scenario ID        | Description                                        | File                       | Status     |
|----------|--------------------|----------------------------------------------------|----------------------------|------------|
| IT-01–13 | FSR-01–FSR-13      | Facility search (radius, filters, color band)      | `test_facility_search.py`  | ⚠️ Planned |
| IT-14–15 | FSE-01–FSE-02      | Facility search validation errors                  | `test_facility_search.py`  | ⚠️ Planned |
| IT-16–18 | FDT-01–FDT-03      | Facility detail                                    | `test_facility_detail.py`  | ⚠️ Planned |
| IT-19–25 | RLS-01–RLS-07      | Release time series + largest                      | `test_release_trends.py`   | ⚠️ Planned |
| IT-26–32 | CHM-01–CHM-07      | Chemicals list + autocomplete                      | `test_chemicals.py`        | ⚠️ Planned |
| IT-33–38 | SUP-01–SUP-06      | Superfund search + detail                          | `test_superfund.py`        | ⚠️ Planned |
| IT-39–46 | DEM-01–DEM-08      | Demographics county + tract                        | `test_demographics.py`     | ⚠️ Planned |
| IT-47–51 | EXP-01–EXP-05      | CSV export                                         | `test_export.py`           | ⚠️ Planned |
| IT-52–58 | META-01–META-07    | Data vintage metadata                              | `test_meta.py`             | ⚠️ Planned |

