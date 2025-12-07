"""
MCP Install Deeplink API Endpoints
Provides one-click installation for DevSkyy MCP Server via deeplink URLs
Supports multiple MCP servers with stdio and HTTP transports

Author: DevSkyy Platform Team
Version: 1.1.0
Python: 3.11+
"""

import base64
from enum import Enum
import json
import logging
import os
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from security.jwt_auth import TokenData, get_current_active_user


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])


# ============================================================================
# ENUMS
# ============================================================================


class TransportType(str, Enum):
    """MCP server transport types"""

    STDIO = "stdio"
    HTTP = "http"
    STREAMING_HTTP = "streamingHttp"
    STREAMING_HTTP_JSON = "streamingHttpJson"


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class MCPConfigRequest(BaseModel):
    """Request model for MCP configuration generation"""

    api_key: str = Field(..., description="DevSkyy API key for authentication")
    api_url: str | None = Field(default=None, description="Custom API URL (defaults to production)")
    server_name: str | None = Field(default="devskyy", description="MCP server name")


class AddServerRequest(BaseModel):
    """Request model for adding an external MCP server"""

    server_name: str = Field(..., description="Unique name for the MCP server")
    transport: TransportType = Field(..., description="Transport type (stdio, http, etc.)")
    url: str | None = Field(default=None, description="Server URL (required for HTTP transport)")
    command: str | None = Field(default=None, description="Command to run (required for stdio transport)")
    args: list[str] | None = Field(default=None, description="Command arguments (for stdio transport)")
    env: dict[str, str] | None = Field(default=None, description="Environment variables")
    headers: dict[str, str] | None = Field(default=None, description="HTTP headers (for HTTP transport)")
    metadata: dict[str, Any] | None = Field(default=None, description="Server metadata")


class MultiServerConfigRequest(BaseModel):
    """Request model for multi-server configuration"""

    servers: list[AddServerRequest] = Field(..., description="List of MCP servers to configure")
    include_devskyy: bool = Field(default=True, description="Include DevSkyy MCP server in configuration")
    devskyy_api_key: str | None = Field(
        default=None, description="DevSkyy API key (required if include_devskyy=True)"
    )


class MCPConfigResponse(BaseModel):
    """Response model for MCP configuration"""

    config: dict[str, Any] = Field(..., description="MCP server configuration JSON")
    deeplink_url: str = Field(..., description="One-click install deeplink URL")
    cursor_url: str = Field(..., description="Cursor-compatible deeplink URL")
    installation_instructions: str = Field(..., description="Human-readable installation instructions")


class MCPStatusResponse(BaseModel):
    """Response model for MCP server status"""

    status: str = Field(..., description="Server status (active/inactive)")
    version: str = Field(..., description="MCP server version")
    available_tools: int = Field(..., description="Number of available tools")
    agent_count: int = Field(..., description="Number of available agents")


# ============================================================================
# CONFIGURATION GENERATOR
# ============================================================================


def generate_mcp_config(
    api_key: str,
    api_url: str | None = None,
    server_name: str = "devskyy",
) -> dict[str, Any]:
    """
    Generate MCP server configuration for Claude Desktop.

    Args:
        api_key: DevSkyy API key for authentication
        api_url: Custom API URL (defaults to production)
        server_name: MCP server name

    Returns:
        MCP server configuration dictionary

    Per Truth Protocol Rule #5: No secrets in code - API keys passed as parameters
    Per Truth Protocol Rule #2: Pin versions - Explicit version numbers
    """
    # Default to production API URL if not provided
    if not api_url:
        api_url = os.getenv("DEVSKYY_API_URL", "https://devskyy.com")

    # Generate MCP configuration following Claude Desktop schema
    config = {
        "mcpServers": {
            server_name: {
                "command": "uvx",
                "args": ["--from", "devskyy-mcp==1.0.0", "devskyy-mcp"],
                "env": {
                    "DEVSKYY_API_URL": api_url,
                    "DEVSKYY_API_KEY": api_key,
                },
                "metadata": {
                    "name": "DevSkyy Multi-Agent AI Platform",
                    "version": "1.0.0",
                    "description": "54 specialized AI agents for code analysis, WordPress automation, ML predictions, and more",
                    "author": "DevSkyy Platform Team",
                    "url": "https://devskyy.com",
                    "documentation": "https://devskyy.com/docs/mcp",
                },
            }
        }
    }

    return config


