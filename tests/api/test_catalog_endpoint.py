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

    async def find_similar_by_sku(self, sku, *, top_k=5):
        # Return all matches except the source SKU
        return [m for m in self._matches if m.sku != sku][:top_k]

    async def answer_question(
        self, question, *, top_k=5, model=None, max_tokens=400, anthropic_client=None
    ):
        # Return a synthetic CatalogAnswer that exercises the response shape.
        # Real LLM behavior is verified at the orchestration layer, not here.
        from orchestration.catalog_retriever import CatalogAnswer

        cited_matches = self._matches[:top_k]
        # Build a fake answer that cites the top SKU to exercise citation parsing
        cited_sku = cited_matches[0].sku if cited_matches else ""
        answer = (
            f"Based on the catalog, [{cited_sku}] is a strong match for your question."
            if cited_sku
            else "I don't have product information matching your question."
        )
        return CatalogAnswer(
            question=question,
            answer=answer,
            citations=[cited_sku] if cited_sku else [],
            matches=cited_matches,
            model=model or "claude-haiku-4-5-20251001",
            input_tokens=200,
            output_tokens=50,
        )


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


# ---------------------------------------------------------------------------
# /products/{sku} — direct lookup (uses real catalog/dossier loaders)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_get_product_returns_full_detail_for_real_sku(client):
    """br-001 is a stable canonical SKU — assert structural shape, not exact values."""
    resp = client.get("/api/v1/catalog/products/br-001")
    assert resp.status_code == 200
    body = resp.json()
    assert body["sku"] == "br-001"
    assert body["collection"] == "black-rose"
    assert body["name"]  # non-empty
    # Dossier should be present for canonical SKUs
    assert body["dossier"] is not None
    assert body["dossier"]["slug"]
    # branding_block holds the rich per-product branding spec
    assert body["dossier"]["branding_block"]


@pytest.mark.unit
def test_get_product_returns_404_for_unknown_sku(client):
    resp = client.get("/api/v1/catalog/products/zz-999")
    assert resp.status_code == 404
    assert "zz-999" in resp.json()["detail"]


@pytest.mark.unit
def test_get_product_published_flag_is_bool(client):
    resp = client.get("/api/v1/catalog/products/br-001")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["published"], bool)
    assert isinstance(body["is_preorder"], bool)


# ---------------------------------------------------------------------------
# /products/{sku}/similar
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_similar_excludes_source_sku(client):
    """Source SKU must NOT appear in its own similar-results."""
    resp = client.get("/api/v1/catalog/products/br-005/similar")
    assert resp.status_code == 200
    body = resp.json()
    assert body["sku"] == "br-005"
    skus = [m["sku"] for m in body["matches"]]
    assert "br-005" not in skus  # the load-bearing assertion
    # Other matches from the fake retriever should be present
    assert "br-004" in skus or "lh-004" in skus


@pytest.mark.unit
def test_similar_top_k_validation(client):
    resp = client.get("/api/v1/catalog/products/br-005/similar", params={"top_k": 0})
    assert resp.status_code == 422
    resp = client.get("/api/v1/catalog/products/br-005/similar", params={"top_k": 21})
    assert resp.status_code == 422


@pytest.mark.unit
def test_similar_returns_404_for_unknown_sku(monkeypatch):
    """When the retriever raises KeyError (SKU not in catalog), surface as 404."""

    class _NotFound:
        async def find_similar_by_sku(self, sku, *, top_k=5):
            raise KeyError(f"SKU {sku!r} not found")

    monkeypatch.setattr(catalog_module, "_retriever", _NotFound())

    app = FastAPI()
    app.include_router(catalog_router, prefix="/api/v1")
    c = TestClient(app)

    resp = c.get("/api/v1/catalog/products/zz-999/similar")
    assert resp.status_code == 404


