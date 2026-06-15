"""Mount the DevSkyy MCP server as an authenticated HTTP endpoint on the FastAPI app.

The same FastMCP instance that the stdio entrypoint (``devskyy_mcp.py``) serves is
exposed here over streamable HTTP at ``/mcp`` so the Next.js dashboard and the
WordPress site can consume the tools over the network — not just local stdio clients.

Auth: a shared Bearer service token (``MCP_SERVICE_TOKEN``). When the token is set
(every non-dev environment MUST set it), the mounted app rejects any request without
``Authorization: Bearer <token>``. When unset (local dev), enforcement is skipped and
a warning is logged — so a deployed, reachable ``/mcp`` is never silently open.

Mutation gating stays in the tool layer (each mutating tool requires its own confirm
flag); this middleware is the coarse network gate in front of all 38 tools.
"""

from __future__ import annotations

import os

from starlette.types import ASGIApp, Receive, Scope, Send
from utils.logging_utils import get_logger

from mcp_tools import mcp  # FastMCP instance; importing registers all tool handlers

logger = get_logger(__name__)

MCP_MOUNT_PATH = "/mcp"
_TOKEN_ENV = "MCP_SERVICE_TOKEN"
_UNAUTHORIZED_BODY = (
    b'{"error":"unauthorized","detail":"MCP requires Authorization: Bearer <MCP_SERVICE_TOKEN>"}'
)


class BearerAuthMiddleware:
    """ASGI middleware enforcing a shared Bearer token on the mounted MCP app.

    Enforced only when ``MCP_SERVICE_TOKEN`` is configured. An unset token in a
    non-development environment is logged as a warning at construction time so a
    reachable-but-open ``/mcp`` cannot ship unnoticed.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        token = os.getenv(_TOKEN_ENV, "").strip()
        if not token and os.getenv("ENVIRONMENT", "development") != "development":
            logger.warning(
                "mcp_endpoint_unauthenticated",
                detail=f"{_TOKEN_ENV} is not set in a non-dev environment; /mcp is OPEN.",
            )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        token = os.getenv(_TOKEN_ENV, "").strip()
        if token:
            headers = dict(scope.get("headers") or [])
            provided = headers.get(b"authorization", b"").decode()
            if provided != f"Bearer {token}":
                await self._reject(send)
                return

        await self.app(scope, receive, send)

    @staticmethod
    async def _reject(send: Send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"www-authenticate", b"Bearer"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": _UNAUTHORIZED_BODY})


def build_mcp_app():
    """Return the auth-wrapped MCP streamable-HTTP ASGI app to mount on FastAPI.

    Calling ``streamable_http_app()`` here also constructs ``mcp.session_manager``,
    which :func:`mcp_session_manager` then exposes to the FastAPI lifespan.
    """
    # Default streamable_http_path is "/mcp"; mounting that app at MCP_MOUNT_PATH
    # ("/mcp") would double the path to "/mcp/mcp". Serve at the app root so the
    # mount path IS the full public endpoint (/mcp).
    mcp.settings.streamable_http_path = "/"
    return BearerAuthMiddleware(mcp.streamable_http_app())


def mcp_session_manager():
    """The MCP session manager. Must be run inside the FastAPI lifespan.

    Only valid after :func:`build_mcp_app` (i.e. ``streamable_http_app()``) has run.
    """
    return mcp.session_manager
