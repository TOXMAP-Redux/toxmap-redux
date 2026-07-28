"""TOXMAP Backend — FastAPI application factory.

Phase 0: health endpoint only.
Phase 2: all 17 domain API endpoints + /api/v1/meta registered here.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.routers import (
    chemicals,
    demographics,
    export,
    facilities,
    geocode,
    layers,
    meta as meta_router,
    releases,
    superfund,
)

logger = logging.getLogger(__name__)

_API_V1 = "/api/v1"

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

_SECURITY_HEADERS: list[tuple[bytes, bytes]] = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"x-xss-protection", b"1; mode=block"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
]


class SecurityHeadersMiddleware:
    """Pure ASGI middleware — adds security headers without BaseHTTPMiddleware.

    Avoids the BaseHTTPMiddleware event-loop conflict when TestClient is used
    with asyncpg (pool_pre_ping=True). Pure ASGI middlewares are safe with
    the starlette TestClient because they do not create background tasks.
    """

    def __init__(self, app: Callable) -> None:  # type: ignore[type-arg]
        self.app = app

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:  # type: ignore[type-arg]
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: dict) -> None:  # type: ignore[type-arg]
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(_SECURITY_HEADERS)
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_headers)


def create_app() -> FastAPI:
    """Application factory — returns a configured FastAPI instance.

    Used by:
    - uvicorn in Docker (``CMD ["uvicorn", "app.main:app", ...]``)
    - TestClient in tests/conftest.py (``api_client`` fixture)
    """
    app = FastAPI(
        title="TOXMAP API",
        description="Geospatial REST API for EPA TRI, Superfund, and Census data.",
        version="0.1.0",
    )

    # --- Rate limiter setup (must precede middleware registration) ---
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # --- Global 500 error sanitizer: no tracebacks, no sqlalchemy detail ---
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "code": "INTERNAL_ERROR"},
        )

    allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
    allowed_origins = [o.strip() for o in allowed_origins_raw.split(",")]

    # Middleware — add_middleware() is LIFO; last added = outermost (runs first on request).
    # Execution order on request:  SlowAPI → SecurityHeaders → CORS → App
    # Execution order on response: App → CORS → SecurityHeaders → SlowAPI
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(SlowAPIMiddleware)

    # --- Infrastructure ---
    @app.get("/health", tags=["infrastructure"])
    async def health() -> dict[str, str]:
        """Liveness probe — returns ok when the FastAPI process is running."""
        return {"status": "ok"}

    # --- Domain routers (Phase 2) ---
    app.include_router(facilities.router, prefix=_API_V1)
    app.include_router(releases.router, prefix=_API_V1)
    app.include_router(chemicals.router, prefix=_API_V1)
    app.include_router(superfund.router, prefix=_API_V1)
    app.include_router(demographics.router, prefix=_API_V1)
    app.include_router(layers.router, prefix=_API_V1)
    app.include_router(export.router, prefix=_API_V1)
    app.include_router(geocode.router, prefix=_API_V1)
    app.include_router(meta_router.router, prefix=_API_V1)

    return app


# Module-level app instance for uvicorn
app = create_app()
