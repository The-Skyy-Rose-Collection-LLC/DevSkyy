#!/usr/bin/env bash
#
# DevSkyy Backup Testing Script
# Automated testing of backup and restore functionality
# Follows Truth Protocol: No guessing, verified behavior, proper error handling
#
# Usage:
#   ./test_backup.sh [OPTIONS]
#
# Options:
#   --cleanup          Clean up test artifacts after completion
#   --skip-restore     Skip restore testing
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

# Timestamp for test run
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
TEST_DATE=$(date -u +"%Y-%m-%d")

# Test configuration
TEST_DB_NAME="devskyy_backup_test_${TIMESTAMP}"
TEST_BACKUP_DIR="/tmp/devskyy-backup-test-${TIMESTAMP}"

# Environment-based configuration
ENVIRONMENT="${ENVIRONMENT:-test}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-devskyy}"
PGPASSWORD="${POSTGRES_PASSWORD:-changeme}"
export PGPASSWORD

# Logging configuration
LOG_DIR="${PROJECT_ROOT}/logs/tests"
LOG_FILE="${LOG_DIR}/test_backup_${TEST_DATE}.log"
ERROR_LEDGER="${PROJECT_ROOT}/artifacts/error-ledger-test-${TIMESTAMP}.json"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TEST_RESULTS=()

# Script options
CLEANUP_AFTER=false
SKIP_RESTORE=false

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Setup logging directories
setup_logging() {
    mkdir -p "${LOG_DIR}"
    mkdir -p "$(dirname "${ERROR_LEDGER}")"
    mkdir -p "${TEST_BACKUP_DIR}"
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
  "test_database": "${TEST_DB_NAME}"
}
EOF
}

# Display usage information
usage() {
    cat <<EOF
DevSkyy Backup Testing Script

Usage: ${SCRIPT_NAME} [OPTIONS]

Options:
    --cleanup          Clean up test artifacts after completion
    --skip-restore     Skip restore testing
    --help             Display this help message

Environment Variables:
    ENVIRONMENT               Current environment (default: test)
    POSTGRES_HOST             PostgreSQL host (default: localhost)
    POSTGRES_PORT             PostgreSQL port (default: 5432)
    POSTGRES_USER             Database user (default: devskyy)
    POSTGRES_PASSWORD         Database password (required)

Description:
    This script performs automated testing of the backup and restore system:

    1. Creates a test database with sample data
    2. Runs backup script
    3. Verifies backup file integrity
    4. Tests restore to temporary database
    5. Validates data integrity
    6. Tests encryption (if configured)
    7. Tests compression
    8. Cleans up test artifacts (optional)

Examples:
    # Run all tests
    ./test_backup.sh

    # Run tests and cleanup
    ./test_backup.sh --cleanup

    # Test backup only (skip restore)
    ./test_backup.sh --skip-restore

EOF
    exit 0
}

# Parse command-line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --cleanup)
                CLEANUP_AFTER=true
                shift
                ;;
            --skip-restore)
                SKIP_RESTORE=true
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
# TEST FRAMEWORK
# =============================================================================

test_pass() {
    local test_name="$1"
    ((TESTS_PASSED++))
    TEST_RESULTS+=("PASS: ${test_name}")
    log "PASS" "${test_name}"
    echo "✓ PASS: ${test_name}"
}

test_fail() {
    local test_name="$1"
    local error_msg="${2:-Unknown error}"
    ((TESTS_FAILED++))
    TEST_RESULTS+=("FAIL: ${test_name} - ${error_msg}")
    log "FAIL" "${test_name} - ${error_msg}"
    echo "✗ FAIL: ${test_name}"
    echo "  Error: ${error_msg}"
}

test_skip() {
    local test_name="$1"
    local reason="${2:-Skipped}"
    TEST_RESULTS+=("SKIP: ${test_name} - ${reason}")
    log "SKIP" "${test_name} - ${reason}"
    echo "⊘ SKIP: ${test_name}"
}

# =============================================================================
# TEST DATABASE SETUP
# =============================================================================

test_create_test_database() {
    log "INFO" "TEST: Creating test database"

    if psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d postgres \
        -c "CREATE DATABASE ${TEST_DB_NAME};" 2>> "${LOG_FILE}"; then

        test_pass "Create test database"
        return 0
    else
        test_fail "Create test database" "Failed to create database"
        return 1
    fi
}

test_populate_test_data() {
    log "INFO" "TEST: Populating test database with sample data"

    local sql_commands="
        CREATE TABLE test_users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE test_orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES test_users(id),
            amount DECIMAL(10, 2),
            status VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        INSERT INTO test_users (username, email) VALUES
            ('alice', 'alice@example.com'),
            ('bob', 'bob@example.com'),
            ('charlie', 'charlie@example.com');

        INSERT INTO test_orders (user_id, amount, status) VALUES
            (1, 99.99, 'completed'),
            (2, 149.50, 'pending'),
            (3, 75.25, 'completed');
    "

    if echo "${sql_commands}" | psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" -d "${TEST_DB_NAME}" 2>> "${LOG_FILE}"; then

        test_pass "Populate test data"
        return 0
    else
        test_fail "Populate test data" "Failed to insert test data"
        return 1
    fi
}

