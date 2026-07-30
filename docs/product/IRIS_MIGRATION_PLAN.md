# Chemical Health Resources Migration Plan
## ATSDR ToxFAQs/ToxProfiles + EPA IRIS ChemicalLanding

**Status:** Draft · **Date:** 2026-07-29 (updated)  
**Author:** Research spike  
**Source data:**
- `scripts/atsdr_toxid_map.csv` (205 records, scraped 2026-07-29)
- `scripts/iris_substance_nmbr_map.csv` (572 records, scraped 2026-07-27)

---

## 1. Background

TOXMAP links chemicals to external health resources via opaque URL parameters
that cannot be derived from CAS numbers or chemical names alone. Both ATSDR
and EPA IRIS use non-sequential, non-derivable identifiers.

### 1.1 ATSDR ToxFAQs and ToxProfiles

ATSDR provides two related resources:
- **ToxFAQs:** Consumer-friendly 2-page summaries (PDF format available)
- **ToxProfiles:** Comprehensive toxicological profiles (detailed health data)

Both use a shared `toxid`/`tid` parameter as the cross-reference key:

```
# ToxFAQs URL pattern:
https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsDetails.aspx?faqid=4&toxid=1    ← Acetone

# ToxProfiles URL pattern:
https://wwwn.cdc.gov/TSP/ToxProfiles/ToxProfiles.aspx?id=5&tid=1        ← Acetone
```

The `toxid` (ToxFAQs) and `tid` (ToxProfiles) parameters are identical for the
same chemical. The `faqid` and `id` parameters differ between systems.

### 1.2 EPA IRIS (Integrated Risk Information System)

EPA IRIS is a larger, more authoritative dataset covering 572 substances with
quantitative toxicological assessments (RfD, RfC, slope factors). IRIS URLs
use an opaque `substance_nmbr` parameter:

```
https://iris.epa.gov/ChemicalLanding/&substance_nmbr=277         ← Lead (inorganic)
```

Neither ATSDR nor IRIS IDs are derivable from CAS numbers or chemical names —
both must be scraped from their respective A-Z indexes.

---

## 2. ATSDR Mapping Methodology

### 2.1 Data Extraction Process

The ATSDR mapping required two different extraction approaches:

**ToxProfiles (static HTML):** The A-Z Index page at
`https://www.atsdr.cdc.gov/toxicological-profiles/glossary/index.html` is
server-rendered HTML. Standard regex extraction works:

```
Pattern: ToxProfiles.aspx?id=(\d+)&tid=(\d+)">([^<]+)
```

**ToxFAQs (JavaScript-rendered):** The page at
`https://wwwn.cdc.gov/TSP/ToxFAQs/ToxFAQsLanding.aspx` uses JavaScript to load
content dynamically when clicking A-Z letter buttons. Static HTML scraping
captures only Letter A. Playwright automation was required to iterate through
all 26 letters and extract chemical links.

### 2.2 ATSDR Data Quality

| Metric | Value |
|--------|-------|
| Total ToxProfiles entries | 187 |
| Total ToxFAQs entries | 202 |
| Combined unique chemicals | 205 |
| With both ToxProfiles + ToxFAQs | 187 |
| ToxFAQs only (no ToxProfile) | 18 |

The `toxid` parameter range is 1–293 (non-contiguous).

### 2.3 ToxFAQs-Only Chemicals

These 18 chemicals have ToxFAQs pages but no corresponding ToxProfile:

| Chemical | toxid | faqid |
|----------|-------|-------|
| Aniline | 79 | 449 |
| Blister Agents (Nitrogen Mustards) | 189 | 921 |
| Blister Agents (Lewisite) | 190 | 923 |
| Blister Agents (Sulfur Mustard) | 191 | 926 |
| Calcium Hypochlorite/Sodium Hypochlorite | 192 | 928 |
| Chlordecone | 118 | 642 |
| Crotonaldehyde | 197 | 948 |
| Diborane | 202 | 965 |
| Hydrogen Chloride | 147 | 759 |
| Hydrogen Peroxide | 55 | 305 |
| Methyl Isocyanate | 116 | 629 |
| Nerve Agents (GA, GB, GD, VX) | 93 | 524 |
| Nitrogen Oxides | 69 | 396 |
| Phosgene | 182 | 1479 |
| Phosgene Oxime | 213 | 1011 |
| Phosphine | 214 | 1014 |
| Selenium Hexafluoride | 215 | 1016 |
| Sodium Hydroxide | 45 | 248 |

