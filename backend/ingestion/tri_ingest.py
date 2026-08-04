"""TRI EPA CSV ingestion script.

Stories 1.2.2–1.2.5 — CLI entrypoint for EPA TRI Basic Data Files → PostGIS.

Usage:
    python -m ingestion.tri_ingest --year 2022
    python -m ingestion.tri_ingest --year 2022 --db-url postgresql+psycopg2://...

Security guardrails (AGENTS.md §11, T-SEC-12 SSRF prevention):
- TRI_BASE_URL is an allow-listed constant — never built from user input.
- All SQL inserts use SQLAlchemy parameterized statements (no f-string SQL).
- Coordinate bounds validated before PostGIS insert.
"""

from __future__ import annotations

import argparse
import io
import logging
import os
import re
import sys
from typing import Any

import pandas as pd
import requests
from sqlalchemy import text
from sqlalchemy.engine import create_engine

from ingestion.tri_parser import (
    US_STATE_CODES,
    compute_aggregated_release_columns,
    normalize_columns,
)

# ATSDR ToxFAQs URL lookup — shared with Superfund service
# Import the dict directly to avoid circular imports
try:
    from app.services.superfund_cas_lookup import _ATSDR as ATSDR_LOOKUP
except ImportError:
    # Fallback for running script directly outside app context
    ATSDR_LOOKUP = {}

logger = logging.getLogger(__name__)

# ── SSRF prevention (T-SEC-12): hard-coded allow-listed base URLs ─────────────
# Never build these from user input, environment variables, or database values.
TRI_BASE_URL = "https://www.epa.gov/"
TRI_DATA_BASE_URL = "https://data.epa.gov/"

# EPA EFService CSV endpoint — year-parameterized, no user input reaches the URL.
# Format: 2022_US returns data from 1987 through 2022 (latest in the interval).
# Confirmed active as of 2026-07.
TRI_CSV_URL_PATTERN = (
    "https://data.epa.gov/efservice/downloads/tri/mv_tri_basic_download/{year}_US/csv"
)

# WGS84 coordinate bounds (AGENTS.md §11 — validate lat/lon before PostGIS insert)
LAT_MIN, LAT_MAX = 17.0, 72.0  # US+territories bounding box
LON_MIN, LON_MAX = -180.0, -65.0


def _validate_url(url: str) -> str:
    """Raise ValueError if url does not start with an allow-listed TRI base URL.

    SSRF prevention: the URL prefix is checked before every HTTP request so that
    a misconfigured or injected URL cannot reach internal network addresses.
    """
    allowed = (TRI_BASE_URL, TRI_DATA_BASE_URL)
    if not any(url.startswith(prefix) for prefix in allowed):
        raise ValueError(
            f"SSRF guard: URL {url!r} is not under any allow-listed prefix "
            f"{allowed!r}. Ingestion aborted."
        )
    return url


def _download_tri_csv(year: int) -> pd.DataFrame:
    """Download and parse the TRI Basic Data Files CSV for a given year.

    Uses the EPA EFService endpoint:
      https://data.epa.gov/efservice/downloads/tri/mv_tri_basic_download/{year}_US/csv
    where {year} is the upper-bound year of the 1987–{year} interval.

    Returns a DataFrame with raw (un-normalized) column names from the CSV.
    """
    csv_url = _validate_url(
        f"https://data.epa.gov/efservice/downloads/tri/mv_tri_basic_download/{year}_US/csv"
    )

    logger.info("Downloading TRI CSV for year %d from %s", year, csv_url)
    resp = requests.get(csv_url, timeout=600, stream=True)
    resp.raise_for_status()

    logger.info("Downloaded TRI CSV (%s bytes)", resp.headers.get("content-length", "unknown"))
    return pd.read_csv(io.BytesIO(resp.content), dtype=str, low_memory=False)


def _clean_numeric(series: pd.Series) -> pd.Series:
    """Convert a string series to float, treating empty/whitespace as None."""
    return pd.to_numeric(series.str.strip().replace({"": None}), errors="coerce")


