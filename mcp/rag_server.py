"""
RAG MCP Server for DevSkyy Platform
====================================

Model Context Protocol (MCP) server for Retrieval-Augmented Generation.

This server exposes DevSkyy's RAG capabilities as MCP tools that can be used
by Claude Desktop or any MCP-compatible client.

Features:
- Semantic search over indexed documents
- Document ingestion from files/directories
- Context retrieval for questions
- Source listing and statistics

Architecture:
- Built on FastMCP (MCP Python SDK)
- Integrates with DevSkyy's RAG pipeline
- ChromaDB for vector storage
- Sentence Transformers for embeddings

Version: 1.0.0
Python: 3.11+
Framework: FastMCP

Usage:
    python mcp/rag_server.py

    # Or use with Claude Desktop
    {
      "mcpServers": {
        "devskyy-rag": {
          "command": "python",
          "args": ["/path/to/mcp/rag_server.py"],
          "env": {
            "OPENAI_API_KEY": "your-key"
          }
        }
      }
    }
"""

import json
import os
import sys
from enum import Enum
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from pydantic import BaseModel, ConfigDict, Field

    from mcp.server.fastmcp import FastMCP
except ImportError as e:
    print(f"❌ Missing required package: {e}")
    print("Install with: pip install fastmcp pydantic")
    sys.exit(1)

# Import RAG components
try:
    from orchestration.document_ingestion import DocumentIngestionPipeline, IngestionConfig
    from orchestration.embedding_engine import EmbeddingConfig, EmbeddingProvider
    from orchestration.query_rewriter import (
        AdvancedQueryRewriter,
        QueryRewriterConfig,
        QueryRewriteStrategy,
    )
    from orchestration.vector_store import VectorDBType, VectorStoreConfig
except ImportError as e:
    print(f"❌ RAG components not available: {e}")
    print("Make sure orchestration module is properly installed")
    sys.exit(1)


# =============================================================================
# Configuration
# =============================================================================

VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/vectordb")
COLLECTION_NAME = os.getenv("RAG_COLLECTION", "devskyy_docs")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
CHARACTER_LIMIT = 25000
REDIS_URL = os.getenv("REDIS_URL", None)

# Global pipeline instance
_pipeline: DocumentIngestionPipeline | None = None

# Global query rewriter instance
_rewriter: AdvancedQueryRewriter | None = None


# =============================================================================
# Initialize MCP Server
# =============================================================================

mcp = FastMCP(
    "devskyy_rag_mcp",
    dependencies=["chromadb>=0.5.0", "sentence-transformers>=3.0.0", "pydantic>=2.5.0"],
)


# =============================================================================
# Enums & Models
# =============================================================================


class ResponseFormat(str, Enum):
    """Output format for tool responses."""

    MARKDOWN = "markdown"
    JSON = "json"


