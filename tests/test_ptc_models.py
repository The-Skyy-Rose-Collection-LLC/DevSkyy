"""
Tests for Programmatic Tool Calling Models
===========================================

Tests CallerInfo, ContainerInfo, and enhanced ToolCall/CompletionResponse models.

Following TDD: Write tests first, then implement models.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from llm.base import (
    CallerInfo,
    CallerType,
    CompletionResponse,
    ContainerInfo,
    ToolCall,
)

# =============================================================================
# CallerInfo Tests
# =============================================================================


def test_caller_info_direct():
    """Test direct caller (traditional tool use)."""
    caller = CallerInfo(type=CallerType.DIRECT)

    assert caller.type == CallerType.DIRECT
    assert caller.tool_id is None
    assert not caller.is_programmatic


def test_caller_info_code_execution():
    """Test code execution caller (programmatic tool use)."""
    caller = CallerInfo(type=CallerType.CODE_EXECUTION, tool_id="srvtoolu_abc123")

    assert caller.type == CallerType.CODE_EXECUTION
    assert caller.tool_id == "srvtoolu_abc123"
    assert caller.is_programmatic


def test_caller_info_validation():
    """Test CallerInfo validates required fields."""
    # Should work with valid type
    CallerInfo(type=CallerType.DIRECT)
    CallerInfo(type=CallerType.CODE_EXECUTION, tool_id="srv_123")

    # Code execution requires tool_id
    with pytest.raises(ValueError, match="tool_id required"):
        CallerInfo(type=CallerType.CODE_EXECUTION)


# =============================================================================
# ContainerInfo Tests
# =============================================================================


def test_container_info_creation():
    """Test ContainerInfo basic creation."""
    expires_at = datetime.now(UTC) + timedelta(minutes=4)
    container = ContainerInfo(id="cont_abc123", expires_at=expires_at)

    assert container.id == "cont_abc123"
    assert container.expires_at == expires_at
    assert not container.is_expired


def test_container_info_expiration():
    """Test container expiration checking."""
    # Not expired (4 minutes from now)
    future = datetime.now(UTC) + timedelta(minutes=4)
    container = ContainerInfo(id="cont_123", expires_at=future)
    assert not container.is_expired
    assert 230 < container.time_remaining_seconds < 250

    # Expired (1 minute ago)
    past = datetime.now(UTC) - timedelta(minutes=1)
    expired = ContainerInfo(id="cont_456", expires_at=past)
    assert expired.is_expired
    assert expired.time_remaining_seconds == 0


def test_container_info_time_remaining():
    """Test time_remaining_seconds calculation."""
    # Exactly 5 minutes from now
    expires = datetime.now(UTC) + timedelta(minutes=5)
    container = ContainerInfo(id="cont_789", expires_at=expires)

    remaining = container.time_remaining_seconds
    assert 295 < remaining < 305  # ~300 seconds, allow 5s tolerance


# =============================================================================
# ToolCall with Caller Tests
# =============================================================================


def test_tool_call_direct():
    """Test ToolCall with direct caller."""
    call = ToolCall(
        id="toolu_001",
        type="function",
        function={"name": "search_products", "arguments": {"query": "jewelry"}},
        caller=CallerInfo(type=CallerType.DIRECT),
    )

    assert call.id == "toolu_001"
    assert call.name == "search_products"
    assert call.arguments == {"query": "jewelry"}
    assert not call.is_programmatic
    assert call.caller is not None  # Type guard
    assert call.caller.type == CallerType.DIRECT


def test_tool_call_programmatic():
    """Test ToolCall with code execution caller."""
    call = ToolCall(
        id="toolu_002",
        type="function",
        function={"name": "query_database", "arguments": {"sql": "SELECT * FROM products"}},
        caller=CallerInfo(type=CallerType.CODE_EXECUTION, tool_id="srvtoolu_abc"),
    )

    assert call.is_programmatic
    assert call.caller is not None  # Type guard
    assert call.caller.type == CallerType.CODE_EXECUTION
    assert call.caller.tool_id == "srvtoolu_abc"


def test_tool_call_backward_compatible():
    """Test ToolCall works without caller (backward compatibility)."""
    call = ToolCall(
        id="toolu_003",
        type="function",
        function={"name": "old_tool", "arguments": {}},
    )

    assert call.caller is None
    assert not call.is_programmatic  # Should default to False


# =============================================================================
# CompletionResponse with Container Tests
# =============================================================================


def test_completion_response_with_container():
    """Test CompletionResponse includes container info."""
    expires = datetime.now(UTC) + timedelta(minutes=4)
    container = ContainerInfo(id="cont_xyz", expires_at=expires)

    response = CompletionResponse(
        content="Analysis complete",
        model="claude-sonnet-4-20250514",
        provider="anthropic",
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        finish_reason="end_turn",
        container=container,
    )

    assert response.container is not None
    assert response.container.id == "cont_xyz"
    assert not response.container.is_expired


def test_completion_response_without_container():
    """Test CompletionResponse works without container (non-PTC)."""
    response = CompletionResponse(
        content="Hello",
        model="claude-sonnet-4-20250514",
        provider="anthropic",
        input_tokens=10,
        output_tokens=5,
        total_tokens=15,
        finish_reason="end_turn",
    )

    assert response.container is None


def test_completion_response_with_programmatic_tools():
    """Test CompletionResponse with programmatic tool calls."""
    expires = datetime.now(UTC) + timedelta(minutes=4)
    container = ContainerInfo(id="cont_123", expires_at=expires)

    tool_calls = [
        ToolCall(
            id="toolu_001",
            type="function",
            function={"name": "search_products", "arguments": {"query": "watches"}},
            caller=CallerInfo(type=CallerType.CODE_EXECUTION, tool_id="srvtoolu_code"),
        ),
        ToolCall(
            id="toolu_002",
            type="function",
            function={"name": "search_products", "arguments": {"query": "jewelry"}},
            caller=CallerInfo(type=CallerType.CODE_EXECUTION, tool_id="srvtoolu_code"),
        ),
    ]

    response = CompletionResponse(
        content="",
        model="claude-sonnet-4-20250514",
        provider="anthropic",
        input_tokens=200,
        output_tokens=50,
        total_tokens=250,
        finish_reason="tool_use",
        tool_calls=tool_calls,
        container=container,
    )

    assert response.has_tool_calls
    assert len(response.tool_calls) == 2
    assert all(tc.is_programmatic for tc in response.tool_calls)
    assert response.container is not None


# =============================================================================
# Mixed Tool Calls (Direct + Programmatic)
# =============================================================================


def test_mixed_tool_calls():
    """Test response with both direct and programmatic calls."""
    tool_calls = [
        # Direct call
        ToolCall(
            id="toolu_direct",
            type="function",
            function={"name": "generate_3d", "arguments": {"prompt": "ring"}},
            caller=CallerInfo(type=CallerType.DIRECT),
        ),
        # Programmatic call
        ToolCall(
            id="toolu_prog",
            type="function",
            function={"name": "search_products", "arguments": {"query": "ring"}},
            caller=CallerInfo(type=CallerType.CODE_EXECUTION, tool_id="srvtoolu_123"),
        ),
    ]

    response = CompletionResponse(
        content="",
        model="claude-sonnet-4-20250514",
        provider="anthropic",
        input_tokens=150,
        output_tokens=75,
        total_tokens=225,
        finish_reason="tool_use",
        tool_calls=tool_calls,
    )

    # Count programmatic vs direct
    programmatic = [tc for tc in response.tool_calls if tc.is_programmatic]
    direct = [tc for tc in response.tool_calls if not tc.is_programmatic]

    assert len(programmatic) == 1
    assert len(direct) == 1
    assert programmatic[0].name == "search_products"
    assert direct[0].name == "generate_3d"


# =============================================================================
# Serialization Tests
# =============================================================================


def test_caller_info_to_dict():
    """Test CallerInfo serialization."""
    caller = CallerInfo(type=CallerType.CODE_EXECUTION, tool_id="srvtoolu_abc")
    data = caller.to_dict()

    assert data == {
        "type": "code_execution_20250825",
        "tool_id": "srvtoolu_abc",
    }


def test_container_info_to_dict():
    """Test ContainerInfo serialization."""
    # Use future time to avoid immediate expiration
    expires = datetime.now(UTC) + timedelta(minutes=5)
    container = ContainerInfo(id="cont_123", expires_at=expires)
    data = container.to_dict()

    assert data["id"] == "cont_123"
    assert "expires_at" in data
    assert data["is_expired"] is False
    assert "time_remaining_seconds" in data
    assert data["time_remaining_seconds"] > 0


def test_tool_call_to_dict():
    """Test ToolCall serialization with caller."""
    call = ToolCall(
        id="toolu_001",
        type="function",
        function={"name": "search", "arguments": {"q": "test"}},
        caller=CallerInfo(type=CallerType.CODE_EXECUTION, tool_id="srvtoolu_abc"),
    )
    data = call.to_dict()

    assert data["id"] == "toolu_001"
    assert data["caller"]["type"] == "code_execution_20250825"
    assert data["caller"]["tool_id"] == "srvtoolu_abc"


# =============================================================================
# Edge Cases
# =============================================================================


def test_container_exactly_at_expiration():
    """Test container exactly at expiration time."""
    now = datetime.now(UTC)
    container = ContainerInfo(id="cont_edge", expires_at=now)

    # At exact expiration, should be considered expired
    assert container.is_expired or container.time_remaining_seconds < 1


def test_caller_info_invalid_type():
    """Test CallerInfo rejects invalid types."""
    with pytest.raises(ValueError):
        CallerInfo(type="invalid_type")  # type: ignore


@pytest.mark.parametrize(
    "minutes,expected_expired",
    [
        (-1, True),  # 1 minute ago - expired
        (0, True),  # Now - expired
        (1, False),  # 1 minute from now - not expired
        (4, False),  # 4 minutes from now - not expired
        (5, False),  # 5 minutes from now - not expired
    ],
)
def test_container_expiration_parametrized(minutes: int, expected_expired: bool):
    """Test various expiration scenarios."""
    expires = datetime.now(UTC) + timedelta(minutes=minutes)
    container = ContainerInfo(id=f"cont_{minutes}", expires_at=expires)

    assert container.is_expired == expected_expired