def _filter_valid_us_facilities(df: pd.DataFrame) -> pd.DataFrame:
    """Retain only US facilities with valid coordinates (story 1.2.5)."""
    before = len(df)

    # State filter
    df = df[df["state_code"].isin(US_STATE_CODES)].copy()

    # Coordinate parsing and bounds validation
    df["latitude"] = _clean_numeric(df["latitude"])
    df["longitude"] = _clean_numeric(df["longitude"])

    df = df[
        df["latitude"].between(LAT_MIN, LAT_MAX, inclusive="both")
        & df["longitude"].between(LON_MIN, LON_MAX, inclusive="both")
    ].copy()

    after = len(df)
    logger.info("Coordinate filter: %d → %d facilities (removed %d)", before, after, before - after)
    return df


# CAS number pattern: 2-7 digits, hyphen, 2 digits, hyphen, 1 digit (e.g., 71-36-3)
_CAS_PATTERN = re.compile(r"^\d{2,7}-\d{2}-\d$")

# TRI category code pattern: N followed by 3 digits (e.g., N010, N090, N982)
# These are EPA TRI Form R codes, NOT CAS numbers
_TRI_CATEGORY_PATTERN = re.compile(r"^N\d{3}$")

# Mapping of TRI category codes (N###) to correct PubChem URLs
# For element compounds, use /element/{Element}
# For chemical classes, use search URLs or NULL
_TRI_CATEGORY_PUBCHEM = {
    # Metal compounds → link to element page
    "N010": "https://pubchem.ncbi.nlm.nih.gov/element/Antimony",  # ANTIMONY COMPOUNDS
    "N020": "https://pubchem.ncbi.nlm.nih.gov/element/Arsenic",  # ARSENIC COMPOUNDS
    "N040": "https://pubchem.ncbi.nlm.nih.gov/element/Barium",  # BARIUM COMPOUNDS
    "N050": "https://pubchem.ncbi.nlm.nih.gov/element/Beryllium",  # BERYLLIUM COMPOUNDS
    "N078": "https://pubchem.ncbi.nlm.nih.gov/element/Cadmium",  # CADMIUM COMPOUNDS
    "N090": "https://pubchem.ncbi.nlm.nih.gov/element/Chromium",  # CHROMIUM COMPOUNDS
    "N096": "https://pubchem.ncbi.nlm.nih.gov/element/Cobalt",  # COBALT AND COBALT COMPOUNDS
    "N100": "https://pubchem.ncbi.nlm.nih.gov/element/Copper",  # COPPER COMPOUNDS
    "N420": "https://pubchem.ncbi.nlm.nih.gov/element/Lead",  # LEAD AND LEAD COMPOUNDS
    "N450": "https://pubchem.ncbi.nlm.nih.gov/element/Manganese",  # MANGANESE AND MANGANESE COMPOUNDS
    "N458": "https://pubchem.ncbi.nlm.nih.gov/element/Mercury",  # MERCURY AND MERCURY COMPOUNDS
    "N495": "https://pubchem.ncbi.nlm.nih.gov/element/Nickel",  # NICKEL COMPOUNDS
    "N725": "https://pubchem.ncbi.nlm.nih.gov/element/Selenium",  # SELENIUM COMPOUNDS
    "N740": "https://pubchem.ncbi.nlm.nih.gov/element/Silver",  # SILVER AND SILVER COMPOUNDS
    "N760": "https://pubchem.ncbi.nlm.nih.gov/element/Thallium",  # THALLIUM AND THALLIUM COMPOUNDS
    "N770": "https://pubchem.ncbi.nlm.nih.gov/compound/Vanadium",  # VANADIUM COMPOUNDS (no element page)
    "N982": "https://pubchem.ncbi.nlm.nih.gov/element/Zinc",  # ZINC COMPOUNDS
    # Other categories → specific compound or search URL
    "N084": "https://pubchem.ncbi.nlm.nih.gov/#query=chlorophenols",  # CHLOROPHENOLS
    "N106": "https://pubchem.ncbi.nlm.nih.gov/compound/Cyanide",  # CYANIDE COMPOUNDS (CID 768)
    "N120": "https://pubchem.ncbi.nlm.nih.gov/#query=diisocyanates",  # DIISOCYANATES
    "N125": "https://pubchem.ncbi.nlm.nih.gov/compound/590836",  # DINP (CID 590836)
    "N150": "https://pubchem.ncbi.nlm.nih.gov/#query=dioxin",  # DIOXIN AND DIOXIN-LIKE COMPOUNDS
    "N171": "https://pubchem.ncbi.nlm.nih.gov/#query=ethylenebisdithiocarbamic",  # EBDC salts/esters
    "N230": "https://pubchem.ncbi.nlm.nih.gov/#query=glycol+ethers",  # CERTAIN GLYCOL ETHERS
    "N270": "https://pubchem.ncbi.nlm.nih.gov/compound/18529",  # HBCD (CID 18529)
    "N503": "https://pubchem.ncbi.nlm.nih.gov/compound/89594",  # NICOTINE (CID 89594)
    "N511": None,  # NITRATE COMPOUNDS - too broad, no single compound
    "N530": "https://pubchem.ncbi.nlm.nih.gov/compound/1752",  # NONYLPHENOL (CID 1752)
    "N535": "https://pubchem.ncbi.nlm.nih.gov/#query=nonylphenol+ethoxylates",  # NPEs
    "N575": "https://pubchem.ncbi.nlm.nih.gov/#query=polybrominated+biphenyls",  # PBBs
    "N583": "https://pubchem.ncbi.nlm.nih.gov/#query=polychlorinated+alkanes",  # PCAs
    "N590": "https://pubchem.ncbi.nlm.nih.gov/#query=polycyclic+aromatic",  # PACs
    "N746": "https://pubchem.ncbi.nlm.nih.gov/compound/441071",  # STRYCHNINE (CID 441071)
    "N874": "https://pubchem.ncbi.nlm.nih.gov/compound/54678486",  # WARFARIN (CID 54678486)
}


