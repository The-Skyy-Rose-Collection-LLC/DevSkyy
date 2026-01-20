"""
Tests for Cohere Embedding Engine
==================================

Tests Cohere embedding functionality following TEST_STRATEGY.md patterns.

Coverage:
- Query embedding (search_query input type)
- Batch embedding (search_document input type)
- Dimension validation
- API error handling
"""

import pytest

from orchestration.embedding_engine import (
    CohereEmbeddingEngine,
    EmbeddingConfig,
    EmbeddingProvider,
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cohere_embed_query(mock_api_keys, mock_cohere_client, monkeypatch):
    """Test query embedding with Cohere."""
    config = EmbeddingConfig(provider=EmbeddingProvider.COHERE)
    engine = CohereEmbeddingEngine(config)

    # Mock the Cohere client
    monkeypatch.setattr("cohere.AsyncClient", lambda **_kwargs: mock_cohere_client)

    await engine.initialize()

    # Test query embedding
    embedding = await engine.embed_query("test query")

    assert len(embedding) == 1024  # embed-english-v3.0 dimension
    assert all(isinstance(v, float) for v in embedding)
    assert embedding == [0.1] * 1024  # First embedding from mock

    # Verify the mock was called with search_query input type
    mock_cohere_client.embed.assert_called_once()
    call_kwargs = mock_cohere_client.embed.call_args.kwargs
    assert call_kwargs["input_type"] == "search_query"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cohere_embed_batch(mock_api_keys, mock_cohere_client, monkeypatch):
    """Test batch embedding with Cohere."""
    config = EmbeddingConfig(provider=EmbeddingProvider.COHERE)
    engine = CohereEmbeddingEngine(config)

    # Mock the Cohere client
    monkeypatch.setattr("cohere.AsyncClient", lambda **_kwargs: mock_cohere_client)

    await engine.initialize()

    # Test batch embedding
    texts = ["doc1", "doc2", "doc3"]
    embeddings = await engine.embed_batch(texts)

    assert len(embeddings) == 3
    assert all(len(e) == 1024 for e in embeddings)
    assert embeddings[0] == [0.1] * 1024
    assert embeddings[1] == [0.2] * 1024
    assert embeddings[2] == [0.3] * 1024

    # Verify the mock was called with search_document input type
    mock_cohere_client.embed.assert_called_once()
    call_kwargs = mock_cohere_client.embed.call_args.kwargs
    assert call_kwargs["input_type"] == "search_document"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cohere_dimension(mock_api_keys, mock_cohere_client, monkeypatch):
    """Test Cohere embedding dimension is correctly set."""
    config = EmbeddingConfig(provider=EmbeddingProvider.COHERE)
    engine = CohereEmbeddingEngine(config)

    # Mock the Cohere client
    monkeypatch.setattr("cohere.AsyncClient", lambda **_kwargs: mock_cohere_client)

    await engine.initialize()

    assert engine.dimension == 1024
    assert engine._initialized is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cohere_embed_single_text(mock_api_keys, mock_cohere_client, monkeypatch):
    """Test single text embedding (uses search_document input type)."""
    config = EmbeddingConfig(provider=EmbeddingProvider.COHERE)
    engine = CohereEmbeddingEngine(config)

    # Mock the Cohere client
    monkeypatch.setattr("cohere.AsyncClient", lambda **_kwargs: mock_cohere_client)

    await engine.initialize()

    # Test single text embedding
    embedding = await engine.embed_text("test document")

    assert len(embedding) == 1024
    assert all(isinstance(v, float) for v in embedding)

    # Verify the mock was called with search_document input type
    mock_cohere_client.embed.assert_called_once()
    call_kwargs = mock_cohere_client.embed.call_args.kwargs
    assert call_kwargs["input_type"] == "search_document"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cohere_embed_truncation(mock_api_keys, mock_cohere_client, monkeypatch):
    """Test that long texts are truncated."""
    config = EmbeddingConfig(provider=EmbeddingProvider.COHERE, max_length=512)
    engine = CohereEmbeddingEngine(config)

    # Mock the Cohere client
    monkeypatch.setattr("cohere.AsyncClient", lambda **_kwargs: mock_cohere_client)

    await engine.initialize()

    # Create a very long text (> max_length * 4 characters)
    long_text = "a" * 3000
    embedding = await engine.embed_text(long_text)

    # Verify text was truncated
    assert len(embedding) == 1024
    call_args = mock_cohere_client.embed.call_args.kwargs
    actual_text = call_args["texts"][0]
    assert len(actual_text) <= 512 * 4  # max_length * 4


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cohere_batch_chunking(mock_api_keys, monkeypatch):
    """Test that large batches are chunked (Cohere limit: 96 texts)."""
    from unittest.mock import AsyncMock

    config = EmbeddingConfig(provider=EmbeddingProvider.COHERE, batch_size=32)
    engine = CohereEmbeddingEngine(config)

    # Create a custom mock that returns the correct number of embeddings based on input
    custom_mock = AsyncMock()

    async def mock_embed_dynamic(**kwargs):
        texts = kwargs.get("texts", [])
        # Return embeddings matching the number of texts
        embed_response = AsyncMock()
        embed_response.embeddings = [[0.1] * 1024 for _ in texts]
        return embed_response

    custom_mock.embed = mock_embed_dynamic

    # Mock the Cohere client
    monkeypatch.setattr("cohere.AsyncClient", lambda **_kwargs: custom_mock)

    await engine.initialize()

    # Test with 100 texts (should be chunked into batches of 32)
    texts = [f"doc{i}" for i in range(100)]
    embeddings = await engine.embed_batch(texts)

    # Should receive all 100 embeddings
    assert len(embeddings) == 100
    assert all(len(e) == 1024 for e in embeddings)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cohere_not_initialized_error(mock_api_keys):
    """Test that using engine before initialization raises error."""
    config = EmbeddingConfig(provider=EmbeddingProvider.COHERE)
    engine = CohereEmbeddingEngine(config)

    # Don't initialize

    with pytest.raises(RuntimeError, match="not initialized"):
        await engine.embed_text("test")

    with pytest.raises(RuntimeError, match="not initialized"):
        await engine.embed_query("test")

    with pytest.raises(RuntimeError, match="not initialized"):
        await engine.embed_batch(["test"])


@pytest.mark.unit
def test_cohere_missing_api_key():
    """Test that missing API key raises error."""
    config = EmbeddingConfig(provider=EmbeddingProvider.COHERE, cohere_api_key=None)
    engine = CohereEmbeddingEngine(config)

    import os

    # Remove env var if it exists
    old_key = os.environ.pop("COHERE_API_KEY", None)

    try:
        import asyncio

        with pytest.raises(ValueError, match="API key required"):
            asyncio.run(engine.initialize())
    finally:
        # Restore env var
        if old_key:
            os.environ["COHERE_API_KEY"] = old_key


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cohere_get_info(mock_api_keys, mock_cohere_client, monkeypatch):
    """Test get_info returns correct metadata."""
    config = EmbeddingConfig(provider=EmbeddingProvider.COHERE)
    engine = CohereEmbeddingEngine(config)

    # Mock the Cohere client
    monkeypatch.setattr("cohere.AsyncClient", lambda **_kwargs: mock_cohere_client)

    await engine.initialize()

    info = engine.get_info()

    assert info["provider"] == "cohere"
    assert info["dimension"] == 1024
    assert info["initialized"] is True
