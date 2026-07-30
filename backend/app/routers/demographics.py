"""FastAPI router for Census demographics endpoints.

Routes:
  GET /api/v1/demographics/county
  GET /api/v1/demographics/tract

Phase 2 — story 2.4.x.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.demographics import DemographicsCollection
from app.services.demographics_service import (
    get_county_demographics,
    get_tract_demographics,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["demographics"])


@router.get("/demographics/county", response_model=DemographicsCollection)
async def county_demographics(
    state: Annotated[
        str | None,
        Query(min_length=2, max_length=2, description="2-letter state code (optional; omit to return all counties)"),
    ] = None,
    census_year: Annotated[
        int,
        Query(description="Census year (default 2000)"),
    ] = 2000,
    fields: Annotated[
        str | None,
        Query(description="Comma-separated field names to include"),
    ] = None,
    db: AsyncSession = Depends(get_db),
) -> DemographicsCollection:
    return await get_county_demographics(
        session=db,
        state=state,
        census_year=census_year,
        fields=fields,
    )


@router.get("/demographics/tract", response_model=DemographicsCollection)
async def tract_demographics(
    county_fips: Annotated[
        str,
        Query(min_length=5, max_length=5, description="5-digit county FIPS code"),
    ],
    census_year: Annotated[
        int,
        Query(description="Census year (default 2000)"),
    ] = 2000,
    db: AsyncSession = Depends(get_db),
) -> DemographicsCollection:
    return await get_tract_demographics(
        session=db,
        county_fips=county_fips,
        census_year=census_year,
    )
