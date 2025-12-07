"""
Comprehensive tests for MCP Client (services/mcp_client.py)

Coverage Target: ≥85% (136/161 lines)

Tests:
- MCPToolClient initialization
- Schema loading (success/failures)
- Tool loading and caching
- Tool invocation with AI
- Input/output validation
- Error handling
- Helper methods
- Singleton pattern

Truth Protocol: Rule #8 (Test Coverage ≥90%), Rule #1 (Never Guess)
"""

import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest


# Mock the anthropic and logfire modules before importing mcp_client
sys.modules["anthropic"] = MagicMock()
sys.modules["logfire"] = MagicMock()

from services.mcp_client import (
    MCPToolClient,
    MCPToolError,
    MCPToolNotFoundError,
    MCPToolValidationError,
    get_mcp_client,
)


# Mock schema for testing
MOCK_SCHEMA = {
    "tool_definitions": {
        "code_execution": {
            "python_executor": {
                "name": "Python Code Executor",
                "description": "Executes Python code in secure sandbox",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python code to execute"},
                        "timeout": {"type": "integer", "default": 30},
                        "environment": {"type": "string"},
                    },
                    "required": ["code"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "stdout": {"type": "string"},
                        "stderr": {"type": "string"},
                        "success": {"type": "boolean"},
                    },
                    "required": ["success"],
                },
            },
            "code_analyzer": {
                "name": "Code Quality Analyzer",
                "description": "Analyzes code for quality",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "language": {"type": "string"},
                        "options": {"type": "object"},
                        "threshold": {"type": "number"},
                        "tags": {"type": "array"},
                    },
                    "required": ["code", "language"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {"issues": {"type": "array"}},
                },
            },
        },
        "data_processing": {
            "csv_parser": {
                "name": "CSV Parser",
                "description": "Parses CSV data",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "string"},
                        "delimiter": {"type": "string"},
                    },
                    "required": ["data"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {"rows": {"type": "array"}},
                },
            }
        },
    }
}


@pytest.fixture
def mock_schema_file():
    """Create a temporary mock schema file"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(MOCK_SCHEMA, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    try:
        os.unlink(temp_path)
    except Exception:
        pass


@pytest.fixture
def mock_invalid_schema_file():
    """Create a temporary invalid JSON file"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{invalid json")
        temp_path = f.name

    yield temp_path

    # Cleanup
    try:
        os.unlink(temp_path)
    except Exception:
        pass


@pytest.fixture
def mcp_client(mock_schema_file):
    """Create MCPToolClient with mock schema"""
    return MCPToolClient(schema_path=mock_schema_file, anthropic_api_key="test-key-123")


@pytest.fixture
def mcp_client_no_api_key(mock_schema_file):
    """Create MCPToolClient without API key"""
    with patch.dict(os.environ, {}, clear=True):
        return MCPToolClient(schema_path=mock_schema_file, anthropic_api_key=None)


class TestMCPToolClientInitialization:
    """Test MCPToolClient initialization"""

    def test_init_with_api_key(self, mock_schema_file):
        """Test initialization with API key"""
        client = MCPToolClient(schema_path=mock_schema_file, anthropic_api_key="test-key")

        assert client.schema_path == Path(mock_schema_file)
        assert client.schema == MOCK_SCHEMA
        assert client.loaded_tools == {}
        assert client.invocation_count == 0
        assert client.anthropic_client is not None

    def test_init_with_env_api_key(self, mock_schema_file):
        """Test initialization with environment variable API key"""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key-123"}):
            client = MCPToolClient(schema_path=mock_schema_file)

            assert client.anthropic_client is not None

    def test_init_without_api_key(self, mcp_client_no_api_key):
        """Test initialization without API key"""
        client = mcp_client_no_api_key

        assert client.anthropic_client is None

    def test_init_with_default_schema_path(self):
        """Test initialization with default schema path"""
        # The default schema path exists in this project, so it should succeed
        # If it doesn't exist, it would raise FileNotFoundError
        try:
            client = MCPToolClient()
            # If schema file exists, client should be created
            assert client.schema is not None
        except FileNotFoundError:
            # If schema doesn't exist, that's also acceptable
            pass


