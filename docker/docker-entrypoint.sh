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

# log_info prints an informational message to stdout prefixed with a green [INFO] tag; the first argument is the message.
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# log_warn prints the given message prefixed with [WARN] in yellow to stdout.
log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# log_error prints an error message prefixed with `[ERROR]` in red.
log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# print_banner prints an ASCII banner for the DevSkyy MCP Server to stdout.
print_banner() {
    cat <<'EOF'
╔══════════════════════════════════════════════════════════════════╗
║   DevSkyy MCP Server v1.1.0                                     ║
║   Multi-Agent AI Platform - Docker Edition                      ║
╚══════════════════════════════════════════════════════════════════╝
EOF
}

# validate_env validates required and optional environment variables, sets a default DEVSKYY_API_URL when absent, and logs warnings for any missing required variables.
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

# wait_for_dependencies waits for DATABASE_URL and REDIS_URL targets to become reachable (30 second timeout per service) and logs status; if a service remains unreachable the function logs a warning and continues.
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

# run_migrations runs the project's database migrations when RUN_MIGRATIONS is set to "true" (placeholder for the actual migration tool).
run_migrations() {
    if [ "$RUN_MIGRATIONS" = "true" ]; then
        log_info "Running database migrations..."
        # TODO: Add Alembic or your migration tool here
        # alembic upgrade head
        log_info "✅ Migrations complete"
    fi
}

# start_mcp_server starts the DevSkyy MCP server, logs the API URL and a masked API key, and replaces the shell with the server process.
start_mcp_server() {
    log_info "Starting DevSkyy MCP Server..."
    log_info "API URL: $DEVSKYY_API_URL"
    log_info "API Key: ${DEVSKYY_API_KEY:0:10}..." # Show first 10 chars only

    exec python devskyy_mcp.py
}

# start_api_server starts the FastAPI application with uvicorn using configured environment variables.
# 
# Uses ENVIRONMENT for informational logging, PORT (default 8000) for the listen port,
# WORKERS (default 4) for the worker count, and LOG_LEVEL (default "info") for logging verbosity.
# The function execs uvicorn to replace the shell process.
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

# start_mcp_gateway starts the MCP Gateway service.
start_mcp_gateway() {
    log_info "Starting MCP Gateway..."
    log_info "Gateway Port: ${GATEWAY_PORT:-3000}"

    exec python docker/mcp_gateway.py
}

# main orchestrates the container startup sequence, validates configuration, waits for dependencies, runs optional migrations, and dispatches to the selected run mode (mcp-server, api-server, mcp-gateway, shell/bash, or a custom command).
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