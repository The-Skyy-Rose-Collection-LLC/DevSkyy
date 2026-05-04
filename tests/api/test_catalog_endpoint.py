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

    def get_info(self) -> dict:
        return {
            "embedder": {"provider": "voyage", "dimension": 1024},
            "namespace": "catalog",
            "initialized": True,
        }

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
    """Each test gets a clean singleton slot AND a fresh answer cache.

    Resetting the retriever isn't enough now that /answer caches responses —
    cached answers from one test would short-circuit the retriever in the next,
    masking bugs (e.g. 503 error path tests would see the cache and return 200).
    """
    monkeypatch.setattr(catalog_module, "_retriever", None)
    monkeypatch.setattr(catalog_module, "_answer_cache", None)


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
    detail = resp.json()["detail"]
    assert "zz-999" in detail
    # Server filesystem path must NOT leak in 404 detail (security/info-disclosure)
    assert "/Users/" not in detail
    assert ".csv" not in detail
    assert "DevSkyy" not in detail


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


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retriever_answer_question_passes_full_branding_to_llm(monkeypatch):
    """Per-match BRANDING SPEC budget must accommodate real-world dossier content.

    SkyyRose dossier branding_blocks routinely run 1500-3000 chars. A 300-char
    truncation lost details past the first paragraph (e.g. hood interior linings,
    sleeve placements). This regression test pins the budget at >=1000 chars
    so it can't be silently shrunk back.
    """
    from unittest.mock import AsyncMock, MagicMock

    from orchestration.catalog_retriever import CatalogMatch, CatalogRetriever

    # Construct a long branding spec where the answer detail lives at char ~1100
    # — past the old 300-char cap, but inside the new budget.
    long_branding = (
        "Front: silicone cut-out patch on right chest, white/grey tonal. "
        "Front pocket: clean, no logo. "
        "Front drawstrings: white flat. "
        + ("PADDING. " * 80)  # ~720 chars of filler
        + "HOOD-INSIDE: GREY contrast lining with the Black Rose logo "
        "sublimated throughout — repeating three-rose-cluster pattern. "
        "Visible only when hood is laid open."
    )
    # Confirm fixture invariants:
    #   - the load-bearing detail is past the old 300-char cap (would have been truncated)
    #   - and within the new 1500-char budget (must be visible after fix)
    detail_pos = long_branding.index("GREY contrast lining")
    assert detail_pos > 300, f"fixture detail at char {detail_pos} — must be past old 300 cap"
    assert (
        detail_pos < 1500
    ), f"fixture detail at char {detail_pos} — must be within new 1500 budget"

    fake_response = MagicMock()
    fake_text_block = MagicMock(type="text")
    fake_text_block.text = "Inside the hood is a [br-005] grey contrast lining."
    fake_response.content = [fake_text_block]
    fake_response.usage = MagicMock(input_tokens=500, output_tokens=20)

    fake_anthropic = MagicMock()
    fake_anthropic.messages.create = AsyncMock(return_value=fake_response)

    retriever = CatalogRetriever()
    retriever._initialized = True

    async def fake_retrieve(query, *, top_k=5, collection=None):
        return [
            CatalogMatch(
                sku="br-005",
                name="BLACK Rose Hoodie — Signature Edition",
                collection="black-rose",
                score=0.9,
                branding_spec=long_branding,
                description="black pullover hoodie",
            ),
        ]

    monkeypatch.setattr(retriever, "retrieve", fake_retrieve)

    await retriever.answer_question("what's inside the hood?", anthropic_client=fake_anthropic)

    user_content = fake_anthropic.messages.create.call_args.kwargs["messages"][0]["content"]
    # The hood-interior detail (past char 1000 in the dossier) MUST reach the LLM.
    # If anyone shrinks the per-match budget below ~1100 chars this test fails.
    assert "GREY contrast lining" in user_content, (
        "BRANDING SPEC budget too small — detail past char 1000 was truncated. "
        "Tightening commit (catalog_retriever.py answer_question) explicitly raised "
        "this from 300 to 1500 chars; do not regress."
    )
    # Block format uses === separators
    assert "===" in user_content
    # SKU + collection are present in the block header
    assert "[br-005]" in user_content
    assert "black-rose" in user_content
    # Description is included
    assert "DESCRIPTION:" in user_content


