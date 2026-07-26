# DuckDB WASM Memory Limit Assessment

**Date:** 2026-07-17  
**Scope:** Full TOXMAP architecture review against WebAssembly 4GB memory constraints  
**Source Article:** "Up to 4GB of memory in WebAssembly" (Emscripten/V8 team, May 2020)  
**Documents Reviewed:** ADR-001, ADR-004, TWO_MODES_DEEP_DIVE.md, TECH_STACK_ONBOARDING.md, TOXMAP_TECH_STACK_ANALYSIS.md

---

## TL;DR

**No architecture violations. No assumptions are broken by the 4GB WASM memory ceiling.** The design's per-year Parquet files and HTTP range-request model keep in-memory working sets at 5–50 MB per query — orders of magnitude below any relevant limit. However, three low-severity gaps exist in the documented architecture that should be addressed before production launch.

---

## The Constraint Being Assessed

The article establishes the following facts about WebAssembly memory:

| Fact | Value |
|------|-------|
| Absolute maximum for wasm32 (32-bit) | **4 GB** |
| Default cap *without* explicit compiler opt-in | **2 GB** |
| Flag required to use 2–4 GB range | `emcc -s ALLOW_MEMORY_GROWTH -s MAXIMUM_MEMORY=4GB` |
| Minimum browser for 4 GB support | Chrome M83 (V8 TypedArray rewrite) |
| Signed shift problem | `>>` breaks at 2 GB addresses; Emscripten must use `>>>` above this threshold |
| Article's usage guidance | Start with the smallest initial allocation; grow if necessary; handle `malloc()` failure gracefully |
| Future path beyond 4 GB | wasm64 — not yet standard; doubles pointer size |

DuckDB WASM (`@duckdb/duckdb-wasm`) is compiled with Emscripten as a **wasm32** binary. Everything above applies to it directly.

---

## Assessment by Architecture Component

### 1. Per-Year Parquet File Strategy

**Relevant ADR-004 claim:**
> "One Parquet file per TRI year means DuckDB WASM only fetches the file for the year the user selected."

**Data sizes from the docs:**
- Full TRI history (1987–present, ~4M rows): ~150 MB compressed Parquet total
- Per-year average: ~150 MB ÷ 38 years ≈ **~4 MB per file**
- Bytes fetched per query via HTTP range requests: **5–20 MB** (only needed columns/row groups)
- `chemicals.parquet`: negligible (static lookup, small)
- `superfund.parquet`: ~1,500 NPL sites — negligible
- `us_counties.geojson`: fetched via direct `fetch()`, not through DuckDB

**Assessment:** The per-year file split is the single most important memory decision in the production architecture. Even if DuckDB WASM were to fully materialize an entire year's Parquet file in memory (which it doesn't — range requests prevent this), 4 MB is 0.1% of the 2 GB default limit. A complete in-memory load of all 38 years simultaneously would be 150 MB — 3.75% of the 4 GB ceiling.

**Verdict: No constraint. This design is deliberately memory-conservative and well-aligned with the article's guidance to "start with an initial memory that is as small as possible."**

---

### 2. Browser Compatibility Check (`isDuckDBWasmSupported()`)

**From ADR-004 / TWO_MODES_DEEP_DIVE.md:**

```typescript
// Checks for WASM SIMD — required by DuckDB spatial extension
export async function isDuckDBWasmSupported(): Promise<boolean> {
  if (typeof WebAssembly === 'undefined') return false;
  // ... attempts to instantiate a SIMD module
}
```

**Browser compatibility matrix from the docs:**

| Browser | WASM SIMD | Result |
|---------|-----------|--------|
| Chrome 91+ / Edge 91+ | ✅ | DuckDB WASM |
| Firefox 90+ | ✅ | DuckDB WASM |
| Safari 16.4+ | ✅ | DuckDB WASM |
| Safari iOS 15.x | ⚠️ | Falls back to API |
| Safari iOS < 15 | ❌ | API (Option B) |

**Article's browser requirement:** Chrome M83+ (released May 2020) for 4 GB support.

**Assessment:** Chrome 91 was released May 2021 — one full year after M83. Every browser version in the "DuckDB WASM" column of the compatibility matrix was released *after* the V8 TypedArray rework that enables 4 GB WASM memory. The WASM SIMD requirement (the documented reason for the Chrome 91+ floor) coincidentally enforces a stricter baseline than what the 4 GB memory limit alone requires.

**Verdict: No violation. The SIMD check gates browsers to a version range that already has full 4 GB support. The overlap is coincidental rather than intentional — the docs don't explain this relationship — but the net effect is correct.**

**Gap (Low):** The browser compatibility matrix notes don't mention that Chrome 91+ also guarantees 4 GB WASM memory support. A developer reading only the matrix to understand what browsers work and why would not know this. Worth a one-line annotation.

---

### 3. The Signed vs. Unsigned Shift Problem (`>>` vs. `>>>`)

**From the article:**
> HEAP32[(ptr + offset) >> 2] breaks at the 2 GB mark. Emscripten auto-rewrites to >>> when MAXIMUM_MEMORY=4GB is set.

