# TOXMAP API Contract

**Date:** 2026-07-15 (amended 2026-07-16)
**Base URL (dev/CI):** `http://localhost:8000`
**Base URL (production):** _None — production runs DuckDB WASM in the browser with no backend server. See [ADR-004](../adr/ADR-004-zero-budget-hosting.md). Endpoints marked ⚠️ do not exist in production._
**Format:** OpenAPI 3.1-compatible descriptions with example JSON payloads  
**Validation:** Use [Schemathesis](https://schemathesis.readthedocs.io/) or `pytest` + `jsonschema` to validate responses against these contracts.  
**Seed Data:** [TOXMAP_TEST_SEED_DATA.md](../testing/TOXMAP_TEST_SEED_DATA.md)  
**Acceptance Tests:** [TOXMAP_ACCEPTANCE_TESTS.md](../testing/TOXMAP_ACCEPTANCE_TESTS.md)

---

## Common Patterns

### GeoJSON FeatureCollection Envelope

All spatial search endpoints return this shape:

```json
{
  "type": "FeatureCollection",
  "features": [ /* array of Feature objects */ ],
  "meta": {
    "total_count": 3,
    "query": { /* echo of request parameters */ },
    "units": { /* field-level units for numeric properties */ }
  }
}
```

### Error Response (all 4xx/5xx)

```json
{
  "detail": "Human-readable description of the error",
  "code": "MACHINE_READABLE_CODE",
  "field": "offending_param_name_if_applicable"
}
```

### Coordinate Convention

All coordinates are **[longitude, latitude]** in GeoJSON geometry (per RFC 7946), but query parameters use `lat=` and `lon=` in natural reading order.

### Number Formatting

API responses return raw `float` values. **The frontend** is responsible for comma-formatting numbers in the UI (per UCD 2011 §"Commas in Numbers" — F-17). Contract tests validate the raw numeric value; E2E tests validate the formatted display.

---

## Endpoint Catalog

| Method | Path                                            | Description                                     | Layer           |
|--------|-------------------------------------------------|-------------------------------------------------|-----------------|
| GET    | `/api/v1/facilities`                            | Radius + viewport search                        | TRI Core        |
| GET    | `/api/v1/facilities/browse`                     | Browse mode — all facilities (no radius)        | TRI Core        |
| GET    | `/api/v1/facilities/{tri_facility_id}`          | Facility detail                                 | TRI Core        |
| GET    | `/api/v1/facilities/{tri_facility_id}/releases` | Time series                                     | TRI Core        |
| GET    | `/api/v1/releases/largest`                      | Largest release by chemical ± state             | TRI Core        |
| GET    | `/api/v1/chemicals`                             | Full chemical list                              | Chemicals       |
| GET    | `/api/v1/chemicals/search`                      | Auto-complete                                   | Chemicals       |
| GET    | `/api/v1/geocode`                               | Address → lat/lon (Photon proxy) ⚠️ dev only   | Geocoding       |
| GET    | `/api/v1/superfund/browse`                      | Browse mode — all Superfund sites (no radius)   | Superfund       |
| GET    | `/api/v1/superfund`                             | Superfund radius search                         | Superfund       |
| GET    | `/api/v1/superfund/{epa_id}`                    | Superfund site detail                           | Superfund       |
| GET    | `/api/v1/demographics/county`                   | County polygons + demographics                  | Demographics    |
| GET    | `/api/v1/demographics/tract`                    | Census tract polygons                           | Demographics    |
| GET    | `/api/v1/layers/nuclear`                        | Nuclear plant locations                         | Optional Layers |
| GET    | `/api/v1/layers/npri`                           | Canadian NPRI facilities                        | Optional Layers |
| GET    | `/api/v1/layers/congressional-districts`        | Congressional district boundaries               | Optional Layers |
| GET    | `/api/v1/tribes`                                | List tribes with TRI facility counts 📋 Phase 8 | Tribal Lands    |
| GET    | `/api/v1/export/csv`                            | Streaming CSV export                            | Export          |
| GET    | `/api/v1/export/map-metadata`                   | Current filter state for map snapshot           | Export          |
| GET    | `/api/v1/meta`                                  | TRI data vintage + available years ⚠️ dev only  | Metadata        |

> **⚠️ Dev-only endpoints** (`/api/v1/geocode`, `/api/v1/meta`) exist only when FastAPI is running. In production (DuckDB WASM mode), geocoding calls Photon (photon.komoot.io) directly from the browser per ADR-006, and data vintage metadata is read from `manifest.json` on Cloudflare R2. See [ADR-004](../adr/ADR-004-zero-budget-hosting.md), [ADR-006](../adr/ADR-006-photon-geocoding.md), and [TWO_MODES_DEEP_DIVE.md](../TWO_MODES_DEEP_DIVE.md).
>
> **📋 Phase 8 endpoints** (`/api/v1/tribes`) and the `tribal_only` parameter on facility endpoints are planned for Phase 8 (Tribal Lands Data) — a post-MVP enhancement. See the [Development Roadmap](../product/TOXMAP_DEVELOPMENT_ROADMAP.md) for details.

---

## 1. `GET /api/v1/facilities`

**Description:** Search for TRI facilities by location. Results are scoped to the viewport bounding box (no empty rows). Optionally restrict to a specific state.

### Request Parameters

| Parameter           | Type   | Required | Default | Description                                                                       |
|---------------------|--------|----------|---------|-----------------------------------------------------------------------------------|
| `lat`               | float  | ✅        | —       | Center latitude (WGS84)                                                           |
| `lon`               | float  | ✅        | —       | Center longitude (WGS84)                                                          |
| `radius_miles`      | float  | ✅        | —       | Search radius (max: 500)                                                          |
| `bbox`              | string | ❌        | null    | Viewport bounding box: `minLon,minLat,maxLon,maxLat` — scopes results table       |
| `year`              | int    | ❌        | latest  | TRI reporting year (1987–present)                                                 |
| `chemical`          | string | ❌        | null    | Chemical name (case-insensitive, partial match)                                   |
| `naics`             | string | ❌        | null    | NAICS code prefix (e.g., `325` matches all `325xxx`)                              |
| `medium`            | string | ❌        | null    | One of: `air`, `water`, `land`, `underground`                                     |
| `state`             | string | ❌        | null    | Two-letter state code (e.g., `VA`)                                                |
| `restrict_to_state` | bool   | ❌        | `false` | If `true` + `state` set, filters results to that state only                       |
| `limit`             | int    | ❌        | `500`   | Max features returned (1–2000). When results are truncated, `meta.truncated=true` |

### Success Response — 200

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-76.4785, 39.2197]
      },
      "properties": {
        "id": 1,
        "tri_facility_id": "21219BTHLS3RD",
        "name": "BETHLEHEM STEEL CORP - SPARROWS POINT",
        "city": "SPARROWS POINT",
        "state_code": "MD",
        "naics_code": "331110",
        "naics_desc": "Iron and Steel Mills",
        "total_release_lbs": 12485.0,
        "reporting_year": 2008,
        "color_band": "orange"
      }
    }
  ],
  "meta": {
    "total_count": 1,
    "returned_count": 1,
    "truncated": false,
    "query": {
      "lat": 39.2197,
      "lon": -76.4785,
      "radius_miles": 10,
      "year": 2008,
      "chemical": "LEAD COMPOUNDS",
      "medium": null,
      "state": null,
      "restrict_to_state": false,
      "bbox": null,
      "limit": 500
    }
  }
}
```

### Color Band Logic

| `total_release_lbs` Range | `color_band` |
|---------------------------|--------------|
| 0 – 999                   | `"green"`    |
| 1,000 – 9,999             | `"yellow"`   |
| 10,000 – 99,999           | `"orange"`   |
| ≥ 100,000                 | `"red"`      |

### Error Responses

| Status | Condition              | Example body                                                                                                      |
|--------|------------------------|-------------------------------------------------------------------------------------------------------------------|
| 422    | Missing `lat` or `lon` | `{"detail": "lat is required", "code": "MISSING_PARAM", "field": "lat"}`                                          |
| 400    | `radius_miles` > 500   | `{"detail": "radius_miles cannot exceed 500", "code": "RADIUS_TOO_LARGE", "field": "radius_miles"}`               |
| 400    | `limit` > 2000         | `{"detail": "limit cannot exceed 2000", "code": "LIMIT_TOO_LARGE", "field": "limit"}`                             |
| 400    | Invalid `medium` value | `{"detail": "medium must be one of: air, water, land, underground", "code": "INVALID_MEDIUM", "field": "medium"}` |
| 422    | Non-numeric `lat`      | `{"detail": "value is not a valid float", "code": "TYPE_ERROR", "field": "lat"}`                                  |

---

## 1b. `GET /api/v1/facilities/browse`

**Description:** Browse mode endpoint for the map's initial view. Returns ALL TRI facilities without radius constraint. Used when no search has been submitted — MapLibre handles viewport subsetting client-side.

> **Added 2026-07-28:** The original `/api/v1/facilities` endpoint requires `lat`, `lon`, and `radius_miles`. This made browse mode impossible without a fixed center point. The 500-mile radius cap meant only ~500 facilities (central US) could be loaded. This endpoint removes that constraint.

### Request Parameters

| Parameter | Type   | Required | Default | Description                                                   |
|-----------|--------|----------|---------|---------------------------------------------------------------|
| `year`    | int    | ❌        | latest  | TRI reporting year (1987–present)                             |
| `chemical`| string | ❌        | null    | Chemical name (case-insensitive, partial match)               |
| `medium`  | string | ❌        | null    | One of: `air`, `water`, `land`, `underground`                 |
| `state`   | string | ❌        | null    | Two-letter state code (e.g., `CA`)                            |
| `limit`   | int    | ❌        | `30000` | Max features returned (1–30000). Default returns all US facilities. |

### Success Response — 200

Same GeoJSON FeatureCollection shape as `/api/v1/facilities`. The `meta.query` echoes browse-mode params instead of spatial params:

```json
{
  "type": "FeatureCollection",
  "features": [ /* ... 21,889 features ... */ ],
  "meta": {
    "total_count": 21889,
    "returned_count": 21889,
    "truncated": false,
    "query": {
      "browse_all": true,
      "year": null,
      "chemical": null,
      "medium": null,
      "state": null,
      "limit": 30000
    }
  }
}
```

### Frontend Usage

```typescript
// Browse mode (no search submitted): fetch all facilities
const { data } = useMapFacilities(null)  // null triggers browse endpoint

