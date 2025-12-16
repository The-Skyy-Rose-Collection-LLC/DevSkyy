#!/usr/bin/env python3
"""
OpenAI MCP Server for DevSkyy Platform
Provides 7 MCP tools for GPT-4o/o1-preview integration with DevSkyy's 54 agents.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any

import openai
from pydantic import BaseModel, Field

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = None
if os.getenv("OPENAI_API_KEY"):
    openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
else:
    logger.warning("OPENAI_API_KEY not found in environment variables")

# DevSkyy integration
devskyy_api_key = os.getenv("DEVSKYY_API_KEY")
if not devskyy_api_key:
    logger.warning("DEVSKYY_API_KEY not found in environment variables")


# Pydantic models for request validation
class CompletionRequest(BaseModel):
    prompt: str = Field(..., description="The prompt to complete")
    model: str = Field(default="gpt-4o", description="OpenAI model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=4096)


class CodeGenerationRequest(BaseModel):
    description: str = Field(..., description="Description of code to generate")
    language: str = Field(default="python", description="Programming language")
    include_tests: bool = Field(default=False, description="Include unit tests")
    include_docs: bool = Field(default=True, description="Include documentation")


class VisionAnalysisRequest(BaseModel):
    image_url: str = Field(..., description="URL of image to analyze")
    prompt: str = Field(default="Describe this image", description="Analysis prompt")
    detail_level: str = Field(default="auto", pattern="^(low|high|auto)$")


class FunctionCallingRequest(BaseModel):
    prompt: str = Field(..., description="Prompt requiring function calls")
    functions: list[dict[str, Any]] = Field(..., description="Available functions")
    model: str = Field(default="gpt-4o", description="OpenAI model to use")


class ModelSelectorRequest(BaseModel):
    task_description: str = Field(..., description="Description of the task")
    priority: str = Field(default="balanced", pattern="^(speed|quality|cost|balanced)$")


class DevSkyyAgentRequest(BaseModel):
    agent_name: str = Field(..., description="Name of DevSkyy agent to invoke")
    action: str = Field(..., description="Action to perform")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Action parameters")


# Initialize MCP server
server = Server("devskyy-openai")


@server.list_tools()
async def list_tools() -> ListToolsResult:
    """List all available MCP tools."""
    tools = [
        Tool(
            name="openai_completion",
            description="Generate text completions using OpenAI models (GPT-4o, GPT-4o-mini, o1-preview)",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The prompt to complete",
                    },
                    "model": {
                        "type": "string",
                        "default": "gpt-4o",
                        "enum": ["gpt-4o", "gpt-4o-mini", "o1-preview"],
                    },
                    "temperature": {
                        "type": "number",
                        "default": 0.7,
                        "minimum": 0.0,
                        "maximum": 2.0,
                    },
                    "max_tokens": {"type": "integer", "minimum": 1, "maximum": 4096},
                },
                "required": ["prompt"],
            },
        ),
        Tool(
            name="openai_code_generation",
            description="Generate code with documentation and optional tests",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Description of code to generate",
                    },
                    "language": {
                        "type": "string",
                        "default": "python",
                        "description": "Programming language",
                    },
                    "include_tests": {
                        "type": "boolean",
                        "default": False,
                        "description": "Include unit tests",
                    },
                    "include_docs": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include documentation",
                    },
                },
                "required": ["description"],
            },
        ),
        Tool(
            name="openai_vision_analysis",
            description="Analyze images using GPT-4o vision capabilities",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_url": {
                        "type": "string",
                        "description": "URL of image to analyze",
                    },
                    "prompt": {
                        "type": "string",
                        "default": "Describe this image",
                        "description": "Analysis prompt",
                    },
                    "detail_level": {
                        "type": "string",
                        "default": "auto",
                        "enum": ["low", "high", "auto"],
                    },
                },
                "required": ["image_url"],
            },
        ),
        Tool(
            name="openai_function_calling",
            description="Execute function calls using OpenAI models with structured outputs",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Prompt requiring function calls",
                    },
                    "functions": {
                        "type": "array",
                        "description": "Available functions",
                    },
                    "model": {
                        "type": "string",
                        "default": "gpt-4o",
                        "enum": ["gpt-4o", "gpt-4o-mini"],
                    },
                },
                "required": ["prompt", "functions"],
            },
        ),
        Tool(
            name="openai_model_selector",
            description="Select optimal OpenAI model based on task requirements",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Description of the task",
                    },
                    "priority": {
                        "type": "string",
                        "default": "balanced",
                        "enum": ["speed", "quality", "cost", "balanced"],
                    },
                },
                "required": ["task_description"],
            },
        ),
        Tool(
            name="devskyy_agent_openai",
            description="Integrate with DevSkyy's 54 agents using OpenAI models",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Name of DevSkyy agent to invoke",
                    },
                    "action": {"type": "string", "description": "Action to perform"},
                    "parameters": {
                        "type": "object",
                        "description": "Action parameters",
                    },
                },
                "required": ["agent_name", "action"],
            },
        ),
        Tool(
            name="openai_capabilities_info",
            description="Get information about OpenAI model capabilities and DevSkyy integration",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "enum": ["gpt-4o", "gpt-4o-mini", "o1-preview", "all"],
                    }
                },
            },
        ),
    ]
    return ListToolsResult(tools=tools)


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    """Handle tool calls."""
    try:
        if name == "openai_completion":
            return await handle_completion(arguments)
        elif name == "openai_code_generation":
            return await handle_code_generation(arguments)
        elif name == "openai_vision_analysis":
            return await handle_vision_analysis(arguments)
        elif name == "openai_function_calling":
            return await handle_function_calling(arguments)
        elif name == "openai_model_selector":
            return await handle_model_selector(arguments)
        elif name == "devskyy_agent_openai":
            return await handle_devskyy_agent(arguments)
        elif name == "openai_capabilities_info":
            return await handle_capabilities_info(arguments)
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                isError=True,
            )
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")], isError=True
        )


async def handle_completion(arguments: dict[str, Any]) -> CallToolResult:
    """Handle OpenAI completion requests."""
    if not openai_client:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text="OpenAI client not initialized. Please set OPENAI_API_KEY.",
                )
            ],
            isError=True,
        )

    try:
        request = CompletionRequest(**arguments)

        # Handle o1-preview model (no temperature/max_tokens)
        if request.model == "o1-preview":
            response = await openai_client.chat.completions.create(
                model=request.model,
                messages=[{"role": "user", "content": request.prompt}],
            )
        else:
            response = await openai_client.chat.completions.create(
                model=request.model,
                messages=[{"role": "user", "content": request.prompt}],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

        result = response.choices[0].message.content
        return CallToolResult(content=[TextContent(type="text", text=result)])
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Completion error: {str(e)}")],
            isError=True,
        )


async def handle_code_generation(arguments: dict[str, Any]) -> CallToolResult:
    """Handle code generation requests."""
    if not openai_client:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text="OpenAI client not initialized. Please set OPENAI_API_KEY.",
                )
            ],
            isError=True,
        )

    try:
        request = CodeGenerationRequest(**arguments)

        prompt = f"""Generate {request.language} code for: {request.description}

