"""FastAPI router for the largest-release endpoint.

Routes:
  GET /api/v1/releases/largest

Phase 2 — story 2.4.x.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.facility import LargestReleaseResponse
from app.services.release_service import get_largest_release

logger = logging.getLogger(__name__)

router = APIRouter(tags=["releases"])


@router.get("/releases/largest", response_model=LargestReleaseResponse)
async def largest_release(
    chemical: Annotated[
        str, Query(min_length=1, description="Chemical name (partial match)")
    ],
    year: Annotated[
        int | None,
        Query(description="Reporting year (omit for latest available)"),
    ] = None,
    state: Annotated[
        str | None,
        Query(max_length=2, description="2-letter state code filter"),
    ] = None,
    db: AsyncSession = Depends(get_db),
) -> LargestReleaseResponse:
    result = await get_largest_release(
        session=db, chemical=chemical, year=year, state=state
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No releases found for the specified chemical",
        )
    return result