# ---------------------------------------------------------------------------
# /answer caching
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_answer_cache_miss_then_hit(client):
    """First call populates cache; second identical call short-circuits."""
    r1 = client.get("/api/v1/catalog/answer", params={"q": "what black hoodies?"})
    assert r1.status_code == 200
    assert r1.json()["cache_hit"] is False

    r2 = client.get("/api/v1/catalog/answer", params={"q": "what black hoodies?"})
    assert r2.status_code == 200
    assert r2.json()["cache_hit"] is True
    # Same answer text — cached response is faithfully replayed
    assert r2.json()["answer"] == r1.json()["answer"]


@pytest.mark.unit
def test_answer_cache_normalizes_query_case_and_whitespace(client):
    """Trivially-different queries should share a cache slot."""
    r1 = client.get("/api/v1/catalog/answer", params={"q": "What Black Hoodies?"})
    assert r1.json()["cache_hit"] is False

    # Same words, different case + extra whitespace — should be a cache hit
    r2 = client.get("/api/v1/catalog/answer", params={"q": "  what black hoodies?  "})
    assert r2.json()["cache_hit"] is True


@pytest.mark.unit
def test_answer_cache_distinguishes_top_k(client):
    """Different top_k values must NOT share a cache slot — context differs."""
    r1 = client.get("/api/v1/catalog/answer", params={"q": "anything", "top_k": 3})
    assert r1.json()["cache_hit"] is False

    r2 = client.get("/api/v1/catalog/answer", params={"q": "anything", "top_k": 5})
    assert r2.json()["cache_hit"] is False  # different top_k = different cache key


