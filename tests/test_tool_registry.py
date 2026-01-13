"""
Tests for ToolRegistry governance features.

Tests:
- Rate limiting (per-tool, per-user)
- Permission checking
- Export methods (OpenAI, Anthropic, MCP)
- Input validation
- Timeout enforcement
"""

import asyncio
import time

import pytest

from core.runtime.tool_registry import (
    ExecutionStatus,
    ParameterType,
    ToolCallContext,
    ToolCategory,
    ToolParameter,
    ToolRegistry,
    ToolSeverity,
    ToolSpec,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def registry():
    """Fresh ToolRegistry instance for each test."""
    return ToolRegistry()


@pytest.fixture
def sample_tool_spec():
    """Sample tool specification for testing."""
    return ToolSpec(
        name="test_tool",
        description="A test tool",
        category=ToolCategory.SYSTEM,
        severity=ToolSeverity.READ_ONLY,
        parameters=[
            ToolParameter(
                name="arg1",
                type=ParameterType.STRING,
                description="First argument",
                required=True,
            ),
            ToolParameter(
                name="arg2",
                type=ParameterType.INTEGER,
                description="Second argument",
                default=0,
            ),
        ],
        permissions={"test:read"},
        rate_limit=5,  # 5 requests per minute
        timeout_seconds=10.0,
    )


@pytest.fixture
def rate_limited_tool_spec():
    """Tool with strict rate limit for testing."""
    return ToolSpec(
        name="rate_limited_tool",
        description="Tool with strict rate limit",
        category=ToolCategory.COMMERCE,
        severity=ToolSeverity.HIGH,
        parameters=[],  # No required parameters
        permissions=set(),  # No permissions required for testing
        rate_limit=2,  # Only 2 requests per minute
        timeout_seconds=5.0,
    )


@pytest.fixture
def protected_tool_spec():
    """Tool requiring specific permissions."""
    return ToolSpec(
        name="protected_tool",
        description="Tool requiring permissions",
        category=ToolCategory.SECURITY,
        severity=ToolSeverity.DESTRUCTIVE,
        permissions={"admin:write", "security:manage"},
        timeout_seconds=30.0,
    )


# =============================================================================
# Test Rate Limiting
# =============================================================================


@pytest.mark.asyncio
async def test_rate_limiting_allows_within_limit(registry, rate_limited_tool_spec):
    """Test that rate limiting allows requests within the limit."""

    async def handler(**kwargs):
        return {"success": True}

    registry.register(rate_limited_tool_spec, handler)

    context = ToolCallContext(user_id="test_user")

    # First request should succeed
    result1 = await registry.execute("rate_limited_tool", {}, context)
    assert result1.success is True

    # Second request should also succeed (within limit of 2)
    result2 = await registry.execute("rate_limited_tool", {}, context)
    assert result2.success is True


@pytest.mark.asyncio
async def test_rate_limiting_blocks_when_exceeded(registry, rate_limited_tool_spec):
    """Test that rate limiting blocks requests when limit exceeded."""

    async def handler(**kwargs):
        return {"success": True}

    registry.register(rate_limited_tool_spec, handler)

    context = ToolCallContext(user_id="test_user")

    # Make 2 successful requests (at limit)
    await registry.execute("rate_limited_tool", {}, context)
    await registry.execute("rate_limited_tool", {}, context)

    # Third request should be rate limited
    result3 = await registry.execute("rate_limited_tool", {}, context)
    assert result3.success is False
    assert result3.error_type == "RateLimitError"
    assert "Rate limit exceeded" in result3.error


@pytest.mark.asyncio
async def test_rate_limiting_per_user(registry, rate_limited_tool_spec):
    """Test that rate limiting is enforced per-user."""

    async def handler(**kwargs):
        return {"success": True}

    registry.register(rate_limited_tool_spec, handler)

    # User 1 makes 2 requests (at limit)
    context1 = ToolCallContext(user_id="user1")
    await registry.execute("rate_limited_tool", {}, context1)
    await registry.execute("rate_limited_tool", {}, context1)

    # User 2 should still be able to make requests
    context2 = ToolCallContext(user_id="user2")
    result = await registry.execute("rate_limited_tool", {}, context2)
    assert result.success is True


@pytest.mark.asyncio
async def test_rate_limiting_resets_after_window(registry, rate_limited_tool_spec):
    """Test that rate limiting resets after time window."""

    async def handler(**kwargs):
        return {"success": True}

    registry.register(rate_limited_tool_spec, handler)

    context = ToolCallContext(user_id="test_user")

    # Make 2 requests
    await registry.execute("rate_limited_tool", {}, context)
    await registry.execute("rate_limited_tool", {}, context)

    # Wait for rate limit window to expire (60 seconds + buffer)
    # For testing, we'll simulate by manipulating the tracker directly
    key = ("rate_limited_tool", "test_user")
    if key in registry._rate_limit_tracker:
        # Set timestamps to 61 seconds ago
        old_time = time.time() - 61.0
        registry._rate_limit_tracker[key] = [old_time, old_time]

    # Should now be able to make more requests
    result = await registry.execute("rate_limited_tool", {}, context)
    assert result.success is True


@pytest.mark.asyncio
async def test_rate_limiting_skips_for_no_user_id(registry, rate_limited_tool_spec):
    """Test that rate limiting is skipped when no user_id provided."""

    async def handler(**kwargs):
        return {"success": True}

    registry.register(rate_limited_tool_spec, handler)

    # Context without user_id (admin/system calls)
    context = ToolCallContext()

    # Should be able to make many requests without rate limiting
    for _ in range(10):
        result = await registry.execute("rate_limited_tool", {}, context)
        assert result.success is True


# =============================================================================
# Test Permission Checking
# =============================================================================


@pytest.mark.asyncio
async def test_permission_check_allows_with_permission(registry, protected_tool_spec):
    """Test that permission check allows when user has required permissions."""

    async def handler(**kwargs):
        return {"success": True}

    registry.register(protected_tool_spec, handler)

    # Context with required permissions
    context = ToolCallContext(
        user_id="test_user",
        permissions={"admin:write", "security:manage"},
    )

    result = await registry.execute("protected_tool", {}, context)
    assert result.success is True


@pytest.mark.asyncio
async def test_permission_check_blocks_without_permission(registry, protected_tool_spec):
    """Test that permission check blocks when user lacks permissions."""

    async def handler(**kwargs):
        return {"success": True}

    registry.register(protected_tool_spec, handler)

    # Context without required permissions
    context = ToolCallContext(
        user_id="test_user",
        permissions={"user:read"},  # Missing admin:write and security:manage
    )

    result = await registry.execute("protected_tool", {}, context)
    assert result.success is False
    assert result.error_type == "ValidationError"
    assert "Missing permissions" in result.error


@pytest.mark.asyncio
async def test_permission_check_allows_for_admin(registry, protected_tool_spec):
    """Test that permission check always allows for admin users."""

    async def handler(**kwargs):
        return {"success": True}

    registry.register(protected_tool_spec, handler)

    # Admin context without specific permissions
    context = ToolCallContext(
        user_id="admin_user",
        permissions=set(),  # No specific permissions
        is_admin=True,  # But is admin
    )

    result = await registry.execute("protected_tool", {}, context)
    assert result.success is True


# =============================================================================
# Test Export Methods
# =============================================================================


def test_export_to_openai_functions(registry, sample_tool_spec):
    """Test export to OpenAI function calling format."""
    registry.register(sample_tool_spec)

    functions = registry.to_openai_functions()

    assert len(functions) == 1
    func = functions[0]
    assert func["name"] == "test_tool"
    assert func["description"] == "A test tool"
    assert "parameters" in func
    assert func["parameters"]["type"] == "object"
    assert "arg1" in func["parameters"]["properties"]
    assert "required" in func["parameters"]
    assert "arg1" in func["parameters"]["required"]


def test_export_to_anthropic_tools(registry, sample_tool_spec):
    """Test export to Anthropic tool format."""
    # Add some Advanced Tool Use features
    sample_tool_spec.defer_loading = True
    sample_tool_spec.allowed_callers = ["code_execution_20250825"]
    sample_tool_spec.input_examples = [{"arg1": "test", "arg2": 123}]

    registry.register(sample_tool_spec)

    tools = registry.to_anthropic_tools()

    assert len(tools) == 1
    tool = tools[0]
    assert tool["name"] == "test_tool"
    assert tool["description"] == "A test tool"
    assert "input_schema" in tool
    assert tool["input_schema"]["type"] == "object"
    # Check Advanced Tool Use fields
    assert tool["defer_loading"] is True
    assert tool["allowed_callers"] == ["code_execution_20250825"]
    assert len(tool["input_examples"]) == 1


def test_export_to_mcp_tools(registry, sample_tool_spec):
    """Test export to MCP tool format."""
    registry.register(sample_tool_spec)

    tools = registry.to_mcp_tools()

    assert len(tools) == 1
    tool = tools[0]
    assert tool["name"] == "test_tool"
    assert tool["description"] == "A test tool"
    assert "inputSchema" in tool
    assert tool["inputSchema"]["type"] == "object"
    assert "annotations" in tool
    # Check severity hints
    assert tool["annotations"]["readOnlyHint"] is True  # READ_ONLY severity
    assert tool["annotations"]["destructiveHint"] is False
    assert tool["annotations"]["idempotentHint"] is False


def test_export_schema_complete(registry, sample_tool_spec):
    """Test complete registry schema export."""
    registry.register(sample_tool_spec)

    schema = registry.export_schema()

    assert schema["version"] == "1.0.0"
    assert schema["total_tools"] == 1
    assert "categories" in schema
    assert schema["categories"]["system"] == 1
    assert "tools" in schema
    assert len(schema["tools"]) == 1


# =============================================================================
# Test Input Validation
# =============================================================================


@pytest.mark.asyncio
async def test_input_validation_required_params(registry, sample_tool_spec):
    """Test validation of required parameters."""

    async def handler(**kwargs):
        return {"success": True}

    registry.register(sample_tool_spec, handler)

    # Missing required param
    result = await registry.execute("test_tool", {"arg2": 123})
    assert result.success is False
    assert result.error_type == "ValidationError"
    assert "Missing required parameter: arg1" in result.error


@pytest.mark.asyncio
async def test_input_validation_type_checking(registry):
    """Test type validation of parameters."""
    spec = ToolSpec(
        name="typed_tool",
        description="Tool with type constraints",
        category=ToolCategory.SYSTEM,
        parameters=[
            ToolParameter(
                name="number_param",
                type=ParameterType.INTEGER,
                description="Must be integer",
                required=True,
            ),
        ],
    )

    async def handler(**kwargs):
        return {"success": True}

    registry.register(spec, handler)

    # Wrong type (string instead of integer)
    result = await registry.execute("typed_tool", {"number_param": "not_a_number"})
    assert result.success is False
    assert "must be integer" in result.error


@pytest.mark.asyncio
async def test_input_validation_enum_constraint(registry):
    """Test enum constraint validation."""
    spec = ToolSpec(
        name="enum_tool",
        description="Tool with enum constraint",
        category=ToolCategory.SYSTEM,
        parameters=[
            ToolParameter(
                name="status",
                type=ParameterType.STRING,
                description="Status",
                required=True,
                enum=["active", "inactive", "pending"],
            ),
        ],
    )

    async def handler(**kwargs):
        return {"success": True}

    registry.register(spec, handler)

    # Invalid enum value
    result = await registry.execute("enum_tool", {"status": "invalid"})
    assert result.success is False
    assert "must be one of" in result.error


# =============================================================================
# Test Timeout Enforcement
# =============================================================================


@pytest.mark.asyncio
async def test_timeout_enforcement(registry):
    """Test that tool execution times out after configured limit."""
    spec = ToolSpec(
        name="slow_tool",
        description="Tool that takes too long",
        category=ToolCategory.SYSTEM,
        timeout_seconds=0.5,  # 500ms timeout
    )

    async def slow_handler(**kwargs):
        await asyncio.sleep(2.0)  # Takes 2 seconds
        return {"success": True}

    registry.register(spec, slow_handler)

    result = await registry.execute("slow_tool", {})
    assert result.success is False
    assert result.status == ExecutionStatus.TIMEOUT
    assert "timed out" in result.error.lower()


# =============================================================================
# Test Caching
# =============================================================================


@pytest.mark.asyncio
async def test_caching_enabled(registry):
    """Test that caching works when enabled."""
    spec = ToolSpec(
        name="cacheable_tool",
        description="Tool with caching",
        category=ToolCategory.SYSTEM,
        cacheable=True,
        cache_ttl_seconds=60,
    )

    call_count = 0

    async def handler(**kwargs):
        nonlocal call_count
        call_count += 1
        return {"count": call_count}

    registry.register(spec, handler)

    # First call
    result1 = await registry.execute("cacheable_tool", {"key": "value"})
    assert result1.success is True
    assert result1.result["count"] == 1
    assert result1.from_cache is False

    # Second call with same params should be cached
    result2 = await registry.execute("cacheable_tool", {"key": "value"})
    assert result2.success is True
    assert result2.result["count"] == 1  # Same as first call
    assert result2.from_cache is True
    assert call_count == 1  # Handler only called once


# =============================================================================
# Test Tool Registry Integration
# =============================================================================


@pytest.mark.asyncio
async def test_tool_registry_decorator(registry):
    """Test tool registration via decorator."""

    @registry.tool(
        name="decorated_tool",
        description="Tool registered via decorator",
        category=ToolCategory.COMMERCE,
        severity=ToolSeverity.LOW,
    )
    async def decorated_handler(product_name: str) -> dict:
        return {"product": product_name}

    # Tool should be registered
    tool = registry.get("decorated_tool")
    assert tool is not None
    assert tool.name == "decorated_tool"

    # Should be executable
    result = await registry.execute("decorated_tool", {"product_name": "Test Product"})
    assert result.success is True
    assert result.result["product"] == "Test Product"


@pytest.mark.asyncio
async def test_tool_registry_get_by_category(registry, sample_tool_spec):
    """Test filtering tools by category."""
    registry.register(sample_tool_spec)

    system_tools = registry.get_by_category(ToolCategory.SYSTEM)
    assert len(system_tools) == 1
    assert system_tools[0].name == "test_tool"

    commerce_tools = registry.get_by_category(ToolCategory.COMMERCE)
    assert len(commerce_tools) == 0


@pytest.mark.asyncio
async def test_tool_registry_get_by_severity(registry, sample_tool_spec):
    """Test filtering tools by severity."""
    registry.register(sample_tool_spec)

    read_only_tools = registry.get_by_severity(ToolSeverity.READ_ONLY)
    assert len(read_only_tools) == 1

    destructive_tools = registry.get_by_severity(ToolSeverity.DESTRUCTIVE)
    assert len(destructive_tools) == 0
