"""Context7 documentation bridge — anti-hallucination for library code.

Every agent MUST verify library APIs via Context7 before generating code.
This bridge provides resolve_library() and query_docs() as async tools.

API: https://context7.com/api
- GET /v2/libs/search — resolve library name → ID
- GET /v2/context — query docs by library ID

Usage:
    bridge = Context7Bridge()
    lib = await bridge.resolve_library("next.js", "routing setup")
    docs = await bridge.query_docs(lib.id, "how to create dynamic routes")

    # Or one-shot:
    result = await bridge.lookup("woocommerce", "add product via REST API")
    print(result["library"].title)
    for snippet in result["snippets"]:
        print(snippet.code)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class Context7Error(Exception):
    """Raised when Context7 API returns an error or is unreachable."""


# ---------------------------------------------------------------------------
# Data models (immutable)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LibraryInfo:
    """Immutable metadata about a Context7 library."""

    id: str
    title: str
    description: str
    snippets: int = 0
    trust_score: int = 0


@dataclass(frozen=True)
class DocSnippet:
    """Immutable documentation snippet from Context7."""

    title: str
    description: str
    language: str
    code: str
    source_url: str


# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------


class Context7Bridge:
    """Async bridge to the Context7 Public API.

    Provides two core operations:
    1. resolve_library(name, query) → LibraryInfo (best match)
    2. query_docs(library_id, query) → list[DocSnippet]

    Plus a convenience:
    3. lookup(name, query) → {"library": LibraryInfo, "snippets": list[DocSnippet]}
    """

    def __init__(
        self,
        base_url: str = "https://context7.com/api",
        timeout: int = 30,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout

    async def _get(
        self,
        path: str,
        params: dict[str, str],
    ) -> dict[str, Any]:
        """Make a GET request to Context7 API."""
        url = f"{self.base_url}{path}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        raise Context7Error(
                            f"Context7 API error {resp.status}: {body}"
                        )
                    return await resp.json()
        except aiohttp.ClientError as exc:
            raise Context7Error(f"Context7 request failed: {exc}") from exc

    async def resolve_library(
        self,
        library_name: str,
        query: str,
    ) -> LibraryInfo:
        """Resolve a library name to a Context7-compatible ID.

        Args:
            library_name: Library name to search for (e.g., "react", "woocommerce")
            query: The task context for relevance ranking

        Returns:
            LibraryInfo for the best finalized match

        Raises:
            ValueError: If library_name or query is empty
            Context7Error: If no results or API error
        """
        if not library_name or not library_name.strip():
            raise ValueError("library_name must not be empty")
        if not query or not query.strip():
            raise ValueError("query must not be empty")

        data = await self._get(
            "/v2/libs/search",
            {"libraryName": library_name.strip(), "query": query.strip()},
        )

        results = data.get("results", [])
        if not results:
            raise Context7Error(
                f"No libraries found for '{library_name}'"
            )

        # Filter to finalized only
        finalized = [
            r for r in results
            if r.get("state") == "finalized"
        ]
        if not finalized:
            raise Context7Error(
                f"No finalized libraries found for '{library_name}' "
                f"({len(results)} results, none finalized)"
            )

        # Return best match (API already ranks by relevance)
        best = finalized[0]
        return LibraryInfo(
            id=best["id"],
            title=best.get("title", library_name),
            description=best.get("description", ""),
            snippets=best.get("totalSnippets", 0),
            trust_score=best.get("trustScore", 0),
        )

    async def query_docs(
        self,
        library_id: str,
        query: str,
    ) -> list[DocSnippet]:
        """Query Context7 for documentation snippets.

        Args:
            library_id: Context7 library ID (e.g., "/vercel/next.js")
            query: The question or task to search for

        Returns:
            List of DocSnippet with code and documentation

        Raises:
            ValueError: If library_id or query is empty
            Context7Error: On API error
        """
        if not library_id or not library_id.strip():
            raise ValueError("library_id must not be empty")
        if not query or not query.strip():
            raise ValueError("query must not be empty")

        data = await self._get(
            "/v2/context",
            {"libraryId": library_id.strip(), "query": query.strip()},
        )

        snippets: list[DocSnippet] = []

        # Code snippets
        for cs in data.get("codeSnippets", []):
            code_list = cs.get("codeList", [])
            code = code_list[0]["code"] if code_list else ""
            lang = code_list[0]["language"] if code_list else cs.get("codeLanguage", "")
            snippets.append(DocSnippet(
                title=cs.get("codeTitle", ""),
                description=cs.get("codeDescription", ""),
                language=lang,
                code=code,
                source_url=cs.get("codeId", ""),
            ))

        # Info snippets (prose documentation)
        for info in data.get("infoSnippets", []):
            snippets.append(DocSnippet(
                title=info.get("breadcrumb", info.get("pageId", "Doc")),
                description="",
                language="markdown",
                code=info.get("content", ""),
                source_url=info.get("pageId", ""),
            ))

        return snippets

    async def lookup(
        self,
        library_name: str,
        query: str,
    ) -> dict[str, Any]:
        """Convenience: resolve + query in one call.

        Returns:
            {"library": LibraryInfo, "snippets": list[DocSnippet]}
        """
        lib = await self.resolve_library(library_name, query)
        docs = await self.query_docs(lib.id, query)
        return {"library": lib, "snippets": docs}
