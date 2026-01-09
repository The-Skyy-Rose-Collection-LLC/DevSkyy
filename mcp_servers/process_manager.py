"""
MCP Process Manager
===================

Manages MCP server process lifecycles with health monitoring and auto-restart.

Features:
- Start/stop/restart individual servers
- Health monitoring with automatic recovery
- Dependency-aware startup ordering
- Graceful shutdown with timeout
- Process supervision and restart policies

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

import httpx
from pydantic import BaseModel, Field

from errors.production_errors import MCPServerError

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class ProcessStatus(str, Enum):
    """MCP server process status."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
    RESTARTING = "restarting"


class RestartPolicy(str, Enum):
    """Process restart behavior on failure."""

    NEVER = "never"
    ON_FAILURE = "on_failure"
    ALWAYS = "always"


# =============================================================================
# Models
# =============================================================================


@dataclass
class MCPServerProcess:
    """Tracks a running MCP server process."""

    server_id: str
    process: subprocess.Popen | None = None
    status: ProcessStatus = ProcessStatus.STOPPED
    pid: int | None = None
    started_at: datetime | None = None
    restart_count: int = 0
    last_health_check: datetime | None = None
    health_consecutive_failures: int = 0


class MCPServerDefinition(BaseModel):
    """Configuration for an MCP server process."""

    model_config = {"extra": "forbid"}

    # Identity
    server_id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(default="", description="Server description")

    # Process configuration
    entrypoint: str = Field(..., description="Path to server script")
    runtime: str = Field(default="python3.11", description="Runtime command")
    args: list[str] = Field(default_factory=list, description="Additional arguments")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    cwd: str | None = Field(default=None, description="Working directory")

    # Health & Lifecycle
    health_endpoint: str = Field(default="/health", description="Health check endpoint")
    port: int | None = Field(default=None, description="Server port")
    health_check_interval: int = Field(default=30, description="Health check interval (seconds)")
    health_check_timeout: int = Field(default=5, description="Health check timeout (seconds)")
    startup_timeout: int = Field(default=30, description="Startup timeout (seconds)")
    shutdown_timeout: int = Field(default=10, description="Graceful shutdown timeout")

    # Restart policy
    restart_policy: RestartPolicy = Field(default=RestartPolicy.ON_FAILURE)
    max_restarts: int = Field(default=3, description="Max restart attempts")
    restart_delay: int = Field(default=5, description="Delay between restarts")

    # Metadata
    capabilities: list[str] = Field(default_factory=list, description="Server capabilities")
    tool_count: int = Field(default=0, description="Number of tools provided")
    depends_on: list[str] = Field(default_factory=list, description="Server dependencies")
    version: str = Field(default="1.0.0")
    enabled: bool = Field(default=True)


# =============================================================================
# MCP Process Manager
# =============================================================================


