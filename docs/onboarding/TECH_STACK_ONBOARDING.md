# TOXMAP Clone — Tech Stack Onboarding Guide

**Audience:** Junior engineers new to the project  
**Last Updated:** 2026-07-16  
**Related Docs:** [ADR-001](../adr/ADR-001-fastapi-postgis-react.md) · [ADR-004](../adr/ADR-004-zero-budget-hosting.md)

---

## What Are We Building?

TOXMAP is an open-source clone of a tool originally built by the National Library of Medicine (NLM/NIH) and 
decommissioned in 2019. It lets the public explore EPA Toxic Release Inventory (TRI) data on an interactive map — find
out which facilities near you released chemicals into the air, water, or land, in what quantities, and over time.

The original was built on proprietary ESRI software and Adobe Flash. We're rebuilding it entirely with open-source 
tools, $0 hosting, and modern standards.

---

## The Two Modes: Dev vs. Production

One of the first things to understand is that the app runs in **two different modes**, and the architecture differs meaningfully between them:

| Mode                    | When                  | Data Layer                     | Hosting               |
|-------------------------|-----------------------|--------------------------------|-----------------------|
| **Development / Local** | Your laptop, CI tests | FastAPI → PostgreSQL + PostGIS | Docker Compose        |
| **Production**          | Live site             | DuckDB WASM (in the browser)   | Cloudflare Pages + R2 |

In production there is **no server at all**. TRI data is pre-processed into Parquet files and served from static file 
storage. The browser runs a SQL engine via WebAssembly to query those files directly. This is what keeps our hosting 
cost at exactly $0.

> ⚠️ **Common misconception:** TRI data is not simply "read-only and updated once a year." Facilities can revise their
> submissions year-round, and the EPA updates the public database at multiple checkpoints: a preliminary release in 
> July, multiple refreshes through October, a quality-frozen dataset in October, and a spring data refresh the following
> year. The static-file approach is valid because TRI updates on a **known, predictable schedule** — not because data 
> never changes. The build pipeline must run at each EPA checkpoint, not once annually. See 
> [TWO_MODES_DEEP_DIVE.md](TWO_MODES_DEEP_DIVE.md) for the full picture.

The architecture diagrams in [ADR-004](../adr/ADR-004-zero-budget-hosting.md) explain this in full. For local development, just use Docker Compose — the
database is running on your machine.

> **Go deeper:** [TWO_MODES_DEEP_DIVE.md](TWO_MODES_DEEP_DIVE.md) covers the why, when, and how of both modes in full 
> detail — recommended reading once you've finished this document.

---

## Architecture at a Glance

```
LOCAL / CI                              PRODUCTION
──────────────────────────────────────  ──────────────────────────────────────
Browser (React + MapLibre + Recharts)   Browser (React + MapLibre + Recharts)
         │ REST/JSON                             │ HTTP range requests
         ▼                                       ▼
FastAPI (Python 3.12)           ←→      DuckDB WASM (in-browser SQL)
         │ SQLAlchemy (async)                    │
         ▼                                       ▼
PostgreSQL 16 + PostGIS 3.4             Parquet files on Cloudflare R2
```

---

## The Backend Stack

### Python 3.12

We write the entire backend in Python. Python is the dominant language in the data and geospatial world — the ecosystem 
of libraries for working with geographic data (geopandas, shapely, GeoAlchemy2) is unmatched in any other language. All 
backend code lives under `backend/`.

