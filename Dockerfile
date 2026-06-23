# syntax=docker/dockerfile:1.7
# =============================================================================
# DevSkyy Platform — Python API / Worker image (multi-stage, security-hardened)
# =============================================================================
# ONE image, three roles (selected by the compose `command:`):
#   • API          → docker-entrypoint.sh (default) → uvicorn main_enterprise:app
#   • task worker  → python -m agent_sdk.worker
#   • elite worker → python -m skyyrose.elite_studio worker
# The frontend (Next.js) is NOT built here — it deploys to Vercel (devskyy.app).
# Baking it in served zero requests and doubled build time.
#
# INSTALL_TARGET selects which optional-dependency extras to add on top of the
# base deps (default "all"). NOTE: the ML stack (torch/transformers/diffusers/
# chromadb) lives in the BASE [project.dependencies], so every target pulls it —
# a genuinely torch-free image needs those moved into an optional group first.
#   docker build .                              # INSTALL_TARGET=all (default)
#   docker build --build-arg INSTALL_TARGET=api # base + api extras only
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: dependency builder — installs third-party wheels into a clean prefix.
# Cache key is pyproject.toml + README.md only, so source edits never bust it.
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build toolchain for native wheels. On arm64 several deps have no prebuilt wheel
# and compile from source: reportlab's renderPM needs freetype (ft2build.h),
# Pillow needs jpeg/zlib, asyncpg/psycopg need libpq.
RUN apt-get update --fix-missing || apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libfreetype6-dev \
        libjpeg-dev \
        zlib1g-dev \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# uv = fast, reliable resolver/installer. python:3.12-slim ships NO setuptools and
# pip backtracks for ~10min on the large .[all] set (then dies on a missing
# setuptools.build_meta during sdist metadata builds). uv resolves deterministically
# and provisions build envs robustly. Installed into the system interpreter so the
# production stage's site-packages copy still works.
COPY --from=ghcr.io/astral-sh/uv:0.9.2 /uv /uvx /bin/

# Which optional-dependency set to install (see pyproject [project.optional-dependencies]).
ARG INSTALL_TARGET=all

ENV UV_HTTP_TIMEOUT=600 \
    UV_SYSTEM_PYTHON=1 \
    UV_LINK_MODE=copy

# Only metadata first → this expensive layer is cached until deps actually change.
# The devskyy wheel built here is intentionally empty (source isn't copied yet);
# the runtime stage adds the source via COPY . . and runs it from /app.
COPY pyproject.toml README.md ./

# BuildKit cache mount keeps uv's wheel cache warm across rebuilds.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system ".[${INSTALL_TARGET}]"

# -----------------------------------------------------------------------------
# Stage 2: production runtime — slim, non-root, only runtime libs.
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS production

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app:/app/sdk/python" \
    PORT=8000

# Runtime-only system libs: libpq5 (postgres clients), curl (healthcheck),
# tini (PID1), libgl1 + libglib2.0-0 (OpenCV/cv2 — imagery & render-QC pipeline),
# libfreetype6 (Pillow text rendering on arm64 source builds), fonts-dejavu-core
# (TrueType font the imagery overlays load by path — otherwise a bitmap fallback).
RUN apt-get update --fix-missing || apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        ca-certificates \
        tini \
        libgl1 \
        libglib2.0-0 \
        libfreetype6 \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Non-root runtime user.
RUN groupadd -r devskyy && useradd -r -g devskyy -m -u 1000 devskyy

WORKDIR /app

# Installed third-party packages + console scripts from the builder.
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Application source. `.dockerignore` already stripped VCS, deps, secrets, the
# frontend, and all binary media — so this copies code + canonical text data
# (catalog CSV, visual manifest, per-SKU dossiers) and nothing heavy.
COPY . .

RUN chmod +x /app/docker-entrypoint.sh && \
    mkdir -p /app/logs /app/data /app/uploads && \
    chown -R devskyy:devskyy /app

USER devskyy

# OCI metadata (overridable at build time via --build-arg).
ARG BUILD_VERSION=dev
ARG BUILD_REVISION=unknown
LABEL org.opencontainers.image.title="DevSkyy Platform" \
      org.opencontainers.image.description="AI-driven luxury fashion e-commerce platform (API + workers)" \
      org.opencontainers.image.vendor="SkyyRose" \
      org.opencontainers.image.source="https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy" \
      org.opencontainers.image.version="${BUILD_VERSION}" \
      org.opencontainers.image.revision="${BUILD_REVISION}"

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT}/health" || exit 1

EXPOSE 8000

# tini = PID 1 → proper signal forwarding / zombie reaping for the workers.
ENTRYPOINT ["/usr/bin/tini", "--", "/app/docker-entrypoint.sh"]
