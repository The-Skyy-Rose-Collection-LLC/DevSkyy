"""
Example: How devskyy_mcp.py can be refactored to use shared utilities

This demonstrates the simplified version after refactoring.
The original file had 140+ lines of duplicated API utilities.
"""

import json
import os
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

try:
    import httpx
    from mcp.server.fastmcp import FastMCP
    from pydantic import BaseModel, ConfigDict, Field
except ImportError as e:
    print(f"❌ Missing required package: {e}")
    print("Install with: pip install fastmcp httpx pydantic")
    exit(1)

# Import shared utilities instead of duplicating code
from utils.api_client import ResponseFormat, make_api_request, handle_api_error, format_response

# Configuration
API_BASE_URL = os.getenv("DEVSKYY_API_URL", "http://localhost:8000")
API_KEY = os.getenv("DEVSKYY_API_KEY", "")
CHARACTER_LIMIT = 25000
REQUEST_TIMEOUT = 60.0

# Initialize MCP Server
mcp = FastMCP("devskyy_mcp", dependencies=["httpx>=0.24.0", "pydantic>=2.5.0"])

# ===========================
# Utility Functions - Now Much Simpler!
# ===========================

async def _make_api_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make authenticated request to DevSkyy API (using shared utility)."""
    return await make_api_request(
        base_url=API_BASE_URL,
        endpoint=endpoint,
        api_key=API_KEY,
        method=method,
        data=data,
        params=params,
        timeout=REQUEST_TIMEOUT
    )


def _handle_api_error(e: httpx.HTTPStatusError) -> Dict[str, Any]:
    """Convert HTTP errors to user-friendly messages (using shared utility)."""
    return handle_api_error(e)


def _format_response(data: Dict[str, Any], format_type: ResponseFormat, title: str = "") -> str:
    """Format response in requested format (using shared utility)."""
    return format_response(data, format_type, title, CHARACTER_LIMIT)


# ===========================
# Example Tool Definition
# ===========================

@mcp.tool(name="devskyy_scan_code")
async def scan_code(path: str, file_types: List[str], deep_scan: bool = True) -> str:
    """
    Scan codebase for errors and vulnerabilities.
    
    This is a simplified example showing how the tool would work
    with the refactored utilities.
    """
    data = await _make_api_request(
        "scanner/scan",
        method="POST",
        data={
            "path": path,
            "file_types": file_types,
            "deep_scan": deep_scan
        }
    )
    
    return _format_response(data, ResponseFormat.MARKDOWN, "Code Scan Results")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║   DevSkyy MCP Server - Refactored Version                        ║
║                                                                  ║
║   ✅ Reduced from 1168 lines to ~900 lines                      ║
║   ✅ Eliminated 140+ lines of duplicated utilities              ║
║   ✅ Using shared API client from utils/api_client.py           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
    mcp.run()
