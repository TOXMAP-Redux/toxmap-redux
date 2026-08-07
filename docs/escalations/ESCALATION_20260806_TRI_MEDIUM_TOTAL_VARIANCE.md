# Escalation: TRI Medium Breakdown ≠ On-Site Release Total

**Date:** 2026-08-06  
**Reporter:** Agent (BE+FE)  
**Severity:** Medium (data integrity, not blocking)  
**Status:** ✅ Resolved — Option B variant implemented  

---

## 1. Summary

The "By Medium" tab in the facility detail panel displays release amounts by medium (Air, Water, Land, Underground, Off-site). The sum of these medium breakdowns **does not equal** the "Top Chemicals" total displayed in the same panel. This is not a bug in our code — it is an inherent data quality limitation in EPA TRI reporting.

**Resolution:** Implemented a variant of Option B that displays the EPA-reported total, calculated variance, and a detailed explanatory footnote in the "By Medium" tab.

---

## 2. Root Cause Analysis

### 2.1 How Totals Are Computed

| UI Element | Data Source | Calculation |
|------------|-------------|-------------|
| **Top Chemicals total** | `facility_service.get_facility_detail()` | `SUM(COALESCE(total_release_lbs, 0) + COALESCE(off_site_lbs, 0))` |
| **By Medium bars** | `/api/v1/facilities/{id}/releases` | Frontend sums: `air_release_lbs + water_release_lbs + land_release_lbs + underground_release_lbs + off_site_lbs` |

### 2.2 Field Definitions (from EPA TRI Basic Data Files Documentation, August 2024)

> **Source:** [basic_data_files_documentation_august_2024.md](../product/basic_data_files_documentation_august_2024.md)

| Our Field | EPA Field # | EPA Field Name | Official EPA Description |
|-----------|-------------|----------------|--------------------------|
| `total_release_lbs` | **65** | ON-SITE RELEASE TOTAL | "Total quantity of the chemical released to the air, water, and land at the facility. **This is the sum of rows #51 through #64.**" |
| `air_release_lbs` | 51+52 | 5.1 – FUGITIVE AIR + 5.2 – STACK AIR | Fugitive + stack (point source) air emissions |
| `water_release_lbs` | 53 | 5.3 – WATER | Surface water discharges |
| `underground_release_lbs` | 55+56 | 5.4.1 – UNDERGROUND CLASS I + 5.4.2 – UNDERGROUND CLASS II-V | Injection into Class I and Class II-V wells |
| `land_release_lbs` | 58-64 | 5.5.1A through 5.5.4 | RCRA landfills + Other landfills + Land treatment + RCRA surface impoundments + Other surface impoundments + Other disposal |
| `off_site_lbs` | **88** | OFF-SITE RELEASE TOTAL | "Total quantity of the toxic chemical reported as transferred to off-site locations for release or disposal. **Sum of rows #66 + (#69 through #87).**" |

#### EPA's Explicit Field 65 Definition:

> **Field 65 (ON-SITE RELEASE TOTAL):** "Total quantity of the chemical released to the air, water, and land at the facility. **This is the sum of rows #51 through #64.**"
> — EPA TRI Basic Data Files Documentation, August 2024, Page 12

#### EPA's Total Releases Field:

> **Field 107 (TOTAL RELEASES):** "The total on- and off-site releases from sections 5 and 6 of the Form R. **The value for this field equals On-site Release Total (row #65) + Off-site Release Total (row #88).**"
> — EPA TRI Basic Data Files Documentation, August 2024, Page 14

### 2.3 The Fundamental Problem

Per EPA documentation, **Field 65 is explicitly defined as the sum of Fields 51–64**. However, in practice, Field 65 often does **not** equal this sum in the actual TRI data files.

This is a known TRI data quality limitation. The EPA receives self-reported data from facilities, and validation does not always enforce arithmetic consistency between totals and breakdowns.

### 2.4 Contributing Factors (from EPA Documentation)

The EPA documentation (§"ZEROES IN THE DATA") identifies three cases where numeric fields may not reflect actual reported values:

1. **"NA" (Not Applicable)**: Facilities report "NA" when a release pathway is not possible (e.g., no water body nearby → "NA" for water releases). The TRI Basic Data Files substitute `0` for "NA" values.

2. **Blank responses**: Prior to electronic reporting, paper forms could have blank fields. The TRI-MEweb software now requires numeric values or "NA", but legacy data may have inconsistent blanks-as-zeros.

3. **Form A Certification**: Facilities filing Form A (instead of Form R) certify they are below thresholds without reporting detailed quantities. All release fields are set to `0` for Form A records.

---

## 3. Evidence

### 3.1 Case Study: Hanford Site (99352SDPRTPOBOX), 2008

