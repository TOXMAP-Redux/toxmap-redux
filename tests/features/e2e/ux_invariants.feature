# UX Design Invariants
# Full spec: docs/testing/TOXMAP_ACCEPTANCE_TESTS.md Feature 8
#
# This file contains ONLY the 11 canonical UX invariants derived from UCD 2011.
# All regression tests have been moved to regression_tests.feature per F-P6-06.
#
# Phase mapping:
#   @phase-3 — Invariants 1, 2, 3, 4, 7, 8, 9 (core search/map)
#   @phase-4 — Invariant 6 (Superfund layer distinction)
#   @phase-5 — Invariants 5, 10, 11 (Demographics overlay)
@e2e
Feature: UX Design Invariants

  Background:
    Given the application is running at "http://localhost:3000"
    And the seed database is loaded

  # ══════════════════════════════════════════════════════════════════════════
  # Phase 3 — Core UX Invariants (Search & Map)
  # ══════════════════════════════════════════════════════════════════════════

  # ── Invariant 1 ───────────────────────────────────────────────────────────
  # UCD 2011 finding: Two panels visible simultaneously caused confusion
  # Study reference: toxmap-usability-2011.md §"Two Panels at Once"
  @phase-3
  Scenario: Invariant 1 — Map Contents and Search Results never visible simultaneously
    Given I am on the map page
    Then the map contents panel is visible
    And the search results panel is NOT visible
    When I perform a search for "BENZENE" near "Houston, TX"
    Then the search results panel is visible
    And the map contents panel is NOT visible

  # ── Invariant 2 ───────────────────────────────────────────────────────────
  # UCD 2011 finding: Empty placeholder rows in paginated results confused users
  # Study reference: toxmap-usability-2011.md §"Understanding the Table of Results"
  @phase-3
  Scenario: Invariant 2 — Search results table never contains empty placeholder rows
    Given I am on the map page
    When I perform a search for "LEAD COMPOUNDS" near "Sparrows Point, MD"
    Then every row in the results table has a facility name
    And every row in the results table has a release amount

  # ── Invariant 3 ───────────────────────────────────────────────────────────
  # UCD 2011 finding: Continental US should be default in state dropdown
  # Study reference: toxmap-usability-2011.md §"Browsing by Continental U.S. vs. City/State/Zip"
  # Updated for Option C: state dropdown is now a filter (no checkbox)
  @phase-3
  Scenario: Invariant 3 — State dropdown filters results
    Given I am on the map page
    When I click the search panel tab
    Then the state filter dropdown is present with label "Filter to state (optional)"

  # ── Invariant 4 ───────────────────────────────────────────────────────────
  # UCD 2011 finding: "Quick Search" and "Demographics" labels were confusing
  # Study reference: toxmap-usability-2011.md §"Quick Search Label" and §"Demographics Label"
  @phase-3
  Scenario: Invariant 4 — Correct panel labels
    Given I am on the map page
    Then no element with text "Quick Search" exists in the DOM
    And the search panel label is "Search Chemical Releases by Location"

  # ── Invariant 7 ───────────────────────────────────────────────────────────
  # UCD 2011 finding: Users didn't realize 2008 was the latest available year
  # Study reference: toxmap-usability-2011.md §"Why 2008 Data?"
  @phase-3
  Scenario: Invariant 7 — Latest year label visible on map contents panel
    Given I am on the map page
    Then the latest year toggle label contains "(latest year)"

  # ── Invariant 8 ───────────────────────────────────────────────────────────
  # UCD 2011 finding: Numbers without commas were hard to read
  # Study reference: toxmap-usability-2011.md §"Commas in Numbers"
  @phase-3
  Scenario: Invariant 8 — Release quantities are comma-formatted
    Given I am on the map page
    When I perform a search for "LEAD COMPOUNDS" near "Sparrows Point, MD"
    Then all visible release amounts contain a comma or dash

  # ── Invariant 9 ───────────────────────────────────────────────────────────
  # UCD 2011 finding: Close button on popups was often inaccessible
  # Study reference: toxmap-usability-2011.md §"Closing Facility Pop-Ups"
  @phase-3
  Scenario: Invariant 9 — Facility popup has close link at bottom
    Given I am on the map page
    When I perform a search for "LEAD COMPOUNDS" near "Sparrows Point, MD"
    And I click on the first result in the results table
    Then the close link at the bottom of the popup is present

  # ══════════════════════════════════════════════════════════════════════════
  # Phase 4 — Superfund Layer Distinction
  # ══════════════════════════════════════════════════════════════════════════

  # ── Invariant 6 ───────────────────────────────────────────────────────────
  # UCD 2011 finding: Users confused TRI circles with Superfund diamonds
  # Study reference: toxmap-usability-2011.md §"Marker Shape Distinction"
  @phase-4
  Scenario: Invariant 6 — Distinct TRI circle vs Superfund diamond icons
    Given I am on the map page
    Then the Superfund layer toggle is present
    And the TRI layer toggle is present
    When I select the "Superfund" dataset
    And I type "Front Royal, VA" into the location field
    And I click Search
    Then the results sidebar shows "AVTEX FIBERS INC"
    When I click on "AVTEX FIBERS INC" in the Superfund results
    Then the Superfund detail panel opens
    And the TRI facility detail panel is not shown

  # ══════════════════════════════════════════════════════════════════════════
  # Phase 5 — Demographics Overlay Invariants
  # ══════════════════════════════════════════════════════════════════════════

  # ── Invariant 5 ───────────────────────────────────────────────────────────
  # UCD 2011 finding: mouse-over-only legend values were unusable
  # Study reference: toxmap-usability-2011.md §"Legend Hover Only"
  @phase-5
  Scenario: Invariant 5 — Demographic legend values visible without mouse interaction
    Given I am on the map page
    When I open the "US Census & Health Data" panel
    And I select "Population" > "% Under 18" > "Census 2000"
    Then the legend is visible on screen
    And the legend shows at least 3 color-range entries
    And each legend entry has a visible numeric value without hovering
    And each legend entry includes the unit "%"

  # ── Invariant 10 ──────────────────────────────────────────────────────────
  # UCD 2011 finding: Users assumed causation from mortality overlay
  # Study reference: toxmap-usability-2011.md §"Explanation of Mortality Categories"
  @phase-5
  Scenario: Invariant 10 — Co-occurrence disclaimer appears only on mortality tabs
    Given I am on the map page
    When I open the "US Census & Health Data" panel
    And I select "Mortality" > "Cancer Mortality" > "Female" > "Census 2000"
    Then the text "Correlation does not imply causation" is visible
    When I switch to the "Population" tab in the demographic panel
    Then the text "Correlation does not imply causation" is NOT visible
    When I switch to "Income" tab in the demographic panel
    Then the text "Correlation does not imply causation" is NOT visible

  # ── Invariant 11 ──────────────────────────────────────────────────────────
  # UCD 2011 finding: Only one demographic layer visible at a time
  # Study reference: toxmap-usability-2011.md §"Analysis: TOXMAP 2015 Features"
  # Original TOXMAP allowed only one demographic overlay at a time,
  # preventing visual clutter when overlaying census data on TRI/Superfund maps.
  @phase-5
  Scenario: Invariant 11 — Only one demographic layer visible at a time
    Given I am on the map page
    When I enable the Census & Health Data panel
    And I select "Census 2020" from the census year dropdown
    And I select "Population" from the census category
    And I click "Total Population" sub-layer
    Then the demographics layer is visible on the map
    When I select "Income" from the census category
    And I click "Median Household Income" sub-layer
    Then the previous demographic layer is removed
    And only the income layer is visible
