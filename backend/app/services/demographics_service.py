"""Service layer for Census county demographic queries.

Phase 2 — story 2.4.x.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from geoalchemy2.shape import to_shape
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.census_county import CensusCounty
from app.schemas.demographics import (
    DEMOGRAPHICS_UNITS,
    DemographicsCollection,
    DemographicsCollectionMeta,
    DemographicsFeature,
    DemographicsFeatureProperties,
)

logger = logging.getLogger(__name__)


def _county_to_feature(county: CensusCounty) -> DemographicsFeature:
    """Convert an ORM CensusCounty to a GeoJSON Feature."""
    if county.boundary is not None:
        shape = to_shape(county.boundary)
        geom: dict[str, Any] = json.loads(json.dumps(shape.__geo_interface__))
    else:
        geom = {"type": "Point", "coordinates": [0.0, 0.0]}

    def _f(val: object) -> float | None:
        return float(val) if val is not None else None  # type: ignore[arg-type]

    state_fips = county.fips_code[:2] if county.fips_code else None
    props = DemographicsFeatureProperties(
        fips_code=county.fips_code,
        name=county.name,
        state_code=county.state_code,
        state_fips=state_fips,
        census_year=county.census_year,
        total_pop=county.total_pop,
        median_income=_f(county.median_income),
        pct_under_18=_f(county.pct_under_18),
        pct_over_65=_f(county.pct_over_65),
        pct_nonwhite=_f(county.pct_nonwhite),
        cancer_mortality_female_per_100k=_f(county.cancer_mortality_female_per_100k),
    )
    return DemographicsFeature(geometry=geom, properties=props)


async def get_county_demographics(
    session: AsyncSession,
    state: str | None,
    census_year: int,
    fields: str | None,
) -> DemographicsCollection:
    """Return county GeoJSON for a given state and census year.
    
    If state is None, returns all counties for the census year.
    """
    if state:
        stmt = select(CensusCounty).where(
            CensusCounty.state_code == state.upper()[:2],
            CensusCounty.census_year == census_year,
        )
    else:
        stmt = select(CensusCounty).where(
            CensusCounty.census_year == census_year,
        )
    counties = (await session.execute(stmt)).scalars().all()
    features = [_county_to_feature(c) for c in counties]

    return DemographicsCollection(
        features=features,
        meta=DemographicsCollectionMeta(
            total_count=len(features),
            census_year=census_year,
            state=state.upper()[:2] if state else None,
            units=DEMOGRAPHICS_UNITS,
        ),
    )


async def get_tract_demographics(
    session: AsyncSession,
    county_fips: str,
    census_year: int,
) -> DemographicsCollection:
    """Return county-level records matching the 5-digit FIPS prefix.

    Tract-level data is not ingested yet; this returns county rows whose
    fips_code starts with the requested prefix (i.e., exact county match).
    """
    prefix = county_fips[:5]
    stmt = select(CensusCounty).where(
        CensusCounty.fips_code.startswith(prefix),
        CensusCounty.census_year == census_year,
    )
    counties = (await session.execute(stmt)).scalars().all()
    features = [_county_to_feature(c) for c in counties]
    state_code = county_fips[:2] if len(county_fips) >= 2 else ""

    return DemographicsCollection(
        features=features,
        meta=DemographicsCollectionMeta(
            total_count=len(features),
            census_year=census_year,
            state=state_code,
            units=DEMOGRAPHICS_UNITS,
        ),
    )
