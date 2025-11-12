#!/usr/bin/env python3
"""
MCP Gateway Service
Routes requests to multiple MCP servers (DevSkyy, HuggingFace, custom servers)
Provides unified HTTP interface for MCP protocol

Author: DevSkyy Platform Team
Version: 1.0.0
Python: 3.11+
"""

import asyncio
import json
import logging
import os
import subprocess
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import httpx


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
    "huggingface": {
        "type": "http",
        "url": "https://huggingface.co/mcp",
        "headers": {
            "Authorization": f"Bearer {os.getenv('HUGGING_FACE_TOKEN', '')}"
        } if os.getenv("HUGGING_FACE_TOKEN") else {},
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
    id: Optional[str | int] = Field(default=None, description="Request ID")


class MCPResponse(BaseModel):
    """MCP protocol response"""

    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    result: Optional[Any] = Field(default=None, description="Method result")
    error: Optional[dict[str, Any]] = Field(default=None, description="Error object")
    id: Optional[str | int] = Field(default=None, description="Request ID")


# =============================================================================
# MCP SERVER CLIENTS
# =============================================================================


class StdioMCPClient:
    """Client for stdio-based MCP servers"""

    def __init__(self, server_config: dict[str, Any]):
        """
        Initialize a stdio-based MCP client using the provided server configuration.
        
        Parameters:
            server_config (dict[str, Any]): Configuration dictionary with the following keys:
                - "command": required; the executable (string or list) to run for the MCP subprocess.
                - "args": optional; list of command-line arguments to pass to the subprocess (defaults to empty list).
                - "env": optional; mapping of environment variables to set for the subprocess (defaults to empty dict).
        
        This sets the client's command, args, env, and initializes the subprocess handle to None.
        """
        self.command = server_config["command"]
        self.args = server_config.get("args", [])
        self.env = server_config.get("env", {})
        self.process: Optional[subprocess.Popen] = None

    async def start(self):
        """
        Start and attach a subprocess for the stdio MCP server.
        
        Starts the configured command as a subprocess with stdin/stdout/stderr pipes, merging the instance's environment overrides into the current environment, and stores the resulting subprocess object on `self.process`.
        """
        env = os.environ.copy()
        env.update(self.env)

        self.process = subprocess.Popen(
            [self.command] + self.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
        )

        logger.info(f"Started stdio MCP server: {self.command}")

    async def call(self, request: MCPRequest) -> MCPResponse:
        """
        Send an MCPRequest to the managed stdio subprocess and parse its JSON-RPC response.
        
        Parameters:
            request (MCPRequest): The JSON-RPC request to send; the subprocess will be started if it is not already running.
        
        Returns:
            MCPResponse: The parsed JSON-RPC response from the subprocess.
        """
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
        """
        Terminate the managed subprocess and wait up to 5 seconds for it to exit.
        
        If a subprocess is running, this sends a termination signal and waits up to 5 seconds for the process to exit. Does nothing if no subprocess is present.
        
        Raises:
            subprocess.TimeoutExpired: If the process does not exit within 5 seconds.
        """
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            logger.info("Closed stdio MCP server")


class HttpMCPClient:
    """Client for HTTP-based MCP servers"""

    def __init__(self, server_config: dict[str, Any]):
        """
        Create an HTTP MCP client configured for a target server.
        
        Parameters:
            server_config (dict[str, Any]): Configuration for the HTTP server. Must contain the key `"url"` with the target endpoint. May include `"headers"` to send with each request.
        
        """
        self.url = server_config["url"]
        self.headers = server_config.get("headers", {})
        self.client = httpx.AsyncClient(timeout=30.0)

    async def call(self, request: MCPRequest) -> MCPResponse:
        """
        Forward an MCP JSON-RPC request to the configured HTTP MCP server.
        
        If the HTTP request succeeds, returns the server's response parsed as an MCPResponse. If an HTTP transport or protocol error occurs, returns an MCPResponse with `error` set to `{"code": -32000, "message": "<error message>"}` and the original request `id`.
        
        @returns MCPResponse: The parsed MCPResponse from the server, or an error MCPResponse on HTTP failure.
        """
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
        """
        Initialize the gateway and prepare an empty registry for MCP server clients.
        
        The registry maps server names to their client instances (either StdioMCPClient or HttpMCPClient).
        """
        self.clients: dict[str, StdioMCPClient | HttpMCPClient] = {}

    async def initialize(self):
        """
        Initialize and register MCP server clients from the MCP_SERVERS configuration.
        
        Creates and stores a client instance for each configured server: for servers of type "stdio" it starts a StdioMCPClient (starting its subprocess), and for type "http" it creates an HttpMCPClient. Successful clients are added to the gateway's client registry and failures are logged; the method handles exceptions internally and does not raise.
        """
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

    async def route_request(
        self, server_name: str, request: MCPRequest
    ) -> MCPResponse:
        """
        Forward an MCPRequest to the MCP server identified by server_name and return its MCPResponse.
        
        If the named server is not registered, returns an MCPResponse with error code -32601.
        If forwarding the request raises an exception, returns an MCPResponse with error code -32603 and the original request id.
        
        Parameters:
            server_name (str): Name of the configured MCP server to route the request to.
            request (MCPRequest): JSON-RPC 2.0 formatted request to forward.
        
        Returns:
            MCPResponse: The MCP server's response, or an error response with `id` set to the original request id.
        """
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
                error={"code": -32603, "message": f"Internal error: {str(e)}"},
                id=request.id,
            )

    async def shutdown(self):
        """
        Close and cleanly shut down all registered MCP clients.
        
        Iterates over each client in the gateway's registry and awaits its `close()` coroutine. Exceptions raised while closing an individual client are caught and logged, and do not prevent attempts to shut down remaining clients.
        """
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
    """
    Initialize the gateway and prepare configured MCP servers when the FastAPI application starts.
    
    Logs startup banners, triggers gateway initialization, and records the listening port and active server list.
    """
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
    """
    Perform shutdown tasks for the MCP gateway, closing all managed MCP server clients and logging progress.
    """
    logger.info("Shutting down MCP Gateway...")
    await gateway.shutdown()
    logger.info("✅ Gateway shutdown complete")