class MCPProcessManager:
    """
    Manages MCP server process lifecycles.

    Usage:
        manager = MCPProcessManager()
        manager.register_server(MCPServerDefinition(
            server_id="devskyy-main",
            name="DevSkyy Main MCP",
            entrypoint="/path/to/devskyy_mcp.py",
            port=8001,
        ))
        await manager.start_server("devskyy-main")
        await manager.stop_all()
    """

    _instance: MCPProcessManager | None = None

    def __init__(self, config_path: str | None = None) -> None:
        self._servers: dict[str, MCPServerDefinition] = {}
        self._processes: dict[str, MCPServerProcess] = {}
        self._health_tasks: dict[str, asyncio.Task] = {}
        self._shutdown_event = asyncio.Event()

        if config_path:
            self._load_config(config_path)

    @classmethod
    def get_instance(cls) -> MCPProcessManager:
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # -------------------------------------------------------------------------
    # Registration
    # -------------------------------------------------------------------------

    def register_server(self, definition: MCPServerDefinition) -> None:
        """Register an MCP server definition."""
        self._servers[definition.server_id] = definition
        self._processes[definition.server_id] = MCPServerProcess(server_id=definition.server_id)
        logger.info(f"Registered MCP server: {definition.name} ({definition.server_id})")

    def unregister_server(self, server_id: str) -> None:
        """Unregister an MCP server (must be stopped first)."""
        if self.get_status(server_id) == ProcessStatus.RUNNING:
            raise RuntimeError(f"Cannot unregister running server: {server_id}")
        self._servers.pop(server_id, None)
        self._processes.pop(server_id, None)

    def list_servers(self) -> list[MCPServerDefinition]:
        """List all registered servers."""
        return list(self._servers.values())

    def get_server(self, server_id: str) -> MCPServerDefinition | None:
        """Get server definition by ID."""
        return self._servers.get(server_id)

    # -------------------------------------------------------------------------
    # Lifecycle Management
    # -------------------------------------------------------------------------

    async def start_server(self, server_id: str) -> bool:
        """
        Start an MCP server process.

        Returns:
            True if started successfully
        """
        if server_id not in self._servers:
            raise ValueError(f"Unknown server: {server_id}")

        definition = self._servers[server_id]
        process_info = self._processes[server_id]

        if process_info.status == ProcessStatus.RUNNING:
            logger.warning(f"Server already running: {server_id}")
            return True

        # Check dependencies
        for dep_id in definition.depends_on:
            if self.get_status(dep_id) != ProcessStatus.RUNNING:
                logger.info(f"Starting dependency {dep_id} for {server_id}")
                await self.start_server(dep_id)

        process_info.status = ProcessStatus.STARTING

        try:
            # Build command
            cmd = [definition.runtime, definition.entrypoint] + definition.args

            # Prepare environment
            env = {**os.environ, **definition.env}

            # Start process
            process = subprocess.Popen(
                cmd,
                env=env,
                cwd=definition.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )

            process_info.process = process
            process_info.pid = process.pid
            process_info.started_at = datetime.now(UTC)

            # Wait for startup
            if definition.port:
                startup_success = await self._wait_for_startup(
                    server_id, definition.startup_timeout
                )
                if not startup_success:
                    await self._handle_startup_failure(server_id)
                    return False

            process_info.status = ProcessStatus.RUNNING

            # Start health monitoring
            if definition.port and definition.health_check_interval > 0:
                self._start_health_monitor(server_id)

            logger.info(f"Started MCP server: {definition.name} (PID: {process.pid})")
            return True

        except Exception as e:
            process_info.status = ProcessStatus.FAILED
            logger.error(f"Failed to start server {server_id}: {e}")
            raise MCPServerError(server_id, f"Startup failed: {e}", cause=e)

    async def stop_server(self, server_id: str, force: bool = False) -> bool:
        """Stop an MCP server process."""
        if server_id not in self._processes:
            return True

        process_info = self._processes[server_id]
        definition = self._servers.get(server_id)

        if process_info.status == ProcessStatus.STOPPED:
            return True

        # Stop health monitoring
        self._stop_health_monitor(server_id)

        process_info.status = ProcessStatus.STOPPING

        if process_info.process:
            try:
                if force:
                    process_info.process.kill()
                else:
                    # Graceful shutdown
                    process_info.process.terminate()

                    # Wait for graceful shutdown
                    timeout = definition.shutdown_timeout if definition else 10
                    try:
                        await asyncio.wait_for(
                            asyncio.to_thread(process_info.process.wait), timeout=timeout
                        )
                    except TimeoutError:
                        logger.warning(f"Graceful shutdown timeout for {server_id}, forcing...")
                        process_info.process.kill()
                        process_info.process.wait()

                logger.info(f"Stopped MCP server: {server_id}")

            except Exception as e:
                logger.error(f"Error stopping server {server_id}: {e}")

        process_info.status = ProcessStatus.STOPPED
        process_info.process = None
        process_info.pid = None

        return True

    async def restart_server(self, server_id: str) -> bool:
        """Restart an MCP server."""
        process_info = self._processes.get(server_id)
        if process_info:
            process_info.status = ProcessStatus.RESTARTING

        await self.stop_server(server_id)

        # Wait before restart
        definition = self._servers.get(server_id)
        delay = definition.restart_delay if definition else 5
        await asyncio.sleep(delay)

        return await self.start_server(server_id)

    async def start_all(self) -> dict[str, bool]:
        """Start all enabled servers (respecting dependencies)."""
        results = {}
        started = set()

        for server_id, definition in self._servers.items():
            if definition.enabled and server_id not in started:
                results[server_id] = await self._start_with_deps(server_id, started)

        return results

    async def stop_all(self) -> dict[str, bool]:
        """Stop all running servers (reverse dependency order)."""
        results = {}

        for server_id in reversed(list(self._processes.keys())):
            if self.get_status(server_id) == ProcessStatus.RUNNING:
                results[server_id] = await self.stop_server(server_id)

        return results

    # -------------------------------------------------------------------------
    # Status & Health
    # -------------------------------------------------------------------------

    def get_status(self, server_id: str) -> ProcessStatus:
        """Get process status for a server."""
        if server_id in self._processes:
            return self._processes[server_id].status
        return ProcessStatus.STOPPED

    def get_all_status(self) -> dict[str, ProcessStatus]:
        """Get status for all servers."""
        return {sid: p.status for sid, p in self._processes.items()}

    async def health_check(self, server_id: str) -> bool:
        """Perform health check on a server."""
        definition = self._servers.get(server_id)
        if not definition or not definition.port:
            return False

        try:
            async with httpx.AsyncClient(timeout=definition.health_check_timeout) as client:
                url = f"http://localhost:{definition.port}{definition.health_endpoint}"
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False

    async def health_check_all(self) -> dict[str, bool]:
        """Health check all running servers."""
        results = {}
        for server_id in self._servers:
            if self.get_status(server_id) == ProcessStatus.RUNNING:
                results[server_id] = await self.health_check(server_id)
        return results

    # -------------------------------------------------------------------------
    # Private Methods
    # -------------------------------------------------------------------------

    async def _wait_for_startup(self, server_id: str, timeout: int) -> bool:
        """Wait for server to become healthy."""
        start = datetime.now(UTC)
        while (datetime.now(UTC) - start).total_seconds() < timeout:
            if await self.health_check(server_id):
                return True
            await asyncio.sleep(1)
        return False

    async def _handle_startup_failure(self, server_id: str) -> None:
        """Handle startup failure."""
        process_info = self._processes[server_id]
        process_info.status = ProcessStatus.FAILED

        if process_info.process:
            process_info.process.terminate()
            process_info.process = None

    def _start_health_monitor(self, server_id: str) -> None:
        """Start background health monitoring for a server."""
        if server_id in self._health_tasks:
            return

        async def monitor():
            definition = self._servers[server_id]
            process_info = self._processes[server_id]

            while not self._shutdown_event.is_set():
                await asyncio.sleep(definition.health_check_interval)

                if process_info.status != ProcessStatus.RUNNING:
                    break

                healthy = await self.health_check(server_id)
                process_info.last_health_check = datetime.now(UTC)

                if healthy:
                    process_info.health_consecutive_failures = 0
                else:
                    process_info.health_consecutive_failures += 1
                    logger.warning(
                        f"Health check failed for {server_id} "
                        f"({process_info.health_consecutive_failures} consecutive)"
                    )

                    # Auto-restart if policy allows
                    if (
                        definition.restart_policy != RestartPolicy.NEVER
                        and process_info.health_consecutive_failures >= 3
                        and process_info.restart_count < definition.max_restarts
                    ):
                        logger.info(f"Auto-restarting unhealthy server: {server_id}")
                        process_info.restart_count += 1
                        await self.restart_server(server_id)

        self._health_tasks[server_id] = asyncio.create_task(monitor())

    def _stop_health_monitor(self, server_id: str) -> None:
        """Stop health monitoring for a server."""
        if server_id in self._health_tasks:
            self._health_tasks[server_id].cancel()
            del self._health_tasks[server_id]

    async def _start_with_deps(self, server_id: str, started: set[str]) -> bool:
        """Start server with dependencies."""
        if server_id in started:
            return True

        definition = self._servers.get(server_id)
        if not definition:
            return False

        # Start dependencies first
        for dep_id in definition.depends_on:
            if dep_id not in started:
                await self._start_with_deps(dep_id, started)

        # Start this server
        result = await self.start_server(server_id)
        if result:
            started.add(server_id)
        return result

    def _load_config(self, config_path: str) -> None:
        """Load server definitions from config file."""
        import json

        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Config file not found: {config_path}")
            return

        with open(path) as f:
            config = json.load(f)

        for server_config in config.get("servers", []):
            definition = MCPServerDefinition(**server_config)
            self.register_server(definition)


__all__ = [
    "ProcessStatus",
    "RestartPolicy",
    "MCPServerProcess",
    "MCPServerDefinition",
    "MCPProcessManager",
]
