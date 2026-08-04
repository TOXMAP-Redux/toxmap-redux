"""FastAPI router for geocode proxy endpoint.

Routes:
  GET /api/v1/geocode

Proxies to Photon (photon.komoot.io) — a free, no-key geocoder built on
OpenStreetMap data. Replaced Nominatim (OSM Foundation) which was blocking
requests from server IPs. Photon is CORS-enabled and does not require a
User-Agent policy compliance step.

Phase 2 — story 2.7.x.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(tags=["geocode"])

_PHOTON_URL = "https://photon.komoot.io/api/"
_USER_AGENT = "TOXMAP-clone/1.0 (open-source; github.com/TOXMAP-Redux/toxmap-redux)"
_TIMEOUT_SECONDS = 10.0


@router.get("/geocode")
async def geocode(
    q: Annotated[
        str,
        Query(min_length=1, description="Address or place name to geocode"),
    ],
    limit: Annotated[int, Query(ge=1, le=5)] = 1,
) -> list[dict[str, Any]]:
    """Proxy a geocode request to Photon and return normalised results.

    Photon returns GeoJSON FeatureCollection; coordinates are [lon, lat].
    """
    params: dict[str, str] = {
        "q": q,
        "limit": str(limit),
        "lang": "en",
    }
    headers = {"User-Agent": _USER_AGENT}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.get(_PHOTON_URL, params=params, headers=headers)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
    except httpx.ConnectError as exc:
        logger.warning("Photon connection error: %s", exc)
        raise HTTPException(status_code=503, detail="Geocode service is unreachable") from exc
    except httpx.TimeoutException as exc:
        logger.warning("Photon timeout: %s", exc)
        raise HTTPException(status_code=503, detail="Geocode service timed out") from exc
    except httpx.HTTPStatusError as exc:
        logger.warning("Photon HTTP error: %s", exc)
        raise HTTPException(status_code=503, detail="Geocode service returned an error") from exc

    features: list[dict[str, Any]] = data.get("features", [])
    results = []
    for feature in features:
        coords = feature.get("geometry", {}).get("coordinates")
        props = feature.get("properties", {})
        if not coords or len(coords) < 2:
            continue
        lon, lat = float(coords[0]), float(coords[1])
        display_name = ", ".join(
            filter(
                None,
                [
                    props.get("name"),
                    props.get("city"),
                    props.get("state"),
                    props.get("country"),
                ],
            )
        )
        results.append(
            {
                "display_name": display_name or q,
                "lat": lat,
                "lon": lon,
                "place_type": props.get("type"),
                "boundingbox": None,
            }
        )

    return results
