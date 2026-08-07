# Escalation: Discrepancy Aggregation May Mask Year-Over-Year Data Quality Issues

**Date:** 2026-08-06  
**Severity:** Medium (Data Integrity / UX Concern)  
**Status:** ✅ Resolved — Option A implemented  
**Related Defect:** 7.BUG.38 (TRI medium discrepancy display)  
**Reporter:** AI Agent (Frontend Engineer)

> **Terminology Note:** This document was originally written using the term "variance". 
> This was later corrected to "discrepancy" — "variance" is a statistical term (σ²), 
> while "discrepancy" correctly describes the arithmetic difference between values that 
> should match but don't. The UI and code now use "discrepancy" throughout.

---

## 1. Executive Summary

The current discrepancy display implementation in the "By Medium" tab aggregates both the medium sum and EPA-reported total across **all reporting years**. This can produce a misleading discrepancy of zero (or near-zero) when positive and negative year-over-year discrepancies cancel each other out — hiding real data quality inconsistencies from users.

---

## 2. Root Cause Analysis

### 2.1 Current Implementation

In `FacilityDrawer.tsx`, variance is calculated as:

```typescript
// Medium breakdown aggregated across ALL years
const mediumData = releases.length > 0
  ? [
      { medium: 'Air', lbs: releases.reduce((sum, r) => sum + (r.air_release_lbs ?? 0), 0) },
      { medium: 'Water', lbs: releases.reduce((sum, r) => sum + (r.water_release_lbs ?? 0), 0) },
      // ... etc
    ]
  : []

const mediumSum = mediumData.reduce((sum, d) => sum + d.lbs, 0)

// EPA total is also SUM across all years (from backend)
const epaTotal = detail.total_release_lbs ?? 0
const variance = mediumSum - epaTotal
```

### 2.2 The Problem

Both values are aggregated across all reporting years in the dataset. Variance is then computed on these aggregated totals.

**Example scenario:**

| Year | Air | Water | Land | Medium Sum | EPA Total (Field 65) | Variance |
|------|-----|-------|------|------------|----------------------|----------|
| 2008 | 1,000 | 500 | 200 | 1,700 | 3,700 | **−2,000** |
| 2009 | 2,500 | 800 | 500 | 3,800 | 1,800 | **+2,000** |
| **Aggregate** | 3,500 | 1,300 | 700 | **5,500** | **5,500** | **0** |

The aggregate variance shows **0%** — implying perfect data quality — when in reality both years had **significant** data quality issues (2,000 lbs variance each year, just in opposite directions).

### 2.3 Why This Matters

1. **Misleading user perception**: Users may trust data that appears "clean" when it has known quality issues.
2. **Public health decisions**: TOXMAP data informs real-world environmental health assessments. Masking data quality issues undermines informed decision-making.
3. **UCD 2011 precedent**: The original NLM TOXMAP did not display variance at all — we added this transparency feature specifically to help users understand data limitations. If the feature can mislead, it's worse than not having it.

---

## 3. Evidence

### 3.1 Data Model Confirms Aggregation

From `backend/app/services/facility_service.py`:

```python
# 7.BUG.37: Calculate total_release_lbs across ALL years INCLUDING off-site transfers
total_subq = (
    select(
        func.sum(func.coalesce(ReleaseEvent.total_release_lbs, 0) + func.coalesce(ReleaseEvent.off_site_lbs, 0))
    )
    ...
)
```

The backend explicitly sums across all years when returning `total_release_lbs` for facility detail.

### 3.2 Frontend Aggregation Logic

From `FacilityDrawer.tsx` lines 132-143:

```typescript
const mediumData = releases.length > 0
  ? [
      { medium: 'Air', lbs: releases.reduce((sum, r) => sum + (r.air_release_lbs ?? 0), 0) },
      // ... reduces over ALL releases (all years × all chemicals)
    ]
```

The `releases` array contains all release events for the facility across all years. The reduce operation sums them all.

### 3.3 Variance Cancellation is Mathematically Inevitable

Given EPA TRI data quality issues are random (facility self-reporting errors, Form A certifications, amendments), there is no systematic bias. Some years will over-report, others under-report. Over a 15+ year span, these are likely to partially or fully cancel.

---

## 4. Proposed Solutions

### Option A: Per-Year Variance in Trend Tab (Recommended)

**Description:** Add a secondary Y-axis or tooltip to the 15-Year Trend chart showing variance per year. This surfaces data quality issues at the year level while keeping the aggregate view intact.