def _pubchem_url(cas: str | None) -> str | None:
    """Return a PubChem compound URL for a CAS number, or None if invalid/absent.

    PubChem resolves /compound/<CAS> to the canonical compound page, so no
    API call is required — the URL is constructed directly from the CAS number.

    IMPORTANT: TRI category codes (N###) are NOT CAS numbers. They are EPA
    Form R codes for chemical categories. We handle these separately:
    - If a TRI category code has a known PubChem mapping, use that
    - Otherwise, return None to avoid broken 404 links

    7.BUG.22 fix: Validate CAS format before generating URL.
    """
    if not cas:
        return None

    cas = cas.strip()

    # Check if this is a TRI category code (N###)
    if _TRI_CATEGORY_PATTERN.match(cas):
        # Use the mapping, or None if not mapped
        return _TRI_CATEGORY_PUBCHEM.get(cas)

    # Validate CAS number format (e.g., 71-36-3, 7440-50-8)
    if not _CAS_PATTERN.match(cas):
        logger.warning("Invalid CAS number format: %r — skipping PubChem URL", cas)
        return None

    return f"https://pubchem.ncbi.nlm.nih.gov/compound/{cas}"


def _atsdr_url(name: str | None) -> str | None:
    """Return an ATSDR ToxFAQs URL for a chemical name, or None if not covered.

    ATSDR only publishes ToxFAQs for ~200 priority hazardous substances.
    The lookup is done by exact chemical name match (uppercase).
    """
    if name and ATSDR_LOOKUP:
        return ATSDR_LOOKUP.get(name.upper())
    return None


def _upsert_chemicals(df: pd.DataFrame, conn: Any) -> dict[str, int]:
    """Insert new chemicals, skip duplicates. Returns chemical_name → id map."""
    unique_chems = df[["chemical_name", "cas_number", "classification"]].drop_duplicates(
        subset=["chemical_name"]
    )

    chem_map: dict[str, int] = {}
    for _, row in unique_chems.iterrows():
        name = row["chemical_name"].strip().upper() if pd.notna(row["chemical_name"]) else None
        if not name:
            continue
        cas = row["cas_number"].strip() if pd.notna(row.get("cas_number")) else None
        # Normalize CAS: empty string → None
        if cas == "":
            cas = None

        result = conn.execute(
            text(
                "INSERT INTO chemicals (cas_number, name, pubchem_url, atsdr_url) "
                "VALUES (:cas, :name, :pubchem_url, :atsdr_url) "
                "ON CONFLICT DO NOTHING "
                "RETURNING id"
            ),
            {
                "cas": cas,
                "name": name,
                "pubchem_url": _pubchem_url(cas),
                "atsdr_url": _atsdr_url(name),
            },
        )
        row_id = result.scalar()
        if row_id is None:
            # Row already existed — fetch its id
            row_id = conn.execute(
                text("SELECT id FROM chemicals WHERE name = :name"),
                {"name": name},
            ).scalar()
        if row_id is not None:
            chem_map[name] = row_id

    logger.info("Chemicals: %d distinct names → %d mapped", len(unique_chems), len(chem_map))
    return chem_map


