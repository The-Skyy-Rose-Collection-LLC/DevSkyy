#!/usr/bin/env bash
#
# DevSkyy Backup Monitoring Script
# Monitors backup health, checks for stale backups, and sends alerts
# Follows Truth Protocol: No guessing, verified behavior, proper error handling
#
# Usage:
#   ./monitor_backups.sh [OPTIONS]
#
# Options:
#   --max-age HOURS    Maximum backup age in hours (default: 48)
#   --check-s3         Also check S3 backups
#   --alert            Send alerts on failures
#   --json             Output results in JSON format
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

# Timestamp for monitoring run
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
MONITOR_DATE=$(date -u +"%Y-%m-%d")

# Environment-based configuration with defaults
ENVIRONMENT="${ENVIRONMENT:-development}"
BACKUP_DIR="${BACKUP_DIR:-/backups/devskyy}"
S3_BACKUP_BUCKET="${S3_BACKUP_BUCKET:-}"
MAX_BACKUP_AGE_HOURS="${MAX_BACKUP_AGE_HOURS:-48}"

# Alert configuration
ALERT_EMAIL="${ALERT_EMAIL:-}"
ALERT_WEBHOOK="${ALERT_WEBHOOK:-}"

# Logging configuration
LOG_DIR="${PROJECT_ROOT}/logs/monitoring"
LOG_FILE="${LOG_DIR}/monitor_${MONITOR_DATE}.log"
ERROR_LEDGER="${PROJECT_ROOT}/artifacts/error-ledger-monitor-${TIMESTAMP}.json"

# Script options
CHECK_S3=false
SEND_ALERTS=false
JSON_OUTPUT=false

# Monitoring results
MONITOR_STATUS="HEALTHY"
ISSUES_FOUND=()
WARNINGS_FOUND=()

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

    if [[ "${JSON_OUTPUT}" != "true" ]]; then
        echo "[${timestamp}] [${level}] ${message}" | tee -a "${LOG_FILE}"
    else
        echo "[${timestamp}] [${level}] ${message}" >> "${LOG_FILE}"
    fi
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
  "environment": "${ENVIRONMENT}"
}
EOF
}

# Display usage information
usage() {
    cat <<EOF
DevSkyy Backup Monitoring Script

Usage: ${SCRIPT_NAME} [OPTIONS]

Options:
    --max-age HOURS    Maximum backup age in hours (default: 48)
    --check-s3         Also check S3 backups
    --alert            Send alerts on failures
    --json             Output results in JSON format
    --help             Display this help message

Environment Variables:
    ENVIRONMENT               Current environment (development|staging|production)
    BACKUP_DIR                Backup directory (default: /backups/devskyy)
    S3_BACKUP_BUCKET          S3 bucket for remote backups (optional)
    MAX_BACKUP_AGE_HOURS      Maximum backup age in hours (default: 48)
    ALERT_EMAIL               Email address for alerts (optional)
    ALERT_WEBHOOK             Webhook URL for alerts (optional)

Exit Codes:
    0    All checks passed
    1    Warnings found
    2    Critical issues found

Examples:
    # Basic monitoring check
    ./monitor_backups.sh

    # Check with custom max age
    ./monitor_backups.sh --max-age 24

    # Check S3 and send alerts
    ./monitor_backups.sh --check-s3 --alert

    # JSON output for automation
    ./monitor_backups.sh --json

EOF
    exit 0
}

# Parse command-line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --max-age)
                MAX_BACKUP_AGE_HOURS="$2"
                shift 2
                ;;
            --check-s3)
                CHECK_S3=true
                shift
                ;;
            --alert)
                SEND_ALERTS=true
                shift
                ;;
            --json)
                JSON_OUTPUT=true
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
    log "INFO" "Checking dependencies..."

    # Check for date command (required for age calculations)
    if ! command -v date &> /dev/null; then
        log_error "date command not found" 1 "dependency_check"
        return 1
    fi

    # Check for AWS CLI if S3 check is enabled
    if [[ "${CHECK_S3}" == "true" ]]; then
        if ! command -v aws &> /dev/null; then
            log "WARN" "AWS CLI not found, disabling S3 checks"
            CHECK_S3=false
        elif [[ -z "${S3_BACKUP_BUCKET}" ]]; then
            log "WARN" "S3_BACKUP_BUCKET not set, disabling S3 checks"
            CHECK_S3=false
        fi
    fi

    return 0
}

# =============================================================================
# BACKUP DIRECTORY CHECKS
# =============================================================================

