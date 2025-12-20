#!/bin/bash
set -euo pipefail

# ============================================
# STAGING ROLLBACK SCRIPT
# ============================================
# Safely rolls back to previous deployment state
# Restores Docker containers, databases, and configurations
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${SCRIPT_DIR}/logs/rollback_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
AUTO_MODE=false
BACKUP_PATH=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --auto)
            AUTO_MODE=true
            shift
            ;;
        --backup)
            BACKUP_PATH="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--auto] [--backup /path/to/backup]"
            exit 1
            ;;
    esac
done

# ============================================
# LOGGING FUNCTIONS
# ============================================

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $1" | tee -a "$LOG_FILE"
}

# ============================================
# VERIFICATION FUNCTIONS
# ============================================

verify_backup_exists() {
    log "Verifying backup exists..."

    # If backup path provided, use it
    if [ -n "$BACKUP_PATH" ]; then
        if [ ! -d "$BACKUP_PATH" ]; then
            log_error "Specified backup path does not exist: $BACKUP_PATH"
            return 1
        fi
        log_success "Using specified backup: $BACKUP_PATH"
        return 0
    fi

    # Otherwise, use last backup
    if [ ! -f "${SCRIPT_DIR}/.last_backup" ]; then
        log_error "No previous backup found"
        log "Available backups:"
        ls -lt "${SCRIPT_DIR}/backups/" 2>/dev/null || echo "  None"
        return 1
    fi

    BACKUP_PATH=$(cat "${SCRIPT_DIR}/.last_backup")

    if [ ! -d "$BACKUP_PATH" ]; then
        log_error "Backup directory does not exist: $BACKUP_PATH"
        return 1
    fi

    log_success "Found backup at: $BACKUP_PATH"

    # Display backup contents
    log "Backup contains:"
    ls -lh "$BACKUP_PATH" | tail -n +2 | awk '{print "  - " $9 " (" $5 ")"}'
}

confirm_rollback() {
    if [ "$AUTO_MODE" = true ]; then
        log "Running in automatic mode, skipping confirmation"
        return 0
    fi

    log_warning "=========================================="
    log_warning "WARNING: ROLLBACK OPERATION"
    log_warning "=========================================="
    log_warning "This will:"
    log_warning "  1. Stop all current staging services"
    log_warning "  2. Restore previous deployment state"
    log_warning "  3. Restore database backups"
    log_warning "  4. Restart services with previous version"
    log_warning ""
    log_warning "Backup source: $BACKUP_PATH"
    log_warning ""

    read -p "Are you sure you want to proceed? (yes/no): " -r
    echo

    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log "Rollback cancelled by user"
        exit 0
    fi

    log_success "Rollback confirmed"
}

# ============================================
# ROLLBACK FUNCTIONS
# ============================================

stop_current_deployment() {
    log "Stopping current deployment..."

    cd "$SCRIPT_DIR"

    # Stop all containers with timeout
    if docker-compose -f docker-compose.staging.yml ps -q 2>/dev/null | grep -q .; then
        docker-compose -f docker-compose.staging.yml stop -t 30
        docker-compose -f docker-compose.staging.yml rm -f
        log_success "Current deployment stopped"
    else
        log "No running containers to stop"
    fi
}

restore_docker_compose() {
    log "Restoring docker-compose configuration..."

    if [ -f "${BACKUP_PATH}/docker-compose.staging.yml" ]; then
        cp "${BACKUP_PATH}/docker-compose.staging.yml" "${SCRIPT_DIR}/"
        log_success "docker-compose.staging.yml restored"
    else
        log_warning "No docker-compose.staging.yml found in backup"
    fi
}

restore_environment() {
    log "Restoring environment configuration..."

    if [ -f "${BACKUP_PATH}/.env.staging" ]; then
        cp "${BACKUP_PATH}/.env.staging" "${SCRIPT_DIR}/"
        log_success ".env.staging restored"
    else
        log_warning "No .env.staging found in backup"
    fi
}

restore_git_version() {
    log "Restoring git version..."

    if [ ! -f "${BACKUP_PATH}/git_commit.txt" ]; then
        log_warning "No git commit information found in backup"
        return 0
    fi

    BACKUP_COMMIT=$(cat "${BACKUP_PATH}/git_commit.txt")

    cd "$PROJECT_ROOT"

    # Check if commit exists
    if ! git cat-file -e "$BACKUP_COMMIT" 2>/dev/null; then
        log_error "Backup commit $BACKUP_COMMIT does not exist in repository"
        return 1
    fi

    # Checkout the commit
    log "Checking out commit: $BACKUP_COMMIT"
    git checkout "$BACKUP_COMMIT"

    log_success "Git version restored to commit: ${BACKUP_COMMIT:0:8}"
}

