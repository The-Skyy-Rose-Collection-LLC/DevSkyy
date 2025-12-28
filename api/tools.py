"""
Tools API Endpoints
===================

Real tool listing and testing endpoints.
Aggregates tools from all agents via the registry.

Author: DevSkyy Platform Team
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from api.dashboard import AGENT_CLASSES, agent_registry

logger = logging.getLogger(__name__)

tools_router = APIRouter(tags=["Tools"])


# =============================================================================
# Response Models
# =============================================================================


class ToolInfo(BaseModel):
    """Tool information."""

    name: str
    category: str
    description: str = ""
    agent_id: str = ""
    agent_type: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)


class ToolTestRequest(BaseModel):
    """Request to test a tool."""

    tool_name: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class ToolTestResponse(BaseModel):
    """Response from tool test."""

    result: Any = None
    error: str | None = None
    duration_ms: float = 0.0


# =============================================================================
# Tool Categories
# =============================================================================

TOOL_CATEGORIES = {
    "commerce": ["inventory", "pricing", "orders", "products", "integration"],
    "creative": ["visual", "3d", "editing", "generation"],
    "marketing": ["content", "seo", "social", "planning", "email"],
    "support": ["routing", "response", "analysis", "workflow"],
    "operations": ["logistics", "inventory", "fulfillment", "shipping", "deployment"],
    "analytics": ["reporting", "analysis", "visualization", "monitoring", "forecasting"],
}


# =============================================================================
# Endpoints
# =============================================================================


@tools_router.get("/tools", response_model=list[ToolInfo])
async def list_tools() -> list[ToolInfo]:
    """List all available tools across all agents."""
    all_tools = []

    for agent_type in AGENT_CLASSES:
        try:
            agent = agent_registry.get_agent(agent_type)
            agent_tools = getattr(agent, "available_tools", [])

            for tool in agent_tools:
                if isinstance(tool, str):
                    tool_name = tool
                    tool_desc = ""
                    tool_params = {}
                elif hasattr(tool, "name"):
                    tool_name = tool.name
                    tool_desc = getattr(tool, "description", "")
                    tool_params = getattr(tool, "parameters", {})
                else:
                    tool_name = str(tool)
                    tool_desc = ""
                    tool_params = {}

                # Determine category from agent type
                categories = TOOL_CATEGORIES.get(agent_type, [])
                category = categories[0] if categories else agent_type

                all_tools.append(
                    ToolInfo(
                        name=tool_name,
                        category=category,
                        description=tool_desc,
                        agent_id=f"{agent_type}-001",
                        agent_type=agent_type,
                        parameters=tool_params if isinstance(tool_params, dict) else {},
                    )
                )
        except Exception as e:
            logger.warning(f"Failed to get tools from {agent_type}: {e}")
            continue

    return all_tools


@tools_router.get("/tools/category/{category}", response_model=list[ToolInfo])
async def list_tools_by_category(category: str) -> list[ToolInfo]:
    """List tools filtered by category."""
    all_tools = await list_tools()
    return [t for t in all_tools if t.category == category]


@tools_router.post("/tools/test", response_model=ToolTestResponse)
async def test_tool(request: ToolTestRequest) -> ToolTestResponse:
    """Test a tool with given parameters."""
    import time

    start_time = time.time()

    try:
        # Find the agent that has this tool
        for agent_type in AGENT_CLASSES:
            try:
                agent = agent_registry.get_agent(agent_type)
                agent_tools = getattr(agent, "available_tools", [])

                tool_names = []
                for tool in agent_tools:
                    if isinstance(tool, str):
                        tool_names.append(tool)
                    elif hasattr(tool, "name"):
                        tool_names.append(tool.name)

                if request.tool_name in tool_names:
                    # Found the agent, execute the tool
                    if hasattr(agent, "use_tool"):
                        result = await agent.use_tool(request.tool_name, request.parameters)
                        duration_ms = (time.time() - start_time) * 1000
                        return ToolTestResponse(result=result, duration_ms=duration_ms)
                    else:
                        return ToolTestResponse(
                            error=f"Agent {agent_type} does not support tool execution",
                            duration_ms=(time.time() - start_time) * 1000,
                        )
            except Exception:
                continue

        return ToolTestResponse(
            error=f"Tool '{request.tool_name}' not found",
            duration_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        logger.exception(f"Tool test failed: {e}")
        return ToolTestResponse(
            error=str(e),
            duration_ms=(time.time() - start_time) * 1000,
        )


@tools_router.get("/tools/categories", response_model=dict[str, list[str]])
async def list_categories() -> dict[str, list[str]]:
    """List all tool categories."""
    return TOOL_CATEGORIES