@pytest.mark.unit
def test_cache_stats_endpoint(client):
    """GET /cache/stats reports hit/miss counts and configuration."""
    # Warm the cache with one miss + one hit
    client.get("/api/v1/catalog/answer", params={"q": "alpha"})
    client.get("/api/v1/catalog/answer", params={"q": "alpha"})

    resp = client.get("/api/v1/catalog/cache/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["hits"] == 1
    assert body["misses"] == 1
    assert body["hit_rate_percent"] == 50.0
    assert body["size"] == 1
    assert body["maxsize"] >= 1
    assert body["ttl_seconds"] >= 0


@pytest.mark.unit
def test_cache_clear_endpoint(client):
    """POST /cache/clear empties the cache and resets counters."""
    client.get("/api/v1/catalog/answer", params={"q": "alpha"})
    client.get("/api/v1/catalog/answer", params={"q": "alpha"})

    resp = client.post("/api/v1/catalog/cache/clear")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    stats = client.get("/api/v1/catalog/cache/stats").json()
    assert stats["hits"] == 0
    assert stats["misses"] == 0
    assert stats["size"] == 0


@pytest.mark.unit
def test_cache_disabled_when_ttl_zero(monkeypatch, fake_matches):
    """CATALOG_ANSWER_CACHE_TTL=0 disables caching entirely."""
    # Build a cache with TTL=0 directly and verify get/put are no-ops
    import asyncio

    from api.v1.catalog import AnswerCache

    cache = AnswerCache(maxsize=10, ttl_seconds=0)

    async def _run():
        await cache.put("q", 5, {"answer": "test"})
        result = await cache.get("q", 5)
        return result

    assert asyncio.run(_run()) is None
    assert cache.get_stats()["size"] == 0


# ---------------------------------------------------------------------------
# /answer/stream — Server-Sent Events
# ---------------------------------------------------------------------------


class _FakeStreamContext:
    """Minimal mock of anthropic's `messages.stream()` async-context manager."""

    def __init__(
        self, deltas: list[str], final_input_tokens: int = 100, final_output_tokens: int = 30
    ):
        self._deltas = deltas
        self._final_input = final_input_tokens
        self._final_output = final_output_tokens

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    @property
    def text_stream(self):
        async def _gen():
            for d in self._deltas:
                yield d

        return _gen()

    async def get_final_message(self):
        from unittest.mock import MagicMock

        msg = MagicMock()
        msg.usage = MagicMock(input_tokens=self._final_input, output_tokens=self._final_output)
        return msg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retriever_answer_question_stream_emits_correct_chunk_sequence(monkeypatch):
    """Streaming yields: matches → text deltas → done — in that order."""
    from unittest.mock import MagicMock

    from orchestration.catalog_retriever import CatalogMatch, CatalogRetriever

    fake_anthropic = MagicMock()
    fake_anthropic.messages.stream = MagicMock(
        return_value=_FakeStreamContext(
            deltas=["Inside the hood ", "is a [br-005] grey ", "contrast lining."],
            final_input_tokens=1500,
            final_output_tokens=42,
        )
    )

    retriever = CatalogRetriever()
    retriever._initialized = True

    async def fake_retrieve(query, *, top_k=5, collection=None):
        return [
            CatalogMatch(
                sku="br-005",
                name="BLACK Rose Hoodie",
                collection="black-rose",
                score=0.9,
                branding_spec="hood lining",
                description="black hoodie",
            )
        ]

    monkeypatch.setattr(retriever, "retrieve", fake_retrieve)

    chunks = []
    async for c in retriever.answer_question_stream(
        "what's inside the hood?", top_k=1, anthropic_client=fake_anthropic
    ):
        chunks.append(c)

    # Sequence: matches first, 3 text deltas, then done
    assert len(chunks) == 5
    assert chunks[0]["type"] == "matches"
    assert len(chunks[0]["matches"]) == 1
    assert chunks[0]["matches"][0]["sku"] == "br-005"

    # Text deltas in order
    assert [c["type"] for c in chunks[1:4]] == ["text", "text", "text"]
    assert chunks[1]["delta"] == "Inside the hood "
    assert chunks[2]["delta"] == "is a [br-005] grey "
    assert chunks[3]["delta"] == "contrast lining."

    # Done event has citations + token counts
    done = chunks[4]
    assert done["type"] == "done"
    assert done["citations"] == ["br-005"]  # parsed from accumulated deltas
    assert done["input_tokens"] == 1500
    assert done["output_tokens"] == 42
    assert done["model"] == "claude-haiku-4-5-20251001"


@pytest.mark.unit
def test_stream_endpoint_emits_sse_format(monkeypatch, fake_matches):
    """The /answer/stream endpoint produces text/event-stream with `data:` lines."""

    # Stub the retriever to use a fake anthropic stream
    class _Streamer:
        def __init__(self, matches):
            self._matches = matches

        async def answer_question_stream(self, q, *, top_k=5):
            from orchestration.catalog_retriever import _extract_citations

            yield {
                "type": "matches",
                "matches": [
                    {
                        "sku": m.sku,
                        "name": m.name,
                        "collection": m.collection,
                        "score": m.score,
                        "description": m.description,
                        "branding_spec": m.branding_spec,
                    }
                    for m in self._matches[:top_k]
                ],
            }
            for delta in ["Hello ", "[br-005] ", "world."]:
                yield {"type": "text", "delta": delta}
            yield {
                "type": "done",
                "citations": _extract_citations("Hello [br-005] world."),
                "input_tokens": 200,
                "output_tokens": 10,
                "model": "claude-haiku-4-5-20251001",
            }

    monkeypatch.setattr(catalog_module, "_retriever", _Streamer(fake_matches))

    app = FastAPI()
    app.include_router(catalog_router, prefix="/api/v1")
    c = TestClient(app)

    resp = c.get("/api/v1/catalog/answer/stream", params={"q": "test query"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    # Parse SSE: one event per "data: <json>\n\n" frame
    events = []
    for line in resp.text.split("\n\n"):
        line = line.strip()
        if line.startswith("data: "):
            import json as _json

            events.append(_json.loads(line[len("data: ") :]))

    types = [e["type"] for e in events]
    assert types[0] == "matches"
    assert types[-1] == "done"
    assert "text" in types  # at least one text delta
    # Citations end up in the final done event
    done = events[-1]
    assert done["citations"] == ["br-005"]


@pytest.mark.unit
def test_stream_endpoint_emits_error_event_on_failure(monkeypatch):
    """If the retriever raises mid-stream, an `error` event is emitted instead of crashing."""

    class _Exploder:
        async def answer_question_stream(self, q, *, top_k=5):
            raise RuntimeError("voyage SDK timeout — internal hostname")
            yield  # unreachable, but makes this an async generator

    monkeypatch.setattr(catalog_module, "_retriever", _Exploder())

    app = FastAPI()
    app.include_router(catalog_router, prefix="/api/v1")
    c = TestClient(app, raise_server_exceptions=False)

    resp = c.get("/api/v1/catalog/answer/stream", params={"q": "anything"})
    assert resp.status_code == 200  # stream itself opens fine
    # The error is in the stream body, not the HTTP status
    assert "error" in resp.text
    assert "RuntimeError" in resp.text
    assert "internal hostname" not in resp.text  # internal detail still redacted
