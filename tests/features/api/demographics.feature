Feature: Demographics County Overlay

  Background:
    Given the seed database is loaded

  Scenario: County demographics for VA returns Warren County
    When I GET "/api/v1/demographics/county?state=VA"
    Then the response status is 200
    And the response is a GeoJSON FeatureCollection
    And the response meta contains "units"

  Scenario: Demographics missing state returns 422
    When I GET "/api/v1/demographics/county"
    Then the response status is 422
