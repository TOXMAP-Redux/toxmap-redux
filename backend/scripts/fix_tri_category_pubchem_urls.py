#!/usr/bin/env python3
"""Fix broken PubChem URLs for TRI chemical categories (N### codes).

Bug 7.BUG.22: TRI category codes (N010, N090, N100, etc.) are EPA Form R codes,
NOT CAS numbers. PubChem URLs like /compound/N090 return 404.

This script:
1. Finds all chemicals with TRI category codes as CAS numbers
2. Updates their pubchem_url to correct PubChem element or search URLs
3. Also clears the invalid cas_number since these are categories, not compounds

Usage:
    docker-compose exec backend python -m scripts.fix_tri_category_pubchem_urls
    docker-compose exec backend python -m scripts.fix_tri_category_pubchem_urls --dry-run
"""

from __future__ import annotations

import argparse
import logging
import sys

from sqlalchemy import create_engine, text

from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Create sync engine from async URL (replace asyncpg with psycopg2)
sync_url = (
    str(settings.database_url).replace("+asyncpg", "").replace("postgresql://", "postgresql://")
)
sync_engine = create_engine(sync_url)

# Mapping of TRI category codes to correct PubChem URLs
# For element compounds, use /element/{Element}
# For chemical classes, use search URLs or None
TRI_CATEGORY_PUBCHEM = {
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
    "N770": "https://pubchem.ncbi.nlm.nih.gov/compound/Vanadium",  # VANADIUM COMPOUNDS
    "N982": "https://pubchem.ncbi.nlm.nih.gov/element/Zinc",  # ZINC COMPOUNDS
    # Other categories → specific compound or search URL
    "N084": "https://pubchem.ncbi.nlm.nih.gov/#query=chlorophenols",  # CHLOROPHENOLS
    "N106": "https://pubchem.ncbi.nlm.nih.gov/compound/Cyanide",  # CYANIDE COMPOUNDS
    "N120": "https://pubchem.ncbi.nlm.nih.gov/#query=diisocyanates",  # DIISOCYANATES
    "N125": "https://pubchem.ncbi.nlm.nih.gov/compound/590836",  # DINP
    "N150": "https://pubchem.ncbi.nlm.nih.gov/#query=dioxin",  # DIOXIN COMPOUNDS
    "N171": "https://pubchem.ncbi.nlm.nih.gov/#query=ethylenebisdithiocarbamic",  # EBDC
    "N230": "https://pubchem.ncbi.nlm.nih.gov/#query=glycol+ethers",  # GLYCOL ETHERS
    "N270": "https://pubchem.ncbi.nlm.nih.gov/compound/18529",  # HBCD
    "N503": "https://pubchem.ncbi.nlm.nih.gov/compound/89594",  # NICOTINE
    "N511": None,  # NITRATE COMPOUNDS - too broad
    "N530": "https://pubchem.ncbi.nlm.nih.gov/compound/1752",  # NONYLPHENOL
    "N535": "https://pubchem.ncbi.nlm.nih.gov/#query=nonylphenol+ethoxylates",  # NPEs
    "N575": "https://pubchem.ncbi.nlm.nih.gov/#query=polybrominated+biphenyls",  # PBBs
    "N583": "https://pubchem.ncbi.nlm.nih.gov/#query=polychlorinated+alkanes",  # PCAs
    "N590": "https://pubchem.ncbi.nlm.nih.gov/#query=polycyclic+aromatic",  # PACs
    "N746": "https://pubchem.ncbi.nlm.nih.gov/compound/441071",  # STRYCHNINE
    "N874": "https://pubchem.ncbi.nlm.nih.gov/compound/54678486",  # WARFARIN
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )
    args = parser.parse_args()

    with sync_engine.connect() as conn:
        # Find all chemicals with TRI category codes (N###) as CAS numbers
        result = conn.execute(
            text("""
                SELECT id, name, cas_number, pubchem_url
                FROM chemicals
                WHERE cas_number ~ '^N[0-9]{3}$'
                ORDER BY cas_number
            """)
        )
        rows = result.fetchall()

        if not rows:
            logger.info("No chemicals with TRI category codes found. Nothing to fix.")
            return 0

        logger.info("Found %d chemicals with TRI category codes (N###):", len(rows))
        for row in rows:
            logger.info("  [%s] %s — current URL: %s", row.cas_number, row.name, row.pubchem_url)

        if args.dry_run:
            logger.info("\n--- DRY RUN: No changes made ---")
            logger.info("\nProposed changes:")
            for row in rows:
                new_url = TRI_CATEGORY_PUBCHEM.get(row.cas_number)
                if new_url != row.pubchem_url:
                    logger.info("  [%s] %s", row.cas_number, row.name)
                    logger.info("    OLD: %s", row.pubchem_url)
                    logger.info("    NEW: %s", new_url)
            return 0

        # Update each chemical with the correct PubChem URL
        updated = 0
        for row in rows:
            new_url = TRI_CATEGORY_PUBCHEM.get(row.cas_number)
            if new_url != row.pubchem_url:
                conn.execute(
                    text("""
                        UPDATE chemicals
                        SET pubchem_url = :new_url
                        WHERE id = :id
                    """),
                    {"new_url": new_url, "id": row.id},
                )
                updated += 1
                logger.info("Updated [%s] %s → %s", row.cas_number, row.name, new_url or "(NULL)")

        conn.commit()
        logger.info("\n✅ Updated %d of %d chemicals with TRI category codes.", updated, len(rows))

        # Verify the fix
        result = conn.execute(
            text("""
                SELECT COUNT(*) FROM chemicals
                WHERE pubchem_url LIKE '%/compound/N%'
            """)
        )
        remaining = result.scalar()
        if remaining:
            logger.warning("⚠️ %d chemicals still have broken /compound/N### URLs!", remaining)
            return 1
        else:
            logger.info("✅ No broken /compound/N### URLs remain.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
