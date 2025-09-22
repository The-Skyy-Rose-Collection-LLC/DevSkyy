# Multi-stage build for production optimization
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --only=production

COPY frontend/ ./
RUN npm run build

# Python backend stage
FROM python:3.12-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# System deps
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python deps first (better layer caching)
COPY requirements.txt ./
COPY backend/requirements.txt ./backend/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r backend/requirements.txt

# Copy backend application
COPY . .

# Copy built frontend from previous stage
COPY --from=frontend-builder /frontend/build ./static

# Configure nginx for serving static files
COPY nginx.conf /etc/nginx/nginx.conf

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

EXPOSE 8000 80

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "nginx && uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4"]
