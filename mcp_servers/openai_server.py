"""
OpenAI MCP Server for DevSkyy Platform
======================================

Model Context Protocol (MCP) server implementation specifically optimized
for OpenAI's models (GPT-4o, GPT-4o-mini, o1-preview).

This server exposes DevSkyy's AI capabilities as MCP tools that can be used
by OpenAI's API, Claude Desktop, or any MCP-compatible client.

Features:
- OpenAI model integration (GPT-4o, GPT-4o-mini, o1-preview)
- Function calling and structured outputs
- Vision capabilities (GPT-4o, GPT-4o-mini)
- Code generation and analysis
- DevSkyy agent orchestration
- WordPress automation
- E-commerce tools

Architecture:
- Built on FastMCP (MCP Python SDK)
- Integrates with DevSkyy's LLM registry
- Supports all OpenAI capabilities
- Enterprise-grade error handling

Version: 1.0.0
Python: 3.11+
Framework: FastMCP

Installation:
    pip install fastmcp httpx pydantic openai python-jose[cryptography]

Usage:
    # Run the server
    python server.py

    # Or use with Claude Desktop/MCP clients
    {
      "mcpServers": {
        "devskyy-openai": {
          "command": "python",
          "args": ["/path/to/server.py"],
          "env": {
            "OPENAI_API_KEY": "your-openai-key-here",
            "DEVSKYY_API_URL": "https://api.devskyy.com",
            "DEVSKYY_API_KEY": "your-devskyy-key-here"
          }
        }
      }
    }
"""

import json
import os
from enum import Enum
from typing import Any, Literal

try:
    import httpx
    from mcp.server.fastmcp import FastMCP
    from pydantic import BaseModel, ConfigDict, Field
except ImportError as e:
    print(f"❌ Missing required package: {e}")
    print("Install with: pip install fastmcp httpx pydantic openai python-jose[cryptography]")
    exit(1)

# =============================================================================
# Configuration
# =============================================================================