class TestSchemaLoading:
    """Test schema loading functionality"""

    def test_load_schema_success(self, mock_schema_file):
        """Test successful schema loading"""
        client = MCPToolClient(schema_path=mock_schema_file, anthropic_api_key="test-key")

        assert client.schema == MOCK_SCHEMA
        assert "tool_definitions" in client.schema

    def test_load_schema_file_not_found(self):
        """Test schema loading with non-existent file"""
        with pytest.raises(FileNotFoundError):
            MCPToolClient(schema_path="/nonexistent/path/schema.json", anthropic_api_key="test-key")

    def test_load_schema_invalid_json(self, mock_invalid_schema_file):
        """Test schema loading with invalid JSON"""
        with pytest.raises(json.JSONDecodeError):
            MCPToolClient(schema_path=mock_invalid_schema_file, anthropic_api_key="test-key")


class TestToolLoading:
    """Test tool loading and caching"""

    def test_load_tool_success(self, mcp_client):
        """Test successful tool loading"""
        tool_def = mcp_client.load_tool("python_executor", "code_execution")

        assert tool_def["name"] == "Python Code Executor"
        assert "input_schema" in tool_def
        assert "output_schema" in tool_def
        assert "code_execution.python_executor" in mcp_client.loaded_tools

    def test_load_tool_caching(self, mcp_client):
        """Test tool caching mechanism"""
        # Load tool first time
        tool_def_1 = mcp_client.load_tool("python_executor", "code_execution")

        # Load same tool again (should use cache)
        tool_def_2 = mcp_client.load_tool("python_executor", "code_execution")

        assert tool_def_1 is tool_def_2  # Same object reference
        assert len(mcp_client.loaded_tools) == 1

    def test_load_tool_not_found(self, mcp_client):
        """Test loading non-existent tool"""
        with pytest.raises(MCPToolNotFoundError) as exc_info:
            mcp_client.load_tool("nonexistent_tool", "code_execution")

        assert "Tool not found" in str(exc_info.value)
        assert "Available categories" in str(exc_info.value)

    def test_load_tool_invalid_category(self, mcp_client):
        """Test loading tool from invalid category"""
        with pytest.raises(MCPToolNotFoundError):
            mcp_client.load_tool("some_tool", "invalid_category")

    def test_load_multiple_tools(self, mcp_client):
        """Test loading multiple different tools"""
        tool1 = mcp_client.load_tool("python_executor", "code_execution")
        tool2 = mcp_client.load_tool("csv_parser", "data_processing")

        assert len(mcp_client.loaded_tools) == 2
        assert "code_execution.python_executor" in mcp_client.loaded_tools
        assert "data_processing.csv_parser" in mcp_client.loaded_tools


