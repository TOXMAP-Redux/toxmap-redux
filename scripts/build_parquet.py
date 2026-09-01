#!/usr/bin/env python3
"""Parquet build pipeline: PostGIS → .parquet + .meta.json + manifest.json.

Stories 1.5.1, 1.5.3, 1.5.4 — produces files consumed by DuckDB WASM in production.

Output files:
  tri_{YYYY}.parquet            TRI facility + release data for one year
  tri_{YYYY}.meta.json          Sidecar: vintage_label, row_count, schema_version, etc.
  superfund.parquet             All Superfund/NPL sites
  superfund.meta.json           Sidecar
  manifest.json                 Index of all built Parquet vintages (R2 root file)

Usage:
    python scripts/build_parquet.py --year 2022 --vintage-label "October 2024 freeze"
    python scripts/build_parquet.py --year 2022 --vintage-label "Oct 2024" --output-dir ./data/parquet

Security guardrails:
- No user input reaches SQL (parameterized queries only).
- Output paths are restricted to --output-dir (no path traversal).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Schema version — increment when column set changes incompatibly
SCHEMA_VERSION = "1.0.0"

# EPA TRI source URL (displayed in meta.json for auditability)
TRI_SOURCE_URL_PATTERN = (
    "https://www.epa.gov/toxics-release-inventory-tri-program/"
    "tri-basic-data-files-calendar-years-1987-{year}"
)
SUPERFUND_SOURCE_URL = (
    "https://www.epa.gov/superfund/superfund-data-and-reports"
)


def _safe_output_path(output_dir: Path, filename: str) -> Path:
    """Return a safe output path within output_dir. Rejects path traversal."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise ValueError(f"Unsafe filename: {filename!r}")
    return output_dir / filename


def _build_tri_parquet(year: int, db_url: str, output_dir: Path, vintage_label: str) -> dict:
    """Query PostGIS for TRI data for a given year and write to Parquet.

    Returns the meta.json content as a dict.
    """
    try:
        import pandas as pd
        import pyarrow as pa
        import pyarrow.parquet as pq
        from sqlalchemy import text
        from sqlalchemy.engine import create_engine
    except ImportError as e:
        raise RuntimeError(
            "pyarrow and pandas are required. Install with: "
            "pip install 'toxmap-backend[ingestion]'"
        ) from e

    engine = create_engine(db_url, echo=False)

    query = text("""
        SELECT
            f.tri_facility_id,
            f.name                   AS facility_name,
            f.address,
            f.city,
            f.state_code,
            f.zip_code,
            f.county,
            f.naics_code,
            f.naics_desc,
            ST_Y(f.location)         AS latitude,
            ST_X(f.location)         AS longitude,
            c.cas_number,
            c.name                   AS chemical_name,
            c.category               AS chemical_category,
            r.reporting_year,
            r.total_release_lbs,
            r.air_release_lbs,
            r.water_release_lbs,
            r.land_release_lbs,
            r.underground_release_lbs,
            r.off_site_lbs,
            r.unit_of_measure,
            r.form_type
        FROM release_events r
        JOIN facilities f ON f.id = r.facility_id
        JOIN chemicals c ON c.id = r.chemical_id
        WHERE r.reporting_year = :year
        ORDER BY f.tri_facility_id, c.name
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"year": year})

    logger.info("TRI %d: %d rows loaded from PostGIS", year, len(df))

    parquet_file = _safe_output_path(output_dir, f"tri_{year}.parquet")
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, str(parquet_file), compression="snappy")
    logger.info("Wrote %s (%d bytes)", parquet_file, parquet_file.stat().st_size)

    meta = {
        "vintage_label": vintage_label,
        "year": year,
        "epa_source_url": TRI_SOURCE_URL_PATTERN.format(year=year),
        "row_count": len(df),
        "schema_version": SCHEMA_VERSION,
        "build_timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
        "parquet_file": parquet_file.name,
    }
    meta_file = _safe_output_path(output_dir, f"tri_{year}.meta.json")
    meta_file.write_text(json.dumps(meta, indent=2))
    logger.info("Wrote %s", meta_file)

    return meta


def _build_superfund_parquet(db_url: str, output_dir: Path, vintage_label: str) -> dict:
    """Query PostGIS for all Superfund sites and write to Parquet."""
    try:
        import pandas as pd
        import pyarrow as pa
        import pyarrow.parquet as pq
        from sqlalchemy import text
        from sqlalchemy.engine import create_engine
    except ImportError as e:
        raise RuntimeError("pyarrow and pandas required") from e

    engine = create_engine(db_url, echo=False)

    query = text("""
        SELECT
            epa_id,
            name,
            address,
            city,
            state_code,
            county,
            zip_code,
            status,
            hrs_score,
            npl_date::text AS npl_date,
            epa_progress_url,
            contaminants,
            ST_Y(location) AS latitude,
            ST_X(location) AS longitude
        FROM superfund_sites
        ORDER BY epa_id
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    logger.info("Superfund: %d rows loaded from PostGIS", len(df))

    parquet_file = _safe_output_path(output_dir, "superfund.parquet")
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, str(parquet_file), compression="snappy")
    logger.info("Wrote %s", parquet_file)

    meta = {
        "vintage_label": vintage_label,
        "epa_source_url": SUPERFUND_SOURCE_URL,
        "row_count": len(df),
        "schema_version": SCHEMA_VERSION,
        "build_timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
        "parquet_file": parquet_file.name,
    }
    meta_file = _safe_output_path(output_dir, "superfund.meta.json")
    meta_file.write_text(json.dumps(meta, indent=2))

    return meta


