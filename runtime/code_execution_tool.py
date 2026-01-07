"""
Code Execution Tool for Programmatic Tool Calling
==================================================

Defines the code_execution tool that enables Claude to call tools
programmatically within a sandboxed container.

This tool is managed by Anthropic's infrastructure. When included in
a request, Claude can write Python code that calls other tools as
async functions, enabling batch operations and data filtering.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

from core.runtime.tool_registry import (
    ParameterType,
    ToolCategory,
    ToolParameter,
    ToolSeverity,
    ToolSpec,
)

# =============================================================================
# Code Execution Tool Definition
# =============================================================================

CODE_EXECUTION_TOOL = ToolSpec(
    name="code_execution",
    description="""
    Execute Python code in a secure, sandboxed container.

    Available capabilities:
    - Call any tool with allowed_callers=["code_execution_20250825"] as async functions
    - Process tool results programmatically (filter, aggregate, transform)
    - Execute batch operations (loops, parallel calls)
    - Implement conditional logic based on tool results

    Example usage:
    ```python
    # Batch query
    results = []
    for category in ["jewelry", "watches", "accessories"]:
        data = await search_products(query=category)
        results.extend(data)

    # Filter and aggregate
    high_value = [p for p in results if p['price'] > 1000]
    total_revenue = sum(p['price'] for p in high_value)
    print(f"High-value products: {len(high_value)}, Total: ${total_revenue}")
    ```

    The code runs in Anthropic's managed container with:
    - Python 3.11.12
    - 5GiB RAM, 5GiB disk
    - No internet access (security)
    - 4.5 minute execution timeout
    """,
    category=ToolCategory.SYSTEM,
    severity=ToolSeverity.HIGH,
    version="20250825",
    parameters=[
        ToolParameter(
            name="code",
            type=ParameterType.STRING,
            description="Python code to execute. Tools callable via await tool_name(**params)",
            required=True,
        )
    ],
    # This tool is callable directly by Claude (Claude decides when to use code execution)
    allowed_callers=["direct"],
    timeout_seconds=300.0,  # 5 minutes (container timeout is ~4.5min)
    # This is a managed tool - actual execution happens in Anthropic's infrastructure
    handler_path=None,
)


# =============================================================================
# Exports
# =============================================================================

__all__ = ["CODE_EXECUTION_TOOL"]