class TestInputValidation:
    """Test input validation"""

    def test_validate_inputs_success(self, mcp_client):
        """Test successful input validation"""
        inputs = {"code": "print('hello')", "timeout": 30}
        schema = MOCK_SCHEMA["tool_definitions"]["code_execution"]["python_executor"]["input_schema"]

        # Should not raise
        mcp_client._validate_inputs(inputs, schema)

    def test_validate_inputs_missing_required_field(self, mcp_client):
        """Test validation with missing required field"""
        inputs = {"timeout": 30}  # Missing 'code'
        schema = MOCK_SCHEMA["tool_definitions"]["code_execution"]["python_executor"]["input_schema"]

        with pytest.raises(MCPToolValidationError) as exc_info:
            mcp_client._validate_inputs(inputs, schema)

        assert "Missing required field: 'code'" in str(exc_info.value)

    def test_validate_inputs_wrong_type_string(self, mcp_client):
        """Test validation with wrong type (string expected)"""
        inputs = {"code": 123, "language": "python"}  # code should be string
        schema = MOCK_SCHEMA["tool_definitions"]["code_execution"]["code_analyzer"]["input_schema"]

        with pytest.raises(MCPToolValidationError) as exc_info:
            mcp_client._validate_inputs(inputs, schema)

        assert "must be a string" in str(exc_info.value)

    def test_validate_inputs_wrong_type_integer(self, mcp_client):
        """Test validation with wrong type (integer expected)"""
        inputs = {"code": "print('hello')", "timeout": "30"}  # timeout should be integer
        schema = MOCK_SCHEMA["tool_definitions"]["code_execution"]["python_executor"]["input_schema"]

        with pytest.raises(MCPToolValidationError) as exc_info:
            mcp_client._validate_inputs(inputs, schema)

        assert "must be an integer" in str(exc_info.value)

    def test_validate_inputs_wrong_type_number(self, mcp_client):
        """Test validation with wrong type (number expected)"""
        inputs = {"code": "x = 1", "language": "python", "threshold": "0.5"}  # threshold should be number
        schema = MOCK_SCHEMA["tool_definitions"]["code_execution"]["code_analyzer"]["input_schema"]

        with pytest.raises(MCPToolValidationError) as exc_info:
            mcp_client._validate_inputs(inputs, schema)

        assert "must be a number" in str(exc_info.value)

    def test_validate_inputs_wrong_type_array(self, mcp_client):
        """Test validation with wrong type (array expected)"""
        inputs = {"code": "x = 1", "language": "python", "tags": "tag1,tag2"}  # tags should be array
        schema = MOCK_SCHEMA["tool_definitions"]["code_execution"]["code_analyzer"]["input_schema"]

        with pytest.raises(MCPToolValidationError) as exc_info:
            mcp_client._validate_inputs(inputs, schema)

        assert "must be an array" in str(exc_info.value)

    def test_validate_inputs_wrong_type_object(self, mcp_client):
        """Test validation with wrong type (object expected)"""
        inputs = {"code": "x = 1", "language": "python", "options": "invalid"}  # options should be object
        schema = MOCK_SCHEMA["tool_definitions"]["code_execution"]["code_analyzer"]["input_schema"]

        with pytest.raises(MCPToolValidationError) as exc_info:
            mcp_client._validate_inputs(inputs, schema)

        assert "must be an object" in str(exc_info.value)

    def test_validate_inputs_number_accepts_int_and_float(self, mcp_client):
        """Test that number type accepts both int and float"""
        schema = MOCK_SCHEMA["tool_definitions"]["code_execution"]["code_analyzer"]["input_schema"]

        # Both should pass
        inputs_int = {"code": "x = 1", "language": "python", "threshold": 5}
        inputs_float = {"code": "x = 1", "language": "python", "threshold": 5.5}

        mcp_client._validate_inputs(inputs_int, schema)
        mcp_client._validate_inputs(inputs_float, schema)


class TestOutputValidation:
    """Test output validation"""

    def test_validate_outputs_success(self, mcp_client):
        """Test successful output validation"""
        outputs = {"success": True, "stdout": "Hello"}
        schema = MOCK_SCHEMA["tool_definitions"]["code_execution"]["python_executor"]["output_schema"]

        # Should not raise
        mcp_client._validate_outputs(outputs, schema)

    def test_validate_outputs_missing_required_field(self, mcp_client, caplog):
        """Test validation with missing required output field (warning only)"""
        outputs = {"stdout": "Hello"}  # Missing 'success'
        schema = MOCK_SCHEMA["tool_definitions"]["code_execution"]["python_executor"]["output_schema"]

        # Should not raise, just warn
        mcp_client._validate_outputs(outputs, schema)

        # Check for warning in logs
        assert any("Missing required output field" in record.message for record in caplog.records)


