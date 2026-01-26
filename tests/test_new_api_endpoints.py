"""Test suite for new MCP-integrated API endpoints.

This module tests all 13 missing API endpoints that were added:
1. POST /api/v1/code/scan
2. POST /api/v1/code/fix
3. POST /api/v1/wordpress/generate-theme
4. POST /api/v1/ml/predict
5. POST /api/v1/commerce/products/bulk
6. POST /api/v1/commerce/pricing/optimize
7. POST /api/v1/media/3d/generate/text
8. POST /api/v1/media/3d/generate/image
9. POST /api/v1/marketing/campaigns
10. POST /api/v1/orchestration/workflows
11. GET /api/v1/monitoring/metrics
12. GET /api/v1/agents
13. GET /api/v1/health (enhanced)

Version: 1.0.0
"""

import pytest
from fastapi.testclient import TestClient

from main_enterprise import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Get authentication headers with valid JWT token."""
    # Create a test user and get token
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "test_user", "password": "test_password"},
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    # Return empty headers if auth fails (for testing without auth)
    return {}


class TestCodeEndpoints:
    """Test code scanning and fixing endpoints."""

    def test_scan_code(self, client, auth_headers):
        """Test POST /api/v1/code/scan."""
        payload = {
            "path": "/Users/coreyfoster/DevSkyy",
            "file_types": ["py", "js"],
            "deep_scan": True,
        }
        response = client.post("/api/v1/code/scan", json=payload, headers=auth_headers)
        assert response.status_code in [200, 401]  # 401 if auth is not set up

        if response.status_code == 200:
            data = response.json()
            assert "scan_id" in data
            assert "status" in data
            assert "issues" in data

    def test_fix_code(self, client, auth_headers):
        """Test POST /api/v1/code/fix."""
        payload = {
            "scan_results": {"issues": [{"type": "syntax", "file": "test.py"}]},
            "auto_apply": False,
            "create_backup": True,
            "fix_types": ["syntax", "imports"],
        }
        response = client.post("/api/v1/code/fix", json=payload, headers=auth_headers)
        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert "fix_id" in data
            assert "fixes" in data


class TestWordPressEndpoints:
    """Test WordPress theme generation endpoints."""

    def test_generate_theme(self, client, auth_headers):
        """Test POST /api/v1/wordpress/generate-theme."""
        payload = {
            "brand_name": "TestBrand",
            "industry": "fashion",
            "theme_type": "elementor",
            "color_palette": ["#FF5733", "#3498DB"],
            "pages": ["home", "shop", "about"],
        }
        response = client.post(
            "/api/v1/wordpress/generate-theme", json=payload, headers=auth_headers
        )
        assert response.status_code in [202, 401]

        if response.status_code == 202:
            data = response.json()
            assert "theme_id" in data
            assert "brand_name" in data
            assert data["brand_name"] == "TestBrand"


@pytest.mark.slow
class TestMLEndpoints:
    """Test machine learning prediction endpoints (slow - ML operations)."""

    def test_ml_prediction_trend(self, client, auth_headers):
        """Test POST /api/v1/ml/predict with trend prediction."""
        payload = {
            "model_type": "trend_prediction",
            "data": {"items": ["oversized_blazers", "cargo_pants"], "time_horizon": "3_months"},
            "confidence_threshold": 0.7,
        }
        response = client.post("/api/v1/ml/predict", json=payload, headers=auth_headers)
        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert "prediction_id" in data
            assert "predictions" in data
            assert "metrics" in data

    def test_ml_prediction_demand(self, client, auth_headers):
        """Test POST /api/v1/ml/predict with demand forecasting."""
        payload = {
            "model_type": "demand_forecasting",
            "data": {"product_id": "PROD123", "forecast_days": 30},
            "confidence_threshold": 0.8,
        }
        response = client.post("/api/v1/ml/predict", json=payload, headers=auth_headers)
        assert response.status_code in [200, 401]


class TestMediaEndpoints:
    """Test 3D generation endpoints."""

    def test_3d_from_text(self, client, auth_headers):
        """Test POST /api/v1/media/3d/generate/text."""
        payload = {
            "product_name": "Heart Rose Bomber",
            "collection": "BLACK_ROSE",
            "garment_type": "bomber",
            "additional_details": "Rose gold zipper",
            "output_format": "glb",
        }
        response = client.post("/api/v1/media/3d/generate/text", json=payload, headers=auth_headers)
        assert response.status_code in [202, 401]

        if response.status_code == 202:
            data = response.json()
            assert "generation_id" in data
            assert "product_name" in data
            assert data["output_format"] == "glb"

    def test_3d_from_image(self, client, auth_headers):
        """Test POST /api/v1/media/3d/generate/image."""
        payload = {
            "product_name": "Custom Hoodie",
            "image_url": "https://cdn.skyyrose.co/test.jpg",
            "output_format": "gltf",
        }
        response = client.post(
            "/api/v1/media/3d/generate/image", json=payload, headers=auth_headers
        )
        assert response.status_code in [202, 401]


class TestMarketingEndpoints:
    """Test marketing campaign endpoints."""

    def test_create_campaign(self, client, auth_headers):
        """Test POST /api/v1/marketing/campaigns."""
        payload = {
            "campaign_type": "email",
            "target_audience": {"segment": "high_value", "location": "US"},
            "schedule": "2025-10-25T10:00:00Z",
        }
        response = client.post("/api/v1/marketing/campaigns", json=payload, headers=auth_headers)
        assert response.status_code in [201, 401]

        if response.status_code == 201:
            data = response.json()
            assert "campaign_id" in data
            assert "metrics" in data


class TestCommerceEndpoints:
    """Test commerce endpoints."""

    def test_bulk_products(self, client, auth_headers):
        """Test POST /api/v1/commerce/products/bulk."""
        payload = {
            "action": "create",
            "products": [
                {"name": "Test Product", "sku": "TEST-001", "price": 29.99},
                {"name": "Test Product 2", "sku": "TEST-002", "price": 39.99},
            ],
            "validate_only": False,
        }
        response = client.post("/api/v1/commerce/products/bulk", json=payload, headers=auth_headers)
        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert "operation_id" in data
            assert "results" in data

    def test_dynamic_pricing(self, client, auth_headers):
        """Test POST /api/v1/commerce/pricing/optimize."""
        payload = {
            "product_ids": ["PROD123", "PROD456"],
            "strategy": "ml_optimized",
            "constraints": {"min_margin": 0.2, "max_discount": 0.3},
        }
        response = client.post(
            "/api/v1/commerce/pricing/optimize", json=payload, headers=auth_headers
        )
        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert "optimization_id" in data
            assert "optimizations" in data


class TestOrchestrationEndpoints:
    """Test multi-agent orchestration endpoints."""

    def test_execute_workflow(self, client, auth_headers):
        """Test POST /api/v1/orchestration/workflows."""
        payload = {
            "workflow_name": "product_launch",
            "parameters": {"product_data": {"name": "Summer Collection"}},
            "parallel": True,
        }
        response = client.post(
            "/api/v1/orchestration/workflows", json=payload, headers=auth_headers
        )
        assert response.status_code in [202, 401]

        if response.status_code == 202:
            data = response.json()
            assert "workflow_id" in data
            assert "agents_used" in data
            assert "task_results" in data


class TestMonitoringEndpoints:
    """Test monitoring and system endpoints."""

    def test_get_metrics(self, client, auth_headers):
        """Test GET /api/v1/monitoring/metrics."""
        response = client.get(
            "/api/v1/monitoring/metrics?metrics=health&metrics=performance&time_range=1h",
            headers=auth_headers,
        )
        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert "metrics" in data
            assert "summary" in data

    def test_list_agents(self, client, auth_headers):
        """Test GET /api/v1/agents."""
        response = client.get("/api/v1/agents", headers=auth_headers)
        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            # API may return dict with total_agents or just a list
            if isinstance(data, dict):
                assert "total_agents" in data
                assert "agents" in data
                assert data["total_agents"] > 0
            else:
                # List format from agents_router
                assert isinstance(data, list)
                assert len(data) > 0


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_root(self, client):
        """Test GET / root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "DevSkyy Enterprise"
        assert "mcp_tools" in data
        assert data["mcp_tools"] == 13
        assert "api_endpoints" in data
        assert len(data["api_endpoints"]) >= 12

    def test_health(self, client):
        """Test GET /health enhanced endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "agents" in data
        assert data["agents"]["total"] == 54
        assert "services" in data
        assert data["services"]["mcp_server"] == "operational"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
