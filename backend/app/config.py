"""TOXMAP Backend — Application settings.

Loads from environment variables (and backend/.env if present).
All database connection strings are read here — never hardcoded.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration sourced exclusively from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Async URL used by FastAPI / SQLAlchemy (asyncpg driver)
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/toxmap"
    # Sync URL used by Alembic and psycopg2-based tools
    database_url_sync: str = "postgresql+psycopg2://postgres:postgres@postgres:5432/toxmap"
    # CORS — comma-separated list of allowed origins
    allowed_origins: str = "http://localhost:3000"


settings = Settings()
