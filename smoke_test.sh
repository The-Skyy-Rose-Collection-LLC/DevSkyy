#!/bin/bash
# DevSkyy Smoke Test Script
# Verifies that the application is running correctly
# Usage: ./smoke_test.sh [PORT]

PORT=${1:-8000}
BASE_URL="http://localhost:$PORT"
PASSED=0
FAILED=0

echo "=========================================="
echo "  DevSkyy Smoke Test"
echo "  Testing: $BASE_URL"
echo "=========================================="
echo ""

test_endpoint() {
    local name="$1"
    local endpoint="$2"
    local expected="$3"

    response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint" 2>/dev/null)

    if [ "$response" = "$expected" ]; then
        echo "[PASS] $name ($endpoint) - HTTP $response"
        ((PASSED++))
    else
        echo "[FAIL] $name ($endpoint) - Expected $expected, got $response"
        ((FAILED++))
    fi
}

test_json_field() {
    local name="$1"
    local endpoint="$2"
    local field="$3"
    local expected="$4"

    value=$(curl -s "$BASE_URL$endpoint" 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('$field',''))" 2>/dev/null)

    if [ "$value" = "$expected" ]; then
        echo "[PASS] $name - $field=$expected"
        ((PASSED++))
    else
        echo "[FAIL] $name - Expected $field=$expected, got $field=$value"
        ((FAILED++))
    fi
}

echo "Testing HTTP endpoints..."
echo ""

# Basic endpoint tests
test_endpoint "Health Check" "/health" "200"
test_endpoint "System Status" "/status" "200"
test_endpoint "Root Page" "/" "200"
test_endpoint "Dashboard" "/dashboard" "200"
test_endpoint "API Docs" "/docs" "200"
test_endpoint "OpenAPI Spec" "/openapi.json" "200"

echo ""
echo "Testing API responses..."
echo ""

# JSON response tests
test_json_field "Health Status" "/health" "status" "healthy"
test_json_field "System Status" "/status" "status" "operational"

echo ""
echo "=========================================="
echo "  Results: $PASSED passed, $FAILED failed"
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    echo ""
    echo "  All tests passed! Application is ready."
    echo ""
    echo "  Dashboard: $BASE_URL/dashboard"
    echo "  API Docs:  $BASE_URL/docs"
    echo ""
    exit 0
else
    echo ""
    echo "  Some tests failed. Check the application logs."
    echo ""
    exit 1
fi
