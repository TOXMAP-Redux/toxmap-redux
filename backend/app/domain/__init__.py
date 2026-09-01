"""app/domain/__init__.py

Domain layer: pure business logic with zero I/O dependencies.

Modules in this package are imported by services and schemas but have no
database, network, or filesystem side effects. They are fully unit-testable
without mocking.
"""

from app.domain.color_band import assign_color_band
from app.domain.geo_utils import (
    MILES_TO_METERS,
    BBox,
    miles_to_meters,
    parse_bbox,
    validate_lat,
    validate_lon,
    validate_radius,
)

__all__ = [
    "assign_color_band",
    "MILES_TO_METERS",
    "BBox",
    "miles_to_meters",
    "parse_bbox",
    "validate_lat",
    "validate_lon",
    "validate_radius",
]
