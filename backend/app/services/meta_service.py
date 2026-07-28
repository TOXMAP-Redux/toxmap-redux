"""Service layer for GET /api/v1/meta.

Phase 2 — story 2.7.3.
"""

from __future__ import annotations

import logging

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.facility import Facility
from app.models.release_event import ReleaseEvent
from app.schemas.meta import MetaResponse

logger = logging.getLogger(__name__)


async def get_meta(session: AsyncSession) -> MetaResponse | None:
    """Return API metadata. Returns None (→ 503) if release_events is empty."""
    years_result = await session.execute(
        select(distinct(ReleaseEvent.reporting_year)).order_by(
            ReleaseEvent.reporting_year
        )
    )
    available_years: list[int] = [row[0] for row in years_result.all()]

    if not available_years:
        return None  # caller returns 503

    latest_year: int = max(available_years)

    fac_count: int = (
        await session.execute(select(func.count()).select_from(Facility))
    ).scalar() or 0

    rel_count: int = (
        await session.execute(select(func.count()).select_from(ReleaseEvent))
    ).scalar() or 0

    # Dev-mode stub: no ingestion metadata table exists yet (tracked as known
    # limitation in Phase 2 notes). A real vintage_label is written by the
    # ingestion pipeline's --vintage flag and read from a metadata table.
    # In production DuckDB WASM mode, the label comes from manifest.json on R2.
    # "unknown" is reserved for truly empty databases (handled above by the
    # None / 503 guard). Here we construct a factual label from what we know:
    # the max reporting year in the database and the fact it is seed/dev data.
    vintage_label_stub = (
        f"Seed data · {min(available_years)}–{latest_year}"
        if latest_year
        else "unknown"
    )

    return MetaResponse(
        vintage_label=vintage_label_stub,
        build_date="unknown",
        available_years=available_years,
        latest_year=latest_year,
        total_facility_count=fac_count,
        total_release_event_count=rel_count,
        source="fastapi-dev",
    )
