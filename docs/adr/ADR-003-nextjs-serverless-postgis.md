# ADR-003: Next.js · Node API · Supabase/PostGIS · MapLibre

| Field | Value |
|-------|-------|
| **ID** | ADR-003 |
| **Title** | Next.js Full-Stack + Supabase/PostGIS as JS-Unified Architecture |
| **Date** | 2026-07-15 |
| **Status** | **Rejected — Superseded by [ADR-001](ADR-001-fastapi-postgis-react.md)** |
| **Deciders** | Architecture Review |
| **NLM Sources** | [PMC2703818](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2703818/) · [PMC4251466](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4251466/) · [UCD Usability Study 2011](https://dpcpsi.nih.gov/sites/g/files/mnhszr346/files/FR508_10-4004_NLM_11-03-11.pdf) |
| **Supersedes** | — |
| **Superseded by** | [ADR-001](ADR-001-fastapi-postgis-react.md) (2026-07-16) |

---

## Context

Same context as [ADR-001](ADR-001-fastapi-postgis-react.md). Per NLM peer-reviewed sources ([PMC2703818](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2703818/), [PMC4251466](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4251466/)), the original TOXMAP served not just TRI data but also **Superfund/NPL sites, U.S. Census demographic overlays, Canadian NPRI, nuclear plant locations, and congressional district boundaries** — all toggleable map layers. The 2013 redesign migrated from MySQL → PostgreSQL, validating managed-PostgreSQL services like Supabase as a deployment target.

This ADR documents a JavaScript/TypeScript-unified contender — a single language across frontend and backend, leveraging Supabase (managed PostgreSQL + PostGIS) for geospatial queries. This option minimizes infrastructure ownership at the cost of some vendor coupling.

The driving question: **Can a JS-only team ship a full-featured ToxMap clone (including Superfund, Census, and optional layers) without operating their own database infrastructure?**

---

## Decision

**If adopted, the following stack would be used:**

```
Frontend:          Next.js 15 (App Router) + React 19
Map Rendering:     MapLibre GL JS (via react-map-gl)
Charts:            Recharts or Observable Plot
Styling:           Tailwind CSS 4.x
Backend API:       Next.js Route Handlers (Node.js runtime) or Hono
Database:          Supabase (managed PostgreSQL 16 + PostGIS 3.4)
Geospatial:        Supabase PostGIS functions via supabase-js RPC
ORM:               Drizzle ORM (type-safe) or Supabase auto-generated types
Data Ingestion:    Node.js ETL script (csv-parse + Supabase bulk insert)
Deployment:        Vercel (frontend + API) + Supabase (database)
Alt Deployment:    Fly.io (Next.js) + Supabase self-hosted (Docker)
CI/CD:             GitHub Actions
```

---

## System Architecture

### Option A: Vercel + Supabase (Managed — Zero Infra)

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser Client                        │
│  Next.js 15 · MapLibre GL · react-map-gl · Recharts         │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP (fetch / Server Components)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Next.js 15 (Vercel Edge / Node.js)              │
│                                                              │
│  app/                                                        │
│  ├── page.tsx             # Map explorer (Server Component)  │
│  ├── facilities/[id]/     # Facility detail page             │
│  └── api/                                                    │
│      ├── facilities/route.ts   # Radius search endpoint      │
│      ├── chemicals/route.ts    # Chemical filter list        │
│      └── export/route.ts       # CSV streaming export        │
└──────────────────────┬──────────────────────────────────────┘
                       │ supabase-js (REST + RPC)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Supabase (managed PostgreSQL + PostGIS)         │
│                                                              │
│  PostGIS functions exposed as Supabase RPC:                  │
│  rpc('facilities_near', { lat, lon, radius_meters })         │
│  → calls ST_DWithin internally                               │
│                                                              │
│  Row Level Security (RLS): public read-only policies         │
│  Realtime: disabled (not needed for this use case)           │
└─────────────────────────────────────────────────────────────┘
```

### Option B: Self-Hosted (Fly.io + Supabase Docker / Coolify)

```
┌───────────────────────────────────────────────────────┐
│  Fly.io Machine (Next.js + Node.js)                    │
│  ← same code as Option A, different runtime target     │
└───────────────────────┬───────────────────────────────┘
                        │ PostgreSQL wire protocol
                        ▼
┌───────────────────────────────────────────────────────┐
│  Supabase (self-hosted via Docker) or bare PostgreSQL  │
│  on Fly.io persistent volume                           │
└───────────────────────────────────────────────────────┘
```

---

## Key Implementation Patterns

### Supabase PostGIS RPC (SQL Function)

```sql
-- Defined once in Supabase SQL editor or migration
CREATE OR REPLACE FUNCTION facilities_near(
    lat       FLOAT,
    lon       FLOAT,
    radius_m  FLOAT,
    year_filter INT DEFAULT NULL,
    chemical_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    id              INT,
    tri_facility_id TEXT,
    name            TEXT,
    lat             FLOAT,
    lon             FLOAT,
    total_release   NUMERIC,
    chemical_name   TEXT
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        f.id,
        f.tri_facility_id,
        f.name,
        ST_Y(f.location::geometry) AS lat,
        ST_X(f.location::geometry) AS lon,
        SUM(re.total_release_lbs)  AS total_release,
        c.name                     AS chemical_name
    FROM facilities f
    JOIN release_events re ON re.facility_id = f.id
    JOIN chemicals c       ON c.id = re.chemical_id
    WHERE ST_DWithin(
        f.location::geography,
        ST_MakePoint(lon, lat)::geography,
        radius_m
    )
    AND (year_filter IS NULL OR re.reporting_year = year_filter)
    AND (chemical_filter IS NULL OR c.name ILIKE '%' || chemical_filter || '%')
    GROUP BY f.id, f.tri_facility_id, f.name, f.location, c.name
$$;
```

### Superfund / NPL RPC (NLM 2006 enhancement)

```sql
CREATE OR REPLACE FUNCTION superfund_near(
    lat      FLOAT,
    lon      FLOAT,
    radius_m FLOAT
)
RETURNS TABLE (
    id         INT,
    epa_id     TEXT,
    name       TEXT,
    lat        FLOAT,
    lon        FLOAT,
    hrs_score  NUMERIC,
    status     TEXT
)
LANGUAGE sql STABLE AS $$
    SELECT
        id, epa_id, name,
        ST_Y(location::geometry) AS lat,
        ST_X(location::geometry) AS lon,
        hrs_score, status
    FROM superfund_sites
    WHERE ST_DWithin(
        location::geography,
        ST_MakePoint(lon, lat)::geography,
        radius_m
    )
$$;
```

### Next.js Route Handler (TypeScript)

```typescript
// app/api/facilities/route.ts
import { createClient } from "@supabase/supabase-js";
import { NextRequest, NextResponse } from "next/server";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl;
  const lat = parseFloat(searchParams.get("lat") ?? "0");
  const lon = parseFloat(searchParams.get("lon") ?? "0");
  const radiusMiles = parseFloat(searchParams.get("radius_miles") ?? "25");
  const year = searchParams.get("year") ? parseInt(searchParams.get("year")!) : null;
  const chemical = searchParams.get("chemical") ?? null;

  const { data, error } = await supabase.rpc("facilities_near", {
    lat,
    lon,
    radius_m: radiusMiles * 1609.34,
    year_filter: year,
    chemical_filter: chemical,
  });

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  // Convert to GeoJSON FeatureCollection
  const geojson = {
    type: "FeatureCollection",
    features: data.map((f: any) => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [f.lon, f.lat] },
      properties: { id: f.id, name: f.name, totalRelease: f.total_release },
    })),
  };

  return NextResponse.json(geojson);
}
```

### Drizzle ORM Schema (Type-Safe)

```typescript
// db/schema.ts
import { pgTable, serial, text, smallint, numeric, customType } from "drizzle-orm/pg-core";

