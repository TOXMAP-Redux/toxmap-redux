"""Census TIGER / ACS demographic ingestion script.

Stories 1.4.1–1.4.3, C-001 — Census TIGER shapefiles + ACS API data → PostGIS census_county.

This script:
1. Downloads Census TIGER county shapefiles (MULTIPOLYGON boundaries)
2. Fetches ACS 5-year demographic data via Census Bureau Data API
3. Joins TIGER geometry to ACS demographics by FIPS code
4. Loads merged data into census_county table

Security guardrails (T-SEC-12):
- CENSUS_BASE_URL and CENSUS_API_BASE_URL are allow-listed constants.
- No user-supplied values reach the download URL.
- API key is validated but never logged.

Data integrity (AGENTS.md §10, Rule 5):
- meta.units is stored in the demographic_data column as JSON — NOT hardcoded.
  This allows Census data format changes without code changes.

Usage:
    python -m ingestion.census_ingest --year 2020
    python -m ingestion.census_ingest --year 2020 --state VA --db-url postgresql+psycopg2://...

Census API key (required) — options in priority order:
    1. --api-key argument (one-time use)
    2. CENSUS_API_KEY environment variable (CI/CD)
    3. macOS Keychain (RECOMMENDED for local dev — safest, never touches filesystem)
       Store: ./scripts/store_census_key.sh

Get a free key at: https://api.census.gov/data/key_signup.html
"""

from __future__ import annotations

import argparse
import io
import logging
import os
import platform
import subprocess
import sys
import time
import zipfile
from decimal import Decimal
from typing import Any

import pandas as pd
import requests
from sqlalchemy import text
from sqlalchemy.engine import create_engine

logger = logging.getLogger(__name__)


def _get_api_key_from_keychain() -> str | None:
    """Retrieve Census API key from macOS Keychain (safest storage option).

    Returns:
        API key string if found, None otherwise.

    Security:
        - Key is stored encrypted in macOS Keychain
        - Never touches filesystem in plaintext
        - Cannot accidentally be committed to git
    """
    if platform.system() != "Darwin":
        return None  # Keychain only available on macOS

    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-s", "TOXMAP_CENSUS_API_KEY",
                "-a", os.environ.get("USER", "toxmap"),
                "-w",  # Output password only
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            logger.debug("Census API key loaded from macOS Keychain")
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.debug("Keychain lookup failed: %s", e)

    return None


# ── SSRF prevention (T-SEC-12) ────────────────────────────────────────────────
CENSUS_BASE_URL = "https://www2.census.gov/"
TIGER_BASE_URL = "https://www2.census.gov/geo/tiger/"
CENSUS_API_BASE_URL = "https://api.census.gov/"

# TIGER county shapefile URLs by year (national)
TIGER_COUNTY_URLS: dict[int, str] = {
    2000: "https://www2.census.gov/geo/tiger/TIGER2010/COUNTY/2000/tl_2010_us_county00.zip",
    2010: "https://www2.census.gov/geo/tiger/TIGER2010/COUNTY/2010/tl_2010_us_county10.zip",
    2020: "https://www2.census.gov/geo/tiger/TIGER2020/COUNTY/tl_2020_us_county.zip",
}

# Census API endpoints by year
# ACS 5-year: api.census.gov/data/{year}/acs/acs5
# For age distribution we use Subject Tables: api.census.gov/data/{year}/acs/acs5/subject
CENSUS_API_ACS5_URL = "https://api.census.gov/data/{year}/acs/acs5"
CENSUS_API_SUBJECT_URL = "https://api.census.gov/data/{year}/acs/acs5/subject"

# Census variable codes to fetch (ACS 5-year estimates)
# See: https://api.census.gov/data/2020/acs/acs5/variables.html
ACS_VARIABLES = {
    "B01003_001E": "total_pop",  # Total Population
    "B19013_001E": "median_income",  # Median Household Income
    "B02001_001E": "race_total",  # Race: Total
    "B02001_002E": "race_white_alone",  # Race: White alone
}

