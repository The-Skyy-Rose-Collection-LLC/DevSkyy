#!/bin/bash
# DevSkyy Health Check Script
# Verifies all critical endpoints and services are functioning
# Usage: ./health_check.sh [base_url]

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
BASE_URL="${1:-http://localhost:8000}"
TIMEOUT=10
PASSED=0
FAILED=0

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}DevSkyy Health Check${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Base URL: ${BASE_URL}"
echo ""

# Helper function to check endpoint
check_endpoint() {
    local name="$1"
    local endpoint="$2"
    local expected_status="${3:-200}"
    local method="${4:-GET}"

    echo -n "Checking ${name}... "

    response=$(curl -s -o /dev/null -w "%{http_code}" -X ${method} "${BASE_URL}${endpoint}" --max-time ${TIMEOUT} || echo "000")

    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP ${response})"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (Expected HTTP ${expected_status}, got ${response})"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Helper function to check JSON response
check_json_endpoint() {
    local name="$1"
    local endpoint="$2"
    local expected_field="$3"

    echo -n "Checking ${name}... "

    response=$(curl -s "${BASE_URL}${endpoint}" --max-time ${TIMEOUT} || echo "{}")

    if echo "$response" | grep -q "\"${expected_field}\""; then
        echo -e "${GREEN}✅ PASS${NC} (field '${expected_field}' found)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (field '${expected_field}' not found)"
        echo "Response: ${response}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# 1. Basic Health Check
echo -e "${YELLOW}[1/8] Basic Health Checks${NC}"
check_endpoint "Root endpoint" "/" 200
check_json_endpoint "Health endpoint" "/health" "status"
check_endpoint "OpenAPI docs" "/docs" 200
check_endpoint "OpenAPI spec" "/openapi.json" 200
echo ""

# 2. API v1 Endpoints
echo -e "${YELLOW}[2/8] API v1 Endpoints${NC}"
# Most API endpoints require authentication, so we expect 401/403
check_endpoint "Agents endpoint (auth required)" "/api/v1/agents" 401
check_endpoint "Dashboard endpoint (auth required)" "/api/v1/dashboard/data" 401
echo ""

# 3. Authentication Endpoints
echo -e "${YELLOW}[3/8] Authentication Endpoints${NC}"
# These should return 422 (validation error) without body, not 500
check_endpoint "Login endpoint (no credentials)" "/api/v1/auth/login" 422 POST
check_endpoint "Register endpoint (no data)" "/api/v1/auth/register" 422 POST
echo ""

# 4. Static Files (if configured)
echo -e "${YELLOW}[4/8] Static Files${NC}"
check_endpoint "Favicon (if exists)" "/favicon.ico" 404  # 404 is ok if not configured
echo ""

# 5. CORS Headers
echo -e "${YELLOW}[5/8] CORS Configuration${NC}"
echo -n "Checking CORS headers... "
cors_header=$(curl -s -I "${BASE_URL}/" | grep -i "access-control-allow-origin" || echo "")
if [ -n "$cors_header" ]; then
    echo -e "${GREEN}✅ PASS${NC} (CORS enabled)"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠️  WARN${NC} (CORS not detected - may be intentional)"
    PASSED=$((PASSED + 1))
fi
echo ""

# 6. Response Time
echo -e "${YELLOW}[6/8] Performance Check${NC}"
echo -n "Checking response time... "
response_time=$(curl -s -o /dev/null -w "%{time_total}" "${BASE_URL}/health" || echo "999")
response_time_ms=$(echo "$response_time * 1000" | bc)
if (( $(echo "$response_time < 1.0" | bc -l) )); then
    echo -e "${GREEN}✅ PASS${NC} (${response_time_ms}ms < 1000ms)"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠️  WARN${NC} (${response_time_ms}ms > 1000ms)"
    PASSED=$((PASSED + 1))
fi
echo ""

# 7. Error Handling
echo -e "${YELLOW}[7/8] Error Handling${NC}"
check_endpoint "404 handling" "/nonexistent-endpoint" 404
echo ""

# 8. Container Stats (if running in Docker)
echo -e "${YELLOW}[8/8] Container Stats${NC}"
if command -v docker &> /dev/null; then
    container_name=$(docker ps --filter "publish=8000" --format "{{.Names}}" | head -1)
    if [ -n "$container_name" ]; then
        echo "Container: ${container_name}"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" "${container_name}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${YELLOW}⚠️  No container found on port 8000${NC}"
        PASSED=$((PASSED + 1))
    fi
else
    echo -e "${YELLOW}⚠️  Docker not available${NC}"
    PASSED=$((PASSED + 1))
fi
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Health Check Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Passed: ${GREEN}${PASSED}${NC}"
echo -e "Failed: ${RED}${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All health checks passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some health checks failed${NC}"
    exit 1
fi
