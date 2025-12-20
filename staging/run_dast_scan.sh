#!/bin/bash
set -euo pipefail

# DAST and Vulnerability Scanning for Staging Environment
# Runs OWASP ZAP and Nuclei scans, collects and categorizes findings

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORTS_DIR="${SCRIPT_DIR}/reports/dast"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
STAGING_URL="${STAGING_URL:-https://staging.skyyrose.com}"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ZAP_PORT="${ZAP_PORT:-8090}"
ZAP_API_KEY="${ZAP_API_KEY:-changeme}"
MAX_SCAN_DURATION="${MAX_SCAN_DURATION:-3600}" # 1 hour max
NUCLEI_TIMEOUT="${NUCLEI_TIMEOUT:-30m}"

# Report files
ZAP_JSON_REPORT="${REPORTS_DIR}/zap_report_${TIMESTAMP}.json"
ZAP_HTML_REPORT="${REPORTS_DIR}/zap_report_${TIMESTAMP}.html"
NUCLEI_JSON_REPORT="${REPORTS_DIR}/nuclei_report_${TIMESTAMP}.json"
COMBINED_REPORT="${REPORTS_DIR}/combined_vulnerability_report_${TIMESTAMP}.json"
SUMMARY_REPORT="${REPORTS_DIR}/vulnerability_summary_${TIMESTAMP}.txt"

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

check_prerequisites() {
    log "Checking prerequisites..."

    local missing_tools=()

    # Check for ZAP
    if ! command -v docker &> /dev/null && ! command -v zap.sh &> /dev/null; then
        missing_tools+=("OWASP ZAP (docker or zap.sh)")
    fi

    # Check for Nuclei
    if ! command -v nuclei &> /dev/null; then
        missing_tools+=("Nuclei")
    fi

    # Check for Python
    if ! command -v python3 &> /dev/null; then
        missing_tools+=("Python3")
    fi

    # Check for jq
    if ! command -v jq &> /dev/null; then
        missing_tools+=("jq")
    fi

    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_error "Missing required tools:"
        for tool in "${missing_tools[@]}"; do
            echo "  - $tool"
        done
        echo ""
        echo "Install instructions:"
        echo "  OWASP ZAP: docker pull owasp/zap2docker-stable"
        echo "  Nuclei:    go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest"
        echo "  jq:        brew install jq (macOS) or apt-get install jq (Linux)"
        exit 1
    fi

    log_success "All prerequisites met"
}

setup_reports_directory() {
    log "Setting up reports directory..."
    mkdir -p "${REPORTS_DIR}"
    mkdir -p "${REPORTS_DIR}/archive"

    # Archive old reports (keep last 30 days)
    find "${REPORTS_DIR}" -name "*.json" -mtime +30 -exec mv {} "${REPORTS_DIR}/archive/" \; 2>/dev/null || true
}

