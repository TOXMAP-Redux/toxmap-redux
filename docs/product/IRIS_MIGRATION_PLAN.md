# IRIS Migration Plan — ATSDR ToxFAQ → EPA IRIS ChemicalLanding

**Status:** Draft · **Date:** 2026-07-27  
**Author:** Research spike  
**Source data:** `scripts/iris_substance_nmbr_map.csv` (572 records, scraped 2026-07-27)

---

## 1. Background

The current codebase links each chemical to its ATSDR ToxFAQ page via an opaque
`toxid` parameter:

```
https://wwwn.cdc.gov/TSP/substances/ToxSubstance.aspx?toxid=22   ← Lead Compounds
```

EPA's IRIS (Integrated Risk Information System) is a larger, more authoritative
dataset covering 572 substances with quantitative toxicological assessments (RfD,
RfC, slope factors). IRIS ChemicalLanding URLs use a similarly opaque
`substance_nmbr` parameter:

```
https://iris.epa.gov/ChemicalLanding/&substance_nmbr=277         ← Lead (inorganic)
```

Neither ID is derivable from a CAS number or chemical name alone — both must be
scraped from their respective A-Z indexes.

---

## 2. Mapping Methodology

The scrape of `https://iris.epa.gov/AtoZ/alpha/` (server-rendered HTML table)
extracted all 572 IRIS entries. Full mapping is at
[`scripts/iris_substance_nmbr_map.csv`](../../scripts/iris_substance_nmbr_map.csv).

### 2.1 Primary match key: CAS Registry Number

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

### 2.2 Resolving TRI compound categories (N-codes) via PubChem Synonyms

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

### 2.3 Seed chemical mapping (verified)

All 6 test seed chemicals have confirmed IRIS entries:

| TRI Name | CAS | IRIS `substance_nmbr` | Resolution path |
|---------|-----|----------------------|-----------------|
| LEAD COMPOUNDS (N420) | NULL | **277** | N-code → PubChem → CAS 7439-92-1 |
| COPPER | 7440-50-8 | **368** | direct CAS |
| STYRENE | 100-42-5 | **104** | direct CAS |
| CHLORINE | 7782-50-5 | **405** | direct CAS |
| BENZENE | 71-43-2 | **276** | direct CAS |
| AMMONIA | 7664-41-7 | **422** | direct CAS |

### 2.4 Edge cases

| Situation | Count | Resolution |
|-----------|-------|------------|
| TRI compound category, N-code indexed by PubChem | varies | N-code → PubChem → CAS → IRIS |
| TRI compound category, N-code NOT in PubChem | varies | Hardcoded elemental CAS override |
| IRIS entry with "Various" CASRNs (mixtures) | 8 | No automatic match; `iris_url = NULL` |
| IRIS entry with "None" CASRN | 4 | No automatic match; `iris_url = NULL` |
| TRI chemical not in IRIS at all | majority | `iris_url = NULL` (IRIS covers ~560 of ~800+ TRI chemicals) |

---

## 3. IRIS Data Quality Notes

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

## 4. Required Codebase Changes

### 4.1 Database — new column

Add `iris_url TEXT` to the `chemicals` table via Alembic:

```python
# New Alembic migration
op.add_column("chemicals", sa.Column("iris_url", sa.Text(), nullable=True))
```

No existing data is affected; column defaults to `NULL`.

> **Blocked:** A new column requires a corresponding field in
> `TOXMAP_API_CONTRACT.md` **before** the column is added. This requires
> human approval per AGENTS.md §3.

### 4.2 Ingestion — populate iris_url and normalise pubchem_url

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

### 4.3 Backend schemas

Add `iris_url` to `ChemicalSummary` and `ChemicalSearch` in
`backend/app/schemas/chemical.py`:

```python
class ChemicalSummary(BaseModel):
    ...
    atsdr_url: str | None = None   # retained for backward compatibility
    iris_url:  str | None = None   # new
    pubchem_url: str | None = None
```

### 4.4 API contract update (**human approval required**)

`TOXMAP_API_CONTRACT.md` must be updated to add `iris_url` to the
`GET /api/v1/chemicals` and `GET /api/v1/chemicals/{id}` response shapes.
This is a **protected file** (AGENTS.md §4) — agent cannot modify it.

### 4.5 Frontend — add IRIS link

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

## 5. Decision Required: Replace or Supplement ATSDR?

Two options:

| Option | Pros | Cons |
|--------|------|------|
| **A — Supplement:** keep `atsdr_url`, add `iris_url` | No data loss; ATSDR has different chemical coverage | Two external link columns; wider API surface |
| **B — Replace:** rename `atsdr_url` → `iris_url`; drop ATSDR | Simpler schema | ATSDR covers ~300+ chemicals not in IRIS (e.g., many CERCLA priority list substances); those chemicals lose their health link |

**Recommendation:** Option A (supplement). IRIS does not cover all TRI chemicals,
so removing ATSDR links would leave ~480+ chemicals with no health resource link.
Show IRIS link where available; fall back to ATSDR.

---

## 6. Rollout Order

1. **Human:** Approve API contract addition of `iris_url` field
2. **Human:** Approve new `iris_map.py` lookup table data (derived from scrape)
3. **DE:** Alembic migration + `iris_map.py` generation script
4. **BE:** Add `iris_url` to ORM model, schema, and service layer
5. **DE:** Update ingestion to populate `iris_url` during TRI ingest
6. **FE:** Render IRIS link in SearchPanel and FacilityDrawer
7. **QA:** Add Gherkin scenario for T-08 variant: IRIS link opens in new tab

---

## 7. Mapping Artifact

The complete `substance_nmbr` → (name, CASRN, iris_url) table is persisted at:

```
scripts/iris_substance_nmbr_map.csv
```

Re-scrape command (run periodically as IRIS adds new assessments):

```bash
python scripts/scrape_iris_substance_nmbr.py --output scripts/iris_substance_nmbr_map.csv
```

The scraper is fully idempotent and takes ~2 seconds against the live IRIS site.
