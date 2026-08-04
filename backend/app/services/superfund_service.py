"""Service layer for Superfund site queries.

Phase 2 — stories 2.6.x.
Phase 4 — story 4.1.1 browse mode (all sites, no radius constraint).
"""

from __future__ import annotations

import logging

from geoalchemy2 import Geography
from geoalchemy2.shape import to_shape
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chemical import Chemical
from app.models.superfund_site import SuperfundSite
from app.schemas.superfund import (
    SuperfundCollection,
    SuperfundCollectionMeta,
    SuperfundContaminant,
    SuperfundDetail,
    SuperfundFeature,
    SuperfundFeatureProperties,
)
from app.services.superfund_cas_lookup import SUPERFUND_CAS_LOOKUP

logger = logging.getLogger(__name__)

_MILES_TO_METERS = 1609.344

_VALID_STATUSES = {"NPL", "Proposed", "Deleted"}


async def get_all_superfund_browse(
    session: AsyncSession,
    status: str | None = None,
    state: str | None = None,
    limit: int = 5000,
) -> SuperfundCollection:
    """Browse mode: fetch ALL Superfund sites without radius constraint.

    Used for the always-on diamond layer on the map.
    ~1,700 NPL sites total — fetched once, MapLibre handles viewport subsetting.
    """
    stmt = select(SuperfundSite)

    if state:
        stmt = stmt.where(SuperfundSite.state_code == state.upper()[:2])

    if status and status in _VALID_STATUSES:
        stmt = stmt.where(SuperfundSite.status == status)

    stmt = stmt.limit(limit)
    sites = (await session.execute(stmt)).scalars().all()

    features: list[SuperfundFeature] = []
    for site in sites:
        shape = to_shape(site.location)
        geom = {"type": "Point", "coordinates": [shape.x, shape.y]}
        npl_str: str | None = str(site.npl_date) if site.npl_date is not None else None
        props = SuperfundFeatureProperties(
            id=site.id,
            epa_id=site.epa_id,
            name=site.name,
            city=site.city,
            state_code=site.state_code,
            status=site.status,
            hrs_score=(float(site.hrs_score) if site.hrs_score is not None else None),
            npl_date=npl_str,
            contaminants=list(site.contaminants) if site.contaminants else [],
            marker_shape="diamond",
        )
        features.append(SuperfundFeature(geometry=geom, properties=props))

    return SuperfundCollection(
        features=features,
        meta=SuperfundCollectionMeta(total_count=len(features)),
    )


async def get_superfund_near(
    session: AsyncSession,
    lat: float,
    lon: float,
    radius_miles: float,
    chemical: str | None,
    state: str | None,
    restrict_to_state: bool,
    status: str | None,
) -> SuperfundCollection:
    """Spatial Superfund search → GeoJSON FeatureCollection."""
    radius_meters = radius_miles * _MILES_TO_METERS
    point_geo = cast(func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326), Geography)
    site_geo = cast(SuperfundSite.location, Geography)

    stmt = select(SuperfundSite).where(func.ST_DWithin(site_geo, point_geo, radius_meters))

    if state:
        stmt = stmt.where(SuperfundSite.state_code == state.upper()[:2])

    if status and status in _VALID_STATUSES:
        stmt = stmt.where(SuperfundSite.status == status)

    if chemical:
        # Partial case-insensitive search across the contaminants text array
        stmt = stmt.where(
            func.array_to_string(SuperfundSite.contaminants, "|").ilike(f"%{chemical}%")
        )

    sites = (await session.execute(stmt)).scalars().all()

    features: list[SuperfundFeature] = []
    for site in sites:
        shape = to_shape(site.location)
        geom = {"type": "Point", "coordinates": [shape.x, shape.y]}
        npl_str: str | None = str(site.npl_date) if site.npl_date is not None else None
        props = SuperfundFeatureProperties(
            id=site.id,
            epa_id=site.epa_id,
            name=site.name,
            city=site.city,
            state_code=site.state_code,
            status=site.status,
            hrs_score=(float(site.hrs_score) if site.hrs_score is not None else None),
            npl_date=npl_str,
            contaminants=list(site.contaminants) if site.contaminants else [],
            marker_shape="diamond",
        )
        features.append(SuperfundFeature(geometry=geom, properties=props))

    return SuperfundCollection(
        features=features,
        meta=SuperfundCollectionMeta(total_count=len(features)),
    )


