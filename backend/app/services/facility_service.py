"""Service layer for facility spatial queries and detail lookups.

Phase 2 — stories 2.1.1, 2.1.2, 2.2.x.
ADR-007 — Chemical families for transparent right-to-know search.

All SQL is built via SQLAlchemy Core/ORM expressions — no f-string SQL.
PostGIS distance calculations use Geography cast for accurate metre-based results.
"""

from __future__ import annotations

import logging
from typing import Any

from geoalchemy2 import Geography
from geoalchemy2.shape import to_shape
from sqlalchemy import cast, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chemical import Chemical
from app.models.facility import Facility
from app.models.release_event import ReleaseEvent
from app.schemas.facility import (
    FacilityCollection,
    FacilityCollectionMeta,
    FacilityDetail,
    FacilityFeature,
    FacilityFeatureProperties,
    SearchExpansion,
    TopChemical,
    assign_color_band,
)
from app.services.chemical_service import (
    get_family_chemical_names,
    get_family_info_by_chemical,
)

logger = logging.getLogger(__name__)

_MILES_TO_METERS = 1609.344
_BROWSE_LIMIT = 50000  # Max facilities for browse mode (all US TRI ~22k)


def _geo_point(lon: float, lat: float) -> Any:
    """Return a SQLAlchemy Geography expression for the given WGS84 point."""
    return cast(func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326), Geography)


def _fac_geography(location: Any) -> Any:
    """Cast a Facility.location geometry to Geography for distance math."""
    return cast(location, Geography)


async def _resolve_year(session: AsyncSession, year: int | None) -> int | None:
    """Return *year* if provided, else MAX(reporting_year) from release_events."""
    if year is not None:
        return year
    result = await session.execute(select(func.max(ReleaseEvent.reporting_year)))
    return result.scalar()


async def _expand_chemical_family(
    session: AsyncSession,
    chemical: str | None,
) -> tuple[list[str] | None, SearchExpansion | None]:
    """Expand a chemical to its family members (ADR-007).

    Returns:
        Tuple of (list of chemical names to search, SearchExpansion info)
        If chemical doesn't belong to a family, returns (None, None)
    """
    if not chemical:
        return None, None

    # Check if this chemical belongs to a family
    family_chemicals = await get_family_chemical_names(session, chemical)
    if family_chemicals is None or len(family_chemicals) <= 1:
        # Not in a family or is the only member
        return None, None

    # Get family info for the response
    family_info = await get_family_info_by_chemical(session, chemical)
    if family_info is None:
        return None, None

    expansion = SearchExpansion(
        expanded=True,
        family_name=family_info.family_name,
        searched_chemicals=family_chemicals,
        description=family_info.description,
        nlm_url=family_info.nlm_url,
    )

    return family_chemicals, expansion


