#!/usr/bin/env bash
#
# DevSkyy Database Restore Script
# Production-ready PostgreSQL restore with decryption, decompression, and verification
# Follows Truth Protocol: No guessing, verified behavior, proper error handling
#
# Usage:
#   ./restore_database.sh [OPTIONS] <backup-file-or-s3-path>
#
# Options:
#   --test-only        Restore to a temporary test database only
#   --from-s3          Download backup from S3 before restoring
#   --no-verify        Skip verification steps
#   --force            Skip confirmation prompt
#   --help             Display this help message
#

set -euo pipefail  # Exit on error, undefined variables, pipe failures

# =============================================================================
# CONFIGURATION
# =============================================================================

# Script metadata
SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Timestamp for logging
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
RESTORE_DATE=$(date -u +"%Y-%m-%d")

# Environment-based configuration with defaults
ENVIRONMENT="${ENVIRONMENT:-development}"
BACKUP_DIR="${BACKUP_DIR:-/backups/devskyy}"
S3_BACKUP_BUCKET="${S3_BACKUP_BUCKET:-}"
TEMP_DIR="${TEMP_DIR:-/tmp/devskyy-restore}"

# Database connection parameters
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-devskyy}"
POSTGRES_USER="${POSTGRES_USER:-devskyy}"
PGPASSWORD="${POSTGRES_PASSWORD:-changeme}"
export PGPASSWORD

# Test database for verification
TEST_DB_NAME="devskyy_restore_test_${TIMESTAMP}"

# Logging configuration
LOG_DIR="${PROJECT_ROOT}/logs/restores"
LOG_FILE="${LOG_DIR}/restore_${RESTORE_DATE}.log"
ERROR_LEDGER="${PROJECT_ROOT}/artifacts/error-ledger-restore-${TIMESTAMP}.json"

# Script options
TEST_ONLY=false
FROM_S3=false
SKIP_VERIFICATION=false
FORCE_RESTORE=false
BACKUP_SOURCE=""

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Setup logging directories
setup_logging() {
    mkdir -p "${LOG_DIR}"
    mkdir -p "$(dirname "${ERROR_LEDGER}")"
    mkdir -p "${TEMP_DIR}"
}

# Logging function with timestamp
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "[${timestamp}] [${level}] ${message}" | tee -a "${LOG_FILE}"
}

# Error tracking for Truth Protocol compliance
log_error() {
    local error_msg="$1"
    local error_code="${2:-1}"
    local context="${3:-unknown}"

    log "ERROR" "${error_msg}"

    # Append to error ledger in JSON format
    cat >> "${ERROR_LEDGER}" <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "script": "${SCRIPT_NAME}",
  "error": "${error_msg}",
  "error_code": ${error_code},
  "context": "${context}",
  "environment": "${ENVIRONMENT}",
  "backup_source": "${BACKUP_SOURCE}"
}
EOF
}

# Display usage information
usage() {
    cat <<EOF
DevSkyy Database Restore Script

Usage: ${SCRIPT_NAME} [OPTIONS] <backup-file-or-s3-path>

Options:
    --test-only        Restore to a temporary test database only
    --from-s3          Download backup from S3 before restoring
    --no-verify        Skip verification steps
    --force            Skip confirmation prompt (USE WITH CAUTION)
    --help             Display this help message

Arguments:
    backup-file-or-s3-path    Path to backup file or S3 URI

Environment Variables:
    ENVIRONMENT               Current environment (development|staging|production)
    BACKUP_DIR                Backup directory (default: /backups/devskyy)
    S3_BACKUP_BUCKET          S3 bucket for remote backups (optional)

    POSTGRES_HOST             PostgreSQL host (default: localhost)
    POSTGRES_PORT             PostgreSQL port (default: 5432)
    POSTGRES_DB               Database name (default: devskyy)
    POSTGRES_USER             Database user (default: devskyy)
    POSTGRES_PASSWORD         Database password (required)

Examples:
    # Restore from local backup file
    ./restore_database.sh /backups/devskyy/devskyy_backup_20250116T120000Z.sql.gz

    # Test restore to temporary database
    ./restore_database.sh --test-only devskyy_backup_20250116T120000Z.sql.gz

    # Download from S3 and restore
    ./restore_database.sh --from-s3 s3://my-bucket/prod/2025-01-16/backup.sql.gz.gpg

    # Force restore without confirmation (DANGEROUS)
    ./restore_database.sh --force backup.sql.gz

EOF
    exit 0
}

