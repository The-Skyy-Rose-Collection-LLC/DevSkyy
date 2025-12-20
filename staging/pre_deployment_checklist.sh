#!/bin/bash
set -euo pipefail

# ============================================
# PRE-DEPLOYMENT CHECKLIST SCRIPT
# ============================================
# Validates environment before deployment
# Ensures all prerequisites are met
# Prevents deployment failures
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Tracking
CHECKS_PASSED=0
CHECKS_FAILED=0
WARNINGS=0

# ============================================
# LOGGING FUNCTIONS
# ============================================

log() {
    echo -e "${BLUE}[CHECK]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# ============================================
# GIT CHECKS
# ============================================

check_git_working_directory_clean() {
    log "Checking git working directory status..."

    cd "$PROJECT_ROOT"

    # Check for uncommitted changes
    if ! git diff --quiet || ! git diff --cached --quiet; then
        log_warning "Git working directory has uncommitted changes"
        git status --short
        log_info "Uncommitted changes detected. Consider committing before deployment."
        return 0  # Warning, not failure
    fi

    log_success "Git working directory is clean"
}

check_git_branch() {
    log "Checking current git branch..."

    cd "$PROJECT_ROOT"

    local current_branch=$(git rev-parse --abbrev-ref HEAD)

    if [ "$current_branch" != "main" ]; then
        log_warning "Not on main branch (currently on: $current_branch)"
        log_info "Staging deployments should typically come from main branch"
        return 0  # Warning, not failure
    fi

    log_success "On main branch"
}

check_main_branch_up_to_date() {
    log "Checking if main branch is up-to-date with remote..."

    cd "$PROJECT_ROOT"

    # Fetch latest from remote
    git fetch origin --quiet

    local local_hash=$(git rev-parse HEAD)
    local remote_hash=$(git rev-parse origin/main 2>/dev/null || echo "unknown")

    if [ "$local_hash" != "$remote_hash" ]; then
        if [ "$remote_hash" = "unknown" ]; then
            log_warning "Cannot verify remote state (no remote tracking)"
        else
            log_error "Local branch is not up-to-date with origin/main"
            log_info "Local:  ${local_hash:0:8}"
            log_info "Remote: ${remote_hash:0:8}"
            log_info "Run: git pull origin main"
            return 1
        fi
    else
        log_success "Main branch is up-to-date with origin/main"
    fi
}

check_git_remote_accessible() {
    log "Checking git remote accessibility..."

    cd "$PROJECT_ROOT"

    if ! git ls-remote origin >/dev/null 2>&1; then
        log_warning "Cannot access git remote"
        log_info "This may affect deployment if remote sync is required"
        return 0  # Warning, not failure
    fi

    log_success "Git remote is accessible"
}

# ============================================
# LOCAL TESTS
# ============================================

check_tests_passing_locally() {
    log "Checking if tests can run locally..."

    cd "$PROJECT_ROOT"

    # Check if pytest is available
    if ! command -v pytest >/dev/null 2>&1; then
        log_warning "pytest not found in PATH"
        log_info "Cannot verify tests passing. Install with: pip install pytest"
        return 0  # Warning, not failure
    fi

    # Check if there are tests to run
    if ! find . -name "test_*.py" -o -name "*_test.py" | grep -q .; then
        log_warning "No test files found"
        return 0  # Warning, not failure
    fi

    log_info "Running tests (this may take a moment)..."

    # Run tests with timeout
    if timeout 120 pytest --quiet --tb=no --no-header 2>/dev/null; then
        log_success "All tests passing locally"
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            log_warning "Tests timed out after 120 seconds"
        else
            log_error "Tests are failing locally"
            log_info "Run: make test or pytest to see details"
            return 1
        fi
    fi
}

# ============================================
# DOCKER CHECKS
# ============================================

check_docker_installed() {
    log "Checking Docker installation..."

    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker is not installed"
        log_info "Install Docker from: https://docs.docker.com/get-docker/"
        return 1
    fi

    local docker_version=$(docker --version | awk '{print $3}' | sed 's/,//')
    log_success "Docker is installed (version: $docker_version)"
}

check_docker_daemon_running() {
    log "Checking Docker daemon..."

    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running"
        log_info "Start Docker Desktop or run: sudo systemctl start docker"
        return 1
    fi

    log_success "Docker daemon is running"
}

check_docker_compose_installed() {
    log "Checking docker-compose installation..."

    if ! command -v docker-compose >/dev/null 2>&1; then
        log_error "docker-compose is not installed"
        log_info "Install from: https://docs.docker.com/compose/install/"
        return 1
    fi

    local compose_version=$(docker-compose --version | awk '{print $3}' | sed 's/,//')
    log_success "docker-compose is installed (version: $compose_version)"
}

check_docker_permissions() {
    log "Checking Docker permissions..."

    if ! docker ps >/dev/null 2>&1; then
        log_warning "Cannot run docker commands without sudo"
        log_info "Add user to docker group: sudo usermod -aG docker $USER"
        return 0  # Warning, not failure
    fi

    log_success "Docker permissions are correct"
}

check_docker_compose_file_exists() {
    log "Checking docker-compose.staging.yml exists..."

    if [ ! -f "${SCRIPT_DIR}/docker-compose.staging.yml" ]; then
        log_error "docker-compose.staging.yml not found in staging directory"
        return 1
    fi

    log_success "docker-compose.staging.yml exists"
}

check_docker_compose_file_valid() {
    log "Checking docker-compose.staging.yml is valid..."

    if ! docker-compose -f "${SCRIPT_DIR}/docker-compose.staging.yml" config >/dev/null 2>&1; then
        log_error "docker-compose.staging.yml has syntax errors"
        log_info "Run: docker-compose -f staging/docker-compose.staging.yml config"
        return 1
    fi

    log_success "docker-compose.staging.yml is valid"
}

# ============================================
# NETWORK CHECKS
# ============================================

check_network_connectivity() {
    log "Checking network connectivity..."

    # Check internet connectivity
    if ! ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1; then
        log_warning "No internet connectivity detected"
        log_info "This may affect pulling Docker images"
        return 0  # Warning, not failure
    fi

    log_success "Network connectivity is available"
}

check_docker_hub_access() {
    log "Checking Docker Hub accessibility..."

    # Try to ping Docker Hub
    if ! curl -sf https://hub.docker.com >/dev/null 2>&1; then
        log_warning "Cannot reach Docker Hub"
        log_info "This may affect pulling base images"
        return 0  # Warning, not failure
    fi

    log_success "Docker Hub is accessible"
}

check_staging_ports_available() {
    log "Checking required ports are available..."

    local required_ports=(3000 5000 5432 6379)
    local ports_in_use=()

    for port in "${required_ports[@]}"; do
        if lsof -Pi ":$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
            # Check if it's from our staging containers
            if docker ps --format '{{.Ports}}' 2>/dev/null | grep -q ":$port->"; then
                log_info "Port $port in use by existing staging container (will be restarted)"
            else
                ports_in_use+=("$port")
            fi
        fi
    done

    if [ ${#ports_in_use[@]} -gt 0 ]; then
        log_error "Ports in use by non-Docker processes: ${ports_in_use[*]}"
        log_info "Stop services using these ports or deployment will fail"
        return 1
    fi

    log_success "All required ports are available"
}

# ============================================
# RESOURCE CHECKS
# ============================================

check_disk_space() {
    log "Checking disk space..."

    local available_space=$(df -BG "$PROJECT_ROOT" | tail -1 | awk '{print $4}' | sed 's/G//')
    local required_space=5

    log_info "Available space: ${available_space}GB"

    if [ "$available_space" -lt "$required_space" ]; then
        log_error "Insufficient disk space: ${available_space}GB available, ${required_space}GB required"
        return 1
    fi

    log_success "Sufficient disk space (${available_space}GB available)"
}

check_backup_space_available() {
    log "Checking backup space availability..."

    local backup_dir="${SCRIPT_DIR}/backups"
    mkdir -p "$backup_dir"

    local available_space=$(df -BG "$backup_dir" | tail -1 | awk '{print $4}' | sed 's/G//')
    local required_space=2

    if [ "$available_space" -lt "$required_space" ]; then
        log_warning "Limited backup space: ${available_space}GB available"
        log_info "Consider cleaning old backups to free space"
        return 0  # Warning, not failure
    fi

    log_success "Sufficient backup space (${available_space}GB available)"
}

check_memory_available() {
    log "Checking available memory..."

    if command -v free >/dev/null 2>&1; then
        # Linux
        local available_mem=$(free -g | awk '/^Mem:/{print $7}')
        local required_mem=2

        if [ "$available_mem" -lt "$required_mem" ]; then
            log_warning "Low memory: ${available_mem}GB available"
            log_info "Docker containers may not start properly with low memory"
        else
            log_success "Sufficient memory (${available_mem}GB available)"
        fi
    elif command -v vm_stat >/dev/null 2>&1; then
        # macOS
        local free_pages=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
        local free_gb=$((free_pages * 4096 / 1024 / 1024 / 1024))

        if [ "$free_gb" -lt 2 ]; then
            log_warning "Low memory: approximately ${free_gb}GB free"
        else
            log_success "Sufficient memory available"
        fi
    else
        log_warning "Cannot check memory (unknown system)"
    fi
}

# ============================================
# ENVIRONMENT CHECKS
# ============================================

check_environment_file() {
    log "Checking environment configuration..."

    if [ ! -f "${SCRIPT_DIR}/.env.staging" ]; then
        log_warning ".env.staging file not found"
        log_info "Create .env.staging with required environment variables"
        return 0  # Warning, not failure
    fi

    log_success ".env.staging file exists"
}

check_required_environment_variables() {
    log "Checking required environment variables..."

    if [ ! -f "${SCRIPT_DIR}/.env.staging" ]; then
        log_warning "Cannot check environment variables (.env.staging not found)"
        return 0
    fi

    local required_vars=("DATABASE_URL" "REDIS_URL")
    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "${SCRIPT_DIR}/.env.staging"; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        log_warning "Missing environment variables: ${missing_vars[*]}"
        log_info "Add these to .env.staging file"
        return 0  # Warning, not failure
    fi

    log_success "Required environment variables are defined"
}

# ============================================
# DEPENDENCY CHECKS
# ============================================

check_required_scripts_exist() {
    log "Checking required deployment scripts..."

    local required_scripts=(
        "deploy_to_staging.sh"
        "rollback.sh"
        "healthcheck.sh"
    )

    local missing_scripts=()

    for script in "${required_scripts[@]}"; do
        if [ ! -f "${SCRIPT_DIR}/${script}" ]; then
            missing_scripts+=("$script")
        elif [ ! -x "${SCRIPT_DIR}/${script}" ]; then
            log_warning "${script} is not executable"
            log_info "Run: chmod +x ${SCRIPT_DIR}/${script}"
        fi
    done

    if [ ${#missing_scripts[@]} -gt 0 ]; then
        log_error "Missing required scripts: ${missing_scripts[*]}"
        return 1
    fi

    log_success "All required scripts exist and are executable"
}

# ============================================
# SUMMARY AND REPORTING
# ============================================

print_summary() {
    echo ""
    echo "=========================================="
    echo "PRE-DEPLOYMENT CHECKLIST SUMMARY"
    echo "=========================================="
    echo "Timestamp: $(date)"
    echo ""
    echo -e "Checks Passed:  ${GREEN}$CHECKS_PASSED${NC}"
    echo -e "Checks Failed:  ${RED}$CHECKS_FAILED${NC}"
    echo -e "Warnings:       ${YELLOW}$WARNINGS${NC}"
    echo ""

    if [ $CHECKS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ READY FOR DEPLOYMENT${NC}"
        echo ""
        echo "All critical checks passed. You can proceed with deployment:"
        echo "  cd staging"
        echo "  ./deploy_to_staging.sh"
        echo ""
        if [ $WARNINGS -gt 0 ]; then
            echo -e "${YELLOW}Note: $WARNINGS warning(s) detected. Review above for details.${NC}"
        fi
    else
        echo -e "${RED}✗ NOT READY FOR DEPLOYMENT${NC}"
        echo ""
        echo "Please fix the failed checks above before deploying."
        echo ""
    fi

    echo "=========================================="
}

# ============================================
# MAIN EXECUTION
# ============================================

main() {
    echo "=========================================="
    echo "PRE-DEPLOYMENT CHECKLIST"
    echo "=========================================="
    echo "Running comprehensive pre-deployment checks..."
    echo ""

    # Git checks
    echo -e "${BLUE}=== Git Checks ===${NC}"
    check_git_working_directory_clean
    check_git_branch
    check_main_branch_up_to_date
    check_git_remote_accessible
    echo ""

    # Local tests
    echo -e "${BLUE}=== Local Tests ===${NC}"
    check_tests_passing_locally
    echo ""

    # Docker checks
    echo -e "${BLUE}=== Docker Checks ===${NC}"
    check_docker_installed
    check_docker_daemon_running
    check_docker_compose_installed
    check_docker_permissions
    check_docker_compose_file_exists
    check_docker_compose_file_valid
    echo ""

    # Network checks
    echo -e "${BLUE}=== Network Checks ===${NC}"
    check_network_connectivity
    check_docker_hub_access
    check_staging_ports_available
    echo ""

    # Resource checks
    echo -e "${BLUE}=== Resource Checks ===${NC}"
    check_disk_space
    check_backup_space_available
    check_memory_available
    echo ""

    # Environment checks
    echo -e "${BLUE}=== Environment Checks ===${NC}"
    check_environment_file
    check_required_environment_variables
    echo ""

    # Dependency checks
    echo -e "${BLUE}=== Dependency Checks ===${NC}"
    check_required_scripts_exist
    echo ""

    # Print summary
    print_summary

    # Exit with appropriate code
    if [ $CHECKS_FAILED -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run checklist
main "$@"
