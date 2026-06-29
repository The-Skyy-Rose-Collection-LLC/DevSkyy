"""Wire tests for POST /commerce/products/bulk endpoint (T3-2).

TDD — written before implementation (RED state).

Verifies:
- Real delegation to CommerceAgent for create/update actions (not fake 10% failure loop)
- ProductResult.product_id sourced from agent return dict (woocommerce_id/id)
- Agent error dict {"error": "..."} → ProductResult.status="failed" with that message
- validate_only=True → no agent write calls fired
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1 import commerce as commerce_module
from api.v1.commerce import router
from core.task_status_store import get_initialized_task_status_store
from security.jwt_oauth2_auth import TokenPayload, TokenType, get_current_user

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_user() -> TokenPayload:
    return TokenPayload(
        sub="test-user",
        jti="jti-test",
        type=TokenType.ACCESS,
        roles=["api_user"],
    )


def _mock_store() -> MagicMock:
    """Async-capable TaskStatusStore stub — sync-path tests don't call it."""
    store = MagicMock()
    store.set_status = AsyncMock()
    store.update_status = AsyncMock()
    store.get_status = AsyncMock(return_value=None)
    return store


def _make_client(agent_cls: type, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Isolated FastAPI app with auth and store deps overridden."""
    monkeypatch.setattr(commerce_module, "CommerceAgent", agent_cls)
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: _mock_user()
    app.dependency_overrides[get_initialized_task_status_store] = _mock_store
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# (a) Real mapping — agent called, results carry woocommerce_id as product_id
# ---------------------------------------------------------------------------


def test_create_maps_agent_success_to_product_result(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each product POST → sync_product_to_woocommerce; return dict wired to ProductResult."""

    class _StubAgent:
        async def initialize(self) -> None:
            return None

        async def sync_product_to_woocommerce(
            self,
            name: str,
            price: float,
            sku: str | None = None,
            description: str = "",
            short_description: str = "",
            stock_quantity: int | None = None,
            status: str = "draft",
            categories: list | None = None,
            tags: list | None = None,
            images: list | None = None,
        ) -> dict:
            return {"id": 123, "woocommerce_id": 123, "name": name}

    client = _make_client(_StubAgent, monkeypatch)
    resp = client.post(
        "/commerce/products/bulk",
        json={
            "action": "create",
            "products": [
                {"name": "Black Rose Tee", "price": 89.99, "sku": "br-001"},
                {"name": "Signature Hoodie", "price": 120.00, "sku": "sg-001"},
            ],
        },
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "completed"
    assert body["total_products"] == 2
    results = body["results"]
    assert len(results) == 2
    for r in results:
        assert r["status"] == "success", f"expected success, got {r}"
        # product_id must come from woocommerce_id/id in agent return — NOT a fake uuid
        assert r["product_id"] == "123", f"product_id mismatch: {r['product_id']}"
    assert body["successful"] == 2
    assert body["failed"] == 0


# ---------------------------------------------------------------------------
# (b) Agent error dict → ProductResult.status="failed" with exact message
# ---------------------------------------------------------------------------


def test_create_agent_error_dict_maps_to_failed_result(monkeypatch: pytest.MonkeyPatch) -> None:
    """{"error": "..."} in agent return → ProductResult.status='failed', message=error string."""

    class _StubAgent:
        async def initialize(self) -> None:
            return None

        async def sync_product_to_woocommerce(
            self,
            name: str,
            price: float,
            sku: str | None = None,
            **kwargs: object,
        ) -> dict:
            return {"error": "WordPress client not connected"}

    client = _make_client(_StubAgent, monkeypatch)
    resp = client.post(
        "/commerce/products/bulk",
        json={
            "action": "create",
            "products": [{"name": "Black Rose Tee", "price": 89.99, "sku": "br-001"}],
        },
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    results = body["results"]
    assert len(results) == 1
    assert results[0]["status"] == "failed"
    assert results[0]["message"] == "WordPress client not connected"
    assert body["successful"] == 0
    assert body["failed"] == 1


# ---------------------------------------------------------------------------
# (c) validate_only=True → no write methods called on the agent
# ---------------------------------------------------------------------------


def test_validate_only_skips_all_agent_write_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """validate_only=True must return a result per product without touching write methods."""

    write_calls: list[str] = []

    class _StubAgent:
        async def initialize(self) -> None:
            return None

        async def sync_product_to_woocommerce(self, *args: object, **kwargs: object) -> dict:
            write_calls.append("sync_product_to_woocommerce")
            return {"id": 999, "woocommerce_id": 999}

        async def update_woocommerce_product(self, *args: object, **kwargs: object) -> dict:
            write_calls.append("update_woocommerce_product")
            return {"id": 999}

    client = _make_client(_StubAgent, monkeypatch)
    resp = client.post(
        "/commerce/products/bulk",
        json={
            "action": "create",
            "products": [{"name": "Test Product", "price": 50.00, "sku": "tt-001"}],
            "validate_only": True,
        },
    )

    assert resp.status_code == 200, resp.text
    # No write methods must have been called
    assert write_calls == [], f"write methods fired: {write_calls}"
    body = resp.json()
    results = body["results"]
    assert len(results) == 1
    assert results[0]["status"] in ("success", "skipped")


# ---------------------------------------------------------------------------
# (d) update path — update_woocommerce_product; result['id'] → product_id
# ---------------------------------------------------------------------------


def test_update_maps_agent_success_to_product_result(monkeypatch: pytest.MonkeyPatch) -> None:
    """action=update → update_woocommerce_product(product_id, updates); id wired through."""

    class _StubAgent:
        async def initialize(self) -> None:
            return None

        async def update_woocommerce_product(self, product_id: int, updates: dict) -> dict:
            return {"id": product_id}

    client = _make_client(_StubAgent, monkeypatch)
    resp = client.post(
        "/commerce/products/bulk",
        json={
            "action": "update",
            "products": [{"id": 42, "price": 99.99, "sku": "br-001"}],
        },
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "completed"
    results = body["results"]
    assert len(results) == 1
    assert results[0]["status"] == "success"
    assert results[0]["product_id"] == "42"
    assert body["successful"] == 1
    assert body["failed"] == 0


# ---------------------------------------------------------------------------
# (e) delete path — _wordpress_client.delete_product; product_id from input id
# ---------------------------------------------------------------------------


def test_delete_maps_agent_success_to_product_result(monkeypatch: pytest.MonkeyPatch) -> None:
    """action=delete → _ensure_wordpress_client + _wordpress_client.delete_product."""

    class _StubAgent:
        async def initialize(self) -> None:
            return None

        async def _ensure_wordpress_client(self) -> None:
            wc = MagicMock()
            wc.delete_product = AsyncMock(return_value={"deleted": True})
            self._wordpress_client = wc

    client = _make_client(_StubAgent, monkeypatch)
    resp = client.post(
        "/commerce/products/bulk",
        json={
            "action": "delete",
            "products": [{"id": 99, "sku": "sg-001"}],
        },
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    results = body["results"]
    assert len(results) == 1
    assert results[0]["status"] == "success"
    # product_id is sourced from the input id, not the delete_product return value
    assert results[0]["product_id"] == "99"
    assert body["successful"] == 1
    assert body["failed"] == 0


def test_delete_missing_client_maps_to_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    """delete with no WordPress client available → status='failed', honest (no fake success)."""

    class _StubAgent:
        async def initialize(self) -> None:
            return None

        async def _ensure_wordpress_client(self) -> None:
            self._wordpress_client = None

    client = _make_client(_StubAgent, monkeypatch)
    resp = client.post(
        "/commerce/products/bulk",
        json={
            "action": "delete",
            "products": [{"id": 7, "sku": "lh-001"}],
        },
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    results = body["results"]
    assert len(results) == 1
    assert results[0]["status"] == "failed"
    assert body["failed"] == 1