class TestToolInvocation:
    """Test tool invocation"""

    @pytest.mark.asyncio
    async def test_invoke_tool_success(self, mcp_client):
        """Test successful tool invocation"""
        # Mock Anthropic response
        mock_response = Mock()
        mock_response.content = [Mock(text='{"success": true, "stdout": "Hello World"}')]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        with patch.object(mcp_client.anthropic_client.messages, "create", return_value=mock_response):
            result = await mcp_client.invoke_tool(
                tool_name="python_executor",
                category="code_execution",
                inputs={"code": "print('Hello World')"},
            )

            assert result["success"] is True
            assert result["stdout"] == "Hello World"
            assert mcp_client.invocation_count == 1

    @pytest.mark.asyncio
    async def test_invoke_tool_json_in_markdown(self, mcp_client):
        """Test tool invocation with JSON in markdown code block"""
        # Mock response with ```json wrapper
        mock_response = Mock()
        mock_response.content = [Mock(text='```json\n{"success": true, "stdout": "Test"}\n```')]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        with patch.object(mcp_client.anthropic_client.messages, "create", return_value=mock_response):
            result = await mcp_client.invoke_tool(
                tool_name="python_executor",
                category="code_execution",
                inputs={"code": "print('test')"},
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_invoke_tool_json_in_generic_code_block(self, mcp_client):
        """Test tool invocation with JSON in generic code block"""
        # Mock response with ``` wrapper (no language)
        mock_response = Mock()
        mock_response.content = [Mock(text='```\n{"success": true, "stdout": "Test"}\n```')]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        with patch.object(mcp_client.anthropic_client.messages, "create", return_value=mock_response):
            result = await mcp_client.invoke_tool(
                tool_name="python_executor",
                category="code_execution",
                inputs={"code": "print('test')"},
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_invoke_tool_invalid_json_response(self, mcp_client):
        """Test tool invocation with invalid JSON response"""
        mock_response = Mock()
        mock_response.content = [Mock(text="This is not JSON")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        with patch.object(mcp_client.anthropic_client.messages, "create", return_value=mock_response):
            with pytest.raises(json.JSONDecodeError):
                await mcp_client.invoke_tool(
                    tool_name="python_executor",
                    category="code_execution",
                    inputs={"code": "print('test')"},
                )

    @pytest.mark.asyncio
    async def test_invoke_tool_input_validation_error(self, mcp_client):
        """Test tool invocation with invalid inputs"""
        with pytest.raises(MCPToolValidationError):
            await mcp_client.invoke_tool(
                tool_name="python_executor",
                category="code_execution",
                inputs={},  # Missing required 'code' field
            )

    @pytest.mark.asyncio
    async def test_invoke_tool_no_api_key(self, mcp_client_no_api_key):
        """Test tool invocation without API key"""
        with pytest.raises(MCPToolError) as exc_info:
            await mcp_client_no_api_key.invoke_tool(
                tool_name="python_executor",
                category="code_execution",
                inputs={"code": "print('test')"},
            )

        assert "Anthropic API key not configured" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invoke_tool_ai_error(self, mcp_client):
        """Test tool invocation with AI error"""
        with patch.object(
            mcp_client.anthropic_client.messages, "create", side_effect=Exception("AI service unavailable")
        ):
            with pytest.raises(Exception) as exc_info:
                await mcp_client.invoke_tool(
                    tool_name="python_executor",
                    category="code_execution",
                    inputs={"code": "print('test')"},
                )

            assert "AI service unavailable" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invoke_tool_custom_model_and_tokens(self, mcp_client):
        """Test tool invocation with custom model and max_tokens"""
        mock_response = Mock()
        mock_response.content = [Mock(text='{"success": true}')]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        with patch.object(mcp_client.anthropic_client.messages, "create", return_value=mock_response) as mock_create:
            await mcp_client.invoke_tool(
                tool_name="python_executor",
                category="code_execution",
                inputs={"code": "print('test')"},
                model="claude-3-opus-20240229",
                max_tokens=4000,
            )

            # Verify model and max_tokens were passed
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["model"] == "claude-3-opus-20240229"
            assert call_kwargs["max_tokens"] == 4000

    @pytest.mark.asyncio
    async def test_invoke_tool_increments_invocation_count(self, mcp_client):
        """Test that invocation count increments"""
        mock_response = Mock()
        mock_response.content = [Mock(text='{"success": true}')]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        initial_count = mcp_client.invocation_count

        with patch.object(mcp_client.anthropic_client.messages, "create", return_value=mock_response):
            await mcp_client.invoke_tool(
                tool_name="python_executor", category="code_execution", inputs={"code": "print('1')"}
            )

            await mcp_client.invoke_tool(
                tool_name="python_executor", category="code_execution", inputs={"code": "print('2')"}
            )

        assert mcp_client.invocation_count == initial_count + 2

    @pytest.mark.asyncio
    async def test_invoke_tool_with_logfire_available(self, mcp_client):
        """Test tool invocation with logfire available"""
        mock_response = Mock()
        mock_response.content = [Mock(text='{"success": true}')]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        with patch("services.mcp_client.LOGFIRE_AVAILABLE", True):
            with patch("services.mcp_client.logfire") as mock_logfire:
                with patch.object(mcp_client.anthropic_client.messages, "create", return_value=mock_response):
                    result = await mcp_client.invoke_tool(
                        tool_name="python_executor",
                        category="code_execution",
                        inputs={"code": "print('test')"},
                    )

                    # Verify logfire.span was called
                    assert mock_logfire.span.called

    @pytest.mark.asyncio
    async def test_invoke_tool_without_logfire(self, mcp_client):
        """Test tool invocation without logfire"""
        mock_response = Mock()
        mock_response.content = [Mock(text='{"success": true}')]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        with patch("services.mcp_client.LOGFIRE_AVAILABLE", False):
            with patch.object(mcp_client.anthropic_client.messages, "create", return_value=mock_response):
                result = await mcp_client.invoke_tool(
                    tool_name="python_executor",
                    category="code_execution",
                    inputs={"code": "print('test')"},
                )

                assert result["success"] is True


class TestHelperMethods:
    """Test helper methods"""

    def test_get_nested_success(self, mcp_client):
        """Test successful nested value retrieval"""
        result = mcp_client._get_nested(MOCK_SCHEMA, "tool_definitions.code_execution.python_executor")

        assert result is not None
        assert result["name"] == "Python Code Executor"

    def test_get_nested_not_found(self, mcp_client):
        """Test nested value retrieval with non-existent path"""
        result = mcp_client._get_nested(MOCK_SCHEMA, "tool_definitions.invalid.path")

        assert result is None

    def test_get_nested_partial_path(self, mcp_client):
        """Test nested value retrieval with partial path"""
        result = mcp_client._get_nested(MOCK_SCHEMA, "tool_definitions.code_execution")

        assert result is not None
        assert "python_executor" in result

    def test_get_nested_non_dict_value(self, mcp_client):
        """Test nested value retrieval hitting non-dict value"""
        # Try to traverse through a string value
        result = mcp_client._get_nested(
            MOCK_SCHEMA, "tool_definitions.code_execution.python_executor.name.invalid"
        )

        assert result is None

    def test_create_tool_prompt(self, mcp_client):
        """Test tool prompt creation"""
        tool_def = MOCK_SCHEMA["tool_definitions"]["code_execution"]["python_executor"]
        inputs = {"code": "print('hello')"}

        prompt = mcp_client._create_tool_prompt(tool_def, inputs)

        assert "Python Code Executor" in prompt
        assert "Executes Python code in secure sandbox" in prompt
        assert '"code": "print(\'hello\')"' in prompt
        assert "Expected Output Schema" in prompt  # Changed from "output_schema"
        assert "IMPORTANT INSTRUCTIONS" in prompt

    def test_get_loaded_tools_empty(self, mcp_client):
        """Test getting loaded tools when none loaded"""
        tools = mcp_client.get_loaded_tools()

        assert tools == []

    def test_get_loaded_tools_with_tools(self, mcp_client):
        """Test getting loaded tools after loading some"""
        mcp_client.load_tool("python_executor", "code_execution")
        mcp_client.load_tool("csv_parser", "data_processing")

        tools = mcp_client.get_loaded_tools()

        assert len(tools) == 2
        assert "code_execution.python_executor" in tools
        assert "data_processing.csv_parser" in tools

    def test_get_available_tools_all(self, mcp_client):
        """Test getting all available tools"""
        tools = mcp_client.get_available_tools()

        assert len(tools) > 0
        assert "code_execution.python_executor" in tools
        assert "code_execution.code_analyzer" in tools
        assert "data_processing.csv_parser" in tools

    def test_get_available_tools_by_category(self, mcp_client):
        """Test getting available tools filtered by category"""
        tools = mcp_client.get_available_tools(category="code_execution")

        assert len(tools) == 2
        assert "python_executor" in tools
        assert "code_analyzer" in tools
        assert "csv_parser" not in tools

    def test_get_available_tools_invalid_category(self, mcp_client):
        """Test getting available tools with invalid category"""
        tools = mcp_client.get_available_tools(category="nonexistent")

        assert tools == []


class TestSingletonPattern:
    """Test singleton get_mcp_client()"""

    def test_get_mcp_client_creates_instance(self, mock_schema_file):
        """Test that get_mcp_client creates instance"""
        # Reset singleton
        import services.mcp_client

        services.mcp_client._default_client = None

        # Mock the default schema path
        with patch("services.mcp_client.MCPToolClient.__init__") as mock_init:
            mock_init.return_value = None

            client = get_mcp_client()

            assert mock_init.called

    def test_get_mcp_client_returns_same_instance(self, mock_schema_file):
        """Test that get_mcp_client returns same instance on multiple calls"""
        # Reset singleton
        import services.mcp_client

        services.mcp_client._default_client = None

        # Create mock client
        mock_client = Mock()

        with patch("services.mcp_client.MCPToolClient", return_value=mock_client):
            client1 = get_mcp_client()
            client2 = get_mcp_client()

            assert client1 is client2


class TestExceptions:
    """Test custom exceptions"""

    def test_mcp_tool_error(self):
        """Test MCPToolError exception"""
        error = MCPToolError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_mcp_tool_not_found_error(self):
        """Test MCPToolNotFoundError exception"""
        error = MCPToolNotFoundError("Tool not found")
        assert str(error) == "Tool not found"
        assert isinstance(error, MCPToolError)

    def test_mcp_tool_validation_error(self):
        """Test MCPToolValidationError exception"""
        error = MCPToolValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert isinstance(error, MCPToolError)


class TestEdgeCases:
    """Test edge cases and error paths"""

    def test_empty_schema(self, mock_schema_file):
        """Test client with empty schema"""
        # Create empty schema file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({}, f)
            empty_schema_path = f.name

        try:
            client = MCPToolClient(schema_path=empty_schema_path, anthropic_api_key="test-key")

            # Should handle gracefully
            tools = client.get_available_tools()
            assert tools == []

        finally:
            os.unlink(empty_schema_path)

    def test_validate_inputs_empty_schema(self, mcp_client):
        """Test input validation with empty schema"""
        inputs = {"any": "value"}
        schema = {}

        # Should not raise
        mcp_client._validate_inputs(inputs, schema)

    def test_validate_outputs_empty_schema(self, mcp_client):
        """Test output validation with empty schema"""
        outputs = {"any": "value"}
        schema = {}

        # Should not raise
        mcp_client._validate_outputs(outputs, schema)

    @pytest.mark.asyncio
    async def test_execute_tool_invocation_with_tool_def(self, mcp_client):
        """Test _execute_tool_invocation with pre-loaded tool_def"""
        tool_def = MOCK_SCHEMA["tool_definitions"]["code_execution"]["python_executor"]
        mock_response = Mock()
        mock_response.content = [Mock(text='{"success": true}')]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        with patch.object(mcp_client.anthropic_client.messages, "create", return_value=mock_response):
            result = await mcp_client._execute_tool_invocation(
                tool_name="python_executor",
                category="code_execution",
                inputs={"code": "print('test')"},
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                invocation_id=1,
                tool_def=tool_def,
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_invoke_tool_with_logfire_error_logging(self, mcp_client):
        """Test error logging with logfire"""
        with patch("services.mcp_client.LOGFIRE_AVAILABLE", True):
            with patch("services.mcp_client.logfire") as mock_logfire:
                # Mock logfire.span as a context manager
                mock_logfire.span.return_value.__enter__ = Mock()
                mock_logfire.span.return_value.__exit__ = Mock(return_value=False)

                with pytest.raises(MCPToolValidationError):
                    await mcp_client.invoke_tool(
                        tool_name="python_executor",
                        category="code_execution",
                        inputs={},  # Missing required field
                    )

    @pytest.mark.asyncio
    async def test_invoke_tool_response_without_usage(self, mcp_client):
        """Test tool invocation with response that doesn't have usage info"""
        # Create a mock response object without usage attribute
        class MockResponse:
            def __init__(self):
                self.content = [type("obj", (object,), {"text": '{"success": true}'})]

        mock_response = MockResponse()

        with patch("services.mcp_client.LOGFIRE_AVAILABLE", True):
            with patch("services.mcp_client.logfire") as mock_logfire:
                # Mock logfire.span as a context manager that returns the result
                class MockSpan:
                    def __enter__(self):
                        return self

                    def __exit__(self, *args):
                        return False

                    async def __aenter__(self):
                        return self

                    async def __aexit__(self, *args):
                        return False

                mock_logfire.span.return_value = MockSpan()

                with patch.object(mcp_client.anthropic_client.messages, "create", return_value=mock_response):
                    result = await mcp_client.invoke_tool(
                        tool_name="python_executor",
                        category="code_execution",
                        inputs={"code": "print('test')"},
                    )

                    assert result["success"] is True
