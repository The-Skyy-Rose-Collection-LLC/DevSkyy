"""
DevSkyy Reranker
================

Production-grade reranking for RAG pipelines using Cohere Rerank API.

Reranking improves RAG relevance by 20-40% by re-scoring initial
vector search results using a cross-encoder model.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Enums & Models
# =============================================================================


class RerankerProvider(str, Enum):
    """Supported reranker providers."""

    COHERE = "cohere"


class RerankerConfig(BaseModel):
    """Reranker configuration."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    provider: RerankerProvider = Field(default=RerankerProvider.COHERE)

    # Cohere settings
    cohere_model: str = Field(default="rerank-english-v3.0")
    cohere_api_key: str | None = Field(default=None)

    # Reranking settings
    top_n: int = Field(default=5, ge=1, le=100)
    max_chunks_per_doc: int = Field(default=10, ge=1, le=100)


@dataclass
class RankedResult:
    """A single reranked result."""

    text: str
    score: float
    index: int
    metadata: dict[str, any] | None = None


# =============================================================================
# Base Reranker
# =============================================================================


class BaseReranker:
    """Abstract base class for rerankers."""

    def __init__(self, config: RerankerConfig):
        self.config = config
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the reranker."""
        raise NotImplementedError

    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_n: int | None = None,
    ) -> list[RankedResult]:
        """
        Rerank documents by relevance to query.

        Args:
            query: Search query
            documents: List of document texts to rerank
            top_n: Number of top results to return (defaults to config.top_n)

        Returns:
            List of RankedResult, sorted by relevance score (descending)
        """
        raise NotImplementedError

    async def rerank_with_metadata(
        self,
        query: str,
        documents: list[tuple[str, dict]],
        top_n: int | None = None,
    ) -> list[RankedResult]:
        """
        Rerank documents with metadata.

        Args:
            query: Search query
            documents: List of (text, metadata) tuples
            top_n: Number of top results to return

        Returns:
            List of RankedResult with metadata preserved
        """
        raise NotImplementedError


# =============================================================================
# Cohere Reranker Implementation
# =============================================================================


class CohereReranker(BaseReranker):
    """Cohere Rerank API implementation."""

    # Available models
    MODELS = [
        "rerank-english-v3.0",
        "rerank-multilingual-v3.0",
        "rerank-english-v2.0",
        "rerank-multilingual-v2.0",
    ]

    def __init__(self, config: RerankerConfig):
        super().__init__(config)
        self._client = None

    async def initialize(self) -> None:
        """Initialize Cohere client."""
        try:
            import cohere

            api_key = self.config.cohere_api_key or os.getenv("COHERE_API_KEY")
            if not api_key:
                raise ValueError("Cohere API key required for reranking")

            self._client = cohere.AsyncClient(api_key=api_key)
            self._initialized = True
            logger.info(f"Cohere Reranker initialized: {self.config.cohere_model}")

        except ImportError:
            raise ImportError("cohere not installed. Run: pip install cohere")
        except Exception as e:
            logger.error(f"Cohere Reranker initialization failed: {e}")
            raise

    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_n: int | None = None,
    ) -> list[RankedResult]:
        """Rerank documents using Cohere Rerank API."""
        if not self._initialized or not self._client:
            raise RuntimeError("Cohere reranker not initialized")

        if not documents:
            return []

        top_n = top_n or self.config.top_n

        # Cohere Rerank API call
        response = await self._client.rerank(
            model=self.config.cohere_model,
            query=query,
            documents=documents,
            top_n=min(top_n, len(documents)),
            max_chunks_per_doc=self.config.max_chunks_per_doc,
        )

        # Convert to RankedResult
        results = [
            RankedResult(
                text=documents[result.index],
                score=result.relevance_score,
                index=result.index,
                metadata=None,
            )
            for result in response.results
        ]

        logger.debug(
            f"Reranked {len(documents)} documents, returned top {len(results)}"
        )
        return results

    async def rerank_with_metadata(
        self,
        query: str,
        documents: list[tuple[str, dict]],
        top_n: int | None = None,
    ) -> list[RankedResult]:
        """Rerank documents with metadata preserved."""
        if not self._initialized or not self._client:
            raise RuntimeError("Cohere reranker not initialized")

        if not documents:
            return []

        # Extract texts and metadata
        texts = [doc[0] for doc in documents]
        metadata_list = [doc[1] for doc in documents]

        top_n = top_n or self.config.top_n

        # Rerank using texts
        response = await self._client.rerank(
            model=self.config.cohere_model,
            query=query,
            documents=texts,
            top_n=min(top_n, len(texts)),
            max_chunks_per_doc=self.config.max_chunks_per_doc,
        )

        # Convert to RankedResult with metadata
        results = [
            RankedResult(
                text=texts[result.index],
                score=result.relevance_score,
                index=result.index,
                metadata=metadata_list[result.index],
            )
            for result in response.results
        ]

        logger.debug(
            f"Reranked {len(documents)} documents with metadata, returned top {len(results)}"
        )
        return results


# =============================================================================
# Factory
# =============================================================================


def create_reranker(config: RerankerConfig | None = None) -> BaseReranker:
    """
    Create a reranker instance.

    Args:
        config: Reranker configuration. Uses defaults if not provided.

    Returns:
        BaseReranker: Configured reranker instance.

    Example:
        >>> config = RerankerConfig(provider=RerankerProvider.COHERE)
        >>> reranker = create_reranker(config)
        >>> await reranker.initialize()
        >>> results = await reranker.rerank("query", ["doc1", "doc2", "doc3"])
    """
    if config is None:
        config = RerankerConfig()

    if config.provider == RerankerProvider.COHERE:
        return CohereReranker(config)
    else:
        raise ValueError(f"Unsupported reranker provider: {config.provider}")
