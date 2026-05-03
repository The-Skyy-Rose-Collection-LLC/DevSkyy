"""
Tests for Voyage AI Embedding Engine
=====================================

Mirrors the Cohere test pattern in test_embedding_engine.py, adapted for Voyage's
sync SDK (no AsyncClient — engine wraps .embed() with asyncio.to_thread).

Coverage:
- Asymmetric document/query input_type routing
- MRL output_dimension truncation
- Cache key includes model + output_dimension
- Batch chunking + parallel asyncio.gather
- Truncation, missing API key, not initialized error, get_info
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from orchestration.embedding_engine import (
    EmbeddingConfig,
    EmbeddingProvider,
    VoyageEmbeddingEngine,
    get_embedding_cache,
)


def _make_voyage_result(n: int, dim: int = 1024) -> SimpleNamespace:
    """Build a fake voyageai .embed() result with ``n`` embeddings of size ``dim``."""
    # Use distinguishable embeddings (0.1, 0.2, 0.3, ...) so we can assert ordering
    embeddings = [[round(0.1 * (i + 1), 4)] * dim for i in range(n)]
    return SimpleNamespace(embeddings=embeddings, total_tokens=n)


@pytest.fixture
def mock_voyage_client():
    """Fake voyageai.Client — sync .embed() that returns matching-length embeddings."""
    client = MagicMock()

    def _embed(texts, model, input_type, **kwargs):
        # Honor output_dimension if caller passed it (MRL truncation)
        dim = kwargs.get("output_dimension", 1024)
        return _make_voyage_result(len(texts), dim=dim)

    client.embed.side_effect = _embed
    return client


@pytest.fixture
def voyage_api_key(monkeypatch):
    monkeypatch.setenv("VOYAGE_API_KEY", "test_voyage_key")


@pytest.fixture(autouse=True)
async def _clear_embedding_cache():
    """Voyage cache keys include model+dim; clear between tests to avoid bleed."""
    cache = get_embedding_cache()
    await cache.clear()
    yield
    await cache.clear()


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_voyage_initialize_dimension(voyage_api_key, mock_voyage_client, monkeypatch):
    """Native dim of voyage-3-large is 1024."""
    config = EmbeddingConfig(provider=EmbeddingProvider.VOYAGE)
    engine = VoyageEmbeddingEngine(config)

    monkeypatch.setattr("voyageai.Client", lambda **_kwargs: mock_voyage_client)
    await engine.initialize()

    assert engine.dimension == 1024
    assert engine._initialized is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_voyage_initialize_with_mrl_truncation(
    voyage_api_key, mock_voyage_client, monkeypatch
):
    """voyage_output_dimension overrides the model's native dimension (MRL)."""
    config = EmbeddingConfig(
        provider=EmbeddingProvider.VOYAGE,
        voyage_output_dimension=256,
    )
    engine = VoyageEmbeddingEngine(config)

    monkeypatch.setattr("voyageai.Client", lambda **_kwargs: mock_voyage_client)
    await engine.initialize()

    assert engine.dimension == 256


@pytest.mark.unit
def test_voyage_missing_api_key(monkeypatch):
    """Missing VOYAGE_API_KEY raises ValueError on initialize."""
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    config = EmbeddingConfig(provider=EmbeddingProvider.VOYAGE, voyage_api_key=None)
    engine = VoyageEmbeddingEngine(config)

    import asyncio

    with pytest.raises(ValueError, match="Voyage API key required"):
        asyncio.run(engine.initialize())


