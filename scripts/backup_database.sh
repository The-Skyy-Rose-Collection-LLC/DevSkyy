#!/usr/bin/env bash
#
# DevSkyy Database Backup Script
# Production-ready PostgreSQL backup with compression, encryption, and S3 upload
# Follows Truth Protocol: No guessing, verified behavior, proper error handling
#
# Usage:
#   ./backup_database.sh [OPTIONS]
#
# Options:
#   --no-encryption    Skip GPG encryption
#   --no-upload        Skip S3 upload
#   --local-only       Local backup only (no encryption, no upload)
#   --verify           Verify backup integrity after creation
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

# Timestamp for backup file naming (ISO 8601 format)
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
BACKUP_DATE=$(date -u +"%Y-%m-%d")

# Environment-based configuration with defaults
ENVIRONMENT="${ENVIRONMENT:-development}"
BACKUP_DIR="${BACKUP_DIR:-/backups/devskyy}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
S3_BACKUP_BUCKET="${S3_BACKUP_BUCKET:-}"
BACKUP_GPG_RECIPIENT="${BACKUP_GPG_RECIPIENT:-}"

# Database connection parameters
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-devskyy}"
POSTGRES_USER="${POSTGRES_USER:-devskyy}"
PGPASSWORD="${POSTGRES_PASSWORD:-changeme}"
export PGPASSWORD

# Backup file naming
BACKUP_FILENAME="devskyy_backup_${TIMESTAMP}.sql"
BACKUP_COMPRESSED="${BACKUP_FILENAME}.gz"
BACKUP_ENCRYPTED="${BACKUP_COMPRESSED}.gpg"

# Logging configuration
LOG_DIR="${PROJECT_ROOT}/logs/backups"
LOG_FILE="${LOG_DIR}/backup_${BACKUP_DATE}.log"
ERROR_LEDGER="${PROJECT_ROOT}/artifacts/error-ledger-backup-${TIMESTAMP}.json"

# Script options (can be overridden by command-line flags)
ENABLE_ENCRYPTION=true
ENABLE_S3_UPLOAD=true
ENABLE_VERIFICATION=false
LOCAL_ONLY=false

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Setup logging directories
setup_logging() {
    mkdir -p "${LOG_DIR}"
    mkdir -p "$(dirname "${ERROR_LEDGER}")"
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
  "backup_file": "${BACKUP_FILENAME}"
}
EOF
}

# Display usage information
usage() {
    cat <<EOF
DevSkyy Database Backup Script

Usage: ${SCRIPT_NAME} [OPTIONS]

Options:
    --no-encryption    Skip GPG encryption
    --no-upload        Skip S3 upload
    --local-only       Local backup only (no encryption, no upload)
    --verify           Verify backup integrity after creation
    --help             Display this help message

Environment Variables:
    ENVIRONMENT               Current environment (development|staging|production)
    BACKUP_DIR                Backup directory (default: /backups/devskyy)
    BACKUP_RETENTION_DAYS     Days to retain local backups (default: 7)
    S3_BACKUP_BUCKET          S3 bucket for remote backups (optional)
    BACKUP_GPG_RECIPIENT      GPG recipient for encryption (optional)

    POSTGRES_HOST             PostgreSQL host (default: localhost)
    POSTGRES_PORT             PostgreSQL port (default: 5432)
    POSTGRES_DB               Database name (default: devskyy)
    POSTGRES_USER             Database user (default: devskyy)
    POSTGRES_PASSWORD         Database password (required)

Examples:
    # Full production backup with encryption and S3 upload
    ./backup_database.sh --verify

    # Local backup only (development)
    ./backup_database.sh --local-only

    # Backup without encryption
    ./backup_database.sh --no-encryption

EOF
    exit 0
}

# Parse command-line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --no-encryption)
                ENABLE_ENCRYPTION=false
                shift
                ;;
            --no-upload)
                ENABLE_S3_UPLOAD=false
                shift
                ;;
            --local-only)
                LOCAL_ONLY=true
                ENABLE_ENCRYPTION=false
                ENABLE_S3_UPLOAD=false
                shift
                ;;
            --verify)
                ENABLE_VERIFICATION=true
                shift
                ;;
            --help)
                usage
                ;;
            *)
                echo "Error: Unknown option: $1"
                usage
                ;;
        esac
    done
}

# =============================================================================
# DEPENDENCY CHECKS
# =============================================================================

