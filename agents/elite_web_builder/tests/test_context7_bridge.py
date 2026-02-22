"""Tests for tools/context7_bridge.py — Context7 documentation lookup.

Every agent must verify library APIs against Context7 docs before
generating code. This bridge provides resolve + query as a tool.
"""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tools.context7_bridge import (
    Context7Bridge,
    Context7Error,
    LibraryInfo,
    DocSnippet,
)


# ---------------------------------------------------------------------------
# Data model tests
# ---------------------------------------------------------------------------


class TestLibraryInfo:
    def test_frozen(self) -> None:
        lib = LibraryInfo(
            id="/vercel/next.js",
            title="Next.js",
            description="The React Framework",
            snippets=3629,
            trust_score=10,
        )
        with pytest.raises(AttributeError):
            lib.id = "/other/lib"  # type: ignore[misc]

    def test_fields(self) -> None:
        lib = LibraryInfo(
            id="/vercel/next.js",
            title="Next.js",
            description="The React Framework",
            snippets=3629,
            trust_score=10,
        )
        assert lib.id == "/vercel/next.js"
        assert lib.title == "Next.js"
        assert lib.snippets == 3629
        assert lib.trust_score == 10

    def test_optional_fields_default(self) -> None:
        lib = LibraryInfo(
            id="/x/y",
            title="Y",
            description="Desc",
        )
        assert lib.snippets == 0
        assert lib.trust_score == 0


class TestDocSnippet:
    def test_frozen(self) -> None:
        snip = DocSnippet(
            title="Example",
            description="How to use X",
            language="python",
            code="import x",
            source_url="https://example.com/docs",
        )
        with pytest.raises(AttributeError):
            snip.title = "Changed"  # type: ignore[misc]

    def test_fields(self) -> None:
        snip = DocSnippet(
            title="Example",
            description="How to use X",
            language="python",
            code="import x",
            source_url="https://example.com/docs",
        )
        assert snip.title == "Example"
        assert snip.language == "python"
        assert snip.code == "import x"


# ---------------------------------------------------------------------------
# Context7Bridge construction
# ---------------------------------------------------------------------------


class TestBridgeConstruction:
    def test_default_base_url(self) -> None:
        bridge = Context7Bridge()
        assert bridge.base_url == "https://context7.com/api"

    def test_custom_base_url(self) -> None:
        bridge = Context7Bridge(base_url="https://custom.api.com")
        assert bridge.base_url == "https://custom.api.com"

    def test_default_timeout(self) -> None:
        bridge = Context7Bridge()
        assert bridge.timeout == 30


# ---------------------------------------------------------------------------
# resolve_library — success paths
# ---------------------------------------------------------------------------


