# DevSkyy Platform - Multi-stage Docker Build
# Optimized for production deployment with security hardening

# Build stage for Node.js frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy source code
COPY src/ ./src/
COPY config/typescript/ ./config/typescript/
COPY config/testing/ ./config/testing/

# Build frontend assets
RUN npm run build

# Build stage for Python backend
FROM python:3.11-slim AS backend-builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1

# Set work directory
WORKDIR /app

# Copy Poetry configuration
COPY pyproject.toml poetry.lock ./

# Configure Poetry
RUN poetry config virtualenvs.create false

# Install Python dependencies
RUN poetry install --only=main --no-dev

# Production stage
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app"

# Create non-root user for security
RUN groupadd -r devskyy && useradd -r -g devskyy devskyy

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set work directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy frontend build artifacts
COPY --from=frontend-builder /app/frontend/dist ./static/

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/uploads && \
    chown -R devskyy:devskyy /app

# Switch to non-root user
USER devskyy

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "main_enterprise:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
