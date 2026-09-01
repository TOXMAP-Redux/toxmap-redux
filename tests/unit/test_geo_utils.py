"""Unit tests for app.domain.geo_utils.

Layer 1 — pure function tests, no I/O.
"""

import pytest

from app.domain.geo_utils import (
    MILES_TO_METERS,
    MAX_RADIUS_MILES,
    BBox,
    format_bbox,
    miles_to_meters,
    parse_bbox,
    validate_lat,
    validate_lon,
    validate_radius,
)


class TestMilesToMeters:
    """Tests for miles_to_meters conversion."""

    def test_conversion_constant(self) -> None:
        """Verify the conversion constant is correct."""
        assert MILES_TO_METERS == 1609.344

    @pytest.mark.parametrize(
        "miles,expected_meters",
        [
            (0, 0.0),
            (1, 1609.344),
            (10, 16093.44),
            (100, 160934.4),
            (500, 804672.0),  # Max search radius
        ],
    )
    def test_conversion_values(self, miles: float, expected_meters: float) -> None:
        """Verify conversion for various distances."""
        assert miles_to_meters(miles) == pytest.approx(expected_meters)

    def test_fractional_miles(self) -> None:
        """Fractional miles are converted correctly."""
        # Half mile
        assert miles_to_meters(0.5) == pytest.approx(804.672)
        # Quarter mile
        assert miles_to_meters(0.25) == pytest.approx(402.336)


class TestValidateLat:
    """Tests for latitude validation."""

    @pytest.mark.parametrize(
        "lat",
        [
            0,
            45,
            -45,
            90,
            -90,
            89.999999,
            -89.999999,
        ],
    )
    def test_valid_latitudes(self, lat: float) -> None:
        """Valid latitudes return None (no error)."""
        assert validate_lat(lat) is None

    @pytest.mark.parametrize(
        "lat",
        [
            90.0001,
            -90.0001,
            91,
            -91,
            180,
            -180,
            1000,
        ],
    )
    def test_invalid_latitudes(self, lat: float) -> None:
        """Invalid latitudes return ValidationError."""
        error = validate_lat(lat)
        assert error is not None
        assert error.field == "lat"
        assert error.value == lat

    def test_boundary_values(self) -> None:
        """Exact boundary values are valid."""
        assert validate_lat(90) is None
        assert validate_lat(-90) is None


class TestValidateLon:
    """Tests for longitude validation."""

    @pytest.mark.parametrize(
        "lon",
        [
            0,
            90,
            -90,
            180,
            -180,
            179.999999,
            -179.999999,
        ],
    )
    def test_valid_longitudes(self, lon: float) -> None:
        """Valid longitudes return None (no error)."""
        assert validate_lon(lon) is None

    @pytest.mark.parametrize(
        "lon",
        [
            180.0001,
            -180.0001,
            181,
            -181,
            360,
            1000,
        ],
    )
    def test_invalid_longitudes(self, lon: float) -> None:
        """Invalid longitudes return ValidationError."""
        error = validate_lon(lon)
        assert error is not None
        assert error.field == "lon"
        assert error.value == lon


class TestValidateRadius:
    """Tests for radius validation."""

    def test_max_radius_constant(self) -> None:
        """Verify max radius constant is 500 miles."""
        assert MAX_RADIUS_MILES == 500.0

    @pytest.mark.parametrize(
        "radius",
        [
            0.1,
            1,
            50,
            100,
            499.99,
            500,
        ],
    )
    def test_valid_radii(self, radius: float) -> None:
        """Valid radii return None (no error)."""
        assert validate_radius(radius) is None

    @pytest.mark.parametrize(
        "radius",
        [
            0,
            -1,
            -100,
        ],
    )
    def test_non_positive_radii(self, radius: float) -> None:
        """Zero and negative radii are invalid."""
        error = validate_radius(radius)
        assert error is not None
        assert error.field == "radius_miles"

    @pytest.mark.parametrize(
        "radius",
        [
            500.0001,
            501,
            1000,
        ],
    )
    def test_exceeds_max_radius(self, radius: float) -> None:
        """Radii exceeding max are invalid."""
        error = validate_radius(radius)
        assert error is not None
        assert error.field == "radius_miles"

    def test_custom_max_radius(self) -> None:
        """Custom max_radius parameter works."""
        assert validate_radius(100, max_miles=50) is not None
        assert validate_radius(50, max_miles=100) is None


