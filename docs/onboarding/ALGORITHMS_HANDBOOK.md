# TOXMAP Algorithms Handbook

> **Expert audit of all key algorithms used by the Backend Engineer (BE) and Data Engineer (DE) agents.**
>
> **Author:** Principal Backend/Data Engineer  
> **Version:** 1.1  
> **Last Updated:** 2026-08-20

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Data Ingestion Algorithms](#2-data-ingestion-algorithms)
3. [Spatial Query Algorithms](#3-spatial-query-algorithms)
4. [Data Aggregation Algorithms](#4-data-aggregation-algorithms)
5. [Search and Ranking Algorithms](#5-search-and-ranking-algorithms)
6. [Classification Algorithms](#6-classification-algorithms)
7. [Data Pipeline Algorithms](#7-data-pipeline-algorithms)
8. [Performance Analysis](#8-performance-analysis)
9. [Security Considerations](#9-security-considerations)
10. [Performance Optimizations & Recommendations](#10-performance-optimizations--recommendations)

---

## 1. Executive Summary

The TOXMAP backend/data stack implements approximately **15 distinct algorithms** across ingestion, querying, aggregation, search, and data export. This audit covers:

| Category | Algorithm Count | Complexity Range | Risk Level |
|----------|----------------|------------------|------------|
| Data Ingestion | 5 | O(n) to O(n log n) | Medium |
| Spatial Queries | 4 | O(log n) to O(n) | Low |
| Aggregation | 3 | O(n) to O(n²) | Medium |
| Search/Ranking | 2 | O(n log n) | Low |
| Classification | 3 | O(1) to O(n) | Low |
| Data Pipeline | 3 | O(n) | Low |

**Overall Assessment:** The codebase demonstrates solid engineering with appropriate use of database-level optimizations (PostGIS GIST indexes, trigram indexes for text search, GIN indexes for array queries). Chemical family lookups use an in-memory cache to avoid repeated database queries. See §10 for details on key optimizations and future improvement opportunities.

---

## 2. Data Ingestion Algorithms

### 2.1 TRI Column Normalization

**Location:** [backend/ingestion/tri_parser.py](../backend/ingestion/tri_parser.py)

**Algorithm:** Dictionary-based column remapping with regex prefix stripping

```python
# Strip "N. " prefix from EPA CSV headers, then lookup in TRI_COLUMN_MAP
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    number_prefix = re.compile(r"^\d+\.\s+")
    # Strip + uppercase + map
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(c) where c = number of columns (~40) |
| **Pros** | Single source of truth for column names; handles year-to-year EPA format changes |
| **Cons** | Case-insensitive lookup requires .upper() on every column |
| **Maintainability** | ✅ Excellent — adding new column aliases is trivial |
| **Issues** | None identified |

**Best Practice:** The `TRI_COLUMN_ALIASES` fallback handles legacy formats gracefully.

---

### 2.2 Release Quantity Aggregation

**Location:** [backend/ingestion/tri_parser.py](../backend/ingestion/tri_parser.py) → `compute_aggregated_release_columns()`

**Algorithm:** Sum of leaf-level TRI fields to avoid double-counting subtotals

```python
# Air = fugitive (Field 51) + stack (Field 52)
# Land = RCRA landfill + other landfills + land treatment + RCRA surface + other surface + other disposal
# Underground = Class I + Class II-V wells
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(n × k) where n = rows, k = fields per medium (~6) |
| **Pros** | Avoids double-counting by using leaf fields only (not subtotals) |
| **Cons** | Requires knowing the TRI field hierarchy intimately |
| **Maintainability** | ✅ Field lists are explicit constants (`LAND_RELEASE_FIELDS`, etc.) |
| **Issues** | Missing columns silently treated as 0 — could mask data quality issues |

**Data Integrity Note:** The algorithm correctly distinguishes:
- `NULL` → data absent (not reported)
- `0.0` → explicitly reported zero releases
- Form A certification artifacts (`form_type = 'A'`) → zeros are not measured values

---

### 2.3 Facility Upsert Algorithm

**Location:** [backend/ingestion/tri_ingest.py](../backend/ingestion/tri_ingest.py) → `_upsert_facilities()`

**Algorithm:** PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` with PostGIS point creation

```sql
INSERT INTO facilities (..., location)
VALUES (..., ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
ON CONFLICT (tri_facility_id) DO UPDATE SET ...
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(n) single pass with database roundtrip per row |
| **Pros** | Atomic upsert prevents duplicates; updates existing records with latest data |
| **Cons** | Row-by-row execution is slower than bulk insert |
| **Maintainability** | ✅ Good — standard SQLAlchemy parameterized pattern |
| **Issues** | ⚠️ Could be optimized with `bulk_save_objects()` for initial load |

**Recommendation:** For full TRI refresh (~22K facilities), consider batching with `executemany()` or `COPY`.

---

### 2.4 Superfund ArcGIS Pagination

**Location:** [backend/ingestion/superfund_ingest.py](../backend/ingestion/superfund_ingest.py) → `_download_superfund_arcgis()`

**Algorithm:** Cursor-based pagination against EPA ArcGIS Feature Service

```python
BATCH_SIZE = 1000  # ArcGIS allows up to 2000
# Fetch in batches using offset pagination, request centroid coordinates
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(n/batch_size) network roundtrips |
| **Pros** | Handles large datasets without memory exhaustion; returns polygon centroids |
| **Cons** | Offset pagination can miss or duplicate records if data changes during fetch |
| **Maintainability** | ✅ Good — retry logic with exponential backoff recommended |
| **Issues** | None critical; ArcGIS service occasionally returns stale data |

---

### 2.5 Census TIGER Shapefile Processing

**Location:** [backend/ingestion/census_ingest.py](../backend/ingestion/census_ingest.py) → `_download_tiger_counties()`

**Algorithm:** Download ZIP, extract shapefile, reproject to WGS84

```python
# geopandas handles CRS transformation
if gdf.crs and gdf.crs.to_epsg() != 4326:
    gdf = gdf.to_crs(epsg=4326)
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(n) where n = county polygons (~3,200 US counties) |
| **Pros** | Automatic CRS detection and reprojection |
| **Cons** | Entire shapefile loaded into memory |
| **Maintainability** | ✅ Good — handles multiple TIGER vintages (2000, 2010, 2020) |
| **Issues** | Column name differences across vintages require fallback logic |

---

## 3. Spatial Query Algorithms

### 3.1 Radius Search with ST_DWithin

**Location:** [backend/app/services/facility_service.py](../backend/app/services/facility_service.py) → `get_facilities_near()`

**Algorithm:** PostGIS Geography-based distance filter using GIST index

```python
# Cast to Geography for accurate meter-based distance on spheroid
point_geo = cast(func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326), Geography)
fac_geo = cast(Facility.location, Geography)

# ST_DWithin uses GIST index for fast spatial filter
stmt.where(func.ST_DWithin(fac_geo, point_geo, radius_meters))
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(log n) due to GIST index; O(k) for result set |
| **Pros** | Uses Geography type for accurate distances; index-backed |
| **Cons** | Geography cast has slight overhead vs. Geometry |
| **Maintainability** | ✅ Excellent — well-documented pattern |
| **Issues** | None |

**Critical Note:** The code correctly uses `ST_DWithin` (index-backed) rather than `ST_Distance` (full table scan).

---

### 3.2 Bounding Box Filter

**Location:** [backend/app/services/facility_service.py](../backend/app/services/facility_service.py)

**Algorithm:** PostGIS `ST_MakeEnvelope` + `ST_Within`

```python
func.ST_Within(
    Facility.location,
    func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326),
)
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(log n) with GIST index |
| **Pros** | Efficient viewport-based filtering for map tiles |
| **Cons** | Rectangle approximation may include corner outliers |
| **Maintainability** | ✅ Good |
| **Issues** | Coordinate parsing from string could fail silently (caught and logged) |

---

### 3.3 Superfund Contaminant Array Search

**Location:** [backend/app/services/superfund_service.py](../backend/app/services/superfund_service.py) → `get_superfund_near()`

**Algorithm:** PostgreSQL array containment query using GIN index

```python
# Exact match using array containment (index-backed)
SuperfundSite.contaminants.any(chemical.upper())

# Alternative for substring matching (full scan)
func.array_to_string(SuperfundSite.contaminants, "|").ilike(f"%{chemical}%")
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(log n) with GIN index for exact matches |
| **Pros** | GIN index enables efficient `ANY()` / `@>` queries; EPA contaminant names are standardized |
| **Cons** | Partial matching (ILIKE) bypasses index |
| **Maintainability** | ✅ Good |
| **Issues** | None — use exact match queries to leverage the index |

**Index:** `idx_superfund_contaminants_gin` (see migration `g2b3c4d5e6f7`)

---

### 3.4 Two-Phase Spatial Query Optimization

**Location:** [backend/app/services/facility_service.py](../backend/app/services/facility_service.py) → `get_facilities_near()`

**Algorithm:** Filter facilities spatially FIRST, then aggregate releases

```python
# STEP 1: Find facility IDs matching spatial + attribute filters (uses GIST index)
matching_fac_ids = select(Facility.id).where(func.ST_DWithin(...))

# STEP 2: Aggregate releases ONLY for matching facilities (uses B-tree index)
rel_stmt = select(...).where(ReleaseEvent.facility_id.in_(matching_fac_ids))

# STEP 3: Final join to get facility details
stmt = select(Facility, ...).join(rel_sub, rel_sub.c.facility_id == Facility.id)
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(log n) spatial + O(k log k) aggregation where k << n |
| **Pros** | Avoids scanning 1M+ release_events for global queries |
| **Cons** | Subquery materialization overhead |
| **Maintainability** | ✅ Well-documented with performance comments |
| **Issues** | None — this is a key performance optimization |

**Performance Impact:** Reduces p95 latency from ~5s to <500ms for radius searches.

---

## 4. Data Aggregation Algorithms

### 4.1 All-Years vs Single-Year Aggregation

**Location:** [backend/app/services/facility_service.py](../backend/app/services/facility_service.py)

**Algorithm:** Conditional GROUP BY based on year parameter

```python
if effective_year is not None:
    # Single year: group by facility + year
    select(
        ReleaseEvent.facility_id,
        func.sum(ReleaseEvent.total_release_lbs).label("total_lbs"),
        ReleaseEvent.reporting_year,
    ).group_by(ReleaseEvent.facility_id, ReleaseEvent.reporting_year)
else:
    # All years: aggregate across all years, use max year for display
    select(
        ReleaseEvent.facility_id,
        func.sum(ReleaseEvent.total_release_lbs).label("total_lbs"),
        func.max(ReleaseEvent.reporting_year).label("reporting_year"),
    ).group_by(ReleaseEvent.facility_id)
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(n) aggregate over release_events |
| **Pros** | Handles "All years" use case correctly (7.BUG.29 fix) |
| **Cons** | Two code paths to maintain |
| **Maintainability** | ✅ Good — bug fix well-documented |
| **Issues** | None after 7.BUG.29 fix |

---

### 4.2 Chemical Family Expansion (ADR-007)

**Location:** [backend/app/services/facility_service.py](../backend/app/services/facility_service.py) → `_expand_chemical_family()`

**Algorithm:** Lookup chemical → family → all family members, then OR across names

```python
# Expand "LEAD" to ["LEAD", "LEAD COMPOUNDS", "LEAD AND LEAD COMPOUNDS"]
family_chemicals = await get_family_chemical_names(session, chemical)

# Search uses OR across all family members
rel_stmt = rel_stmt.where(
    or_(*[Chemical.name.ilike(f"%{chem}%") for chem in family_chemicals])
)
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(1) lookup via in-memory cache; O(f) ILIKE clauses where f = family size (~3) |
| **Pros** | Transparent "right-to-know" search per NLM design; cached at startup |
| **Cons** | Multiple ILIKE clauses for large families |
| **Maintainability** | ✅ Good — expansion logic centralized in `chemical_service.py` |
| **Issues** | None — cache eliminates database roundtrips |

**Implementation Note:** Family mappings are loaded into `_FAMILY_CACHE` at startup (see §10). The frontend uses `chemical_families.json` for parity in DuckDB WASM mode.

---

### 4.3 Top Chemicals Aggregation

**Location:** [backend/app/services/facility_service.py](../backend/app/services/facility_service.py) → `get_facility_detail()`

**Algorithm:** GROUP BY chemical with SUM, ORDER BY DESC, LIMIT 5

```python
select(
    Chemical.name,
    func.sum(
        func.coalesce(ReleaseEvent.total_release_lbs, 0) + 
        func.coalesce(ReleaseEvent.off_site_lbs, 0)
    ).label("total_lbs"),
).join(ReleaseEvent, ...).group_by(Chemical.name, ...).order_by(desc("total_lbs")).limit(5)
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(n log 5) with LIMIT optimization |
| **Pros** | Includes off-site transfers for accurate TOTAL |
| **Cons** | Multiple columns in GROUP BY due to Pydantic schema needs |
| **Maintainability** | ✅ Good |
| **Issues** | None |

---

## 5. Search and Ranking Algorithms

### 5.1 Site Search Autocomplete (ADR-010)

**Location:** [backend/app/services/facility_service.py](../backend/app/services/facility_service.py) → `search_facilities()`

**Algorithm:** Tiered relevance scoring with UNION ALL across TRI and Superfund, backed by trigram indexes

```python
# Relevance scoring tiers
tri_score_expr = case(
    (func.upper(Facility.tri_facility_id) == q_upper, 1.0),   # Exact ID
    (Facility.tri_facility_id.ilike(q_prefix), 0.95),          # ID prefix
    (func.upper(Facility.name) == q_upper, 0.90),              # Exact name
    (Facility.name.ilike(q_prefix), 0.80),                     # Name prefix
    (Facility.name.ilike(q_pattern), 0.60),                    # Name contains
    (Facility.tri_facility_id.ilike(q_pattern), 0.50),         # ID contains
    else_=0.0,
)

# UNION ALL both datasets, order by score DESC
combined = union_all(tri_stmt, sf_stmt).subquery()
final_stmt = select(combined).order_by(desc(combined.c.relevance_score), combined.c.name).limit(limit)
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(log n) filter via trigram index + O(k log k) sort |
| **Pros** | Unified search across TRI and Superfund; deterministic ranking; index-backed |
| **Cons** | Six CASE branches per dataset |
| **Maintainability** | ✅ Good — scoring tiers clearly documented |
| **Issues** | None — trigram indexes enable fast ILIKE matching |

**Indexes:** `idx_facilities_name_trgm`, `idx_superfund_name_trgm` (see §10 for details)

---

### 5.2 Chemical Search Autocomplete

**Location:** [backend/app/services/chemical_service.py](../backend/app/services/chemical_service.py) → `search_chemicals()`

**Algorithm:** Simple ILIKE with LIMIT

```python
select(Chemical).where(Chemical.name.ilike(f"%{q}%")).order_by(Chemical.name).limit(10)
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(n) without index; O(log n) with trigram index |
| **Pros** | Simple and effective for ~800 chemicals |
| **Cons** | No ranking/scoring |
| **Maintainability** | ✅ Excellent |
| **Issues** | None for current scale |

---

## 6. Classification Algorithms

### 6.1 Color Band Assignment

**Location:** [backend/app/domain/color_band.py](../backend/app/domain/color_band.py) → `assign_color_band()`

**Algorithm:** Threshold-based bucketing (NLM TOXMAP design)

```python
_THRESHOLD_RED = 100_000     # ≥ 100K lbs
_THRESHOLD_ORANGE = 10_000   # ≥ 10K lbs
_THRESHOLD_YELLOW = 1_000    # ≥ 1K lbs
# else green (or NULL)

def assign_color_band(total_lbs: float | None) -> ColorBand:
    if total_lbs is None: return "green"
    if total_lbs >= _THRESHOLD_RED: return "red"
    if total_lbs >= _THRESHOLD_ORANGE: return "orange"
    if total_lbs >= _THRESHOLD_YELLOW: return "yellow"
    return "green"
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(1) |
| **Pros** | Pure function; fully testable; matches NLM design exactly |
| **Cons** | None |
| **Maintainability** | ✅ Excellent — thresholds are named constants |
| **Issues** | None |

---

### 6.2 PubChem URL Generation

**Location:** [backend/ingestion/tri_ingest.py](../backend/ingestion/tri_ingest.py) → `_pubchem_url()`

**Algorithm:** CAS number validation + direct URL construction; TRI category code mapping

```python
_CAS_PATTERN = re.compile(r"^\d{2,7}-\d{2}-\d$")
_TRI_CATEGORY_PATTERN = re.compile(r"^N\d{3}$")

def _pubchem_url(cas: str | None) -> str | None:
    # Check for TRI category codes (N###) → use curated mapping
    if _TRI_CATEGORY_PATTERN.match(cas):
        return _TRI_CATEGORY_PUBCHEM.get(cas)
    # Validate CAS format
    if not _CAS_PATTERN.match(cas):
        return None
    return f"https://pubchem.ncbi.nlm.nih.gov/compound/{cas}"
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(1) regex match |
| **Pros** | Validates CAS format; handles TRI category codes (N###) separately |
| **Cons** | Regex compilation on every call (minor) |
| **Maintainability** | ✅ Good — curated mapping for category codes |
| **Issues** | None after 7.BUG.22 fix |

---

### 6.3 Coordinate Validation

**Location:** [backend/app/domain/geo_utils.py](../backend/app/domain/geo_utils.py)

**Algorithm:** Bounds checking against WGS84 limits

```python
_LAT_MIN, _LAT_MAX = -90.0, 90.0
_LON_MIN, _LON_MAX = -180.0, 180.0
MAX_RADIUS_MILES = 500.0

def validate_lat(lat: float) -> ValidationError | None:
    if not _LAT_MIN <= lat <= _LAT_MAX:
        return ValidationError(field="lat", message="...", value=lat)
    return None
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(1) |
| **Pros** | Pure functions; clear error messages; domain-separated |
| **Cons** | None |
| **Maintainability** | ✅ Excellent |
| **Issues** | None |

---

## 7. Data Pipeline Algorithms

### 7.1 Parquet Build Pipeline

**Location:** [scripts/build_parquet.py](../scripts/build_parquet.py)

**Algorithm:** PostGIS → pandas DataFrame → PyArrow → Parquet with Snappy compression

```python
df = pd.read_sql(query, conn, params={"year": year})
table = pa.Table.from_pandas(df, preserve_index=False)
pq.write_table(table, str(parquet_file), compression="snappy")
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(n) row scan + O(n log n) Parquet encoding |
| **Pros** | Snappy compression balances size/speed; schema preserved |
| **Cons** | Entire year loaded into memory |
| **Maintainability** | ✅ Good — clear separation of concerns |
| **Issues** | None |

---

### 7.2 Manifest Management

**Location:** [scripts/build_parquet.py](../scripts/build_parquet.py) → `_update_manifest()`

**Algorithm:** Load existing manifest, remove old entry for year, append new entry, sort by year DESC

```python
manifest["vintages"] = [v for v in manifest.get("vintages", []) if v.get("year") != year]
manifest["vintages"].append({...new_entry...})
manifest["vintages"].sort(key=lambda v: v.get("year", 0), reverse=True)
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(v) where v = number of vintages (~5-10) |
| **Pros** | Atomic update; idempotent |
| **Cons** | File-based locking not implemented (CI handles serialization) |
| **Maintainability** | ✅ Good |
| **Issues** | None |

---

### 7.3 Seed Validation (T-03)

**Location:** [scripts/build_parquet.py](../scripts/build_parquet.py) → `validate_parquet_seeds()`

**Algorithm:** DuckDB query against built Parquet to assert known-good values

```python
result = con.execute("""
    SELECT total_release_lbs, land_release_lbs
    FROM read_parquet(?)
    WHERE tri_facility_id = '89319BHPCP7MILE'
      AND chemical_name ILIKE '%copper%'
      AND reporting_year = 2008
""", [str(parquet_file)]).fetchone()

if float(total_lbs) != 8205.0 or float(land_lbs) != 8205.0:
    raise AssertionError("T-03 validation FAILED")
```

| Aspect | Assessment |
|--------|------------|
| **Complexity** | O(n) Parquet scan (no index) |
| **Pros** | Catches data integrity issues before R2 upload |
| **Cons** | Single seed value; could be more comprehensive |
| **Maintainability** | ✅ Good — assertion values from peer-reviewed source |
| **Issues** | None |

---

## 8. Performance Analysis

### Query Performance Characteristics

| Algorithm | Typical Latency | Index Usage | Scalability |
|-----------|-----------------|-------------|-------------|
| Radius search (ST_DWithin) | 50-200ms | GIST on `location` | ✅ Excellent |
| All facilities browse | 200-500ms | B-tree on `state_code` | ✅ Good |
| Chemical search | <50ms | None (small table) | ✅ Good |
| Site search autocomplete | <50ms | GIN trigram on `name` | ✅ Excellent |
| Superfund contaminant search | <100ms | GIN on `contaminants` | ✅ Good |
| Chemical family expansion | <1ms | In-memory cache | ✅ Excellent |

### Memory Usage Patterns

| Operation | Peak Memory | Notes |
|-----------|-------------|-------|
| TRI ingestion (1 year) | ~2GB | Full CSV in pandas DataFrame |
| Census shapefile load | ~500MB | GeoPandas with WKT |
| Parquet build | ~1GB | DataFrame + PyArrow table |
| API request (browse) | ~50MB | ORM objects + GeoJSON |

---

## 9. Security Considerations

### SQL Injection Prevention

All database queries use **parameterized statements** via SQLAlchemy:

```python
# ✅ CORRECT — parameterized
conn.execute(text("SELECT * FROM facilities WHERE state_code = :state"), {"state": state})

# ❌ NEVER DONE — f-string SQL
# conn.execute(text(f"SELECT * FROM facilities WHERE state_code = '{state}'"))
```

### SSRF Prevention

All external URL fetches validate against **allow-listed prefixes**:

```python
TRI_BASE_URL = "https://www.epa.gov/"
TRI_DATA_BASE_URL = "https://data.epa.gov/"

def _validate_url(url: str) -> str:
    allowed = (TRI_BASE_URL, TRI_DATA_BASE_URL)
    if not any(url.startswith(prefix) for prefix in allowed):
        raise ValueError(f"SSRF guard: URL {url!r} is not under allowed prefix")
    return url
```

### Path Traversal Prevention

Parquet output paths are validated:

```python
def _safe_output_path(output_dir: Path, filename: str) -> Path:
    if ".." in filename or "/" in filename or "\\" in filename:
        raise ValueError(f"Unsafe filename: {filename!r}")
    return output_dir / filename
```

---

## 10. Performance Optimizations & Recommendations

This section covers the key optimizations already in place, plus opportunities for future improvement.

### Key Optimizations (Already Implemented)

These optimizations are critical to understand when working with the codebase:

#### 1. Trigram Indexes for Name Searches

PostgreSQL's `pg_trgm` extension enables fast substring matching via GIN indexes. This powers the autocomplete search across both TRI facilities and Superfund sites.

```sql
-- Enabled via Alembic migrations
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_facilities_name_trgm ON facilities USING GIN (name gin_trgm_ops);
CREATE INDEX idx_superfund_name_trgm ON superfund_sites USING GIN (name gin_trgm_ops);
```

**Why it matters:** Without these indexes, `ILIKE '%pattern%'` queries require full table scans. With trigram indexes, autocomplete latency drops from ~500ms to <50ms.

**Files:** `backend/alembic/versions/f1a2b3c4d5e6_add_facility_search_indexes.py`, `g2b3c4d5e6f7_add_superfund_search_indexes.py`

#### 2. Chemical Family In-Memory Cache

Chemical families (ADR-007) enable "right-to-know" search expansion (e.g., "LEAD" → "LEAD", "LEAD COMPOUNDS"). Rather than querying the database on every facility search, family mappings are loaded once at startup.

**Backend:** `app/services/chemical_service.py` defines `load_family_cache()`, called via a `@app.on_event("startup")` hook in `main.py`. The cache is a simple `dict[str, list[str]]` mapping chemical names to their family members.

**Frontend (DuckDB WASM mode):** `hooks/useChemicalFamilies.ts` fetches `chemical_families.json` from R2. This file is generated during the Parquet build pipeline (`scripts/build_parquet.py`).

**Why it matters:** Eliminates 6 database queries per facility search request when family expansion is active.

#### 3. GIN Index for Superfund Contaminants

Superfund sites store contaminants as a PostgreSQL `TEXT[]` array. A GIN index enables efficient containment queries.

```sql
CREATE INDEX idx_superfund_contaminants_gin ON superfund_sites USING GIN (contaminants);
```

**Why it matters:** Enables `WHERE contaminants @> ARRAY['LEAD']` queries to use the index instead of scanning all rows.

**File:** `backend/alembic/versions/g2b3c4d5e6f7_add_superfund_search_indexes.py`

---

### Future Improvements

These are potential optimizations not yet implemented. Consider them when addressing performance issues:

#### Medium Priority

1. **Batch facility upserts during ingestion**
   - Current: Row-by-row `INSERT ... ON CONFLICT` (~22K rows)
   - Improvement: Use `executemany()` or PostgreSQL `COPY` for bulk loads
   - Expected impact: 5-10x faster TRI refresh

2. **Additional seed validation assertions**
   - Current: T-03 (BHP Copper facility) validated in Parquet build
   - Improvement: Add T-04 (Superfund AVTEX site) and multi-year chemical assertions
   - Benefit: Earlier detection of data integrity issues

3. **Read replicas for browse queries**
   - Browse mode (`/api/v1/facilities/browse`) scans the full dataset
   - A read replica could offload these queries from the write primary
   - Relevant for high-traffic deployments

#### Low Priority

1. **Pre-compute all-years aggregates**
   - Materialized view or separate aggregate table
   - Updated during nightly ingestion
   - Benefit: Sub-10ms response for "All years" facility totals

2. **Query result caching (Redis)**
   - Cache frequently-accessed chemical searches
   - TTL of 1 hour for browse results
   - Note: Current in-memory caching may be sufficient at scale

---

## Appendix A: Algorithm Complexity Summary

| Algorithm | Time | Space | Database Ops |
|-----------|------|-------|--------------|
| TRI column normalization | O(c) | O(c) | 0 |
| Release aggregation | O(n×k) | O(n) | 0 |
| Facility upsert | O(n) | O(1) | n INSERTs |
| Radius search | O(log n + k) | O(k) | 1 SELECT |
| Site search | O(n) | O(k) | 1 UNION SELECT |
| Color band | O(1) | O(1) | 0 |
| Parquet build | O(n log n) | O(n) | 1 SELECT |

Where:
- n = total rows in table
- k = result set size
- c = column count (~40)

---

## Appendix B: Index Usage Verification

Run periodically to verify indexes are being used:

```sql
-- Check spatial index usage
EXPLAIN ANALYZE
SELECT * FROM facilities
WHERE ST_DWithin(
    location::geography,
    ST_SetSRID(ST_MakePoint(-76.4785, 39.2197), 4326)::geography,
    16093.4  -- 10 miles
);

-- Should show: "Index Scan using idx_facilities_location"
```

---

*Document maintained by: Principal Backend/Data Engineer*  
*Last reviewed: 2026-08-20*
