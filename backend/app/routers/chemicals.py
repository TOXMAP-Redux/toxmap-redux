"""FastAPI router for chemical list and search endpoints.

Routes:
  GET /api/v1/chemicals
  GET /api/v1/chemicals/search

Phase 2 — stories 2.5.x.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.chemical import ChemicalSearch, ChemicalSummary
from app.services.chemical_service import get_all_chemicals, search_chemicals

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chemicals"])


@router.get("/chemicals", response_model=list[ChemicalSummary])
async def list_chemicals(
    db: AsyncSession = Depends(get_db),
) -> list[ChemicalSummary]:
    """Return all TRI chemicals sorted alphabetically."""
    return await get_all_chemicals(db)


@router.get("/chemicals/search", response_model=list[ChemicalSearch])
async def search_chemicals_endpoint(
    q: Annotated[
        str,
        Query(min_length=2, description="Partial chemical name (min 2 chars)"),
    ],
    db: AsyncSession = Depends(get_db),
) -> list[ChemicalSearch]:
    """Case-insensitive partial chemical name search (max 10 results).

    Returns an empty array (not 404) when no chemicals match.
    """
    return await search_chemicals(db, q)
