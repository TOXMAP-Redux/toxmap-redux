# TOXMAP `data-testid` Registry

**Last updated:** 2026-08-08  
**Purpose:** Canonical list of every `data-testid` attribute used in Playwright E2E tests and React components. Frontend developers MUST use these exact strings. QA engineers MUST use these exact strings in selectors.

> **Rule:** If a `data-testid` is not in this registry, it does not exist. Add it here before using it in any test or component.

---

## Map Container

| `data-testid`   | Component              | Used in Gherkin Step       |
|-----------------|------------------------|----------------------------|
| `map-container` | `<Map>` root `<div>`   | `"I am on the map page"`   |
| `map-canvas`    | MapLibre GL `<canvas>` | zoom/coordinate assertions |

---

## Sidebar & Panels

| `data-testid`          | Component                | Used in Gherkin Step                                 |
|------------------------|--------------------------|------------------------------------------------------|
| `sidebar-panel`        | `<Sidebar>` root element | UX Invariant 1 — single panel check                  |
| `map-contents-panel`   | `<MapContentsPanel>`     | `"Map Contents panel is NOT visible"`                |
| `search-panel`         | `<SearchPanel>`          | `"Search Chemical Releases by Location"` label check |
| `sidebar-collapse-btn` | Sidebar chevron button   | collapse/expand                                      |

> **Note:** To assert the active panel, combine `sidebar-panel` with the **separate** `data-active` attribute:  
> `[data-testid="sidebar-panel"][data-active="true"]`.  
> `data-active` is **not** part of the `data-testid` value — it is a distinct HTML attribute added to the same element.

---

## Search Panel Inputs

| `data-testid`                  | Component                                  | Used in Gherkin Step                        |
|--------------------------------|--------------------------------------------|---------------------------------------------|
| `location-input`               | Location text field                        | `'I type "{text}" into the location field'` |
| `chemical-input`               | Chemical text field                        | `'I type "{text}" into the chemical field'` |
| `chemical-autocomplete-option` | Each autocomplete dropdown item            | `"Wait for autocomplete"` + click           |
| `year-select`                  | Year `<select>` dropdown                   | `'I select year "{year}"'`                  |
| `state-select`                 | State `<select>` dropdown (labeled "Filter to state (optional)") | UX Invariant 3 — state filter tests         |
| `search-submit-btn`            | Search `<button>`                          | `"I click Search"`                          |
| `dataset-radio-both`           | Both (TRI + Superfund) radio button        | Default selection; combined search (Fig 2015-4) |
| `dataset-radio-tri`            | TRI radio button                           | T-04 dataset switch                         |
| `dataset-radio-superfund`      | Superfund radio button                     | T-02, T-04                                  |
| `facility-search-input`        | Facility ID/name search text field (ADR-010) | `'I type "{text}" into the facility search field'` |
| `facility-search-dropdown`     | Facility autocomplete dropdown container   | `"Wait for facility autocomplete"`          |
| `facility-search-option`       | Each facility autocomplete dropdown item   | Facility search result click                |
| `facility-match-badge`         | ID/Name match type badge on search result  | `"match type badge shows 'ID Match'"`       |
| `site-type-badge`              | TRI/Superfund type badge on search result (ADR-010) | `"site type badge shows 'TRI' or 'Superfund'"` |

---

## Results Table

| `data-testid`         | Component              | Used in Gherkin Step              |
|-----------------------|------------------------|-----------------------------------|
| `results-table`       | `<ResultsTable>` root  | UX Invariant 2 — empty row check  |
| `results-row`         | Each `<tr>` in results | `"every row has a facility name"` |
| `results-row-name`    | Facility name `<td>`   | facility name assertions          |
| `results-row-release` | Release amount `<td>` (TRI mode)    | comma-format assertions           |
| `results-row-hrs`     | HRS score `<td>` (Superfund mode)   | Superfund results — T-04 *(col replaces release when dataset=superfund)* |

---

## Facility Detail

