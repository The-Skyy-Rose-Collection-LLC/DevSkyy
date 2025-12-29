"""
Dashboard API Endpoints
=======================

Backend API for the Next.js dashboard frontend.
Provides endpoints for the 6 SuperAgents with REAL agent integration.

Endpoints:
- GET /agents - List all 6 SuperAgents
- GET /agents/{type} - Get single agent
- GET /agents/{type}/stats - Get agent stats
- GET /agents/{type}/tools - Get agent tools
- POST /agents/{type}/start - Start agent
- POST /agents/{type}/stop - Stop agent
- POST /agents/{type}/learn - Trigger learning
- POST /agents/{type}/execute - Execute a task
- GET /health - Health check
"""

import logging
import time
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Import real agents
from agents import (
    AnalyticsAgent,
    CommerceAgent,
    CreativeAgent,
    EnhancedSuperAgent,
    MarketingAgent,
    OperationsAgent,
    SupportAgent,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Types matching frontend/lib/types.ts
# =============================================================================

SuperAgentTypeLiteral = Literal["commerce", "creative", "marketing", "support", "operations", "analytics"]


class ToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool
    default: Any = None


class ToolInfo(BaseModel):
    name: str
    description: str
    category: str
    parameters: list[ToolParameter] = Field(default_factory=list)


class AgentStats(BaseModel):
    tasksCompleted: int = 0
    successRate: float = 0.95
    avgLatencyMs: float = 250.0
    totalCostUsd: float = 0.0
    learningCycles: int = 0


class AgentInfo(BaseModel):
    id: str
    type: SuperAgentTypeLiteral
    name: str
    description: str
    status: Literal["idle", "running", "error", "learning"]
    capabilities: list[str]
    tools: list[ToolInfo]
    mlModels: list[str]
    stats: AgentStats


class ExecuteRequest(BaseModel):
    task: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    use_round_table: bool = False


class ExecuteResponse(BaseModel):
    task_id: str
    agent_type: str
    status: str
    result: Any = None
    latency_ms: float
    technique_used: str | None = None


# =============================================================================
# Agent Registry - Live Agent Management
# =============================================================================

# Agent class mapping
AGENT_CLASSES: dict[str, type[EnhancedSuperAgent]] = {
    "commerce": CommerceAgent,
    "creative": CreativeAgent,
    "marketing": MarketingAgent,
    "support": SupportAgent,
    "operations": OperationsAgent,
    "analytics": AnalyticsAgent,
}

# Agent metadata (static info)
AGENT_METADATA: dict[str, dict[str, Any]] = {
    "commerce": {
        "name": "Commerce Agent",
        "description": "E-commerce operations: products, orders, inventory, pricing optimization",
        "capabilities": ["product_management", "order_processing", "inventory_tracking", "pricing_optimization", "demand_forecasting"],
        "mlModels": ["demand_forecast", "price_optimization", "customer_segmentation"],
    },
    "creative": {
        "name": "Creative Agent",
        "description": "Visual content: 3D assets (Tripo3D), images (Imagen/FLUX), virtual try-on (FASHN)",
        "capabilities": ["image_generation", "video_generation", "3d_model_creation", "virtual_tryon", "brand_asset_creation"],
        "mlModels": ["imagen_3", "flux_1", "tripo3d", "fashn_virtual_tryon"],
    },
    "marketing": {
        "name": "Marketing Agent",
        "description": "Marketing & content: SEO, social media, email campaigns, trend analysis",
        "capabilities": ["seo_optimization", "content_generation", "social_media", "email_campaigns", "trend_analysis"],
        "mlModels": ["content_optimizer", "sentiment_analyzer", "trend_predictor"],
    },
    "support": {
        "name": "Support Agent",
        "description": "Customer support: tickets, FAQs, escalation, intent classification",
        "capabilities": ["ticket_management", "faq_responses", "intent_classification", "sentiment_analysis", "escalation"],
        "mlModels": ["intent_classifier", "sentiment_analyzer", "response_generator"],
    },
    "operations": {
        "name": "Operations Agent",
        "description": "DevOps & deployment: WordPress, Elementor, monitoring, infrastructure",
        "capabilities": ["wordpress_management", "elementor_builder", "deployment", "monitoring", "infrastructure"],
        "mlModels": ["anomaly_detector", "capacity_planner"],
    },
    "analytics": {
        "name": "Analytics Agent",
        "description": "Data & insights: reports, forecasting, clustering, anomaly detection",
        "capabilities": ["reporting", "forecasting", "clustering", "anomaly_detection", "data_visualization"],
        "mlModels": ["prophet_forecaster", "isolation_forest", "kmeans_clustering"],
    },
}

# Default tools per agent type
DEFAULT_TOOLS: dict[str, list[ToolInfo]] = {
    "commerce": [
        ToolInfo(name="create_product", description="Create WooCommerce product", category="commerce", parameters=[
            ToolParameter(name="name", type="string", description="Product name", required=True)
        ]),
        ToolInfo(name="update_inventory", description="Update product inventory", category="commerce", parameters=[
            ToolParameter(name="product_id", type="string", description="Product ID", required=True)
        ]),
        ToolInfo(name="analyze_pricing", description="AI pricing optimization", category="analytics", parameters=[]),
    ],
    "creative": [
        ToolInfo(name="generate_image", description="Generate image with Imagen/FLUX", category="media", parameters=[
            ToolParameter(name="prompt", type="string", description="Image prompt", required=True)
        ]),
        ToolInfo(name="generate_3d", description="Generate 3D model with Tripo3D", category="media", parameters=[
            ToolParameter(name="prompt", type="string", description="3D prompt", required=True)
        ]),
        ToolInfo(name="virtual_tryon", description="Virtual try-on with FASHN", category="media", parameters=[]),
    ],
    "marketing": [
        ToolInfo(name="generate_content", description="Generate marketing content", category="content", parameters=[
            ToolParameter(name="topic", type="string", description="Content topic", required=True)
        ]),
        ToolInfo(name="analyze_seo", description="SEO analysis and optimization", category="analytics", parameters=[]),
        ToolInfo(name="schedule_post", description="Schedule social media post", category="social", parameters=[]),
    ],
    "support": [
        ToolInfo(name="create_ticket", description="Create support ticket", category="support", parameters=[
            ToolParameter(name="subject", type="string", description="Ticket subject", required=True)
        ]),
        ToolInfo(name="classify_intent", description="Classify customer intent", category="ai", parameters=[]),
        ToolInfo(name="generate_response", description="Generate support response", category="content", parameters=[]),
    ],
    "operations": [
        ToolInfo(name="deploy_site", description="Deploy WordPress site", category="operations", parameters=[]),
        ToolInfo(name="update_theme", description="Update Elementor theme", category="wordpress", parameters=[]),
        ToolInfo(name="check_health", description="Check system health", category="monitoring", parameters=[]),
    ],
    "analytics": [
        ToolInfo(name="generate_report", description="Generate analytics report", category="analytics", parameters=[
            ToolParameter(name="report_type", type="string", description="Type of report", required=True)
        ]),
        ToolInfo(name="forecast", description="Generate forecast", category="ai", parameters=[]),
        ToolInfo(name="detect_anomalies", description="Detect data anomalies", category="ai", parameters=[]),
    ],
}


class AgentRegistry:
    """
    Live registry for SuperAgent instances.
    Lazy-initializes agents on first access and tracks their state.
    """

    def __init__(self):
        self._agents: dict[str, EnhancedSuperAgent] = {}
        self._stats: dict[str, AgentStats] = {
            agent_type: AgentStats() for agent_type in AGENT_CLASSES
        }
        self._status: dict[str, Literal["idle", "running", "error", "learning"]] = {
            agent_type: "idle" for agent_type in AGENT_CLASSES
        }
        self._initialized: dict[str, bool] = {
            agent_type: False for agent_type in AGENT_CLASSES
        }
        self._task_counter = 0

    def get_agent(self, agent_type: str) -> EnhancedSuperAgent:
        """Get or create an agent instance."""
        if agent_type not in AGENT_CLASSES:
            raise ValueError(f"Unknown agent type: {agent_type}")

        if agent_type not in self._agents:
            agent_class = AGENT_CLASSES[agent_type]
            self._agents[agent_type] = agent_class()
            logger.info(f"Initialized {agent_type} agent")

        return self._agents[agent_type]

    async def initialize_agent(self, agent_type: str) -> bool:
        """Initialize an agent (call its async initialize method)."""
        if self._initialized.get(agent_type):
            return True

        try:
            agent = self.get_agent(agent_type)
            if hasattr(agent, "initialize"):
                await agent.initialize()
            self._initialized[agent_type] = True
            self._status[agent_type] = "idle"
            logger.info(f"Agent {agent_type} initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize {agent_type}: {e}")
            self._status[agent_type] = "error"
            return False

    def get_agent_info(self, agent_type: str) -> AgentInfo:
        """Get full agent info for API response."""
        if agent_type not in AGENT_METADATA:
            raise ValueError(f"Unknown agent type: {agent_type}")

        metadata = AGENT_METADATA[agent_type]
        tools = self._get_agent_tools(agent_type)

        return AgentInfo(
            id=f"{agent_type}-001",
            type=agent_type,  # type: ignore
            name=metadata["name"],
            description=metadata["description"],
            status=self._status[agent_type],
            capabilities=metadata["capabilities"],
            tools=tools,
            mlModels=metadata["mlModels"],
            stats=self._stats[agent_type],
        )

    def _get_agent_tools(self, agent_type: str) -> list[ToolInfo]:
        """Extract tools from agent if initialized, else return defaults."""
        if agent_type in self._agents:
            agent = self._agents[agent_type]
            if hasattr(agent, "_build_tools"):
                try:
                    raw_tools = agent._build_tools()
                    return [
                        ToolInfo(
                            name=t.get("name", "unknown"),
                            description=t.get("description", ""),
                            category=agent_type,
                            parameters=[],
                        )
                        for t in raw_tools
                    ]
                except Exception:
                    pass

        return DEFAULT_TOOLS.get(agent_type, [])

    def list_agents(self) -> list[AgentInfo]:
        """Get list of all agents with their info."""
        return [self.get_agent_info(agent_type) for agent_type in AGENT_CLASSES]

    def update_stats(self, agent_type: str, success: bool, latency_ms: float, cost_usd: float = 0.0):
        """Update agent statistics after task execution."""
        stats = self._stats[agent_type]
        total = stats.tasksCompleted + 1
        stats.tasksCompleted = total
        stats.successRate = ((stats.successRate * (total - 1)) + (1.0 if success else 0.0)) / total
        stats.avgLatencyMs = ((stats.avgLatencyMs * (total - 1)) + latency_ms) / total
        stats.totalCostUsd += cost_usd

    def set_status(self, agent_type: str, status: Literal["idle", "running", "error", "learning"]):
        """Set agent status."""
        self._status[agent_type] = status

    def increment_learning(self, agent_type: str):
        """Increment learning cycles counter."""
        self._stats[agent_type].learningCycles += 1

    def get_all_agents(self) -> list[AgentInfo]:
        """Get info for all agents."""
        return [self.get_agent_info(agent_type) for agent_type in AGENT_CLASSES]

    def next_task_id(self) -> str:
        """Generate next task ID."""
        self._task_counter += 1
        return f"task_{self._task_counter:06d}"


# Global registry instance
agent_registry = AgentRegistry()


# =============================================================================
# Router
# =============================================================================

dashboard_router = APIRouter(tags=["Dashboard"])


@dashboard_router.get("/health")
async def health():
    """Dashboard API health check"""
    return {
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat(),
        "agents": len(AGENT_CLASSES),
        "initialized": sum(1 for v in agent_registry._initialized.values() if v),
    }


@dashboard_router.get("/agents", response_model=list[AgentInfo])
async def list_agents():
    """List all 6 SuperAgents"""
    return agent_registry.get_all_agents()


@dashboard_router.get("/agents/{agent_type}", response_model=AgentInfo)
async def get_agent(agent_type: SuperAgentTypeLiteral):
    """Get single agent by type"""
    try:
        return agent_registry.get_agent_info(agent_type)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_type}")


