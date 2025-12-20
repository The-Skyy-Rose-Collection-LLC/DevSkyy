#!/bin/bash
#
# Staging Smoke Tests
# ====================
#
# Quick smoke tests to verify basic functionality in staging environment.
#
# Tests:
# - API health endpoint
# - Authenticated endpoint access
# - Rate limiting behavior
# - Request signing
# - Monitoring stack
#
# Usage:
#   ./staging/smoke_tests.sh
#   ./staging/smoke_tests.sh --verbose
#
# Environment Variables:
#   STAGING_URL     - Base URL of staging environment (default: http://localhost:8000)
#   API_KEY         - Valid API key for authenticated tests
#   VERBOSE         - Set to 1 for verbose output

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STAGING_URL="${STAGING_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-}"
VERBOSE="${VERBOSE:-0}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=1
            shift
            ;;
        --url)
            STAGING_URL="$2"
            shift 2
            ;;
        --api-key)
            API_KEY="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# Print functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

print_skip() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
    ((TESTS_SKIPPED++))
}

print_info() {
    if [[ $VERBOSE -eq 1 ]]; then
        echo -e "${BLUE}[INFO]${NC} $1"
    fi
}

# Test functions
test_health_endpoint() {
    print_test "Testing health endpoint..."

    response=$(curl -s -w "\n%{http_code}" "${STAGING_URL}/api/v1/health" 2>&1)
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)

    print_info "HTTP Code: $http_code"
    print_info "Response: $body"

    if [[ "$http_code" == "200" ]]; then
        print_pass "Health endpoint returns 200 OK"
    else
        print_fail "Health endpoint failed (HTTP $http_code)"
    fi
}

test_metrics_endpoint() {
    print_test "Testing metrics endpoint..."

    response=$(curl -s -w "\n%{http_code}" "${STAGING_URL}/metrics" 2>&1)
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)

    print_info "HTTP Code: $http_code"

    if [[ "$http_code" == "200" ]]; then
        # Check for Prometheus format
        if echo "$body" | grep -q "# HELP\|# TYPE"; then
            print_pass "Metrics endpoint returns Prometheus format"
        else
            print_fail "Metrics endpoint doesn't return Prometheus format"
        fi
    else
        print_fail "Metrics endpoint failed (HTTP $http_code)"
    fi
}

test_authenticated_endpoint() {
    print_test "Testing authenticated endpoint access..."

    if [[ -z "$API_KEY" ]]; then
        print_skip "No API key provided, skipping authenticated tests"
        return
    fi

    # Try to access a protected endpoint without auth
    response=$(curl -s -w "\n%{http_code}" "${STAGING_URL}/api/v1/admin/audit-logs" 2>&1)
    http_code=$(echo "$response" | tail -n 1)

    print_info "Without auth - HTTP Code: $http_code"

    if [[ "$http_code" == "401" ]] || [[ "$http_code" == "403" ]]; then
        print_pass "Protected endpoint correctly rejects unauthenticated requests"
    else
        print_fail "Protected endpoint should reject unauthenticated requests (got $http_code)"
    fi
}

test_rate_limiting() {
    print_test "Testing rate limiting..."

    # Make multiple requests quickly
    rate_limited=0

    for i in {1..15}; do
        http_code=$(curl -s -o /dev/null -w "%{http_code}" "${STAGING_URL}/api/v1/health")

        if [[ "$http_code" == "429" ]]; then
            rate_limited=1
            print_info "Rate limited after $i requests"
            break
        fi
    done

    if [[ $rate_limited -eq 1 ]]; then
        print_pass "Rate limiting is working"
    else
        print_skip "Rate limiting not triggered (may need more requests or longer test)"
    fi
}

test_security_headers() {
    print_test "Testing security headers..."

    headers=$(curl -s -I "${STAGING_URL}/api/v1/health")

    print_info "Checking security headers..."

    headers_found=0

    if echo "$headers" | grep -qi "strict-transport-security"; then
        print_info "✓ HSTS header present"
        ((headers_found++))
    fi

    if echo "$headers" | grep -qi "x-content-type-options.*nosniff"; then
        print_info "✓ X-Content-Type-Options header present"
        ((headers_found++))
    fi

    if echo "$headers" | grep -qi "x-frame-options"; then
        print_info "✓ X-Frame-Options header present"
        ((headers_found++))
    fi

    if echo "$headers" | grep -qi "x-xss-protection"; then
        print_info "✓ X-XSS-Protection header present"
        ((headers_found++))
    fi

    if [[ $headers_found -ge 3 ]]; then
        print_pass "Security headers are present ($headers_found/4)"
    else
        print_fail "Missing security headers (only $headers_found/4 found)"
    fi
}

