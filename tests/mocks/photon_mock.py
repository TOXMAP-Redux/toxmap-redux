# tests/mocks/photon_mock.py
#
# Mock Photon geocoding responses for CI stability.
#
# In CI, network calls to Photon (photon.komoot.io) can be flaky.
# This mock provides deterministic responses for known test locations.
#
# Usage:
#   Set TEST_MOCK_GEOCODING=1 environment variable to enable mocking.
#   The frontend will use these coordinates instead of calling Photon.
#

import json
from typing import Optional

# Known test locations with their expected coordinates
# These match the locations used in E2E test scenarios
MOCK_LOCATIONS = {
    # T-01: Lead near Sparrows Point MD
    "sparrows point, md": {
        "lat": 39.2197,
        "lon": -76.4785,
        "display_name": "Sparrows Point, Baltimore County, Maryland, USA",
    },
    "sparrows point": {
        "lat": 39.2197,
        "lon": -76.4785,
        "display_name": "Sparrows Point, Baltimore County, Maryland, USA",
    },
    
    # T-03: Copper near Ely NV
    "ruth, nv": {
        "lat": 39.2919,
        "lon": -115.0319,
        "display_name": "Ruth, White Pine County, Nevada, USA",
    },
    "ely, nv": {
        "lat": 39.2474,
        "lon": -114.8894,
        "display_name": "Ely, White Pine County, Nevada, USA",
    },
    
    # T-04: Superfund near Front Royal VA
    "front royal, va": {
        "lat": 38.9179,
        "lon": -78.1942,
        "display_name": "Front Royal, Warren County, Virginia, USA",
    },
    # ZIP code (US zip code geocoding fix)
    "22630": {
        "lat": 38.918,
        "lon": -78.194,
        "display_name": "22630, Front Royal, Warren County, Virginia, USA",
    },
    
    # T-09: Benzene near Houston TX
    "houston, tx": {
        "lat": 29.7604,
        "lon": -95.3698,
        "display_name": "Houston, Harris County, Texas, USA",
    },
    "houston": {
        "lat": 29.7604,
        "lon": -95.3698,
        "display_name": "Houston, Harris County, Texas, USA",
    },
    
    # T-07: Chlorine SC (Aiken area)
    "aiken, sc": {
        "lat": 33.5601,
        "lon": -81.7198,
        "display_name": "Aiken, Aiken County, South Carolina, USA",
    },
}


def mock_photon_response(query: str) -> Optional[dict]:
    """
    Return a mock Photon-style response for a known query.
    
    Args:
        query: Location search string (case-insensitive)
        
    Returns:
        Mock Photon GeoJSON response, or None if query not in mock data
    """
    normalized = query.lower().strip()
    
    if normalized in MOCK_LOCATIONS:
        loc = MOCK_LOCATIONS[normalized]
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [loc["lon"], loc["lat"]],
                    },
                    "properties": {
                        "name": loc["display_name"],
                        "osm_type": "relation",
                        "osm_id": 123456,
                        "country": "United States",
                        "countrycode": "US",
                        "type": "city",
                    },
                }
            ],
        }
    
    return None


def get_mock_coordinates(query: str) -> Optional[tuple]:
    """
    Get mock coordinates for a known location.
    
    Args:
        query: Location search string (case-insensitive)
        
    Returns:
        Tuple of (lat, lon), or None if query not in mock data
    """
    normalized = query.lower().strip()
    
    if normalized in MOCK_LOCATIONS:
        loc = MOCK_LOCATIONS[normalized]
        return (loc["lat"], loc["lon"])
    
    return None


# Export for use in conftest.py or step definitions
__all__ = ["MOCK_LOCATIONS", "mock_photon_response", "get_mock_coordinates"]
