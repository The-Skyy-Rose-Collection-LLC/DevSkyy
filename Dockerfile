# ============================================================================
# DevSkyy Enterprise Platform - Unified Multi-Stage Dockerfile
# Version: 5.2.0 | Truth Protocol Compliant
# ============================================================================
# This Dockerfile supports multiple environments through build targets:
#   - development: Full dev tools, hot reload, debugging
#   - production: Minimal, security-hardened, optimized
# ============================================================================

# Build arguments for flexibility
ARG PYTHON_VERSION=3.11
ARG BUILD_DATE="unknown"
ARG VCS_REF="unknown"

# ============================================================================
# Stage 1: Base Image (Common Foundation)
# ============================================================================
FROM python:${PYTHON_VERSION}-slim AS base

# Metadata for tracking
LABEL maintainer="DevSkyy Enterprise Team <enterprise@devskyy.com>"
LABEL org.opencontainers.image.title="DevSkyy Enterprise Platform"
LABEL org.opencontainers.image.version="5.2.0"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.description="Enterprise AI Platform with Multi-Agent Orchestration"

# Python environment variables (best practices)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Create non-root user early (security best practice - Truth Protocol Rule #13)
RUN groupadd -r devskyy -g 1000 && \
    useradd -r -u 1000 -g devskyy -m -s /bin/bash devskyy && \
    mkdir -p /app && \
    chown -R devskyy:devskyy /app

# Install system dependencies (minimal set)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials
    gcc \
    g++ \
    make \
    # PostgreSQL client libraries
    libpq-dev \
    libpq5 \
    # Networking utilities
    curl \
    wget \
    # SSL/TLS support
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# ============================================================================
# Stage 2: Dependencies Builder (Python Packages)
# ============================================================================
FROM base AS dependencies

# Copy requirements files first (Docker layer caching optimization)
COPY requirements.txt requirements-production.txt ./

# SECURITY: Install critical security updates per Truth Protocol Rule #13
# - pip>=25.3: Fixes CVE-2025-8869 (path traversal)
# - cryptography>=46.0.3: Fixes CVE-2024-26130, CVE-2023-50782, CVE-2024-0727, GHSA-h4gh-qq45-vh27
# - setuptools>=78.1.1: Fixes CVE-2025-47273, CVE-2024-6345
RUN pip install --no-cache-dir --upgrade \
    "pip>=25.3" \
    "cryptography>=46.0.3,<47.0.0" \
    "setuptools>=78.1.1,<79.0.0"

# Install production dependencies
RUN pip install --no-cache-dir --user -r requirements-production.txt

# ============================================================================
# Stage 3: Development Environment (Optional Target)
# ============================================================================
FROM dependencies AS development

# Install additional development dependencies
COPY requirements-dev.txt requirements-test.txt ./
RUN pip install --no-cache-dir --user -r requirements-dev.txt && \
    pip install --no-cache-dir --user -r requirements-test.txt

# Copy application code with proper ownership
COPY --chown=devskyy:devskyy . .

# Create necessary directories for development
RUN mkdir -p /app/logs /app/data /app/artifacts /app/.pytest_cache && \
    chown -R devskyy:devskyy /app

# Switch to non-root user
USER devskyy

# Add Python user packages to PATH
ENV PATH=/root/.local/bin:$PATH

# Development environment variables
ENV ENVIRONMENT=development \
    LOG_LEVEL=DEBUG \
    RELOAD=true

# Expose development ports
EXPOSE 8000 5678

# Health check for development
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Development command with hot reload
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]

# ============================================================================
# Stage 4: Production Environment (Default Target)
# ============================================================================
FROM base AS production

# Copy Python packages from dependencies stage (minimal footprint)
COPY --from=dependencies --chown=devskyy:devskyy /root/.local /home/devskyy/.local

# Copy application code with proper ownership (Truth Protocol Rule #13)
COPY --chown=devskyy:devskyy . .

# Create production directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/artifacts && \
    chown -R devskyy:devskyy /app && \
    # Remove unnecessary files to reduce image size
    find /app -type f -name "*.pyc" -delete && \
    find /app -type d -name "__pycache__" -delete && \
    find /app -type d -name ".pytest_cache" -delete

# Switch to non-root user (Truth Protocol Rule #13 - Security Baseline)
USER devskyy

# Add Python user packages to PATH
ENV PATH=/home/devskyy/.local/bin:$PATH

# Production environment variables
ENV ENVIRONMENT=production \
    PORT=8000 \
    WORKERS=4 \
    LOG_LEVEL=INFO \
    RELOAD=false

# Expose application port
EXPOSE ${PORT}

# Enhanced health check for production (Truth Protocol Rule #12)
# P95 Latency < 200ms requirement
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/v1/monitoring/health || exit 1

# Production command with multiple workers for performance
# Per Truth Protocol Rule #12: P95 < 200ms SLO
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers ${WORKERS} --log-level ${LOG_LEVEL}"]

# ============================================================================
# Build Instructions:
# ============================================================================
# Development:
#   docker build --target development -t devskyy:dev .
#   docker run -p 8000:8000 -v $(pwd):/app devskyy:dev
#
# Production:
#   docker build --target production -t devskyy:prod \
#     --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
#     --build-arg VCS_REF=$(git rev-parse --short HEAD) .
#   docker run -p 8000:8000 devskyy:prod
# ============================================================================
