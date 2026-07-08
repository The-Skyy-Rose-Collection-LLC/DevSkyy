# Clothing 3D Worker — TRELLIS pipeline background processor.
#
# Build:
#   docker build -f deploy/clothing_3d/Dockerfile -t devskyy/clothing-3d-worker:latest .
#
# Run (HF Space backend, in-memory queue/store):
#   docker run --rm -e TRELLIS_BACKEND=hf_space devskyy/clothing-3d-worker:latest
#
# Run (Replicate backend, Redis queue/store):
#   docker run --rm \
#     -e TRELLIS_BACKEND=replicate \
#     -e REPLICATE_API_TOKEN=$REPLICATE_API_TOKEN \
#     -e REDIS_URL=redis://redis:6379/0 \
#     -e CLOTHING_3D_CONCURRENCY=4 \
#     devskyy/clothing-3d-worker:latest

FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    THREE_D_OUTPUT_DIR=/var/data/3d-models-generated \
    TRELLIS_CACHE_DIR=/var/cache/trellis \
    LOG_LEVEL=INFO

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Application source (only what the worker actually needs). Copied before the
# pip install below because `pip install -e .` needs pyproject.toml + the
# package source present to resolve the editable install.
COPY pyproject.toml requirements-trellis.txt /app/
COPY core/ /app/core/
COPY services/ /app/services/
COPY pipelines/ /app/pipelines/
COPY agents/ /app/agents/
COPY security/ /app/security/

RUN pip install --no-cache-dir -e . -r requirements-trellis.txt redis

RUN mkdir -p "$THREE_D_OUTPUT_DIR" "$TRELLIS_CACHE_DIR"

# Run as unprivileged user.
RUN useradd --create-home --uid 10001 worker \
    && chown -R worker:worker /app /var/data /var/cache
USER worker

# Healthcheck: exit-code from `cli health` — non-zero when no backend is healthy.
HEALTHCHECK --interval=30s --timeout=15s --start-period=20s --retries=3 \
    CMD python -m pipelines.clothing_3d.cli health || exit 1

ENTRYPOINT ["python", "-m", "pipelines.clothing_3d.worker"]
