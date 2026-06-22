# DevSkyy Platform - Multi-stage Docker Build
# Optimized for production deployment with security hardening
# Enterprise hardening: Retry logic, timeouts, minimal layers

# =============================================================================
# Stage 1: Frontend Builder (Next.js Dashboard)
# =============================================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files from frontend directory
COPY frontend/package*.json ./

# Install dependencies with legacy peer deps (React version conflicts)
RUN npm ci --legacy-peer-deps && npm cache clean --force

# Copy Next.js source code from frontend directory
COPY frontend/app/ ./app/
COPY frontend/components/ ./components/
COPY frontend/contexts/ ./contexts/
COPY frontend/hooks/ ./hooks/
COPY frontend/lib/ ./lib/
COPY frontend/public/ ./public/
COPY frontend/types/ ./types/
COPY frontend/*.config.js ./
COPY frontend/*.config.ts ./
COPY frontend/tsconfig*.json ./
COPY frontend/next-env.d.ts ./

# Build Next.js application
RUN npm run build

# =============================================================================
# Stage 2: Python Backend Builder
# =============================================================================
FROM python:3.12-slim AS backend-builder

# Prevent apt from hanging
ENV DEBIAN_FRONTEND=noninteractive

# Set Python environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Enterprise hardening: apt-get with retry logic and timeout
RUN apt-get update --fix-missing || apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy project metadata only. Dependencies resolve from pyproject.toml; the
# application source is added in the production stage and run from /app, so the
# builder only needs to install third-party deps. setuptools' explicit
# packages.find produces an (empty) devskyy wheel here — verified to build from
# pyproject.toml + README.md alone — which keeps this expensive layer cacheable
# (busts only when pyproject/README change, not on source edits).
COPY pyproject.toml README.md ./

# Install all production dependencies. Documented Docker install target is
# ".[all]" (requirements.txt is a deprecated -e . stub). Longer timeout for the
# large ML wheels (torch/transformers/diffusers).
RUN pip install --no-cache-dir --timeout=600 ".[all]"

# =============================================================================
# Stage 3: Production Runtime
# =============================================================================
FROM python:3.12-slim AS production

# Prevent apt from hanging
ENV DEBIAN_FRONTEND=noninteractive

# Set Python environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app"

# Create non-root user for security
RUN groupadd -r devskyy && useradd -r -g devskyy -m -u 1000 devskyy

# Install runtime dependencies with retry logic
RUN apt-get update --fix-missing || apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy Next.js build artifacts
COPY --from=frontend-builder /app/frontend/.next ./.next/
COPY --from=frontend-builder /app/frontend/public ./public/

# Verify Next.js build artifacts exist
RUN test -d ./.next || (echo "ERROR: .next directory not found" && exit 1)
RUN test -d ./public || (echo "ERROR: public directory not found" && exit 1)

# Copy application code
COPY sdk/python/agent_sdk/ ./agent_sdk/
COPY agents/ ./agents/
COPY api/ ./api/
COPY adk/ ./adk/
COPY core/ ./core/
COPY utils/ ./utils/
COPY integrations/ ./integrations/
COPY llm/ ./llm/
COPY mcp_servers/ ./mcp_servers/
COPY orchestration/ ./orchestration/
COPY security/ ./security/
COPY wordpress/ ./wordpress/
COPY main_enterprise.py ./
COPY mcp_tools/ ./mcp_tools/
COPY devskyy_mcp.py ./
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/uploads && \
    chown -R devskyy:devskyy /app

# Switch to non-root user
USER devskyy

# Health check with timeout
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start with entrypoint script that handles startup errors
ENTRYPOINT ["/app/docker-entrypoint.sh"]