@pytest.mark.unit
def test_similar_returns_409_when_dossier_missing(monkeypatch):
    """When the source SKU exists but has no dossier, return 409 — not 503.

    A missing dossier is an authoring problem (data, not service), so
    surface a different code than infrastructure failure.
    """
    from skyyrose.core.dossier_loader import DossierMissingError

    class _NoDossier:
        async def find_similar_by_sku(self, sku, *, top_k=5):
            raise DossierMissingError(f"dossier missing for {sku}")

    monkeypatch.setattr(catalog_module, "_retriever", _NoDossier())

    app = FastAPI()
    app.include_router(catalog_router, prefix="/api/v1")
    c = TestClient(app)

    resp = c.get("/api/v1/catalog/products/br-001/similar")
    assert resp.status_code == 409


@pytest.mark.unit
def test_similar_returns_503_on_unexpected_error(monkeypatch):
    """Generic infrastructure errors still map to 503 with sanitized detail."""

    class _Exploder:
        async def find_similar_by_sku(self, *args, **kwargs):
            raise RuntimeError("voyage SDK timeout — internal hostname")

    monkeypatch.setattr(catalog_module, "_retriever", _Exploder())

    app = FastAPI()
    app.include_router(catalog_router, prefix="/api/v1")
    c = TestClient(app, raise_server_exceptions=False)

    resp = c.get("/api/v1/catalog/products/br-005/similar")
    assert resp.status_code == 503
    detail = resp.json()["detail"]
    assert "RuntimeError" in detail
    assert "internal hostname" not in detail