class TestParseBbox:
    """Tests for bounding box parsing."""

    def test_valid_bbox(self) -> None:
        """Valid bbox string is parsed correctly."""
        result = parse_bbox("-122.5,37.5,-122.0,38.0")
        assert result is not None
        assert result == BBox(-122.5, 37.5, -122.0, 38.0)

    def test_conus_bbox(self) -> None:
        """CONUS bounding box parses correctly."""
        # Approximate CONUS bounds
        result = parse_bbox("-125,24,-66,50")
        assert result is not None
        assert result.min_lon == -125
        assert result.min_lat == 24
        assert result.max_lon == -66
        assert result.max_lat == 50

    @pytest.mark.parametrize(
        "bbox_str",
        [
            "",
            "invalid",
            "1,2,3",  # Only 3 parts
            "1,2,3,4,5",  # 5 parts
            "a,b,c,d",  # Non-numeric
            "1.0,2.0,three,4.0",  # Mixed
        ],
    )
    def test_invalid_format(self, bbox_str: str) -> None:
        """Invalid format returns None."""
        assert parse_bbox(bbox_str) is None

    def test_out_of_range_longitude(self) -> None:
        """Longitude outside [-180, 180] returns None."""
        assert parse_bbox("181,0,182,1") is None
        assert parse_bbox("-181,0,-180,1") is None

    def test_out_of_range_latitude(self) -> None:
        """Latitude outside [-90, 90] returns None."""
        assert parse_bbox("0,91,1,92") is None
        assert parse_bbox("0,-91,1,-90") is None

    def test_min_greater_than_max(self) -> None:
        """Min > max returns None."""
        # min_lon > max_lon
        assert parse_bbox("10,0,5,1") is None
        # min_lat > max_lat
        assert parse_bbox("0,10,1,5") is None

    def test_whitespace_handling(self) -> None:
        """Whitespace around values is trimmed."""
        result = parse_bbox(" -122.5 , 37.5 , -122.0 , 38.0 ")
        assert result is not None
        assert result == BBox(-122.5, 37.5, -122.0, 38.0)


class TestBBox:
    """Tests for BBox namedtuple."""

    def test_contains_point_inside(self) -> None:
        """Point inside bbox returns True."""
        bbox = BBox(-122.5, 37.5, -122.0, 38.0)
        assert bbox.contains(-122.25, 37.75) is True

    def test_contains_point_on_boundary(self) -> None:
        """Point on bbox boundary returns True."""
        bbox = BBox(-122.5, 37.5, -122.0, 38.0)
        assert bbox.contains(-122.5, 37.5) is True  # Corner
        assert bbox.contains(-122.0, 38.0) is True  # Opposite corner

    def test_contains_point_outside(self) -> None:
        """Point outside bbox returns False."""
        bbox = BBox(-122.5, 37.5, -122.0, 38.0)
        assert bbox.contains(-123.0, 37.75) is False  # West
        assert bbox.contains(-121.0, 37.75) is False  # East
        assert bbox.contains(-122.25, 37.0) is False  # South
        assert bbox.contains(-122.25, 39.0) is False  # North


class TestFormatBbox:
    """Tests for bbox formatting."""

    def test_round_trip(self) -> None:
        """Parse and format should round-trip."""
        original = "-122.5,37.5,-122.0,38.0"
        parsed = parse_bbox(original)
        assert parsed is not None
        formatted = format_bbox(parsed)
        assert formatted == original

    def test_format_values(self) -> None:
        """Format produces expected string."""
        bbox = BBox(-122.5, 37.5, -122.0, 38.0)
        assert format_bbox(bbox) == "-122.5,37.5,-122.0,38.0"