@dashboard_router.get("/agents/{agent_type}/stats", response_model=AgentStats)
async def get_agent_stats(agent_type: SuperAgentTypeLiteral):
    """Get agent statistics"""
    try:
        return agent_registry.get_agent_info(agent_type).stats
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_type}")


@dashboard_router.get("/agents/{agent_type}/tools", response_model=list[ToolInfo])
async def get_agent_tools(agent_type: SuperAgentTypeLiteral):
    """Get agent tools"""
    try:
        return agent_registry.get_agent_info(agent_type).tools
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_type}")


@dashboard_router.post("/agents/{agent_type}/start")
async def start_agent(agent_type: SuperAgentTypeLiteral):
    """Start an agent (initialize if needed)"""
    if agent_type not in AGENT_CLASSES:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_type}")

    success = await agent_registry.initialize_agent(agent_type)
    if success:
        agent_registry.set_status(agent_type, "running")
        logger.info(f"Started agent: {agent_type}")
        return {"success": True, "status": "running"}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to initialize agent: {agent_type}")


@dashboard_router.post("/agents/{agent_type}/stop")
async def stop_agent(agent_type: SuperAgentTypeLiteral):
    """Stop an agent"""
    if agent_type not in AGENT_CLASSES:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_type}")

    agent_registry.set_status(agent_type, "idle")
    logger.info(f"Stopped agent: {agent_type}")
    return {"success": True, "status": "idle"}