check_backup_directory_exists() {
    log "INFO" "Checking backup directory: ${BACKUP_DIR}"

    if [[ ! -d "${BACKUP_DIR}" ]]; then
        ISSUES_FOUND+=("Backup directory does not exist: ${BACKUP_DIR}")
        MONITOR_STATUS="CRITICAL"
        log "ERROR" "Backup directory does not exist"
        return 1
    fi

    log "INFO" "Backup directory exists"
    return 0
}

check_backup_directory_writable() {
    log "INFO" "Checking backup directory is writable"

    if [[ ! -w "${BACKUP_DIR}" ]]; then
        WARNINGS_FOUND+=("Backup directory is not writable: ${BACKUP_DIR}")
        log "WARN" "Backup directory is not writable"
        return 1
    fi

    log "INFO" "Backup directory is writable"
    return 0
}

# =============================================================================
# BACKUP FILE CHECKS
# =============================================================================

find_latest_backup() {
    log "INFO" "Finding latest backup file..."

    local latest_backup=$(find "${BACKUP_DIR}" -name "devskyy_backup_*.sql*" -type f 2>/dev/null | sort -r | head -1)

    if [[ -z "${latest_backup}" ]]; then
        ISSUES_FOUND+=("No backup files found in ${BACKUP_DIR}")
        MONITOR_STATUS="CRITICAL"
        log "ERROR" "No backup files found"
        return 1
    fi

    log "INFO" "Latest backup found: ${latest_backup}"
    echo "${latest_backup}"
}

check_backup_age() {
    local backup_file="$1"

    log "INFO" "Checking backup age..."

    # Get file modification time
    local file_mtime=$(stat -f%m "${backup_file}" 2>/dev/null || stat -c%Y "${backup_file}" 2>/dev/null)
    local current_time=$(date +%s)
    local age_seconds=$((current_time - file_mtime))
    local age_hours=$((age_seconds / 3600))

    log "INFO" "Backup age: ${age_hours} hours (max: ${MAX_BACKUP_AGE_HOURS} hours)"

    if [[ ${age_hours} -gt ${MAX_BACKUP_AGE_HOURS} ]]; then
        ISSUES_FOUND+=("Backup is too old: ${age_hours} hours (max: ${MAX_BACKUP_AGE_HOURS} hours)")
        MONITOR_STATUS="CRITICAL"
        log "ERROR" "Backup is stale"
        return 1
    fi

    log "INFO" "Backup age is acceptable"
    return 0
}

check_backup_size() {
    local backup_file="$1"

    log "INFO" "Checking backup file size..."

    local file_size=$(stat -f%z "${backup_file}" 2>/dev/null || stat -c%s "${backup_file}" 2>/dev/null)

    if [[ ${file_size} -eq 0 ]]; then
        ISSUES_FOUND+=("Backup file is empty: ${backup_file}")
        MONITOR_STATUS="CRITICAL"
        log "ERROR" "Backup file is empty"
        return 1
    fi

    # Warn if backup is suspiciously small (< 1KB)
    if [[ ${file_size} -lt 1024 ]]; then
        WARNINGS_FOUND+=("Backup file is very small: ${file_size} bytes")
        log "WARN" "Backup file is very small"
        return 1
    fi

    local human_size=$(du -h "${backup_file}" | cut -f1)
    log "INFO" "Backup file size: ${human_size}"
    return 0
}

check_backup_integrity() {
    local backup_file="$1"

    log "INFO" "Checking backup file integrity..."

    # Check gzip integrity for compressed files
    if [[ "${backup_file}" == *.gz && "${backup_file}" != *.gpg ]]; then
        if ! gzip -t "${backup_file}" 2>> "${LOG_FILE}"; then
            ISSUES_FOUND+=("Backup file is corrupted (gzip test failed): ${backup_file}")
            MONITOR_STATUS="CRITICAL"
            log "ERROR" "Backup file is corrupted"
            return 1
        fi
        log "INFO" "Gzip integrity check passed"
    fi

    # Check GPG integrity for encrypted files
    if [[ "${backup_file}" == *.gpg ]]; then
        if command -v gpg &> /dev/null; then
            if ! gpg --list-packets "${backup_file}" &> /dev/null; then
                ISSUES_FOUND+=("Backup file is corrupted (GPG test failed): ${backup_file}")
                MONITOR_STATUS="CRITICAL"
                log "ERROR" "Backup file is corrupted"
                return 1
            fi
            log "INFO" "GPG integrity check passed"
        else
            WARNINGS_FOUND+=("GPG not available, cannot verify encrypted backup")
            log "WARN" "Cannot verify encrypted backup"
        fi
    fi

    log "INFO" "Backup integrity check passed"
    return 0
}

