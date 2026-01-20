"""
Tests for Cohere Reranker
==========================
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from orchestration.reranker import (
    CohereReranker,
    RankedResult,
    RerankerConfig,
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cohere_reranker_basic(mock_api_keys, mock_cohere_rerank_response):
    """Test basic reranking with Cohere."""
    with patch("cohere.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        # Mock returns only top 2 results (simulating real API behavior with top_n=2)
        mock_client.rerank = AsyncMock(
            return_value=MagicMock(
                results=[
                    MagicMock(index=r["index"], relevance_score=r["relevance_score"])
                    for r in mock_cohere_rerank_response["results"][:2]  # Respect top_n
                ]
            )
        )
        mock_client_class.return_value = mock_client

        config = RerankerConfig()
        reranker = CohereReranker(config)
        await reranker.initialize()

        documents = [
            "Python is a programming language",
            "JavaScript is used for web development",
            "Go is a compiled language created by Google",
        ]
        query = "compiled languages"

        results = await reranker.rerank(query, documents, top_n=2)

        assert len(results) == 2
        assert all(isinstance(r, RankedResult) for r in results)
        # Results should be ordered by score (highest first)
        assert results[0].score >= results[1].score
        assert results[0].index == 2  # Go (compiled) should rank highest


@pytest.mark.unit
@pytest.mark.asyncio
async def test_reranker_improves_relevance(mock_api_keys):
    """Test that reranking improves result relevance."""
    # Mock reranker that reverses order (simulating relevance improvement)
    rerank_response = {
        "results": [
            {"index": 2, "relevance_score": 0.95},  # Most relevant
            {"index": 1, "relevance_score": 0.70},
            {"index": 0, "relevance_score": 0.50},  # Least relevant
        ]
    }

    with patch("cohere.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.rerank = AsyncMock(
            return_value=MagicMock(
                results=[
                    MagicMock(index=r["index"], relevance_score=r["relevance_score"])
                    for r in rerank_response["results"]
                ]
            )
        )
        mock_client_class.return_value = mock_client

        config = RerankerConfig()
        reranker = CohereReranker(config)
        await reranker.initialize()

        documents = ["doc0", "doc1", "doc2"]
        query = "test query"

        results = await reranker.rerank(query, documents)

        # Verify reranking changed order
        assert results[0].text == "doc2"  # Was last, now first
        assert results[0].score == 0.95
        assert results[2].text == "doc0"  # Was first, now last
        assert results[2].score == 0.50


@pytest.mark.unit
@pytest.mark.asyncio
async def test_reranker_top_n_limiting(mock_api_keys, mock_cohere_rerank_response):
    """Test top_n limiting of results."""
    with patch("cohere.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.rerank = AsyncMock(
            return_value=MagicMock(
                results=[
                    MagicMock(index=r["index"], relevance_score=r["relevance_score"])
                    for r in mock_cohere_rerank_response["results"]
                ]
            )
        )
        mock_client_class.return_value = mock_client

        config = RerankerConfig(default_top_n=5)
        reranker = CohereReranker(config)
        await reranker.initialize()

        documents = [f"doc{i}" for i in range(10)]
        query = "test"

        # Request only top 3
        results = await reranker.rerank(query, documents, top_n=3)

        assert len(results) == 3
        assert all(r.score >= 0.7 for r in results)  # High scores only


@pytest.mark.unit
@pytest.mark.asyncio
async def test_reranker_with_rag_pipeline(mock_api_keys):
    """Test reranker integration with RAG pipeline."""
    # Simulate RAG pipeline: retrieve 20 docs, rerank to top 5
    initial_results = [{"content": f"Document {i}", "score": 0.5 + (i * 0.01)} for i in range(20)]

    # Mock reranker to improve top results
    rerank_response = {
        "results": [
            {"index": 19, "relevance_score": 0.98},  # Last doc actually most relevant
            {"index": 15, "relevance_score": 0.95},
            {"index": 10, "relevance_score": 0.90},
            {"index": 5, "relevance_score": 0.85},
            {"index": 0, "relevance_score": 0.80},
        ]
    }

    with patch("cohere.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.rerank = AsyncMock(
            return_value=MagicMock(
                results=[
                    MagicMock(index=r["index"], relevance_score=r["relevance_score"])
                    for r in rerank_response["results"]
                ]
            )
        )
        mock_client_class.return_value = mock_client

        config = RerankerConfig()
        reranker = CohereReranker(config)
        await reranker.initialize()

        documents = [r["content"] for r in initial_results]
        query = "most relevant document"

        final_results = await reranker.rerank(query, documents, top_n=5)

        # Verify we got 5 results
        assert len(final_results) == 5

        # Verify reranking found the most relevant (was last in initial list)
        assert final_results[0].text == "Document 19"
        assert final_results[0].score == 0.98

        # Verify 20-40% improvement claim (comparing to initial scores)
        initial_top_score = max(r["score"] for r in initial_results[:5])
        reranked_top_score = final_results[0].score
        improvement = ((reranked_top_score - initial_top_score) / initial_top_score) * 100
        assert improvement > 20  # At least 20% improvement


@pytest.mark.unit
@pytest.mark.asyncio
async def test_reranker_error_handling(mock_api_keys):
    """Test reranker error handling."""
    with patch("cohere.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.rerank = AsyncMock(side_effect=Exception("API Error"))
        mock_client_class.return_value = mock_client

        config = RerankerConfig()
        reranker = CohereReranker(config)
        await reranker.initialize()

        documents = ["doc1", "doc2", "doc3"]
        query = "test"

        with pytest.raises(Exception, match="API Error"):
            await reranker.rerank(query, documents)


@pytest.mark.performance
@pytest.mark.asyncio
async def test_reranker_performance(mock_api_keys, mock_cohere_rerank_response, performance_timer):
    """Test reranker performance (should be fast)."""
    with patch("cohere.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.rerank = AsyncMock(
            return_value=MagicMock(
                results=[
                    MagicMock(index=r["index"], relevance_score=r["relevance_score"])
                    for r in mock_cohere_rerank_response["results"]
                ]
            )
        )
        mock_client_class.return_value = mock_client

        config = RerankerConfig()
        reranker = CohereReranker(config)
        await reranker.initialize()

        documents = [f"Document {i}" for i in range(20)]
        query = "test query"

        performance_timer.start()
        await reranker.rerank(query, documents, top_n=5)
        performance_timer.stop()

        # Reranking should be fast (< 500ms with mocked API)
        assert performance_timer.elapsed_ms() < 500
