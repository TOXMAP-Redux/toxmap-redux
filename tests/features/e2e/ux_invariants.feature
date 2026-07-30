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

  # ── Invariant 10 (Phase 5 — Demographics) ────────────────────────────────
  @skip
  Scenario: Invariant 10 — Co-occurrence disclaimer on mortality tab only
    Given I open the TOXMAP application
    Then a demographics invariant stub exists

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

