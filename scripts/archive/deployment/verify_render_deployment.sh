#!/usr/bin/env bash
#
# Render Deployment Verification Script
# ======================================
#
# Comprehensive verification of deployed DevSkyy backend on Render.
# Tests all critical endpoints, database connectivity, and API functionality.
#
# Usage:
#   ./scripts/verify_render_deployment.sh https://devskyy-api.onrender.com
#   ./scripts/verify_render_deployment.sh https://api.skyyrose.com
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${1:-https://devskyy-api.onrender.com}"
TIMEOUT=10
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  DevSkyy Render Deployment Verification               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}\n"
echo -e "${BLUE}Target:${NC} $BASE_URL\n"

# Helper functions
test_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED_TESTS++))
    ((TOTAL_TESTS++))
}

test_fail() {
    echo -e "${RED}✗${NC} $1"
    if [ -n "${2:-}" ]; then
        echo -e "  ${YELLOW}→${NC} $2"
    fi
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
}

test_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    if [ -n "${2:-}" ]; then
        echo -e "  ${YELLOW}→${NC} $2"
    fi
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}Error: $1 is required but not installed${NC}"
        exit 1
    fi
}

# Check dependencies
check_command curl
check_command jq

# Test 1: Basic Health Check
echo -e "${BLUE}[1/12] Basic Health Check${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$BASE_URL/health" || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    test_pass "Health endpoint returns 200 OK"

    # Validate JSON response
    if echo "$BODY" | jq -e '.status' > /dev/null 2>&1; then
        STATUS=$(echo "$BODY" | jq -r '.status')
        if [ "$STATUS" = "healthy" ]; then
            test_pass "Health status is 'healthy'"
        else
            test_fail "Health status is '$STATUS'" "Expected 'healthy'"
        fi

        # Check version
        if echo "$BODY" | jq -e '.version' > /dev/null 2>&1; then
            VERSION=$(echo "$BODY" | jq -r '.version')
            test_pass "Version reported: $VERSION"
        fi

        # Check environment
        if echo "$BODY" | jq -e '.environment' > /dev/null 2>&1; then
            ENV=$(echo "$BODY" | jq -r '.environment')
            if [ "$ENV" = "production" ]; then
                test_pass "Environment is 'production'"
            else
                test_warn "Environment is '$ENV'" "Expected 'production'"
            fi
        fi
    else
        test_fail "Invalid JSON response" "$BODY"
    fi
else
    test_fail "Health endpoint failed with HTTP $HTTP_CODE" "Service may not be running"
fi
echo ""

# Test 2: Readiness Check (Database & Redis)
echo -e "${BLUE}[2/12] Readiness Check (Database & Redis)${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$BASE_URL/health/ready" || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    test_pass "Readiness endpoint returns 200 OK"

    if echo "$BODY" | jq -e '.' > /dev/null 2>&1; then
        # Check database connectivity
        if echo "$BODY" | jq -e '.database' > /dev/null 2>&1; then
            DB_STATUS=$(echo "$BODY" | jq -r '.database')
            if [ "$DB_STATUS" = "connected" ]; then
                test_pass "Database connected"
            else
                test_fail "Database not connected: $DB_STATUS"
            fi
        fi

        # Check Redis connectivity
        if echo "$BODY" | jq -e '.redis' > /dev/null 2>&1; then
            REDIS_STATUS=$(echo "$BODY" | jq -r '.redis')
            if [ "$REDIS_STATUS" = "connected" ]; then
                test_pass "Redis connected"
            else
                test_fail "Redis not connected: $REDIS_STATUS"
            fi
        fi
    fi
else
    test_fail "Readiness check failed with HTTP $HTTP_CODE" "Database or Redis may not be configured"
fi
echo ""

# Test 3: API Documentation
echo -e "${BLUE}[3/12] API Documentation${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$BASE_URL/docs" || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)

if [ "$HTTP_CODE" = "200" ]; then
    test_pass "Swagger UI accessible at /docs"
else
    test_fail "Swagger UI not accessible" "HTTP $HTTP_CODE"
fi

RESPONSE=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$BASE_URL/redoc" || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)

if [ "$HTTP_CODE" = "200" ]; then
    test_pass "ReDoc accessible at /redoc"
else
    test_fail "ReDoc not accessible" "HTTP $HTTP_CODE"
fi

RESPONSE=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$BASE_URL/openapi.json" || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)