async def get_superfund_detail(
    session: AsyncSession,
    epa_id: str,
) -> SuperfundDetail | None:
    """Return full detail for a single Superfund site."""
    result = await session.execute(select(SuperfundSite).where(SuperfundSite.epa_id == epa_id))
    site = result.scalar_one_or_none()
    if site is None:
        return None

    shape = to_shape(site.location)
    npl_str: str | None = str(site.npl_date) if site.npl_date is not None else None
    # Enrich contaminant names with CAS numbers, ATSDR URLs, and PubChem URLs
    # from the chemicals table via a single batch name-match query.
    # For contaminants not in TRI, use the supplementary CAS lookup.
    # 7.BUG.23: Filter out placeholder contaminant names that have no informational value
    placeholder_contaminants = {
        "NOT PROVIDED",
        "UNKNOWN",
        "UNKNOWN LIQ WASTE",
        "N/A",
        "NA",
        "NONE",
        "",
    }
    contaminant_names: list[str] = [
        c for c in (site.contaminants or []) if c.upper().strip() not in placeholder_contaminants
    ]
    if contaminant_names:
        chem_rows = (
            await session.execute(
                select(
                    Chemical.name,
                    Chemical.cas_number,
                    Chemical.atsdr_url,
                    Chemical.pubchem_url,
                ).where(func.upper(Chemical.name).in_([c.upper() for c in contaminant_names]))
            )
        ).all()
        chem_map: dict[str, tuple[str | None, str | None, str | None]] = {
            row.name.upper(): (row.cas_number, row.atsdr_url, row.pubchem_url) for row in chem_rows
        }
    else:
        chem_map = {}

    def _enrich_contaminant(name: str) -> SuperfundContaminant:
        """Build enriched contaminant with CAS/URLs from TRI or supplementary lookup."""
        name_upper = name.upper()

        # Check supplementary lookup for ATSDR URL (fallback for TRI entries missing ATSDR)
        lookup_result = SUPERFUND_CAS_LOOKUP.get(name_upper)
        supplementary_atsdr = None
        if lookup_result:
            # Handle both 2-tuple (cas, atsdr) and 3-tuple (cas, atsdr, pubchem)
            supplementary_atsdr = lookup_result[1] if len(lookup_result) > 1 else None
            # Note: lookup_result[2] contains PubChem URL when available, but not currently used

        if name_upper in chem_map:
            # Found in TRI chemicals table
            cas, atsdr, pubchem = chem_map[name_upper]
            # Use supplementary ATSDR if TRI doesn't have one
            if not atsdr and supplementary_atsdr:
                atsdr = supplementary_atsdr
            return SuperfundContaminant(
                name=name,
                cas_number=cas,
                atsdr_url=atsdr,
                pubchem_url=pubchem,
            )
        # Not in TRI - use supplementary lookup
        if lookup_result:
            cas = lookup_result[0]
            atsdr = lookup_result[1] if len(lookup_result) > 1 else None
            # Use explicit PubChem URL if provided, else auto-generate from CAS
            pubchem = None
            if len(lookup_result) > 2 and lookup_result[2]:
                pubchem = lookup_result[2]
            elif cas and cas != "N/A":
                pubchem = f"https://pubchem.ncbi.nlm.nih.gov/compound/{cas}"
            return SuperfundContaminant(
                name=name,
                cas_number=cas if cas != "N/A" else None,
                atsdr_url=atsdr,
                pubchem_url=pubchem,
            )
        # Not found in any lookup
        return SuperfundContaminant(
            name=name,
            cas_number=None,
            atsdr_url=None,
            pubchem_url=None,
        )

    contaminants = [_enrich_contaminant(c) for c in contaminant_names]

    return SuperfundDetail(
        id=site.id,
        epa_id=site.epa_id,
        name=site.name,
        address=site.address,
        city=site.city,
        state_code=site.state_code,
        zip_code=site.zip_code,
        county=site.county,
        status=site.status,
        hrs_score=(float(site.hrs_score) if site.hrs_score is not None else None),
        npl_date=npl_str,
        contaminants=contaminants,
        epa_progress_url=site.epa_progress_url,
        location={"lat": shape.y, "lon": shape.x},
    )