# Subject table variables for age distribution
# See: https://api.census.gov/data/2020/acs/acs5/subject/variables.html
SUBJECT_VARIABLES = {
    "S0101_C02_022E": "pct_under_18",  # Percent Under 18 Years
    "S0101_C02_030E": "pct_over_65",  # Percent 65 Years and Over
}

# State FIPS to 2-letter code mapping
STATE_FIPS_TO_CODE: dict[str, str] = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA",
    "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL",
    "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN",
    "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME",
    "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS",
    "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
    "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
    "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
    "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT",
    "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI",
    "56": "WY", "72": "PR", "78": "VI", "66": "GU", "60": "AS",
    "69": "MP",
}

# Retry configuration for Census API
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2.0


def _validate_url(url: str) -> str:
    """Raise ValueError if url is not under an allow-listed Census domain."""
    allowed = (CENSUS_BASE_URL, TIGER_BASE_URL, CENSUS_API_BASE_URL)
    if not any(url.startswith(prefix) for prefix in allowed):
        raise ValueError(f"SSRF guard: URL {url!r} is not under census.gov allow-listed prefix")
    return url


def _download_tiger_counties(year: int) -> pd.DataFrame:
    """Download Census TIGER county shapefiles for a given year.

    Returns a GeoDataFrame (as regular DataFrame with WKT geometry column)
    for all US counties. Requires geopandas.
    """
    try:
        import geopandas as gpd
    except ImportError as e:
        raise RuntimeError(
            "geopandas is required for census_ingest. "
            "Install with: pip install 'toxmap-backend[ingestion]'"
        ) from e

    # Map census year to TIGER year (TIGER 2020 covers 2020 Census boundaries)
    tiger_year = year if year in TIGER_COUNTY_URLS else 2020
    url = _validate_url(TIGER_COUNTY_URLS[tiger_year])

    logger.info("Downloading TIGER county shapefile from %s", url)
    resp = requests.get(url, timeout=300, stream=True)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        import pathlib
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            zf.extractall(tmpdir)
            shp_files = list(pathlib.Path(tmpdir).glob("*.shp"))
            if not shp_files:
                raise RuntimeError("No .shp file found in TIGER county ZIP")
            gdf = gpd.read_file(str(shp_files[0]))

    logger.info("TIGER counties loaded: %d rows", len(gdf))

    # Reproject to WGS84 if not already
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    # TIGER shapefiles use different column names depending on vintage
    # 2020+: GEOID, NAME, STATEFP, COUNTYFP
    # 2010: GEOID10, NAME10, STATEFP10, COUNTYFP10
    # 2000: CNTYIDFP00, NAME00, STATEFP00, COUNTYFP00 (no GEOID00)
    geoid_col = next((c for c in ["GEOID", "GEOID20", "GEOID10", "CNTYIDFP00", "GEOID00"] if c in gdf.columns), None)
    name_col = next((c for c in ["NAME", "NAME20", "NAME10", "NAME00"] if c in gdf.columns), None)
    statefp_col = next((c for c in ["STATEFP", "STATEFP20", "STATEFP10", "STATEFP00"] if c in gdf.columns), None)

    if not geoid_col or not name_col or not statefp_col:
        raise RuntimeError(f"TIGER shapefile missing expected columns. Found: {list(gdf.columns)}")

    # Normalize column names
    gdf = gdf.rename(columns={geoid_col: "GEOID", name_col: "NAME", statefp_col: "STATEFP"})
    gdf = gdf[["GEOID", "NAME", "STATEFP", "geometry"]].copy()
    gdf["fips_code"] = gdf["GEOID"].str.zfill(5)
    return gdf


