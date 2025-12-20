#!/bin/bash
set -euo pipefail

# ============================================
# STAGING HEALTH CHECK SCRIPT
# ============================================
# Comprehensive health monitoring for all staging services
# Returns 0 if all critical services are healthy, 1 otherwise
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
HEALTH_REPORT="${SCRIPT_DIR}/reports/health_${TIMESTAMP}.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verbosity flag
VERBOSE=false
JSON_OUTPUT=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -j|--json)
            JSON_OUTPUT=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Health status tracking
CRITICAL_FAILURES=0
WARNING_ISSUES=0
CHECKS_PASSED=0

# JSON output structure
declare -A HEALTH_STATUS

# ============================================
# LOGGING FUNCTIONS
# ============================================

log() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
    fi
}

log_success() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${GREEN}[$(date +'%H:%M:%S')] ✓${NC} $1"
    fi
}

log_error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ✗${NC} $1" >&2
}

log_warning() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠${NC} $1"
    fi
}

# ============================================
# HEALTH CHECK FUNCTIONS
# ============================================

check_docker_running() {
    log "Checking Docker daemon..."

    if docker info >/dev/null 2>&1; then
        log_success "Docker daemon is running"
        HEALTH_STATUS[docker]="healthy"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        return 0
    else
        log_error "Docker daemon is not running"
        HEALTH_STATUS[docker]="unhealthy"
        CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
        return 1
    fi
}

check_containers_running() {
    log "Checking container status..."

    cd "$SCRIPT_DIR"

    # Expected containers
    local expected_containers=(
        "staging-frontend"
        "staging-backend"
        "staging-postgres"
        "staging-redis"
    )

    local all_running=true

    for container in "${expected_containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            log_success "$container is running"
            HEALTH_STATUS["container_${container}"]="running"
            CHECKS_PASSED=$((CHECKS_PASSED + 1))
        else
            log_error "$container is not running"
            HEALTH_STATUS["container_${container}"]="not_running"
            CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
            all_running=false
        fi
    done

    # Optional containers (non-critical)
    local optional_containers=(
        "staging-prometheus"
        "staging-grafana"
        "staging-alertmanager"
        "staging-node-exporter"
    )

    for container in "${optional_containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            log_success "$container is running"
            HEALTH_STATUS["container_${container}"]="running"
        else
            log_warning "$container is not running (optional)"
            HEALTH_STATUS["container_${container}"]="not_running"
            WARNING_ISSUES=$((WARNING_ISSUES + 1))
        fi
    done

    if [ "$all_running" = true ]; then
        return 0
    else
        return 1
    fi
}

