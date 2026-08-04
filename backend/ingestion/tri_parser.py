"""TRI CSV column mapping and normalization utilities.

Story 1.2.1 — `TRI_COLUMN_MAP`, aggregation field lists, and helper functions.

AGENTS.md §10 data integrity rule: Never hardcode EPA column names outside this
map. EPA TRI CSV column names change between release years. All ingestion code
must use TRI_COLUMN_MAP to normalize raw header names to canonical names.

Column name source: EPA TRI Basic Data Files documentation (2022 release year).
Verify column names via:
  https://www.epa.gov/toxics-release-inventory-tri-program/tri-basic-data-files-calendar-years-1987-2022
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

# ── Column mapping: raw EPA CSV header → canonical internal name ──────────────
# AGENTS.md §10: Never hardcode EPA column names outside this map.
# Source: EPA EFService endpoint (2022_US). The CSV uses numbered headers of
# the form "N. COLUMN NAME". normalize_columns() strips the "N. " prefix,
# leaving bare column names that are looked up here (case-insensitive).
#
# Verified column names from 2022_US CSV header (post-strip):
#   YEAR, TRIFD, FRS ID, FACILITY NAME, STREET ADDRESS, CITY, COUNTY, ST, ZIP,
#   LATITUDE, LONGITUDE, PRIMARY SIC, PRIMARY NAICS, CHEMICAL, CAS#,
#   CLASSIFICATION, FORM TYPE, UNIT OF MEASURE, 5.1 - FUGITIVE AIR,
#   5.2 - STACK AIR, 5.3 - WATER, 5.4 - UNDERGROUND,
#   5.4.1 - UNDERGROUND CL I, 5.4.2 - UNDERGROUND C II-V,
#   5.5.1 - LANDFILLS, 5.5.1A - RCRA C LANDFILL, 5.5.1B - OTHER LANDFILLS,
#   5.5.2 - LAND TREATMENT, 5.5.3 - SURFACE IMPNDMNT,
#   5.5.3A - RCRA SURFACE IM, 5.5.3B - OTHER SURFACE I,
#   5.5.4 - OTHER DISPOSAL, ON-SITE RELEASE TOTAL, OFF-SITE RELEASE TOTAL

TRI_COLUMN_MAP: dict[str, str] = {
    # Facility identification
    "YEAR": "reporting_year",  # Field 1
    "TRIFD": "tri_facility_id",  # Field 2 (2006+); pre-2006 = TRIFID (alias)
    "FRS ID": "frs_id",  # Field 3
    "FACILITY NAME": "facility_name",  # Field 4
    "STREET ADDRESS": "address",  # Field 5
    "CITY": "city",  # Field 6
    "COUNTY": "county",  # Field 7
    "ST": "state_code",  # Field 8
    "ZIP": "zip_code",  # Field 9
    # Geographic coordinates (WGS84 decimal degrees)
    "LATITUDE": "latitude",  # Field 12
    "LONGITUDE": "longitude",  # Field 13
    # Industry codes
    "PRIMARY SIC": "primary_sic",  # Field 24
    "PRIMARY NAICS": "naics_code",  # Field 30
    "INDUSTRY SECTOR": "naics_desc",  # Field 23
    # Chemical identification
    "CHEMICAL": "chemical_name",  # Field 37
    "CAS#": "cas_number",  # Field 40 (no space before #)
    "CLASSIFICATION": "classification",  # Field 43
    "FORM TYPE": "form_type",  # Field 49: 'R' or 'A'
    "UNIT OF MEASURE": "unit_of_measure",  # Field 50: 'Pounds' or 'Grams'
    # On-site release total (Field 65) — NOT Field 107 (total all transfers)
    "ON-SITE RELEASE TOTAL": "total_release_lbs",
    # Off-site release total (Field 88)
    "OFF-SITE RELEASE TOTAL": "off_site_lbs",
    # Air: fugitive (Field 51) + stack air (Field 52)
    "5.1 - FUGITIVE AIR": "5.1_fugitive_air",
    "5.2 - STACK AIR": "5.2_stack_air",
    # Water: surface water discharges (Field 53)
    "5.3 - WATER": "5.3_water",
    # Underground subtotal (Field 54) — NOT used in aggregation to avoid double-counting
    "5.4 - UNDERGROUND": "5.4_underground_subtotal",
    # Underground injection leaf fields (Fields 55-56)
    "5.4.1 - UNDERGROUND CL I": "5.5.1_underground_cls1",
    "5.4.2 - UNDERGROUND C II-V": "5.5.2_underground_cls2to5",
    # Land subtotals (Fields 57, 61) — NOT used in aggregation (double-counts A+B)
    "5.5.1 - LANDFILLS": "5.5.1_landfills_subtotal",
    "5.5.3 - SURFACE IMPNDMNT": "5.5.3_surface_subtotal",
    # Land leaf fields (Fields 58, 59, 60, 62, 63, 64)
    "5.5.1A - RCRA C LANDFILL": "5.5.1a_rcra_landfill",
    "5.5.1B - OTHER LANDFILLS": "5.5.1b_other_landfills",
    "5.5.2 - LAND TREATMENT": "5.5.2_land_treatment",
    "5.5.3A - RCRA SURFACE IM": "5.5.3a_rcra_surface",
    "5.5.3B - OTHER SURFACE I": "5.5.3b_other_surface",
    "5.5.4 - OTHER DISPOSAL": "5.5.4_other_disposal",
}

# Alternate header names seen in older or alternative EPA CSV layouts
TRI_COLUMN_ALIASES: dict[str, str] = {
    "TRIFID": "tri_facility_id",  # pre-2006 name for Field 2
    "FACILITY.NAME": "facility_name",
    "FACILITY_NAME": "facility_name",
    "STREET ADDRESS": "address",
    "STREET.ADDRESS": "address",
    "FACILITY STREET": "address",
    "STATE": "state_code",
    "ZIP.CODE": "zip_code",
    "CAS #": "cas_number",
    "CAS NUMBER": "cas_number",
    "CAS.NUMBER": "cas_number",
    "REPORTING YEAR": "reporting_year",
    "PRIMARY NAICS CODE": "naics_code",
    "NAICS TITLE": "naics_desc",
    "PRIMARY SIC CODE": "primary_sic",
    "INDUSTRY SECTOR": "naics_desc",
    # Underground columns — alternate names
    "5.4 - UNDERGROUND": "5.4_underground_subtotal",  # aggregate subtotal; NOT used in sum
}

# Air release fields (sum of fugitive + stack air, TRI Fields 51+52)
AIR_RELEASE_FIELDS: list[str] = [
    "5.1_fugitive_air",
    "5.2_stack_air",
]

# Land release fields — leaf-level only (avoids double-counting subtotals 57 and 61).
# Fields 58+59 sum to Field 57 (landfills total); Fields 62+63 sum to Field 61 (surface total).
# Using the leaf fields gives: RCRA landfill + other landfills + land treatment
#   + RCRA surface impoundment + other surface + other disposal
LAND_RELEASE_FIELDS: list[str] = [
    "5.5.1a_rcra_landfill",
    "5.5.1b_other_landfills",
    "5.5.2_land_treatment",
    "5.5.3a_rcra_surface",
    "5.5.3b_other_surface",
    "5.5.4_other_disposal",
]

# Underground injection fields (Fields 55+56)
UNDERGROUND_RELEASE_FIELDS: list[str] = [
    "5.5.1_underground_cls1",
    "5.5.2_underground_cls2to5",
]

# Valid US state codes for filtering (excludes territories not in TRI scope)
US_STATE_CODES: frozenset[str] = frozenset(
    {
        "AL",
        "AK",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DE",
        "FL",
        "GA",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MD",
        "MA",
        "MI",
        "MN",
        "MS",
        "MO",
        "MT",
        "NE",
        "NV",
        "NH",
        "NJ",
        "NM",
        "NY",
        "NC",
        "ND",
        "OH",
        "OK",
        "OR",
        "PA",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VT",
        "VA",
        "WA",
        "WV",
        "WI",
        "WY",
        "DC",
        "PR",
        "VI",
        "GU",
        "AS",
        "MP",  # territories included in TRI
    }
)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename raw EPA CSV columns to canonical names using TRI_COLUMN_MAP.

    The EPA EFService CSV uses numbered headers of the form "N. COLUMN NAME"
    (e.g. "1. YEAR", "2. TRIFD"). This function strips the leading number+dot+space
    prefix before looking up in TRI_COLUMN_MAP, so the map stays clean.

    Falls back to TRI_COLUMN_ALIASES for legacy or alternative column names.
    """
    import re

    number_prefix = re.compile(r"^\d+\.\s+")

    # Strip whitespace + numbered prefix from column headers
    stripped: list[str] = []
    for col in df.columns:
        s = col.strip()
        s = number_prefix.sub("", s)  # remove "N. " prefix if present
        stripped.append(s)
    df.columns = pd.Index(stripped)

    # Build rename map: primary map + aliases (primary takes precedence)
    combined_map: dict[str, str] = {}
    for col in df.columns:
        upper_col = col.upper()
        if upper_col in TRI_COLUMN_MAP:
            combined_map[col] = TRI_COLUMN_MAP[upper_col]
        elif upper_col in TRI_COLUMN_ALIASES:
            combined_map[col] = TRI_COLUMN_ALIASES[upper_col]
        else:
            logger.debug("Unrecognised TRI column (not mapped): %r", col)

    return df.rename(columns=combined_map)


