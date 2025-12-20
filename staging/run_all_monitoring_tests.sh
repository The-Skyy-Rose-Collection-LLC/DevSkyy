#!/bin/bash

################################################################################
# DevSkyy Complete Monitoring Verification Suite Runner
# Purpose: Run all monitoring verification tests in sequence
# Usage: ./run_all_monitoring_tests.sh
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/monitoring_logs"
mkdir -p "$LOG_DIR"

MASTER_REPORT="$LOG_DIR/master_monitoring_report_$(date +%Y%m%d_%H%M%S).txt"
MASTER_JSON="$LOG_DIR/master_monitoring_report_$(date +%Y%m%d_%H%M%S).json"

# Test results
declare -A TEST_RESULTS
declare -A TEST_DURATIONS

################################################################################
# Utility Functions
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$MASTER_REPORT"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$MASTER_REPORT"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$MASTER_REPORT"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$MASTER_REPORT"
}

print_banner() {
    echo -e "\n${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  $1"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}\n"
}

print_header() {
    echo -e "\n${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}  $1${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

format_duration() {
    local seconds=$1
    local minutes=$((seconds / 60))
    local remaining_seconds=$((seconds % 60))

    if [ $minutes -gt 0 ]; then
        echo "${minutes}m ${remaining_seconds}s"
    else
        echo "${remaining_seconds}s"
    fi
}

run_test() {
    local test_name=$1
    local test_command=$2
    local required=$3  # "required" or "optional"

    print_header "$test_name"

    log_info "Starting test: $test_name"
    log_info "Command: $test_command"

    local start_time=$(date +%s)

    # Run the test
    if eval "$test_command"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        TEST_RESULTS["$test_name"]="PASSED"
        TEST_DURATIONS["$test_name"]=$duration

        log_success "$test_name completed in $(format_duration $duration)"
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        TEST_RESULTS["$test_name"]="FAILED"
        TEST_DURATIONS["$test_name"]=$duration

        log_error "$test_name failed after $(format_duration $duration)"

        if [ "$required" == "required" ]; then
            log_error "This is a required test. Stopping test suite."
            return 1
        else
            log_warning "This is an optional test. Continuing with remaining tests."
            return 0
        fi
    fi
}

################################################################################
# Test Execution
################################################################################

run_monitoring_verification() {
    run_test \
        "Monitoring Health Verification" \
        "bash $SCRIPT_DIR/monitoring_verification.sh" \
        "required"
}

run_security_metrics_verification() {
    run_test \
        "Security Metrics Verification" \
        "python3 $SCRIPT_DIR/verify_security_metrics.py" \
        "required"
}

run_grafana_verification() {
    run_test \
        "Grafana Dashboards Verification" \
        "python3 $SCRIPT_DIR/verify_grafana_dashboards.py" \
        "optional"
}

run_alert_verification() {
    run_test \
        "Alert System Verification" \
        "bash $SCRIPT_DIR/verify_alerts.sh" \
        "optional"
}

run_performance_baseline() {
    log_info "Performance baseline collection takes 30 minutes by default"
    log_info "Skipping in quick test mode. Run separately for full baseline."
    log_warning "To collect performance baseline, run: ./monitoring_performance_baseline.sh"

    TEST_RESULTS["Performance Baseline Collection"]="SKIPPED"
    TEST_DURATIONS["Performance Baseline Collection"]=0
}

################################################################################
# Report Generation
################################################################################

generate_master_report() {
    print_header "Generating Master Report"

    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local total_tests=${#TEST_RESULTS[@]}
    local passed_tests=0
    local failed_tests=0
    local skipped_tests=0

    for test in "${!TEST_RESULTS[@]}"; do
        case "${TEST_RESULTS[$test]}" in
            PASSED)
                ((passed_tests++))
                ;;
            FAILED)
                ((failed_tests++))
                ;;
            SKIPPED)
                ((skipped_tests++))
                ;;
        esac
    done

    # Generate JSON report
    cat > "$MASTER_JSON" <<EOF
{
  "timestamp": "$timestamp",
  "test_suite": "DevSkyy Monitoring Verification Suite",
  "summary": {
    "total_tests": $total_tests,
    "passed": $passed_tests,
    "failed": $failed_tests,
    "skipped": $skipped_tests,
    "pass_rate": $(echo "scale=2; $passed_tests * 100 / ($total_tests - $skipped_tests)" | bc)
  },
  "test_results": {
EOF

    local first=true
    for test in "${!TEST_RESULTS[@]}"; do
        if [ "$first" = false ]; then
            echo "," >> "$MASTER_JSON"
        fi
        first=false

        cat >> "$MASTER_JSON" <<EOF
    "$test": {
      "status": "${TEST_RESULTS[$test]}",
      "duration_seconds": ${TEST_DURATIONS[$test]}
    }
EOF
    done

    cat >> "$MASTER_JSON" <<EOF

  },
  "reports_location": "$LOG_DIR"
}
EOF

    log_success "Master JSON report saved to: $MASTER_JSON"
}