if [ "$HTTP_CODE" = "200" ]; then
    test_pass "OpenAPI spec accessible at /openapi.json"
else
    test_fail "OpenAPI spec not accessible" "HTTP $HTTP_CODE"
fi
echo ""

# Test 4: Agent Endpoints
echo -e "${BLUE}[4/12] Agent Endpoints${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$BASE_URL/api/v1/agents" || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    test_pass "List agents endpoint returns 200 OK"

    if echo "$BODY" | jq -e '. | length' > /dev/null 2>&1; then
        AGENT_COUNT=$(echo "$BODY" | jq '. | length')
        if [ "$AGENT_COUNT" -gt 0 ]; then
            test_pass "Found $AGENT_COUNT agents"

            # Check for specific agents
            AGENTS=$(echo "$BODY" | jq -r '.[].id' 2>/dev/null || echo "")
            if echo "$AGENTS" | grep -q "commerce"; then
                test_pass "Commerce agent available"
            fi
            if echo "$AGENTS" | grep -q "creative"; then
                test_pass "Creative agent available"
            fi
        else
            test_fail "No agents found" "Expected at least 1 agent"
        fi
    fi
else
    test_fail "List agents failed with HTTP $HTTP_CODE"
fi
echo ""

# Test 5: Brand Context Endpoint
echo -e "${BLUE}[5/12] Brand Context${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$BASE_URL/api/v1/brand/context" || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    test_pass "Brand context endpoint returns 200 OK"

    if echo "$BODY" | jq -e '.name' > /dev/null 2>&1; then
        BRAND_NAME=$(echo "$BODY" | jq -r '.name')
        if [ "$BRAND_NAME" = "SkyyRose" ]; then
            test_pass "Brand name is 'SkyyRose'"
        else
            test_fail "Unexpected brand name: $BRAND_NAME"
        fi
    fi
else
    test_fail "Brand context failed with HTTP $HTTP_CODE"
fi
echo ""

# Test 6: CORS Headers
echo -e "${BLUE}[6/12] CORS Configuration${NC}"
ORIGIN="https://devskyy-dashboard.vercel.app"
RESPONSE=$(curl -s -H "Origin: $ORIGIN" -H "Access-Control-Request-Method: POST" -w "\n%{http_code}" --max-time $TIMEOUT "$BASE_URL/api/v1/agents" || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)

if [ "$HTTP_CODE" = "200" ]; then
    # Check CORS headers (need curl -i for headers)
    HEADERS=$(curl -s -i -H "Origin: $ORIGIN" --max-time $TIMEOUT "$BASE_URL/health" | head -20)

    if echo "$HEADERS" | grep -qi "access-control-allow-origin"; then
        test_pass "CORS headers present"
    else
        test_warn "CORS headers not found" "May need to configure CORS_ORIGINS"
    fi
else
    test_fail "CORS preflight check failed"
fi
echo ""

# Test 7: Security Headers
echo -e "${BLUE}[7/12] Security Headers${NC}"
HEADERS=$(curl -s -i --max-time $TIMEOUT "$BASE_URL/health" | head -20)

if echo "$HEADERS" | grep -qi "x-frame-options"; then
    test_pass "X-Frame-Options header present"
else
    test_warn "X-Frame-Options header missing" "Consider adding for clickjacking protection"
fi

if echo "$HEADERS" | grep -qi "x-content-type-options"; then
    test_pass "X-Content-Type-Options header present"
else
    test_warn "X-Content-Type-Options header missing"
fi

if echo "$HEADERS" | grep -qi "strict-transport-security"; then
    test_pass "Strict-Transport-Security header present"
else
    test_warn "HSTS header missing" "Expected for HTTPS"
fi
echo ""

