#!/bin/bash

################################################################################
# DevSkyy Phase 2 - Deployment Verification Script
# Version: 2.0.0
# Last Updated: 2025-12-19
################################################################################

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="docker-compose.staging.yml"

# Counters
PASSED=0
FAILED=0
WARNINGS=0

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_test() {
    echo -n "$1... "
}

pass() {
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}"
    if [ -n "${1:-}" ]; then
        echo -e "  ${RED}Error: $1${NC}"
    fi
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠ WARNING${NC}"
    if [ -n "${1:-}" ]; then
        echo -e "  ${YELLOW}Warning: $1${NC}"
    fi
    ((WARNINGS++))
}

################################################################################
# Service Health Checks
################################################################################

check_service_health() {
    print_header "Service Health Checks"

    # Check if all services are running
    print_test "All services running"
    cd "$PROJECT_DIR"
    SERVICES=$(docker-compose -f "$COMPOSE_FILE" ps --services)
    ALL_RUNNING=true
    for service in $SERVICES; do
        if ! docker-compose -f "$COMPOSE_FILE" ps "$service" | grep -q "Up"; then
            ALL_RUNNING=false
            fail "$service is not running"
            break
        fi
    done
    if $ALL_RUNNING; then
        pass
    fi

    # Check PostgreSQL
    print_test "PostgreSQL health"
    if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U staging_user &> /dev/null; then
        pass
    else
        fail "PostgreSQL is not ready"
    fi

    # Check Redis
    print_test "Redis health"
    if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping | grep -q "PONG"; then
        pass
    else
        fail "Redis is not responding"
    fi

    # Check application
    print_test "Application health endpoint"
    if curl -sf http://localhost:8000/health | grep -q "healthy"; then
        pass
    else
        fail "Application health check failed"
    fi

    # Check Nginx
    print_test "Nginx health"
    if curl -sf http://localhost/health &> /dev/null; then
        pass
    else
        warn "Nginx health check failed (may not be configured)"
    fi

    # Check Prometheus
    print_test "Prometheus health"
    if curl -sf http://localhost:9090/-/healthy &> /dev/null; then
        pass
    else
        fail "Prometheus is not healthy"
    fi

    # Check Grafana
    print_test "Grafana health"
    if curl -sf http://localhost:3000/api/health &> /dev/null; then
        pass
    else
        fail "Grafana is not healthy"
    fi

    # Check AlertManager
    print_test "AlertManager health"
    if curl -sf http://localhost:9093/-/healthy &> /dev/null; then
        pass
    else
        fail "AlertManager is not healthy"
    fi

    # Check Loki
    print_test "Loki health"
    if curl -sf http://localhost:3100/ready | grep -q "ready"; then
        pass
    else
        warn "Loki is not ready"
    fi
}

################################################################################
# Database Connectivity Checks
################################################################################

