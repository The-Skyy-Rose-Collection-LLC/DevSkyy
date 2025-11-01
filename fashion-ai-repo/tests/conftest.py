"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.core.config import Config, load_config


@pytest.fixture
def client():
    """
    Create a TestClient bound to the FastAPI application for use in tests.
    
    Returns:
        TestClient: A TestClient instance initialized with the FastAPI app.
    """
    return TestClient(app)


@pytest.fixture
def config():
    """
    Load and return the application's test configuration.
    
    Returns:
        Config: The loaded configuration object.
    """
    return load_config()


@pytest.fixture
def sample_design_payload():
    """
    Provide a sample design payload dictionary used in tests.
    
    Returns:
        dict: Dictionary with keys "style", "color", and "season" set to "modern", "crimson", and "spring", respectively.
    """
    return {"style": "modern", "color": "crimson", "season": "spring"}


@pytest.fixture
def sample_product_payload():
    """
    Provide a sample product payload used in tests.
    
    Returns:
        dict: A product dictionary with keys:
            - "name": product title string,
            - "description": product description string,
            - "price_cents": integer price in cents.
    """
    return {
        "name": "Modern Crimson Collection",
        "description": "AI-generated modern design",
        "price_cents": 12000,
    }