# ---------------------------------------------------------------------------
# Asymmetric document/query routing
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_voyage_embed_text_uses_document_input_type(
    voyage_api_key, mock_voyage_client, monkeypatch
):
    """embed_text() must call SDK with input_type='document' for indexing."""
    config = EmbeddingConfig(provider=EmbeddingProvider.VOYAGE)
    engine = VoyageEmbeddingEngine(config)
    monkeypatch.setattr("voyageai.Client", lambda **_kwargs: mock_voyage_client)
    await engine.initialize()

    embedding = await engine.embed_text("a black rose hoodie")

    assert len(embedding) == 1024
    mock_voyage_client.embed.assert_called_once()
    call_kwargs = mock_voyage_client.embed.call_args.kwargs
    assert call_kwargs["input_type"] == "document"
    assert call_kwargs["model"] == "voyage-3-large"
    assert call_kwargs["texts"] == ["a black rose hoodie"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_voyage_embed_query_uses_query_input_type(
    voyage_api_key, mock_voyage_client, monkeypatch
):
    """embed_query() must call SDK with input_type='query' for retrieval."""
    config = EmbeddingConfig(provider=EmbeddingProvider.VOYAGE)
    engine = VoyageEmbeddingEngine(config)
    monkeypatch.setattr("voyageai.Client", lambda **_kwargs: mock_voyage_client)
    await engine.initialize()

    embedding = await engine.embed_query("what hoodies are in stock?")

    assert len(embedding) == 1024
    mock_voyage_client.embed.assert_called_once()
    call_kwargs = mock_voyage_client.embed.call_args.kwargs
    assert call_kwargs["input_type"] == "query"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_voyage_embed_batch_uses_document_input_type(
    voyage_api_key, mock_voyage_client, monkeypatch
):
    """embed_batch() must use 'document' (it's an indexing path)."""
    config = EmbeddingConfig(provider=EmbeddingProvider.VOYAGE)
    engine = VoyageEmbeddingEngine(config)
    monkeypatch.setattr("voyageai.Client", lambda **_kwargs: mock_voyage_client)
    await engine.initialize()

    embeddings = await engine.embed_batch(["doc1", "doc2", "doc3"])

    assert len(embeddings) == 3
    assert all(len(e) == 1024 for e in embeddings)
    call_kwargs = mock_voyage_client.embed.call_args.kwargs
    assert call_kwargs["input_type"] == "document"


# ---------------------------------------------------------------------------
# MRL output_dimension truncation
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_voyage_passes_output_dimension_when_set(
    voyage_api_key, mock_voyage_client, monkeypatch
):
    """voyage_output_dimension is forwarded to the SDK (MRL truncation)."""
    config = EmbeddingConfig(provider=EmbeddingProvider.VOYAGE, voyage_output_dimension=512)
    engine = VoyageEmbeddingEngine(config)
    monkeypatch.setattr("voyageai.Client", lambda **_kwargs: mock_voyage_client)
    await engine.initialize()

    embedding = await engine.embed_text("hello")

    assert len(embedding) == 512  # mock honors output_dimension
    call_kwargs = mock_voyage_client.embed.call_args.kwargs
    assert call_kwargs.get("output_dimension") == 512


@pytest.mark.unit
@pytest.mark.asyncio
async def test_voyage_omits_output_dimension_when_none(
    voyage_api_key, mock_voyage_client, monkeypatch
):
    """When voyage_output_dimension is None, the kwarg must NOT be sent.

    Sending ``output_dimension=None`` to Voyage's SDK is treated as an explicit
    request and may differ from the native default. Better to omit entirely.
    """
    config = EmbeddingConfig(provider=EmbeddingProvider.VOYAGE, voyage_output_dimension=None)
    engine = VoyageEmbeddingEngine(config)
    monkeypatch.setattr("voyageai.Client", lambda **_kwargs: mock_voyage_client)
    await engine.initialize()

    await engine.embed_text("hello")

    call_kwargs = mock_voyage_client.embed.call_args.kwargs
    assert "output_dimension" not in call_kwargs


# ---------------------------------------------------------------------------
# Caching: cache key must include model + output_dimension
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_voyage_query_is_cached(voyage_api_key, mock_voyage_client, monkeypatch):
    """Second identical query hits the cache (single SDK call total)."""
    config = EmbeddingConfig(provider=EmbeddingProvider.VOYAGE)
    engine = VoyageEmbeddingEngine(config)
    monkeypatch.setattr("voyageai.Client", lambda **_kwargs: mock_voyage_client)
    await engine.initialize()

    e1 = await engine.embed_query("luxury hoodie")
    e2 = await engine.embed_query("luxury hoodie")

    assert e1 == e2
    assert mock_voyage_client.embed.call_count == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_voyage_cache_key_namespaces_by_dimension(
    voyage_api_key, mock_voyage_client, monkeypatch
):
    """Same query at different output_dimensions must NOT share cache entries."""
    monkeypatch.setattr("voyageai.Client", lambda **_kwargs: mock_voyage_client)

    e_native = VoyageEmbeddingEngine(
        EmbeddingConfig(provider=EmbeddingProvider.VOYAGE, voyage_output_dimension=None)
    )
    e_trunc = VoyageEmbeddingEngine(
        EmbeddingConfig(provider=EmbeddingProvider.VOYAGE, voyage_output_dimension=512)
    )
    await e_native.initialize()
    await e_trunc.initialize()

    v_native = await e_native.embed_query("luxury hoodie")
    v_trunc = await e_trunc.embed_query("luxury hoodie")

    # Two distinct SDK calls — cache did NOT collapse them
    assert mock_voyage_client.embed.call_count == 2
    assert len(v_native) == 1024
    assert len(v_trunc) == 512


# ---------------------------------------------------------------------------
# Batch chunking + parallel asyncio.gather
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_voyage_batch_chunking(voyage_api_key, mock_voyage_client, monkeypatch):
    """batch_size caps each SDK request; total docs returned must match input."""
    config = EmbeddingConfig(provider=EmbeddingProvider.VOYAGE, batch_size=32)
    engine = VoyageEmbeddingEngine(config)
    monkeypatch.setattr("voyageai.Client", lambda **_kwargs: mock_voyage_client)
    await engine.initialize()

    texts = [f"doc{i}" for i in range(100)]
    embeddings = await engine.embed_batch(texts)

    assert len(embeddings) == 100
    assert all(len(e) == 1024 for e in embeddings)
    # ceil(100/32) = 4 chunks
    assert mock_voyage_client.embed.call_count == 4


@pytest.mark.unit
@pytest.mark.asyncio
async def test_voyage_batch_caps_at_128(voyage_api_key, mock_voyage_client, monkeypatch):
    """Even with batch_size=256 in config, runtime cap is 128 per Voyage SDK guidance."""
    config = EmbeddingConfig(provider=EmbeddingProvider.VOYAGE, batch_size=256)
    engine = VoyageEmbeddingEngine(config)
    monkeypatch.setattr("voyageai.Client", lambda **_kwargs: mock_voyage_client)
    await engine.initialize()

    texts = [f"doc{i}" for i in range(200)]
    await engine.embed_batch(texts)

    # 200 docs / cap=128 = 2 chunks (128 + 72)
    assert mock_voyage_client.embed.call_count == 2
    first_call_texts = mock_voyage_client.embed.call_args_list[0].kwargs["texts"]
    assert len(first_call_texts) == 128


# ---------------------------------------------------------------------------
# Truncation, error paths, get_info
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_voyage_truncates_long_text(voyage_api_key, mock_voyage_client, monkeypatch):
    """Texts longer than max_length*4 chars are truncated before SDK call."""
    config = EmbeddingConfig(provider=EmbeddingProvider.VOYAGE, max_length=512)
    engine = VoyageEmbeddingEngine(config)
    monkeypatch.setattr("voyageai.Client", lambda **_kwargs: mock_voyage_client)
    await engine.initialize()

    long_text = "x" * 5000
    await engine.embed_text(long_text)

    sent = mock_voyage_client.embed.call_args.kwargs["texts"][0]
    assert len(sent) <= 512 * 4


@pytest.mark.unit
@pytest.mark.asyncio
async def test_voyage_not_initialized_error(voyage_api_key):
    """Using engine before initialize() raises RuntimeError."""
    config = EmbeddingConfig(provider=EmbeddingProvider.VOYAGE)
    engine = VoyageEmbeddingEngine(config)

    with pytest.raises(RuntimeError, match="not initialized"):
        await engine.embed_text("test")
    with pytest.raises(RuntimeError, match="not initialized"):
        await engine.embed_query("test")
    with pytest.raises(RuntimeError, match="not initialized"):
        await engine.embed_batch(["test"])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_voyage_get_info(voyage_api_key, mock_voyage_client, monkeypatch):
    """get_info returns provider/dimension/initialized."""
    config = EmbeddingConfig(provider=EmbeddingProvider.VOYAGE)
    engine = VoyageEmbeddingEngine(config)
    monkeypatch.setattr("voyageai.Client", lambda **_kwargs: mock_voyage_client)
    await engine.initialize()

    info = engine.get_info()
    assert info["provider"] == "voyage"
    assert info["dimension"] == 1024
    assert info["initialized"] is True
