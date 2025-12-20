#!/bin/bash
set -euo pipefail

# ============================================
# STAGING LOGS COLLECTION SCRIPT
# ============================================
# Collects logs from all staging services
# Compresses and archives with timestamp
# Maintains retention policy (last 5 deployments)
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOGS_DIR="${SCRIPT_DIR}/collected_logs"
COLLECTION_DIR="${LOGS_DIR}/${TIMESTAMP}"
ARCHIVE_FILE="${LOGS_DIR}/logs_${TIMESTAMP}.tar.gz"
MAX_ARCHIVES=5

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Options
TAIL_LINES=1000
INCLUDE_ALL=false
COMPRESS=true
CLEANUP_OLD=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--all)
            INCLUDE_ALL=true
            shift
            ;;
        -n|--lines)
            TAIL_LINES="$2"
            shift 2
            ;;
        --no-compress)
            COMPRESS=false
            shift
            ;;
        --no-cleanup)
            CLEANUP_OLD=false
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -a, --all           Collect all logs (not just tail)"
            echo "  -n, --lines N       Number of lines to tail (default: 1000)"
            echo "  --no-compress       Don't compress the collected logs"
            echo "  --no-cleanup        Don't cleanup old log archives"
            echo "  -h, --help          Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# ============================================
# LOGGING FUNCTIONS
# ============================================

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $1"
}

# ============================================
# LOG COLLECTION FUNCTIONS
# ============================================

setup_collection_directory() {
    log "Setting up collection directory..."

    mkdir -p "$COLLECTION_DIR"
    mkdir -p "${COLLECTION_DIR}/containers"
    mkdir -p "${COLLECTION_DIR}/system"
    mkdir -p "${COLLECTION_DIR}/application"

    log_success "Collection directory created: $COLLECTION_DIR"
}

collect_container_logs() {
    log "Collecting container logs..."

    cd "$SCRIPT_DIR"

    # Get list of all staging containers
    local containers=$(docker ps -a --format '{{.Names}}' --filter "name=staging-" 2>/dev/null || echo "")

    if [ -z "$containers" ]; then
        log_warning "No staging containers found"
        return 0
    fi

    local collected=0

    while IFS= read -r container; do
        if [ -z "$container" ]; then
            continue
        fi

        log "Collecting logs from: $container"

        local log_file="${COLLECTION_DIR}/containers/${container}.log"

        if [ "$INCLUDE_ALL" = true ]; then
            # Collect all logs
            docker logs "$container" > "$log_file" 2>&1 || {
                log_warning "Failed to collect logs from $container"
                continue
            }
        else
            # Collect last N lines
            docker logs --tail "$TAIL_LINES" "$container" > "$log_file" 2>&1 || {
                log_warning "Failed to collect logs from $container"
                continue
            }
        fi

        # Get log size
        local log_size=$(du -h "$log_file" | cut -f1)
        log_success "Collected $log_size from $container"

        collected=$((collected + 1))
    done <<< "$containers"

    log_success "Collected logs from $collected containers"
}

collect_docker_compose_logs() {
    log "Collecting docker-compose logs..."

    cd "$SCRIPT_DIR"

    if [ ! -f "docker-compose.staging.yml" ]; then
        log_warning "docker-compose.staging.yml not found"
        return 0
    fi

    local compose_log="${COLLECTION_DIR}/system/docker-compose.log"

    if [ "$INCLUDE_ALL" = true ]; then
        docker-compose -f docker-compose.staging.yml logs --no-color > "$compose_log" 2>&1 || {
            log_warning "Failed to collect docker-compose logs"
            return 0
        }
    else
        docker-compose -f docker-compose.staging.yml logs --no-color --tail "$TAIL_LINES" > "$compose_log" 2>&1 || {
            log_warning "Failed to collect docker-compose logs"
            return 0
        }
    fi

    log_success "Collected docker-compose logs"
}