def _upsert_facilities(df: pd.DataFrame, conn: Any) -> dict[str, int]:
    """Insert/update facilities. Returns tri_facility_id → id map."""
    unique_facs = df.drop_duplicates(subset=["tri_facility_id"])
    fac_map: dict[str, int] = {}

    for _, row in unique_facs.iterrows():
        tri_id = str(row["tri_facility_id"]).strip()
        lat = float(row["latitude"])
        lon = float(row["longitude"])

        result = conn.execute(
            text(
                "INSERT INTO facilities "
                "(tri_facility_id, name, address, city, state_code, zip_code, county, "
                " naics_code, naics_desc, frs_id, primary_sic, location) "
                "VALUES (:tid, :name, :addr, :city, :state, :zip, :county, "
                "        :naics, :naics_desc, :frs, :sic, "
                "        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) "
                "ON CONFLICT (tri_facility_id) DO UPDATE SET "
                "  name = EXCLUDED.name, "
                "  address = EXCLUDED.address, "
                "  city = EXCLUDED.city, "
                "  state_code = EXCLUDED.state_code, "
                "  zip_code = EXCLUDED.zip_code, "
                "  county = EXCLUDED.county, "
                "  naics_code = EXCLUDED.naics_code, "
                "  naics_desc = EXCLUDED.naics_desc, "
                "  frs_id = EXCLUDED.frs_id, "
                "  primary_sic = EXCLUDED.primary_sic, "
                "  location = EXCLUDED.location "
                "RETURNING id"
            ),
            {
                "tid": tri_id,
                "name": str(row.get("facility_name", "")).strip() or None,
                "addr": str(row.get("address", "")).strip() or None,
                "city": str(row.get("city", "")).strip() or None,
                "state": str(row.get("state_code", "")).strip() or None,
                "zip": str(row.get("zip_code", "")).strip() or None,
                "county": str(row.get("county", "")).strip() or None,
                "naics": str(row.get("naics_code", "")).strip() or None,
                "naics_desc": str(row.get("naics_desc", "")).strip() or None,
                "frs": str(row.get("frs_id", "")).strip() or None,
                "sic": str(row.get("primary_sic", "")).strip() or None,
                "lat": lat,
                "lon": lon,
            },
        )
        row_id = result.scalar()
        if row_id is not None:
            fac_map[tri_id] = row_id

    logger.info("Facilities: %d unique TRIFIDs → %d upserted", len(unique_facs), len(fac_map))
    return fac_map


def _insert_releases(
    df: pd.DataFrame,
    fac_map: dict[str, int],
    chem_map: dict[str, int],
    conn: Any,
) -> int:
    """Bulk-insert release events. Returns number of rows inserted."""
    rows_inserted = 0

    for _, row in df.iterrows():
        tri_id = str(row["tri_facility_id"]).strip()
        chem_name = str(row.get("chemical_name", "")).strip().upper()
        year_raw = row.get("reporting_year")
        fac_id = fac_map.get(tri_id)
        chem_id = chem_map.get(chem_name)

        if fac_id is None or chem_id is None:
            continue

        try:
            year = int(year_raw)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue

        # total_release_lbs: NULL = data absent; 0.0 = reported zero (AGENTS.md §10 rule 3)
        total_raw = row.get("total_release_lbs")
        total_lbs: float | None = None
        if pd.notna(total_raw) and str(total_raw).strip() != "":
            total_lbs = float(str(total_raw).strip())

        off_raw = row.get("off_site_lbs")
        off_lbs: float | None = None
        if pd.notna(off_raw) and str(off_raw).strip() != "":
            off_lbs = float(str(off_raw).strip())

        def _to_float(val: object) -> float:
            try:
                return float(str(val).strip()) if pd.notna(val) else 0.0
            except (ValueError, TypeError):
                return 0.0

        unit = str(row.get("unit_of_measure", "Pounds")).strip() or "Pounds"
        form = str(row.get("form_type", "R")).strip() or "R"

        conn.execute(
            text(
                "INSERT INTO release_events "
                "(facility_id, chemical_id, reporting_year, total_release_lbs, "
                " air_release_lbs, water_release_lbs, land_release_lbs, "
                " underground_release_lbs, off_site_lbs, unit_of_measure, form_type) "
                "VALUES (:fid, :cid, :year, :total, :air, :water, :land, :underground, "
                "        :off_site, :unit, :form) "
                "ON CONFLICT ON CONSTRAINT uq_release_events_fac_chem_year DO NOTHING"
            ),
            {
                "fid": fac_id,
                "cid": chem_id,
                "year": year,
                "total": total_lbs,
                "air": _to_float(row.get("air_release_lbs")),
                "water": _to_float(row.get("water_release_lbs")),
                "land": _to_float(row.get("land_release_lbs")),
                "underground": _to_float(row.get("underground_release_lbs")),
                "off_site": off_lbs,
                "unit": unit,
                "form": form,
            },
        )
        rows_inserted += 1

    logger.info("Release events: %d rows inserted", rows_inserted)
    return rows_inserted