# ---------------------------------------------------------------------------
# /answer — RAG with LLM synthesis
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_answer_returns_grounded_response(client):
    """Endpoint returns the answer text + citations + matches + token counts."""
    resp = client.get("/api/v1/catalog/answer", params={"q": "what black hoodies do you have?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["question"] == "what black hoodies do you have?"
    assert body["answer"]  # non-empty
    assert isinstance(body["citations"], list)
    assert body["model"] == "claude-haiku-4-5-20251001"
    assert body["input_tokens"] == 200
    assert body["output_tokens"] == 50
    assert "elapsed_ms" in body
    # Fake retriever cites top match (br-005)
    assert "br-005" in body["citations"]
    # And surfaces the retrieval context
    assert len(body["matches"]) >= 1
    assert body["matches"][0]["sku"] == "br-005"


@pytest.mark.unit
def test_answer_default_top_k_is_5(client):
    resp = client.get("/api/v1/catalog/answer", params={"q": "anything"})
    assert resp.status_code == 200
    # Fake has 3 matches; top_k=5 returns all 3
    assert len(resp.json()["matches"]) == 3


@pytest.mark.unit
def test_answer_rejects_short_query(client):
    """Very short queries are rejected — RAG quality drops below 3 chars."""
    resp = client.get("/api/v1/catalog/answer", params={"q": "x"})
    assert resp.status_code == 422


@pytest.mark.unit
def test_answer_rejects_oversize_query(client):
    resp = client.get("/api/v1/catalog/answer", params={"q": "x" * 501})
    assert resp.status_code == 422


@pytest.mark.unit
def test_answer_top_k_validation(client):
    """top_k for /answer is capped at 10 (smaller than /search) — context budget for LLM."""
    resp = client.get("/api/v1/catalog/answer", params={"q": "anything", "top_k": 0})
    assert resp.status_code == 422
    resp = client.get("/api/v1/catalog/answer", params={"q": "anything", "top_k": 11})
    assert resp.status_code == 422


@pytest.mark.unit
def test_answer_returns_503_on_llm_error(monkeypatch):
    """Anthropic SDK errors map to 503 with sanitized detail (no leaked hostname)."""

    class _Exploder:
        async def answer_question(self, *args, **kwargs):
            raise RuntimeError("anthropic API DNS panic — secret hostname")

    monkeypatch.setattr(catalog_module, "_retriever", _Exploder())

    app = FastAPI()
    app.include_router(catalog_router, prefix="/api/v1")
    c = TestClient(app, raise_server_exceptions=False)

    resp = c.get("/api/v1/catalog/answer", params={"q": "anything"})
    assert resp.status_code == 503
    detail = resp.json()["detail"]
    assert "RuntimeError" in detail
    assert "secret hostname" not in detail


# ---------------------------------------------------------------------------
# answer_question contract — verify the retriever-level method (mocked LLM)
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retriever_answer_question_constructs_grounded_prompt(monkeypatch):
    """Verify CatalogRetriever.answer_question builds correct prompt + parses citations."""
    from unittest.mock import AsyncMock, MagicMock

    from orchestration.catalog_retriever import CatalogMatch, CatalogRetriever

    fake_response = MagicMock()
    fake_text_block = MagicMock(type="text")
    fake_text_block.text = (
        "The [br-005] BLACK Rose Hoodie is a heavyweight black hoodie with silver "
        "Cinzel embroidery. The [br-004] is a similar option without the signature trim. "
        "Also see [BR-005] which I'm citing again to test dedup."
    )
    fake_response.content = [fake_text_block]
    fake_response.usage = MagicMock(input_tokens=234, output_tokens=78)

    fake_anthropic = MagicMock()
    fake_anthropic.messages.create = AsyncMock(return_value=fake_response)

    # Stub retrieve so we don't hit Voyage/Pinecone
    retriever = CatalogRetriever()
    retriever._initialized = True

    async def fake_retrieve(query, *, top_k=5, collection=None):
        return [
            CatalogMatch(
                sku="br-005",
                name="BLACK Rose Hoodie",
                collection="black-rose",
                score=0.9,
                branding_spec="silver Cinzel",
                description="black hoodie",
            ),
            CatalogMatch(
                sku="br-004",
                name="BLACK Rose Hoodie",
                collection="black-rose",
                score=0.85,
                branding_spec="rose embroidery",
                description="black hoodie",
            ),
        ]

    monkeypatch.setattr(retriever, "retrieve", fake_retrieve)

    answer = await retriever.answer_question(
        "what black hoodies do you have?",
        top_k=2,
        anthropic_client=fake_anthropic,
    )

    # Citations are extracted in order of first mention, dedup'd, lowercase only
    # ([BR-005] uppercase is intentionally NOT matched by the citation regex)
    assert answer.citations == ["br-005", "br-004"]
    assert answer.input_tokens == 234
    assert answer.output_tokens == 78
    assert len(answer.matches) == 2
    assert answer.model == "claude-haiku-4-5-20251001"

    # Verify the prompt actually got sent to Claude with grounding context
    fake_anthropic.messages.create.assert_called_once()
    call_kwargs = fake_anthropic.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-haiku-4-5-20251001"
    user_content = call_kwargs["messages"][0]["content"]
    assert "br-005" in user_content
    assert "br-004" in user_content
    assert "what black hoodies do you have?" in user_content


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retriever_answer_question_handles_no_matches(monkeypatch):
    """When retrieval returns nothing, the LLM is told to refuse rather than hallucinate."""
    from unittest.mock import AsyncMock, MagicMock

    from orchestration.catalog_retriever import CatalogRetriever

    fake_response = MagicMock()
    fake_text_block = MagicMock(type="text")
    fake_text_block.text = "I don't have any products that match that query."
    fake_response.content = [fake_text_block]
    fake_response.usage = MagicMock(input_tokens=80, output_tokens=15)

    fake_anthropic = MagicMock()
    fake_anthropic.messages.create = AsyncMock(return_value=fake_response)

    retriever = CatalogRetriever()
    retriever._initialized = True

    async def fake_retrieve(query, *, top_k=5, collection=None):
        return []

    monkeypatch.setattr(retriever, "retrieve", fake_retrieve)

    answer = await retriever.answer_question(
        "what motorcycle helmets do you sell?",
        anthropic_client=fake_anthropic,
    )

    assert answer.citations == []
    assert len(answer.matches) == 0
    # Prompt must instruct the LLM to refuse; no hallucinated context
    user_content = fake_anthropic.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "No catalog excerpts" in user_content
    assert "without inventing" in user_content