// Search mode (user submitted a search): fetch within radius
const { data } = useMapFacilities({ lat, lon, radiusMiles: 25, ... })
```

### Performance Notes

- **Payload size:** ~22k facilities × ~200 bytes = ~4.4 MB (gzipped ~600 KB)
- **Response time:** < 2s (single PostGIS query, no spatial constraint)
- **Caching:** Frontend fetches once per session; MapLibre handles viewport rendering

---

## 2. `GET /api/v1/facilities/{tri_facility_id}`

**Description:** Full facility record including location, NAICS, county, and a summary of the most recent year's top chemical releases.

### Path Parameters

| Parameter         | Type   | Description                                   |
|-------------------|--------|-----------------------------------------------|
| `tri_facility_id` | string | EPA TRI Facility ID (e.g., `89319BHPCP7MILE`) |

### Success Response — 200

```json
{
  "id": 2,
  "tri_facility_id": "89319BHPCP7MILE",
  "name": "ROBINSON NEVADA MINING CO",
  "address": "7 MILES W OF ELY ON HWY 50",
  "city": "RUTH",
  "state_code": "NV",
  "zip_code": "89319",
  "county": "WHITE PINE",
  "naics_code": "212234",
  "naics_desc": "Copper Ore and Nickel Ore Mining",
  "location": {
    "lat": 39.2919,
    "lon": -115.0319
  },
  "latest_year": 2008,
  "top_chemicals": [
    {
      "chemical_name": "COPPER",
      "cas_number": "7440-50-8",
      "total_release_lbs": 8205.0,
      "unit_of_measure": "Pounds",
      "atsdr_url": "https://www.atsdr.cdc.gov/toxfaqs/tfacts132.pdf",
      "pubchem_url": "https://pubchem.ncbi.nlm.nih.gov/compound/23978"
    }
  ]
}
```

### Error Responses

| Status | Condition             | Example body                                                              |
|--------|-----------------------|---------------------------------------------------------------------------|
| 404    | Facility ID not found | `{"detail": "Facility '89319BHPCP7MILE' not found", "code": "NOT_FOUND"}` |

---

## 3. `GET /api/v1/facilities/{tri_facility_id}/releases`

**Description:** Time series of annual release data for a facility. Used to populate the 15-year trend chart (Tab 3 in the bar chart panel) and the yearly breakdown table (Tab 2).

### Query Parameters

| Parameter     | Type   | Required | Default             | Description                   |
|---------------|--------|----------|---------------------|-------------------------------|
| `from_year`   | int    | ❌        | `current_year - 14` | Start year                    |
| `to_year`     | int    | ❌        | `current_year`      | End year                      |
| `chemical_id` | int    | ❌        | null                | Filter to a specific chemical |
| `medium`      | string | ❌        | null                | Filter totals to one medium   |

### Success Response — 200

```json
[
  {
    "reporting_year": 2008,
    "chemical_name": "COPPER",
    "cas_number": "7440-50-8",
    "total_release_lbs": 8205.0,
    "air_release_lbs": 0.0,
    "water_release_lbs": 0.0,
    "land_release_lbs": 8205.0,
    "underground_release_lbs": 0.0,
    "unit_of_measure": "Pounds",
    "form_type": "R"
  },
  {
    "reporting_year": 2007,
    "chemical_name": "COPPER",
    "cas_number": "7440-50-8",
    "total_release_lbs": 7890.0,
    "air_release_lbs": 0.0,
    "water_release_lbs": 0.0,
    "land_release_lbs": 7890.0,
    "underground_release_lbs": 0.0,
    "unit_of_measure": "Pounds",
    "form_type": "R"
  }
]
```

**Contract invariants:**
- Array is sorted by `reporting_year` descending
- No `null` values for `total_release_lbs` — years with no data are omitted entirely (no placeholder nulls)
- Each item has all four medium fields present (may be `0.0`, never `null`)
- `unit_of_measure` is always present and always `"Pounds"` or `"Grams"` — never omitted
- `form_type` is always present: `"R"` for Form R records, `"A"` for Form A Certification records
- `cas_number` may be `null` for TRI compound categories (e.g. LEAD COMPOUNDS = N420)

---

## 4. `GET /api/v1/releases/largest`

**Description:** Returns the single facility with the highest total release of a given chemical, optionally restricted to a state. Used for the T-07 "state vs. nationwide comparison" scenario.

### Query Parameters

| Parameter  | Type   | Required | Description                                                |
|------------|--------|----------|------------------------------------------------------------|
| `chemical` | string | ✅        | Chemical name (exact or partial)                           |
| `year`     | int    | ❌        | TRI year (default: latest)                                 |
| `state`    | string | ❌        | Two-letter state code — if omitted, returns nationwide top |

### Success Response — 200

```json
{
  "tri_facility_id": "29801DSTLR0001",
  "name": "BORDEN CHEMICALS AND PLASTICS INC",
  "city": "AIKEN",
  "state_code": "SC",
  "chemical_name": "CHLORINE",
  "cas_number": "7782-50-5",
  "reporting_year": 2008,
  "total_release_lbs": 85000.0,
  "unit_of_measure": "Pounds",
  "location": {
    "lat": 33.5601,
    "lon": -81.7198
  }
}
```

### Error Responses

| Status | Condition                                             |
|--------|-------------------------------------------------------|
| 404    | No releases found for `chemical` (+ `state` if given) |
| 422    | Missing `chemical`                                    |

---

## 5. `GET /api/v1/chemicals`

**Description:** Full list of all chemicals in the database. Used for the Chemical Information panel and Superfund chemical list (T-02).

### Query Parameters

None.

### Success Response — 200

```json
[
  {
    "id": 5,
    "cas_number": "71-43-2",
    "name": "BENZENE",
    "category": "Volatile Organic Compounds",
    "atsdr_url": "https://www.atsdr.cdc.gov/toxfaqs/tfacts3.pdf",
    "pubchem_url": "https://pubchem.ncbi.nlm.nih.gov/compound/241"
  },
  {
    "id": 6,
    "cas_number": "7664-41-7",
    "name": "AMMONIA",
    "category": "Inorganic Compounds",
    "atsdr_url": "https://www.atsdr.cdc.gov/toxfaqs/tfacts126.pdf",
    "pubchem_url": "https://pubchem.ncbi.nlm.nih.gov/compound/222"
  }
]
```

**Contract invariants:**
- Sorted alphabetically by `name`
- `atsdr_url` and `pubchem_url` may be `null` if not yet populated; never omitted from response
- `atsdr_url` for family member chemicals (e.g., "ZINC COMPOUNDS") is inherited from the family parent ("ZINC") per ADR-007 when no direct ATSDR match exists

---

## 6. `GET /api/v1/chemicals/search`

**Description:** Live auto-complete for the chemical name input field. Returns up to 10 matches.

### Query Parameters

| Parameter | Type   | Required | Constraints   | Description           |
|-----------|--------|----------|---------------|-----------------------|
| `q`       | string | ✅        | min length: 2 | Partial chemical name |

### Success Response — 200

```json
[
  {
    "id": 5,
    "cas_number": "71-43-2",
    "name": "BENZENE"
  },
  {
    "id": 3,
    "cas_number": "100-42-5",
    "name": "STYRENE"
  }
]
```

**Contract invariants:**
- Maximum 10 results
- Response time ≤ 100ms (enforced in acceptance tests)
- Empty array (not 404) when no matches found

### Error Responses

| Status | Condition                           |
|--------|-------------------------------------|
| 422    | `q` parameter missing or length < 2 |

---

## 7. `GET /api/v1/superfund/browse`

**Description:** Browse mode endpoint for the Superfund always-on map layer. Returns ALL Superfund/NPL sites without radius constraint. Used for the diamond layer on the map — MapLibre handles viewport subsetting client-side.

> **Added 2026-07-28:** Mirrors the TRI `/api/v1/facilities/browse` pattern. The original `/api/v1/superfund` endpoint requires `lat`, `lon`, and `radius_miles` capped at 500. This made the always-on layer impossible without viewport-driven refetching. This endpoint removes that constraint.

### Request Parameters

| Parameter | Type   | Required | Default | Description                                   |
|-----------|--------|----------|---------|-----------------------------------------------|
| `status`  | string | ❌        | null    | One of: `NPL`, `CERCLIS`, `Deleted`           |
| `state`   | string | ❌        | null    | Two-letter state code (e.g., `CA`)            |
| `limit`   | int    | ❌        | `5000`  | Max features returned (1–5000). Default returns all US sites. |

### Success Response — 200

Same GeoJSON FeatureCollection shape as `/api/v1/superfund`. The `meta.query` echoes browse-mode params instead of spatial params:

```json
{
  "type": "FeatureCollection",
  "features": [ /* ... ~1,700 features ... */ ],
  "meta": {
    "total_count": 1742,
    "query": {
      "browse_all": true,
      "status": null,
      "state": null,
      "limit": 5000
    }
  }
}
```

### Frontend Usage

```typescript
// Always-on Superfund layer: fetch all sites once
const { data } = useSuperfundViewport()  // no params → browse endpoint