# Parse command-line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --test-only)
                TEST_ONLY=true
                shift
                ;;
            --from-s3)
                FROM_S3=true
                shift
                ;;
            --no-verify)
                SKIP_VERIFICATION=true
                shift
                ;;
            --force)
                FORCE_RESTORE=true
                shift
                ;;
            --help)
                usage
                ;;
            -*)
                echo "Error: Unknown option: $1"
                usage
                ;;
            *)
                BACKUP_SOURCE="$1"
                shift
                ;;
        esac
    done

    # Validate backup source was provided
    if [[ -z "${BACKUP_SOURCE}" ]]; then
        echo "Error: Backup file or S3 path is required"
        usage
    fi
}

# =============================================================================
# DEPENDENCY CHECKS
# =============================================================================

check_dependencies() {
    log "INFO" "Checking required dependencies..."

    local missing_deps=()

    # Check for psql
    if ! command -v psql &> /dev/null; then
        missing_deps+=("postgresql-client or postgresql")
    fi

    # Check for pg_restore
    if ! command -v pg_restore &> /dev/null; then
        missing_deps+=("postgresql-client or postgresql")
    fi

    # Check for gzip
    if ! command -v gzip &> /dev/null; then
        missing_deps+=("gzip")
    fi

    # Check for GPG
    if ! command -v gpg &> /dev/null; then
        log "WARN" "GPG not found, encrypted backups cannot be restored"
    fi

    # Check for AWS CLI if S3 download is requested
    if [[ "${FROM_S3}" == "true" ]]; then
        if ! command -v aws &> /dev/null; then
            missing_deps+=("awscli")
        fi
    fi

    # Report missing critical dependencies
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing required dependencies: ${missing_deps[*]}" 1 "dependency_check"
        echo "Error: Missing required dependencies: ${missing_deps[*]}"
        exit 1
    fi

    log "INFO" "All required dependencies are available"
}

# =============================================================================
# CONFIRMATION
# =============================================================================

confirm_restore() {
    if [[ "${FORCE_RESTORE}" == "true" ]]; then
        log "WARN" "Force mode enabled, skipping confirmation"
        return 0
    fi

    if [[ "${TEST_ONLY}" == "true" ]]; then
        log "INFO" "Test mode - will restore to temporary database: ${TEST_DB_NAME}"
        return 0
    fi

    cat <<EOF

================================================================================
WARNING: DATABASE RESTORE OPERATION
================================================================================

This operation will REPLACE the current database with the backup:

    Database:       ${POSTGRES_DB}
    Host:           ${POSTGRES_HOST}:${POSTGRES_PORT}
    Backup Source:  ${BACKUP_SOURCE}
    Environment:    ${ENVIRONMENT}

ALL CURRENT DATA IN ${POSTGRES_DB} WILL BE LOST!

This action cannot be undone without another backup.

================================================================================

EOF

    read -p "Are you sure you want to continue? (type 'yes' to confirm): " -r
    echo

    if [[ ! "${REPLY}" == "yes" ]]; then
        log "INFO" "Restore cancelled by user"
        echo "Restore cancelled."
        exit 0
    fi

    log "INFO" "User confirmed restore operation"
}

# =============================================================================
# DOWNLOAD FROM S3
# =============================================================================

download_from_s3() {
    local s3_path="$1"
    local local_filename=$(basename "${s3_path}")
    local local_path="${TEMP_DIR}/${local_filename}"

    log "INFO" "Downloading backup from S3..."
    log "INFO" "Source: ${s3_path}"
    log "INFO" "Destination: ${local_path}"

    if ! aws s3 cp "${s3_path}" "${local_path}" 2>> "${LOG_FILE}"; then
        log_error "S3 download failed" 2 "s3_download"
        exit 2
    fi

    log "INFO" "Download completed successfully"
    echo "${local_path}"
}

# =============================================================================
# DECRYPT BACKUP
# =============================================================================

