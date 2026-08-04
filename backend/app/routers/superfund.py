"""FastAPI router for Superfund site endpoints.

Routes:
  GET /api/v1/superfund/browse
  GET /api/v1/superfund
  GET /api/v1/superfund/{epa_id}

Phase 2 — stories 2.6.x.
Phase 4 — story 4.1.1 browse mode.
"""

from __future__ import annotations

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.superfund import SuperfundCollection, SuperfundDetail
from app.services.superfund_service import (
    get_all_superfund_browse,
    get_superfund_detail,
    get_superfund_near,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["superfund"])

# Literal type for Superfund status — FastAPI validates natively with proper 422 format
_SuperfundStatus = Literal["NPL", "Proposed", "Deleted"]


@router.get("/superfund/browse", response_model=SuperfundCollection)
async def browse_all_superfund(
    status: Annotated[
        _SuperfundStatus | None,
        Query(description="Site status: NPL | Proposed | Deleted"),
    ] = None,
    state: Annotated[
        str | None,
        Query(max_length=2, description="2-letter state code"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=5000)] = 5000,
    db: AsyncSession = Depends(get_db),
) -> SuperfundCollection:
    """Browse mode: fetch ALL Superfund sites without radius constraint.

    Used for the always-on diamond layer on the map.
    No spatial parameters required. MapLibre handles viewport subsetting client-side.
    """
    return await get_all_superfund_browse(
        session=db,
        status=status,
        state=state,
        limit=limit,
    )


@router.get("/superfund", response_model=SuperfundCollection)
async def list_superfund(
    lat: Annotated[
        float,
        Query(ge=-90.0, le=90.0, description="Center latitude (WGS84)"),
    ],
    lon: Annotated[
        float,
        Query(ge=-180.0, le=180.0, description="Center longitude (WGS84)"),
    ],
    radius_miles: Annotated[
        float,
        Query(gt=0, le=500.0, description="Search radius in miles (max 500)"),
    ],
    chemical: Annotated[
        str | None,
        Query(description="Filter by contaminant name (partial match)"),
    ] = None,
    state: Annotated[
        str | None,
        Query(max_length=2, description="2-letter state code"),
    ] = None,
    restrict_to_state: Annotated[bool, Query()] = False,
    status: Annotated[
        _SuperfundStatus | None,
        Query(description="Site status: NPL | Proposed | Deleted"),
    ] = None,
    db: AsyncSession = Depends(get_db),
) -> SuperfundCollection:
    if restrict_to_state and (not state or len(state) != 2):
        raise RequestValidationError(
            [
                {
                    "type": "value_error",
                    "loc": ("query", "state"),
                    "msg": "restrict_to_state=true requires a 2-character state code",
                    "input": state,
                }
            ]
        )
    return await get_superfund_near(
        session=db,
        lat=lat,
        lon=lon,
        radius_miles=radius_miles,
        chemical=chemical,
        state=state,
        restrict_to_state=restrict_to_state,
        status=status,
    )


@router.get("/superfund/{epa_id}", response_model=SuperfundDetail)
async def get_superfund_site(
    epa_id: str,
    db: AsyncSession = Depends(get_db),
) -> SuperfundDetail:
    detail = await get_superfund_detail(db, epa_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Superfund site not found")
    return detail