// Search mode (user submitted a Superfund search): fetch within radius
const { data } = useSuperfundSearch({ lat, lon, radiusMiles: 25, ... })
```

### Performance Notes

- **Payload size:** ~1,700 sites × ~200 bytes = ~340 KB (gzipped ~50 KB)
- **Response time:** < 500ms (single PostGIS query, no spatial constraint)
- **Caching:** Frontend fetches once on mount; MapLibre handles viewport rendering

---

## 7b. `GET /api/v1/superfund`

**Description:** Search for Superfund/NPL sites by location. Returns GeoJSON FeatureCollection with diamond markers.

### Query Parameters

| Parameter           | Type   | Required | Description                         |
|---------------------|--------|----------|-------------------------------------|
| `lat`               | float  | ✅        | Center latitude                     |
| `lon`               | float  | ✅        | Center longitude                    |
| `radius_miles`      | float  | ✅        | Search radius (max: 500)            |
| `chemical`          | string | ❌        | Filter by contaminant name          |
| `state`             | string | ❌        | Two-letter state code               |
| `restrict_to_state` | bool   | ❌        | Default: `false`                    |
| `status`            | string | ❌        | One of: `NPL`, `CERCLIS`, `Deleted` |

### Success Response — 200

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-78.1942, 38.9179]
      },
      "properties": {
        "id": 1,
        "epa_id": "VAD070358684",
        "name": "AVTEX FIBERS INC",
        "city": "FRONT ROYAL",
        "state_code": "VA",
        "status": "NPL",
        "hrs_score": 50.51,
        "npl_date": "1983-09-08",
        "contaminants": ["STYRENE", "CARBON DISULFIDE", "ZINC"],
        "marker_shape": "diamond"
      }
    }
  ],
  "meta": {
    "total_count": 1,
    "query": {
      "lat": 38.9179,
      "lon": -78.1942,
      "radius_miles": 10,
      "chemical": "STYRENE",
      "state": null,
      "restrict_to_state": false,
      "status": null
    }
  }
}
```

