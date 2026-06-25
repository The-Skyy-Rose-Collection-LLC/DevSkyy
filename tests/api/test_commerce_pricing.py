"""Tests for the dynamic pricing endpoint (``api/v1/commerce.py``).

Verifies ``/commerce/pricing/optimize`` is wired to ``CommerceAgent`` with the
canonical catalog as the ``current_price`` source. The prior implementation
returned hardcoded values (``current_price=89.99``, ``optimized_price=79.99``,
``revenue_impact=450.0``). These tests lock the real wiring, the honest
``estimated_revenue_impact=None`` (the agent does not model it), and the
graceful skip / 503 paths when the pricing model is unavailable or a SKU is
unknown.
"""

from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1 import commerce as commerce_module
from api.v1.commerce import router


@pytest.fixture
def mock_user():
    from security.jwt_oauth2_auth import TokenPayload, TokenType

    return TokenPayload(
        sub="user_123",
        jti="jti_123",
        type=TokenType.ACCESS,
        roles=["user"],
        exp=datetime.now(UTC),
        iat=datetime.now(UTC),
    )


def _make_client(mock_user, agent_cls, price_map, monkeypatch) -> TestClient:
    from security.jwt_oauth2_auth import get_current_user

    # Replace the real agent (no heavy initialize / no ml model) and pin the
    # catalog price map so the test is independent of catalog data drift.
    monkeypatch.setattr(commerce_module, "CommerceAgent", agent_cls)
    monkeypatch.setattr(commerce_module, "_catalog_price_map", lambda: price_map)

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: mock_user
    return TestClient(app)


def test_optimize_pricing_returns_real_optimization(mock_user, monkeypatch):
    class _StubAgent:
        async def initialize(self):
            return None

        async def optimize_price(self, sku, factors=None):
            return {"sku": sku, "recommended_price": 30.0, "confidence": 0.9}

    client = _make_client(mock_user, _StubAgent, {"br-001": 50.0}, monkeypatch)
    resp = client.post(
        "/commerce/pricing/optimize",
        json={"product_ids": ["br-001"], "strategy": "ml_optimized"},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total_products"] == 1
    opt = body["optimizations"][0]
    assert opt["product_id"] == "br-001"
    assert opt["current_price"] == 50.0  # from the catalog SOT, not hardcoded
    assert opt["optimized_price"] == 30.0  # from the agent
    assert opt["price_change"] == -20.0
    assert opt["price_change_pct"] == -40.0
    assert opt["estimated_revenue_impact"] is None  # honest: agent does not model it
    assert opt["confidence"] == 0.9


def test_optimize_pricing_ml_unavailable_returns_503(mock_user, monkeypatch):
    class _NoMLAgent:
        async def initialize(self):
            return None

        async def optimize_price(self, sku, factors=None):
            return {"sku": sku, "error": "ML module not available"}

    client = _make_client(mock_user, _NoMLAgent, {"br-001": 50.0}, monkeypatch)
    resp = client.post(
        "/commerce/pricing/optimize",
        json={"product_ids": ["br-001"]},
    )
    assert resp.status_code == 503, resp.text


def test_optimize_pricing_skips_unknown_sku(mock_user, monkeypatch):
    class _StubAgent:
        async def initialize(self):
            return None

        async def optimize_price(self, sku, factors=None):
            return {"recommended_price": 30.0, "confidence": 0.8}

    client = _make_client(mock_user, _StubAgent, {"br-001": 50.0}, monkeypatch)
    resp = client.post(
        "/commerce/pricing/optimize",
        json={"product_ids": ["zz-999", "br-001"]},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["optimizations"]) == 1
    assert body["optimizations"][0]["product_id"] == "br-001"
    assert body["aggregate_metrics"]["skipped_count"] == 1
    assert body["aggregate_metrics"]["skipped"][0]["product_id"] == "zz-999"
