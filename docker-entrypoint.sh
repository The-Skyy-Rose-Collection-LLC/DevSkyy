#!/bin/bash
# Enterprise startup script with error handling and logging
# Ensures all errors are visible before the process crashes

# Don't use set -e; we want to see errors before exiting
exec 2>&1  # Redirect stderr to stdout so all output goes to logs

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ======================================"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] DevSkyy Enterprise Platform Startup"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ======================================"

# Set environment variables FIRST (before any Python imports)
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export ENVIRONMENT="${ENVIRONMENT:-production}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Environment: $ENVIRONMENT"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Log Level: $LOG_LEVEL"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Python Unbuffered: True"

# Test Python is working
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Testing Python installation..."
python3 -c "import sys; print(f'Python {sys.version}')" || {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Python not found or failed to import"
    exit 1
}

# Generate required secrets if not provided (BEFORE uvicorn startup)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Checking secrets..."
if [ -z "$JWT_SECRET_KEY" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Generating JWT_SECRET_KEY..."
    JWT_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))" 2>&1) || {
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Failed to generate JWT_SECRET_KEY: $JWT_KEY"
        exit 1
    }
    export JWT_SECRET_KEY="$JWT_KEY"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] JWT_SECRET_KEY generated (length: ${#JWT_SECRET_KEY})"
fi

if [ -z "$ENCRYPTION_MASTER_KEY" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Generating ENCRYPTION_MASTER_KEY..."
    ENC_KEY=$(python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())" 2>&1) || {
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Failed to generate ENCRYPTION_MASTER_KEY: $ENC_KEY"
        exit 1
    }
    export ENCRYPTION_MASTER_KEY="$ENC_KEY"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ENCRYPTION_MASTER_KEY generated (length: ${#ENCRYPTION_MASTER_KEY})"
fi

# Check if main_enterprise.py exists
if [ ! -f "/app/main_enterprise.py" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: main_enterprise.py not found"
    ls -la /app/ | head -20
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] main_enterprise.py found"

# Test that we can import the module (check for syntax errors)
# NOTE: Import test is skipped - uvicorn will catch import errors and fail fast
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Skipping import validation - uvicorn will catch errors on startup"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ======================================"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting uvicorn server..."
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ======================================"

# Start application - use exec to replace shell with uvicorn
# Enterprise production settings:
# - workers: 1 (Fly.io VM constraint, use horizontal scaling)
# - timeout-keep-alive: 65s (Fly.io proxy timeout is 60s, allow buffer)
# - lifespan: on (enable startup/shutdown lifecycle)
# - proxy-headers: enabled for X-Forwarded-* from Fly.io proxy
exec python3 -m uvicorn main_enterprise:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --timeout-keep-alive 65 \
    --lifespan on \
    --proxy-headers \
    --forwarded-allow-ips '*' \
    --access-log 2>&1