**Contract invariants:**
- `marker_shape` is always `"diamond"` — distinct from TRI `"circle"` (enforced by UX invariant 6)
- `hrs_score` is a float 0–100 or `null` for CERCLIS-only sites
- `contaminants` is always an array (never `null`), may be empty `[]`

---

## 8. `GET /api/v1/superfund/{epa_id}`

**Description:** Full Superfund site detail record. Used for the T-04 scenario.

### Success Response — 200

```json
{
  "id": 1,
  "epa_id": "VAD070358684",
  "name": "AVTEX FIBERS INC",
  "address": "BOX 1169 KENDRICK LN",
  "city": "FRONT ROYAL",
  "state_code": "VA",
  "zip_code": "22630",
  "county": "WARREN",
  "status": "NPL",
  "hrs_score": 50.51,
  "npl_date": "1983-09-08",
  "contaminants": [
    {
      "name": "STYRENE",
      "cas_number": "100-42-5",
      "atsdr_url": "https://www.atsdr.cdc.gov/toxfaqs/tfacts53.pdf"
    },
    {
      "name": "CARBON DISULFIDE",
      "cas_number": "75-15-0",
      "atsdr_url": "https://www.atsdr.cdc.gov/toxfaqs/tfacts119.pdf"
    }
  ],
  "epa_progress_url": "https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.Cleanup&id=0302388",
  "location": {
    "lat": 38.9179,
    "lon": -78.1942
  }
}
```

### Error Responses

| Status | Condition        |
|--------|------------------|
| 404    | EPA ID not found |

---

## 9. `GET /api/v1/demographics/county`

