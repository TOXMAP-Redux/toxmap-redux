# ADR-007: Chemical Families for Transparent Right-to-Know Search

| Field             | Value                                                                                                     |
|-------------------|-----------------------------------------------------------------------------------------------------------|
| **ID**            | ADR-007                                                                                                   |
| **Title**         | Chemical Families for Transparent Right-to-Know Search                                                    |
| **Date**          | 2026-07-31                                                                                                |
| **Status**        | **Accepted**                                                                                              |
| **Deciders**      | Architecture Review                                                                                       |
| **NLM Sources**   | [NBK590906](https://www.ncbi.nlm.nih.gov/books/NBK590906/) (Lead and Lead Compounds)                      |
| **EPA Sources**   | [TRI Chemical List](https://www.epa.gov/toxics-release-inventory-tri-program/tri-listed-chemicals)       |
| **Supersedes**    | —                                                                                                         |
| **Superseded by** | —                                                                                                         |

---

## Context

### The Problem

EPA TRI allows facilities to report the same element/compound under multiple reporting categories. For lead, facilities may report releases under any of three distinct TRI chemical names:

| TRI Chemical Name           | CAS Number    | Meaning                                      |
|-----------------------------|---------------|----------------------------------------------|
| LEAD                        | 7439-92-1     | Elemental lead only                          |
| LEAD COMPOUNDS              | N420          | Lead as part of another chemical substance   |
| LEAD AND LEAD COMPOUNDS     | N420          | Combined reporting (either or both)          |

Per the EPA: *"Facilities report waste management of both lead and lead compounds to TRI. For TRI, 'lead' only includes elemental lead, while 'lead compounds' includes lead that is part of another chemical substance. Facilities may report lead compounds separately from lead..."*

This pattern recurs across many metal categories:
- **Manganese**: MANGANESE, MANGANESE COMPOUNDS, MANGANESE AND MANGANESE COMPOUNDS
- **Mercury**: MERCURY, MERCURY COMPOUNDS
- **Chromium**: CHROMIUM, CHROMIUM COMPOUNDS
- **Nickel**: NICKEL, NICKEL COMPOUNDS
- **Zinc**: ZINC, ZINC COMPOUNDS
- **Copper**: COPPER, COPPER COMPOUNDS
- **Cobalt**: COBALT, COBALT COMPOUNDS
- **Arsenic**: ARSENIC, ARSENIC COMPOUNDS
- **Cadmium**: CADMIUM, CADMIUM COMPOUNDS
- **Antimony**: ANTIMONY, ANTIMONY COMPOUNDS
- **Barium**: BARIUM, BARIUM COMPOUNDS

### The Impact on Citizens

A citizen searching for "lead" to understand releases in their community may:

1. **See incomplete results** — only facilities that reported under "LEAD" (elemental), missing those that reported under "LEAD COMPOUNDS" or the combined category
2. **Underestimate total releases** — if a facility releases both elemental lead and lead compounds, only partial data appears
3. **Miss the health picture** — the NLM [15th Report on Carcinogens](https://www.ncbi.nlm.nih.gov/books/NBK590906/) treats "Lead and Lead Compounds" as a single carcinogen class because health effects are comparable

This **defeats the purpose of right-to-know legislation** — citizens shouldn't need to understand EPA's internal reporting taxonomy to get accurate release totals.

---

## Decision

**Implement Chemical Families with Transparent OR Expansion**

When a user searches for a parent element (e.g., "lead"), the system will:

1. **Auto-expand** the search to include all related TRI reporting categories (LEAD, LEAD COMPOUNDS, LEAD AND LEAD COMPOUNDS)
2. **Aggregate releases** across all family members per facility per year
3. **Preserve audit trail** — show breakdown by chemical variant in facility detail view
4. **Disclose expansion** — display a banner explaining the search was expanded, with link to EPA/NLM documentation
5. **Offer opt-out** — provide "Search exact term only" option for researchers who need raw data

### Data Model

```sql
-- Chemical families table (parent → children mapping)
CREATE TABLE chemical_families (
    id SERIAL PRIMARY KEY,
    family_name VARCHAR(100) NOT NULL UNIQUE,  -- e.g., "LEAD"
    description TEXT,                           -- e.g., "Lead and all lead compounds"
    nlm_url VARCHAR(500),                       -- Link to NLM carcinogen report
    epa_url VARCHAR(500)                        -- Link to EPA TRI documentation
);

-- Join table linking chemicals to their family
CREATE TABLE chemical_family_members (
    chemical_id INTEGER NOT NULL REFERENCES chemicals(id),
    family_id INTEGER NOT NULL REFERENCES chemical_families(id),
    is_parent BOOLEAN DEFAULT FALSE,            -- TRUE for the canonical search term
    PRIMARY KEY (chemical_id, family_id)
);
```

### API Changes

**Request** (unchanged):
```
GET /api/v1/facilities?chemical=lead&...
```

**Response** (new `search_expansion` field):
```json
{
  "type": "FeatureCollection",
  "features": [...],
  "meta": {
    "total_count": 2085,
    "query": {
      "chemical": "LEAD",
      "search_expansion": {
        "expanded": true,
        "family_name": "LEAD",
        "searched_chemicals": [
          "LEAD",
          "LEAD COMPOUNDS", 
          "LEAD AND LEAD COMPOUNDS"
        ],
        "description": "Lead and all lead compounds",
        "nlm_url": "https://www.ncbi.nlm.nih.gov/books/NBK590906/",
        "epa_note": "Facilities may report lead and lead compounds separately or combined."
      }
    }
  }
}
```

### Facility Detail Breakdown

When viewing a facility's releases, show the breakdown by chemical variant:

```
Lead Releases (2024)
├── LEAD                         500 lbs (elemental)
├── LEAD COMPOUNDS             1,200 lbs
└── Total Lead Family          1,700 lbs
```

### UI Disclosure Banner

When search is expanded, display an informational banner:

```
ℹ️ Showing combined results for "Lead", "Lead Compounds", and "Lead and Lead Compounds"
   per EPA TRI reporting categories. Learn more ↗
   [Search exact term only]
```

---

## Curated Chemical Families

Initial release includes the following families (to be expanded based on user feedback):

| Family Name | Members | Rationale |
|-------------|---------|-----------|
| LEAD | LEAD, LEAD COMPOUNDS, LEAD AND LEAD COMPOUNDS | NLM carcinogen class |
| MERCURY | MERCURY, MERCURY COMPOUNDS | NLM carcinogen class |
| CHROMIUM | CHROMIUM, CHROMIUM COMPOUNDS | NLM carcinogen class (hexavalent) |
| NICKEL | NICKEL, NICKEL COMPOUNDS | NLM carcinogen class |
| ARSENIC | ARSENIC, ARSENIC COMPOUNDS | NLM carcinogen class |
| CADMIUM | CADMIUM, CADMIUM COMPOUNDS | NLM carcinogen class |
| MANGANESE | MANGANESE, MANGANESE COMPOUNDS, MANGANESE AND MANGANESE COMPOUNDS | EPA reporting pattern |
| ZINC | ZINC, ZINC COMPOUNDS, ZINC AND ZINC COMPOUNDS | EPA reporting pattern |
| COPPER | COPPER, COPPER COMPOUNDS | EPA reporting pattern |
| COBALT | COBALT, COBALT COMPOUNDS | EPA reporting pattern |
| ANTIMONY | ANTIMONY, ANTIMONY COMPOUNDS | EPA reporting pattern |
| BARIUM | BARIUM, BARIUM COMPOUNDS | EPA reporting pattern |
| BERYLLIUM | BERYLLIUM, BERYLLIUM COMPOUNDS | NLM carcinogen class |
| SELENIUM | SELENIUM, SELENIUM COMPOUNDS | EPA reporting pattern |
| SILVER | SILVER, SILVER COMPOUNDS | EPA reporting pattern |
| THALLIUM | THALLIUM, THALLIUM COMPOUNDS | EPA reporting pattern |
| VANADIUM | VANADIUM, VANADIUM COMPOUNDS | EPA reporting pattern |
| CYANIDE | CYANIDE, CYANIDE COMPOUNDS | EPA reporting pattern |

---

## Alternatives Considered

### Option B: Frontend-Only Expansion

- Autocomplete shows "LEAD (includes compounds)" as a selectable option
- Selection triggers 3 parallel API calls, merged client-side

**Rejected because:**
- Increases client complexity and network requests
- Aggregation logic duplicated in frontend
- Harder to maintain curated family list
- No single-request audit trail

### Option C: Disclosure Only (No Expansion)

- When user selects "LEAD", show warning about other reporting categories
- User must manually search each term

**Rejected because:**
- Puts burden on citizens who shouldn't need EPA taxonomy knowledge
- Defeats right-to-know purpose of the application
- Most users won't understand or act on the warning

### Option D: Always Combine All Variants

- Merge LEAD, LEAD COMPOUNDS, etc. into a single "LEAD" chemical in the database

**Rejected because:**
- Destroys audit trail — can't verify data against EPA source
- Prevents researchers from accessing raw reporting categories
- Inconsistent with EPA's own data model

---

## Consequences

### Positive

1. **Citizens get complete picture** — searching "lead" shows all lead releases, not just elemental
2. **Transparency preserved** — breakdown shown in detail view, opt-out available
3. **Educational** — links to NLM/EPA help users understand reporting categories
4. **Extensible** — new families can be added via database without code changes
5. **Audit-friendly** — raw data preserved, expansion logged in meta

### Negative

1. **Larger result sets** — may increase initial load for popular chemicals
2. **Maintenance burden** — must keep family definitions current with EPA TRI list
3. **Slight complexity** — API response includes expansion metadata

### Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Family definitions become stale | Annual review against EPA TRI chemical list updates |
| User confusion about expanded results | Clear disclosure banner with "learn more" link |
| Researchers need exact matches | "Search exact term only" option in UI |

---

## Implementation Plan

1. **Database migration** — Add `chemical_families` and `chemical_family_members` tables
2. **Seed data** — Populate with curated family definitions
3. **Chemical service** — Update `search_chemicals` to return family info
4. **Facility service** — Update search to expand family chemicals, aggregate releases
5. **API schema** — Add `search_expansion` to response meta
6. **Frontend banner** — Display disclosure when `search_expansion.expanded = true`
7. **Detail view** — Show breakdown by chemical variant in facility releases
8. **Documentation** — Update API contract and user guide

---

## Implementation Status

**Completed:** 2026-07-31

| Step | Status | Notes |
|------|--------|-------|
| 1. Database migration | ✅ | `chemical_families` and `chemical_family_members` tables created via Alembic |
| 2. Seed data | ✅ | 18 families, 26 member chemicals seeded via `seed_chemical_families.py` |
| 3. Chemical service | ✅ | `get_chemical_family()` returns family info for parent chemicals |
| 4. Facility service | ✅ | `get_facilities_near()` and `get_all_facilities_browse()` expand family chemicals; `exact_match` parameter controls expansion |
| 5. API schema | ✅ | `search_expansion` field in response meta; `exact_match` query parameter |
| 6. Frontend banner | ✅ | `ChemicalFamilyBanner.tsx` displays disclosure with "Search exact term only" button |
| 7. Detail view | ⬜ | Deferred — breakdown by chemical variant in facility detail |
| 8. Documentation | ✅ | ADR-007 accepted; API contract updated |

### Bug Fixes (7.BUG.9–7.BUG.15)

| Bug | Issue | Fix |
|-----|-------|-----|
| 7.BUG.9 | Seed script import error | Changed `async_session_factory` → `AsyncSessionLocal` |
| 7.BUG.10 | Exact match not narrowing | Used `func.upper(Chemical.name) == chemical.upper()` when `exact_match=true` |
| 7.BUG.11 | SearchPanel scroll broken | Wrapped form in scrollable container with `minHeight: 0` |
| 7.BUG.12 | Banner missing padding | Added padding wrapper around `ChemicalFamilyBanner` |
| 7.BUG.13 | Sidebar resize lag/map interference | Direct DOM manipulation + capture-phase events |
| 7.BUG.14 | PostCSS ESM error | Changed to CommonJS syntax |
| 7.BUG.15 | MERCURY family not expanding | Added whitespace normalization to seed script; fixed MERCURY/CHROMIUM/ZINC/etc. families with correct TRI chemical names (35 members total) |

---

## References

1. EPA TRI Chemical List: https://www.epa.gov/toxics-release-inventory-tri-program/tri-listed-chemicals
2. NLM 15th Report on Carcinogens — Lead and Lead Compounds: https://www.ncbi.nlm.nih.gov/books/NBK590906/
3. EPA TRI Reporting FAQ: https://www.epa.gov/toxics-release-inventory-tri-program/tri-frequently-asked-questions
4. ATSDR ToxFAQs — Lead: https://www.atsdr.cdc.gov/toxfaqs/tfacts13.pdf