class TestResolveLibrary:
    @pytest.mark.asyncio
    async def test_resolve_returns_best_match(self) -> None:
        """Should return the top result from Context7 search."""
        mock_response = {
            "results": [
                {
                    "id": "/vercel/next.js",
                    "title": "Next.js",
                    "description": "The React Framework",
                    "totalSnippets": 3629,
                    "trustScore": 10,
                    "state": "finalized",
                },
                {
                    "id": "/other/next",
                    "title": "Next Other",
                    "description": "Something else",
                    "totalSnippets": 50,
                    "trustScore": 5,
                    "state": "finalized",
                },
            ]
        }
        bridge = Context7Bridge()
        with patch.object(bridge, "_get", new_callable=AsyncMock, return_value=mock_response):
            result = await bridge.resolve_library("next.js", "How to set up routing")

        assert result.id == "/vercel/next.js"
        assert result.title == "Next.js"
        assert result.snippets == 3629

    @pytest.mark.asyncio
    async def test_resolve_filters_non_finalized(self) -> None:
        """Should skip libraries that aren't in 'finalized' state."""
        mock_response = {
            "results": [
                {
                    "id": "/bad/lib",
                    "title": "Bad Lib",
                    "description": "Processing",
                    "totalSnippets": 9999,
                    "trustScore": 10,
                    "state": "processing",
                },
                {
                    "id": "/good/lib",
                    "title": "Good Lib",
                    "description": "Ready",
                    "totalSnippets": 100,
                    "trustScore": 8,
                    "state": "finalized",
                },
            ]
        }
        bridge = Context7Bridge()
        with patch.object(bridge, "_get", new_callable=AsyncMock, return_value=mock_response):
            result = await bridge.resolve_library("lib", "query")

        assert result.id == "/good/lib"

    @pytest.mark.asyncio
    async def test_resolve_no_results_raises(self) -> None:
        """Should raise Context7Error if no libraries match."""
        mock_response = {"results": []}
        bridge = Context7Bridge()
        with patch.object(bridge, "_get", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(Context7Error, match="No libraries found"):
                await bridge.resolve_library("nonexistent-lib-xyz", "query")

    @pytest.mark.asyncio
    async def test_resolve_all_non_finalized_raises(self) -> None:
        """Should raise if all results are non-finalized."""
        mock_response = {
            "results": [
                {
                    "id": "/x/y",
                    "title": "Y",
                    "description": "D",
                    "totalSnippets": 10,
                    "trustScore": 5,
                    "state": "error",
                },
            ]
        }
        bridge = Context7Bridge()
        with patch.object(bridge, "_get", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(Context7Error, match="No finalized"):
                await bridge.resolve_library("y", "query")

    @pytest.mark.asyncio
    async def test_resolve_empty_library_name_raises(self) -> None:
        bridge = Context7Bridge()
        with pytest.raises(ValueError, match="library_name"):
            await bridge.resolve_library("", "query")

    @pytest.mark.asyncio
    async def test_resolve_empty_query_raises(self) -> None:
        bridge = Context7Bridge()
        with pytest.raises(ValueError, match="query"):
            await bridge.resolve_library("react", "")


# ---------------------------------------------------------------------------
# query_docs — success paths
# ---------------------------------------------------------------------------


class TestQueryDocs:
    @pytest.mark.asyncio
    async def test_query_returns_snippets(self) -> None:
        mock_response = {
            "codeSnippets": [
                {
                    "codeTitle": "App Router Setup",
                    "codeDescription": "How to set up the app router",
                    "codeLanguage": "typescript",
                    "codeTokens": 200,
                    "codeId": "https://nextjs.org/docs/app/getting-started",
                    "pageTitle": "Getting Started",
                    "codeList": [
                        {"language": "typescript", "code": "export default function RootLayout() {}"}
                    ],
                }
            ],
            "infoSnippets": [],
        }
        bridge = Context7Bridge()
        with patch.object(bridge, "_get", new_callable=AsyncMock, return_value=mock_response):
            snippets = await bridge.query_docs("/vercel/next.js", "app router setup")

        assert len(snippets) == 1
        assert snippets[0].title == "App Router Setup"
        assert snippets[0].language == "typescript"
        assert "RootLayout" in snippets[0].code

    @pytest.mark.asyncio
    async def test_query_empty_results_returns_empty(self) -> None:
        mock_response = {"codeSnippets": [], "infoSnippets": []}
        bridge = Context7Bridge()
        with patch.object(bridge, "_get", new_callable=AsyncMock, return_value=mock_response):
            snippets = await bridge.query_docs("/vercel/next.js", "nonexistent feature")

        assert snippets == []

    @pytest.mark.asyncio
    async def test_query_includes_info_snippets(self) -> None:
        """Info snippets (prose docs) should also be returned."""
        mock_response = {
            "codeSnippets": [],
            "infoSnippets": [
                {
                    "pageId": "https://docs.example.com/intro",
                    "breadcrumb": "Docs > Intro",
                    "content": "Welcome to the library.",
                    "contentTokens": 50,
                }
            ],
        }
        bridge = Context7Bridge()
        with patch.object(bridge, "_get", new_callable=AsyncMock, return_value=mock_response):
            snippets = await bridge.query_docs("/example/lib", "introduction")

        assert len(snippets) == 1
        assert snippets[0].title == "Docs > Intro"
        assert snippets[0].code == "Welcome to the library."
        assert snippets[0].language == "markdown"

    @pytest.mark.asyncio
    async def test_query_empty_library_id_raises(self) -> None:
        bridge = Context7Bridge()
        with pytest.raises(ValueError, match="library_id"):
            await bridge.query_docs("", "query")

    @pytest.mark.asyncio
    async def test_query_empty_query_raises(self) -> None:
        bridge = Context7Bridge()
        with pytest.raises(ValueError, match="query"):
            await bridge.query_docs("/vercel/next.js", "")

    @pytest.mark.asyncio
    async def test_query_multiple_code_examples(self) -> None:
        """A snippet with multiple code examples should use the first."""
        mock_response = {
            "codeSnippets": [
                {
                    "codeTitle": "Multi-lang",
                    "codeDescription": "Example in multiple languages",
                    "codeLanguage": "javascript",
                    "codeTokens": 100,
                    "codeId": "https://example.com",
                    "pageTitle": "Multi",
                    "codeList": [
                        {"language": "javascript", "code": "const x = 1"},
                        {"language": "typescript", "code": "const x: number = 1"},
                    ],
                }
            ],
            "infoSnippets": [],
        }
        bridge = Context7Bridge()
        with patch.object(bridge, "_get", new_callable=AsyncMock, return_value=mock_response):
            snippets = await bridge.query_docs("/example/lib", "example")

        assert snippets[0].code == "const x = 1"
        assert snippets[0].language == "javascript"


# ---------------------------------------------------------------------------
# lookup convenience method
# ---------------------------------------------------------------------------


class TestLookup:
    @pytest.mark.asyncio
    async def test_lookup_resolves_then_queries(self) -> None:
        """lookup() should call resolve_library then query_docs."""
        bridge = Context7Bridge()

        lib = LibraryInfo(
            id="/vercel/next.js",
            title="Next.js",
            description="Framework",
            snippets=100,
            trust_score=10,
        )
        snip = DocSnippet(
            title="Routing",
            description="How routing works",
            language="typescript",
            code="export default function Page() {}",
            source_url="https://nextjs.org/docs",
        )

        with patch.object(bridge, "resolve_library", new_callable=AsyncMock, return_value=lib), \
             patch.object(bridge, "query_docs", new_callable=AsyncMock, return_value=[snip]):
            result = await bridge.lookup("next.js", "how does routing work")

        assert result["library"].id == "/vercel/next.js"
        assert len(result["snippets"]) == 1
        assert result["snippets"][0].title == "Routing"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_context7_error_is_exception(self) -> None:
        err = Context7Error("Something went wrong")
        assert isinstance(err, Exception)
        assert str(err) == "Something went wrong"

    @pytest.mark.asyncio
    async def test_get_http_error_raises(self) -> None:
        """HTTP errors from the API should become Context7Error."""
        bridge = Context7Bridge()
        mock_resp = MagicMock()
        mock_resp.status = 429
        mock_resp.text = AsyncMock(return_value='{"error":"rate_limited","message":"Too many requests"}')
        mock_resp.raise_for_status = MagicMock(side_effect=Exception("429"))

        with patch("aiohttp.ClientSession") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session.get = MagicMock(return_value=mock_resp)
            mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_resp.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_session

            with pytest.raises(Context7Error, match="429"):
                await bridge._get("/v2/libs/search", {"libraryName": "x", "query": "y"})
