"""
RAGAnything Service
===================

Commercial-grade multimodal knowledge-base service backed by RAGAnything (v1.2.10)
and LightRAG.  Bridges to the existing UnifiedLLMClient and BaseEmbeddingEngine so
LLM routing and embedding caching stay centralised.

Each *collection* is an isolated LightRAG instance with its own graph + vector
storage under ``config.base_dir/<collection>/``.  Collections are lazy-loaded on
first access and cached for the process lifetime.

This service does **not** bridge to the existing ChromaDB/Pinecone stack —
LightRAG manages its own JSON-based entity graph and NanoVectorDB files.

Usage::

    from services.rag_anything_service import get_rag_anything_service

    svc = await get_rag_anything_service()
    await svc.ingest_document("skyyrose-catalog", "/path/to/lookbook.pdf")
    result = await svc.query("skyyrose-catalog", "What materials are used in Midnight?")
"""

from __future__ import annotations

import asyncio
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from llm.base import Message
from llm.unified_llm_client import LLMRequest, UnifiedLLMClient
from orchestration.embedding_engine import (
    BaseEmbeddingEngine,
    EmbeddingConfig,
    EmbeddingProvider,
    create_embedding_engine,
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Bridge: LLM
# ---------------------------------------------------------------------------


def _make_llm_func(llm_client: UnifiedLLMClient):
    """
    Return a RAGAnything/LightRAG-compatible LLM coroutine wired to UnifiedLLMClient.

    RAGAnything calls this hundreds of times during ingestion for entity extraction.
    ``skip_classification=True`` prevents TaskClassifier overhead on every call;
    temperature=0.1 keeps graph extraction deterministic.
    """

    async def llm_model_func(
        prompt: str,
        system_prompt: str | None = None,
        history_messages: list[dict] | None = None,
        **kwargs,
    ) -> str:
        messages: list[Message] = []
        if system_prompt:
            messages.append(Message.system(system_prompt))
        if history_messages:
            for m in history_messages:
                role = m.get("role", "user")
                content = m.get("content", "")
                if role == "assistant":
                    messages.append(Message.assistant(content))
                else:
                    messages.append(Message.user(content))
        messages.append(Message.user(prompt))

        request = LLMRequest(
            messages=messages,
            skip_classification=True,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.1),
        )
        response = await llm_client.complete(request)
        return response.content

    return llm_model_func


# ---------------------------------------------------------------------------
# Bridge: Embeddings
# ---------------------------------------------------------------------------


def _make_embedding_func(engine: BaseEmbeddingEngine):
    """
    Return a LightRAG ``EmbeddingFunc`` wrapping the existing embedding engine.

    LightRAG requires its own ``EmbeddingFunc`` dataclass (not a plain callable)
    because it introspects ``embedding_dim`` for vector index sizing.
    The inner async function converts the engine's List[List[float]] output to
    a numpy array as LightRAG expects.
    """
    import numpy as np
    from lightrag.utils import EmbeddingFunc

    async def _embed(texts: list[str]) -> np.ndarray:
        vecs = await engine.embed_batch(texts)
        return np.array(vecs, dtype=np.float32)

    return EmbeddingFunc(embedding_dim=engine.dimension, func=_embed)


# ---------------------------------------------------------------------------
# Service configuration
# ---------------------------------------------------------------------------


@dataclass
class RAGAnythingServiceConfig:
    """
    Configuration for RAGAnythingService.

    All settings can be overridden via environment variables so the service
    behaves correctly in both development and production without code changes.
    """

    # Root directory — each collection is a named sub-directory
    base_dir: Path = field(
        default_factory=lambda: Path(os.getenv("RAGANYTHING_BASE_DIR", "data/raganything"))
    )
    # LightRAG query mode: local | global | hybrid | naive | mix
    default_mode: str = field(default_factory=lambda: os.getenv("RAGANYTHING_DEFAULT_MODE", "mix"))
    # Which embedding provider to use (must match EmbeddingProvider enum name)
    embedding_provider: EmbeddingProvider = field(
        default_factory=lambda: EmbeddingProvider[
            os.getenv("RAGANYTHING_EMBEDDING_PROVIDER", "OPENAI").upper()
        ]
    )
    # Multimodal extraction flags (passed to RAGAnythingConfig)
    enable_image_processing: bool = True
    enable_table_processing: bool = True


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------


