"""Tests for the LoRA Training API (api/v1/lora.py).

Covers all 4 routes:
  POST /lora/train       → 202 accepted (background dispatch, not awaited inline)
  GET  /lora/dataset/preview → 200 summary shape
  GET  /lora/versions/{version} → 200 or 404
  GET  /lora/products/{sku}/history → 200 (may be empty list)

All imagery backends are monkeypatched — no real WooCommerce calls, no real GPU
training, no real SQLite reads.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1 import lora as lmod
from api.v1.lora import lora_router
from imagery.lora_version_tracker import LoRAVersion, ProductContribution

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(lora_router)
    return TestClient(app)


def _make_lora_version(version: str = "v1.0.0") -> LoRAVersion:
    """Return a minimal LoRAVersion dataclass instance for stubbing."""
    return LoRAVersion(
        id=1,
        version=version,
        base_model="runwayml/stable-diffusion-v1-5",
        created_at=datetime(2026, 6, 26, 0, 0, 0),
        training_config={"epochs": 100, "lr": 1e-4},
        model_path="models/skyyrose-luxury-lora",
        total_images=120,
        total_products=10,
        collections={"SIGNATURE": 5, "BLACK_ROSE": 5},
        products=[
            ProductContribution(
                id=1,
                lora_version_id=1,
                product_id=101,
                sku="sg-001",
                product_name="The Classic",
                collection="SIGNATURE",
                images_count=12,
                quality_score=0.85,
            )
        ],
    )


def _make_product_source(sku: str = "sg-001", collection: str = "SIGNATURE") -> MagicMock:
    """Return a mock ProductTrainingSource with real-looking data."""
    p = MagicMock()
    p.product_id = 101
    p.sku = sku
    p.name = "The Classic"
    p.collection = collection
    p.image_urls = ["https://example.com/img1.jpg", "https://example.com/img2.jpg"]
    p.local_image_paths = []  # pre-download; always empty at preview stage
    p.quality_score = 0.85
    return p


# ---------------------------------------------------------------------------
# POST /lora/train → 202
# ---------------------------------------------------------------------------


def test_train_returns_202(monkeypatch):
    """Train dispatches background task and returns 202 immediately."""
    trainer_instance = MagicMock()
    trainer_instance.train_from_products = AsyncMock(return_value=Path("models/output"))

    TrainerClass = MagicMock(return_value=trainer_instance)
    monkeypatch.setattr(lmod, "SkyyRoseLoRATrainer", TrainerClass)

    resp = _client().post(
        "/lora/train",
        json={"collections": ["SIGNATURE", "BLACK_ROSE"], "max_products": 20, "epochs": 50},
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "accepted"
    assert "message" in body
    assert "monitor" in body


def test_train_with_version_echoes_version(monkeypatch):
    """When caller supplies a version it is echoed back in the response."""
    trainer_instance = MagicMock()
    trainer_instance.train_from_products = AsyncMock(return_value=Path("models/output"))
    monkeypatch.setattr(lmod, "SkyyRoseLoRATrainer", MagicMock(return_value=trainer_instance))

    resp = _client().post(
        "/lora/train",
        json={"version": "v2.0.0", "epochs": 100},
    )
    assert resp.status_code == 202
    assert resp.json()["version"] == "v2.0.0"


def test_train_still_202_when_background_task_raises(monkeypatch):
    """Even if training eventually fails, the request has already returned 202."""
    trainer_instance = MagicMock()
    trainer_instance.train_from_products = AsyncMock(side_effect=ImportError("diffusers missing"))
    monkeypatch.setattr(lmod, "SkyyRoseLoRATrainer", MagicMock(return_value=trainer_instance))

    # Under TestClient(raise_server_exceptions=True default), an unhandled background
    # exception would propagate and fail the test. If we still get 202, the wrapper
    # caught and logged it correctly.
    resp = _client().post("/lora/train", json={"epochs": 100})
    assert resp.status_code == 202


def test_train_dispatches_not_inline(monkeypatch):
    """train_from_products is called (by BackgroundTasks) — not blocking the response."""
    trainer_instance = MagicMock()
    train_mock = AsyncMock(return_value=Path("models/output"))
    trainer_instance.train_from_products = train_mock
    monkeypatch.setattr(lmod, "SkyyRoseLoRATrainer", MagicMock(return_value=trainer_instance))

    resp = _client().post("/lora/train", json={"collections": ["SIGNATURE"], "epochs": 10})
    assert resp.status_code == 202
    # TestClient executes BackgroundTasks before returning, so assert it ran exactly once.
    train_mock.assert_called_once()
    # Confirm collections + epochs were forwarded
    _, kwargs = train_mock.call_args
    assert kwargs.get("epochs") == 10
    assert "SIGNATURE" in (kwargs.get("collections") or [])


# ---------------------------------------------------------------------------
# GET /lora/dataset/preview
# ---------------------------------------------------------------------------


def test_preview_returns_summary_shape(monkeypatch):
    """Preview builds correct counts from mocked products."""
    products = [
        _make_product_source("sg-001", "SIGNATURE"),
        _make_product_source("sg-002", "SIGNATURE"),
        _make_product_source("br-001", "BLACK_ROSE"),
    ]

    async def _fake_fetch(**kwargs):
        return products

    monkeypatch.setattr(lmod, "fetch_products_from_woocommerce", _fake_fetch)

    resp = _client().get("/lora/dataset/preview?collections=SIGNATURE,BLACK_ROSE&max_products=50")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_products"] == 3
    assert body["total_images"] == 6  # 3 products × 2 images each
    assert "avg_quality_score" in body
    assert "collections" in body
    assert body["collections"]["SIGNATURE"] == 2
    assert body["collections"]["BLACK_ROSE"] == 1
    assert "sample_products" in body
    assert len(body["sample_products"]) <= 5


def test_preview_no_collections_fetches_all(monkeypatch):
    """Omitting collections param fetches without collection filter."""
    products = [_make_product_source("sg-001")]

    async def _fake_fetch(**kwargs):
        return products

    monkeypatch.setattr(lmod, "fetch_products_from_woocommerce", _fake_fetch)

    resp = _client().get("/lora/dataset/preview")
    assert resp.status_code == 200
    assert resp.json()["total_products"] == 1


def test_preview_wc_failure_is_502_or_503(monkeypatch):
    """WooCommerce fetch failure → 502 or 503; raw exception NOT in response body."""

    async def _boom(**kwargs):
        raise ConnectionError("WC is down")

    monkeypatch.setattr(lmod, "fetch_products_from_woocommerce", _boom)

    resp = _client().get("/lora/dataset/preview")
    assert resp.status_code in (502, 503)
    # Raw exception string must not leak to the client
    assert "WC is down" not in resp.text


# ---------------------------------------------------------------------------
# GET /lora/versions/{version}
# ---------------------------------------------------------------------------


def test_version_info_happy_path(monkeypatch):
    """Existing version returns 200 with all expected fields."""
    lv = _make_lora_version("v1.0.0")

    tracker_instance = MagicMock()
    tracker_instance.initialize = AsyncMock()
    tracker_instance.get_version = AsyncMock(return_value=lv)
    monkeypatch.setattr(lmod, "LoRAVersionTracker", MagicMock(return_value=tracker_instance))

    resp = _client().get("/lora/versions/v1.0.0")
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "v1.0.0"
    assert body["base_model"] == lv.base_model
    assert body["total_products"] == lv.total_products
    assert body["total_images"] == lv.total_images
    assert "collections" in body
    assert "products" in body


def test_version_info_not_found_is_404(monkeypatch):
    """Missing version → 404, not 500."""
    tracker_instance = MagicMock()
    tracker_instance.initialize = AsyncMock()
    tracker_instance.get_version = AsyncMock(side_effect=ValueError("Version not found: v9.9.9"))
    monkeypatch.setattr(lmod, "LoRAVersionTracker", MagicMock(return_value=tracker_instance))

    resp = _client().get("/lora/versions/v9.9.9")
    assert resp.status_code == 404


def test_version_info_tracker_error_is_502(monkeypatch):
    """Unexpected DB error → 502; exception text not leaked."""
    tracker_instance = MagicMock()
    tracker_instance.initialize = AsyncMock()
    tracker_instance.get_version = AsyncMock(side_effect=RuntimeError("DB exploded"))
    monkeypatch.setattr(lmod, "LoRAVersionTracker", MagicMock(return_value=tracker_instance))

    resp = _client().get("/lora/versions/v1.0.0")
    assert resp.status_code == 502
    assert "DB exploded" not in resp.text


# ---------------------------------------------------------------------------
# GET /lora/products/{sku}/history
# ---------------------------------------------------------------------------


def test_product_history_returns_versions_list(monkeypatch):
    """SKU with training history returns 200 and the list."""
    lv = _make_lora_version("v1.0.0")
    tracker_instance = MagicMock()
    tracker_instance.initialize = AsyncMock()
    tracker_instance.get_product_history = AsyncMock(return_value=[lv])
    monkeypatch.setattr(lmod, "LoRAVersionTracker", MagicMock(return_value=tracker_instance))

    resp = _client().get("/lora/products/sg-001/history")
    assert resp.status_code == 200
    body = resp.json()
    assert body["sku"] == "sg-001"
    assert len(body["versions"]) == 1
    assert body["versions"][0]["version"] == "v1.0.0"


def test_product_history_empty_is_200(monkeypatch):
    """SKU with no history returns 200 with empty list (not 404)."""
    tracker_instance = MagicMock()
    tracker_instance.initialize = AsyncMock()
    tracker_instance.get_product_history = AsyncMock(return_value=[])
    monkeypatch.setattr(lmod, "LoRAVersionTracker", MagicMock(return_value=tracker_instance))

    resp = _client().get("/lora/products/new-sku/history")
    assert resp.status_code == 200
    body = resp.json()
    assert body["sku"] == "new-sku"
    assert body["versions"] == []


def test_product_history_tracker_error_is_502(monkeypatch):
    """Unexpected DB error → 502; exception text not leaked."""
    tracker_instance = MagicMock()
    tracker_instance.initialize = AsyncMock()
    tracker_instance.get_product_history = AsyncMock(side_effect=RuntimeError("DB exploded"))
    monkeypatch.setattr(lmod, "LoRAVersionTracker", MagicMock(return_value=tracker_instance))

    resp = _client().get("/lora/products/sg-001/history")
    assert resp.status_code == 502
    assert "DB exploded" not in resp.text
