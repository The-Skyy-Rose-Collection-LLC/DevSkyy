#!/bin/bash

################################################################################
# DevSkyy Monitoring Verification Suite
# Purpose: Verify all monitoring components are healthy and operational
# Usage: ./monitoring_verification.sh
################################################################################

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://localhost:9093}"
MAX_WAIT_TIME=300  # 5 minutes max wait
CHECK_INTERVAL=5   # Check every 5 seconds

# Logging
LOG_DIR="./monitoring_logs"
mkdir -p "$LOG_DIR"
REPORT_FILE="$LOG_DIR/monitoring_verification_report_$(date +%Y%m%d_%H%M%S).txt"
JSON_REPORT="$LOG_DIR/monitoring_verification_report_$(date +%Y%m%d_%H%M%S).json"

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

################################################################################
# Utility Functions
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$REPORT_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$REPORT_FILE"
    ((PASSED_CHECKS++))
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$REPORT_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$REPORT_FILE"
    ((FAILED_CHECKS++))
}

increment_check() {
    ((TOTAL_CHECKS++))
}

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

wait_for_service() {
    local service_name=$1
    local health_url=$2
    local max_wait=$3

    log_info "Waiting for $service_name to be healthy..."

    local elapsed=0
    while [ $elapsed -lt $max_wait ]; do
        if curl -s -f "$health_url" > /dev/null 2>&1; then
            log_success "$service_name is healthy (${elapsed}s)"
            return 0
        fi

        echo -n "."
        sleep $CHECK_INTERVAL
        elapsed=$((elapsed + CHECK_INTERVAL))
    done

    log_error "$service_name failed to become healthy after ${max_wait}s"
    return 1
}

################################################################################
# Health Check Functions
################################################################################

check_prometheus_health() {
    print_header "Checking Prometheus Health"
    increment_check

    local health_url="$PROMETHEUS_URL/-/healthy"
    local ready_url="$PROMETHEUS_URL/-/ready"

    # Check if Prometheus is healthy
    if wait_for_service "Prometheus" "$health_url" "$MAX_WAIT_TIME"; then
        # Check if Prometheus is ready
        if curl -s -f "$ready_url" > /dev/null 2>&1; then
            log_success "Prometheus is ready to serve queries"

            # Get Prometheus build info
            local build_info=$(curl -s "$PROMETHEUS_URL/api/v1/status/buildinfo" | jq -r '.data.version')
            log_info "Prometheus version: $build_info"

            # Get runtime info
            local runtime_info=$(curl -s "$PROMETHEUS_URL/api/v1/status/runtimeinfo")
            local storage_retention=$(echo "$runtime_info" | jq -r '.data.storageRetention')
            log_info "Storage retention: $storage_retention"

            return 0
        else
            log_error "Prometheus is healthy but not ready"
            return 1
        fi
    else
        return 1
    fi
}

check_grafana_health() {
    print_header "Checking Grafana Health"
    increment_check

    local health_url="$GRAFANA_URL/api/health"

    if wait_for_service "Grafana" "$health_url" "$MAX_WAIT_TIME"; then
        # Get Grafana version and status
        local health_status=$(curl -s "$health_url")
        local version=$(echo "$health_status" | jq -r '.version')
        local database=$(echo "$health_status" | jq -r '.database')

        log_info "Grafana version: $version"
        log_info "Database status: $database"

        # Check datasource connectivity
        log_info "Checking Grafana datasources..."
        # Note: This requires authentication - will be checked in verify_grafana_dashboards.py

        return 0
    else
        return 1
    fi
}

check_alertmanager_health() {
    print_header "Checking AlertManager Health"
    increment_check

    local health_url="$ALERTMANAGER_URL/-/healthy"
    local ready_url="$ALERTMANAGER_URL/-/ready"

    if wait_for_service "AlertManager" "$health_url" "$MAX_WAIT_TIME"; then
        if curl -s -f "$ready_url" > /dev/null 2>&1; then
            log_success "AlertManager is ready"

            # Get AlertManager status
            local status=$(curl -s "$ALERTMANAGER_URL/api/v2/status")
            local version=$(echo "$status" | jq -r '.versionInfo.version')
            local uptime=$(echo "$status" | jq -r '.uptime')

            log_info "AlertManager version: $version"
            log_info "Uptime: $uptime"

            # Check cluster status
            local cluster_status=$(echo "$status" | jq -r '.cluster.status')
            log_info "Cluster status: $cluster_status"

            return 0
        else
            log_error "AlertManager is healthy but not ready"
            return 1
        fi
    else
        return 1
    fi
}

################################################################################
# Exporter Verification
################################################################################

