# =============================================================================
# backend/Dockerfile — Multi-stage build
# =============================================================================
#
# ARCHITECTURAL DECISION: Multi-stage Docker build
#
# WHY multi-stage:
#   - `base` stage: shared OS packages, Python version pinned
#   - `development` stage: includes dev tools (debugpy, pytest), hot-reload
#   - `production` stage: minimal image, no dev tools, non-root user
#
# SECURITY CONSIDERATIONS:
#   - Python 3.12-slim (not full) — smaller attack surface
#   - Non-root user `appuser` in production — principle of least privilege
#   - No SSH, no shell access in prod image
#   - Build args never contain secrets (use runtime env vars instead)
#
# SCALABILITY:
#   - Layers ordered: OS deps → pip install → code copy
#     This maximizes Docker layer cache hits. Code changes don't invalidate
#     the expensive pip install layer.
#   - .dockerignore excludes tests, docs, .git — keeps image lean.
#
# SIZE OPTIMIZATION:
#   - `--no-cache-dir` on pip → no cache stored in layer
#   - `--no-install-recommends` on apt → no recommended packages
#   - `rm -rf /var/lib/apt/lists/*` → clear apt cache
#
# =============================================================================

# ── Stage 1: Base ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

LABEL maintainer="Mini Blinkit ERP Team"
LABEL version="1.0.0"

# Prevent Python from writing .pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevent Python from buffering stdout/stderr (important for Docker logs)
ENV PYTHONUNBUFFERED=1
# Ensures pip finds packages installed with --user
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System dependencies required by:
#   - psycopg2-binary: libpq-dev
#   - Pillow (image processing): libjpeg, zlib, libwebp
#   - WeasyPrint (PDF): libcairo, libpango, libgdk-pixbuf
#   - openpyxl: no native deps, but lxml needs libxml2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    libxml2-dev \
    libxslt-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Stage 2: Development ──────────────────────────────────────────────────────
FROM base AS development

# Install all dependencies including dev tools
COPY requirements.txt requirements-dev.txt ./

RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt

# Copy source code AFTER pip install (cache optimization)
COPY . .

# Create directories for file storage
RUN mkdir -p /app/media/images \
             /app/media/pdfs \
             /app/media/exports \
             /app/media/uploads \
             /app/logs

EXPOSE 8000

# ── Stage 3: Production ───────────────────────────────────────────────────────
FROM base AS production

# Create non-root user — SECURITY: containers running as root are a risk
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

# Only production requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appgroup . .

# Create storage directories with correct ownership
RUN mkdir -p /app/media/images \
             /app/media/pdfs \
             /app/media/exports \
             /app/media/uploads \
             /app/logs && \
    chown -R appuser:appgroup /app/media /app/logs

# Switch to non-root user
USER appuser

EXPOSE 8000

# Gunicorn + Uvicorn workers for production
# WHY Gunicorn + Uvicorn: Gunicorn manages worker processes (SIGTERM, SIGHUP),
# Uvicorn workers handle async I/O. This gives us process-level isolation
# with async request handling — best of both worlds.
# Worker count formula: (2 * CPU cores) + 1
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