**Description:** County-level demographic polygons for a state. Used for the "US Census & Health Data" overlay. Returns demographic data with **units metadata** so the frontend can display inline labels without hardcoding (UX invariant 5 / F-14).

### Query Parameters

| Parameter     | Type   | Required | Description                                           |
|---------------|--------|----------|-------------------------------------------------------|
| `state`       | string | ✅        | Two-letter state code                                 |
| `census_year` | int    | ❌        | Default: `2000`. Options: `2000`, `2020`              |
| `fields`      | string | ❌        | Comma-separated field names to include (default: all) |

### Success Response — 200

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-78.40, 38.76], [-78.40, 38.99], [-78.00, 38.99], [-78.00, 38.76], [-78.40, 38.76]]]
      },
      "properties": {
        "fips_code": "51187",
        "name": "Warren County",
        "state_code": "VA",
        "census_year": 2000,
        "total_pop": 31584,
        "median_income": 41246.00,
        "pct_under_18": 24.7,
        "pct_over_65": 11.2,
        "pct_nonwhite": 8.4,
        "cancer_mortality_female_per_100k": 148.7
      }
    }
  ],
  "meta": {
    "total_count": 1,
    "census_year": 2000,
    "state": "VA",
    "units": {
      "total_pop": "people",
      "median_income": "$",
      "pct_under_18": "%",
      "pct_over_65": "%",
      "pct_nonwhite": "%",
      "cancer_mortality_female_per_100k": "per 100,000"
    }
  }
}
```

**Contract invariants:**
- `meta.units` object is always present and always contains an entry for every numeric field in `properties`
- This is the machine-readable source for the inline legend labels (F-14)
- `cancer_mortality_female_per_100k` may be `null` if not seeded for that county

---

## 10. `GET /api/v1/demographics/tract`

**Description:** Census tract polygons for a county. Sub-county resolution for the demographic overlay.

### Query Parameters

| Parameter     | Type   | Required | Description                              |
|---------------|--------|----------|------------------------------------------|
| `county_fips` | string | ✅        | 5-digit county FIPS code (e.g., `51187`) |
| `census_year` | int    | ❌        | Default: `2000`                          |

### Success Response — 200

Same shape as `/demographics/county` — GeoJSON FeatureCollection with Polygon geometries and the same `meta.units` object. Each feature `fips_code` is an 11-digit tract FIPS starting with the county FIPS prefix.

---

## 11. `GET /api/v1/layers/nuclear`

**Description:** U.S. commercial nuclear power plant locations.

### Success Response — 200

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-76.7021, 39.4704]
      },
      "properties": {
        "id": 1,
        "plant_name": "CALVERT CLIFFS NUCLEAR POWER PLANT",
        "operator": "Constellation Energy",
        "state_code": "MD",
        "status": "Operating",
        "marker_shape": "atom"
      }
    }
  ],
  "meta": { "total_count": 1 }
}
```

---

## 12. `GET /api/v1/layers/npri`

**Description:** Canadian National Pollutant Release Inventory (NPRI) facility locations.

### Query Parameters

| Parameter  | Type   | Required | Description                       |
|------------|--------|----------|-----------------------------------|
| `province` | string | ❌        | Two-letter Canadian province code |

### Success Response — 200

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [-79.3832, 43.6532] },
      "properties": {
        "npri_id": "1001",
        "name": "EXAMPLE ONTARIO FACILITY",
        "province": "ON",
        "marker_shape": "circle",
        "marker_color": "#a855f7"
      }
    }
  ],
  "meta": { "total_count": 1 }
}
```

---

## 13. `GET /api/v1/layers/congressional-districts`

**Description:** U.S. congressional district boundary polygons. Used as a toggleable overlay layer (NLM 2013 redesign feature). Boundaries are sourced from U.S. Census TIGER shapefiles post-redistricting.

### Query Parameters

| Parameter | Type   | Required | Description                                                          |
|-----------|--------|----------|----------------------------------------------------------------------|
| `state`   | string | ❌        | Two-letter state code — if omitted, returns all districts nationwide |

### Success Response — 200

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "MultiPolygon",
        "coordinates": [ [ [ [-78.40, 38.76], [-78.00, 38.76], [-78.00, 38.99], [-78.40, 38.99], [-78.40, 38.76] ] ] ]
      },
      "properties": {
        "id": 1,
        "state_code": "VA",
        "district_number": 5,
        "representative_name": null,
        "congress_number": 119
      }
    }
  ],
  "meta": { "total_count": 1, "state": "VA" }
}
```

**Contract invariants:**
- Geometry is always `MultiPolygon` (single-polygon districts are wrapped in the MultiPolygon envelope)
- `representative_name` may be `null` — this data requires a separate legislative data source and is optional
- `congress_number` is the U.S. Congress session number (119th = 2025–2027)

### Error Responses

| Status | Condition            |
|--------|----------------------|
| 400    | Invalid `state` code |

---

## 14. `GET /api/v1/export/csv`

**Description:** Streaming CSV download of filtered TRI facilities and their release data. Implements chunked transfer encoding — does not buffer the full result set.

### Query Parameters

Same as `GET /api/v1/facilities` (all parameters accepted).

### Success Response — 200

```
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="toxmap-export-2008-lead-compounds.csv"
Transfer-Encoding: chunked

tri_facility_id,name,address,city,state_code,naics_code,chemical_name,cas_number,reporting_year,total_release_lbs,air_release_lbs,water_release_lbs,land_release_lbs,underground_release_lbs,unit_of_measure,form_type
21219BTHLS3RD,"BETHLEHEM STEEL CORP - SPARROWS POINT","3200 SPARROWS POINT RD","SPARROWS POINT",MD,331110,"LEAD COMPOUNDS",,2008,12485.0,8200.0,3785.0,500.0,0.0,Pounds,R
```