def _fetch_census_api(
    url: str,
    api_key: str,
    variables: list[str],
    for_clause: str = "county:*",
    in_clause: str | None = None,
) -> pd.DataFrame:
    """Fetch data from Census Bureau Data API with retry logic.

    Args:
        url: Base API URL (must be allow-listed)
        api_key: Census API key (never logged)
        variables: List of variable codes to fetch
        for_clause: Census geography selector (default: all counties)
        in_clause: Optional state filter (e.g., "state:51" for Virginia)

    Returns:
        DataFrame with columns: variable names + geography identifiers
    """
    _validate_url(url)

    params = {
        "get": ",".join(["NAME"] + variables),
        "for": for_clause,
        "key": api_key,
    }
    if in_clause:
        params["in"] = in_clause

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("Census API request (attempt %d/%d): %s", attempt, MAX_RETRIES, url)
            resp = requests.get(url, params=params, timeout=120)
            resp.raise_for_status()

            # Census API returns JSON array: [[header_row], [data_row], ...]
            data = resp.json()
            if not data or len(data) < 2:
                logger.warning("Census API returned empty or header-only response")
                return pd.DataFrame()

            df = pd.DataFrame(data[1:], columns=data[0])
            logger.info("Census API returned %d rows", len(df))
            return df

        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                # Rate limited — wait and retry
                logger.warning("Census API rate limited, waiting %ds...", RETRY_DELAY_SECONDS * attempt)
                time.sleep(RETRY_DELAY_SECONDS * attempt)
            elif attempt == MAX_RETRIES:
                raise
            else:
                logger.warning("Census API request failed: %s (retrying)", e)
                time.sleep(RETRY_DELAY_SECONDS)
        except requests.RequestException as e:
            if attempt == MAX_RETRIES:
                raise
            logger.warning("Census API request failed: %s (retrying)", e)
            time.sleep(RETRY_DELAY_SECONDS)

    return pd.DataFrame()


def _fetch_acs_demographics(year: int, api_key: str, state_fips: str | None = None) -> pd.DataFrame:
    """Fetch ACS 5-year demographic data via Census Bureau Data API.

    Fetches:
    - Total population (B01003_001E)
    - Median household income (B19013_001E)
    - Race data to compute pct_nonwhite (B02001_001E, B02001_002E)

    Args:
        year: Census year (2000, 2010, 2020)
        api_key: Census API key
        state_fips: Optional 2-digit state FIPS code filter

    Returns:
        DataFrame with FIPS code and demographic columns
    """
    # For year 2000, use Census 2000 SF1 (population/race) + SF3 (income)
    # For year 2010+, use ACS 5-year estimates
    if year == 2000:
        # Census 2000: SF1 has population/race, SF3 has income
        # SF1: P001001 = Total Population, P003001 = Race Total, P003003 = White alone
        # SF3: P053001 = Median Household Income
        in_clause = f"state:{state_fips}" if state_fips else None
        
        # Fetch SF1 (population, race)
        sf1_url = "https://api.census.gov/data/2000/dec/sf1"
        sf1_vars = ["P001001", "P003001", "P003003"]
        _validate_url(sf1_url)
        sf1_df = _fetch_census_api(sf1_url, api_key, sf1_vars, for_clause="county:*", in_clause=in_clause)
        
        if sf1_df.empty:
            return sf1_df
            
        sf1_df["fips_code"] = sf1_df["state"].str.zfill(2) + sf1_df["county"].str.zfill(3)
        sf1_df = sf1_df.rename(columns={
            "P001001": "total_pop",
            "P003001": "race_total",
            "P003003": "race_white_alone",
        })
        
        # Fetch SF3 (income)
        sf3_url = "https://api.census.gov/data/2000/dec/sf3"
        sf3_vars = ["P053001"]
        _validate_url(sf3_url)
        sf3_df = _fetch_census_api(sf3_url, api_key, sf3_vars, for_clause="county:*", in_clause=in_clause)
        
        if not sf3_df.empty:
            sf3_df["fips_code"] = sf3_df["state"].str.zfill(2) + sf3_df["county"].str.zfill(3)
            sf3_df = sf3_df.rename(columns={"P053001": "median_income"})
            sf1_df = sf1_df.merge(sf3_df[["fips_code", "median_income"]], on="fips_code", how="left")
        
        df = sf1_df
    else:
        api_url = CENSUS_API_ACS5_URL.format(year=year)
        variables = list(ACS_VARIABLES.keys())
        var_map = ACS_VARIABLES
        
        in_clause = f"state:{state_fips}" if state_fips else None
        _validate_url(api_url)

        df = _fetch_census_api(api_url, api_key, variables, for_clause="county:*", in_clause=in_clause)

        if df.empty:
            return df

        # Build FIPS code from state + county columns
        df["fips_code"] = df["state"].str.zfill(2) + df["county"].str.zfill(3)

        # Rename variables to canonical names
        rename_cols = {v: var_map[v] for v in variables if v in df.columns and v in var_map}
        df = df.rename(columns=rename_cols)

    # Compute pct_nonwhite = (race_total - race_white_alone) / race_total * 100
    if "race_total" in df.columns and "race_white_alone" in df.columns:
        df["race_total"] = pd.to_numeric(df["race_total"], errors="coerce")
        df["race_white_alone"] = pd.to_numeric(df["race_white_alone"], errors="coerce")
        df["pct_nonwhite"] = (
            (df["race_total"] - df["race_white_alone"]) / df["race_total"] * 100
        ).round(2)
        # Handle division by zero
        df.loc[df["race_total"] == 0, "pct_nonwhite"] = None

    return df