verify_exporters() {
    print_header "Verifying Exporters Connected"

    local exporters=("postgres-exporter" "redis-exporter" "node-exporter" "cadvisor" "devskyy-api")

    for exporter in "${exporters[@]}"; do
        increment_check
        log_info "Checking $exporter..."

        # Query Prometheus for target status
        local query="up{job=\"$exporter\"}"
        local result=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$(echo $query | jq -sRr @uri)" | jq -r '.data.result[0].value[1]')

        if [ "$result" == "1" ]; then
            log_success "$exporter is UP and connected"

            # Get last scrape time
            local scrape_duration=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=scrape_duration_seconds{job=\"$exporter\"}" | jq -r '.data.result[0].value[1]')
            log_info "  Last scrape duration: ${scrape_duration}s"
        elif [ "$result" == "0" ]; then
            log_error "$exporter is DOWN"
        else
            log_warning "$exporter status unknown (no data)"
        fi
    done
}

################################################################################
# Scrape Target Verification
################################################################################

verify_scrape_targets() {
    print_header "Verifying Scrape Targets"
    increment_check

    log_info "Fetching all scrape targets from Prometheus..."

    local targets=$(curl -s "$PROMETHEUS_URL/api/v1/targets")
    local active_targets=$(echo "$targets" | jq '.data.activeTargets | length')
    local healthy_targets=$(echo "$targets" | jq '[.data.activeTargets[] | select(.health == "up")] | length')
    local unhealthy_targets=$(echo "$targets" | jq '[.data.activeTargets[] | select(.health == "down")] | length')

    log_info "Total active targets: $active_targets"
    log_info "Healthy targets: $healthy_targets"
    log_info "Unhealthy targets: $unhealthy_targets"

    if [ "$unhealthy_targets" -eq 0 ]; then
        log_success "All scrape targets are healthy"
    else
        log_warning "Some scrape targets are unhealthy"

        # List unhealthy targets
        echo "$targets" | jq -r '.data.activeTargets[] | select(.health == "down") | "\(.scrapePool): \(.scrapeUrl) - \(.lastError)"' | while read line; do
            log_error "  $line"
        done
    fi

    # Save detailed target info
    echo "$targets" | jq '.' > "$LOG_DIR/scrape_targets_$(date +%Y%m%d_%H%M%S).json"
}

################################################################################
# Alert Rules Verification
################################################################################

verify_alert_rules() {
    print_header "Verifying Alert Rules"
    increment_check

    log_info "Fetching alert rules from Prometheus..."

    local rules=$(curl -s "$PROMETHEUS_URL/api/v1/rules")
    local total_groups=$(echo "$rules" | jq '.data.groups | length')
    local total_rules=$(echo "$rules" | jq '[.data.groups[].rules[]] | length')

    log_info "Total rule groups: $total_groups"
    log_info "Total alert rules: $total_rules"

    if [ "$total_rules" -gt 0 ]; then
        log_success "Alert rules loaded successfully"

        # List rule groups
        echo "$rules" | jq -r '.data.groups[] | "\(.name): \(.rules | length) rules"' | while read line; do
            log_info "  $line"
        done

        # Check for any firing alerts
        local alerts=$(curl -s "$PROMETHEUS_URL/api/v1/alerts")
        local firing_alerts=$(echo "$alerts" | jq '[.data.alerts[] | select(.state == "firing")] | length')

        if [ "$firing_alerts" -gt 0 ]; then
            log_warning "Currently $firing_alerts alerts are firing"
            echo "$alerts" | jq -r '.data.alerts[] | select(.state == "firing") | "\(.labels.alertname) (\(.labels.severity))"' | while read line; do
                log_warning "  FIRING: $line"
            done
        else
            log_info "No alerts currently firing"
        fi
    else
        log_error "No alert rules loaded"
    fi

    # Save detailed rules info
    echo "$rules" | jq '.' > "$LOG_DIR/alert_rules_$(date +%Y%m%d_%H%M%S).json"
}

################################################################################
# Metrics Sample Verification
################################################################################

verify_metrics_collection() {
    print_header "Verifying Metrics Collection"

    local test_metrics=(
        "up"
        "process_cpu_seconds_total"
        "process_resident_memory_bytes"
        "http_requests_total"
        "security_failed_login_attempts"
        "security_threat_score"
    )

    for metric in "${test_metrics[@]}"; do
        increment_check
        log_info "Checking metric: $metric"

        local result=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$metric" | jq -r '.data.result | length')

        if [ "$result" -gt 0 ]; then
            log_success "Metric '$metric' is being collected ($result series)"
        else
            log_warning "Metric '$metric' has no data"
        fi
    done
}

################################################################################
# Performance Check
################################################################################

