# ADR-006: Photon (Komoot) for Browser-Direct Geocoding

| Field         | Value |
|---------------|-------|
| **ID**        | ADR-006 |
| **Title**     | Photon (Komoot) for Browser-Direct Geocoding |
| **Date**      | 2026-07-27 |
| **Status**    | **Accepted** |
| **Deciders**  | FE Engineering (Phase 3 implementation) |
| **Parent ADR**| [ADR-001](ADR-001-fastapi-postgis-react.md) (this ADR specifies the geocoding implementation referenced in ADR-001 §API Endpoints) |
| **Related**   | [ADR-009](ADR-009-cloudflare-workers-geocoding-proxy.md) (production scaling via Workers proxy) |

---

## Context

Phase 3 requires converting a user-typed location string (e.g. "Sparrows Point, MD") into
coordinates (lat/lon) so the map can zoom and the facility search can be scoped. Two design
questions arose:

1. **Which geocoding service?** The original plan referenced Nominatim (OpenStreetMap Foundation)
   via a backend proxy.
2. **Backend proxy or browser-direct?** The original design routed geocoding through the FastAPI
   backend (`GET /api/v1/geocode`) which proxied Nominatim.

Both questions were resolved by operational constraints discovered during Phase 3.

---

## Problem

### Nominatim blocked our server IP

When the FastAPI backend (running in Docker) attempted to call
`https://nominatim.openstreetmap.org/search`, the OSM Foundation returned:

```
Access denied. See https://operations.osmfoundation.org/policies/nominatim/
```

The server IP — likely in a cloud/datacenter range — was flagged by Nominatim's rate-limiting
system regardless of the User-Agent string used. This is a known issue with Nominatim when called
from server infrastructure rather than end-user browsers.

### SSL inspection in Docker networking

An additional constraint: the Docker container's outbound HTTPS traffic passes through a
network-level SSL inspection proxy (common in enterprise/VPN environments), which terminates
TLS and re-presents a self-signed certificate. `httpx` in the backend container raised
`SSL certificate error: self-signed certificate in certificate chain` for all HTTPS calls to
external services.

---

## Decision

**Use Photon (photon.komoot.io) called directly from the browser.**

