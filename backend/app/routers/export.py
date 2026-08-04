"""FastAPI router for data export endpoints.

Routes:
  GET /api/v1/export/csv
  GET /api/v1/export/map-metadata

Phase 2 — story 2.7.x.
"""

from __future__ import annotations

import csv
import datetime
import io
import logging
import re
from collections.abc import Generator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.facility_service import get_export_rows

logger = logging.getLogger(__name__)

router = APIRouter(tags=["export"])

_CSV_FIELDS = [
    "tri_facility_id",
    "name",
    "address",
    "city",
    "state_code",
    "naics_code",
    "chemical_name",
    "cas_number",
    "reporting_year",
    "total_release_lbs",
    "air_release_lbs",
    "water_release_lbs",
    "land_release_lbs",
    "underground_release_lbs",
    "unit_of_measure",
    "form_type",
]

_VALID_MEDIA = {"air", "water", "land", "underground"}


def _safe_slug(text: str | None, max_len: int = 30) -> str:
    """Sanitise text to a safe filename component."""
    if not text:
        return "all"
    return re.sub(r"[^\w\-]", "-", text).lower()[:max_len]


def _csv_generator(rows: list[dict[str, Any]]) -> Generator[str, None, None]:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_CSV_FIELDS)
    writer.writeheader()
    yield buf.getvalue()
    buf.seek(0)
    buf.truncate(0)

    for row in rows:
        writer.writerow(row)
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate(0)


@router.get("/export/csv")
async def export_csv(
    lat: Annotated[float, Query(ge=-90.0, le=90.0)],
    lon: Annotated[float, Query(ge=-180.0, le=180.0)],
    radius_miles: Annotated[float, Query(gt=0, le=500.0)],
    bbox: Annotated[str | None, Query()] = None,
    year: Annotated[int | None, Query()] = None,
    chemical: Annotated[str | None, Query()] = None,
    naics: Annotated[str | None, Query()] = None,
    medium: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query(max_length=2)] = None,
    restrict_to_state: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=2000)] = 500,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream a CSV of facility release data matching the spatial query."""
    rows = await get_export_rows(
        session=db,
        lat=lat,
        lon=lon,
        radius_miles=radius_miles,
        bbox=bbox,
        year=year,
        chemical=chemical,
        naics=naics,
        medium=medium if medium in _VALID_MEDIA else None,
        state=state,
        limit=limit,
    )
    year_label = str(year) if year is not None else "latest"
    chem_slug = _safe_slug(chemical)
    filename = f"toxmap_{year_label}_{chem_slug}.csv"

    return StreamingResponse(
        _csv_generator(rows),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/export/map-metadata")
async def export_map_metadata(
    lat: Annotated[float, Query(ge=-90.0, le=90.0)],
    lon: Annotated[float, Query(ge=-180.0, le=180.0)],
    radius_miles: Annotated[float, Query(gt=0, le=500.0)],
    bbox: Annotated[str | None, Query()] = None,
    year: Annotated[int | None, Query()] = None,
    chemical: Annotated[str | None, Query()] = None,
    naics: Annotated[str | None, Query()] = None,
    medium: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query(max_length=2)] = None,
    restrict_to_state: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=2000)] = 500,
) -> dict[str, Any]:
    """Return metadata describing the export that would be generated."""
    year_label = str(year) if year is not None else "latest"
    chem_slug = _safe_slug(chemical)
    filename = f"toxmap_{year_label}_{chem_slug}.csv"
    generated_at = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "export_filename": filename,
        "query": {
            "lat": lat,
            "lon": lon,
            "radius_miles": radius_miles,
            "bbox": bbox,
            "year": year,
            "chemical": chemical,
            "naics": naics,
            "medium": medium,
            "state": state,
            "restrict_to_state": restrict_to_state,
            "limit": limit,
        },
        "generated_at": generated_at,
    }