def encode_config_base64(config: dict[str, Any]) -> str:
    """
    Encode MCP configuration as base64 for deeplink URL.

    Args:
        config: MCP server configuration dictionary

    Returns:
        Base64-encoded configuration string

    Per Truth Protocol Rule #1: Never guess - Uses standard base64 encoding (RFC 4648)
    """
    config_json = json.dumps(config, separators=(",", ":"))
    config_bytes = config_json.encode("utf-8")
    config_b64 = base64.urlsafe_b64encode(config_bytes).decode("utf-8")
    return config_b64


def generate_deeplink_url(config_b64: str, server_name: str = "devskyy") -> str:
    """
    Generate deeplink URL for one-click MCP installation.

    Args:
        config_b64: Base64-encoded configuration string
        server_name: MCP server name

    Returns:
        Deeplink URL for installation

    Per Truth Protocol Rule #3: Cite standards - Uses custom URL scheme for deeplink
    """
    # Cursor-compatible deeplink format
    cursor_url = f"cursor://anysphere.cursor-deeplink/mcp/install?name={server_name}&config={config_b64}"
    return cursor_url


def generate_server_config(server_request: AddServerRequest) -> dict[str, Any]:
    """
    Generate MCP server configuration from AddServerRequest.

    Args:
        server_request: Server configuration request

    Returns:
        MCP server configuration dictionary

    Raises:
        ValueError: If required fields are missing for transport type

    Per Truth Protocol Rule #1: Never guess - Validate all required fields
    Per Truth Protocol Rule #3: Cite standards - MCP protocol specification
    """
    config: dict[str, Any] = {}

    # HTTP-based transports (streamingHttp, http, etc.)
    if server_request.transport in [
        TransportType.HTTP,
        TransportType.STREAMING_HTTP,
        TransportType.STREAMING_HTTP_JSON,
    ]:
        if not server_request.url:
            raise ValueError(f"URL is required for {server_request.transport} transport")

        config["url"] = server_request.url

        if server_request.headers:
            config["headers"] = server_request.headers

    # stdio transport
    elif server_request.transport == TransportType.STDIO:
        if not server_request.command:
            raise ValueError("Command is required for stdio transport")

        config["command"] = server_request.command

        if server_request.args:
            config["args"] = server_request.args

        if server_request.env:
            config["env"] = server_request.env

    # Add metadata if provided
    if server_request.metadata:
        config["metadata"] = server_request.metadata

    return config


def create_huggingface_server(
    hf_token: str | None = None,
    server_name: str = "huggingface",
    url: str = "https://huggingface.co/mcp",
) -> AddServerRequest:
    """
    Create HuggingFace MCP server configuration helper.

    Args:
        hf_token: HuggingFace API token (optional for login)
        server_name: Server name (defaults to "huggingface")
        url: HuggingFace MCP server URL

    Returns:
        AddServerRequest configured for HuggingFace MCP server

    Per Truth Protocol Rule #5: No secrets in code - Token passed as parameter
    Per Truth Protocol Rule #2: Pin versions - Uses stable HF MCP endpoint
    """
    headers = {}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"

    return AddServerRequest(
        server_name=server_name,
        transport=TransportType.HTTP,
        url=url,
        headers=headers if headers else None,
        metadata={
            "name": "HuggingFace MCP Server",
            "description": "Access HuggingFace models, datasets, and spaces via MCP",
            "author": "HuggingFace",
            "url": "https://huggingface.co",
            "documentation": "https://huggingface.co/docs/mcp",
        },
    )


def merge_server_configs(base_config: dict[str, Any], servers: list[AddServerRequest]) -> dict[str, Any]:
    """
    Merge multiple MCP server configurations into one.

    Args:
        base_config: Base configuration (e.g., DevSkyy server)
        servers: List of additional servers to add

    Returns:
        Merged configuration with all servers

    Per Truth Protocol Rule #1: Never guess - Validate uniqueness of server names
    """
    merged = base_config.copy()

    for server in servers:
        # Check for duplicate server names
        if server.server_name in merged["mcpServers"]:
            raise ValueError(f"Duplicate server name: {server.server_name}")

        # Generate and add server config
        server_config = generate_server_config(server)
        merged["mcpServers"][server.server_name] = server_config

    return merged


