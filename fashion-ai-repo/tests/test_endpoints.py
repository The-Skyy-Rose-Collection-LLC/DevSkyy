"""API endpoint tests."""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """
    Verify the API root (/) responds with service status "online" and includes a "version" field.
    
    Asserts the HTTP status code is 200, the JSON payload's "status" equals "online", and that a "version" key is present.
    """
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
    """
    Verify the /api/system/status endpoint responds with status 200 and includes a payload containing "agents".
    
    Asserts that the HTTP response code is 200, the JSON "status" field equals 200, a "payload" field is present, and that "agents" exists within the payload.
    """
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