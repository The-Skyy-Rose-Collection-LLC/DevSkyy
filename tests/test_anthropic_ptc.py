"""
Tests for Anthropic Client Programmatic Tool Calling Integration
=================================================================

Tests beta headers, container support, and response parsing for PTC.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from llm.base import CallerType, Message
from llm.providers.anthropic import AnthropicClient


@pytest.fixture
def mock_response_direct_tool():
    """Mock Anthropic API response with direct tool call."""
    return {
        "id": "msg_123",
        "type": "message",
        "role": "assistant",
        "content": [
            {"type": "text", "text": "I'll search for products."},
            {
                "type": "tool_use",
                "id": "toolu_abc123",
                "name": "search_products",
                "input": {"query": "jewelry"},
            },
        ],
        "model": "claude-sonnet-4-20250514",
        "stop_reason": "tool_use",
        "usage": {"input_tokens": 100, "output_tokens": 50},
    }


@pytest.fixture
def mock_response_programmatic_tool():
    """Mock Anthropic API response with programmatic tool call."""
    expires_at = (datetime.now(UTC) + timedelta(minutes=4)).isoformat().replace("+00:00", "Z")
    return {
        "id": "msg_456",
        "type": "message",
        "role": "assistant",
        "content": [
            {"type": "text", "text": "Running batch search."},
            {
                "type": "server_tool_use",
                "id": "srvtoolu_code",
                "name": "code_execution",
                "input": {"code": "results = await search_products('jewelry')"},
            },
            {
                "type": "tool_use",
                "id": "toolu_prog123",
                "name": "search_products",
                "input": {"query": "jewelry"},
                "caller": {"type": "code_execution_20250825", "tool_id": "srvtoolu_code"},
            },
        ],
        "container": {"id": "cont_xyz789", "expires_at": expires_at},
        "model": "claude-sonnet-4-20250514",
        "stop_reason": "tool_use",
        "usage": {"input_tokens": 150, "output_tokens": 75},
    }


@pytest.mark.asyncio
async def test_anthropic_client_default_ptc_enabled():
    """Test AnthropicClient enables PTC by default."""
    client = AnthropicClient()
    assert client.enable_ptc is True


@pytest.mark.asyncio
async def test_anthropic_client_ptc_can_be_disabled():
    """Test AnthropicClient PTC can be disabled."""
    client = AnthropicClient(enable_ptc=False)
    assert client.enable_ptc is False


@pytest.mark.asyncio
async def test_anthropic_client_beta_header_when_ptc_enabled():
    """Test beta header is added when PTC is enabled."""
    client = AnthropicClient(enable_ptc=True)
    headers = client._get_headers()

    assert "anthropic-beta" in headers
    assert headers["anthropic-beta"] == "advanced-tool-use-2025-11-20"


@pytest.mark.asyncio
async def test_anthropic_client_no_beta_header_when_ptc_disabled():
    """Test no beta header when PTC is disabled."""
    client = AnthropicClient(enable_ptc=False)
    headers = client._get_headers()

    assert "anthropic-beta" not in headers


@pytest.mark.asyncio
async def test_anthropic_client_parse_direct_tool_call(mock_response_direct_tool):
    """Test parsing direct tool call (traditional tool use)."""
    client = AnthropicClient()

    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = MagicMock(json=lambda: mock_response_direct_tool)

        response = await client.complete(
            messages=[Message.user("Search for jewelry")],
            tools=[
                {
                    "name": "search_products",
                    "description": "Search products",
                    "parameters": {"type": "object", "properties": {}},
                }
            ],
        )

    # Validate response
    assert response.content == "I'll search for products."
    assert len(response.tool_calls) == 1

    # Validate tool call
    tool_call = response.tool_calls[0]
    assert tool_call.id == "toolu_abc123"
    assert tool_call.name == "search_products"
    assert tool_call.arguments == {"query": "jewelry"}

    # Should be direct call (no caller info in original response)
    assert tool_call.caller is None
    assert not tool_call.is_programmatic


@pytest.mark.asyncio
async def test_anthropic_client_parse_programmatic_tool_call(mock_response_programmatic_tool):
    """Test parsing programmatic tool call from code execution."""
    client = AnthropicClient(enable_ptc=True)

    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = MagicMock(json=lambda: mock_response_programmatic_tool)

        response = await client.complete(
            messages=[Message.user("Batch search")],
            tools=[
                {
                    "type": "code_execution_20250825",
                    "name": "code_execution",
                },
                {
                    "name": "search_products",
                    "description": "Search products",
                    "parameters": {"type": "object", "properties": {}},
                    "allowed_callers": ["code_execution_20250825"],
                },
            ],
        )

    # Validate container info
    assert response.container is not None
    assert response.container.id == "cont_xyz789"
    assert not response.container.is_expired

    # Validate tool calls
    assert len(response.tool_calls) == 1
    tool_call = response.tool_calls[0]
    assert tool_call.id == "toolu_prog123"
    assert tool_call.name == "search_products"

    # Should be programmatic call
    assert tool_call.caller is not None
    assert tool_call.caller.type == CallerType.CODE_EXECUTION
    assert tool_call.caller.tool_id == "srvtoolu_code"
    assert tool_call.is_programmatic


@pytest.mark.asyncio
async def test_anthropic_client_container_reuse():
    """Test container ID is sent in request for reuse."""
    client = AnthropicClient(enable_ptc=True)

    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = MagicMock(
            json=lambda: {
                "id": "msg_789",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": "Done"}],
                "model": "claude-sonnet-4-20250514",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 50, "output_tokens": 10},
            }
        )

        await client.complete(messages=[Message.user("Continue")], container_id="cont_existing123")

        # Verify container ID was sent in request
        call_args = mock_request.call_args
        request_data = call_args.kwargs["json"]
        assert request_data["container"] == "cont_existing123"


@pytest.mark.asyncio
async def test_anthropic_client_no_container_when_not_provided():
    """Test no container field sent when container_id not provided."""
    client = AnthropicClient(enable_ptc=True)

    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = MagicMock(
            json=lambda: {
                "id": "msg_101",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": "Hello"}],
                "model": "claude-sonnet-4-20250514",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }
        )

        await client.complete(messages=[Message.user("Hello")])

        # Verify no container field in request
        call_args = mock_request.call_args
        request_data = call_args.kwargs["json"]
        assert "container" not in request_data


@pytest.mark.asyncio
async def test_anthropic_client_mixed_tool_calls():
    """Test response with both direct and programmatic tool calls."""
    expires_at = (datetime.now(UTC) + timedelta(minutes=4)).isoformat().replace("+00:00", "Z")
    mixed_response = {
        "id": "msg_mixed",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "tool_use",
                "id": "toolu_direct",
                "name": "generate_3d",
                "input": {"prompt": "ring"},
            },
            {
                "type": "tool_use",
                "id": "toolu_prog",
                "name": "search_products",
                "input": {"query": "ring"},
                "caller": {"type": "code_execution_20250825", "tool_id": "srvtoolu_123"},
            },
        ],
        "container": {"id": "cont_mixed", "expires_at": expires_at},
        "model": "claude-sonnet-4-20250514",
        "stop_reason": "tool_use",
        "usage": {"input_tokens": 200, "output_tokens": 100},
    }

    client = AnthropicClient(enable_ptc=True)

    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = MagicMock(json=lambda: mixed_response)

        response = await client.complete(
            messages=[Message.user("Create and search for ring")],
            tools=[
                {"type": "code_execution_20250825", "name": "code_execution"},
                {
                    "name": "search_products",
                    "description": "Search",
                    "parameters": {},
                    "allowed_callers": ["code_execution_20250825"],
                },
                {
                    "name": "generate_3d",
                    "description": "Generate 3D",
                    "parameters": {},
                    "allowed_callers": ["direct"],
                },
            ],
        )

    assert len(response.tool_calls) == 2

    # First call: direct
    direct_call = response.tool_calls[0]
    assert direct_call.name == "generate_3d"
    assert not direct_call.is_programmatic

    # Second call: programmatic
    prog_call = response.tool_calls[1]
    assert prog_call.name == "search_products"
    assert prog_call.is_programmatic
    assert prog_call.caller is not None  # Type guard
    assert prog_call.caller.tool_id == "srvtoolu_123"


@pytest.mark.asyncio
async def test_anthropic_client_backward_compatible_response():
    """Test client handles old responses without caller/container fields."""
    old_response = {
        "id": "msg_old",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "tool_use",
                "id": "toolu_old",
                "name": "old_tool",
                "input": {"arg": "value"},
            }
        ],
        "model": "claude-sonnet-4-20250514",
        "stop_reason": "tool_use",
        "usage": {"input_tokens": 50, "output_tokens": 25},
    }

    client = AnthropicClient(enable_ptc=True)

    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = MagicMock(json=lambda: old_response)

        response = await client.complete(
            messages=[Message.user("Test")],
            tools=[{"name": "old_tool", "description": "Test", "parameters": {}}],
        )

    # Should handle gracefully
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].caller is None
    assert not response.tool_calls[0].is_programmatic
    assert response.container is None


@pytest.mark.asyncio
async def test_anthropic_client_max_tokens_default_increased():
    """Test default max_tokens increased for PTC."""
    client = AnthropicClient(enable_ptc=True)

    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = MagicMock(
            json=lambda: {
                "id": "msg_test",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": "Test"}],
                "model": "claude-sonnet-4-20250514",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }
        )

        # Call without specifying max_tokens
        await client.complete(messages=[Message.user("Test")])

        # Check that request used increased default
        call_args = mock_request.call_args
        request_data = call_args.kwargs["json"]
        # Should use higher default for PTC (4096 instead of 1024)
        assert request_data["max_tokens"] >= 4096