check_container_health() {
    log "Checking container health status..."

    cd "$SCRIPT_DIR"

    local unhealthy_containers=()

    # Get containers with health checks
    while IFS= read -r line; do
        local container_name=$(echo "$line" | awk '{print $1}')
        local health_status=$(echo "$line" | awk '{print $2}')

        if [ "$health_status" = "healthy" ]; then
            log_success "$container_name health check: $health_status"
            HEALTH_STATUS["health_${container_name}"]="healthy"
            CHECKS_PASSED=$((CHECKS_PASSED + 1))
        elif [ "$health_status" = "unhealthy" ]; then
            log_error "$container_name health check: $health_status"
            HEALTH_STATUS["health_${container_name}"]="unhealthy"
            unhealthy_containers+=("$container_name")
            CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
        elif [ "$health_status" = "starting" ]; then
            log_warning "$container_name health check: $health_status"
            HEALTH_STATUS["health_${container_name}"]="starting"
            WARNING_ISSUES=$((WARNING_ISSUES + 1))
        fi
    done < <(docker ps --format '{{.Names}}\t{{.Status}}' | grep -E '\(health' | sed -E 's/.*\((healthy|unhealthy|starting)\).*/\1/' | paste <(docker ps --format '{{.Names}}' | grep -E 'staging-') -)

    if [ ${#unhealthy_containers[@]} -gt 0 ]; then
        return 1
    fi

    return 0
}

check_ports_listening() {
    log "Checking port availability..."

    local ports=(
        "3000:Frontend"
        "5000:Backend API"
        "5432:PostgreSQL"
        "6379:Redis"
    )

    local all_listening=true

    for port_info in "${ports[@]}"; do
        local port="${port_info%%:*}"
        local service="${port_info##*:}"

        if lsof -Pi ":$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_success "Port $port ($service) is listening"
            HEALTH_STATUS["port_${port}"]="listening"
            CHECKS_PASSED=$((CHECKS_PASSED + 1))
        else
            log_error "Port $port ($service) is not listening"
            HEALTH_STATUS["port_${port}"]="not_listening"
            CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
            all_listening=false
        fi
    done

    # Optional ports
    local optional_ports=(
        "3100:Grafana"
        "9090:Prometheus"
        "9093:Alertmanager"
        "9100:Node Exporter"
    )

    for port_info in "${optional_ports[@]}"; do
        local port="${port_info%%:*}"
        local service="${port_info##*:}"

        if lsof -Pi ":$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_success "Port $port ($service) is listening"
            HEALTH_STATUS["port_${port}"]="listening"
        else
            log_warning "Port $port ($service) is not listening (optional)"
            HEALTH_STATUS["port_${port}"]="not_listening"
            WARNING_ISSUES=$((WARNING_ISSUES + 1))
        fi
    done

    if [ "$all_listening" = true ]; then
        return 0
    else
        return 1
    fi
}

check_database_connectivity() {
    log "Checking PostgreSQL connectivity..."

    # Check if container is running first
    if ! docker ps --format '{{.Names}}' | grep -q "staging-postgres"; then
        log_error "PostgreSQL container is not running"
        HEALTH_STATUS[postgres_connectivity]="container_not_running"
        CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
        return 1
    fi

    # Check if postgres is ready
    if docker exec staging-postgres pg_isready -U postgres >/dev/null 2>&1; then
        log_success "PostgreSQL is accepting connections"
        HEALTH_STATUS[postgres_connectivity]="healthy"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))

        # Check database size
        local db_size=$(docker exec staging-postgres psql -U postgres -t -c "SELECT pg_size_pretty(pg_database_size('postgres'));" 2>/dev/null | xargs || echo "unknown")
        log "Database size: $db_size"
        HEALTH_STATUS[postgres_size]="$db_size"

        # Check connection count
        local connections=$(docker exec staging-postgres psql -U postgres -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | xargs || echo "unknown")
        log "Active connections: $connections"
        HEALTH_STATUS[postgres_connections]="$connections"

        return 0
    else
        log_error "PostgreSQL is not accepting connections"
        HEALTH_STATUS[postgres_connectivity]="unhealthy"
        CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
        return 1
    fi
}

check_redis_connectivity() {
    log "Checking Redis connectivity..."

    # Check if container is running first
    if ! docker ps --format '{{.Names}}' | grep -q "staging-redis"; then
        log_error "Redis container is not running"
        HEALTH_STATUS[redis_connectivity]="container_not_running"
        CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
        return 1
    fi

    # Check if Redis responds to PING
    if docker exec staging-redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        log_success "Redis is responding"
        HEALTH_STATUS[redis_connectivity]="healthy"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))

        # Get Redis info
        local redis_memory=$(docker exec staging-redis redis-cli INFO memory 2>/dev/null | grep "used_memory_human:" | cut -d: -f2 | tr -d '\r' || echo "unknown")
        log "Redis memory usage: $redis_memory"
        HEALTH_STATUS[redis_memory]="$redis_memory"

        local redis_keys=$(docker exec staging-redis redis-cli DBSIZE 2>/dev/null | awk '{print $2}' || echo "unknown")
        log "Redis keys: $redis_keys"
        HEALTH_STATUS[redis_keys]="$redis_keys"

        return 0
    else
        log_error "Redis is not responding"
        HEALTH_STATUS[redis_connectivity]="unhealthy"
        CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
        return 1
    fi
}

