"""Service layer for chemical list and search queries.

Phase 2 — stories 2.5.x.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chemical import Chemical
from app.schemas.chemical import ChemicalSearch, ChemicalSummary

logger = logging.getLogger(__name__)


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


async def search_chemicals(
    session: AsyncSession,
    q: str,
) -> list[ChemicalSearch]:
    """Case-insensitive partial name search, up to 10 results."""
    result = await session.execute(
        select(Chemical)
        .where(Chemical.name.ilike(f"%{q}%"))
        .order_by(Chemical.name)
        .limit(10)
    )
    return [
        ChemicalSearch(
            id=c.id,
            cas_number=c.cas_number,
            name=c.name,
            atsdr_url=c.atsdr_url,
            pubchem_url=c.pubchem_url,
        )
        for c in result.scalars().all()
    ]