Photon is a free geocoder operated by Komoot GmbH, backed by OpenStreetMap data:
- Full CORS support (`Access-Control-Allow-Origin: *`) — browser `fetch()` works without a proxy
- No API key required
- Excellent US address coverage (same OSM data as Nominatim)
- Unaffected by server-IP blocks (browser calls use the end-user's residential/business IP)
- Unaffected by corporate SSL inspection (browser uses the host OS certificate store)

The FastAPI `GET /api/v1/geocode` endpoint **remains in the codebase** (pointing to Photon) but
the React frontend does NOT call it. The backend endpoint may be used by CLI tools, scripts, or
future server-side features.

---

## Implementation (`frontend/src/api/geocode.ts`)

Three fair-use mitigations are built into the module:

| Mitigation | Implementation |
|-----------|---------------|
| **In-memory cache** | `Map<string, GeocodeResult>` keyed on normalised (lowercase/trimmed) query. Max 200 entries with LRU eviction. Repeated queries produce zero network calls. |
| **1-second throttle** | `_throttledFetch()` enforces ≥ 1,000 ms between distinct HTTP requests. Since geocoding is triggered only on explicit Search button click (not keystrokes), this rarely introduces latency. |
| **Attribution** | Photon's usage policy requires crediting Photon/Komoot and OpenStreetMap. `PHOTON_ATTRIBUTION` is rendered as JSX links in `DataVintageLabel` in the map footer. `dangerouslySetInnerHTML` is **not** used — links are plain JSX `<a>` elements with `rel="noopener noreferrer"`. |

---

## Viewport-Scoping Race Condition (Also Fixed in Phase 3)

A related bug was discovered during Phase 3 integration: the `useViewportFacilities` hook fired
two concurrent requests when a new search was submitted — one with the pre-zoom viewport bbox
and one with the post-zoom bbox. The pre-zoom bbox (US overview at zoom 4) sometimes excluded
the search target, and the stale request completed last, overwriting the correct results with 0.

Two fixes were applied:

1. **`setMapBbox(null)` in `handleSearchSubmit`** — resets the viewport bbox before the new
   search runs, so the initial request has no stale viewport constraint.
2. **`AbortSignal` threaded through `fetchFacilities`** — the hook's `AbortController` is now
   passed as the `signal` option to `fetch()`, properly cancelling in-flight requests when
   new parameters arrive.

---

## Fair-Use Status

Photon's [usage policy](https://photon.komoot.io/) asks for:
- Reasonable (non-bulk, non-automated) request rates ✅ (user-click triggered only)
- Attribution to Photon/Komoot and OpenStreetMap ✅ (rendered in map footer)
- Identification of the application ✅ (browser `Referer` header identifies `localhost:3000`)

TOXMAP makes at most one geocode call per Search button click from a real user. This is well
within reasonable fair-use bounds.

### Production Scaling

Two scaling paths are available if TOXMAP receives significant traffic:

**1. Cloudflare Workers Proxy (Recommended first step) — ADR-009**

A thin Workers proxy provides global caching (not per-browser) and aggregate rate limiting for ~$0-5/month. This solves the aggregate overload problem without self-hosting:

- Free tier: 100K requests/day (~3M/month)
- Global cache: 60-80% hit rate vs. 10-20% per-browser
- Analytics: visibility into actual request volumes

See **[ADR-009](ADR-009-cloudflare-workers-geocoding-proxy.md)** for implementation details.

**2. Self-hosted Photon (For high traffic or offline use)**

Photon is Apache 2.0-licensed and can be deployed on a VPS for ~$16/month (US-only) to ~$105/month (planet-wide). See **[SELF_HOSTING_GUIDE.md](../deployment/SELF_HOSTING_GUIDE.md)** for complete step-by-step instructions.

The `geocodeLocation()` function signature is unchanged — only the `_PHOTON_URL` constant (or `VITE_GEOCODE_PROXY_URL`) needs updating.

Alternatively, a commercial hosted geocoder (e.g. MapTiler, Geoapify) with a free tier can be
swapped in the same module. The rest of the codebase is entirely unaffected.

---

## Consequences

### Positive
- Geocoding works reliably from any development environment without requiring server internet access
- No API key to manage, rotate, or accidentally commit
- Browser calls use the end-user's IP → much lower rate-limiting risk than server-side calls
- Cache eliminates redundant calls for repeated searches

### Negative / Trade-offs
- The FastAPI `GET /api/v1/geocode` backend endpoint is now unused by the frontend (maintenance burden: low — the endpoint is small and tested)
- For headless/server-side rendering scenarios, geocoding would need to move back to the backend with a different service (Photon self-hosted recommended)
- Photon's free public instance has no SLA — downtime would fail user geocoding (graceful fallback: error message prompts user to try a different format)

### Neutral
- `VITE_NOMINATIM_UA` env var is now unused; removed from `.env.example`

---

## Alternatives Considered

| Option | Reason Rejected |
|--------|----------------|
| Nominatim backend proxy | Blocked by server IP; SSL inspection in container |
| Nominatim browser-direct | Same IP-block issue would apply for server deployments; same policy concerns |
| OpenCage / MapTiler geocoder | Require API keys; adds secret management overhead |
| HERE / Google Geocoding API | Paid; violates $0 budget constraint (ADR-004) |
| Self-hosted Photon immediately | Operationally complex for Phase 3 development; deferred to production if needed |

---

## Related ADRs

- [ADR-008](ADR-008-geocoding-confidence-scoring.md) — Extends this ADR with multi-candidate scoring and confidence feedback
- [ADR-004](ADR-004-zero-budget-hosting.md) — Constrains to $0 budget (no paid geocoding APIs)
- [ADR-001](ADR-001-fastapi-postgis-react.md) — Defines React frontend architecture
