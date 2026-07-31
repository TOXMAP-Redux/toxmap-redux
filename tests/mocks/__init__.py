# tests/mocks/__init__.py
#
# Mock modules for E2E and integration testing.
#

from .photon_mock import (
    MOCK_LOCATIONS,
    mock_photon_response,
    get_mock_coordinates,
)

__all__ = [
    "MOCK_LOCATIONS",
    "mock_photon_response",
    "get_mock_coordinates",
]