class RAGAnythingService:
    """
    Multimodal knowledge-base service for commercial RAG operations.

    Manages per-collection RAGAnything instances backed by LightRAG's graph +
    vector storage.  Provides async ingest, query, list, and delete operations
    gated by the billing layer at the API boundary.

    Args:
        config:           Service configuration (or None for env-var defaults).
        llm_client:       Shared UnifiedLLMClient — reuses existing LLM routing.
        embedding_engine: Pre-initialised engine, or None to create one from config.
    """

    def __init__(
        self,
        config: RAGAnythingServiceConfig | None = None,
        llm_client: UnifiedLLMClient | None = None,
        embedding_engine: BaseEmbeddingEngine | None = None,
    ) -> None:
        self._config = config or RAGAnythingServiceConfig()
        self._llm_client = llm_client or UnifiedLLMClient()
        self._external_engine = embedding_engine
        self._engine: BaseEmbeddingEngine | None = None
        self._instances: dict[str, Any] = {}  # collection name → RAGAnything
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the shared embedding engine and ensure the storage root exists."""
        async with self._lock:
            if self._initialized:
                return
            self._config.base_dir.mkdir(parents=True, exist_ok=True)
            if self._external_engine:
                self._engine = self._external_engine
            else:
                eng_cfg = EmbeddingConfig(provider=self._config.embedding_provider)
                self._engine = create_embedding_engine(eng_cfg)
                await self._engine.initialize()
            self._initialized = True
            logger.info("RAGAnythingService initialized", base_dir=str(self._config.base_dir))

    async def _get_instance(self, collection: str) -> Any:
        """Return a cached RAGAnything instance, creating it on first access."""
        if collection not in self._instances:
            async with self._lock:
                if collection not in self._instances:
                    await self._create_instance(collection)
        return self._instances[collection]

    async def _create_instance(self, collection: str) -> None:
        """
        Instantiate LightRAG + RAGAnything for a new collection.

        LightRAG owns the graph and vector storage under ``<base_dir>/<collection>/``.
        RAGAnything wraps LightRAG and adds multimodal document parsing, with its
        parser output going to ``<base_dir>/<collection>/parser_output/``.
        """
        from lightrag import LightRAG
        from raganything import RAGAnything
        from raganything import RAGAnythingConfig as LibConfig

        work_dir = self._config.base_dir / collection
        work_dir.mkdir(parents=True, exist_ok=True)

        llm_func = _make_llm_func(self._llm_client)
        emb_func = _make_embedding_func(self._engine)

        lightrag_instance = LightRAG(
            working_dir=str(work_dir),
            llm_model_func=llm_func,
            embedding_func=emb_func,
        )

        lib_cfg = LibConfig(
            working_dir=str(work_dir / "parser_output"),
            enable_image_processing=self._config.enable_image_processing,
            enable_table_processing=self._config.enable_table_processing,
        )
        rag = RAGAnything(
            lightrag=lightrag_instance,
            llm_model_func=llm_func,
            embedding_func=emb_func,
            config=lib_cfg,
        )
        self._instances[collection] = rag
        logger.info("RAGAnything collection ready", collection=collection, path=str(work_dir))

    async def ingest_document(
        self,
        collection: str,
        file_path: str | Path,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Ingest a document into *collection*.

        Supports any format RAGAnything handles: PDF (with embedded images/tables),
        DOCX, plain text, CSV, and common image formats.

        ``process_document_complete`` is synchronous; it runs in a thread executor
        to avoid blocking the async event loop during long parsing operations.

        Args:
            collection: Knowledge base name (e.g. "skyyrose-catalog").
            file_path:  Path to the source file.
            metadata:   Optional key-value pairs (reserved for future LightRAG versions).

        Returns:
            Dict with ``doc_id``, ``collection``, ``status``, ``file``.
        """
        rag = await self._get_instance(collection)
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        logger.info("Ingesting document", collection=collection, file=str(file_path))

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: rag.process_document_complete(
                file_path=str(file_path),
                doc_id=file_path.stem,
            ),
        )

        return {
            "doc_id": file_path.stem,
            "collection": collection,
            "status": "ingested",
            "file": file_path.name,
        }

    async def query(
        self,
        collection: str,
        question: str,
        mode: str | None = None,
        top_k: int = 10,
    ) -> dict[str, Any]:
        """
        Query *collection* using LightRAG's graph-vector hybrid retrieval.

        Mode options:
        - ``local``  — entity-centric, best for specific fact lookups
        - ``global`` — theme-centric, best for broad concept questions
        - ``hybrid`` — combines local + global
        - ``mix``    — default; balances graph traversal and vector similarity
        - ``naive``  — plain vector similarity (fastest, least graph-aware)

        Source references are embedded inline in LightRAG's answer text.

        Args:
            collection: Knowledge base name.
            question:   Natural-language query.
            mode:       Retrieval mode (defaults to config default_mode).
            top_k:      Number of entities/chunks to retrieve.

        Returns:
            Dict with ``answer``, ``collection``, ``mode``, ``sources``.
        """
        rag = await self._get_instance(collection)
        effective_mode = mode or self._config.default_mode

        logger.info(
            "RAG query",
            collection=collection,
            mode=effective_mode,
            question=question[:80],
        )

        answer = await rag.aquery(query=question, mode=effective_mode, top_k=top_k)

        return {
            "answer": answer,
            "collection": collection,
            "mode": effective_mode,
            "sources": [],  # LightRAG embeds source references in the answer text
        }

    async def list_collections(self) -> list[dict[str, Any]]:
        """Return all known collections and their disk sizes."""
        collections = []
        if self._config.base_dir.exists():
            for d in sorted(self._config.base_dir.iterdir()):
                if d.is_dir():
                    size_mb = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) / 1e6
                    collections.append(
                        {
                            "name": d.name,
                            "size_mb": round(size_mb, 2),
                            "loaded": d.name in self._instances,
                        }
                    )
        return collections

    async def delete_collection(self, collection: str) -> None:
        """Delete a collection and remove its storage from disk."""
        if collection in self._instances:
            del self._instances[collection]
        work_dir = self._config.base_dir / collection
        if work_dir.exists():
            shutil.rmtree(work_dir)
        logger.info("Collection deleted", collection=collection)

    async def close(self) -> None:
        """Release all cached RAGAnything instances."""
        self._instances.clear()
        logger.info("RAGAnythingService closed")


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

_service_instance: RAGAnythingService | None = None


async def get_rag_anything_service(
    config: RAGAnythingServiceConfig | None = None,
) -> RAGAnythingService:
    """
    Return the process-level singleton RAGAnythingService, initialising on first call.

    Mirrors the ``create_rag_context_manager`` pattern in
    ``orchestration/rag_context_manager.py``.
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = RAGAnythingService(config=config)
        await _service_instance.initialize()
    return _service_instance
