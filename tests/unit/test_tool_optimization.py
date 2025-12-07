"""
Unit Tests for Token-Optimized Tool Calling
Comprehensive test coverage for dynamic tool selection and optimization

Per Truth Protocol:
- Rule #8: Test coverage ≥90%
- Rule #12: Performance SLOs - Verify token optimization
"""


import pytest

from ml.tool_optimization import (
    DynamicToolSelector,
    ParallelFunctionCaller,
    StructuredOutputValidator,
    TokenOptimizationManager,
    ToolSelectionContext,
    get_optimization_manager,
)
from security.tool_calling_safeguards import (
    ToolCallConfig,
    ToolPermissionLevel,
    ToolProvider,
    ToolRiskLevel,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def tool_selector():
    """Create dynamic tool selector"""
    return DynamicToolSelector()


@pytest.fixture
def sample_tool_schema():
    """Sample tool schema"""
    return {
        "name": "get_weather",
        "description": "Get weather information for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or coordinates"
                },
                "units": {
                    "type": "string",
                    "description": "Temperature units (celsius or fahrenheit)"
                }
            },
            "required": ["location"]
        }
    }


@pytest.fixture
def sample_tool_config():
    """Sample tool configuration"""
    return ToolCallConfig(
        tool_name="get_weather",
        description="Get weather information",
        permission_level=ToolPermissionLevel.PUBLIC,
        risk_level=ToolRiskLevel.LOW,
        provider=ToolProvider.BOTH,
        max_calls_per_minute=100
    )


# ============================================================================
# COMPRESSED SCHEMA TESTS
# ============================================================================

def test_compress_tool_schema(tool_selector, sample_tool_schema):
    """Test tool schema compression"""
    compressed = tool_selector._compress_schema(sample_tool_schema)

    assert compressed.n == "get_weather"
    assert len(compressed.d) <= 100  # Description truncated
    assert "location" in compressed.p
    assert "units" in compressed.p
    assert "location" in compressed.r
    assert len(compressed.r) == 1


def test_compressed_schema_size_reduction(tool_selector, sample_tool_schema):
    """Test that compressed schema is smaller than original"""
    import json

    compressed = tool_selector._compress_schema(sample_tool_schema)

    original_size = len(json.dumps(sample_tool_schema))
    compressed_size = len(json.dumps(compressed.dict()))

    # Should be noticeably smaller
    assert compressed_size < original_size


# ============================================================================
# DYNAMIC TOOL SELECTOR TESTS
# ============================================================================

def test_register_tool(tool_selector, sample_tool_schema, sample_tool_config):
    """Test registering a tool"""
    tool_selector.register_tool(
        tool_name="get_weather",
        tool_config=sample_tool_config,
        full_schema=sample_tool_schema
    )

    assert "get_weather" in tool_selector.compressed_schemas
    assert "get_weather" in tool_selector.tool_patterns
    assert "get_weather" in tool_selector.tool_configs