**Contract invariants:**
- First row is always the header row
- `total_release_lbs` values in the CSV are raw floats (comma formatting is a UI concern)
- `cas_number` column is empty (not "null") for TRI compound categories such as LEAD COMPOUNDS
- `unit_of_measure` column is always present: `Pounds` or `Grams`
- `form_type` column is always present: `R` or `A`
- Filename in `Content-Disposition` encodes the active `chemical`, `year`, and date
- Response uses chunked transfer for large results (not buffered)

---

## 15. `GET /api/v1/export/map-metadata`

**Description:** Returns the current query state serialized as a JSON object, used by the frontend to construct a map image snapshot filename and export parameters.

### Query Parameters

Same as `GET /api/v1/facilities`.

### Success Response — 200

```json
{
  "export_filename": "toxmap-MD-LEAD-COMPOUNDS-2008-20260715.csv",
  "query": {
    "lat": 39.2197,
    "lon": -76.4785,
    "radius_miles": 10,
    "year": 2008,
    "chemical": "LEAD COMPOUNDS",
    "state": "MD",
    "restrict_to_state": true
  },
  "generated_at": "2026-07-15T15:00:00Z"
}
```

---

## 16. `GET /api/v1/geocode`

**Description:** Server-side proxy to Photon (photon.komoot.io, OpenStreetMap geocoder). Converts a free-text address or place name to lat/lon coordinates. Proxying through the backend provides an alternative to browser-direct calls and may be used by CLI tools or scripts.

> **Note for DuckDB WASM (ADR-004 Option A production path):** When the backend is not deployed, this endpoint does not exist. The frontend calls Photon directly from the browser using `frontend/src/api/geocode.ts`, which implements a 1-second throttle and 200-entry LRU cache per ADR-006. See the SEED_CITY_COORDS fallback in ADR-001 for offline/test use.

### Query Parameters

| Parameter      | Type   | Required | Description                                                  |
|----------------|--------|----------|--------------------------------------------------------------|
| `q`            | string | ✅        | Free-text address or place name (e.g., `Sparrows Point, MD`) |
| `countrycodes` | string | ❌        | Default: `us` — restrict to country (ISO 3166-1 alpha-2)     |
| `limit`        | int    | ❌        | Default: `1` — number of results to return (max 5)           |

### Success Response — 200

```json
[
  {
    "display_name": "Sparrows Point, Baltimore County, Maryland, United States",
    "lat": 39.2197,
    "lon": -76.4785,
    "place_type": "suburb",
    "boundingbox": [39.19, 39.25, -76.52, -76.44]
  }
]
```

**Contract invariants:**
- Always returns a JSON array (may be empty `[]` if no match found)
- `lat` and `lon` are floats in WGS84
- The proxy uses Photon's CORS-enabled API (ADR-006); no API key required
- Response time target: < 500ms (Photon p95 in North America)

### Error Responses

| Status | Condition                    |
|--------|------------------------------|
| 422    | `q` parameter missing or empty |
| 503    | Photon upstream unreachable  |

---

## 17. `GET /api/v1/meta` ⚠️ Dev only

**Description:** Returns metadata about the TRI data currently loaded in the FastAPI development database — the data vintage label, the EPA snapshot date, and the full list of available TRI reporting years. Used by the React app at startup to:
1. Populate the year-picker dropdown with years actually present in the database
2. Display the data vintage indicator in the map footer (e.g. `"2022 TRI · October 2024 freeze"`)

> **Production note:** This endpoint does not exist when the app runs in DuckDB WASM mode. The React app reads `manifest.json` directly from Cloudflare R2 instead. The `manifest.json` schema is intentionally identical to this response so a single client-side adapter handles both sources. When `VITE_DATA_SOURCE=api`, call `/api/v1/meta`. When `VITE_DATA_SOURCE=duckdb`, fetch `{R2_BASE_URL}/manifest.json` and parse the `years` array.

### Query Parameters

None.

### Success Response — 200

```json
{
  "vintage_label": "October 2024 freeze",
  "build_date": "2024-10-20",
  "available_years": [1987, 1988, 1989, 2020, 2021, 2022, 2023, 2024],
  "latest_year": 2024,
  "total_facility_count": 93241,
  "total_release_event_count": 4183752,
  "source": "fastapi-dev"
}
```

**Field definitions:**

| Field                       | Type                   | Description                                                                                                                                                                                                                                      |
|-----------------------------|------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `vintage_label`             | string                 | Human-readable EPA data snapshot label, e.g. `"October 2024 freeze"`, `"April 2025 spring refresh"`, `"August 2024 preliminary"`. Set during the ingestion run via `--vintage` CLI flag. Never `null` — if missing from DB, returns `"unknown"`. |
| `build_date`                | string (ISO 8601 date) | Date the ingestion pipeline ran, e.g. `"2024-10-20"`.                                                                                                                                                                                            |
| `available_years`           | int[]                  | Sorted ascending list of TRI reporting years present in the `release_events` table. The frontend uses this to constrain the year-picker.                                                                                                         |
| `latest_year`               | int                    | `MAX(reporting_year)` in the `release_events` table. Used as the default year when `year=` param is omitted.                                                                                                                                     |
| `total_facility_count`      | int                    | Row count of the `facilities` table. Useful for diagnosing truncated ingestion runs.                                                                                                                                                             |
| `total_release_event_count` | int                    | Row count of `release_events`.                                                                                                                                                                                                                   |
| `source`                    | string                 | Always `"fastapi-dev"` for this endpoint; always `"r2-manifest"` when parsed from `manifest.json`. Allows the React adapter to distinguish sources without branching on `VITE_DATA_SOURCE`.                                                      |

**Contract invariants:**
- `available_years` is always sorted ascending and never empty (if empty, the database is not seeded — return 503)
- `vintage_label` is never `null`; return `"unknown"` if the ingestion metadata record is missing
- `latest_year` equals `available_years[available_years.length - 1]`

