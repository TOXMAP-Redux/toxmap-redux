# ADR-004: Zero-Budget Hosting Strategy

| Field          | Value                                                                                                           |
|----------------|-----------------------------------------------------------------------------------------------------------------|
| **ID**         | ADR-004                                                                                                         |
| **Title**      | Zero-Budget Hosting — Static-First on Cloudflare Pages + DuckDB WASM (Primary) or Fly.io + Supabase (Networked) |
| **Date**       | 2026-07-16                                                                                                      |
| **Status**     | **Accepted**                                                                                                    |
| **Deciders**   | Architecture Review                                                                                             |
| **Parent ADR** | [ADR-001](ADR-001-fastapi-postgis-react.md) (this ADR constrains the deployment target of ADR-001's stack)      |

> ⚠️ **Amendment — 2026-07-16:** The original framing of this ADR assumed TRI data is "read-only and updated once a year." 
> This is incorrect. Per the official [EPA TRI Data Considerations](https://www.epa.gov/trinationalanalysis/tri-data-considerations) 
> page: facilities submit revisions, withdrawals, and late submissions year-round via TRI-MEweb, and the EPA refreshes 
> the public database at multiple checkpoints — a preliminary release in July, multiple Aug–Oct refreshes, an October 
> data freeze (authoritative), and a spring data refresh incorporating retroactive corrections. EPA's own measurement 
> shows release quantities can differ by +1.4% and waste management quantities by +9% between an August preliminary 
> snapshot and the October freeze snapshot for the same reporting year. The static-file architecture remains valid 
> because TRI updates on a **predictable, known schedule** rather than in real-time. However, the build pipeline must 
> run at three checkpoints per year (August, October, April) rather than once annually, and all Parquet files must carry
> data vintage metadata. The `build_data.py` and GitHub Actions workflow in this ADR have been updated accordingly.

---

## Context

The project has a $0 budget. ADR-001 defines the application stack (FastAPI + PostGIS + React/MapLibre) but does not specify a deployment target. This ADR answers: **where does the app run if we cannot spend any money?**

Three viable zero-budget paths exist. They are not mutually exclusive — they can be adopted in sequence (localhost → free-tier PaaS → static-first) as the project matures.

**The desktop app question:** A desktop app (Electron or Tauri) is a fourth option. It is analyzed in §Option D and **not recommended as a primary path** — distribution friction is high and the static-first approach already works offline via a service worker.

---

## The Core Constraint: PostGIS

The biggest cost driver is the database. Full TRI history (1987–present, ~4M rows) requires:
- ~2 GB raw CSV
- ~800 MB as normalized PostgreSQL + PostGIS

Free database tiers that support PostGIS:

| Service                | Storage | PostGIS    | Cold Start             | Cost |
|------------------------|---------|------------|------------------------|------|
| **Supabase free**      | 500 MB  | ✅          | None                   | $0   |
| Neon.tech free         | 512 MB  | ⚠️ Limited | None                   | $0   |
| Render PostgreSQL free | 256 MB  | ✅          | None (90-day expiry)   | $0   |
| Railway free           | 512 MB  | ✅          | None ($5/month credit) | $0*  |
| ElephantSQL free       | 20 MB   | ❌          | None                   | $0   |

**500 MB holds approximately 5–7 years of TRI data** (not full 1987–present history). This is the binding constraint for all server-based options.

---

## Option A: Static-First — GitHub Pages + DuckDB WASM ✅ Recommended Primary

**The insight:** TRI data is read-only and released annually. There is no requirement for a live server — the data can be pre-processed into static files that a browser queries directly via WebAssembly.

### How It Works

```
Build pipeline (GitHub Actions, runs annually on TRI release):
  EPA TRI CSV
    └─► Python ingestion script
          ├─► Parquet files (TRI data, ~150 MB compressed)
          ├─► PMTiles file (map tile set, ~600 MB for US)
          └─► GeoJSON files (Superfund sites, census boundaries)

Runtime (browser only, no server):
  Browser
    ├─► React + MapLibre GL  ← Cloudflare Pages / GitHub Pages (free CDN)
    ├─► PMTiles tile source  ← Served from Cloudflare R2 free tier (10 GB free)
    └─► DuckDB WASM          ← Queries Parquet files via HTTP range requests
```

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│  GitHub Actions (annual build + on PR)                  │
│                                                         │
│  tri_ingest.py → facilities.parquet (per year)          │
│                → superfund.parquet                      │
│                → us_counties.geojson                    │
│                → tiles.pmtiles                          │
└────────────────────────┬────────────────────────────────┘
                         │ push to GitHub Releases / R2
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Static file hosting (free)                             │
│                                                         │
│  Cloudflare Pages    ← React app bundle (~2 MB)         │
│  Cloudflare R2       ← Parquet + PMTiles (~800 MB)      │
│  (10 GB free / month, HTTP range requests supported)    │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Browser                                                │
│                                                         │
│  MapLibre GL JS ─ PMTiles protocol            ──► tiles │
│  DuckDB WASM ─ HTTP range requests on Parquet ──► data  │
│  React 18    ─ UI state management                      │
│                                                         │
│  No server. No database. No cold starts.                │
└─────────────────────────────────────────────────────────┘
```

### DuckDB WASM Spatial Query Example

```typescript
// In the browser — no backend needed
import * as duckdb from "@duckdb/duckdb-wasm";

const db = await duckdb.createInMemory();
await db.open({ query: { castTimestampToDate: true } });

const conn = await db.connect();

// Load DuckDB spatial extension
await conn.query("INSTALL spatial; LOAD spatial;");

// Radius search — equivalent to PostGIS ST_DWithin
const results = await conn.query(`
  SELECT
    tri_facility_id,
    name,
    city,
    state_code,
    total_release_lbs,
    ST_Distance(
      ST_Point(lon, lat)::GEOGRAPHY,
      ST_Point($lon, $lat)::GEOGRAPHY
    ) / 1609.34 AS distance_miles
  FROM read_parquet('https://r2.toxmap.pages.dev/tri/2022.parquet')
  WHERE chemical_name = $chemical
    AND ST_DWithin(
      ST_Point(lon, lat)::GEOGRAPHY,
      ST_Point($lon, $lat)::GEOGRAPHY,
      $radius_meters
    )
  ORDER BY total_release_lbs DESC
`, { lat: 39.2197, lon: -76.4785, chemical: "LEAD COMPOUNDS", radius_meters: 16093.4 });
```

### Free Services Used

| Service | What For | Free Tier |
|---------|---------|-----------|
| **Cloudflare Pages** | React app hosting | Unlimited requests, unlimited bandwidth |
| **Cloudflare R2** | Parquet + PMTiles static files | 10 GB storage, 10M reads/month — free forever |
| **Cloudflare Workers** | Optional geocoding proxy (ADR-009) | 100K requests/day — enables global cache + rate limiting |
| **GitHub Actions** | Annual data build + CI | 2,000 min/month free |
| **GitHub Releases** | Parquet file versioning | Unlimited storage for public repos |
| **Protomaps** | US basemap tile generation | Open-source tool, self-run |
| **Photon (Komoot)** | Geocoding (ADR-006) | Free, fair-use policy |
| **OpenFreeMap** | Basemap tiles (ADR-005) | Free, no limits stated |

**Total monthly cost: $0.00**

### Tradeoffs

**✅ Advantages:**
- Truly $0 forever — no server, no DB, no cold starts, no expiry
- Works offline via service worker after first load
- Scales infinitely via CDN (Cloudflare handles traffic spikes)
- No backend security surface (no server to compromise)
- Full TRI history (1987–present) fits in ~800 MB Parquet
- DuckDB WASM spatial extension covers all required queries

**❌ Disadvantages:**
- First query per session requires downloading Parquet range (~5–20 MB, depending on filter)
- DuckDB WASM startup: ~1–2 seconds cold (cached thereafter)
- No real-time data — data currency is bounded by the EPA's update schedule (preliminary July, authoritative October freeze, spring refresh); 3 builds/year required rather than 1
- Parquet files must carry vintage metadata (.meta.json sidecar) to inform users of data currency; omitting this is a data integrity issue
- Superfund + Census GeoJSON needs separate handling (small files, fine)
- `restrict_to_state` and `bbox` filtering done client-side (not an issue with DuckDB)
- Export to CSV is client-side streaming (works fine with DuckDB WASM)

### ADR-001 Changes Required

Option A **replaces the FastAPI backend entirely**. Changes to ADR-001:
- `Backend API`: FastAPI → DuckDB WASM (in-browser)
- `Database`: PostgreSQL + PostGIS → Parquet files on Cloudflare R2
- `Data Ingestion`: pandas/geopandas → same Python script, output is `.parquet` not SQL
- `Deployment`: Docker Compose → `npm run build` + Cloudflare Pages deploy

The React frontend, MapLibre GL, Recharts, and all UX architecture decisions are **unchanged**.
### Cloudflare R2 CORS Configuration (M-1)

DuckDB WASM issues HTTP range requests (`Range: bytes=...`) from the browser to R2. Without CORS headers, the browser blocks these requests. Apply the following CORS policy to the R2 bucket via the Cloudflare dashboard or `wrangler`:

```json
[
  {
    "AllowedOrigins": [
      "https://toxmap.pages.dev",
      "http://localhost:3000"
    ],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["Range", "Content-Type"],
    "ExposeHeaders": ["Content-Length", "Content-Range", "Accept-Ranges"],
    "MaxAgeSeconds": 86400
  }
]
```

**Via `wrangler` CLI:**
```bash
wrangler r2 bucket cors put toxmap-data --rules '[{"AllowedOrigins":["https://toxmap.pages.dev","http://localhost:3000"],"AllowedMethods":["GET","HEAD"],"AllowedHeaders":["Range","Content-Type"],"ExposeHeaders":["Content-Length","Content-Range","Accept-Ranges"],"MaxAgeSeconds":86400}]'
```

**Note:** Add `http://localhost:3000` to `AllowedOrigins` for local development; remove it before production deployment if strict security is required.

### DuckDB WASM Browser Compatibility Check (9.3)

The DuckDB spatial extension requires **WebAssembly SIMD** (Single Instruction Multiple Data). Safari on iOS < 15 and some older Android browsers do not support WASM SIMD. The app must detect support at startup and fall back gracefully to the Fly.io API (Option B) if WASM is unavailable.

```typescript
// frontend/src/lib/duckdbCompat.ts

/**
 * Tests whether the current browser supports WebAssembly SIMD,
 * which is required by the DuckDB spatial extension.
 * Falls back to Option B (Fly.io FastAPI) if unsupported.
 */
export async function isDuckDBWasmSupported(): Promise<boolean> {
  if (typeof WebAssembly === 'undefined') return false;
  try {
    // Minimal WASM SIMD test module (v128 type + i32x4 splat instruction)
    const simdTest = new Uint8Array([
      0, 97, 115, 109, 1, 0, 0, 0,  // WASM magic + version
      1, 5, 1, 96, 0, 1, 123,        // type section: () -> v128
      3, 2, 1, 0,                    // function section
      10, 10, 1, 8, 0, 65, 0,        // code section: i32.const 0
      253, 15, 253, 98, 11,          // i32x4.splat, i8x16.popcnt, end
    ]);
    await WebAssembly.instantiate(simdTest);
    return true;
  } catch {
    return false;
  }
}

/**
 * Determine the active data source based on browser capability and
 * the VITE_DATA_SOURCE environment variable.
 * - "duckdb": use DuckDB WASM (production default, Option A)
 * - "api":    use Fly.io FastAPI (Option B fallback or local dev)
 */
export async function resolveDataSource(): Promise<'duckdb' | 'api'> {
  const envOverride = import.meta.env.VITE_DATA_SOURCE;
  const VALID_SOURCES = ['api', 'duckdb'] as const;
  if (envOverride && !VALID_SOURCES.includes(envOverride as 'api' | 'duckdb')) {
    console.warn(`VITE_DATA_SOURCE="${envOverride}" is not valid; must be "api" or "duckdb". Defaulting to DuckDB WASM.`);
  }
  if (envOverride === 'api') return 'api';
  if (envOverride === 'duckdb') {
    const supported = await isDuckDBWasmSupported();
    if (!supported) {
      console.warn('DuckDB WASM SIMD not supported in this browser; falling back to API');
      return 'api';
    }
    return 'duckdb';
  }
  // Default: try DuckDB, fall back to API
  return (await isDuckDBWasmSupported()) ? 'duckdb' : 'api';
}
```

**Browser compatibility matrix:**

| Browser | WASM SIMD | DuckDB Spatial | Data Source |
|---------|-----------|----------------|-------------|
| Chrome 91+ / Edge 91+ | ✅ | ✅ | DuckDB WASM |
| Firefox 90+ | ✅ | ✅ | DuckDB WASM |
| Safari 16.4+ (macOS/iOS) | ✅ | ✅ | DuckDB WASM |
| Safari iOS 15.x | ⚠️ Partial | ⚠️ May fail | Falls back to API |
| Safari iOS < 15 | ❌ | ❌ | API (Option B) |
| Chrome Android 91+ | ✅ | ✅ | DuckDB WASM |

---

## Option B: Free-Tier PaaS — Cloudflare Pages + Fly.io + Supabase

Use if you need a **live searchable API** (e.g., for real-time data updates or multi-user state) and are willing to accept the 500 MB Supabase database constraint.

### Stack

```
Frontend:  Cloudflare Pages (React + MapLibre)  — free, unlimited
API:       Fly.io (FastAPI, 256 MB RAM)          — free: 3 shared VMs, 160 GB outbound
Database:  Supabase (PostgreSQL 16 + PostGIS)    — free: 500 MB, 2 GB egress/month
```

> ⚠️ **ADR-002 (Spring Modulith) is incompatible with this option.** The standard Spring Boot JVM uses ~280 MB at idle — exceeding Fly.io's 256 MB free VM limit before handling a single request. GraalVM native compilation can reduce this to ~90 MB but requires weeks of Hibernate Spatial reflection configuration. See [ADR-002 §Zero-Budget Hosting Compatibility](ADR-002-spring-modulith-postgis.md) for the full analysis. **FastAPI (ADR-001) is the only viable backend choice for Option B at $0.**

### Fly.io FastAPI Deployment

```toml
# fly.toml
app = "toxmap-api"
primary_region = "iad"  # Washington DC — closest to EPA data users

[build]
  dockerfile = "backend/Dockerfile"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true   # stops after 5min idle — cold start ~2sec
  auto_start_machines = true
  min_machines_running = 0    # $0 when idle

[vm]
  memory = "256mb"
  cpu_kind = "shared"
  cpus = 1
```

### Data Size vs. Supabase 500 MB Limit

| Data Type | Approximate Size | Notes |
|-----------|------------------|-------|
| TRI (latest year only) | ~15 MB | 2024 data |
| TRI (5 years: 2020–2024) | ~75 MB | |
| TRI (10 years: 2015–2024) | ~150 MB | |
| TRI (20 years: 2005–2024) | ~300 MB | Recommended subset |
| TRI (full history: 1987–2024) | ~800 MB | ❌ Exceeds 500 MB |
| **Census demographics** | **~100 MB** | TIGER boundaries + ACS data |

**Storage budget for Supabase 500 MB free tier:**
- TRI 20-year (2005–2024): ~300 MB
- Census (one year): ~100 MB
- **Total:** ~400 MB ✅ (tight but fits)

**Recommendation:** Load TRI 2005–present (~300 MB) + Census 2020 (~100 MB) = ~400 MB. For multiple census years or pre-2005 TRI data, use Option A (Parquet files on R2).

> **Note:** Census ingestion peaks at ~250–300 MB RAM. Do NOT run `census_ingest.py` on Fly.io's 256 MB free-tier VMs — run locally via Docker Compose, then connect to Supabase with `--db-url`.

### Tradeoffs

**✅ Advantages:**
- ADR-001 stack unchanged — FastAPI, PostGIS, same API contract
- All 57 acceptance tests run against the live API
- Supabase dashboard for data inspection
- Easier to add real-time features later (Supabase realtime)

**❌ Disadvantages:**
- Fly.io free VM has 256 MB RAM — fine for API, tight for concurrent geospatial queries
- Fly.io cold start: ~2 seconds after idle (set `min_machines_running = 1` to avoid, but uses free quota)
- Supabase 500 MB = ~20 years TRI + 1 census year max (400 MB combined)
- Census ingestion must run locally (exceeds Fly.io 256 MB RAM) — cannot ingest census data directly on Fly.io
- Supabase free tier pauses after 1 week of inactivity (must unpause manually)
- Combined free tier limits are easily exceeded with moderate traffic

---

## Option C: Localhost — Docker Compose (Developer / Demo Use)

Already defined in ADR-001. The right choice for:
- Individual developers running the full stack locally
- Conference demos or presentations
- Contributors testing against the full dataset

**No hosting required. $0 forever. Unlimited data.**

```bash
# One-command startup
docker compose up

# Ingest latest TRI data
docker compose exec backend python -m ingestion.tri_ingest --year 2024

# App available at http://localhost:3000
```

**Limitation:** Not shareable — only the person running Docker Compose can use it.

---

## Option D: Desktop App — Tauri + DuckDB (Not Recommended as Primary)

A Tauri desktop app wraps the React frontend in a Rust shell with a bundled DuckDB database. This is effectively Option A (DuckDB) packaged for offline installation.

### Why Tauri Instead of Electron

| | Electron | Tauri |
|---|---------|-------|
| App size | ~150 MB | ~10–15 MB |
| RAM usage | ~200 MB base | ~50 MB base |
| Language | Node.js | Rust |
| WebView | Bundled Chromium | OS WebView (WebKit/Edge) |

### When to Choose This

- Users have no internet access (field researchers, government networks)
- Users want to work with the full 1987–present dataset offline
- Distribution to non-technical users who won't run Docker

### When NOT to Choose This

- You want shared/collaborative access
- You want zero distribution friction (no installer)
- Option A (static-first with service worker) already works offline after first load

**Verdict:** Option A solves the offline use case without the distribution overhead of a desktop app installer. If a native app is specifically required later, Tauri can wrap the same React codebase.

---

## Option E: Spring Modulith Desktop App — Fat Jar + Embedded Database

Two concrete variants exist. Both involve shipping a self-contained Java application that the user runs locally, with the React frontend served by the embedded Spring Boot server and opened in the user's default browser.

### Variant E-1: Spring Modulith Fat Jar + H2 Spatial (Pure Java, No External DB)

```
User runs: java -jar toxmap.jar
Spring Boot starts → serves React on http://localhost:8080
Browser opens automatically
H2 in-process spatial database backs all queries
```

**What H2 Spatial supports for this use case:**

| Query | PostGIS | H2 Spatial | Status |
|-------|---------|-----------|--------|
| `ST_DWithin` (radius search) | ✅ | ✅ | Required — covered |
| `ST_GeomFromText` | ✅ | ✅ | Required — covered |
| `ST_Distance` | ✅ | ✅ | Required — covered |
| `ST_Contains` (bbox filter) | ✅ | ✅ | Required — covered |
| `GIST index` | ✅ | ❌ (uses R-tree) | Performance difference only |
| `ST_ClusterDBSCAN` | ✅ | ❌ | Not required — clustering is client-side in MapLibre |
| `ST_Transform` (reprojection) | ✅ | ✅ | Covered |

H2 Spatial covers **all queries we actually need**. The missing functions (`ClusterDBSCAN`) are handled client-side by MapLibre GL anyway.

**Distribution size:**

| Component | Size |
|-----------|------|
| Spring Boot fat jar | ~80 MB |
| H2 database jar (bundled) | ~8 MB |
| React build (bundled in `resources/static/`) | ~5 MB |
| TRI data (SQLite/H2 file, 10 years) | ~150 MB |
| **Total without JRE** | **~243 MB** |
| JRE 21 (bundled via `jlink`) | ~50–70 MB |
| **Total with bundled JRE** | **~310 MB** |

Compare: Tauri + DuckDB = **~18 MB total** (data file separate).

### Variant E-2: Spring Modulith Fat Jar + Embedded PostgreSQL + PostGIS

Uses `io.zonky.test:embedded-postgresql` to start an embedded PostgreSQL process with PostGIS extension automatically. Full PostGIS compatibility, no query changes from ADR-001.

```java
// Auto-starts an embedded PostgreSQL with PostGIS on app launch
@Bean
public EmbeddedPostgres embeddedPostgres() throws IOException {
    return EmbeddedPostgres.builder()
        .setPort(15432)
        .start();
}
```

**Distribution size:**

| Component | Size |
|-----------|------|
| Spring Boot fat jar | ~80 MB |
| Embedded PostgreSQL binaries | ~50 MB |
| PostGIS extension | ~20 MB |
| React build | ~5 MB |
| TRI data (10 years) | ~250 MB |
| JRE 21 (bundled) | ~65 MB |
| **Total** | **~470 MB** |

### Option E Competitive Analysis

| Criterion | Option A (Static+WASM) | Option D (Tauri+DuckDB) | E-1 (Fat Jar+H2) | E-2 (Fat Jar+PG) |
|-----------|----------------------|------------------------|-----------------|-----------------|
| Distribution size | 0 MB (browser) | ~18 MB | ~310 MB | ~470 MB |
| Install required | ❌ | ✅ installer | ✅ (`java -jar`) | ✅ (`java -jar`) |
| JRE required | ❌ | ❌ | ✅ (or bundle) | ✅ (or bundle) |
| Full TRI history | ✅ (Parquet on R2) | ✅ (bundled) | ⚠️ (size grows) | ⚠️ (size grows) |
| Offline use | ✅ (service worker) | ✅ | ✅ | ✅ |
| PostGIS queries | DuckDB spatial | DuckDB spatial | H2 spatial | ✅ Full PostGIS |
| Cold start | ~1s (WASM) | <1s | ~5–8s (JVM) | ~10–15s (JVM+PG) |
| MapLibre GL WebGL | ✅ (browser) | ⚠️ (OS WebView*) | ✅ (user's browser) | ✅ (user's browser) |
| Team language | Any | Any + Rust | Java only | Java only |
| $0 budget | ✅ | ✅ | ✅ | ✅ |

> *Tauri uses the OS WebView (WebKit on macOS/Linux, Edge on Windows). WebKit on macOS supports WebGL; Edge on Windows supports WebGL. MapLibre GL works on both.

### The One Scenario Where Option E Wins

Option E-1 or E-2 is the **correct choice** when **all** of the following are true:

1. The team is exclusively Java and will not introduce Python, Rust, or TypeScript build tooling
2. Distribution to non-technical users who cannot run `docker compose up` or open a browser
3. True air-gap requirement (no internet, ever — not just "works offline after first load")
4. The project grows into a broader platform requiring Spring Modulith's hard module boundaries across 5+ data domains

If **any** of those four conditions is false, Option A or D is better.

### Verdict: Not Competitive for This Project

Option E is not competitive for the ToxMap clone because:

1. **Size vs. function ratio is poor** — 310–470 MB for functionality that Tauri + DuckDB delivers in 18 MB
2. **JVM cold start** — 5–15 seconds before the app is usable; unacceptable for a map explorer
3. **The Python pipeline exists anyway** — ingestion always runs in Python (geopandas). A Java-only team would still need Python for data builds.
4. **Option A already solves offline** — service worker caches enough for offline use post-first-visit, without any install
5. **GraalVM native** could shrink E-1 to ~80 MB with <100ms startup — bringing it closer to Tauri — but adds weeks of Hibernate Spatial native configuration work, eliminating the "Java team familiarity" advantage

**If a pure-Java desktop path is ever needed**, the correct progression is: E-1 (H2 Spatial) with GraalVM native compilation. This produces a ~80 MB binary with sub-second startup. But this is a future option, not a Day 1 choice.

---

## Decision

**Adopt in this sequence:**

| Phase | Deployment | Cost | When |
|-------|-----------|------|------|
| **Now** | Option C (Docker Compose localhost) | $0 | Development + testing |
| **MVP** | Option A (Cloudflare Pages + R2 + DuckDB WASM) | $0 | First public release |
| **If API needed** | Option B (+ Fly.io + Supabase, 20yr data) | $0 | If real-time features required |
| **If air-gap + Java-only team** | Option E-1 (Fat Jar + H2 Spatial + GraalVM native) | $0 | Future — if all 4 conditions in §Option E met |

Option A is the **primary zero-budget hosting target** because:
1. $0 forever with no expiry, no pausing, no credit limits
2. Full TRI history (1987–present) — no data truncation
3. No cold starts — pure CDN + WASM
4. Offline-capable via service worker after first visit
5. Same React/MapLibre frontend from ADR-001, unchanged

---

## Migration Path: ADR-001 → Option A

The only component that changes is the **API layer**. The migration is additive, not a rewrite:

```
ADR-001 (FastAPI + PostGIS)        Option A (DuckDB WASM)
────────────────────────────       ──────────────────────────────
GET /api/v1/facilities          →  useQuery('SELECT ... FROM parquet WHERE ST_DWithin...')
GET /api/v1/chemicals/search    →  useQuery('SELECT ... FROM chemicals.parquet WHERE name ILIKE')
GET /api/v1/superfund           →  useQuery('SELECT ... FROM superfund.parquet WHERE ST_DWithin')
GET /api/v1/demographics/county →  fetch('counties.geojson') (small file, no query needed)
GET /api/v1/export/csv          →  duckdb.export_csv() (client-side)
```

**Keep FastAPI for local development** — it's still the correct tool for running acceptance tests and development. The Parquet/DuckDB path is the production deployment target.

### Build Pipeline (`build_data.py`)

```python
# Runs in GitHub Actions at three EPA data checkpoints per year (Aug preliminary, Oct freeze, Apr spring refresh).
# ⚠️ TRI data is NOT read-only — facilities revise submissions year-round via TRI-MEweb.
# The October freeze is the authoritative dataset. Do not treat a single annual August build as sufficient.
# Source: EPA TRI Data Considerations — https://www.epa.gov/toxics-release-inventory-tri-program/tri-data-considerations
import geopandas as gpd
import pandas as pd
import json
from datetime import date

def build_parquet(year: int, output_dir: str, vintage_label: str) -> None:
    """Convert TRI CSV to Parquet for DuckDB WASM consumption.

    Args:
        year: TRI reporting year (e.g., 2022)
        output_dir: local output directory
        vintage_label: describes the EPA data snapshot used, e.g. "October 2024 freeze".
                       Displayed in the UI. ⚠️ Never omit — a file without vintage context is ambiguous.
    """
    df = pd.read_csv(f"tri_{year}.csv", dtype=str, low_memory=False)
    df = clean_tri_dataframe(df)
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])

    # Write per-year Parquet — DuckDB WASM uses HTTP range requests
    # so per-year files enable efficient year filtering
    df.to_parquet(
        f"{output_dir}/tri_{year}.parquet",
        compression="snappy",
        index=False
    )

    # Write vintage sidecar — read by React app to display data currency in the UI
    meta = {
        "tri_reporting_year": year,
        "epa_vintage_label": vintage_label,
        "build_date": date.today().isoformat(),
        "record_count": len(df),
    }
    with open(f"{output_dir}/tri_{year}.meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Built {output_dir}/tri_{year}.parquet ({len(df):,} records, vintage: {vintage_label})")

# TRI_COLUMN_MAP: maps raw EPA CSV column names to normalized field names.
# Column names vary slightly by year; update this dict when EPA changes their schema.
TRI_COLUMN_MAP = {
    "4. FACILITY NAME": "name",
    "6. FACILITY STREET": "address",
    "7. FACILITY CITY": "city",
    "8. ST": "state_code",
    "9. ZIP": "zip_code",
    "10. COUNTY": "county",
    "12. LATITUDE": "lat",
    "13. LONGITUDE": "lon",
    "15. TRI FACILITY ID": "tri_facility_id",
    "22. INDUSTRY SECTOR CODE": "naics_code",
    # ... extend as needed per year
}

def clean_tri_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize TRI CSV column names and drop rows with missing or invalid coordinates.
    Operations: rename columns per TRI_COLUMN_MAP, coerce lat/lon to float,
    drop rows where lat or lon is NaN or outside plausible US bounds."""
    df = df.rename(columns=TRI_COLUMN_MAP)
    df["lat"] = pd.to_numeric(df.get("lat"), errors="coerce")
    df["lon"] = pd.to_numeric(df.get("lon"), errors="coerce")
    df = df.dropna(subset=["lat", "lon"])
    # Plausibility filter: continental US + Alaska + Hawaii + territories
    df = df[(df["lat"].between(-25, 72)) & (df["lon"].between(-180, -60))]
    return df
```

### GitHub Actions Workflow

```yaml
# .github/workflows/build-data.yml
name: Build TRI Data

on:
  schedule:
    # ⚠️ Three triggers required — see TRI data cadence note below.
    # Source: EPA TRI Data Considerations (https://www.epa.gov/toxics-release-inventory-tri-program/tri-data-considerations)
    - cron: "0 0 15 8 *"   # Aug 15: preliminary dataset (raw, incomplete — label clearly; not for primary production build)
    - cron: "0 0 20 10 *"  # Oct 20: after EPA data freeze — authoritative dataset for National Analysis (PRIMARY build)
    - cron: "0 0 1 4 *"    # Apr 1:  after spring data refresh — retroactive corrections to prior years
  workflow_dispatch:
    inputs:
      years:
        description: "TRI years to rebuild (e.g. '2020 2021 2022' or 'latest')"
        default: "latest"
      vintage_label:
        description: "Human-readable vintage label shown in UI (e.g. 'October 2024 freeze')"
        required: true

# TRI DATA CADENCE NOTE:
# TRI data is NOT read-only and is NOT updated only once a year.
# - Facilities submit revisions, withdrawals, and late submissions via TRI-MEweb year-round.
# - July 1: Reporting deadline; EPA releases preliminary dataset.
# - July–October: EPA processes late submissions; public database refreshed multiple times.
# - October: Data quality review complete; dataset FROZEN for National Analysis.
# - Following Spring: Spring data refresh incorporates post-freeze changes; reflected in next year's analysis.
# - Multi-year ongoing: Historical data receives retroactive corrections continuously.
# Measured drift (EPA): Oct 2023 → Oct 2024 for 2022 data: +9% waste management, +1.4% release quantities.
# The October freeze is the authoritative source; August preliminary is incomplete.
# All Parquet files must include vintage metadata (.meta.json sidecar) to identify the EPA snapshot used.

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install pandas geopandas pyarrow
      - run: python scripts/build_data.py --years ${{ inputs.years || 'latest' }} --vintage "${{ inputs.vintage_label || 'Automated build' }}"
      - name: Upload to Cloudflare R2
        uses: cloudflare/wrangler-action@v3
        with:
          command: r2 object put toxmap-data/ --recursive dist/parquet/
          apiToken: ${{ secrets.CF_API_TOKEN }}
```

---

## Consequences

### Positive (Option A)
- Zero ongoing cost — no credit card, no vendor lock-in beyond free Cloudflare tier
- Works offline after first page load (service worker caches WASM + small Parquet chunks)
- Eliminates backend security surface entirely
- Full 1987–present TRI history at no extra cost
- CDN-native — every user gets sub-100ms tile delivery worldwide
- Open-source contributors can run it with `npm start` — no Docker, no DB setup

### Negative (Option A)
- DuckDB WASM first-query latency: ~1–2 seconds cold (acceptable; cached on repeat queries)
- Parquet HTTP range queries require CORS headers on R2 — one-time config
- Loss of server-side query validation — must validate inputs in the React layer
- Real-time data updates (if ever needed) require a backend re-introduction

### Neutral
- The [TOXMAP_ACCEPTANCE_TESTS.md](../testing/TOXMAP_ACCEPTANCE_TESTS.md) API layer tests still apply against the FastAPI dev server; E2E Playwright tests apply unchanged against the static build

---

## Alternatives Considered

- **Vercel + PlanetScale**: PlanetScale discontinued free tier 2024; rejected
- **Netlify Functions + FaunaDB**: No PostGIS/spatial support; rejected
- **Heroku free tier**: Eliminated free tier 2022; rejected
- **Google Cloud free tier (Cloud Run + Cloud SQL)**: Cloud SQL has no free tier; rejected
- **AWS free tier**: 12-month expiry only; rejected
- **Electron desktop app**: 150MB installer vs. 10MB Tauri vs. 0MB static; rejected for primary path