| `data-testid`             | Component                    | Used in Gherkin Step                  |
|---------------------------|------------------------------|---------------------------------------|
| `facility-detail-panel`   | Facility drawer root         | `"facility detail panel opens"`       |
| `popup-close-bottom`      | Bottom close link/button     | UX Invariant 9 — close link at bottom |
| `facility-release-amount` | Release quantity display     | UX Invariant 8 — comma formatting     |
| `facility-chart-tab-1`    | Top chemicals tab button     | T-01, T-03 chart tab                  |
| `facility-chart-tab-2`    | Release by medium tab button | T-03 medium distribution              |
| `facility-chart-tab-3`    | 15-year trend tab button     | trend chart assertions                |
| `facility-tri-id-link`    | TRI ID `<a>` link to EPA EnviroFacts (ADR-010) | `"TRI ID link is visible"` |
| `facility-epa-report-link` | EPA TRI Facility Report `<a>` (ADR-010) | `"EPA TRI Facility Report link is visible"` |
| `atsdr-link`              | ATSDR ToxFAQ `<a>`           | T-08 external link test               |
| `pubchem-link`            | PubChem `<a>`                | external link assertions              |
| `medium-discrepancy-section` | By Medium tab aggregate discrepancy box (7.BUG.38) | `"the medium discrepancy section is visible"` |
| `medium-epa-total`        | EPA-reported total value (7.BUG.38) | `"the EPA-reported total is displayed"` |
| `medium-discrepancy-value`   | Calculated aggregate discrepancy ±X lbs (7.BUG.38) | discrepancy percentage display |
| `medium-discrepancy-footnote`| Explanatory footnote with Trend tab CTA (7.BUG.38) | `"the discrepancy footnote explains TRI data quality"` |
| `trend-tooltip`           | Custom tooltip in 15-Year Trend chart (7.BUG.38) | per-year discrepancy hover details |
| `trend-tooltip-discrepancy`  | Discrepancy line within Trend tooltip (7.BUG.38) | per-year discrepancy value display |
| `trend-discrepancy-legend`   | Legend explaining ≥5% discrepancy ring indicator (7.BUG.38) | discrepancy legend assertions |

---

## Superfund

| `data-testid`                 | Component                  | Used in Gherkin Step                             |
|-------------------------------|----------------------------|--------------------------------------------------|
| `superfund-detail-panel`      | Superfund drawer root      | T-04                                             |
| `superfund-contaminants-list` | Contaminant `<ul>`         | `"contaminants list containing STYRENE"`         |
| `superfund-contaminant-link`  | ATSDR `<a>` per contaminant (rendered when `atsdr_url` non-null) | T-04 ATSDR link per contaminant |
| `superfund-epa-progress-link` | EPA progress profile `<a>` | T-04 — `"link to the EPA site progress profile"` |
| `superfund-hrs-score`         | HRS score badge            | HRS score assertion                              |
| `superfund-legend`            | Superfund legend container (UCD-17 3-way status) | `"the Superfund legend shows..."` |
| `superfund-legend-npl-final`  | NPL Final legend entry (square icon) | UCD-17 — `"NPL (Final)" entry with a square icon` |
| `superfund-legend-proposed`   | Proposed legend entry (diamond icon) | UCD-17 — `"Proposed" entry with a diamond icon` |
| `superfund-legend-deleted`    | Deleted legend entry (X-square icon) | UCD-17 — `"Deleted" entry with an X-square icon` |
| `superfund-icon-square`       | Square SVG icon (NPL Final) | UCD-17 shape assertion |
| `superfund-icon-diamond`      | Diamond SVG icon (Proposed) | UCD-17 shape assertion |
| `superfund-icon-xsquare`      | X-Square SVG icon (Deleted) | UCD-17 shape assertion |

---

## Export (Epic 6.EXPORT)

| `data-testid`          | Component                          | Used in Gherkin Step                               |
|------------------------|------------------------------------|----------------------------------------------------|
| `export-csv-btn`       | "Download CSV" button in ResultsTable header | `"I click the Download CSV button"`          |
| `map-screenshot-btn`   | Screenshot button in map controls  | `"I click the Save Map Image button"`              |
| `facility-export-btn`  | Export button in FacilityDrawer    | `"I click the facility export button"`             |
| `superfund-export-btn` | Export button in SuperfundDrawer   | `"I click the Superfund export button"`            |

> **Note:** Export buttons are disabled when no data is available. Use `aria-disabled="true"` for accessibility assertions.