restore_database() {
    log "Restoring database backups..."

    # Start just the database container for restoration
    cd "$SCRIPT_DIR"

    if [ -f "${BACKUP_PATH}/postgres_backup.sql" ]; then
        log "Starting PostgreSQL for restoration..."

        # Start only postgres
        docker-compose -f docker-compose.staging.yml up -d postgres

        # Wait for postgres to be ready
        log "Waiting for PostgreSQL to be ready..."
        for i in {1..30}; do
            if docker exec staging-postgres pg_isready -U postgres >/dev/null 2>&1; then
                break
            fi
            sleep 2
        done

        # Restore database
        log "Restoring PostgreSQL database..."
        docker exec -i staging-postgres psql -U postgres < "${BACKUP_PATH}/postgres_backup.sql" >/dev/null 2>&1

        log_success "PostgreSQL database restored"
    else
        log_warning "No PostgreSQL backup found"
    fi
}

restore_redis() {
    log "Restoring Redis data..."

    if [ -f "${BACKUP_PATH}/redis_dump.rdb" ]; then
        # Start redis container
        cd "$SCRIPT_DIR"
        docker-compose -f docker-compose.staging.yml up -d redis

        # Wait for Redis to be ready
        log "Waiting for Redis to be ready..."
        for i in {1..30}; do
            if docker exec staging-redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
                break
            fi
            sleep 2
        done

        # Stop Redis to restore dump
        docker-compose -f docker-compose.staging.yml stop redis

        # Copy dump file
        docker cp "${BACKUP_PATH}/redis_dump.rdb" staging-redis:/data/dump.rdb

        # Start Redis again
        docker-compose -f docker-compose.staging.yml up -d redis

        log_success "Redis data restored"
    else
        log_warning "No Redis backup found"
    fi
}

rebuild_images() {
    log "Rebuilding Docker images from restored code..."

    cd "$SCRIPT_DIR"

    if ! docker-compose -f docker-compose.staging.yml build; then
        log_error "Failed to rebuild Docker images"
        return 1
    fi

    log_success "Docker images rebuilt"
}

restart_all_services() {
    log "Restarting all services..."

    cd "$SCRIPT_DIR"

    # Start all services
    if ! docker-compose -f docker-compose.staging.yml up -d; then
        log_error "Failed to start services"
        return 1
    fi

    log_success "All services restarted"
}

wait_for_services() {
    log "Waiting for services to become healthy..."

    local max_attempts=60  # 5 minutes
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        log "Health check attempt $attempt/$max_attempts..."

        if "${SCRIPT_DIR}/healthcheck.sh" >/dev/null 2>&1; then
            log_success "All services are healthy"
            return 0
        fi

        sleep 5
        attempt=$((attempt + 1))
    done

    log_error "Services did not become healthy within timeout"
    return 1
}

# ============================================
# VERIFICATION FUNCTIONS
# ============================================

run_smoke_tests() {
    log "Running smoke tests to verify rollback..."

    local tests_passed=0
    local tests_failed=0

    # Test frontend
    if curl -sf http://localhost:3000 >/dev/null 2>&1; then
        log_success "Frontend is responding"
        tests_passed=$((tests_passed + 1))
    else
        log_error "Frontend is not responding"
        tests_failed=$((tests_failed + 1))
    fi

    # Test backend
    if curl -sf http://localhost:5000/health >/dev/null 2>&1; then
        log_success "Backend API is responding"
        tests_passed=$((tests_passed + 1))
    else
        log_error "Backend API is not responding"
        tests_failed=$((tests_failed + 1))
    fi

    # Test PostgreSQL
    if docker exec staging-postgres pg_isready -U postgres >/dev/null 2>&1; then
        log_success "PostgreSQL is accepting connections"
        tests_passed=$((tests_passed + 1))
    else
        log_error "PostgreSQL is not accepting connections"
        tests_failed=$((tests_failed + 1))
    fi

    # Test Redis
    if docker exec staging-redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        log_success "Redis is responding"
        tests_passed=$((tests_passed + 1))
    else
        log_error "Redis is not responding"
        tests_failed=$((tests_failed + 1))
    fi

    log "Smoke tests: $tests_passed passed, $tests_failed failed"

    if [ $tests_failed -gt 0 ]; then
        return 1
    fi

    return 0
}