print_summary() {
    print_banner "DevSkyy Monitoring Verification Suite - Summary"

    echo "" | tee -a "$MASTER_REPORT"
    echo "╔════════════════════════════════════════════════════════════╗" | tee -a "$MASTER_REPORT"
    echo "║          MONITORING VERIFICATION SUITE COMPLETE            ║" | tee -a "$MASTER_REPORT"
    echo "╚════════════════════════════════════════════════════════════╝" | tee -a "$MASTER_REPORT"
    echo "" | tee -a "$MASTER_REPORT"

    echo "Timestamp: $(date)" | tee -a "$MASTER_REPORT"
    echo "" | tee -a "$MASTER_REPORT"

    # Calculate totals
    local total_tests=${#TEST_RESULTS[@]}
    local passed_tests=0
    local failed_tests=0
    local skipped_tests=0
    local total_duration=0

    for test in "${!TEST_RESULTS[@]}"; do
        case "${TEST_RESULTS[$test]}" in
            PASSED)
                ((passed_tests++))
                ;;
            FAILED)
                ((failed_tests++))
                ;;
            SKIPPED)
                ((skipped_tests++))
                ;;
        esac
        total_duration=$((total_duration + ${TEST_DURATIONS[$test]}))
    done

    local effective_tests=$((total_tests - skipped_tests))
    local pass_rate=0
    if [ $effective_tests -gt 0 ]; then
        pass_rate=$(echo "scale=2; $passed_tests * 100 / $effective_tests" | bc)
    fi

    echo "Test Summary:" | tee -a "$MASTER_REPORT"
    echo "─────────────────────────────────────────────────────────────" | tee -a "$MASTER_REPORT"
    echo "  Total Tests:    $total_tests" | tee -a "$MASTER_REPORT"
    echo "  Passed:         $passed_tests" | tee -a "$MASTER_REPORT"
    echo "  Failed:         $failed_tests" | tee -a "$MASTER_REPORT"
    echo "  Skipped:        $skipped_tests" | tee -a "$MASTER_REPORT"
    echo "  Pass Rate:      ${pass_rate}%" | tee -a "$MASTER_REPORT"
    echo "  Total Duration: $(format_duration $total_duration)" | tee -a "$MASTER_REPORT"
    echo "" | tee -a "$MASTER_REPORT"

    echo "Detailed Results:" | tee -a "$MASTER_REPORT"
    echo "─────────────────────────────────────────────────────────────" | tee -a "$MASTER_REPORT"

    for test in "${!TEST_RESULTS[@]}"; do
        local status="${TEST_RESULTS[$test]}"
        local duration=$(format_duration ${TEST_DURATIONS[$test]})

        local status_symbol
        local status_color
        case "$status" in
            PASSED)
                status_symbol="✓"
                status_color="${GREEN}"
                ;;
            FAILED)
                status_symbol="✗"
                status_color="${RED}"
                ;;
            SKIPPED)
                status_symbol="⊘"
                status_color="${YELLOW}"
                ;;
        esac

        printf "  ${status_color}${status_symbol}${NC} %-45s ${status_color}%-8s${NC} (%s)\n" \
            "$test" "$status" "$duration" | tee -a "$MASTER_REPORT"
    done

    echo "" | tee -a "$MASTER_REPORT"
    echo "Reports Location:" | tee -a "$MASTER_REPORT"
    echo "─────────────────────────────────────────────────────────────" | tee -a "$MASTER_REPORT"
    echo "  Master Report: $MASTER_REPORT" | tee -a "$MASTER_REPORT"
    echo "  Master JSON:   $MASTER_JSON" | tee -a "$MASTER_REPORT"
    echo "  All Logs:      $LOG_DIR/" | tee -a "$MASTER_REPORT"
    echo "" | tee -a "$MASTER_REPORT"

    # Overall status
    if [ $failed_tests -eq 0 ]; then
        echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}" | tee -a "$MASTER_REPORT"
        echo -e "${GREEN}║                 ALL TESTS PASSED ✓                         ║${NC}" | tee -a "$MASTER_REPORT"
        echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}" | tee -a "$MASTER_REPORT"
    else
        echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}" | tee -a "$MASTER_REPORT"
        echo -e "${RED}║              SOME TESTS FAILED ✗                           ║${NC}" | tee -a "$MASTER_REPORT"
        echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}" | tee -a "$MASTER_REPORT"
    fi

    echo "" | tee -a "$MASTER_REPORT"
}

################################################################################
# Main Execution
################################################################################

main() {
    print_banner "DevSkyy Monitoring Verification Suite"

    log_info "Starting comprehensive monitoring verification"
    log_info "Logs directory: $LOG_DIR"
    echo ""

    # Check prerequisites
    print_header "Checking Prerequisites"

    log_info "Checking for required tools..."

    if ! command -v curl &> /dev/null; then
        log_error "curl is not installed"
        exit 1
    fi
    log_success "curl is available"

    if ! command -v jq &> /dev/null; then
        log_error "jq is not installed"
        exit 1
    fi
    log_success "jq is available"

    if ! command -v python3 &> /dev/null; then
        log_error "python3 is not installed"
        exit 1
    fi
    log_success "python3 is available"

    if ! command -v bc &> /dev/null; then
        log_error "bc is not installed"
        exit 1
    fi
    log_success "bc is available"

    echo ""

    # Run test suite
    local suite_start=$(date +%s)

    run_monitoring_verification || exit 1
    run_security_metrics_verification || exit 1
    run_grafana_verification
    run_alert_verification
    run_performance_baseline

    local suite_end=$(date +%s)
    local suite_duration=$((suite_end - suite_start))

    log_info "Test suite completed in $(format_duration $suite_duration)"

    # Generate reports
    generate_master_report
    print_summary

    # Exit with appropriate code
    if [ ${TEST_RESULTS["Monitoring Health Verification"]} != "PASSED" ] || \
       [ ${TEST_RESULTS["Security Metrics Verification"]} != "PASSED" ]; then
        exit 1
    fi

    exit 0
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n\n${YELLOW}Test suite interrupted by user${NC}\n"; exit 130' INT

# Run main function
main "$@"
