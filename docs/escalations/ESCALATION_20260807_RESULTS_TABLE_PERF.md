# Performance Bug: Location Search 60-Second Delay

**Created:** 2026-08-07  
**Resolved:** 2026-08-07  
**Status:** ✅ RESOLVED  
**Severity:** P0 Critical (UX-blocking, 60s search latency)

---

## Problem Statement

Location searches (e.g., "Seattle, WA 98166") took 60+ seconds while the CPU spiked (fan ramped up loudly), while chemical searches on the same location returned in ~1 second.

## Root Cause

**Query structure inefficiency in `facility_service.py`:**

The original SQL query aggregated ALL ~1M release_events rows first, then applied the spatial filter. This caused:
- Full table scan on release_events (~1M rows)
- Unnecessary Chemical JOIN when no chemical filter was applied
- 60+ seconds of database processing

## Solution

**Flip the query order: filter facilities spatially FIRST, then aggregate only their releases.**

```python
# BEFORE: Aggregated ALL releases, then filtered spatially
rel_stmt = (
    select(...)
    .join(Chemical, ...)  # Unnecessary when no chemical filter!
    .group_by(ReleaseEvent.facility_id)
)
rel_sub = rel_stmt.subquery()
stmt = (
    select(Facility, rel_sub.c.total_lbs)
    .join(rel_sub, ...)
    .where(func.ST_DWithin(...))  # Too late! Already scanned 1M rows
)

# AFTER: Filter facilities spatially, then aggregate only their releases
matching_fac_stmt = (
    select(Facility.id)
    .where(func.ST_DWithin(...))  # Uses PostGIS GiST index → ~150 rows
)
matching_fac_ids = matching_fac_stmt.scalar_subquery()

rel_stmt = (
    select(...)
    .where(ReleaseEvent.facility_id.in_(matching_fac_ids))  # Only ~10K rows
    .group_by(ReleaseEvent.facility_id)
)
# Chemical JOIN only added when chemical filter is present
if needs_chemical_join:
    rel_stmt = rel_stmt.join(Chemical, ...)
```

## Performance Improvement

| Search Type | Before | After | Speedup |
|-------------|--------|-------|---------|
| Seattle (no chemical) | 63,110 ms | 37 ms | **1,700x** |
| Seattle + LEAD | 1,109 ms | ~40 ms | **27x** |

## Files Changed

| File | Change |
|------|--------|
| `backend/app/services/facility_service.py` | Refactored `get_facilities_near()` to filter spatially first, then aggregate |
| `backend/app/services/facility_service.py` | Refactored `get_all_facilities_browse()` to conditionally join Chemical table |

## Verification

```bash
# Direct backend test (bypasses all network overhead)
docker exec toxmap-backend curl -s -o /dev/null -w "Time: %{time_total}s\n" \
  "http://localhost:8000/api/v1/facilities?lat=47.580138&lon=-122.3273036&radius_miles=25&state=WA&restrict_to_state=true"
# Before: Time: 61.141387s
# After:  Time: 0.273468s
```

## Defect Logged

Added as **7.PERF.1** in `B-002_DEFECT_TRIAGE.md`.