def _update_manifest(
    output_dir: Path,
    year: int,
    vintage_label: str,
    tri_meta: dict,
    superfund_meta: dict,
) -> None:
    """Update (or create) manifest.json with the new vintage entry.

    Story 1.5.4: manifest.json schema.
    Required fields per spec:
      vintage_label, year, tri_parquet_key, superfund_parquet_key,
      census_parquet_key, build_timestamp_utc, epa_vintage_label
    """
    manifest_file = _safe_output_path(output_dir, "manifest.json")

    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text())
    else:
        manifest = {"vintages": []}

    # Remove any existing entry for this year
    manifest["vintages"] = [
        v for v in manifest.get("vintages", []) if v.get("year") != year
    ]

    manifest["vintages"].append({
        "vintage_label": vintage_label,
        "year": year,
        "tri_parquet_key": tri_meta["parquet_file"],
        "superfund_parquet_key": superfund_meta["parquet_file"],
        "census_parquet_key": None,   # populated in Phase 7 (story 1.5.5)
        "build_timestamp_utc": tri_meta["build_timestamp_utc"],
        "epa_vintage_label": vintage_label,  # non-empty per Phase 1 DoD gate
        "row_count": tri_meta["row_count"],
        "schema_version": SCHEMA_VERSION,
    })

    # Sort by year descending (latest first)
    manifest["vintages"].sort(key=lambda v: v.get("year", 0), reverse=True)
    manifest_file.write_text(json.dumps(manifest, indent=2))
    logger.info("manifest.json updated: %d entries", len(manifest["vintages"]))


def validate_parquet_seeds(output_dir: Path, year: int) -> None:
    """Story 1.5.3: validate T-03 seed assertion in the built Parquet.

    Raises AssertionError if the assertion fails — ingestion must stop.
    """
    try:
        import duckdb
    except ImportError:
        logger.warning("duckdb not installed — skipping Parquet seed validation")
        return

    parquet_file = _safe_output_path(output_dir, f"tri_{year}.parquet")
    if not parquet_file.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_file}")

    # T-03 assertion: 89319BHPCP7MILE → COPPER → 8205.0 → land → 2008
    con = duckdb.connect()
    result = con.execute(
        """
        SELECT total_release_lbs, land_release_lbs
        FROM read_parquet(?)
        WHERE tri_facility_id = '89319BHPCP7MILE'
          AND chemical_name ILIKE '%copper%'
          AND reporting_year = 2008
        """,
        [str(parquet_file)],
    ).fetchone()

    if result is None:
        raise AssertionError(
            "T-03 Parquet validation FAILED: "
            "89319BHPCP7MILE / COPPER / 2008 row not found in Parquet output. "
            "Data integrity compromised — escalate per AGENTS.md §12."
        )

    total_lbs, land_lbs = result
    if float(total_lbs) != 8205.0 or float(land_lbs) != 8205.0:
        raise AssertionError(
            f"T-03 Parquet validation FAILED: expected total=8205.0 land=8205.0, "
            f"got total={total_lbs} land={land_lbs}. "
            "Data integrity compromised — escalate per AGENTS.md §12."
        )

    logger.info(
        "T-03 Parquet validation PASSED: 89319BHPCP7MILE → COPPER → %s lbs → land → 2008",
        total_lbs,
    )


