"""
DevSkyy Vector Store
====================

Production-grade vector database abstraction for RAG pipelines.

Supports:
- ChromaDB (local, default)
- Pinecone (cloud, optional)

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Performance: LRU Cache for Vector Search Results
# =============================================================================


class VectorSearchCache:
    """Thread-safe LRU cache for vector search results.

    Caches search results by embedding hash to reduce redundant vector queries.
    Provides significant latency improvement for repeated searches.
    """

    def __init__(self, maxsize: int = 256, ttl_seconds: int = 300):
        """Initialize the cache.

        Args:
            maxsize: Maximum number of cached results (default: 256)
            ttl_seconds: Time-to-live in seconds (default: 300 = 5 minutes)
        """
        self._maxsize = maxsize
        self._ttl = ttl_seconds
        self._cache: OrderedDict[str, tuple[list[dict[str, Any]], float]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0

    def _generate_key(
        self, embedding: list[float], top_k: int, filter_metadata: dict | None
    ) -> str:
        """Generate a cache key from embedding and search params."""
        # Round embedding values to reduce key variations
        rounded_emb = [round(v, 6) for v in embedding[:32]]  # First 32 dims for key
        content = json.dumps({"e": rounded_emb, "k": top_k, "f": filter_metadata}, sort_keys=True)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:32]

    async def get(
        self, embedding: list[float], top_k: int, filter_metadata: dict | None
    ) -> list[dict[str, Any]] | None:
        """Get search results from cache if available and not expired."""
        import time

        key = self._generate_key(embedding, top_k, filter_metadata)
        async with self._lock:
            if key in self._cache:
                results, timestamp = self._cache[key]
                if time.time() - timestamp < self._ttl:
                    self._cache.move_to_end(key)
                    self._hits += 1
                    logger.debug(f"Vector search cache hit for key: {key[:8]}...")
                    return results
                else:
                    del self._cache[key]
            self._misses += 1
            return None

    async def put(
        self,
        embedding: list[float],
        top_k: int,
        filter_metadata: dict | None,
        results: list[dict[str, Any]],
    ) -> None:
        """Store search results in cache."""
        import time

        key = self._generate_key(embedding, top_k, filter_metadata)
        async with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key] = (results, time.time())
            else:
                if len(self._cache) >= self._maxsize:
                    self._cache.popitem(last=False)
                self._cache[key] = (results, time.time())

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
            "ttl_seconds": self._ttl,
        }

    async def clear(self) -> None:
        """Clear the cache."""
        async with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0


# Global vector search cache instance
_vector_search_cache: VectorSearchCache | None = None


def get_vector_search_cache() -> VectorSearchCache:
    """Get or create the global vector search cache instance."""
    global _vector_search_cache
    if _vector_search_cache is None:
        ttl = int(os.getenv("VECTOR_SEARCH_CACHE_TTL", "300"))
        _vector_search_cache = VectorSearchCache(maxsize=256, ttl_seconds=ttl)
        logger.info(f"Initialized vector search cache with maxsize=256, ttl={ttl}s")
    return _vector_search_cache


# ChromaDB batch size for optimal performance
CHROMA_BATCH_SIZE = 1000


# =============================================================================
# Enums & Models
# =============================================================================


class VectorDBType(str, Enum):
    """Supported vector database types."""

    CHROMADB = "chromadb"
    PINECONE = "pinecone"


class DocumentStatus(str, Enum):
    """Document indexing status."""

    PENDING = "pending"
    INDEXED = "indexed"
    FAILED = "failed"
    DELETED = "deleted"


@dataclass
class Document:
    """Document for vector storage."""

    id: str = field(default_factory=lambda: str(uuid4()))
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None
    source: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: DocumentStatus = DocumentStatus.PENDING

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
        }


@dataclass
class SearchResult:
    """Search result from vector store."""

    document: Document
    score: float
    distance: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document": self.document.to_dict(),
            "score": self.score,
            "distance": self.distance,
        }


class VectorStoreConfig(BaseModel):
    """Vector store configuration."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    db_type: VectorDBType = Field(default=VectorDBType.CHROMADB)
    collection_name: str = Field(default="devskyy_docs")
    persist_directory: str = Field(default="./data/vectordb")

    # ChromaDB settings
    chroma_host: str | None = Field(default=None)
    chroma_port: int = Field(default=8000)

    # Pinecone settings
    pinecone_api_key: str | None = Field(default=None)
    pinecone_environment: str = Field(default="us-east-1")
    pinecone_index_name: str = Field(default="devskyy-rag")

    # Search settings
    default_top_k: int = Field(default=5, ge=1, le=100)
    similarity_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0
    )  # Lower threshold for L2 distance


