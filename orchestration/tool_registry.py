"""
DevSkyy Tool Registry (DEPRECATED)
===================================

**DEPRECATION NOTICE**: This module has been moved to `core.runtime`.

All tool registry functionality has been consolidated in `core.runtime.tool_registry`.
This compatibility layer will be removed in 6 months (2026-07-02).

Migration Guide:
    # OLD (deprecated)
    from orchestration.tool_registry import ToolRegistry, BUILTIN_TOOLS

    # NEW (recommended)
    from core.runtime import ToolRegistry, BUILTIN_TOOLS

All imports from this module will issue DeprecationWarning.
"""

import warnings
from typing import Any

# Issue deprecation warning
warnings.warn(
    "orchestration.tool_registry is deprecated and will be removed in 6 months. "
    "Use 'from core.runtime import ToolRegistry, BUILTIN_TOOLS' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Import everything from new location
# ruff: noqa: E402 - Imports after deprecation warning is intentional
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
    # Enums
    "ToolCategory",
    "ToolSeverity",
    "ParameterType",
    "ExecutionStatus",
    # Context
    "ToolCallContext",
    # Models
    "ToolParameter",
    "ToolSpec",
    "ToolDefinition",
    # Results
    "ToolExecutionResult",
    # Registry
    "ToolRegistry",
    # Built-in Tools
    "BUILTIN_TOOLS",
]


# Provide deprecation message on module-level access
def __getattr__(name: str) -> Any:
    """Issue warning on attribute access."""
    if name not in __all__:
        raise AttributeError(f"module 'orchestration.tool_registry' has no attribute '{name}'")

    warnings.warn(
        f"Accessing {name} from orchestration.tool_registry is deprecated. "
        f"Use 'from core.runtime import {name}' instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Return from new location
    import core.runtime.tool_registry as new_module

    return getattr(new_module, name)