collect_container_stats() {
    log "Collecting container statistics..."

    # Current stats
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}" \
        > "${COLLECTION_DIR}/system/container_stats.txt" 2>/dev/null || {
        log_warning "Failed to collect container stats"
    }

    # Container inspect info
    local containers=$(docker ps --format '{{.Names}}' --filter "name=staging-" 2>/dev/null || echo "")

    if [ -n "$containers" ]; then
        while IFS= read -r container; do
            if [ -z "$container" ]; then
                continue
            fi

            docker inspect "$container" > "${COLLECTION_DIR}/containers/${container}_inspect.json" 2>/dev/null || {
                log_warning "Failed to inspect $container"
            }
        done <<< "$containers"
    fi

    log_success "Collected container statistics"
}

collect_system_logs() {
    log "Collecting system logs..."

    # Docker daemon logs (if accessible)
    if command -v journalctl >/dev/null 2>&1; then
        journalctl -u docker --since "1 hour ago" > "${COLLECTION_DIR}/system/docker_daemon.log" 2>/dev/null || {
            log_warning "Could not collect Docker daemon logs"
        }
    fi

    # System information
    cat > "${COLLECTION_DIR}/system/system_info.txt" <<EOF
Timestamp: $(date)
Hostname: $(hostname)
Kernel: $(uname -a)
Docker Version: $(docker --version 2>/dev/null || echo "N/A")
Docker Compose Version: $(docker-compose --version 2>/dev/null || echo "N/A")

Disk Usage:
$(df -h)

Memory Usage:
$(free -h 2>/dev/null || vm_stat)

Network Interfaces:
$(ifconfig 2>/dev/null || ip addr)

EOF

    log_success "Collected system logs"
}

collect_application_logs() {
    log "Collecting application logs..."

    # Deployment logs
    if [ -d "${SCRIPT_DIR}/logs" ]; then
        mkdir -p "${COLLECTION_DIR}/application/deployment_logs"

        # Copy recent deployment logs
        find "${SCRIPT_DIR}/logs" -name "deploy_*.log" -mtime -7 -exec cp {} "${COLLECTION_DIR}/application/deployment_logs/" \; 2>/dev/null || true
        find "${SCRIPT_DIR}/logs" -name "rollback_*.log" -mtime -7 -exec cp {} "${COLLECTION_DIR}/application/deployment_logs/" \; 2>/dev/null || true

        log_success "Collected deployment logs"
    fi

    # Health check reports
    if [ -d "${SCRIPT_DIR}/reports" ]; then
        mkdir -p "${COLLECTION_DIR}/application/health_reports"

        # Copy recent health reports
        find "${SCRIPT_DIR}/reports" -name "health_*.json" -mtime -7 -exec cp {} "${COLLECTION_DIR}/application/health_reports/" \; 2>/dev/null || true
        find "${SCRIPT_DIR}/reports" -name "deployment_*.txt" -mtime -7 -exec cp {} "${COLLECTION_DIR}/application/health_reports/" \; 2>/dev/null || true

        log_success "Collected health reports"
    fi

    # Application logs from mounted volumes (if any)
    if docker volume ls --format '{{.Name}}' | grep -q "staging"; then
        log "Found staging volumes, attempting to collect logs..."

        # This would require volume inspection and copying
        # Implementation depends on specific volume structure
        log_warning "Volume log collection not fully implemented"
    fi
}

