"""Service layer for facility spatial queries and detail lookups.

Phase 2 — stories 2.1.1, 2.1.2, 2.2.x.
ADR-007 — Chemical families for transparent right-to-know search.
ADR-010 — Site search autocomplete (TRI ID, EPA ID, name).

All SQL is built via SQLAlchemy Core/ORM expressions — no f-string SQL.
PostGIS distance calculations use Geography cast for accurate metre-based results.
"""

from __future__ import annotations

import logging
from typing import Any

from geoalchemy2 import Geography
from geoalchemy2.shape import to_shape
from sqlalchemy import case, cast, desc, func, literal, or_, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chemical import Chemical
from app.models.facility import Facility
from app.models.release_event import ReleaseEvent
from app.models.superfund_site import SuperfundSite
from app.schemas.facility import (
    FacilityCollection,
    FacilityCollectionMeta,
    FacilityDetail,
    FacilityFeature,
    FacilityFeatureProperties,
    SearchExpansion,
    SiteSearchResult,
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
    """Return *year* if provided, else None (meaning all years).
    
    BUG FIX 7.BUG.29: Previously returned MAX(reporting_year) when year=None,
    which caused "All years" searches to show only the latest year. Now returns
    None to trigger all-years aggregation in the search queries.
    """
    if year is not None:
        return year
    # Return None to indicate "all years" - the search queries will
    # aggregate across all years instead of filtering to a single year
    return None


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
    """Spatial facility search → GeoJSON FeatureCollection.
    
    Performance: Filter facilities spatially FIRST (via PostGIS GiST index),
    then aggregate only their releases. This avoids scanning the entire
    release_events table (~1M rows). See 7.PERF.1.
    """
    effective_year = await _resolve_year(session, year)
    radius_meters = radius_miles * _MILES_TO_METERS

    # ADR-007: Expand chemical to family members if applicable (unless exact_match)
    family_chemicals: list[str] | None = None
    search_expansion: SearchExpansion | None = None
    if not exact_match:
        family_chemicals, search_expansion = await _expand_chemical_family(session, chemical)

    # --- STEP 1: Find facility IDs matching spatial + attribute filters ---
    # This uses the PostGIS GiST index for fast spatial lookup (~200 results typically)
    point_geo = _geo_point(lon, lat)
    fac_geo = _fac_geography(Facility.location)
    
    matching_fac_stmt = (
        select(Facility.id)
        .where(func.ST_DWithin(fac_geo, point_geo, radius_meters))
    )
    
    if naics:
        matching_fac_stmt = matching_fac_stmt.where(Facility.naics_code.startswith(naics))
    
    if state:
        matching_fac_stmt = matching_fac_stmt.where(Facility.state_code == state.upper()[:2])
    
    if bbox:
        parts = bbox.split(",")
        if len(parts) == 4:
            try:
                min_lon, min_lat, max_lon, max_lat = (float(p) for p in parts)
                matching_fac_stmt = matching_fac_stmt.where(
                    func.ST_Within(
                        Facility.location,
                        func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326),
                    )
                )
            except ValueError:
                logger.warning("Ignoring invalid bbox parameter: %s", bbox)

    matching_fac_ids = matching_fac_stmt.scalar_subquery()

    # --- STEP 2: Aggregate releases ONLY for matching facilities ---
    # This uses idx_releases_facility for fast lookup (~10K rows vs 1M+)
    needs_chemical_join = bool(chemical or family_chemicals)
    
    if effective_year is not None:
        # Single year: group by facility + year
        rel_stmt = (
            select(
                ReleaseEvent.facility_id,
                func.sum(ReleaseEvent.total_release_lbs).label("total_lbs"),
                ReleaseEvent.reporting_year,
            )
            .where(ReleaseEvent.facility_id.in_(matching_fac_ids))
            .where(ReleaseEvent.reporting_year == effective_year)
            .group_by(ReleaseEvent.facility_id, ReleaseEvent.reporting_year)
        )
    else:
        # All years: aggregate across all years, use max year for display
        rel_stmt = (
            select(
                ReleaseEvent.facility_id,
                func.sum(ReleaseEvent.total_release_lbs).label("total_lbs"),
                func.max(ReleaseEvent.reporting_year).label("reporting_year"),
            )
            .where(ReleaseEvent.facility_id.in_(matching_fac_ids))
            .group_by(ReleaseEvent.facility_id)
        )

    # Only join Chemical table when we need to filter by chemical name
    if needs_chemical_join:
        rel_stmt = rel_stmt.join(Chemical, Chemical.id == ReleaseEvent.chemical_id)

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

    # --- STEP 3: Final join to get facility details + release totals ---
    # No need to re-apply naics/state/bbox filters - already applied in matching_fac_ids
    stmt = (
        select(Facility, rel_sub.c.total_lbs, rel_sub.c.reporting_year)
        .join(rel_sub, rel_sub.c.facility_id == Facility.id)
    )

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

    # BUG FIX 7.BUG.29: When year=None (All years), aggregate across ALL years for each
    # facility. Previously grouped by (facility, year) which returned only the peak year.
    #
    # PERF FIX: Only join with Chemical table when filtering by chemical.
    needs_chemical_join = bool(chemical or family_chemicals)
    
    if effective_year is not None:
        # Single year: group by facility + year
        rel_stmt = (
            select(
                ReleaseEvent.facility_id,
                func.sum(ReleaseEvent.total_release_lbs).label("total_lbs"),
                ReleaseEvent.reporting_year,
            )
            .where(ReleaseEvent.reporting_year == effective_year)
            .group_by(ReleaseEvent.facility_id, ReleaseEvent.reporting_year)
        )
    else:
        # All years: aggregate across all years, use max year for display
        rel_stmt = (
            select(
                ReleaseEvent.facility_id,
                func.sum(ReleaseEvent.total_release_lbs).label("total_lbs"),
                func.max(ReleaseEvent.reporting_year).label("reporting_year"),
            )
            .group_by(ReleaseEvent.facility_id)
        )

    # Only join Chemical table when we need to filter by chemical name
    if needs_chemical_join:
        rel_stmt = rel_stmt.join(Chemical, Chemical.id == ReleaseEvent.chemical_id)

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
    year: int | None = None,
) -> FacilityDetail | None:
    """Return full detail for a single facility including top-5 chemicals.
    
    Args:
        session: Database session
        tri_facility_id: TRI facility ID
        year: If provided, filter top chemicals and totals to this reporting year.
              If None, aggregate across all years.
    """
    result = await session.execute(
        select(Facility).where(Facility.tri_facility_id == tri_facility_id)
    )
    facility = result.scalar_one_or_none()
    if facility is None:
        return None

    # First and latest reporting years for this facility (7.UX.6 — accurate year range labels)
    yr_result = await session.execute(
        select(
            func.min(ReleaseEvent.reporting_year),
            func.max(ReleaseEvent.reporting_year),
        ).where(ReleaseEvent.facility_id == facility.id)
    )
    yr_row = yr_result.one()
    first_reporting_year: int | None = yr_row[0]
    latest_year: int | None = yr_row[1]

    # Build year filter condition (used for both total and top chemicals)
    year_filter = ReleaseEvent.reporting_year == year if year is not None else True

    # Calculate total_release_lbs (filtered by year if provided)
    # Includes off-site transfers so mediums (air + water + land + underground + off-site) sum to TOTAL
    total_result = await session.execute(
        select(
            func.sum(func.coalesce(ReleaseEvent.total_release_lbs, 0) + func.coalesce(ReleaseEvent.off_site_lbs, 0))
        ).where(ReleaseEvent.facility_id == facility.id).where(year_filter)
    )
    total_release_lbs: float | None = None
    total_raw = total_result.scalar()
    if total_raw is not None:
        total_release_lbs = float(total_raw)

    # Top chemicals (filtered by year if provided)
    # Includes off-site transfers to match the total calculation
    top_chemicals: list[TopChemical] = []
    chem_stmt = (
        select(
            Chemical.name,
            Chemical.cas_number,
            Chemical.atsdr_url,
            Chemical.pubchem_url,
            func.sum(
                func.coalesce(ReleaseEvent.total_release_lbs, 0) + func.coalesce(ReleaseEvent.off_site_lbs, 0)
            ).label("total_lbs"),
            ReleaseEvent.unit_of_measure,
        )
        .join(ReleaseEvent, ReleaseEvent.chemical_id == Chemical.id)
        .where(ReleaseEvent.facility_id == facility.id)
        .where(year_filter)
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
    chem_rows = (await session.execute(chem_stmt)).all()

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
        first_reporting_year=first_reporting_year,
        top_chemicals=top_chemicals,
        total_release_lbs=total_release_lbs,
    )


