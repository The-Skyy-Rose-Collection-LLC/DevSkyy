# syntax=docker/dockerfile:1.4
# Multi-stage Docker build for DevSkyy Enterprise Platform
# Optimized for production deployment with minimal attack surface and BuildKit support

# Build stage
FROM python:3.11-slim as builder

# Set build arguments for BuildKit optimization
ARG BUILDKIT_INLINE_CACHE=1
ARG BUILDKIT_MULTI_PLATFORM=1

# Install build dependencies with BuildKit cache mount
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY docker/requirements.txt .
COPY requirements.txt ./requirements-base.txt

# Install Python dependencies with BuildKit cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN groupadd -r devskyy && useradd -r -g devskyy devskyy

# Install runtime dependencies with BuildKit cache mount
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=devskyy:devskyy . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R devskyy:devskyy /app

# Switch to non-root user
USER devskyy

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "main_enterprise:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