// Custom type for PostGIS GEOMETRY
const geometry = customType<{ data: string }>({
  dataType() { return "GEOMETRY(POINT, 4326)"; },
});

export const facilities = pgTable("facilities", {
  id: serial("id").primaryKey(),
  triFacilityId: text("tri_facility_id").notNull().unique(),
  name: text("name").notNull(),
  stateCode: text("state_code"),
  naicsCode: text("naics_code"),
  location: geometry("location").notNull(),
});

export const releaseEvents = pgTable("release_events", {
  id: serial("id").primaryKey(),
  facilityId: serial("facility_id").references(() => facilities.id),
  chemicalId: serial("chemical_id").references(() => chemicals.id),
  reportingYear: smallint("reporting_year").notNull(),
  totalReleaseLbs: numeric("total_release_lbs", { precision: 14, scale: 2 }),
});
```

### TRI CSV Ingestion (Node.js)

```typescript
// scripts/ingest-tri.ts
import { parse } from "csv-parse";
import { createReadStream } from "fs";
import { createClient } from "@supabase/supabase-js";

const BATCH_SIZE = 500;

async function ingestTri(csvPath: string, year: number) {
  const supabase = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_SERVICE_KEY!);
  const records: any[] = [];

  const parser = createReadStream(csvPath).pipe(
    parse({ columns: true, skip_empty_lines: true })
  );

  for await (const row of parser) {
    const lat = parseFloat(row["13. LATITUDE"]);
    const lon = parseFloat(row["14. LONGITUDE"]);
    if (isNaN(lat) || isNaN(lon)) continue;

    records.push({
      tri_facility_id: row["4. TRI FACILITY ID"],
      name: row["5. FACILITY NAME"],
      state_code: row["8. ST"],
      naics_code: row["22. INDUSTRY SECTOR CODE"],
      location: `POINT(${lon} ${lat})`,
    });

    if (records.length === BATCH_SIZE) {
      await supabase.from("facilities").upsert(records, { onConflict: "tri_facility_id" });
      records.length = 0;
    }
  }
  if (records.length) {
    await supabase.from("facilities").upsert(records, { onConflict: "tri_facility_id" });
  }
}
```

---

## Project Structure

```
toxmap/
├── app/                            # Next.js App Router
│   ├── page.tsx                    # Map explorer (root page)
│   ├── facilities/
│   │   └── [id]/page.tsx           # Facility detail
│   └── api/
│       ├── facilities/route.ts
│       ├── chemicals/route.ts
│       └── export/route.ts
├── components/
│   ├── Map/                        # MapLibre GL wrapper
│   ├── FacilityDrawer/             # Slide-out detail panel
│   ├── FilterSidebar/              # Year/chemical/radius controls
│   └── Charts/                     # Release time series
├── db/
│   ├── schema.ts                   # Drizzle schema
│   └── migrations/                 # SQL migrations
├── scripts/
│   └── ingest-tri.ts               # ETL script
├── supabase/
│   └── migrations/                 # Supabase SQL function migrations
├── lib/
│   ├── supabase.ts                 # Client factory
│   └── geo.ts                      # GeoJSON helpers
├── package.json
├── next.config.ts
├── docker-compose.yml              # For local Supabase
└── README.md
```

---

## Consequences

### Positive

- **Single language (TypeScript)** — eliminates Python/Java context-switching; frontend, API, schema, and ingestion scripts all in TypeScript
- **Fastest deployment** — Vercel + Supabase: push to `main` → live in < 5 minutes; zero infrastructure management
- **Full-stack type safety** — Drizzle ORM + Supabase auto-generated types ensure end-to-end type safety from DB schema to UI props
- **Next.js Server Components** — initial map page can be partially server-rendered for faster first paint
- **Supabase free tier** — suitable for development and low-traffic production (500 MB database, 2 GB egress/month free)
- **Excellent DX for JS/TS contributors** — largest contributor pool (JavaScript is the most common open-source language)

### Negative

- **Vendor risk** — Supabase managed tier creates lock-in; mitigated by self-hosting option but adds ops complexity
- **Node.js geospatial limitations** — no pandas/geopandas equivalent; CSV ingestion and coordinate cleaning require more manual work
- **Edge runtime constraints** — Vercel Edge runtime does not support all Node.js APIs; complex streaming/export routes may require `runtime = "nodejs"` override
- **Supabase RPC for complex queries** — geospatial queries must be pre-defined as SQL functions; less flexible for ad-hoc query iteration
- **Weaker ETL tooling** — Python's data cleaning (handling TRI CSV dirty data) is more mature than Node.js equivalents
- **Next.js API latency** — cold start on Vercel serverless can add 200–500ms; unacceptable for interactive map use

### Neutral

- Drizzle ORM's PostGIS/geometry support requires a custom type wrapper (shown above); less turnkey than GeoAlchemy2
- Self-hosted Supabase via Docker requires ~8 GB RAM; heavier than a standalone PostgreSQL + PostGIS setup
- **All UX architecture decisions** from the [2011 usability study](TOXMAP_TECH_STACK_ANALYSIS.md#8-ux-lessons-learned-ucd-inc-usability-study-2011) apply equally to this stack — single sidebar panel, viewport-scoped results, state-restrict checkbox, labeled icons, inline demographic legend. The Supabase RPCs must accept `bbox` and `restrict_to_state` parameters. The `facilities_near` RPC shown above should be extended accordingly.

---

## When to Choose This ADR Over ADR-001 or ADR-002

| Condition | Prefer ADR-003 |
|-----------|---------------|
| Team is exclusively JavaScript/TypeScript | ✅ |
| Deployment simplicity > performance fine-tuning | ✅ |
| Budget is $0 (Vercel + Supabase free tiers) | ✅ |
| Expected traffic is low-to-moderate (< 10K req/day) | ✅ |
| Team needs fast geospatial data wrangling / ETL | ❌ (use ADR-001) |
| High-throughput geospatial query SLAs required | ❌ (use ADR-001 or ADR-002) |
| Growing multi-domain platform needing hard boundaries | ❌ (use ADR-002) |

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Supabase free tier limits hit | Self-host Supabase on Fly.io; schema is portable |
| Vercel cold start latency | Migrate API to Hono on Fly.io (same TS code, different runtime) |
| Node.js TRI data cleaning brittleness | Pre-process CSVs with a one-time Python script before Node.js upsert |
| Supabase RPC inflexibility | Use `supabase-js` `.from().select()` with PostGIS operators for simpler queries |

---

## Alternatives Considered

- **[ADR-001](ADR-001-fastapi-postgis-react.md)** (FastAPI): Preferred when geospatial tooling and data wrangling are top priorities
- **[ADR-002](ADR-002-spring-modulith-postgis.md)** (Spring Modulith): Preferred for Java teams and multi-domain platforms
- **Remix + Supabase**: Similar to Next.js but smaller ecosystem; rejected
- **SvelteKit + Supabase**: More performant frontend; rejected due to smaller contributor pool vs React

---

## Review Checklist

- [ ] Supabase RPC `facilities_near` benchmarked with 90K facilities (local Docker)
- [ ] Node.js TRI CSV ingest tested end-to-end (2022 bulk file ~300MB)
- [ ] Vercel cold start latency measured on `/api/facilities` route
- [ ] Self-hosted Supabase Docker Compose documented and tested
- [ ] ADR reviewed by at least two contributors before status → Accepted