check_api_responding() {
    log "Checking API endpoints..."

    # Frontend
    if curl -sf http://localhost:3000 >/dev/null 2>&1; then
        log_success "Frontend is responding"
        HEALTH_STATUS[frontend_api]="healthy"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        log_error "Frontend is not responding"
        HEALTH_STATUS[frontend_api]="unhealthy"
        CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
    fi

    # Backend health endpoint
    if curl -sf http://localhost:5000/health >/dev/null 2>&1; then
        log_success "Backend health endpoint is responding"
        HEALTH_STATUS[backend_health]="healthy"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))

        # Get response details
        local backend_response=$(curl -s http://localhost:5000/health 2>/dev/null || echo "{}")
        HEALTH_STATUS[backend_response]="$backend_response"
    else
        log_error "Backend health endpoint is not responding"
        HEALTH_STATUS[backend_health]="unhealthy"
        CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
    fi

    # Backend API root
    if curl -sf http://localhost:5000/ >/dev/null 2>&1; then
        log_success "Backend API root is responding"
        HEALTH_STATUS[backend_api]="healthy"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        log_error "Backend API root is not responding"
        HEALTH_STATUS[backend_api]="unhealthy"
        CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
    fi
}

check_monitoring_stack() {
    log "Checking monitoring stack..."

    # Prometheus
    if curl -sf http://localhost:9090/-/healthy >/dev/null 2>&1; then
        log_success "Prometheus is healthy"
        HEALTH_STATUS[prometheus]="healthy"

        # Check Prometheus targets
        local targets_up=$(curl -s http://localhost:9090/api/v1/targets 2>/dev/null | grep -o '"health":"up"' | wc -l | xargs || echo "0")
        log "Prometheus targets up: $targets_up"
        HEALTH_STATUS[prometheus_targets_up]="$targets_up"
    else
        log_warning "Prometheus is not responding (optional)"
        HEALTH_STATUS[prometheus]="unhealthy"
        WARNING_ISSUES=$((WARNING_ISSUES + 1))
    fi

    # Grafana
    if curl -sf http://localhost:3100/api/health >/dev/null 2>&1; then
        log_success "Grafana is healthy"
        HEALTH_STATUS[grafana]="healthy"
    else
        log_warning "Grafana is not responding (optional)"
        HEALTH_STATUS[grafana]="unhealthy"
        WARNING_ISSUES=$((WARNING_ISSUES + 1))
    fi

    # Alertmanager
    if curl -sf http://localhost:9093/-/healthy >/dev/null 2>&1; then
        log_success "Alertmanager is healthy"
        HEALTH_STATUS[alertmanager]="healthy"
    else
        log_warning "Alertmanager is not responding (optional)"
        HEALTH_STATUS[alertmanager]="unhealthy"
        WARNING_ISSUES=$((WARNING_ISSUES + 1))
    fi
}

check_resource_usage() {
    log "Checking resource usage..."

    # Get container resource usage
    local resource_stats=$(docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null || echo "")

    if [ -n "$resource_stats" ]; then
        log "Container resource usage:"
        echo "$resource_stats" | while IFS= read -r line; do
            log "  $line"
        done

        # Check for high CPU usage (> 80%)
        local high_cpu=$(echo "$resource_stats" | awk '$2 ~ /[0-9.]+%/ {gsub(/%/,"",$2); if($2>80) print $1}')
        if [ -n "$high_cpu" ]; then
            log_warning "High CPU usage detected: $high_cpu"
            HEALTH_STATUS[high_cpu_containers]="$high_cpu"
            WARNING_ISSUES=$((WARNING_ISSUES + 1))
        fi

        HEALTH_STATUS[resource_stats]="collected"
    else
        log_warning "Could not collect resource stats"
        HEALTH_STATUS[resource_stats]="unavailable"
    fi
}

check_disk_space() {
    log "Checking disk space..."

    local available_space=$(df -BG "$SCRIPT_DIR" | tail -1 | awk '{print $4}' | sed 's/G//')
    local used_percent=$(df -BG "$SCRIPT_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')

    log "Disk space: ${available_space}GB available (${used_percent}% used)"
    HEALTH_STATUS[disk_space_gb]="$available_space"
    HEALTH_STATUS[disk_used_percent]="$used_percent"

    if [ "$used_percent" -gt 90 ]; then
        log_error "Disk space critical: ${used_percent}% used"
        CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
        return 1
    elif [ "$used_percent" -gt 80 ]; then
        log_warning "Disk space warning: ${used_percent}% used"
        WARNING_ISSUES=$((WARNING_ISSUES + 1))
    fi

    CHECKS_PASSED=$((CHECKS_PASSED + 1))
    return 0
}

# ============================================
# REPORTING FUNCTIONS
# ============================================

generate_json_report() {
    mkdir -p "$(dirname "$HEALTH_REPORT")"

    cat > "$HEALTH_REPORT" <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "overall_status": "$([ $CRITICAL_FAILURES -eq 0 ] && echo "healthy" || echo "unhealthy")",
  "summary": {
    "checks_passed": $CHECKS_PASSED,
    "critical_failures": $CRITICAL_FAILURES,
    "warnings": $WARNING_ISSUES
  },
  "checks": {
EOF

    # Add health status entries
    local first=true
    for key in "${!HEALTH_STATUS[@]}"; do
        if [ "$first" = false ]; then
            echo "," >> "$HEALTH_REPORT"
        fi
        first=false
        echo -n "    \"$key\": \"${HEALTH_STATUS[$key]}\"" >> "$HEALTH_REPORT"
    done

    cat >> "$HEALTH_REPORT" <<EOF

  }
}
EOF

    if [ "$JSON_OUTPUT" = true ]; then
        cat "$HEALTH_REPORT"
    fi
}

print_summary() {
    echo ""
    echo "=========================================="
    echo "HEALTH CHECK SUMMARY"
    echo "=========================================="
    echo "Timestamp: $(date)"
    echo "Checks Passed: $CHECKS_PASSED"
    echo "Critical Failures: $CRITICAL_FAILURES"
    echo "Warnings: $WARNING_ISSUES"
    echo ""

    if [ $CRITICAL_FAILURES -eq 0 ]; then
        echo -e "${GREEN}Overall Status: HEALTHY${NC}"
        if [ $WARNING_ISSUES -gt 0 ]; then
            echo -e "${YELLOW}Note: $WARNING_ISSUES warning(s) detected${NC}"
        fi
    else
        echo -e "${RED}Overall Status: UNHEALTHY${NC}"
        echo -e "${RED}Critical issues detected - immediate attention required${NC}"
    fi

    echo "=========================================="
    echo ""

    if [ "$JSON_OUTPUT" = false ]; then
        echo "JSON report saved to: $HEALTH_REPORT"
    fi
}

# ============================================
# MAIN HEALTH CHECK FLOW
# ============================================

main() {
    if [ "$VERBOSE" = true ]; then
        log "Starting comprehensive health check..."
        echo ""
    fi

    # Run all health checks
    check_docker_running
    check_containers_running
    check_container_health
    check_ports_listening
    check_database_connectivity
    check_redis_connectivity
    check_api_responding
    check_monitoring_stack
    check_resource_usage
    check_disk_space

    # Generate report
    generate_json_report

    # Print summary
    if [ "$JSON_OUTPUT" = false ]; then
        print_summary
    fi

    # Exit with appropriate code
    if [ $CRITICAL_FAILURES -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run health check
main "$@"
