# UCD 2011 Task Scenarios
# Full spec: docs/testing/TOXMAP_ACCEPTANCE_TESTS.md Feature 7
# Phase 3: T-01, T-03, T-08 implemented
# Phase 4: T-02, T-04 (Superfund overlay required)
# Phase 5: T-05, T-06, T-09 (Demographics overlay required)
@e2e
Feature: UCD 2011 Task Scenarios

  Background:
    Given the application is running at "http://localhost:3000"
    And the seed database is loaded

  # ── T-01 (Phase 3) ────────────────────────────────────────────────────────
  @phase-3
  Scenario: T-01 Lead compounds near Sparrows Point MD
    Given I am on the map page
    When I type "Sparrows Point, MD" into the location field
    And I type "LEAD COMPOUNDS" into the chemical field
    And I select year "2008"
    And I click Search
    Then the results sidebar shows "BETHLEHEM STEEL CORP - SPARROWS POINT"
    When I click on "BETHLEHEM STEEL CORP - SPARROWS POINT" in the results
    Then the facility detail panel opens
    And the detail panel shows "12,485 lbs"
    And the release quantities are formatted with commas

  # ── T-03 (Phase 3) ────────────────────────────────────────────────────────
  # Source: TOXMAP_TEST_SEED_DATA.md §2.1 — ROBINSON NEVADA MINING CO in Ruth, NV
  # Acceptance test uses "Ruth, NV" per seed.sql facility location
  @phase-3
  Scenario: T-03 Copper releases near Ruth Nevada
    Given I am on the map page
    When I type "Ruth, NV 89319" into the location field
    And I type "COPPER" into the chemical field
    And I select year "2008"
    And I click Search
    Then the results sidebar shows "ROBINSON NEVADA MINING CO"
    When I click on "ROBINSON NEVADA MINING CO" in the results
    Then the facility detail panel opens
    And the detail panel shows "8,205 lbs"

  # ── T-08 (Phase 3) ────────────────────────────────────────────────────────
  @phase-3
  Scenario: T-08 ATSDR ToxFAQ link opens in new tab preserving map state
    Given I am on the map page
    When I type "AMMONIA" into the chemical field
    And I select the chemical "AMMONIA" from autocomplete
    Then the ATSDR link is visible for the selected chemical
    And the ATSDR link opens in a new tab

  # ── T-02 (Phase 4 — Superfund overlay) ───────────────────────────────────
  @phase-4
  Scenario: T-02 Superfund chemical list accessible within 2 clicks
    Given I am on the map page
    When I select the "Superfund" dataset
    And I type "Front Royal, VA" into the location field
    And I click Search
    Then the results sidebar shows "AVTEX FIBERS INC"
    When I click on "AVTEX FIBERS INC" in the Superfund results
    Then the Superfund detail panel opens
    And the contaminants list is visible

  # ── T-04 (Phase 4 — Superfund overlay) ───────────────────────────────────
  @phase-4
  Scenario: T-04 Styrene Superfund site found near Front Royal VA
    Given I am on the map page
    When I select the "Superfund" dataset
    And I type "Front Royal, VA" into the location field
    And I click Search
    Then the results sidebar shows "AVTEX FIBERS INC"
    When I click on "AVTEX FIBERS INC" in the Superfund results
    Then the Superfund detail panel opens
    And the contaminants list contains "STYRENE"
    And the EPA site progress profile link is present

  # ── T-05 (Phase 5 — Demographics) ────────────────────────────────────────
  # Full spec: TOXMAP_ACCEPTANCE_TESTS.md Feature 7 §T-05
  # Note: Acceptance spec says Census 2000, but age layers are disabled for Census 2000 (API limitation).
  # Using Census 2010 as the available alternative per frontend/src/components/Demographics/CensusHealthPanel.tsx.
  @phase-5
  Scenario: T-05 TRI styrene sites and under-18 demographic overlay work together
    Given I am on the map page
    When I search for TRI facilities releasing "STYRENE" near "Front Royal, VA 22630" in year "2008"
    Then at least one TRI facility marker is visible on the map
    And the results sidebar shows TRI results without a simultaneous Map Contents panel
    When I open the "US Census & Health Data" panel
    And I select "Population" > "% Under 18" > "Census 2010"
    Then the map shows county-level color shading
    And the sidebar switches to show the demographic panel only
    And the TRI facility markers remain visible on the map
    And a legend is visible with inline percentage values and the unit "%"

  # ── T-06 (Phase 5 — Demographics) ────────────────────────────────────────
  # Full spec: TOXMAP_ACCEPTANCE_TESTS.md Feature 7 §T-06
  # Income layer is available for Census 2000 (unlike age layers).
  @phase-5
  Scenario: T-06 Income range overlay applied units shown and layer removable
    Given I am on the map page
    When I open the "US Census & Health Data" panel
    And I select "Income" > "Median Household Income" > "Census 2000"
    Then the map shows county-level color shading
    And the legend shows dollar values with the unit "$"
    And each legend range label includes a "$" symbol
    When I click "Clear layer" in the demographic panel
    Then the county color shading is removed from the map
    And the legend disappears

  # ── T-07 (Phase 3 — API verified; E2E optional) ───────────────────────────
  # Full spec: TOXMAP_ACCEPTANCE_TESTS.md Feature 7 §T-07
  # Source: TOXMAP_TEST_SEED_DATA.md §2.1 — BORDEN CHEMICALS (SC) 85,000 lbs, ENTERPRISE GAS (LA) 342,500 lbs
  # Note: T-07 is verified at API layer; E2E validates state filter and nationwide search UX.
  # With production data, the exact facilities/values may differ, so we test the behavior pattern.
  @phase-3 @api-verified
  Scenario: T-07 Chlorine search supports state filter and nationwide search
    Given I am on the map page
    When I search for "CHLORINE" with state filter "SC"
    Then the results show only SC facilities
    And the results summary shows TRI facilities count greater than 0
    When I clear the state filter
    And I click Search
    Then the results summary shows TRI facilities count greater than 0

  # ── T-09 (Phase 5 — Demographics) ────────────────────────────────────────
  # Full spec: TOXMAP_ACCEPTANCE_TESTS.md Feature 7 §T-09
  # Source: toxmap-usability-2011.md Task T-09, TOXMAP_TEST_SEED_DATA.md §2.1 (EXXONMOBIL, LYONDELLBASELL in Houston)
  # BLOCKED: Mortality tab is disabled pending data integration
  @phase-5 @skip @blocked-mortality
  Scenario: T-09 Benzene releases and cancer mortality overlay with disclaimer
    Given I am on the map page
    When I search for "BENZENE" near "Houston, TX 77002" in year "2008"
    Then at least two benzene TRI facility markers appear in the Houston area
    When I open the "US Census & Health Data" panel
    And I select "Mortality" > "Cancer Mortality" > "Female" > "Census 2000"
    Then the map shows cancer mortality choropleth shading
    And a co-occurrence disclaimer is visible reading "Correlation does not imply causation"
    When I switch to the "Population" tab in the demographic panel
    Then the co-occurrence disclaimer is NOT visible

  # ── T-09-ALT (Phase 5 — Demographics, alternate test while mortality blocked)
  # Validates demographic overlay functionality using Population tab.
  # Age layers require Census 2010 (disabled for Census 2000).
  @phase-5
  Scenario: Demographics overlay works with TRI facility search
    Given I am on the map page
    When I search for "BENZENE" near "Houston, TX 77002" in year "2008"
    Then at least two benzene TRI facility markers appear in the Houston area
    When I open the "US Census & Health Data" panel
    And I select "Population" > "% Under 18" > "Census 2010"
    Then the map shows county-level color shading
    And the demographic legend is visible

  # ── Nationwide Search Regression Tests ──────────────────────────────────────
  # Regression tests for the nationwide chemical search feature (no location required).
  # These catch the bug where Superfund sites matching a chemical were not shown
  # in nationwide search results because the /api/v1/superfund/browse endpoint
  # doesn't support chemical filtering — client-side filtering is required.
  @phase-6 @regression
  Scenario: Nationwide chemical search shows both TRI and Superfund results
    Given I am on the map page
    When I select the "Both" dataset
    And I type "LEAD COMPOUNDS" into the chemical field
    And I leave the location field empty
    And I click Search
    Then the results summary shows TRI facilities count greater than 0
    And the results summary shows Superfund sites count greater than 0

  @phase-6 @regression
  Scenario: Nationwide TRI-only chemical search excludes Superfund sites
    Given I am on the map page
    When I select the "TRI" dataset
    And I type "LEAD COMPOUNDS" into the chemical field
    And I leave the location field empty
    And I click Search
    Then the results summary shows TRI facilities count greater than 0
    And the results summary does not show "Superfund"

  @phase-6 @regression
  Scenario: Nationwide Superfund-only chemical search shows matching sites by contaminant
    Given I am on the map page
    When I select the "Superfund" dataset
    And I type "LEAD" into the chemical field
    And I leave the location field empty
    And I click Search
    Then the results summary shows Superfund sites count greater than 0
    And the results summary does not show "TRI"

  @phase-6 @regression
  Scenario: Nationwide chemical search zooms to US overview
    Given I am on the map page
    When I select the "Both" dataset
    And I type "COPPER" into the chemical field
    And I leave the location field empty
    And I click Search
    Then the map is zoomed to US continental view

  # ── State Filter Regression Tests ────────────────────────────────────────────
  # Tests for the "Filter to state (optional)" dropdown.
  # Default is "All" (all US states + territories).
  # "Continental US" filter excludes AK, HI, and territories (client-side filtering).
  #
  # NOTE: Full CONUS exclusion testing (verify AK/HI/territories are excluded)
  # requires seed data in non-CONUS locations. Current seed data is all CONUS.
  @phase-6 @regression
  Scenario: State filter default is "All" and includes all results
    Given I am on the map page
    When I click the search panel tab
    Then the state filter dropdown shows "All" as the selected option
    When I type "BENZENE" into the chemical field
    And I type "Houston, TX 77002" into the location field
    And I click Search
    Then the results sidebar shows at least one facility

  @phase-6 @regression
  Scenario: Continental US filter option is available and selectable
    Given I am on the map page
    When I click the search panel tab
    Then the state filter dropdown contains "Continental US" option
    When I select "Continental US" from the state filter
    And I type "BENZENE" into the chemical field
    And I type "Houston, TX" into the location field
    And I click Search
    Then the results sidebar shows at least one facility
    And all results are from continental US states

  @phase-6 @regression
  Scenario: Continental US filter excludes Alaska facilities
    Given I am on the map page
    When I click the search panel tab
    And I select "Continental US" from the state filter
    And I type "COPPER" into the chemical field
    And I click Search
    Then all results are from continental US states
    And no result shows "ALASKA MINING" in the facility name
