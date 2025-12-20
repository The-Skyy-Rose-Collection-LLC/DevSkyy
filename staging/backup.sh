#!/bin/bash

################################################################################
# DevSkyy Phase 2 - Backup Script
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
BACKUP_DIR="${PROJECT_DIR}/data/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="staging-backup-${TIMESTAMP}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $*"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $*"
}

################################################################################
# Backup PostgreSQL
################################################################################

backup_postgres() {
    log "Backing up PostgreSQL database..."

    cd "$PROJECT_DIR"

    # Check if postgres container is running
    if ! docker-compose -f "$COMPOSE_FILE" ps postgres | grep -q "Up"; then
        log_error "PostgreSQL container is not running"
        return 1
    fi

    # Get database credentials from .env
    source .env 2>/dev/null || true
    DB_USER="${POSTGRES_USER:-staging_user}"
    DB_NAME="${POSTGRES_DB:-devskyy_staging}"

    # Create database dump
    docker-compose -f "$COMPOSE_FILE" exec -T postgres \
        pg_dump -U "$DB_USER" -F c -b -v "$DB_NAME" \
        > "${BACKUP_DIR}/${BACKUP_NAME}-database.dump" 2>/dev/null

    if [ $? -eq 0 ]; then
        log_success "PostgreSQL backup created: ${BACKUP_NAME}-database.dump"

        # Also create SQL dump for easier inspection
        docker-compose -f "$COMPOSE_FILE" exec -T postgres \
            pg_dump -U "$DB_USER" "$DB_NAME" \
            > "${BACKUP_DIR}/${BACKUP_NAME}-database.sql" 2>/dev/null

        log_success "SQL dump created: ${BACKUP_NAME}-database.sql"
    else
        log_error "PostgreSQL backup failed"
        return 1
    fi
}

################################################################################
# Backup Redis
################################################################################

backup_redis() {
    log "Backing up Redis data..."

    cd "$PROJECT_DIR"

    # Check if redis container is running
    if ! docker-compose -f "$COMPOSE_FILE" ps redis | grep -q "Up"; then
        log_error "Redis container is not running"
        return 1
    fi

    # Trigger Redis SAVE
    docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli SAVE

    # Copy RDB file
    docker cp $(docker-compose -f "$COMPOSE_FILE" ps -q redis):/data/dump.rdb \
        "${BACKUP_DIR}/${BACKUP_NAME}-redis.rdb" 2>/dev/null

    if [ $? -eq 0 ]; then
        log_success "Redis backup created: ${BACKUP_NAME}-redis.rdb"
    else
        log_error "Redis backup failed"
        return 1
    fi
}

################################################################################
# Backup Volumes
################################################################################

backup_volumes() {
    log "Backing up Docker volumes..."

    cd "$PROJECT_DIR"

    # Create volumes backup
    tar -czf "${BACKUP_DIR}/${BACKUP_NAME}-volumes.tar.gz" \
        --exclude='*.log' \
        data/ uploads/ 2>/dev/null || true

    if [ -f "${BACKUP_DIR}/${BACKUP_NAME}-volumes.tar.gz" ]; then
        log_success "Volumes backup created: ${BACKUP_NAME}-volumes.tar.gz"
    else
        log_error "Volumes backup failed"
        return 1
    fi
}

################################################################################
# Backup Configuration
################################################################################

backup_configuration() {
    log "Backing up configuration files..."

    cd "$PROJECT_DIR"

    # Backup configuration (excluding secrets)
    tar -czf "${BACKUP_DIR}/${BACKUP_NAME}-config.tar.gz" \
        --exclude='.env' \
        --exclude='*.key' \
        --exclude='*.pem' \
        config/ docker-compose.staging.yml 2>/dev/null || true

    if [ -f "${BACKUP_DIR}/${BACKUP_NAME}-config.tar.gz" ]; then
        log_success "Configuration backup created: ${BACKUP_NAME}-config.tar.gz"
    else
        log_error "Configuration backup failed"
        return 1
    fi
}

################################################################################
# Create Backup Manifest
################################################################################

create_manifest() {
    log "Creating backup manifest..."

    MANIFEST_FILE="${BACKUP_DIR}/${BACKUP_NAME}-manifest.txt"

    cat > "$MANIFEST_FILE" <<EOF
DevSkyy Staging Backup Manifest
================================
Backup Name: ${BACKUP_NAME}
Timestamp: $(date +'%Y-%m-%d %H:%M:%S')
Environment: staging

Files:
------
EOF

    # List backup files with sizes
    for file in "${BACKUP_DIR}/${BACKUP_NAME}"*; do
        if [ -f "$file" ]; then
            SIZE=$(du -h "$file" | cut -f1)
            echo "  $(basename "$file"): $SIZE" >> "$MANIFEST_FILE"
        fi
    done

    # Add git information
    cd "$PROJECT_DIR"
    echo "" >> "$MANIFEST_FILE"
    echo "Git Information:" >> "$MANIFEST_FILE"
    echo "  Commit: $(git rev-parse HEAD 2>/dev/null || echo 'N/A')" >> "$MANIFEST_FILE"
    echo "  Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'N/A')" >> "$MANIFEST_FILE"

    # Add Docker images
    echo "" >> "$MANIFEST_FILE"
    echo "Docker Images:" >> "$MANIFEST_FILE"
    docker-compose -f "$COMPOSE_FILE" images >> "$MANIFEST_FILE" 2>/dev/null || true

    log_success "Manifest created: ${BACKUP_NAME}-manifest.txt"
}

################################################################################
# Cleanup Old Backups
################################################################################

cleanup_old_backups() {
    log "Cleaning up old backups..."

    # Keep last 14 days of backups
    RETENTION_DAYS=14

    find "$BACKUP_DIR" -name "staging-backup-*" -type f -mtime +$RETENTION_DAYS -delete

    REMAINING=$(find "$BACKUP_DIR" -name "staging-backup-*" -type f | wc -l)
    log_success "Cleanup complete. $REMAINING backup files remaining."
}

################################################################################
# Main Function
################################################################################

main() {
    log "=========================================="
    log "DevSkyy Staging Backup"
    log "=========================================="
    log "Started at: $(date)"
    log ""

    # Run backup steps
    backup_postgres
    backup_redis
    backup_volumes
    backup_configuration
    create_manifest
    cleanup_old_backups

    # Display summary
    echo ""
    log "=========================================="
    log "Backup Summary"
    log "=========================================="
    log "Backup location: $BACKUP_DIR"
    log "Backup name: $BACKUP_NAME"
    echo ""
    log "Backup files:"
    for file in "${BACKUP_DIR}/${BACKUP_NAME}"*; do
        if [ -f "$file" ]; then
            SIZE=$(du -h "$file" | cut -f1)
            log "  $(basename "$file"): $SIZE"
        fi
    done
    echo ""
    log_success "Backup completed successfully!"
    log "Completed at: $(date)"
    log "=========================================="
}

# Run main function
main "$@"
