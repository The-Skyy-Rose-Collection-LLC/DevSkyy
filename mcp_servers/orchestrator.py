"""
MCP Orchestrator
================

Unified facade for managing MCP servers, tools, and catalogs.

Features:
- Process lifecycle management (local servers)
- HTTP client management (remote servers)
- Unified tool registry and catalog generation
- Health monitoring and auto-recovery
- Multi-format tool export

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

import httpx

from .catalog_generator import (
    ExportFormat,
    ToolCatalogGenerator,
    ToolCategory,
    ToolMetadata,
    ToolSeverity,
    UnifiedToolRegistry,
)
from .process_manager import (
    MCPProcessManager,
    MCPServerDefinition,
    ProcessStatus,
)

logger = logging.getLogger(__name__)


# =============================================================================
# HTTP Client Manager
# =============================================================================


class HTTPClientManager:
    """
    Manages HTTP connections to remote MCP servers.

    Usage:
        manager = HTTPClientManager()
        manager.register_server("https://api.example.com/mcp")
        tools = await manager.list_tools(server_url)
    """

    def __init__(self, timeout: int = 30) -> None:
        self._clients: dict[str, httpx.AsyncClient] = {}
        self._timeout = timeout

    def register_server(self, server_url: str, api_key: str | None = None) -> None:
        """Register a remote MCP server."""
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        client = httpx.AsyncClient(
            base_url=server_url,
            headers=headers,
            timeout=self._timeout,
        )
        self._clients[server_url] = client
        logger.info(f"Registered remote MCP server: {server_url}")

    def unregister_server(self, server_url: str) -> None:
        """Unregister a remote MCP server."""
        if server_url in self._clients:
            asyncio.create_task(self._clients[server_url].aclose())
            del self._clients[server_url]

    async def list_tools(self, server_url: str) -> list[dict[str, Any]]:
        """List tools from a remote MCP server."""
        if server_url not in self._clients:
            raise ValueError(f"Server not registered: {server_url}")

        client = self._clients[server_url]
        response = await client.get("/mcp/tools")
        response.raise_for_status()
        return response.json()

    async def call_tool(
        self,
        server_url: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Call a tool on a remote MCP server."""
        if server_url not in self._clients:
            raise ValueError(f"Server not registered: {server_url}")

        client = self._clients[server_url]
        response = await client.post(
            "/mcp/tools/call",
            json={"name": tool_name, "arguments": arguments},
        )
        response.raise_for_status()
        return response.json()

    async def health_check(self, server_url: str) -> bool:
        """Check health of a remote MCP server."""
        if server_url not in self._clients:
            return False

        try:
            client = self._clients[server_url]
            response = await client.get("/health")
            return response.status_code == 200
        except Exception:
            return False

    async def close_all(self) -> None:
        """Close all HTTP clients."""
        for client in self._clients.values():
            await client.aclose()
        self._clients.clear()


# =============================================================================
# MCP Orchestrator
# =============================================================================


