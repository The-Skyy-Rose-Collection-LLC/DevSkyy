#!/usr/bin/env python3
"""
MCP Gateway Service
Routes requests to multiple MCP servers (DevSkyy, HuggingFace, custom servers)
Provides unified HTTP interface for MCP protocol

Author: DevSkyy Platform Team
Version: 1.0.0
Python: 3.11+
"""

import json
import logging
import os
import subprocess
from typing import Any

from fastapi import FastAPI
import httpx
from pydantic import BaseModel, Field


# =============================================================================
# CONFIGURATION
# =============================================================================

GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "3000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# MCP Server configurations
MCP_SERVERS = {
    "devskyy": {
        "type": "stdio",
        "command": "python",
        "args": ["devskyy_mcp.py"],
        "env": {
            "DEVSKYY_API_KEY": os.getenv("DEVSKYY_API_KEY", ""),
            "DEVSKYY_API_URL": os.getenv("DEVSKYY_API_URL", "http://localhost:8000"),
        },
    },
    "neon": {
        "type": "http",
        "url": os.getenv("NEON_MCP_URL", "https://mcp.neon.tech/mcp"),
        "headers": (
            {
                "Authorization": f"Bearer {os.getenv('NEON_API_KEY', '')}",
                "X-Neon-Project-Id": os.getenv("NEON_PROJECT_ID", ""),
            }
            if os.getenv("NEON_API_KEY")
            else {}
        ),
    },
    "huggingface": {
        "type": "http",
        "url": "https://huggingface.co/mcp",
        "headers": (
            {"Authorization": f"Bearer {os.getenv('HUGGING_FACE_TOKEN', '')}"}
            if os.getenv("HUGGING_FACE_TOKEN")
            else {}
        ),
    },
}

# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="DevSkyy MCP Gateway",
    description="Unified gateway for multiple MCP servers",
    version="1.0.0",
)

# =============================================================================
# MODELS
# =============================================================================


class MCPRequest(BaseModel):
    """MCP protocol request"""

    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    method: str = Field(..., description="MCP method to call")
    params: dict[str, Any] = Field(default_factory=dict, description="Method parameters")
    id: str | int | None = Field(default=None, description="Request ID")


class MCPResponse(BaseModel):
    """MCP protocol response"""

    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    result: Any | None = Field(default=None, description="Method result")
    error: dict[str, Any] | None = Field(default=None, description="Error object")
    id: str | int | None = Field(default=None, description="Request ID")


# =============================================================================
# MCP SERVER CLIENTS
# =============================================================================