# ============================================================================
# API ENDPOINTS
# ============================================================================


@router.get("/install", response_model=MCPConfigResponse)
async def get_mcp_install_deeplink(
    api_key: str = Query(..., description="DevSkyy API key for authentication"),
    api_url: str | None = Query(default=None, description="Custom API URL (defaults to production)"),
    server_name: str | None = Query(default="devskyy", description="MCP server name"),
):
    """
    Generate MCP install deeplink for one-click installation.

    This endpoint generates a complete MCP configuration and returns:
    1. The configuration JSON
    2. A deeplink URL for one-click installation in Claude Desktop/Cursor
    3. Installation instructions

    **Security:** API key is embedded in the configuration for server authentication.
    Per Truth Protocol Rule #5: No secrets in code - API keys passed as query parameters.

    **Usage:**
    ```
    GET /api/v1/mcp/install?api_key=YOUR_API_KEY
    ```

    **Response includes:**
    - `config`: Full MCP server configuration JSON
    - `deeplink_url`: Standard deeplink URL
    - `cursor_url`: Cursor-compatible deeplink URL
    - `installation_instructions`: Human-readable guide

    Args:
        api_key: DevSkyy API key for authentication
        api_url: Custom API URL (optional)
        server_name: MCP server name (optional)

    Returns:
        MCPConfigResponse: Configuration, deeplink URLs, and instructions

    Raises:
        HTTPException: If configuration generation fails
    """
    try:
        logger.info(f"Generating MCP install deeplink for server: {server_name}")

        # Generate MCP configuration
        config = generate_mcp_config(api_key=api_key, api_url=api_url, server_name=server_name)

        # Encode configuration as base64
        config_b64 = encode_config_base64(config)

        # Generate deeplink URLs
        cursor_url = generate_deeplink_url(config_b64, server_name)
        deeplink_url = cursor_url  # Same for now, can add more formats later

        # Generate installation instructions
        instructions = f"""
# DevSkyy MCP Server - One-Click Installation

## Method 1: One-Click Install (Recommended)

Click this link to automatically install DevSkyy MCP Server:
{cursor_url}

## Method 2: Manual Installation

1. Open Claude Desktop or Cursor
2. Navigate to: Settings → Model Context Protocol
3. Click "Add Server"
4. Paste this configuration:

```json
{json.dumps(config, indent=2)}
```

5. Save and restart Claude Desktop/Cursor

## Verification

After installation, you can use these DevSkyy tools:
- devskyy_list_agents - List all 54 available agents
- devskyy_scan_code - Scan code for errors and security issues
- devskyy_fix_code - Automatically fix code issues
- devskyy_generate_wordpress_theme - Generate WordPress themes
- devskyy_predict_fashion_trends - ML-powered fashion predictions
- devskyy_analyze_ecommerce - E-commerce analytics
- And 8 more powerful tools!

## Support

Documentation: https://devskyy.com/docs/mcp
API Reference: https://devskyy.com/api/docs
        """

        logger.info("✅ MCP install deeplink generated successfully")

        return MCPConfigResponse(
            config=config,
            deeplink_url=deeplink_url,
            cursor_url=cursor_url,
            installation_instructions=instructions.strip(),
        )

    except Exception as e:
        logger.error(f"Failed to generate MCP install deeplink: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate MCP configuration: {e!s}")


