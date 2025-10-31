"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.core.config import Config, load_config


@pytest.fixture
def client():
    """Create test client for API testing."""
    return TestClient(app)


@pytest.fixture
def config():
    """Load test configuration."""
    return load_config()


@pytest.fixture
def sample_design_payload():
    """Sample design payload for testing."""
    return {"style": "modern", "color": "crimson", "season": "spring"}


@pytest.fixture
def sample_product_payload():
    """Sample product payload for testing."""
    return {
        "name": "Modern Crimson Collection",
        "description": "AI-generated modern design",
        "price_cents": 12000,
    }