### 2.4 Cross-Reference Key

The `toxid` parameter is the canonical cross-reference key:
- In ToxFAQs URLs: `?faqid=XXX&toxid=YYY` — use `toxid`
- In ToxProfiles URLs: `?id=XXX&tid=YYY` — use `tid` (same value as `toxid`)

The scraper maps chemicals by `toxid` and merges both URLs where available.

---

## 3. IRIS Mapping Methodology

The scrape of `https://iris.epa.gov/AtoZ/alpha/` (server-rendered HTML table)
extracted all 572 IRIS entries. Full mapping is at
[`scripts/iris_substance_nmbr_map.csv`](../../scripts/iris_substance_nmbr_map.csv).

### 3.1 Primary match key: CAS Registry Number

| TRI field | IRIS field | Notes |
|-----------|-----------|-------|
| `chemicals.cas_number` | `casrn` column in CSV | Exact string match after normalizing whitespace |

CAS numbers are the canonical cross-reference. The TRI database and IRIS both
use the CAS format `NNNNNNN-NN-N`.

PubChem also accepts CAS numbers directly in compound URLs, so the
`pubchem_url` field can be stored as a stable CAS-based URL with no lookup needed:

```
https://pubchem.ncbi.nlm.nih.gov/compound/7439-92-1  ← always redirects to the canonical CID page
```

Existing `pubchem_url` values that use numeric CIDs (e.g. `/compound/241` for
benzene) should be normalised to the CAS form (`/compound/71-43-2`) during
migration — this makes them human-readable and independent of PubChem internal
ID changes.

### 3.2 Resolving TRI compound categories (N-codes) via PubChem Synonyms

TRI compound categories (e.g. "LEAD COMPOUNDS", internal ID N420) carry no
single CAS number.  The resolution chain is:

```
TRI N-code  →  PubChem Synonyms API  →  canonical CAS  →  IRIS CSV lookup
    N420              CID 5352425            7439-92-1           nmbr=277
```

**PubChem Synonyms API:**
```
GET https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{n_code}/synonyms/JSON
```

The first synonym entry matching `\d{1,7}-\d{2}-\d` is the canonical CAS.

The scraper (`scripts/scrape_iris_substance_nmbr.py`) implements this with
`pubchem_resolve_cas(identifier, session)`.

**Coverage:** PubChem indexes _some_ N-codes as synonyms (N420 for Lead is
confirmed), but not all. Tested results:

| N-code | TRI Category | PubChem resolves? | CAS | IRIS nmbr |
|--------|-------------|-------------------|-----|-----------|
| N420 | Lead Compounds | ✅ | 7439-92-1 | 277 |
| N100 | Copper Compounds | ❌ Not in PubChem | 7440-50-8 | 368 |

For N-codes not indexed by PubChem, use the **elemental/representative CAS**
as a fallback: the IRIS typically has an entry for the element (e.g., "Copper"
at CAS 7440-50-8) that covers compound categories. A small hardcoded override
table is needed only for categories where PubChem resolution fails.

### 3.3 Seed chemical mapping (verified)

All 6 test seed chemicals have confirmed IRIS entries:

| TRI Name | CAS | IRIS `substance_nmbr` | Resolution path |
|---------|-----|----------------------|-----------------|
| LEAD COMPOUNDS (N420) | NULL | **277** | N-code → PubChem → CAS 7439-92-1 |
| COPPER | 7440-50-8 | **368** | direct CAS |
| STYRENE | 100-42-5 | **104** | direct CAS |
| CHLORINE | 7782-50-5 | **405** | direct CAS |
| BENZENE | 71-43-2 | **276** | direct CAS |
| AMMONIA | 7664-41-7 | **422** | direct CAS |

### 3.4 Edge cases