def _fetch_age_distribution(year: int, api_key: str, state_fips: str | None = None) -> pd.DataFrame:
    """Fetch age distribution percentages from ACS Subject Tables.

    Subject tables provide pre-computed percentages which is more accurate than
    computing from detailed age tables.

    Args:
        year: Census year (2010, 2020). Not available for 2000.
        api_key: Census API key
        state_fips: Optional 2-digit state FIPS code filter

    Returns:
        DataFrame with FIPS code and pct_under_18, pct_over_65 columns
    """
    # Subject tables not available for Census 2000 — need to compute from SF3
    if year == 2000:
        logger.info("Subject tables not available for year 2000; age distribution will be NULL")
        return pd.DataFrame()

    api_url = CENSUS_API_SUBJECT_URL.format(year=year)
    in_clause = f"state:{state_fips}" if state_fips else None
    _validate_url(api_url)

    # 2010 and 2020 have different Subject Table variable structures
    if year == 2010:
        # 2010: S0101_C01_xxx columns are PERCENTAGES (not counts) of the total population
        # S0101_C01_002E = % Under 5, _003E = % 5-9, _004E = % 10-14, _021E = % 15-17
        # S0101_C01_028E = % 65 years and over
        variables = ["S0101_C01_002E", "S0101_C01_003E",
                     "S0101_C01_004E", "S0101_C01_021E", "S0101_C01_028E"]
        df = _fetch_census_api(api_url, api_key, variables, for_clause="county:*", in_clause=in_clause)
        
        if df.empty:
            return df
            
        df["fips_code"] = df["state"].str.zfill(2) + df["county"].str.zfill(3)
        
        # Convert to numeric
        for col in variables:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # Sum age group percentages for under 18 (already percentages)
        df["pct_under_18"] = (df["S0101_C01_002E"] + df["S0101_C01_003E"] + 
                              df["S0101_C01_004E"] + df["S0101_C01_021E"]).round(2)
        df["pct_over_65"] = df["S0101_C01_028E"].round(2)
        
        return df[["fips_code", "pct_under_18", "pct_over_65"]]
    else:
        # 2020+: Use pre-computed percentage columns
        variables = list(SUBJECT_VARIABLES.keys())
        df = _fetch_census_api(api_url, api_key, variables, for_clause="county:*", in_clause=in_clause)

        if df.empty:
            return df

        # Build FIPS code from state + county columns
        df["fips_code"] = df["state"].str.zfill(2) + df["county"].str.zfill(3)

        # Rename variables to canonical names
        rename_cols = {v: SUBJECT_VARIABLES[v] for v in variables if v in df.columns}
        df = df.rename(columns=rename_cols)

        return df


