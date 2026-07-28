# Map Layers — Resolution Summary

**Date:** 2026-07-28  
**Status:** ✅ RESOLVED (TRI + Superfund)  
**Resolved by:** Frontend Engineer

---

## Summary

Both TRI facility circles and Superfund site diamonds were limited to ~500 miles from the viewport center because each layer used a radius-based API call capped at 500 miles. Now both layers fetch ALL data once via dedicated `/browse` endpoints.

---

## Architecture (Simplified)

### Data Flow
```
TRI Browse mode ────► GET /api/v1/facilities/browse ────► All ~22k facilities
Superfund Browse ───► GET /api/v1/superfund/browse ─────► All ~1.7k sites
                                                         │
Search mode ────────► GET /api/v1/{facilities|superfund}?lat=...&radius=... ──► Radius-filtered results
```

### Layer Structure
| Layer | Source | Type | Toggle |
|-------|--------|------|--------|
| `facility-circles` | `facilities` | circle | `setLayoutProperty('facility-circles', 'visibility', ...)` |
| `superfund-sites` | `superfund-source` | symbol (diamond icons) | `setLayoutProperty('superfund-sites', 'visibility', ...)` |

### Key Behaviors
| Behavior | Implementation |
|----------|----------------|
| Toggle TRI on/off | `map.setLayoutProperty('facility-circles', 'visibility', ...)` |
| Toggle Superfund on/off | `map.setLayoutProperty('superfund-sites', 'visibility', ...)` |
| Zoom subset | MapLibre viewport clipping (automatic) |
| Circle sizing | Zoom-interpolated `circle-radius` paint property |
| Diamond sizing | Fixed 16x16 SVG icon sprites |

---

## What Was Fixed (2026-07-28)

### Root Cause: Both Layers Used 500-Mile Radius

**TRI Problem (fixed earlier):**
- Browse mode called `/api/v1/facilities` with `lat=39.5, lon=-98.35, radius_miles=500`
- Returned only ~500 facilities within 500 miles of Kansas

**Superfund Problem (fixed today):**
- `useSuperfundViewport` computed center+radius from viewport bbox
- Radius capped at 500 miles: `Math.min(radius, 500)`
- Different zoom levels = different centers = different subsets shown
- **Never showed all ~1,700 sites**

### The Fix (Same Pattern for Both)

| Layer | Old API | New API | Hook Change |
|-------|---------|---------|-------------|
| TRI | `/facilities?lat=...&radius=500` | `/facilities/browse` | `useMapFacilities(null)` → fetch once |
| Superfund | `/superfund?lat=...&radius=500` | `/superfund/browse` | `useSuperfundViewport()` → fetch once, no bbox param |

### Files Changed (Superfund Fix)

| File | Change |
|------|--------|
| `backend/app/routers/superfund.py` | Added `GET /superfund/browse` endpoint |
| `backend/app/services/superfund_service.py` | Added `get_all_superfund_browse()` function |
| `frontend/src/api/superfund.ts` | Added `fetchAllSuperfundBrowse()` API client |
| `frontend/src/hooks/useSuperfundViewport.ts` | Rewritten: fetch once on mount, no bbox dependency |
| `frontend/src/App.tsx` | Removed `mapBbox` param from `useSuperfundViewport()` call |

---

## Additional Fix: React StrictMode Compatibility (2026-07-28)

### Symptom
Superfund diamonds were **still not appearing** even after the `/browse` endpoint was implemented. The sidebar showed "Superfund / NPL Sites" with no count, and debugging revealed the `superfund-source` and `superfund-sites` layer were never created.

### Root Cause: `hasFetchedRef` Set Before Fetch Completion

The `useSuperfundViewport` hook had a classic StrictMode bug:

```typescript
// BROKEN — StrictMode kills this
const hasFetchedRef = useRef(false)

useEffect(() => {
  if (hasFetchedRef.current) return  // Second mount: ref is TRUE, skips fetch
  hasFetchedRef.current = true       // First mount: set TRUE immediately

  fetchAllSuperfundBrowse(...)       // First mount: aborted by StrictMode cleanup
    .then(setData)                   // Never runs — request was aborted
}, [])
```