verify_rollback_successful() {
    log "Verifying rollback was successful..."

    # Check that we're on the correct commit
    if [ -f "${BACKUP_PATH}/git_commit.txt" ]; then
        EXPECTED_COMMIT=$(cat "${BACKUP_PATH}/git_commit.txt")
        CURRENT_COMMIT=$(git -C "$PROJECT_ROOT" rev-parse HEAD)

        if [ "$CURRENT_COMMIT" = "$EXPECTED_COMMIT" ]; then
            log_success "Git version verified: ${CURRENT_COMMIT:0:8}"
        else
            log_warning "Git version mismatch: expected ${EXPECTED_COMMIT:0:8}, got ${CURRENT_COMMIT:0:8}"
        fi
    fi

    # Check container versions
    if [ -f "${BACKUP_PATH}/container_versions.txt" ]; then
        log "Restored container versions:"
        cat "${BACKUP_PATH}/container_versions.txt"
    fi

    log_success "Rollback verification completed"
}

# ============================================
# NOTIFICATION FUNCTIONS
# ============================================

send_notification() {
    local status=$1
    local message=$2

    log "Sending rollback notification..."

    # Create notification file
    NOTIFICATION_FILE="${SCRIPT_DIR}/notifications/rollback_${TIMESTAMP}.txt"
    mkdir -p "$(dirname "$NOTIFICATION_FILE")"

    cat > "$NOTIFICATION_FILE" <<EOF
=====================================
STAGING ROLLBACK NOTIFICATION
=====================================
Timestamp: $(date)
Status: $status
Backup Source: $BACKUP_PATH
Message: $message

CURRENT STATE:
$(docker-compose -f "${SCRIPT_DIR}/docker-compose.staging.yml" ps 2>/dev/null || echo "No containers running")

ROLLBACK LOG:
See: $LOG_FILE

=====================================
EOF

    log_success "Notification saved to: $NOTIFICATION_FILE"

    # In a real environment, you would send this via email, Slack, etc.
    # For now, just display it
    cat "$NOTIFICATION_FILE"
}

# ============================================
# MAIN ROLLBACK FLOW
# ============================================

main() {
    mkdir -p "${SCRIPT_DIR}/logs"
    mkdir -p "${SCRIPT_DIR}/notifications"

    log "=========================================="
    log "STARTING STAGING ROLLBACK"
    log "=========================================="
    log "Timestamp: $(date)"
    log "Auto Mode: $AUTO_MODE"
    log ""

    # Verify backup exists
    if ! verify_backup_exists; then
        log_error "Rollback failed: No valid backup found"
        exit 1
    fi

    # Confirm rollback
    confirm_rollback

    log ""
    log "Phase 1: Stopping Current Deployment"
    log "=========================================="

    if ! stop_current_deployment; then
        log_error "Failed to stop current deployment"
        exit 1
    fi

    log ""
    log "Phase 2: Restoring Configuration"
    log "=========================================="

    restore_docker_compose
    restore_environment

    log ""
    log "Phase 3: Restoring Git Version"
    log "=========================================="

    if ! restore_git_version; then
        log_error "Failed to restore git version"
        exit 1
    fi

    log ""
    log "Phase 4: Rebuilding Images"
    log "=========================================="

    if ! rebuild_images; then
        log_error "Failed to rebuild images"
        exit 1
    fi

    log ""
    log "Phase 5: Restoring Databases"
    log "=========================================="

    restore_database
    restore_redis

    log ""
    log "Phase 6: Restarting Services"
    log "=========================================="

    if ! restart_all_services; then
        log_error "Failed to restart services"
        send_notification "FAILED" "Services failed to restart after rollback"
        exit 1
    fi

    log ""
    log "Phase 7: Health Checks"
    log "=========================================="

    if ! wait_for_services; then
        log_error "Services did not become healthy"
        send_notification "PARTIAL" "Services started but did not become healthy"
        exit 1
    fi

    log ""
    log "Phase 8: Smoke Tests"
    log "=========================================="

    if ! run_smoke_tests; then
        log_warning "Some smoke tests failed"
        send_notification "PARTIAL" "Rollback completed but some tests failed"
    else
        log_success "All smoke tests passed"
    fi

    log ""
    log "Phase 9: Verification"
    log "=========================================="

    verify_rollback_successful

    log ""
    log_success "=========================================="
    log_success "ROLLBACK COMPLETED SUCCESSFULLY"
    log_success "=========================================="
    log_success "Restored from: $BACKUP_PATH"
    log_success "Log File: $LOG_FILE"
    log ""

    send_notification "SUCCESS" "Rollback completed successfully"
}

# Run main rollback
main "$@"
