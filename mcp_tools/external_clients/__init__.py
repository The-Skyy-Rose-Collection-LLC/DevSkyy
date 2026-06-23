"""
External MCP client adapters for DevSkyy.

Provides thin async wrappers around three external MCP surfaces:
- Context7: documentation and library lookup (api.context7.io)
- Playwright: browser automation via local MCP sidecar (localhost:3001)
- Serena: code analysis via local MCP sidecar (localhost:3002)

All network I/O is deferred to method calls — no connections are opened at
import time, so this package loads cleanly on slim containers where the
external servers may be absent.
"""

from mcp_tools.external_clients.context7 import Context7Client, context7_client
from mcp_tools.external_clients.playwright import PlaywrightMCPClient, playwright_client
from mcp_tools.external_clients.serena import SerenaClient, serena_client
from mcp_tools.external_clients.server_manager import (
    MCPServerConfig,
    MCPServerManager,
    MCPServerStatus,
    MCPToolResult,
    mcp_manager,
)

__all__ = [
    "Context7Client",
    "context7_client",
    "PlaywrightMCPClient",
    "playwright_client",
    "SerenaClient",
    "serena_client",
    "MCPServerConfig",
    "MCPServerManager",
    "MCPServerStatus",
    "MCPToolResult",
    "mcp_manager",
]