async def get_facilities_near(
    session: AsyncSession,
    lat: float,
    lon: float,
    radius_miles: float,
    bbox: str | None,
    year: int | None,
    chemical: str | None,
    naics: str | None,
    medium: str | None,
    state: str | None,
    restrict_to_state: bool,
    exact_match: bool,
    limit: int,
    raw_query: dict[str, Any],
) -> FacilityCollection:
    """Spatial facility search → GeoJSON FeatureCollection."""
    effective_year = await _resolve_year(session, year)
    radius_meters = radius_miles * _MILES_TO_METERS

    # ADR-007: Expand chemical to family members if applicable (unless exact_match)
    family_chemicals: list[str] | None = None
    search_expansion: SearchExpansion | None = None
    if not exact_match:
        family_chemicals, search_expansion = await _expand_chemical_family(session, chemical)

    # --- Aggregate releases per (facility, year) in a subquery ---
    rel_stmt = (
        select(
            ReleaseEvent.facility_id,
            func.sum(ReleaseEvent.total_release_lbs).label("total_lbs"),
            ReleaseEvent.reporting_year,
        )
        .join(Chemical, Chemical.id == ReleaseEvent.chemical_id)
        .group_by(ReleaseEvent.facility_id, ReleaseEvent.reporting_year)
    )

    if effective_year is not None:
        rel_stmt = rel_stmt.where(ReleaseEvent.reporting_year == effective_year)

    # ADR-007: Use expanded family chemicals if available
    if family_chemicals:
        # Match any chemical in the family (OR across all names)
        rel_stmt = rel_stmt.where(
            or_(*[Chemical.name.ilike(f"%{chem}%") for chem in family_chemicals])
        )
    elif chemical:
        # ADR-007: When exact_match is true, use exact matching (case-insensitive)
        if exact_match:
            rel_stmt = rel_stmt.where(func.upper(Chemical.name) == chemical.upper())
        else:
            rel_stmt = rel_stmt.where(Chemical.name.ilike(f"%{chemical}%"))

    if medium == "air":
        rel_stmt = rel_stmt.where(ReleaseEvent.air_release_lbs > 0)
    elif medium == "water":
        rel_stmt = rel_stmt.where(ReleaseEvent.water_release_lbs > 0)
    elif medium == "land":
        rel_stmt = rel_stmt.where(ReleaseEvent.land_release_lbs > 0)
    elif medium == "underground":
        rel_stmt = rel_stmt.where(ReleaseEvent.underground_release_lbs > 0)

    rel_sub = rel_stmt.subquery()

    # --- Main spatial query ---
    point_geo = _geo_point(lon, lat)
    fac_geo = _fac_geography(Facility.location)

    stmt = (
        select(Facility, rel_sub.c.total_lbs, rel_sub.c.reporting_year)
        .join(rel_sub, rel_sub.c.facility_id == Facility.id)
        .where(func.ST_DWithin(fac_geo, point_geo, radius_meters))
    )

    if naics:
        stmt = stmt.where(Facility.naics_code.startswith(naics))

    if state:
        stmt = stmt.where(Facility.state_code == state.upper()[:2])

    if bbox:
        parts = bbox.split(",")
        if len(parts) == 4:
            try:
                min_lon, min_lat, max_lon, max_lat = (float(p) for p in parts)
                stmt = stmt.where(
                    func.ST_Within(
                        Facility.location,
                        func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326),
                    )
                )
            except ValueError:
                logger.warning("Ignoring invalid bbox parameter: %s", bbox)

    # Count rows before applying LIMIT (used for truncated flag)
    count_result = await session.execute(select(func.count()).select_from(stmt.subquery()))
    total_count: int = count_result.scalar() or 0

    # Apply ordering + limit
    stmt = stmt.order_by(desc(rel_sub.c.total_lbs)).limit(limit)
    rows = (await session.execute(stmt)).all()

    features: list[FacilityFeature] = []
    for row in rows:
        facility: Facility = row[0]
        total_lbs_raw = row[1]
        rep_year: int = row[2] if row[2] is not None else (effective_year or 0)
        total_lbs: float | None = float(total_lbs_raw) if total_lbs_raw is not None else None
        shape = to_shape(facility.location)
        geom: dict[str, Any] = {
            "type": "Point",
            "coordinates": [shape.x, shape.y],
        }
        props = FacilityFeatureProperties(
            id=facility.id,
            tri_facility_id=facility.tri_facility_id,
            name=facility.name,
            city=facility.city,
            state_code=facility.state_code,
            naics_code=facility.naics_code,
            naics_desc=facility.naics_desc,
            total_release_lbs=total_lbs,
            reporting_year=rep_year,
            color_band=assign_color_band(total_lbs),
            unit_of_measure="Pounds",
            marker_shape="circle",
        )
        features.append(FacilityFeature(geometry=geom, properties=props))

    return FacilityCollection(
        features=features,
        meta=FacilityCollectionMeta(
            total_count=total_count,
            returned_count=len(features),
            truncated=total_count > len(features),
            query=raw_query,
            search_expansion=search_expansion,  # ADR-007
        ),
    )