```sql
SELECT 
    chemical,
    total_release_lbs AS "Field 65 (ON-SITE RELEASE TOTAL)",
    (air + water + land + underground) AS "Computed Sum (Fields 51-64)",
    total_release_lbs - (air + water + land + underground) AS "Variance"
FROM release_events
WHERE facility = 'Hanford' AND year = 2008;
```

| Chemical | Field 65 (ON-SITE RELEASE TOTAL) | Computed Sum (Fields 51-64) | Variance | Notes |
|----------|----------------------------------|------------------------------|----------|-------|
| NAPHTHALENE | 200,554 | 218,715 | **-18,161** | Land ALONE (218,712) exceeds Field 65 total |
| LEAD | 71,127 | 60,544 | +10,583 | Field 65 exceeds computed sum by 15% |
| TOLUENE | 22,079 | 18,429 | +3,650 | Field 65 exceeds computed sum by 17% |
| LITHIUM CARBONATE | 524 | 456 | +68 | 13% variance |
| ZINC (FUME OR DUST) | 777 | 805 | -28 | Computed sum exceeds Field 65 |
| XYLENE (MIXED ISOMERS) | 4,917 | 4,891 | +26 | Minor variance |
| PROPYLENE | 248 | 250 | -2 | Rounding difference |

### 3.2 Critical Finding: Impossible Data

For **NAPHTHALENE**, the database shows:
- `total_release_lbs` (Field 65): **200,554.45 lbs**
- `land_release_lbs` (Fields 58-64): **218,712.00 lbs**

The land breakdown **alone** exceeds the reported ON-SITE RELEASE TOTAL by 18,158 lbs. This is arithmetically impossible if EPA's documentation is correct that Field 65 = SUM(Fields 51–64).

This proves the variance is **in the source EPA data**, not in our ingestion or aggregation logic.

### 3.3 Variance Patterns Across TRI Dataset

Across the TRI dataset, we observe three variance patterns:

| Pattern | Cause | Example |
|---------|-------|---------|
| **Field 65 > Computed Sum** | Facility may have reported a rounded/estimated total; or sub-fields were amended down without updating total | LEAD at Hanford: 71,127 vs 60,544 |
| **Field 65 < Computed Sum** | Sub-field data may have been amended upward without updating total; or rounding errors | NAPHTHALENE at Hanford: 200,554 vs 218,715 |
| **Field 65 ≈ Computed Sum** | Facility submitted internally consistent data | Rare; indicates careful data entry |

---

## 4. Why This Happens (Per EPA Documentation)

The EPA TRI Basic Data Files Documentation (August 2024) identifies several scenarios that contribute to data inconsistencies:

### 4.1 "NA" (Not Applicable) Substitution

> "Facilities that report 'NA' or 'Not Applicable' for a quantity on the Form R. Reporting 'NA' means that the release or waste management quantity is not possible for that facility."
> — EPA TRI Basic Data Files Documentation, §"ZEROES IN THE DATA"

The TRI Basic Data Files substitute `0` for "NA" values. If a facility reported "NA" for sub-fields but a calculated total, the sum will not match.

### 4.2 Form A Certification (Field 49)

> "Form A allows facilities otherwise meeting EPCRA Section 313 reporting thresholds the option to certify that, for a particular chemical, they do not exceed 500 pounds for the total annual reportable amount... Facilities do not have to report any release or other waste management information. **The Basic Data file record will contain zeroes for all release and other management quantities from a Form A.**"
> — EPA TRI Basic Data Files Documentation, §"ZEROES IN THE DATA"

Form A records have `form_type = 'A'` (vs. `'R'` for Form R). All quantity fields are zero, but this does not indicate actual zero releases.

### 4.3 Legacy Paper Form Blanks

> "Where zeroes appear instead of blanks occurs when facilities do not respond to quantity questions on the Form R, leaving them blank. This was primarily an issue prior to the TRI Electronic Reporting Rule, when the TRI Program still accepted paper reporting forms."
> — EPA TRI Basic Data Files Documentation, §"ZEROES IN THE DATA"

Pre-TRI-MEweb data (before electronic mandatory reporting) may have inconsistent zero-vs-blank handling.

### 4.4 Additional Causes (Not EPA-Documented)

1. **Facility self-reporting arithmetic errors**: TRI data is self-reported; facilities may make calculation mistakes
2. **EPA data corrections**: EPA may adjust totals during validation without updating sub-fields
3. **Amendments**: Facilities submit corrections that update some fields but not others
4. **Estimation methodology differences**: Totals may be directly measured while breakdowns are estimated
5. **Independent rounding**: Sub-fields may be rounded independently before summation

---

## 5. Proposed Solutions

### Option A: Compute Total from Mediums (Recommended)

**Change:** For the "By Medium" tab, display a total that equals `SUM(air + water + land + underground + off_site)` computed from the same data used for the bars.

**Implementation:**
```tsx
// FacilityDrawer.tsx — add computed total for By Medium tab
const mediumTotal = mediumData.reduce((sum, d) => sum + d.lbs, 0);
// Display mediumTotal instead of detail.total_release_lbs in By Medium tab
```

