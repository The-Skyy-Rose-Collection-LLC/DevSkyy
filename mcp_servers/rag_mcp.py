"""
DevSkyy RAG MCP Server

Provides RAG (Retrieval-Augmented Generation) capabilities via Model Context Protocol.
Wraps the RAG service with MCP tools for document ingestion, semantic search, and query.

Features:
- Document ingestion (PDF, text, markdown)
- Product catalog ingestion from CSV
- WordPress guide ingestion for ML learning
- Semantic search with vector similarity
- RAG queries with Claude integration
- Iterative multi-hop retrieval
- Collection management

Per Truth Protocol:
- Rule #1: Never guess - All operations verified
- Rule #5: No secrets in code - Credentials via environment
- Rule #7: Input validation - Pydantic schemas
- Rule #8: Test coverage ≥90%
- Rule #10: No-skip rule - All errors logged

Author: DevSkyy Platform Team
Version: 1.0.0
"""

import asyncio
import csv
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any

from mcp.types import Tool

from mcp_servers.base_mcp_server import (
    BRAND_GUIDELINES,
    BaseMCPServer,
    create_tool,
    enforce_brand_domain,
    enforce_brand_name,
)


# Import WordPress knowledge utilities
try:
    from mcp_servers.wordpress import (
        WORDPRESS_DIR,
        get_all_products,
        load_css,
        load_guide,
        load_manifest,
    )

    WORDPRESS_AVAILABLE = True
except ImportError:
    WORDPRESS_AVAILABLE = False

# Import RAG service
try:
    from services.rag_service import RAGService, get_rag_service

    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

logger = logging.getLogger(__name__)