def compute_aggregated_release_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Compute air, land, and underground release aggregates from individual fields.

    TRI CSV does not provide a pre-computed per-medium aggregate for all mediums.
    This function sums the individual section-5 sub-columns to produce the four
    canonical release medium columns consumed by release_events.

    Rules:
    - Missing sub-columns are treated as 0 for aggregation purposes.
    - NaN in a sub-column means it was not reported; treated as 0 for aggregation.
    - total_release_lbs (Field 65) is mapped directly from the CSV — not recomputed.
    - water_release_lbs is Field 53 (single column) — mapped directly.

    Args:
        df: DataFrame with canonical column names (after normalize_columns).

    Returns:
        Same DataFrame with `air_release_lbs`, `land_release_lbs`,
        `underground_release_lbs`, and `water_release_lbs` columns populated.
    """

    def _sum_fields(row_df: pd.DataFrame, fields: list[str]) -> pd.Series:
        present = [f for f in fields if f in row_df.columns]
        if not present:
            return pd.Series(0.0, index=row_df.index)
        return row_df[present].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1)

    df["air_release_lbs"] = _sum_fields(df, AIR_RELEASE_FIELDS)
    df["land_release_lbs"] = _sum_fields(df, LAND_RELEASE_FIELDS)
    df["underground_release_lbs"] = _sum_fields(df, UNDERGROUND_RELEASE_FIELDS)

    # water_release_lbs: Field 53 — single column, mapped directly
    if "5.3_water" in df.columns:
        df["water_release_lbs"] = pd.to_numeric(df["5.3_water"], errors="coerce").fillna(0)
    else:
        df["water_release_lbs"] = 0.0

    return df
