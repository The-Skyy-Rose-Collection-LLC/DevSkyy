#!/bin/bash

################################################################################
# DevSkyy Phase 2 - Staging Deployment Script
# Version: 2.0.0
# Last Updated: 2025-12-19
################################################################################

set -euo pipefail  # Exit on error, undefined variables, pipe failures

# Color output for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="docker-compose.staging.yml"
ENV_FILE=".env"
BACKUP_DIR="${PROJECT_DIR}/data/backups"
LOG_FILE="${PROJECT_DIR}/logs/deployment-$(date +%Y%m%d-%H%M%S).log"

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

################################################################################
# Logging Functions
################################################################################

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $*" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $*" | tee -a "$LOG_FILE"
}

################################################################################
# Pre-flight Checks
################################################################################

preflight_checks() {
    log "Running pre-flight checks..."

    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        log_error "Please do not run this script as root"
        exit 1
    fi

    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    # Check if docker-compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    # Check if .env file exists
    if [ ! -f "${PROJECT_DIR}/${ENV_FILE}" ]; then
        log_error ".env file not found at ${PROJECT_DIR}/${ENV_FILE}"
        log "Please copy .env.staging to .env and configure it"
        exit 1
    fi

    # Check if docker-compose file exists
    if [ ! -f "${PROJECT_DIR}/${COMPOSE_FILE}" ]; then
        log_error "Docker Compose file not found at ${PROJECT_DIR}/${COMPOSE_FILE}"
        exit 1
    fi

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi

    # Check available disk space (minimum 10GB)
    available_space=$(df "${PROJECT_DIR}" | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 10485760 ]; then
        log_error "Insufficient disk space. At least 10GB required"
        exit 1
    fi

    # Check if critical environment variables are set
    source "${PROJECT_DIR}/${ENV_FILE}"

    if [ -z "${DATABASE_URL:-}" ]; then
        log_error "DATABASE_URL not set in .env"
        exit 1
    fi

    if [ -z "${REDIS_URL:-}" ]; then
        log_error "REDIS_URL not set in .env"
        exit 1
    fi

    # Check for default passwords
    if grep -q "CHANGE_THIS_PASSWORD" "${PROJECT_DIR}/${ENV_FILE}"; then
        log_error "Default passwords found in .env file. Please update all passwords."
        exit 1
    fi

    log_success "Pre-flight checks passed"
}

################################################################################
# Backup Current Deployment
################################################################################

backup_current_deployment() {
    log "Creating backup of current deployment..."

    mkdir -p "$BACKUP_DIR"
    BACKUP_TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    BACKUP_FILE="${BACKUP_DIR}/staging-backup-${BACKUP_TIMESTAMP}.tar.gz"

    # Check if containers are running
    if docker-compose -f "${PROJECT_DIR}/${COMPOSE_FILE}" ps | grep -q "Up"; then
        log "Backing up database..."

        # Backup PostgreSQL database
        docker-compose -f "${PROJECT_DIR}/${COMPOSE_FILE}" exec -T postgres \
            pg_dump -U "${POSTGRES_USER:-staging_user}" "${POSTGRES_DB:-devskyy_staging}" \
            > "${BACKUP_DIR}/database-${BACKUP_TIMESTAMP}.sql" 2>> "$LOG_FILE" || true

        # Backup Redis data
        docker-compose -f "${PROJECT_DIR}/${COMPOSE_FILE}" exec -T redis \
            redis-cli SAVE >> "$LOG_FILE" 2>&1 || true
    else
        log_warning "No running containers found. Skipping database backup."
    fi

    # Backup volumes and configuration
    log "Backing up volumes and configuration..."
    cd "$PROJECT_DIR"
    tar -czf "$BACKUP_FILE" \
        --exclude='node_modules' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.git' \
        --exclude='data/backups' \
        data/ logs/ config/ uploads/ 2>> "$LOG_FILE" || true

    if [ -f "$BACKUP_FILE" ]; then
        log_success "Backup created: $BACKUP_FILE"
    else
        log_warning "Backup creation skipped or failed"
    fi
}