API_BASE_URL = os.getenv("DEVSKYY_API_URL", "http://localhost:8000")
API_KEY = os.getenv("DEVSKYY_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CHARACTER_LIMIT = 25000
REQUEST_TIMEOUT = 60.0

# OpenAI-specific settings
OPENAI_MODELS = {
    "gpt-4o": {
        "context_window": 128000,
        "supports_vision": True,
        "supports_function_calling": True,
        "supports_json_mode": True,
        "best_for": ["complex_reasoning", "multimodal", "code", "analysis"],
    },
    "gpt-4o-mini": {
        "context_window": 128000,
        "supports_vision": True,
        "supports_function_calling": True,
        "supports_json_mode": True,
        "best_for": ["simple_tasks", "high_volume", "quick_responses"],
    },
    "o1-preview": {
        "context_window": 128000,
        "supports_vision": False,
        "supports_function_calling": False,
        "supports_json_mode": False,
        "best_for": ["complex_reasoning", "math", "science", "code_review"],
    },
}

DEFAULT_MODEL = "gpt-4o-mini"

# =============================================================================
# Initialize MCP Server
# =============================================================================

mcp = FastMCP(
    "devskyy_openai_mcp", dependencies=["httpx>=0.24.0", "pydantic>=2.5.0", "openai>=1.6.0"]
)

# =============================================================================
# Enums & Models
# =============================================================================


class ResponseFormat(str, Enum):
    """Output format for tool responses."""

    MARKDOWN = "markdown"
    JSON = "json"


class OpenAIModel(str, Enum):
    """Supported OpenAI models."""

    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"
    O1_PREVIEW = "o1-preview"


class TaskType(str, Enum):
    """Task categories for optimal model selection."""

    CODE_GENERATION = "code_generation"
    CODE_ANALYSIS = "code_analysis"
    REASONING = "reasoning"
    MATH = "math"
    VISION = "vision"
    SIMPLE_CHAT = "simple_chat"
    COMPLEX_ANALYSIS = "complex_analysis"
    MULTIMODAL = "multimodal"


# =============================================================================
# Input Models
# =============================================================================


class BaseInput(BaseModel):
    """Base input model for all tools."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' or 'json'"
    )


class OpenAICompletionInput(BaseInput):
    """Input for OpenAI completion requests."""

    prompt: str = Field(
        ..., description="The prompt to send to OpenAI", min_length=1, max_length=50000
    )
    model: OpenAIModel = Field(default=OpenAIModel.GPT4O_MINI, description="OpenAI model to use")
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature (0.0-2.0)"
    )
    max_tokens: int = Field(default=4096, ge=1, le=16384, description="Maximum tokens to generate")
    system_prompt: str | None = Field(
        default=None, description="System prompt for the model", max_length=10000
    )


class CodeGenerationInput(BaseInput):
    """Input for code generation tasks."""

    description: str = Field(
        ..., description="Description of code to generate", min_length=1, max_length=5000
    )
    language: str = Field(
        default="python", description="Programming language (python, javascript, typescript, etc.)"
    )
    context: str | None = Field(
        default=None, description="Additional context or requirements", max_length=5000
    )
    include_tests: bool = Field(default=False, description="Include unit tests")
    include_docs: bool = Field(default=True, description="Include documentation/comments")


class VisionAnalysisInput(BaseInput):
    """Input for vision/image analysis."""

    image_url: str = Field(..., description="URL of image to analyze", max_length=2000)
    prompt: str = Field(..., description="Analysis instructions", min_length=1, max_length=2000)
    detail_level: Literal["low", "high", "auto"] = Field(
        default="auto", description="Image detail level"
    )


class FunctionCallingInput(BaseInput):
    """Input for function calling with OpenAI."""

    prompt: str = Field(..., description="User request", min_length=1, max_length=5000)
    available_functions: list[dict[str, Any]] = Field(
        ..., description="Functions the model can call", min_items=1, max_items=50
    )
    auto_execute: bool = Field(default=False, description="Automatically execute function calls")


class ModelSelectionInput(BaseInput):
    """Input for intelligent model selection."""

    task_description: str = Field(
        ..., description="Description of the task", min_length=1, max_length=1000
    )
    task_type: TaskType | None = Field(default=None, description="Optional task type hint")
    optimize_for: Literal["quality", "speed", "cost"] = Field(
        default="quality", description="Optimization priority"
    )


class DevSkyyAgentInput(BaseInput):
    """Input for DevSkyy agent orchestration."""

    agent_name: str = Field(
        ...,
        description="Agent to invoke (scanner, fixer, theme_builder, etc.)",
        min_length=1,
        max_length=100,
    )
    action: str = Field(..., description="Action to perform", min_length=1, max_length=100)
    parameters: dict[str, Any] = Field(default_factory=dict, description="Action parameters")


# =============================================================================
# Utility Functions
# =============================================================================


async def _make_api_request(
    endpoint: str,
    method: str = "GET",
    data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make authenticated request to DevSkyy API."""
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    url = f"{API_BASE_URL}/api/v1/{endpoint}"

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.request(
                method=method, url=url, headers=headers, json=data, params=params
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return _handle_api_error(e)
    except httpx.TimeoutException:
        return {"error": "Request timed out"}
    except Exception as e:
        return {"error": f"Unexpected error: {type(e).__name__} - {str(e)}"}


def _handle_api_error(e: httpx.HTTPStatusError) -> dict[str, Any]:
    """Convert HTTP errors to user-friendly messages."""
    status = e.response.status_code
    error_messages = {
        400: "Bad request. Check input parameters.",
        401: "Authentication failed. Check DEVSKYY_API_KEY.",
        403: "Permission denied.",
        404: "Resource not found.",
        429: "Rate limit exceeded.",
        500: "API internal error.",
        503: "API temporarily unavailable.",
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
        output.append(f"❌ **Error:** {data['error']}\n")
        if "details" in data:
            output.append(f"**Details:** {data['details']}\n")
        return "\n".join(output)

    for key, value in data.items():
        if isinstance(value, dict):
            output.append(f"### {key.replace('_', ' ').title()}")
            for k, v in value.items():
                output.append(f"- **{k.replace('_', ' ').title()}:** {v}")
        elif isinstance(value, list):
            output.append(f"### {key.replace('_', ' ').title()}")
            for item in value[:10]:
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

    if len(result) > CHARACTER_LIMIT:
        result = result[:CHARACTER_LIMIT] + f"\n\n⚠️ Response truncated to {CHARACTER_LIMIT} chars"

    return result


def _select_optimal_model(task_type: TaskType | None, optimize_for: str) -> str:
    """Select optimal OpenAI model for task."""
    if task_type == TaskType.REASONING or task_type == TaskType.MATH:
        return "o1-preview"

    if task_type == TaskType.VISION or task_type == TaskType.MULTIMODAL:
        return "gpt-4o"

    if task_type == TaskType.COMPLEX_ANALYSIS or task_type == TaskType.CODE_ANALYSIS:
        return "gpt-4o"

    if optimize_for == "cost" or optimize_for == "speed":
        return "gpt-4o-mini"

    if optimize_for == "quality":
        return "gpt-4o"

    return DEFAULT_MODEL


# =============================================================================
# OpenAI-Specific Tools
# =============================================================================


@mcp.tool(
    name="openai_completion",
    annotations={
        "title": "OpenAI Completion",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def openai_completion(params: OpenAICompletionInput) -> str:
    """Generate text using OpenAI models.

    Supports GPT-4o, GPT-4o-mini, and o1-preview models with full
    customization of temperature, max tokens, and system prompts.

    Args:
        params: Completion configuration containing:
            - prompt: User prompt
            - model: OpenAI model to use
            - temperature: Sampling temperature (0.0-2.0)
            - max_tokens: Maximum tokens to generate
            - system_prompt: Optional system instructions
            - response_format: Output format (markdown/json)

    Returns:
        str: Generated text with metadata

    Example:
        >>> openai_completion({
        ...     "prompt": "Explain quantum computing",
        ...     "model": "gpt-4o",
        ...     "temperature": 0.7,
        ...     "max_tokens": 500
        ... })
    """
    data = await _make_api_request(
        "ai/openai/completion",
        method="POST",
        data={
            "prompt": params.prompt,
            "model": params.model.value,
            "temperature": params.temperature,
            "max_tokens": params.max_tokens,
            "system_prompt": params.system_prompt,
        },
    )
    return _format_response(data, params.response_format, "OpenAI Completion")


@mcp.tool(
    name="openai_code_generation",
    annotations={
        "title": "OpenAI Code Generator",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def code_generation(params: CodeGenerationInput) -> str:
    """Generate code using OpenAI's code-optimized models.

    Uses GPT-4o or GPT-4o-mini for code generation with proper syntax,
    documentation, and optional tests.

    Args:
        params: Code generation configuration containing:
            - description: What the code should do
            - language: Programming language
            - context: Additional requirements
            - include_tests: Generate unit tests
            - include_docs: Include documentation
            - response_format: Output format (markdown/json)

    Returns:
        str: Generated code with documentation

    Example:
        >>> code_generation({
        ...     "description": "FastAPI endpoint for user login",
        ...     "language": "python",
        ...     "include_tests": True
        ... })
    """
    data = await _make_api_request(
        "ai/openai/code-generation",
        method="POST",
        data={
            "description": params.description,
            "language": params.language,
            "context": params.context,
            "include_tests": params.include_tests,
            "include_docs": params.include_docs,
        },
    )
    return _format_response(data, params.response_format, "Code Generation")


@mcp.tool(
    name="openai_vision_analysis",
    annotations={
        "title": "OpenAI Vision Analysis",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def vision_analysis(params: VisionAnalysisInput) -> str:
    """Analyze images using GPT-4o or GPT-4o-mini vision capabilities.

    Supports image understanding, object detection, text extraction,
    and visual reasoning.

    Args:
        params: Vision analysis configuration containing:
            - image_url: URL of image to analyze
            - prompt: Analysis instructions
            - detail_level: Image detail (low/high/auto)
            - response_format: Output format (markdown/json)

    Returns:
        str: Image analysis results

    Example:
        >>> vision_analysis({
        ...     "image_url": "https://example.com/product.jpg",
        ...     "prompt": "Describe the product and suggest categories",
        ...     "detail_level": "high"
        ... })
    """
    data = await _make_api_request(
        "ai/openai/vision",
        method="POST",
        data={
            "image_url": params.image_url,
            "prompt": params.prompt,
            "detail_level": params.detail_level,
        },
    )
    return _format_response(data, params.response_format, "Vision Analysis")


@mcp.tool(
    name="openai_function_calling",
    annotations={
        "title": "OpenAI Function Calling",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def function_calling(params: FunctionCallingInput) -> str:
    """Use OpenAI's function calling to invoke structured actions.

    GPT-4o and GPT-4o-mini can intelligently call functions based on
    user requests, enabling structured data extraction and actions.

    Args:
        params: Function calling configuration containing:
            - prompt: User request
            - available_functions: Functions the model can call
            - auto_execute: Execute function calls automatically
            - response_format: Output format (markdown/json)

    Returns:
        str: Function call results

    Example:
        >>> function_calling({
        ...     "prompt": "Get weather in San Francisco",
        ...     "available_functions": [{
        ...         "name": "get_weather",
        ...         "description": "Get weather for a city",
        ...         "parameters": {"city": "string"}
        ...     }],
        ...     "auto_execute": True
        ... })
    """
    data = await _make_api_request(
        "ai/openai/function-calling",
        method="POST",
        data={
            "prompt": params.prompt,
            "functions": params.available_functions,
            "auto_execute": params.auto_execute,
        },
    )
    return _format_response(data, params.response_format, "Function Calling")


@mcp.tool(
    name="openai_model_selector",
    annotations={
        "title": "OpenAI Model Selector",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def model_selector(params: ModelSelectionInput) -> str:
    """Intelligently select the optimal OpenAI model for a task.

    Analyzes task requirements and recommends the best OpenAI model
    based on capabilities, cost, and performance.

    Args:
        params: Model selection configuration containing:
            - task_description: Description of the task
            - task_type: Optional task type hint
            - optimize_for: Priority (quality/speed/cost)
            - response_format: Output format (markdown/json)

    Returns:
        str: Recommended model with rationale

    Example:
        >>> model_selector({
        ...     "task_description": "Complex mathematical proof",
        ...     "task_type": "reasoning",
        ...     "optimize_for": "quality"
        ... })
    """
    optimal_model = _select_optimal_model(params.task_type, params.optimize_for)
    model_info = OPENAI_MODELS[optimal_model]

    result = {
        "recommended_model": optimal_model,
        "model_capabilities": model_info,
        "optimization_priority": params.optimize_for,
        "task_type": params.task_type.value if params.task_type else "general",
        "rationale": f"Selected {optimal_model} for {params.optimize_for} optimization",
    }

    return _format_response(result, params.response_format, "Model Selection")


# =============================================================================
# DevSkyy Integration Tools
# =============================================================================


@mcp.tool(
    name="devskyy_agent_openai",
    annotations={
        "title": "DevSkyy Agent with OpenAI",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def devskyy_agent_openai(params: DevSkyyAgentInput) -> str:
    """Invoke DevSkyy agents using OpenAI models as the LLM backend.

    This integrates DevSkyy's 54 specialized agents with OpenAI's models,
    combining DevSkyy's domain expertise with OpenAI's capabilities.

    Available agents:
    - scanner: Code quality analysis
    - fixer: Automated code fixing
    - theme_builder: WordPress theme generation
    - product_manager: E-commerce product operations
    - pricing_engine: Dynamic pricing optimization
    - ml_predictor: Machine learning predictions
    - marketing: Campaign automation
    - content_generator: Content creation

    Args:
        params: Agent configuration containing:
            - agent_name: Which agent to invoke
            - action: Action to perform
            - parameters: Action parameters
            - response_format: Output format (markdown/json)

    Returns:
        str: Agent execution results

    Example:
        >>> devskyy_agent_openai({
        ...     "agent_name": "scanner",
        ...     "action": "scan_code",
        ...     "parameters": {"path": "./src", "deep_scan": True}
        ... })
    """
    data = await _make_api_request(
        f"agents/{params.agent_name}/{params.action}",
        method="POST",
        data=params.parameters,
    )
    return _format_response(data, params.response_format, f"DevSkyy {params.agent_name}")


@mcp.tool(
    name="openai_capabilities_info",
    annotations={
        "title": "OpenAI Capabilities Info",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def capabilities_info(response_format: ResponseFormat = ResponseFormat.MARKDOWN) -> str:
    """Get detailed information about OpenAI models and capabilities.

    Returns comprehensive information about:
    - Available OpenAI models
    - Model capabilities and limitations
    - Context windows and token limits
    - Best use cases for each model
    - Pricing and performance characteristics

    Args:
        response_format: Output format (markdown or json)

    Returns:
        str: Complete OpenAI capabilities reference
    """
    capabilities = {
        "models": OPENAI_MODELS,
        "default_model": DEFAULT_MODEL,
        "api_configured": bool(OPENAI_API_KEY),
        "supported_features": [
            "Text generation",
            "Code generation and analysis",
            "Vision and image understanding",
            "Function calling",
            "JSON mode",
            "Structured outputs",
            "Long context (128K tokens)",
            "Advanced reasoning (o1-preview)",
        ],
        "integrations": [
            "DevSkyy 54 AI agents",
            "WordPress automation",
            "E-commerce tools",
            "Marketing automation",
            "Code scanning and fixing",
        ],
    }
    return _format_response(capabilities, response_format, "OpenAI MCP Server Capabilities")


@mcp.tool(
    name="devskyy_tool_registry",
    annotations={
        "title": "DevSkyy Tool Registry",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def tool_registry_info(
    category: str | None = None,
    response_format: ResponseFormat = ResponseFormat.MARKDOWN,
) -> str:
    """List all available tools from DevSkyy's Tool Runtime.

    Returns the complete tool registry with specifications, categories,
    and severity levels. This enables deterministic tool discovery.

    Args:
        category: Optional filter by category (content, commerce, media, etc.)
        response_format: Output format (markdown or json)

    Returns:
        str: Tool registry listing with specifications
    """
    try:
        # Import Tool Runtime
        import sys

        sys.path.insert(0, str(__file__).replace("/mcp/openai_server.py", ""))
        from core.runtime.tool_registry import get_tool_registry

        registry = get_tool_registry()
        tools = registry.list_enabled()

        # Filter by category if specified
        if category:
            tools = [t for t in tools if t.category.value == category]

        # Format tool list
        tool_list = []
        for tool in tools:
            tool_list.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "category": tool.category.value,
                    "severity": tool.severity.value,
                    "timeout_seconds": tool.timeout_seconds,
                    "idempotent": tool.idempotent,
                    "cacheable": tool.cacheable,
                }
            )

        result = {
            "total_tools": len(tool_list),
            "category_filter": category,
            "tools": tool_list,
        }
        return _format_response(result, response_format, "DevSkyy Tool Registry")
    except ImportError as e:
        return _format_response(
            {"error": f"Tool Runtime not available: {e}"},
            response_format,
            "DevSkyy Tool Registry",
        )


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    # Validate configuration
    if not OPENAI_API_KEY:
        print("⚠️  Warning: OPENAI_API_KEY not set.")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")

    if not API_KEY:
        print("⚠️  Warning: DEVSKYY_API_KEY not set (DevSkyy integration disabled).")
        print("   Set it with: export DEVSKYY_API_KEY='your-key-here'")

    print(
        f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   DevSkyy OpenAI MCP Server v1.0.0                          ║
║   Model Context Protocol for OpenAI Integration             ║
║                                                              ║
║   OpenAI Models • Function Calling • Vision • Code Gen      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

✅ Configuration:
   DevSkyy API: {API_BASE_URL}
   DevSkyy Key: {'Set ✓' if API_KEY else 'Not Set ⚠️'}
   OpenAI Key: {'Set ✓' if OPENAI_API_KEY else 'Not Set ⚠️'}

🔧 Available Tools:
   • openai_completion - Generate text with OpenAI models
   • openai_code_generation - Generate code with documentation
   • openai_vision_analysis - Analyze images (GPT-4o/4o-mini)
   • openai_function_calling - Structured function invocation
   • openai_model_selector - Intelligent model selection
   • devskyy_agent_openai - DevSkyy agents with OpenAI backend
   • devskyy_tool_registry - Tool Runtime discovery
   • openai_capabilities_info - Model capabilities reference

📚 Supported Models:
   • GPT-4o - Most capable, vision, function calling
   • GPT-4o-mini - Fast and efficient, vision support
   • o1-preview - Advanced reasoning for complex tasks

🔗 DevSkyy API: {API_BASE_URL}/docs
📖 OpenAI Docs: https://platform.openai.com/docs

Starting OpenAI MCP server on stdio...
"""
    )

    # Run the server
    mcp.run()