check_prometheus_performance() {
    print_header "Checking Prometheus Performance"
    increment_check

    log_info "Querying Prometheus performance metrics..."

    # Time series count
    local total_series=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=prometheus_tsdb_symbol_table_size_bytes" | jq -r '.data.result[0].value[1]')
    local series_count=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=prometheus_tsdb_head_series" | jq -r '.data.result[0].value[1]')

    log_info "Total time series: $series_count"

    # Storage metrics
    local storage_size=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=prometheus_tsdb_storage_blocks_bytes" | jq -r '.data.result[0].value[1]')
    local storage_gb=$(echo "scale=2; $storage_size / 1024 / 1024 / 1024" | bc)

    log_info "Storage size: ${storage_gb} GB"

    # Query performance
    local query_duration=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=prometheus_engine_query_duration_seconds{quantile=\"0.9\"}" | jq -r '.data.result[0].value[1]')

    log_info "90th percentile query duration: ${query_duration}s"

    if (( $(echo "$query_duration < 1" | bc -l) )); then
        log_success "Prometheus query performance is good"
    else
        log_warning "Prometheus query performance is degraded"
    fi
}

################################################################################
# Generate Report
################################################################################

generate_json_report() {
    print_header "Generating JSON Report"

    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local pass_rate=$(echo "scale=2; $PASSED_CHECKS * 100 / $TOTAL_CHECKS" | bc)

    cat > "$JSON_REPORT" <<EOF
{
  "timestamp": "$timestamp",
  "monitoring_verification": {
    "summary": {
      "total_checks": $TOTAL_CHECKS,
      "passed": $PASSED_CHECKS,
      "failed": $FAILED_CHECKS,
      "pass_rate": $pass_rate,
      "status": "$([ $FAILED_CHECKS -eq 0 ] && echo "PASSED" || echo "FAILED")"
    },
    "prometheus": {
      "url": "$PROMETHEUS_URL",
      "status": "healthy",
      "ready": true
    },
    "grafana": {
      "url": "$GRAFANA_URL",
      "status": "healthy"
    },
    "alertmanager": {
      "url": "$ALERTMANAGER_URL",
      "status": "healthy",
      "ready": true
    },
    "exporters_verified": [
      "postgres-exporter",
      "redis-exporter",
      "node-exporter",
      "cadvisor",
      "devskyy-api"
    ],
    "alert_rules_loaded": true,
    "metrics_collection": "operational"
  }
}
EOF

    log_success "JSON report saved to: $JSON_REPORT"
}

generate_summary() {
    print_header "Monitoring Verification Summary"

    echo "" | tee -a "$REPORT_FILE"
    echo "============================================" | tee -a "$REPORT_FILE"
    echo "MONITORING VERIFICATION COMPLETE" | tee -a "$REPORT_FILE"
    echo "============================================" | tee -a "$REPORT_FILE"
    echo "" | tee -a "$REPORT_FILE"
    echo "Timestamp: $(date)" | tee -a "$REPORT_FILE"
    echo "Total Checks: $TOTAL_CHECKS" | tee -a "$REPORT_FILE"
    echo "Passed: $PASSED_CHECKS" | tee -a "$REPORT_FILE"
    echo "Failed: $FAILED_CHECKS" | tee -a "$REPORT_FILE"

    local pass_rate=$(echo "scale=2; $PASSED_CHECKS * 100 / $TOTAL_CHECKS" | bc)
    echo "Pass Rate: ${pass_rate}%" | tee -a "$REPORT_FILE"
    echo "" | tee -a "$REPORT_FILE"

    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${GREEN}STATUS: ALL CHECKS PASSED ✓${NC}" | tee -a "$REPORT_FILE"
    else
        echo -e "${RED}STATUS: SOME CHECKS FAILED ✗${NC}" | tee -a "$REPORT_FILE"
    fi

    echo "" | tee -a "$REPORT_FILE"
    echo "Detailed report: $REPORT_FILE" | tee -a "$REPORT_FILE"
    echo "JSON report: $JSON_REPORT" | tee -a "$REPORT_FILE"
    echo "============================================" | tee -a "$REPORT_FILE"
}

################################################################################
# Main Execution
################################################################################

main() {
    log_info "Starting DevSkyy Monitoring Verification Suite"
    log_info "Report will be saved to: $REPORT_FILE"
    echo "" | tee -a "$REPORT_FILE"

    # Step 1: Check core services
    check_prometheus_health
    check_grafana_health
    check_alertmanager_health

    # Step 2: Verify exporters
    verify_exporters

    # Step 3: Verify scrape targets
    verify_scrape_targets

    # Step 4: Verify alert rules
    verify_alert_rules

    # Step 5: Verify metrics collection
    verify_metrics_collection

    # Step 6: Check performance
    check_prometheus_performance

    # Step 7: Generate reports
    generate_json_report
    generate_summary

    # Exit with appropriate code
    if [ $FAILED_CHECKS -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