decrypt_backup() {
    local encrypted_path="$1"

    # Check if file is encrypted
    if [[ "${encrypted_path}" != *.gpg ]]; then
        log "INFO" "Backup is not encrypted, skipping decryption"
        echo "${encrypted_path}"
        return 0
    fi

    local decrypted_path="${encrypted_path%.gpg}"

    log "INFO" "Decrypting backup..."

    if ! gpg --decrypt \
        --output "${decrypted_path}" \
        "${encrypted_path}" 2>> "${LOG_FILE}"; then

        log_error "GPG decryption failed" 3 "decryption"
        exit 3
    fi

    log "INFO" "Decryption completed successfully"
    echo "${decrypted_path}"
}

# =============================================================================
# DECOMPRESS BACKUP
# =============================================================================

decompress_backup() {
    local compressed_path="$1"

    # Check if file is compressed
    if [[ "${compressed_path}" != *.gz ]]; then
        log "INFO" "Backup is not compressed, skipping decompression"
        echo "${compressed_path}"
        return 0
    fi

    local decompressed_path="${compressed_path%.gz}"

    log "INFO" "Decompressing backup..."

    if ! gzip -dc "${compressed_path}" > "${decompressed_path}"; then
        log_error "Decompression failed" 4 "decompression"
        exit 4
    fi

    log "INFO" "Decompression completed successfully"
    echo "${decompressed_path}"
}

# =============================================================================
# PREPARE BACKUP FILE
# =============================================================================

prepare_backup() {
    local source="${BACKUP_SOURCE}"
    local backup_file=""

    # Download from S3 if requested
    if [[ "${FROM_S3}" == "true" ]]; then
        backup_file=$(download_from_s3 "${source}")
    else
        # Check if file exists locally
        if [[ ! -f "${source}" ]]; then
            # Try in backup directory
            if [[ -f "${BACKUP_DIR}/${source}" ]]; then
                backup_file="${BACKUP_DIR}/${source}"
            else
                log_error "Backup file not found: ${source}" 5 "file_not_found"
                exit 5
            fi
        else
            backup_file="${source}"
        fi
    fi

    log "INFO" "Preparing backup file: ${backup_file}"

    # Decrypt if necessary
    backup_file=$(decrypt_backup "${backup_file}")

    # Decompress if necessary
    backup_file=$(decompress_backup "${backup_file}")

    # Verify file is readable SQL
    if [[ ! -f "${backup_file}" ]]; then
        log_error "Prepared backup file not found: ${backup_file}" 6 "preparation"
        exit 6
    fi

    log "INFO" "Backup prepared successfully: ${backup_file}"
    echo "${backup_file}"
}

# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

check_database_connection() {
    log "INFO" "Checking database connection..."

    if ! pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" &> /dev/null; then
        log_error "Database is not ready at ${POSTGRES_HOST}:${POSTGRES_PORT}" 7 "connection"
        exit 7
    fi

    log "INFO" "Database connection successful"
}

create_test_database() {
    log "INFO" "Creating test database: ${TEST_DB_NAME}"

    if ! psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d postgres \
        -c "CREATE DATABASE ${TEST_DB_NAME};" 2>> "${LOG_FILE}"; then

        log_error "Failed to create test database" 8 "test_db_creation"
        exit 8
    fi

    log "INFO" "Test database created successfully"
}

drop_test_database() {
    log "INFO" "Dropping test database: ${TEST_DB_NAME}"

    psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d postgres \
        -c "DROP DATABASE IF EXISTS ${TEST_DB_NAME};" 2>> "${LOG_FILE}" || true
}

terminate_database_connections() {
    local target_db="$1"

    log "INFO" "Terminating existing connections to ${target_db}..."

    psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d postgres \
        -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${target_db}' AND pid <> pg_backend_pid();" \
        2>> "${LOG_FILE}" || true
}

restore_to_database() {
    local backup_file="$1"
    local target_db="$2"

    log "INFO" "Restoring backup to database: ${target_db}"
    log "INFO" "Backup file: ${backup_file}"

    # Terminate existing connections
    terminate_database_connections "${target_db}"

    # If restoring to main database (not test), drop and recreate
    if [[ "${target_db}" == "${POSTGRES_DB}" ]]; then
        log "INFO" "Dropping and recreating database: ${target_db}"

        # Drop database
        if ! psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d postgres \
            -c "DROP DATABASE IF EXISTS ${target_db};" 2>> "${LOG_FILE}"; then

            log_error "Failed to drop database" 9 "database_drop"
            exit 9
        fi

        # Create database
        if ! psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d postgres \
            -c "CREATE DATABASE ${target_db};" 2>> "${LOG_FILE}"; then

            log_error "Failed to create database" 10 "database_create"
            exit 10
        fi
    fi

    # Restore from backup
    log "INFO" "Running restore operation..."

    if ! psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${target_db}" \
        -f "${backup_file}" 2>> "${LOG_FILE}"; then

        log_error "Database restore failed" 11 "restore"
        exit 11
    fi

    log "INFO" "Restore completed successfully"
}