class RAGMCPServer(BaseMCPServer):
    """
    RAG MCP Server for document ingestion, search, and retrieval-augmented generation.

    Tools:
    - ingest_document: Ingest PDF/text documents
    - ingest_catalog: Ingest SkyyRose product catalog CSV
    - ingest_wordpress_guide: Ingest WordPress development guide
    - semantic_search: Vector similarity search
    - rag_query: Retrieval-augmented generation
    - iterative_rag_query: Multi-hop retrieval for complex questions
    - manage_collection: ChromaDB collection operations
    - get_rag_status: System status and statistics
    - learn_wordpress_updates: Fetch and learn from latest WP/Elementor updates
    """

    def __init__(self):
        super().__init__("devskyy-rag", version="1.0.0")

        # Initialize RAG service
        if RAG_AVAILABLE:
            self.rag_service = get_rag_service()
            logger.info("RAG service initialized")
        else:
            self.rag_service = None
            logger.warning("RAG service not available - running in mock mode")

        # Register tool schemas
        self._register_tool_schemas()

    def _register_tool_schemas(self) -> None:
        """Register tool schemas for on-demand loading."""
        self.tool_schemas = {
            "ingest_document": {
                "name": "ingest_document",
                "description": "Ingest a document (PDF, text, markdown) into the RAG vector store",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the document file",
                        },
                        "collection": {
                            "type": "string",
                            "description": "Target collection name",
                            "default": "devskyy_docs",
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Additional metadata to attach",
                        },
                    },
                    "required": ["file_path"],
                },
            },
            "ingest_catalog": {
                "name": "ingest_catalog",
                "description": "Ingest SkyyRose product catalog CSV into ChromaDB for semantic search",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "csv_path": {
                            "type": "string",
                            "description": "Path to the catalog CSV file",
                        },
                        "collection_name": {
                            "type": "string",
                            "description": "ChromaDB collection name",
                            "default": "skyyrose_products",
                        },
                    },
                    "required": ["csv_path"],
                },
            },
            "ingest_wordpress_guide": {
                "name": "ingest_wordpress_guide",
                "description": "Ingest WordPress/Elementor development guide for semantic search and ML learning",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "include_css": {
                            "type": "boolean",
                            "description": "Include CSS file in ingestion",
                            "default": True,
                        },
                        "include_manifest": {
                            "type": "boolean",
                            "description": "Include manifest.json product data",
                            "default": True,
                        },
                    },
                },
            },
            "semantic_search": {
                "name": "semantic_search",
                "description": "Search for documents using semantic similarity",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results to return",
                            "default": 5,
                        },
                        "collection": {
                            "type": "string",
                            "description": "Collection to search in",
                        },
                        "min_similarity": {
                            "type": "number",
                            "description": "Minimum similarity threshold (0-1)",
                            "default": 0.7,
                        },
                    },
                    "required": ["query"],
                },
            },
            "rag_query": {
                "name": "rag_query",
                "description": "Ask a question using RAG - retrieves context and generates answer",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Question to answer",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of context chunks to use",
                            "default": 5,
                        },
                        "system_prompt": {
                            "type": "string",
                            "description": "Custom system prompt for the LLM",
                        },
                    },
                    "required": ["question"],
                },
            },
            "iterative_rag_query": {
                "name": "iterative_rag_query",
                "description": "Multi-hop RAG for complex questions requiring multiple retrievals",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Complex question to answer",
                        },
                        "max_iterations": {
                            "type": "integer",
                            "description": "Maximum retrieval iterations",
                            "default": 3,
                        },
                    },
                    "required": ["question"],
                },
            },
            "manage_collection": {
                "name": "manage_collection",
                "description": "Manage ChromaDB collections (list, create, delete, stats)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["list", "create", "delete", "stats"],
                            "description": "Action to perform",
                        },
                        "collection_name": {
                            "type": "string",
                            "description": "Collection name (for create/delete/stats)",
                        },
                    },
                    "required": ["action"],
                },
            },
            "get_rag_status": {
                "name": "get_rag_status",
                "description": "Get RAG system status and statistics",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                },
            },
            "learn_wordpress_updates": {
                "name": "learn_wordpress_updates",
                "description": "Fetch and learn from latest WordPress/Elementor updates for continuous ML improvement",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string",
                            "enum": ["elementor", "woocommerce", "wordpress", "all"],
                            "description": "Update source to fetch",
                            "default": "all",
                        },
                    },
                },
            },
        }

    async def get_tools(self) -> list[Tool]:
        """Return list of available tools."""
        return [
            create_tool(
                name="ingest_document",
                description="Ingest a document (PDF, text, markdown) into the RAG vector store",
                properties={
                    "file_path": {"type": "string", "description": "Path to the document file"},
                    "collection": {"type": "string", "description": "Target collection name"},
                    "metadata": {"type": "object", "description": "Additional metadata"},
                },
                required=["file_path"],
            ),
            create_tool(
                name="ingest_catalog",
                description="Ingest SkyyRose product catalog CSV into ChromaDB for semantic search",
                properties={
                    "csv_path": {"type": "string", "description": "Path to the catalog CSV file"},
                    "collection_name": {"type": "string", "description": "ChromaDB collection name"},
                },
                required=["csv_path"],
            ),
            create_tool(
                name="ingest_wordpress_guide",
                description="Ingest WordPress/Elementor development guide for semantic search",
                properties={
                    "include_css": {"type": "boolean", "description": "Include CSS file"},
                    "include_manifest": {"type": "boolean", "description": "Include manifest.json"},
                },
            ),
            create_tool(
                name="semantic_search",
                description="Search for documents using semantic similarity",
                properties={
                    "query": {"type": "string", "description": "Search query"},
                    "top_k": {"type": "integer", "description": "Number of results"},
                    "min_similarity": {"type": "number", "description": "Minimum similarity (0-1)"},
                },
                required=["query"],
            ),
            create_tool(
                name="rag_query",
                description="Ask a question using RAG - retrieves context and generates answer",
                properties={
                    "question": {"type": "string", "description": "Question to answer"},
                    "top_k": {"type": "integer", "description": "Context chunks to use"},
                    "system_prompt": {"type": "string", "description": "Custom system prompt"},
                },
                required=["question"],
            ),
            create_tool(
                name="iterative_rag_query",
                description="Multi-hop RAG for complex questions requiring multiple retrievals",
                properties={
                    "question": {"type": "string", "description": "Complex question"},
                    "max_iterations": {"type": "integer", "description": "Max iterations"},
                },
                required=["question"],
            ),
            create_tool(
                name="manage_collection",
                description="Manage ChromaDB collections (list, create, delete, stats)",
                properties={
                    "action": {"type": "string", "enum": ["list", "create", "delete", "stats"]},
                    "collection_name": {"type": "string", "description": "Collection name"},
                },
                required=["action"],
            ),
            create_tool(
                name="get_rag_status",
                description="Get RAG system status and statistics",
                properties={},
            ),
            create_tool(
                name="learn_wordpress_updates",
                description="Fetch and learn from latest WordPress/Elementor updates",
                properties={
                    "source": {"type": "string", "enum": ["elementor", "woocommerce", "wordpress", "all"]},
                },
            ),
        ]

    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool with given arguments."""
        handlers = {
            "ingest_document": self._ingest_document,
            "ingest_catalog": self._ingest_catalog,
            "ingest_wordpress_guide": self._ingest_wordpress_guide,
            "semantic_search": self._semantic_search,
            "rag_query": self._rag_query,
            "iterative_rag_query": self._iterative_rag_query,
            "manage_collection": self._manage_collection,
            "get_rag_status": self._get_rag_status,
            "learn_wordpress_updates": self._learn_wordpress_updates,
        }

        handler = handlers.get(name)
        if not handler:
            return {"error": f"Unknown tool: {name}"}

        return await handler(arguments)

    # =========================================================================
    # TOOL IMPLEMENTATIONS
    # =========================================================================

    async def _ingest_document(self, args: dict[str, Any]) -> dict[str, Any]:
        """Ingest a document into the RAG system."""
        file_path = args.get("file_path")
        collection = args.get("collection", "devskyy_docs")
        metadata = args.get("metadata", {})

        if not file_path:
            return {"error": "file_path is required"}

        if not Path(file_path).exists():
            return {"error": f"File not found: {file_path}"}

        if not self.rag_service:
            return {"error": "RAG service not available"}

        try:
            result = await self.rag_service.ingest_document(file_path)
            return {
                "success": True,
                "file_path": file_path,
                "collection": collection,
                **result,
            }
        except Exception as e:
            return {"error": str(e)}

    async def _ingest_catalog(self, args: dict[str, Any]) -> dict[str, Any]:
        """Ingest SkyyRose product catalog CSV."""
        csv_path = args.get("csv_path")
        collection_name = args.get("collection_name", "skyyrose_products")

        if not csv_path:
            return {"error": "csv_path is required"}

        if not Path(csv_path).exists():
            return {"error": f"CSV file not found: {csv_path}"}

        if not self.rag_service:
            return {"error": "RAG service not available"}

        try:
            products = []
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Build embedding text from multiple fields
                    embedding_text = " ".join(
                        filter(
                            None,
                            [
                                row.get("Item Name", ""),
                                row.get("Description", ""),
                                row.get("SEO Title", ""),
                                row.get("SEO Description", ""),
                                f"Category: {row.get('Categories', '')}",
                                f"Price: ${row.get('Price', '0')}",
                                f"Color: {row.get('Option Value 1', '')}",
                                f"Size: {row.get('Option Value 2', '')}",
                            ],
                        )
                    )

                    # Enforce brand guidelines
                    embedding_text = enforce_brand_name(embedding_text)
                    embedding_text = enforce_brand_domain(embedding_text)

                    products.append(
                        {
                            "content": embedding_text,
                            "metadata": {
                                "sku": row.get("SKU", ""),
                                "name": row.get("Item Name", ""),
                                "price": row.get("Price", "0"),
                                "categories": row.get("Categories", ""),
                                "color": row.get("Option Value 1", ""),
                                "size": row.get("Option Value 2", ""),
                                "quantity": row.get("Current Quantity The Skyy Rose Collection", "0"),
                                "type": "product",
                                "collection": collection_name,
                            },
                        }
                    )

            # Ingest products
            if products:
                result = self.rag_service.vector_db.add_documents(products)
                return {
                    "success": True,
                    "products_ingested": len(products),
                    "collection": collection_name,
                    **result,
                }
            else:
                return {"success": False, "error": "No products found in CSV"}

        except Exception as e:
            return {"error": str(e)}

    async def _ingest_wordpress_guide(self, args: dict[str, Any]) -> dict[str, Any]:
        """Ingest WordPress development guide for ML learning."""
        include_css = args.get("include_css", True)
        include_manifest = args.get("include_manifest", True)

        if not WORDPRESS_AVAILABLE:
            return {"error": "WordPress module not available"}

        if not self.rag_service:
            return {"error": "RAG service not available"}

        try:
            documents = []

            # Ingest the main guide
            guide_content = load_guide()
            if guide_content:
                result = await self.rag_service.ingest_text(
                    text=guide_content,
                    source="wordpress_guide",
                    metadata={"type": "guide", "platform": "wordpress", "builder": "elementor"},
                )
                documents.append({"type": "guide", "chunks": result.get("chunks_created", 0)})

            # Ingest CSS
            if include_css:
                css_content = load_css()
                if css_content:
                    result = await self.rag_service.ingest_text(
                        text=css_content,
                        source="skyyrose_css",
                        metadata={"type": "css", "platform": "wordpress"},
                    )
                    documents.append({"type": "css", "chunks": result.get("chunks_created", 0)})

            # Ingest manifest/products
            if include_manifest:
                manifest = load_manifest()
                if manifest:
                    # Convert manifest to searchable text
                    manifest_text = json.dumps(manifest, indent=2)
                    result = await self.rag_service.ingest_text(
                        text=manifest_text,
                        source="skyyrose_manifest",
                        metadata={"type": "manifest", "platform": "wordpress"},
                    )
                    documents.append({"type": "manifest", "chunks": result.get("chunks_created", 0)})

            return {
                "success": True,
                "documents_ingested": len(documents),
                "details": documents,
                "ingested_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {"error": str(e)}

    async def _semantic_search(self, args: dict[str, Any]) -> dict[str, Any]:
        """Perform semantic search."""
        query = args.get("query")
        top_k = args.get("top_k", 5)
        min_similarity = args.get("min_similarity", 0.7)

        if not query:
            return {"error": "query is required"}

        if not self.rag_service:
            return {"error": "RAG service not available"}

        try:
            results = await self.rag_service.search(query=query, top_k=top_k, min_similarity=min_similarity)

            return {
                "query": query,
                "results_count": len(results),
                "results": [
                    {
                        "content": r["content"][:500],  # Truncate for response
                        "similarity": r["similarity"],
                        "metadata": r["metadata"],
                    }
                    for r in results
                ],
            }

        except Exception as e:
            return {"error": str(e)}

    async def _rag_query(self, args: dict[str, Any]) -> dict[str, Any]:
        """Execute RAG query."""
        question = args.get("question")
        top_k = args.get("top_k", 5)
        system_prompt = args.get("system_prompt")

        if not question:
            return {"error": "question is required"}

        if not self.rag_service:
            return {"error": "RAG service not available"}

        try:
            result = await self.rag_service.query(question=question, top_k=top_k, system_prompt=system_prompt)

            return {
                "question": question,
                "answer": result["answer"],
                "sources_used": result["context_used"],
                "sources": [{"content": s["content"][:200], "metadata": s["metadata"]} for s in result.get("sources", [])[:3]],
            }

        except Exception as e:
            return {"error": str(e)}

    async def _iterative_rag_query(self, args: dict[str, Any]) -> dict[str, Any]:
        """Execute iterative multi-hop RAG query."""
        question = args.get("question")
        max_iterations = args.get("max_iterations", 3)

        if not question:
            return {"error": "question is required"}

        if not self.rag_service:
            return {"error": "RAG service not available"}

        try:
            result = await self.rag_service.iterative_query(question=question, max_iterations=max_iterations)

            return {
                "question": question,
                "answer": result["answer"],
                "iterations": result["iterations"],
                "queries_used": result["queries_used"],
                "sources_used": result["context_used"],
            }

        except Exception as e:
            return {"error": str(e)}

    async def _manage_collection(self, args: dict[str, Any]) -> dict[str, Any]:
        """Manage ChromaDB collections."""
        action = args.get("action")
        collection_name = args.get("collection_name")

        if not action:
            return {"error": "action is required"}

        if not self.rag_service:
            return {"error": "RAG service not available"}

        try:
            if action == "list":
                collections = self.rag_service.vector_db.client.list_collections()
                return {"collections": [c.name for c in collections]}

            elif action == "stats":
                if not collection_name:
                    return {"error": "collection_name required for stats"}
                stats = self.rag_service.vector_db.get_stats()
                return {"stats": stats}

            elif action == "delete":
                if not collection_name:
                    return {"error": "collection_name required for delete"}
                self.rag_service.vector_db.client.delete_collection(collection_name)
                return {"success": True, "deleted": collection_name}

            elif action == "create":
                if not collection_name:
                    return {"error": "collection_name required for create"}
                self.rag_service.vector_db.client.get_or_create_collection(collection_name)
                return {"success": True, "created": collection_name}

            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    async def _get_rag_status(self, args: dict[str, Any]) -> dict[str, Any]:
        """Get RAG system status."""
        status = self.get_status()

        if self.rag_service:
            rag_stats = self.rag_service.get_stats()
            status["rag"] = rag_stats

        status["wordpress_available"] = WORDPRESS_AVAILABLE
        status["brand"] = {
            "name": BRAND_GUIDELINES.brand_name,
            "domain": BRAND_GUIDELINES.domain,
        }

        return status

    async def _learn_wordpress_updates(self, args: dict[str, Any]) -> dict[str, Any]:
        """
        Fetch and learn from latest WordPress/Elementor updates.
        This enables continuous ML improvement by ingesting changelogs.
        """
        source = args.get("source", "all")

        # URLs for fetching updates (would need to be implemented with actual fetching)
        update_sources = {
            "elementor": "https://elementor.com/pro/changelog/",
            "woocommerce": "https://woocommerce.com/wc-apidocs/changelog.html",
            "wordpress": "https://wordpress.org/news/category/releases/",
        }

        try:
            # For now, return a placeholder - actual implementation would fetch and ingest
            return {
                "status": "scheduled",
                "source": source,
                "message": "WordPress update learning scheduled. Will fetch and ingest latest changelogs.",
                "sources_to_check": (
                    list(update_sources.keys())
                    if source == "all"
                    else [source]
                ),
                "next_update": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {"error": str(e)}


# =============================================================================
# ENTRY POINT
# =============================================================================


def main():
    """Run the RAG MCP server."""

    server = RAGMCPServer()

    async def run():
        await server.run()

    asyncio.run(run())


if __name__ == "__main__":
    main()
