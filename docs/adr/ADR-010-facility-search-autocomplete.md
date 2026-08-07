# ADR-010: Site Search Autocomplete (TRI ID, EPA ID, and Name)

| Field             | Value                                                                                                           |
|-------------------|----------------------------------------------------------------------------------------------------------------|
| **ID**            | ADR-010                                                                                                        |
| **Title**         | Site Search Autocomplete (TRI ID, EPA ID, and Facility/Site Name)                                              |
| **Date**          | 2026-08-07                                                                                                     |
| **Status**        | **Accepted**                                                                                                   |
| **Deciders**      | Architecture Review                                                                                            |
| **Parent ADR**    | [ADR-001](ADR-001-fastapi-postgis-react.md) (extends TRI Core API layer)                                       |
| **Related**       | [ADR-007](ADR-007-chemical-families.md) (similar autocomplete pattern for chemicals)                           |
| **Supersedes**    | —                                                                                                              |
| **Superseded by** | —                                                                                                              |

---

## Context

### The Problem

The current TOXMAP API supports facility discovery through two paths:

1. **Spatial search** (`GET /api/v1/facilities`) — find facilities within a radius of a geographic point
2. **Direct lookup** (`GET /api/v1/facilities/{tri_facility_id}`) — retrieve a specific facility by its exact TRI ID

Neither path supports **text-based facility search**. Users cannot:

- Search by **facility name** (e.g., "Bethlehem Steel") without knowing its exact location
- Perform **partial ID lookup** (e.g., "21219BTH" when they only remember part of the ID)
- Find **facilities in a state** by name (e.g., "all steel mills in Pennsylvania")

### User Scenarios Blocked

| Scenario | Current Workaround | Pain Point |
|----------|-------------------|------------|
| Journalist researching "DuPont" facilities | Must download EPA TRI bulk file, grep for name | No in-app solution |
| Researcher with partial TRI ID from a citation | Must visit EPA Envirofacts to lookup full ID | Breaks workflow |
| Community member who knows the "big plant down by the river" | Must manually pan/zoom the map | Frustrating if plant is in a different town |
| Regulator cross-referencing facility by name from a permit | Must query EPA FRS database separately | No integration |

### Usage Patterns in Original TOXMAP

