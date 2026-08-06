"""Backfill ATSDR ToxFAQs URLs for existing chemicals.

This script updates the `chemicals` table to populate `atsdr_url` from the
ATSDR lookup table in superfund_cas_lookup.py.

Run with:
    python -m backend.scripts.backfill_atsdr_urls

Or via Docker:
    docker-compose exec api python -m scripts.backfill_atsdr_urls
"""

from __future__ import annotations

import logging
import os

from sqlalchemy import text
from sqlalchemy.engine import create_engine

# Import ATSDR lookup
try:
    from app.services.atsdr_urls import ATSDR_URLS as ATSDR_LOOKUP
except ImportError:
    from backend.app.services.atsdr_urls import ATSDR_URLS as ATSDR_LOOKUP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def backfill_atsdr_urls(db_url: str | None = None) -> dict[str, int]:
    """Update chemicals table with ATSDR ToxFAQs URLs.

    Lookup priority:
    1. Exact chemical name match in ATSDR lookup
    2. Chemical family name match (e.g., "ZINC COMPOUNDS" → family "ZINC" → ATSDR URL)

    Returns dict with counts: {'updated': N, 'updated_via_family': M, 'skipped': K}
    """
    if db_url is None:
        db_url = os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg2://toxmap:toxmap@localhost:5432/toxmap",
        )

    # Force synchronous driver - replace asyncpg with psycopg2
    db_url = db_url.replace("+asyncpg", "+psycopg2")

    engine = create_engine(db_url)
    updated = 0
    updated_via_family = 0
    skipped = 0

    with engine.begin() as conn:
        # Get all chemicals that don't have atsdr_url set, including family info
        result = conn.execute(
            text("""
                SELECT c.id, c.name, cf.family_name
                FROM chemicals c
                LEFT JOIN chemical_family_members cfm ON c.id = cfm.chemical_id
                LEFT JOIN chemical_families cf ON cfm.family_id = cf.id
                WHERE c.atsdr_url IS NULL
            """)
        )
        chemicals = result.fetchall()

        logger.info("Found %d chemicals without ATSDR URLs", len(chemicals))

        for chem_id, name, family_name in chemicals:
            name_upper = name.upper() if name else None
            atsdr_url = None

            # 1. Try exact name match
            if name_upper:
                atsdr_url = ATSDR_LOOKUP.get(name_upper)

            # 2. If no match, try family name (e.g., ZINC COMPOUNDS → ZINC)
            source = "exact"
            if not atsdr_url and family_name:
                atsdr_url = ATSDR_LOOKUP.get(family_name.upper())
                if atsdr_url:
                    source = "family"

            if atsdr_url:
                conn.execute(
                    text("UPDATE chemicals SET atsdr_url = :url WHERE id = :id"),
                    {"url": atsdr_url, "id": chem_id},
                )
                if source == "family":
                    updated_via_family += 1
                    logger.debug("Updated %s via family %s → %s", name, family_name, atsdr_url)
                else:
                    updated += 1
                    logger.debug("Updated %s → %s", name, atsdr_url)
            else:
                skipped += 1

    logger.info(
        "Backfill complete: %d updated (exact), %d updated (via family), %d skipped",
        updated,
        updated_via_family,
        skipped,
    )
    return {"updated": updated, "updated_via_family": updated_via_family, "skipped": skipped}


if __name__ == "__main__":
    result = backfill_atsdr_urls()
    print(f"Updated: {result['updated']}, Skipped: {result['skipped']}")