### Error Responses

| Status | Condition                                            |
|--------|------------------------------------------------------|
| 503    | Database unreachable or `release_events` table empty |

---

## 18. `GET /api/v1/tribes` 📋 Phase 8

**Description:** Returns a list of all federally recognized tribes that have TRI reporting facilities on their lands. Each entry includes the BIA code, tribe name, and count of facilities. Used to populate the tribe sub-dropdown when "Tribal Lands" is selected in the state filter.

> **Phase 8 (Tribal Lands Data):** This endpoint is planned for the post-MVP Phase 8. It will be implemented as part of story 8.3.3 in the [Development Roadmap](../product/TOXMAP_DEVELOPMENT_ROADMAP.md).

### Query Parameters

None.

### Success Response — 200 (Planned)

```json
{
  "tribes": [
    {
      "bia_code": "NAV",
      "tribe_name": "Navajo Nation",
      "facility_count": 12
    },
    {
      "bia_code": "CHE",
      "tribe_name": "Cherokee Nation",
      "facility_count": 8
    }
  ],
  "meta": {
    "total_tribes": 45,
    "total_tribal_facilities": 127
  }
}
```

**Field definitions:**

| Field             | Type   | Description                                                                 |
|-------------------|--------|-----------------------------------------------------------------------------|
| `bia_code`        | string | Three-letter Bureau of Indian Affairs code (TRI Field 10)                   |
| `tribe_name`      | string | Full tribe name (TRI Field 11, up to 350 characters)                        |
| `facility_count`  | int    | Number of TRI facilities on this tribe's lands                              |
| `total_tribes`    | int    | Count of distinct tribes with at least one TRI facility                     |
| `total_tribal_facilities` | int | Total count of facilities where `bia_code IS NOT NULL`               |

**Contract invariants:**
- Results sorted alphabetically by `tribe_name`
- Only tribes with at least one facility are returned
- `bia_code` is never null in this response

### Related Parameters (Phase 8)

When Phase 8 is implemented, the following parameter will be added to `GET /api/v1/facilities` and `GET /api/v1/facilities/browse`:

| Parameter      | Type | Required | Default | Description                                            |
|----------------|------|----------|---------|--------------------------------------------------------|
| `tribal_only`  | bool | ❌        | `false` | If `true`, returns only facilities where `bia_code IS NOT NULL` |

---

## Pydantic Schema Reference

