Feature: Facility Search by Location

  Background:
    Given the seed database is loaded

  Scenario: T-01 — Sparrows Point facility found by radius search
    When I search for facilities near lat 39.2197 lon -76.4785 within 10 miles for year 2008
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And facility "21219BTHLS3RD" is in the results
    And facility "21219BTHLS3RD" has total_release_lbs 12485.0
    And facility "21219BTHLS3RD" has color_band "orange"

  Scenario: T-03 — Robinson Nevada copper/land filter
    When I search for facilities near lat 39.2919 lon -115.0319 within 5 miles for year 2008 with chemical "copper" and medium "land"
    Then the response status is 200
    And facility "89319BHPCP7MILE" is in the results
    And facility "89319BHPCP7MILE" has total_release_lbs 8205.0

  Scenario: Validation — lat out of bounds
    When I GET "/api/v1/facilities?lat=999&lon=-76.4785&radius_miles=10"
    Then the response status is 422

  Scenario: Validation — radius too large
    When I GET "/api/v1/facilities?lat=39.2&lon=-76.4&radius_miles=5000"
    Then the response status is 422

  # ── Browse mode (no radius constraint) ──────────────────────────────────────

  Scenario: Browse endpoint returns all facilities without radius
    When I GET "/api/v1/facilities/browse"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And the response meta has "browse_all" = true
    And the FeatureCollection contains at least 1 features

  Scenario: Browse endpoint with year filter
    When I GET "/api/v1/facilities/browse?year=2008"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And facility "21219BTHLS3RD" is in the results
    And facility "89319BHPCP7MILE" is in the results

  Scenario: Browse endpoint with state filter
    When I GET "/api/v1/facilities/browse?state=MD"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And every feature has property "state_code" = "MD"

  Scenario: Browse endpoint with chemical filter
    When I GET "/api/v1/facilities/browse?chemical=copper"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And facility "89319BHPCP7MILE" is in the results

  # ── Color band tier coverage ────────────────────────────────────────────────

  Scenario: Color band green — facility with < 1,000 lbs release
    When I search for facilities near lat 38.9150 lon -78.1900 within 5 miles for year 2008
    Then the response status is 200
    And facility "22630SMRLG0001" is in the results
    And facility "22630SMRLG0001" has total_release_lbs 450.0
    And facility "22630SMRLG0001" has color_band "green"

  Scenario: Color band yellow — facility with 1,000–9,999 lbs release
    When I search for facilities near lat 39.2919 lon -115.0319 within 5 miles for year 2008
    Then the response status is 200
    And facility "89319BHPCP7MILE" is in the results
    And facility "89319BHPCP7MILE" has total_release_lbs 8205.0
    And facility "89319BHPCP7MILE" has color_band "yellow"

  Scenario: Color band orange — facility with 10,000–99,999 lbs release
    When I search for facilities near lat 39.2197 lon -76.4785 within 10 miles for year 2008
    Then the response status is 200
    And facility "21219BTHLS3RD" is in the results
    And facility "21219BTHLS3RD" has total_release_lbs 12485.0
    And facility "21219BTHLS3RD" has color_band "orange"

  Scenario: Color band red — facility with ≥ 100,000 lbs release
    When I search for facilities near lat 30.1944 lon -93.2044 within 10 miles for year 2008
    Then the response status is 200
    And facility "70663ENTGR0001" is in the results
    And facility "70663ENTGR0001" has total_release_lbs 342500.0
    And facility "70663ENTGR0001" has color_band "red"

  # ── ADR-007: Chemical Family Expansion ──────────────────────────────────────

  Scenario: Chemical family expansion — LEAD expands to include compounds
    When I GET "/api/v1/facilities/browse?chemical=lead"
    Then the response status is 200
    And the response meta has "search_expansion.expanded" = true
    And the response meta has "search_expansion.family_name" = "LEAD"
    And the response meta "search_expansion.searched_chemicals" contains "LEAD"
    And the response meta "search_expansion.searched_chemicals" contains "LEAD COMPOUNDS"

  Scenario: Chemical family expansion — exact_match=true disables expansion
    When I GET "/api/v1/facilities/browse?chemical=lead&exact_match=true"
    Then the response status is 200
    And the response meta does not have "search_expansion"

  Scenario: Chemical family expansion — exact_match returns fewer results than expanded
    When I GET "/api/v1/facilities/browse?chemical=lead"
    Then the response status is 200
    And I save the result count as "expanded_count"
    When I GET "/api/v1/facilities/browse?chemical=lead&exact_match=true"
    Then the response status is 200
    And the result count is less than "expanded_count"

  Scenario: Non-family chemical — no expansion metadata
    When I GET "/api/v1/facilities/browse?chemical=benzene"
    Then the response status is 200
    And the response meta does not have "search_expansion"

  Scenario: Chemical family expansion — radius search also expands
    When I search for facilities near lat 39.2197 lon -76.4785 within 50 miles for year 2008 with chemical "lead"
    Then the response status is 200
    And the response meta has "search_expansion.expanded" = true
    And the response meta has "search_expansion.family_name" = "LEAD"

  Scenario: Chemical family expansion — radius search with exact_match
    When I search for facilities near lat 39.2197 lon -76.4785 within 50 miles for year 2008 with chemical "lead" and exact_match true
    Then the response status is 200
    And the response meta does not have "search_expansion"

  # ── Regression: 7.BUG.15 — MERCURY family expansion ─────────────────────────
  # Regression test for: MERCURY family only had one member (MERCURY itself)
  # due to whitespace mismatch in seed script. Fix: Added whitespace normalization
  # and correct TRI chemical names like "MERCURY  AND MERCURY COMPOUNDS".

  Scenario: Regression 7.BUG.15 — MERCURY family expands to include compounds
    When I GET "/api/v1/facilities/browse?chemical=mercury"
    Then the response status is 200
    And the response meta has "search_expansion.expanded" = true
    And the response meta has "search_expansion.family_name" = "MERCURY"
    And the response meta "search_expansion.searched_chemicals" has at least 2 items

  Scenario: Regression 7.BUG.15 — CHROMIUM family expands
    When I GET "/api/v1/facilities/browse?chemical=chromium"
    Then the response status is 200
    And the response meta has "search_expansion.expanded" = true
    And the response meta has "search_expansion.family_name" = "CHROMIUM"

  Scenario: Regression 7.BUG.15 — ZINC family expands
    When I GET "/api/v1/facilities/browse?chemical=zinc+compounds"
    Then the response status is 200
    And the response meta has "search_expansion.expanded" = true
    And the response meta has "search_expansion.family_name" = "ZINC"

  Scenario: Regression 7.BUG.15 — All curated families have at least 2 members
    # Verifies that each family expands (i.e., has multiple members)
    When I GET "/api/v1/facilities/browse?chemical=nickel"
    Then the response meta has "search_expansion.expanded" = true
    When I GET "/api/v1/facilities/browse?chemical=arsenic"
    Then the response meta has "search_expansion.expanded" = true
    When I GET "/api/v1/facilities/browse?chemical=cadmium"
    Then the response meta has "search_expansion.expanded" = true
    When I GET "/api/v1/facilities/browse?chemical=manganese"
    Then the response meta has "search_expansion.expanded" = true
    When I GET "/api/v1/facilities/browse?chemical=copper"
    Then the response meta has "search_expansion.expanded" = true

  # ── Regression: 7.BUG.29 — All-years aggregation ────────────────────────────
  # CRITICAL FIX: When year parameter is omitted, total_release_lbs must be the
  # SUM across all reporting years, not just the latest year's value.
  #
  # Root cause: _resolve_year() was converting year=None to max(reporting_year),
  # causing queries to return single-year data instead of aggregated totals.
  #
  # Test data: ExxonMobil (77536EXXO00001) has benzene releases in seed.sql:
  #   2006: 35,600 lbs | 2007: 31,200 lbs | 2008: 28,400 lbs → Total: 95,200 lbs

  Scenario: Regression 7.BUG.29 — Browse without year aggregates ALL years
    When I GET "/api/v1/facilities/browse"
    Then the response status is 200
    And facility "77536EXXO00001" is in the results
    And facility "77536EXXO00001" has total_release_lbs 95200.0

  Scenario: Regression 7.BUG.29 — Browse with year=2008 returns ONLY that year
    When I GET "/api/v1/facilities/browse?year=2008"
    Then the response status is 200
    And facility "77536EXXO00001" is in the results
    And facility "77536EXXO00001" has total_release_lbs 28400.0

  Scenario: Regression 7.BUG.29 — Radius search without year aggregates ALL years
    When I search for facilities near lat 29.7424 lon -95.0215 within 5 miles without year filter
    Then the response status is 200
    And facility "77536EXXO00001" is in the results
    And facility "77536EXXO00001" has total_release_lbs 95200.0

  Scenario: Regression 7.BUG.29 — Radius search with year returns single year
    When I search for facilities near lat 29.7424 lon -95.0215 within 5 miles for year 2008
    Then the response status is 200
    And facility "77536EXXO00001" is in the results
    And facility "77536EXXO00001" has total_release_lbs 28400.0

  Scenario: Regression 7.BUG.29 — Multi-year facility: Bethlehem Steel all-years
    # Bethlehem Steel: 2006=15830 + 2007=14210 + 2008=12485 = 42525 lbs
    When I GET "/api/v1/facilities/browse?state=MD"
    Then the response status is 200
    And facility "21219BTHLS3RD" is in the results
    And facility "21219BTHLS3RD" has total_release_lbs 42525.0

  Scenario: Regression 7.BUG.29 — Multi-year facility: Robinson Nevada all-years
    # Robinson Nevada: 2006=9100 + 2007=7890 + 2008=8205 = 25195 lbs
    When I GET "/api/v1/facilities/browse?state=NV"
    Then the response status is 200
    And facility "89319BHPCP7MILE" is in the results
    And facility "89319BHPCP7MILE" has total_release_lbs 25195.0
