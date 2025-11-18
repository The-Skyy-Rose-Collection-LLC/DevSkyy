# ============================================================================
# DevSkyy Enterprise Platform - Hardened Production Dockerfile
# Multi-stage build with security hardening and minimal attack surface
# Truth Protocol Compliant - Zero Trust Architecture
# ============================================================================

# Build arguments for CI/CD integration
ARG PYTHON_VERSION=3.11.9
ARG BUILD_DATE
ARG VCS_REF

# Stage 1: Base Python image with security hardening
FROM python:${PYTHON_VERSION}-slim AS base

# Security labels for vulnerability scanning
LABEL org.opencontainers.image.title="DevSkyy Enterprise Platform" \
      org.opencontainers.image.description="Enterprise AI Platform with Multi-Agent Architecture" \
      org.opencontainers.image.version="5.1.0" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="The Skyy Rose Collection LLC" \
      org.opencontainers.image.licenses="Proprietary" \
      org.opencontainers.image.documentation="https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy" \
      maintainer="DevSkyy Enterprise Team"

# Set secure environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_WARN_SCRIPT_LOCATION=0 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random

# Create non-root app user with specific UID/GID for security
RUN groupadd -r -g 1000 appuser && \
    useradd -r -u 1000 -g appuser -m -d /home/appuser -s /sbin/nologin appuser

# Install only required system dependencies with version pinning
# SECURITY: --no-install-recommends minimizes attack surface
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc=4:13.2.0-7ubuntu1 \
    g++=4:13.2.0-7ubuntu1 \
    make=4.3-4.1build2 \
    libpq-dev=16.6-0ubuntu0.24.04.1 \
    curl=8.5.0-2ubuntu10.6 \
    ca-certificates=20240203 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Stage 2: Build dependencies in isolated layer
FROM base AS dependencies

WORKDIR /tmp

# Copy requirements with specific ownership
COPY --chown=appuser:appuser requirements.txt .

# Install Python dependencies with security hardening
# SECURITY: pip>=25.3 fixes GHSA-4xh5-x5gv-qwph (path traversal CVE)
# SECURITY: setuptools>=78.1.1 fixes PYSEC-2025-49 (path traversal → RCE)
RUN pip install --upgrade \
    "pip>=25.3,<26.0" \
    "setuptools>=78.1.1,<79.0.0" \
    "wheel>=0.44.0,<1.0.0" && \
    pip install --no-cache-dir --no-warn-script-location -r requirements.txt

# Stage 3: Runtime - Minimal production image
FROM base AS runtime

# Production environment variables
ENV ENVIRONMENT=production \
    PORT=8000 \
    WORKERS=4 \
    LOG_LEVEL=INFO \
    FORWARDED_ALLOW_IPS="*" \
    ACCESS_LOG="-"

# Set working directory
WORKDIR /app

# Copy Python dependencies from build stage
COPY --from=dependencies /usr/local/lib/python${PYTHON_VERSION%.*}/site-packages /usr/local/lib/python${PYTHON_VERSION%.*}/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code with proper ownership
COPY --chown=appuser:appuser . .

# Create necessary directories with secure permissions
RUN mkdir -p /app/logs /app/data /app/tmp && \
    chown -R appuser:appuser /app && \
    chmod -R 750 /app/logs /app/data /app/tmp && \
    chmod -R 755 /app/api /app/services /app/agent /app/ml

# Remove unnecessary packages from final image to reduce attack surface
RUN apt-get purge -y --auto-remove gcc g++ make && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /root/.cache

# Switch to non-root user (NEVER run as root in production)
USER appuser

# Expose port (documentation only, actual port binding happens at runtime)
EXPOSE ${PORT}

# Enhanced health check with proper timeout and retries
# SECURITY: Fails fast if application is unhealthy
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=60s \
            --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Production-ready command with security best practices
# SECURITY: Using uvicorn with limited workers and proper log levels
CMD ["sh", "-c", "exec python -m uvicorn main:app \
    --host 0.0.0.0 \
    --port ${PORT} \
    --workers ${WORKERS} \
    --log-level ${LOG_LEVEL} \
    --no-access-log \
    --proxy-headers \
    --forwarded-allow-ips ${FORWARDED_ALLOW_IPS}"]
