"""Superfund / NPL site ingestion script.

Stories 1.3.1–1.3.2 — EPA ArcGIS Superfund Feature Service → PostGIS superfund_sites.

Security guardrails (AGENTS.md §11, T-SEC-12 SSRF prevention):
- ARCGIS_BASE_URL is an allow-listed constant.
- All SQL uses parameterized statements.

Data source (as of 2026-07):
- EPA ArcGIS Feature Service: FAC_Superfund_Site_Boundaries_EPA_Public
- Updated weekly; contains Final NPL, Proposed, and Deleted sites with polygon centroids.
- Old semspub.epa.gov/src/document/HQ/100001259 is defunct (301 → errorpage).

Usage:
    python -m ingestion.superfund_ingest
    python -m ingestion.superfund_ingest --db-url postgresql+psycopg2://...
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Any

import pandas as pd
import requests
from sqlalchemy import text
from sqlalchemy.engine import create_engine

logger = logging.getLogger(__name__)

# ── SSRF prevention (T-SEC-12) ────────────────────────────────────────────────
ARCGIS_BASE_URL = "https://services.arcgis.com/"
ENVIROFACTS_BASE_URL = "https://data.epa.gov/dmapservice/"

# EPA ArcGIS Feature Service for Superfund site boundaries
# Returns polygon boundaries; we use returnCentroid=true to get point coordinates
SUPERFUND_ARCGIS_URL = (
    "https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/"
    "FAC_Superfund_Site_Boundaries_EPA_Public/FeatureServer/0/query"
)

# EPA Envirofacts SEMS tables for site info and contaminants
SEMS_SITE_URL = "https://data.epa.gov/dmapservice/sems.envirofacts_site"
SEMS_CONTAMINANTS_URL = "https://data.epa.gov/dmapservice/sems.envirofacts_contaminants"

# NPL status codes to include:
#   F = Currently on the Final NPL
#   P = Proposed for NPL
#   D = Deleted from the Final NPL
NPL_STATUS_CODES = ("F", "P", "D")

# WGS84 bounds for validation
LAT_MIN, LAT_MAX = 17.0, 72.0
LON_MIN, LON_MAX = -180.0, -65.0

# ArcGIS query batch size (service typically allows up to 2000)
BATCH_SIZE = 1000

# EPA Superfund Site Profile URL template (uses SEMS site_id, not epa_id)
# Example: https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.Cleanup&id=0302388
EPA_PROGRESS_URL_TEMPLATE = (
    "https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.Cleanup&id={site_id}"
)


def _validate_url(url: str) -> str:
    """Raise ValueError if url is not under an allow-listed prefix."""
    allowed_prefixes = (ARCGIS_BASE_URL, ENVIROFACTS_BASE_URL)
    if not any(url.startswith(prefix) for prefix in allowed_prefixes):
        raise ValueError(f"SSRF guard: URL {url!r} is not under allowed prefixes")
    return url


def _npl_status_to_text(code: str | None) -> str | None:
    """Convert NPL status code to human-readable text."""
    mapping = {
        "F": "NPL",  # Currently on Final NPL
        "P": "Proposed",  # Proposed for NPL
        "D": "Deleted",  # Deleted from Final NPL
    }
    return mapping.get(code) if code else None


def _fetch_sems_site_ids(epa_ids: list[str]) -> dict[str, str]:
    """Fetch SEMS site_id for each EPA ID using bulk query.

    Returns mapping of epa_id → site_id.
    """
    _validate_url(SEMS_SITE_URL)

    epa_id_to_site_id: dict[str, str] = {}
    epa_id_set = set(epa_ids)

    # Fetch all NPL sites in bulk (F, P, D status codes)
    for status_code in NPL_STATUS_CODES:
        offset = 1
        batch_size = 5000

        while True:
            try:
                url = f"{SEMS_SITE_URL}/npl_status_code/equals/{status_code}/{offset}:{offset + batch_size - 1}/json"
                resp = requests.get(url, timeout=120)
                resp.raise_for_status()
                data = resp.json()

                if not data:
                    break

                for record in data:
                    epa_id = record.get("epa_id")
                    site_id = record.get("site_id")
                    if epa_id and site_id and epa_id in epa_id_set:
                        epa_id_to_site_id[epa_id] = site_id

                logger.info(
                    "  SEMS %s: fetched %d records (mapped: %d)",
                    status_code,
                    len(data),
                    len(epa_id_to_site_id),
                )

                if len(data) < batch_size:
                    break

                offset += batch_size

            except (requests.RequestException, ValueError) as exc:
                logger.warning(
                    "Failed to fetch SEMS sites (%s offset %d): %s", status_code, offset, exc
                )
                break

    logger.info("Resolved %d EPA IDs to SEMS site_ids", len(epa_id_to_site_id))
    return epa_id_to_site_id


def _fetch_contaminants(site_ids: list[str]) -> dict[str, list[str]]:
    """Fetch contaminants for each SEMS site_id using bulk query.

    Returns mapping of site_id → list of unique contaminant names.
    """
    _validate_url(SEMS_CONTAMINANTS_URL)

    site_contaminants: dict[str, set[str]] = {}
    site_id_set = set(site_ids)

    # Fetch all contaminants in bulk pages
    offset = 1
    batch_size = 10000
    total_fetched = 0

    while True:
        try:
            url = f"{SEMS_CONTAMINANTS_URL}/{offset}:{offset + batch_size - 1}/json"
            resp = requests.get(url, timeout=120)
            resp.raise_for_status()
            data = resp.json()

            if not data:
                break

            for record in data:
                site_id = record.get("fk_site_id")
                name = record.get("preferred_contaminant_name")
                if site_id and name and site_id in site_id_set:
                    if site_id not in site_contaminants:
                        site_contaminants[site_id] = set()
                    site_contaminants[site_id].add(name.strip())

            total_fetched += len(data)
            logger.info(
                "  Contaminants: fetched %d records (total: %d, sites with data: %d)",
                len(data),
                total_fetched,
                len(site_contaminants),
            )

            if len(data) < batch_size:
                break

            offset += batch_size

        except (requests.RequestException, ValueError) as exc:
            logger.warning("Failed to fetch contaminants (offset %d): %s", offset, exc)
            break

    # Convert sets to sorted lists
    result = {site_id: sorted(names) for site_id, names in site_contaminants.items()}
    logger.info("Fetched contaminants for %d sites", len(result))
    return result


def _download_superfund_arcgis() -> pd.DataFrame:
    """Download EPA Superfund NPL sites from ArcGIS Feature Service.

    Uses pagination to retrieve all sites, requesting polygon centroids
    as point coordinates.
    """
    _validate_url(SUPERFUND_ARCGIS_URL)

    # Build WHERE clause for NPL sites only
    status_filter = ",".join(f"'{s}'" for s in NPL_STATUS_CODES)
    where_clause = f"NPL_STATUS_CODE IN ({status_filter})"

    # Fields to retrieve
    out_fields = (
        "EPA_ID,SITE_NAME,STREET_ADDR_TXT,CITY_NAME,STATE_CODE,COUNTY,ZIP_CODE,NPL_STATUS_CODE"
    )

    all_features: list[dict[str, Any]] = []
    offset = 0

    logger.info("Downloading Superfund NPL sites from ArcGIS Feature Service")

    while True:
        params = {
            "where": where_clause,
            "outFields": out_fields,
            "returnGeometry": "false",
            "returnCentroid": "true",
            "f": "json",
            "resultOffset": offset,
            "resultRecordCount": BATCH_SIZE,
        }

        resp = requests.get(SUPERFUND_ARCGIS_URL, params=params, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            raise RuntimeError(f"ArcGIS query error: {data['error']}")

        features = data.get("features", [])
        if not features:
            break

        all_features.extend(features)
        logger.info("  Fetched %d sites (total: %d)", len(features), len(all_features))

        # Check if there are more records
        if not data.get("exceededTransferLimit", False):
            break

        offset += BATCH_SIZE

    logger.info("Downloaded %d Superfund NPL sites from ArcGIS", len(all_features))

    # Convert to DataFrame
    rows = []
    for feat in all_features:
        attrs = feat.get("attributes", {})
        centroid = feat.get("centroid", {})

        rows.append(
            {
                "epa_id": attrs.get("EPA_ID"),
                "site_name": attrs.get("SITE_NAME"),
                "address": attrs.get("STREET_ADDR_TXT"),
                "city": attrs.get("CITY_NAME"),
                "state_code": attrs.get("STATE_CODE"),
                "county": attrs.get("COUNTY"),
                "zip_code": attrs.get("ZIP_CODE"),
                "status": _npl_status_to_text(attrs.get("NPL_STATUS_CODE")),
                "latitude": centroid.get("y"),
                "longitude": centroid.get("x"),
            }
        )

    return pd.DataFrame(rows)


def _ingest_superfund(
    df: pd.DataFrame,
    conn: object,
    epa_to_contaminants: dict[str, list[str]] | None = None,
    epa_to_site_id: dict[str, str] | None = None,
) -> int:
    """Upsert Superfund sites with contaminants and EPA progress URLs.

    Args:
        df: DataFrame with site data from ArcGIS.
        conn: Database connection.
        epa_to_contaminants: Mapping of EPA ID → list of contaminant names.
        epa_to_site_id: Mapping of EPA ID → SEMS site_id (for building EPA progress URLs).

    Returns:
        Number of rows processed.
    """
    rows = 0
    skipped = 0
    contaminants_map = epa_to_contaminants or {}
    site_id_map = epa_to_site_id or {}

    for _, row in df.iterrows():
        epa_id = str(row.get("epa_id") or "").strip()
        if not epa_id:
            skipped += 1
            continue

        lat = row.get("latitude")
        lon = row.get("longitude")

        if lat is None or lon is None:
            logger.debug("Skipping %s: missing coordinates", epa_id)
            skipped += 1
            continue

        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            logger.debug("Skipping %s: invalid coordinates", epa_id)
            skipped += 1
            continue

        if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
            logger.debug("Skipping %s: out-of-bounds lat=%s lon=%s", epa_id, lat, lon)
            skipped += 1
            continue

        # Get contaminants for this site (or None if not available)
        contaminants = contaminants_map.get(epa_id)

        # Build EPA progress URL from SEMS site_id (if available)
        site_id = site_id_map.get(epa_id)
        epa_progress_url = (
            EPA_PROGRESS_URL_TEMPLATE.format(site_id=site_id) if site_id else None
        )

        conn.execute(  # type: ignore[union-attr]
            text(
                "INSERT INTO superfund_sites "
                "(epa_id, name, address, city, state_code, county, zip_code, "
                " status, contaminants, epa_progress_url, location) "
                "VALUES (:eid, :name, :addr, :city, :state, :county, :zip, "
                "        :status, :contaminants, :epa_progress_url, "
                "        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) "
                "ON CONFLICT (epa_id) DO UPDATE SET "
                "  name = EXCLUDED.name, "
                "  address = EXCLUDED.address, "
                "  city = EXCLUDED.city, "
                "  state_code = EXCLUDED.state_code, "
                "  county = EXCLUDED.county, "
                "  zip_code = EXCLUDED.zip_code, "
                "  status = EXCLUDED.status, "
                "  contaminants = COALESCE(EXCLUDED.contaminants, superfund_sites.contaminants), "
                "  epa_progress_url = COALESCE(EXCLUDED.epa_progress_url, superfund_sites.epa_progress_url), "
                "  location = EXCLUDED.location"
            ),
            {
                "eid": epa_id,
                "name": str(row.get("site_name") or "").strip() or None,
                "addr": str(row.get("address") or "").strip() or None,
                "city": str(row.get("city") or "").strip() or None,
                "state": str(row.get("state_code") or "").strip() or None,
                "county": str(row.get("county") or "").strip() or None,
                "zip": str(row.get("zip_code") or "").strip() or None,
                "status": str(row.get("status") or "").strip() or None,
                "contaminants": contaminants,
                "epa_progress_url": epa_progress_url,
                "lat": lat,
                "lon": lon,
            },
        )
        rows += 1

    if skipped:
        logger.info("Skipped %d sites with missing/invalid data", skipped)

    return rows


def ingest_superfund(db_url: str, skip_contaminants: bool = False) -> None:
    """Download EPA Superfund NPL sites and upsert into superfund_sites.

    Args:
        db_url: PostgreSQL connection URL.
        skip_contaminants: If True, skip fetching contaminants from SEMS API.
    """
    df = _download_superfund_arcgis()
    logger.info("Superfund DataFrame: %d rows, columns: %s", len(df), list(df.columns))

    epa_to_contaminants: dict[str, list[str]] = {}
    epa_to_site_id: dict[str, str] = {}

    if not skip_contaminants:
        # Fetch contaminants from SEMS Envirofacts API
        epa_ids = df["epa_id"].dropna().unique().tolist()
        logger.info("Fetching SEMS site IDs for %d EPA IDs...", len(epa_ids))

        epa_to_site_id = _fetch_sems_site_ids(epa_ids)
        logger.info("Resolved %d EPA IDs to SEMS site_ids (for EPA progress URLs)", len(epa_to_site_id))

        if epa_to_site_id:
            # Fetch contaminants for each site
            site_ids = list(epa_to_site_id.values())
            logger.info("Fetching contaminants for %d sites from SEMS...", len(site_ids))

            site_to_contaminants = _fetch_contaminants(site_ids)

            # Map back to EPA IDs
            for epa_id, site_id in epa_to_site_id.items():
                contaminants = site_to_contaminants.get(site_id)
                if contaminants:
                    epa_to_contaminants[epa_id] = contaminants

            logger.info("Mapped contaminants for %d sites", len(epa_to_contaminants))

    engine = create_engine(db_url, echo=False)
    with engine.begin() as conn:
        rows = _ingest_superfund(df, conn, epa_to_contaminants, epa_to_site_id)

    logger.info("Superfund ingestion complete: %d sites upserted", rows)


def main() -> None:
    """CLI entrypoint: python -m ingestion.superfund_ingest"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    parser = argparse.ArgumentParser(description="Ingest EPA Superfund/NPL sites into PostGIS.")
    parser.add_argument(
        "--db-url",
        default=os.environ.get(
            "DATABASE_URL_SYNC",
            "postgresql+psycopg2://postgres:postgres@postgres:5432/toxmap",
        ),
    )
    parser.add_argument(
        "--skip-contaminants",
        action="store_true",
        help="Skip fetching contaminants from SEMS API (faster, but no contaminant data).",
    )
    args = parser.parse_args()

    try:
        ingest_superfund(db_url=args.db_url, skip_contaminants=args.skip_contaminants)
    except Exception:
        logger.exception("Superfund ingestion failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
