"""Standalone slim MCP HTTP service.

Serves ONLY the DevSkyy MCP server over streamable HTTP at ``/mcp`` — without the
heavy ``main_enterprise`` router monolith (no torch / ML stack). Reuses the
shared mount in :mod:`mcp_tools.http_mount`. Tool modules whose optional
dependencies are absent on this slim image skip registration via the resilient
loader in :mod:`mcp_tools.tools`.

What works standalone here: ``tools/list`` and self-contained tools (e.g. the
WooCommerce tools, which talk to skyyrose.co's WC REST directly via httpx).
Tools that proxy to the full FastAPI backend return a runtime error when invoked
(no backend is deployed alongside this slim service) — they still list.

Run: ``uvicorn mcp_service:app --host 0.0.0.0 --port 8000``
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from utils.logging_utils import get_logger

from mcp_tools.http_mount import MCP_MOUNT_PATH, build_mcp_app, mcp_session_manager, tool_count

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Run the MCP streamable-HTTP session manager for the app lifetime."""
    async with mcp_session_manager().run():
        logger.info("mcp_service_ready", mount=MCP_MOUNT_PATH)
        yield


app = FastAPI(
    title="DevSkyy MCP Service",
    description="Standalone streamable-HTTP MCP endpoint (slim, no ML stack).",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> JSONResponse:
    """Liveness probe for the Fly health check.

    ``tool_count`` is computed at runtime (never hand-typed) — see
    :func:`mcp_tools.http_mount.tool_count`.
    """
    return JSONResponse({"status": "ok", "service": "mcp", "tool_count": await tool_count()})


@app.get("/ready")
async def ready() -> JSONResponse:
    """Readiness probe."""
    return JSONResponse({"status": "ready"})


# Mount the auth-wrapped MCP streamable-HTTP app. Done at import (before the
# lifespan starts) because build_mcp_app() also constructs mcp.session_manager,
# which the lifespan above runs. The mount path IS the full public endpoint.
app.mount(MCP_MOUNT_PATH, build_mcp_app())
