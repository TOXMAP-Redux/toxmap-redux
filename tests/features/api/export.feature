Feature: CSV Export

  Background:
    Given the seed database is loaded

  Scenario: CSV export returns CSV content type
    When I GET "/api/v1/export/csv?lat=39.2197&lon=-76.4785&radius_miles=10&year=2008"
    Then the response status is 200
    And the response content type is "text/csv"
    And the response body contains "tri_facility_id"

  Scenario: Map metadata export
    When I GET "/api/v1/export/map-metadata?lat=39.2197&lon=-76.4785&radius_miles=10"
    Then the response status is 200
    And the response field "export_filename" is not null
