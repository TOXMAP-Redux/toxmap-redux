# ADR-011: Census Bureau API for Demographic Overlays

| Field             | Value                                                                                                                                           |
|-------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| **ID**            | ADR-011                                                                                                                                         |
| **Title**         | Census Bureau API for Demographic Overlays, SEER Mortality Descoped                                                                             |
| **Date**          | 2026-08-09                                                                                                                                      |
| **Status**        | **Accepted**                                                                                                                                    |
| **Deciders**      | Phase Manager + Backend/Data/Security Engineer coordination                                                                                     |
| **Census Sources**| [Census Bureau Data API](https://www.census.gov/data/developers/data-sets/decennial-census.html) · [ToS](https://www.census.gov/data/developers/about/terms-of-service.html) |
| **SEER Sources**  | [SEER Mortality](https://seer.cancer.gov/mortality/) · [SEER DUA](https://seer.cancer.gov/data-software/documentation/seerstat/nov2025/seer-dua-nov2025.html) |
| **Supersedes**    | —                                                                                                                                               |
| **Superseded by** | —                                                                                                                                               |

---

## Context

The original NLM TOXMAP aggregated data from **multiple separate sources** per the [NLM TOXNET "Has Moved" page](https://www.nlm.nih.gov/toxnet/index.html):

| Data Type              | Original TOXMAP Source                          | Our Implementation Status |
|------------------------|-------------------------------------------------|---------------------------|
| TRI Facilities/Releases| EPA TRI Program                                 | ✅ Working                |
| Superfund Sites        | EPA Superfund Program                           | ✅ Working                |
| County Boundaries      | Census TIGER shapefiles                         | ✅ Working                |
| Population Demographics| Census Bureau ACS/Decennial                     | ⚠️ Addressed by this ADR |
| **Cancer/Mortality**   | **NIH/NCI SEER Mortality Data**                 | ❌ Descoped by this ADR   |

### Problem Statement

The census data pipeline had critical issues:

1. **Census year mismatch**: Database contained 2022 data only; API defaulted to year 2000; result was 0 features returned
2. **Missing demographics**: All 3,229 counties had NULL values for income, age distribution, and other ACS variables
3. **Wrong data source for mortality**: The schema's mortality columns (`cancer_mortality_*`, `heart_disease_mortality_*`) cannot be populated from Census Bureau data — they require NIH/NCI SEER, a completely separate data system with restrictive data use agreements

### SEER Data Use Agreement Analysis

Per the [SEER Research Data Use Agreement (November 2025)](https://seer.cancer.gov/data-software/documentation/seerstat/nov2025/seer-dua-nov2025.html):

| DUA Requirement | TOXMAP-redux Conflict |
|-----------------|----------------------|
| **§4** — Use restricted to research purposes | Public web app = general public access |
| **§10** — Cannot release data to any other person | Public API = releasing to anyone |
| **§3** — All team members must sign DUA | Anonymous public users cannot sign |
| **§11** — Required safeguards (no credential sharing) | Public API = no authentication |
| **§14** — Suppress counts 1–4 | County-level could expose small cells |

**Conclusion**: SEER mortality data is legally incompatible with a public web application.

---

## Decision

### 1. Use Census Bureau Data API for Demographics

Adopt the Census Bureau's public REST API for all demographic overlay data:

- **API endpoint**: `api.census.gov/data/{year}/acs/acs5`
- **Authentication**: Free API key (request at https://api.census.gov/data/key_signup.html)
- **Response format**: JSON (clean, no file parsing required)
- **Coverage**: 2000, 2010, 2020 Decennial + all ACS 5-year estimates

**Variables to fetch:**

| Variable Code     | Description                    | Maps to Column   |
|-------------------|--------------------------------|------------------|
| `B01003_001E`     | Total population               | `total_pop`      |
| `B19013_001E`     | Median household income        | `median_income`  |
| `S0101_C02_022E`  | % population under 18          | `pct_under_18`   |
| `S0101_C02_030E`  | % population 65+               | `pct_over_65`    |
| `B02001_001E`, `B02001_002E` | Total pop, White alone | `pct_nonwhite` (computed) |

### 2. Descope Mortality Tab for MVP

Remove mortality data from the MVP scope entirely:

- Disable the Mortality tab in the UI with tooltip: "Mortality data requires NIH SEER integration (coming in future release)"
- Remove mortality columns from API responses
- Document SEER integration as Phase 15+ work

### 3. Future Health Data Alternatives

Evaluate these publicly accessible alternatives for future phases:

| Source | Data Type | Access | Recommended Phase |
|--------|-----------|--------|-------------------|
| [CDC/ATSDR SVI](https://www.atsdr.cdc.gov/place-health/php/svi/) | Social Vulnerability Index | Public download | Phase 9+ |
| [CDC WONDER](https://wonder.cdc.gov/) | Mortality statistics | Public API | Phase 15+ |
| [EPA EJSCREEN](https://www.epa.gov/ejscreen) | Environmental justice indicators | Public REST API | Phase 10+ |

---

## Why Census API Over Alternatives

### Census API vs. Pre-compiled CSVs

| Aspect | Census Bureau API | Pre-compiled CSVs |
|--------|-------------------|-------------------|
| **Reliability** | Stable government endpoint | URLs change, files go offline |
| **Format** | JSON response | CSV parsing required |
| **Versioning** | Clear year parameter | Filename conventions vary |
| **Maintenance** | API handles updates | Must track file locations |

### Census API vs. SEER County Attributes

| Aspect | Census Bureau API | SEER County Attributes |
|--------|-------------------|------------------------|
| **Access** | REST API → JSON | `.exe`/`.txt.gz` files for SEER*Stat software |
| **Data format** | JSON response | Fixed-width text files (custom parsing needed) |
| **Geographic focus** | Counties (what we need) | Census tracts (designed for cancer research) |
| **Year coverage** | 2000, 2010, 2020 Decennial + all ACS years | 1990, 2000 Decennial + ACS rolling windows only |
| **Integration effort** | `curl` → parse JSON | Download → unzip → parse fixed-width → map to schema |

**Key limitation from SEER docs:**
> "The time-dependent county attributes... are estimated at various time points using data obtained from the **1990 and 2000 U.S. Decennial Census long form survey**, and a series of **American Community Survey (ACS) 5-year estimates from 2006 to 2024**."

SEER does **not** provide exact 2010 or 2020 decennial data.

---

## Data Source Compliance

### Census Bureau API — ✅ Compliant

Per [Census Bureau API Terms of Service](https://www.census.gov/data/developers/about/terms-of-service.html):

| ToS Requirement | TOXMAP-redux Compliance |
|-----------------|------------------------|
| **Use clause** — "develop a service to search, display, analyze, retrieve, view" | ✅ Exactly what we're doing |
| **No re-identification** — cannot identify individuals, households, businesses | ✅ We display aggregate county-level data only |
| **No false representation** — cannot modify data and claim Census source | ✅ We display data as received |
| **No endorsement claims** — cannot imply Census endorsement | ✅ We won't claim this |
| **Attribution required** | ✅ Added to UI |

**Required attribution notice (implemented):**
> "This product uses the Census Bureau Data API but is not endorsed or certified by the Census Bureau."

---

## Implementation

### Backend Changes (`census_ingest.py`)

```python
CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY")
CENSUS_API_BASE = "https://api.census.gov/data"

async def fetch_acs_demographics(year: int = 2020) -> pd.DataFrame:
    """Fetch county demographics via Census Bureau Data API."""
    if not CENSUS_API_KEY:
        raise ValueError("CENSUS_API_KEY env var required for ACS data")
    
    url = f"{CENSUS_API_BASE}/{year}/acs/acs5"
    params = {
        "get": "NAME,B01003_001E,B19013_001E,B02001_001E,B02001_002E",
        "for": "county:*",
        "key": CENSUS_API_KEY
    }
    # ... fetch and parse JSON response
```

### Frontend Changes

1. **Pass `census_year` parameter** from UI controls to API
2. **Disable Mortality tab** with informational tooltip
3. **Add Census attribution** to CensusHealthPanel footer

### Configuration

Add to `.env.example`:
```bash
CENSUS_API_KEY=your_key_here  # Free: https://api.census.gov/data/key_signup.html
```

---

## Consequences

### Positive

- **Reliable data source**: Census Bureau API is stable, well-documented, and free
- **Legal compliance**: No data use agreements required for Census data
- **Simpler architecture**: Direct JSON responses, no file parsing
- **Clear scope**: Mortality descoped removes legal uncertainty

### Negative

- **No mortality data in MVP**: Users expecting health statistics will be disappointed
- **API key required**: Adds deployment configuration step
- **Rate limits**: Census API has rate limits (may need caching for high traffic)

### Neutral

- **Future work identified**: SEER integration documented as Phase 15+ for evaluation of CDC WONDER or other alternatives

---

## Storage and Memory Impact

### Data Sizes

| Component | Size | Notes |
|-----------|------|-------|
| **TIGER shapefile download** | ~77 MB | Compressed ZIP, one-time download per census year |
| **PostGIS county geometries** | ~80-100 MB | 3,229 counties × ~25 KB avg MULTIPOLYGON |
| **Census API response** | ~3-5 MB | JSON for all counties (per year) |
| **Demographics columns** | <1 MB | 6 numeric fields × 3,229 rows |

**Total `census_county` table:** ~85-100 MB in PostGIS

### $0 Budget Feasibility

| Hosting Option | Free Limit | Census Impact | Status |
|----------------|------------|---------------|--------|
| **Option A: Static (DuckDB WASM)** | 10 GB R2 | Census as GeoJSON/Parquet ~30 MB | ✅ Fine |
| **Option B: Supabase Free** | 500 MB | Census ~100 MB + TRI ~300 MB = 400 MB | ⚠️ Tight but fits |
| **Cloudflare R2** | 10 GB storage | Census + TRI + Superfund < 1 GB | ✅ Fine |

### Runtime Memory (Ingestion)

| Stage | Peak Memory | Notes |
|-------|-------------|-------|
| TIGER download + unzip | ~200 MB | geopandas holds full shapefile in memory |
| Census API fetch | ~50 MB | pandas DataFrame of all counties |
| PostGIS upsert | ~100 MB | Batched writes |

**Total ingestion peak:** ~250-300 MB

### Deployment Recommendation

**Run census ingestion locally via Docker Compose**, not on Fly.io's 256 MB free tier VMs. The TIGER shapefile processing exceeds 256 MB RAM. After ingestion completes locally:

- **Option A:** Run `build_parquet.py` to export census data to Parquet/GeoJSON, then upload to R2
- **Option B:** Connect to Supabase and run ingestion script with `--db-url` pointing to Supabase

**Verdict:** $0 budget remains feasible. Census data adds ~100 MB to storage, well within all free tier limits.

---

## Related Documents

- [AUDIT_CENSUS_PIPELINE_20260809.md](../escalations/AUDIT_CENSUS_PIPELINE_20260809.md) — Original audit report
- [ADR-001-fastapi-postgis-react.md](ADR-001-fastapi-postgis-react.md) — Primary architecture (defines demographic overlay requirement)
- [TOXMAP_API_CONTRACT.md](../api/TOXMAP_API_CONTRACT.md) — API contract for `/api/v1/demographics/county`

---

## References

1. Census Bureau Data API — https://www.census.gov/data/developers/data-sets/decennial-census.html
2. Census Bureau API Terms of Service — https://www.census.gov/data/developers/about/terms-of-service.html
3. Census API Key Signup — https://api.census.gov/data/key_signup.html
4. NLM TOXNET Has Moved — https://www.nlm.nih.gov/toxnet/index.html
5. SEER County/Tract Attributes — https://seer.cancer.gov/seerstat/variables/countyattribs/
6. SEER Research Data Use Agreement — https://seer.cancer.gov/data-software/documentation/seerstat/nov2025/seer-dua-nov2025.html
7. CDC/ATSDR Social Vulnerability Index — https://www.atsdr.cdc.gov/place-health/php/svi/
8. CDC WONDER — https://wonder.cdc.gov/
9. EPA EJSCREEN — https://www.epa.gov/ejscreen
