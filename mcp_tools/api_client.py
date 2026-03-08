"""Shared API client utilities: _make_api_request, _handle_api_error, _format_response."""

import json
import traceback
from typing import Any

import httpx
from utils.logging_utils import (
    get_correlation_id,
    log_api_request,
    log_api_response,
    log_error,
    set_correlation_id,
)
from utils.rate_limiting import check_rate_limit
from utils.request_deduplication import deduplicate_request

from mcp_tools.server import API_BASE_URL, API_KEY, CHARACTER_LIMIT, REQUEST_TIMEOUT, logger
from mcp_tools.types import ResponseFormat


async def _make_api_request(
    endpoint: str,
    method: str = "GET",
    data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Make authenticated request to DevSkyy API with correlation tracking and logging.

    Args:
        endpoint: API endpoint path
        method: HTTP method
        data: Request body data
        params: Query parameters

    Returns:
        API response dictionary
    """
    # Generate correlation ID for request tracking
    correlation_id = get_correlation_id()
    set_correlation_id(correlation_id)

    # RATE LIMITING: Check rate limit before proceeding
    user_id = "mcp_server"  # Default user ID for MCP server requests
    allowed, retry_after = await check_rate_limit(user_id=user_id, endpoint=endpoint, tokens=1)

    if not allowed:
        logger.warning(
            "rate_limit_exceeded",
            endpoint=endpoint,
            retry_after=retry_after,
            correlation_id=correlation_id,
        )
        return {
            "error": f"Rate limit exceeded. Retry after {retry_after:.2f} seconds.",
            "retry_after": retry_after,
            "correlation_id": correlation_id,
        }

    # REQUEST DEDUPLICATION: Deduplicate concurrent identical requests
    async def make_request():
        """Inner function for actual request execution"""

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "X-Correlation-ID": correlation_id,  # Track across services
        }

        url = f"{API_BASE_URL}/api/v1/{endpoint}"

        # Log outgoing request
        await log_api_request(
            endpoint=endpoint,
            method=method,
            params=params or data,
            correlation_id=correlation_id,
        )

        import time

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.request(
                    method=method, url=url, headers=headers, json=data, params=params
                )
                response.raise_for_status()

                duration_ms = (time.time() - start_time) * 1000

                # Log successful response
                await log_api_response(
                    endpoint=endpoint,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                )

                return response.json()

        except httpx.HTTPStatusError as e:
            duration_ms = (time.time() - start_time) * 1000

            # Log error response
            await log_api_response(
                endpoint=endpoint,
                status_code=e.response.status_code,
                duration_ms=duration_ms,
                error=str(e),
            )

            return _handle_api_error(e)

        except httpx.TimeoutException as e:
            duration_ms = (time.time() - start_time) * 1000

            error_msg = (
                f"Request timed out after {duration_ms:.0f}ms. The DevSkyy API may be overloaded."
            )

            # Log timeout with stack trace
            await log_error(
                error=e,
                context={
                    "endpoint": endpoint,
                    "method": method,
                    "duration_ms": duration_ms,
                    "timeout": REQUEST_TIMEOUT,
                },
                stack_trace=traceback.format_exc(),
            )

            return {"error": error_msg}

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            # Log unexpected error with full context
            await log_error(
                error=e,
                context={
                    "endpoint": endpoint,
                    "method": method,
                    "duration_ms": duration_ms,
                    "url": url,
                },
                stack_trace=traceback.format_exc(),
            )

            return {
                "error": f"Unexpected error: {type(e).__name__} - {str(e)}",
                "correlation_id": correlation_id,
                "stack_trace": traceback.format_exc(),
            }

    # REQUEST DEDUPLICATION: Wrap request execution with deduplication
    return await deduplicate_request(
        endpoint=endpoint,
        method=method,
        request_func=make_request,
        data=data,
        params=params,
    )


def _handle_api_error(e: httpx.HTTPStatusError) -> dict[str, Any]:
    """Convert HTTP errors to user-friendly messages."""
    status = e.response.status_code

    error_messages = {
        400: "Bad request. Check your input parameters.",
        401: "Authentication failed. Check your DEVSKYY_API_KEY environment variable.",
        403: "Permission denied. Your API key doesn't have access to this resource.",
        404: "Resource not found. The endpoint or resource doesn't exist.",
        429: "Rate limit exceeded. Wait a moment before trying again.",
        500: "DevSkyy API internal error. Try again or contact support.",
        503: "DevSkyy API is temporarily unavailable. Try again shortly.",
    }

    message = error_messages.get(status, f"API error (HTTP {status})")

    return {
        "error": message,
        "status_code": status,
        "details": e.response.text[:500] if e.response.text else None,
    }


def _format_response(data: dict[str, Any], format_type: ResponseFormat, title: str = "") -> str:
    """Format response in requested format."""
    if format_type == ResponseFormat.JSON:
        return json.dumps(data, indent=2)

    # Markdown formatting
    output = []
    if title:
        output.append(f"# {title}\n")

    if "error" in data:
        output.append(f"\u274c **Error:** {data['error']}\n")
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
    if len(result) > CHARACTER_LIMIT:
        truncated = result[:CHARACTER_LIMIT]
        truncated += f"\n\n\u26a0\ufe0f **Response Truncated**\nOriginal length: {len(result)} characters.\nShowing first {CHARACTER_LIMIT} characters. Use JSON format for complete data."
        return truncated

    return result