async def get_all_facilities_browse(
    session: AsyncSession,
    year: int | None,
    chemical: str | None,
    medium: str | None,
    state: str | None,
    bbox: str | None = None,
    exact_match: bool = False,
    limit: int = _BROWSE_LIMIT,
) -> FacilityCollection:
    """Browse mode: fetch ALL facilities without radius constraint.

    Used for the initial map view showing all TRI facilities nationwide.
    Filters by year/chemical/medium/state/bbox are applied but no spatial constraint.
    Results are ordered by total_release_lbs desc.
    ADR-007: Expands chemical families automatically (unless exact_match).
    """
    effective_year = await _resolve_year(session, year)

    # ADR-007: Expand chemical to family members if applicable (unless exact_match)
    family_chemicals: list[str] | None = None
    search_expansion: SearchExpansion | None = None
    if not exact_match:
        family_chemicals, search_expansion = await _expand_chemical_family(session, chemical)

    # Aggregate releases per (facility, year) in a subquery
    rel_stmt = (
        select(
            ReleaseEvent.facility_id,
            func.sum(ReleaseEvent.total_release_lbs).label("total_lbs"),
            ReleaseEvent.reporting_year,
        )
        .join(Chemical, Chemical.id == ReleaseEvent.chemical_id)
        .group_by(ReleaseEvent.facility_id, ReleaseEvent.reporting_year)
    )

    if effective_year is not None:
        rel_stmt = rel_stmt.where(ReleaseEvent.reporting_year == effective_year)

    # ADR-007: Use expanded family chemicals if available
    if family_chemicals:
        rel_stmt = rel_stmt.where(
            or_(*[Chemical.name.ilike(f"%{chem}%") for chem in family_chemicals])
        )
    elif chemical:
        # ADR-007: When exact_match is true, use exact matching (case-insensitive)
        if exact_match:
            rel_stmt = rel_stmt.where(func.upper(Chemical.name) == chemical.upper())
        else:
            rel_stmt = rel_stmt.where(Chemical.name.ilike(f"%{chemical}%"))

    if medium == "air":
        rel_stmt = rel_stmt.where(ReleaseEvent.air_release_lbs > 0)
    elif medium == "water":
        rel_stmt = rel_stmt.where(ReleaseEvent.water_release_lbs > 0)
    elif medium == "land":
        rel_stmt = rel_stmt.where(ReleaseEvent.land_release_lbs > 0)
    elif medium == "underground":
        rel_stmt = rel_stmt.where(ReleaseEvent.underground_release_lbs > 0)

    rel_sub = rel_stmt.subquery()

    # Main query - no spatial constraint
    stmt = select(Facility, rel_sub.c.total_lbs, rel_sub.c.reporting_year).join(
        rel_sub, rel_sub.c.facility_id == Facility.id
    )

    if state:
        stmt = stmt.where(Facility.state_code == state.upper()[:2])

    # Apply bbox filter if provided (format: "min_lon,min_lat,max_lon,max_lat")
    if bbox:
        parts = bbox.split(",")
        if len(parts) == 4:
            try:
                min_lon, min_lat, max_lon, max_lat = (float(p) for p in parts)
                stmt = stmt.where(
                    func.ST_Within(
                        Facility.location,
                        func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326),
                    )
                )
            except ValueError:
                logger.warning("Ignoring invalid bbox parameter: %s", bbox)

    # Count total before limit
    count_result = await session.execute(select(func.count()).select_from(stmt.subquery()))
    total_count: int = count_result.scalar() or 0

    # Apply ordering + limit
    stmt = stmt.order_by(desc(rel_sub.c.total_lbs)).limit(limit)
    rows = (await session.execute(stmt)).all()

    features: list[FacilityFeature] = []
    for row in rows:
        facility: Facility = row[0]
        total_lbs_raw = row[1]
        rep_year: int = row[2] if row[2] is not None else (effective_year or 0)
        total_lbs: float | None = float(total_lbs_raw) if total_lbs_raw is not None else None
        shape = to_shape(facility.location)
        geom: dict[str, Any] = {
            "type": "Point",
            "coordinates": [shape.x, shape.y],
        }
        props = FacilityFeatureProperties(
            id=facility.id,
            tri_facility_id=facility.tri_facility_id,
            name=facility.name,
            city=facility.city,
            state_code=facility.state_code,
            naics_code=facility.naics_code,
            naics_desc=facility.naics_desc,
            total_release_lbs=total_lbs,
            reporting_year=rep_year,
            color_band=assign_color_band(total_lbs),
            unit_of_measure="Pounds",
            marker_shape="circle",
        )
        features.append(FacilityFeature(geometry=geom, properties=props))

    raw_query = {
        "browse_all": True,
        "year": year,
        "chemical": chemical,
        "medium": medium,
        "state": state,
        "limit": limit,
    }

    return FacilityCollection(
        features=features,
        meta=FacilityCollectionMeta(
            total_count=total_count,
            returned_count=len(features),
            truncated=total_count > len(features),
            query=raw_query,
            search_expansion=search_expansion,  # ADR-007
        ),
    )


async def get_facility_detail(
    session: AsyncSession,
    tri_facility_id: str,
) -> FacilityDetail | None:
    """Return full detail for a single facility including top-5 chemicals."""
    result = await session.execute(
        select(Facility).where(Facility.tri_facility_id == tri_facility_id)
    )
    facility = result.scalar_one_or_none()
    if facility is None:
        return None

    # Latest reporting year for this facility
    yr_result = await session.execute(
        select(func.max(ReleaseEvent.reporting_year)).where(ReleaseEvent.facility_id == facility.id)
    )
    latest_year: int | None = yr_result.scalar()

    top_chemicals: list[TopChemical] = []
    if latest_year is not None:
        chem_rows = (
            await session.execute(
                select(
                    Chemical.name,
                    Chemical.cas_number,
                    Chemical.atsdr_url,
                    Chemical.pubchem_url,
                    func.sum(ReleaseEvent.total_release_lbs).label("total_lbs"),
                    ReleaseEvent.unit_of_measure,
                )
                .join(ReleaseEvent, ReleaseEvent.chemical_id == Chemical.id)
                .where(
                    ReleaseEvent.facility_id == facility.id,
                    ReleaseEvent.reporting_year == latest_year,
                )
                .group_by(
                    Chemical.name,
                    Chemical.cas_number,
                    Chemical.atsdr_url,
                    Chemical.pubchem_url,
                    ReleaseEvent.unit_of_measure,
                )
                .order_by(desc("total_lbs"))
                .limit(5)
            )
        ).all()

        for row in chem_rows:
            lbs = float(row.total_lbs) if row.total_lbs is not None else 0.0
            top_chemicals.append(
                TopChemical(
                    chemical_name=row.name,
                    cas_number=row.cas_number,
                    total_release_lbs=lbs,
                    unit_of_measure=row.unit_of_measure or "Pounds",
                    atsdr_url=row.atsdr_url,
                    pubchem_url=row.pubchem_url,
                )
            )

    shape = to_shape(facility.location)
    return FacilityDetail(
        id=facility.id,
        tri_facility_id=facility.tri_facility_id,
        name=facility.name,
        address=facility.address,
        city=facility.city,
        state_code=facility.state_code,
        zip_code=facility.zip_code,
        county=facility.county,
        naics_code=facility.naics_code,
        naics_desc=facility.naics_desc,
        location={"lat": shape.y, "lon": shape.x},
        latest_year=latest_year,
        top_chemicals=top_chemicals,
    )