collect_database_logs() {
    log "Collecting database logs..."

    # PostgreSQL logs
    if docker ps --format '{{.Names}}' | grep -q "staging-postgres"; then
        log "Collecting PostgreSQL logs..."

        # Get PostgreSQL logs
        docker exec staging-postgres pg_controldata 2>/dev/null > "${COLLECTION_DIR}/application/postgres_control.txt" || {
            log_warning "Could not collect PostgreSQL control data"
        }

        # Get active queries
        docker exec staging-postgres psql -U postgres -c "SELECT now() - query_start as duration, query FROM pg_stat_activity WHERE state = 'active';" \
            > "${COLLECTION_DIR}/application/postgres_active_queries.txt" 2>/dev/null || {
            log_warning "Could not collect PostgreSQL active queries"
        }

        # Get database sizes
        docker exec staging-postgres psql -U postgres -c "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database;" \
            > "${COLLECTION_DIR}/application/postgres_sizes.txt" 2>/dev/null || {
            log_warning "Could not collect PostgreSQL database sizes"
        }

        log_success "Collected PostgreSQL logs"
    fi

    # Redis logs
    if docker ps --format '{{.Names}}' | grep -q "staging-redis"; then
        log "Collecting Redis logs..."

        # Get Redis info
        docker exec staging-redis redis-cli INFO > "${COLLECTION_DIR}/application/redis_info.txt" 2>/dev/null || {
            log_warning "Could not collect Redis info"
        }

        # Get Redis config
        docker exec staging-redis redis-cli CONFIG GET '*' > "${COLLECTION_DIR}/application/redis_config.txt" 2>/dev/null || {
            log_warning "Could not collect Redis config"
        }

        log_success "Collected Redis logs"
    fi
}

collect_monitoring_logs() {
    log "Collecting monitoring logs..."

    # Prometheus logs
    if docker ps --format '{{.Names}}' | grep -q "staging-prometheus"; then
        log "Collecting Prometheus data..."

        # Get Prometheus targets
        curl -s http://localhost:9090/api/v1/targets 2>/dev/null | python3 -m json.tool > "${COLLECTION_DIR}/application/prometheus_targets.json" 2>/dev/null || {
            log_warning "Could not collect Prometheus targets"
        }

        # Get Prometheus alerts
        curl -s http://localhost:9090/api/v1/alerts 2>/dev/null | python3 -m json.tool > "${COLLECTION_DIR}/application/prometheus_alerts.json" 2>/dev/null || {
            log_warning "Could not collect Prometheus alerts"
        }

        log_success "Collected Prometheus data"
    fi

    # Grafana logs
    if docker ps --format '{{.Names}}' | grep -q "staging-grafana"; then
        log "Collecting Grafana logs..."

        # Grafana logs are in the container logs already
        log_success "Grafana logs included in container logs"
    fi
}