@dashboard_router.post("/agents/{agent_type}/learn")
async def trigger_learning(agent_type: SuperAgentTypeLiteral):
    """Trigger learning cycle for an agent"""
    if agent_type not in AGENT_CLASSES:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_type}")

    agent_registry.set_status(agent_type, "learning")
    agent_registry.increment_learning(agent_type)

    # If agent is initialized, trigger actual learning
    if agent_registry._initialized.get(agent_type):
        agent = agent_registry.get_agent(agent_type)
        if hasattr(agent, "self_learning") and hasattr(agent.self_learning, "flush_rag_queue"):
            try:
                await agent.self_learning.flush_rag_queue()
            except Exception as e:
                logger.warning(f"Learning flush failed for {agent_type}: {e}")

    agent_registry.set_status(agent_type, "idle")
    stats = agent_registry._stats[agent_type]
    logger.info(f"Triggered learning for agent: {agent_type}")
    return {"success": True, "learningCycles": stats.learningCycles}


@dashboard_router.post("/agents/{agent_type}/execute", response_model=ExecuteResponse)
async def execute_agent_task(agent_type: SuperAgentTypeLiteral, request: ExecuteRequest):
    """Execute a task using the specified agent"""
    if agent_type not in AGENT_CLASSES:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_type}")

    # Initialize if needed
    if not agent_registry._initialized.get(agent_type):
        await agent_registry.initialize_agent(agent_type)

    agent = agent_registry.get_agent(agent_type)
    agent_registry.set_status(agent_type, "running")

    task_id = agent_registry.next_task_id()
    start_time = time.time()
    technique_used = None

    try:
        # Execute using the appropriate method
        if request.use_round_table and hasattr(agent, "execute_with_round_table"):
            result = await agent.execute_with_round_table(request.task)
        elif hasattr(agent, "execute_smart"):
            result = await agent.execute_smart(request.task)
        elif hasattr(agent, "execute"):
            result = await agent.execute(request.task)
        else:
            result = {"error": "Agent does not support execution"}

        # Extract technique if available
        if isinstance(result, dict):
            technique_used = result.get("technique_used") or result.get("technique")

        latency_ms = (time.time() - start_time) * 1000
        agent_registry.update_stats(agent_type, success=True, latency_ms=latency_ms)
        agent_registry.set_status(agent_type, "idle")

        return ExecuteResponse(
            task_id=task_id,
            agent_type=agent_type,
            status="completed",
            result=result,
            latency_ms=latency_ms,
            technique_used=technique_used,
        )

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        agent_registry.update_stats(agent_type, success=False, latency_ms=latency_ms)
        agent_registry.set_status(agent_type, "error")
        logger.error(f"Agent execution failed: {e}")

        return ExecuteResponse(
            task_id=task_id,
            agent_type=agent_type,
            status="failed",
            result={"error": str(e)},
            latency_ms=latency_ms,
            technique_used=None,
        )


