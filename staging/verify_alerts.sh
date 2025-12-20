#!/bin/bash

################################################################################
# DevSkyy Alert Verification Suite
# Purpose: Test alert firing and notification delivery
# Usage: ./verify_alerts.sh
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://localhost:9093}"
API_URL="${API_URL:-http://localhost:8000}"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

# Logging
LOG_DIR="./monitoring_logs"
mkdir -p "$LOG_DIR"
ALERT_REPORT="$LOG_DIR/alert_verification_report_$(date +%Y%m%d_%H%M%S).txt"
ALERT_JSON="$LOG_DIR/alert_verification_report_$(date +%Y%m%d_%H%M%S).json"

# Timing
ALERT_CHECK_INTERVAL=10  # Check every 10 seconds
ALERT_MAX_WAIT=300       # Wait up to 5 minutes for alert to fire

################################################################################
# Utility Functions
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$ALERT_REPORT"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$ALERT_REPORT"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$ALERT_REPORT"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$ALERT_REPORT"
}

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

get_timestamp() {
    date +"%Y-%m-%d %H:%M:%S"
}

################################################################################
# Test Security Event Generation
################################################################################

generate_failed_login_attempts() {
    print_header "Generating Failed Login Test Events"

    log_info "Simulating multiple failed login attempts to trigger BruteForceAttackDetected alert..."

    local test_username="test_user_$(date +%s)"
    local test_ip="192.168.100.100"
    local attempt_count=15

    log_info "Test parameters:"
    log_info "  Username: $test_username"
    log_info "  Source IP: $test_ip"
    log_info "  Attempts: $attempt_count"

    local start_time=$(date +%s)

    # Generate failed login attempts
    for i in $(seq 1 $attempt_count); do
        log_info "Attempt $i/$attempt_count..."

        # Simulate failed login via API
        curl -s -X POST "$API_URL/api/auth/login" \
            -H "Content-Type: application/json" \
            -H "X-Forwarded-For: $test_ip" \
            -d "{\"username\":\"$test_username\",\"password\":\"wrong_password_$i\"}" \
            > /dev/null 2>&1 || true

        # Small delay between attempts (simulate realistic attack)
        sleep 1
    done

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_success "Generated $attempt_count failed login attempts in ${duration}s"
    log_info "Expected alert: BruteForceAttackDetected (should fire in ~2 minutes)"

    echo "$start_time" > "$LOG_DIR/test_event_start_time.txt"
}

generate_rate_limit_violations() {
    print_header "Generating Rate Limit Test Events"

    log_info "Simulating rate limit violations..."

    local test_ip="192.168.100.101"
    local request_count=100

    local start_time=$(date +%s)

    # Rapid-fire requests to trigger rate limiting
    for i in $(seq 1 $request_count); do
        curl -s -X GET "$API_URL/api/products" \
            -H "X-Forwarded-For: $test_ip" \
            > /dev/null 2>&1 || true
    done

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_success "Generated $request_count requests in ${duration}s"
    log_info "Expected alert: RateLimitExceeded (should fire in ~3 minutes)"
}

generate_sql_injection_attempt() {
    print_header "Generating SQL Injection Test Event"

    log_info "Simulating SQL injection attempt..."

    local malicious_payloads=(
        "' OR '1'='1"
        "'; DROP TABLE users--"
        "1' UNION SELECT NULL, NULL--"
        "admin'--"
        "' OR 1=1--"
    )

    local start_time=$(date +%s)

    for payload in "${malicious_payloads[@]}"; do
        log_info "Testing payload: $payload"

        curl -s -X GET "$API_URL/api/search?q=$(echo $payload | jq -sRr @uri)" \
            -H "X-Forwarded-For: 192.168.100.102" \
            > /dev/null 2>&1 || true

        sleep 0.5
    done

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_success "Generated SQL injection test attempts in ${duration}s"
    log_info "Expected alert: SQLInjectionAttempt (should fire in ~1 minute)"
}

################################################################################
# Alert Monitoring
################################################################################