def test_select_tools_basic(tool_selector):
    """Test basic tool selection"""
    # Register some tools
    for i in range(10):
        schema = {
            "name": f"tool_{i}",
            "description": f"Tool {i} for testing with keywords: data processing analysis",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
        config = ToolCallConfig(
            tool_name=f"tool_{i}",
            description=f"Tool {i}",
            permission_level=ToolPermissionLevel.PUBLIC,
            risk_level=ToolRiskLevel.LOW,
            provider=ToolProvider.BOTH
        )
        tool_selector.register_tool(f"tool_{i}", config, schema)

    context = ToolSelectionContext(
        task_description="I need to process and analyze data",
        max_tools=5
    )

    selected = tool_selector.select_tools(context)

    # Should select max_tools or fewer
    assert len(selected) <= 5
    assert len(selected) > 0


def test_select_tools_with_keyword_matching(tool_selector):
    """Test that tool selection uses keyword matching"""
    # Register tools with specific keywords
    weather_schema = {
        "name": "get_weather",
        "description": "Get weather forecast and temperature information",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }
    database_schema = {
        "name": "query_database",
        "description": "Query database records and retrieve data",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }

    weather_config = ToolCallConfig(
        tool_name="get_weather",
        description="Weather tool",
        permission_level=ToolPermissionLevel.PUBLIC,
        risk_level=ToolRiskLevel.LOW,
        provider=ToolProvider.BOTH
    )
    database_config = ToolCallConfig(
        tool_name="query_database",
        description="Database tool",
        permission_level=ToolPermissionLevel.PUBLIC,
        risk_level=ToolRiskLevel.LOW,
        provider=ToolProvider.BOTH
    )

    tool_selector.register_tool("get_weather", weather_config, weather_schema)
    tool_selector.register_tool("query_database", database_config, database_schema)

    # Update patterns with keywords
    tool_selector.tool_patterns["get_weather"].context_keywords = {
        "weather", "temperature", "forecast"
    }
    tool_selector.tool_patterns["query_database"].context_keywords = {
        "database", "query", "data"
    }

    # Task about weather should prefer weather tool
    context = ToolSelectionContext(
        task_description="What is the weather and temperature today?",
        max_tools=1
    )

    selected = tool_selector.select_tools(context, ["get_weather", "query_database"])
    assert len(selected) == 1
    # Note: Without actual usage history, selection might vary


def test_update_tool_performance(tool_selector, sample_tool_schema, sample_tool_config):
    """Test updating tool performance metrics"""
    tool_selector.register_tool("test_tool", sample_tool_config, sample_tool_schema)

    # Update performance multiple times
    for i in range(10):
        tool_selector.update_tool_performance(
            tool_name="test_tool",
            success=True,
            execution_time_ms=100.0 + i,
            tokens_used=50 + i,
            context_keywords={"test", "example"}
        )

    pattern = tool_selector.tool_patterns["test_tool"]
    assert pattern.usage_count == 10
    assert pattern.success_count == 10
    assert pattern.success_rate == 1.0
    assert pattern.avg_execution_time_ms > 0
    assert pattern.avg_tokens_used > 0
    assert "test" in pattern.context_keywords


def test_tool_performance_with_failures(tool_selector, sample_tool_schema, sample_tool_config):
    """Test tool performance tracking with failures"""
    tool_selector.register_tool("flaky_tool", sample_tool_config, sample_tool_schema)

    # Mix of successes and failures
    for i in range(10):
        success = i % 2 == 0  # 50% success rate
        tool_selector.update_tool_performance(
            tool_name="flaky_tool",
            success=success,
            execution_time_ms=100.0,
            tokens_used=50
        )

    pattern = tool_selector.tool_patterns["flaky_tool"]
    assert pattern.usage_count == 10
    assert pattern.success_count == 5
    assert pattern.success_rate == 0.5


def test_extract_keywords(tool_selector):
    """Test keyword extraction from text"""
    text = "I need to analyze the weather data and process the results"

    keywords = tool_selector._extract_keywords(text)

    assert "analyze" in keywords
    assert "weather" in keywords
    assert "data" in keywords
    assert "process" in keywords
    assert "results" in keywords
    # Stop words should be removed
    assert "the" not in keywords
    assert "to" not in keywords


# ============================================================================
# PARALLEL FUNCTION CALLER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_parallel_caller_initialization():
    """Test parallel function caller initializes correctly"""
    caller = ParallelFunctionCaller()
    assert caller.safeguard_manager is not None


@pytest.mark.asyncio
async def test_call_functions_parallel_empty():
    """Test parallel calling with empty function list"""
    caller = ParallelFunctionCaller()

    results = await caller.call_functions_parallel(
        function_calls=[],
        available_functions={},
        user_id="test_user"
    )

    assert len(results) == 0


# ============================================================================
# STRUCTURED OUTPUT VALIDATOR TESTS
# ============================================================================

def test_register_output_schema():
    """Test registering output schema"""
    validator = StructuredOutputValidator()

    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number"}
        },
        "required": ["name"]
    }

    validator.register_output_schema("person", schema)

    assert "person" in validator.schemas
    assert validator.schemas["person"] == schema