The decommissioned NLM TOXMAP included a "Facility Quick Search" feature that allowed text-based facility lookup. The [UCD 2011 usability study](https://www.ncbi.nlm.nih.gov/books/NBK590906/) documented users attempting to search by facility name as a primary interaction pattern.

---

## Decision

**Add `GET /api/v1/facilities/search` endpoint with ranked TRI ID, EPA ID (Superfund), and name matching.**

This endpoint searches **both TRI facilities and Superfund sites**, returning unified results with a `site_type` discriminator. The unified search supports:

- **TRI facilities**: searchable by TRI Facility ID (e.g., `89319BHPCP7MILE`) or facility name
- **Superfund sites**: searchable by EPA Site ID (e.g., `WAD009248671`) or site name

### Endpoint Specification

```text
GET /api/v1/facilities/search?q={query}&state={state}&limit={limit}
```

| Parameter | Type   | Required | Default | Constraints              | Description                                        |
|-----------|--------|----------|---------|--------------------------|---------------------------------------------------|
| `q`       | string | ✅        | —       | min 2 chars, max 100     | Search query (TRI ID, EPA ID, or facility/site name) |
| `state`   | string | ❌        | null    | 2-letter uppercase       | Filter results to specific state                  |
| `limit`   | int    | ❌        | 10      | 1–50                     | Maximum results returned                       |

### Response Schema

```json
[
  {
    "id": 2,
    "site_type": "tri",
    "site_id": "89319BHPCP7MILE",
    "name": "ROBINSON NEVADA MINING CO",
    "city": "RUTH",
    "state_code": "NV",
    "county": "WHITE PINE",
    "match_type": "id",
    "relevance_score": 1.0
  },
  {
    "id": 123,
    "site_type": "superfund",
    "site_id": "WAD009248671",
    "name": "HANFORD 100-AREA (USDOE)",
    "city": "RICHLAND",
    "state_code": "WA",
    "county": "BENTON",
    "match_type": "name",
    "relevance_score": 0.60
  }
]
```

### Ranking Algorithm

Results are ranked by `relevance_score` using a deterministic scoring formula applied to **both datasets**:

| Match Type | Condition | Score | Rationale |
|------------|-----------|-------|-----------|
| Exact TRI ID | `UPPER(tri_facility_id) = UPPER(q)` | 1.0 | User knows the exact TRI ID — return it first |
| Exact EPA ID | `UPPER(epa_id) = UPPER(q)` | 1.0 | User knows the exact Superfund EPA ID |
| TRI ID prefix | `tri_facility_id ILIKE q%` | 0.95 | ID prefix match is strong signal |
| EPA ID prefix | `epa_id ILIKE q%` | 0.95 | Superfund ID prefix match |
| Exact name | `UPPER(name) = UPPER(q)` | 0.90 | Exact facility/site name match |
| Name prefix | `name ILIKE q%` | 0.80 | Name starts with query |
| Name contains | `name ILIKE %q%` | 0.60 | Name contains query |
| TRI ID contains | `tri_facility_id ILIKE %q%` | 0.50 | Partial TRI ID match (not prefix) |
| EPA ID contains | `epa_id ILIKE %q%` | 0.50 | Partial EPA ID match (not prefix) |

**Tie-breaking:** Within the same score tier, order by `name ASC` for deterministic results.

### Performance Target

| Metric | SLA | Rationale |
|--------|-----|-----------|
| p95 latency | < 100ms | Matches chemical search SLA; suitable for typeahead |
| p99 latency | < 200ms | Acceptable for autocomplete UX |

---

## Database Changes

### New Index: Trigram GIN on Facility Name

To meet the 100ms SLA for `ILIKE %query%` searches on ~22,000 facilities, we require a trigram index:

```sql
-- Enable trigram extension (already available in PostGIS images)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- TRI Facilities: GIN index for fast ILIKE pattern matching on name
CREATE INDEX idx_facilities_name_trgm 
    ON facilities USING GIN (name gin_trgm_ops);

-- TRI Facilities: B-tree index on TRI ID for prefix searches
CREATE INDEX idx_facilities_tri_id_upper 
    ON facilities (UPPER(tri_facility_id) varchar_pattern_ops);

-- Superfund Sites: GIN index for fast ILIKE pattern matching on name
CREATE INDEX idx_superfund_name_trgm 
    ON superfund_sites USING GIN (name gin_trgm_ops);

-- Superfund Sites: B-tree index on EPA ID for prefix searches
CREATE INDEX idx_superfund_epa_id_upper 
    ON superfund_sites (UPPER(epa_id) varchar_pattern_ops);
```

### Alembic Migration

```python
# backend/alembic/versions/xxx_add_site_search_indexes.py
"""Add trigram indexes for unified site search (TRI + Superfund).

Revision ID: xxx
Revises: [previous]
Create Date: 2026-08-07
"""
from alembic import op

revision = 'xxx'
down_revision = '[previous]'

def upgrade():
    # Enable pg_trgm extension for fuzzy text search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    
    # TRI Facilities indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_facilities_name_trgm 
        ON facilities USING GIN (name gin_trgm_ops)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_facilities_tri_id_pattern 
        ON facilities (UPPER(tri_facility_id) varchar_pattern_ops)
    """)
    
    # Superfund Sites indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_superfund_name_trgm 
        ON superfund_sites USING GIN (name gin_trgm_ops)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_superfund_epa_id_pattern 
        ON superfund_sites (UPPER(epa_id) varchar_pattern_ops)
    """)

def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_superfund_epa_id_pattern")
    op.execute("DROP INDEX IF EXISTS idx_superfund_name_trgm")
    op.execute("DROP INDEX IF EXISTS idx_facilities_tri_id_pattern")
    op.execute("DROP INDEX IF EXISTS idx_facilities_name_trgm")
    # Note: pg_trgm extension is left in place (may be used elsewhere)
```

### Index Size Estimates

| Index | Estimated Size | Notes |
|-------|---------------|-------|
| `idx_facilities_name_trgm` | ~2–4 MB | GIN index on 22K rows × avg 30-char name |
| `idx_facilities_tri_id_pattern` | ~1 MB | B-tree on 15-char fixed-width IDs |
| `idx_superfund_name_trgm` | ~0.5 MB | GIN index on 2K rows × avg 25-char name |
| `idx_superfund_epa_id_pattern` | ~0.2 MB | B-tree on 12-char EPA IDs |

Total additional storage: **< 8 MB** — negligible impact on database size.

---

## API Contract Addition

Add to `docs/api/TOXMAP_API_CONTRACT.md` §Endpoint Catalog:

```markdown
| GET | `/api/v1/facilities/search` | Site autocomplete (TRI ID, EPA ID, or name) | TRI + Superfund |
```

### Full Endpoint Documentation

```markdown
## X. `GET /api/v1/facilities/search`

**Description:** Search for TRI facilities and Superfund sites by ID or name with ranked results.
Returns matches ordered by relevance score, with exact ID matches prioritized. Searches both
TRI facilities (by TRI ID or name) and Superfund sites (by EPA ID or name). Used for unified
site search autocomplete in the search panel.

### Query Parameters

| Parameter | Type   | Required | Default | Constraints          | Description                                  |
|-----------|--------|----------|---------|----------------------|----------------------------------------------|
| `q`       | string | ✅        | —       | 2–100 chars          | Search query (TRI ID, EPA ID, or name)       |
| `state`   | string | ❌        | null    | 2-letter uppercase   | Filter to state                              |
| `limit`   | int    | ❌        | 10      | 1–50                 | Max results                                  |

### Success Response — 200

```json
[
  {
    "id": 1,
    "site_type": "tri",
    "site_id": "21219BTHLS3RD",
    "name": "BETHLEHEM STEEL CORP - SPARROWS POINT",
    "city": "SPARROWS POINT",
    "state_code": "MD",
    "county": "BALTIMORE",
    "match_type": "name",
    "relevance_score": 0.80
  },
  {
    "id": 123,
    "site_type": "superfund",
    "site_id": "WAD009248671",
    "name": "HANFORD 100-AREA (USDOE)",
    "city": "RICHLAND",
    "state_code": "WA",
    "county": "BENTON",
    "match_type": "id",
    "relevance_score": 1.0
  }
]
```

### Response Fields

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | int | ❌ | Internal database ID (table-specific) |
| `site_type` | enum | ❌ | `"tri"` or `"superfund"` — discriminates result type |
| `site_id` | string | ❌ | TRI Facility ID (for `site_type="tri"`) or EPA Site ID (for `site_type="superfund"`) |
| `name` | string | ❌ | Facility or site name |
| `city` | string | ✅ | City |
| `state_code` | string | ✅ | 2-letter state code |
| `county` | string | ✅ | County name |
| `match_type` | enum | ❌ | `"id"` or `"name"` — which field matched |
| `relevance_score` | float | ❌ | 0.0–1.0 ranking score |

### Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| 422 | `q` missing or < 2 chars | `{"detail": "q must be at least 2 characters", "code": "VALIDATION_ERROR"}` |
| 422 | `limit` out of range | `{"detail": "limit must be between 1 and 50", "code": "VALIDATION_ERROR"}` |
| 422 | Invalid `state` | `{"detail": "state must be a 2-letter code", "code": "VALIDATION_ERROR"}` |

### Notes

- Returns empty array `[]` (not 404) when no facilities/sites match
- Results from both datasets are merged and ordered by `relevance_score DESC`, then `name ASC`
- Exact TRI ID or EPA ID matches always appear first (score = 1.0)
- Search is case-insensitive for both ID and name
- Use `site_type` to determine how to handle the selection (TRI vs Superfund drawer)

```text
---

## Implementation Details

### Service Layer

```python
# backend/app/services/facility_service.py

from sqlalchemy import case, desc, func, or_, select
from app.models.facility import Facility
from app.schemas.facility import FacilitySearchResult

async def search_facilities(
    session: AsyncSession,
    q: str,
    state: str | None = None,
    limit: int = 10,
) -> list[FacilitySearchResult]:
    """Search facilities by TRI ID or name with ranked relevance scoring.
    
    Scoring tiers:
    - 1.00: Exact TRI ID match
    - 0.95: TRI ID prefix match
    - 0.90: Exact name match
    - 0.80: Name prefix match
    - 0.60: Name contains match
    - 0.50: TRI ID contains match
    """
    q_upper = q.upper()
    q_pattern = f"%{q}%"
    q_prefix = f"{q}%"
    
    # Relevance scoring via CASE expression
    score_expr = case(
        # Tier 1: Exact TRI ID
        (func.upper(Facility.tri_facility_id) == q_upper, 1.0),
        # Tier 2: TRI ID prefix
        (Facility.tri_facility_id.ilike(q_prefix), 0.95),
        # Tier 3: Exact name
        (func.upper(Facility.name) == q_upper, 0.90),
        # Tier 4: Name prefix
        (Facility.name.ilike(q_prefix), 0.80),
        # Tier 5: Name contains
        (Facility.name.ilike(q_pattern), 0.60),
        # Tier 6: TRI ID contains
        (Facility.tri_facility_id.ilike(q_pattern), 0.50),
        else_=0.0,
    ).label("relevance_score")
    
    # Match type determination
    match_type_expr = case(
        (or_(
            func.upper(Facility.tri_facility_id) == q_upper,
            Facility.tri_facility_id.ilike(q_prefix),
            Facility.tri_facility_id.ilike(q_pattern),
        ), "id"),
        else_="name",
    ).label("match_type")
    
    stmt = (
        select(
            Facility.id,
            Facility.tri_facility_id,
            Facility.name,
            Facility.city,
            Facility.state_code,
            Facility.county,
            match_type_expr,
            score_expr,
        )
        .where(
            or_(
                Facility.tri_facility_id.ilike(q_pattern),
                Facility.name.ilike(q_pattern),
            )
        )
        .where(score_expr > 0)  # Exclude non-matches
        .order_by(desc(score_expr), Facility.name)
        .limit(limit)
    )
    
    if state:
        stmt = stmt.where(Facility.state_code == state.upper())
    
    rows = (await session.execute(stmt)).all()
    
    return [
        FacilitySearchResult(
            id=row.id,
            tri_facility_id=row.tri_facility_id,
            name=row.name,
            city=row.city,
            state_code=row.state_code,
            county=row.county,
            match_type=row.match_type,
            relevance_score=float(row.relevance_score),
        )
        for row in rows
    ]
```

### Router Layer

```python
# backend/app/routers/facilities.py (addition)

@router.get("/facilities/search", response_model=list[FacilitySearchResult])
async def search_facilities_endpoint(
    q: Annotated[
        str,
        Query(min_length=2, max_length=100, description="Search query (TRI ID or name)"),
    ],
    state: Annotated[
        str | None,
        Query(max_length=2, description="Filter to 2-letter state code"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    db: AsyncSession = Depends(get_db),
) -> list[FacilitySearchResult]:
    """Search facilities by TRI ID or name.
    
    Returns ranked results with exact ID matches first, followed by name matches.
    Empty array returned when no facilities match (not 404).
    """
    return await search_facilities(db, q, state, limit)
```

### Pydantic Schema

```python
# backend/app/schemas/facility.py (addition)

class FacilitySearchResult(BaseModel):
    """Facility search result with relevance scoring."""
    
    id: int
    tri_facility_id: str
    name: str
    city: str | None
    state_code: str | None
    county: str | None
    match_type: Literal["id", "name"]
    relevance_score: float = Field(ge=0.0, le=1.0)
    
    model_config = ConfigDict(from_attributes=True)
```

---

## Frontend Integration

### API Client

```typescript
// frontend/src/api/facilities.ts (addition)

export interface FacilitySearchResult {
  id: number
  tri_facility_id: string
  name: string
  city: string | null
  state_code: string | null
  county: string | null
  match_type: 'id' | 'name'
  relevance_score: number
}

export async function searchFacilities(
  q: string,
  state?: string,
  limit = 10
): Promise<FacilitySearchResult[]> {
  const params = new URLSearchParams({ q })
  if (state) params.set('state', state)
  if (limit !== 10) params.set('limit', String(limit))
  
  const res = await fetch(`${API_BASE}/api/v1/facilities/search?${params}`)
  if (!res.ok) throw new Error(`Facility search failed: ${res.status}`)
  return res.json()
}
```

### Hook with Debounce

```typescript
// frontend/src/hooks/useFacilitySearch.ts

import { useEffect, useState } from 'react'
import { searchFacilities, FacilitySearchResult } from '../api/facilities'

export function useFacilitySearch(query: string, state?: string) {
  const [results, setResults] = useState<FacilitySearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  
  useEffect(() => {
    // Don't search until 2 chars (API requirement)
    if (query.length < 2) {
      setResults([])
      setError(null)
      return
    }
    
    const controller = new AbortController()
    const timer = setTimeout(async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await searchFacilities(query, state)
        if (!controller.signal.aborted) {
          setResults(data)
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err : new Error('Search failed'))
          setResults([])
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }, 300) // 300ms debounce (matches chemical search)
    
    return () => {
      clearTimeout(timer)
      controller.abort()
    }
  }, [query, state])
  
  return { results, loading, error }
}
```

---

## Alternatives Considered

### Option B: Full-Text Search with `tsvector`

Use PostgreSQL's native full-text search (`to_tsvector` / `to_tsquery`) instead of trigram matching.

**Pros:**

- Better for phrase matching and linguistic normalization (stemming)
- Built-in ranking with `ts_rank`

**Rejected because:**

- Facility names are proper nouns, not prose — linguistic normalization hurts accuracy
- TRI IDs are alphanumeric codes, not words — FTS doesn't help
- `ILIKE %query%` with trigram index better matches user expectations
- Simpler implementation with predictable behavior

### Option C: Elasticsearch / Typesense External Service

Deploy a dedicated search service (Elasticsearch, Typesense, Meilisearch) for facility search.

**Pros:**

- Purpose-built for search use cases
- Advanced features: typo tolerance, faceting, synonyms

**Rejected because:**

- Violates zero-budget hosting constraint (ADR-004)
- Adds infrastructure complexity and failure modes
- 22K facilities is trivially searchable with PostgreSQL + trigram
- Overkill for the problem scope

### Option D: Client-Side Search (DuckDB WASM)

In production mode (DuckDB WASM), perform facility search client-side by loading the Parquet file and filtering in-browser.

**Pros:**

- No new backend endpoint needed for production
- Consistent with ADR-004 architecture

**Partially accepted:**

- Production (DuckDB WASM mode) will use client-side Parquet search
- Dev mode uses the FastAPI endpoint for faster iteration
- This ADR specifies the backend endpoint; a future ADR may specify the DuckDB WASM equivalent

---

## Consequences

### Positive

1. **Unblocks common user workflows** — facility lookup by name is a frequently requested feature
2. **Matches original TOXMAP UX** — restores functionality that existed in the NLM version
3. **Consistent API pattern** — mirrors `GET /api/v1/chemicals/search` autocomplete design
4. **Performant** — trigram index meets 100ms SLA target
5. **Minimal footprint** — < 5 MB additional index storage

### Negative

1. **New endpoint to maintain** — adds to API surface area
2. **Index maintenance** — trigram index must be kept up to date (automatic with standard PostgreSQL)
3. **DuckDB parity gap** — production mode needs separate Parquet-based implementation (deferred)

### Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Trigram index degrades search quality for short queries | Low | Medium | Enforce min 2-char query; add exact-match tier |
| Users expect fuzzy matching (typo tolerance) | Medium | Low | Document exact-match behavior; consider `pg_trgm.similarity()` threshold in future |
| DuckDB WASM search implementation delayed | Medium | Medium | Backend endpoint available in dev mode; FE can ship with dev-mode search only initially |

---

## Testing Requirements

### Unit Tests

```python
# tests/unit/test_facility_search.py

class TestFacilitySearch:
    async def test_exact_id_match_returns_first(self, db_session):
        """Exact TRI ID match should have score 1.0 and appear first."""
        results = await search_facilities(db_session, "89319BHPCP7MILE")
        assert results[0].tri_facility_id == "89319BHPCP7MILE"
        assert results[0].relevance_score == 1.0
        assert results[0].match_type == "id"
    
    async def test_partial_id_prefix(self, db_session):
        """TRI ID prefix match should score 0.95."""
        results = await search_facilities(db_session, "89319")
        assert any(r.relevance_score == 0.95 for r in results)
    
    async def test_name_prefix_match(self, db_session):
        """Name prefix match should score 0.80."""
        results = await search_facilities(db_session, "ROBINSON")
        assert any(r.name.startswith("ROBINSON") for r in results)
        assert any(r.relevance_score == 0.80 for r in results)
    
    async def test_name_contains_match(self, db_session):
        """Name contains match should score 0.60."""
        results = await search_facilities(db_session, "STEEL")
        steel_results = [r for r in results if "STEEL" in r.name]
        assert len(steel_results) > 0
    
    async def test_state_filter(self, db_session):
        """State filter limits results to specified state."""
        results = await search_facilities(db_session, "MINING", state="NV")
        assert all(r.state_code == "NV" for r in results)
    
    async def test_empty_results_returns_empty_array(self, db_session):
        """No matches returns [], not 404."""
        results = await search_facilities(db_session, "ZZZZNOTAFACILITY")
        assert results == []
    
    async def test_case_insensitive(self, db_session):
        """Search is case-insensitive."""
        upper_results = await search_facilities(db_session, "BETHLEHEM")
        lower_results = await search_facilities(db_session, "bethlehem")
        assert upper_results == lower_results
    
    async def test_limit_respected(self, db_session):
        """Limit parameter caps result count."""
        results = await search_facilities(db_session, "INC", limit=3)
        assert len(results) <= 3
```

### Gherkin Scenarios

```gherkin
# tests/features/api/facility_search.feature

Feature: Facility Search Autocomplete
  As a TOXMAP user
  I want to search for facilities by ID or name
  So that I can quickly find a specific facility without knowing its location

  Background:
    Given the TRI database is seeded with test facilities

  Scenario: Search by exact TRI facility ID
    When I GET "/api/v1/facilities/search?q=89319BHPCP7MILE"
    Then the response status should be 200
    And the response should contain 1 or more results
    And the first result should have "tri_facility_id" = "89319BHPCP7MILE"
    And the first result should have "match_type" = "id"
    And the first result should have "relevance_score" = 1.0

  Scenario: Search by facility name (partial match)
    When I GET "/api/v1/facilities/search?q=BETHLEHEM"
    Then the response status should be 200
    And the response should contain a result with "name" containing "BETHLEHEM"
    And all results should have "match_type" = "name"

  Scenario: Search with state filter
    When I GET "/api/v1/facilities/search?q=MINING&state=NV"
    Then the response status should be 200
    And all results should have "state_code" = "NV"

  Scenario: Search with no matches returns empty array
    When I GET "/api/v1/facilities/search?q=XYZNOTEXIST"
    Then the response status should be 200
    And the response should be an empty array

  Scenario: Query too short returns 422
    When I GET "/api/v1/facilities/search?q=A"
    Then the response status should be 422
    And the response should have "detail" containing "at least 2 characters"

  Scenario: Results ordered by relevance score
    When I GET "/api/v1/facilities/search?q=ROBINSON"
    Then the response status should be 200
    And results should be ordered by "relevance_score" descending
```

### Performance Benchmark

```python
# tests/benchmarks/test_performance.py (addition)

@pytest.mark.benchmark
def test_facility_search_under_100ms(api_client, benchmark):
    """Facility name search p95 < 100ms (SLA from ADR-010)."""
    def search():
        return api_client.get("/api/v1/facilities/search", params={"q": "steel"})
    
    result = benchmark.pedantic(search, iterations=100, rounds=5)
    assert result.status_code == 200
    # Benchmark plugin reports p95 automatically
```

---

## Implementation Plan

| Phase | Task | Owner | Est. Points | Depends On |
|-------|------|-------|-------------|------------|
| 1 | Alembic migration: `pg_trgm` + indexes | DE | 1 | — |
| 2 | Pydantic schema: `FacilitySearchResult` | BE | 1 | — |
| 3 | Service function: `search_facilities()` | BE | 3 | 1 |
| 4 | Router endpoint: `GET /facilities/search` | BE | 1 | 2, 3 |
| 5 | Update `TOXMAP_API_CONTRACT.md` | BE | 1 | 4 |
| 6 | Unit tests + Gherkin scenarios | QA | 2 | 4 |
| 7 | Performance benchmark | QA | 1 | 4 |
| 8 | Frontend API client | FE | 1 | 4 |
| 9 | `useFacilitySearch` hook | FE | 2 | 8 |
| 10 | SearchPanel UI integration | FE | 3 | 9 |
| **Total** | | | **16 pts** | |

---

## Security Considerations

### Input Validation

All query parameters are validated via Pydantic before reaching the database:

```python
q: Annotated[str, Query(min_length=2, max_length=100)]  # Length bounds
state: Annotated[str | None, Query(max_length=2)]       # State code format
limit: Annotated[int, Query(ge=1, le=50)]               # Reasonable bounds
```

### SQL Injection Prevention

The service layer uses SQLAlchemy's parameterized queries exclusively:

```python
# Safe: parameterized ILIKE
stmt = stmt.where(Facility.name.ilike(f"%{q}%"))

# Unsafe (NEVER DO THIS):
# stmt = text(f"SELECT * FROM facilities WHERE name ILIKE '%{q}%'")
```

### Rate Limiting

The endpoint inherits the global rate limit from FastAPI middleware (if configured). For autocomplete use cases, the 300ms debounce on the frontend provides natural request throttling.

### Information Disclosure

The endpoint returns only public EPA TRI data. No internal IDs, audit fields, or sensitive metadata are exposed.

---

## Open Questions

1. **Should fuzzy matching (typo tolerance) be supported?**
   - `pg_trgm` provides `similarity()` function for fuzzy matching
   - Could add `fuzzy=true` query parameter to enable `similarity(name, q) > 0.3` filtering
   - **Deferred** to future enhancement based on user feedback

2. **Should address search be supported?**
   - Users might search "3200 Sparrows Point Rd" expecting to find the facility
   - Would require additional index and scoring tiers
   - **Deferred** — facility name and ID cover primary use cases

3. **DuckDB WASM parity?**
   - Production mode (no backend) needs equivalent search capability
   - Parquet file includes `name` and `tri_facility_id` columns
   - `SELECT * FROM read_parquet(...) WHERE name ILIKE '%q%' ORDER BY ...`
   - **Deferred** to Phase 7+ when DuckDB WASM hooks are implemented

---

## References

1. [EPA TRI Facility ID Format](https://www.epa.gov/enviro/tri-search-basic-search)
2. [PostgreSQL pg_trgm Documentation](https://www.postgresql.org/docs/current/pgtrgm.html)
3. [Original NLM TOXMAP Facility Search (archived)](https://web.archive.org/web/2018*/toxmap.nlm.nih.gov)
4. [ADR-001 Data Model](ADR-001-fastapi-postgis-react.md)
5. [Chemical Search Pattern (ADR-007)](ADR-007-chemical-families.md)

---

## Implementation Status

**Completed:** 2026-08-07 (Pre-Phase 7 addition)

| Step | Status | Notes |
|------|--------|-------|
| 1. Alembic migration | ✅ | `f1a2b3c4d5e6_add_facility_search_indexes.py` — pg_trgm + GIN/B-tree indexes |
| 2. Pydantic schema | ✅ | `FacilitySearchResult` added to `backend/app/schemas/facility.py` |
| 3. Service function | ✅ | `search_facilities()` in `backend/app/services/facility_service.py` |
| 4. Router endpoint | ✅ | `GET /api/v1/facilities/search` in `backend/app/routers/facilities.py` |
| 5. Gherkin scenarios | ✅ | 8 scenarios added to `tests/features/api/facility_search.feature` |
| 6. Step definitions | ✅ | New steps in `tests/steps/api_steps.py` for array results, relevance scores |
| 7. Frontend API client | ✅ | `searchFacilities()` in `frontend/src/api/facilities.ts` |
| 8. Frontend hook | ✅ | `useFacilitySearch` in `frontend/src/hooks/useFacilitySearch.ts` |
| 9. CHANGELOG | ✅ | Entry added to `[Unreleased]` section |
| 10. API contract update | ✅ | Endpoint added to `TOXMAP_API_CONTRACT.md` §1c + catalog |
| 11. Frontend UI | ✅ | `FacilitySearchInput` component integrated into `SearchPanel` |
| 12. Test ID registry | ✅ | `facility-search-*` IDs added to `TEST_ID_REGISTRY.md` |

### Files Created/Modified

**Backend:**
- `backend/alembic/versions/f1a2b3c4d5e6_add_facility_search_indexes.py` (new)
- `backend/app/schemas/facility.py` (modified — added `FacilitySearchResult`)
- `backend/app/services/facility_service.py` (modified — added `search_facilities()`)
- `backend/app/routers/facilities.py` (modified — added endpoint)

**Frontend:**
- `frontend/src/api/types.ts` (modified — added `FacilitySearchResult` type)
- `frontend/src/api/facilities.ts` (modified — added `searchFacilities()`)
- `frontend/src/hooks/useFacilitySearch.ts` (new)
- `frontend/src/components/Sidebar/FacilitySearchInput.tsx` (new)
- `frontend/src/components/Sidebar/SearchPanel.tsx` (modified — integrated FacilitySearchInput)
- `frontend/src/components/Sidebar/Sidebar.tsx` (modified — wires onFacilitySearchSelect)

**Tests:**
- `tests/features/api/facility_search.feature` (modified — 8 new scenarios)
- `tests/steps/api_steps.py` (modified — new step definitions)

**Docs:**
- `docs/api/TOXMAP_API_CONTRACT.md` (modified — added §1c endpoint spec)
- `docs/testing/TEST_ID_REGISTRY.md` (modified — added facility-search-* test IDs)