def ingest_year(year: int, db_url: str) -> None:
    """Full ingestion pipeline for one TRI reporting year.

    1. Download CSV from EPA EFService (allow-listed URL)
    2. Normalize column names via TRI_COLUMN_MAP
    3. Compute aggregated release medium columns
    4. Filter to the requested year only (CSV may include all years 1987–{year})
    5. Filter to valid US facilities with coordinate bounds
    6. Upsert facilities and chemicals
    7. Insert release events
    """
    logger.info("Starting TRI ingestion for year %d", year)

    df_raw = _download_tri_csv(year)
    logger.info("Loaded %d raw rows", len(df_raw))

    df = normalize_columns(df_raw)
    df = compute_aggregated_release_columns(df)

    # Filter to the requested year only
    if "reporting_year" in df.columns:
        before_year = len(df)
        df = df[df["reporting_year"].astype(str).str.strip() == str(year)].copy()
        logger.info("Year filter %d: %d → %d rows", year, before_year, len(df))
    else:
        logger.warning("'reporting_year' column not found — ingesting all years from CSV")

    df = _filter_valid_us_facilities(df)
    logger.info("%d facilities after coordinate filtering", len(df))

    engine = create_engine(db_url, echo=False)
    with engine.begin() as conn:
        # Advance SERIAL sequences to the current MAX id.
        # Required after seed.sql inserts with explicit IDs (which do not
        # advance the PostgreSQL SERIAL sequence automatically).
        # Use GREATEST(MAX(id), 1) to avoid setval(seq, 0) error on empty tables
        # (sequences are 1-based; 0 is out of bounds).
        conn.execute(
            text(
                "SELECT setval(pg_get_serial_sequence('facilities', 'id'), "
                "       GREATEST(COALESCE((SELECT MAX(id) FROM facilities), 0), 1))"
            )
        )
        conn.execute(
            text(
                "SELECT setval(pg_get_serial_sequence('chemicals', 'id'), "
                "       GREATEST(COALESCE((SELECT MAX(id) FROM chemicals), 0), 1))"
            )
        )
        chem_map = _upsert_chemicals(df, conn)
        fac_map = _upsert_facilities(df, conn)
        rows = _insert_releases(df, fac_map, chem_map, conn)

    logger.info("TRI ingestion complete: %d release rows for year %d", rows, year)


def main() -> None:
    """CLI entrypoint: python -m ingestion.tri_ingest --year YYYY"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Ingest EPA TRI Basic Data Files CSV into PostGIS."
    )
    parser.add_argument(
        "--year",
        type=int,
        required=True,
        help="TRI reporting year (e.g. 2022)",
    )
    parser.add_argument(
        "--db-url",
        default=os.environ.get(
            "DATABASE_URL_SYNC",
            "postgresql+psycopg2://postgres:postgres@postgres:5432/toxmap",
        ),
        help="SQLAlchemy sync database URL (default: DATABASE_URL_SYNC env var)",
    )
    args = parser.parse_args()

    if args.year < 1987 or args.year > 2030:
        parser.error(f"--year must be between 1987 and 2030, got {args.year}")

    try:
        ingest_year(year=args.year, db_url=args.db_url)
    except Exception:
        logger.exception("TRI ingestion failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