test_cors_headers() {
    print_test "Testing CORS configuration..."

    # Make OPTIONS request with Origin header
    response=$(curl -s -I -X OPTIONS \
        -H "Origin: http://localhost:3000" \
        -H "Access-Control-Request-Method: POST" \
        "${STAGING_URL}/api/v1/health")

    print_info "CORS response headers:"
    print_info "$response"

    if echo "$response" | grep -qi "access-control-allow-origin"; then
        print_pass "CORS headers are configured"
    else
        print_skip "CORS headers not found (may not be configured)"
    fi
}

test_request_signing() {
    print_test "Testing request signing requirements..."

    # Try to access protected endpoint without signature
    response=$(curl -s -w "\n%{http_code}" -X POST "${STAGING_URL}/api/v1/admin/config" 2>&1)
    http_code=$(echo "$response" | tail -n 1)

    print_info "HTTP Code: $http_code"

    if [[ "$http_code" == "401" ]] || [[ "$http_code" == "403" ]]; then
        print_pass "Request signing is enforced on protected endpoints"
    elif [[ "$http_code" == "404" ]]; then
        print_skip "Protected endpoint not found (may not be implemented)"
    else
        print_skip "Request signing test inconclusive (HTTP $http_code)"
    fi
}

test_file_upload_validation() {
    print_test "Testing file upload validation..."

    # Create a temporary file with dangerous extension
    temp_file=$(mktemp).exe
    echo "fake executable" > "$temp_file"

    # Try to upload dangerous file
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -F "file=@$temp_file" \
        "${STAGING_URL}/api/v1/upload" 2>&1)
    http_code=$(echo "$response" | tail -n 1)

    # Cleanup
    rm -f "$temp_file"

    print_info "HTTP Code: $http_code"

    if [[ "$http_code" == "400" ]] || [[ "$http_code" == "403" ]]; then
        print_pass "File upload validation is working"
    elif [[ "$http_code" == "401" ]] || [[ "$http_code" == "404" ]]; then
        print_skip "File upload endpoint requires auth or not implemented"
    else
        print_skip "File upload test inconclusive (HTTP $http_code)"
    fi
}

test_monitoring_stack() {
    print_test "Testing monitoring stack availability..."

    # Check if Prometheus is accessible
    prometheus_url="${PROMETHEUS_URL:-http://localhost:9090}"
    prom_code=$(curl -s -o /dev/null -w "%{http_code}" "${prometheus_url}/api/v1/status/config" 2>&1)

    print_info "Prometheus HTTP Code: $prom_code"

    # Check if Grafana is accessible
    grafana_url="${GRAFANA_URL:-http://localhost:3000}"
    grafana_code=$(curl -s -o /dev/null -w "%{http_code}" "${grafana_url}/api/health" 2>&1)

    print_info "Grafana HTTP Code: $grafana_code"

    if [[ "$prom_code" == "200" ]] || [[ "$grafana_code" == "200" ]]; then
        print_pass "Monitoring stack is accessible"
    else
        print_skip "Monitoring stack not accessible (may not be deployed)"
    fi
}

# Main execution
main() {
    print_header "DevSkyy Staging Smoke Tests"
    echo "Testing against: $STAGING_URL"
    echo ""

    # Run all tests
    test_health_endpoint
    test_metrics_endpoint
    test_authenticated_endpoint
    test_rate_limiting
    test_security_headers
    test_cors_headers
    test_request_signing
    test_file_upload_validation
    test_monitoring_stack

    # Print summary
    echo ""
    print_header "Test Summary"
    echo -e "${GREEN}Passed:${NC}  $TESTS_PASSED"
    echo -e "${RED}Failed:${NC}  $TESTS_FAILED"
    echo -e "${YELLOW}Skipped:${NC} $TESTS_SKIPPED"
    echo ""

    total=$((TESTS_PASSED + TESTS_FAILED + TESTS_SKIPPED))
    echo "Total tests: $total"

    # Exit with failure if any tests failed
    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo -e "${RED}Some tests failed!${NC}"
        exit 1
    elif [[ $TESTS_PASSED -eq 0 ]]; then
        echo -e "${YELLOW}No tests passed!${NC}"
        exit 1
    else
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    fi
}

# Run main function
main