React 18 StrictMode double-invokes effects to detect side effects:
1. **First mount:** Sets `hasFetchedRef = true`, starts fetch, then React aborts via cleanup
2. **Second mount:** Sees `hasFetchedRef = true`, skips fetch entirely
3. **Result:** Data is never fetched, diamonds never appear

### The Fix: Track Successful Completion, Not Attempt

```typescript
// FIXED — matches useMapFacilities pattern
const hasSucceededRef = useRef(false)
const abortRef = useRef<AbortController | null>(null)

useEffect(() => {
  if (hasSucceededRef.current) return  // Only skip if SUCCEEDED before

  if (abortRef.current) abortRef.current.abort()
  const controller = new AbortController()
  abortRef.current = controller

  fetchAllSuperfundBrowse(controller.signal)
    .then((result) => {
      hasSucceededRef.current = true   // Mark success AFTER data arrives
      setData(result)
    })
    .catch(...)

  return () => controller.abort()
}, [])
```

### File Changed

| File | Change |
|------|--------|
| `frontend/src/hooks/useSuperfundViewport.ts` | Replaced `hasFetchedRef` with `hasSucceededRef` pattern; only mark fetched after success |

### Pattern Reference
The `useMapFacilities` hook (for TRI data) already implemented this pattern correctly with `lastSuccessfulKeyRef`. The Superfund hook was written with a simpler but broken pattern.

---

## Answers to Critical Questions

### 1. Are all diamonds on the same layer?
**Yes.** All Superfund sites render on a single `superfund-sites` symbol layer. Two icon sprites (`superfund-diamond-filled` for NPL, `superfund-diamond-outline` for CERCLIS/Deleted) are selected by the `status` property.

### 2. Shouldn't we just be able to toggle them on/off?
**Yes, and now we can.** Toggle works via `setLayoutProperty('superfund-sites', 'visibility', ...)`.

### 3. Shouldn't zooming just subset?
**Yes, and now it does.** The full dataset (~1,700 sites) is fetched once. MapLibre handles viewport clipping automatically. Zooming in/out changes which diamonds are visible without refetching.

### 4. Is a backend change required to enable more than 500 mi radius?
**Yes — and it was implemented.** The existing endpoint has `radius_miles` capped at 500. The new `/api/v1/superfund/browse` endpoint bypasses this constraint for the always-on layer.

### 5. Can we use a fetch-all API call in browse mode?
**Yes — this is the implemented solution.** The new `/api/v1/superfund/browse` endpoint returns all sites (up to 5k limit, currently ~1,700).

---

## Verified Behavior

| Test | TRI | Superfund |
|------|-----|-----------|
| Initial load shows all US sites | ✅ ~22k circles | ✅ ~1.7k diamonds |
| Toggle hides all markers | ✅ | ✅ |
| Toggle shows all markers | ✅ | ✅ |
| Zoom in reduces visible count | ✅ | ✅ |
| Zoom out increases visible count | ✅ | ✅ |
| Pan doesn't trigger refetch | ✅ | ✅ |

---

## Performance Notes

| Layer | Payload | Gzipped |
|-------|---------|---------|
| TRI | ~22k × 200 bytes = ~4.4 MB | ~600 KB |
| Superfund | ~1.7k × 200 bytes = ~340 KB | ~50 KB |

- **No refetch on pan/zoom:** Both datasets fetched once, MapLibre handles rendering
- **No clustering:** Circle/diamond size is constant or zoom-interpolated

---

## Future Considerations

1. **Progressive loading:** If either dataset grows significantly, consider tile-based loading
2. **Re-enable clustering:** If MapLibre fixes the Supercluster bug with imperative source creation
3. **WebGL optimization:** For >50k points, consider deck.gl or MapLibre's globe view