**Implementation:**
1. Compute per-year variance in the `trendData` calculation
2. Add variance to each data point: `{ year, lbs, variance, variancePct }`
3. Show variance in tooltip: "2008: 3,700 lbs (variance: −2,000 lbs)"
4. Optionally color bars by variance magnitude (red/yellow/green)

**Pros:**
- Most complete visibility — users see exactly which years have issues
- No loss of aggregate information
- Natural fit in the existing Trend tab

**Cons:**
- More complex implementation
- May add visual clutter

**Effort:** Medium (4-6 hours)

---

### Option B: Worst-Case Variance Indicator

**Description:** In addition to aggregate variance, show the "worst single-year variance" as a secondary indicator.

**Implementation:**
1. Calculate variance for each year separately
2. Find `max(abs(yearVariance))` and which year it occurred
3. Display: "Aggregate variance: 0% | Worst year: 2008 (−35%)"

**Pros:**
- Simple to implement
- Immediately flags data quality concerns even when aggregate looks clean
- Minimal UI change

**Cons:**
- Only shows one year — doesn't reveal if multiple years have issues
- Requires explanation to avoid confusion

**Effort:** Low (1-2 hours)

---

### Option C: Single-Year Mode Only

**Description:** Only display variance when a single year is selected in the year filter. When viewing aggregate (all years), hide variance entirely or show a warning that aggregation may mask issues.

**Implementation:**
1. Check if `selectedYear` filter is active and is a single year
2. If yes: show variance as currently implemented
3. If no: either hide variance section, or show: "Select a single year to view data quality variance"

**Pros:**
- Eliminates the masking problem entirely
- Simplest behavioral fix
- Variance is most meaningful at single-year level anyway

**Cons:**
- Users lose visibility into aggregate data quality
- May confuse users who expect consistency ("why does this disappear?")

**Effort:** Low (1 hour)

---

### Option D: Variance Volatility Warning

**Description:** Compute a "variance volatility" metric (e.g., standard deviation of year-over-year variance). If volatility is high, show a warning even if aggregate is near zero.

**Implementation:**
1. Calculate variance for each year
2. Compute standard deviation of yearly variances
3. If stddev > threshold (e.g., 10% of average release): show warning badge
4. Display: "⚠️ High variance volatility — data quality varies significantly by year"

**Pros:**
- Alerts users to hidden issues without removing aggregate display
- Statistically principled

**Cons:**
- Requires threshold tuning
- More abstract concept for users to understand

**Effort:** Medium (2-3 hours)

---

## 5. Impact Assessment

| Option | Accuracy | UX Clarity | Implementation | Risk |
|--------|----------|------------|----------------|------|
| **A: Per-Year in Trend** | ★★★★★ | ★★★★☆ | Medium | Low |
| **B: Worst-Case Indicator** | ★★★★☆ | ★★★★★ | Low | Low |
| **C: Single-Year Only** | ★★★★★ | ★★★☆☆ | Low | Medium (UX confusion) |
| **D: Volatility Warning** | ★★★★☆ | ★★★☆☆ | Medium | Medium (threshold debate) |

---

## 6. Decision Made

**Selected:** ✅ **Option A — Per-Year Variance in Trend Tab**  
**Date:** 2026-08-06  
**Rationale:** User reviewed options and selected Option A as "the best" — provides most complete visibility without losing any information.

---

## 7. Implementation Summary

**Changes implemented in `FacilityDrawer.tsx`:**

1. **Per-year variance in Trend tab:**
   - Extended `trendData` to include `mediumSum`, `variance`, and `variancePct` for each year
   - Custom tooltip shows EPA total, medium sum, and variance with color coding (green/red)
   - Red ring indicator around dots for years with ≥5% variance
   - Legend explaining the variance indicator

2. **Aggregate variance label update (By Medium tab):**
   - Renamed "Variance (medium sum vs. EPA total)" → "Aggregate Variance (all years)"
   - Updated footnote to warn that aggregate may mask year-over-year issues
   - Added call-to-action: "see the 15-Year Trend tab for per-year variance details"

**New test IDs added:**
- `trend-tooltip` — Custom tooltip element in Trend chart
- `trend-tooltip-variance` — Variance line within tooltip
- `trend-variance-legend` — Legend explaining variance indicators

**Status:** ✅ Implemented — 2026-08-06

---

