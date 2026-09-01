"""Color band classification for TRI release quantities.

NLM TOXMAP used four color tiers to visualize facility release magnitudes.
This module implements the same classification logic.

Thresholds (from ADR-001 / TOXMAP_API_CONTRACT.md):
    - green:  < 1,000 lbs (or null/unknown)
    - yellow: 1,000 – 9,999 lbs
    - orange: 10,000 – 99,999 lbs
    - red:    ≥ 100,000 lbs
"""

from __future__ import annotations

from typing import Literal

ColorBand = Literal["green", "yellow", "orange", "red"]

# Thresholds in pounds — these are product decisions from NLM design
_THRESHOLD_RED = 100_000
_THRESHOLD_ORANGE = 10_000
_THRESHOLD_YELLOW = 1_000


def assign_color_band(total_lbs: float | None) -> ColorBand:
    """Map total release pounds to a NLM color band.

    Args:
        total_lbs: Total on-site release quantity in pounds.
            None means unknown or unreported.

    Returns:
        One of "green", "yellow", "orange", "red".

    Examples:
        >>> assign_color_band(None)
        'green'
        >>> assign_color_band(0)
        'green'
        >>> assign_color_band(999)
        'green'
        >>> assign_color_band(1_000)
        'yellow'
        >>> assign_color_band(10_000)
        'orange'
        >>> assign_color_band(100_000)
        'red'
    """
    if total_lbs is None:
        return "green"
    if total_lbs >= _THRESHOLD_RED:
        return "red"
    if total_lbs >= _THRESHOLD_ORANGE:
        return "orange"
    if total_lbs >= _THRESHOLD_YELLOW:
        return "yellow"
    return "green"


def get_thresholds() -> dict[ColorBand, float]:
    """Return color band thresholds for reference.

    Returns:
        Dict mapping color names to their minimum threshold in pounds.
        "green" has threshold 0 (anything below yellow).
    """
    return {
        "green": 0,
        "yellow": _THRESHOLD_YELLOW,
        "orange": _THRESHOLD_ORANGE,
        "red": _THRESHOLD_RED,
    }
