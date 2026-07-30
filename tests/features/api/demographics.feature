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
