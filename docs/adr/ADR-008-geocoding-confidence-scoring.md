# ADR-008: Geocoding Confidence Scoring and Viewport Bias

| Field         | Value |
|---------------|-------|
| **ID**        | ADR-008 |
| **Title**     | Geocoding Confidence Scoring and Viewport Bias |
| **Date**      | 2026-08-04 |
| **Status**    | **Accepted** |
| **Deciders**  | FE Engineering (Phase 7 bug fix / improvement) |
| **Parent ADR**| [ADR-006](ADR-006-photon-geocoding.md) (this ADR extends ADR-006's Photon implementation) |

---

## Context

During Phase 7 QA testing, a geocoding fidelity gap was identified when comparing TOXMAP's
Photon-based geocoding results against Google Maps for the same address queries. The test case
`100 Mill Rd, Port Townsend, WA` demonstrated several issues:

1. **Ambiguous queries** (e.g., `100 Mill Rd` without city/state) resolved to arbitrary matches
   globally, without communicating uncertainty to the user.
2. **No location bias** — Photon was called without the user's current map viewport, so distant
   matches could win over nearby ones for ambiguous queries.
3. **No confidence feedback** — Users could not distinguish between high-confidence rooftop
   matches and low-confidence street interpolations.
4. **First-result acceptance** — The system blindly accepted Photon's first result without
   scoring candidates against the original query.

---

## Problem Statement

Users interpret geocode pin placement as "correct" regardless of underlying confidence. For
address-level workflows, an approximate or interpolated match can appear hundreds of meters
from the actual location, causing users to search in the wrong area and miss relevant TRI
facilities or Superfund sites.

The existing implementation (ADR-006) solved the operational problem of getting geocoding to
work at all. This ADR addresses the **quality** problem of ensuring geocoding results meet
user expectations for address-level fidelity.

---

## Decision

Extend the Photon geocoding client (`frontend/src/api/geocode.ts`) with:

1. **Multi-candidate scoring** — Request 5 candidates from Photon and score each against the
   original query.
2. **Viewport proximity bias** — Pass the user's current map center (`lat`/`lon`) to Photon
   to favor nearby matches for ambiguous queries.
3. **Confidence classification** — Assign each result a confidence level (`exact`, `high`,
   `approximate`, `low`) based on weighted scoring criteria.
4. **UI feedback** — Display the resolved canonical address with a confidence badge, and
   show a warning for approximate/low-confidence matches.

---

## Scoring Algorithm

Candidates are scored on a 0.0–1.0 scale using weighted signals:

| Signal | Weight | Description |
|--------|--------|-------------|
| House number match | +0.35 | Exact match of house number (e.g., `100` = `100`) |
| Street name similarity | +0.25 | Normalized string comparison (handles `Rd`↔`Road`, etc.) |
| City match | +0.10 | Case-insensitive city name match |
| State match | +0.10 | State code match (parsed from query or Photon response) |
| Postal code match | +0.10 | Exact or prefix match of ZIP code |
| Viewport proximity | +0.10 | Distance from current map center (closer = higher) |

### Confidence Thresholds

| Score Range | Confidence Level | UI Treatment |
|-------------|------------------|--------------|
| ≥ 0.85 | `exact` | Green badge "Exact" |
| 0.65 – 0.84 | `high` | Blue badge "High" |
| 0.40 – 0.64 | `approximate` | Amber badge "Approximate" + warning text |
| < 0.40 | `low` | Red badge "Low confidence" + warning text |

---

## Implementation

### `geocode.ts` Changes

```typescript
export interface GeocodeResult {
  lat: number
  lon: number
  displayName: string
  state?: string
  confidence: number           // 0.0–1.0
  confidenceLevel: GeocodeConfidence  // 'exact' | 'high' | 'approximate' | 'low'
  houseNumber?: string
  street?: string
  city?: string
  postcode?: string
  osmType?: string
}

export interface GeocodeOptions {
  biasLat?: number   // Current map center latitude
  biasLon?: number   // Current map center longitude
}

export async function geocodeLocation(
  location: string,
  options: GeocodeOptions = {}
): Promise<GeocodeResult | null>
```

Key implementation details:

1. **Query parsing** — Extract house number, street name, city, state, and postal code from
   the free-text query for scoring.
2. **Street name normalization** — Map common abbreviations (`Rd`→`road`, `St`→`street`, etc.)
   before comparison.
3. **Haversine distance** — Calculate distance from viewport center for proximity scoring.
4. **Photon parameters** — Pass `lat`, `lon`, and `limit=5` to Photon API.

### UI Changes

- **SearchPanel** — New `resolvedGeocode` prop displays:
  - `📍 Resolved location` heading
  - Canonical address from Photon (e.g., `100 Paper Mill Hill Road, Port Townsend, WA, 98368`)
  - Confidence badge (color-coded)
  - Warning text for `approximate` or `low` confidence

- **App.tsx** — Passes current `viewState.latitude`/`longitude` as bias coordinates.

---

## Query Enrichment

The implementation automatically enriches queries with US context when appropriate:

| Query Pattern | Enrichment |
|---------------|------------|
| 5-digit number (ZIP code) | Append `, USA` |
| Contains US state code or name | Append `, USA` |
| Contains US postal code | Append `, USA` |

This reduces international false matches without requiring users to type "USA" explicitly.

---

## Test Cases

| Query | Expected Confidence | Expected Location |
|-------|---------------------|-------------------|
| `100 Mill Rd, Port Townsend, WA 98368` | `exact` or `high` | Near Port Townsend Paper Corp |
| `100 Mill Rd, Port Townsend, WA` | `high` | Near Port Townsend Paper Corp |
| `100 Mill Rd` (ambiguous) | `approximate` or `low` | May resolve elsewhere; warning shown |
| `Mill Rd, Port Townsend` (no house #) | `approximate` | Street-level match only |
| `100 Mill Rd Port Townsed` (typo) | `approximate` or `low` | Best effort; warning shown |

---

## Consequences

### Positive

- Users see the canonical resolved address, not just their input
- Confidence badges set appropriate expectations for match quality
- Viewport bias improves relevance for ambiguous queries
- Warning messages guide users to refine low-confidence queries
- Multi-candidate scoring picks better matches than first-result acceptance

### Negative / Trade-offs

- Additional latency (~50ms) for scoring 5 candidates client-side
- Scoring heuristics may not perfectly match user intent in all cases
- Cache key now includes bias coordinates (slightly lower cache hit rate)

### Neutral

- Photon request limit increased from 1 to 5 (well within fair-use)
- `geocodeLocationWithCandidates()` function exported for future disambiguation UI

---

## Future Enhancements

The following are out of scope for this ADR but enabled by this architecture:

1. **"Did you mean…" disambiguation** — Show top 3 candidates when confidence < 0.65
2. **Low-confidence marker style** — Hollow or amber pin for approximate geocodes
3. **Telemetry** — Track `geocode_confidence_bucket` for quality monitoring
4. **Retry with enrichment** — Auto-retry with city/state/postcode if first attempt is low-confidence

---

## Alternatives Considered

| Option | Reason Rejected |
|--------|----------------|
| Require structured address input | Poor UX; users expect free-text |
| Use Google Geocoding API | Paid; violates $0 budget (ADR-004) |
| Server-side scoring | Adds latency; browser has viewport context |
| Always show disambiguation | Excessive UX friction for high-confidence queries |
| Lower confidence thresholds | Would show false "Exact" badges for ambiguous matches |

---

## Related ADRs

- [ADR-006](ADR-006-photon-geocoding.md) — Establishes Photon as the geocoding service
- [ADR-004](ADR-004-zero-budget-hosting.md) — Constrains to $0 budget (no paid geocoding APIs)
- [ADR-001](ADR-001-fastapi-postgis-react.md) — Defines React frontend architecture