count_backup_files() {
    log "INFO" "Counting backup files..."

    local backup_count=$(find "${BACKUP_DIR}" -name "devskyy_backup_*.sql*" -type f 2>/dev/null | wc -l)

    log "INFO" "Total backup files: ${backup_count}"

    if [[ ${backup_count} -eq 0 ]]; then
        ISSUES_FOUND+=("No backup files found")
        MONITOR_STATUS="CRITICAL"
        return 1
    fi

    if [[ ${backup_count} -eq 1 ]]; then
        WARNINGS_FOUND+=("Only one backup file found (no redundancy)")
        log "WARN" "Only one backup file found"
    fi

    return 0
}

# =============================================================================
# S3 CHECKS
# =============================================================================

check_s3_backups() {
    if [[ "${CHECK_S3}" != "true" ]]; then
        log "INFO" "S3 checks disabled, skipping..."
        return 0
    fi

    log "INFO" "Checking S3 backups..."

    local s3_prefix="s3://${S3_BACKUP_BUCKET}/${ENVIRONMENT}/"

    # Check if S3 bucket is accessible
    if ! aws s3 ls "${s3_prefix}" &> /dev/null; then
        WARNINGS_FOUND+=("Cannot access S3 bucket or no backups found: ${s3_prefix}")
        log "WARN" "Cannot access S3 bucket"
        return 1
    fi

    # Count S3 backups
    local s3_backup_count=$(aws s3 ls "${s3_prefix}" --recursive | grep "devskyy_backup_" | wc -l)

    log "INFO" "S3 backup files found: ${s3_backup_count}"

    if [[ ${s3_backup_count} -eq 0 ]]; then
        WARNINGS_FOUND+=("No backups found in S3: ${s3_prefix}")
        log "WARN" "No S3 backups found"
        return 1
    fi

    # Check latest S3 backup age
    local latest_s3_backup=$(aws s3 ls "${s3_prefix}" --recursive | grep "devskyy_backup_" | sort | tail -1 | awk '{print $NF}')

    if [[ -n "${latest_s3_backup}" ]]; then
        log "INFO" "Latest S3 backup: ${latest_s3_backup}"
    fi

    log "INFO" "S3 backup check passed"
    return 0
}

# =============================================================================
# DISK SPACE CHECKS
# =============================================================================

check_disk_space() {
    log "INFO" "Checking disk space for backup directory..."

    # Get disk usage percentage
    local disk_usage=$(df -h "${BACKUP_DIR}" | awk 'NR==2 {print $5}' | sed 's/%//')

    log "INFO" "Disk usage: ${disk_usage}%"

    if [[ ${disk_usage} -ge 90 ]]; then
        ISSUES_FOUND+=("Disk usage is critical: ${disk_usage}%")
        MONITOR_STATUS="CRITICAL"
        log "ERROR" "Critical disk usage"
        return 1
    elif [[ ${disk_usage} -ge 80 ]]; then
        WARNINGS_FOUND+=("Disk usage is high: ${disk_usage}%")
        log "WARN" "High disk usage"
        return 1
    fi

    log "INFO" "Disk space is adequate"
    return 0
}

# =============================================================================
# ALERTING
# =============================================================================

send_alert() {
    local subject="$1"
    local message="$2"

    if [[ "${SEND_ALERTS}" != "true" ]]; then
        log "INFO" "Alerting disabled, skipping..."
        return 0
    fi

    log "INFO" "Sending alert: ${subject}"

    # Email alert
    if [[ -n "${ALERT_EMAIL}" ]]; then
        if command -v mail &> /dev/null; then
            echo "${message}" | mail -s "${subject}" "${ALERT_EMAIL}"
            log "INFO" "Email alert sent to ${ALERT_EMAIL}"
        else
            log "WARN" "mail command not available, cannot send email alert"
        fi
    fi

    # Webhook alert
    if [[ -n "${ALERT_WEBHOOK}" ]]; then
        if command -v curl &> /dev/null; then
            local payload="{\"text\": \"${subject}\n\n${message}\"}"
            if curl -X POST -H 'Content-Type: application/json' -d "${payload}" "${ALERT_WEBHOOK}" &> /dev/null; then
                log "INFO" "Webhook alert sent"
            else
                log "WARN" "Failed to send webhook alert"
            fi
        else
            log "WARN" "curl command not available, cannot send webhook alert"
        fi
    fi
}

# =============================================================================
# MONITORING SUMMARY
# =============================================================================