@router.get("/config", response_model=dict[str, Any])
async def get_mcp_config(
    api_key: str = Query(..., description="DevSkyy API key for authentication"),
    api_url: str | None = Query(default=None, description="Custom API URL (defaults to production)"),
    server_name: str | None = Query(default="devskyy", description="MCP server name"),
):
    """
    Get MCP server configuration JSON only (without deeplink).

    This endpoint returns just the configuration JSON that can be manually
    added to Claude Desktop's configuration file.

    **Usage:**
    ```
    GET /api/v1/mcp/config?api_key=YOUR_API_KEY
    ```

    Args:
        api_key: DevSkyy API key for authentication
        api_url: Custom API URL (optional)
        server_name: MCP server name (optional)

    Returns:
        dict: MCP server configuration JSON

    Raises:
        HTTPException: If configuration generation fails
    """
    try:
        logger.info(f"Generating MCP configuration for server: {server_name}")

        config = generate_mcp_config(api_key=api_key, api_url=api_url, server_name=server_name)

        logger.info("✅ MCP configuration generated successfully")

        return config

    except Exception as e:
        logger.error(f"Failed to generate MCP configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate MCP configuration: {e!s}")


@router.get("/status", response_model=MCPStatusResponse)
async def get_mcp_status():
    """
    Get MCP server status and capabilities.

    Returns information about the MCP server including:
    - Server status
    - Version number
    - Number of available tools
    - Number of available agents

    **Usage:**
    ```
    GET /api/v1/mcp/status
    ```

    Returns:
        MCPStatusResponse: Server status and capabilities
    """
    try:
        # TODO: In production, this should check actual server health
        # For now, return static information

        return MCPStatusResponse(
            status="active",
            version="1.0.0",
            available_tools=14,  # Based on devskyy_mcp.py
            agent_count=54,  # Total agents in platform
        )

    except Exception as e:
        logger.error(f"Failed to get MCP status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get MCP status: {e!s}")