| Situation | Count | Resolution |
|-----------|-------|------------|
| TRI compound category, N-code indexed by PubChem | varies | N-code → PubChem → CAS → IRIS |
| TRI compound category, N-code NOT in PubChem | varies | Hardcoded elemental CAS override |
| IRIS entry with "Various" CASRNs (mixtures) | 8 | No automatic match; `iris_url = NULL` |
| IRIS entry with "None" CASRN | 4 | No automatic match; `iris_url = NULL` |
| TRI chemical not in IRIS at all | majority | `iris_url = NULL` (IRIS covers ~560 of ~800+ TRI chemicals) |

---

## 4. IRIS Data Quality Notes

| Metric | Value |
|--------|-------|
| Total IRIS substances | 572 |
| `substance_nmbr` range | 2 – 1039 (non-contiguous; ~467 unused IDs) |
| Substances with a unique CASRN | 560 |
| Substances with "Various" CASRN | 8 |
| Substances with no CASRN | 4 |
| TRI chemicals covered by IRIS (estimate) | ~320 of ~800+ |

The `substance_nmbr` sequence has large gaps (e.g., 639 → 642) indicating
deleted or merged entries over time. The scraped IDs are the live canonical set.

---

## 5. Required Codebase Changes

### 5.1 Database — new column

Add `iris_url TEXT` to the `chemicals` table via Alembic:

```python
# New Alembic migration
op.add_column("chemicals", sa.Column("iris_url", sa.Text(), nullable=True))
```

No existing data is affected; column defaults to `NULL`.

> **Blocked:** A new column requires a corresponding field in
> `TOXMAP_API_CONTRACT.md` **before** the column is added. This requires
> human approval per AGENTS.md §3.

### 5.2 Ingestion — populate iris_url and normalise pubchem_url

**IRIS lookup table** — generated from the CSV via a helper in `tri_ingest.py`:

```python
# Loads scripts/iris_substance_nmbr_map.csv at startup
IRIS_BY_CAS: dict[str, str] = {row["casrn"]: row["iris_url"] for row in iris_csv}
```

**Resolution logic during ingestion:**

```python
def build_iris_url(cas: str | None, tri_ncode: str | None) -> str | None:
    # 1. Direct CAS lookup (covers ~560 IRIS substances)
    if cas and cas in IRIS_BY_CAS:
        return IRIS_BY_CAS[cas]
    # 2. N-code via PubChem Synonyms (covers N420/Lead and others indexed by PubChem)
    if tri_ncode:
        resolved_cas, _ = pubchem_resolve_cas(tri_ncode, session)
        if resolved_cas and resolved_cas in IRIS_BY_CAS:
            return IRIS_BY_CAS[resolved_cas]
    # 3. Fallback override table for N-codes PubChem doesn't index
    if tri_ncode and tri_ncode in NCODE_ELEMENTAL_CAS:
        elemental_cas = NCODE_ELEMENTAL_CAS[tri_ncode]
        return IRIS_BY_CAS.get(elemental_cas)
    return None

# Minimal override table — only needed for N-codes not in PubChem
NCODE_ELEMENTAL_CAS: dict[str, str] = {
    "N100": "7440-50-8",   # Copper Compounds → elemental copper
    "N010": "7440-38-2",   # Arsenic Compounds → inorganic arsenic
    # ... add others as discovered during full TRI ingest
}
```

**pubchem_url normalisation** — change CID-based URLs to CAS-based URLs:

```python
def normalise_pubchem_url(cas: str | None, existing_url: str | None) -> str | None:
    # CAS-based URLs are stable, human-readable, and PubChem redirects them correctly.
    # e.g. /compound/241 (benzene CID) → /compound/71-43-2 (benzene CAS)
    if cas:
        return f"https://pubchem.ncbi.nlm.nih.gov/compound/{cas}"
    return existing_url  # keep CID-based URL for compound categories until resolved
```

### 5.3 Backend schemas

Add `iris_url` to `ChemicalSummary` and `ChemicalSearch` in
`backend/app/schemas/chemical.py`:

```python
class ChemicalSummary(BaseModel):
    ...
    atsdr_url: str | None = None   # retained for backward compatibility
    iris_url:  str | None = None   # new
    pubchem_url: str | None = None
```

### 5.4 API contract update (**human approval required**)