check_database_connectivity() {
    print_header "Database Connectivity Checks"

    # PostgreSQL connection
    print_test "PostgreSQL connection"
    if docker-compose -f "${PROJECT_DIR}/${COMPOSE_FILE}" exec -T postgres \
        psql -U staging_user -d devskyy_staging -c "SELECT 1" &> /dev/null; then
        pass
    else
        fail "Cannot connect to PostgreSQL"
    fi

    # Check database exists
    print_test "Database exists"
    if docker-compose -f "${PROJECT_DIR}/${COMPOSE_FILE}" exec -T postgres \
        psql -U staging_user -c "\l" | grep -q "devskyy_staging"; then
        pass
    else
        fail "Database 'devskyy_staging' does not exist"
    fi

    # Check tables exist
    print_test "Database tables exist"
    TABLE_COUNT=$(docker-compose -f "${PROJECT_DIR}/${COMPOSE_FILE}" exec -T postgres \
        psql -U staging_user -d devskyy_staging -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
    if [ "$TABLE_COUNT" -gt 0 ]; then
        pass
        echo "  Found $TABLE_COUNT tables"
    else
        warn "No tables found in database"
    fi

    # Check PostgreSQL version
    print_test "PostgreSQL version"
    PG_VERSION=$(docker-compose -f "${PROJECT_DIR}/${COMPOSE_FILE}" exec -T postgres \
        psql -U staging_user -t -c "SELECT version();" | head -1)
    echo "  $PG_VERSION"
    pass
}

################################################################################
# Redis Connectivity Checks
################################################################################

check_redis_connectivity() {
    print_header "Redis Connectivity Checks"

    # Redis ping
    print_test "Redis PING"
    if docker-compose -f "${PROJECT_DIR}/${COMPOSE_FILE}" exec -T redis redis-cli ping | grep -q "PONG"; then
        pass
    else
        fail "Redis PING failed"
    fi

    # Redis SET/GET test
    print_test "Redis SET/GET operations"
    docker-compose -f "${PROJECT_DIR}/${COMPOSE_FILE}" exec -T redis redis-cli SET verify_test "success" &> /dev/null
    RESULT=$(docker-compose -f "${PROJECT_DIR}/${COMPOSE_FILE}" exec -T redis redis-cli GET verify_test | tr -d '\r')
    if [ "$RESULT" = "success" ]; then
        pass
        docker-compose -f "${PROJECT_DIR}/${COMPOSE_FILE}" exec -T redis redis-cli DEL verify_test &> /dev/null
    else
        fail "Redis SET/GET test failed"
    fi

    # Check Redis info
    print_test "Redis info"
    REDIS_VERSION=$(docker-compose -f "${PROJECT_DIR}/${COMPOSE_FILE}" exec -T redis \
        redis-cli INFO server | grep "redis_version" | cut -d: -f2 | tr -d '\r')
    echo "  Version: $REDIS_VERSION"
    pass

    # Check Redis memory
    print_test "Redis memory usage"
    REDIS_MEMORY=$(docker-compose -f "${PROJECT_DIR}/${COMPOSE_FILE}" exec -T redis \
        redis-cli INFO memory | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
    echo "  Memory: $REDIS_MEMORY"
    pass
}

################################################################################
# API Endpoint Checks
################################################################################

check_api_endpoints() {
    print_header "API Endpoint Checks"

    # Root endpoint
    print_test "GET /"
    if curl -sf http://localhost:8000/ &> /dev/null; then
        pass
    else
        fail "Root endpoint not accessible"
    fi

    # Health endpoint
    print_test "GET /health"
    HEALTH=$(curl -sf http://localhost:8000/health)
    if echo "$HEALTH" | grep -q "healthy"; then
        pass
    else
        fail "Health endpoint returned unexpected response"
    fi

    # API docs
    print_test "GET /docs"
    if curl -sf http://localhost:8000/docs &> /dev/null; then
        pass
    else
        warn "API docs not accessible"
    fi

    # Metrics endpoint
    print_test "GET /metrics"
    if curl -sf http://localhost:8000/metrics | grep -q "http_requests_total"; then
        pass
    else
        warn "Metrics endpoint not returning expected data"
    fi

    # Agent status endpoint
    print_test "GET /api/v1/agents/status"
    if curl -sf http://localhost:8000/api/v1/agents/status &> /dev/null; then
        pass
    else
        warn "Agent status endpoint not accessible"
    fi
}

################################################################################
# Monitoring Stack Checks
################################################################################

check_monitoring_stack() {
    print_header "Monitoring Stack Checks"

    # Prometheus targets
    print_test "Prometheus targets"
    TARGETS=$(curl -sf http://localhost:9090/api/v1/targets 2>/dev/null)
    if echo "$TARGETS" | grep -q "activeTargets"; then
        UP_TARGETS=$(echo "$TARGETS" | grep -o '"health":"up"' | wc -l)
        echo "  $UP_TARGETS targets UP"
        pass
    else
        fail "Cannot fetch Prometheus targets"
    fi

    # Prometheus metrics
    print_test "Application metrics in Prometheus"
    if curl -sf http://localhost:8000/metrics | grep -q "http_requests_total"; then
        pass
    else
        warn "Application not exposing metrics"
    fi

    # Grafana datasources
    print_test "Grafana datasources"
    if curl -sf http://localhost:3000/api/datasources &> /dev/null; then
        pass
    else
        warn "Cannot access Grafana datasources (may require authentication)"
    fi

    # AlertManager status
    print_test "AlertManager status"
    if curl -sf http://localhost:9093/api/v2/status &> /dev/null; then
        pass
    else
        fail "Cannot access AlertManager status"
    fi

    # Loki ready
    print_test "Loki ready state"
    if curl -sf http://localhost:3100/ready | grep -q "ready"; then
        pass
    else
        warn "Loki not ready"
    fi

    # Check exporters
    print_test "PostgreSQL exporter"
    if curl -sf http://localhost:9187/metrics | grep -q "postgres_up"; then
        pass
    else
        warn "PostgreSQL exporter not working"
    fi

    print_test "Redis exporter"
    if curl -sf http://localhost:9121/metrics | grep -q "redis_up"; then
        pass
    else
        warn "Redis exporter not working"
    fi

    print_test "Node exporter"
    if curl -sf http://localhost:9100/metrics | grep -q "node_cpu"; then
        pass
    else
        warn "Node exporter not working"
    fi
}

################################################################################
# Security Checks
################################################################################

check_security() {
    print_header "Security Checks"

    # Check for default passwords in .env
    print_test "No default passwords in .env"
    cd "$PROJECT_DIR"
    if grep -q "CHANGE_THIS_PASSWORD" .env 2>/dev/null; then
        fail "Default passwords found in .env"
    else
        pass
    fi

    # Check session cookie settings
    print_test "Secure session cookie settings"
    if grep -q "SESSION_COOKIE_SECURE=true" .env 2>/dev/null; then
        pass
    else
        warn "SESSION_COOKIE_SECURE not set to true"
    fi

    # Check MFA enabled
    print_test "MFA enabled"
    if grep -q "MFA_ENABLED=true" .env 2>/dev/null; then
        pass
    else
        warn "MFA not enabled"
    fi

    # Check rate limiting enabled
    print_test "Rate limiting enabled"
    if grep -q "RATE_LIMIT_ENABLED=true" .env 2>/dev/null; then
        pass
    else
        warn "Rate limiting not enabled"
    fi

    # Check file permissions
    print_test ".env file permissions"
    ENV_PERMS=$(stat -f "%A" .env 2>/dev/null || stat -c "%a" .env 2>/dev/null)
    if [ "$ENV_PERMS" = "600" ] || [ "$ENV_PERMS" = "400" ]; then
        pass
    else
        warn ".env file should have 600 or 400 permissions (currently: $ENV_PERMS)"
    fi
}

################################################################################
# Resource Usage Checks
################################################################################

check_resource_usage() {
    print_header "Resource Usage Checks"

    cd "$PROJECT_DIR"

    # Check disk space
    print_test "Disk space"
    DISK_USAGE=$(df -h "$PROJECT_DIR" | awk 'NR==2 {print $5}' | tr -d '%')
    if [ "$DISK_USAGE" -lt 80 ]; then
        pass
        echo "  Disk usage: ${DISK_USAGE}%"
    else
        warn "Disk usage is high: ${DISK_USAGE}%"
    fi

    # Check container memory usage
    print_test "Container memory usage"
    MEMORY_ISSUES=false
    while IFS= read -r line; do
        CONTAINER=$(echo "$line" | awk '{print $1}')
        MEM_USAGE=$(echo "$line" | awk '{print $2}' | tr -d '%')
        if (( $(echo "$MEM_USAGE > 80" | bc -l) )); then
            MEMORY_ISSUES=true
            warn "$CONTAINER using ${MEM_USAGE}% memory"
        fi
    done < <(docker stats --no-stream --format "{{.Name}} {{.MemPerc}}" $(docker-compose -f "$COMPOSE_FILE" ps -q) 2>/dev/null)

    if ! $MEMORY_ISSUES; then
        pass
    fi

    # Check container CPU usage
    print_test "Container CPU usage"
    CPU_ISSUES=false
    while IFS= read -r line; do
        CONTAINER=$(echo "$line" | awk '{print $1}')
        CPU_USAGE=$(echo "$line" | awk '{print $2}' | tr -d '%')
        if (( $(echo "$CPU_USAGE > 70" | bc -l) )); then
            CPU_ISSUES=true
            warn "$CONTAINER using ${CPU_USAGE}% CPU"
        fi
    done < <(docker stats --no-stream --format "{{.Name}} {{.CPUPerc}}" $(docker-compose -f "$COMPOSE_FILE" ps -q) 2>/dev/null)

    if ! $CPU_ISSUES; then
        pass
    fi

    # Check Docker volumes
    print_test "Docker volumes exist"
    EXPECTED_VOLUMES=("postgres_staging_data" "redis_staging_data" "prometheus_staging_data" "grafana_staging_data" "loki_staging_data" "alertmanager_staging_data")
    VOLUME_ISSUES=false
    for vol in "${EXPECTED_VOLUMES[@]}"; do
        if ! docker volume ls | grep -q "$vol"; then
            warn "Volume $vol not found"
            VOLUME_ISSUES=true
        fi
    done
    if ! $VOLUME_ISSUES; then
        pass
    fi
}

################################################################################
# Configuration Checks
################################################################################

check_configuration() {
    print_header "Configuration Checks"

    cd "$PROJECT_DIR"

    # Check .env file exists
    print_test ".env file exists"
    if [ -f ".env" ]; then
        pass
    else
        fail ".env file not found"
    fi

    # Check docker-compose file exists
    print_test "docker-compose.staging.yml exists"
    if [ -f "$COMPOSE_FILE" ]; then
        pass
    else
        fail "docker-compose.staging.yml not found"
    fi

    # Check critical env vars
    print_test "Critical environment variables set"
    source .env 2>/dev/null || true
    MISSING_VARS=()

    [ -z "${DATABASE_URL:-}" ] && MISSING_VARS+=("DATABASE_URL")
    [ -z "${REDIS_URL:-}" ] && MISSING_VARS+=("REDIS_URL")
    [ -z "${SECRET_KEY:-}" ] && MISSING_VARS+=("SECRET_KEY")
    [ -z "${JWT_SECRET_KEY:-}" ] && MISSING_VARS+=("JWT_SECRET_KEY")

    if [ ${#MISSING_VARS[@]} -eq 0 ]; then
        pass
    else
        fail "Missing variables: ${MISSING_VARS[*]}"
    fi

    # Check log directory
    print_test "Log directory exists"
    if [ -d "logs" ]; then
        pass
    else
        warn "Log directory not found"
    fi

    # Check data directory
    print_test "Data directory exists"
    if [ -d "data" ]; then
        pass
    else
        warn "Data directory not found"
    fi

    # Check uploads directory
    print_test "Uploads directory exists"
    if [ -d "uploads" ]; then
        pass
    else
        warn "Uploads directory not found"
    fi
}

################################################################################
# Network Connectivity Checks
################################################################################

check_network_connectivity() {
    print_header "Network Connectivity Checks"

    # Check internal Docker network
    print_test "Docker network exists"
    if docker network ls | grep -q "staging-network"; then
        pass
    else
        fail "staging-network not found"
    fi

    # Test inter-service connectivity
    print_test "App can reach PostgreSQL"
    if docker-compose -f "${PROJECT_DIR}/${COMPOSE_FILE}" exec -T devskyy-app \
        nc -zv postgres 5432 &> /dev/null; then
        pass
    else
        fail "Application cannot reach PostgreSQL"
    fi

    print_test "App can reach Redis"
    if docker-compose -f "${PROJECT_DIR}/${COMPOSE_FILE}" exec -T devskyy-app \
        nc -zv redis 6379 &> /dev/null; then
        pass
    else
        fail "Application cannot reach Redis"
    fi

    # Check external connectivity (if needed)
    print_test "Internet connectivity"
    if docker-compose -f "${PROJECT_DIR}/${COMPOSE_FILE}" exec -T devskyy-app \
        curl -sf https://www.google.com &> /dev/null; then
        pass
    else
        warn "No internet connectivity from application container"
    fi
}

################################################################################
# Summary Report
################################################################################

print_summary() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Verification Summary${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "Total Tests: $((PASSED + FAILED + WARNINGS))"
    echo -e "${GREEN}Passed:      $PASSED${NC}"
    echo -e "${RED}Failed:      $FAILED${NC}"
    echo -e "${YELLOW}Warnings:    $WARNINGS${NC}"
    echo ""

    if [ $FAILED -eq 0 ]; then
        if [ $WARNINGS -eq 0 ]; then
            echo -e "${GREEN}✓ All checks passed!${NC}"
            echo -e "${GREEN}Deployment is ready for use.${NC}"
        else
            echo -e "${YELLOW}⚠ All critical checks passed, but there are warnings.${NC}"
            echo -e "${YELLOW}Please review the warnings above.${NC}"
        fi
    else
        echo -e "${RED}✗ Deployment verification FAILED!${NC}"
        echo -e "${RED}Please fix the failed checks before proceeding.${NC}"
        exit 1
    fi
    echo ""
}

################################################################################
# Main Function
################################################################################

main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}DevSkyy Staging Deployment Verification${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "Started at: $(date)"

    check_service_health
    check_database_connectivity
    check_redis_connectivity
    check_api_endpoints
    check_monitoring_stack
    check_security
    check_resource_usage
    check_configuration
    check_network_connectivity

    print_summary

    echo -e "Completed at: $(date)"
}

# Run main function
main "$@"