class MCPOrchestrator:
    """
    Unified orchestrator for all MCP operations.

    Combines:
    - Process management for local MCP servers
    - HTTP client management for remote servers
    - Unified tool registry and catalog generation
    - Health monitoring across all servers

    Usage:
        orchestrator = MCPOrchestrator()

        # Register local server
        orchestrator.register_local_server(MCPServerDefinition(...))
        await orchestrator.start_server("server-id")

        # Register remote server
        orchestrator.register_remote_server("https://api.example.com/mcp")

        # Build unified catalog
        await orchestrator.build_catalog()
        catalog = orchestrator.export_catalog(ExportFormat.OPENAI)
    """

    _instance: MCPOrchestrator | None = None

    def __init__(self, config_path: str | None = None) -> None:
        self.process_manager = MCPProcessManager(config_path)
        self.http_manager = HTTPClientManager()
        self.tool_registry = UnifiedToolRegistry()
        self.catalog_generator = ToolCatalogGenerator(self.tool_registry)

        self._remote_servers: dict[str, str] = {}  # server_id -> url

    @classmethod
    def get_instance(cls) -> MCPOrchestrator:
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # -------------------------------------------------------------------------
    # Server Registration
    # -------------------------------------------------------------------------

    def register_local_server(self, definition: MCPServerDefinition) -> None:
        """Register a local MCP server."""
        self.process_manager.register_server(definition)
        logger.info(f"Registered local server: {definition.name}")

    def register_remote_server(
        self,
        server_id: str,
        server_url: str,
        api_key: str | None = None,
    ) -> None:
        """Register a remote MCP server."""
        self.http_manager.register_server(server_url, api_key)
        self._remote_servers[server_id] = server_url
        logger.info(f"Registered remote server: {server_id} ({server_url})")

    def unregister_server(self, server_id: str) -> None:
        """Unregister a server (local or remote)."""
        # Try local first
        try:
            self.process_manager.unregister_server(server_id)
            logger.info(f"Unregistered local server: {server_id}")
            return
        except Exception:
            pass

        # Try remote
        if server_id in self._remote_servers:
            url = self._remote_servers.pop(server_id)
            self.http_manager.unregister_server(url)
            logger.info(f"Unregistered remote server: {server_id}")

    # -------------------------------------------------------------------------
    # Server Lifecycle (Local Only)
    # -------------------------------------------------------------------------

    async def start_server(self, server_id: str) -> bool:
        """Start a local MCP server."""
        return await self.process_manager.start_server(server_id)

    async def stop_server(self, server_id: str, force: bool = False) -> bool:
        """Stop a local MCP server."""
        return await self.process_manager.stop_server(server_id, force)

    async def restart_server(self, server_id: str) -> bool:
        """Restart a local MCP server."""
        return await self.process_manager.restart_server(server_id)

    async def start_all_local(self) -> dict[str, bool]:
        """Start all enabled local servers."""
        return await self.process_manager.start_all()

    async def stop_all_local(self) -> dict[str, bool]:
        """Stop all running local servers."""
        return await self.process_manager.stop_all()

    # -------------------------------------------------------------------------
    # Health & Status
    # -------------------------------------------------------------------------

    def get_status(self, server_id: str) -> ProcessStatus | str:
        """Get status of a server (local or remote)."""
        # Try local first
        status = self.process_manager.get_status(server_id)
        if status != ProcessStatus.STOPPED:
            return status

        # Check if it's a remote server
        if server_id in self._remote_servers:
            return "remote"

        return ProcessStatus.STOPPED

    def get_all_status(self) -> dict[str, ProcessStatus | str]:
        """Get status of all servers."""
        status = self.process_manager.get_all_status()

        # Add remote servers
        for server_id in self._remote_servers:
            status[server_id] = "remote"

        return status

    async def health_check_all(self) -> dict[str, bool]:
        """Health check all servers (local and remote)."""
        results = {}

        # Local servers
        local_health = await self.process_manager.health_check_all()
        results.update(local_health)

        # Remote servers
        for server_id, url in self._remote_servers.items():
            results[server_id] = await self.http_manager.health_check(url)

        return results

    # -------------------------------------------------------------------------
    # Tool Registry & Catalog
    # -------------------------------------------------------------------------

    async def build_catalog(self, include_local: bool = True, include_remote: bool = True) -> None:
        """Build unified tool catalog from all servers."""
        logger.info("Building unified tool catalog...")

        # Clear existing registry
        for tool_name in list(self.tool_registry._tools.keys()):
            self.tool_registry.unregister_tool(tool_name)

        # Collect from local servers
        if include_local:
            await self._collect_local_tools()

        # Collect from remote servers
        if include_remote:
            await self._collect_remote_tools()

        stats = self.tool_registry.get_statistics()
        logger.info(f"Catalog built: {stats.total_tools} tools from {stats.total_servers} servers")

        if stats.conflicts:
            logger.warning(f"Detected {len(stats.conflicts)} tool conflicts")

    async def _collect_local_tools(self) -> None:
        """Collect tools from local servers."""
        for definition in self.process_manager.list_servers():
            if self.process_manager.get_status(definition.server_id) != ProcessStatus.RUNNING:
                continue

            # Extract tools from capabilities (simplified - real impl would introspect server)
            for capability in definition.capabilities:
                # Create tool metadata from capability
                tool = ToolMetadata(
                    name=f"{definition.server_id}_{capability}",
                    description=f"{capability} capability from {definition.name}",
                    server_id=definition.server_id,
                    category=ToolCategory.SYSTEM,
                    severity=ToolSeverity.MEDIUM,
                    input_schema={"type": "object", "properties": {}},
                    read_only=True,
                )
                self.tool_registry.register_tool(tool)

    async def _collect_remote_tools(self) -> None:
        """Collect tools from remote servers."""
        for server_id, url in self._remote_servers.items():
            try:
                tools_data = await self.http_manager.list_tools(url)

                for tool_data in tools_data:
                    # Parse tool metadata from remote response
                    tool = ToolMetadata(
                        name=tool_data["name"],
                        description=tool_data.get("description", ""),
                        server_id=server_id,
                        category=ToolCategory(tool_data.get("category", ToolCategory.SYSTEM.value)),
                        severity=ToolSeverity(tool_data.get("severity", ToolSeverity.MEDIUM.value)),
                        input_schema=tool_data.get("inputSchema", {}),
                        read_only=tool_data.get("readOnly", False),
                        idempotent=tool_data.get("idempotent", False),
                    )
                    self.tool_registry.register_tool(tool)

            except Exception as e:
                logger.error(f"Failed to collect tools from {server_id}: {e}")

    # -------------------------------------------------------------------------
    # Catalog Export
    # -------------------------------------------------------------------------

    def export_catalog(self, format: ExportFormat) -> Any:
        """Export catalog in specified format."""
        if format == ExportFormat.OPENAI:
            return self.catalog_generator.to_openai_format()
        elif format == ExportFormat.ANTHROPIC:
            return self.catalog_generator.to_anthropic_format()
        elif format == ExportFormat.MCP:
            return self.catalog_generator.to_mcp_format()
        elif format == ExportFormat.JSON:
            return self.catalog_generator.to_json_format()
        elif format == ExportFormat.MARKDOWN:
            return self.catalog_generator.to_markdown_format()
        else:
            raise ValueError(f"Unsupported format: {format}")

    def export_catalog_to_file(self, format: ExportFormat, output_path: str | Path) -> None:
        """Export catalog to file."""
        self.catalog_generator.export_to_file(format, output_path)

    def export_all_formats(self, output_dir: str | Path) -> dict[ExportFormat, Path]:
        """Export catalog to all formats."""
        return self.catalog_generator.export_all_formats(output_dir)

    # -------------------------------------------------------------------------
    # Tool Operations
    # -------------------------------------------------------------------------

    def get_tool(self, tool_name: str) -> ToolMetadata | None:
        """Get tool metadata by name."""
        return self.tool_registry.get_tool(tool_name)

    def get_all_tools(self) -> list[ToolMetadata]:
        """Get all registered tools."""
        return self.tool_registry.get_all_tools()

    def search_tools(self, query: str) -> list[ToolMetadata]:
        """Search tools by name or description."""
        return self.tool_registry.search_tools(query)

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Call a tool (local or remote)."""
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")

        server_id = tool.server_id

        # Check if it's a remote server
        if server_id in self._remote_servers:
            url = self._remote_servers[server_id]
            return await self.http_manager.call_tool(url, tool_name, arguments)

        # For local servers, we'd need to implement direct tool calling
        # This would require MCP protocol implementation
        raise NotImplementedError("Local tool calling not yet implemented")

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    async def shutdown(self) -> None:
        """Shutdown all servers and close connections."""
        logger.info("Shutting down MCP orchestrator...")

        # Stop all local servers
        await self.process_manager.stop_all()

        # Close all HTTP clients
        await self.http_manager.close_all()

        logger.info("MCP orchestrator shutdown complete")


__all__ = [
    "HTTPClientManager",
    "MCPOrchestrator",
]