`TOXMAP_API_CONTRACT.md` must be updated to add `iris_url` to the
`GET /api/v1/chemicals` and `GET /api/v1/chemicals/{id}` response shapes.
This is a **protected file** (AGENTS.md §4) — agent cannot modify it.

### 5.5 Frontend — add IRIS link

In `SearchPanel` and `FacilityDrawer`, render an IRIS link alongside or in
place of the ATSDR link wherever `chemical.iris_url` is non-null.

Suggested label: **"EPA IRIS"** (consistent with EPA branding).

```tsx
{chemical.iris_url && (
  <a
    href={chemical.iris_url}
    target="_blank"
    rel="noopener noreferrer"
    data-testid="iris-link"
  >
    EPA IRIS
  </a>
)}
```

---

## 6. Decision Required: ATSDR + IRIS Integration Strategy

Now that we have complete ATSDR ToxFAQs/ToxProfiles mapping (205 chemicals) alongside
the IRIS mapping (572 chemicals), the question is how to present these links to users.

### 6.1 Coverage Analysis

| Resource | Total Chemicals | TRI Coverage (est.) | Unique Content |
|----------|----------------|---------------------|----------------|
| ATSDR ToxFAQs | 202 | ~150 | Consumer-friendly 2-page summaries |
| ATSDR ToxProfiles | 187 | ~150 | Detailed toxicological profiles |
| EPA IRIS | 572 | ~320 | Quantitative risk assessments (RfD, RfC) |

### 6.2 Options

| Option | Pros | Cons |
|--------|------|------|
| **A — Show all three:** ToxFAQs + ToxProfiles + IRIS | Maximum information; different audiences | Cluttered UI; may overwhelm users |
| **B — ATSDR unified + IRIS:** Single "ATSDR" link (prefer ToxProfiles) + IRIS | Cleaner; two link categories | Loses ToxFAQs consumer format |
| **C — Smart fallback:** IRIS primary, ATSDR fallback for non-IRIS chemicals | IRIS is authoritative; ATSDR fills gaps | IRIS UI is less consumer-friendly |

**Recommendation:** Option B (ATSDR unified + IRIS). Show:
- **"ATSDR"** link → ToxProfiles URL where available, fallback to ToxFAQs
- **"EPA IRIS"** link → IRIS URL where available

This gives users access to both consumer-friendly ATSDR content and authoritative
IRIS risk assessments without overwhelming the UI.

---

## 7. Rollout Order

1. **Human:** Approve API contract addition of `iris_url` and `atsdr_toxprofiles_url` fields
2. **Human:** Approve ATSDR mapping data (`scripts/atsdr_toxid_map.csv`)
3. **Human:** Approve IRIS mapping data (`scripts/iris_substance_nmbr_map.csv`)
4. **DE:** Alembic migration + lookup table generation
5. **BE:** Add URL fields to ORM model, schema, and service layer
6. **DE:** Update ingestion to populate URLs during TRI ingest
7. **FE:** Render ATSDR and IRIS links in SearchPanel and FacilityDrawer
8. **QA:** Add Gherkin scenarios for external link validation

---

## 8. Mapping Artifacts

### 8.1 ATSDR ToxFAQs/ToxProfiles Mapping

The complete `toxid` → (name, toxprofiles_url, toxfaqs_url) table is persisted at:

```
scripts/atsdr_toxid_map.csv
scripts/atsdr_toxfaqs_raw.csv   # Raw ToxFAQs data (Playwright extraction)
```

Re-generation command:

```bash
# Requires saved HTML files in docs/product/
python scripts/scrape_atsdr_toxfaqs.py --output scripts/atsdr_toxid_map.csv
```

**Note:** ToxFAQs extraction requires Playwright automation since the page uses
JavaScript to load content dynamically. The `atsdr_toxfaqs_raw.csv` file was
generated via browser automation clicking through all A-Z letters.

### 8.2 EPA IRIS Mapping

The complete `substance_nmbr` → (name, CASRN, iris_url) table is persisted at:

```
scripts/iris_substance_nmbr_map.csv
```

Re-scrape command (run periodically as IRIS adds new assessments):

```bash
python scripts/scrape_iris_substance_nmbr.py --output scripts/iris_substance_nmbr_map.csv
```

The scraper is fully idempotent and takes ~2 seconds against the live IRIS site.