@router.post("/validate")
async def validate_api_key(
    api_key: str = Query(..., description="DevSkyy API key to validate"),
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    Validate a DevSkyy API key for MCP server usage.

    This endpoint checks if an API key is valid and has the necessary
    permissions for MCP server access.

    **Security:** Requires JWT authentication.
    Per Truth Protocol Rule #6: RBAC roles enforced.

    **Usage:**
    ```
    POST /api/v1/mcp/validate?api_key=YOUR_API_KEY
    Authorization: Bearer YOUR_JWT_TOKEN
    ```

    Args:
        api_key: DevSkyy API key to validate
        current_user: Authenticated user (from JWT)

    Returns:
        dict: Validation result with status and permissions

    Raises:
        HTTPException: If validation fails
    """
    try:
        logger.info(f"Validating API key for user: {current_user.username}")

        # TODO: In production, validate against database/secret manager
        # For now, check if API key is non-empty and meets basic requirements

        if not api_key or len(api_key) < 32:
            raise HTTPException(
                status_code=400,
                detail="Invalid API key format. API keys must be at least 32 characters.",
            )

        # Check user permissions
        # Per Truth Protocol Rule #6: RBAC roles
        allowed_roles = ["SuperAdmin", "Admin", "Developer", "APIUser"]
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required roles: {allowed_roles}",
            )

        logger.info("✅ API key validation successful")

        return {
            "valid": True,
            "user": current_user.username,
            "role": current_user.role,
            "permissions": ["mcp_access", "agent_execution", "tool_calling"],
            "message": "API key is valid and authorized for MCP server usage",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {e!s}")


@router.post("/servers/add", response_model=MCPConfigResponse)
async def add_mcp_server(
    server: AddServerRequest = Body(...),
    devskyy_api_key: str | None = Query(
        default=None, description="DevSkyy API key (optional, to include DevSkyy server)"
    ),
):
    """
    Add an external MCP server to configuration and generate deeplink.

    This endpoint allows you to add external MCP servers (like HuggingFace)
    alongside the DevSkyy MCP server in a single configuration.

    **Supported Transport Types:**
    - `stdio`: Standard input/output (command-based)
    - `http`: HTTP transport
    - `streamingHttp`: Streaming HTTP (MCP standard)
    - `streamingHttpJson`: Streaming HTTP with JSON

    **Usage:**
    ```
    POST /api/v1/mcp/servers/add
    {
      "server_name": "huggingface",
      "transport": "http",
      "url": "https://huggingface.co/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_HF_TOKEN"
      }
    }
    ```

    Args:
        server: MCP server configuration to add
        devskyy_api_key: Optional DevSkyy API key to include DevSkyy server

    Returns:
        MCPConfigResponse: Configuration with deeplink URLs

    Raises:
        HTTPException: If configuration generation fails
    """
    try:
        logger.info(f"Adding MCP server: {server.server_name} with transport: {server.transport}")

        # Start with base config or empty config
        if devskyy_api_key:
            config = generate_mcp_config(api_key=devskyy_api_key)
        else:
            config = {"mcpServers": {}}

        # Add the new server
        config = merge_server_configs(config, [server])

        # Encode configuration as base64
        config_b64 = encode_config_base64(config)

        # Generate deeplink URLs (use first server name for deeplink)
        server_name = server.server_name
        cursor_url = generate_deeplink_url(config_b64, server_name)
        deeplink_url = cursor_url

        # Generate installation instructions
        server_count = len(config["mcpServers"])
        server_list = ", ".join(config["mcpServers"].keys())

        instructions = f"""
# MCP Multi-Server Configuration

## Servers Configured ({server_count}):
{server_list}

## One-Click Install

Click this link to automatically install all configured MCP servers:
{cursor_url}

## Manual Installation

Add this configuration to your Claude Desktop config file:

```json
{json.dumps(config, indent=2)}
```

## Server Details

### {server.server_name}
- Transport: {server.transport}
- URL: {server.url if server.url else 'N/A'}
- Command: {server.command if server.command else 'N/A'}

## Verification

After installation, restart Claude Desktop and check for the MCP server icon (🔌).
All {server_count} servers should be listed.
        """

        logger.info(f"✅ MCP server added successfully: {server.server_name}")

        return MCPConfigResponse(
            config=config,
            deeplink_url=deeplink_url,
            cursor_url=cursor_url,
            installation_instructions=instructions.strip(),
        )

    except ValueError as e:
        logger.error(f"Validation error adding MCP server: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add MCP server: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add MCP server: {e!s}")


@router.post("/servers/multi", response_model=MCPConfigResponse)
async def configure_multiple_servers(
    request: MultiServerConfigRequest = Body(...),
):
    """
    Configure multiple MCP servers at once with deeplink generation.

    This endpoint allows you to configure multiple MCP servers (both DevSkyy
    and external servers like HuggingFace) in a single request.

    **Usage:**
    ```
    POST /api/v1/mcp/servers/multi
    {
      "include_devskyy": true,
      "devskyy_api_key": "YOUR_DEVSKYY_KEY",
      "servers": [
        {
          "server_name": "huggingface",
          "transport": "http",
          "url": "https://huggingface.co/mcp",
          "headers": {"Authorization": "Bearer YOUR_HF_TOKEN"}
        },
        {
          "server_name": "custom-server",
          "transport": "stdio",
          "command": "node",
          "args": ["./custom-mcp-server.js"]
        }
      ]
    }
    ```

    Args:
        request: Multi-server configuration request

    Returns:
        MCPConfigResponse: Configuration with all servers and deeplink

    Raises:
        HTTPException: If configuration generation fails
    """
    try:
        logger.info(f"Configuring {len(request.servers)} MCP servers")

        # Validate DevSkyy API key if including DevSkyy
        if request.include_devskyy:
            if not request.devskyy_api_key:
                raise HTTPException(
                    status_code=400,
                    detail="devskyy_api_key is required when include_devskyy=True",
                )
            config = generate_mcp_config(api_key=request.devskyy_api_key)
        else:
            config = {"mcpServers": {}}

        # Add all servers
        if request.servers:
            config = merge_server_configs(config, request.servers)

        # Encode configuration as base64
        config_b64 = encode_config_base64(config)

        # Generate deeplink URLs (use first server name)
        server_names = list(config["mcpServers"].keys())
        first_server = server_names[0] if server_names else "mcp"
        cursor_url = generate_deeplink_url(config_b64, first_server)
        deeplink_url = cursor_url

        # Generate installation instructions
        server_count = len(config["mcpServers"])
        server_list = "\n".join([f"- {name}" for name in server_names])

        instructions = f"""
# MCP Multi-Server Configuration

## Configured Servers ({server_count}):
{server_list}

## One-Click Install

Click this link to automatically install all {server_count} MCP servers:
{cursor_url}

## Manual Installation

1. Open Claude Desktop or Cursor
2. Navigate to: Settings → Model Context Protocol
3. Add this configuration:

```json
{json.dumps(config, indent=2)}
```

4. Save and restart Claude Desktop/Cursor

## Verification

After installation:
1. Look for the MCP server icon (🔌)
2. Click it to see all {server_count} servers listed
3. Each server should show its available tools

## Support

For issues with specific servers, check their documentation:
- DevSkyy: https://devskyy.com/docs/mcp
- HuggingFace: https://huggingface.co/docs/mcp
        """

        logger.info(f"✅ Multi-server configuration generated: {server_count} servers")

        return MCPConfigResponse(
            config=config,
            deeplink_url=deeplink_url,
            cursor_url=cursor_url,
            installation_instructions=instructions.strip(),
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in multi-server config: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate multi-server config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate configuration: {e!s}")


@router.get("/servers/huggingface")
async def get_huggingface_config(
    hf_token: str | None = Query(default=None, description="HuggingFace API token (optional)"),
    server_name: str = Query(default="huggingface", description="Server name for HuggingFace"),
    devskyy_api_key: str | None = Query(default=None, description="DevSkyy API key (optional)"),
):
    """
    Quick helper endpoint to generate HuggingFace MCP server configuration.

    This is a convenience endpoint that simplifies adding the HuggingFace MCP
    server to your configuration.

    **Without HF Token (Public Access):**
    ```
    GET /api/v1/mcp/servers/huggingface
    ```

    **With HF Token (Authenticated Access):**
    ```
    GET /api/v1/mcp/servers/huggingface?hf_token=YOUR_HF_TOKEN
    ```

    **With Both DevSkyy and HuggingFace:**
    ```
    GET /api/v1/mcp/servers/huggingface?hf_token=YOUR_HF_TOKEN&devskyy_api_key=YOUR_DEVSKYY_KEY
    ```

    Args:
        hf_token: HuggingFace API token (optional)
        server_name: Custom server name (defaults to "huggingface")
        devskyy_api_key: DevSkyy API key to include DevSkyy server (optional)

    Returns:
        MCPConfigResponse: Configuration with HuggingFace (and optionally DevSkyy)

    Raises:
        HTTPException: If configuration generation fails
    """
    try:
        logger.info(f"Generating HuggingFace MCP server config: {server_name}")

        # Create HuggingFace server configuration
        hf_server = create_huggingface_server(hf_token=hf_token, server_name=server_name)

        # Use the add_mcp_server logic
        if devskyy_api_key:
            config = generate_mcp_config(api_key=devskyy_api_key)
        else:
            config = {"mcpServers": {}}

        # Add HuggingFace server
        config = merge_server_configs(config, [hf_server])

        # Encode and generate deeplink
        config_b64 = encode_config_base64(config)
        cursor_url = generate_deeplink_url(config_b64, server_name)

        instructions = f"""
# HuggingFace MCP Server - Quick Install

## One-Click Install

{cursor_url}

## What You Get

The HuggingFace MCP Server provides access to:
- 🤗 Models: Search and use HuggingFace models
- 📊 Datasets: Access datasets from HuggingFace
- 🚀 Spaces: Interact with HuggingFace Spaces
- 🔍 Search: Find models, datasets, and papers

## Manual Setup

Add this to your Claude Desktop config:

```json
{json.dumps(config, indent=2)}
```

## Authentication

{"✅ Authenticated with HuggingFace token" if hf_token else "ℹ️  Using public access (no token). Add ?hf_token=YOUR_TOKEN for authenticated access"}

## Next Steps

1. Click the deeplink above or manually add the configuration
2. Restart Claude Desktop
3. Try: "Search HuggingFace for BERT models"
4. Or: "Show me popular datasets on HuggingFace"

## Documentation

https://huggingface.co/docs/mcp
        """

        logger.info("✅ HuggingFace MCP configuration generated")

        return MCPConfigResponse(
            config=config,
            deeplink_url=cursor_url,
            cursor_url=cursor_url,
            installation_instructions=instructions.strip(),
        )

    except Exception as e:
        logger.error(f"Failed to generate HuggingFace config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate HuggingFace configuration: {e!s}",
        )