```python
# app/schemas/facility.py

from pydantic import BaseModel, Field
from typing import Literal, Optional
from enum import Enum

class ColorBand(str, Enum):
    GREEN  = "green"    # 0–999 lbs
    YELLOW = "yellow"   # 1,000–9,999 lbs
    ORANGE = "orange"   # 10,000–99,999 lbs
    RED    = "red"      # ≥ 100,000 lbs

class Medium(str, Enum):
    AIR         = "air"
    WATER       = "water"
    LAND        = "land"
    UNDERGROUND = "underground"

class PointGeometry(BaseModel):
    type: Literal["Point"]
    coordinates: list[float]  # [lon, lat]

class FacilityProperties(BaseModel):
    """Properties for each feature in the GeoJSON search result list.
    NOTE: marker_shape is a virtual/computed field — it is NOT stored in the database.
    It is always "circle" for TRI facilities and is added by the serializer layer."""
    id: int
    tri_facility_id: str
    name: str
    city: Optional[str]
    state_code: Optional[str]
    naics_code: Optional[str]
    naics_desc: Optional[str]
    total_release_lbs: Optional[float]
    reporting_year: int
    color_band: ColorBand
    # unit_of_measure: propagated from the underlying release_events row.
    # 'Pounds' for all non-dioxin chemicals (all seed data). 'Grams' for dioxin/dioxin-like
    # compounds (TRI classification DIOXIN, N150 category). The frontend MUST use this
    # field to display the correct unit label ("lbs" or "g") alongside total_release_lbs
    # in facility search results and map popups. See A-048 in TOXMAP_DESIGN_ASSUMPTIONS.md.
    unit_of_measure: str = "Pounds"
    marker_shape: Literal["circle"] = "circle"  # virtual field, not in DB

class FacilityFeature(BaseModel):
    type: Literal["Feature"]
    geometry: PointGeometry
    properties: FacilityProperties

class QueryMeta(BaseModel):
    total_count: int
    returned_count: int       # may be < total_count when truncated=True
    truncated: bool = False   # True when results were capped by the limit param
    query: dict
    units: Optional[dict] = None

class FacilityCollection(BaseModel):
    type: Literal["FeatureCollection"]
    features: list[FacilityFeature]
    meta: QueryMeta

class ReleaseEvent(BaseModel):
    reporting_year: int
    chemical_name: str
    # cas_number is None for TRI compound categories (e.g. LEAD COMPOUNDS = N420,
    # COPPER COMPOUNDS = N100). These categories use N-prefix TRI IDs, not CAS numbers.
    cas_number: Optional[str]
    total_release_lbs: float
    air_release_lbs: float        # never null — 0.0 if no air release; fugitive + stack
    water_release_lbs: float
    land_release_lbs: float       # never null — computed sum of TRI Fields 57–64
    underground_release_lbs: float
    # unit_of_measure: 'Pounds' for all non-dioxin chemicals (default).
    # 'Grams' for dioxin and dioxin-like compounds (TRI classification DIOXIN, N150 category).
    # The frontend MUST display this unit label alongside release quantities.
    # Color-band thresholds (green/yellow/orange/red) apply to pounds only;
    # for grams records, apply a 453.592-factor conversion before band assignment
    # OR display with "g" unit and a separate grams-specific band scale.
    unit_of_measure: str = "Pounds"
    # form_type: 'R' = Form R (measured quantities). 'A' = Form A Certification
    # (all zeros are certification artifacts, not measured zero releases).
    form_type: str = "R"

class LargestReleaseResponse(BaseModel):
    tri_facility_id: str
    name: str
    city: Optional[str]
    state_code: str
    chemical_name: str
    # cas_number is Optional — compound categories (e.g. LEAD COMPOUNDS = N420) have no CAS.
    cas_number: Optional[str]
    reporting_year: int
    total_release_lbs: float
    unit_of_measure: str = "Pounds"
    location: dict  # {"lat": float, "lon": float}

class ChemicalSummary(BaseModel):
    id: int
    # cas_number is None for TRI compound categories (N-prefix IDs such as N420 for
    # LEAD COMPOUNDS, N100 for COPPER COMPOUNDS). Never omit this field from the response.
    cas_number: Optional[str]
    name: str
    category: Optional[str]
    atsdr_url: Optional[str]
    pubchem_url: Optional[str]

class ErrorResponse(BaseModel):
    detail: str
    code: str
    field: Optional[str] = None

class TopChemical(BaseModel):
    """One entry in the facility detail top_chemicals list.
    top_chemicals = up to 5 chemicals ranked by total_release_lbs DESC
    for the facility's most recent reporting year (MAX(reporting_year))."""
    chemical_name: str
    # cas_number is None for TRI compound categories (e.g. LEAD COMPOUNDS = N420).
    cas_number: Optional[str]
    total_release_lbs: float
    unit_of_measure: str = "Pounds"  # 'Pounds' or 'Grams' — display alongside quantity
    atsdr_url: Optional[str]
    pubchem_url: Optional[str]

class FacilityDetail(BaseModel):
    """Full facility record returned by GET /api/v1/facilities/{tri_facility_id}.
    latest_year = MAX(reporting_year) across all release_events for this facility."""
    id: int
    tri_facility_id: str
    name: str
    address: Optional[str]
    city: Optional[str]
    state_code: Optional[str]
    zip_code: Optional[str]
    county: Optional[str]
    naics_code: Optional[str]
    naics_desc: Optional[str]
    location: dict   # {"lat": float, "lon": float}
    latest_year: int
    top_chemicals: list[TopChemical]

class SuperfundFeatureProperties(BaseModel):
    """Properties for each feature in the Superfund GeoJSON search result.
    NOTE: marker_shape is always 'diamond' — virtual field, not stored in DB."""
    id: int
    epa_id: str
    name: str
    city: Optional[str]
    state_code: Optional[str]
    status: Optional[str]
    hrs_score: Optional[float]
    npl_date: Optional[str]
    contaminants: list[str]
    marker_shape: Literal["diamond"] = "diamond"  # virtual field, not in DB

class SuperfundContaminant(BaseModel):
    name: str
    cas_number: Optional[str]
    atsdr_url: Optional[str]
    pubchem_url: Optional[str]

class SuperfundDetail(BaseModel):
    """Full Superfund site record returned by GET /api/v1/superfund/{epa_id}."""
    id: int
    epa_id: str
    name: str
    address: Optional[str]
    city: Optional[str]
    state_code: Optional[str]
    zip_code: Optional[str]
    county: Optional[str]
    status: Optional[str]
    hrs_score: Optional[float]
    npl_date: Optional[str]
    contaminants: list[SuperfundContaminant]
    epa_progress_url: Optional[str]
    location: dict   # {"lat": float, "lon": float}

class DataVintageResponse(BaseModel):
    """Response for GET /api/v1/meta (dev only).

    Schema is intentionally identical to the per-year objects in manifest.json on R2
    so the React app can use a single adapter for both sources.

    ⚠️ vintage_label must reflect the EPA data snapshot used during ingestion:
    - "October YYYY freeze"       → authoritative; use for production builds
    - "April YYYY spring refresh" → most corrected historical data
    - "August YYYY preliminary"   → incomplete; label clearly; not for production default
    Never use "unknown" in a production build — enforce via CLI flag validation.
    """
    vintage_label: str          # e.g. "October 2024 freeze"
    build_date: str             # ISO 8601 date: "2024-10-20"
    available_years: list[int]  # sorted ascending; never empty
    latest_year: int            # == available_years[-1]
    total_facility_count: int
    total_release_event_count: int
    source: Literal["fastapi-dev"] = "fastapi-dev"
```

---

## Schemathesis Contract Test Command

Once the OpenAPI spec is generated from FastAPI (`/openapi.json`), run:

```bash
# Stateful contract testing against the seed database
schemathesis run http://localhost:8000/openapi.json \
  --base-url http://localhost:8000 \
  --checks all \
  --hypothesis-max-examples 50 \
  --stateful=links

# Targeted contract test for a specific endpoint
schemathesis run http://localhost:8000/openapi.json \
  --endpoint "/api/v1/facilities" \
  --method GET \
  --checks response_schema_conformance,not_a_server_error
```

---

## Performance SLAs (Contract-Level)

| Endpoint                                            | p95 Target | Test Method                                 |
|-----------------------------------------------------|------------|---------------------------------------------|
| `GET /api/v1/facilities` (radius ≤ 50mi, seeded DB) | < 500ms    | `pytest-benchmark`                          |
| `GET /api/v1/facilities` (viewport bbox re-fetch)   | < 200ms    | `pytest-benchmark`                          |
| `GET /api/v1/chemicals/search`                      | < 100ms    | Gherkin step assertion                      |
| `GET /api/v1/superfund` (radius ≤ 50mi)             | < 300ms    | `pytest-benchmark`                          |
| `GET /api/v1/export/csv` (first byte)               | < 1,000ms  | `pytest-benchmark`                          |
| `GET /api/v1/demographics/county`                   | < 400ms    | `pytest-benchmark`                          |
| `GET /api/v1/geocode`                               | < 500ms    | `pytest-benchmark` (Photon p95)             |
| `GET /api/v1/meta`                                  | < 50ms     | `pytest-benchmark` (simple aggregate query) |

