"""FastAPI router for /api/v1/meta endpoint.

Phase 2 — story 2.7.3.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.meta import MetaResponse
from app.services.meta_service import get_meta

logger = logging.getLogger(__name__)

router = APIRouter(tags=["meta"])


@router.get("/meta", response_model=MetaResponse)
async def api_meta(
    db: AsyncSession = Depends(get_db),
) -> MetaResponse:
    """Return API metadata: available years, facility counts, vintage label."""
    result = await get_meta(db)
    if result is None:
        raise HTTPException(
            status_code=503,
            detail="No release event data available — database may not be seeded",
        )
    return result
