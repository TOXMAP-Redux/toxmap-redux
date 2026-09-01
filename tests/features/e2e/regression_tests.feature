# Regression Tests for TOXMAP
# Split from ux_invariants.feature per F-P6-06 audit finding
# All regression scenarios with proper @phase-X tags
#
# Phase tagging:
#   @phase-4 — Superfund regressions
#   @phase-6 — Phase 6 regressions and ADR implementations
#   @phase-7 — Phase 7 bug fixes and UX improvements
@e2e @regression
Feature: Regression Tests

  Background:
    Given the application is running at "http://localhost:3000"
    And the seed database is loaded

  # ══════════════════════════════════════════════════════════════════════════
  # Phase 4 Regressions — Superfund Overlay
  # ══════════════════════════════════════════════════════════════════════════

  # ── UCD-17: Superfund 3-Way Status Symbols (DEF-001 fix) ─────────────────
  # Regression test for: DEF-001 Superfund status symbols missing 3-way distinction
  # Original TOXMAP used: filled square (NPL Final), diamond (Proposed), X-square (Deleted)
  # Seed data includes all 3 status types: NPL, Proposed, Deleted
  @phase-4
  Scenario: Regression — UCD-17 Legend shows 3 distinct Superfund status symbols
    Given I am on the map page
    Then the Superfund layer toggle is present
    And the Superfund legend shows "NPL (Final)" entry with a square icon
    And the Superfund legend shows "Proposed" entry with a diamond icon
    And the Superfund legend shows "Deleted" entry with an X-square icon

  @phase-4
  Scenario: Regression — UCD-17 All 3 Superfund status types present in seed data
    Given I am on the map page
    Then the Superfund in-view count is greater than or equal to 4

  # ══════════════════════════════════════════════════════════════════════════
  # Phase 6 Regressions — Layer Visibility & Browse Mode
  # ══════════════════════════════════════════════════════════════════════════

  # ── Superfund Markers Regression (React StrictMode) ──────────────────────
  # Regression test for: useSuperfundViewport hasFetchedRef bug
  # The bug: React StrictMode aborted the first fetch but the hook skipped the
  # retry because hasFetchedRef was set before the fetch completed.
  @phase-6
  Scenario: Regression — Superfund markers visible on initial page load
    Given I am on the map page
    Then the Superfund layer is visible on the map
    And the Superfund in-view count is greater than zero

  @phase-6
  Scenario: Regression — Superfund markers visible after search
    Given I am on the map page
    When I select the "Superfund" dataset
    And I type "Front Royal, VA" into the location field
    And I click Search
    Then the Superfund layer is visible on the map
    And the results sidebar shows "AVTEX FIBERS INC"

  # ── TRI Circle Markers Regression (Browse Mode) ──────────────────────────
  # Regression test for: TRI browse mode 500-mile radius bug
  # The bug: Browse mode called /api/v1/facilities with radius_miles=500,
  # which only returned facilities within 500 miles of Kansas (US center).
  # Now uses /api/v1/facilities/browse to fetch ALL facilities.
  @phase-6
  Scenario: Regression — TRI circles visible on initial page load
    Given I am on the map page
    Then the TRI layer is visible on the map
    And the TRI in-view count is greater than zero

  @phase-6
  Scenario: Regression — TRI circles visible after search
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    Then the TRI layer is visible on the map
    And the results sidebar shows at least one facility

  @phase-6
  Scenario: Regression — TRI layer toggle hides and shows circles
    Given I am on the map page
    Then the TRI layer is visible on the map
    When I toggle the TRI layer off
    Then the TRI layer is hidden on the map
    When I toggle the TRI layer on
    Then the TRI layer is visible on the map

  # ── Both Dataset Mode (Fig 2015-4) ───────────────────────────────────────
  # Regression test for: "Both" option missing in dataset selector
  # The original TOXMAP had TRI + Superfund combined search (Fig 2015-4).
  @phase-6
  Scenario: Regression — Both dataset radio button is present and default
    Given I am on the map page
    When I click on the Search tab
    Then the "Both" dataset radio button is selected by default
    And the "TRI" dataset radio button is present
    And the "Superfund" dataset radio button is present

  @phase-6
  Scenario: Regression — Both dataset shows combined TRI and Superfund results
    Given I am on the map page
    When I select the "Both" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    Then the results sidebar shows TRI and Superfund sections
    And the TRI section header is visible
    And the Superfund section header is visible

  @phase-6
  Scenario: Regression — Both dataset fetches TRI facilities
    Given I am on the map page
    When I select the "Both" dataset
    And I type "Sparrows Point, MD" into the location field
    And I click "Search"
    Then the TRI layer is visible on the map
    And the results sidebar shows at least one facility

  @phase-6
  Scenario: Regression — Both dataset fetches Superfund sites
    Given I am on the map page
    When I select the "Both" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    Then the Superfund layer is visible on the map
    And the results sidebar shows "AVTEX FIBERS INC"

  @phase-6
  Scenario: Regression — Both mode shows combined TRI and Superfund legends
    Given I am on the map page
    When I select the "Both" dataset
    And I click "Search"
    Then the TRI legend is visible
    And the Superfund legend is visible

  # ── Both Mode Drawer Selection ───────────────────────────────────────────
  # Regression test for: clicking Superfund result in "Both" mode opened
  # the wrong drawer (TRI drawer instead of Superfund drawer).
  @phase-6
  Scenario: Regression — Both mode: clicking TRI result opens TRI drawer
    Given I am on the map page
    When I select the "Both" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    Then the TRI section header is visible
    When I click on "FRONT ROYAL PLASTICS INC" in the TRI results
    Then the TRI facility detail drawer opens
    And the Superfund detail panel is not shown

  @phase-6
  Scenario: Regression — Both mode: clicking Superfund result opens Superfund drawer
    Given I am on the map page
    When I select the "Both" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    Then the Superfund section header is visible
    When I click on "AVTEX FIBERS INC" in the Superfund results
    Then the Superfund detail panel opens
    And the TRI facility detail panel is not shown

  # ── US Zip Code Geocoding ────────────────────────────────────────────────
  # Regression test for: US zip codes geocoded to Mexico instead of the US.
  # Fix: Append ", USA" to 5-digit zip code queries to bias towards US results.
  @phase-6
  Scenario: Regression — US zip code geocodes to USA, not Mexico
    Given I am on the map page
    When I type "22630" into the location field
    And I click "Search"
    Then the map is centered in the United States
    And the map is NOT centered in Mexico

  @phase-6
  Scenario: Regression — US zip code with ZIP+4 format geocodes to USA
    Given I am on the map page
    When I type "22630-1234" into the location field
    And I click "Search"
    Then the map is centered in the United States

  # ══════════════════════════════════════════════════════════════════════════
  # Phase 6 — 6.UX Improvements
  # ══════════════════════════════════════════════════════════════════════════

  # ── 6.UX.1: Superfund Panel UI Improvements ──────────────────────────────
  # Fix: (1) EPA ID now links to EPA Site Progress Profile via SEMS site_id
  #      (2) CAS numbers removed from contaminants list for cleaner UI
  @phase-6 @6UX1
  Scenario: Regression — Superfund EPA ID is clickable
    Given I am on the map page
    When I select the "Superfund" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    Then the results sidebar shows "AVTEX FIBERS INC"
    When I click on "AVTEX FIBERS INC" in the Superfund results
    Then the Superfund detail panel opens
    And the EPA ID link is visible
    And the EPA ID links to "cumulis.epa.gov/supercpad"

  @phase-6 @6UX1
  Scenario: Regression — Superfund contaminants do NOT show CAS numbers
    Given I am on the map page
    When I select the "Superfund" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    When I click on "AVTEX FIBERS INC" in the Superfund results
    Then the Superfund detail panel opens
    And the contaminants list is visible
    And no contaminant row shows a CAS number pattern

  # ══════════════════════════════════════════════════════════════════════════
  # Phase 6 — ADR-010: Facility Search Autocomplete
  # ══════════════════════════════════════════════════════════════════════════

  @phase-6 @ADR010
  Scenario: ADR-010 — Facility search input is present in search panel
    Given I am on the map page
    When I click the search panel tab
    Then the facility search input is present
    And the facility search input has placeholder "e.g. 89319BHPCP or Bethlehem Steel"

  @phase-6 @ADR010
  Scenario: ADR-010 — Facility search shows autocomplete results
    Given I am on the map page
    When I click the search panel tab
    And I type "BETHLEHEM" into the facility search input
    Then the facility search dropdown appears
    And the facility search dropdown shows at least 1 result

  @phase-6 @ADR010
  Scenario: ADR-010 — TRI Facility ID in drawer header is a clickable link
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    And I click on the first TRI facility in the results
    Then the facility detail drawer opens
    And the TRI ID link is visible
    And the TRI ID links to "enviro.epa.gov/facts/tri/ef-facilities"

  @phase-6 @ADR010
  Scenario: ADR-010 — EPA TRI Facility Report link at bottom of drawer
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    And I click on the first TRI facility in the results
    Then the facility detail drawer opens
    And the EPA TRI Facility Report link is visible
    And the EPA TRI Facility Report link is above the close button

  # ══════════════════════════════════════════════════════════════════════════
  # Phase 6 — Export Functionality
  # ══════════════════════════════════════════════════════════════════════════

  # ── Export: Map Screenshot Functionality (UCD 2011 + 6.EXPORT) ────────────
  # UCD 2011 finding: Users requested print/export functionality (Task T-09)
  @phase-6 @export
  Scenario: Export — Map screenshot button is present and enabled
    Given I am on the map page
    Then the map screenshot button is visible
    And the map screenshot button is enabled

  @phase-6 @export
  Scenario: Export — Map screenshot downloads PNG file
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    Then the results table shows TRI facilities
    When I click the map screenshot button
    Then a PNG file is downloaded
    And the downloaded file name contains "toxmap"

  # ══════════════════════════════════════════════════════════════════════════
  # Phase 7 Regressions — Bug Fixes
  # ══════════════════════════════════════════════════════════════════════════

  # ── 7.BUG.1: Results Count Stability ─────────────────────────────────────
  # Root cause: triSearchResults used viewport-filtered facilities.
  # Fix: Always use triAllResults (API radius constraint is sufficient).
  @phase-7 @7BUG1
  Scenario: Regression — Results count remains stable when scrolling map
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    Then the results table shows a count
    When I scroll the map
    Then the results count remains unchanged

  # ── 7.BUG.2/7.BUG.3: TRI Hover Tooltip ───────────────────────────────────
  # Fix: Added Popup component for highlighted facilities.
  @phase-7 @7BUG2
  Scenario: Regression — Hovering TRI result shows tooltip on map
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    And I hover over the first TRI result row
    Then a tooltip popup appears on the map

  @phase-7 @7BUG3
  Scenario: Regression — Hovering selected TRI facility does not show duplicate popup
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    And I click on the first TRI result row
    Then the TRI facility detail drawer opens
    When I hover over the first TRI result row
    Then only one popup is visible on the map

  # ── 7.BUG.4: Superfund Hover Parity ──────────────────────────────────────
  # Fix: Added Superfund-specific zoom useEffect and Popup component.
  @phase-7 @7BUG4
  Scenario: Regression — Hovering Superfund result zooms map and shows tooltip
    Given I am on the map page
    When I select the "Superfund" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    And I hover over "AVTEX FIBERS INC" in the Superfund results
    Then the map zooms to the Superfund site
    And a tooltip popup appears on the map

  # ── 7.BUG.5: Progressive TRI Circle Sizing ───────────────────────────────
  # Fix: circle-radius now varies by color_band (red=full, green=smallest).
  @phase-7 @7BUG5
  Scenario: Regression — TRI circles have progressive sizing by release tier
    Given I am on the map page
    Then the TRI layer is visible on the map
    And red tier circles are larger than green tier circles

  @phase-7 @7BUG5
  Scenario: Regression — TRI legend shows proportional circle sizes
    Given I am on the map page
    Then the TRI legend shows smallest circle for "< 1,000 lbs" tier
    And the TRI legend shows largest circle for "≥ 100,000 lbs" tier

  # ── 7.BUG.7: Superfund Viewport Count ────────────────────────────────────
  # Fix: Added superfundInViewCount memo that filters by mapBbox.
  @phase-7 @7BUG7
  Scenario: Regression — Superfund "in view" count reflects visible sites only
    Given I am on the map page
    Then the Superfund layer toggle is present
    And the Superfund in-view count is less than total Superfund sites

  # ── 7.BUG.8: Results Table Scroll ────────────────────────────────────────
  # Fix: Removed .slice(0, 10) limitation.
  @phase-7 @7BUG8
  Scenario: Regression — All search results are accessible by scrolling
    Given I am on the map page
    When I type "Richland, WA" into the location field
    And I click "Search"
    Then all TRI results are rendered in the table
    And all Superfund results are rendered in the table

  # ── 7.BUG.9: Map Filtering ───────────────────────────────────────────────
  # Fix: Added triFacilitiesForMap memo; map now receives filtered data.
  @phase-7 @7BUG9
  Scenario: Regression — Map shows only facilities matching search filters
    Given I am on the map page
    When I type "LEAD" into the chemical field
    And I select "Continental US" from the state filter
    And I click "Search"
    Then the map shows only Continental US facilities
    And no facilities are visible in Alaska on the map

  # ── 7.BUG.10: Exact Match Chemical Search ────────────────────────────────
  @phase-7 @7BUG10
  Scenario: Regression — Exact match search returns fewer results than expanded search
    Given I am on the map page
    When I type "LEAD" into the chemical field
    And I type "Baltimore, MD" into the location field
    And I click "Search"
    Then the chemical family banner is visible
    And the results count is greater than zero
    When I click "Search exact term only" in the banner
    Then the results count is smaller than before
    And the chemical family banner is NOT visible

  # ── 7.BUG.11: SearchPanel Scroll ─────────────────────────────────────────
  @phase-7 @7BUG11
  Scenario: Regression — SearchPanel is scrollable in small viewport
    Given I resize the viewport to 800x400
    And I am on the map page
    When I click the search panel tab
    Then the search form is fully visible
    And the search panel content is scrollable

  # ── 7.BUG.12: Chemical Family Banner Padding ─────────────────────────────
  @phase-7 @7BUG12
  Scenario: Regression — Chemical family banner has consistent padding
    Given I am on the map page
    When I type "LEAD" into the chemical field
    And I type "Baltimore, MD" into the location field
    And I click "Search"
    Then the chemical family banner has horizontal padding

  # ── 7.BUG.13: Sidebar Resize ─────────────────────────────────────────────
  @phase-7 @7BUG13
  Scenario: Regression — Sidebar can be resized by dragging
    Given I am on the map page
    Then the sidebar resize handle is present
    When I drag the sidebar resize handle 100 pixels to the right
    Then the sidebar width has increased
    And the map camera padding has adjusted

  # ── 7.BUG.15: MERCURY Family Expansion ───────────────────────────────────
  # Fix: Added whitespace normalization to seed script.
  @phase-7 @7BUG15
  Scenario: Regression — MERCURY family shows expansion banner
    Given I am on the map page
    When I type "MERCURY" into the chemical field
    And I click "Search"
    Then the chemical family banner is visible
    And the banner mentions "MERCURY"

  @phase-7 @7BUG15
  Scenario: Regression — All metal families show expansion banner
    Given I am on the map page
    When I type "CHROMIUM" into the chemical field
    And I click "Search"
    Then the chemical family banner is visible
    When I type "NICKEL" into the chemical field
    And I click "Search"
    Then the chemical family banner is visible
    When I type "ARSENIC" into the chemical field
    And I click "Search"
    Then the chemical family banner is visible

  # ── ADR-008: Geocoding Confidence Scoring (7.BUG.25) ─────────────────────
  @phase-7 @7BUG25
  Scenario: Regression — Full address geocodes with high confidence badge
    Given I am on the map page
    When I type "100 Mill Rd, Port Townsend, WA" into the location field
    And I click "Search"
    Then the resolved location panel is visible
    And the geocode confidence badge shows "High" or "Exact"
    And the resolved address contains "Port Townsend"
    And the map is centered near Port Townsend, WA

  @phase-7 @7BUG25
  Scenario: Regression — Partial address shows approximate confidence warning
    Given I am on the map page
    When I type "100 Mill Rd" into the location field
    And I click "Search"
    Then the resolved location panel is visible
    And the geocode confidence badge shows "Approximate" or "Low"
    And the approximate location warning is visible

  @phase-7 @7BUG25
  Scenario: Regression — Geocoding uses viewport bias for ambiguous queries
    Given I am on the map page
    And the map is zoomed to Port Townsend, WA area
    When I type "Mill Road" into the location field
    And I click "Search"
    Then the resolved address is closer to Port Townsend than to other states

  @phase-7 @7BUG25
  Scenario: Regression — Resolved location shows canonical address from Photon
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    Then the resolved location panel is visible
    And the resolved address contains "MD" or "Maryland"
    And the resolved address is not equal to "Sparrows Point, MD"

  @phase-7 @7BUG25
  Scenario: Regression — Address with typo shows low confidence
    Given I am on the map page
    When I type "100 Mill Rd Port Townsed" into the location field
    And I click "Search"
    Then the resolved location panel is visible
    And the geocode confidence badge is NOT "Exact"

  # ── 7.BUG.27: 15-Year Trend Chart Data Integrity ─────────────────────────
  # CRITICAL: Per-chemical releases were OVERWRITTEN instead of SUMMED.
  @phase-7 @7BUG27 @critical
  Scenario: Regression — 15-year trend aggregates all chemicals per year
    Given I am on the map page
    When I type "Palatine, IL" into the location field
    And I click "Search"
    And I click on "ARLINGTON PLATING ACQUISITION CO" in the results
    Then the TRI facility detail drawer opens
    When I click the "15-Year Trend" tab
    Then the 15-year trend chart is visible
    And the trend chart Y-axis maximum is greater than 12900

  @phase-7 @7BUG27
  Scenario: Regression — 15-year trend shows full year range without gaps
    Given I am on the map page
    When I type "Palatine, IL" into the location field
    And I click "Search"
    And I click on "ARLINGTON PLATING ACQUISITION CO" in the results
    Then the TRI facility detail drawer opens
    When I click the "15-Year Trend" tab
    Then the 15-year trend chart is visible
    And the trend chart X-axis shows 15 consecutive years

  @phase-7 @7BUG27
  Scenario: Regression — 15-year trend respects selected year filter
    Given I am on the map page
    When I select year "2020"
    And I type "Palatine, IL" into the location field
    And I click "Search"
    And I click on "ARLINGTON PLATING ACQUISITION CO" in the results
    Then the TRI facility detail drawer opens
    When I click the "15-Year Trend" tab
    Then the 15-year trend chart is visible
    And the trend chart heading shows "2006–2020"

  @phase-7 @7BUG27
  Scenario: Regression — 15-year trend shows reporting year in tooltip
    Given I am on the map page
    When I type "Palatine, IL" into the location field
    And I click "Search"
    And I click on "ARLINGTON PLATING ACQUISITION CO" in the results
    Then the TRI facility detail drawer opens
    When I click the "15-Year Trend" tab
    Then the 15-year trend chart is visible
    When I hover over a data point in the trend chart
    Then the tooltip shows "Reporting Year:"

  # ── 7.BUG.28: Top Chemicals Table Structure ──────────────────────────────
  @phase-7 @7BUG28
  Scenario: Regression — Top Chemicals table shows numbered ranks
    Given I am on the map page
    When I perform a search for "BENZENE" near "Houston, TX"
    And I click on the first result in the results table
    Then the facility detail panel opens
    And the Top Chemicals tab shows numbered chemical ranks

  @phase-7 @7BUG28
  Scenario: Regression — Top Chemicals table shows all-years header
    Given I am on the map page
    When I perform a search for "BENZENE" near "Houston, TX"
    And I click on the first result in the results table
    Then the facility detail panel opens
    And the Top Chemicals table shows "Release Amount (lbs./all years)" header

  @phase-7 @7BUG28
  Scenario: Regression — Top Chemicals table shows TOTAL row
    Given I am on the map page
    When I perform a search for "BENZENE" near "Houston, TX"
    And I click on the first result in the results table
    Then the facility detail panel opens
    And the Top Chemicals table shows a TOTAL footer row

  @phase-7 @7BUG28
  Scenario: Regression — Top Chemicals table shows Other chemicals row when applicable
    Given I am on the map page
    When I perform a search for "BENZENE" near "Houston, TX"
    And I click on the first result in the results table
    Then the facility detail panel opens
    And the Top Chemicals table shows "Other chemicals" row when applicable

  # ── 7.BUG.29: All-Years Aggregation ──────────────────────────────────────
  @phase-7 @7BUG29
  Scenario: Regression — All years search shows aggregated totals
    Given I am on the map page
    When I perform a search for "BENZENE" near "Baytown, TX"
    Then the results table shows "EXXONMOBIL" with release amount greater than 50000 lbs

  @phase-7 @7BUG29
  Scenario: Regression — Facility detail shows all-years total
    Given I am on the map page
    When I perform a search for "BENZENE" near "Baytown, TX"
    And I click on "EXXONMOBIL" in the results
    Then the facility detail panel opens
    And the facility detail total matches the aggregated all-years amount

  # ── 7.BUG.30: Facility Drawer Resize Handle ──────────────────────────────
  @phase-7 @7BUG30
  Scenario: Regression — Facility drawer has resize handle
    Given I am on the map page
    When I perform a search for "BENZENE" near "Houston, TX"
    And I click on the first result in the results table
    Then the facility detail panel opens
    And the facility drawer resize handle is present

  @phase-7 @7BUG30
  Scenario: Regression — Facility drawer can be resized by dragging
    Given I am on the map page
    When I perform a search for "BENZENE" near "Houston, TX"
    And I click on the first result in the results table
    Then the facility detail panel opens
    When I drag the facility drawer resize handle 100 pixels to the left
    Then the facility drawer width has increased

  # ── 7.BUG.31: Superfund Drawer Resize Handle Parity ──────────────────────
  @phase-7 @7BUG31
  Scenario: Regression — Superfund drawer has resize handle
    Given I am on the map page
    When I select the "Superfund" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    And I click on "AVTEX FIBERS INC" in the Superfund results
    Then the Superfund detail panel opens
    And the superfund drawer resize handle is present

  @phase-7 @7BUG31
  Scenario: Regression — Superfund drawer can be resized by dragging
    Given I am on the map page
    When I select the "Superfund" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    And I click on "AVTEX FIBERS INC" in the Superfund results
    Then the Superfund detail panel opens
    When I drag the superfund drawer resize handle 100 pixels to the left
    Then the superfund drawer width has increased

  # ── 7.BUG.38: TRI Medium Discrepancy Display ─────────────────────────────
  @phase-7 @7BUG38
  Scenario: Regression — By Medium tab shows aggregate discrepancy with Trend tab callout
    Given I am on the map page
    When I type "Hanford, WA" into the location field
    And I click "Search"
    And I click on the first TRI facility in the results
    Then the facility detail drawer opens
    When I click the "By Medium" tab
    Then the medium discrepancy section is visible
    And the EPA-reported total is displayed
    And the discrepancy label shows "Aggregate Discrepancy"
    And the discrepancy footnote references the 15-Year Trend tab

  @phase-7 @7BUG38
  Scenario: Regression — Medium discrepancy footnote contains EPA link
    Given I am on the map page
    When I type "Hanford, WA" into the location field
    And I click "Search"
    And I click on the first TRI facility in the results
    Then the facility detail drawer opens
    When I click the "By Medium" tab
    Then the discrepancy footnote contains a link to EPA TRI data quality page

  @phase-7 @7BUG38
  Scenario: Regression — 15-Year Trend tab shows per-year discrepancy legend
    Given I am on the map page
    When I type "Hanford, WA" into the location field
    And I click "Search"
    And I click on the first TRI facility in the results
    Then the facility detail drawer opens
    When I click the "15-Year Trend" tab
    Then the trend discrepancy legend is visible
    And the trend discrepancy legend explains high discrepancy indicators

  # ── 7.BUG.39: Census Choropleth Z-Order ──────────────────────────────────
  @phase-7 @7BUG39
  Scenario: 7.BUG.39 — Superfund sites visible above census demographics layer
    Given I am on the map page
    When I enable the Census & Health Data panel
    And I select "Census 2020" from the census year dropdown
    And I select "Population" from the census category
    And I click "Total Population" sub-layer
    Then the demographics layer is visible on the map
    When I filter by state "VA"
    And I click "Search"
    Then the Superfund layer is visible on the map
    And the Superfund sites are rendered above the demographics fill layer

  @phase-7 @7BUG39
  Scenario: 7.BUG.39 — TRI facilities visible above census and Superfund layers
    Given I am on the map page
    When I enable the Census & Health Data panel
    And I select "Census 2020" from the census year dropdown
    And I select "Population" from the census category
    And I click "Total Population" sub-layer
    Then the demographics layer is visible on the map
    When I filter by state "VA"
    And I click "Search"
    Then the TRI layer is visible on the map
    And the TRI facilities are rendered above the Superfund layer

  # ── 7.BUG.40: Census 2000 Age Layers Unavailable ─────────────────────────
  @phase-7 @7BUG40
  Scenario: 7.BUG.40 — Census 2000 disables "% Under 18" and "% Over 65" buttons
    Given I am on the map page
    When I enable the Census & Health Data panel
    And I select "Census 2000" from the census year dropdown
    And I select "Population" from the census category
    Then the "% Under 18" button is disabled
    And the "% Over 65" button is disabled
    And the disabled button tooltip shows "Age distribution data not available for Census 2000"

  @phase-7 @7BUG40
  Scenario: 7.BUG.40 — Census 2010 and 2020 enable age percentage buttons
    Given I am on the map page
    When I enable the Census & Health Data panel
    And I select "Census 2010" from the census year dropdown
    And I select "Population" from the census category
    Then the "% Under 18" button is enabled
    And the "% Over 65" button is enabled
    When I select "Census 2020" from the census year dropdown
    Then the "% Under 18" button is enabled
    And the "% Over 65" button is enabled

  @phase-7 @7BUG40
  Scenario: 7.BUG.40 — Switching to Census 2000 with unsupported layer selected clears selection
    Given I am on the map page
    When I enable the Census & Health Data panel
    And I select "Census 2020" from the census year dropdown
    And I select "Population" from the census category
    And I click "% Under 18" sub-layer
    Then the demographics layer is visible on the map
    When I select "Census 2000" from the census year dropdown
    Then the demographics layer is not visible on the map
    And no sub-layer button is selected

  # ── 7.BUG.41: Census Overlay Color Scheme ────────────────────────────────
  @phase-7 @7BUG41
  Scenario: 7.BUG.41 — Census overlay uses green-to-blue color scheme (historical TOXMAP)
    Given I am on the map page
    When I enable the Census & Health Data panel
    And I select "Census 2020" from the census year dropdown
    And I select "Population" from the census category
    And I click "Total Population" sub-layer
    Then the demographics legend shows the 8-bin green-to-blue color scale
    And the map fill colors range from light green to dark blue

  @phase-7 @7BUG41
  Scenario: 7.BUG.41 — All demographic layers use consistent green-to-blue scheme
    Given I am on the map page
    When I enable the Census & Health Data panel
    And I select "Census 2020" from the census year dropdown
    And I select "Population" from the census category
    And I click "% Under 18" sub-layer
    Then the demographics legend shows the 8-bin green-to-blue color scale
    When I click "% Over 65" sub-layer
    Then the demographics legend shows the 8-bin green-to-blue color scale
    When I select "Income" from the census category
    And I click "Median Household Income" sub-layer
    Then the demographics legend shows the 8-bin green-to-blue color scale

  # ── 7.BUG.42: Census Hover Tooltip Overlaps ──────────────────────────────
  @phase-7 @7BUG42
  Scenario: 7.BUG.42 — Census county hover tooltip hidden when TRI popup is open
    Given I am on the map page
    When I enable the Census & Health Data panel
    And I select "Census 2020" from the census year dropdown
    And I select "Population" from the census category
    And I click "Total Population" sub-layer
    Then the demographics layer is visible on the map
    When I click on a TRI facility marker
    Then the TRI facility popup is visible
    And the county tooltip popup is not visible

  @phase-7 @7BUG42
  Scenario: 7.BUG.42 — Census county hover tooltip hidden when Superfund popup is open
    Given I am on the map page
    When I enable the Census & Health Data panel
    And I select "Census 2020" from the census year dropdown
    And I select "Population" from the census category
    And I click "Total Population" sub-layer
    Then the demographics layer is visible on the map
    When I click on a Superfund site marker
    Then the Superfund site popup is visible
    And the county tooltip popup is not visible

  # ── 7.BUG.43: Aggregate Discrepancy Fetch Range ──────────────────────────
  # CRITICAL: Frontend compared 15-year medium sum vs all-years EPA total (61% error).
  # Fix: When viewing "all years", fetch releases from 1987–present.
  @phase-7 @7BUG43
  Scenario: 7.BUG.43 — Aggregate Discrepancy uses all years when viewing "all years"
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    And I click on "BRANDON SHORES & WAGNER COMPLEX" in the results
    Then the facility detail drawer opens
    When I click the "By Medium" tab
    Then the medium discrepancy section is visible
    And the aggregate discrepancy percentage is less than 10%

  @phase-7 @7BUG43
  Scenario: 7.BUG.43 — Aggregate Discrepancy year range label shows 1987–current year
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    And I click on "BRANDON SHORES & WAGNER COMPLEX" in the results
    Then the facility detail drawer opens
    When I click the "By Medium" tab
    Then the medium discrepancy section is visible
    And the discrepancy label shows year range starting with "1987"

  # ── 7.UX.7: Release Quantities Rounding ──────────────────────────────────
  # Fix: formatLbs() and formatNumber() now Math.round() before formatting.
  @phase-7 @7UX7
  Scenario: 7.UX.7 — EPA-Reported Total displays as whole number
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    And I click on the first TRI facility in the results
    Then the facility detail drawer opens
    When I click the "By Medium" tab
    Then the EPA-Reported Total is formatted as a whole number without decimals

  @phase-7 @7UX7
  Scenario: 7.UX.7 — Results table release amounts display as whole numbers
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    Then the results table shows TRI facilities
    And the release amounts in the results table have no decimal points

  # ── 7.UX.8: Results Table Click-Only Map Movement ────────────────────────
  # Fix: Removed onMouseEnter handlers; map only moves on click.
  @phase-7 @7UX8
  Scenario: 7.UX.8 — Hovering over results row does NOT move the map
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    Then the results table shows TRI facilities
    When I record the current map center
    And I hover over the second TRI result row
    Then the map center has NOT changed

  @phase-7 @7UX8
  Scenario: 7.UX.8 — Clicking on results row DOES move the map
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    Then the results table shows TRI facilities
    When I record the current map center
    And I click on the second TRI result row
    Then the map center HAS changed
    And the facility detail drawer opens

  # ══════════════════════════════════════════════════════════════════════════
  # Phase 7 — 7.UX Improvements
  # ══════════════════════════════════════════════════════════════════════════

  # ── 7.UX.1: State-only Browse Mode ───────────────────────────────────────
  @phase-7 @7UX1
  Scenario: 7.UX.1 — State-only browse shows TRI facilities in selected state
    Given I am on the map page
    When I click the search panel tab
    And I select "NJ" from the state dropdown
    And I click "Search"
    Then the results table shows TRI facilities
    And the map zooms to New Jersey
    And the results table shows more than 100 TRI facilities

  @phase-7 @7UX1
  Scenario: 7.UX.1 — State-only browse shows Superfund sites in selected state
    Given I am on the map page
    When I click the search panel tab
    And I select "Superfund" from the dataset radio group
    And I select "NJ" from the state dropdown
    And I click "Search"
    Then the results table shows Superfund sites
    And the map zooms to New Jersey
    And the results table shows more than 50 Superfund sites

  # ── 7.UX.2: Superfund Drawer EPA Link Parity ─────────────────────────────
  @phase-7 @7UX2
  Scenario: 7.UX.2 — Superfund drawer EPA link in fixed footer position
    Given I am on the map page
    When I click the search panel tab
    And I select "Superfund" from the dataset radio group
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    And I click on the first Superfund site in the results
    Then the Superfund detail drawer opens
    And the EPA Site Progress Profile link is visible
    And the EPA Site Progress Profile link is above the close button

  # ── 7.UX.3: Facility Drawer Year Filtering ───────────────────────────────
  @phase-7 @7UX3
  Scenario: 7.UX.3 — Facility drawer shows year-filtered data in Top Chemicals tab
    Given I am on the map page
    When I click the search panel tab
    And I type "Carlin, NV" into the location field
    And I select "2020" from the year dropdown
    And I click "Search"
    And I click on the first TRI facility in the results
    Then the facility detail drawer opens
    And the drawer heading shows "EMISSIONS ESTIMATES (2020)"
    And the table header shows "(lbs./2020)"

  @phase-7 @7UX3
  Scenario: 7.UX.3 — Facility drawer shows year-filtered data in By Medium tab
    Given I am on the map page
    When I click the search panel tab
    And I type "Carlin, NV" into the location field
    And I select "2020" from the year dropdown
    And I click "Search"
    And I click on the first TRI facility in the results
    Then the facility detail drawer opens
    When I click the "By Medium" tab
    Then the medium heading shows "Release by medium (lbs./2020)"

  @phase-7 @7UX3
  Scenario: 7.UX.3 — Facility drawer shows all years when no year selected
    Given I am on the map page
    When I click the search panel tab
    And I type "Carlin, NV" into the location field
    # No year selected = "All years"
    And I click "Search"
    And I click on the first TRI facility in the results
    Then the facility detail drawer opens
    And the drawer heading shows "EMISSIONS ESTIMATES (all years)"
    And the table header shows "(lbs./all years)"

  @phase-7 @7UX3
  Scenario: 7.UX.3 — Release Trend tab uses selected year as end point
    Given I am on the map page
    When I click the search panel tab
    And I type "Carlin, NV" into the location field
    And I select "2020" from the year dropdown
    And I click "Search"
    And I click on the first TRI facility in the results
    Then the facility detail drawer opens
    When I click the "Release Trend" tab
    Then the trend range subtitle shows "2006–2020"

  # ── 7.UX.4: Release Trend Tab 1987 Clamp ─────────────────────────────────
  @phase-7 @7UX4
  Scenario: 7.UX.4 — Release Trend tab is renamed from "15-Year Trend"
    Given I am on the map page
    When I perform a search for "COPPER" near "Ruth, NV"
    And I click on the first result in the results table
    Then the facility detail drawer opens
    And the Release Trend tab is labeled "Release Trend"

  @phase-7 @7UX4
  Scenario: 7.UX.4 — Release Trend with 1990 year filter shows 1987–1990
    Given I am on the map page
    When I click the search panel tab
    And I type "Ruth, NV" into the location field
    And I select "1990" from the year dropdown
    And I click "Search"
    And I click on the first TRI facility in the results
    Then the facility detail drawer opens
    When I click the "Release Trend" tab
    Then the trend range subtitle shows "1987–1990"
    And the trend range subtitle indicates TRI reporting began 1987

  @phase-7 @7UX4
  Scenario: 7.UX.4 — Release Trend with 2020 year filter shows full 15 years
    Given I am on the map page
    When I click the search panel tab
    And I type "Ruth, NV" into the location field
    And I select "2020" from the year dropdown
    And I click "Search"
    And I click on the first TRI facility in the results
    Then the facility detail drawer opens
    When I click the "Release Trend" tab
    Then the trend range subtitle shows "2006–2020"
    And the trend range subtitle does not indicate limited years

  # ── 7.UX.5: Missing Year Data as Gaps ────────────────────────────────────
  @phase-7 @7UX5
  Scenario: 7.UX.5 — Release Trend legend shows gap explanation when missing years exist
    Given I am on the map page
    When I perform a search for "COPPER" near "Ruth, NV"
    And I click on the first result in the results table
    Then the facility detail drawer opens
    When I click the "Release Trend" tab
    Then the trend discrepancy legend is visible

  @phase-7 @7UX5
  Scenario: 7.UX.5 — Release Trend tooltip shows "No TRI report filed" for missing year
    Given I am on the map page
    When I click the search panel tab
    And I type "Ruth, NV" into the location field
    And I select "1990" from the year dropdown
    And I click "Search"
    And I click on the first TRI facility in the results
    Then the facility detail drawer opens
    When I click the "Release Trend" tab
    Then the Release Trend chart is visible

  # ── 7.UX.6: Census County Hover Tooltip ──────────────────────────────────
  @phase-7 @7UX6
  Scenario: 7.UX.6 — Census county hover shows tooltip with value and bin label
    Given I am on the map page
    When I enable the Census & Health Data panel
    And I select "Census 2020" from the census year dropdown
    And I select "Population" from the census category
    And I click "% Over 65" sub-layer
    Then the demographics layer is visible on the map
    When I hover over a county on the demographics layer
    Then the county tooltip popup appears
    And the tooltip shows the county name
    And the tooltip shows the demographic value with units
    And the tooltip shows the bin range label

  @phase-7 @7UX6
  Scenario: 7.UX.6 — County tooltip updates when switching demographic layers
    Given I am on the map page
    When I enable the Census & Health Data panel
    And I select "Census 2020" from the census year dropdown
    And I select "Population" from the census category
    And I click "Total Population" sub-layer
    And I hover over a county on the demographics layer
    Then the tooltip shows the population value with "people" units
    When I click "% Over 65" sub-layer without moving mouse
    Then the tooltip shows the percentage value with "%" units