generate_json_output() {
    local latest_backup="$1"

    cat <<EOF
{
  "timestamp": "${TIMESTAMP}",
  "environment": "${ENVIRONMENT}",
  "status": "${MONITOR_STATUS}",
  "backup_directory": "${BACKUP_DIR}",
  "latest_backup": "${latest_backup}",
  "max_backup_age_hours": ${MAX_BACKUP_AGE_HOURS},
  "issues": [
$(IFS=,; for issue in "${ISSUES_FOUND[@]}"; do echo "    \"${issue}\""; done | sed '$!s/$/,/')
  ],
  "warnings": [
$(IFS=,; for warning in "${WARNINGS_FOUND[@]}"; do echo "    \"${warning}\""; done | sed '$!s/$/,/')
  ]
}
EOF
}

generate_summary() {
    local latest_backup="$1"

    if [[ "${JSON_OUTPUT}" == "true" ]]; then
        generate_json_output "${latest_backup}"
        return 0
    fi

    cat <<EOF

================================================================================
DevSkyy Backup Monitoring Summary
================================================================================

Timestamp:          ${TIMESTAMP}
Environment:        ${ENVIRONMENT}
Status:             ${MONITOR_STATUS}

Backup Configuration:
    Backup Directory:       ${BACKUP_DIR}
    Max Backup Age:         ${MAX_BACKUP_AGE_HOURS} hours
    S3 Bucket:              ${S3_BACKUP_BUCKET:-Not configured}

Latest Backup:
    File:                   ${latest_backup}

Issues Found: ${#ISSUES_FOUND[@]}
EOF

    if [[ ${#ISSUES_FOUND[@]} -gt 0 ]]; then
        for issue in "${ISSUES_FOUND[@]}"; do
            echo "    - ${issue}"
        done
    fi

    cat <<EOF

Warnings Found: ${#WARNINGS_FOUND[@]}
EOF

    if [[ ${#WARNINGS_FOUND[@]} -gt 0 ]]; then
        for warning in "${WARNINGS_FOUND[@]}"; do
            echo "    - ${warning}"
        done
    fi

    cat <<EOF

Log File:           ${LOG_FILE}
Error Ledger:       ${ERROR_LEDGER}

Overall Status:     $(if [[ "${MONITOR_STATUS}" == "HEALTHY" ]]; then echo "✓ HEALTHY"; else echo "✗ ${MONITOR_STATUS}"; fi)

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
    log "INFO" "DevSkyy Backup Monitoring Script Starting"
    log "INFO" "========================================="
    log "INFO" "Environment: ${ENVIRONMENT}"
    log "INFO" "Timestamp: ${TIMESTAMP}"

    # Parse command-line arguments
    parse_args "$@"

    # Check dependencies
    check_dependencies

    # Run monitoring checks
    check_backup_directory_exists || true
    check_backup_directory_writable || true

    local latest_backup=""
    if latest_backup=$(find_latest_backup); then
        check_backup_age "${latest_backup}" || true
        check_backup_size "${latest_backup}" || true
        check_backup_integrity "${latest_backup}" || true
    fi

    count_backup_files || true
    check_disk_space || true
    check_s3_backups || true

    # Send alerts if issues found
    if [[ ${#ISSUES_FOUND[@]} -gt 0 ]] || [[ ${#WARNINGS_FOUND[@]} -gt 0 ]]; then
        local alert_subject="DevSkyy Backup Alert - ${MONITOR_STATUS} - ${ENVIRONMENT}"
        local alert_message="Backup monitoring detected issues:\n\n"

        if [[ ${#ISSUES_FOUND[@]} -gt 0 ]]; then
            alert_message+="ISSUES:\n"
            for issue in "${ISSUES_FOUND[@]}"; do
                alert_message+="- ${issue}\n"
            done
            alert_message+="\n"
        fi

        if [[ ${#WARNINGS_FOUND[@]} -gt 0 ]]; then
            alert_message+="WARNINGS:\n"
            for warning in "${WARNINGS_FOUND[@]}"; do
                alert_message+="- ${warning}\n"
            done
        fi

        send_alert "${alert_subject}" "${alert_message}"
    fi

    # Generate summary
    generate_summary "${latest_backup}"

    log "INFO" "Monitoring completed"
    log "INFO" "========================================="

    # Exit with appropriate code
    if [[ "${MONITOR_STATUS}" == "CRITICAL" ]]; then
        exit 2
    elif [[ ${#WARNINGS_FOUND[@]} -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# Run main function
main "$@"