# =============================================================================
# VERIFICATION
# =============================================================================

verify_restore() {
    local target_db="$1"

    if [[ "${SKIP_VERIFICATION}" == "true" ]]; then
        log "INFO" "Verification skipped"
        return 0
    fi

    log "INFO" "Verifying restored database..."

    # Check if database exists
    local db_exists=$(psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d postgres \
        -tAc "SELECT 1 FROM pg_database WHERE datname='${target_db}';" 2>> "${LOG_FILE}")

    if [[ "${db_exists}" != "1" ]]; then
        log_error "Database does not exist after restore" 12 "verification"
        return 1
    fi

    # Count tables in restored database
    local table_count=$(psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${target_db}" \
        -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>> "${LOG_FILE}")

    log "INFO" "Database contains ${table_count} tables"

    if [[ "${table_count}" -eq 0 ]]; then
        log "WARN" "No tables found in restored database"
    fi

    # Get database size
    local db_size=$(psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${target_db}" \
        -tAc "SELECT pg_size_pretty(pg_database_size('${target_db}'));" 2>> "${LOG_FILE}")

    log "INFO" "Database size: ${db_size}"

    log "INFO" "Verification completed successfully"
}

# =============================================================================
# CLEANUP
# =============================================================================

cleanup_temp_files() {
    log "INFO" "Cleaning up temporary files..."

    if [[ -d "${TEMP_DIR}" ]]; then
        rm -rf "${TEMP_DIR}"
    fi

    log "INFO" "Cleanup completed"
}

# =============================================================================
# RESTORE SUMMARY
# =============================================================================

generate_summary() {
    local backup_file="$1"
    local target_db="$2"

    cat <<EOF

================================================================================
DevSkyy Database Restore Summary
================================================================================

Timestamp:          ${TIMESTAMP}
Environment:        ${ENVIRONMENT}

Source Backup:      ${BACKUP_SOURCE}
Restored From:      ${backup_file}

Target Database:    ${target_db}
Host:               ${POSTGRES_HOST}:${POSTGRES_PORT}

Test Mode:          ${TEST_ONLY}
Verification:       $(if [[ "${SKIP_VERIFICATION}" == "true" ]]; then echo "SKIPPED"; else echo "COMPLETED"; fi)

Log File:           ${LOG_FILE}
Error Ledger:       ${ERROR_LEDGER}

Status:             SUCCESS

================================================================================
EOF
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    # Initialize logging
    setup_logging

    log "INFO" "========================================="
    log "INFO" "DevSkyy Database Restore Script Starting"
    log "INFO" "========================================="
    log "INFO" "Environment: ${ENVIRONMENT}"
    log "INFO" "Timestamp: ${TIMESTAMP}"

    # Parse command-line arguments
    parse_args "$@"

    # Pre-flight checks
    check_dependencies
    check_database_connection

    # Confirm restore operation
    confirm_restore

    # Prepare backup file (download, decrypt, decompress)
    backup_file=$(prepare_backup)

    # Determine target database
    local target_db="${POSTGRES_DB}"
    if [[ "${TEST_ONLY}" == "true" ]]; then
        create_test_database
        target_db="${TEST_DB_NAME}"
    fi

    # Perform restore
    restore_to_database "${backup_file}" "${target_db}"

    # Verify restore
    verify_restore "${target_db}"

    # Cleanup
    if [[ "${TEST_ONLY}" == "true" ]]; then
        log "INFO" "Test restore successful. Test database will be kept for inspection: ${TEST_DB_NAME}"
        log "INFO" "To drop test database, run: psql -d postgres -c 'DROP DATABASE ${TEST_DB_NAME};'"
    fi

    cleanup_temp_files

    # Generate summary
    generate_summary "${backup_file}" "${target_db}"

    log "INFO" "Restore completed successfully"
    log "INFO" "========================================="

    exit 0
}

# Run main function
main "$@"