# ---------------------------------------------------------------------------
# ADR-010: Site Search Autocomplete (TRI ID, EPA ID, and Name)
# ---------------------------------------------------------------------------


async def search_facilities(
    session: AsyncSession,
    q: str,
    state: str | None = None,
    limit: int = 10,
) -> list[SiteSearchResult]:
    """Search TRI facilities AND Superfund sites by ID or name with ranked relevance scoring.

    ADR-010 ranking tiers (applied to both datasets):
    - 1.00: Exact TRI ID or EPA ID match (case-insensitive)
    - 0.95: TRI ID or EPA ID prefix match
    - 0.90: Exact name match (case-insensitive)
    - 0.80: Name prefix match
    - 0.60: Name contains match
    - 0.50: TRI ID or EPA ID contains match (but not prefix)

    Results from both datasets are merged and ordered by relevance_score DESC, then name ASC.
    Returns empty list (not exception) when no matches found.
    """
    q_upper = q.upper()
    q_pattern = f"%{q}%"
    q_prefix = f"{q}%"

    # ── TRI Facilities Query ───────────────────────────────────────────────
    tri_score_expr = case(
        (func.upper(Facility.tri_facility_id) == q_upper, 1.0),
        (Facility.tri_facility_id.ilike(q_prefix), 0.95),
        (func.upper(Facility.name) == q_upper, 0.90),
        (Facility.name.ilike(q_prefix), 0.80),
        (Facility.name.ilike(q_pattern), 0.60),
        (Facility.tri_facility_id.ilike(q_pattern), 0.50),
        else_=0.0,
    ).label("relevance_score")

    tri_match_type_expr = case(
        (
            or_(
                func.upper(Facility.tri_facility_id) == q_upper,
                Facility.tri_facility_id.ilike(q_prefix),
                Facility.tri_facility_id.ilike(q_pattern),
            ),
            "id",
        ),
        else_="name",
    ).label("match_type")

    tri_stmt = select(
        Facility.id.label("id"),
        literal("tri").label("site_type"),
        Facility.tri_facility_id.label("site_id"),
        Facility.name.label("name"),
        Facility.city.label("city"),
        Facility.state_code.label("state_code"),
        Facility.county.label("county"),
        tri_match_type_expr,
        tri_score_expr,
    ).where(
        or_(
            Facility.tri_facility_id.ilike(q_pattern),
            Facility.name.ilike(q_pattern),
        )
    )

    if state:
        tri_stmt = tri_stmt.where(Facility.state_code == state.upper()[:2])

    # ── Superfund Sites Query ──────────────────────────────────────────────
    sf_score_expr = case(
        (func.upper(SuperfundSite.epa_id) == q_upper, 1.0),
        (SuperfundSite.epa_id.ilike(q_prefix), 0.95),
        (func.upper(SuperfundSite.name) == q_upper, 0.90),
        (SuperfundSite.name.ilike(q_prefix), 0.80),
        (SuperfundSite.name.ilike(q_pattern), 0.60),
        (SuperfundSite.epa_id.ilike(q_pattern), 0.50),
        else_=0.0,
    ).label("relevance_score")

    sf_match_type_expr = case(
        (
            or_(
                func.upper(SuperfundSite.epa_id) == q_upper,
                SuperfundSite.epa_id.ilike(q_prefix),
                SuperfundSite.epa_id.ilike(q_pattern),
            ),
            "id",
        ),
        else_="name",
    ).label("match_type")

    sf_stmt = select(
        SuperfundSite.id.label("id"),
        literal("superfund").label("site_type"),
        SuperfundSite.epa_id.label("site_id"),
        SuperfundSite.name.label("name"),
        SuperfundSite.city.label("city"),
        SuperfundSite.state_code.label("state_code"),
        SuperfundSite.county.label("county"),
        sf_match_type_expr,
        sf_score_expr,
    ).where(
        or_(
            SuperfundSite.epa_id.ilike(q_pattern),
            SuperfundSite.name.ilike(q_pattern),
        )
    )

    if state:
        sf_stmt = sf_stmt.where(SuperfundSite.state_code == state.upper()[:2])

    # ── UNION ALL and order by score ───────────────────────────────────────
    combined = union_all(tri_stmt, sf_stmt).subquery()
    final_stmt = (
        select(combined)
        .order_by(desc(combined.c.relevance_score), combined.c.name)
        .limit(limit)
    )

    rows = (await session.execute(final_stmt)).all()

    return [
        SiteSearchResult(
            id=row.id,
            site_type=row.site_type,
            site_id=row.site_id,
            name=row.name,
            city=row.city,
            state_code=row.state_code,
            county=row.county,
            match_type=row.match_type,
            relevance_score=float(row.relevance_score),
        )
        for row in rows
    ]


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


async def get_export_rows_browse(
    session: AsyncSession,
    year: int | None,
    chemical: str | None,
    naics: str | None,
    medium: str | None,
    state: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    """Return per-chemical release rows for CSV export, browse mode (no spatial filter).
    
    Used for nationwide searches filtered by chemical/state without lat/lon constraint.
    """
    effective_year = await _resolve_year(session, year)

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
