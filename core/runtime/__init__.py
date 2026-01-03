"""
Core Runtime Module
===================

Unified tool registry and execution runtime for DevSkyy platform.

This module consolidates:
- runtime/tools.py (ToolRegistry, ToolSpec, ToolCallContext)
- orchestration/tool_registry.py (37 built-in tool definitions)

Architecture:
- tool_registry.py: Main registry with tool definitions
- tool_spec.py: Tool specification models
- tool_context.py: Execution context
- tool_executor.py: Execution engine

Usage:
    from core.runtime import ToolRegistry, ToolSpec, ToolCallContext

    registry = ToolRegistry()
    result = await registry.execute("tool_name", params, context)
"""

# Execution context (will be in tool_context.py after split)
from core.runtime.tool_registry import (
    BUILTIN_TOOLS,
    ExecutionStatus,
    ParameterType,
    ToolCallContext,
    ToolCategory,
    ToolDefinition,
    ToolExecutionResult,
    ToolParameter,
    ToolRegistry,
    ToolSeverity,
    ToolSpec,
)

__all__ = [
    # Main registry
    "ToolRegistry",
    # Models
    "ToolSpec",
    "ToolDefinition",
    "ToolParameter",
    "ToolExecutionResult",
    "ToolCallContext",
    # Enums
    "ToolCategory",
    "ToolSeverity",
    "ParameterType",
    "ExecutionStatus",
    # Tool definitions
    "BUILTIN_TOOLS",
]

__version__ = "1.0.0"
