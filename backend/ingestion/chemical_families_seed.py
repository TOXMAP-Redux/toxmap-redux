"""Seed chemical families data (ADR-007).

Populates chemical_families and chemical_family_members tables with curated
mappings for metals and compound categories. Run after tri_ingest.py so
that the chemicals table is populated.

Usage:
    python -m ingestion.chemical_families_seed
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import NamedTuple

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.chemical import Chemical
from app.models.chemical_family import ChemicalFamily, ChemicalFamilyMember

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class FamilyDef(NamedTuple):
    """Definition of a chemical family."""

    family_name: str
    description: str
    nlm_url: str | None
    epa_url: str | None
    # List of (chemical_name, is_parent) tuples
    members: list[tuple[str, bool]]


# Curated chemical families per ADR-007
CHEMICAL_FAMILIES: list[FamilyDef] = [
    FamilyDef(
        family_name="LEAD",
        description="Lead and all lead compounds — NLM carcinogen class",
        nlm_url="https://www.ncbi.nlm.nih.gov/books/NBK590906/",
        epa_url="https://www.epa.gov/toxics-release-inventory-tri-program/tri-listed-chemicals",
        members=[
            ("LEAD", True),
            ("LEAD COMPOUNDS", False),
            ("LEAD AND LEAD COMPOUNDS", False),
        ],
    ),
    FamilyDef(
        family_name="MERCURY",
        description="Mercury and mercury compounds — NLM carcinogen class",
        nlm_url="https://www.ncbi.nlm.nih.gov/books/NBK590893/",
        epa_url=None,
        members=[
            ("MERCURY", True),
            ("MERCURY COMPOUNDS", False),
            ("MERCURY AND MERCURY COMPOUNDS", False),
        ],
    ),
    FamilyDef(
        family_name="CHROMIUM",
        description="Chromium and chromium compounds",
        nlm_url="https://www.ncbi.nlm.nih.gov/books/NBK590856/",
        epa_url=None,
        members=[
            ("CHROMIUM", True),
            ("CHROMIUM COMPOUNDS", False),
            # Actual TRI name has long suffix - will be matched by normalization
            ("CHROMIUM COMPOUNDS (EXCEPT FOR CHROMITE ORE MINED IN THE TRANSVAAL REGION)", False),
        ],
    ),
    FamilyDef(
        family_name="NICKEL",
        description="Nickel and nickel compounds — NLM carcinogen class",
        nlm_url="https://www.ncbi.nlm.nih.gov/books/NBK590895/",
        epa_url=None,
        members=[
            ("NICKEL", True),
            ("NICKEL COMPOUNDS", False),
        ],
    ),
    FamilyDef(
        family_name="ARSENIC",
        description="Arsenic and inorganic arsenic compounds — known human carcinogen",
        nlm_url="https://www.ncbi.nlm.nih.gov/books/NBK590851/",
        epa_url=None,
        members=[
            ("ARSENIC", True),
            ("ARSENIC COMPOUNDS", False),
        ],
    ),
    FamilyDef(
        family_name="CADMIUM",
        description="Cadmium and cadmium compounds — known human carcinogen",
        nlm_url="https://www.ncbi.nlm.nih.gov/books/NBK590854/",
        epa_url=None,
        members=[
            ("CADMIUM", True),
            ("CADMIUM COMPOUNDS", False),
        ],
    ),
    FamilyDef(
        family_name="MANGANESE",
        description="Manganese and manganese compounds",
        nlm_url=None,
        epa_url=None,
        members=[
            ("MANGANESE", True),
            ("MANGANESE COMPOUNDS", False),
            ("MANGANESE AND MANGANESE COMPOUNDS", False),
        ],
    ),
    FamilyDef(
        family_name="ZINC",
        description="Zinc and zinc compounds",
        nlm_url=None,
        epa_url=None,
        members=[
            ("ZINC COMPOUNDS", True),  # No plain ZINC in TRI
            ("ZINC (FUME OR DUST)", False),
            ("ZINC AND ZINC COMPOUNDS", False),
        ],
    ),
    FamilyDef(
        family_name="COPPER",
        description="Copper and copper compounds",
        nlm_url=None,
        epa_url=None,
        members=[
            ("COPPER", True),
            ("COPPER COMPOUNDS", False),
        ],
    ),
    FamilyDef(
        family_name="COBALT",
        description="Cobalt and cobalt compounds — reasonably anticipated carcinogen",
        nlm_url="https://www.ncbi.nlm.nih.gov/books/NBK590857/",
        epa_url=None,
        members=[
            ("COBALT", True),
            ("COBALT COMPOUNDS", False),
        ],
    ),
    FamilyDef(
        family_name="ANTIMONY",
        description="Antimony and antimony compounds",
        nlm_url=None,
        epa_url=None,
        members=[
            ("ANTIMONY", True),
            ("ANTIMONY COMPOUNDS", False),
        ],
    ),
    FamilyDef(
        family_name="BARIUM",
        description="Barium and barium compounds",
        nlm_url=None,
        epa_url=None,
        members=[
            ("BARIUM", True),
            ("BARIUM COMPOUNDS", False),
        ],
    ),
    FamilyDef(
        family_name="BERYLLIUM",
        description="Beryllium and beryllium compounds — known human carcinogen",
        nlm_url="https://www.ncbi.nlm.nih.gov/books/NBK590853/",
        epa_url=None,
        members=[
            ("BERYLLIUM", True),
            ("BERYLLIUM COMPOUNDS", False),
        ],
    ),
    FamilyDef(
        family_name="SELENIUM",
        description="Selenium and selenium compounds",
        nlm_url=None,
        epa_url=None,
        members=[
            ("SELENIUM", True),
            ("SELENIUM COMPOUNDS", False),
        ],
    ),
    FamilyDef(
        family_name="SILVER",
        description="Silver and silver compounds",
        nlm_url=None,
        epa_url=None,
        members=[
            ("SILVER", True),
            ("SILVER COMPOUNDS", False),
            ("SILVER AND SILVER COMPOUNDS", False),
        ],
    ),
    FamilyDef(
        family_name="THALLIUM",
        description="Thallium and thallium compounds",
        nlm_url=None,
        epa_url=None,
        members=[
            ("THALLIUM", True),
            ("THALLIUM COMPOUNDS", False),
            ("THALLIUM AND THALLIUM COMPOUNDS", False),
        ],
    ),
    FamilyDef(
        family_name="VANADIUM",
        description="Vanadium and vanadium compounds",
        nlm_url=None,
        epa_url=None,
        members=[
            ("VANADIUM", True),
            ("VANADIUM COMPOUNDS", False),
            ("VANADIUM (EXCEPT WHEN CONTAINED IN AN ALLOY)", False),
        ],
    ),
    FamilyDef(
        family_name="CYANIDE",
        description="Cyanide and cyanide compounds",
        nlm_url=None,
        epa_url=None,
        members=[
            ("CYANIDE COMPOUNDS", True),  # No plain CYANIDE in TRI
            ("HYDROGEN CYANIDE", False),
        ],
    ),
]


def _normalize_chemical_name(name: str) -> str:
    """Normalize chemical name: uppercase, collapse whitespace."""
    return re.sub(r"\s+", " ", name.upper().strip())


async def seed_chemical_families(session: AsyncSession) -> None:
    """Populate chemical_families and chemical_family_members tables."""

    # Build a lookup of chemical names to IDs (normalized)
    result = await session.execute(select(Chemical.id, Chemical.name))
    chemical_lookup = {_normalize_chemical_name(row.name): row.id for row in result.all()}

    families_inserted = 0
    members_inserted = 0

    for family_def in CHEMICAL_FAMILIES:
        # Upsert family
        family_stmt = (
            insert(ChemicalFamily)
            .values(
                family_name=family_def.family_name,
                description=family_def.description,
                nlm_url=family_def.nlm_url,
                epa_url=family_def.epa_url,
            )
            .on_conflict_do_update(
                index_elements=["family_name"],
                set_={
                    "description": family_def.description,
                    "nlm_url": family_def.nlm_url,
                    "epa_url": family_def.epa_url,
                },
            )
            .returning(ChemicalFamily.id)
        )

        result = await session.execute(family_stmt)
        family_id = result.scalar_one()
        families_inserted += 1

        # Insert members
        for chem_name, is_parent in family_def.members:
            normalized_name = _normalize_chemical_name(chem_name)
            chem_id = chemical_lookup.get(normalized_name)
            if chem_id is None:
                logger.warning(
                    "Chemical '%s' not found in database for family '%s'",
                    chem_name,
                    family_def.family_name,
                )
                continue

            member_stmt = (
                insert(ChemicalFamilyMember)
                .values(
                    chemical_id=chem_id,
                    family_id=family_id,
                    is_parent=is_parent,
                )
                .on_conflict_do_update(
                    index_elements=["chemical_id", "family_id"],
                    set_={"is_parent": is_parent},
                )
            )
            await session.execute(member_stmt)
            members_inserted += 1

    await session.commit()
    logger.info(
        "Seeded %d chemical families with %d member mappings",
        families_inserted,
        members_inserted,
    )


async def main() -> None:
    """Entry point."""
    async with AsyncSessionLocal() as session:
        await seed_chemical_families(session)


if __name__ == "__main__":
    asyncio.run(main())
