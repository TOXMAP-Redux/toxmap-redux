"""FastAPI router for facility endpoints.

Routes:
  GET /api/v1/facilities
  GET /api/v1/facilities/{tri_facility_id}
  GET /api/v1/facilities/{tri_facility_id}/releases

Phase 2 — stories 2.1.1, 2.1.2, 2.2.x, 2.3.x.
"""

from __future__ import annotations

import datetime
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.facility import (
    FacilityCollection,
    FacilityDetail,
    ReleaseEventSchema,
)
from app.services.facility_service import (
    get_facilities_near,
    get_facility_detail,
    get_all_facilities_browse,
)
from app.services.release_service import get_facility_releases

logger = logging.getLogger(__name__)

router = APIRouter(tags=["facilities"])

_VALID_MEDIA = {"air", "water", "land", "underground"}


@router.get("/facilities/browse", response_model=FacilityCollection)
async def browse_all_facilities(
    year: Annotated[
        int | None,
        Query(description="Reporting year (omit for latest available)"),
    ] = None,
    chemical: Annotated[
        str | None,
        Query(description="Filter by chemical name (partial, case-insensitive)"),
    ] = None,
    medium: Annotated[
        str | None,
        Query(description="Release medium: air | water | land | underground"),
    ] = None,
    state: Annotated[
        str | None,
        Query(max_length=2, description="2-letter state code"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=30000)] = 30000,
    db: AsyncSession = Depends(get_db),
) -> FacilityCollection:
    """Browse mode: fetch ALL TRI facilities without radius constraint.
    
    Used for the initial map view showing all facilities nationwide.
    No spatial parameters required. MapLibre handles viewport subsetting client-side.
    """
    if medium is not None and medium not in _VALID_MEDIA:
        raise HTTPException(
            status_code=422,
            detail=f"medium must be one of: {', '.join(sorted(_VALID_MEDIA))}",
        )

    return await get_all_facilities_browse(
        session=db,
        year=year,
        chemical=chemical,
        medium=medium,
        state=state,
        limit=limit,
    )


@router.get("/facilities", response_model=FacilityCollection)
async def list_facilities(
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
    bbox: Annotated[
        str | None,
        Query(description="Bounding box: minLon,minLat,maxLon,maxLat"),
    ] = None,
    year: Annotated[
        int | None,
        Query(description="Reporting year (omit for latest available)"),
    ] = None,
    chemical: Annotated[
        str | None,
        Query(description="Filter by chemical name (partial, case-insensitive)"),
    ] = None,
    naics: Annotated[
        str | None,
        Query(description="Filter by NAICS code prefix"),
    ] = None,
    medium: Annotated[
        str | None,
        Query(description="Release medium: air | water | land | underground"),
    ] = None,
    state: Annotated[
        str | None,
        Query(max_length=2, description="2-letter state code"),
    ] = None,
    restrict_to_state: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=2000)] = 500,
    db: AsyncSession = Depends(get_db),
) -> FacilityCollection:
    if medium is not None and medium not in _VALID_MEDIA:
        raise HTTPException(
            status_code=422,
            detail=f"medium must be one of: {', '.join(sorted(_VALID_MEDIA))}",
        )
    if restrict_to_state and (not state or len(state) != 2):
        raise HTTPException(
            status_code=422,
            detail="restrict_to_state=true requires a 2-character state code",
        )

    raw_query: dict[str, Any] = {
        "lat": lat,
        "lon": lon,
        "radius_miles": radius_miles,
        "year": year,
        "chemical": chemical,
        "naics": naics,
        "medium": medium,
        "state": state,
        "restrict_to_state": restrict_to_state,
    }
    return await get_facilities_near(
        session=db,
        lat=lat,
        lon=lon,
        radius_miles=radius_miles,
        bbox=bbox,
        year=year,
        chemical=chemical,
        naics=naics,
        medium=medium,
        state=state,
        restrict_to_state=restrict_to_state,
        limit=limit,
        raw_query=raw_query,
    )


@router.get(
    "/facilities/{tri_facility_id}",
    response_model=FacilityDetail,
)
async def get_facility(
    tri_facility_id: str,
    db: AsyncSession = Depends(get_db),
) -> FacilityDetail:
    detail = await get_facility_detail(db, tri_facility_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Facility not found")
    return detail


@router.get(
    "/facilities/{tri_facility_id}/releases",
    response_model=list[ReleaseEventSchema],
)
async def list_facility_releases(
    tri_facility_id: str,
    from_year: Annotated[int | None, Query()] = None,
    to_year: Annotated[int | None, Query()] = None,
    chemical_id: Annotated[int | None, Query()] = None,
    medium: Annotated[str | None, Query()] = None,
    db: AsyncSession = Depends(get_db),
) -> list[ReleaseEventSchema]:
    today = datetime.date.today()
    eff_from = from_year if from_year is not None else today.year - 14
    eff_to = to_year if to_year is not None else today.year

    if medium is not None and medium not in _VALID_MEDIA:
        raise HTTPException(
            status_code=422,
            detail=f"medium must be one of: {', '.join(sorted(_VALID_MEDIA))}",
        )

    releases = await get_facility_releases(
        session=db,
        tri_facility_id=tri_facility_id,
        from_year=eff_from,
        to_year=eff_to,
        chemical_id=chemical_id,
        medium=medium,
    )
    if releases is None:
        raise HTTPException(status_code=404, detail="Facility not found")
    return releases
