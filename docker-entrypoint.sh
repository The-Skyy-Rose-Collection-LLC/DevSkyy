#!/bin/bash
# Enterprise startup script with error handling and logging

set -e

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting DevSkyy Enterprise Platform..."

# Generate required secrets if not provided
if [ -z "$JWT_SECRET_KEY" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Generating JWT_SECRET_KEY (development only)..."
    export JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
fi

if [ -z "$ENCRYPTION_MASTER_KEY" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Generating ENCRYPTION_MASTER_KEY (development only)..."
    export ENCRYPTION_MASTER_KEY=$(python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())")
fi

# Set default environment variables
export ENVIRONMENT="${ENVIRONMENT:-production}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export PYTHON_ENV="${PYTHON_ENV:-production}"
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Environment: $ENVIRONMENT"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Log Level: $LOG_LEVEL"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Python Path: $PYTHONPATH"

# Start application with error handling
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting uvicorn server..."
exec uvicorn main_enterprise:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --timeout-keep-alive 65 \
    --timeout-notify 30 \
    --access-log