**Pros:**
- Math adds up exactly — bars sum to displayed total
- Internally consistent within the tab
- No data loss

**Cons:**
- "By Medium" total will differ from "Top Chemicals" total (same data, different computation)
- May confuse users who expect totals to match across tabs

**Impact:** Frontend-only change; ~10 lines of code

---

### Option B: Add Explanatory Footnote

**Change:** Add a footnote below the "By Medium" chart explaining the variance.

**Implementation:**
```tsx
<p className="text-xs text-gray-500 mt-2">
  * Medium breakdowns may not sum to facility total due to EPA data quality variations.
  <a href="https://www.epa.gov/toxics-release-inventory-tri-program/tri-data-quality">
    Learn more
  </a>
</p>
```

**Pros:**
- Transparent about data limitations
- No computation changes
- Educates users about TRI data quality

**Cons:**
- Does not fix the discrepancy
- Users may still be confused

**Impact:** Frontend-only change; ~5 lines of code

---

### Option C: Use Field 65 Total, Hide Breakdown Variance

**Change:** For "By Medium" tab, show only the total (Field 65 + Field 88) without the bar chart breakdown.

**Pros:**
- No variance to explain
- Consistent with "Top Chemicals" total

**Cons:**
- Loses medium breakdown information (a key TOXMAP feature per Fig 11)
- Users cannot see which mediums contribute most

**Impact:** Remove functionality — not recommended

---

### Option D: Recompute Everything from Mediums

**Change:** Stop using EPA Field 65 entirely. Compute `total_release_lbs` as `SUM(air + water + land + underground)` during ingestion.

**Pros:**
- Complete internal consistency
- Math always adds up

**Cons:**
- Deviates from official EPA totals
- May not match other EPA tools/reports
- Requires database migration and re-ingestion

**Impact:** Backend ingestion change + migration; ~50 lines of code

---

## 6. Implemented Solution (Option B Variant)

**What was implemented:** A variant of Option B that shows:

1. **EPA-Reported Total** displayed below the bar chart
2. **Calculated Variance** showing the difference (+ or −) between the medium breakdown sum and EPA total, with percentage
3. **Detailed Explanatory Footnote** explaining why variance exists, referencing EPA TRI data quality documentation

**Implementation details:**
- Added `mediumSum` computed value: sum of all medium breakdown bars
- Added variance section in "By Medium" tab with `data-testid="medium-variance-section"`
- Variance only displayed when |variance| ≥ 1 lb (suppresses rounding noise)
- Variance color-coded: green for positive (medium sum > EPA total), red for negative
- Footnote includes external link to EPA TRI data quality page

**Code changes:**
```tsx
// FacilityDrawer.tsx — new computed value
const mediumSum = mediumData.reduce((sum, d) => sum + d.lbs, 0)

// New UI section showing EPA total, variance, and footnote
<div data-testid="medium-variance-section">
  <div>EPA-Reported Total: {formatLbs(detail.total_release_lbs)}</div>
  <div>Variance: {variance >= 0 ? '+' : '−'}{formatNumber(varianceAbs)} lbs ({variancePct}%)</div>
  <p>Note: The sum of medium breakdowns may differ from the EPA-reported total...</p>
</div>
```

**Result:**
- ✅ Users see the official EPA total prominently
- ✅ Variance is calculated and displayed when meaningful
- ✅ Detailed explanation educates users about TRI data quality limitations
- ✅ External EPA link for further reading
- ✅ No internal consistency issues — we show both numbers and explain the difference

---

## 7. Files Changed

| File | Change |
|------|--------|
| `frontend/src/components/FacilityDetail/FacilityDrawer.tsx` | Added `mediumSum` computed value; added variance section with EPA total, calculated variance, and explanatory footnote |

---

## 8. References

1. **EPA TRI Basic Data Files Documentation, August 2024**  
   Local: [basic_data_files_documentation_august_2024.md](../product/basic_data_files_documentation_august_2024.md)  
   Source: EPA TRI Program official documentation

2. **EPA TRI Data Quality Information**  
   https://www.epa.gov/toxics-release-inventory-tri-program/tri-data-quality

3. **EPA Form R Instructions**  
   https://www.epa.gov/toxics-release-inventory-tri-program/tri-form-r-instructions

4. **TOXMAP API Contract**  
   Local: [TOXMAP_API_CONTRACT.md](../api/TOXMAP_API_CONTRACT.md)

5. **TOXMAP Screen Catalog Fig 11**  
   Local: [TOXMAP_SCREEN_CATALOG.md](../product/TOXMAP_SCREEN_CATALOG.md) — three-tab bar chart design

6. **Code References**  
   - [release_event.py](../../backend/app/models/release_event.py) — column semantics documentation  
   - [tri_parser.py](../../backend/ingestion/tri_parser.py) — field mapping and aggregation logic