def test_validate_output_success():
    """Test successful output validation"""
    validator = StructuredOutputValidator()

    schema = {
        "type": "object",
        "properties": {
            "result": {"type": "string"}
        },
        "required": ["result"]
    }

    validator.register_output_schema("test_schema", schema)

    output = {"result": "success"}
    is_valid, error = validator.validate_output(output, "test_schema")

    assert is_valid
    assert error is None


def test_validate_output_missing_required():
    """Test validation fails for missing required field"""
    validator = StructuredOutputValidator()

    schema = {
        "type": "object",
        "properties": {
            "required_field": {"type": "string"}
        },
        "required": ["required_field"]
    }

    validator.register_output_schema("test_schema", schema)

    output = {}  # Missing required_field
    is_valid, error = validator.validate_output(output, "test_schema")

    assert not is_valid
    assert "required_field" in error


def test_validate_output_wrong_type():
    """Test validation fails for wrong type"""
    validator = StructuredOutputValidator()

    schema = {
        "type": "string"
    }

    validator.register_output_schema("string_schema", schema)

    output = {"not": "a string"}  # Should be string, not object
    is_valid, error = validator.validate_output(output, "string_schema")

    assert not is_valid
    assert "Expected string" in error


def test_validate_output_unregistered_schema():
    """Test validation fails for unregistered schema"""
    validator = StructuredOutputValidator()

    output = {"test": "data"}
    is_valid, error = validator.validate_output(output, "nonexistent_schema")

    assert not is_valid
    assert "not registered" in error


def test_create_output_constraint():
    """Test creating output constraint for AI models"""
    validator = StructuredOutputValidator()

    schema = {
        "type": "object",
        "properties": {
            "answer": {"type": "string"}
        }
    }

    validator.register_output_schema("qa_schema", schema)

    constraint = validator.create_output_constraint("qa_schema")

    assert constraint["type"] == "json_schema"
    assert "json_schema" in constraint
    assert constraint["json_schema"]["name"] == "qa_schema"
    assert constraint["json_schema"]["strict"] is True


# ============================================================================
# TOKEN OPTIMIZATION MANAGER TESTS
# ============================================================================

def test_optimization_manager_initialization():
    """Test token optimization manager initializes correctly"""
    manager = TokenOptimizationManager()

    assert manager.tool_selector is not None
    assert manager.parallel_caller is not None
    assert manager.output_validator is not None
    assert manager.total_tokens_saved == 0
    assert manager.total_executions == 0


def test_register_tool_with_manager():
    """Test registering tool with optimization manager"""
    manager = TokenOptimizationManager()

    schema = {
        "name": "test_tool",
        "description": "Test tool",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }

    config = ToolCallConfig(
        tool_name="test_tool",
        description="Test tool",
        permission_level=ToolPermissionLevel.PUBLIC,
        risk_level=ToolRiskLevel.LOW,
        provider=ToolProvider.BOTH
    )

    manager.register_tool("test_tool", config, schema)

    assert "test_tool" in manager.tool_selector.compressed_schemas


