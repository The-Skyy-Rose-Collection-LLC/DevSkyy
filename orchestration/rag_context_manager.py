"""
DevSkyy RAG Context Manager
============================

Unified RAG pipeline orchestration for SuperAgents.

Flow:
    Query → (Optional) Rewrite → Vector Search → (Optional) Rerank → RAG Context

Integrates:
- VectorStore (ChromaDB/Pinecone)
- QueryRewriter (5 strategies)
- Reranker (Cohere)

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from typing import Any

import structlog
from pydantic import BaseModel, ConfigDict, Field

from orchestration.query_rewriter import (
    AdvancedQueryRewriter,
    QueryRewriterConfig,
    QueryRewriteStrategy,
)
from orchestration.reranker import BaseReranker, RerankerConfig, create_reranker
from orchestration.vector_store import (
    BaseVectorStore,
    SearchResult,
    VectorStoreConfig,
    create_vector_store,
)

logger = structlog.get_logger(__name__)


# =============================================================================
# Configuration
# =============================================================================


class RAGContextConfig(BaseModel):
    """Configuration for RAG context retrieval."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    # Vector search settings
    top_k: int = Field(default=5, ge=1, le=100, description="Number of documents to retrieve")
    similarity_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Minimum similarity score"
    )

    # Query rewriting
    use_query_rewriting: bool = Field(default=False, description="Enable query rewriting")
    rewrite_strategy: str = Field(default="zero_shot", description="Query rewrite strategy to use")
    num_query_variations: int = Field(
        default=3, ge=1, le=5, description="Number of query variations"
    )

    # Reranking
    use_reranking: bool = Field(default=False, description="Enable reranking")
    rerank_top_n: int = Field(
        default=5, ge=1, le=100, description="Number of documents after reranking"
    )

    # Caching
    cache_enabled: bool = Field(default=True, description="Enable context caching")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")

    # Redis connection (optional)
    redis_url: str | None = Field(default=None, description="Redis URL for caching")


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class RAGDocument:
    """A single document from RAG retrieval."""

    content: str
    score: float
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)
    rerank_score: float | None = None


@dataclass
class RAGContext:
    """Complete RAG context for an agent."""

    query: str
    documents: list[RAGDocument]
    rewritten_queries: list[str] | None = None
    total_retrieved: int = 0
    strategy_used: str = "direct"
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_combined_context(self, max_length: int = 4000) -> str:
        """
        Combine all documents into a single context string.

        Args:
            max_length: Maximum character length for combined context

        Returns:
            Combined context string
        """
        if not self.documents:
            return ""

        combined = []
        current_length = 0

        for i, doc in enumerate(self.documents):
            # Format: [Source 1] (score: 0.95) Content...
            source_label = f"[{doc.source}]" if doc.source else f"[Document {i+1}]"
            score_label = f"(score: {doc.score:.2f})"
            if doc.rerank_score is not None:
                score_label += f" (rerank: {doc.rerank_score:.2f})"

            doc_text = f"{source_label} {score_label}\n{doc.content}\n"

            if current_length + len(doc_text) > max_length:
                break

            combined.append(doc_text)
            current_length += len(doc_text)

        return "\n---\n".join(combined)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "documents": [
                {
                    "content": doc.content,
                    "score": doc.score,
                    "source": doc.source,
                    "metadata": doc.metadata,
                    "rerank_score": doc.rerank_score,
                }
                for doc in self.documents
            ],
            "rewritten_queries": self.rewritten_queries,
            "total_retrieved": self.total_retrieved,
            "strategy_used": self.strategy_used,
            "metadata": self.metadata,
        }


# =============================================================================
# RAG Context Manager
# =============================================================================