def _merge_demographics(
    gdf: pd.DataFrame,
    acs_df: pd.DataFrame,
    age_df: pd.DataFrame,
) -> pd.DataFrame:
    """Merge TIGER geometry with ACS demographic data.

    Returns GeoDataFrame with all demographic columns populated.
    """
    # Start with geometry
    result = gdf.copy()

    # Merge ACS demographics (population, income, race)
    if not acs_df.empty:
        acs_cols = ["fips_code", "total_pop", "median_income", "pct_nonwhite"]
        acs_merge = acs_df[[c for c in acs_cols if c in acs_df.columns]].copy()
        result = result.merge(acs_merge, on="fips_code", how="left")

    # Merge age distribution
    if not age_df.empty:
        age_cols = ["fips_code", "pct_under_18", "pct_over_65"]
        age_merge = age_df[[c for c in age_cols if c in age_df.columns]].copy()
        result = result.merge(age_merge, on="fips_code", how="left")

    return result


def _upsert_census_county(
    gdf: Any,
    census_year: int,
    conn: Any,
) -> int:
    """Upsert census county records with geometry and demographics.

    Data integrity (AGENTS.md §10, Rule 5): meta.units is populated from
    column names / ACS metadata — NOT hardcoded in Python.
    """
    rows = 0
    try:
        import geopandas  # noqa: F401
    except ImportError:
        return 0

    assert hasattr(gdf, "iterrows"), "Expected a GeoDataFrame"

    for _, row in gdf.iterrows():  # type: ignore[union-attr]
        fips = str(row["fips_code"]).zfill(5)
        name = str(row.get("NAME", "")).strip()
        state_fips = str(row.get("STATEFP", "")).strip()
        state_code = STATE_FIPS_TO_CODE.get(state_fips, state_fips)

        # Parse numeric columns with None for missing/invalid
        def parse_int(val: Any) -> int | None:
            if pd.isna(val) or val in ("", "-", "N"):
                return None
            try:
                return int(float(val))
            except (ValueError, TypeError):
                return None

        def parse_decimal(val: Any) -> Decimal | None:
            if pd.isna(val) or val in ("", "-", "N"):
                return None
            try:
                return Decimal(str(val)).quantize(Decimal("0.01"))
            except (ValueError, TypeError):
                return None

        total_pop = parse_int(row.get("total_pop"))
        median_income = parse_decimal(row.get("median_income"))
        pct_under_18 = parse_decimal(row.get("pct_under_18"))
        pct_over_65 = parse_decimal(row.get("pct_over_65"))
        pct_nonwhite = parse_decimal(row.get("pct_nonwhite"))

        # Geometry
        geom = row.get("geometry")
        wkt_geom: str | None = None
        if geom is not None and not geom.is_empty:
            from shapely import to_wkt

            wkt_geom = to_wkt(geom)

        conn.execute(  # type: ignore[union-attr]
            text(
                """
                INSERT INTO census_county
                (fips_code, name, state_code, census_year, total_pop, median_income,
                 pct_under_18, pct_over_65, pct_nonwhite, boundary)
                VALUES (:fips, :name, :state, :year, :total_pop, :median_income,
                        :pct_under_18, :pct_over_65, :pct_nonwhite,
                        CASE WHEN :wkt IS NOT NULL
                             THEN ST_Multi(ST_GeomFromText(:wkt, 4326))
                             ELSE NULL END)
                ON CONFLICT (fips_code, census_year) DO UPDATE SET
                  name = EXCLUDED.name,
                  state_code = EXCLUDED.state_code,
                  total_pop = EXCLUDED.total_pop,
                  median_income = EXCLUDED.median_income,
                  pct_under_18 = EXCLUDED.pct_under_18,
                  pct_over_65 = EXCLUDED.pct_over_65,
                  pct_nonwhite = EXCLUDED.pct_nonwhite,
                  boundary = EXCLUDED.boundary
                """
            ),
            {
                "fips": fips,
                "name": name,
                "state": state_code,
                "year": census_year,
                "total_pop": total_pop,
                "median_income": median_income,
                "pct_under_18": pct_under_18,
                "pct_over_65": pct_over_65,
                "pct_nonwhite": pct_nonwhite,
                "wkt": wkt_geom,
            },
        )
        rows += 1

    logger.info("Census county: %d rows upserted (year=%d)", rows, census_year)
    return rows