## 7.1 Follow-up Fix: Always Show Variance in Tooltip

**Issue discovered:** After implementing Option A, it was observed that years with very small variance (< 1 lb) did not show variance information in the tooltip at all. This was confusing because users couldn't tell if:
- ✅ Variance was ~0 (good data quality)
- ❓ Data was missing
- ❓ Something was broken

**Example:** CLEAN HARBORS DEER TRAIL LLC (108555 EAST HIGHWAY 36, DEER TRAIL, CO) — year 2015 showed only "EPA Total: 895,752.46 lbs" with no variance details, even though the facility had data that year.

**Resolution:** Implemented **Option B** — always show Medium Sum and Variance in tooltip when there is any data for that year (EPA Total > 0 or Medium Sum > 0). Variance near zero now displays as "+0 lbs (0.0%)" in green, making it clear the data is consistent.

**Change:** Updated tooltip condition from `hasVariance = Math.abs(data.variance) >= 1` to `hasData = data.lbs > 0 || data.mediumSum > 0`.

**Date:** 2026-08-06

---

## 7.2 Follow-up Fix: Conditional Note Display Based on Per-Year Discrepancy Analysis

**Issue discovered (2026-08-07):** After the initial fixes, it was observed that the By Medium tab note could be confusing in certain scenarios. Specifically:

1. **PRODUCERS CHEMICAL CO (Sugar Grove, IL):** Showed a simple note ("See the 15-Year Trend tab for year-by-year release data") even though the 15-Year Trend tab showed **multiple years with ≥5% discrepancy** (red ring indicators). The aggregate discrepancy was ~0 because +/− values canceled out.

2. **MERCER GENERATING STATION (Hamilton Township, NJ):** Showed the same note as above, which was appropriate since this facility has **no meaningful discrepancies** at either the aggregate or per-year level.

**Problem:** The note did not distinguish between "aggregate minimal because data is clean" vs "aggregate minimal because discrepancies cancel out."

**Resolution:** Implemented a **three-tier conditional note** in the By Medium tab:

| Condition | Note Display |
|-----------|--------------|
| **Aggregate ≥ 1 lb** | "This aggregate discrepancy is calculated across all reporting years. Positive and negative year-over-year discrepancies may cancel out — **see the 15-Year Trend tab for per-year discrepancy details**." |
| **Aggregate < 1 lb BUT any year has ≥5%** | "While the aggregate discrepancy is minimal, **some individual years show ≥5% discrepancies** that cancel out — see the 15-Year Trend tab for per-year details." |
| **Aggregate < 1 lb AND no years have ≥5%** | "The EPA total combines on-site releases with off-site transfers. See the 15-Year Trend tab for year-by-year release data." |

**Code change:** Added `hasYearWithHighDiscrepancy` variable computed from `trendData.some(d => d.discrepancyPct >= 5 && d.lbs > 0)` and updated the conditional rendering of the footnote.

**Date:** 2026-08-07

---

## Addendum: Evidence for Three-Tier Note Display (2026-08-07)

### A.1 Variant 1: Aggregate Discrepancy ≥ 1 lb

**Facility:** CLEAN HARBORS DEER TRAIL LLC. (Deer Trail, CO)  
**TRI Facility ID:** `80105SFTYK10855`

**API-Verified Data:**
```
EPA Total (all years): 26,478,608.28 lbs
Aggregate Discrepancy: +35,824.32 lbs (0.1%)
```

**Per-Year Breakdown (2012-2024):**
| Year | EPA Total | Medium Sum | Discrepancy |
|------|-----------|------------|-------------|
| 2012 | 952,243 | 914,804 | **−37,439** |
| 2013 | 913,723 | 914,804 | +1,081 |
| 2014 | 873,797 | 914,804 | **+41,006** |
| 2015 | 895,752 | 895,752 | 0 |
| 2016 | 884,762 | 914,804 | **+30,042** |
| 2017 | 896,629 | 914,804 | +18,175 |
| 2018 | 473,327 | 473,327 | 0 |
| 2019 | 887,753 | 914,804 | +27,051 |
| 2020 | 298,228 | 298,228 | 0 |
| 2021 | 902,783 | 914,804 | +12,020 |
| 2022 | 697,750 | 697,750 | 0 |
| 2023 | 795,667 | 795,667 | 0 |
| 2024 | 914,804 | 914,804 | 0 |

**UI displays:** "Aggregate Discrepancy (all years): +35,824.32 lbs (0.1%)" with full explanation note.

