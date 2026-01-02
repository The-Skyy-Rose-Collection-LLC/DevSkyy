# mcp/server_manager.py
"""
MCP Server Manager for DevSkyy Enterprise Platform.

This module manages connections to MCP servers including:
- Context7: Documentation and library lookup
- Playwright: Browser automation and testing
- Serena: Code analysis and validation
- Custom DevSkyy servers

Design: Unified interface for all MCP server interactions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel, Field

from errors.production_errors import MCPServerError

logger = logging.getLogger(__name__)


class MCPServerStatus(str, Enum):
    """MCP server connection status."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""

    name: str
    url: str
    capabilities: list[str] = field(default_factory=list)
    auth_token: str | None = None
    timeout_seconds: float = 30.0
    max_retries: int = 3
    health_endpoint: str = "/health"


class MCPToolResult(BaseModel):
    """Result from an MCP tool call."""

    success: bool = Field(..., description="Whether the call succeeded")
    data: dict[str, Any] = Field(default_factory=dict, description="Result data")
    error: str | None = Field(None, description="Error message if failed")
    server_name: str = Field(..., description="Name of the server that handled the call")


class MCPServerManager:
    """
    Manage MCP server connections for DevSkyy agents.

    Integrates with:
    - Context7: Documentation and library lookup
    - Playwright: Browser automation and testing
    - Serena: Code analysis and validation
    - DevSkyy custom servers: RAG, agents, WooCommerce

    Usage:
        manager = MCPServerManager()
        await manager.connect("context7")
        result = await manager.call_tool("context7", "resolve-library-id", {...})
    """

    # Default server configurations
    DEFAULT_SERVERS: dict[str, MCPServerConfig] = {
        "context7": MCPServerConfig(
            name="Context7",
            url="https://api.context7.io/mcp",
            capabilities=["documentation", "library_search", "code_examples"],
        ),
        "playwright": MCPServerConfig(
            name="Playwright MCP",
            url="http://localhost:3001/mcp",
            capabilities=["browser_automation", "screenshot", "testing"],
        ),
        "serena": MCPServerConfig(
            name="Serena",
            url="http://localhost:3002/mcp",
            capabilities=["code_analysis", "validation", "refactoring"],
        ),
        "devskyy-rag": MCPServerConfig(
            name="DevSkyy RAG",
            url="http://localhost:3003/mcp",
            capabilities=["rag_query", "rag_ingest", "semantic_search"],
        ),
        "devskyy-agents": MCPServerConfig(
            name="DevSkyy Agents",
            url="http://localhost:3004/mcp",
            capabilities=["agent_execution", "workflow", "round_table"],
        ),
        "woocommerce": MCPServerConfig(
            name="WooCommerce MCP",
            url="http://localhost:3005/mcp",
            capabilities=["products", "orders", "inventory", "sync"],
        ),
        "huggingface": MCPServerConfig(
            name="Hugging Face",
            url="https://huggingface.co/mcp",
            capabilities=["model_search", "dataset_search", "inference"],
        ),
    }

    def __init__(self) -> None:
        """Initialize the MCP server manager."""
        self._clients: dict[str, httpx.AsyncClient] = {}
        self._status: dict[str, MCPServerStatus] = {}
        self._configs: dict[str, MCPServerConfig] = dict(self.DEFAULT_SERVERS)

    def register_server(self, server_id: str, config: MCPServerConfig) -> None:
        """Register a new MCP server configuration."""
        self._configs[server_id] = config
        self._status[server_id] = MCPServerStatus.DISCONNECTED

    async def connect(self, server_id: str) -> bool:
        """
        Connect to an MCP server.

        Args:
            server_id: Identifier for the server to connect to

        Returns:
            True if connection successful, False otherwise

        Raises:
            ValueError: If server_id is not registered
        """
        if server_id not in self._configs:
            raise ValueError(f"Unknown MCP server: {server_id}")

        config = self._configs[server_id]
        self._status[server_id] = MCPServerStatus.CONNECTING

        try:
            headers = {"Content-Type": "application/json"}
            if config.auth_token:
                headers["Authorization"] = f"Bearer {config.auth_token}"

            client = httpx.AsyncClient(
                base_url=config.url,
                timeout=config.timeout_seconds,
                headers=headers,
            )

            # Test connection with health check
            try:
                response = await client.get(config.health_endpoint)
                if response.status_code == 200:
                    self._clients[server_id] = client
                    self._status[server_id] = MCPServerStatus.CONNECTED
                    logger.info(f"Connected to MCP server: {config.name}")
                    return True
                else:
                    await client.aclose()
                    self._status[server_id] = MCPServerStatus.ERROR
                    logger.warning(
                        f"MCP server {config.name} health check failed: {response.status_code}"
                    )
                    return False
            except httpx.RequestError:
                # Server might not have health endpoint, try to proceed
                self._clients[server_id] = client
                self._status[server_id] = MCPServerStatus.CONNECTED
                logger.info(f"Connected to MCP server: {config.name} (no health check)")
                return True

        except Exception as e:
            self._status[server_id] = MCPServerStatus.ERROR
            logger.error(f"Failed to connect to MCP server {config.name}: {e}")
            return False

    async def disconnect(self, server_id: str) -> None:
        """Disconnect from an MCP server."""
        if server_id in self._clients:
            await self._clients[server_id].aclose()
            del self._clients[server_id]
        self._status[server_id] = MCPServerStatus.DISCONNECTED

    async def disconnect_all(self) -> None:
        """Disconnect from all connected servers."""
        for server_id in list(self._clients.keys()):
            await self.disconnect(server_id)

    def get_status(self, server_id: str) -> MCPServerStatus:
        """Get connection status for a server."""
        return self._status.get(server_id, MCPServerStatus.DISCONNECTED)

    def is_connected(self, server_id: str) -> bool:
        """Check if a server is connected."""
        return self.get_status(server_id) == MCPServerStatus.CONNECTED

    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        auto_connect: bool = True,
    ) -> MCPToolResult:
        """
        Call a tool on an MCP server.

        Args:
            server_id: Server to call
            tool_name: Name of the tool
            arguments: Tool arguments
            auto_connect: Whether to auto-connect if disconnected

        Returns:
            MCPToolResult with the response

        Raises:
            MCPServerError: If the call fails
        """
        # Auto-connect if needed
        if auto_connect and not self.is_connected(server_id):
            if not await self.connect(server_id):
                raise MCPServerError(
                    server_id,
                    f"Failed to connect to server: {server_id}",
                )

        if server_id not in self._clients:
            raise MCPServerError(
                server_id,
                f"Not connected to server: {server_id}",
            )

        client = self._clients[server_id]
        config = self._configs[server_id]

        try:
            response = await client.post(
                "/tools/call",
                json={
                    "tool": tool_name,
                    "arguments": arguments,
                },
            )

            if response.status_code == 200:
                data = response.json()
                return MCPToolResult(
                    success=True,
                    data=data,
                    server_name=config.name,
                )
            else:
                error_msg = f"Tool call failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg = error_data["error"]
                except Exception:
                    error_msg = response.text or error_msg

                return MCPToolResult(
                    success=False,
                    error=error_msg,
                    server_name=config.name,
                )

        except httpx.RequestError as e:
            raise MCPServerError(
                server_id,
                f"Request to {config.name} failed: {str(e)}",
                cause=e,
            )

    async def list_tools(self, server_id: str) -> list[dict[str, Any]]:
        """List available tools on an MCP server."""
        if not self.is_connected(server_id):
            if not await self.connect(server_id):
                return []

        client = self._clients[server_id]

        try:
            response = await client.get("/tools/list")
            if response.status_code == 200:
                return response.json().get("tools", [])
            return []
        except Exception as e:
            logger.error(f"Failed to list tools for {server_id}: {e}")
            return []

    def get_server_capabilities(self, server_id: str) -> list[str]:
        """Get capabilities for a server."""
        if server_id in self._configs:
            return self._configs[server_id].capabilities
        return []

    async def __aenter__(self) -> MCPServerManager:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.disconnect_all()


# Singleton instance
mcp_manager = MCPServerManager()
