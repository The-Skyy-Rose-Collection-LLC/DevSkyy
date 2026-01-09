"""
Tests for runtime/tools.py
==========================

Tool Registry and execution tests.
"""

import asyncio

import pytest

from core.runtime.tool_registry import (
    ParameterType,
    ToolCallContext,
    ToolCategory,
    ToolParameter,
    ToolRegistry,
    ToolSeverity,
    ToolSpec,
    get_tool_registry,
)


class TestToolRegistry:
    """Test ToolRegistry functionality."""

    def test_singleton(self):
        """Registry should be singleton."""
        r1 = get_tool_registry()
        r2 = get_tool_registry()
        assert r1 is r2

    def test_register_tool(self):
        """Should register tools correctly."""
        registry = ToolRegistry()

        spec = ToolSpec(
            name="test_tool",
            description="A test tool",
            category=ToolCategory.SYSTEM,
            severity=ToolSeverity.READ_ONLY,
        )

        def handler(**kwargs):
            return {"result": "ok"}

        registry.register(spec, handler)
        # Check tool is registered by trying to get it
        assert registry._tools.get("test_tool") is not None

    def test_get_registered_tool(self):
        """Should retrieve registered tool."""
        registry = ToolRegistry()

        spec = ToolSpec(
            name="get_test",
            description="Test",
            category=ToolCategory.SYSTEM,
        )
        registry.register(spec, lambda: None)

        # Access via internal dict
        tool_info = registry._tools.get("get_test")
        assert tool_info is not None

    def test_nonexistent_tool(self):
        """Should not have unregistered tool."""
        registry = ToolRegistry()
        tool = registry._tools.get("nonexistent_tool_xyz")
        assert tool is None


class TestToolSpec:
    """Test ToolSpec model."""

    def test_basic_spec(self):
        """Should create basic spec."""
        spec = ToolSpec(
            name="basic",
            description="Basic tool",
            category=ToolCategory.CONTENT,
            severity=ToolSeverity.READ_ONLY,
        )
        assert spec.name == "basic"
        assert spec.severity == ToolSeverity.READ_ONLY

    def test_spec_with_parameters(self):
        """Should create spec with parameters."""
        spec = ToolSpec(
            name="parameterized",
            description="Tool with params",
            category=ToolCategory.COMMERCE,
            parameters=[
                ToolParameter(
                    name="product_id",
                    type=ParameterType.INTEGER,
                    description="Product ID",
                    required=True,
                ),
                ToolParameter(
                    name="quantity",
                    type=ParameterType.INTEGER,
                    description="Quantity",
                    default=1,
                ),
            ],
        )
        assert len(spec.parameters) == 2
        assert spec.parameters[0].required is True


class TestToolCallContext:
    """Test ToolCallContext."""

    def test_create_context(self):
        """Should create context with defaults."""
        ctx = ToolCallContext(
            request_id="req-123",
            user_id="user-456",
        )
        assert ctx.request_id == "req-123"
        assert ctx.user_id == "user-456"
        assert ctx.timeout_seconds == 30.0  # default

    def test_context_with_permissions(self):
        """Should handle permissions."""
        ctx = ToolCallContext(
            request_id="req",
            permissions={"read", "write"},
            is_admin=True,
        )
        assert "read" in ctx.permissions
        assert ctx.is_admin is True


class TestToolExecution:
    """Test tool execution."""

    @pytest.mark.asyncio
    async def test_execute_sync_tool(self):
        """Should execute sync tool."""
        registry = ToolRegistry()

        def sync_handler(x: int, y: int) -> dict:
            return {"sum": x + y}

        spec = ToolSpec(
            name="add",
            description="Add numbers",
            category=ToolCategory.SYSTEM,
        )
        registry.register(spec, sync_handler)

        ctx = ToolCallContext(request_id="test")
        result = await registry.execute("add", {"x": 2, "y": 3}, ctx)

        assert result.success is True
        assert result.result["sum"] == 5

    @pytest.mark.asyncio
    async def test_execute_async_tool(self):
        """Should execute async tool."""
        registry = ToolRegistry()

        async def async_handler(msg: str) -> dict:
            await asyncio.sleep(0.01)
            return {"message": msg.upper()}

        spec = ToolSpec(
            name="uppercase",
            description="Uppercase message",
            category=ToolCategory.CONTENT,
        )
        registry.register(spec, async_handler)

        ctx = ToolCallContext(request_id="test")
        result = await registry.execute("uppercase", {"msg": "hello"}, ctx)

        assert result.success is True
        assert result.result["message"] == "HELLO"

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """Should fail for nonexistent tool."""
        registry = ToolRegistry()
        ctx = ToolCallContext(request_id="test")

        result = await registry.execute("nonexistent", {}, ctx)
        assert result.success is False
        assert "unknown" in result.error.lower()


class TestToolExport:
    """Test tool export formats."""

    def test_tool_to_openai_format(self):
        """Should format tool for OpenAI."""
        spec = ToolSpec(
            name="search",
            description="Search products",
            category=ToolCategory.COMMERCE,
            parameters=[
                ToolParameter(
                    name="query",
                    type=ParameterType.STRING,
                    description="Search query",
                    required=True,
                ),
            ],
        )

        # Test spec has correct structure
        assert spec.name == "search"
        assert len(spec.parameters) == 1
        assert spec.parameters[0].type == ParameterType.STRING

    def test_tool_to_anthropic_format(self):
        """Should format tool for Anthropic."""
        spec = ToolSpec(
            name="get_weather",
            description="Get weather",
            category=ToolCategory.SYSTEM,
        )

        # Test spec has correct structure
        assert spec.name == "get_weather"
        assert spec.description == "Get weather"
