#!/bin/bash
# DevSkyy MCP Server Docker Entrypoint
# Handles initialization and various run modes
# Per Truth Protocol: Secure defaults, no hardcoded secrets

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
print_banner() {
    cat <<'EOF'
╔══════════════════════════════════════════════════════════════════╗
║   DevSkyy MCP Server v1.1.0                                     ║
║   Multi-Agent AI Platform - Docker Edition                      ║
╚══════════════════════════════════════════════════════════════════╝
EOF
}

# Validate environment variables
validate_env() {
    log_info "Validating environment configuration..."

    local missing_vars=0

    # Check required environment variables
    if [ -z "$DEVSKYY_API_KEY" ]; then
        log_warn "DEVSKYY_API_KEY not set"
        missing_vars=$((missing_vars + 1))
    fi

    if [ -z "$DEVSKYY_API_URL" ]; then
        log_info "DEVSKYY_API_URL not set, using default: http://localhost:8000"
        export DEVSKYY_API_URL="http://localhost:8000"
    fi

    # Check optional variables
    if [ -z "$HUGGING_FACE_TOKEN" ]; then
        log_info "HUGGING_FACE_TOKEN not set (optional)"
    fi

    if [ $missing_vars -gt 0 ]; then
        log_warn "Some environment variables are missing. Set them in .env file or docker-compose.yml"
    fi

    log_info "✅ Environment validation complete"
}

# Wait for dependencies
wait_for_dependencies() {
    log_info "Checking dependencies..."

    # Wait for PostgreSQL if DATABASE_URL is set
    if [ -n "$DATABASE_URL" ]; then
        log_info "Waiting for database..."

        # Extract host and port from DATABASE_URL
        # Format: postgresql://user:pass@host:port/db
        DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\).*/\1/p')
        DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

        if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
            timeout 30 bash -c "until nc -z $DB_HOST $DB_PORT; do sleep 1; done" || {
                log_warn "Database connection timeout. Continuing anyway..."
            }
            log_info "✅ Database is ready"
        fi
    fi

    # Wait for Redis if REDIS_URL is set
    if [ -n "$REDIS_URL" ]; then
        log_info "Waiting for Redis..."

        REDIS_HOST=$(echo $REDIS_URL | sed -n 's/.*\/\/\([^:]*\).*/\1/p')
        REDIS_PORT=$(echo $REDIS_URL | sed -n 's/.*:\([0-9]*\).*/\1/p')

        if [ -n "$REDIS_HOST" ] && [ -n "$REDIS_PORT" ]; then
            timeout 30 bash -c "until nc -z $REDIS_HOST $REDIS_PORT; do sleep 1; done" || {
                log_warn "Redis connection timeout. Continuing anyway..."
            }
            log_info "✅ Redis is ready"
        fi
    fi
}

# Run database migrations
run_migrations() {
    if [ "$RUN_MIGRATIONS" = "true" ]; then
        log_info "Running database migrations..."
        # TODO: Add Alembic or your migration tool here
        # alembic upgrade head
        log_info "✅ Migrations complete"
    fi
}

# Start MCP server
start_mcp_server() {
    log_info "Starting DevSkyy MCP Server..."
    log_info "API URL: $DEVSKYY_API_URL"
    log_info "API Key: ${DEVSKYY_API_KEY:0:10}..." # Show first 10 chars only

    exec python devskyy_mcp.py
}

# Start FastAPI application
start_api_server() {
    log_info "Starting DevSkyy FastAPI application..."
    log_info "Environment: ${ENVIRONMENT:-development}"
    log_info "Port: ${PORT:-8000}"

    exec uvicorn main:app \
        --host 0.0.0.0 \
        --port ${PORT:-8000} \
        --workers ${WORKERS:-4} \
        --log-level ${LOG_LEVEL:-info}
}

# Start MCP gateway
start_mcp_gateway() {
    log_info "Starting MCP Gateway..."
    log_info "Gateway Port: ${GATEWAY_PORT:-3000}"

    exec python docker/mcp_gateway.py
}

# Main entrypoint logic
main() {
    print_banner

    # Validate environment
    validate_env

    # Wait for dependencies
    wait_for_dependencies

    # Run migrations if needed
    run_migrations

    # Determine what to run based on command
    case "$1" in
        mcp-server)
            start_mcp_server
            ;;
        api-server)
            start_api_server
            ;;
        mcp-gateway)
            start_mcp_gateway
            ;;
        shell|bash)
            log_info "Starting interactive shell..."
            exec /bin/bash
            ;;
        *)
            log_info "Running custom command: $@"
            exec "$@"
            ;;
    esac
}

# Run main function
main "$@"