**Learn more:** [Python 3.12 docs](https://docs.python.org/3.12/)

---

### FastAPI

**What it is:** A modern Python web framework for building HTTP APIs. You define an endpoint as a function, add type 
annotations, and FastAPI handles routing, request parsing, validation, and documentation generation automatically.

**Why we use it:** It's async-first (important for database-heavy workloads), generates an OpenAPI spec automatically 
(`/docs` in your browser), and is exceptionally fast to prototype with. The entire API contract in
[`TOXMAP_API_CONTRACT.md`](../api/TOXMAP_API_CONTRACT.md) is implemented with FastAPI routers.

**Key concept — async:** Our FastAPI handlers use Python's `async/await` syntax so they don't block while waiting on the
database. If you haven't worked with async Python before, read the FastAPI async guide linked below.

```python
# Example: a FastAPI route handler
@router.get("/facilities")
async def get_facilities(lat: float, lon: float, radius_miles: float = 25):
    results = await facility_service.get_near(lat, lon, radius_miles)
    return results
```

**Learn more:** [FastAPI docs (start with "First Steps")](https://fastapi.tiangolo.com/tutorial/first-steps/)

---

### Pydantic v2

**What it is:** A data validation library. You declare a model class with typed fields, and Pydantic validates that 
incoming JSON matches those types — and will give a clear error message if it doesn't.

**Why we use it:** FastAPI is built on Pydantic. Every request body and response shape in our API is defined as a 
Pydantic model. This is your contract with the frontend.

```python
# Example: a Pydantic response schema
class FacilityResponse(BaseModel):
    tri_facility_id: str
    name: str
    city: str
    state_code: str
    total_release_lbs: float | None
```

**Learn more:** [Pydantic v2 docs](https://docs.pydantic.dev/latest/)

---

### PostgreSQL 16 + PostGIS 3.4

**What it is:** PostgreSQL is the world's most advanced open-source relational database. PostGIS is an extension that 
adds geographic data types and spatial functions — it turns PostgreSQL into a full GIS (Geographic Information System)
database.

**Why we use it:** TRI data is inherently geographic. Every facility has a latitude/longitude. PostGIS lets us write 
SQL like:

```sql
-- "Give me all facilities within 25 miles of this point"
SELECT * FROM facilities
WHERE ST_DWithin(
  ST_Transform(location, 3857),
  ST_Transform(ST_GeomFromText('POINT(-76.47 39.22)', 4326), 3857),
  40233.6  -- 25 miles in meters
);
```

This runs in under 50ms against 90,000+ facilities because of a spatial index (GIST index on the `location` column). 
You cannot achieve this performance with a simple lat/lon column and a `WHERE` clause.

**Key types to know:**
- `GEOMETRY(POINT, 4326)` — stores a lat/lon point in [WGS84 (EPSG:4326)](https://epsg.io/4326), the coordinate system GPS uses
- `GEOMETRY(MULTIPOLYGON, 4326)` — stores a polygon (e.g., a county boundary)
- `GIST index` — a spatial index that makes geographic queries fast

**Learn more:**
- [PostgreSQL tutorial](https://www.postgresql.org/docs/current/tutorial.html)
- [PostGIS intro](https://postgis.net/workshops/postgis-intro/)

---

### SQLAlchemy 2.0 (async) + GeoAlchemy2

**What it is:** SQLAlchemy is the standard Python ORM (Object-Relational Mapper). You define your database tables as 
Python classes, and SQLAlchemy translates Python operations into SQL. GeoAlchemy2 adds PostGIS geometry types and 
spatial functions to SQLAlchemy.

**Why we use it:** Without an ORM we'd write raw SQL strings everywhere, which is error-prone and hard to refactor. 
SQLAlchemy gives us type-safe, composable queries.

```python
# ORM model definition
class Facility(Base):
    __tablename__ = "facilities"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    location: Mapped[WKBElement] = mapped_column(Geometry("POINT", srid=4326))
```

**Note on "async":** SQLAlchemy 2.0 introduced first-class `async/await` support. We use `AsyncSession` everywhere — 
this is more complex than the classic synchronous API. If you see `await session.execute(...)`, that's the async pattern.

**Learn more:**
- [SQLAlchemy 2.0 ORM quickstart](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
- [GeoAlchemy2 docs](https://geoalchemy-2.readthedocs.io/)

---

### Alembic

**What it is:** A database migration tool that pairs with SQLAlchemy. When you change a model (add a column, create a 
table), you write a migration file that describes that change. Alembic applies migrations in order so every environment
(your laptop, CI, production) stays in sync.

**Why we use it:** Never modify the database schema directly in psql. Always create a migration. This makes schema 
changes reviewable, reversible, and reproducible.

```bash
# Create a new migration after changing a model
alembic revision --autogenerate -m "add naics_desc to facilities"

# Apply all pending migrations
alembic upgrade head
```

**Learn more:** [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)

---

### pandas + geopandas (Data Ingestion)

**What they are:** pandas is the standard Python library for tabular data manipulation (think: programmable Excel). 
geopandas extends pandas with geographic geometry columns and spatial operations.

**Why we use them:** The EPA releases TRI data as bulk CSV files — millions of rows per year. We use pandas to parse, 
clean, and reshape these CSVs, and geopandas to handle coordinate reprojection and load the results into PostGIS.

```python
# Ingestion pipeline sketch
df = pd.read_csv("tri_2022.csv", dtype=str)
df["lat"] = pd.to_numeric(df["LATITUDE"], errors="coerce")
df["lon"] = pd.to_numeric(df["LONGITUDE"], errors="coerce")
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lon"], df["lat"]), crs="EPSG:4326")
gdf.to_postgis("facilities_staging", engine, if_exists="replace")
```

The ingestion scripts live in `backend/ingestion/`. You rarely touch them day-to-day, but knowing they exist is important.

**Learn more:**
- [pandas getting started](https://pandas.pydata.org/docs/getting_started/index.html)
- [geopandas intro](https://geopandas.org/en/stable/getting_started/introduction.html)

---

## The Frontend Stack

### React 18 + TypeScript

**What it is:** React is the dominant JavaScript UI library. TypeScript adds static types to JavaScript — it catches 
bugs at compile time that would otherwise blow up at runtime in the browser.

**Why we use it:** React's component model is a good fit for a complex, stateful map application with many interactive
panels. TypeScript is non-negotiable on any project where correctness matters — our API responses are typed so the 
compiler tells you if you're reading a field that doesn't exist.

All frontend code lives under `frontend/src/`. The entry point is `App.tsx`.

**Learn more:**
- [React beta docs ("Learn React")](https://react.dev/learn)
- [TypeScript in 5 minutes](https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes.html)

---

### Vite

**What it is:** The build tool and development server for the frontend. `npm run dev` starts Vite, which hot-reloads 
your changes in the browser instantly. `npm run build` compiles everything into a static bundle ready for deployment.

**Why we use it:** Vite is dramatically faster than older tools (Webpack, CRA) and requires almost no configuration.

**Learn more:** [Vite getting started](https://vitejs.dev/guide/)

---

### MapLibre GL JS (via react-map-gl)

**What it is:** MapLibre GL JS is an open-source WebGL-powered map rendering library. It renders interactive, 
vector-based maps in the browser at 60fps. `react-map-gl` is a React wrapper around it.

**Why we use it:** TOXMAP is fundamentally a map application. MapLibre supports:
- Rendering 100,000+ facility pins efficiently via WebGL
- Cluster aggregation (grouping nearby pins at low zoom levels)
- Color expressions (pins change color based on release volume — red = high, green = low)
- Toggleable overlay layers (Superfund sites, census boundaries, nuclear plants)
- PMTiles protocol (serving our self-hosted basemap tiles)

This is the heart of the user experience. The `Map/` component and `useViewportFacilities.ts` hook are the most 
important pieces of frontend code to understand.

**Learn more:**
- [MapLibre GL JS docs](https://maplibre.org/maplibre-gl-js/docs/)
- [react-map-gl docs](https://visgl.github.io/react-map-gl/)

---

### Recharts

**What it is:** A charting library for React built on D3.

**Why we use it:** Each facility detail panel shows two charts sourced directly from the original TOXMAP:
1. A **bar chart** of the top 5 chemicals released at that facility
2. A **15-year trend line** of total releases over time

Recharts makes these straightforward to implement with composable React components.

**Learn more:** [Recharts docs](https://recharts.org/en-US/)

---

### Tailwind CSS

**What it is:** A utility-first CSS framework. Instead of writing `.button { padding: 8px 16px; ... }` in a separate 
CSS file, you apply classes directly in your JSX: `<button className="px-4 py-2 bg-blue-600 text-white rounded">`.

**Why we use it:** It keeps styles co-located with markup, makes it easy to enforce a consistent design language, and 
eliminates the CSS class-naming problem entirely.

**Learn more:** [Tailwind CSS core concepts](https://tailwindcss.com/docs/utility-first)

---

## Production Deployment Stack

These tools handle how the app is hosted and updated once it's live.

### DuckDB WASM

**What it is:** DuckDB is an in-process analytical SQL database engine — think SQLite but column-oriented and optimized
for analytical queries. DuckDB WASM is a WebAssembly build of DuckDB that runs entirely inside the browser.

**Why we use it:** In production, there's no FastAPI server. The browser downloads DuckDB WASM and uses it to query 
Parquet files hosted on Cloudflare R2 — via HTTP range requests (fetching only the parts of the file it needs). This 
gives us SQL-powered geospatial queries with zero server infrastructure.

```typescript
// In-browser query — no backend required
const conn = await db.connect();
await conn.query("INSTALL spatial; LOAD spatial;");
const results = await conn.query(`
  SELECT name, total_release_lbs
  FROM read_parquet('https://r2.example.com/tri/2022.parquet')
  WHERE chemical_name = 'LEAD COMPOUNDS'
    AND ST_DWithin(ST_Point(lon, lat)::GEOGRAPHY, ST_Point(-76.48, 39.22)::GEOGRAPHY, 16093)
  ORDER BY total_release_lbs DESC
`);
```

**Learn more:** [DuckDB WASM docs](https://duckdb.org/docs/api/wasm/overview.html)

---

### Apache Parquet

**What it is:** A columnar binary file format designed for analytical queries. Unlike CSV, Parquet stores data 
column-by-column with compression, so a query that only needs `chemical_name` and `total_release_lbs` can fetch just 
those columns from the file over the network — without downloading the entire dataset.

**Why we use it:** DuckDB WASM queries Parquet files via HTTP range requests. This is what makes the browser-side SQL
queries practical — you're not downloading 800 MB to answer one query.

**Learn more:** [Apache Parquet overview](https://parquet.apache.org/docs/overview/)

---

### OpenFreeMap (Basemap Tiles)

**What it is:** [OpenFreeMap](https://openfreemap.org) is a free, open-source hosted vector tile service operated by a single developer (Tilen Mrak). It publishes global vector tiles derived from OpenStreetMap data under the ODbL licence, served from a CDN. No API key is required.

**Why we use it:** Map tiles are the basemap (roads, borders, labels) under our data overlay. Commercial tile services (Google Maps, Mapbox) cost money at scale. OpenFreeMap provides the same quality tiles at $0 with no signup or API key. MapLibre GL JS points at their Liberty style URL directly.

**ADR:** [ADR-005](../adr/ADR-005-openfreemap-basemap-tiles.md) documents why self-hosted PMTiles on R2 (the original plan in ADR-004) was abandoned: the Protomaps world build is 127 GiB; the US extract is ~2.5 GiB; Wrangler has a 300 MiB upload limit; working upload requires a separate S3 API credential flow. OpenFreeMap eliminates all of this.

**Self-hosting fallback:** If OpenFreeMap ever becomes unavailable, the complete procedure for extracting and uploading a US basemap tile file to R2 is documented in `docs/deployment/PMTILES_R2_UPLOAD.md`.

**Learn more:** [OpenFreeMap GitHub](https://github.com/hyperknot/openfreemap) · [MapLibre GL JS style spec](https://maplibre.org/maplibre-style-spec/)

---

### Cloudflare Pages + Cloudflare R2

**What they are:**
- **Cloudflare Pages** — static website hosting (like GitHub Pages, but global CDN). Hosts the compiled React app bundle.
- **Cloudflare R2** — S3-compatible object storage. Hosts the Parquet data files. Free tier: 10 GB storage + 10M reads/month, forever. Note: the basemap tiles are served from OpenFreeMap (ADR-005), not R2, so the full 10 GB is available for Parquet files.

**Why we use them:** They're genuinely free with no expiry, and Cloudflare's global CDN means fast load times for all users. The combination of Pages + R2 is what achieves the $0/month goal.

**Learn more:** [Cloudflare Pages docs](https://developers.cloudflare.com/pages/) · [Cloudflare R2 docs](https://developers.cloudflare.com/r2/)

---

### GitHub Actions

**What it is:** GitHub's built-in CI/CD system. Workflows are YAML files in `.github/workflows/` that run on events 
(push, PR, schedule).

**What we use it for:**
- **On every PR:** Run pytest (backend tests) + Playwright (E2E tests) + schemathesis (API contract tests)
- **Three times per year (EPA data checkpoints):** Re-run the ingestion pipeline, regenerate Parquet files, upload to R2. The build triggers on the August preliminary release, the October data freeze (authoritative), and the following spring's data refresh for retroactive corrections. See [TWO_MODES_DEEP_DIVE.md §Part 6](TWO_MODES_DEEP_DIVE.md#part-6-how-parquet-files-are-built) for the full schedule and why a single annual build is insufficient.

**Learn more:** [GitHub Actions quickstart](https://docs.github.com/en/actions/quickstart)

---

## The Testing Stack

### pytest + pytest-asyncio

**What it is:** pytest is the standard Python test runner. pytest-asyncio adds support for `async def` test functions
(needed because our service layer is async).

**When you use it:** Unit and integration tests for backend services, ingestion logic, and API route handlers.

```bash
cd backend
pytest tests/unit/           # unit tests only
pytest tests/integration/    # requires a running database
```

**Learn more:** [pytest docs](https://docs.pytest.org/en/stable/getting-started.html)

---

### pytest-bdd

**What it is:** A pytest plugin that lets you write tests in Gherkin syntax — `Given / When / Then` — and wire them to 
Python step definitions. The 57 Gherkin scenarios in [`TOXMAP_ACCEPTANCE_TESTS.md`](../testing/TOXMAP_ACCEPTANCE_TESTS.md) are the source of truth for 
what the app must do.

**Why we use it:** BDD (Behavior-Driven Development) scenarios are readable by non-engineers. Product requirements are 
expressed as acceptance tests from the start, not added as an afterthought.

```gherkin
Scenario: Find lead release near Sparrows Point MD
  Given the map is centered near "Sparrows Point, MD"
  When I search for chemical "LEAD COMPOUNDS" within 25 miles
  Then I see facility "BETHLEHEM STEEL SPARROWS POINT" in the results
  And the displayed release amount is formatted with commas
```

**Learn more:** [pytest-bdd docs](https://pytest-bdd.readthedocs.io/en/stable/)

---

### Playwright

**What it is:** A browser automation framework. It controls a real browser (Chromium, Firefox, or WebKit) and can click,
type, assert on what's visible — exactly like a user would.

**When we use it:** End-to-end tests that simulate real user task scenarios (the 9 UCD 2011 tasks in the acceptance 
tests). These tests run against a full stack — frontend, FastAPI, and database all running together.

We use `data-testid` attributes throughout the React components so Playwright can find elements reliably without 
depending on CSS classes or text that might change. All test IDs are registered in [`TEST_ID_REGISTRY.md`](../testing/TEST_ID_REGISTRY.md).

```typescript
// Example Playwright test
await page.goto('/');
await page.getByTestId('chemical-autocomplete').fill('lead');
await page.getByTestId('chemical-suggestion-LEAD COMPOUNDS').click();
await expect(page.getByTestId('results-table')).toContainText('BETHLEHEM STEEL');
```

**Learn more:** [Playwright docs](https://playwright.dev/docs/intro)

---

### schemathesis

**What it is:** An API fuzzing and contract testing tool. It reads our FastAPI-generated OpenAPI spec and automatically
generates hundreds of test cases from it — including edge cases and invalid inputs — to find bugs we didn't think to test 
for.

**Why we use it:** It's a "free" layer of API correctness testing. Running `schemathesis run /openapi.json --checks all` 
in CI catches schema drift and missing validation before a PR merges.

**Learn more:** [schemathesis docs](https://schemathesis.readthedocs.io/)

---

## Infrastructure & Tooling

### Docker + Docker Compose

**What it is:** Docker packages an application and all its dependencies into a container — a reproducible, isolated 
environment. Docker Compose defines multi-container setups with a single YAML file.

**Why we use it:** `docker compose up` on your laptop starts PostgreSQL + PostGIS + FastAPI + the React dev server. No
manual database installation, no version mismatches. It works identically in CI.

```bash
# Start everything locally
docker compose up

# Run backend only (if you're working on the API)
docker compose up db backend
```

**Learn more:** [Docker getting started](https://docs.docker.com/get-started/)

---

### Nominatim (OpenStreetMap Geocoding)

**What it is:** A free, open-source geocoding API provided by OpenStreetMap. Geocoding converts a human-readable address 
("Sparrows Point, MD") into coordinates (lat/lon).

**Why we use it:** The location search field needs to convert what the user types into map coordinates. Nominatim is 
free and doesn't require an API key, but it has a strict rate limit of 1 request/second — we debounce user input by 
500ms to comply.

In local/dev mode, geocoding goes through a server-side proxy endpoint (`GET /api/v1/geocode?q=`). In production 
(DuckDB WASM mode, no backend), the frontend calls Nominatim directly.

**Learn more:** [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/)

---

## Geospatial Concepts You'll Need

If geospatial data is new to you, here are the three concepts that come up constantly:

### Coordinate Reference Systems (CRS)
Coordinates can be expressed in different systems. We use two:
- **EPSG:4326 (WGS84):** Latitude/longitude in decimal degrees. GPS uses this. This is how all our data is stored.
- **EPSG:3857 (Web Mercator):** A projected system in meters. PostGIS uses this for distance calculations because 
- `ST_DWithin` on lat/lon degrees doesn't give accurate meter-based distances.

When you see `ST_Transform(..., 3857)` in a query, we're converting to meters to do the distance math, then the result 
is used for filtering.

### GeoJSON
The standard JSON format for geographic data. A `FeatureCollection` is what our API returns for map overlay data:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [-76.48, 39.22] },
      "properties": { "name": "Bethlehem Steel", "total_release_lbs": 48200 }
    }
  ]
}
```

### GIST Index
A spatial index type in PostgreSQL. Unlike a regular B-tree index (which sorts values), a GIST index organizes data by 
spatial proximity. This is what makes `ST_DWithin` fast — without it, every radius query would scan every row in the 
table.

---

## How It All Fits Together: Request Lifecycle

Here's what happens when a user searches for "lead compounds near Sparrows Point, MD":

```
1. User types "lead compounds" in ChemicalAutocomplete
   → useChemicalAutocomplete hook calls GET /api/v1/chemicals/search?q=lead
   → FastAPI queries: SELECT * FROM chemicals WHERE name ILIKE 'lead%'
   → Returns suggestions; user selects "LEAD COMPOUNDS"

2. User types "Sparrows Point, MD" in location field
   → useGeocode hook debounces 500ms, calls Nominatim
   → Returns { lat: 39.22, lon: -76.48 }

3. Map pans to that location; user adjusts radius slider to 25 miles

4. useViewportFacilities hook fires GET /api/v1/facilities
   ?lat=39.22&lon=-76.48&radius_miles=25&chemical=LEAD+COMPOUNDS&year=2022
   → FastAPI calls facility_service.get_near(...)
   → SQLAlchemy executes ST_DWithin query against PostGIS
   → Returns GeoJSON FeatureCollection

5. React renders pins on MapLibre GL map (color-coded by release_lbs)
   Results table populates in sidebar (viewport-scoped, no empty rows)

6. User clicks a facility pin
   → GET /api/v1/facilities/{tri_facility_id}
   → GET /api/v1/facilities/{tri_facility_id}/releases?from_year=2008&to_year=2022
   → Recharts renders bar chart + trend line in facility drawer
```

---

## Getting Started Locally

```bash
# 1. Clone the repo
git clone https://github.com/TOXMAP-Redux/toxmap-redux.git
cd toxmap-redux

# 2. Start the full stack
docker compose up

# 3. Run data ingestion (loads seed data for tests)
docker compose exec backend python -m ingestion.tri_ingest --seed

# 4. Frontend is at http://localhost:3000
# 5. API docs (Swagger UI) are at http://localhost:8000/docs
# 6. API docs (ReDoc) are at http://localhost:8000/redoc

# 7. Run backend tests
docker compose exec backend pytest

# 8. Run Playwright E2E tests (requires full stack running)
pytest tests/features/e2e/
```

---

## Key Files to Read First

| File | Why |
|---|---|
| [`docs/adr/ADR-001-fastapi-postgis-react.md`](../adr/ADR-001-fastapi-postgis-react.md) | Why we chose each piece of the stack |
| [`docs/adr/ADR-004-zero-budget-hosting.md`](../adr/ADR-004-zero-budget-hosting.md) | Why production has no server |
| [`docs/TWO_MODES_DEEP_DIVE.md`](TWO_MODES_DEEP_DIVE.md) | In-depth guide to dev vs. production mode |
| [`docs/api/TOXMAP_API_CONTRACT.md`](../api/TOXMAP_API_CONTRACT.md) | Every API endpoint with example responses |
| [`docs/testing/TOXMAP_ACCEPTANCE_TESTS.md`](../testing/TOXMAP_ACCEPTANCE_TESTS.md) | The 57 Gherkin scenarios that define done |
| [`docs/testing/TEST_ID_REGISTRY.md`](../testing/TEST_ID_REGISTRY.md) | All `data-testid` values for Playwright |
| [`docs/product/TOXMAP_SCREEN_CATALOG.md`](../product/TOXMAP_SCREEN_CATALOG.md) | Annotated screenshots of the original TOXMAP |

---

## Where to Get Help

- **Architecture questions:** Read the ADR for that decision first — most "why" questions are answered there
- **API shape questions:** [`TOXMAP_API_CONTRACT.md`](../api/TOXMAP_API_CONTRACT.md) is authoritative
- **UX questions:** The 2011 UCD usability study findings in [ADR-001 §UX Architecture Decisions](../adr/ADR-001-fastapi-postgis-react.md#ux-architecture-decisions-ucd-inc-usability-study-2011) explain every non-obvious frontend constraint
- **"Why no X?"** Check [`GOVERNANCE.md`](../GOVERNANCE.md) and [`docs/adr/STATUS.md`](../adr/README.md) — the rejected ADRs (ADR-002, ADR-003) document what was considered and why it was set aside

