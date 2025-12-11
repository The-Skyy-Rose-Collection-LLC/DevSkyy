"""
Shared API Client Utilities for DevSkyy Platform

This module consolidates API-related functionality:
- HTTP client with retry logic
- Error handling and formatting
- Response formatting (JSON/Markdown)

Extracted from devskyy_mcp.py to eliminate duplication.
"""

import json
from enum import Enum
from typing import Any, Dict, Optional

try:
    import httpx
except ImportError:
    httpx = None


class ResponseFormat(str, Enum):
    """Output format for API responses."""
    MARKDOWN = "markdown"
    JSON = "json"


async def make_api_request(
    base_url: str,
    endpoint: str,
    api_key: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = 60.0
) -> Dict[str, Any]:
    """
    Make authenticated request to API.
    
    Args:
        base_url: Base URL of the API
        endpoint: API endpoint (e.g., "agents/list")
        api_key: API authentication key
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Request body data
        params: Query parameters
        timeout: Request timeout in seconds
        
    Returns:
        API response as dictionary
    """
    if httpx is None:
        return {"error": "httpx not installed. Run: pip install httpx"}
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    url = f"{base_url}/api/v1/{endpoint}"
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return handle_api_error(e)
    except httpx.TimeoutException:
        return {
            "error": "Request timed out. The API may be overloaded. Try again in a moment."
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {type(e).__name__} - {str(e)}"
        }


def handle_api_error(e: "httpx.HTTPStatusError") -> Dict[str, Any]:
    """
    Convert HTTP errors to user-friendly messages.
    
    Args:
        e: HTTP status error exception
        
    Returns:
        Error dictionary with message and details
    """
    status = e.response.status_code
    
    error_messages = {
        400: "Bad request. Check your input parameters.",
        401: "Authentication failed. Check your API key.",
        403: "Permission denied. Your API key doesn't have access to this resource.",
        404: "Resource not found. The endpoint or resource doesn't exist.",
        429: "Rate limit exceeded. Wait a moment before trying again.",
        500: "API internal error. Try again or contact support.",
        503: "API is temporarily unavailable. Try again shortly."
    }
    
    message = error_messages.get(status, f"API error (HTTP {status})")
    
    return {
        "error": message,
        "status_code": status,
        "details": e.response.text[:500] if e.response.text else None
    }


def format_response(
    data: Dict[str, Any],
    format_type: ResponseFormat,
    title: str = "",
    character_limit: int = 25000
) -> str:
    """
    Format API response in requested format.
    
    Args:
        data: Response data to format
        format_type: Output format (markdown or json)
        title: Optional title for markdown output
        character_limit: Maximum characters in output
        
    Returns:
        Formatted response string
    """
    if format_type == ResponseFormat.JSON:
        return json.dumps(data, indent=2)
    
    # Markdown formatting
    output = []
    
    if title:
        output.append(f"# {title}\n")
    
    if "error" in data:
        output.append(f"❌ **Error:** {data['error']}\n")
        if "details" in data:
            output.append(f"**Details:** {data['details']}\n")
        return "\n".join(output)
    
    # Format based on data structure
    for key, value in data.items():
        if isinstance(value, dict):
            output.append(f"### {key.replace('_', ' ').title()}")
            for k, v in value.items():
                output.append(f"- **{k.replace('_', ' ').title()}:** {v}")
        elif isinstance(value, list):
            output.append(f"### {key.replace('_', ' ').title()}")
            for item in value[:10]:  # Limit list display
                if isinstance(item, dict):
                    output.append(f"- {json.dumps(item, indent=2)}")
                else:
                    output.append(f"- {item}")
            if len(value) > 10:
                output.append(f"  _(and {len(value) - 10} more)_")
        else:
            output.append(f"**{key.replace('_', ' ').title()}:** {value}")
        output.append("")
    
    result = "\n".join(output)
    
    # Check character limit
    if len(result) > character_limit:
        truncated = result[:character_limit]
        truncated += (
            f"\n\n⚠️ **Response Truncated**\n"
            f"Original length: {len(result)} characters.\n"
            f"Showing first {character_limit} characters. "
            f"Use JSON format for complete data."
        )
        return truncated
    
    return result