Requirements:
- Language: {request.language}
- Include documentation: {request.include_docs}
- Include tests: {request.include_tests}
- Follow best practices and clean code principles
- Add type hints where applicable
- Include error handling

Please provide complete, production-ready code."""

        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        result = response.choices[0].message.content
        return CallToolResult(content=[TextContent(type="text", text=result)])
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Code generation error: {str(e)}")],
            isError=True,
        )


async def handle_vision_analysis(arguments: dict[str, Any]) -> CallToolResult:
    """Handle vision analysis requests."""
    if not openai_client:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text="OpenAI client not initialized. Please set OPENAI_API_KEY.",
                )
            ],
            isError=True,
        )

    try:
        request = VisionAnalysisRequest(**arguments)

        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": request.prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": request.image_url,
                                "detail": request.detail_level,
                            },
                        },
                    ],
                }
            ],
            temperature=0.5,
        )

        result = response.choices[0].message.content
        return CallToolResult(content=[TextContent(type="text", text=result)])
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Vision analysis error: {str(e)}")],
            isError=True,
        )


async def handle_function_calling(arguments: dict[str, Any]) -> CallToolResult:
    """Handle function calling requests."""
    if not openai_client:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text="OpenAI client not initialized. Please set OPENAI_API_KEY.",
                )
            ],
            isError=True,
        )

    try:
        request = FunctionCallingRequest(**arguments)

        response = await openai_client.chat.completions.create(
            model=request.model,
            messages=[{"role": "user", "content": request.prompt}],
            functions=request.functions,
            function_call="auto",
            temperature=0.3,
        )

        result = response.choices[0].message
        if result.function_call:
            function_result = {
                "function_called": result.function_call.name,
                "arguments": json.loads(result.function_call.arguments),
                "content": result.content,
            }
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(function_result, indent=2))]
            )
        else:
            return CallToolResult(content=[TextContent(type="text", text=result.content)])
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Function calling error: {str(e)}")],
            isError=True,
        )


async def handle_model_selector(arguments: dict[str, Any]) -> CallToolResult:
    """Handle model selection requests."""
    try:
        request = ModelSelectorRequest(**arguments)

        # Model selection logic based on task and priority
        task_lower = request.task_description.lower()

        if request.priority == "speed" or request.priority == "cost":
            recommended = "gpt-4o-mini"
        elif request.priority == "quality":
            if any(
                keyword in task_lower
                for keyword in ["reasoning", "complex", "analysis", "math", "logic"]
            ):
                recommended = "o1-preview"
            else:
                recommended = "gpt-4o"
        else:  # balanced
            if any(keyword in task_lower for keyword in ["image", "vision", "photo", "picture"]):
                recommended = "gpt-4o"
            elif any(
                keyword in task_lower
                for keyword in ["reasoning", "complex analysis", "mathematical"]
            ):
                recommended = "o1-preview"
            elif any(keyword in task_lower for keyword in ["simple", "quick", "basic"]):
                recommended = "gpt-4o-mini"
            else:
                recommended = "gpt-4o"

        result = {
            "recommended_model": recommended,
            "reasoning": f"Based on task '{request.task_description}' and priority '{request.priority}'",
            "alternatives": {
                "gpt-4o": "Best for general tasks, vision, function calling",
                "gpt-4o-mini": "Faster and cheaper for simple tasks",
                "o1-preview": "Best for complex reasoning and analysis",
            },
        }

        return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, indent=2))])
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Model selection error: {str(e)}")],
            isError=True,
        )


async def handle_devskyy_agent(arguments: dict[str, Any]) -> CallToolResult:
    """Handle DevSkyy agent integration requests."""
    try:
        request = DevSkyyAgentRequest(**arguments)

        # This would integrate with your existing DevSkyy agent system
        # For now, providing a mock response structure
        result = {
            "agent": request.agent_name,
            "action": request.action,
            "parameters": request.parameters,
            "status": "success",
            "message": f"DevSkyy agent '{request.agent_name}' executed action '{request.action}'",
            "integration_note": "This is a mock response. Integrate with your actual DevSkyy agent system.",
        }

        return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, indent=2))])
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"DevSkyy agent error: {str(e)}")],
            isError=True,
        )


async def handle_capabilities_info(arguments: dict[str, Any]) -> CallToolResult:
    """Handle capabilities information requests."""
    try:
        model = arguments.get("model", "all")

        capabilities = {
            "gpt-4o": {
                "context_window": "128K tokens",
                "capabilities": ["text", "vision", "function_calling", "json_mode"],
                "best_for": [
                    "general tasks",
                    "vision analysis",
                    "function calling",
                    "structured outputs",
                ],
                "limitations": ["higher cost than mini", "slower than mini"],
            },
            "gpt-4o-mini": {
                "context_window": "128K tokens",
                "capabilities": ["text", "vision", "function_calling", "json_mode"],
                "best_for": ["simple tasks", "cost optimization", "speed"],
                "limitations": ["less capable than full gpt-4o"],
            },
            "o1-preview": {
                "context_window": "128K tokens",
                "capabilities": ["advanced_reasoning", "complex_analysis"],
                "best_for": [
                    "complex reasoning",
                    "mathematical problems",
                    "deep analysis",
                ],
                "limitations": [
                    "no vision",
                    "no function calling",
                    "no temperature control",
                    "higher latency",
                ],
            },
        }

        if model == "all":
            result = {
                "devskyy_integration": "54 agents available for integration",
                "mcp_tools": 7,
                "models": capabilities,
            }
        else:
            result = capabilities.get(model, {"error": f"Unknown model: {model}"})

        return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, indent=2))])
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Capabilities info error: {str(e)}")],
            isError=True,
        )


async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting DevSkyy OpenAI MCP Server...")

    # Check environment variables
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable is required")
        sys.exit(1)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
