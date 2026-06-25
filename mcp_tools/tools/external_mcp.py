"""
Tool wrappers that expose external MCP client methods as @mcp.tool() callables.

Covered surfaces:
- Context7  (resolve_library, get_docs, search_docs, get_code_examples)
- Playwright (navigate, screenshot, click, fill, evaluate,
               get_page_content, test_3d_viewer, test_wordpress_page)
- Serena     (analyze_file, find_issues, validate_security,
               full_project_audit, check_code_style)

Every tool body is wrapped in try/except so errors are returned as a JSON
envelope rather than propagating as exceptions.  No network calls are made at
import time — the client singletons are lazy-connecting.

Registration: add "external_mcp" to _TOOL_MODULES in mcp_tools/tools/__init__.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp_tools.external_clients import context7_client, playwright_client, serena_client
from mcp_tools.server import CHARACTER_LIMIT, logger, mcp

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ok(data: Any) -> str:
    """Serialise a successful result to a JSON string, truncated to CHARACTER_LIMIT."""
    text = json.dumps({"success": True, "data": data}, default=str)
    if len(text) > CHARACTER_LIMIT:
        text = text[:CHARACTER_LIMIT]
    return text


def _err(tool: str, exc: Exception) -> str:
    """Serialise an error result."""
    return json.dumps({"success": False, "tool": tool, "error": str(exc)})


# ---------------------------------------------------------------------------
# Context7 tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="context7_resolve_library",
    annotations={
        "title": "Context7 — Resolve Library ID",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def context7_resolve_library(
    library_name: str,
    query: str | None = None,
) -> str:
    """Resolve a library name to its Context7-compatible ID.

    Calls the Context7 MCP server at api.context7.io.  Returns the library
    info dict (including ``id``) needed by the other context7_* tools.

    Args:
        library_name: Name of the library, e.g. ``"fastapi"`` or ``"trimesh"``.
        query: Optional free-text hint about what you are looking for.

    Returns:
        JSON string with ``{"success": true, "data": {library info}}`` or an
        error envelope if the server is unreachable or the library is unknown.
    """
    try:
        result = await context7_client.resolve_library(library_name, query)
        return _ok(result)
    except Exception as exc:
        logger.error("context7_resolve_library failed", exc_info=exc)
        return _err("context7_resolve_library", exc)


@mcp.tool(
    name="context7_get_docs",
    annotations={
        "title": "Context7 — Get Library Documentation",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def context7_get_docs(
    library_id: str,
    query: str,
    max_tokens: int = 5000,
) -> str:
    """Fetch documentation for a library from Context7.

    Args:
        library_id: Context7-compatible library ID, e.g. ``"/fastapi/fastapi"``.
            Obtain this from ``context7_resolve_library`` first.
        query: Specific topic or question, e.g. ``"dependency injection"``.
        max_tokens: Soft cap on how many tokens to return (default 5000).

    Returns:
        JSON string with ``{"success": true, "data": "<docs text>"}`` or an
        error envelope.
    """
    try:
        result = await context7_client.get_docs(library_id, query, max_tokens)
        return _ok(result)
    except Exception as exc:
        logger.error("context7_get_docs failed", exc_info=exc)
        return _err("context7_get_docs", exc)


@mcp.tool(
    name="context7_search_docs",
    annotations={
        "title": "Context7 — Search Documentation",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def context7_search_docs(
    query: str,
    library_name: str | None = None,
) -> str:
    """Search documentation across all Context7 libraries (or within one).

    Args:
        query: Free-text search query.
        library_name: Optional library name to scope the search, e.g.
            ``"pydantic"``.  When provided the library is resolved first.

    Returns:
        JSON string with ``{"success": true, "data": [result, ...]}`` or an
        error envelope.
    """
    try:
        result = await context7_client.search_docs(query, library_name)
        return _ok(result)
    except Exception as exc:
        logger.error("context7_search_docs failed", exc_info=exc)
        return _err("context7_search_docs", exc)


@mcp.tool(
    name="context7_get_code_examples",
    annotations={
        "title": "Context7 — Get Code Examples",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def context7_get_code_examples(
    library_name: str,
    topic: str,
) -> str:
    """Fetch fenced code-block examples for a library topic from Context7.

    Internally resolves the library, fetches its documentation, and extracts
    all fenced code blocks that match the topic.

    Args:
        library_name: Library name, e.g. ``"httpx"``.
        topic: Topic to find examples for, e.g. ``"async streaming response"``.

    Returns:
        JSON string with ``{"success": true, "data": [{"language": ..., "code":
        ..., "topic": ...}, ...]}`` or an error envelope.
    """
    try:
        result = await context7_client.get_code_examples(library_name, topic)
        return _ok(result)
    except Exception as exc:
        logger.error("context7_get_code_examples failed", exc_info=exc)
        return _err("context7_get_code_examples", exc)


# ---------------------------------------------------------------------------
# Playwright tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="playwright_navigate",
    annotations={
        "title": "Playwright — Navigate to URL",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def playwright_navigate(url: str) -> str:
    """Navigate the Playwright browser to a URL.

    Requires the Playwright MCP sidecar to be running on localhost:3001.

    Args:
        url: Fully-qualified URL to navigate to.

    Returns:
        JSON string with ``{"success": true, "data": {navigation result}}`` or
        an error envelope.
    """
    try:
        result = await playwright_client.navigate(url)
        return _ok(result)
    except Exception as exc:
        logger.error("playwright_navigate failed", exc_info=exc)
        return _err("playwright_navigate", exc)


@mcp.tool(
    name="playwright_screenshot",
    annotations={
        "title": "Playwright — Take Screenshot",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def playwright_screenshot(
    full_page: bool = False,
    selector: str | None = None,
    output_path: str | None = None,
) -> str:
    """Take a screenshot of the current browser page.

    Args:
        full_page: Capture the full scrollable page (default False).
        selector: Optional CSS selector to capture only that element.
        output_path: Optional filesystem path to write the PNG file.

    Returns:
        JSON string with ``{"success": true, "data": "<base64-encoded PNG>"}``
        or an error envelope.  The raw bytes are base64-encoded so they survive
        JSON serialisation.
    """
    try:
        import base64

        path: Path | None = Path(output_path) if output_path else None
        image_bytes = await playwright_client.screenshot(
            output_path=path,
            full_page=full_page,
            selector=selector,
        )
        return _ok(base64.b64encode(image_bytes).decode() if image_bytes else None)
    except Exception as exc:
        logger.error("playwright_screenshot failed", exc_info=exc)
        return _err("playwright_screenshot", exc)


@mcp.tool(
    name="playwright_click",
    annotations={
        "title": "Playwright — Click Element",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def playwright_click(selector: str) -> str:
    """Click an element in the current browser page.

    Args:
        selector: CSS selector identifying the element to click.

    Returns:
        JSON string with click result or an error envelope.
    """
    try:
        result = await playwright_client.click(selector)
        return _ok(result)
    except Exception as exc:
        logger.error("playwright_click failed", exc_info=exc)
        return _err("playwright_click", exc)


@mcp.tool(
    name="playwright_fill",
    annotations={
        "title": "Playwright — Fill Input Field",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def playwright_fill(selector: str, value: str) -> str:
    """Fill an input field in the current browser page.

    Args:
        selector: CSS selector for the input element.
        value: Text value to type into the input.

    Returns:
        JSON string with fill result or an error envelope.
    """
    try:
        result = await playwright_client.fill(selector, value)
        return _ok(result)
    except Exception as exc:
        logger.error("playwright_fill failed", exc_info=exc)
        return _err("playwright_fill", exc)


@mcp.tool(
    name="playwright_evaluate",
    annotations={
        "title": "Playwright — Evaluate JavaScript",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def playwright_evaluate(script: str) -> str:
    """Evaluate a JavaScript expression in the current browser page.

    Args:
        script: JavaScript code to execute, e.g.
            ``"document.title"`` or ``"window.__jsErrors || []"``.

    Returns:
        JSON string with ``{"success": true, "data": <script return value>}``
        or an error envelope.
    """
    try:
        result = await playwright_client.evaluate(script)
        return _ok(result)
    except Exception as exc:
        logger.error("playwright_evaluate failed", exc_info=exc)
        return _err("playwright_evaluate", exc)


@mcp.tool(
    name="playwright_get_page_content",
    annotations={
        "title": "Playwright — Get Page HTML",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def playwright_get_page_content() -> str:
    """Return the full outer HTML of the current browser page.

    Returns:
        JSON string with ``{"success": true, "data": "<html>...</html>"}`` or
        an error envelope.
    """
    try:
        result = await playwright_client.get_page_content()
        return _ok(result)
    except Exception as exc:
        logger.error("playwright_get_page_content failed", exc_info=exc)
        return _err("playwright_get_page_content", exc)


@mcp.tool(
    name="playwright_test_3d_viewer",
    annotations={
        "title": "Playwright — Test 3D Viewer",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def playwright_test_3d_viewer(product_url: str) -> str:
    """Run the 5-step SkyyRose 3D viewer test suite against a product page.

    Checks: button exists → modal opens → canvas rendered → loading completes
    → WebGL context available.

    Args:
        product_url: Fully-qualified URL of the product page to test.

    Returns:
        JSON string with ``{"success": true, "data": {"tests_passed": N,
        "tests_failed": N, "details": [...]}}`` or an error envelope.
    """
    try:
        result = await playwright_client.test_3d_viewer(product_url)
        # Remove raw screenshot bytes from the serialised result to stay within
        # CHARACTER_LIMIT; callers that need the image should use playwright_screenshot.
        result.pop("screenshot", None)
        return _ok(result)
    except Exception as exc:
        logger.error("playwright_test_3d_viewer failed", exc_info=exc)
        return _err("playwright_test_3d_viewer", exc)


@mcp.tool(
    name="playwright_test_wordpress_page",
    annotations={
        "title": "Playwright — Test WordPress Page",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def playwright_test_wordpress_page(page_url: str) -> str:
    """Run the 3-step WordPress page test suite.

    Checks: page loads → no JS errors → Elementor content present.

    Args:
        page_url: Fully-qualified URL of the WordPress page to test.

    Returns:
        JSON string with ``{"success": true, "data": {"tests_passed": N,
        "tests_failed": N, "details": [...]}}`` or an error envelope.
    """
    try:
        result = await playwright_client.test_wordpress_page(page_url)
        return _ok(result)
    except Exception as exc:
        logger.error("playwright_test_wordpress_page failed", exc_info=exc)
        return _err("playwright_test_wordpress_page", exc)


# ---------------------------------------------------------------------------
# Serena tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="serena_analyze_file",
    annotations={
        "title": "Serena — Analyze File",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def serena_analyze_file(file_path: str) -> str:
    """Analyze a single source file with Serena.

    Requires the Serena MCP sidecar to be running on localhost:3002.

    Args:
        file_path: Absolute or project-relative path to the file.

    Returns:
        JSON string with analysis results (issues, symbols, metrics) or an
        error envelope.
    """
    try:
        result = await serena_client.analyze_file(file_path)
        return _ok(result)
    except Exception as exc:
        logger.error("serena_analyze_file failed", exc_info=exc)
        return _err("serena_analyze_file", exc)


@mcp.tool(
    name="serena_find_issues",
    annotations={
        "title": "Serena — Find Issues in Code",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def serena_find_issues(
    code: str,
    language: str = "python",
) -> str:
    """Find bugs and quality issues in an inline code snippet.

    Args:
        code: Source code to analyze.
        language: Programming language (default ``"python"``).

    Returns:
        JSON string with ``{"success": true, "data": [issue, ...]}`` or an
        error envelope.
    """
    try:
        result = await serena_client.find_issues(code, language)
        return _ok(result)
    except Exception as exc:
        logger.error("serena_find_issues failed", exc_info=exc)
        return _err("serena_find_issues", exc)


@mcp.tool(
    name="serena_validate_security",
    annotations={
        "title": "Serena — Security Scan",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def serena_validate_security(file_path: str) -> str:
    """Run Serena's security scanner against a single file.

    Detects common vulnerabilities such as injection risks, insecure crypto,
    hardcoded secrets, and OWASP Top-10 patterns.

    Args:
        file_path: Absolute or project-relative path to the file.

    Returns:
        JSON string with security scan results or an error envelope.
    """
    try:
        result = await serena_client.validate_security(file_path)
        return _ok(result)
    except Exception as exc:
        logger.error("serena_validate_security failed", exc_info=exc)
        return _err("serena_validate_security", exc)


@mcp.tool(
    name="serena_full_project_audit",
    annotations={
        "title": "Serena — Full Project Audit",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def serena_full_project_audit(project_root: str) -> str:
    """Run a full Serena audit across all Python files in a project directory.

    Skips ``__pycache__``, ``.venv``, ``node_modules``, and ``.git``.
    Returns per-severity counts (critical / high / medium / low) plus a
    per-file breakdown.

    Args:
        project_root: Absolute path to the project root directory.

    Returns:
        JSON string with ``{"success": true, "data": {"files_analyzed": N,
        "total_issues": N, "critical": N, "high": N, "medium": N, "low": N,
        "files": [...]}}`` or an error envelope.
    """
    try:
        result = await serena_client.full_project_audit(project_root)
        return _ok(result)
    except Exception as exc:
        logger.error("serena_full_project_audit failed", exc_info=exc)
        return _err("serena_full_project_audit", exc)


@mcp.tool(
    name="serena_check_code_style",
    annotations={
        "title": "Serena — Check Code Style",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def serena_check_code_style(
    code: str,
    style_guide: str = "pep8",
) -> str:
    """Check inline code against a style guide using Serena.

    Args:
        code: Source code to check.
        style_guide: Style guide to enforce — ``"pep8"`` (default), ``"google"``,
            etc.

    Returns:
        JSON string with ``{"success": true, "data": [violation, ...]}`` or an
        error envelope.
    """
    try:
        result = await serena_client.check_code_style(code, style_guide)
        return _ok(result)
    except Exception as exc:
        logger.error("serena_check_code_style failed", exc_info=exc)
        return _err("serena_check_code_style", exc)