class StdioMCPClient:
    """Client for stdio-based MCP servers"""

    def __init__(self, server_config: dict[str, Any]):
        self.command = server_config["command"]
        self.args = server_config.get("args", [])
        self.env = server_config.get("env", {})
        self.process: subprocess.Popen | None = None

    async def start(self):
        """Start the stdio process"""
        env = os.environ.copy()
        env.update(self.env)

        self.process = subprocess.Popen(
            [self.command, *self.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
        )

        logger.info(f"Started stdio MCP server: {self.command}")

    async def call(self, request: MCPRequest) -> MCPResponse:
        """Call MCP method via stdio"""
        if not self.process:
            await self.start()

        # Send request
        request_json = request.model_dump_json() + "\n"
        self.process.stdin.write(request_json)
        self.process.stdin.flush()

        # Read response
        response_line = self.process.stdout.readline()
        response_data = json.loads(response_line)

        return MCPResponse(**response_data)

    async def close(self):
        """Close the stdio process"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            logger.info("Closed stdio MCP server")


class HttpMCPClient:
    """Client for HTTP-based MCP servers"""

    def __init__(self, server_config: dict[str, Any]):
        self.url = server_config["url"]
        self.headers = server_config.get("headers", {})
        self.client = httpx.AsyncClient(timeout=30.0)

    async def call(self, request: MCPRequest) -> MCPResponse:
        """Call MCP method via HTTP"""
        try:
            response = await self.client.post(
                self.url,
                json=request.model_dump(),
                headers=self.headers,
            )
            response.raise_for_status()
            return MCPResponse(**response.json())
        except httpx.HTTPError as e:
            logger.error(f"HTTP MCP request failed: {e}")
            return MCPResponse(
                error={"code": -32000, "message": str(e)},
                id=request.id,
            )

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# =============================================================================
# GATEWAY MANAGER
# =============================================================================


class MCPGateway:
    """Manages multiple MCP server clients"""

    def __init__(self):
        self.clients: dict[str, StdioMCPClient | HttpMCPClient] = {}

    async def initialize(self):
        """Initialize all MCP clients"""
        for server_name, config in MCP_SERVERS.items():
            try:
                if config["type"] == "stdio":
                    client = StdioMCPClient(config)
                    await client.start()
                elif config["type"] == "http":
                    client = HttpMCPClient(config)
                else:
                    logger.warning(f"Unknown server type: {config['type']}")
                    continue

                self.clients[server_name] = client
                logger.info(f"✅ Initialized MCP server: {server_name}")

            except Exception as e:
                logger.error(f"❌ Failed to initialize {server_name}: {e}")

    async def route_request(self, server_name: str, request: MCPRequest) -> MCPResponse:
        """Route request to specific MCP server"""
        client = self.clients.get(server_name)

        if not client:
            return MCPResponse(
                error={
                    "code": -32601,
                    "message": f"MCP server not found: {server_name}",
                },
                id=request.id,
            )

        try:
            return await client.call(request)
        except Exception as e:
            logger.error(f"MCP request failed: {e}")
            return MCPResponse(
                error={"code": -32603, "message": f"Internal error: {e!s}"},
                id=request.id,
            )

    async def shutdown(self):
        """Shutdown all MCP clients"""
        for server_name, client in self.clients.items():
            try:
                await client.close()
                logger.info(f"Closed MCP server: {server_name}")
            except Exception as e:
                logger.error(f"Error closing {server_name}: {e}")


# =============================================================================
# GATEWAY INSTANCE
# =============================================================================

gateway = MCPGateway()


# =============================================================================
# API ENDPOINTS
# =============================================================================


@app.on_event("startup")
async def startup():
    """Initialize gateway on startup"""
    logger.info("=" * 70)
    logger.info("DevSkyy MCP Gateway v1.0.0")
    logger.info("=" * 70)
    logger.info("Initializing MCP servers...")

    await gateway.initialize()

    logger.info("=" * 70)
    logger.info(f"✅ Gateway ready on port {GATEWAY_PORT}")
    logger.info(f"✅ Active servers: {list(gateway.clients.keys())}")
    logger.info("=" * 70)


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    logger.info("Shutting down MCP Gateway...")
    await gateway.shutdown()
    logger.info("✅ Gateway shutdown complete")


@app.get("/")
async def root():
    """Gateway status endpoint"""
    return {
        "name": "DevSkyy MCP Gateway",
        "version": "1.0.0",
        "servers": list(gateway.clients.keys()),
        "status": "active",
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "servers": dict.fromkeys(gateway.clients.keys(), "active"),
    }


@app.post("/mcp/{server_name}")
async def mcp_request(server_name: str, request: MCPRequest):
    """
    Route MCP request to specific server

    Args:
        server_name: Name of MCP server (devskyy, huggingface, etc.)
        request: MCP JSON-RPC request

    Returns:
        MCP JSON-RPC response
    """
    logger.info(f"Routing request to {server_name}: {request.method}")

    response = await gateway.route_request(server_name, request)
    return response


@app.get("/servers")
async def list_servers():
    """List all available MCP servers"""
    return {
        "servers": {
            name: {
                "type": MCP_SERVERS[name]["type"],
                "status": "active",
            }
            for name in gateway.clients
        }
    }


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting MCP Gateway...")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=GATEWAY_PORT,
        log_level=LOG_LEVEL.lower(),
    )