run_zap_scan() {
    log "Starting OWASP ZAP scan on ${STAGING_URL}..."

    # Check if ZAP is already running
    if curl -s "http://localhost:${ZAP_PORT}" > /dev/null 2>&1; then
        log_warning "ZAP appears to be already running on port ${ZAP_PORT}"
        log "Using existing ZAP instance..."
    else
        log "Starting ZAP daemon..."
        if command -v docker &> /dev/null; then
            # Start ZAP in daemon mode using Docker
            docker run -d --name zap-daemon \
                -p "${ZAP_PORT}:${ZAP_PORT}" \
                -e ZAP_PORT="${ZAP_PORT}" \
                owasp/zap2docker-stable \
                zap.sh -daemon -host 0.0.0.0 -port "${ZAP_PORT}" -config api.key="${ZAP_API_KEY}" \
                > /dev/null 2>&1

            # Wait for ZAP to start
            log "Waiting for ZAP to initialize..."
            for i in {1..60}; do
                if curl -s "http://localhost:${ZAP_PORT}" > /dev/null 2>&1; then
                    log_success "ZAP started successfully"
                    break
                fi
                sleep 2
            done
        else
            log_error "Docker not available. Please start ZAP manually."
            return 1
        fi
    fi

    # Spider the application
    log "Spidering application to discover URLs..."
    SPIDER_ID=$(curl -s "http://localhost:${ZAP_PORT}/JSON/spider/action/scan/" \
        --data-urlencode "url=${STAGING_URL}" \
        --data "apikey=${ZAP_API_KEY}" | jq -r '.scan')

    # Wait for spider to complete
    while true; do
        SPIDER_STATUS=$(curl -s "http://localhost:${ZAP_PORT}/JSON/spider/view/status/?scanId=${SPIDER_ID}&apikey=${ZAP_API_KEY}" | jq -r '.status')
        if [ "$SPIDER_STATUS" == "100" ]; then
            log_success "Spidering complete"
            break
        fi
        echo -n "."
        sleep 5
    done
    echo ""

    # Active scan
    log "Starting active scan..."
    SCAN_ID=$(curl -s "http://localhost:${ZAP_PORT}/JSON/ascan/action/scan/" \
        --data-urlencode "url=${STAGING_URL}" \
        --data "apikey=${ZAP_API_KEY}" | jq -r '.scan')

    # Wait for active scan to complete (with timeout)
    local elapsed=0
    while true; do
        SCAN_STATUS=$(curl -s "http://localhost:${ZAP_PORT}/JSON/ascan/view/status/?scanId=${SCAN_ID}&apikey=${ZAP_API_KEY}" | jq -r '.status')
        if [ "$SCAN_STATUS" == "100" ]; then
            log_success "Active scan complete"
            break
        fi

        if [ $elapsed -ge $MAX_SCAN_DURATION ]; then
            log_warning "Scan timeout reached (${MAX_SCAN_DURATION}s), stopping scan..."
            curl -s "http://localhost:${ZAP_PORT}/JSON/ascan/action/stop/?scanId=${SCAN_ID}&apikey=${ZAP_API_KEY}" > /dev/null
            break
        fi

        echo -n "."
        sleep 10
        elapsed=$((elapsed + 10))
    done
    echo ""

    # Generate reports
    log "Generating ZAP reports..."

    # JSON report
    curl -s "http://localhost:${ZAP_PORT}/JSON/core/view/alerts/?baseurl=${STAGING_URL}&apikey=${ZAP_API_KEY}" \
        > "${ZAP_JSON_REPORT}"

    # HTML report
    curl -s "http://localhost:${ZAP_PORT}/OTHER/core/other/htmlreport/?apikey=${ZAP_API_KEY}" \
        > "${ZAP_HTML_REPORT}"

    log_success "ZAP reports saved to:"
    log "  JSON: ${ZAP_JSON_REPORT}"
    log "  HTML: ${ZAP_HTML_REPORT}"

    # Parse and display summary
    local critical=$(jq '[.alerts[] | select(.risk == "High")] | length' "${ZAP_JSON_REPORT}")
    local high=$(jq '[.alerts[] | select(.risk == "Medium")] | length' "${ZAP_JSON_REPORT}")
    local medium=$(jq '[.alerts[] | select(.risk == "Low")] | length' "${ZAP_JSON_REPORT}")
    local low=$(jq '[.alerts[] | select(.risk == "Informational")] | length' "${ZAP_JSON_REPORT}")

    log "ZAP Scan Summary:"
    log "  Critical: ${critical}"
    log "  High:     ${high}"
    log "  Medium:   ${medium}"
    log "  Low:      ${low}"

    # Cleanup ZAP daemon if we started it
    if command -v docker &> /dev/null; then
        docker stop zap-daemon > /dev/null 2>&1 || true
        docker rm zap-daemon > /dev/null 2>&1 || true
    fi
}

