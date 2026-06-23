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

# Generate required secrets if not provided (BEFORE uvicorn startup). This keeps
# the API + workers bootable without a committed .env; .env.docker is the
# expected production source (see docs/DOCKER.md). Ephemeral keys rotate on
# restart — set them explicitly for any real deployment.
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Checking secrets..."
ts() { date '+%Y-%m-%d %H:%M:%S'; }
gen_secret() {
    # $1 = env var name, $2 = python expression that prints the secret value.
    # printenv reads the named var without eval (call sites pass literal names).
    var="$1"
    [ -n "$(printenv "$var")" ] && return 0
    echo "[$(ts)] Generating $var..."
    val=$(python3 -c "$2" 2>&1) || {
        echo "[$(ts)] ERROR: Failed to generate $var: $val"
        exit 1
    }
    export "$var=$val"
    echo "[$(ts)] $var generated (length: ${#val})"
}

gen_secret JWT_SECRET_KEY "import secrets; print(secrets.token_urlsafe(64))"
gen_secret JWT_REFRESH_SECRET_KEY "import secrets; print(secrets.token_urlsafe(64))"
gen_secret ENCRYPTION_MASTER_KEY "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"

# Command dispatch: this one image serves the API *and* the background workers.
# If compose (or `docker run`) passed a command, run THAT instead of uvicorn —
# the workers still inherit the secret bootstrap above. The API role passes no
# command and falls through to the uvicorn default below.
if [ "$#" -gt 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Executing passed command: $*"
    exec "$@"
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
