"""Lazy RAG context provider for the devskyy_docs vector collection.

Module-level singleton — the pipeline is initialized once on first call and
reused for the lifetime of the process.  All agents share the same
ChromaDB connection without any coordination code in individual agents.

Usage (from any async context):
    from orchestration.docs_context import get_docs_context

    context_chunks = await get_docs_context("How do I use FastAPI dependency injection?")
    # Returns: [{"text": "...", "source": "fastapi-reference.md"}, ...]
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Module-level singletons — shared across all agents in the process
_pipeline: Any = None
_initialized: bool = False
_init_lock: asyncio.Lock | None = None


async def _lock() -> asyncio.Lock:
    global _init_lock
    if _init_lock is None:
        _init_lock = asyncio.Lock()
    return _init_lock


async def _ensure_ready() -> Any:
    """Initialize the pipeline once; return it (or None if unavailable)."""
    global _pipeline, _initialized

    if _initialized:
        return _pipeline

    async with await _lock():
        if _initialized:  # Double-checked locking
            return _pipeline
        try:
            from orchestration.document_ingestion import DocumentIngestionPipeline, IngestionConfig
            from orchestration.vector_store import VectorStoreConfig, create_vector_store

            vs_config = VectorStoreConfig(collection_name="devskyy_docs")
            pipeline = DocumentIngestionPipeline(config=IngestionConfig())
            pipeline._vector_store = create_vector_store(vs_config)
            await pipeline.initialize()
            _pipeline = pipeline
            logger.info("docs_context: devskyy_docs RAG provider ready")
        except Exception as exc:
            logger.warning("docs_context: init failed — agents will run without docs RAG: %s", exc)
        _initialized = True

    return _pipeline


async def get_docs_context(
    question: str,
    top_k: int = 3,
) -> list[dict[str, str]]:
    """Return up to *top_k* context chunks for *question*, formatted for RAGPrompting.

    Each item is ``{"text": "...", "source": "filename.md"}``.
    Returns an empty list on failure so callers degrade silently.
    """
    pipeline = await _ensure_ready()
    if pipeline is None:
        return []
    try:
        results = await pipeline.search(question, top_k=top_k)
        return [
            {
                "text": r.get("document", {}).get("content", ""),
                "source": r.get("document", {}).get("source", "unknown"),
            }
            for r in results
            if r.get("document", {}).get("content")
        ]
    except Exception as exc:
        logger.warning("docs_context: search failed: %s", exc)
        return []