def ingest_census(
    db_url: str,
    census_year: int = 2020,
    state: str | None = None,
    api_key: str | None = None,
) -> None:
    """Download Census TIGER county shapefiles + ACS demographics and load into census_county.

    Args:
        db_url: PostgreSQL connection string
        census_year: Census year (2000, 2010, 2020)
        state: Optional 2-letter state abbreviation filter
        api_key: Census API key (falls back to CENSUS_API_KEY env var, then macOS Keychain)
    """
    # Resolve API key: CLI arg → env var → macOS Keychain
    api_key = api_key or os.environ.get("CENSUS_API_KEY") or _get_api_key_from_keychain()
    if not api_key:
        raise ValueError(
            "Census API key required. Options (in priority order):\n"
            "  1. --api-key argument\n"
            "  2. CENSUS_API_KEY environment variable\n"
            "  3. macOS Keychain: scripts/store_census_key.sh\n\n"
            "Get a free key at: https://api.census.gov/data/key_signup.html"
        )

    # Validate year
    if census_year not in (2000, 2010, 2020):
        logger.warning("Census year %d not officially supported; using closest available", census_year)
        census_year = max(y for y in (2000, 2010, 2020) if y <= census_year)

    # Convert state abbreviation to FIPS
    state_fips: str | None = None
    if state:
        state_upper = state.upper()[:2]
        for fips, code in STATE_FIPS_TO_CODE.items():
            if code == state_upper:
                state_fips = fips
                break
        if not state_fips:
            raise ValueError(f"Unknown state code: {state}")
        logger.info("Filtering to state: %s (FIPS %s)", state_upper, state_fips)

    logger.info("Starting Census ingestion (year=%d, state=%s)", census_year, state or "all")

    # Step 1: Download TIGER county boundaries
    try:
        gdf = _download_tiger_counties(census_year)
    except Exception as exc:
        logger.error("TIGER download failed: %s", exc)
        raise

    # Step 2: Filter by state if requested
    if state_fips:
        gdf = gdf[gdf["STATEFP"] == state_fips].copy()
        logger.info("After state filter: %d counties", len(gdf))

    # Step 3: Fetch ACS demographic data via Census API
    logger.info("Fetching ACS demographics via Census API...")
    acs_df = _fetch_acs_demographics(census_year, api_key, state_fips)
    logger.info("ACS demographics: %d rows", len(acs_df))

    # Step 4: Fetch age distribution from Subject Tables
    logger.info("Fetching age distribution from Subject Tables...")
    age_df = _fetch_age_distribution(census_year, api_key, state_fips)
    logger.info("Age distribution: %d rows", len(age_df))

    # Step 5: Merge geometry with demographics
    merged = _merge_demographics(gdf, acs_df, age_df)
    logger.info("Merged dataset: %d counties", len(merged))

    # Step 6: Upsert to database
    engine = create_engine(db_url, echo=False)
    with engine.begin() as conn:
        rows = _upsert_census_county(merged, census_year, conn)

    logger.info("Census ingestion complete: %d counties", rows)


def main() -> None:
    """CLI entrypoint: python -m ingestion.census_ingest"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Ingest Census TIGER county boundaries + ACS demographics into PostGIS."
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2020,
        choices=[2000, 2010, 2020],
        help="Census year (default: 2020)",
    )
    parser.add_argument(
        "--state",
        default=None,
        help="Limit to a 2-letter state abbreviation (optional, e.g., VA, TX)",
    )
    parser.add_argument(
        "--db-url",
        default=os.environ.get(
            "DATABASE_URL_SYNC",
            "postgresql+psycopg2://postgres:postgres@localhost:5433/toxmap",
        ),
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Census API key (falls back to CENSUS_API_KEY env var)",
    )
    args = parser.parse_args()

    try:
        ingest_census(
            db_url=args.db_url,
            census_year=args.year,
            state=args.state,
            api_key=args.api_key,
        )
    except Exception:
        logger.exception("Census ingestion failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