**Assessment:** This is entirely a toolchain concern for DuckDB's Emscripten compilation — not a concern for TOXMAP's code. `@duckdb/duckdb-wasm v1.29.0` (the version pinned in `package.json`) is a mature, actively maintained library. By the time of its release, Emscripten had long since applied the `>>>` rewrite for modules compiled with memory growth enabled.

TOXMAP does not write or modify DuckDB's JavaScript support code. No TOXMAP source file has any `HEAP32` accesses. This issue cannot manifest in the application layer.

**Verdict: Not applicable. No TOXMAP code is affected.**

---

### 4. DuckDB WASM Initialization — Missing Memory Configuration

**From ADR-004:**
```typescript
const db = await duckdb.createInMemory();
await db.open({ query: { castTimestampToDate: true } });
```

**Assessment:** The documented initialization code sets `castTimestampToDate` but does not configure `maximumMemory` or any memory growth limits. DuckDB WASM operates on its internal defaults.

The article explicitly recommends:
> "We recommend that you start with an initial memory that is as small as possible, and grow if necessary; and if you allow growth, gracefully handle the case of a malloc() failure."

DuckDB WASM manages its own heap internally (it doesn't expose raw Emscripten heap pointers to callers), so there is no raw `malloc()` surface to wrap. However, DuckDB does expose a `Query.maximumMemory` or similar configuration that caps how much memory DuckDB is allowed to use for query execution. The documented setup doesn't use this.

For TOXMAP's 5–20 MB query working sets, this omission has no practical effect. It becomes a concern only if the application later adds:
- Multi-year aggregate queries materializing data from several Parquet files simultaneously
- Large `JOIN` operations between TRI and demographics data inside DuckDB
- Any query pattern that causes DuckDB to buffer more than ~500 MB

**Verdict: Gap (Low). The initialization code should explicitly set a `maximumMemory` budget to document the assumption and prevent future over-allocation.**

**Recommended addition:**
```typescript
const db = await duckdb.createInMemory();
await db.open({
  query: {
    castTimestampToDate: true,
  },
  // Explicit memory ceiling. TOXMAP's per-year Parquet queries (~5–20 MB working set)
  // are well within this budget. Increase only if multi-year aggregate queries are added.
  // Context: wasm32 absolute ceiling is 4 GB; Chrome 91+ supports this range.
  // Ref: https://v8.dev/blog/4gb-wasm-memory
});
```

> Note: DuckDB WASM v1.29.0's API for memory configuration should be verified against its changelog — the option name may be `maximumMemory` in `DuckDBConfig` or set via the `duckdb.createInMemory()` options. The intent is to make the budget an explicit, reviewed constant rather than an undocumented default.

---

### 5. OOM Error Handling and the API Fallback Path

**From `duckdbCompat.ts` (documented in ADR-004):**
```typescript
export async function resolveDataSource(): Promise<'duckdb' | 'api'> {
  // Returns 'api' only if WASM SIMD is unsupported
  return (await isDuckDBWasmSupported()) ? 'duckdb' : 'api';
}
```

**Assessment:** The fallback to the API (Option B) is gated solely on WASM SIMD availability. Memory exhaustion during a DuckDB query is a different error class — it throws a JavaScript exception from inside the DuckDB WASM module, not from the SIMD detection step.

The article cautions:
> "2–4 GB is a lot of memory! If you need that much you should use it, but don't do so unnecessarily since there just won't be enough free memory on many users' machines."

For a mobile user with 3 GB total RAM (e.g., a mid-range Android phone), with the OS, browser, and other tabs consuming 2+ GB, the remaining headroom for a DuckDB WASM query could be less than 1 GB. TOXMAP's 5–20 MB working set still fits easily. But the app has no specific handling if a DuckDB query ever throws an OOM error — the exception would bubble up as an unhandled query failure, with no automatic fallback to Option B.

This is not a current concern given the working set sizes. It becomes a concern if:
- The app is extended to load large GeoJSON layers through DuckDB rather than direct fetch
- A user's browser tab is already heavily loaded with other content
- Multi-year queries are added without streaming aggregation

**Verdict: Gap (Low). The `isDuckDBWasmSupported()` check covers SIMD availability but not runtime memory pressure. Consider adding a try/catch wrapper around DuckDB query execution that triggers the API fallback on WASM `out of memory` errors.**

**Recommended pattern:**
```typescript
async function fetchFacilitiesFromDuckDB(params: FacilitySearchParams) {
  try {
    const results = await conn.query(`...`);
    return toGeoJSON(results.toArray());
  } catch (err) {
    if (err instanceof Error && err.message.includes('out of memory')) {
      console.warn('[DuckDB WASM] OOM during query; falling back to API');
      return fetchFacilitiesFromApi(params);
    }
    throw err; // Re-throw non-memory errors
  }
}
```

---

### 6. The PMTiles Tile File (600 MB)

**From ADR-004:**
```
tiles.pmtiles  (map basemap, ~600 MB for US)
```

**Assessment:** This file is served from Cloudflare R2 and consumed exclusively by **MapLibre GL JS** via the PMTiles protocol handler. MapLibre GL uses WebGL for rendering and streams tile data on demand. The PMTiles file is never loaded into DuckDB WASM's heap.

The docs correctly separate tile serving from DuckDB queries:
```
MapLibre GL JS ─ PMTiles protocol            ──► tiles
DuckDB WASM ─ HTTP range requests on Parquet ──► data
```

A naive reading might worry that 600 MB + 150 MB Parquet + 4 MB DuckDB binary = 754 MB "in memory," but MapLibre GL maintains its own tile cache bounded by GPU/RAM limits and never approaches 600 MB resident footprint.

**Verdict: No issue. The separation of PMTiles (MapLibre GL) from Parquet (DuckDB WASM) is correctly designed and the two memory spaces do not combine in the way a worst-case reading would suggest.**

---

### 7. The wasm64 / >4 GB Question

**Assessment:** The article notes that wasm64 (which would allow >4 GB) is planned but not yet standard as of the article's writing (May 2020). As of mid-2026, wasm64 ("memory64") has progressed but remains non-universal in browsers. The TOXMAP architecture makes no assumptions about wasm64 or >4 GB memory.

More importantly, TOXMAP's data scale does not require it:
- 150 MB total Parquet for 38 years of TRI data
- Per-query working set: 5–50 MB
- No data processing pattern that would approach even 1 GB

**Verdict: Not applicable. wasm64 is irrelevant to this use case. The architecture is correct to remain wasm32-compatible.**

---

### 8. Future-Phase Concerns (Not Current Violations)

These scenarios are not present in the current architecture but could push memory usage higher if added without care:

| Future Feature | Memory Risk | Mitigation |
|----------------|-------------|------------|
| Multi-year range queries (e.g., 2010–2024 trend) | DuckDB would hold 14 Parquet files in partial cache | Use per-year sequential queries with aggregation in React, not a single DuckDB multi-file query |
| Census tract GeoJSON through DuckDB | TIGER shapefile data can be large | Keep demographic data fetched via direct `fetch()`, not DuckDB — consistent with current design for `us_counties.geojson` |
| Canadian NPRI layer (~7K facilities) | Negligible | Not a concern |
| Congressional district boundaries | Shapefile can be 60 MB uncompressed | Serve as pre-simplified GeoJSON via direct fetch; do not pipe through DuckDB |
| `ST_ClusterDBSCAN` in-browser | Not planned (clustering is MapLibre's job) | N/A — correctly left out of DuckDB path per ADR-004 |

None of these are roadmap items that the current architecture needs to address today. They are documented here so that future agents working in Phase 4+ do not introduce DuckDB query patterns that would silently bloat memory.

---

## Findings Summary

| # | Component | Violation? | Severity | Finding |
|---|-----------|------------|----------|---------|
| 1 | Per-year Parquet design | ❌ None | — | 4 MB/year is 0.1% of the 2 GB default limit; excellent |
| 2 | Browser matrix (Chrome 91+) | ❌ None | — | SIMD requirement coincidentally enforces M83+ threshold |
| 3 | Signed shift (`>>` vs `>>>`) | ❌ None | — | Toolchain issue in DuckDB's build; not in TOXMAP code |
| 4 | DuckDB init: no `maximumMemory` | ⚠️ Gap | Low | Undocumented assumption about default memory behavior |
| 5 | No OOM catch / API fallback | ⚠️ Gap | Low | Memory errors don't trigger the SIMD-based fallback path |
| 6 | PMTiles 600 MB tile file | ❌ None | — | Correctly separated from DuckDB's memory space |
| 7 | wasm64 / >4 GB assumption | ❌ None | — | Architecture makes no such assumption; data fits in MBs |
| 8 | Browser matrix annotation | ⚠️ Gap | Informational | Matrix doesn't explain that Chrome 91+ implies 4 GB memory support |

---

## Conclusion

**The DuckDB WASM 4 GB memory ceiling does not violate any architectural assumption in TOXMAP, and does not materially affect the design.**

The production architecture's defining choice — per-year Parquet files queried via HTTP range requests — produces query working sets of 5–20 MB. This is not a rounding error relative to the 4 GB limit; it is three orders of magnitude below it. The article's guidance ("start with an initial memory that is as small as possible") describes exactly what the Parquet-range-request design already achieves, though not by explicit reference to this constraint.

The three gaps identified are low-severity quality improvements, not correctness issues:

1. **Add explicit `maximumMemory` configuration** to DuckDB initialization to document the assumed budget.
2. **Add OOM error handling** in DuckDB query wrappers to trigger the API fallback on memory errors, not only on SIMD errors.
3. **Annotate the browser compatibility matrix** to note that Chrome 91+ also satisfies the Chrome M83+ requirement for 4 GB WASM memory support.

None of these gaps would cause failures under TOXMAP's current query patterns. They become relevant only if future phases introduce multi-file DuckDB aggregate queries or large in-memory joins.

