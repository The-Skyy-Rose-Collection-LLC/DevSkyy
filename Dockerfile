# ============================================================================
# DevSkyy Enterprise Platform - Production Dockerfile
# Multi-stage build for optimized production container with CI/CD integration
# ============================================================================

# Build arguments for CI/CD integration
ARG PYTHON_VERSION=3.11
ARG BUILD_DATE
ARG VCS_REF

# Stage 1: Base Python image
FROM python:${PYTHON_VERSION}-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Dependencies
FROM base AS dependencies

WORKDIR /tmp

# Copy requirements first for better caching
# Use Docker-specific isolated requirements
COPY docker/requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 3: Production Application
FROM base AS application

# Build metadata for CI/CD tracking
LABEL maintainer="DevSkyy Enterprise Team" \
      version="5.1.0" \
      description="DevSkyy Enterprise AI Platform" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}"

# Production environment variables
ENV ENVIRONMENT=production \
    PORT=8000 \
    WORKERS=4 \
    LOG_LEVEL=INFO

WORKDIR /app

# Copy Python dependencies from previous stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

# Switch to non-root user for security
USER appuser

# Expose port
EXPOSE ${PORT}

# Enhanced health check for production
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Production command with configurable workers
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers ${WORKERS} --log-level ${LOG_LEVEL}"]