@app.get("/")
async def root():
    """
    Provide gateway status including the gateway name, version, list of active servers, and overall status.
    
    Returns:
        status (dict): Dictionary with keys:
            - name (str): Human-readable gateway name.
            - version (str): Gateway version string.
            - servers (list[str]): Names of initialized/registered MCP servers.
            - status (str): Overall gateway status (e.g., "active").
    """
    return {
        "name": "DevSkyy MCP Gateway",
        "version": "1.0.0",
        "servers": list(gateway.clients.keys()),
        "status": "active",
    }


@app.get("/health")
async def health():
    """
    Report gateway health and per-server activity status.
    
    Returns:
        dict: A dictionary with keys:
            - "status": the overall gateway status (the string "healthy").
            - "servers": a mapping of server names to their activity status (each value is the string "active").
    """
    return {
        "status": "healthy",
        "servers": {
            name: "active" for name in gateway.clients.keys()
        },
    }


@app.post("/mcp/{server_name}")
async def mcp_request(server_name: str, request: MCPRequest):
    """
    Forward an MCP JSON-RPC request to the named MCP server.
    
    Parameters:
        server_name (str): Identifier of the target MCP server (e.g., "devskyy", "huggingface").
        request (MCPRequest): JSON-RPC 2.0 request to send to the server.
    
    Returns:
        MCPResponse: JSON-RPC 2.0 response from the server, containing either a `result` or an `error`.
    """
    logger.info(f"Routing request to {server_name}: {request.method}")

    response = await gateway.route_request(server_name, request)
    return response


@app.get("/servers")
async def list_servers():
    """
    Return a mapping of available MCP servers and their reported status.
    
    Returns:
        dict: A dictionary with a "servers" key mapping server names to objects containing:
            - "type" (str): the configured server type (e.g., "stdio" or "http").
            - "status" (str): the server status, currently "active".
    """
    return {
        "servers": {
            name: {
                "type": MCP_SERVERS[name]["type"],
                "status": "active",
            }
            for name in gateway.clients.keys()
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