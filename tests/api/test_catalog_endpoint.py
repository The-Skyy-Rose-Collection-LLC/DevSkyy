"""Tests for /api/v1/catalog/* endpoints.

These tests inject a fake CatalogRetriever via the module-level singleton
slot, so we verify the endpoint contract WITHOUT calling Voyage/Pinecone.
The retriever's own contract is tested in tests/orchestration/.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1 import catalog as catalog_module
from api.v1.catalog import router as catalog_router
from orchestration.catalog_retriever import CatalogMatch

# ---------------------------------------------------------------------------
# Fake retriever — quacks like CatalogRetriever, returns fixed matches
# ---------------------------------------------------------------------------


class _FakeRetriever:
    def __init__(self, matches: list[CatalogMatch]):
        self._matches = matches
        self._namespace = "catalog"
        # Minimal embedder stub for the /health endpoint
        self._embedder = type(
            "FakeEmbedder",
            (),
            {"get_info": staticmethod(lambda: {"provider": "voyage", "dimension": 1024})},
        )()

    async def retrieve(self, query, *, top_k=5, collection=None):
        return self._matches[:top_k]

    async def retrieve_by_collection(self, slug, *, top_k=5):
        return [m for m in self._matches if m.collection == slug][:top_k]


@pytest.fixture
def fake_matches() -> list[CatalogMatch]:
    return [
        CatalogMatch(
            sku="br-005",
            name="BLACK Rose Hoodie — Signature Edition",
            collection="black-rose",
            score=0.741,
            branding_spec="silver Cinzel",
            description="Heavyweight black hoodie",
        ),
        CatalogMatch(
            sku="br-004",
            name="BLACK Rose Hoodie",
            collection="black-rose",
            score=0.738,
            branding_spec="rose embroidery",
            description="Standard black hoodie",
        ),
        CatalogMatch(
            sku="lh-004",
            name="Love Hurts Bomber Jacket",
            collection="love-hurts",
            score=0.620,
            branding_spec="crimson",
            description="Romantic bomber",
        ),
    ]


@pytest.fixture
def client(fake_matches, monkeypatch):
    """FastAPI TestClient with a fake retriever pre-seeded into the singleton slot.

    Avoids booting the full main_enterprise app (which initializes DB,
    Sentry, OTel) — we just mount our router on a bare FastAPI instance.
    """
    fake = _FakeRetriever(fake_matches)
    monkeypatch.setattr(catalog_module, "_retriever", fake)

    app = FastAPI()
    app.include_router(catalog_router, prefix="/api/v1")
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_singleton(monkeypatch):
    """Each test gets a clean singleton slot (overridden by `client` fixture above)."""
    monkeypatch.setattr(catalog_module, "_retriever", None)


# ---------------------------------------------------------------------------
# /search — happy paths
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_search_returns_top_k_matches(client):
    resp = client.get("/api/v1/catalog/search", params={"q": "gothic luxury hoodie", "top_k": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == "gothic luxury hoodie"
    assert body["top_k"] == 2
    assert body["collection"] is None
    assert len(body["matches"]) == 2
    assert body["matches"][0]["sku"] == "br-005"
    assert body["matches"][0]["score"] == pytest.approx(0.741)
    assert "elapsed_ms" in body and body["elapsed_ms"] >= 0


@pytest.mark.unit
def test_search_default_top_k_is_5(client):
    resp = client.get("/api/v1/catalog/search", params={"q": "anything"})
    assert resp.status_code == 200
    assert resp.json()["top_k"] == 5


@pytest.mark.unit
def test_search_with_collection_filter(client):
    resp = client.get(
        "/api/v1/catalog/search",
        params={"q": "hoodie", "collection": "black-rose"},
    )
    assert resp.status_code == 200
    assert resp.json()["collection"] == "black-rose"


# ---------------------------------------------------------------------------
# /search — input validation
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_search_rejects_empty_query(client):
    resp = client.get("/api/v1/catalog/search", params={"q": ""})
    assert resp.status_code == 422


@pytest.mark.unit
def test_search_rejects_oversize_query(client):
    resp = client.get("/api/v1/catalog/search", params={"q": "x" * 501})
    assert resp.status_code == 422


@pytest.mark.unit
def test_search_rejects_top_k_out_of_range(client):
    resp = client.get("/api/v1/catalog/search", params={"q": "x", "top_k": 0})
    assert resp.status_code == 422
    resp = client.get("/api/v1/catalog/search", params={"q": "x", "top_k": 21})
    assert resp.status_code == 422


@pytest.mark.unit
def test_search_rejects_invalid_collection_slug(client):
    """Collection slugs must be lowercase-hyphen format."""
    for bad in ["Black-Rose", "black_rose", "BLACK-ROSE", "black rose", "1black"]:
        resp = client.get("/api/v1/catalog/search", params={"q": "x", "collection": bad})
        assert resp.status_code == 422, f"expected 422 for slug={bad!r}, got {resp.status_code}"


@pytest.mark.unit
def test_search_accepts_valid_collection_slugs(client):
    for ok in ["black-rose", "love-hurts", "signature", "kids-capsule"]:
        resp = client.get("/api/v1/catalog/search", params={"q": "x", "collection": ok})
        assert resp.status_code == 200, f"expected 200 for slug={ok!r}"


# ---------------------------------------------------------------------------
# /collections/{slug}/featured
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_collection_featured_filters_by_slug(client):
    resp = client.get("/api/v1/catalog/collections/black-rose/featured")
    assert resp.status_code == 200
    body = resp.json()
    assert body["collection"] == "black-rose"
    skus = [m["sku"] for m in body["matches"]]
    # Both fake matches in black-rose collection should be returned
    assert "br-005" in skus
    assert "br-004" in skus
    # Love-hurts items should NOT appear
    assert "lh-004" not in skus


@pytest.mark.unit
def test_collection_featured_top_k_validation(client):
    resp = client.get("/api/v1/catalog/collections/black-rose/featured", params={"top_k": 0})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_health_reports_ok_when_retriever_available(client):
    resp = client.get("/api/v1/catalog/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["embedder"] == {"provider": "voyage", "dimension": 1024}
    assert body["namespace"] == "catalog"


# ---------------------------------------------------------------------------
# Failure surface — retriever errors must surface as 503 with sanitized detail
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_search_returns_503_when_retriever_raises(monkeypatch):
    """If the retriever explodes, the endpoint returns 503 with a generic message
    (no internal exception details leaked to the client)."""

    class _Exploder:
        async def retrieve(self, *args, **kwargs):
            raise RuntimeError("internal pinecone DNS panic — secret hostname")

    monkeypatch.setattr(catalog_module, "_retriever", _Exploder())

    app = FastAPI()
    app.include_router(catalog_router, prefix="/api/v1")
    c = TestClient(app, raise_server_exceptions=False)

    resp = c.get("/api/v1/catalog/search", params={"q": "anything"})
    assert resp.status_code == 503
    detail = resp.json()["detail"]
    assert "RuntimeError" in detail  # type name is fine to expose
    assert "secret hostname" not in detail  # internal message is not leaked
