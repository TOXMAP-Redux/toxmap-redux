"""TOXMAP Backend — Async SQLAlchemy engine and session factory.

Import ``AsyncSession`` and ``get_db`` here for use in FastAPI dependency
injection. Alembic uses ``DATABASE_URL_SYNC`` from config (not this module).
"""

import os
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings


class Base(DeclarativeBase):
    """Shared declarative base for all SQLAlchemy ORM models."""


# In test environments (TESTING=1), use NullPool to prevent asyncpg connection
# pool Futures from leaking across pytest-asyncio's per-test event loops.
# NullPool creates a fresh connection per request and closes it immediately —
# no pooling, no cross-loop Future conflicts.
_engine_kwargs: dict[str, Any] = {"echo": False}
if os.getenv("TESTING") == "1":
    _engine_kwargs["poolclass"] = NullPool
else:
    _engine_kwargs["pool_pre_ping"] = True

engine = create_async_engine(settings.database_url, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session per request."""
    async with AsyncSessionLocal() as session:
        yield session
