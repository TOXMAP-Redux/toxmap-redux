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