# =============================================================================
# Base Vector Store
# =============================================================================


class BaseVectorStore(ABC):
    """Abstract base class for vector stores."""

    def __init__(self, config: VectorStoreConfig):
        self.config = config
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector store connection."""
        pass

    @abstractmethod
    async def add_documents(
        self, documents: list[Document], embeddings: list[list[float]]
    ) -> list[str]:
        """Add documents with embeddings."""
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        top_k: int | None = None,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar documents."""
        pass

    @abstractmethod
    async def delete_documents(self, document_ids: list[str]) -> int:
        """Delete documents by ID."""
        pass

    @abstractmethod
    async def get_document(self, document_id: str) -> Document | None:
        """Get a single document by ID."""
        pass

    @abstractmethod
    async def list_sources(self) -> list[str]:
        """List all unique document sources."""
        pass

    @abstractmethod
    async def get_collection_stats(self) -> dict[str, Any]:
        """Get collection statistics."""
        pass

    async def close(self) -> None:
        """Close the vector store connection."""
        self._initialized = False


# =============================================================================
# ChromaDB Implementation
# =============================================================================


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB vector store implementation."""

    def __init__(self, config: VectorStoreConfig):
        super().__init__(config)
        self._client = None
        self._collection = None

    async def initialize(self) -> None:
        """Initialize ChromaDB connection."""
        try:
            import chromadb
            from chromadb.config import Settings

            # Create persist directory
            os.makedirs(self.config.persist_directory, exist_ok=True)

            # Initialize client
            if self.config.chroma_host:
                # Remote ChromaDB server
                self._client = chromadb.HttpClient(
                    host=self.config.chroma_host,
                    port=self.config.chroma_port,
                )
            else:
                # Local persistent ChromaDB
                self._client = chromadb.PersistentClient(
                    path=self.config.persist_directory,
                    settings=Settings(anonymized_telemetry=False),
                )

            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": "cosine"},
            )

            self._initialized = True
            logger.info(f"ChromaDB initialized: {self.config.collection_name}")

        except ImportError:
            raise ImportError("chromadb not installed. Run: pip install chromadb")
        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
            raise

    async def add_documents(
        self, documents: list[Document], embeddings: list[list[float]]
    ) -> list[str]:
        """Add documents with embeddings to ChromaDB using batch operations.

        For large ingestion, batches documents in chunks of 1000 (ChromaDB optimal)
        to prevent memory issues and improve throughput.
        """
        if not self._initialized or not self._collection:
            raise RuntimeError("ChromaDB not initialized")

        ids = [doc.id for doc in documents]
        contents = [doc.content for doc in documents]
        metadatas = [
            {**doc.metadata, "source": doc.source, "created_at": doc.created_at.isoformat()}
            for doc in documents
        ]

        # Use batch operations for large document sets
        if len(documents) > CHROMA_BATCH_SIZE:
            logger.info(f"Using batch mode for {len(documents)} documents")
            for i in range(0, len(documents), CHROMA_BATCH_SIZE):
                batch_end = min(i + CHROMA_BATCH_SIZE, len(documents))
                self._collection.add(
                    ids=ids[i:batch_end],
                    embeddings=embeddings[i:batch_end],
                    documents=contents[i:batch_end],
                    metadatas=metadatas[i:batch_end],
                )
                logger.debug(f"Added batch {i // CHROMA_BATCH_SIZE + 1}: {batch_end - i} documents")
        else:
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas,
            )

        logger.info(f"Added {len(documents)} documents to ChromaDB")
        return ids

    async def search(
        self,
        query_embedding: list[float],
        top_k: int | None = None,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar documents in ChromaDB with caching.

        Results are cached by embedding hash for faster repeated queries.
        """
        if not self._initialized or not self._collection:
            raise RuntimeError("ChromaDB not initialized")

        k = top_k or self.config.default_top_k

        # Check cache first
        cache = get_vector_search_cache()
        cached = await cache.get(query_embedding, k, filter_metadata)
        if cached is not None:
            # Reconstruct SearchResult from cached data
            return [
                SearchResult(
                    document=Document(
                        id=r["id"],
                        content=r["content"],
                        metadata=r["metadata"],
                        source=r["source"],
                        status=DocumentStatus.INDEXED,
                    ),
                    score=r["score"],
                    distance=r["distance"],
                )
                for r in cached
            ]

        # Build where filter
        where_filter = None
        if filter_metadata:
            where_filter = dict(filter_metadata.items())

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i] if results["distances"] else None
                # Convert L2 distance to similarity score (0-1 range)
                # Using formula: score = 1 / (1 + distance)
                score = 1 / (1 + distance) if distance is not None else 0.0

                # Filter by similarity threshold
                if score < self.config.similarity_threshold:
                    continue

                doc = Document(
                    id=doc_id,
                    content=results["documents"][0][i] if results["documents"] else "",
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    source=(
                        results["metadatas"][0][i].get("source", "") if results["metadatas"] else ""
                    ),
                    status=DocumentStatus.INDEXED,
                )
                search_results.append(SearchResult(document=doc, score=score, distance=distance))

        # Cache results
        cache_data = [
            {
                "id": r.document.id,
                "content": r.document.content,
                "metadata": r.document.metadata,
                "source": r.document.source,
                "score": r.score,
                "distance": r.distance,
            }
            for r in search_results
        ]
        await cache.put(query_embedding, k, filter_metadata, cache_data)

        return search_results

    async def delete_documents(self, document_ids: list[str]) -> int:
        """Delete documents from ChromaDB."""
        if not self._initialized or not self._collection:
            raise RuntimeError("ChromaDB not initialized")

        self._collection.delete(ids=document_ids)
        logger.info(f"Deleted {len(document_ids)} documents from ChromaDB")
        return len(document_ids)

    async def get_document(self, document_id: str) -> Document | None:
        """Get a single document from ChromaDB."""
        if not self._initialized or not self._collection:
            raise RuntimeError("ChromaDB not initialized")

        result = self._collection.get(ids=[document_id], include=["documents", "metadatas"])

        if result["ids"]:
            return Document(
                id=result["ids"][0],
                content=result["documents"][0] if result["documents"] else "",
                metadata=result["metadatas"][0] if result["metadatas"] else {},
                source=result["metadatas"][0].get("source", "") if result["metadatas"] else "",
                status=DocumentStatus.INDEXED,
            )
        return None

    async def list_sources(self) -> list[str]:
        """List all unique document sources."""
        if not self._initialized or not self._collection:
            raise RuntimeError("ChromaDB not initialized")

        # Get all documents metadata
        result = self._collection.get(include=["metadatas"])
        sources = set()
        if result["metadatas"]:
            for meta in result["metadatas"]:
                if meta and "source" in meta:
                    sources.add(meta["source"])
        return sorted(sources)

    async def get_collection_stats(self) -> dict[str, Any]:
        """Get ChromaDB collection statistics."""
        if not self._initialized or not self._collection:
            raise RuntimeError("ChromaDB not initialized")

        count = self._collection.count()
        sources = await self.list_sources()

        return {
            "db_type": "chromadb",
            "collection_name": self.config.collection_name,
            "document_count": count,
            "unique_sources": len(sources),
            "persist_directory": self.config.persist_directory,
        }


