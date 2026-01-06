#!/bin/bash
# Test script for new MCP-integrated API endpoints
# Usage: ./scripts/test_new_endpoints.sh [API_URL] [API_TOKEN]

set -e

API_URL="${1:-http://localhost:8000}"
API_TOKEN="${2:-}"

echo "========================================"
echo "Testing DevSkyy API Endpoints"
echo "========================================"
echo "API URL: $API_URL"
echo ""

# Function to make authenticated requests
make_request() {
    local method=$1
    local endpoint=$2
    local data=$3

    if [ -n "$API_TOKEN" ]; then
        if [ "$method" = "GET" ]; then
            curl -s -X GET "$API_URL$endpoint" \
                -H "Authorization: Bearer $API_TOKEN" \
                -H "Content-Type: application/json"
        else
            curl -s -X "$method" "$API_URL$endpoint" \
                -H "Authorization: Bearer $API_TOKEN" \
                -H "Content-Type: application/json" \
                -d "$data"
        fi
    else
        if [ "$method" = "GET" ]; then
            curl -s -X GET "$API_URL$endpoint" \
                -H "Content-Type: application/json"
        else
            curl -s -X "$method" "$API_URL$endpoint" \
                -H "Content-Type: application/json" \
                -d "$data"
        fi
    fi
}

echo "1. Testing Root Endpoint (GET /)"
echo "----------------------------------------"
make_request GET "/" | jq '.'
echo ""

echo "2. Testing Health Check (GET /health)"
echo "----------------------------------------"
make_request GET "/health" | jq '.'
echo ""

if [ -n "$API_TOKEN" ]; then
    echo "3. Testing Code Scan (POST /api/v1/code/scan)"
    echo "----------------------------------------"
    make_request POST "/api/v1/code/scan" '{
        "path": ".",
        "file_types": ["py"],
        "deep_scan": false
    }' | jq '.'
    echo ""

    echo "4. Testing Code Fix (POST /api/v1/code/fix)"
    echo "----------------------------------------"
    make_request POST "/api/v1/code/fix" '{
        "scan_results": {"issues": []},
        "auto_apply": false,
        "create_backup": true
    }' | jq '.'
    echo ""

    echo "5. Testing WordPress Theme Generation (POST /api/v1/wordpress/generate-theme)"
    echo "----------------------------------------"
    make_request POST "/api/v1/wordpress/generate-theme" '{
        "brand_name": "TestBrand",
        "industry": "fashion",
        "theme_type": "elementor"
    }' | jq '.'
    echo ""

    echo "6. Testing ML Prediction (POST /api/v1/ml/predict)"
    echo "----------------------------------------"
    make_request POST "/api/v1/ml/predict" '{
        "model_type": "trend_prediction",
        "data": {"items": ["oversized_blazers"], "time_horizon": "3_months"},
        "confidence_threshold": 0.7
    }' | jq '.'
    echo ""

    echo "7. Testing Bulk Products (POST /api/v1/commerce/products/bulk)"
    echo "----------------------------------------"
    make_request POST "/api/v1/commerce/products/bulk" '{
        "action": "create",
        "products": [{"name": "Test", "sku": "TEST-001", "price": 29.99}]
    }' | jq '.'
    echo ""

    echo "8. Testing Dynamic Pricing (POST /api/v1/commerce/pricing/optimize)"
    echo "----------------------------------------"
    make_request POST "/api/v1/commerce/pricing/optimize" '{
        "product_ids": ["PROD123"],
        "strategy": "ml_optimized"
    }' | jq '.'
    echo ""

    echo "9. Testing 3D Text Generation (POST /api/v1/media/3d/generate/text)"
    echo "----------------------------------------"
    make_request POST "/api/v1/media/3d/generate/text" '{
        "product_name": "Test Hoodie",
        "collection": "SIGNATURE",
        "garment_type": "hoodie",
        "output_format": "glb"
    }' | jq '.'
    echo ""

    echo "10. Testing 3D Image Generation (POST /api/v1/media/3d/generate/image)"
    echo "----------------------------------------"
    make_request POST "/api/v1/media/3d/generate/image" '{
        "product_name": "Test Product",
        "image_url": "https://example.com/image.jpg",
        "output_format": "glb"
    }' | jq '.'
    echo ""

    echo "11. Testing Marketing Campaign (POST /api/v1/marketing/campaigns)"
    echo "----------------------------------------"
    make_request POST "/api/v1/marketing/campaigns" '{
        "campaign_type": "email",
        "target_audience": {"segment": "high_value"}
    }' | jq '.'
    echo ""

    echo "12. Testing Multi-Agent Workflow (POST /api/v1/orchestration/workflows)"
    echo "----------------------------------------"
    make_request POST "/api/v1/orchestration/workflows" '{
        "workflow_name": "product_launch",
        "parameters": {"product_data": {"name": "Test"}},
        "parallel": true
    }' | jq '.'
    echo ""

    echo "13. Testing Monitoring Metrics (GET /api/v1/monitoring/metrics)"
    echo "----------------------------------------"
    make_request GET "/api/v1/monitoring/metrics?metrics=health&time_range=1h" | jq '.'
    echo ""

    echo "14. Testing Agent List (GET /api/v1/agents)"
    echo "----------------------------------------"
    make_request GET "/api/v1/agents" | jq '.'
    echo ""
else
    echo "⚠️  API_TOKEN not provided - skipping authenticated endpoint tests"
    echo "   Usage: $0 [API_URL] [API_TOKEN]"
    echo ""
fi

echo "========================================"
echo "All tests completed!"
echo "========================================"
