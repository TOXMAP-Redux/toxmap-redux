# TOXMAP Backend
# Python 3.12 + FastAPI + uvicorn (dev mode with hot-reload)
# Production Dockerfile (docker-compose.prod.yml) will be added in Phase 7.

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg2-binary, geoalchemy2, and geopandas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    libgdal-dev \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*

# Trust PyPI hosts (needed when a corporate proxy performs SSL inspection)
ENV PIP_TRUSTED_HOST="pypi.org pypi.python.org files.pythonhosted.org"

# Install Python dependencies from pyproject.toml (base + test + ingestion extras)
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[test,ingestion]"

# Copy application source
COPY . .

# Create non-root user for security (semgrep: dockerfile.security.missing-user)
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose uvicorn port
EXPOSE 8000

# Dev mode: hot-reload enabled (--reload)
# In docker-compose.yml, backend source is volume-mounted to /app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