class BaseInput(BaseModel):
    """Base input model for all tools."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' or 'json'"
    )


class RAGQueryInput(BaseInput):
    """Input for RAG search queries."""

    query: str = Field(..., description="Search query", min_length=1, max_length=5000)
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")
    source_filter: str | None = Field(default=None, description="Filter by source path")


class RAGIngestInput(BaseInput):
    """Input for document ingestion."""

    path: str = Field(..., description="File or directory path to ingest", min_length=1)
    recursive: bool = Field(default=True, description="Recursively ingest subdirectories")


class RAGContextInput(BaseInput):
    """Input for context retrieval."""

    question: str = Field(..., description="Question to get context for", min_length=1)
    max_tokens: int = Field(default=2000, ge=100, le=8000, description="Maximum context tokens")
    top_k: int = Field(default=5, ge=1, le=10, description="Number of chunks to retrieve")


class RAGQueryRewriteInput(BaseInput):
    """Input for query rewriting."""

    query: str = Field(..., description="Query to rewrite", min_length=1, max_length=5000)
    strategy: str = Field(
        default="zero_shot",
        description="Rewriting strategy: zero_shot, few_shot, sub_queries, step_back, hyde",
    )
    num_variations: int = Field(default=3, ge=1, le=5, description="Number of query variations")


# =============================================================================
# Helper Functions
# =============================================================================


async def get_pipeline() -> DocumentIngestionPipeline:
    """Get or create the RAG pipeline."""
    global _pipeline

    if _pipeline is None:
        # Configure vector store
        vector_config = VectorStoreConfig(
            db_type=VectorDBType.CHROMADB,
            collection_name=COLLECTION_NAME,
            persist_directory=VECTOR_DB_PATH,
        )

        # Configure embeddings
        embedding_config = EmbeddingConfig(
            provider=(
                EmbeddingProvider.SENTENCE_TRANSFORMERS
                if EMBEDDING_PROVIDER == "sentence_transformers"
                else EmbeddingProvider.OPENAI
            ),
        )

        # Create and initialize pipeline
        from orchestration.embedding_engine import create_embedding_engine
        from orchestration.vector_store import create_vector_store

        vector_store = create_vector_store(vector_config)
        embedding_engine = create_embedding_engine(embedding_config)

        _pipeline = DocumentIngestionPipeline(
            vector_store=vector_store,
            embedding_engine=embedding_engine,
            config=IngestionConfig(),
        )
        await _pipeline.initialize()

    return _pipeline


def get_rewriter() -> AdvancedQueryRewriter:
    """Get or create the query rewriter."""
    global _rewriter

    if _rewriter is None:
        config = QueryRewriterConfig(
            redis_url=REDIS_URL,
            cache_enabled=REDIS_URL is not None,
        )
        _rewriter = AdvancedQueryRewriter(config)

    return _rewriter


def format_response(data: dict[str, Any], fmt: ResponseFormat) -> str:
    """Format response based on requested format."""
    if fmt == ResponseFormat.JSON:
        return json.dumps(data, indent=2, default=str)

    # Markdown format
    output = []

    if "error" in data:
        return f"❌ **Error:** {data['error']}"

    if "results" in data:
        output.append(f"## Search Results ({len(data['results'])} found)\n")
        for i, result in enumerate(data["results"], 1):
            doc = result.get("document", {})
            score = result.get("score", 0)
            source = doc.get("source", "unknown")
            content = doc.get("content", "")[:500]
            output.append(f"### {i}. {source} (score: {score:.3f})")
            output.append(f"```\n{content}\n```\n")

    if "context" in data:
        output.append("## Retrieved Context\n")
        output.append(data["context"])

    if "ingestion" in data:
        ing = data["ingestion"]
        output.append("## Ingestion Results\n")
        output.append(f"- **Files processed:** {ing.get('total_files', 0)}")
        output.append(f"- **Chunks created:** {ing.get('total_chunks', 0)}")
        output.append(f"- **Duration:** {ing.get('duration_seconds', 0):.2f}s")
        if ing.get("failed_files"):
            output.append(f"- **Failed:** {', '.join(ing['failed_files'])}")

    if "sources" in data:
        output.append("## Indexed Sources\n")
        for source in data["sources"]:
            output.append(f"- {source}")

    if "stats" in data:
        stats = data["stats"]
        output.append("## RAG Statistics\n")
        output.append(f"```json\n{json.dumps(stats, indent=2)}\n```")

    return "\n".join(output) if output else json.dumps(data, indent=2)


# =============================================================================
# MCP Tools
# =============================================================================


@mcp.tool()
async def rag_query(input: RAGQueryInput) -> str:
    """
    Search the knowledge base for relevant documents.

    Use this tool to find information from indexed documents using semantic search.
    Returns the most relevant document chunks based on the query.

    Args:
        input: Query parameters including search text and filters

    Returns:
        Search results with document content and relevance scores
    """
    try:
        pipeline = await get_pipeline()

        filter_metadata = None
        if input.source_filter:
            filter_metadata = {"source": {"$contains": input.source_filter}}

        results = await pipeline.search(
            query=input.query,
            top_k=input.top_k,
            filter_metadata=filter_metadata,
        )

        response = {"results": results, "query": input.query, "count": len(results)}
        return format_response(response, input.response_format)[:CHARACTER_LIMIT]

    except Exception as e:
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def rag_ingest(input: RAGIngestInput) -> str:
    """
    Ingest documents into the knowledge base.

    Use this tool to add new documents (markdown, text, PDF) to the RAG system.
    Documents are chunked, embedded, and stored in the vector database.

    Args:
        input: Path to file or directory to ingest

    Returns:
        Ingestion statistics including chunks created and any failures
    """
    try:
        pipeline = await get_pipeline()
        path = Path(input.path)

        if not path.exists():
            return format_response(
                {"error": f"Path not found: {input.path}"}, input.response_format
            )

        if path.is_file():
            doc_ids = await pipeline.ingest_file(path)
            result = {
                "ingestion": {
                    "total_files": 1,
                    "total_chunks": len(doc_ids),
                    "duration_seconds": 0,
                    "sources_indexed": [str(path)],
                }
            }
        else:
            ing_result = await pipeline.ingest_directory(path, recursive=input.recursive)
            result = {"ingestion": ing_result.to_dict()}

        return format_response(result, input.response_format)[:CHARACTER_LIMIT]

    except Exception as e:
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def rag_get_context(input: RAGContextInput) -> str:
    """
    Get relevant context for answering a question.

    Use this tool to retrieve context from the knowledge base that can help
    answer a specific question. Returns formatted context with source citations.

    Args:
        input: Question and context parameters

    Returns:
        Formatted context string with source citations
    """
    try:
        pipeline = await get_pipeline()

        context = await pipeline.get_context_for_question(
            question=input.question,
            max_tokens=input.max_tokens,
            top_k=input.top_k,
        )

        response = {"context": context, "question": input.question}
        return format_response(response, input.response_format)[:CHARACTER_LIMIT]

    except Exception as e:
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def rag_query_rewrite(input: RAGQueryRewriteInput) -> str:
    """
    Rewrite a query to improve RAG retrieval.

    Use this tool to improve query quality before semantic search.
    Supports multiple rewriting strategies:
    - zero_shot: Simple paraphrasing
    - few_shot: Uses examples for consistent style
    - sub_queries: Decomposes complex questions
    - step_back: Generates higher-level conceptual questions
    - hyde: Generates hypothetical answer passages

    Args:
        input: Query and rewriting parameters

    Returns:
        Rewritten query variations with explanations
    """
    try:
        rewriter = get_rewriter()

        # Map strategy string to enum
        strategy_map = {
            "zero_shot": QueryRewriteStrategy.ZERO_SHOT,
            "few_shot": QueryRewriteStrategy.FEW_SHOT,
            "sub_queries": QueryRewriteStrategy.SUB_QUERIES,
            "step_back": QueryRewriteStrategy.STEP_BACK,
            "hyde": QueryRewriteStrategy.HYDE,
        }

        strategy = strategy_map.get(input.strategy, QueryRewriteStrategy.ZERO_SHOT)

        rewritten = rewriter.rewrite(
            query=input.query,
            strategy=strategy,
            num_variations=input.num_variations,
        )

        response = {
            "rewritten": {
                "original_query": rewritten.original_query,
                "rewritten_queries": rewritten.rewritten_queries,
                "strategy": rewritten.strategy_used,
                "reasoning": rewritten.reasoning,
            }
        }

        return format_response(response, input.response_format)[:CHARACTER_LIMIT]

    except Exception as e:
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def rag_list_sources(input: BaseInput) -> str:
    """
    List all indexed document sources.

    Use this tool to see what documents have been indexed in the knowledge base.

    Returns:
        List of all indexed source paths
    """
    try:
        pipeline = await get_pipeline()
        sources = await pipeline._vector_store.list_sources()

        response = {"sources": sources, "count": len(sources)}
        return format_response(response, input.response_format)[:CHARACTER_LIMIT]

    except Exception as e:
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def rag_stats(input: BaseInput) -> str:
    """
    Get RAG system statistics.

    Use this tool to check the status of the RAG system including
    vector store stats and embedding engine info.

    Returns:
        System statistics and configuration
    """
    try:
        pipeline = await get_pipeline()
        stats = await pipeline.get_stats()

        response = {"stats": stats}
        return format_response(response, input.response_format)[:CHARACTER_LIMIT]

    except Exception as e:
        return format_response({"error": str(e)}, input.response_format)


# =============================================================================
# Main Entry Point
# =============================================================================


if __name__ == "__main__":
    print("🚀 Starting DevSkyy RAG MCP Server...")
    print(f"   Vector DB: {VECTOR_DB_PATH}")
    print(f"   Collection: {COLLECTION_NAME}")
    print(f"   Embeddings: {EMBEDDING_PROVIDER}")
    mcp.run()
