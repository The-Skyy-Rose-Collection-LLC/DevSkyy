#!/bin/bash

################################################################################
# DevSkyy Phase 2 - Restore Script
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

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $*"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $*"
}

################################################################################
# List Available Backups
################################################################################

list_backups() {
    log "Available backups:"
    echo ""

    if [ ! -d "$BACKUP_DIR" ]; then
        log_error "Backup directory not found: $BACKUP_DIR"
        exit 1
    fi

    # Find unique backup timestamps
    BACKUPS=$(find "$BACKUP_DIR" -name "staging-backup-*-manifest.txt" -type f | sort -r)

    if [ -z "$BACKUPS" ]; then
        log_error "No backups found in $BACKUP_DIR"
        exit 1
    fi

    INDEX=1
    declare -A BACKUP_MAP

    while IFS= read -r manifest; do
        BACKUP_NAME=$(basename "$manifest" | sed 's/-manifest.txt//')
        TIMESTAMP=$(echo "$BACKUP_NAME" | sed 's/staging-backup-//')

        # Get backup info
        if [ -f "$manifest" ]; then
            DATE=$(grep "Timestamp:" "$manifest" | cut -d: -f2- | xargs)
            COMMIT=$(grep "Commit:" "$manifest" | cut -d: -f2 | xargs)
        fi

        echo -e "${GREEN}[$INDEX]${NC} $TIMESTAMP"
        echo "    Date: $DATE"
        echo "    Commit: ${COMMIT:0:8}"

        # Check which files exist
        FILES=""
        [ -f "${BACKUP_DIR}/${BACKUP_NAME}-database.dump" ] && FILES="${FILES}DB "
        [ -f "${BACKUP_DIR}/${BACKUP_NAME}-redis.rdb" ] && FILES="${FILES}Redis "
        [ -f "${BACKUP_DIR}/${BACKUP_NAME}-volumes.tar.gz" ] && FILES="${FILES}Volumes "
        [ -f "${BACKUP_DIR}/${BACKUP_NAME}-config.tar.gz" ] && FILES="${FILES}Config "
        echo "    Available: $FILES"
        echo ""

        BACKUP_MAP[$INDEX]=$BACKUP_NAME
        ((INDEX++))
    done <<< "$BACKUPS"

    echo "$INDEX" > /tmp/backup_count

    # Save backup map to temp file
    for key in "${!BACKUP_MAP[@]}"; do
        echo "$key=${BACKUP_MAP[$key]}"
    done > /tmp/backup_map
}

################################################################################
# Restore PostgreSQL
################################################################################

restore_postgres() {
    local BACKUP_NAME=$1

    log "Restoring PostgreSQL database..."

    cd "$PROJECT_DIR"

    # Get database credentials from .env
    source .env 2>/dev/null || true
    DB_USER="${POSTGRES_USER:-staging_user}"
    DB_NAME="${POSTGRES_DB:-devskyy_staging}"

    # Check if dump file exists
    DUMP_FILE="${BACKUP_DIR}/${BACKUP_NAME}-database.dump"
    if [ ! -f "$DUMP_FILE" ]; then
        log_error "Database backup file not found: $DUMP_FILE"
        return 1
    fi

    # Stop application to prevent connections
    log "Stopping application..."
    docker-compose -f "$COMPOSE_FILE" stop devskyy-app

    # Drop existing database and recreate
    log_warning "Dropping existing database..."
    docker-compose -f "$COMPOSE_FILE" exec -T postgres \
        psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS ${DB_NAME};" postgres 2>/dev/null

    docker-compose -f "$COMPOSE_FILE" exec -T postgres \
        psql -U "$DB_USER" -c "CREATE DATABASE ${DB_NAME};" postgres 2>/dev/null

    # Restore from dump
    log "Restoring database from backup..."
    cat "$DUMP_FILE" | docker-compose -f "$COMPOSE_FILE" exec -T postgres \
        pg_restore -U "$DB_USER" -d "$DB_NAME" -v 2>/dev/null

    if [ $? -eq 0 ]; then
        log_success "PostgreSQL database restored successfully"
    else
        log_error "PostgreSQL restore failed"
        return 1
    fi
}

################################################################################
# Restore Redis
################################################################################

restore_redis() {
    local BACKUP_NAME=$1

    log "Restoring Redis data..."

    cd "$PROJECT_DIR"

    # Check if dump file exists
    RDB_FILE="${BACKUP_DIR}/${BACKUP_NAME}-redis.rdb"
    if [ ! -f "$RDB_FILE" ]; then
        log_error "Redis backup file not found: $RDB_FILE"
        return 1
    fi

    # Stop Redis
    log "Stopping Redis..."
    docker-compose -f "$COMPOSE_FILE" stop redis

    # Copy RDB file to container volume
    REDIS_CONTAINER=$(docker-compose -f "$COMPOSE_FILE" ps -q redis)
    if [ -n "$REDIS_CONTAINER" ]; then
        docker cp "$RDB_FILE" "${REDIS_CONTAINER}:/data/dump.rdb"
    else
        log_error "Redis container not found"
        return 1
    fi

    # Start Redis
    log "Starting Redis..."
    docker-compose -f "$COMPOSE_FILE" start redis

    # Wait for Redis to be ready
    sleep 5

    if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping | grep -q "PONG"; then
        log_success "Redis data restored successfully"
    else
        log_error "Redis restore failed"
        return 1
    fi
}