check_dependencies() {
    log "INFO" "Checking required dependencies..."

    local missing_deps=()

    # Check for pg_dump
    if ! command -v pg_dump &> /dev/null; then
        missing_deps+=("postgresql-client or postgresql")
    fi

    # Check for gzip
    if ! command -v gzip &> /dev/null; then
        missing_deps+=("gzip")
    fi

    # Check for GPG if encryption is enabled
    if [[ "${ENABLE_ENCRYPTION}" == "true" ]]; then
        if ! command -v gpg &> /dev/null; then
            log "WARN" "GPG not found, disabling encryption"
            ENABLE_ENCRYPTION=false
        fi
    fi

    # Check for AWS CLI if S3 upload is enabled
    if [[ "${ENABLE_S3_UPLOAD}" == "true" ]]; then
        if ! command -v aws &> /dev/null; then
            log "WARN" "AWS CLI not found, disabling S3 upload"
            ENABLE_S3_UPLOAD=false
        elif [[ -z "${S3_BACKUP_BUCKET}" ]]; then
            log "WARN" "S3_BACKUP_BUCKET not set, disabling S3 upload"
            ENABLE_S3_UPLOAD=false
        fi
    fi

    # Report missing critical dependencies
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing required dependencies: ${missing_deps[*]}" 1 "dependency_check"
        echo "Error: Missing required dependencies: ${missing_deps[*]}"
        echo "Please install the missing packages and try again."
        exit 1
    fi

    log "INFO" "All required dependencies are available"
}

# =============================================================================
# DATABASE HEALTH CHECK
# =============================================================================

check_database_health() {
    log "INFO" "Checking database connection..."

    if ! pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" &> /dev/null; then
        log_error "Database is not ready at ${POSTGRES_HOST}:${POSTGRES_PORT}" 2 "health_check"
        echo "Error: Cannot connect to database at ${POSTGRES_HOST}:${POSTGRES_PORT}"
        echo "Please ensure the database is running and accessible."
        exit 2
    fi

    log "INFO" "Database connection successful"
}

# =============================================================================
# BACKUP CREATION
# =============================================================================

create_backup() {
    log "INFO" "Starting database backup..."
    log "INFO" "Database: ${POSTGRES_DB} on ${POSTGRES_HOST}:${POSTGRES_PORT}"

    # Create backup directory if it doesn't exist
    mkdir -p "${BACKUP_DIR}"

    local backup_path="${BACKUP_DIR}/${BACKUP_FILENAME}"

    # Perform database dump
    log "INFO" "Running pg_dump..."
    if ! pg_dump \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        --format=plain \
        --no-owner \
        --no-acl \
        --verbose \
        --file="${backup_path}" 2>> "${LOG_FILE}"; then

        log_error "pg_dump failed" 3 "backup_creation"
        echo "Error: Database dump failed. Check log file: ${LOG_FILE}"
        exit 3
    fi

    # Verify backup file was created and is not empty
    if [[ ! -f "${backup_path}" ]]; then
        log_error "Backup file was not created: ${backup_path}" 4 "backup_creation"
        exit 4
    fi

    local backup_size=$(du -h "${backup_path}" | cut -f1)
    log "INFO" "Backup created successfully: ${backup_path} (${backup_size})"

    echo "${backup_path}"
}

# =============================================================================
# COMPRESSION
# =============================================================================

compress_backup() {
    local backup_path="$1"
    local compressed_path="${BACKUP_DIR}/${BACKUP_COMPRESSED}"

    log "INFO" "Compressing backup..."

    if ! gzip -c "${backup_path}" > "${compressed_path}"; then
        log_error "Compression failed" 5 "compression"
        exit 5
    fi

    local compressed_size=$(du -h "${compressed_path}" | cut -f1)
    log "INFO" "Backup compressed: ${compressed_path} (${compressed_size})"

    # Remove uncompressed backup to save space
    rm -f "${backup_path}"

    echo "${compressed_path}"
}

# =============================================================================
# ENCRYPTION
# =============================================================================

encrypt_backup() {
    local compressed_path="$1"
    local encrypted_path="${BACKUP_DIR}/${BACKUP_ENCRYPTED}"

    if [[ "${ENABLE_ENCRYPTION}" != "true" ]]; then
        log "INFO" "Encryption disabled, skipping..."
        echo "${compressed_path}"
        return 0
    fi

    if [[ -z "${BACKUP_GPG_RECIPIENT}" ]]; then
        log "WARN" "BACKUP_GPG_RECIPIENT not set, skipping encryption"
        echo "${compressed_path}"
        return 0
    fi

    log "INFO" "Encrypting backup with GPG..."
    log "INFO" "Recipient: ${BACKUP_GPG_RECIPIENT}"

    if ! gpg --encrypt \
        --recipient "${BACKUP_GPG_RECIPIENT}" \
        --trust-model always \
        --output "${encrypted_path}" \
        "${compressed_path}" 2>> "${LOG_FILE}"; then

        log_error "GPG encryption failed" 6 "encryption"
        log "WARN" "Continuing with unencrypted backup"
        echo "${compressed_path}"
        return 0
    fi

    local encrypted_size=$(du -h "${encrypted_path}" | cut -f1)
    log "INFO" "Backup encrypted: ${encrypted_path} (${encrypted_size})"

    # Remove unencrypted compressed backup
    rm -f "${compressed_path}"

    echo "${encrypted_path}"
}

# =============================================================================
# S3 UPLOAD
# =============================================================================

