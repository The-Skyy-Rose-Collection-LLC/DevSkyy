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

import logging
import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Enums & Models
# =============================================================================


class EmbeddingProvider(str, Enum):
    """Supported embedding providers."""

    SENTENCE_TRANSFORMERS = "sentence_transformers"
    OPENAI = "openai"
    COHERE = "cohere"


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
    cohere_input_type: str = Field(default="search_document")  # search_document, search_query, classification, clustering

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
                f"SentenceTransformer initialized: {self.config.st_model_name} (dim={self._dimension})"
            )

        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. Run: pip install sentence-transformers"
            )
        except Exception as e:
            logger.error(f"SentenceTransformer initialization failed: {e}")
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
        """Generate query embedding (same as text for this model)."""
        return await self.embed_text(query)


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
            from openai import AsyncOpenAI

            api_key = self.config.openai_api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key required")

            self._client = AsyncOpenAI(api_key=api_key)
            self._dimension = self.MODEL_DIMS.get(self.config.openai_model, 1536)
            self._initialized = True
            logger.info(
                f"OpenAI Embeddings initialized: {self.config.openai_model} (dim={self._dimension})"
            )

        except ImportError:
            raise ImportError("openai not installed. Run: pip install openai")
        except Exception as e:
            logger.error(f"OpenAI Embeddings initialization failed: {e}")
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
        """Generate embeddings for multiple texts."""
        if not self._initialized or not self._client:
            raise RuntimeError("OpenAI client not initialized")

        # Truncate texts
        truncated = [t[: self.config.max_length * 4] for t in texts]

        # Process in batches (OpenAI limit is ~2048 inputs)
        all_embeddings = []
        batch_size = min(self.config.batch_size, 100)

        for i in range(0, len(truncated), batch_size):
            batch = truncated[i : i + batch_size]
            response = await self._client.embeddings.create(
                input=batch,
                model=self.config.openai_model,
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def embed_query(self, query: str) -> list[float]:
        """Generate query embedding (same as text for OpenAI)."""
        return await self.embed_text(query)


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
                f"Cohere Embeddings initialized: {self.config.cohere_model} (dim={self._dimension})"
            )

        except ImportError:
            raise ImportError("cohere not installed. Run: pip install cohere")
        except Exception as e:
            logger.error(f"Cohere Embeddings initialization failed: {e}")
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
        """Generate embeddings for multiple texts."""
        if not self._initialized or not self._client:
            raise RuntimeError("Cohere client not initialized")

        # Truncate texts
        truncated = [t[: self.config.max_length * 4] for t in texts]

        # Cohere has a limit of 96 texts per request
        all_embeddings = []
        batch_size = min(self.config.batch_size, 96)

        for i in range(0, len(truncated), batch_size):
            batch = truncated[i : i + batch_size]
            response = await self._client.embed(
                texts=batch,
                model=self.config.cohere_model,
                input_type=self.config.cohere_input_type,
            )
            all_embeddings.extend(response.embeddings)

        return all_embeddings

    async def embed_query(self, query: str) -> list[float]:
        """
        Generate query embedding using search_query input type.

        This uses Cohere's optimized query embedding mode for better
        retrieval performance.
        """
        if not self._initialized or not self._client:
            raise RuntimeError("Cohere client not initialized")

        # Truncate if needed
        if len(query) > self.config.max_length * 4:
            query = query[: self.config.max_length * 4]

        response = await self._client.embed(
            texts=[query],
            model=self.config.cohere_model,
            input_type="search_query",  # Use query-optimized mode
        )
        return response.embeddings[0]


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
    else:
        return SentenceTransformerEngine(config)