run_nuclei_scan() {
    log "Starting Nuclei vulnerability scan on ${STAGING_URL}..."

    # Update Nuclei templates
    log "Updating Nuclei templates..."
    nuclei -update-templates > /dev/null 2>&1 || true

    # Run Nuclei scan
    log "Running Nuclei scan (this may take a while)..."
    nuclei \
        -u "${STAGING_URL}" \
        -timeout "${NUCLEI_TIMEOUT}" \
        -severity critical,high,medium,low,info \
        -json \
        -silent \
        -stats \
        -o "${NUCLEI_JSON_REPORT}" \
        2>&1 | tee /tmp/nuclei_stats.log

    if [ -f "${NUCLEI_JSON_REPORT}" ]; then
        log_success "Nuclei scan complete"
        log "Report saved to: ${NUCLEI_JSON_REPORT}"

        # Parse and display summary
        local critical=$(jq -s '[.[] | select(.info.severity == "critical")] | length' "${NUCLEI_JSON_REPORT}" 2>/dev/null || echo 0)
        local high=$(jq -s '[.[] | select(.info.severity == "high")] | length' "${NUCLEI_JSON_REPORT}" 2>/dev/null || echo 0)
        local medium=$(jq -s '[.[] | select(.info.severity == "medium")] | length' "${NUCLEI_JSON_REPORT}" 2>/dev/null || echo 0)
        local low=$(jq -s '[.[] | select(.info.severity == "low")] | length' "${NUCLEI_JSON_REPORT}" 2>/dev/null || echo 0)
        local info=$(jq -s '[.[] | select(.info.severity == "info")] | length' "${NUCLEI_JSON_REPORT}" 2>/dev/null || echo 0)

        log "Nuclei Scan Summary:"
        log "  Critical: ${critical}"
        log "  High:     ${high}"
        log "  Medium:   ${medium}"
        log "  Low:      ${low}"
        log "  Info:     ${info}"
    else
        log_warning "No Nuclei findings or scan failed"
        echo "[]" > "${NUCLEI_JSON_REPORT}"
    fi
}

parse_and_combine_results() {
    log "Parsing and combining scan results..."

    # Parse ZAP results
    if [ -f "${SCRIPT_DIR}/parse_zap_results.py" ]; then
        log "Parsing ZAP results..."
        python3 "${SCRIPT_DIR}/parse_zap_results.py" \
            "${ZAP_JSON_REPORT}" \
            "${REPORTS_DIR}/zap_parsed_${TIMESTAMP}.json"
    fi

    # Parse Nuclei results
    if [ -f "${SCRIPT_DIR}/parse_nuclei_results.py" ]; then
        log "Parsing Nuclei results..."
        python3 "${SCRIPT_DIR}/parse_nuclei_results.py" \
            "${NUCLEI_JSON_REPORT}" \
            "${REPORTS_DIR}/nuclei_parsed_${TIMESTAMP}.json"
    fi

    # Combine and triage
    if [ -f "${SCRIPT_DIR}/vulnerability_triage.py" ]; then
        log "Running vulnerability triage..."
        python3 "${SCRIPT_DIR}/vulnerability_triage.py" \
            "${REPORTS_DIR}/zap_parsed_${TIMESTAMP}.json" \
            "${REPORTS_DIR}/nuclei_parsed_${TIMESTAMP}.json" \
            "${COMBINED_REPORT}"
    fi
}

compare_with_baseline() {
    log "Comparing results with baseline..."

    local baseline_file="${REPORTS_DIR}/vulnerability_baseline.json"

    if [ -f "${SCRIPT_DIR}/compare_baseline.py" ] && [ -f "${baseline_file}" ]; then
        python3 "${SCRIPT_DIR}/compare_baseline.py" \
            "${COMBINED_REPORT}" \
            "${baseline_file}" \
            "${REPORTS_DIR}/vulnerability_delta_${TIMESTAMP}.json"

        log_success "Baseline comparison complete"
    else
        if [ ! -f "${baseline_file}" ]; then
            log_warning "No baseline file found at ${baseline_file}"
            log "Creating initial baseline from current scan..."
            cp "${COMBINED_REPORT}" "${baseline_file}"
        fi
    fi
}