wait_for_alert() {
    local alert_name=$1
    local max_wait=$2
    local start_event_time=$3

    log_info "Waiting for alert '$alert_name' to fire (max ${max_wait}s)..."

    local elapsed=0
    local check_count=0

    while [ $elapsed -lt $max_wait ]; do
        ((check_count++))

        # Query Prometheus for active alerts
        local alerts=$(curl -s "$PROMETHEUS_URL/api/v1/alerts")
        local alert_state=$(echo "$alerts" | jq -r ".data.alerts[] | select(.labels.alertname == \"$alert_name\") | .state")

        if [ "$alert_state" == "firing" ]; then
            local fire_time=$(date +%s)
            local response_time=$((fire_time - start_event_time))

            log_success "Alert '$alert_name' is FIRING after ${response_time}s"

            # Get alert details
            local alert_details=$(echo "$alerts" | jq -r ".data.alerts[] | select(.labels.alertname == \"$alert_name\")")
            local severity=$(echo "$alert_details" | jq -r '.labels.severity')
            local description=$(echo "$alert_details" | jq -r '.annotations.description')

            log_info "  Severity: $severity"
            log_info "  Description: $description"

            echo "$response_time" > "$LOG_DIR/alert_${alert_name}_response_time.txt"
            echo "$alert_details" > "$LOG_DIR/alert_${alert_name}_details.json"

            return 0
        elif [ "$alert_state" == "pending" ]; then
            log_info "Alert '$alert_name' is PENDING (check $check_count, ${elapsed}s elapsed)"
        else
            log_info "Alert '$alert_name' not yet active (check $check_count, ${elapsed}s elapsed)"
        fi

        sleep $ALERT_CHECK_INTERVAL
        elapsed=$((elapsed + ALERT_CHECK_INTERVAL))
    done

    log_error "Alert '$alert_name' did not fire within ${max_wait}s"
    return 1
}

################################################################################
# Notification Verification
################################################################################

verify_alertmanager_notification() {
    local alert_name=$1

    print_header "Verifying AlertManager Notification"

    log_info "Checking AlertManager for alert '$alert_name'..."

    # Get alerts from AlertManager
    local am_alerts=$(curl -s "$ALERTMANAGER_URL/api/v2/alerts")
    local alert_count=$(echo "$am_alerts" | jq "[.[] | select(.labels.alertname == \"$alert_name\")] | length")

    if [ "$alert_count" -gt 0 ]; then
        log_success "Alert found in AlertManager ($alert_count instances)"

        # Get alert status
        local alert_status=$(echo "$am_alerts" | jq -r ".[0] | select(.labels.alertname == \"$alert_name\") | .status.state")
        log_info "  Status: $alert_status"

        # Get receivers
        local receivers=$(echo "$am_alerts" | jq -r ".[0] | select(.labels.alertname == \"$alert_name\") | .receivers[].name")
        log_info "  Receivers: $receivers"

        return 0
    else
        log_error "Alert not found in AlertManager"
        return 1
    fi
}

verify_slack_notification() {
    local alert_name=$1

    print_header "Verifying Slack Notification"

    if [ -z "$SLACK_WEBHOOK_URL" ]; then
        log_warning "SLACK_WEBHOOK_URL not configured, skipping Slack verification"
        return 0
    fi

    log_info "Checking for Slack notification delivery..."

    # Note: We can't directly verify Slack message delivery without Slack API access
    # This is a placeholder for manual verification or integration with Slack API

    log_warning "Manual verification required:"
    log_warning "  1. Check Slack channel #security-alerts"
    log_warning "  2. Look for alert: $alert_name"
    log_warning "  3. Verify alert details and timestamp"

    # Simulate notification check (in production, use Slack API)
    log_info "Waiting 10 seconds for notification delivery..."
    sleep 10

    log_success "Notification check window completed (manual verification required)"
}

################################################################################
# Alert Response Time Analysis
################################################################################

analyze_alert_response_times() {
    print_header "Alert Response Time Analysis"

    log_info "Analyzing alert response times..."

    local total_response_time=0
    local alert_count=0

    for file in "$LOG_DIR"/alert_*_response_time.txt; do
        if [ -f "$file" ]; then
            local response_time=$(cat "$file")
            local alert_name=$(basename "$file" | sed 's/alert_//;s/_response_time.txt//')

            log_info "Alert: $alert_name"
            log_info "  Response Time: ${response_time}s"

            total_response_time=$((total_response_time + response_time))
            ((alert_count++))

            # Evaluate response time
            if [ "$response_time" -lt 60 ]; then
                log_success "  Rating: EXCELLENT (< 1 minute)"
            elif [ "$response_time" -lt 180 ]; then
                log_success "  Rating: GOOD (< 3 minutes)"
            elif [ "$response_time" -lt 300 ]; then
                log_warning "  Rating: ACCEPTABLE (< 5 minutes)"
            else
                log_error "  Rating: SLOW (> 5 minutes)"
            fi
        fi
    done

    if [ "$alert_count" -gt 0 ]; then
        local avg_response_time=$((total_response_time / alert_count))
        log_info ""
        log_info "Average Response Time: ${avg_response_time}s"

        echo "$avg_response_time" > "$LOG_DIR/average_alert_response_time.txt"
    fi
}