async def get_export_rows(
    session: AsyncSession,
    lat: float,
    lon: float,
    radius_miles: float,
    bbox: str | None,
    year: int | None,
    chemical: str | None,
    naics: str | None,
    medium: str | None,
    state: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    """Return per-chemical release rows for CSV export, same spatial filters as
    get_facilities_near but one row per (facility, chemical, year)."""
    effective_year = await _resolve_year(session, year)
    radius_meters = radius_miles * _MILES_TO_METERS
    point_geo = _geo_point(lon, lat)
    fac_geo = _fac_geography(Facility.location)

    stmt = (
        select(
            Facility.tri_facility_id,
            Facility.name,
            Facility.address,
            Facility.city,
            Facility.state_code,
            Facility.naics_code,
            Chemical.name.label("chemical_name"),
            Chemical.cas_number,
            ReleaseEvent.reporting_year,
            ReleaseEvent.total_release_lbs,
            ReleaseEvent.air_release_lbs,
            ReleaseEvent.water_release_lbs,
            ReleaseEvent.land_release_lbs,
            ReleaseEvent.underground_release_lbs,
            ReleaseEvent.unit_of_measure,
            ReleaseEvent.form_type,
        )
        .join(ReleaseEvent, ReleaseEvent.facility_id == Facility.id)
        .join(Chemical, Chemical.id == ReleaseEvent.chemical_id)
        .where(func.ST_DWithin(fac_geo, point_geo, radius_meters))
    )

    if effective_year is not None:
        stmt = stmt.where(ReleaseEvent.reporting_year == effective_year)

    if chemical:
        stmt = stmt.where(Chemical.name.ilike(f"%{chemical}%"))

    if naics:
        stmt = stmt.where(Facility.naics_code.startswith(naics))

    if state:
        stmt = stmt.where(Facility.state_code == state.upper()[:2])

    if medium == "air":
        stmt = stmt.where(ReleaseEvent.air_release_lbs > 0)
    elif medium == "water":
        stmt = stmt.where(ReleaseEvent.water_release_lbs > 0)
    elif medium == "land":
        stmt = stmt.where(ReleaseEvent.land_release_lbs > 0)
    elif medium == "underground":
        stmt = stmt.where(ReleaseEvent.underground_release_lbs > 0)

    if bbox:
        parts = bbox.split(",")
        if len(parts) == 4:
            try:
                min_lon, min_lat, max_lon, max_lat = (float(p) for p in parts)
                stmt = stmt.where(
                    func.ST_Within(
                        Facility.location,
                        func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326),
                    )
                )
            except ValueError:
                pass

    stmt = stmt.limit(limit)
    rows = (await session.execute(stmt)).all()

    def _fmt(val: object) -> str:
        return str(val) if val is not None else ""

    return [
        {
            "tri_facility_id": row.tri_facility_id,
            "name": row.name,
            "address": row.address or "",
            "city": row.city or "",
            "state_code": row.state_code or "",
            "naics_code": row.naics_code or "",
            "chemical_name": row.chemical_name,
            "cas_number": row.cas_number or "",
            "reporting_year": row.reporting_year,
            "total_release_lbs": _fmt(row.total_release_lbs),
            "air_release_lbs": _fmt(row.air_release_lbs),
            "water_release_lbs": _fmt(row.water_release_lbs),
            "land_release_lbs": _fmt(row.land_release_lbs),
            "underground_release_lbs": _fmt(row.underground_release_lbs),
            "unit_of_measure": row.unit_of_measure,
            "form_type": row.form_type,
        }
        for row in rows
    ]