# Test 8: SSL/TLS Certificate
echo -e "${BLUE}[8/12] SSL/TLS Certificate${NC}"
if [[ "$BASE_URL" =~ ^https:// ]]; then
    # Extract hostname
    HOSTNAME=$(echo "$BASE_URL" | sed 's|https://||' | cut -d'/' -f1)

    # Check certificate validity
    if command -v openssl &> /dev/null; then
        CERT_INFO=$(echo | openssl s_client -servername "$HOSTNAME" -connect "$HOSTNAME:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "")

        if [ -n "$CERT_INFO" ]; then
            test_pass "SSL certificate valid"

            # Check expiry
            EXPIRY=$(echo "$CERT_INFO" | grep "notAfter" | cut -d'=' -f2)
            test_pass "Certificate expires: $EXPIRY"
        else
            test_warn "Could not verify SSL certificate"
        fi
    else
        test_warn "openssl not installed, skipping certificate check"
    fi
else
    test_fail "Not using HTTPS" "Production should use HTTPS"
fi
echo ""

# Test 9: Response Time
echo -e "${BLUE}[9/12] Performance${NC}"
START=$(date +%s%N)
curl -s --max-time $TIMEOUT "$BASE_URL/health" > /dev/null
END=$(date +%s%N)
RESPONSE_TIME=$(( (END - START) / 1000000 ))  # Convert to milliseconds

if [ "$RESPONSE_TIME" -lt 500 ]; then
    test_pass "Response time: ${RESPONSE_TIME}ms (excellent)"
elif [ "$RESPONSE_TIME" -lt 1000 ]; then
    test_pass "Response time: ${RESPONSE_TIME}ms (good)"
elif [ "$RESPONSE_TIME" -lt 2000 ]; then
    test_warn "Response time: ${RESPONSE_TIME}ms (acceptable)" "Consider optimization"
else
    test_warn "Response time: ${RESPONSE_TIME}ms (slow)" "May need performance tuning"
fi
echo ""

# Test 10: Metrics Endpoint
echo -e "${BLUE}[10/12] Monitoring & Metrics${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$BASE_URL/metrics" || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    test_pass "Prometheus metrics endpoint accessible"

    # Check for key metrics
    if echo "$BODY" | grep -q "http_requests_total"; then
        test_pass "HTTP request metrics present"
    fi

    if echo "$BODY" | grep -q "agent_executions_total"; then
        test_pass "Agent execution metrics present"
    fi
else
    test_warn "Metrics endpoint not accessible" "HTTP $HTTP_CODE"
fi
echo ""

# Test 11: Error Handling
echo -e "${BLUE}[11/12] Error Handling${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$BASE_URL/api/v1/nonexistent" || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)

if [ "$HTTP_CODE" = "404" ]; then
    test_pass "404 error for invalid endpoint"
else
    test_warn "Unexpected response for invalid endpoint: HTTP $HTTP_CODE"
fi

# Test invalid method
RESPONSE=$(curl -s -X DELETE -w "\n%{http_code}" --max-time $TIMEOUT "$BASE_URL/health" || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)

if [ "$HTTP_CODE" = "405" ]; then
    test_pass "405 error for invalid method"
else
    test_warn "Unexpected response for invalid method: HTTP $HTTP_CODE"
fi
echo ""

# Test 12: Rate Limiting
echo -e "${BLUE}[12/12] Rate Limiting${NC}"
# Make multiple rapid requests
RATE_LIMIT_TRIGGERED=false
for i in {1..10}; do
    RESPONSE=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$BASE_URL/health" || echo "000")
    HTTP_CODE=$(echo "$RESPONSE" | tail -1)

    if [ "$HTTP_CODE" = "429" ]; then
        RATE_LIMIT_TRIGGERED=true
        break
    fi
done

if [ "$RATE_LIMIT_TRIGGERED" = true ]; then
    test_pass "Rate limiting is active (429 Too Many Requests)"
else
    test_warn "Rate limiting not triggered" "May not be configured"
fi
echo ""

# Summary
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Verification Summary                                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo -e ""
echo -e "  Total Tests:  $TOTAL_TESTS"
echo -e "  ${GREEN}Passed:${NC}       $PASSED_TESTS"
echo -e "  ${RED}Failed:${NC}       $FAILED_TESTS"
echo -e ""

# Calculate success rate
if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo -e "  Success Rate: ${SUCCESS_RATE}%"
    echo -e ""
fi

# Overall result
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ Deployment verification passed!${NC}"
    echo -e "  Your DevSkyy backend is ready for production use."
    echo -e ""
    echo -e "  ${BLUE}Next steps:${NC}"
    echo -e "  • Test critical user flows"
    echo -e "  • Set up monitoring alerts"
    echo -e "  • Configure custom domain"
    echo -e "  • Update frontend BACKEND_URL"
    exit 0
else
    echo -e "${RED}✗ Deployment verification failed${NC}"
    echo -e "  Please address the failed tests before going to production."
    echo -e ""
    echo -e "  ${BLUE}Check:${NC}"
    echo -e "  • Render Dashboard → Logs for errors"
    echo -e "  • Environment variables are set correctly"
    echo -e "  • Database and Redis are running"
    exit 1
fi