################################################################################
# Pull Latest Code
################################################################################

pull_latest_code() {
    log "Pulling latest code from repository..."

    cd "$PROJECT_DIR"

    # Store current commit for rollback
    PREVIOUS_COMMIT=$(git rev-parse HEAD)
    echo "$PREVIOUS_COMMIT" > "${BACKUP_DIR}/previous-commit.txt"

    # Fetch latest changes
    git fetch origin >> "$LOG_FILE" 2>&1

    # Pull latest changes (use main branch by default)
    git pull origin main >> "$LOG_FILE" 2>&1

    CURRENT_COMMIT=$(git rev-parse HEAD)

    if [ "$PREVIOUS_COMMIT" != "$CURRENT_COMMIT" ]; then
        log_success "Code updated from $PREVIOUS_COMMIT to $CURRENT_COMMIT"
    else
        log "Already up to date"
    fi
}

################################################################################
# Build Docker Images
################################################################################

build_images() {
    log "Building Docker images..."

    cd "$PROJECT_DIR"

    # Build images with no cache to ensure latest dependencies
    docker-compose -f "$COMPOSE_FILE" build --no-cache >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        log_success "Docker images built successfully"
    else
        log_error "Failed to build Docker images"
        exit 1
    fi
}

################################################################################
# Start Services
################################################################################

start_services() {
    log "Starting services in dependency order..."

    cd "$PROJECT_DIR"

    # Stop any running services first
    log "Stopping existing services..."
    docker-compose -f "$COMPOSE_FILE" down >> "$LOG_FILE" 2>&1

    # Start database first
    log "Starting PostgreSQL..."
    docker-compose -f "$COMPOSE_FILE" up -d postgres

    # Wait for PostgreSQL to be healthy
    log "Waiting for PostgreSQL to be healthy..."
    for i in {1..30}; do
        if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U "${POSTGRES_USER:-staging_user}" &> /dev/null; then
            log_success "PostgreSQL is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "PostgreSQL failed to start within 30 seconds"
            exit 1
        fi
        sleep 1
    done

    # Start Redis
    log "Starting Redis..."
    docker-compose -f "$COMPOSE_FILE" up -d redis

    # Wait for Redis to be healthy
    log "Waiting for Redis to be healthy..."
    for i in {1..10}; do
        if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping &> /dev/null; then
            log_success "Redis is ready"
            break
        fi
        if [ $i -eq 10 ]; then
            log_error "Redis failed to start within 10 seconds"
            exit 1
        fi
        sleep 1
    done

    # Start application
    log "Starting application..."
    docker-compose -f "$COMPOSE_FILE" up -d devskyy-app

    # Wait for application to be healthy
    log "Waiting for application to be healthy..."
    for i in {1..60}; do
        if curl -sf http://localhost:8000/health &> /dev/null; then
            log_success "Application is ready"
            break
        fi
        if [ $i -eq 60 ]; then
            log_error "Application failed to start within 60 seconds"
            log "Check logs with: docker-compose -f $COMPOSE_FILE logs devskyy-app"
            exit 1
        fi
        sleep 1
    done

    # Start Nginx
    log "Starting Nginx..."
    docker-compose -f "$COMPOSE_FILE" up -d nginx

    # Start monitoring stack
    log "Starting monitoring stack..."
    docker-compose -f "$COMPOSE_FILE" up -d prometheus grafana alertmanager loki promtail

    # Start exporters
    log "Starting exporters..."
    docker-compose -f "$COMPOSE_FILE" up -d postgres-exporter redis-exporter node-exporter

    log_success "All services started successfully"
}

################################################################################
# Run Smoke Tests
################################################################################

