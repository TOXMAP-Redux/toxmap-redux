Feature: Demographics County Overlay

  Background:
    Given the seed database is loaded

  Scenario: County demographics for VA returns Warren County
    When I GET "/api/v1/demographics/county?state=VA"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And the response meta contains "units"
    And the FeatureCollection contains exactly 1 features
    And every feature has property "state_fips" = "51"

  Scenario: County demographics without state returns all counties
    # Regression test: state parameter must be optional for choropleth to
    # render when user selects a demographic layer without searching first.
    When I GET "/api/v1/demographics/county"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And the response meta contains "units"
    And the FeatureCollection contains at least 3 features

  Scenario: County demographics for TX returns Harris County
    When I GET "/api/v1/demographics/county?state=TX"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And the FeatureCollection contains exactly 1 features
    And every feature has property "state_fips" = "48"

  Scenario: County demographics for non-existent state returns empty collection
    When I GET "/api/v1/demographics/county?state=ZZ"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And the FeatureCollection contains exactly 0 features

  @C-006
  Scenario: Filter demographics by census year
    # Verifies that the census_year parameter filters results correctly.
    # Test counties in seed.sql have census_year=2000.
    When I GET "/api/v1/demographics/county?state=VA&census_year=2000"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And the FeatureCollection contains exactly 1 features
    And the response meta has "census_year" = 2000

  @C-006
  Scenario: Census year filter excludes non-matching years
    # When querying for a year not in our seed data, no results should return.
    # Seed data has census_year=2000, so 2010 should return 0 features.
    When I GET "/api/v1/demographics/county?state=VA&census_year=2010"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And the FeatureCollection contains exactly 0 features