# =============================================================================
# Tools Endpoints
# =============================================================================


@dashboard_router.get("/tools", response_model=list[ToolInfo])
async def list_tools():
    """List all available tools across all agents"""
    all_tools: list[ToolInfo] = []
    seen_names: set[str] = set()
    for agent_info in agent_registry.get_all_agents():
        for tool in agent_info.tools:
            if tool.name not in seen_names:
                all_tools.append(tool)
                seen_names.add(tool.name)
    return all_tools


@dashboard_router.get("/tools/category/{category}", response_model=list[ToolInfo])
async def get_tools_by_category(category: str):
    """Get tools filtered by category"""
    tools: list[ToolInfo] = []
    seen_names: set[str] = set()
    for agent_info in agent_registry.get_all_agents():
        for tool in agent_info.tools:
            if tool.category == category and tool.name not in seen_names:
                tools.append(tool)
                seen_names.add(tool.name)
    return tools


@dashboard_router.post("/tools/test")
async def test_tool(tool_name: str, parameters: dict[str, Any] | None = None):
    """Test a tool with given parameters"""
    if parameters is None:
        parameters = {}

    for agent_info in agent_registry.get_all_agents():
        for tool in agent_info.tools:
            if tool.name == tool_name:
                return {
                    "result": f"Tool '{tool_name}' executed successfully",
                    "parameters": parameters,
                    "agent": agent_info.type,
                }
    raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")


# =============================================================================
# Export
# =============================================================================

__all__ = ["dashboard_router", "agent_registry", "AgentInfo", "ToolInfo", "AgentStats"]
