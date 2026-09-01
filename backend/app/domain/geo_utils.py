"""Geographic utilities for spatial queries.

Pure functions for coordinate validation, unit conversion, and bounding box parsing.
No database or network I/O — fully unit-testable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import NamedTuple

logger = logging.getLogger(__name__)

# Conversion constant: 1 mile = 1609.344 meters (exact)
MILES_TO_METERS: float = 1609.344

# WGS84 coordinate bounds
_LAT_MIN = -90.0
_LAT_MAX = 90.0
_LON_MIN = -180.0
_LON_MAX = 180.0

# API constraint: maximum search radius
MAX_RADIUS_MILES: float = 500.0


class BBox(NamedTuple):
    """Bounding box in WGS84 coordinates (min_lon, min_lat, max_lon, max_lat)."""

    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    def contains(self, lon: float, lat: float) -> bool:
        """Check if a point is within this bounding box."""
        return (
            self.min_lon <= lon <= self.max_lon and self.min_lat <= lat <= self.max_lat
        )


@dataclass
class ValidationError:
    """Structured validation error for API response."""

    field: str
    message: str
    value: float | str | None


def miles_to_meters(miles: float) -> float:
    """Convert miles to meters.

    Args:
        miles: Distance in statute miles.

    Returns:
        Distance in meters.

    Examples:
        >>> miles_to_meters(1)
        1609.344
        >>> miles_to_meters(0)
        0.0
        >>> round(miles_to_meters(100), 2)
        160934.4
    """
    return miles * MILES_TO_METERS


def validate_lat(lat: float) -> ValidationError | None:
    """Validate latitude is within WGS84 bounds [-90, 90].

    Args:
        lat: Latitude in decimal degrees.

    Returns:
        ValidationError if invalid, None if valid.

    Examples:
        >>> validate_lat(0)
        >>> validate_lat(90)
        >>> validate_lat(91) is not None
        True
    """
    if not _LAT_MIN <= lat <= _LAT_MAX:
        return ValidationError(
            field="lat",
            message=f"Latitude must be between {_LAT_MIN} and {_LAT_MAX}",
            value=lat,
        )
    return None


def validate_lon(lon: float) -> ValidationError | None:
    """Validate longitude is within WGS84 bounds [-180, 180].

    Args:
        lon: Longitude in decimal degrees.

    Returns:
        ValidationError if invalid, None if valid.

    Examples:
        >>> validate_lon(0)
        >>> validate_lon(180)
        >>> validate_lon(181) is not None
        True
    """
    if not _LON_MIN <= lon <= _LON_MAX:
        return ValidationError(
            field="lon",
            message=f"Longitude must be between {_LON_MIN} and {_LON_MAX}",
            value=lon,
        )
    return None


def validate_radius(radius_miles: float, max_miles: float = MAX_RADIUS_MILES) -> ValidationError | None:
    """Validate search radius is positive and within maximum.

    Args:
        radius_miles: Search radius in miles.
        max_miles: Maximum allowed radius (default 500).

    Returns:
        ValidationError if invalid, None if valid.

    Examples:
        >>> validate_radius(50)
        >>> validate_radius(500)
        >>> validate_radius(501) is not None
        True
        >>> validate_radius(0) is not None
        True
        >>> validate_radius(-1) is not None
        True
    """
    if radius_miles <= 0:
        return ValidationError(
            field="radius_miles",
            message="Radius must be greater than 0",
            value=radius_miles,
        )
    if radius_miles > max_miles:
        return ValidationError(
            field="radius_miles",
            message=f"Radius must not exceed {max_miles} miles",
            value=radius_miles,
        )
    return None


def parse_bbox(bbox_str: str) -> BBox | None:
    """Parse a comma-separated bbox string into a BBox tuple.

    Expected format: "min_lon,min_lat,max_lon,max_lat"

    Args:
        bbox_str: Comma-separated string of four coordinates.

    Returns:
        BBox namedtuple if valid, None if invalid.

    Examples:
        >>> parse_bbox("-122.5,37.5,-122.0,38.0")
        BBox(min_lon=-122.5, min_lat=37.5, max_lon=-122.0, max_lat=38.0)
        >>> parse_bbox("invalid")
        >>> parse_bbox("1,2,3")
        >>> parse_bbox("")
    """
    if not bbox_str:
        return None

    parts = bbox_str.split(",")
    if len(parts) != 4:
        logger.warning("Invalid bbox format (expected 4 parts): %s", bbox_str)
        return None

    try:
        min_lon, min_lat, max_lon, max_lat = (float(p.strip()) for p in parts)
    except ValueError:
        logger.warning("Invalid bbox values (non-numeric): %s", bbox_str)
        return None

    # Validate coordinate ranges
    if not (_LON_MIN <= min_lon <= _LON_MAX and _LON_MIN <= max_lon <= _LON_MAX):
        logger.warning("Invalid bbox longitude values: %s", bbox_str)
        return None
    if not (_LAT_MIN <= min_lat <= _LAT_MAX and _LAT_MIN <= max_lat <= _LAT_MAX):
        logger.warning("Invalid bbox latitude values: %s", bbox_str)
        return None

    # Validate min < max
    if min_lon > max_lon or min_lat > max_lat:
        logger.warning("Invalid bbox (min > max): %s", bbox_str)
        return None

    return BBox(min_lon, min_lat, max_lon, max_lat)


def format_bbox(bbox: BBox) -> str:
    """Format a BBox as a comma-separated string.

    Args:
        bbox: BBox namedtuple.

    Returns:
        Comma-separated string "min_lon,min_lat,max_lon,max_lat".

    Examples:
        >>> format_bbox(BBox(-122.5, 37.5, -122.0, 38.0))
        '-122.5,37.5,-122.0,38.0'
    """
    return f"{bbox.min_lon},{bbox.min_lat},{bbox.max_lon},{bbox.max_lat}"
