"""Advanced tools: multi-agent workflow orchestration."""

from typing import Any

from pydantic import Field

from mcp_tools.api_client import _format_response, _make_api_request
from mcp_tools.security import secure_tool
from mcp_tools.server import mcp
from mcp_tools.types import BaseAgentInput


class MultiAgentWorkflowInput(BaseAgentInput):
    """Input for orchestrating multiple agents."""

    workflow_name: str = Field(
        ...,
        description="Workflow to execute (e.g., 'product_launch', 'campaign_optimization')",
        min_length=1,
        max_length=100,
    )
    parameters: dict[str, Any] = Field(..., description="Workflow-specific parameters")
    agents: list[str] | None = Field(
        default=None,
        description="Specific agents to use (auto-selected if not provided)",
        max_length=20,
    )
    parallel: bool = Field(default=True, description="Execute agents in parallel when possible")


@mcp.tool(
    name="devskyy_multi_agent_workflow",
    annotations={
        "title": "DevSkyy Multi-Agent Orchestration",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
        "defer_loading": True,
        "input_examples": [
            {
                "workflow_name": "product_launch",
                "parameters": {
                    "product_data": {"name": "Summer Collection", "category": "seasonal"},
                    "launch_date": "2025-11-01",
                },
                "parallel": True,
            },
            {
                "workflow_name": "campaign_optimization",
                "parameters": {"campaign_id": "camp_123", "optimize_for": "conversions"},
                "agents": ["marketing", "analytics"],
            },
            {
                "workflow_name": "inventory_optimization",
                "parameters": {"warehouse_id": "wh_001", "forecast_days": 30},
            },
            {
                "workflow_name": "customer_reengagement",
                "parameters": {"segment": "inactive_90d", "offer_type": "discount"},
                "parallel": True,
            },
        ],
    },
)
@secure_tool("multi_agent_workflow")
async def multi_agent_workflow(params: MultiAgentWorkflowInput) -> str:
    """Orchestrate multiple AI agents for complex workflows.

    **INDUSTRY FIRST**: Agent-to-agent orchestration for enterprise automation.

    The Multi-Agent Orchestrator coordinates multiple specialized agents to
    accomplish complex business workflows:

    **Pre-built Workflows:**

    1. **product_launch**: Complete product launch automation
       - Product creation with AI descriptions
       - SEO optimization
       - Marketing campaign creation
       - Social media scheduling
       - Inventory setup

    2. **campaign_optimization**: Marketing campaign improvement
       - Performance analysis
       - A/B testing
       - Content regeneration
       - Audience refinement

    3. **inventory_optimization**: Stock management
       - Demand forecasting
       - Reorder point calculation
       - Supplier coordination
       - Price adjustments

    4. **customer_reengagement**: Win back inactive customers
       - Segmentation analysis
       - Personalized offer generation
       - Multi-channel outreach
       - Journey tracking

    **Custom Workflows:**
    Define your own multi-agent workflows by specifying agents and parameters.

    Args:
        params (MultiAgentWorkflowInput): Workflow configuration containing:
            - workflow_name: Pre-built or custom workflow name
            - parameters: Workflow-specific settings
            - agents: Specific agents to use (auto-selected if empty)
            - parallel: Execute in parallel when possible
            - response_format: Output format (markdown/json)

    Returns:
        str: Workflow execution results from all agents

    Example:
        >>> multi_agent_workflow({
        ...     "workflow_name": "product_launch",
        ...     "parameters": {
        ...         "product_data": {"name": "Summer Collection", ...},
        ...         "launch_date": "2025-11-01"
        ...     },
        ...     "parallel": True
        ... })
    """
    data = await _make_api_request(
        "workflows/execute",
        method="POST",
        data={
            "workflow_name": params.workflow_name,
            "parameters": params.parameters,
            "agents": params.agents,
            "parallel": params.parallel,
        },
    )

    return _format_response(data, params.response_format, f"Workflow: {params.workflow_name}")