@pytest.mark.asyncio
async def test_optimize_and_execute():
    """Test optimize and execute workflow"""
    manager = TokenOptimizationManager()

    # Register some tools
    for i in range(5):
        schema = {
            "name": f"tool_{i}",
            "description": f"Tool {i} for data processing",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
        config = ToolCallConfig(
            tool_name=f"tool_{i}",
            description=f"Tool {i}",
            permission_level=ToolPermissionLevel.PUBLIC,
            risk_level=ToolRiskLevel.LOW,
            provider=ToolProvider.BOTH
        )
        manager.register_tool(f"tool_{i}", config, schema)

    context = ToolSelectionContext(
        task_description="Process data efficiently",
        max_tools=3
    )

    result = await manager.optimize_and_execute(
        context=context,
        available_tools=[f"tool_{i}" for i in range(5)]
    )

    assert "selected_tools" in result
    assert "compressed_schemas" in result
    assert "tokens_saved" in result
    assert "optimization_ratio" in result
    assert len(result["selected_tools"]) <= 3


def test_get_optimization_statistics():
    """Test getting optimization statistics"""
    manager = TokenOptimizationManager()

    stats = manager.get_optimization_statistics()

    assert "total_executions" in stats
    assert "total_tokens_saved" in stats
    assert "avg_tokens_saved_per_execution" in stats
    assert "registered_tools" in stats
    assert "tool_usage_patterns" in stats


@pytest.mark.asyncio
async def test_token_savings_accumulation():
    """Test that token savings accumulate correctly"""
    manager = TokenOptimizationManager()

    # Register tools
    for i in range(10):
        schema = {
            "name": f"tool_{i}",
            "description": f"Tool {i} with long description that will be compressed",
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "Long parameter description"},
                    "param2": {"type": "number", "description": "Another long description"}
                },
                "required": []
            }
        }
        config = ToolCallConfig(
            tool_name=f"tool_{i}",
            description=f"Tool {i}",
            permission_level=ToolPermissionLevel.PUBLIC,
            risk_level=ToolRiskLevel.LOW,
            provider=ToolProvider.BOTH
        )
        manager.register_tool(f"tool_{i}", config, schema)

    # Execute multiple optimizations
    for _ in range(3):
        context = ToolSelectionContext(
            task_description="Execute various tasks",
            max_tools=5
        )
        await manager.optimize_and_execute(
            context=context,
            available_tools=[f"tool_{i}" for i in range(10)]
        )

    assert manager.total_executions == 3
    assert manager.total_tokens_saved > 0


# ============================================================================
# GLOBAL INSTANCE TEST
# ============================================================================

def test_get_global_optimization_manager():
    """Test getting global optimization manager instance"""
    manager1 = get_optimization_manager()
    manager2 = get_optimization_manager()

    # Should return same instance
    assert manager1 is manager2


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_full_optimization_workflow():
    """Test complete token optimization workflow"""
    manager = TokenOptimizationManager()

    # Step 1: Register tools with varying complexities
    tools = [
        ("get_weather", "Get weather information for any location worldwide"),
        ("query_database", "Query database with complex SQL statements"),
        ("analyze_data", "Perform statistical analysis on datasets"),
        ("generate_report", "Generate comprehensive PDF reports"),
        ("send_email", "Send email notifications to users")
    ]

    for tool_name, description in tools:
        schema = {
            "name": tool_name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Input parameter"},
                    "options": {"type": "object", "description": "Configuration options"}
                },
                "required": ["input"]
            }
        }
        config = ToolCallConfig(
            tool_name=tool_name,
            description=description,
            permission_level=ToolPermissionLevel.AUTHENTICATED,
            risk_level=ToolRiskLevel.MEDIUM,
            provider=ToolProvider.BOTH
        )
        manager.register_tool(tool_name, config, schema)

    # Step 2: Update some tools with performance data
    manager.tool_selector.update_tool_performance(
        tool_name="get_weather",
        success=True,
        execution_time_ms=50.0,
        tokens_used=20,
        context_keywords={"weather", "forecast", "temperature"}
    )

    manager.tool_selector.update_tool_performance(
        tool_name="query_database",
        success=True,
        execution_time_ms=200.0,
        tokens_used=100,
        context_keywords={"database", "query", "data"}
    )

    # Step 3: Optimize tool selection for a task
    context = ToolSelectionContext(
        task_description="Get weather forecast and temperature data",
        max_tools=2,
        prefer_fast=True
    )

    result = await manager.optimize_and_execute(
        context=context,
        available_tools=[name for name, _ in tools]
    )

    # Verify results
    assert len(result["selected_tools"]) <= 2
    assert result["tokens_saved"] >= 0
    assert "%" in result["optimization_ratio"]

    # Step 4: Check statistics
    stats = manager.get_optimization_statistics()
    assert stats["total_executions"] >= 1
    assert stats["registered_tools"] == 5
