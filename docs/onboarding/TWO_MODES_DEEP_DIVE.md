# The Two Modes: Dev vs. Production — Deep Dive

**Audience:** Engineers new to the project  
**Last Updated:** 2026-07-16  
**Related Docs:** [Tech Stack Onboarding](TECH_STACK_ONBOARDING.md) · [ADR-001](../adr/ADR-001-fastapi-postgis-react.md) · [ADR-004](../adr/ADR-004-zero-budget-hosting.md)

---

## Why This Document Exists

The TOXMAP codebase runs differently depending on where it's deployed. The same React frontend, the same query logic, the same test scenarios — but the data layer underneath is completely different in production vs. your laptop. If nobody explains this to you up front, you will eventually be confused by a line like:

```typescript
const dataSource = await resolveDataSource(); // "duckdb" or "api"
```

...and wonder why the app has two code paths for what seems like the same thing.

This document explains the whole picture: **why** two modes exist, **when** each one applies, and **how** each one works under the hood.

---

## Part 1: The Why

### The Fundamental Problem: Hosting Costs Money

Most web applications follow the same pattern: a browser talks to a server, the server talks to a database, the database returns data. This is simple, well-understood, and expensive.

"Expensive" means: you need a server running 24/7. Servers cost money. Databases cost money. The bigger your dataset, the more they cost.

TOXMAP has a $0 budget. Permanently.

This rules out the obvious solution (rent a VPS and run PostgreSQL). It rules out most cloud database services, which have either pay-per-query pricing or free tiers that expire after 12 months or pause after a week of inactivity.

### The Insight That Changes Everything

TRI data follows a **known, structured update schedule** — not a live, always-changing stream.

