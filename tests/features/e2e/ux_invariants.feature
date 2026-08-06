# UX Design Invariants (Phase 3: Invariants 1, 2, 3, 4, 7, 8, 9)
# Full spec: docs/testing/TOXMAP_ACCEPTANCE_TESTS.md Feature 8
# Phase 4+: Invariants 5, 6, 10 (require Superfund/Demographics overlays)
Feature: UX Design Invariants

  Background:
    Given the application is running at "http://localhost:3000"
    And the seed database is loaded

  # ── Invariant 1 (Phase 3) ─────────────────────────────────────────────────

  Scenario: Invariant 1 — Map Contents and Search Results never visible simultaneously
    Given I am on the map page
    Then the map contents panel is visible
    And the search results panel is NOT visible
    When I perform a search for "BENZENE" near "Houston, TX"
    Then the search results panel is visible
    And the map contents panel is NOT visible

  # ── Invariant 2 (Phase 3) ─────────────────────────────────────────────────

  Scenario: Invariant 2 — Search results table never contains empty placeholder rows
    Given I am on the map page
    When I perform a search for "LEAD COMPOUNDS" near "Sparrows Point, MD"
    Then every row in the results table has a facility name
    And every row in the results table has a release amount

  # ── Invariant 3 (Phase 3) ─────────────────────────────────────────────────
  # Updated for Option C: state dropdown is now a filter (no checkbox)

  Scenario: Invariant 3 — State dropdown filters results
    Given I am on the map page
    When I click the search panel tab
    Then the state filter dropdown is present with label "Filter to state (optional)"

  # ── Invariant 4 (Phase 3) ─────────────────────────────────────────────────

  Scenario: Invariant 4 — Correct panel labels
    Given I am on the map page
    Then no element with text "Quick Search" exists in the DOM
    And the search panel label is "Search Chemical Releases by Location"

  # ── Invariant 7 (Phase 3) ─────────────────────────────────────────────────

  Scenario: Invariant 7 — Latest year label visible on map contents panel
    Given I am on the map page
    Then the latest year toggle label contains "(latest year)"

  # ── Invariant 8 (Phase 3) ─────────────────────────────────────────────────

  Scenario: Invariant 8 — Release quantities are comma-formatted
    Given I am on the map page
    When I perform a search for "LEAD COMPOUNDS" near "Sparrows Point, MD"
    Then all visible release amounts contain a comma or dash

  # ── Invariant 9 (Phase 3) ─────────────────────────────────────────────────

  Scenario: Invariant 9 — Facility popup has close link at bottom
    Given I am on the map page
    When I perform a search for "LEAD COMPOUNDS" near "Sparrows Point, MD"
    And I click on the first result in the results table
    Then the close link at the bottom of the popup is present

  # ── Invariant 5 (Phase 5 — Demographics) ─────────────────────────────────
  # Full spec: TOXMAP_ACCEPTANCE_TESTS.md Feature 8 §Invariant 5
  # UCD 2011 finding: mouse-over-only legend values were unusable
  Scenario: Invariant 5 — Demographic legend values visible without mouse interaction
    Given I am on the map page
    When I open the "US Census & Health Data" panel
    And I select "Population" > "% Under 18" > "Census 2000"
    Then the legend is visible on screen
    And the legend shows at least 3 color-range entries
    And each legend entry has a visible numeric value without hovering
    And each legend entry includes the unit "%"

  # ── Invariant 10 (Phase 5 — Demographics) ────────────────────────────────
  # Full spec: TOXMAP_ACCEPTANCE_TESTS.md Feature 8 §Invariant 10
  # UCD 2011 §"Explanation of Mortality Categories": users assumed causation
  Scenario: Invariant 10 — Co-occurrence disclaimer appears only on mortality tabs
    Given I am on the map page
    When I open the "US Census & Health Data" panel
    And I select "Mortality" > "Cancer Mortality" > "Female" > "Census 2000"
    Then the text "Correlation does not imply causation" is visible
    When I switch to the "Population" tab in the demographic panel
    Then the text "Correlation does not imply causation" is NOT visible
    When I switch to "Income" tab in the demographic panel
    Then the text "Correlation does not imply causation" is NOT visible

  # ── Invariant 6 (Phase 4 — Superfund) ────────────────────────────────────

  Scenario: Invariant 6 — Distinct TRI circle vs Superfund diamond icons
    Given I am on the map page
    Then the Superfund layer toggle is present
    And the TRI layer toggle is present
    When I select the "Superfund" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    Then the results sidebar shows "AVTEX FIBERS INC"
    When I click on "AVTEX FIBERS INC" in the Superfund results
    Then the Superfund detail panel opens
    And the TRI facility detail panel is not shown

  # ── Superfund Markers Regression (React StrictMode) ──────────────────────
  # Regression test for: useSuperfundViewport hasFetchedRef bug
  # The bug: React StrictMode aborted the first fetch but the hook skipped the
  # retry because hasFetchedRef was set before the fetch completed.
  # This test ensures Superfund diamonds appear on initial page load.

  Scenario: Regression — Superfund markers visible on initial page load
    Given I am on the map page
    Then the Superfund layer is visible on the map
    And the Superfund in-view count is greater than zero

  Scenario: Regression — Superfund markers visible after search
    Given I am on the map page
    When I select the "Superfund" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    Then the Superfund layer is visible on the map
    And the results sidebar shows "AVTEX FIBERS INC"

  # ── TRI Circle Markers Regression (Browse Mode) ──────────────────────────
  # Regression test for: TRI browse mode 500-mile radius bug
  # The bug: Browse mode called /api/v1/facilities with radius_miles=500,
  # which only returned facilities within 500 miles of Kansas (US center).
  # Now uses /api/v1/facilities/browse to fetch ALL facilities.
  # This test ensures TRI circles appear on initial page load.

  Scenario: Regression — TRI circles visible on initial page load
    Given I am on the map page
    Then the TRI layer is visible on the map
    And the TRI in-view count is greater than zero

  Scenario: Regression — TRI circles visible after search
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    Then the TRI layer is visible on the map
    And the results sidebar shows at least one facility

  Scenario: Regression — TRI layer toggle hides and shows circles
    Given I am on the map page
    Then the TRI layer is visible on the map
    When I toggle the TRI layer off
    Then the TRI layer is hidden on the map
    When I toggle the TRI layer on
    Then the TRI layer is visible on the map

  # ── UCD-17: Superfund 3-Way Status Symbols (DEF-001 fix) ─────────────────
  # Regression test for: DEF-001 Superfund status symbols missing 3-way distinction
  # Original TOXMAP used: filled square (NPL Final), diamond (Proposed), X-square (Deleted)
  # Seed data includes all 3 status types: NPL, Proposed, Deleted
  # This test ensures the legend shows all 3 distinct status symbols.

  Scenario: UCD-17 — Legend shows 3 distinct Superfund status symbols
    Given I am on the map page
    Then the Superfund layer toggle is present
    And the Superfund legend shows "NPL (Final)" entry with a square icon
    And the Superfund legend shows "Proposed" entry with a diamond icon
    And the Superfund legend shows "Deleted" entry with an X-square icon

  Scenario: UCD-17 — All 3 Superfund status types present in seed data
    Given I am on the map page
    Then the Superfund in-view count is greater than or equal to 4

  # ── Regression: Both Dataset Option (Fig 2015-4) ─────────────────────────
  # Regression test for: "Both" option missing in dataset selector
  # The original TOXMAP had TRI + Superfund combined search (Fig 2015-4).
  # This test ensures the "Both" radio button exists and is the default.

  Scenario: Regression — Both dataset radio button is present and default
    Given I am on the map page
    When I click on the Search tab
    Then the "Both" dataset radio button is selected by default
    And the "TRI" dataset radio button is present
    And the "Superfund" dataset radio button is present

  Scenario: Regression — Both dataset shows combined TRI and Superfund results
    Given I am on the map page
    When I select the "Both" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    Then the results sidebar shows TRI and Superfund sections
    And the TRI section header is visible
    And the Superfund section header is visible

  Scenario: Regression — Both dataset fetches TRI facilities
    Given I am on the map page
    When I select the "Both" dataset
    And I type "Sparrows Point, MD" into the location field
    And I click "Search"
    Then the TRI layer is visible on the map
    And the results sidebar shows at least one facility

  Scenario: Regression — Both dataset fetches Superfund sites
    Given I am on the map page
    When I select the "Both" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    Then the Superfund layer is visible on the map
    And the results sidebar shows "AVTEX FIBERS INC"

  # ── Regression: Both Mode Drawer Selection ───────────────────────────────
  # Regression test for: clicking Superfund result in "Both" mode opened
  # the wrong drawer (TRI drawer instead of Superfund drawer).
  # Root cause: handleOpenDetail checked dataset instead of result type.

  Scenario: Regression — Both mode: clicking TRI result opens TRI drawer
    Given I am on the map page
    When I select the "Both" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    Then the TRI section header is visible
    When I click on "FRONT ROYAL PLASTICS INC" in the TRI results
    Then the TRI facility detail drawer opens
    And the Superfund detail panel is not shown

  Scenario: Regression — Both mode: clicking Superfund result opens Superfund drawer
    Given I am on the map page
    When I select the "Both" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    Then the Superfund section header is visible
    When I click on "AVTEX FIBERS INC" in the Superfund results
    Then the Superfund detail panel opens
    And the TRI facility detail panel is not shown

  # ── Regression: US Zip Code Geocoding ────────────────────────────────────
  # Regression test for: US zip codes geocoded to Mexico instead of the US.
  # Root cause: Photon is a global geocoder; "22630" matched a Mexican location.
  # Fix: Append ", USA" to 5-digit zip code queries to bias towards US results.

  Scenario: Regression — US zip code geocodes to USA, not Mexico
    Given I am on the map page
    When I type "22630" into the location field
    And I click "Search"
    Then the map is centered in the United States
    And the map is NOT centered in Mexico

  Scenario: Regression — US zip code with ZIP+4 format geocodes to USA
    Given I am on the map page
    When I type "22630-1234" into the location field
    And I click "Search"
    Then the map is centered in the United States

  # ── Regression: Results Count Stability (7.BUG.1) ────────────────────────
  # Regression test for: results count changed from 6→7 when scrolling map.
  # Root cause: triSearchResults used viewport-filtered facilities.
  # Fix: Always use triAllResults (API radius constraint is sufficient).

  Scenario: Regression — Results count remains stable when scrolling map
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    Then the results table shows a count
    When I scroll the map
    Then the results count remains unchanged

  # ── Regression: TRI Hover Tooltip (7.BUG.2, 7.BUG.3) ─────────────────────
  # Regression test for: hovering TRI result did not show tooltip on map.
  # Fix: Added Popup component for highlighted facilities.

  Scenario: Regression — Hovering TRI result shows tooltip on map
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    And I hover over the first TRI result row
    Then a tooltip popup appears on the map

  Scenario: Regression — Hovering selected TRI facility does not show duplicate popup
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    And I click on the first TRI result row
    Then the TRI facility detail drawer opens
    When I hover over the first TRI result row
    Then only one popup is visible on the map

  # ── Regression: Superfund Hover Parity (7.BUG.4) ─────────────────────────
  # Regression test for: Superfund results did not zoom/tooltip like TRI.
  # Fix: Added Superfund-specific zoom useEffect and Popup component.

  Scenario: Regression — Hovering Superfund result zooms map and shows tooltip
    Given I am on the map page
    When I select the "Superfund" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    And I hover over "AVTEX FIBERS INC" in the Superfund results
    Then the map zooms to the Superfund site
    And a tooltip popup appears on the map

  # ── Regression: Progressive TRI Circle Sizing (7.BUG.5) ──────────────────
  # Regression test for: all TRI circles were same size regardless of tier.
  # Fix: circle-radius now varies by color_band (red=full, green=smallest).

  Scenario: Regression — TRI circles have progressive sizing by release tier
    Given I am on the map page
    Then the TRI layer is visible on the map
    And red tier circles are larger than green tier circles

  Scenario: Regression — TRI legend shows proportional circle sizes
    Given I am on the map page
    Then the TRI legend shows smallest circle for "< 1,000 lbs" tier
    And the TRI legend shows largest circle for "≥ 100,000 lbs" tier

  # ── Regression: Superfund Viewport Count (7.BUG.7) ───────────────────────
  # Regression test for: Superfund "in view" count showed total (1,816) instead
  # of viewport-filtered count (e.g., 3 visible sites).
  # Fix: Added superfundInViewCount memo that filters by mapBbox.

  Scenario: Regression — Superfund "in view" count reflects visible sites only
    Given I am on the map page
    Then the Superfund layer toggle is present
    And the Superfund in-view count is less than total Superfund sites

  # ── Regression: Results Table Scroll (7.BUG.8) ───────────────────────────
  # Regression test for: Results table limited to 10 items; users couldn't
  # access remaining results. Fix: Removed .slice(0, 10) limitation.

  Scenario: Regression — All search results are accessible by scrolling
    Given I am on the map page
    When I type "Richland, WA" into the location field
    And I click "Search"
    Then all TRI results are rendered in the table
    And all Superfund results are rendered in the table

  # ── Regression: Map Filtering (7.BUG.9) ──────────────────────────────────
  # Regression test for: Map displayed ALL facilities regardless of search
  # filters (CONUS, chemical). Results table was correct but map was not.
  # Fix: Added triFacilitiesForMap memo; map now receives filtered data.

  Scenario: Regression — Map shows only facilities matching search filters
    Given I am on the map page
    When I type "LEAD" into the chemical field
    And I select "Continental US" from the state filter
    And I click "Search"
    Then the map shows only Continental US facilities
    And no facilities are visible in Alaska on the map

  # ── ADR-007: Chemical Family Expansion Regressions ───────────────────────

  # Regression test for 7.BUG.10: exact_match not narrowing results.
  # When user clicks "Search exact term only", search should return ONLY
  # facilities reporting under that exact chemical name, not the family.

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

  # Regression test for 7.BUG.11: SearchPanel scroll broken in small windows.

  Scenario: Regression — SearchPanel is scrollable in small viewport
    Given I resize the viewport to 800x400
    And I am on the map page
    When I click the search panel tab
    Then the search form is fully visible
    And the search panel content is scrollable

  # Regression test for 7.BUG.12: Chemical family banner padding.

  Scenario: Regression — Chemical family banner has consistent padding
    Given I am on the map page
    When I type "LEAD" into the chemical field
    And I type "Baltimore, MD" into the location field
    And I click "Search"
    Then the chemical family banner has horizontal padding

  # Regression test for 7.BUG.13: Sidebar resize functionality.

  Scenario: Regression — Sidebar can be resized by dragging
    Given I am on the map page
    Then the sidebar resize handle is present
    When I drag the sidebar resize handle 100 pixels to the right
    Then the sidebar width has increased
    And the map camera padding has adjusted

  # Regression test for 7.BUG.15: MERCURY family not expanding.
  # The bug: MERCURY family only had 1 member due to whitespace mismatch
  # in seed script. Fix: Added whitespace normalization to seed script.

  Scenario: Regression — MERCURY family shows expansion banner
    Given I am on the map page
    When I type "MERCURY" into the chemical field
    And I click "Search"
    Then the chemical family banner is visible
    And the banner mentions "MERCURY"

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
  # Regression tests for: Geocoding fidelity gap (Google Maps vs Photon).
  # Root cause: First-result acceptance without scoring; no viewport bias.
  # Fix: Multi-candidate scoring with confidence levels and UI feedback.

  Scenario: Regression — Full address geocodes with high confidence badge
    Given I am on the map page
    When I type "100 Mill Rd, Port Townsend, WA" into the location field
    And I click "Search"
    Then the resolved location panel is visible
    And the geocode confidence badge shows "High" or "Exact"
    And the resolved address contains "Port Townsend"
    And the map is centered near Port Townsend, WA

  Scenario: Regression — Partial address shows approximate confidence warning
    Given I am on the map page
    When I type "100 Mill Rd" into the location field
    And I click "Search"
    Then the resolved location panel is visible
    And the geocode confidence badge shows "Approximate" or "Low"
    And the approximate location warning is visible

  Scenario: Regression — Geocoding uses viewport bias for ambiguous queries
    Given I am on the map page
    And the map is zoomed to Port Townsend, WA area
    When I type "Mill Road" into the location field
    And I click "Search"
    Then the resolved address is closer to Port Townsend than to other states

  Scenario: Regression — Resolved location shows canonical address from Photon
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I click "Search"
    Then the resolved location panel is visible
    And the resolved address contains "MD" or "Maryland"
    And the resolved address is not equal to "Sparrows Point, MD"

  Scenario: Regression — Address with typo shows low confidence
    Given I am on the map page
    When I type "100 Mill Rd Port Townsed" into the location field
    And I click "Search"
    Then the resolved location panel is visible
    And the geocode confidence badge is NOT "Exact"

  # ── 6.UX.1: Superfund Panel UI Improvements ──────────────────────────────
  # Regression tests for: EPA ID link + CAS number removal.
  # Fix: (1) EPA ID now links to EPA Site Progress Profile via SEMS site_id
  #      (2) CAS numbers removed from contaminants list for cleaner UI

  @regression @6UX1
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

  @regression @6UX1
  Scenario: Regression — Superfund contaminants do NOT show CAS numbers
    Given I am on the map page
    When I select the "Superfund" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    When I click on "AVTEX FIBERS INC" in the Superfund results
    Then the Superfund detail panel opens
    And the contaminants list is visible
    And no contaminant row shows a CAS number pattern

  # ── Regression: 15-Year Trend Chart Data Integrity (7.BUG.27) ────────────
  # CRITICAL regression tests for: 15-year trend chart data loss.
  # Root cause: Per-chemical releases were OVERWRITTEN instead of SUMMED.
  # For Arlington Plating 2017: 6 chemicals totaling 12,916 lbs, but chart
  # showed only 12,636 lbs (the last chemical processed).
  # Fix: Changed dataByYear.set(year, lbs) to dataByYear.set(year, currentTotal + lbs)

  @regression @7BUG27 @critical
  Scenario: Regression — 15-year trend aggregates all chemicals per year
    Given I am on the map page
    When I type "Palatine, IL" into the location field
    And I click "Search"
    And I click on "ARLINGTON PLATING ACQUISITION CO" in the results
    Then the TRI facility detail drawer opens
    When I click the "15-Year Trend" tab
    Then the 15-year trend chart is visible
    And the trend chart Y-axis maximum is greater than 12900
    # If aggregation is broken, max would be ~12,636 (1-BROMOPROPANE only)
    # Correct aggregation: 12,916 lbs (sum of all 6 chemicals)

  @regression @7BUG27
  Scenario: Regression — 15-year trend shows full year range without gaps
    Given I am on the map page
    When I type "Palatine, IL" into the location field
    And I click "Search"
    And I click on "ARLINGTON PLATING ACQUISITION CO" in the results
    Then the TRI facility detail drawer opens
    When I click the "15-Year Trend" tab
    Then the 15-year trend chart is visible
    And the trend chart X-axis shows 15 consecutive years

  @regression @7BUG27
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
    # 15-year range ending at selected year: 2020 - 14 = 2006

  @regression @7BUG27
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

  # ── Regression: 7.BUG.28 — Top Chemicals Table Structure ──────────────────────
  # CRITICAL UI FIX: Top Chemicals table must match Fig 11 in SCREEN_CATALOG.md:
  # - Numbered ranks: 1), 2), 3), 4), 5)
  # - Column header: "Release Amount (lbs./all years)"
  # - "Other chemicals" row when facility has > 5 chemicals
  # - TOTAL footer row showing facility total

  @regression @7BUG28
  Scenario: Regression — Top Chemicals table shows numbered ranks
    Given I am on the map page
    When I perform a search for "BENZENE" near "Houston, TX"
    And I click on the first result in the results table
    Then the facility detail panel opens
    And the Top Chemicals tab shows numbered chemical ranks

  @regression @7BUG28
  Scenario: Regression — Top Chemicals table shows all-years header
    Given I am on the map page
    When I perform a search for "BENZENE" near "Houston, TX"
    And I click on the first result in the results table
    Then the facility detail panel opens
    And the Top Chemicals table shows "Release Amount (lbs./all years)" header

  @regression @7BUG28
  Scenario: Regression — Top Chemicals table shows TOTAL row
    Given I am on the map page
    When I perform a search for "BENZENE" near "Houston, TX"
    And I click on the first result in the results table
    Then the facility detail panel opens
    And the Top Chemicals table shows a TOTAL footer row

  @regression @7BUG28
  Scenario: Regression — Top Chemicals table shows Other chemicals row when applicable
    Given I am on the map page
    When I perform a search for "BENZENE" near "Houston, TX"
    And I click on the first result in the results table
    Then the facility detail panel opens
    And the Top Chemicals table shows "Other chemicals" row when applicable

  # ── Regression: 7.BUG.29 — All-Years Aggregation ──────────────────────────────
  # CRITICAL DATA FIX: When searching without a year filter ("All years"),
  # release amounts must be aggregated across ALL reporting years, not just
  # the latest year. This was a backend bug where _resolve_year() converted
  # year=None to the latest year instead of returning None for aggregation.
  #
  # Test data: ExxonMobil has releases in 2006, 2007, 2008.
  # - Single year (2008): ~28,400 lbs
  # - All years sum: ~95,200 lbs

  @regression @7BUG29
  Scenario: Regression — All years search shows aggregated totals
    Given I am on the map page
    When I perform a search for "BENZENE" near "Baytown, TX"
    Then the results table shows "EXXONMOBIL" with release amount greater than 50000 lbs

  @regression @7BUG29
  Scenario: Regression — Facility detail shows all-years total
    Given I am on the map page
    When I perform a search for "BENZENE" near "Baytown, TX"
    And I click on "EXXONMOBIL" in the results
    Then the facility detail panel opens
    And the facility detail total matches the aggregated all-years amount

  # ── Regression: 7.BUG.30 — Facility Drawer Resize Handle ───────────────────────
  # UI FIX: FacilityDrawer now has a resize handle for horizontal adjustment.
  # Fix: Added resize handle to left edge using same pattern as Sidebar.tsx.

  @regression @7BUG30
  Scenario: Regression — Facility drawer has resize handle
    Given I am on the map page
    When I perform a search for "BENZENE" near "Houston, TX"
    And I click on the first result in the results table
    Then the facility detail panel opens
    And the facility drawer resize handle is present

  @regression @7BUG30
  Scenario: Regression — Facility drawer can be resized by dragging
    Given I am on the map page
    When I perform a search for "BENZENE" near "Houston, TX"
    And I click on the first result in the results table
    Then the facility detail panel opens
    When I drag the facility drawer resize handle 100 pixels to the left
    Then the facility drawer width has increased

  # ── Regression: 7.BUG.31 — Superfund Drawer Resize Handle Parity ───────────────
  # UI FIX: SuperfundDrawer now has resize handle parity with FacilityDrawer.
  # Root cause: After 7.BUG.30 added resize to FacilityDrawer, SuperfundDrawer
  # was still missing the same functionality — inconsistent UX.
  # Fix: Applied identical resize pattern from FacilityDrawer to SuperfundDrawer.

  @regression @7BUG31
  Scenario: Regression — Superfund drawer has resize handle
    Given I am on the map page
    When I select the "Superfund" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    And I click on "AVTEX FIBERS INC" in the Superfund results
    Then the Superfund detail panel opens
    And the superfund drawer resize handle is present

  @regression @7BUG31
  Scenario: Regression — Superfund drawer can be resized by dragging
    Given I am on the map page
    When I select the "Superfund" dataset
    And I type "Front Royal, VA" into the location field
    And I click "Search"
    And I click on "AVTEX FIBERS INC" in the Superfund results
    Then the Superfund detail panel opens
    When I drag the superfund drawer resize handle 100 pixels to the left
    Then the superfund drawer width has increased
