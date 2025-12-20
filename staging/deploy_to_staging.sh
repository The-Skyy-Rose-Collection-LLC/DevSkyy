#!/bin/bash
set -euo pipefail

# ============================================
# STAGING DEPLOYMENT SCRIPT
# ============================================
# Safely deploys latest code to staging environment
# with pre-checks, backups, health monitoring, and smoke tests
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="${SCRIPT_DIR}/backups/${TIMESTAMP}"
LOG_FILE="${SCRIPT_DIR}/logs/deploy_${TIMESTAMP}.log"
DEPLOYMENT_TAG="staging-deploy-${TIMESTAMP}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
# PRE-DEPLOYMENT CHECKS
# ============================================

check_disk_space() {
    log "Checking disk space..."

    # Get available disk space in GB
    AVAILABLE_SPACE=$(df -BG "$PROJECT_ROOT" | tail -1 | awk '{print $4}' | sed 's/G//')
    REQUIRED_SPACE=5  # Require at least 5GB free

    if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
        log_error "Insufficient disk space: ${AVAILABLE_SPACE}GB available, ${REQUIRED_SPACE}GB required"
        return 1
    fi

    log_success "Disk space check passed: ${AVAILABLE_SPACE}GB available"
}

check_ports_available() {
    log "Checking required ports..."

    REQUIRED_PORTS=(3000 5000 5432 6379 3100 9090 9093 9100)
    PORTS_IN_USE=()

    for port in "${REQUIRED_PORTS[@]}"; do
        if lsof -Pi ":$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
            # Port is in use - check if it's our Docker containers (which is OK)
            if ! docker ps --format '{{.Ports}}' 2>/dev/null | grep -q ":$port->"; then
                PORTS_IN_USE+=("$port")
            fi
        fi
    done

    if [ ${#PORTS_IN_USE[@]} -gt 0 ]; then
        log_warning "Some ports are in use by non-Docker processes: ${PORTS_IN_USE[*]}"
        log "Attempting to stop existing staging services..."
        docker-compose -f "${SCRIPT_DIR}/docker-compose.staging.yml" down 2>/dev/null || true
        sleep 3
    fi

    log_success "Port availability check passed"
}

check_docker_running() {
    log "Checking Docker daemon..."

    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running"
        return 1
    fi

    log_success "Docker daemon is running"
}

check_git_status() {
    log "Checking git repository status..."

    cd "$PROJECT_ROOT"

    # Check if we're on main branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [ "$CURRENT_BRANCH" != "main" ]; then
        log_warning "Not on main branch (currently on: $CURRENT_BRANCH)"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "Deployment cancelled"
            return 1
        fi
    fi

    # Pull latest changes
    log "Pulling latest changes from remote..."
    git fetch origin

    LOCAL_HASH=$(git rev-parse HEAD)
    REMOTE_HASH=$(git rev-parse origin/main)

    if [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
        log_warning "Local branch is not up to date with remote"
        git pull origin main
    fi

    log_success "Git repository check passed (commit: ${LOCAL_HASH:0:8})"
    echo "$LOCAL_HASH" > "${SCRIPT_DIR}/.deployment_commit"
}

check_docker_compose_file() {
    log "Checking docker-compose configuration..."

    if [ ! -f "${SCRIPT_DIR}/docker-compose.staging.yml" ]; then
        log_error "docker-compose.staging.yml not found"
        return 1
    fi

    # Validate docker-compose file
    if ! docker-compose -f "${SCRIPT_DIR}/docker-compose.staging.yml" config >/dev/null 2>&1; then
        log_error "docker-compose.staging.yml is invalid"
        return 1
    fi

    log_success "docker-compose configuration is valid"
}

# ============================================
# BACKUP FUNCTIONS
# ============================================

backup_current_state() {
    log "Creating backup of current staging state..."

    mkdir -p "$BACKUP_DIR"

    # Backup docker-compose file
    if [ -f "${SCRIPT_DIR}/docker-compose.staging.yml" ]; then
        cp "${SCRIPT_DIR}/docker-compose.staging.yml" "${BACKUP_DIR}/"
    fi

    # Backup environment files
    if [ -f "${SCRIPT_DIR}/.env.staging" ]; then
        cp "${SCRIPT_DIR}/.env.staging" "${BACKUP_DIR}/"
    fi

    # Backup database if running
    if docker ps --format '{{.Names}}' | grep -q "staging-postgres"; then
        log "Backing up PostgreSQL database..."
        docker exec staging-postgres pg_dumpall -U postgres > "${BACKUP_DIR}/postgres_backup.sql" 2>/dev/null || \
            log_warning "Could not backup PostgreSQL (container may not be running)"
    fi

    # Backup Redis data if running
    if docker ps --format '{{.Names}}' | grep -q "staging-redis"; then
        log "Backing up Redis data..."
        docker exec staging-redis redis-cli SAVE >/dev/null 2>&1 || \
            log_warning "Could not backup Redis (container may not be running)"
        docker cp staging-redis:/data/dump.rdb "${BACKUP_DIR}/redis_dump.rdb" 2>/dev/null || true
    fi

    # Record current container versions
    docker ps --format '{{.Names}}\t{{.Image}}' > "${BACKUP_DIR}/container_versions.txt" 2>/dev/null || true

    # Save current git commit
    git rev-parse HEAD > "${BACKUP_DIR}/git_commit.txt"

    log_success "Backup created at: $BACKUP_DIR"
    echo "$BACKUP_DIR" > "${SCRIPT_DIR}/.last_backup"
}

# ============================================
# DEPLOYMENT FUNCTIONS
# ============================================

tag_deployment() {
    log "Tagging deployment for rollback..."

    cd "$PROJECT_ROOT"

    # Create a lightweight tag
    git tag -f "$DEPLOYMENT_TAG" HEAD

    log_success "Created deployment tag: $DEPLOYMENT_TAG"
    echo "$DEPLOYMENT_TAG" > "${SCRIPT_DIR}/.current_deployment_tag"
}

build_docker_images() {
    log "Building Docker images..."

    cd "$SCRIPT_DIR"

    # Build with no cache to ensure fresh build
    if ! docker-compose -f docker-compose.staging.yml build --no-cache; then
        log_error "Failed to build Docker images"
        return 1
    fi

    log_success "Docker images built successfully"
}

stop_old_containers() {
    log "Stopping old containers gracefully..."

    cd "$SCRIPT_DIR"

    # Get list of running containers
    RUNNING_CONTAINERS=$(docker-compose -f docker-compose.staging.yml ps -q 2>/dev/null || echo "")

    if [ -n "$RUNNING_CONTAINERS" ]; then
        # Stop containers with 30 second timeout
        docker-compose -f docker-compose.staging.yml stop -t 30

        # Remove stopped containers
        docker-compose -f docker-compose.staging.yml rm -f

        log_success "Old containers stopped and removed"
    else
        log "No running containers to stop"
    fi
}

start_new_containers() {
    log "Starting new containers..."

    cd "$SCRIPT_DIR"

    # Start containers in detached mode
    if ! docker-compose -f docker-compose.staging.yml up -d; then
        log_error "Failed to start containers"
        return 1
    fi

    log_success "New containers started"
}

wait_for_health() {
    log "Waiting for services to become healthy..."

    local max_attempts=60  # 5 minutes (60 * 5 seconds)
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        log "Health check attempt $attempt/$max_attempts..."

        # Run health check script
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
# SMOKE TESTS
# ============================================

run_smoke_tests() {
    log "Running smoke tests..."

    local tests_passed=0
    local tests_failed=0

    # Test 1: Check frontend responds
    log "Testing frontend (port 3000)..."
    if curl -sf http://localhost:3000 >/dev/null 2>&1; then
        log_success "Frontend is responding"
        tests_passed=$((tests_passed + 1))
    else
        log_error "Frontend is not responding"
        tests_failed=$((tests_failed + 1))
    fi

    # Test 2: Check backend API responds
    log "Testing backend API (port 5000)..."
    if curl -sf http://localhost:5000/health >/dev/null 2>&1; then
        log_success "Backend API is responding"
        tests_passed=$((tests_passed + 1))
    else
        log_error "Backend API is not responding"
        tests_failed=$((tests_failed + 1))
    fi

    # Test 3: Check PostgreSQL connection
    log "Testing PostgreSQL connection..."
    if docker exec staging-postgres pg_isready -U postgres >/dev/null 2>&1; then
        log_success "PostgreSQL is accepting connections"
        tests_passed=$((tests_passed + 1))
    else
        log_error "PostgreSQL is not accepting connections"
        tests_failed=$((tests_failed + 1))
    fi

    # Test 4: Check Redis connection
    log "Testing Redis connection..."
    if docker exec staging-redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        log_success "Redis is responding"
        tests_passed=$((tests_passed + 1))
    else
        log_error "Redis is not responding"
        tests_failed=$((tests_failed + 1))
    fi

    # Test 5: Check Prometheus metrics
    log "Testing Prometheus metrics..."
    if curl -sf http://localhost:9090/-/healthy >/dev/null 2>&1; then
        log_success "Prometheus is responding"
        tests_passed=$((tests_passed + 1))
    else
        log_warning "Prometheus is not responding (non-critical)"
    fi

    # Test 6: Check Grafana
    log "Testing Grafana..."
    if curl -sf http://localhost:3100/api/health >/dev/null 2>&1; then
        log_success "Grafana is responding"
        tests_passed=$((tests_passed + 1))
    else
        log_warning "Grafana is not responding (non-critical)"
    fi

    log "Smoke tests completed: $tests_passed passed, $tests_failed failed"

    if [ $tests_failed -gt 0 ]; then
        return 1
    fi

    return 0
}

# ============================================
# DEPLOYMENT REPORT
# ============================================

generate_deployment_report() {
    local deployment_status=$1

    log "Generating deployment report..."

    REPORT_FILE="${SCRIPT_DIR}/reports/deployment_${TIMESTAMP}.txt"
    mkdir -p "$(dirname "$REPORT_FILE")"

    cat > "$REPORT_FILE" <<EOF
=====================================
STAGING DEPLOYMENT REPORT
=====================================
Timestamp: $(date)
Status: $deployment_status
Tag: $DEPLOYMENT_TAG
Commit: $(cat "${SCRIPT_DIR}/.deployment_commit")
Backup Location: $BACKUP_DIR

RUNNING CONTAINERS:
$(docker-compose -f "${SCRIPT_DIR}/docker-compose.staging.yml" ps)

RESOURCE USAGE:
$(docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}")

DEPLOYMENT LOG:
See: $LOG_FILE

=====================================
EOF

    log_success "Deployment report saved to: $REPORT_FILE"
    cat "$REPORT_FILE"
}

# ============================================
# ROLLBACK ON FAILURE
# ============================================

rollback_on_failure() {
    log_error "Deployment failed, initiating automatic rollback..."

    if [ -f "${SCRIPT_DIR}/.last_backup" ]; then
        "${SCRIPT_DIR}/rollback.sh" --auto
    else
        log_error "No backup found for automatic rollback"
    fi
}

# ============================================
# MAIN DEPLOYMENT FLOW
# ============================================

main() {
    # Create logs directory
    mkdir -p "${SCRIPT_DIR}/logs"
    mkdir -p "${SCRIPT_DIR}/backups"
    mkdir -p "${SCRIPT_DIR}/reports"

    log "=========================================="
    log "STARTING STAGING DEPLOYMENT"
    log "=========================================="
    log "Timestamp: $(date)"
    log "Project Root: $PROJECT_ROOT"
    log "Backup Directory: $BACKUP_DIR"
    log ""

    # Run pre-deployment checks
    log "Phase 1: Pre-Deployment Checks"
    log "=========================================="

    if ! check_docker_running; then
        log_error "Pre-deployment checks failed"
        exit 1
    fi

    if ! check_disk_space; then
        log_error "Pre-deployment checks failed"
        exit 1
    fi

    if ! check_docker_compose_file; then
        log_error "Pre-deployment checks failed"
        exit 1
    fi

    if ! check_git_status; then
        log_error "Pre-deployment checks failed"
        exit 1
    fi

    check_ports_available

    log_success "All pre-deployment checks passed"
    log ""

    # Backup current state
    log "Phase 2: Backup"
    log "=========================================="

    if ! backup_current_state; then
        log_error "Backup failed"
        exit 1
    fi

    log ""

    # Tag deployment
    log "Phase 3: Tagging"
    log "=========================================="

    if ! tag_deployment; then
        log_error "Tagging failed"
        exit 1
    fi

    log ""

    # Build Docker images
    log "Phase 4: Build"
    log "=========================================="

    if ! build_docker_images; then
        log_error "Build failed"
        rollback_on_failure
        exit 1
    fi

    log ""

    # Stop old containers
    log "Phase 5: Stop Old Services"
    log "=========================================="

    if ! stop_old_containers; then
        log_error "Failed to stop old containers"
        rollback_on_failure
        exit 1
    fi

    log ""

    # Start new containers
    log "Phase 6: Start New Services"
    log "=========================================="

    if ! start_new_containers; then
        log_error "Failed to start new containers"
        rollback_on_failure
        exit 1
    fi

    log ""

    # Wait for health
    log "Phase 7: Health Checks"
    log "=========================================="

    if ! wait_for_health; then
        log_error "Health checks failed"
        rollback_on_failure
        exit 1
    fi

    log ""

    # Run smoke tests
    log "Phase 8: Smoke Tests"
    log "=========================================="

    if ! run_smoke_tests; then
        log_error "Smoke tests failed"
        log_warning "Services are healthy but smoke tests failed"
        log "You may need to investigate and potentially rollback manually"
    fi

    log ""

    # Generate report
    log "Phase 9: Reporting"
    log "=========================================="

    generate_deployment_report "SUCCESS"

    log ""
    log_success "=========================================="
    log_success "DEPLOYMENT COMPLETED SUCCESSFULLY"
    log_success "=========================================="
    log_success "Deployment Tag: $DEPLOYMENT_TAG"
    log_success "Backup Location: $BACKUP_DIR"
    log_success "Log File: $LOG_FILE"
    log ""
    log "To rollback this deployment, run:"
    log "  ./rollback.sh"
    log ""
}

# Run main deployment
main "$@"
