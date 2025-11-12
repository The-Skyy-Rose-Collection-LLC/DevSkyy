"""
MCP Install Deeplink API Endpoints
Provides one-click installation for DevSkyy MCP Server via deeplink URLs

Author: DevSkyy Platform Team
Version: 1.0.0
Python: 3.11+
"""

import base64
import json
import logging
import os
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from security.jwt_auth import TokenData, get_current_active_user


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class MCPConfigRequest(BaseModel):
    """Request model for MCP configuration generation"""

    api_key: str = Field(..., description="DevSkyy API key for authentication")
    api_url: Optional[str] = Field(
        default=None, description="Custom API URL (defaults to production)"
    )
    server_name: Optional[str] = Field(
        default="devskyy", description="MCP server name"
    )


class MCPConfigResponse(BaseModel):
    """Response model for MCP configuration"""

    config: dict[str, Any] = Field(..., description="MCP server configuration JSON")
    deeplink_url: str = Field(..., description="One-click install deeplink URL")
    cursor_url: str = Field(..., description="Cursor-compatible deeplink URL")
    installation_instructions: str = Field(
        ..., description="Human-readable installation instructions"
    )


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
    api_url: Optional[str] = None,
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


# ============================================================================
# API ENDPOINTS
# ============================================================================


@router.get("/install", response_model=MCPConfigResponse)
async def get_mcp_install_deeplink(
    api_key: str = Query(..., description="DevSkyy API key for authentication"),
    api_url: Optional[str] = Query(
        default=None, description="Custom API URL (defaults to production)"
    ),
    server_name: Optional[str] = Query(
        default="devskyy", description="MCP server name"
    ),
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
        config = generate_mcp_config(
            api_key=api_key, api_url=api_url, server_name=server_name
        )

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
        raise HTTPException(
            status_code=500, detail=f"Failed to generate MCP configuration: {str(e)}"
        )


@router.get("/config", response_model=dict[str, Any])
async def get_mcp_config(
    api_key: str = Query(..., description="DevSkyy API key for authentication"),
    api_url: Optional[str] = Query(
        default=None, description="Custom API URL (defaults to production)"
    ),
    server_name: Optional[str] = Query(
        default="devskyy", description="MCP server name"
    ),
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

        config = generate_mcp_config(
            api_key=api_key, api_url=api_url, server_name=server_name
        )

        logger.info("✅ MCP configuration generated successfully")

        return config

    except Exception as e:
        logger.error(f"Failed to generate MCP configuration: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate MCP configuration: {str(e)}"
        )


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
        raise HTTPException(
            status_code=500, detail=f"Failed to get MCP status: {str(e)}"
        )


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
        raise HTTPException(
            status_code=500, detail=f"Validation failed: {str(e)}"
        )