def _build_chemical_families_json(db_url: str, output_dir: Path) -> dict | None:
    """Export chemical family mappings for frontend DuckDB WASM mode (ADR-007, Algorithms Handbook Phase 2b).

    Output: chemical_families.json
    Format: { "LEAD": ["LEAD", "LEAD COMPOUNDS"], "MERCURY": [...], ... }

    This enables the frontend to expand chemical families without API calls,
    matching the backend's in-memory cache behavior.
    """
    from sqlalchemy import text
    from sqlalchemy.engine import create_engine

    engine = create_engine(db_url, echo=False)

    query = text("""
        SELECT
            cf.family_name,
            array_agg(c.name ORDER BY c.name) AS chemicals
        FROM chemical_families cf
        JOIN chemical_family_members cfm ON cfm.family_id = cf.id
        JOIN chemicals c ON c.id = cfm.chemical_id
        GROUP BY cf.id, cf.family_name
        ORDER BY cf.family_name
    """)

    try:
        with engine.connect() as conn:
            result = conn.execute(query)
            rows = result.fetchall()
    except Exception as exc:
        # Tables might not exist (e.g., fresh DB without ingestion)
        logger.warning("Could not query chemical families: %s", exc)
        return None

    if not rows:
        logger.info("No chemical families found, skipping chemical_families.json")
        return None

    # Build the mapping: chemical_name → list of family members
    families: dict[str, list[str]] = {}
    for row in rows:
        family_name, chemicals = row
        for chem in chemicals:
            families[chem.upper()] = list(chemicals)

    output_file = _safe_output_path(output_dir, "chemical_families.json")
    output_file.write_text(json.dumps(families, indent=2, sort_keys=True))
    logger.info("Wrote %s (%d chemicals in families)", output_file, len(families))

    return {
        "file": output_file.name,
        "chemical_count": len(families),
        "family_count": len(rows),
    }


def main() -> None:
    """CLI entrypoint: python scripts/build_parquet.py --year YYYY --vintage-label '...'"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    parser = argparse.ArgumentParser(
        description=(
            "Build Parquet files from PostGIS data for DuckDB WASM production use."
        )
    )
    parser.add_argument("--year", type=int, required=True, help="TRI reporting year")
    parser.add_argument(
        "--vintage-label",
        required=True,
        help='Human-readable vintage label (e.g. "October 2024 freeze")',
    )
    parser.add_argument(
        "--output-dir",
        default=os.environ.get("PARQUET_OUTPUT_DIR", "./data/parquet"),
        help="Directory to write Parquet and meta.json files",
    )
    parser.add_argument(
        "--db-url",
        default=os.environ.get(
            "DATABASE_URL_SYNC",
            "postgresql+psycopg2://postgres:postgres@postgres:5432/toxmap",
        ),
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip T-03 seed assertion (only for testing with partial data)",
    )
    args = parser.parse_args()

    if args.year < 1987 or args.year > 2030:
        parser.error(f"--year must be between 1987 and 2030, got {args.year}")

    if not args.vintage_label.strip():
        parser.error("--vintage-label must be non-empty")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        tri_meta = _build_tri_parquet(
            year=args.year,
            db_url=args.db_url,
            output_dir=output_dir,
            vintage_label=args.vintage_label,
        )
        superfund_meta = _build_superfund_parquet(
            db_url=args.db_url,
            output_dir=output_dir,
            vintage_label=args.vintage_label,
        )
        # Phase 2b: chemical families for frontend family expansion
        _build_chemical_families_json(
            db_url=args.db_url,
            output_dir=output_dir,
        )
        _update_manifest(
            output_dir=output_dir,
            year=args.year,
            vintage_label=args.vintage_label,
            tri_meta=tri_meta,
            superfund_meta=superfund_meta,
        )

        if not args.skip_validation:
            validate_parquet_seeds(output_dir=output_dir, year=args.year)

        logger.info("Parquet build complete for year %d, vintage %r", args.year, args.vintage_label)
    except AssertionError:
        logger.error("Parquet seed validation failed — see above. Escalate to human.")
        sys.exit(2)
    except Exception:
        logger.exception("Parquet build failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