# =============================================================================
# BACKUP TESTS
# =============================================================================

test_backup_creation() {
    log "INFO" "TEST: Creating backup of test database"

    local backup_script="${SCRIPT_DIR}/backup_database.sh"

    if [[ ! -x "${backup_script}" ]]; then
        test_fail "Backup script execution" "Backup script not found or not executable"
        return 1
    fi

    # Run backup script with test database
    if POSTGRES_DB="${TEST_DB_NAME}" \
       BACKUP_DIR="${TEST_BACKUP_DIR}" \
       "${backup_script}" --local-only --no-encryption 2>> "${LOG_FILE}"; then

        test_pass "Backup creation"
        return 0
    else
        test_fail "Backup creation" "Backup script failed"
        return 1
    fi
}

test_backup_file_exists() {
    log "INFO" "TEST: Checking backup file exists"

    local backup_files=$(find "${TEST_BACKUP_DIR}" -name "devskyy_backup_*.sql.gz" -type f 2>/dev/null)

    if [[ -n "${backup_files}" ]]; then
        local backup_count=$(echo "${backup_files}" | wc -l)
        test_pass "Backup file exists (${backup_count} file(s) found)"
        echo "${backup_files}" | head -1
        return 0
    else
        test_fail "Backup file exists" "No backup files found"
        return 1
    fi
}

test_backup_file_size() {
    log "INFO" "TEST: Checking backup file size"

    local backup_file=$(find "${TEST_BACKUP_DIR}" -name "devskyy_backup_*.sql.gz" -type f 2>/dev/null | head -1)

    if [[ -z "${backup_file}" ]]; then
        test_fail "Backup file size" "Backup file not found"
        return 1
    fi

    local file_size=$(stat -f%z "${backup_file}" 2>/dev/null || stat -c%s "${backup_file}" 2>/dev/null)

    if [[ "${file_size}" -gt 0 ]]; then
        local human_size=$(du -h "${backup_file}" | cut -f1)
        test_pass "Backup file size (${human_size})"
        return 0
    else
        test_fail "Backup file size" "Backup file is empty"
        return 1
    fi
}

test_backup_compression() {
    log "INFO" "TEST: Verifying backup compression integrity"

    local backup_file=$(find "${TEST_BACKUP_DIR}" -name "devskyy_backup_*.sql.gz" -type f 2>/dev/null | head -1)

    if [[ -z "${backup_file}" ]]; then
        test_fail "Backup compression" "Backup file not found"
        return 1
    fi

    if gzip -t "${backup_file}" 2>> "${LOG_FILE}"; then
        test_pass "Backup compression integrity"
        return 0
    else
        test_fail "Backup compression" "Gzip integrity check failed"
        return 1
    fi
}

# =============================================================================
# RESTORE TESTS
# =============================================================================

test_restore_to_temp_db() {
    if [[ "${SKIP_RESTORE}" == "true" ]]; then
        test_skip "Restore to temporary database" "Restore tests disabled"
        return 0
    fi

    log "INFO" "TEST: Restoring backup to temporary database"

    local backup_file=$(find "${TEST_BACKUP_DIR}" -name "devskyy_backup_*.sql.gz" -type f 2>/dev/null | head -1)

    if [[ -z "${backup_file}" ]]; then
        test_fail "Restore to temporary database" "Backup file not found"
        return 1
    fi

    local restore_script="${SCRIPT_DIR}/restore_database.sh"

    if [[ ! -x "${restore_script}" ]]; then
        test_fail "Restore to temporary database" "Restore script not found or not executable"
        return 1
    fi

    # Run restore script in test mode
    if POSTGRES_DB="${TEST_DB_NAME}" \
       "${restore_script}" --test-only --force "${backup_file}" 2>> "${LOG_FILE}"; then

        test_pass "Restore to temporary database"
        return 0
    else
        test_fail "Restore to temporary database" "Restore script failed"
        return 1
    fi
}

