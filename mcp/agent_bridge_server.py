"""
DevSkyy Agent-MCP Bridge Server
================================

Exposes all 6 SuperAgents as MCP tools for Claude Desktop and other MCP clients.

This bridge enables:
- All agent tools accessible via MCP protocol
- LLM Round Table competition endpoint
- Router-based model selection
- Self-learning insights and reports

Architecture:
    MCP Client (Claude Desktop, etc.)
        |
        v
    Agent-MCP Bridge Server (FastMCP)
        |
        +-- commerce_* (15 tools from CommerceAgent)
        +-- creative_* (10 tools from CreativeAgent)
        +-- marketing_* (12 tools from MarketingAgent)
        +-- support_* (8 tools from SupportAgent)
        +-- operations_* (17 tools from OperationsAgent)
        +-- analytics_* (10 tools from AnalyticsAgent)
        +-- orchestration_* (Round Table, Router, Learning)

Version: 1.0.0
Python: 3.11+
Framework: FastMCP

Usage:
    python mcp/agent_bridge_server.py

    # Claude Desktop config
    {
      "mcpServers": {
        "devskyy-agents": {
          "command": "python",
          "args": ["/path/to/mcp/agent_bridge_server.py"],
          "env": {
            "OPENAI_API_KEY": "your-key",
            "ANTHROPIC_API_KEY": "your-key"
          }
        }
      }
    }
"""

import json
import logging
import os
import sys
import traceback
from enum import Enum
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# Custom Exceptions for Better Error Classification
# =============================================================================


