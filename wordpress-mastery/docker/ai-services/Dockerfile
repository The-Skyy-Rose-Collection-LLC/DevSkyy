# Luxury AI Services Docker Container
# Advanced eCommerce AI capabilities for WordPress WooCommerce
# 
# Registry: docker.io/skyyrosellc/devskyy
# Version: 1.0.0

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with secure versions
# SECURITY: pip>=25.3 fixes GHSA-4xh5-x5gv-qwph, setuptools>=78.1.1 fixes CVE-2025-47273
RUN pip install --no-cache-dir --upgrade "pip>=25.3" "setuptools>=78.1.1,<79.0.0" && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/models /app/cache /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV AI_MODEL_PATH=/app/models
ENV CACHE_DIR=/app/cache
ENV LOG_LEVEL=INFO

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Create non-root user
RUN useradd -m -u 1000 aiuser && chown -R aiuser:aiuser /app
USER aiuser

# Start the application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "120", "app:app"]