> ⚠️ **Correction to a common misconception:** TRI data is not strictly "read-only and updated once a year." The EPA TRI-Data-Considerations page ([official source](https://www.epa.gov/toxics-release-inventory-tri-program)) is explicit: facilities can and do submit **revisions**, **withdrawals**, and **late submissions** year-round via the EPA TRI-MEweb platform, and the public database is updated multiple times throughout the year. See [the full update cadence below](#the-real-tri-update-cadence) before drawing any architecture conclusions.

The correct framing is: TRI data updates on a **predictable, batch schedule with known checkpoints**, not in real-time. This is what allows a snapshot-based static architecture — with periodic rebuilds at those checkpoints — to be a reasonable production choice.

Because updates arrive in known batches rather than continuously, the data can be pre-processed into static files after each checkpoint, hosted on a CDN, and queried directly from the browser. **No server needs to run between builds.**

### The Real TRI Update Cadence

Understanding this cadence is not optional — it directly shapes how often the build pipeline must run, what metadata Parquet files must carry, and what the UI must tell users.

| Time Window             | What Happens                                                                                                                                                                                                            |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **July 1**              | Annual reporting deadline. Facilities _should_ submit by this date.                                                                                                                                                     |
| **July**                | EPA releases a **preliminary dataset** — raw data exactly as submitted. Incomplete; late filers still processing.                                                                                                       |
| **July – October**      | EPA processes late submissions and early revisions. The public database is refreshed **multiple times** during this window.                                                                                             |
| **October**             | EPA completes its annual data quality review. The TRI dataset is **frozen** for the National Analysis. This is the authoritative, quality-checked version used by official EPA tools (TRI Explorer, National Analysis). |
| **After October**       | Any post-freeze revisions, late submissions, or withdrawals are **not** reflected in that year's National Analysis.                                                                                                     |
| **Following Spring**    | EPA publishes the **spring data refresh** — incorporates all post-October changes. These corrections are reflected in the _next_ year's National Analysis.                                                              |
| **Ongoing, multi-year** | Facilities can retroactively correct historical submissions via TRI-MEweb (revisions, withdrawals, late submissions for prior years). EPA incorporates these into the live public database on a rolling basis.          |

**Source:** EPA [TRI Data Considerations](https://www.epa.gov/trinationalanalysis/tri-data-considerations) 

#### Quantified Drift Between Snapshots

The EPA measured the difference between the October 2023 frozen dataset (used for the 2022 National Analysis) and the October 2024 updated version — one year of retroactive corrections:

- **National waste management quantities: +9%** (primarily soybean processing facilities' revisions)
- **Total release quantities: +1.4%**

**9% is not noise.** A Parquet file built from the July preliminary can materially understate the final picture for a given year. The October-frozen dataset is always the more reliable choice.

#### What This Means for the Architecture

These four implications must be addressed in implementation — they are not handled by the current ADR-004 draft:

1. **The build pipeline must run more than once a year.** Building only on August 1 captures the least complete version of the data. The pipeline should target the October-frozen dataset as its primary source and also run the following spring to pick up the data refresh.

2. **Parquet files must carry data vintage metadata.** A file named `tri_2022.parquet` is ambiguous — it could be the July preliminary, the October freeze, or a spring-refreshed version. A sidecar `manifest.json` must record the **EPA data vintage** (the date/snapshot the data was sourced from EPA, not just the TRI reporting year it covers).

3. **The UI must display data vintage.** Users making public health or research decisions need to see "2022 TRI data (October 2023 freeze)" not just "2022 data." Without this, a user cannot know how current the figures are or how much retroactive correction may have occurred since.

4. **Historical Parquet files must be rebuildable.** The pipeline must support re-generating any prior year's Parquet file (not just the current year) to incorporate spring data refreshes and multi-year retroactive corrections.

### Why Not Just Use a Free Database Tier?

Free PostgreSQL hosting does exist. The table below is from ADR-004:

| Service                | Storage | PostGIS    | Expiry                   |
|------------------------|---------|------------|--------------------------|
| Supabase free          | 500 MB  | ✅          | Pauses after 1 week idle |
| Neon.tech free         | 512 MB  | ⚠️ Limited | None                     |
| Render PostgreSQL free | 256 MB  | ✅          | 90-day expiry            |
| Railway free           | 512 MB  | ✅          | $5/month credit          |

Two problems:
1. **Storage.** Full TRI history (1987–present) is ~800 MB. Nothing in that table fits it.
2. **Reliability.** Free database tiers pause on inactivity, expire, or change their terms. A public project can't depend on a database that goes offline if nobody visits for a week.

The static-first approach avoids both problems completely.

---

## Part 2: The When

There are three deployment contexts. Know which one you're in.

### Mode 1: Local Development (Docker Compose)

**When:** Your laptop. Always.

```
Your browser → FastAPI (localhost:8000) → PostgreSQL + PostGIS (localhost:5432)
```

You run `docker compose up`. Docker starts three containers: the React dev server, a FastAPI process, and a PostgreSQL + PostGIS database. Your browser talks to FastAPI over HTTP. FastAPI queries PostgreSQL with SQL. Everything is local, everything is fast, and you have a real database with real spatial indexes.

**Why FastAPI locally?** Because it makes development and testing predictable:
- You can inspect queries in real time
- Acceptance tests run against the real API
- Alembic migrations work exactly as they will on any server
- The `pytest` test suite covers FastAPI routes and service layer logic
- You don't have to worry about DuckDB WASM startup time while iterating on a feature

**Environment variables that control this:**
```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/toxmap

# frontend/.env
VITE_API_BASE_URL=http://localhost:8000
VITE_DATA_SOURCE=api        # ← tells the frontend: "talk to FastAPI"
```

### Mode 2: Production (Cloudflare Pages + DuckDB WASM)

**When:** The live public site at `toxmap.pages.dev`.

```
Your browser → DuckDB WASM (inside the browser) → Parquet files on Cloudflare R2
```

There is no server. FastAPI does not run. PostgreSQL does not run. The React app is a static bundle hosted on Cloudflare Pages (a CDN). When it needs data, it uses DuckDB WASM — a SQL database engine compiled to WebAssembly that runs entirely inside the browser tab — to query Parquet files fetched from Cloudflare R2.

**Environment variables that control this:**
```bash
# frontend/.env.production
VITE_DATA_SOURCE=duckdb      # ← tells the frontend: "use DuckDB WASM"
VITE_R2_BASE_URL=https://pub-XXXXX.r2.dev
```

### Mode 3: Free-Tier PaaS — Option B (Optional, Future)

**When:** If real-time data or multi-user state is ever needed, and the team is willing to accept the database size constraint.

```
Your browser → FastAPI on Fly.io → Supabase (PostgreSQL + PostGIS, 500 MB)
```

This uses the same FastAPI stack as local development but deployed to Fly.io's free tier (256 MB VMs) and Supabase's free PostgreSQL. The tradeoff: only ~20 years of TRI data fits in 500 MB, Supabase pauses after a week of inactivity, and Fly.io machines cold-start after idle. Option B is not the current production target — it's a fallback if a live API becomes necessary.

**This document focuses on Mode 1 and Mode 2.** Mode 3 is covered in [ADR-004 §Option B](../adr/ADR-004-zero-budget-hosting.md).

---

## Part 3: How Dev Mode Works

### The Stack

```
┌────────────────────────────────────────────────┐
│  Browser                                       │
│  React 18 + MapLibre GL + Recharts + Tailwind  │
│  VITE_DATA_SOURCE=api                          │
└─────────────────┬──────────────────────────────┘
                  │ HTTP/JSON (REST)
                  ▼
┌────────────────────────────────────────────────┐
│  FastAPI (uvicorn, port 8000)                  │
│  Routers → Service Layer → SQLAlchemy (async)  │
└─────────────────┬──────────────────────────────┘
                  │ asyncpg driver
                  ▼
┌────────────────────────────────────────────────┐
│  PostgreSQL 16 + PostGIS 3.4 (port 5432)       │
│  facilities · release_events · chemicals       │
│  superfund_sites · census_county               │
│  GIST spatial indexes                          │
└────────────────────────────────────────────────┘
```

### Starting It

```bash
# Start all three containers
docker compose up

# Health check (wait ~30s for PostGIS to initialize)
curl http://localhost:8000/health
# → {"status": "ok"}

# Load seed data (7 TRI facilities, defined in TOXMAP_TEST_SEED_DATA.md)
docker compose exec backend psql -U postgres -d toxmap -f /app/tests/fixtures/seed.sql

# Swagger UI (interactive API docs — auto-generated by FastAPI)
open http://localhost:8000/docs

# React app
open http://localhost:3000
```

### What Happens When the Frontend Fetches Data

With `VITE_DATA_SOURCE=api`, every data fetch goes through the typed API client in `frontend/src/api/`. Here's the lifecycle for a facility search:

```
1. User interacts with the map or search panel
   ↓
2. A React hook fires (e.g., useViewportFacilities)
   ↓
3. Hook calls api/facilities.ts → GET /api/v1/facilities?lat=...&lon=...&radius_miles=25
   ↓
4. FastAPI router (routers/facilities.py) receives the request
   FastAPI validates params automatically via Pydantic type annotations
   ↓
5. Router calls facility_service.get_near(lat, lon, radius_miles, session)
   ↓
6. Service builds SQLAlchemy query with GeoAlchemy2 spatial functions:
   ST_DWithin(ST_Transform(location, 3857), ST_Transform(point, 3857), radius_meters)
   ↓
7. asyncpg sends the query to PostgreSQL + PostGIS
   PostGIS uses the GIST index on facilities.location — result in <50ms
   ↓
8. SQLAlchemy maps rows to Facility ORM objects
   FastAPI serializes them to GeoJSON via Pydantic response model
   ↓
9. Browser receives GeoJSON FeatureCollection
   MapLibre GL renders facility pins, colored by total_release_lbs
```

### Running the Tests in Dev Mode

The test suite is designed to run against the dev stack:

```bash
# Backend unit + integration tests (requires PostGIS running)
docker compose exec backend pytest tests/

# API contract fuzzing (generates hundreds of test cases from /openapi.json)
docker compose exec backend schemathesis run http://localhost:8000/openapi.json --checks all

# Playwright E2E tests (requires full stack + seed data)
pytest tests/features/e2e/

# BDD acceptance tests only
docker compose exec backend pytest tests/ -m acceptance
```

All 57 Gherkin acceptance scenarios in [`TOXMAP_ACCEPTANCE_TESTS.md`](../testing/TOXMAP_ACCEPTANCE_TESTS.md) are executed against the FastAPI dev server. This is intentional — you need a real, queryable server to verify behavior like "returns only in-state facilities when restrict_to_state=true."

---

## Part 4: How Production Mode Works

### The Stack

```
┌────────────────────────────────────────────────────┐
│  Browser                                           │
│  React 18 + MapLibre GL + Recharts + Tailwind      │
│  VITE_DATA_SOURCE=duckdb                           │
│                                                    │
│  ┌─────────────────────────────────────────────┐   │
│  │  DuckDB WASM (WebAssembly, in-browser)      │   │
│  │  + Spatial Extension (WASM SIMD required)   │   │
│  │  Queries Parquet via HTTP range requests    │   │
│  └──────────────────┬──────────────────────────┘   │
└─────────────────────┼──────────────────────────────┘
                      │ HTTP Range Requests (bytes=N-M)
                      ▼
┌────────────────────────────────────────────────────┐
│  Cloudflare R2 (object storage, free tier)         │
│                                                    │
│  tri_1987.parquet   tri_2022.parquet               │
│  tri_1988.parquet   tri_2023.parquet               │
│  ...                tri_2024.parquet               │
│  superfund.parquet  chemicals.parquet              │
│  us_counties.geojson                               │
│  tiles.pmtiles  (map basemap)                      │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│  Cloudflare Pages (CDN, free tier)                 │
│  React app bundle (~2 MB) — served globally        │
└────────────────────────────────────────────────────┘
```

### What is DuckDB WASM, Exactly?

DuckDB is an analytical SQL database engine — think SQLite but column-oriented and tuned for queries that aggregate large datasets (sums, filters, group-bys). "WASM" means it's compiled to [WebAssembly](https://developer.mozilla.org/en-US/docs/WebAssembly), a binary format that browsers can execute at near-native speed.

When the React app loads in production:
1. The browser downloads the DuckDB WASM binary (~5 MB, cached after first visit)
2. The app runs `INSTALL spatial; LOAD spatial;` to activate geospatial functions
3. DuckDB is now a live, in-browser SQL engine with PostGIS-equivalent spatial capabilities

No server involved. The "database" is running inside the user's browser tab.

### What are Parquet Files?

Parquet is a **columnar binary file format** — the data is stored column-by-column instead of row-by-row like a CSV. This matters because:

- **Compression is much better.** Column values are often repetitive (`state_code = "TX"` for thousands of rows), and columnar storage compresses them efficiently. Full TRI history (~4M rows, ~2 GB as CSV) compresses to ~150 MB in Parquet.
- **HTTP range requests.** Parquet files support fetching only the columns and row groups you need via HTTP `Range: bytes=N-M` headers. A query that only reads `chemical_name` and `total_release_lbs` doesn't download `address`, `zip_code`, or any other column.
- **DuckDB natively understands Parquet.** The query `SELECT ... FROM read_parquet('https://...')` just works — DuckDB fetches only the byte ranges it needs.

The result: a browser query that filters 4 million rows by chemical and location only fetches 5–20 MB of data from R2, not 150 MB.

### What Does a Production Query Look Like?

In dev mode, the frontend calls `GET /api/v1/facilities?lat=39.22&lon=-76.48&radius_miles=25`. In production, the **same hook** runs a DuckDB WASM query instead:

```typescript
// frontend/src/api/facilities.ts (simplified)

// Dev mode path
async function fetchFacilitiesFromApi(params: FacilitySearchParams) {
  const response = await fetch(`${API_BASE}/api/v1/facilities?${toQueryString(params)}`);
  return response.json();
}

// Production mode path
async function fetchFacilitiesFromDuckDB(params: FacilitySearchParams) {
  const { lat, lon, radiusMiles, chemical, year } = params;
  const radiusMeters = radiusMiles * 1609.34;

  const results = await conn.query(`
    SELECT
      tri_facility_id,
      name,
      city,
      state_code,
      lat,
      lon,
      total_release_lbs,
      ST_Distance(
        ST_Point(lon, lat)::GEOGRAPHY,
        ST_Point($lon, $lat)::GEOGRAPHY
      ) / 1609.34 AS distance_miles
    FROM read_parquet('${R2_BASE_URL}/tri_${year}.parquet')
    WHERE chemical_name = $chemical
      AND ST_DWithin(
        ST_Point(lon, lat)::GEOGRAPHY,
        ST_Point($lon, $lat)::GEOGRAPHY,
        $radiusMeters
      )
    ORDER BY total_release_lbs DESC
  `, { lat, lon, chemical, radiusMeters });

  return toGeoJSON(results.toArray());
}

// The hook calls whichever is appropriate
export async function fetchFacilities(params: FacilitySearchParams) {
  const source = await resolveDataSource();
  return source === 'duckdb'
    ? fetchFacilitiesFromDuckDB(params)
    : fetchFacilitiesFromApi(params);
}
```

**The critical insight:** The SQL query in the DuckDB path is logically identical to what PostGIS executes on the server in dev mode. `ST_DWithin` means the same thing in both. The abstraction boundary is in the API client layer — everything above it (React components, hooks, rendering) is identical in both modes.

### The Migration Mapping

This table from ADR-004 shows exactly how each API endpoint maps to a DuckDB WASM query:

| Dev Mode (FastAPI)                | Production Mode (DuckDB WASM)                                                  |
|-----------------------------------|--------------------------------------------------------------------------------|
| `GET /api/v1/facilities`          | `SELECT ... FROM read_parquet('.../tri_YEAR.parquet') WHERE ST_DWithin(...)`   |
| `GET /api/v1/chemicals/search?q=` | `SELECT ... FROM read_parquet('.../chemicals.parquet') WHERE name ILIKE '%q%'` |
| `GET /api/v1/superfund`           | `SELECT ... FROM read_parquet('.../superfund.parquet') WHERE ST_DWithin(...)`  |
| `GET /api/v1/demographics/county` | `fetch('.../us_counties.geojson')` — small file, no query needed               |
| `GET /api/v1/export/csv`          | `duckdb.exportToCsv(...)` — client-side export                                 |

The React components, MapLibre GL rendering, Recharts charts, sidebar panels, URL routing, and all UX behavior are **100% identical** between modes. Only the data-fetch layer changes.

---

## Part 5: How the Switch is Made

### The `VITE_DATA_SOURCE` Environment Variable

The mode is controlled by a single environment variable set at build time:

```bash
VITE_DATA_SOURCE=api      # → dev mode  (talk to FastAPI)
VITE_DATA_SOURCE=duckdb   # → production mode (use DuckDB WASM)
```

`VITE_` prefixed variables are baked into the compiled JavaScript bundle by Vite at build time — they're not runtime config. This means the production bundle doesn't include FastAPI code paths, and the dev bundle doesn't load the 5 MB DuckDB WASM binary.

### The Browser Compatibility Check

DuckDB WASM's spatial extension requires **WebAssembly SIMD** — a CPU instruction set feature exposed through WASM. Older browsers (Safari on iOS < 15, some older Android WebViews) don't support it.

The app checks for SIMD support at startup and falls back to the FastAPI API (Option B) if it's unavailable:

```typescript
// frontend/src/lib/duckdbCompat.ts

export async function isDuckDBWasmSupported(): Promise<boolean> {
  if (typeof WebAssembly === 'undefined') return false;
  try {
    // Attempt to instantiate a minimal WASM module that uses SIMD instructions.
    // If the browser doesn't support WASM SIMD, this throws and we return false.
    const simdTest = new Uint8Array([
      0, 97, 115, 109, 1, 0, 0, 0,   // WASM magic + version
      1, 5, 1, 96, 0, 1, 123,         // type section: () -> v128
      3, 2, 1, 0,                     // function section
      10, 10, 1, 8, 0, 65, 0,         // code section: i32.const 0
      253, 15, 253, 98, 11,           // i32x4.splat, i8x16.popcnt, end
    ]);
    await WebAssembly.instantiate(simdTest);
    return true;
  } catch {
    return false;
  }
}

export async function resolveDataSource(): Promise<'duckdb' | 'api'> {
  const envOverride = import.meta.env.VITE_DATA_SOURCE;
  if (envOverride === 'api') return 'api';
  if (envOverride === 'duckdb') {
    return (await isDuckDBWasmSupported()) ? 'duckdb' : 'api';
  }
  // No override: try DuckDB, fall back to API
  return (await isDuckDBWasmSupported()) ? 'duckdb' : 'api';
}
```

**Browser compatibility matrix:**

| Browser                    | WASM SIMD  | Result            |
|----------------------------|------------|-------------------|
| Chrome 91+ / Edge 91+      | ✅          | DuckDB WASM       |
| Firefox 90+                | ✅          | DuckDB WASM       |
| Safari 16.4+ (macOS + iOS) | ✅          | DuckDB WASM       |
| Safari iOS 15.x            | ⚠️ Partial | Falls back to API |
| Safari iOS < 15            | ❌          | API (Option B)    |
| Chrome Android 91+         | ✅          | DuckDB WASM       |

**Practical implication:** When developing locally, you never see this fallback because `VITE_DATA_SOURCE=api` forces the API path. In production, `resolveDataSource()` runs on every page load. If it returns `'api'` on a browser that doesn't support WASM SIMD, the app needs a live FastAPI server (Option B) to work — otherwise the fallback has nothing to fall back to. This is a known gap to address before launch.

---

## Part 6: How Parquet Files Are Built

The Parquet files on Cloudflare R2 don't appear by magic. They're generated by a Python build pipeline that runs in GitHub Actions. The previous draft of this document described the pipeline as running "annually in August." **That is wrong** — see the [TRI update cadence](#the-real-tri-update-cadence) above for why.

### When It Should Run

The build must be triggered at each EPA data checkpoint, not just once a year:

```yaml
# .github/workflows/build-data.yml
on:
  schedule:
    - cron: "0 0 15 8 *"   # August 15: preliminary dataset (raw, incomplete — use with care)
    - cron: "0 0 20 10 *"  # October 20: post-freeze dataset (authoritative for National Analysis)
    - cron: "0 0 1 4 *"    # April 1: after spring data refresh (retroactive corrections)
  workflow_dispatch:
    inputs:
      years:
        description: "TRI years to rebuild (e.g. '2020 2021 2022' or 'latest')"
        default: "latest"
      vintage_label:
        description: "Human-readable vintage label (e.g. 'October 2024 freeze')"
        required: true
```

**Why three triggers?**
- **August 15** — Captures the preliminary dataset. Useful for early inspection but **not** recommended for the primary production build. Label these clearly as preliminary.
- **October 20** — After the EPA's annual data freeze. This is the authoritative version used in official EPA tools. **This is the primary build for production.**
- **April 1** — After the spring data refresh, which incorporates post-freeze revisions, late submissions, and retroactive corrections to prior years. This is important for historical accuracy.

Each run must rebuild only what changed — the `workflow_dispatch` inputs allow targeting specific years rather than re-processing all 38+ years of history on every trigger.

### Data Vintage Metadata

Every Parquet build must record its **data vintage** — when the underlying EPA source data was snapshotted. Without this, a `tri_2022.parquet` file is ambiguous: it could be the July preliminary (least complete), the October freeze (authoritative), or a spring-refreshed version (most corrected). Users and downstream tools need to know the difference.

The build script writes a sidecar `manifest.json` to R2 alongside the Parquet files:

```python
# scripts/build_data.py
import json
from datetime import date

def build_parquet(year: int, output_dir: str, vintage_label: str) -> None:
    """Convert one year's TRI CSV into a Parquet file for DuckDB WASM.
    
    Args:
        year: TRI reporting year (e.g., 2022)
        output_dir: local output directory
        vintage_label: human-readable label describing the EPA data snapshot used,
                       e.g. "October 2024 freeze", "April 2025 spring refresh",
                       "August 2024 preliminary". Displayed in the UI.
    """
    df = pd.read_csv(f"tri_{year}.csv", dtype=str, low_memory=False)
    df = clean_tri_dataframe(df)
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

    df.to_parquet(
        f"{output_dir}/tri_{year}.parquet",
        compression="snappy",
        index=False
    )

    # Write vintage metadata sidecar
    meta = {
        "tri_reporting_year": year,
        "epa_vintage_label": vintage_label,       # displayed in the UI
        "build_date": date.today().isoformat(),    # when this Parquet was generated
        "record_count": len(df),
    }
    with open(f"{output_dir}/tri_{year}.meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Built {output_dir}/tri_{year}.parquet ({len(df):,} records, vintage: {vintage_label})")
```

The React app reads the `.meta.json` sidecar alongside each Parquet query and displays the vintage label to the user.

Note: `pyarrow` (the Parquet writer used by pandas) is only in the `[ingestion]` extras in `pyproject.toml`. You don't need it installed to run the FastAPI backend.

### File Layout on R2

```
toxmap-data/                  ← Cloudflare R2 bucket
├── tri_1987.parquet
├── tri_1987.meta.json         ← {"tri_reporting_year": 1987, "epa_vintage_label": "April 2025 spring refresh", ...}
├── tri_1988.parquet
├── tri_1988.meta.json
├── ...
├── tri_2024.parquet
├── tri_2024.meta.json         ← {"tri_reporting_year": 2024, "epa_vintage_label": "October 2024 freeze", ...}
├── chemicals.parquet
├── superfund.parquet
├── superfund.meta.json
├── us_counties.geojson
└── tiles.pmtiles              ← OpenStreetMap basemap tiles (~600 MB for US)
```

One Parquet file per TRI year means DuckDB WASM only fetches the file for the year the user selected. If someone filters to 2022 data, `tri_1987.parquet` through `tri_2021.parquet` are never touched.

### CORS Configuration (Don't Skip This)

DuckDB WASM issues HTTP range requests from the browser to R2. The browser enforces CORS on cross-origin requests. Without the right headers on the R2 bucket, every query fails silently.

The required CORS policy for the R2 bucket:

```json
[
  {
    "AllowedOrigins": ["https://toxmap.pages.dev", "http://localhost:3000"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["Range", "Content-Type"],
    "ExposeHeaders": ["Content-Length", "Content-Range", "Accept-Ranges"],
    "MaxAgeSeconds": 86400
  }
]
```

The `Range` header in `AllowedHeaders` is the critical line — without it, the browser refuses to send range requests, DuckDB WASM can't fetch partial Parquet files, and every query returns nothing. This is the most common gotcha when setting up production for the first time.

---

## Part 7: What's the Same in Both Modes

This is the part that should feel reassuring. A very large portion of the codebase is **completely unaffected by which mode is active**.

### Identical in Both Modes

| Component                                     | Why                                                                         |
|-----------------------------------------------|-----------------------------------------------------------------------------|
| React components (Map, Sidebar, Charts, etc.) | Pure UI; doesn't care where data came from                                  |
| MapLibre GL rendering                         | Renders GeoJSON; source of GeoJSON is irrelevant                            |
| Recharts charts                               | Renders data arrays; source is irrelevant                                   |
| Tailwind CSS styles                           | CSS doesn't know about data sources                                         |
| URL hash routing (`/#/map?lat=...`)           | Hash state managed by React Router                                          |
| UX invariants from the 2011 UCD study         | Viewport-scoped results, single sidebar, labeled icons — all UI constraints |
| Playwright E2E tests                          | Tests interact with the UI; most don't care about data source               |
| Gherkin scenarios (user-visible behavior)     | Describe user-facing outcomes, not implementation                           |
| Photon geocoding (ADR-006)                    | Address → lat/lon is always client-side (browser-direct to Photon)         |

### Different Between Modes

| Component                 | Dev Mode                         | Production Mode                                 |
|---------------------------|----------------------------------|-------------------------------------------------|
| Data fetch implementation | `fetch('/api/v1/...')`           | `conn.query('SELECT ... FROM read_parquet...')` |
| Data storage              | PostgreSQL + PostGIS (Docker)    | Parquet files on Cloudflare R2                  |
| Query execution           | PostGIS (ST_DWithin on server)   | DuckDB WASM spatial (ST_DWithin in browser)     |
| Hosting                   | `docker compose up`              | Cloudflare Pages (static)                       |
| Backend process           | FastAPI (uvicorn)                | None                                            |
| Data freshness            | Instant (whatever's in the DB)   | Annual build cycle                              |
| `VITE_DATA_SOURCE`        | `api`                            | `duckdb`                                        |
| Test suite coverage       | All tests including schemathesis | E2E Playwright only (no FastAPI to test)        |

---

## Part 8: Practical Scenarios

### "I'm adding a new filter (e.g., NAICS sector code). What do I change?"

You need to change both paths:

1. **FastAPI route** — add `naics: str | None = None` to the query params in `routers/facilities.py`
2. **Service layer** — add `.where(Facility.naics_code == naics)` to the SQLAlchemy query in `services/facility_service.py`
3. **DuckDB query** — add `AND naics_code = $naics` to the Parquet query in `api/facilities.ts`
4. **React component** — add the NAICS filter input to `SearchPanel/`
5. **Acceptance test** — add a Gherkin scenario covering the new filter
6. **API contract** — update `TOXMAP_API_CONTRACT.md` with the new parameter

The service layer and DuckDB query are the two places that diverge. Both need to produce the same results for the same inputs.

### "I'm working on the chart UI. Do I need to worry about modes?"

No. Recharts gets an array of `{ year: number, total_release_lbs: number }` objects. It doesn't know or care whether those came from FastAPI or DuckDB WASM. Work against dev mode, run the Playwright tests, and the production path works automatically.

### "A Playwright E2E test is failing. Is it a dev mode bug or a production bug?"

If `VITE_DATA_SOURCE=api` (dev mode) and the test fails, the bug is in FastAPI, the service layer, or the React component. Fix it there.

If `VITE_DATA_SOURCE=duckdb` (production mode) and the test fails but dev mode passes, the DuckDB WASM query diverges from the FastAPI behavior. This is a data-fetch parity bug — fix the DuckDB query in `api/facilities.ts` to match what the API returns.

### "I want to test against the production data path locally."

```bash
# In frontend/.env.local (not committed), override:
VITE_DATA_SOURCE=duckdb
VITE_R2_BASE_URL=http://localhost:9000   # point at a local MinIO or R2 dev bucket

npm run dev
```

This runs the React app in DuckDB WASM mode against locally hosted Parquet files. You'll need to run the build script first to generate the Parquet files:

```bash
cd backend
python scripts/build_data.py --years 2022 --output ./parquet_local/
# Then serve them locally with: python -m http.server 9000 --directory ./parquet_local/
```

### "The DuckDB query is slow. How do I debug it?"

Open the browser DevTools Network tab. Look for requests to Cloudflare R2 with `Range: bytes=` headers. Each of those is DuckDB fetching a byte range from a Parquet file. If you see many small requests (50+), DuckDB is scanning too much metadata — the Parquet file may need better row group sizing. If you see one large request (many MB), the filter isn't using column pruning effectively.

DuckDB WASM exposes `EXPLAIN` and `EXPLAIN ANALYZE` the same way as regular DuckDB:

```typescript
const plan = await conn.query("EXPLAIN SELECT ... FROM read_parquet(...)");
console.table(plan.toArray());
```

---

## Part 9: The Deployment Sequence

ADR-004 defines the intended rollout order:

| Phase                          | What                                               | Cost |
|--------------------------------|----------------------------------------------------|------|
| **Now (development)**          | Docker Compose locally                             | $0   |
| **MVP (first public release)** | Cloudflare Pages + R2 + DuckDB WASM                | $0   |
| **If real-time data needed**   | + Fly.io (FastAPI) + Supabase (PostGIS, 20yr data) | $0   |

The project starts in Mode 1 (Docker Compose). The first public release deploys Mode 2 (static-first). Mode 3 (Fly.io + Supabase) is only introduced if a feature genuinely requires a live backend — user accounts, real-time notifications, or data updated more frequently than annually.

The reason this order matters: Mode 2 enforces discipline. Building the DuckDB WASM path forces the data model to be clean, the queries to be self-contained, and the frontend to be stateless. If you skip Mode 2 and go straight to Mode 3, you accumulate server-side state that becomes expensive to migrate away from later.

---

## Part 10: Mental Models to Take Away

**Mental model 1: The modes are a seam, not a fork.**  
The codebase is not two separate apps. It's one app with a thin abstraction layer (`resolveDataSource()` + the API client functions in `frontend/src/api/`) that swaps implementations. Everything above that seam is identical. Build features against dev mode; they work in production automatically.

**Mental model 2: Parquet files are "the database at rest."**  
In production there is no running database process, but there is still a database — it's just frozen into Parquet files on a CDN. DuckDB WASM is the query engine that knows how to read it. When you add a new table in dev (via an Alembic migration), you also need to add it to the Parquet build pipeline. Otherwise production doesn't get it.

**Mental model 3: DuckDB WASM is PostGIS's function-compatible sibling for our query set.**  
Every spatial function we use — `ST_DWithin`, `ST_Distance`, `ST_Point`, `ST_GeomFromText` — exists in both PostGIS and DuckDB's spatial extension with identical semantics. If a query returns correct results against PostGIS in dev, the same SQL returns correct results in DuckDB WASM in production. The two engines are interchangeable for our specific query patterns.

**Mental model 4: "No backend" doesn't mean "no logic."**  
Input validation, query construction, error handling, and data transformation all still exist in production — they've just moved from the FastAPI server into the React/TypeScript layer. The DuckDB query functions in `frontend/src/api/` are the production equivalent of the FastAPI service layer. They need the same care.

---

## Quick Reference

| Question                                     | Answer                                                                                                  |
|----------------------------------------------|---------------------------------------------------------------------------------------------------------|
| How do I start dev mode?                     | `docker compose up`                                                                                     |
| How do I know which mode is active?          | Check `VITE_DATA_SOURCE` in your `.env`                                                                 |
| Where does the mode switch happen in code?   | `frontend/src/lib/duckdbCompat.ts` → `resolveDataSource()`                                              |
| Where do DuckDB queries live?                | `frontend/src/api/*.ts` (each endpoint file)                                                            |
| Where do FastAPI routes live?                | `backend/app/routers/*.py`                                                                              |
| Where are Parquet files stored?              | Cloudflare R2 (`toxmap-data/` bucket)                                                                   |
| When are Parquet files rebuilt?              | GitHub Actions: August 15 (preliminary), October 20 (freeze), April 1 (spring refresh) + manual trigger |
| What controls whether the browser uses WASM? | `isDuckDBWasmSupported()` — tests for WASM SIMD support                                                 |
| What's the most common CORS mistake?         | Forgetting `Range` in R2 `AllowedHeaders`                                                               |
| Does the React UI change between modes?      | No — only the data-fetch layer changes                                                                  |
| Do Playwright tests run in both modes?       | E2E tests can run against either; most are mode-agnostic                                                |
| Where is the full decision record for this?  | [ADR-004](../adr/ADR-004-zero-budget-hosting.md)                                                        |