class AgentBridgeError(Exception):
    """Base exception for Agent Bridge errors."""

    def __init__(self, message: str, error_code: str = "BRIDGE_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class AgentNotAvailableError(AgentBridgeError):
    """Raised when an agent is not available or failed to initialize."""

    def __init__(self, agent_type: str, reason: str = ""):
        message = f"Agent '{agent_type}' is not available"
        if reason:
            message += f": {reason}"
        super().__init__(message, "AGENT_NOT_AVAILABLE")
        self.agent_type = agent_type


class AgentExecutionError(AgentBridgeError):
    """Raised when agent execution fails."""

    def __init__(self, agent_type: str, operation: str, reason: str):
        message = f"Agent '{agent_type}' failed to execute '{operation}': {reason}"
        super().__init__(message, "AGENT_EXECUTION_ERROR")
        self.agent_type = agent_type
        self.operation = operation


class AgentTimeoutError(AgentBridgeError):
    """Raised when agent execution times out."""

    def __init__(self, agent_type: str, timeout_seconds: float):
        message = f"Agent '{agent_type}' timed out after {timeout_seconds}s"
        super().__init__(message, "AGENT_TIMEOUT")
        self.agent_type = agent_type
        self.timeout_seconds = timeout_seconds

try:
    from pydantic import BaseModel, ConfigDict, Field

    from mcp.server.fastmcp import FastMCP
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Install with: pip install fastmcp pydantic")
    sys.exit(1)

# Import agents
try:
    from agents import (
        AnalyticsAgent,
        CommerceAgent,
        CreativeAgent,
        MarketingAgent,
        OperationsAgent,
        SupportAgent,
    )
    from agents.base_super_agent import TaskCategory  # SuperAgentType used in type hints
except ImportError as e:
    print(f"Agent imports failed: {e}")
    sys.exit(1)

# Import LLM components
try:
    from llm.round_table import LLMRoundTable
    from llm.router import LLMRouter, RoutingStrategy
except ImportError:
    LLMRoundTable = None
    LLMRouter = None

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

CHARACTER_LIMIT = 30000
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")

# Global agent instances (lazy loaded)
_agents: dict[str, Any] = {}
_router: LLMRouter | None = None
_round_table: LLMRoundTable | None = None

# =============================================================================
# Initialize MCP Server
# =============================================================================

mcp = FastMCP(
    "devskyy_agent_bridge",
    dependencies=[
        "pydantic>=2.5.0",
        "aiohttp>=3.9.0",
    ],
)

# =============================================================================
# Enums & Models
# =============================================================================


class ResponseFormat(str, Enum):
    """Output format for tool responses."""

    MARKDOWN = "markdown"
    JSON = "json"


class AgentType(str, Enum):
    """Available agent types."""

    COMMERCE = "commerce"
    CREATIVE = "creative"
    MARKETING = "marketing"
    SUPPORT = "support"
    OPERATIONS = "operations"
    ANALYTICS = "analytics"


class BaseInput(BaseModel):
    """Base input model for all tools."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' or 'json'"
    )


# =============================================================================
# Commerce Agent Inputs
# =============================================================================


class CommerceGetProductInput(BaseInput):
    """Input for getting product details."""

    sku: str = Field(..., description="Product SKU")
    include_stock: bool = Field(default=True, description="Include stock info")
    include_analytics: bool = Field(default=False, description="Include sales analytics")


class CommerceUpdateProductInput(BaseInput):
    """Input for updating a product."""

    sku: str = Field(..., description="Product SKU")
    updates: dict[str, Any] = Field(..., description="Fields to update")


class CommerceCreateProductInput(BaseInput):
    """Input for creating a product."""

    name: str = Field(..., description="Product name")
    collection: str = Field(..., description="Collection (BLACK_ROSE, LOVE_HURTS, SIGNATURE)")
    price: float = Field(..., ge=0, description="Base price")
    description: str = Field(..., description="Product description")
    variants: list[dict] | None = Field(default=None, description="Size/color variants")


class CommerceInventoryInput(BaseInput):
    """Input for inventory operations."""

    sku: str = Field(..., description="Product SKU")
    quantity: int | None = Field(default=None, description="Quantity (for updates)")
    action: str = Field(default="get", description="Action: get, set, add, subtract")


class CommerceForecastInput(BaseInput):
    """Input for demand forecasting."""

    sku: str = Field(..., description="Product SKU")
    days_ahead: int = Field(default=30, ge=7, le=90, description="Forecast horizon in days")


class CommerceOrderInput(BaseInput):
    """Input for order operations."""

    order_id: str = Field(..., description="Order ID")
    include_history: bool = Field(default=False, description="Include order history")


class CommerceOrderStatusInput(BaseInput):
    """Input for updating order status."""

    order_id: str = Field(..., description="Order ID")
    status: str = Field(
        ..., description="New status (pending, processing, shipped, delivered, cancelled)"
    )
    notify_customer: bool = Field(default=True, description="Send notification to customer")


# =============================================================================
# Creative Agent Inputs
# =============================================================================


class CreativeGenerateImageInput(BaseInput):
    """Input for image generation."""

    prompt: str = Field(..., description="Image generation prompt")
    collection: str = Field(default="SIGNATURE", description="Collection style")
    aspect_ratio: str = Field(default="1:1", description="Aspect ratio (1:1, 16:9, 9:16)")
    provider: str = Field(default="auto", description="Provider: auto, google_imagen, flux")


class CreativeGenerate3DInput(BaseInput):
    """Input for 3D model generation."""

    product_name: str = Field(..., description="Product name")
    garment_type: str = Field(..., description="Garment type (hoodie, bomber, tee, etc.)")
    collection: str = Field(default="SIGNATURE", description="Collection")
    output_format: str = Field(default="glb", description="Output format: glb, usdz, fbx")


class CreativeVirtualTryonInput(BaseInput):
    """Input for virtual try-on."""

    model_image: str = Field(..., description="Model/person image path or URL")
    garment_image: str = Field(..., description="Garment image path or URL")
    category: str = Field(default="tops", description="Garment category: tops, bottoms, outerwear")


# =============================================================================
# Marketing Agent Inputs
# =============================================================================


class MarketingContentInput(BaseInput):
    """Input for content generation."""

    content_type: str = Field(
        ..., description="Type: social_post, email, blog, product_description"
    )
    topic: str = Field(..., description="Content topic or product name")
    platform: str = Field(
        default="instagram", description="Platform: instagram, tiktok, email, blog"
    )
    tone: str = Field(default="luxury", description="Tone: luxury, casual, bold, playful")


class MarketingSEOInput(BaseInput):
    """Input for SEO analysis."""

    url: str | None = Field(default=None, description="Page URL to analyze")
    content: str | None = Field(default=None, description="Content to optimize")
    keywords: list[str] | None = Field(default=None, description="Target keywords")


class MarketingCampaignInput(BaseInput):
    """Input for campaign management."""

    action: str = Field(..., description="Action: create, analyze, schedule")
    campaign_type: str = Field(default="product_launch", description="Campaign type")
    products: list[str] | None = Field(default=None, description="Product SKUs")
    start_date: str | None = Field(default=None, description="Start date (ISO format)")


# =============================================================================
# Support Agent Inputs
# =============================================================================


class SupportTicketInput(BaseInput):
    """Input for ticket operations."""

    action: str = Field(..., description="Action: create, update, close, get")
    ticket_id: str | None = Field(default=None, description="Ticket ID (for update/close/get)")
    subject: str | None = Field(default=None, description="Ticket subject (for create)")
    message: str | None = Field(default=None, description="Ticket message")
    priority: str = Field(default="normal", description="Priority: low, normal, high, urgent")


class SupportFAQInput(BaseInput):
    """Input for FAQ queries."""

    question: str = Field(..., description="Customer question")
    category: str | None = Field(default=None, description="FAQ category filter")


class SupportEscalationInput(BaseInput):
    """Input for escalation handling."""

    ticket_id: str = Field(..., description="Ticket ID to escalate")
    reason: str = Field(..., description="Escalation reason")
    assign_to: str | None = Field(default=None, description="Assign to specific agent/team")


# =============================================================================
# Operations Agent Inputs
# =============================================================================


class OperationsWordPressInput(BaseInput):
    """Input for WordPress operations."""

    action: str = Field(..., description="Action: update_plugin, create_page, backup, optimize")
    target: str | None = Field(default=None, description="Target plugin/page/resource")
    options: dict[str, Any] | None = Field(default=None, description="Additional options")


class OperationsDeployInput(BaseInput):
    """Input for deployment operations."""

    environment: str = Field(default="staging", description="Environment: staging, production")
    version: str | None = Field(default=None, description="Version to deploy")
    rollback: bool = Field(default=False, description="Rollback to previous version")


class OperationsMonitorInput(BaseInput):
    """Input for monitoring operations."""

    metric: str = Field(..., description="Metric: uptime, response_time, error_rate, traffic")
    period: str = Field(default="24h", description="Time period: 1h, 24h, 7d, 30d")


# =============================================================================
# Analytics Agent Inputs
# =============================================================================


class AnalyticsSalesInput(BaseInput):
    """Input for sales analytics."""

    period: str = Field(default="30d", description="Time period: 7d, 30d, 90d, 1y")
    group_by: str = Field(default="day", description="Group by: hour, day, week, month")
    product_ids: list[str] | None = Field(default=None, description="Filter by product SKUs")


class AnalyticsCustomerInput(BaseInput):
    """Input for customer analytics."""

    metric: str = Field(..., description="Metric: acquisition, retention, ltv, segments")
    segment: str | None = Field(default=None, description="Customer segment filter")
    period: str = Field(default="30d", description="Time period")


class AnalyticsReportInput(BaseInput):
    """Input for report generation."""

    report_type: str = Field(..., description="Type: sales, inventory, customers, marketing")
    period: str = Field(..., description="Time period")
    format: str = Field(default="json", description="Format: json, csv, pdf")


# =============================================================================
# Orchestration Inputs
# =============================================================================


class RoundTableInput(BaseInput):
    """Input for LLM Round Table competition."""

    prompt: str = Field(..., description="Prompt for all LLMs to compete on")
    task_type: str = Field(default="general", description="Task type for scoring")
    max_providers: int = Field(default=4, ge=2, le=6, description="Max providers to compete")


class RouterSelectInput(BaseInput):
    """Input for router model selection."""

    task_type: str = Field(..., description="Task type: reasoning, creative, code, analysis")
    requirements: str | None = Field(default=None, description="Specific requirements")
    budget: str = Field(default="balanced", description="Budget: economy, balanced, premium")


class LearningReportInput(BaseInput):
    """Input for self-learning reports."""

    agent_type: AgentType | None = Field(default=None, description="Filter by agent type")
    metric: str = Field(default="all", description="Metric: success_rate, latency, cost, all")
    period: str = Field(default="7d", description="Time period")


# =============================================================================
# Helper Functions
# =============================================================================


async def get_agent(agent_type: AgentType) -> Any:
    """Get or create an agent instance.

    Args:
        agent_type: The type of agent to get.

    Returns:
        The agent instance.

    Raises:
        AgentNotAvailableError: If the agent cannot be created or initialized.
    """
    global _agents

    if agent_type.value not in _agents:
        agent_classes = {
            AgentType.COMMERCE: CommerceAgent,
            AgentType.CREATIVE: CreativeAgent,
            AgentType.MARKETING: MarketingAgent,
            AgentType.SUPPORT: SupportAgent,
            AgentType.OPERATIONS: OperationsAgent,
            AgentType.ANALYTICS: AnalyticsAgent,
        }
        agent_class = agent_classes.get(agent_type)
        if not agent_class:
            raise AgentNotAvailableError(
                agent_type.value,
                reason="Unknown agent type",
            )
        try:
            agent = agent_class()
            await agent.initialize()
            _agents[agent_type.value] = agent
            logger.info(f"Agent '{agent_type.value}' initialized successfully")
        except ImportError as e:
            raise AgentNotAvailableError(
                agent_type.value,
                reason=f"Missing dependency: {e}",
            ) from e
        except AttributeError as e:
            raise AgentNotAvailableError(
                agent_type.value,
                reason=f"Agent initialization error: {e}",
            ) from e
        except Exception as e:
            logger.error(
                f"Failed to initialize agent '{agent_type.value}': {e}",
                exc_info=True,
            )
            raise AgentNotAvailableError(
                agent_type.value,
                reason=str(e),
            ) from e

    agent = _agents.get(agent_type.value)
    if not agent:
        raise AgentNotAvailableError(agent_type.value)
    return agent


async def get_router() -> LLMRouter | None:
    """Get or create the LLM Router."""
    global _router
    if _router is None and LLMRouter:
        _router = LLMRouter(strategy=RoutingStrategy.PRIORITY)
    return _router


async def get_round_table() -> LLMRoundTable | None:
    """Get or create the LLM Round Table."""
    global _round_table
    if _round_table is None and LLMRoundTable:
        _round_table = LLMRoundTable()
    return _round_table


def format_response(data: dict[str, Any], fmt: ResponseFormat) -> str:
    """Format response based on requested format.

    Args:
        data: Response data dict with 'result', 'error', 'agent', etc.
        fmt: Output format (JSON or Markdown).

    Returns:
        Formatted response string.
    """
    if fmt == ResponseFormat.JSON:
        return json.dumps(data, indent=2, default=str)

    # Markdown format
    output = []

    if "error" in data:
        error_msg = f"**Error:** {data['error']}"
        if "error_code" in data:
            error_msg = f"**Error [{data['error_code']}]:** {data['error']}"
        if "error_type" in data:
            error_msg += f"\n- Type: `{data['error_type']}`"
        if "suggestion" in data:
            error_msg += f"\n- Suggestion: {data['suggestion']}"
        return error_msg

    if "result" in data:
        result = data["result"]
        if isinstance(result, dict):
            output.append("## Result\n")
            for key, value in result.items():
                output.append(f"- **{key}:** {value}")
        elif isinstance(result, list):
            output.append(f"## Results ({len(result)} items)\n")
            for i, item in enumerate(result[:10], 1):
                output.append(f"{i}. {item}")
        else:
            output.append(f"## Result\n{result}")

    if "agent" in data:
        output.insert(0, f"*Agent: {data['agent']}*\n")

    if "stats" in data:
        output.append("\n## Statistics")
        output.append(f"```json\n{json.dumps(data['stats'], indent=2)}\n```")

    return "\n".join(output) if output else json.dumps(data, indent=2)


def format_error_response(
    error: Exception,
    fmt: ResponseFormat,
    agent_type: str = "",
    operation: str = "",
) -> str:
    """Format an error response with full context.

    Args:
        error: The exception that occurred.
        fmt: Output format.
        agent_type: Optional agent type for context.
        operation: Optional operation name for context.

    Returns:
        Formatted error response string.
    """
    error_data: dict[str, Any] = {
        "error": str(error),
        "error_type": type(error).__name__,
    }

    # Add specific error codes and suggestions for known error types
    if isinstance(error, AgentNotAvailableError):
        error_data["error_code"] = error.error_code
        error_data["suggestion"] = "Check that the agent is properly configured and all dependencies are installed."
    elif isinstance(error, AgentExecutionError):
        error_data["error_code"] = error.error_code
        error_data["suggestion"] = "Review the input parameters and try again. Check agent logs for details."
    elif isinstance(error, AgentTimeoutError):
        error_data["error_code"] = error.error_code
        error_data["suggestion"] = "The operation took too long. Try with simpler inputs or check system load."
    elif isinstance(error, TimeoutError):
        error_data["error_code"] = "TIMEOUT"
        error_data["suggestion"] = "The operation timed out. Try again or increase timeout settings."
    elif isinstance(error, ConnectionError):
        error_data["error_code"] = "CONNECTION_ERROR"
        error_data["suggestion"] = "Check network connectivity and service availability."
    elif isinstance(error, ValueError):
        error_data["error_code"] = "INVALID_INPUT"
        error_data["suggestion"] = "Check that all input parameters are valid."
    elif isinstance(error, PermissionError):
        error_data["error_code"] = "PERMISSION_DENIED"
        error_data["suggestion"] = "Check that the agent has the required permissions."

    if agent_type:
        error_data["agent"] = agent_type
    if operation:
        error_data["operation"] = operation

    return format_response(error_data, fmt)


# =============================================================================
# Commerce Agent MCP Tools
# =============================================================================


@mcp.tool()
async def commerce_get_product(input: CommerceGetProductInput) -> str:
    """
    Get product details from the commerce system.

    Retrieves comprehensive product information including variants,
    pricing, stock levels, and optionally sales analytics.

    Returns product data or error if not found.
    """
    try:
        agent = await get_agent(AgentType.COMMERCE)

        result = await agent.execute_with_learning(
            prompt=f"Get product details for SKU: {input.sku}",
            task_category=TaskCategory.DATA_EXTRACTION,
            context={
                "sku": input.sku,
                "include_stock": input.include_stock,
                "include_analytics": input.include_analytics,
            },
        )

        return format_response(
            {
                "agent": "commerce",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except AgentNotAvailableError as e:
        logger.error(f"commerce_get_product: agent not available - {e}")
        return format_error_response(e, input.response_format, "commerce", "get_product")
    except TimeoutError as e:
        logger.error(f"commerce_get_product: timeout - {e}")
        return format_error_response(
            AgentTimeoutError("commerce", 30.0),
            input.response_format,
            "commerce",
            "get_product",
        )
    except ValueError as e:
        logger.error(f"commerce_get_product: invalid input - {e}")
        return format_error_response(e, input.response_format, "commerce", "get_product")
    except Exception as e:
        logger.error(f"commerce_get_product failed: {e}", exc_info=True)
        return format_error_response(e, input.response_format, "commerce", "get_product")


@mcp.tool()
async def commerce_update_product(input: CommerceUpdateProductInput) -> str:
    """
    Update product information in WooCommerce.

    Updates specified fields for a product including price,
    description, variants, images, and metadata.

    Returns updated product data or error.
    """
    try:
        agent = await get_agent(AgentType.COMMERCE)

        result = await agent.execute_with_learning(
            prompt=f"Update product {input.sku} with: {json.dumps(input.updates)}",
            task_category=TaskCategory.DATA_EXTRACTION,
            context={"sku": input.sku, "updates": input.updates},
        )

        return format_response(
            {
                "agent": "commerce",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except AgentNotAvailableError as e:
        logger.error(f"commerce_update_product: agent not available - {e}")
        return format_error_response(e, input.response_format, "commerce", "update_product")
    except TimeoutError as e:
        logger.error(f"commerce_update_product: timeout - {e}")
        return format_error_response(
            AgentTimeoutError("commerce", 30.0),
            input.response_format,
            "commerce",
            "update_product",
        )
    except ValueError as e:
        logger.error(f"commerce_update_product: invalid input - {e}")
        return format_error_response(e, input.response_format, "commerce", "update_product")
    except Exception as e:
        logger.error(f"commerce_update_product failed: {e}", exc_info=True)
        return format_error_response(e, input.response_format, "commerce", "update_product")


@mcp.tool()
async def commerce_create_product(input: CommerceCreateProductInput) -> str:
    """
    Create a new product in WooCommerce.

    Creates a new product with specified details including
    collection assignment, pricing, and variants.

    Returns created product ID and details.
    """
    try:
        agent = await get_agent(AgentType.COMMERCE)
        if not agent:
            return format_response({"error": "Commerce agent not available"}, input.response_format)

        result = await agent.execute_with_learning(
            prompt=f"Create new product: {input.name} in {input.collection} collection",
            task_category=TaskCategory.REASONING,
            context={
                "name": input.name,
                "collection": input.collection,
                "price": input.price,
                "description": input.description,
                "variants": input.variants,
            },
        )

        return format_response(
            {
                "agent": "commerce",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"commerce_create_product failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def commerce_inventory(input: CommerceInventoryInput) -> str:
    """
    Manage product inventory levels.

    Get, set, add, or subtract inventory quantities.
    Supports warehouse-specific operations.

    Returns current/updated inventory status.
    """
    try:
        agent = await get_agent(AgentType.COMMERCE)
        if not agent:
            return format_response({"error": "Commerce agent not available"}, input.response_format)

        if input.action == "get":
            prompt = f"Get inventory for SKU: {input.sku}"
        else:
            prompt = (
                f"{input.action.capitalize()} inventory for {input.sku}: quantity={input.quantity}"
            )

        result = await agent.execute_with_learning(
            prompt=prompt,
            task_category=TaskCategory.DATA_EXTRACTION,
            context={"sku": input.sku, "quantity": input.quantity, "action": input.action},
        )

        return format_response(
            {
                "agent": "commerce",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"commerce_inventory failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def commerce_forecast_demand(input: CommerceForecastInput) -> str:
    """
    Forecast product demand using ML models.

    Uses Prophet time-series forecasting to predict
    future demand for inventory planning.

    Returns demand forecast with confidence intervals.
    """
    try:
        agent = await get_agent(AgentType.COMMERCE)
        if not agent:
            return format_response({"error": "Commerce agent not available"}, input.response_format)

        result = await agent.execute_with_learning(
            prompt=f"Forecast demand for {input.sku} for next {input.days_ahead} days",
            task_category=TaskCategory.REASONING,
            context={"sku": input.sku, "days_ahead": input.days_ahead},
        )

        return format_response(
            {
                "agent": "commerce",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"commerce_forecast_demand failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def commerce_get_order(input: CommerceOrderInput) -> str:
    """
    Get order details from WooCommerce.

    Retrieves comprehensive order information including
    items, customer, shipping, and payment details.

    Returns order data or error if not found.
    """
    try:
        agent = await get_agent(AgentType.COMMERCE)
        if not agent:
            return format_response({"error": "Commerce agent not available"}, input.response_format)

        result = await agent.execute_with_learning(
            prompt=f"Get order details for order #{input.order_id}",
            task_category=TaskCategory.DATA_EXTRACTION,
            context={"order_id": input.order_id, "include_history": input.include_history},
        )

        return format_response(
            {
                "agent": "commerce",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"commerce_get_order failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def commerce_update_order_status(input: CommerceOrderStatusInput) -> str:
    """
    Update order status in WooCommerce.

    Updates order status and optionally notifies customer.
    Tracks status history for audit purposes.

    Returns updated order status.
    """
    try:
        agent = await get_agent(AgentType.COMMERCE)
        if not agent:
            return format_response({"error": "Commerce agent not available"}, input.response_format)

        result = await agent.execute_with_learning(
            prompt=f"Update order #{input.order_id} status to {input.status}",
            task_category=TaskCategory.REASONING,
            context={
                "order_id": input.order_id,
                "status": input.status,
                "notify_customer": input.notify_customer,
            },
        )

        return format_response(
            {
                "agent": "commerce",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"commerce_update_order_status failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


# =============================================================================
# Creative Agent MCP Tools
# =============================================================================


@mcp.tool()
async def creative_generate_image(input: CreativeGenerateImageInput) -> str:
    """
    Generate product or marketing images.

    Uses Google Imagen or HuggingFace FLUX to create
    brand-aligned imagery for SkyyRose products.

    Returns image URL or path.
    """
    try:
        agent = await get_agent(AgentType.CREATIVE)
        if not agent:
            return format_response({"error": "Creative agent not available"}, input.response_format)

        result = await agent.execute_with_learning(
            prompt=f"Generate image: {input.prompt}",
            task_category=TaskCategory.CREATIVE,
            context={
                "collection": input.collection,
                "aspect_ratio": input.aspect_ratio,
                "provider": input.provider,
            },
        )

        return format_response(
            {
                "agent": "creative",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"creative_generate_image failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def creative_generate_3d_model(input: CreativeGenerate3DInput) -> str:
    """
    Generate 3D model for product visualization.

    Uses Tripo3D to create GLB/USDZ models from
    product descriptions for AR/web display.

    Returns model URL and format details.
    """
    try:
        agent = await get_agent(AgentType.CREATIVE)
        if not agent:
            return format_response({"error": "Creative agent not available"}, input.response_format)

        result = await agent.execute_with_learning(
            prompt=f"Generate 3D model for {input.product_name} ({input.garment_type})",
            task_category=TaskCategory.CREATIVE,
            context={
                "product_name": input.product_name,
                "garment_type": input.garment_type,
                "collection": input.collection,
                "output_format": input.output_format,
            },
        )

        return format_response(
            {
                "agent": "creative",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"creative_generate_3d_model failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def creative_virtual_tryon(input: CreativeVirtualTryonInput) -> str:
    """
    Generate virtual try-on image.

    Uses FASHN API to overlay garment on model photo
    for realistic product visualization.

    Returns try-on image URL.
    """
    try:
        agent = await get_agent(AgentType.CREATIVE)
        if not agent:
            return format_response({"error": "Creative agent not available"}, input.response_format)

        result = await agent.execute_with_learning(
            prompt="Virtual try-on: garment on model",
            task_category=TaskCategory.CREATIVE,
            context={
                "model_image": input.model_image,
                "garment_image": input.garment_image,
                "category": input.category,
            },
        )

        return format_response(
            {
                "agent": "creative",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"creative_virtual_tryon failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


# =============================================================================
# Marketing Agent MCP Tools
# =============================================================================


@mcp.tool()
async def marketing_generate_content(input: MarketingContentInput) -> str:
    """
    Generate marketing content.

    Creates brand-aligned content for social media,
    email campaigns, blogs, and product descriptions.

    Returns generated content with platform optimization.
    """
    try:
        agent = await get_agent(AgentType.MARKETING)
        if not agent:
            return format_response(
                {"error": "Marketing agent not available"}, input.response_format
            )

        result = await agent.execute_with_learning(
            prompt=f"Generate {input.content_type} about {input.topic} for {input.platform}",
            task_category=TaskCategory.CREATIVE,
            context={
                "content_type": input.content_type,
                "topic": input.topic,
                "platform": input.platform,
                "tone": input.tone,
            },
        )

        return format_response(
            {
                "agent": "marketing",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"marketing_generate_content failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def marketing_seo_analysis(input: MarketingSEOInput) -> str:
    """
    Analyze and optimize content for SEO.

    Evaluates content/pages for SEO best practices
    and provides optimization recommendations.

    Returns SEO score and suggestions.
    """
    try:
        agent = await get_agent(AgentType.MARKETING)
        if not agent:
            return format_response(
                {"error": "Marketing agent not available"}, input.response_format
            )

        prompt = "Analyze SEO"
        if input.url:
            prompt += f" for URL: {input.url}"
        if input.content:
            prompt += f" for content: {input.content[:200]}..."

        result = await agent.execute_with_learning(
            prompt=prompt,
            task_category=TaskCategory.ANALYSIS,
            context={"url": input.url, "content": input.content, "keywords": input.keywords},
        )

        return format_response(
            {
                "agent": "marketing",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"marketing_seo_analysis failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def marketing_campaign(input: MarketingCampaignInput) -> str:
    """
    Manage marketing campaigns.

    Create, analyze, or schedule marketing campaigns
    across channels with performance tracking.

    Returns campaign details or analysis.
    """
    try:
        agent = await get_agent(AgentType.MARKETING)
        if not agent:
            return format_response(
                {"error": "Marketing agent not available"}, input.response_format
            )

        result = await agent.execute_with_learning(
            prompt=f"{input.action.capitalize()} {input.campaign_type} campaign",
            task_category=TaskCategory.REASONING,
            context={
                "action": input.action,
                "campaign_type": input.campaign_type,
                "products": input.products,
                "start_date": input.start_date,
            },
        )

        return format_response(
            {
                "agent": "marketing",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"marketing_campaign failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


# =============================================================================
# Support Agent MCP Tools
# =============================================================================


@mcp.tool()
async def support_ticket(input: SupportTicketInput) -> str:
    """
    Manage customer support tickets.

    Create, update, close, or retrieve support tickets
    with priority and assignment handling.

    Returns ticket details or confirmation.
    """
    try:
        agent = await get_agent(AgentType.SUPPORT)
        if not agent:
            return format_response({"error": "Support agent not available"}, input.response_format)

        prompt = f"{input.action.capitalize()} support ticket"
        if input.ticket_id:
            prompt += f" #{input.ticket_id}"
        if input.subject:
            prompt += f": {input.subject}"

        result = await agent.execute_with_learning(
            prompt=prompt,
            task_category=TaskCategory.REASONING,
            context={
                "action": input.action,
                "ticket_id": input.ticket_id,
                "subject": input.subject,
                "message": input.message,
                "priority": input.priority,
            },
        )

        return format_response(
            {
                "agent": "support",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"support_ticket failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def support_faq_search(input: SupportFAQInput) -> str:
    """
    Search FAQ knowledge base.

    Finds relevant FAQ answers for customer questions
    using semantic search and RAG.

    Returns matching FAQ entries.
    """
    try:
        agent = await get_agent(AgentType.SUPPORT)
        if not agent:
            return format_response({"error": "Support agent not available"}, input.response_format)

        result = await agent.execute_with_learning(
            prompt=f"Find FAQ answer for: {input.question}",
            task_category=TaskCategory.QA,
            context={"question": input.question, "category": input.category},
        )

        return format_response(
            {
                "agent": "support",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"support_faq_search failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def support_escalate(input: SupportEscalationInput) -> str:
    """
    Escalate support ticket to higher tier.

    Escalates complex issues to senior agents or
    specialized teams with full context transfer.

    Returns escalation confirmation and assignment.
    """
    try:
        agent = await get_agent(AgentType.SUPPORT)
        if not agent:
            return format_response({"error": "Support agent not available"}, input.response_format)

        result = await agent.execute_with_learning(
            prompt=f"Escalate ticket #{input.ticket_id}: {input.reason}",
            task_category=TaskCategory.REASONING,
            context={
                "ticket_id": input.ticket_id,
                "reason": input.reason,
                "assign_to": input.assign_to,
            },
        )

        return format_response(
            {
                "agent": "support",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"support_escalate failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


# =============================================================================
# Operations Agent MCP Tools
# =============================================================================


@mcp.tool()
async def operations_wordpress(input: OperationsWordPressInput) -> str:
    """
    Manage WordPress operations.

    Update plugins, create pages, run backups,
    optimize database, and manage Elementor templates.

    Returns operation result or status.
    """
    try:
        agent = await get_agent(AgentType.OPERATIONS)
        if not agent:
            return format_response(
                {"error": "Operations agent not available"}, input.response_format
            )

        result = await agent.execute_with_learning(
            prompt=f"WordPress: {input.action} {input.target or ''}",
            task_category=TaskCategory.REASONING,
            context={"action": input.action, "target": input.target, "options": input.options},
        )

        return format_response(
            {
                "agent": "operations",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"operations_wordpress failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def operations_deploy(input: OperationsDeployInput) -> str:
    """
    Manage deployments.

    Deploy to staging/production, rollback versions,
    and manage deployment pipelines.

    Returns deployment status and details.
    """
    try:
        agent = await get_agent(AgentType.OPERATIONS)
        if not agent:
            return format_response(
                {"error": "Operations agent not available"}, input.response_format
            )

        action = "Rollback" if input.rollback else "Deploy"
        result = await agent.execute_with_learning(
            prompt=f"{action} to {input.environment} {input.version or 'latest'}",
            task_category=TaskCategory.REASONING,
            context={
                "environment": input.environment,
                "version": input.version,
                "rollback": input.rollback,
            },
        )

        return format_response(
            {
                "agent": "operations",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"operations_deploy failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def operations_monitor(input: OperationsMonitorInput) -> str:
    """
    Get system monitoring metrics.

    Retrieve uptime, response times, error rates,
    and traffic statistics.

    Returns metrics data and alerts.
    """
    try:
        agent = await get_agent(AgentType.OPERATIONS)
        if not agent:
            return format_response(
                {"error": "Operations agent not available"}, input.response_format
            )

        result = await agent.execute_with_learning(
            prompt=f"Get {input.metric} metrics for {input.period}",
            task_category=TaskCategory.ANALYSIS,
            context={"metric": input.metric, "period": input.period},
        )

        return format_response(
            {
                "agent": "operations",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"operations_monitor failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


# =============================================================================
# Analytics Agent MCP Tools
# =============================================================================


@mcp.tool()
async def analytics_sales(input: AnalyticsSalesInput) -> str:
    """
    Get sales analytics.

    Retrieve sales data, revenue trends, and
    product performance metrics.

    Returns sales analytics and visualizations.
    """
    try:
        agent = await get_agent(AgentType.ANALYTICS)
        if not agent:
            return format_response(
                {"error": "Analytics agent not available"}, input.response_format
            )

        result = await agent.execute_with_learning(
            prompt=f"Get sales analytics for {input.period} grouped by {input.group_by}",
            task_category=TaskCategory.ANALYSIS,
            context={
                "period": input.period,
                "group_by": input.group_by,
                "product_ids": input.product_ids,
            },
        )

        return format_response(
            {
                "agent": "analytics",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"analytics_sales failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def analytics_customers(input: AnalyticsCustomerInput) -> str:
    """
    Get customer analytics.

    Retrieve customer acquisition, retention, LTV,
    and segmentation data.

    Returns customer insights and trends.
    """
    try:
        agent = await get_agent(AgentType.ANALYTICS)
        if not agent:
            return format_response(
                {"error": "Analytics agent not available"}, input.response_format
            )

        result = await agent.execute_with_learning(
            prompt=f"Get customer {input.metric} analytics for {input.period}",
            task_category=TaskCategory.ANALYSIS,
            context={"metric": input.metric, "segment": input.segment, "period": input.period},
        )

        return format_response(
            {
                "agent": "analytics",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"analytics_customers failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def analytics_generate_report(input: AnalyticsReportInput) -> str:
    """
    Generate analytics report.

    Creates comprehensive reports for sales, inventory,
    customers, or marketing performance.

    Returns report data in requested format.
    """
    try:
        agent = await get_agent(AgentType.ANALYTICS)
        if not agent:
            return format_response(
                {"error": "Analytics agent not available"}, input.response_format
            )

        result = await agent.execute_with_learning(
            prompt=f"Generate {input.report_type} report for {input.period}",
            task_category=TaskCategory.REASONING,
            context={
                "report_type": input.report_type,
                "period": input.period,
                "format": input.format,
            },
        )

        return format_response(
            {
                "agent": "analytics",
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"analytics_generate_report failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


# =============================================================================
# Orchestration MCP Tools
# =============================================================================


@mcp.tool()
async def orchestration_round_table(input: RoundTableInput) -> str:
    """
    Run LLM Round Table competition.

    All configured LLM providers compete on the same
    prompt, scored on quality, relevance, and efficiency.

    Returns winning response with scores.
    """
    try:
        round_table = await get_round_table()
        if not round_table:
            return format_response(
                {
                    "error": "Round Table not available",
                    "note": "LLM Round Table module not imported",
                },
                input.response_format,
            )

        # Run competition
        result = await round_table.compete(
            prompt=input.prompt,
            task_type=input.task_type,
            max_providers=input.max_providers,
        )

        return format_response(
            {
                "competition": "round_table",
                "winner": result.winner if hasattr(result, "winner") else "N/A",
                "scores": result.scores if hasattr(result, "scores") else {},
                "result": (
                    result.winning_response if hasattr(result, "winning_response") else str(result)
                ),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"orchestration_round_table failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def orchestration_router_select(input: RouterSelectInput) -> str:
    """
    Select optimal LLM provider for a task.

    Uses intelligent routing based on task type,
    requirements, and budget constraints.

    Returns recommended provider with reasoning.
    """
    try:
        router = await get_router()
        if not router:
            return format_response(
                {"error": "Router not available", "note": "LLM Router module not imported"},
                input.response_format,
            )

        # Get provider recommendation
        provider = router.select_provider(
            task_type=input.task_type,
            requirements=input.requirements,
            budget=input.budget,
        )

        return format_response(
            {
                "router": "llm_router",
                "recommended_provider": provider,
                "task_type": input.task_type,
                "budget": input.budget,
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"orchestration_router_select failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def orchestration_learning_report(input: LearningReportInput) -> str:
    """
    Get self-learning insights and reports.

    Retrieves agent performance metrics, technique
    effectiveness, and optimization recommendations.

    Returns learning analytics and insights.
    """
    try:
        stats = {}

        if input.agent_type:
            agent = await get_agent(input.agent_type)
            if agent and hasattr(agent, "get_stats"):
                stats[input.agent_type.value] = agent.get_stats()
        else:
            # Get stats from all agents
            for agent_type in AgentType:
                try:
                    agent = await get_agent(agent_type)
                    if agent and hasattr(agent, "get_stats"):
                        stats[agent_type.value] = agent.get_stats()
                except Exception:
                    pass

        return format_response(
            {
                "report": "self_learning",
                "metric": input.metric,
                "period": input.period,
                "stats": stats,
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as e:
        logger.error(f"orchestration_learning_report failed: {e}")
        return format_response({"error": str(e)}, input.response_format)


@mcp.tool()
async def orchestration_list_agents(input: BaseInput) -> str:
    """
    List all available agents and their capabilities.

    Returns summary of all 6 SuperAgents with their
    tools, status, and capabilities.
    """
    agents_info = {
        "commerce": {
            "name": "Commerce Agent",
            "capabilities": ["products", "orders", "inventory", "pricing", "shipping"],
            "tools": 15,
        },
        "creative": {
            "name": "Creative Agent",
            "capabilities": ["images", "3D models", "video", "virtual try-on"],
            "tools": 10,
        },
        "marketing": {
            "name": "Marketing Agent",
            "capabilities": ["content", "SEO", "campaigns", "social media"],
            "tools": 12,
        },
        "support": {
            "name": "Support Agent",
            "capabilities": ["tickets", "FAQ", "chat", "escalation"],
            "tools": 8,
        },
        "operations": {
            "name": "Operations Agent",
            "capabilities": ["WordPress", "Elementor", "deploy", "monitoring"],
            "tools": 17,
        },
        "analytics": {
            "name": "Analytics Agent",
            "capabilities": ["sales", "customers", "forecasting", "reports"],
            "tools": 10,
        },
    }

    return format_response(
        {
            "agents": agents_info,
            "total_tools": sum(a["tools"] for a in agents_info.values()),
            "orchestration_tools": ["round_table", "router_select", "learning_report"],
        },
        input.response_format,
    )[:CHARACTER_LIMIT]


# =============================================================================
# Main Entry Point
# =============================================================================


if __name__ == "__main__":
    print("Starting DevSkyy Agent-MCP Bridge Server...")
    print("   Exposing 6 SuperAgents as MCP tools")
    print("   + Orchestration tools (Round Table, Router, Learning)")
    print()
    print("Available tool prefixes:")
    print("   commerce_*     - E-commerce operations")
    print("   creative_*     - Visual generation")
    print("   marketing_*    - Content and campaigns")
    print("   support_*      - Customer service")
    print("   operations_*   - WordPress and DevOps")
    print("   analytics_*    - Reports and insights")
    print("   orchestration_* - LLM coordination")
    print()
    mcp.run()
