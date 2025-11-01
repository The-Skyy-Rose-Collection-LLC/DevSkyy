"""API endpoint tests."""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "version" in data


def test_health_endpoint(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_design_generation(client: TestClient, sample_design_payload):
    """Test design generation endpoint."""
    response = client.post("/api/design/generate", json=sample_design_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 200
    assert "payload" in data


def test_get_products(client: TestClient):
    """Test product listing endpoint."""
    response = client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 200
    assert "payload" in data


def test_system_status(client: TestClient):
    """Test system status endpoint."""
    response = client.get("/api/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 200
    assert "payload" in data
    assert "agents" in data["payload"]


def test_finance_summary(client: TestClient):
    """Test finance summary endpoint."""
    response = client.get("/api/finance/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 200


def test_analytics(client: TestClient):
    """Test analytics endpoint."""
    response = client.get("/api/analytics")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 200
    assert "metrics" in data["payload"]