---

### A.2 Variant 2: Aggregate Minimal BUT Years Have ≥5% Discrepancy

**Facility:** PRODUCERS CHEMICAL CO (Sugar Grove, IL)  
**TRI Facility ID:** `6055WPRDCR196BU`

**API-Verified Data:**
```
EPA Total (all years): 3,274.01 lbs
Aggregate Discrepancy: ~0 lbs (< 1 lb threshold)
```

**Per-Year Breakdown (2012-2024) — showing years with ≥5%:**
| Year | EPA Total | Medium Sum | Discrepancy | **%** |
|------|-----------|------------|-------------|-------|
| 2012 | 106.67 | 101.00 | −5.67 | **5.3%** |
| 2013 | 94.77 | 101.00 | +6.23 | **6.6%** |
| 2014 | 107.91 | 101.00 | −6.91 | **6.4%** |
| 2015 | 167.00 | 167.00 | 0 | 0% |
| 2016 | 106.20 | 101.00 | −5.20 | 4.9% |
| 2017 | 121.18 | 101.00 | −20.18 | **16.7%** |
| 2018 | 162.00 | 162.00 | 0 | 0% |
| 2019 | 111.45 | 101.00 | −10.45 | **9.4%** |
| 2020 | 66.00 | 66.00 | 0 | 0% |
| 2021 | 107.65 | 101.00 | −6.65 | **6.2%** |
| 2022 | 317.00 | 317.00 | 0 | 0% |
| 2023 | 240.00 | 240.00 | 0 | 0% |
| 2024 | 101.00 | 101.00 | 0 | 0% |

**6 years have ≥5% discrepancy** (2012, 2013, 2014, 2017, 2019, 2021), but the aggregate is ~0 because + and − values cancel.

**UI displays:** "While the aggregate discrepancy is minimal, **some individual years show ≥5% discrepancies** that cancel out — see the 15-Year Trend tab for per-year details."

---

### A.3 Variant 3: No Meaningful Discrepancies

**Facility:** MERCER GENERATING STATION (Hamilton Township, NJ)  
**TRI Facility ID:** `08611MRCRGLAMBE`

**API-Verified Data:**
```
EPA Total (all years): 1,102,727.83 lbs
Aggregate Discrepancy: ~0 lbs (< 1 lb threshold)
```

**Per-Year Breakdown (2012-2024):**
| Year | EPA Total | Medium Sum | Discrepancy | **%** |
|------|-----------|------------|-------------|-------|
| 2015 | 2,588.10 | 2,588.10 | 0 | **0%** |

**Note:** Only 2015 has data within the 15-year window. Year 2010 (1,098,758 lbs) is outside the 2012-2026 range shown in the Trend tab. The single year with data shows **0% discrepancy** — clean data.

**UI displays:** "The EPA total combines on-site releases (air, water, land, underground) with off-site transfers. See the 15-Year Trend tab for year-by-year release data."

---

### A.4 Verification Commands

```bash
# Variant 1: CLEAN HARBORS
curl -s "http://localhost:8000/api/v1/facilities/80105SFTYK10855" | jq '.total_release_lbs'
# Returns: 26478608.28

# Variant 2: PRODUCERS CHEMICAL
curl -s "http://localhost:8000/api/v1/facilities/6055WPRDCR196BU/releases?from_year=2012&to_year=2026" \
  | jq '[.[] | {year: .reporting_year, pct: ...}] | map(select(.pct >= 5))'
# Returns: 6 years with ≥5% discrepancy

# Variant 3: MERCER GENERATING
curl -s "http://localhost:8000/api/v1/facilities/08611MRCRGLAMBE/releases?from_year=2012&to_year=2026" \
  | jq 'length'
# Returns: 6 (all records for 2015 only, all with 0% discrepancy)
```

---

## 8. References

- **Related escalation:** `ESCALATION_20260806_TRI_MEDIUM_TOTAL_VARIANCE.md` (original variance issue)
- **Implementation file:** `frontend/src/components/FacilityDetail/FacilityDrawer.tsx` lines 145-188, 494-560
- **Backend aggregation:** `backend/app/services/facility_service.py` lines 428-438
- **EPA TRI Data Quality:** https://www.epa.gov/toxics-release-inventory-tri-program/tri-data-quality
- **Defect ID:** 7.BUG.38

---

*This escalation was generated by an AI agent. Option A selected and implemented per user decision.*
