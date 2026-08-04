"""Service layer for release-event queries.

Phase 2 — stories 2.3.x, 2.4.x.
"""

from __future__ import annotations

import logging

from geoalchemy2.shape import to_shape
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chemical import Chemical
from app.models.facility import Facility
from app.models.release_event import ReleaseEvent
from app.schemas.facility import LargestReleaseResponse, ReleaseEventSchema

logger = logging.getLogger(__name__)


async def get_facility_releases(
    session: AsyncSession,
    tri_facility_id: str,
    from_year: int,
    to_year: int,
    chemical_id: int | None,
    medium: str | None,
) -> list[ReleaseEventSchema] | None:
    """Return release events for a facility. Returns None when facility is not found."""
    fac_result = await session.execute(
        select(Facility.id).where(Facility.tri_facility_id == tri_facility_id)
    )
    facility_id: int | None = fac_result.scalar_one_or_none()
    if facility_id is None:
        return None

    stmt = (
        select(
            ReleaseEvent,
            Chemical.name.label("chem_name"),
            Chemical.cas_number.label("chem_cas"),
        )
        .join(Chemical, Chemical.id == ReleaseEvent.chemical_id)
        .where(
            ReleaseEvent.facility_id == facility_id,
            ReleaseEvent.reporting_year >= from_year,
            ReleaseEvent.reporting_year <= to_year,
        )
    )

    if chemical_id is not None:
        stmt = stmt.where(ReleaseEvent.chemical_id == chemical_id)

    if medium == "air":
        stmt = stmt.where(ReleaseEvent.air_release_lbs > 0)
    elif medium == "water":
        stmt = stmt.where(ReleaseEvent.water_release_lbs > 0)
    elif medium == "land":
        stmt = stmt.where(ReleaseEvent.land_release_lbs > 0)
    elif medium == "underground":
        stmt = stmt.where(ReleaseEvent.underground_release_lbs > 0)

    stmt = stmt.order_by(desc(ReleaseEvent.reporting_year))
    rows = (await session.execute(stmt)).all()

    def _lbs(val: object) -> float | None:
        return float(val) if val is not None else None  # type: ignore[arg-type]

    return [
        ReleaseEventSchema(
            reporting_year=row.ReleaseEvent.reporting_year,
            chemical_name=row.chem_name,
            cas_number=row.chem_cas,
            total_release_lbs=_lbs(row.ReleaseEvent.total_release_lbs),
            air_release_lbs=_lbs(row.ReleaseEvent.air_release_lbs),
            water_release_lbs=_lbs(row.ReleaseEvent.water_release_lbs),
            land_release_lbs=_lbs(row.ReleaseEvent.land_release_lbs),
            underground_release_lbs=_lbs(row.ReleaseEvent.underground_release_lbs),
            unit_of_measure=row.ReleaseEvent.unit_of_measure,
            form_type=row.ReleaseEvent.form_type,
        )
        for row in rows
    ]


async def get_largest_release(
    session: AsyncSession,
    chemical: str,
    year: int | None,
    state: str | None,
) -> LargestReleaseResponse | None:
    """Return the single facility with the largest total release for a chemical."""
    if year is None:
        yr_result = await session.execute(select(func.max(ReleaseEvent.reporting_year)))
        year = yr_result.scalar()

    # Subquery: aggregate total release per (facility, chemical, year)
    stmt = (
        select(
            Facility.tri_facility_id,
            Facility.name,
            Facility.city,
            Facility.state_code,
            Facility.location,
            Chemical.name.label("chem_name"),
            Chemical.cas_number,
            ReleaseEvent.reporting_year,
            ReleaseEvent.unit_of_measure,
            func.sum(ReleaseEvent.total_release_lbs).label("total_lbs"),
        )
        .join(ReleaseEvent, ReleaseEvent.facility_id == Facility.id)
        .join(Chemical, Chemical.id == ReleaseEvent.chemical_id)
        .where(Chemical.name.ilike(f"%{chemical}%"))
        .group_by(
            Facility.tri_facility_id,
            Facility.name,
            Facility.city,
            Facility.state_code,
            Facility.location,
            Chemical.name,
            Chemical.cas_number,
            ReleaseEvent.reporting_year,
            ReleaseEvent.unit_of_measure,
        )
        .order_by(desc("total_lbs"))
        .limit(1)
    )

    if year is not None:
        stmt = stmt.where(ReleaseEvent.reporting_year == year)

    if state:
        stmt = stmt.where(Facility.state_code == state.upper()[:2])

    row = (await session.execute(stmt)).first()
    if row is None:
        return None

    shape = to_shape(row.location)
    rep_year: int = row.reporting_year if row.reporting_year is not None else (year or 0)
    total_lbs = float(row.total_lbs) if row.total_lbs is not None else 0.0

    return LargestReleaseResponse(
        tri_facility_id=row.tri_facility_id,
        name=row.name,
        city=row.city,
        state_code=row.state_code or "",
        chemical_name=row.chem_name,
        cas_number=row.cas_number,
        reporting_year=rep_year,
        total_release_lbs=total_lbs,
        unit_of_measure=row.unit_of_measure or "Pounds",
        location={"lat": shape.y, "lon": shape.x},
    )