class RAGContextManager:
    """
    Unified RAG pipeline orchestration.

    Coordinates vector search, query rewriting, and reranking for optimal retrieval.
    """

    def __init__(
        self,
        vector_store: BaseVectorStore,
        config: RAGContextConfig | None = None,
        query_rewriter: AdvancedQueryRewriter | None = None,
        reranker: BaseReranker | None = None,
    ):
        """
        Initialize RAG context manager.

        Args:
            vector_store: Initialized vector store
            config: RAG context configuration
            query_rewriter: Optional query rewriter instance
            reranker: Optional reranker instance
        """
        self.vector_store = vector_store
        self.config = config or RAGContextConfig()
        self.query_rewriter = query_rewriter
        self.reranker = reranker

        # Cache for context (in-memory)
        self._cache: dict[str, RAGContext] = {}

        # Optional Redis cache
        self._redis: Any | None = None
        if self.config.cache_enabled and self.config.redis_url:
            self._init_redis()

        logger.info(
            "rag_context_manager_initialized",
            use_rewriting=self.config.use_query_rewriting,
            use_reranking=self.config.use_reranking,
            top_k=self.config.top_k,
        )

    def _init_redis(self) -> None:
        """Initialize Redis cache connection."""
        try:
            import redis

            self._redis = redis.Redis.from_url(self.config.redis_url or "redis://localhost")
            self._redis.ping()
            logger.info("redis_cache_connected")
        except Exception as e:
            logger.warning("redis_cache_failed", error=str(e))
            self._redis = None

    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for a query."""
        content = f"{query}:{self.config.model_dump_json()}"
        return f"devskyy_rag:{hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()}"

    def _get_cached_context(self, query: str) -> RAGContext | None:
        """Retrieve cached RAG context."""
        if not self.config.cache_enabled:
            return None

        cache_key = self._get_cache_key(query)

        # Try Redis first
        if self._redis:
            try:
                import json

                cached = self._redis.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    logger.debug("cache_hit", query=query[:50])
                    # Reconstruct RAGContext from dict
                    docs = [RAGDocument(**doc) for doc in data.get("documents", [])]
                    return RAGContext(
                        query=data["query"],
                        documents=docs,
                        rewritten_queries=data.get("rewritten_queries"),
                        total_retrieved=data.get("total_retrieved", 0),
                        strategy_used=data.get("strategy_used", "direct"),
                        metadata=data.get("metadata", {}),
                    )
            except Exception as e:
                logger.warning("cache_retrieval_failed", error=str(e))

        # Try in-memory cache
        return self._cache.get(cache_key)

    def _cache_context(self, context: RAGContext) -> None:
        """Cache RAG context."""
        if not self.config.cache_enabled:
            return

        cache_key = self._get_cache_key(context.query)

        # Store in Redis
        if self._redis:
            try:
                import json

                self._redis.setex(
                    cache_key,
                    self.config.cache_ttl_seconds,
                    json.dumps(context.to_dict()),
                )
                logger.debug("cache_stored_redis", query=context.query[:50])
            except Exception as e:
                logger.warning("cache_storage_failed", error=str(e))

        # Store in-memory
        self._cache[cache_key] = context
        logger.debug("cache_stored_memory", query=context.query[:50])

    async def get_context(
        self,
        query: str,
        filter_metadata: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> RAGContext:
        """
        Retrieve RAG context for a query.

        Flow:
        1. Check cache
        2. (Optional) Rewrite query
        3. Search vector store (for each query variation)
        4. (Optional) Rerank results
        5. Format as RAGContext
        6. Cache result

        Args:
            query: User query
            filter_metadata: Optional metadata filters for vector search
            correlation_id: Optional correlation ID for logging

        Returns:
            RAGContext with retrieved documents
        """
        import uuid

        correlation_id = correlation_id or str(uuid.uuid4())[:12]

        # Check cache
        cached = self._get_cached_context(query)
        if cached:
            logger.info(f"[{correlation_id}] RAG context retrieved from cache")
            return cached

        logger.info(
            f"[{correlation_id}] Starting RAG retrieval: "
            f"rewriting={self.config.use_query_rewriting}, "
            f"reranking={self.config.use_reranking}"
        )

        # Step 1: Query rewriting (optional)
        queries_to_search = [query]
        rewritten_queries = None
        strategy_used = "direct"

        if self.config.use_query_rewriting and self.query_rewriter:
            try:
                strategy = QueryRewriteStrategy(self.config.rewrite_strategy)
                rewritten = self.query_rewriter.rewrite(
                    query=query,
                    strategy=strategy,
                    num_variations=self.config.num_query_variations,
                )
                queries_to_search = rewritten.rewritten_queries
                rewritten_queries = rewritten.rewritten_queries
                strategy_used = f"rewrite_{strategy.value}"
                logger.info(
                    f"[{correlation_id}] Query rewritten into {len(queries_to_search)} variations"
                )
            except Exception as e:
                logger.warning(f"[{correlation_id}] Query rewriting failed: {e}")
                queries_to_search = [query]

        # Step 2: Vector search for each query
        all_results: list[SearchResult] = []
        for q in queries_to_search:
            try:
                # Get embedding for query (assuming vector_store has embedding model)
                # For now, we'll need to get embeddings externally
                # This is a placeholder - actual implementation depends on vector store setup
                results = await self._search_with_embedding(q, filter_metadata, correlation_id)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"[{correlation_id}] Vector search failed for query '{q}': {e}")

        logger.info(f"[{correlation_id}] Retrieved {len(all_results)} documents from vector store")

        # Step 3: Deduplicate by document ID
        seen_ids = set()
        unique_results = []
        for result in all_results:
            if result.document.id not in seen_ids:
                seen_ids.add(result.document.id)
                unique_results.append(result)

        logger.info(
            f"[{correlation_id}] {len(unique_results)} unique documents after deduplication"
        )

        # Step 4: Reranking (optional)
        reranked_scores = {}
        if self.config.use_reranking and self.reranker and unique_results:
            try:
                # Extract texts for reranking
                texts = [result.document.content for result in unique_results]
                reranked = await self.reranker.rerank(
                    query=query, documents=texts, top_n=self.config.rerank_top_n
                )

                # Build map of rerank scores
                for rr in reranked:
                    reranked_scores[rr.index] = rr.score

                # Keep only reranked results
                unique_results = [unique_results[rr.index] for rr in reranked]
                logger.info(f"[{correlation_id}] Reranked to top {len(unique_results)} documents")
                strategy_used += "_reranked"
            except Exception as e:
                logger.warning(f"[{correlation_id}] Reranking failed: {e}")

        # Step 5: Convert to RAGDocument format
        documents = []
        for i, result in enumerate(unique_results[: self.config.top_k]):
            doc = RAGDocument(
                content=result.document.content,
                score=result.score,
                source=result.document.source,
                metadata=result.document.metadata,
                rerank_score=reranked_scores.get(i),
            )
            documents.append(doc)

        # Step 6: Create RAGContext
        context = RAGContext(
            query=query,
            documents=documents,
            rewritten_queries=rewritten_queries,
            total_retrieved=len(all_results),
            strategy_used=strategy_used,
            metadata={
                "correlation_id": correlation_id,
                "filter_metadata": filter_metadata,
                "num_query_variations": len(queries_to_search),
            },
        )

        # Cache the result
        self._cache_context(context)

        logger.info(
            f"[{correlation_id}] RAG context created: "
            f"{len(documents)} documents, strategy={strategy_used}"
        )

        return context

    async def _search_with_embedding(
        self,
        query: str,
        filter_metadata: dict[str, Any] | None,
        correlation_id: str,
    ) -> list[SearchResult]:
        """
        Search vector store with query embedding.

        This is a helper that handles embedding generation.
        """
        try:
            # Generate embedding using sentence-transformers (default)
            from sentence_transformers import SentenceTransformer

            # Use same model as ingestion (all-MiniLM-L6-v2)
            model = SentenceTransformer("all-MiniLM-L6-v2")
            query_embedding = model.encode(query).tolist()

            # Search vector store
            results = await self.vector_store.search(
                query_embedding=query_embedding,
                top_k=self.config.top_k,
                filter_metadata=filter_metadata,
            )

            return results

        except ImportError:
            logger.error(
                f"[{correlation_id}] sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )
            return []
        except Exception as e:
            logger.error(f"[{correlation_id}] Embedding generation failed: {e}")
            return []


# =============================================================================
# Factory Functions
# =============================================================================


async def create_rag_context_manager(
    vector_store_config: VectorStoreConfig | None = None,
    rag_config: RAGContextConfig | None = None,
    enable_rewriting: bool = False,
    enable_reranking: bool = False,
) -> RAGContextManager:
    """
    Factory function to create a fully configured RAG context manager.

    Args:
        vector_store_config: Vector store configuration
        rag_config: RAG context configuration
        enable_rewriting: Enable query rewriting
        enable_reranking: Enable reranking

    Returns:
        Initialized RAGContextManager
    """
    # Create vector store
    vector_store = create_vector_store(vector_store_config)
    await vector_store.initialize()

    # Create RAG config
    if rag_config is None:
        rag_config = RAGContextConfig(
            use_query_rewriting=enable_rewriting,
            use_reranking=enable_reranking,
        )

    # Create query rewriter (if enabled)
    query_rewriter = None
    if enable_rewriting or rag_config.use_query_rewriting:
        try:
            rewriter_config = QueryRewriterConfig(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                redis_url=rag_config.redis_url,
            )
            query_rewriter = AdvancedQueryRewriter(rewriter_config)
            logger.info("Query rewriter initialized")
        except Exception as e:
            logger.warning(f"Query rewriter initialization failed: {e}")

    # Create reranker (if enabled)
    reranker = None
    if enable_reranking or rag_config.use_reranking:
        try:
            reranker_config = RerankerConfig(
                cohere_api_key=os.getenv("COHERE_API_KEY"),
                top_n=rag_config.rerank_top_n,
            )
            reranker = create_reranker(reranker_config)
            await reranker.initialize()
            logger.info("Reranker initialized")
        except Exception as e:
            logger.warning(f"Reranker initialization failed: {e}")

    # Create RAG context manager
    return RAGContextManager(
        vector_store=vector_store,
        config=rag_config,
        query_rewriter=query_rewriter,
        reranker=reranker,
    )


__all__ = [
    "RAGContextConfig",
    "RAGDocument",
    "RAGContext",
    "RAGContextManager",
    "create_rag_context_manager",
]