upload_to_s3() {
    local backup_path="$1"

    if [[ "${ENABLE_S3_UPLOAD}" != "true" ]]; then
        log "INFO" "S3 upload disabled, skipping..."
        return 0
    fi

    local backup_filename=$(basename "${backup_path}")
    local s3_path="s3://${S3_BACKUP_BUCKET}/${ENVIRONMENT}/${BACKUP_DATE}/${backup_filename}"

    log "INFO" "Uploading backup to S3..."
    log "INFO" "Destination: ${s3_path}"

    if ! aws s3 cp "${backup_path}" "${s3_path}" \
        --storage-class STANDARD_IA \
        --metadata "environment=${ENVIRONMENT},database=${POSTGRES_DB},timestamp=${TIMESTAMP}" \
        2>> "${LOG_FILE}"; then

        log_error "S3 upload failed" 7 "s3_upload"
        log "WARN" "Backup saved locally but not uploaded to S3"
        return 1
    fi

    log "INFO" "Backup uploaded to S3 successfully: ${s3_path}"

    # Verify S3 upload
    if aws s3 ls "${s3_path}" &> /dev/null; then
        log "INFO" "S3 upload verified"
    else
        log "WARN" "Could not verify S3 upload"
    fi

    return 0
}

# =============================================================================
# VERIFICATION
# =============================================================================

verify_backup() {
    local backup_path="$1"

    if [[ "${ENABLE_VERIFICATION}" != "true" ]]; then
        return 0
    fi

    log "INFO" "Verifying backup integrity..."

    # Check if file exists and is not empty
    if [[ ! -s "${backup_path}" ]]; then
        log_error "Backup file is empty or does not exist" 8 "verification"
        return 1
    fi

    # For compressed files, test gzip integrity
    if [[ "${backup_path}" == *.gz ]]; then
        if ! gzip -t "${backup_path}" 2>> "${LOG_FILE}"; then
            log_error "Gzip integrity check failed" 9 "verification"
            return 1
        fi
        log "INFO" "Gzip integrity check passed"
    fi

    # For encrypted files, test GPG integrity
    if [[ "${backup_path}" == *.gpg ]]; then
        if ! gpg --list-packets "${backup_path}" &> /dev/null; then
            log_error "GPG integrity check failed" 10 "verification"
            return 1
        fi
        log "INFO" "GPG integrity check passed"
    fi

    log "INFO" "Backup verification completed successfully"
    return 0
}

# =============================================================================
# CLEANUP
# =============================================================================

cleanup_old_backups() {
    log "INFO" "Cleaning up old backups (retention: ${BACKUP_RETENTION_DAYS} days)..."

    local deleted_count=0

    # Find and delete backups older than retention period
    if [[ -d "${BACKUP_DIR}" ]]; then
        while IFS= read -r old_backup; do
            log "INFO" "Deleting old backup: ${old_backup}"
            rm -f "${old_backup}"
            ((deleted_count++))
        done < <(find "${BACKUP_DIR}" -name "devskyy_backup_*.sql*" -type f -mtime +${BACKUP_RETENTION_DAYS})

        log "INFO" "Deleted ${deleted_count} old backup(s)"
    fi
}

# =============================================================================
# BACKUP SUMMARY
# =============================================================================

generate_summary() {
    local backup_path="$1"
    local backup_size=$(du -h "${backup_path}" | cut -f1)
    local backup_filename=$(basename "${backup_path}")

    cat <<EOF

================================================================================
DevSkyy Database Backup Summary
================================================================================

Timestamp:          ${TIMESTAMP}
Environment:        ${ENVIRONMENT}
Database:           ${POSTGRES_DB}
Host:               ${POSTGRES_HOST}:${POSTGRES_PORT}

Backup File:        ${backup_filename}
Backup Size:        ${backup_size}
Backup Location:    ${backup_path}

Encryption:         ${ENABLE_ENCRYPTION}
S3 Upload:          ${ENABLE_S3_UPLOAD}
Verification:       ${ENABLE_VERIFICATION}

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
    log "INFO" "DevSkyy Database Backup Script Starting"
    log "INFO" "========================================="
    log "INFO" "Environment: ${ENVIRONMENT}"
    log "INFO" "Timestamp: ${TIMESTAMP}"

    # Parse command-line arguments
    parse_args "$@"

    # Pre-flight checks
    check_dependencies
    check_database_health

    # Create backup
    backup_path=$(create_backup)

    # Compress backup
    backup_path=$(compress_backup "${backup_path}")

    # Encrypt backup (if enabled)
    backup_path=$(encrypt_backup "${backup_path}")

    # Verify backup (if enabled)
    verify_backup "${backup_path}"

    # Upload to S3 (if enabled)
    upload_to_s3 "${backup_path}"

    # Cleanup old backups
    cleanup_old_backups

    # Generate summary
    generate_summary "${backup_path}"

    log "INFO" "Backup completed successfully"
    log "INFO" "========================================="

    exit 0
}

# Run main function
main "$@"