| `data-testid`                 | Component                     | Used in Gherkin Step                              |
|-------------------------------|-------------------------------|---------------------------------------------------|
| `census-health-panel`         | `<CensusHealthPanel>` root    | T-05, T-06, T-09                                  |
| `demographic-legend`          | `<InlineLegend>` root         | UX Invariant 5 — inline values                    |
| `demographic-legend-entry`    | Each legend color+range row   | `"each legend entry has a visible numeric value"` |
| `clear-layer-btn`             | "Clear layer" `<button>`      | T-06 — `"I click 'Clear layer'"`                  |
| `cooccurrence-disclaimer`     | Disclaimer `<p>` or `<aside>` | UX Invariant 10 — mortality tab only              |
| `demo-tab-population`         | Population tab button         | `"I select 'Population'"`                         |
| `demo-tab-income`             | Income tab button             | T-06                                              |
| `demo-tab-mortality`          | Mortality tab button          | T-09                                              |
| `demo-sublayer-pct-under-18`  | % Under 18 radio/button       | T-05                                              |
| `demo-sublayer-cancer-female` | Cancer Mortality / Female     | T-09                                              |

---

## Layer Toggles (Map Contents Panel)

| `data-testid`             | Component                                          | Used in Gherkin Step                                 |
|---------------------------|----------------------------------------------------|------------------------------------------------------|
| `layer-toggle-tri-latest` | Latest TRI year toggle                             | UX Invariant 7 — must include text `"(latest year)"` |
| `layer-toggle-tri-{year}` | Per-year TRI toggle (e.g. `layer-toggle-tri-2024`) | year filter assertions                               |
| `layer-toggle-superfund`  | Superfund layer checkbox                           | T-04 Superfund show/hide                             |
| `layer-toggle-nuclear`    | Nuclear plants checkbox                            | nuclear layer assertions                             |

---

## Release by Medium Chart

> Used in T-03 ("Land medium as the largest bar") and Invariant 8 (comma formatting on release amounts).  
> Each bar's `data-medium` attribute holds the release category; the `data-release-lbs` attribute holds the numeric value for assertion.

| `data-testid`                                  | Component                             | Used in Gherkin Step                         |
|------------------------------------------------|---------------------------------------|----------------------------------------------|
| `release-by-medium-chart`                      | `<ReleaseByMediumChart>` container    | T-03 — chart presence check                  |
| `release-chart-bar`                            | Individual `<Bar>` element (Recharts) | T-03 — `data-medium="land"` is tallest bar   |
| `release-chart-bar[data-medium="air"]`         | Air release bar                       | T-03 — assert bar absent or has value 0      |
| `release-chart-bar[data-medium="water"]`       | Water release bar                     | medium breakdown assertions                  |
| `release-chart-bar[data-medium="land"]`        | Land release bar                      | T-03 — assert value `8,205`; must be tallest |
| `release-chart-bar[data-medium="underground"]` | Underground release bar               | medium breakdown assertions                  |

> **Note:** `data-medium` and `data-release-lbs` are **separate** attributes on the same element as `data-testid="release-chart-bar"`.  
> Example selector: `[data-testid="release-chart-bar"][data-medium="land"]`  
> Largest-bar assertion: compare `data-release-lbs` values across all `release-chart-bar` elements.

---

## Onboarding & Global

| `data-testid`           | Component                                                                   | Used in Gherkin Step                            |
|-------------------------|-----------------------------------------------------------------------------|-------------------------------------------------|
| `interpretation-banner` | Release quantity disclaimer banner                                          | first-load check                                |
| `onboarding-tooltip`    | Tour tooltip root                                                           | onboarding visible/hidden                       |
| `data-vintage-label`    | Map footer data vintage indicator (e.g. `"2008 TRI · October 2024 freeze"`) | UX Invariant 11 — vintage visible and non-empty |

---

## Geocoding (ADR-008)

| `data-testid`               | Component                                  | Used in Gherkin Step                                   |
|-----------------------------|--------------------------------------------|--------------------------------------------------------|
| `resolved-geocode`          | Resolved location panel container          | UX Invariant 13 — `"resolved location panel is visible"` |
| `geocode-confidence-badge`  | Confidence level badge (Exact/High/Approximate/Low) | `"geocode confidence badge shows 'High' or 'Exact'"` |

> **Note:** The resolved geocode panel appears below the search form after a location-based search is submitted. It displays the canonical address from Photon and a color-coded confidence badge.

---

## Naming Conventions

- Use kebab-case only: `facility-detail-panel` not `facilityDetailPanel`
- Never use test IDs as CSS selectors for styling — they are exclusively for testing
- For lists of items, use a base ID on the container and `[data-item-id="{value}"]` on individual items (e.g. `data-testid="results-row" data-facility-id="21219BTHLS3RD"`)
- Dynamic IDs (e.g. per-year layer toggles) use a predictable template: `layer-toggle-tri-{year}`

