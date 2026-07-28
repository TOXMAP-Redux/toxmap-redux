"""Superfund / NPL site ingestion script.

Stories 1.3.1–1.3.2 — EPA CERCLIS Active Sites CSV → PostGIS superfund_sites.

Security guardrails (AGENTS.md §11, T-SEC-12 SSRF prevention):
- SUPERFUND_BASE_URL is an allow-listed constant.
- All SQL uses parameterized statements.

Usage:
    python -m ingestion.superfund_ingest
    python -m ingestion.superfund_ingest --db-url postgresql+psycopg2://...
"""

from __future__ import annotations

import argparse
import io
import logging
import os
import sys

import pandas as pd
import requests
from sqlalchemy import text
from sqlalchemy.engine import create_engine

logger = logging.getLogger(__name__)

# ── SSRF prevention (T-SEC-12) ────────────────────────────────────────────────
SUPERFUND_BASE_URL = "https://semspub.epa.gov/"

# EPA CERCLIS NPL Active Sites direct CSV download
SUPERFUND_CSV_URL = (
    "https://semspub.epa.gov/src/document/HQ/100001259"
)

# WGS84 bounds for validation
LAT_MIN, LAT_MAX = 17.0, 72.0
LON_MIN, LON_MAX = -180.0, -65.0


def _validate_url(url: str) -> str:
    """Raise ValueError if url is not under the allow-listed prefix."""
    if not url.startswith(SUPERFUND_BASE_URL):
        raise ValueError(
            f"SSRF guard: URL {url!r} is not under {SUPERFUND_BASE_URL!r}"
        )
    return url


def _download_superfund_csv() -> pd.DataFrame:
    """Download the EPA CERCLIS NPL Active Sites CSV."""
    url = _validate_url(SUPERFUND_CSV_URL)
    logger.info("Downloading Superfund NPL sites from %s", url)
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()

    # EPA CSV may be delivered as UTF-8 or latin-1; some rows have unquoted
    # commas in address fields — use on_bad_lines='skip' to tolerate them.
    _read_opts: dict = dict(dtype=str, low_memory=False, on_bad_lines="skip")
    try:
        df = pd.read_csv(io.BytesIO(resp.content), encoding="utf-8", **_read_opts)
    except UnicodeDecodeError:
        df = pd.read_csv(io.BytesIO(resp.content), encoding="latin-1", **_read_opts)

    logger.info("Downloaded %d rows from Superfund CSV", len(df))
    return df


# Column map for the EPA CERCLIS Active Sites export
# Field names vary by year — map all known variants
SUPERFUND_COLUMN_MAP: dict[str, str] = {
    "EPA ID": "epa_id",
    "SITE ID": "epa_id",
    "SITE.ID": "epa_id",
    "EPA.ID": "epa_id",
    "SITE NAME": "site_name",
    "SITE.NAME": "site_name",
    "NAME": "site_name",
    "STREET ADDRESS": "address",
    "STREET": "address",
    "ADDRESS": "address",
    "CITY": "city",
    "STATE": "state_code",
    "ST": "state_code",
    "ZIP": "zip_code",
    "ZIP CODE": "zip_code",
    "COUNTY": "county",
    "HRS SCORE": "hrs_score",
    "HRS.SCORE": "hrs_score",
    "SCORE": "hrs_score",
    "NPL STATUS": "status",
    "STATUS": "status",
    "NPL DATE": "npl_date",
    "NPL.DATE": "npl_date",
    "LATITUDE": "latitude",
    "LAT": "latitude",
    "LONGITUDE": "longitude",
    "LON": "longitude",
    "LONG": "longitude",
    "SITE PROGRESS PROFILE": "epa_progress_url",
}


def _normalize_superfund_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.strip().str.upper()
    return df.rename(columns={col: SUPERFUND_COLUMN_MAP[col]
                               for col in df.columns
                               if col in SUPERFUND_COLUMN_MAP})


def _ingest_superfund(df: pd.DataFrame, conn: object) -> int:
    """Upsert Superfund sites. Returns number of rows processed."""
    rows = 0
    for _, row in df.iterrows():
        epa_id = str(row.get("epa_id", "")).strip()
        if not epa_id:
            continue

        try:
            lat = float(str(row.get("latitude", "")).strip())
            lon = float(str(row.get("longitude", "")).strip())
        except ValueError:
            logger.debug("Skipping %s: invalid coordinates", epa_id)
            continue

        if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
            logger.debug("Skipping %s: out-of-bounds lat=%s lon=%s", epa_id, lat, lon)
            continue

        hrs_raw = str(row.get("hrs_score", "")).strip()
        hrs: float | None = None
        try:
            hrs = float(hrs_raw) if hrs_raw else None
        except ValueError:
            pass

        conn.execute(  # type: ignore[union-attr]
            text(
                "INSERT INTO superfund_sites "
                "(epa_id, name, address, city, state_code, county, zip_code, "
                " status, hrs_score, epa_progress_url, location) "
                "VALUES (:eid, :name, :addr, :city, :state, :county, :zip, "
                "        :status, :hrs, :url, "
                "        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) "
                "ON CONFLICT (epa_id) DO UPDATE SET "
                "  name = EXCLUDED.name, "
                "  address = EXCLUDED.address, "
                "  city = EXCLUDED.city, "
                "  state_code = EXCLUDED.state_code, "
                "  county = EXCLUDED.county, "
                "  zip_code = EXCLUDED.zip_code, "
                "  status = EXCLUDED.status, "
                "  hrs_score = EXCLUDED.hrs_score, "
                "  epa_progress_url = EXCLUDED.epa_progress_url, "
                "  location = EXCLUDED.location"
            ),
            {
                "eid": epa_id,
                "name": str(row.get("site_name", "")).strip() or None,
                "addr": str(row.get("address", "")).strip() or None,
                "city": str(row.get("city", "")).strip() or None,
                "state": str(row.get("state_code", "")).strip() or None,
                "county": str(row.get("county", "")).strip() or None,
                "zip": str(row.get("zip_code", "")).strip() or None,
                "status": str(row.get("status", "")).strip() or None,
                "hrs": hrs,
                "url": str(row.get("epa_progress_url", "")).strip() or None,
                "lat": lat,
                "lon": lon,
            },
        )
        rows += 1
    return rows


def ingest_superfund(db_url: str) -> None:
    """Download EPA CERCLIS NPL sites CSV and upsert into superfund_sites."""
    df_raw = _download_superfund_csv()
    df = _normalize_superfund_columns(df_raw)
    logger.info("Normalized Superfund DataFrame: %d rows, columns: %s", len(df), list(df.columns))

    engine = create_engine(db_url, echo=False)
    with engine.begin() as conn:
        rows = _ingest_superfund(df, conn)

    logger.info("Superfund ingestion complete: %d sites upserted", rows)


def main() -> None:
    """CLI entrypoint: python -m ingestion.superfund_ingest"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Ingest EPA Superfund/NPL sites into PostGIS."
    )
    parser.add_argument(
        "--db-url",
        default=os.environ.get(
            "DATABASE_URL_SYNC",
            "postgresql+psycopg2://postgres:postgres@postgres:5432/toxmap",
        ),
    )
    args = parser.parse_args()

    try:
        ingest_superfund(db_url=args.db_url)
    except Exception:
        logger.exception("Superfund ingestion failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
