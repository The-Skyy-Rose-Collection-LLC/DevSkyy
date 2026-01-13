# mcp/context7_client.py
"""
Context7 MCP Client for DevSkyy.

Provides access to up-to-date documentation and code examples
for any programming library or framework.

Usage:
    from mcp.context7_client import context7_client

    # Resolve library ID
    library = await context7_client.resolve_library("fastapi")

    # Get documentation
    docs = await context7_client.get_docs(library["id"], "error handling")
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server_manager import mcp_manager

logger = logging.getLogger(__name__)


class Context7Client:
    """
    Context7 MCP client for documentation and library lookup.

    Used by DevSkyy agents for:
    - Looking up library documentation
    - Finding code examples
    - Validating API usage patterns
    - Getting up-to-date framework guides
    """

    SERVER_ID = "context7"

    async def resolve_library(
        self,
        library_name: str,
        query: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Resolve a library name to Context7-compatible ID.

        Args:
            library_name: Name of the library (e.g., "fastapi", "trimesh")
            query: Optional context about what you're looking for

        Returns:
            Library info dict or None if not found
        """
        try:
            result = await mcp_manager.call_tool(
                self.SERVER_ID,
                "resolve-library-id",
                {
                    "libraryName": library_name,
                    "query": query or f"Looking for {library_name} documentation",
                },
            )

            if result.success:
                return result.data.get("library")
            else:
                logger.warning(f"Failed to resolve library {library_name}: {result.error}")
                return None

        except Exception as e:
            logger.error(f"Error resolving library {library_name}: {e}")
            return None

    async def get_docs(
        self,
        library_id: str,
        query: str,
        max_tokens: int = 5000,
    ) -> str:
        """
        Get documentation for a library.

        Args:
            library_id: Context7-compatible library ID (e.g., "/fastapi/fastapi")
            query: Specific topic or question
            max_tokens: Maximum tokens to return

        Returns:
            Documentation text
        """
        try:
            result = await mcp_manager.call_tool(
                self.SERVER_ID,
                "query-docs",
                {
                    "libraryId": library_id,
                    "query": query,
                },
            )

            if result.success:
                return result.data.get("documentation", "")
            else:
                logger.warning(f"Failed to get docs for {library_id}: {result.error}")
                return ""

        except Exception as e:
            logger.error(f"Error getting docs for {library_id}: {e}")
            return ""

    async def search_docs(
        self,
        query: str,
        library_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search documentation across libraries.

        Args:
            query: Search query
            library_name: Optional library to restrict search to

        Returns:
            List of search results
        """
        # First resolve library if specified
        library_id = None
        if library_name:
            library = await self.resolve_library(library_name, query)
            if library:
                library_id = library.get("id")

        try:
            args: dict[str, Any] = {"query": query}
            if library_id:
                args["libraryId"] = library_id

            result = await mcp_manager.call_tool(
                self.SERVER_ID,
                "search-docs",
                args,
            )

            if result.success:
                return result.data.get("results", [])
            return []

        except Exception as e:
            logger.error(f"Error searching docs: {e}")
            return []

    async def get_code_examples(
        self,
        library_name: str,
        topic: str,
    ) -> list[dict[str, Any]]:
        """
        Get code examples for a specific topic.

        Args:
            library_name: Name of the library
            topic: Topic to find examples for

        Returns:
            List of code examples
        """
        # Resolve library
        library = await self.resolve_library(library_name, topic)
        if not library:
            return []

        # Get docs with examples
        docs = await self.get_docs(
            library.get("id", ""),
            f"code examples for {topic}",
        )

        # Parse examples from docs (simplified)
        examples = []
        if docs:
            # Split by code blocks
            parts = docs.split("```")
            for i in range(1, len(parts), 2):
                if i < len(parts):
                    code = parts[i]
                    # Get language hint
                    lines = code.split("\n")
                    language = lines[0].strip() if lines else "python"
                    code_content = "\n".join(lines[1:]) if len(lines) > 1 else code

                    examples.append(
                        {
                            "language": language,
                            "code": code_content.strip(),
                            "topic": topic,
                        }
                    )

        return examples


# Singleton instance
context7_client = Context7Client()
