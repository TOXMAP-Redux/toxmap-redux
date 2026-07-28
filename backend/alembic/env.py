"""Alembic environment configuration for TOXMAP.

Story 1.1.4: configured for:
- Autogenerate from SQLAlchemy ORM models (all 7 tables)
- DATABASE_URL_SYNC from environment variable (psycopg2 sync driver)
- Offline and online migration modes
- GeoAlchemy2 PostGIS geometry types rendered correctly
"""

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import Base so autogenerate can inspect metadata
from app.database import Base

# Import all models to register them with Base.metadata
import app.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# All 7 ORM tables are registered in Base.metadata via app.models import above
target_metadata = Base.metadata

# Tables managed by this app (autogenerate only compares against these)
_APP_TABLES = {m.name for m in Base.metadata.sorted_tables}


def include_object(
    obj: object,
    name: str,
    type_: str,
    reflected: bool,
    compare_to: object,
) -> bool:
    """Exclude PostGIS/TIGER/topology tables from autogenerate comparisons.

    Without this filter, Alembic detects every PostGIS-installed table in the
    public schema as a "removed" table and emits destructive drop_table ops.
    Only tables owned by our ORM metadata are tracked.
    """
    if type_ == "table" and reflected and name not in _APP_TABLES:
        return False
    return True


def get_url() -> str:
    """Return the sync database URL from environment (psycopg2 driver).

    Alembic requires a synchronous connection — never use the asyncpg URL here.
    """
    url = os.environ.get("DATABASE_URL_SYNC")
    if not url:
        # Fallback for local runs outside Docker
        url = config.get_main_option("sqlalchemy.url")
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL without a live DB connection)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (applies SQL directly to the database)."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