# =============================================================================
# Pinecone Implementation
# =============================================================================


class PineconeVectorStore(BaseVectorStore):
    """Pinecone vector store implementation for cloud deployment."""

    def __init__(self, config: VectorStoreConfig):
        super().__init__(config)
        self._index = None
        self._pc = None

    async def initialize(self) -> None:
        """Initialize Pinecone connection."""
        try:
            from pinecone import Pinecone, ServerlessSpec

            api_key = self.config.pinecone_api_key or os.getenv("PINECONE_API_KEY")
            if not api_key:
                raise ValueError("Pinecone API key required")

            self._pc = Pinecone(api_key=api_key)

            # Check if index exists, create if not
            existing_indexes = [idx.name for idx in self._pc.list_indexes()]

            if self.config.pinecone_index_name not in existing_indexes:
                self._pc.create_index(
                    name=self.config.pinecone_index_name,
                    dimension=384,  # all-MiniLM-L6-v2 dimension
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region=self.config.pinecone_environment),
                )

            self._index = self._pc.Index(self.config.pinecone_index_name)
            self._initialized = True
            logger.info(f"Pinecone initialized: {self.config.pinecone_index_name}")

        except ImportError:
            raise ImportError("pinecone-client not installed. Run: pip install pinecone-client")
        except Exception as e:
            logger.error(f"Pinecone initialization failed: {e}")
            raise

    async def add_documents(
        self, documents: list[Document], embeddings: list[list[float]]
    ) -> list[str]:
        """Add documents with embeddings to Pinecone."""
        if not self._initialized or not self._index:
            raise RuntimeError("Pinecone not initialized")

        vectors = []
        for doc, emb in zip(documents, embeddings, strict=False):
            vectors.append(
                {
                    "id": doc.id,
                    "values": emb,
                    "metadata": {
                        "content": doc.content[:8000],  # Pinecone metadata limit
                        "source": doc.source,
                        "created_at": doc.created_at.isoformat(),
                        **{
                            k: v
                            for k, v in doc.metadata.items()
                            if isinstance(v, str | int | float | bool)
                        },
                    },
                }
            )

        # Batch upsert (Pinecone limit is 100 vectors per request)
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            self._index.upsert(vectors=batch)

        logger.info(f"Added {len(documents)} documents to Pinecone")
        return [doc.id for doc in documents]

    async def search(
        self,
        query_embedding: list[float],
        top_k: int | None = None,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar documents in Pinecone."""
        if not self._initialized or not self._index:
            raise RuntimeError("Pinecone not initialized")

        k = top_k or self.config.default_top_k

        results = self._index.query(
            vector=query_embedding,
            top_k=k,
            include_metadata=True,
            filter=filter_metadata,
        )

        search_results = []
        for match in results.matches:
            score = match.score
            if score < self.config.similarity_threshold:
                continue

            metadata = match.metadata or {}
            doc = Document(
                id=match.id,
                content=metadata.get("content", ""),
                metadata={
                    k: v
                    for k, v in metadata.items()
                    if k not in ["content", "source", "created_at"]
                },
                source=metadata.get("source", ""),
                status=DocumentStatus.INDEXED,
            )
            search_results.append(SearchResult(document=doc, score=score, distance=1 - score))

        return search_results

    async def delete_documents(self, document_ids: list[str]) -> int:
        """Delete documents from Pinecone."""
        if not self._initialized or not self._index:
            raise RuntimeError("Pinecone not initialized")

        self._index.delete(ids=document_ids)
        logger.info(f"Deleted {len(document_ids)} documents from Pinecone")
        return len(document_ids)

    async def get_document(self, document_id: str) -> Document | None:
        """Get a single document from Pinecone."""
        if not self._initialized or not self._index:
            raise RuntimeError("Pinecone not initialized")

        result = self._index.fetch(ids=[document_id])

        if document_id in result.vectors:
            vec = result.vectors[document_id]
            metadata = vec.metadata or {}
            return Document(
                id=document_id,
                content=metadata.get("content", ""),
                metadata={
                    k: v
                    for k, v in metadata.items()
                    if k not in ["content", "source", "created_at"]
                },
                source=metadata.get("source", ""),
                status=DocumentStatus.INDEXED,
            )
        return None

    async def list_sources(self) -> list[str]:
        """List unique sources (limited in Pinecone)."""
        # Pinecone doesn't support listing all metadata efficiently
        # Return empty list - use ChromaDB for this feature
        logger.warning("list_sources not fully supported in Pinecone")
        return []

    async def get_collection_stats(self) -> dict[str, Any]:
        """Get Pinecone index statistics."""
        if not self._initialized or not self._index:
            raise RuntimeError("Pinecone not initialized")

        stats = self._index.describe_index_stats()
        return {
            "db_type": "pinecone",
            "index_name": self.config.pinecone_index_name,
            "document_count": stats.total_vector_count,
            "dimensions": stats.dimension,
            "environment": self.config.pinecone_environment,
        }


# =============================================================================
# Factory
# =============================================================================


def create_vector_store(config: VectorStoreConfig | None = None) -> BaseVectorStore:
    """
    Create a vector store instance.

    Args:
        config: Vector store configuration. Uses defaults if not provided.

    Returns:
        BaseVectorStore: Configured vector store instance.

    Example:
        >>> config = VectorStoreConfig(db_type=VectorDBType.CHROMADB)
        >>> store = create_vector_store(config)
        >>> await store.initialize()
    """
    if config is None:
        config = VectorStoreConfig()

    if config.db_type == VectorDBType.PINECONE:
        return PineconeVectorStore(config)
    else:
        return ChromaVectorStore(config)