generate_summary_report() {
    log "Generating summary report..."

    {
        echo "================================="
        echo "DAST VULNERABILITY SCAN SUMMARY"
        echo "================================="
        echo ""
        echo "Scan Date: $(date)"
        echo "Target: ${STAGING_URL}"
        echo "Scan Duration: ${SECONDS} seconds"
        echo ""

        if [ -f "${COMBINED_REPORT}" ]; then
            echo "COMBINED FINDINGS:"
            echo "-----------------"

            local total=$(jq '.statistics.total_vulnerabilities' "${COMBINED_REPORT}" 2>/dev/null || echo "N/A")
            local critical=$(jq '.statistics.by_severity.critical // 0' "${COMBINED_REPORT}" 2>/dev/null || echo "0")
            local high=$(jq '.statistics.by_severity.high // 0' "${COMBINED_REPORT}" 2>/dev/null || echo "0")
            local medium=$(jq '.statistics.by_severity.medium // 0' "${COMBINED_REPORT}" 2>/dev/null || echo "0")
            local low=$(jq '.statistics.by_severity.low // 0' "${COMBINED_REPORT}" 2>/dev/null || echo "0")
            local blockers=$(jq '.blockers | length' "${COMBINED_REPORT}" 2>/dev/null || echo "0")

            echo "Total Vulnerabilities: ${total}"
            echo "  Critical: ${critical}"
            echo "  High:     ${high}"
            echo "  Medium:   ${medium}"
            echo "  Low:      ${low}"
            echo ""
            echo "Production Blockers: ${blockers}"

            if [ "${blockers}" -gt 0 ]; then
                echo ""
                echo "CRITICAL BLOCKERS:"
                jq -r '.blockers[] | "  - [\(.severity)] \(.title)"' "${COMBINED_REPORT}" 2>/dev/null || true
            fi
        fi

        echo ""
        echo "Reports Generated:"
        echo "  ZAP JSON:        ${ZAP_JSON_REPORT}"
        echo "  ZAP HTML:        ${ZAP_HTML_REPORT}"
        echo "  Nuclei JSON:     ${NUCLEI_JSON_REPORT}"
        echo "  Combined Report: ${COMBINED_REPORT}"
        echo "  Summary:         ${SUMMARY_REPORT}"
        echo ""
        echo "================================="

    } | tee "${SUMMARY_REPORT}"
}

check_for_blockers() {
    log "Checking for production blockers..."

    if [ -f "${COMBINED_REPORT}" ]; then
        local blockers=$(jq '.blockers | length' "${COMBINED_REPORT}" 2>/dev/null || echo "0")

        if [ "${blockers}" -gt 0 ]; then
            log_error "Found ${blockers} production blocker(s)!"
            log_error "Review the combined report before proceeding to production"
            return 1
        else
            log_success "No production blockers found"
            return 0
        fi
    else
        log_warning "Combined report not found, cannot determine blockers"
        return 1
    fi
}

main() {
    log "Starting DAST and Vulnerability Scanning"
    log "Target: ${STAGING_URL}"
    echo ""

    check_prerequisites
    setup_reports_directory

    # Run scans in parallel if possible
    if [ "${RUN_PARALLEL:-false}" == "true" ]; then
        log "Running scans in parallel..."
        run_zap_scan &
        ZAP_PID=$!
        run_nuclei_scan &
        NUCLEI_PID=$!

        wait $ZAP_PID
        wait $NUCLEI_PID
    else
        run_zap_scan
        run_nuclei_scan
    fi

    parse_and_combine_results
    compare_with_baseline
    generate_summary_report

    echo ""
    log_success "DAST scanning complete!"
    log "View summary report: ${SUMMARY_REPORT}"
    log "View combined report: ${COMBINED_REPORT}"

    # Check for blockers and exit accordingly
    if check_for_blockers; then
        exit 0
    else
        exit 1
    fi
}

# Execute main function
main "$@"