################################################################################
# Restore Volumes
################################################################################

restore_volumes() {
    local BACKUP_NAME=$1

    log "Restoring volumes..."

    cd "$PROJECT_DIR"

    # Check if volumes backup exists
    VOLUMES_FILE="${BACKUP_DIR}/${BACKUP_NAME}-volumes.tar.gz"
    if [ ! -f "$VOLUMES_FILE" ]; then
        log_warning "Volumes backup file not found: $VOLUMES_FILE"
        return 0
    fi

    # Extract volumes
    log "Extracting volumes backup..."
    tar -xzf "$VOLUMES_FILE" -C "$PROJECT_DIR"

    if [ $? -eq 0 ]; then
        log_success "Volumes restored successfully"
    else
        log_error "Volumes restore failed"
        return 1
    fi
}

################################################################################
# Restore Configuration
################################################################################

restore_configuration() {
    local BACKUP_NAME=$1

    log "Restoring configuration..."

    cd "$PROJECT_DIR"

    # Check if config backup exists
    CONFIG_FILE="${BACKUP_DIR}/${BACKUP_NAME}-config.tar.gz"
    if [ ! -f "$CONFIG_FILE" ]; then
        log_warning "Configuration backup file not found: $CONFIG_FILE"
        return 0
    fi

    # Extract configuration
    log "Extracting configuration backup..."
    tar -xzf "$CONFIG_FILE" -C "$PROJECT_DIR"

    if [ $? -eq 0 ]; then
        log_success "Configuration restored successfully"
    else
        log_error "Configuration restore failed"
        return 1
    fi
}

################################################################################
# Main Function
################################################################################

main() {
    log "=========================================="
    log "DevSkyy Staging Restore"
    log "=========================================="
    log "Started at: $(date)"
    log ""

    # List available backups
    list_backups

    # Get user input
    echo -e "${YELLOW}Select a backup to restore (or 'q' to quit):${NC}"
    read -r SELECTION

    if [ "$SELECTION" = "q" ] || [ "$SELECTION" = "Q" ]; then
        log "Restore cancelled by user"
        exit 0
    fi

    # Validate selection
    if ! [[ "$SELECTION" =~ ^[0-9]+$ ]]; then
        log_error "Invalid selection"
        exit 1
    fi

    # Get backup name from map
    BACKUP_NAME=""
    while IFS='=' read -r key value; do
        if [ "$key" = "$SELECTION" ]; then
            BACKUP_NAME=$value
            break
        fi
    done < /tmp/backup_map

    if [ -z "$BACKUP_NAME" ]; then
        log_error "Invalid backup selection"
        exit 1
    fi

    log "Selected backup: $BACKUP_NAME"

    # Confirmation
    echo ""
    echo -e "${RED}WARNING: This will replace all current data!${NC}"
    echo -e "${YELLOW}Are you sure you want to restore from this backup? (yes/no)${NC}"
    read -r CONFIRM

    if [ "$CONFIRM" != "yes" ]; then
        log "Restore cancelled by user"
        exit 0
    fi

    # Create a backup of current state before restoring
    log "Creating safety backup of current state..."
    "${SCRIPT_DIR}/backup.sh" > /dev/null 2>&1 || true

    # Perform restore
    log ""
    log "Starting restore process..."
    log ""

    restore_postgres "$BACKUP_NAME"
    restore_redis "$BACKUP_NAME"
    restore_volumes "$BACKUP_NAME"
    restore_configuration "$BACKUP_NAME"

    # Restart services
    log ""
    log "Restarting all services..."
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" restart

    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    sleep 10

    # Verify restoration
    log ""
    log "Verifying restored deployment..."

    if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U staging_user &> /dev/null; then
        log_success "PostgreSQL is healthy"
    else
        log_error "PostgreSQL is not responding"
    fi

    if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping | grep -q "PONG"; then
        log_success "Redis is healthy"
    else
        log_error "Redis is not responding"
    fi

    if curl -sf http://localhost:8000/health &> /dev/null; then
        log_success "Application is healthy"
    else
        log_error "Application is not responding"
    fi

    # Display summary
    echo ""
    log "=========================================="
    log "Restore Summary"
    log "=========================================="
    log "Restored from: $BACKUP_NAME"
    log ""
    log_success "Restore completed!"
    log "Completed at: $(date)"
    log "=========================================="
    echo ""
    log "Next steps:"
    log "  1. Run ./staging/verify-deployment.sh to verify the restoration"
    log "  2. Check application logs for any errors"
    log "  3. Test critical functionality"
}

# Run main function
main "$@"
