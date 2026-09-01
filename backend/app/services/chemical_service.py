"""Service layer for chemical list and search queries.

Phase 2 — stories 2.5.x.
ADR-007 — Chemical families for transparent right-to-know search.

Performance optimization (Algorithms Handbook §10, Phase 2):
Chemical family lookups are cached in-memory at startup. Families are static
data (~100 members across ~15 families) that changes only via ingestion.
This eliminates 6 DB queries per facility search request.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chemical import Chemical
from app.models.chemical_family import ChemicalFamily, ChemicalFamilyMember
from app.schemas.chemical import ChemicalFamilyInfo, ChemicalSearch, ChemicalSummary

logger = logging.getLogger(__name__)

# ── In-memory cache for chemical families (Algorithms Handbook §10 Phase 2) ──
# Loaded at startup via load_family_cache(). Thread-safe via asyncio.Lock.
_FAMILY_CACHE: dict[str, list[str]] | None = None  # chemical_name (upper) → family member names
_FAMILY_INFO_CACHE: dict[str, ChemicalFamilyInfo] | None = None  # chemical_name (upper) → info
_CACHE_LOCK = asyncio.Lock()


async def load_family_cache(session: AsyncSession) -> None:
    """Load all chemical family mappings into memory.

    Called once at FastAPI startup. Builds two lookup dicts:
    - _FAMILY_CACHE: chemical name → list of all family member names
    - _FAMILY_INFO_CACHE: chemical name → ChemicalFamilyInfo object

    This eliminates 6 DB queries per get_family_chemical_names() /
    get_family_info_by_chemical() call.
    """
    global _FAMILY_CACHE, _FAMILY_INFO_CACHE

    async with _CACHE_LOCK:
        if _FAMILY_CACHE is not None:
            logger.debug("Family cache already loaded, skipping")
            return

        logger.info("Loading chemical family cache...")

        # Query all family members with their families and chemicals in one pass
        result = await session.execute(
            select(ChemicalFamilyMember)
            .options(
                selectinload(ChemicalFamilyMember.family),
                selectinload(ChemicalFamilyMember.chemical),
            )
        )
        members = result.scalars().all()

        # Group by family
        families_data: dict[int, tuple[ChemicalFamily, list[str]]] = {}
        for member in members:
            fam_id = member.family_id
            if fam_id not in families_data:
                families_data[fam_id] = (member.family, [])
            families_data[fam_id][1].append(member.chemical.name)

        # Build caches
        family_cache: dict[str, list[str]] = {}
        family_info_cache: dict[str, ChemicalFamilyInfo] = {}

        for fam_id, (family, chem_names) in families_data.items():
            sorted_names = sorted(chem_names)
            info = ChemicalFamilyInfo(
                family_name=family.family_name,
                description=family.description,
                nlm_url=family.nlm_url,
                epa_url=family.epa_url,
                member_chemicals=sorted_names,
            )
            # Map each chemical name (uppercase) to the family data
            for name in chem_names:
                key = name.upper()
                family_cache[key] = sorted_names
                family_info_cache[key] = info

        _FAMILY_CACHE = family_cache
        _FAMILY_INFO_CACHE = family_info_cache

        logger.info(
            "Chemical family cache loaded: %d chemicals in %d families",
            len(family_cache),
            len(families_data),
        )


async def get_all_chemicals(session: AsyncSession) -> list[ChemicalSummary]:
    """Return all chemicals sorted alphabetically by name."""
    result = await session.execute(select(Chemical).order_by(Chemical.name))
    return [
        ChemicalSummary(
            id=c.id,
            cas_number=c.cas_number,
            name=c.name,
            category=c.category,
            atsdr_url=c.atsdr_url,
            pubchem_url=c.pubchem_url,
        )
        for c in result.scalars().all()
    ]


async def _get_chemical_family(
    session: AsyncSession,
    chemical_id: int,
) -> ChemicalFamilyInfo | None:
    """Get family info for a chemical if it belongs to a family."""
    # Find the family this chemical belongs to
    result = await session.execute(
        select(ChemicalFamilyMember)
        .where(ChemicalFamilyMember.chemical_id == chemical_id)
        .options(selectinload(ChemicalFamilyMember.family))
    )
    member = result.scalar_one_or_none()
    if member is None:
        return None

    # Get all chemicals in this family
    family = member.family
    members_result = await session.execute(
        select(Chemical.name)
        .join(ChemicalFamilyMember, ChemicalFamilyMember.chemical_id == Chemical.id)
        .where(ChemicalFamilyMember.family_id == family.id)
        .order_by(Chemical.name)
    )
    member_names = [row[0] for row in members_result.all()]

    return ChemicalFamilyInfo(
        family_name=family.family_name,
        description=family.description,
        nlm_url=family.nlm_url,
        epa_url=family.epa_url,
        member_chemicals=member_names,
    )


async def search_chemicals(
    session: AsyncSession,
    q: str,
) -> list[ChemicalSearch]:
    """Case-insensitive partial name search, up to 10 results.

    ADR-007: Results include family info so frontend can display
    expansion warning for chemicals that belong to a family.
    """
    result = await session.execute(
        select(Chemical).where(Chemical.name.ilike(f"%{q}%")).order_by(Chemical.name).limit(10)
    )

    chemicals = result.scalars().all()
    search_results = []

    for c in chemicals:
        family_info = await _get_chemical_family(session, c.id)
        search_results.append(
            ChemicalSearch(
                id=c.id,
                cas_number=c.cas_number,
                name=c.name,
                atsdr_url=c.atsdr_url,
                pubchem_url=c.pubchem_url,
                family=family_info,
            )
        )

    return search_results


async def get_family_chemical_names(
    session: AsyncSession,
    chemical_name: str,
) -> list[str] | None:
    """Get all chemical names in the same family as the given chemical.

    Returns None if the chemical doesn't belong to a family.
    Used by facility search to expand queries.

    Performance: Uses in-memory cache (loaded at startup). Falls back to DB
    query if cache not yet loaded (e.g., during tests).
    """
    # Try cache first (O(1) lookup)
    if _FAMILY_CACHE is not None:
        return _FAMILY_CACHE.get(chemical_name.upper())

    # Fallback to DB query (for tests or if cache not loaded)
    logger.debug("Family cache miss for %s, querying DB", chemical_name)

    # Find the chemical
    result = await session.execute(select(Chemical.id).where(Chemical.name.ilike(chemical_name)))
    chem_id = result.scalar_one_or_none()
    if chem_id is None:
        return None

    # Find the family
    result = await session.execute(
        select(ChemicalFamilyMember.family_id).where(ChemicalFamilyMember.chemical_id == chem_id)
    )
    family_id = result.scalar_one_or_none()
    if family_id is None:
        return None

    # Get all chemical names in this family
    result = await session.execute(
        select(Chemical.name)
        .join(ChemicalFamilyMember, ChemicalFamilyMember.chemical_id == Chemical.id)
        .where(ChemicalFamilyMember.family_id == family_id)
    )
    return [row[0] for row in result.all()]


async def get_family_info_by_chemical(
    session: AsyncSession,
    chemical_name: str,
) -> ChemicalFamilyInfo | None:
    """Get family info for a chemical by name.

    Used by facility search to include expansion metadata in response.

    Performance: Uses in-memory cache (loaded at startup). Falls back to DB
    query if cache not yet loaded (e.g., during tests).
    """
    # Try cache first (O(1) lookup)
    if _FAMILY_INFO_CACHE is not None:
        return _FAMILY_INFO_CACHE.get(chemical_name.upper())

    # Fallback to DB query (for tests or if cache not loaded)
    logger.debug("Family info cache miss for %s, querying DB", chemical_name)

    # Find the chemical
    result = await session.execute(select(Chemical.id).where(Chemical.name.ilike(chemical_name)))
    chem_id = result.scalar_one_or_none()
    if chem_id is None:
        return None

    return await _get_chemical_family(session, chem_id)
