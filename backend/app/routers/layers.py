"""FastAPI router for optional overlay layer endpoints.

Routes:
  GET /api/v1/layers/nuclear
  GET /api/v1/layers/npri
  GET /api/v1/layers/congressional-districts

Phase 2 — stories 2.7.x.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from geoalchemy2.shape import to_shape
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.npri_facility import NpriFacility
from app.models.nuclear_plant import NuclearPlant

logger = logging.getLogger(__name__)

router = APIRouter(tags=["layers"])


@router.get("/layers/nuclear")
async def get_nuclear_layer(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return all nuclear power plants as a GeoJSON FeatureCollection."""
    plants = (await db.execute(select(NuclearPlant))).scalars().all()

    features: list[dict[str, Any]] = []
    for plant in plants:
        shape = to_shape(plant.location)
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [shape.x, shape.y],
                },
                "properties": {
                    "id": plant.id,
                    "plant_name": plant.plant_name,
                    "operator": plant.operator,
                    "state_code": plant.state_code,
                    "status": plant.status,
                    "marker_shape": "atom",
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {"total_count": len(features)},
    }


@router.get("/layers/npri")
async def get_npri_layer(
    province: Annotated[
        str | None,
        Query(description="Canadian province abbreviation filter"),
    ] = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return Canadian NPRI facilities as a GeoJSON FeatureCollection."""
    stmt = select(NpriFacility)
    if province:
        stmt = stmt.where(NpriFacility.province == province.upper()[:2])

    facilities = (await db.execute(stmt)).scalars().all()

    features: list[dict[str, Any]] = []
    for fac in facilities:
        shape = to_shape(fac.location)
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [shape.x, shape.y],
                },
                "properties": {
                    "npri_id": fac.npri_id,
                    "name": fac.name,
                    "province": fac.province,
                    "marker_shape": "circle",
                    "marker_color": "#a855f7",
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {"total_count": len(features)},
    }


@router.get("/layers/congressional-districts")
async def get_congressional_districts(
    state: Annotated[
        str | None,
        Query(max_length=2, description="2-letter state code filter"),
    ] = None,
) -> dict[str, Any]:
    """Stub endpoint — congressional districts table not yet implemented.

    Returns an empty FeatureCollection until a districts table is added.
    """
    # ASSUMPTION: congressional_districts table does not exist in Phase 2.
    # Return empty FeatureCollection per AGENTS.md §8 ambiguity resolution.
    return {
        "type": "FeatureCollection",
        "features": [],
        "meta": {"total_count": 0, "state": state},
    }