create_manifest() {
    log "Creating collection manifest..."

    cat > "${COLLECTION_DIR}/MANIFEST.txt" <<EOF
=====================================
LOG COLLECTION MANIFEST
=====================================
Timestamp: $(date)
Collection ID: $TIMESTAMP
Collection Type: $([ "$INCLUDE_ALL" = true ] && echo "Full" || echo "Tail ($TAIL_LINES lines)")

CONTENTS:
$(find "$COLLECTION_DIR" -type f | sed "s|$COLLECTION_DIR/||" | sort)

SIZES:
$(du -sh "${COLLECTION_DIR}"/* 2>/dev/null || echo "N/A")

CONTAINER STATUS AT COLLECTION TIME:
$(docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Size}}" --filter "name=staging-")

=====================================
EOF

    log_success "Created manifest"
}

# ============================================
# COMPRESSION AND ARCHIVING
# ============================================

compress_logs() {
    if [ "$COMPRESS" = false ]; then
        log "Skipping compression (--no-compress flag)"
        return 0
    fi

    log "Compressing collected logs..."

    # Create tar.gz archive
    cd "$LOGS_DIR"

    if tar -czf "$ARCHIVE_FILE" "$TIMESTAMP" 2>/dev/null; then
        local archive_size=$(du -h "$ARCHIVE_FILE" | cut -f1)
        log_success "Created archive: $(basename "$ARCHIVE_FILE") ($archive_size)"

        # Remove uncompressed directory
        rm -rf "$COLLECTION_DIR"
        log "Removed uncompressed directory"

        return 0
    else
        log_error "Failed to compress logs"
        return 1
    fi
}

# ============================================
# CLEANUP FUNCTIONS
# ============================================

cleanup_old_archives() {
    if [ "$CLEANUP_OLD" = false ]; then
        log "Skipping cleanup (--no-cleanup flag)"
        return 0
    fi

    log "Cleaning up old log archives..."

    cd "$LOGS_DIR"

    # Count existing archives
    local archive_count=$(ls -1 logs_*.tar.gz 2>/dev/null | wc -l | xargs)

    if [ "$archive_count" -le "$MAX_ARCHIVES" ]; then
        log "Archive count ($archive_count) within limit ($MAX_ARCHIVES)"
        return 0
    fi

    # Remove oldest archives, keeping only MAX_ARCHIVES
    local to_remove=$((archive_count - MAX_ARCHIVES))

    log "Removing $to_remove old archive(s)..."

    ls -1t logs_*.tar.gz 2>/dev/null | tail -n "$to_remove" | while IFS= read -r archive; do
        rm -f "$archive"
        log "Removed: $archive"
    done

    log_success "Cleanup completed"
}

cleanup_old_directories() {
    log "Cleaning up old uncompressed log directories..."

    cd "$LOGS_DIR"

    # Remove directories older than 1 day
    find . -maxdepth 1 -type d -name "2*" -mtime +1 -exec rm -rf {} \; 2>/dev/null || true

    log_success "Cleaned up old directories"
}

# ============================================
# REPORTING
# ============================================

generate_summary() {
    log ""
    log "=========================================="
    log "LOG COLLECTION SUMMARY"
    log "=========================================="
    log "Collection ID: $TIMESTAMP"
    log "Collection Type: $([ "$INCLUDE_ALL" = true ] && echo "Full" || echo "Tail ($TAIL_LINES lines)")"
    log ""

    if [ "$COMPRESS" = true ]; then
        if [ -f "$ARCHIVE_FILE" ]; then
            local archive_size=$(du -h "$ARCHIVE_FILE" | cut -f1)
            log_success "Archive: $(basename "$ARCHIVE_FILE")"
            log_success "Size: $archive_size"
            log_success "Location: $ARCHIVE_FILE"
        fi
    else
        local dir_size=$(du -sh "$COLLECTION_DIR" | cut -f1)
        log_success "Directory: $TIMESTAMP"
        log_success "Size: $dir_size"
        log_success "Location: $COLLECTION_DIR"
    fi

    log ""
    log "Archive retention: Last $MAX_ARCHIVES deployments"
    log "Current archives: $(ls -1 "${LOGS_DIR}"/logs_*.tar.gz 2>/dev/null | wc -l | xargs)"
    log ""
    log "To extract archive:"
    if [ "$COMPRESS" = true ]; then
        log "  tar -xzf $ARCHIVE_FILE"
    fi
    log ""
    log "To view manifest:"
    if [ "$COMPRESS" = true ]; then
        log "  tar -xzOf $ARCHIVE_FILE $TIMESTAMP/MANIFEST.txt"
    else
        log "  cat $COLLECTION_DIR/MANIFEST.txt"
    fi
    log "=========================================="
}

# ============================================
# MAIN EXECUTION
# ============================================

main() {
    log "=========================================="
    log "STARTING LOG COLLECTION"
    log "=========================================="
    log "Timestamp: $(date)"
    log "Collection ID: $TIMESTAMP"
    log ""

    # Setup
    setup_collection_directory

    # Collect all logs
    collect_container_logs
    collect_docker_compose_logs
    collect_container_stats
    collect_system_logs
    collect_application_logs
    collect_database_logs
    collect_monitoring_logs

    # Create manifest
    create_manifest

    # Compress
    compress_logs

    # Cleanup
    cleanup_old_archives
    cleanup_old_directories

    # Summary
    generate_summary

    log_success "Log collection completed successfully"
}

# Run main
main "$@"