run_smoke_tests() {
    log "Running smoke tests..."

    # Test application health
    log "Testing application health endpoint..."
    if curl -sf http://localhost:8000/health | grep -q "healthy"; then
        log_success "Application health check passed"
    else
        log_error "Application health check failed"
        return 1
    fi

    # Test database connectivity
    log "Testing database connectivity..."
    if docker-compose -f "${PROJECT_DIR}/${COMPOSE_FILE}" exec -T postgres \
        psql -U "${POSTGRES_USER:-staging_user}" -d "${POSTGRES_DB:-devskyy_staging}" -c "SELECT 1" &> /dev/null; then
        log_success "Database connectivity check passed"
    else
        log_error "Database connectivity check failed"
        return 1
    fi

    # Test Redis connectivity
    log "Testing Redis connectivity..."
    if docker-compose -f "${PROJECT_DIR}/${COMPOSE_FILE}" exec -T redis redis-cli ping | grep -q "PONG"; then
        log_success "Redis connectivity check passed"
    else
        log_error "Redis connectivity check failed"
        return 1
    fi

    # Test Prometheus
    log "Testing Prometheus..."
    if curl -sf http://localhost:9090/-/healthy &> /dev/null; then
        log_success "Prometheus health check passed"
    else
        log_warning "Prometheus health check failed (non-critical)"
    fi

    # Test Grafana
    log "Testing Grafana..."
    if curl -sf http://localhost:3000/api/health &> /dev/null; then
        log_success "Grafana health check passed"
    else
        log_warning "Grafana health check failed (non-critical)"
    fi

    log_success "Smoke tests completed"
    return 0
}

################################################################################
# Report Status
################################################################################

report_status() {
    log "Deployment Status Report"
    log "========================="

    # Get container status
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" ps

    # Get resource usage
    log ""
    log "Resource Usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
        $(docker-compose -f "$COMPOSE_FILE" ps -q)

    # Print access URLs
    log ""
    log "Access URLs:"
    log "  Application:   http://localhost:8000"
    log "  API Docs:      http://localhost:8000/docs"
    log "  Prometheus:    http://localhost:9090"
    log "  Grafana:       http://localhost:3000"
    log "  AlertManager:  http://localhost:9093"

    log ""
    log_success "Deployment completed successfully!"
    log "Deployment log saved to: $LOG_FILE"
}

################################################################################
# Rollback Function
################################################################################

rollback() {
    log_error "Deployment failed. Initiating rollback..."

    cd "$PROJECT_DIR"

    # Stop current deployment
    docker-compose -f "$COMPOSE_FILE" down

    # Restore previous commit if available
    if [ -f "${BACKUP_DIR}/previous-commit.txt" ]; then
        PREVIOUS_COMMIT=$(cat "${BACKUP_DIR}/previous-commit.txt")
        log "Rolling back to commit: $PREVIOUS_COMMIT"
        git checkout "$PREVIOUS_COMMIT"
    fi

    # Find latest backup
    LATEST_BACKUP=$(ls -t "${BACKUP_DIR}"/staging-backup-*.tar.gz 2>/dev/null | head -1)

    if [ -n "$LATEST_BACKUP" ]; then
        log "Restoring from backup: $LATEST_BACKUP"
        cd "$PROJECT_DIR"
        tar -xzf "$LATEST_BACKUP"
    fi

    # Restart services
    log "Restarting services with previous version..."
    docker-compose -f "$COMPOSE_FILE" up -d

    log_error "Rollback completed. Please investigate the deployment failure."
    exit 1
}

################################################################################
# Main Deployment Flow
################################################################################

main() {
    log "=========================================="
    log "DevSkyy Phase 2 - Staging Deployment"
    log "=========================================="
    log "Started at: $(date)"
    log ""

    # Set trap for errors
    trap rollback ERR

    # Run deployment steps
    preflight_checks
    backup_current_deployment
    pull_latest_code
    build_images
    start_services

    # Run smoke tests (don't exit on failure, just warn)
    if ! run_smoke_tests; then
        log_warning "Some smoke tests failed. Please investigate."
    fi

    report_status

    log ""
    log "Completed at: $(date)"
    log "=========================================="
}

# Run main function
main "$@"
