"""RAG (Retrieval-Augmented Generation) MCP tools.

Ports the 6 tools from mcp_servers/rag_server.py into the live MCP surface.
Heavy RAG dependencies (chromadb, sentence-transformers, voyageai, pinecone)
are imported lazily inside each tool body so this module stays import-clean
in environments where those packages are absent.

Configuration (env vars):
    VECTOR_DB_PATH      – path for ChromaDB persistence  (default: ./data/vectordb)
    RAG_COLLECTION      – ChromaDB collection name       (default: devskyy_docs)
    EMBEDDING_PROVIDER  – "sentence_transformers" | "openai" (default: sentence_transformers)
    REDIS_URL           – enable query-rewrite caching   (default: None / disabled)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import Field

from mcp_tools.server import CHARACTER_LIMIT, logger, mcp
from mcp_tools.types import BaseAgentInput, ResponseFormat

# =============================================================================
# Configuration (read once at module import — lightweight, no deps)
# =============================================================================

_VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./data/vectordb")
_COLLECTION_NAME: str = os.getenv("RAG_COLLECTION", "devskyy_docs")
_EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
_REDIS_URL: str | None = os.getenv("REDIS_URL", None)

# Module-level singletons — populated lazily on first tool invocation
_pipeline: Any = None
_rewriter: Any = None


# =============================================================================
# Input models
# =============================================================================


class RAGQueryInput(BaseAgentInput):
    """Input for RAG semantic search queries."""

    query: str = Field(..., description="Search query", min_length=1, max_length=5000)
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")
    source_filter: str | None = Field(default=None, description="Filter by source path substring")


class RAGIngestInput(BaseAgentInput):
    """Input for document ingestion into the vector store."""

    path: str = Field(
        ..., description="Absolute or relative path to a file or directory to ingest", min_length=1
    )
    recursive: bool = Field(
        default=True, description="Recursively ingest subdirectories when path is a directory"
    )


class RAGContextInput(BaseAgentInput):
    """Input for context retrieval given a natural-language question."""

    question: str = Field(..., description="Question to retrieve context for", min_length=1)
    max_tokens: int = Field(
        default=2000, ge=100, le=8000, description="Maximum token budget for returned context"
    )
    top_k: int = Field(default=5, ge=1, le=10, description="Number of document chunks to retrieve")


class RAGQueryRewriteInput(BaseAgentInput):
    """Input for query rewriting to improve retrieval quality."""

    query: str = Field(..., description="Original query to rewrite", min_length=1, max_length=5000)
    strategy: str = Field(
        default="zero_shot",
        description=("Rewriting strategy: zero_shot | few_shot | sub_queries | step_back | hyde"),
    )
    num_variations: int = Field(
        default=3, ge=1, le=5, description="Number of query variations to generate"
    )


# =============================================================================
# Internal helpers
# =============================================================================


def _error_json(message: str) -> str:
    """Return a JSON error envelope, always under CHARACTER_LIMIT."""
    return json.dumps({"error": message}, indent=2)[:CHARACTER_LIMIT]


def _fmt(data: dict[str, Any], fmt: ResponseFormat) -> str:
    """Render *data* in the requested format, capped to CHARACTER_LIMIT."""
    if fmt == ResponseFormat.JSON:
        result = json.dumps(data, indent=2, default=str)
        return result[:CHARACTER_LIMIT]

    # --- Markdown rendering ---
    if "error" in data:
        return f"**Error:** {data['error']}"[:CHARACTER_LIMIT]

    lines: list[str] = []

    if "results" in data:
        lines.append(f"## Search Results ({len(data['results'])} found)\n")
        for i, result in enumerate(data["results"], 1):
            doc = result.get("document", {})
            score = result.get("score", 0)
            source = doc.get("source", "unknown")
            content = str(doc.get("content", ""))[:500]
            lines.append(f"### {i}. {source} (score: {score:.3f})")
            lines.append(f"```\n{content}\n```\n")

    if "context" in data:
        lines.append("## Retrieved Context\n")
        lines.append(str(data["context"]))

    if "ingestion" in data:
        ing = data["ingestion"]
        lines.append("## Ingestion Results\n")
        lines.append(f"- **Files processed:** {ing.get('total_files', 0)}")
        lines.append(f"- **Chunks created:** {ing.get('total_chunks', 0)}")
        lines.append(f"- **Duration:** {ing.get('duration_seconds', 0):.2f}s")
        if ing.get("failed_files"):
            lines.append(f"- **Failed:** {', '.join(ing['failed_files'])}")

    if "sources" in data:
        lines.append(f"## Indexed Sources ({data.get('count', len(data['sources']))} total)\n")
        for src in data["sources"]:
            lines.append(f"- {src}")

    if "stats" in data:
        lines.append("## RAG Statistics\n")
        lines.append(f"```json\n{json.dumps(data['stats'], indent=2)}\n```")

    if "rewritten" in data:
        rw = data["rewritten"]
        lines.append("## Query Rewrite Results\n")
        lines.append(f"**Original:** {rw.get('original_query', '')}\n")
        lines.append(f"**Strategy:** {rw.get('strategy', '')}\n")
        lines.append("**Rewritten queries:**")
        for q in rw.get("rewritten_queries", []):
            lines.append(f"- {q}")
        if rw.get("reasoning"):
            lines.append(f"\n**Reasoning:** {rw['reasoning']}")

    return ("\n".join(lines) if lines else json.dumps(data, indent=2, default=str))[
        :CHARACTER_LIMIT
    ]


async def _get_pipeline() -> Any:
    """Return (or lazily create) the DocumentIngestionPipeline singleton.

    Raises ImportError with a clear message if RAG deps are absent.
    """
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    # Deferred heavy imports — these may fail in slim environments
    from orchestration.document_ingestion import DocumentIngestionPipeline, IngestionConfig
    from orchestration.embedding_engine import (
        EmbeddingConfig,
        EmbeddingProvider,
        create_embedding_engine,
    )
    from orchestration.vector_store import VectorDBType, VectorStoreConfig, create_vector_store

    vector_config = VectorStoreConfig(
        db_type=VectorDBType.CHROMADB,
        collection_name=_COLLECTION_NAME,
        persist_directory=_VECTOR_DB_PATH,
    )
    embedding_config = EmbeddingConfig(
        provider=(
            EmbeddingProvider.SENTENCE_TRANSFORMERS
            if _EMBEDDING_PROVIDER == "sentence_transformers"
            else EmbeddingProvider.OPENAI
        ),
    )
    vector_store = create_vector_store(vector_config)
    embedding_engine = create_embedding_engine(embedding_config)

    _pipeline = DocumentIngestionPipeline(
        vector_store=vector_store,
        embedding_engine=embedding_engine,
        config=IngestionConfig(),
    )
    await _pipeline.initialize()
    return _pipeline


def _get_rewriter() -> Any:
    """Return (or lazily create) the AdvancedQueryRewriter singleton.

    Raises ImportError with a clear message if RAG deps are absent.
    """
    global _rewriter
    if _rewriter is not None:
        return _rewriter

    from orchestration.query_rewriter import AdvancedQueryRewriter, QueryRewriterConfig

    config = QueryRewriterConfig(
        redis_url=_REDIS_URL,
        cache_enabled=_REDIS_URL is not None,
    )
    _rewriter = AdvancedQueryRewriter(config)
    return _rewriter


# =============================================================================
# MCP Tools
# =============================================================================


@mcp.tool(
    name="rag_query",
    annotations={
        "title": "RAG Semantic Search",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def rag_query(params: RAGQueryInput) -> str:
    """Search the knowledge base for relevant documents using semantic search.

    Queries the vector store and returns the top-K most relevant document chunks
    with relevance scores. Optionally filter results by source path.

    Args:
        params: Query parameters — search text, top-k count, optional source filter,
                and response format (markdown | json).

    Returns:
        Ranked list of matching document chunks with source paths and similarity scores.
    """
    try:
        pipeline = await _get_pipeline()

        filter_metadata: dict[str, Any] | None = None
        if params.source_filter:
            filter_metadata = {"source": {"$contains": params.source_filter}}

        results = await pipeline.search(
            query=params.query,
            top_k=params.top_k,
            filter_metadata=filter_metadata,
        )

        data: dict[str, Any] = {
            "results": results,
            "query": params.query,
            "count": len(results),
        }
        return _fmt(data, params.response_format)

    except ImportError as exc:
        logger.warning("rag_query_backend_absent", error=str(exc))
        return _error_json(
            f"RAG backend unavailable — install chromadb and sentence-transformers. ({exc})"
        )
    except Exception as exc:
        logger.error("rag_query_error", error=str(exc))
        return _fmt({"error": str(exc)}, params.response_format)


@mcp.tool(
    name="rag_ingest",
    annotations={
        "title": "RAG Document Ingestion",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def rag_ingest(params: RAGIngestInput) -> str:
    """Ingest documents into the RAG knowledge base.

    Accepts a file path or directory path. Documents are chunked, embedded, and
    persisted in the vector store. Supports markdown, plain text, and PDF files.
    Directories are traversed recursively when *recursive* is True.

    Args:
        params: Path (file or directory), recursive flag, and response format.

    Returns:
        Ingestion statistics: files processed, chunks created, duration, failures.
    """
    try:
        pipeline = await _get_pipeline()
        target = Path(params.path)

        if not target.exists():
            return _fmt({"error": f"Path not found: {params.path}"}, params.response_format)

        if target.is_file():
            doc_ids: list[str] = await pipeline.ingest_file(target)
            result: dict[str, Any] = {
                "ingestion": {
                    "total_files": 1,
                    "total_chunks": len(doc_ids),
                    "duration_seconds": 0,
                    "sources_indexed": [str(target)],
                    "failed_files": [],
                }
            }
        else:
            ing_result = await pipeline.ingest_directory(target, recursive=params.recursive)
            result = {"ingestion": ing_result.to_dict()}

        return _fmt(result, params.response_format)

    except ImportError as exc:
        logger.warning("rag_ingest_backend_absent", error=str(exc))
        return _error_json(
            f"RAG backend unavailable — install chromadb and sentence-transformers. ({exc})"
        )
    except Exception as exc:
        logger.error("rag_ingest_error", error=str(exc))
        return _fmt({"error": str(exc)}, params.response_format)


@mcp.tool(
    name="rag_get_context",
    annotations={
        "title": "RAG Context Retrieval",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def rag_get_context(params: RAGContextInput) -> str:
    """Retrieve formatted context from the knowledge base for a specific question.

    Retrieves the most relevant document chunks and assembles them into a single
    context string with inline source citations, suitable for feeding into an LLM.

    Args:
        params: Question text, max-token budget, top-k chunk count, response format.

    Returns:
        Assembled context string with source citations, ready for prompt injection.
    """
    try:
        pipeline = await _get_pipeline()

        context: str = await pipeline.get_context_for_question(
            question=params.question,
            max_tokens=params.max_tokens,
            top_k=params.top_k,
        )

        data: dict[str, Any] = {"context": context, "question": params.question}
        return _fmt(data, params.response_format)

    except ImportError as exc:
        logger.warning("rag_get_context_backend_absent", error=str(exc))
        return _error_json(
            f"RAG backend unavailable — install chromadb and sentence-transformers. ({exc})"
        )
    except Exception as exc:
        logger.error("rag_get_context_error", error=str(exc))
        return _fmt({"error": str(exc)}, params.response_format)


@mcp.tool(
    name="rag_query_rewrite",
    annotations={
        "title": "RAG Query Rewriter",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def rag_query_rewrite(params: RAGQueryRewriteInput) -> str:
    """Rewrite a query to improve RAG retrieval quality.

    Supports five rewriting strategies:
    - **zero_shot**: Simple paraphrasing, no examples.
    - **few_shot**: Paraphrase guided by in-context examples for consistent style.
    - **sub_queries**: Decomposes a complex question into focused sub-questions.
    - **step_back**: Derives a higher-level conceptual question for broader recall.
    - **hyde**: Generates a hypothetical answer passage to anchor the embedding.

    Args:
        params: Original query, strategy name, number of variations, response format.

    Returns:
        Rewritten query variations with the strategy used and optional reasoning.
    """
    try:
        rewriter = _get_rewriter()

        from orchestration.query_rewriter import QueryRewriteStrategy

        strategy_map: dict[str, QueryRewriteStrategy] = {
            "zero_shot": QueryRewriteStrategy.ZERO_SHOT,
            "few_shot": QueryRewriteStrategy.FEW_SHOT,
            "sub_queries": QueryRewriteStrategy.SUB_QUERIES,
            "step_back": QueryRewriteStrategy.STEP_BACK,
            "hyde": QueryRewriteStrategy.HYDE,
        }
        strategy = strategy_map.get(params.strategy, QueryRewriteStrategy.ZERO_SHOT)

        rewritten = rewriter.rewrite(
            query=params.query,
            strategy=strategy,
            num_variations=params.num_variations,
        )

        data: dict[str, Any] = {
            "rewritten": {
                "original_query": rewritten.original_query,
                "rewritten_queries": rewritten.rewritten_queries,
                "strategy": rewritten.strategy_used,
                "reasoning": rewritten.reasoning,
            }
        }
        return _fmt(data, params.response_format)

    except ImportError as exc:
        logger.warning("rag_query_rewrite_backend_absent", error=str(exc))
        return _error_json(f"RAG backend unavailable — install required dependencies. ({exc})")
    except Exception as exc:
        logger.error("rag_query_rewrite_error", error=str(exc))
        return _fmt({"error": str(exc)}, params.response_format)


@mcp.tool(
    name="rag_list_sources",
    annotations={
        "title": "RAG List Indexed Sources",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def rag_list_sources(params: BaseAgentInput) -> str:
    """List all document sources currently indexed in the knowledge base.

    Args:
        params: Response format (markdown | json).

    Returns:
        List of indexed source paths with total count.
    """
    try:
        pipeline = await _get_pipeline()
        sources: list[str] = await pipeline._vector_store.list_sources()

        data: dict[str, Any] = {"sources": sources, "count": len(sources)}
        return _fmt(data, params.response_format)

    except ImportError as exc:
        logger.warning("rag_list_sources_backend_absent", error=str(exc))
        return _error_json(
            f"RAG backend unavailable — install chromadb and sentence-transformers. ({exc})"
        )
    except Exception as exc:
        logger.error("rag_list_sources_error", error=str(exc))
        return _fmt({"error": str(exc)}, params.response_format)


@mcp.tool(
    name="rag_stats",
    annotations={
        "title": "RAG System Statistics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def rag_stats(params: BaseAgentInput) -> str:
    """Return statistics and configuration for the RAG system.

    Reports vector store document counts, embedding engine info, collection name,
    and backend configuration.

    Args:
        params: Response format (markdown | json).

    Returns:
        System statistics dict including counts, provider, and configuration.
    """
    try:
        pipeline = await _get_pipeline()
        stats: dict[str, Any] = await pipeline.get_stats()

        data: dict[str, Any] = {"stats": stats}
        return _fmt(data, params.response_format)

    except ImportError as exc:
        logger.warning("rag_stats_backend_absent", error=str(exc))
        return _error_json(
            f"RAG backend unavailable — install chromadb and sentence-transformers. ({exc})"
        )
    except Exception as exc:
        logger.error("rag_stats_error", error=str(exc))
        return _fmt({"error": str(exc)}, params.response_format)