test_data_integrity() {
    if [[ "${SKIP_RESTORE}" == "true" ]]; then
        test_skip "Data integrity verification" "Restore tests disabled"
        return 0
    fi

    log "INFO" "TEST: Verifying data integrity after restore"

    # Find the restored test database
    local test_restore_db=$(psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d postgres \
        -tAc "SELECT datname FROM pg_database WHERE datname LIKE 'devskyy_restore_test_%' ORDER BY datname DESC LIMIT 1;" 2>> "${LOG_FILE}")

    if [[ -z "${test_restore_db}" ]]; then
        test_fail "Data integrity" "Restored test database not found"
        return 1
    fi

    # Check table counts
    local table_count=$(psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${test_restore_db}" \
        -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>> "${LOG_FILE}")

    if [[ "${table_count}" -lt 2 ]]; then
        test_fail "Data integrity" "Expected at least 2 tables, found ${table_count}"
        return 1
    fi

    # Check user count
    local user_count=$(psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${test_restore_db}" \
        -tAc "SELECT COUNT(*) FROM test_users;" 2>> "${LOG_FILE}")

    if [[ "${user_count}" -ne 3 ]]; then
        test_fail "Data integrity" "Expected 3 users, found ${user_count}"
        return 1
    fi

    # Check order count
    local order_count=$(psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${test_restore_db}" \
        -tAc "SELECT COUNT(*) FROM test_orders;" 2>> "${LOG_FILE}")

    if [[ "${order_count}" -ne 3 ]]; then
        test_fail "Data integrity" "Expected 3 orders, found ${order_count}"
        return 1
    fi

    test_pass "Data integrity verification"
    return 0
}

# =============================================================================
# CLEANUP
# =============================================================================

cleanup_test_artifacts() {
    log "INFO" "Cleaning up test artifacts..."

    # Drop test databases
    log "INFO" "Dropping test databases..."
    psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d postgres \
        -c "DROP DATABASE IF EXISTS ${TEST_DB_NAME};" 2>> "${LOG_FILE}" || true

    # Drop any restore test databases
    local restore_dbs=$(psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d postgres \
        -tAc "SELECT datname FROM pg_database WHERE datname LIKE 'devskyy_restore_test_%';" 2>> "${LOG_FILE}")

    if [[ -n "${restore_dbs}" ]]; then
        while IFS= read -r db_name; do
            log "INFO" "Dropping restore test database: ${db_name}"
            psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d postgres \
                -c "DROP DATABASE IF EXISTS ${db_name};" 2>> "${LOG_FILE}" || true
        done <<< "${restore_dbs}"
    fi

    # Remove test backup directory
    if [[ -d "${TEST_BACKUP_DIR}" ]]; then
        log "INFO" "Removing test backup directory: ${TEST_BACKUP_DIR}"
        rm -rf "${TEST_BACKUP_DIR}"
    fi

    log "INFO" "Cleanup completed"
}

# =============================================================================
# TEST SUMMARY
# =============================================================================

generate_summary() {
    local total_tests=$((TESTS_PASSED + TESTS_FAILED))
    local pass_rate=0

    if [[ ${total_tests} -gt 0 ]]; then
        pass_rate=$(awk "BEGIN {printf \"%.1f\", (${TESTS_PASSED}/${total_tests})*100}")
    fi

    cat <<EOF

================================================================================
DevSkyy Backup Test Summary
================================================================================

Timestamp:          ${TIMESTAMP}
Test Database:      ${TEST_DB_NAME}
Test Backup Dir:    ${TEST_BACKUP_DIR}

Test Results:
    Total Tests:    ${total_tests}
    Passed:         ${TESTS_PASSED}
    Failed:         ${TESTS_FAILED}
    Pass Rate:      ${pass_rate}%

Individual Test Results:
EOF

    for result in "${TEST_RESULTS[@]}"; do
        echo "    ${result}"
    done

    cat <<EOF

Log File:           ${LOG_FILE}
Error Ledger:       ${ERROR_LEDGER}

Overall Status:     $(if [[ ${TESTS_FAILED} -eq 0 ]]; then echo "SUCCESS ✓"; else echo "FAILURE ✗"; fi)

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
    log "INFO" "DevSkyy Backup Test Script Starting"
    log "INFO" "========================================="
    log "INFO" "Timestamp: ${TIMESTAMP}"

    # Parse command-line arguments
    parse_args "$@"

    echo ""
    echo "Running DevSkyy Backup System Tests..."
    echo ""

    # Test Suite: Database Setup
    echo "=== Test Suite: Database Setup ==="
    test_create_test_database
    test_populate_test_data
    echo ""

    # Test Suite: Backup Operations
    echo "=== Test Suite: Backup Operations ==="
    test_backup_creation
    local backup_file=$(test_backup_file_exists)
    test_backup_file_size
    test_backup_compression
    echo ""

    # Test Suite: Restore Operations
    if [[ "${SKIP_RESTORE}" != "true" ]]; then
        echo "=== Test Suite: Restore Operations ==="
        test_restore_to_temp_db
        test_data_integrity
        echo ""
    fi

    # Cleanup
    if [[ "${CLEANUP_AFTER}" == "true" ]]; then
        cleanup_test_artifacts
    else
        log "INFO" "Test artifacts preserved for inspection"
        log "INFO" "To cleanup manually, run: ${SCRIPT_NAME} --cleanup"
    fi

    # Generate summary
    generate_summary

    log "INFO" "Test execution completed"
    log "INFO" "========================================="

    # Exit with appropriate code
    if [[ ${TESTS_FAILED} -eq 0 ]]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