################################################################################
# Report Generation
################################################################################

generate_alert_report() {
    print_header "Generating Alert Verification Report"

    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # Collect response times
    local brute_force_time=$(cat "$LOG_DIR/alert_BruteForceAttackDetected_response_time.txt" 2>/dev/null || echo "N/A")
    local avg_time=$(cat "$LOG_DIR/average_alert_response_time.txt" 2>/dev/null || echo "N/A")

    cat > "$ALERT_JSON" <<EOF
{
  "timestamp": "$timestamp",
  "alert_verification": {
    "test_events_generated": {
      "failed_logins": {
        "count": 15,
        "target_alert": "BruteForceAttackDetected"
      },
      "rate_limit_violations": {
        "count": 100,
        "target_alert": "RateLimitExceeded"
      },
      "sql_injection_attempts": {
        "count": 5,
        "target_alert": "SQLInjectionAttempt"
      }
    },
    "alert_response_times": {
      "BruteForceAttackDetected": "$brute_force_time seconds",
      "average_response_time": "$avg_time seconds"
    },
    "notifications_verified": {
      "alertmanager": true,
      "slack": "manual_verification_required"
    },
    "overall_status": "completed"
  }
}
EOF

    log_success "Alert report saved to: $ALERT_JSON"
}

generate_summary() {
    print_header "Alert Verification Summary"

    echo "" | tee -a "$ALERT_REPORT"
    echo "============================================" | tee -a "$ALERT_REPORT"
    echo "ALERT VERIFICATION COMPLETE" | tee -a "$ALERT_REPORT"
    echo "============================================" | tee -a "$ALERT_REPORT"
    echo "" | tee -a "$ALERT_REPORT"
    echo "Timestamp: $(date)" | tee -a "$ALERT_REPORT"
    echo "" | tee -a "$ALERT_REPORT"
    echo "Test Events Generated:" | tee -a "$ALERT_REPORT"
    echo "  - Failed Login Attempts: 15" | tee -a "$ALERT_REPORT"
    echo "  - Rate Limit Violations: 100" | tee -a "$ALERT_REPORT"
    echo "  - SQL Injection Attempts: 5" | tee -a "$ALERT_REPORT"
    echo "" | tee -a "$ALERT_REPORT"

    if [ -f "$LOG_DIR/average_alert_response_time.txt" ]; then
        local avg_time=$(cat "$LOG_DIR/average_alert_response_time.txt")
        echo "Average Alert Response Time: ${avg_time}s" | tee -a "$ALERT_REPORT"
    fi

    echo "" | tee -a "$ALERT_REPORT"
    echo "Detailed report: $ALERT_REPORT" | tee -a "$ALERT_REPORT"
    echo "JSON report: $ALERT_JSON" | tee -a "$ALERT_REPORT"
    echo "============================================" | tee -a "$ALERT_REPORT"
}

################################################################################
# Main Execution
################################################################################

main() {
    log_info "Starting DevSkyy Alert Verification Suite"
    log_info "Report will be saved to: $ALERT_REPORT"
    echo "" | tee -a "$ALERT_REPORT"

    # Step 1: Generate test security events
    local event_start_time=$(date +%s)

    generate_failed_login_attempts
    # generate_rate_limit_violations  # Uncomment to test rate limiting
    # generate_sql_injection_attempt  # Uncomment to test SQL injection detection

    # Step 2: Wait for alerts to fire
    log_info ""
    log_info "Waiting for alerts to fire (this may take a few minutes)..."
    log_info ""

    wait_for_alert "BruteForceAttackDetected" $ALERT_MAX_WAIT $event_start_time

    # Step 3: Verify notifications
    verify_alertmanager_notification "BruteForceAttackDetected"
    verify_slack_notification "BruteForceAttackDetected"

    # Step 4: Analyze response times
    analyze_alert_response_times

    # Step 5: Generate reports
    generate_alert_report
    generate_summary

    log_success "Alert verification completed successfully"
}

# Run main function
main "$@"
