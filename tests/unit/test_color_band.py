"""Unit tests for app.domain.color_band.

Layer 1 — pure function tests, no I/O.
"""

import pytest

from app.domain.color_band import assign_color_band, get_thresholds


class TestAssignColorBand:
    """Tests for the assign_color_band function."""

    # --- Boundary value tests ---

    @pytest.mark.parametrize(
        "total_lbs,expected",
        [
            # Green tier: < 1,000 lbs
            (None, "green"),
            (0, "green"),
            (0.0, "green"),
            (999, "green"),
            (999.99, "green"),
            # Yellow tier: 1,000 – 9,999 lbs
            (1_000, "yellow"),
            (1_000.0, "yellow"),
            (5_000, "yellow"),
            (9_999, "yellow"),
            (9_999.99, "yellow"),
            # Orange tier: 10,000 – 99,999 lbs
            (10_000, "orange"),
            (10_000.0, "orange"),
            (50_000, "orange"),
            (99_999, "orange"),
            (99_999.99, "orange"),
            # Red tier: ≥ 100,000 lbs
            (100_000, "red"),
            (100_000.0, "red"),
            (500_000, "red"),
            (1_000_000, "red"),
            (999_999_999, "red"),
        ],
    )
    def test_color_band_boundaries(self, total_lbs: float | None, expected: str) -> None:
        """Verify color band assignment at all tier boundaries."""
        assert assign_color_band(total_lbs) == expected

    # --- Seed data regression tests ---

    def test_t01_bethlehem_steel_copper(self) -> None:
        """T-01: Bethlehem Steel copper release = 8,205 lbs → yellow."""
        # From TOXMAP_TEST_SEED_DATA.md §9: facility 89319BHPCP7MILE, copper to land
        assert assign_color_band(8_205.0) == "yellow"

    def test_facility_with_high_release(self) -> None:
        """Large release → red tier."""
        # Example: 150,000 lbs total release
        assert assign_color_band(150_000) == "red"

    def test_facility_with_zero_release(self) -> None:
        """Facility reported zero releases (different from unreported)."""
        assert assign_color_band(0) == "green"

    # --- Edge cases ---

    def test_negative_value_treated_as_green(self) -> None:
        """Negative values (data errors) fall into green tier."""
        # Negative release doesn't make physical sense but shouldn't crash
        assert assign_color_band(-100) == "green"

    def test_float_precision(self) -> None:
        """Floating point values near boundaries are handled correctly."""
        # Just under yellow threshold
        assert assign_color_band(999.9999999) == "green"
        # At yellow threshold
        assert assign_color_band(1000.0000001) == "yellow"


class TestGetThresholds:
    """Tests for the get_thresholds function."""

    def test_returns_all_four_tiers(self) -> None:
        """Verify all four color tiers are present."""
        thresholds = get_thresholds()
        assert set(thresholds.keys()) == {"green", "yellow", "orange", "red"}

    def test_threshold_values(self) -> None:
        """Verify threshold values match API contract."""
        thresholds = get_thresholds()
        assert thresholds["green"] == 0
        assert thresholds["yellow"] == 1_000
        assert thresholds["orange"] == 10_000
        assert thresholds["red"] == 100_000

    def test_thresholds_are_ordered(self) -> None:
        """Thresholds should increase green < yellow < orange < red."""
        thresholds = get_thresholds()
        assert thresholds["green"] < thresholds["yellow"]
        assert thresholds["yellow"] < thresholds["orange"]
        assert thresholds["orange"] < thresholds["red"]
