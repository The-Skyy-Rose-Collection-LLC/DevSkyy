#!/bin/bash
#
# Enterprise Run Script - Zero Failure Tolerance
# Only successful runs allowed, automatic recovery on failure
#

set -euo pipefail  # Exit on error, undefined variables, pipe failures
IFS=$'\n\t'       # Set Internal Field Separator for safety

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOG_FILE="enterprise_run.log"
PID_FILE="/tmp/devSkyy.pid"
HEALTH_CHECK_URL="http://localhost:8000/health"
MAX_RETRIES=3
RETRY_DELAY=5

# Functions
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

cleanup() {
    log "Cleaning up..."
    if [ -f "$PID_FILE" ]; then
        kill $(cat "$PID_FILE") 2>/dev/null || true
        rm -f "$PID_FILE"
    fi
}

trap cleanup EXIT

# Pre-flight checks
preflight_checks() {
    log "🔍 Running preflight checks..."

    # Check Python version
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
        error "Python 3.9+ required"
        exit 1
    fi

    # Check environment file
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            warning ".env not found, copying from .env.example"
            cp .env.example .env
        else
            error ".env file not found"
            exit 1
        fi
    fi

    # Check required environment variables
    if [ -f ".env" ]; then
        source .env
        if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
            warning "ANTHROPIC_API_KEY not set"
        fi
        if [ -z "${MONGODB_URI:-}" ]; then
            error "MONGODB_URI not set"
            exit 1
        fi
    fi

    # Check dependencies
    log "Installing/updating dependencies..."
    pip install -r requirements.txt --quiet --upgrade

    # Security scan
    log "Running security scan..."
    pip-audit --fix 2>/dev/null || warning "Security vulnerabilities detected"

    log "✅ Preflight checks completed"
}

# Start services with health monitoring
start_services() {
    log "🚀 Starting enterprise services..."

    # Kill any existing instances
    pkill -f "uvicorn main:app" 2>/dev/null || true
    sleep 2

    # Start FastAPI with enterprise configuration
    export ENVIRONMENT=production
    export HIDE_DOCS=false
    export RATE_LIMIT_ENABLED=true

    nohup uvicorn main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 4 \
        --loop uvloop \
        --access-log \
        --log-level info \
        > uvicorn.log 2>&1 &

    echo $! > "$PID_FILE"
    log "Service started with PID: $(cat $PID_FILE)"

    # Wait for service to be ready
    log "Waiting for service to be ready..."
    for i in {1..30}; do
        if curl -s "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
            log "✅ Service is healthy"
            return 0
        fi
        sleep 1
    done

    error "Service failed to start"
    return 1
}

# Health monitoring loop
monitor_health() {
    log "📊 Starting health monitoring..."

    while true; do
        if ! curl -s "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
            warning "Health check failed, attempting recovery..."

            for retry in $(seq 1 $MAX_RETRIES); do
                log "Recovery attempt $retry/$MAX_RETRIES"

                # Try to restart service
                if start_services; then
                    log "✅ Service recovered"
                    break
                fi

                if [ $retry -eq $MAX_RETRIES ]; then
                    error "Failed to recover after $MAX_RETRIES attempts"
                    exit 1
                fi

                sleep $RETRY_DELAY
            done
        fi

        sleep 10  # Check every 10 seconds
    done
}

# Main execution
main() {
    echo "════════════════════════════════════════════════════════════"
    echo "       DevSkyy Enterprise - Zero Failure Tolerance"
    echo "════════════════════════════════════════════════════════════"
    echo

    # Run preflight checks
    preflight_checks

    # Start services
    if ! start_services; then
        error "Failed to start services"
        exit 1
    fi

    # Start frontend if exists
    if [ -d "frontend" ]; then
        log "Starting frontend..."
        cd frontend
        npm install --silent
        npm run build
        npm run preview &
        cd ..
        log "✅ Frontend started"
    fi

    echo
    echo "════════════════════════════════════════════════════════════"
    echo "       ✅ ENTERPRISE SYSTEM RUNNING SUCCESSFULLY"
    echo "════════════════════════════════════════════════════════════"
    echo
    echo "  API:       http://localhost:8000"
    echo "  Docs:      http://localhost:8000/docs"
    echo "  Frontend:  http://localhost:3000"
    echo "  Health:    http://localhost:8000/health"
    echo
    echo "  Press Ctrl+C to stop"
    echo "════════════════════════════════════════════════════════════"
    echo

    # Start health monitoring
    monitor_health
}

# Run main function
main "$@"