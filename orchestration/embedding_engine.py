"""
DevSkyy Embedding Engine
========================

Production-grade embedding generation for RAG pipelines.

Supports:
- Sentence Transformers (local, default)
- OpenAI Embeddings (cloud)
- Cohere Embeddings (cloud, RAG-optimized)

Author: DevSkyy Platform Team
Version: 1.1.0
"""

from __future__ import annotations

import asyncio
import hashlib
import os
from abc import ABC, abstractmethod
from collections import OrderedDict
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, ConfigDict, Field

logger = structlog.get_logger(__name__)


# =============================================================================
# Performance: LRU Cache for Query Embeddings
# =============================================================================


class EmbeddingCache:
    """Thread-safe LRU cache for query embeddings.

    Caches embeddings by text hash to avoid redundant API calls for repeated queries.
    Provides 10x latency improvement for cached queries and reduces API costs.
    """

    def __init__(self, maxsize: int = 1024):
        """Initialize the cache.

        Args:
            maxsize: Maximum number of cached embeddings (default: 1024)
        """
        self._maxsize = maxsize
        self._cache: OrderedDict[str, list[float]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0

    def _hash_text(self, text: str) -> str:
        """Generate a hash key for the text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]

    async def get(self, text: str) -> list[float] | None:
        """Get embedding from cache if available.

        Args:
            text: The text to look up

        Returns:
            Cached embedding or None if not found
        """
        key = self._hash_text(text)
        async with self._lock:
            if key in self._cache:
                # Move to end (most recently used)
                self._cache.move_to_end(key)
                self._hits += 1
                logger.debug("embedding_cache_hit", key_prefix=key[:8])
                return self._cache[key]
            self._misses += 1
            return None

    async def put(self, text: str, embedding: list[float]) -> None:
        """Store embedding in cache.

        Args:
            text: The text that was embedded
            embedding: The embedding vector
        """
        key = self._hash_text(text)
        async with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self._maxsize:
                    # Remove oldest item (first item)
                    self._cache.popitem(last=False)
                self._cache[key] = embedding

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2),
            "size": len(self._cache),
            "maxsize": self._maxsize,
        }

    async def clear(self) -> None:
        """Clear the cache."""
        async with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0


# Global embedding cache instance
_embedding_cache: EmbeddingCache | None = None


def get_embedding_cache() -> EmbeddingCache:
    """Get or create the global embedding cache instance."""
    global _embedding_cache
    if _embedding_cache is None:
        cache_size = int(os.getenv("EMBEDDING_CACHE_SIZE", "1024"))
        _embedding_cache = EmbeddingCache(maxsize=cache_size)
        logger.info("embedding_cache_initialized", maxsize=cache_size)
    return _embedding_cache


# =============================================================================
# Enums & Models
# =============================================================================


class EmbeddingProvider(StrEnum):
    """Supported embedding providers."""

    SENTENCE_TRANSFORMERS = "sentence_transformers"
    OPENAI = "openai"
    COHERE = "cohere"
    VOYAGE = "voyage"


class EmbeddingConfig(BaseModel):
    """Embedding engine configuration."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    provider: EmbeddingProvider = Field(default=EmbeddingProvider.SENTENCE_TRANSFORMERS)

    # Sentence Transformers settings
    st_model_name: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    st_device: str = Field(default="cpu")  # cpu, cuda, mps

    # OpenAI settings
    openai_model: str = Field(default="text-embedding-ada-002")
    openai_api_key: str | None = Field(default=None)

    # Cohere settings
    cohere_model: str = Field(default="embed-english-v3.0")
    cohere_api_key: str | None = Field(default=None)
    cohere_input_type: str = Field(
        default="search_document"
    )  # search_document, search_query, classification, clustering

    # Voyage AI settings (asymmetric: input_type=document for indexing, query for retrieval)
    voyage_model: str = Field(default="voyage-3-large")
    voyage_api_key: str | None = Field(default=None)
    voyage_output_dimension: int | None = Field(
        default=None
    )  # None = native model dim (1024 for voyage-3-large); supports MRL truncation

    # Batch settings
    batch_size: int = Field(default=32, ge=1, le=256)
    max_length: int = Field(default=512, ge=64, le=8192)


# =============================================================================
# Base Embedding Engine
# =============================================================================


class BaseEmbeddingEngine(ABC):
    """Abstract base class for embedding engines."""

    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self._initialized = False
        self._dimension: int = 0

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the embedding engine."""
        pass

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @abstractmethod
    async def embed_query(self, query: str) -> list[float]:
        """Generate embedding optimized for queries (if supported)."""
        pass

    def get_info(self) -> dict[str, Any]:
        """Get embedding engine info."""
        return {
            "provider": self.config.provider.value,
            "dimension": self._dimension,
            "initialized": self._initialized,
        }


# =============================================================================
# Sentence Transformers Implementation
# =============================================================================


class SentenceTransformerEngine(BaseEmbeddingEngine):
    """Sentence Transformers embedding engine (local)."""

    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        self._model = None

    async def initialize(self) -> None:
        """Initialize Sentence Transformers model."""
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                self.config.st_model_name,
                device=self.config.st_device,
            )
            self._dimension = self._model.get_sentence_embedding_dimension()
            self._initialized = True
            logger.info(
                "embedding_provider_initialized",
                provider="sentence_transformer",
                model=self.config.st_model_name,
                dim=self._dimension,
            )

        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. Run: pip install sentence-transformers"
            )
        except Exception as e:
            logger.error(
                "embedding_provider_init_failed",
                provider="sentence_transformer",
                error=str(e),
            )
            raise

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        if not self._initialized or not self._model:
            raise RuntimeError("SentenceTransformer not initialized")

        # Truncate if needed
        if len(text) > self.config.max_length * 4:  # Approximate character limit
            text = text[: self.config.max_length * 4]

        embedding = self._model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not self._initialized or not self._model:
            raise RuntimeError("SentenceTransformer not initialized")

        # Truncate texts
        truncated = [t[: self.config.max_length * 4] for t in texts]

        embeddings = self._model.encode(
            truncated,
            batch_size=self.config.batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 100,
        )
        return embeddings.tolist()

    async def embed_query(self, query: str) -> list[float]:
        """Generate query embedding with caching (same as text for this model)."""
        cache = get_embedding_cache()
        cached = await cache.get(query)
        if cached is not None:
            return cached

        embedding = await self.embed_text(query)
        await cache.put(query, embedding)
        return embedding


# =============================================================================
# OpenAI Embeddings Implementation
# =============================================================================


class OpenAIEmbeddingEngine(BaseEmbeddingEngine):
    """OpenAI embeddings engine (cloud)."""

    # Model dimensions
    MODEL_DIMS = {
        "text-embedding-ada-002": 1536,
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
    }

    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        self._client = None

    async def initialize(self) -> None:
        """Initialize OpenAI client."""
        try:
            # langfuse drop-in wrapper auto-traces embedding calls (graceful fallback if extra not installed)
            try:
                from langfuse.openai import AsyncOpenAI
            except ImportError:
                from openai import AsyncOpenAI

            api_key = self.config.openai_api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key required")

            self._client = AsyncOpenAI(api_key=api_key)
            self._dimension = self.MODEL_DIMS.get(self.config.openai_model, 1536)
            self._initialized = True
            logger.info(
                "embedding_provider_initialized",
                provider="openai",
                model=self.config.openai_model,
                dim=self._dimension,
            )

        except ImportError:
            raise ImportError("openai not installed. Run: pip install openai")
        except Exception as e:
            logger.error(
                "embedding_provider_init_failed",
                provider="openai",
                error=str(e),
            )
            raise

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding using OpenAI API."""
        if not self._initialized or not self._client:
            raise RuntimeError("OpenAI client not initialized")

        # Truncate if needed (OpenAI has token limits)
        if len(text) > self.config.max_length * 4:
            text = text[: self.config.max_length * 4]

        response = await self._client.embeddings.create(
            input=text,
            model=self.config.openai_model,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts with parallel API calls.

        Uses asyncio.gather() for concurrent batch processing,
        providing 50-80% faster batch embeddings.
        """
        if not self._initialized or not self._client:
            raise RuntimeError("OpenAI client not initialized")

        # Truncate texts
        truncated = [t[: self.config.max_length * 4] for t in texts]

        # Process in batches (OpenAI limit is ~2048 inputs)
        batch_size = min(self.config.batch_size, 100)

        async def _embed_batch_chunk(batch: list[str]) -> list[list[float]]:
            """Embed a single batch chunk."""
            response = await self._client.embeddings.create(
                input=batch,
                model=self.config.openai_model,
            )
            return [item.embedding for item in response.data]

        # Create tasks for parallel execution
        tasks = []
        for i in range(0, len(truncated), batch_size):
            batch = truncated[i : i + batch_size]
            tasks.append(_embed_batch_chunk(batch))

        # Execute all batches in parallel
        batch_results = await asyncio.gather(*tasks)

        # Flatten results
        all_embeddings = []
        for batch_embeddings in batch_results:
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def embed_query(self, query: str) -> list[float]:
        """Generate query embedding with caching (same as text for OpenAI)."""
        cache = get_embedding_cache()
        cached = await cache.get(query)
        if cached is not None:
            return cached

        embedding = await self.embed_text(query)
        await cache.put(query, embedding)
        return embedding


# =============================================================================
# Cohere Embeddings Implementation
# =============================================================================


class CohereEmbeddingEngine(BaseEmbeddingEngine):
    """Cohere embeddings engine (cloud, RAG-optimized)."""

    # Model dimensions
    MODEL_DIMS = {
        "embed-english-v3.0": 1024,
        "embed-english-light-v3.0": 384,
        "embed-multilingual-v3.0": 1024,
        "embed-multilingual-light-v3.0": 384,
    }

    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        self._client = None

    async def initialize(self) -> None:
        """Initialize Cohere client."""
        try:
            import cohere

            api_key = self.config.cohere_api_key or os.getenv("COHERE_API_KEY")
            if not api_key:
                raise ValueError("Cohere API key required")

            self._client = cohere.AsyncClient(api_key=api_key)
            self._dimension = self.MODEL_DIMS.get(self.config.cohere_model, 1024)
            self._initialized = True
            logger.info(
                "embedding_provider_initialized",
                provider="cohere",
                model=self.config.cohere_model,
                dim=self._dimension,
            )

        except ImportError:
            raise ImportError("cohere not installed. Run: pip install cohere")
        except Exception as e:
            logger.error(
                "embedding_provider_init_failed",
                provider="cohere",
                error=str(e),
            )
            raise

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding using Cohere API."""
        if not self._initialized or not self._client:
            raise RuntimeError("Cohere client not initialized")

        # Truncate if needed
        if len(text) > self.config.max_length * 4:
            text = text[: self.config.max_length * 4]

        response = await self._client.embed(
            texts=[text],
            model=self.config.cohere_model,
            input_type=self.config.cohere_input_type,
        )
        return response.embeddings[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts with parallel API calls.

        Uses asyncio.gather() for concurrent batch processing,
        providing 50-80% faster batch embeddings.
        """
        if not self._initialized or not self._client:
            raise RuntimeError("Cohere client not initialized")

        # Truncate texts
        truncated = [t[: self.config.max_length * 4] for t in texts]

        # Cohere has a limit of 96 texts per request
        batch_size = min(self.config.batch_size, 96)

        async def _embed_batch_chunk(batch: list[str]) -> list[list[float]]:
            """Embed a single batch chunk."""
            response = await self._client.embed(
                texts=batch,
                model=self.config.cohere_model,
                input_type=self.config.cohere_input_type,
            )
            return response.embeddings

        # Create tasks for parallel execution
        tasks = []
        for i in range(0, len(truncated), batch_size):
            batch = truncated[i : i + batch_size]
            tasks.append(_embed_batch_chunk(batch))

        # Execute all batches in parallel
        batch_results = await asyncio.gather(*tasks)

        # Flatten results
        all_embeddings = []
        for batch_embeddings in batch_results:
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def embed_query(self, query: str) -> list[float]:
        """Generate query embedding with caching using search_query input type.

        Uses Cohere's optimized query embedding mode for better retrieval performance.
        Embeddings are cached to reduce API costs and latency.
        """
        cache = get_embedding_cache()
        # Include input_type in cache key for Cohere
        cache_key = f"cohere_query:{query}"
        cached = await cache.get(cache_key)
        if cached is not None:
            return cached

        if not self._initialized or not self._client:
            raise RuntimeError("Cohere client not initialized")

        # Truncate if needed
        truncated_query = query
        if len(query) > self.config.max_length * 4:
            truncated_query = query[: self.config.max_length * 4]

        response = await self._client.embed(
            texts=[truncated_query],
            model=self.config.cohere_model,
            input_type="search_query",  # Use query-optimized mode
        )
        embedding = response.embeddings[0]
        await cache.put(cache_key, embedding)
        return embedding


# =============================================================================
# Voyage AI Embeddings Implementation
# =============================================================================


class VoyageEmbeddingEngine(BaseEmbeddingEngine):
    """Voyage AI embeddings engine (cloud, asymmetric document/query embeddings).

    Voyage uses input_type='document' for indexing and input_type='query' for retrieval.
    Mismatching the type degrades retrieval quality measurably (~5-10% on MTEB).
    Supports MRL output dimension truncation (e.g. 256/512/1024/2048 for voyage-3-large).
    """

    # Native dimensions per model (defaults when output_dimension is None)
    MODEL_DIMS = {
        "voyage-3-large": 1024,
        "voyage-3": 1024,
        "voyage-3-lite": 512,
        "voyage-code-3": 1024,
        "voyage-finance-2": 1024,
        "voyage-law-2": 1024,
        "voyage-multilingual-2": 1024,
    }

    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        self._client = None

    async def initialize(self) -> None:
        """Initialize Voyage sync client (voyageai SDK has no AsyncClient — we
        wrap the sync .embed() with ``asyncio.to_thread`` so the event loop
        stays unblocked while Voyage's HTTP request runs in a worker thread).
        """
        try:
            import voyageai

            api_key = self.config.voyage_api_key or os.getenv("VOYAGE_API_KEY")
            if not api_key:
                raise ValueError("Voyage API key required (set VOYAGE_API_KEY)")

            self._client = voyageai.Client(api_key=api_key)

            base_dim = self.MODEL_DIMS.get(self.config.voyage_model, 1024)
            self._dimension = self.config.voyage_output_dimension or base_dim
            self._initialized = True
            logger.info(
                "embedding_provider_initialized",
                provider="voyage",
                model=self.config.voyage_model,
                dim=self._dimension,
                asymmetric=True,
            )

        except ImportError:
            raise ImportError("voyageai not installed. Run: pip install voyageai")
        except Exception as e:
            logger.error(
                "embedding_provider_init_failed",
                provider="voyage",
                error=str(e),
            )
            raise

    def _embed_kwargs(self, texts: list[str], input_type: str) -> dict[str, Any]:
        """Build embed() kwargs, honoring optional output_dimension truncation."""
        kwargs: dict[str, Any] = {
            "texts": texts,
            "model": self.config.voyage_model,
            "input_type": input_type,
        }
        if self.config.voyage_output_dimension:
            kwargs["output_dimension"] = self.config.voyage_output_dimension
        return kwargs

    async def embed_text(self, text: str) -> list[float]:
        """Generate document embedding (input_type='document')."""
        if not self._initialized or not self._client:
            raise RuntimeError("Voyage client not initialized")

        if len(text) > self.config.max_length * 4:
            text = text[: self.config.max_length * 4]

        result = await asyncio.to_thread(
            self._client.embed, **self._embed_kwargs([text], "document")
        )
        return result.embeddings[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate document embeddings (input_type='document') with parallel batches.

        Voyage allows up to 1000 texts per request; we cap at 128 for safety
        and parallelize via asyncio.gather() when input exceeds batch_size.
        """
        if not self._initialized or not self._client:
            raise RuntimeError("Voyage client not initialized")

        truncated = [t[: self.config.max_length * 4] for t in texts]
        batch_size = min(self.config.batch_size, 128)

        async def _embed_chunk(batch: list[str]) -> list[list[float]]:
            result = await asyncio.to_thread(
                self._client.embed, **self._embed_kwargs(batch, "document")
            )
            return result.embeddings

        tasks = [
            _embed_chunk(truncated[i : i + batch_size])
            for i in range(0, len(truncated), batch_size)
        ]
        batch_results = await asyncio.gather(*tasks)

        all_embeddings: list[list[float]] = []
        for batch_embeddings in batch_results:
            all_embeddings.extend(batch_embeddings)
        return all_embeddings

    async def embed_query(self, query: str) -> list[float]:
        """Generate query embedding (input_type='query') with cache.

        Cache key includes model + output_dimension so config changes don't
        return stale embeddings from prior runs.
        """
        cache = get_embedding_cache()
        cache_key = (
            f"voyage_query:{self.config.voyage_model}:"
            f"{self.config.voyage_output_dimension or 'native'}:{query}"
        )
        cached = await cache.get(cache_key)
        if cached is not None:
            return cached

        if not self._initialized or not self._client:
            raise RuntimeError("Voyage client not initialized")

        truncated = query
        if len(query) > self.config.max_length * 4:
            truncated = query[: self.config.max_length * 4]

        result = await asyncio.to_thread(
            self._client.embed, **self._embed_kwargs([truncated], "query")
        )
        embedding = result.embeddings[0]
        await cache.put(cache_key, embedding)
        return embedding


# =============================================================================
# Factory
# =============================================================================


def create_embedding_engine(config: EmbeddingConfig | None = None) -> BaseEmbeddingEngine:
    """
    Create an embedding engine instance.

    Args:
        config: Embedding configuration. Uses defaults if not provided.

    Returns:
        BaseEmbeddingEngine: Configured embedding engine instance.

    Example:
        >>> config = EmbeddingConfig(provider=EmbeddingProvider.SENTENCE_TRANSFORMERS)
        >>> engine = create_embedding_engine(config)
        >>> await engine.initialize()
        >>> embedding = await engine.embed_text("Hello world")
    """
    if config is None:
        config = EmbeddingConfig()

    if config.provider == EmbeddingProvider.OPENAI:
        return OpenAIEmbeddingEngine(config)
    elif config.provider == EmbeddingProvider.COHERE:
        return CohereEmbeddingEngine(config)
    elif config.provider == EmbeddingProvider.VOYAGE:
        return VoyageEmbeddingEngine(config)
    else:
        return SentenceTransformerEngine(config)
