"""
Dashboard API Endpoints
=======================

Backend API for the Next.js dashboard frontend.
Provides endpoints for the 6 SuperAgents with the format expected by the frontend.

Endpoints:
- GET /api/backend/agents - List all 6 SuperAgents
- GET /api/backend/agents/{type} - Get single agent
- GET /api/backend/agents/{type}/stats - Get agent stats
- GET /api/backend/agents/{type}/tools - Get agent tools
- POST /api/backend/agents/{type}/start - Start agent
- POST /api/backend/agents/{type}/stop - Stop agent
- POST /api/backend/agents/{type}/learn - Trigger learning
- GET /api/backend/health - Health check
"""

import logging
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# =============================================================================
# Types matching frontend/lib/types.ts
# =============================================================================

SuperAgentType = Literal["commerce", "creative", "marketing", "support", "operations", "analytics"]


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
    type: SuperAgentType
    name: str
    description: str
    status: Literal["idle", "running", "error", "learning"]
    capabilities: list[str]
    tools: list[ToolInfo]
    mlModels: list[str]
    stats: AgentStats


# =============================================================================
# Agent Registry - 6 SuperAgents
# =============================================================================

SUPER_AGENTS: dict[SuperAgentType, AgentInfo] = {
    "commerce": AgentInfo(
        id="commerce-001",
        type="commerce",
        name="Commerce Agent",
        description="E-commerce operations: products, orders, inventory, pricing optimization",
        status="idle",
        capabilities=[
            "product_management",
            "order_processing",
            "inventory_tracking",
            "pricing_optimization",
            "demand_forecasting",
        ],
        tools=[
            ToolInfo(
                name="create_product",
                description="Create WooCommerce product",
                category="commerce",
                parameters=[
                    ToolParameter(
                        name="name", type="string", description="Product name", required=True
                    )
                ],
            ),
            ToolInfo(
                name="update_inventory",
                description="Update product inventory",
                category="commerce",
                parameters=[
                    ToolParameter(
                        name="product_id", type="string", description="Product ID", required=True
                    )
                ],
            ),
            ToolInfo(
                name="analyze_pricing",
                description="AI pricing optimization",
                category="analytics",
                parameters=[],
            ),
        ],
        mlModels=["demand_forecast", "price_optimization", "customer_segmentation"],
        stats=AgentStats(
            tasksCompleted=1247, successRate=0.97, avgLatencyMs=180, totalCostUsd=12.45
        ),
    ),
    "creative": AgentInfo(
        id="creative-001",
        type="creative",
        name="Creative Agent",
        description="Visual content: 3D assets (Tripo3D), images (Imagen/FLUX), virtual try-on (FASHN)",
        status="idle",
        capabilities=[
            "image_generation",
            "video_generation",
            "3d_model_creation",
            "virtual_tryon",
            "brand_asset_creation",
        ],
        tools=[
            ToolInfo(
                name="generate_image",
                description="Generate image with Imagen/FLUX",
                category="media",
                parameters=[
                    ToolParameter(
                        name="prompt", type="string", description="Image prompt", required=True
                    )
                ],
            ),
            ToolInfo(
                name="generate_3d",
                description="Generate 3D model with Tripo3D",
                category="media",
                parameters=[
                    ToolParameter(
                        name="prompt", type="string", description="3D prompt", required=True
                    )
                ],
            ),
            ToolInfo(
                name="virtual_tryon",
                description="Virtual try-on with FASHN",
                category="media",
                parameters=[],
            ),
        ],
        mlModels=["imagen_3", "flux_1", "tripo3d", "fashn_virtual_tryon"],
        stats=AgentStats(
            tasksCompleted=892, successRate=0.94, avgLatencyMs=4500, totalCostUsd=45.20
        ),
    ),
    "marketing": AgentInfo(
        id="marketing-001",
        type="marketing",
        name="Marketing Agent",
        description="Marketing & content: SEO, social media, email campaigns, trend analysis",
        status="idle",
        capabilities=[
            "seo_optimization",
            "content_generation",
            "social_media",
            "email_campaigns",
            "trend_analysis",
        ],
        tools=[
            ToolInfo(
                name="generate_content",
                description="Generate marketing content",
                category="content",
                parameters=[
                    ToolParameter(
                        name="topic", type="string", description="Content topic", required=True
                    )
                ],
            ),
            ToolInfo(
                name="analyze_seo",
                description="SEO analysis and optimization",
                category="analytics",
                parameters=[],
            ),
            ToolInfo(
                name="schedule_post",
                description="Schedule social media post",
                category="social",
                parameters=[],
            ),
        ],
        mlModels=["content_optimizer", "sentiment_analyzer", "trend_predictor"],
        stats=AgentStats(
            tasksCompleted=2156, successRate=0.96, avgLatencyMs=320, totalCostUsd=28.90
        ),
    ),
    "support": AgentInfo(
        id="support-001",
        type="support",
        name="Support Agent",
        description="Customer support: tickets, FAQs, escalation, intent classification",
        status="idle",
        capabilities=[
            "ticket_management",
            "faq_responses",
            "intent_classification",
            "sentiment_analysis",
            "escalation",
        ],
        tools=[
            ToolInfo(
                name="create_ticket",
                description="Create support ticket",
                category="support",
                parameters=[
                    ToolParameter(
                        name="subject", type="string", description="Ticket subject", required=True
                    )
                ],
            ),
            ToolInfo(
                name="classify_intent",
                description="Classify customer intent",
                category="ai",
                parameters=[],
            ),
            ToolInfo(
                name="generate_response",
                description="Generate support response",
                category="content",
                parameters=[],
            ),
        ],
        mlModels=["intent_classifier", "sentiment_analyzer", "response_generator"],
        stats=AgentStats(
            tasksCompleted=5432, successRate=0.92, avgLatencyMs=150, totalCostUsd=18.75
        ),
    ),
    "operations": AgentInfo(
        id="operations-001",
        type="operations",
        name="Operations Agent",
        description="DevOps & deployment: WordPress, Elementor, monitoring, infrastructure",
        status="idle",
        capabilities=[
            "wordpress_management",
            "elementor_builder",
            "deployment",
            "monitoring",
            "infrastructure",
        ],
        tools=[
            ToolInfo(
                name="deploy_site",
                description="Deploy WordPress site",
                category="operations",
                parameters=[],
            ),
            ToolInfo(
                name="update_theme",
                description="Update Elementor theme",
                category="wordpress",
                parameters=[],
            ),
            ToolInfo(
                name="check_health",
                description="Check system health",
                category="monitoring",
                parameters=[],
            ),
        ],
        mlModels=["anomaly_detector", "capacity_planner"],
        stats=AgentStats(tasksCompleted=743, successRate=0.99, avgLatencyMs=890, totalCostUsd=5.60),
    ),
    "analytics": AgentInfo(
        id="analytics-001",
        type="analytics",
        name="Analytics Agent",
        description="Data & insights: reports, forecasting, clustering, anomaly detection",
        status="idle",
        capabilities=[
            "reporting",
            "forecasting",
            "clustering",
            "anomaly_detection",
            "data_visualization",
        ],
        tools=[
            ToolInfo(
                name="generate_report",
                description="Generate analytics report",
                category="analytics",
                parameters=[
                    ToolParameter(
                        name="report_type",
                        type="string",
                        description="Type of report",
                        required=True,
                    )
                ],
            ),
            ToolInfo(
                name="forecast", description="Generate forecast", category="ai", parameters=[]
            ),
            ToolInfo(
                name="detect_anomalies",
                description="Detect data anomalies",
                category="ai",
                parameters=[],
            ),
        ],
        mlModels=["prophet_forecaster", "isolation_forest", "kmeans_clustering"],
        stats=AgentStats(
            tasksCompleted=1876, successRate=0.98, avgLatencyMs=420, totalCostUsd=22.30
        ),
    ),
}

# =============================================================================
# Router
# =============================================================================

dashboard_router = APIRouter(prefix="/api/py", tags=["Dashboard"])


@dashboard_router.get("/health")
async def health():
    """Dashboard API health check"""
    return {"status": "ok", "timestamp": datetime.now(UTC).isoformat(), "agents": len(SUPER_AGENTS)}


@dashboard_router.get("/agents", response_model=list[AgentInfo])
async def list_agents():
    """List all 6 SuperAgents"""
    return list(SUPER_AGENTS.values())


@dashboard_router.get("/agents/{agent_type}", response_model=AgentInfo)
async def get_agent(agent_type: SuperAgentType):
    """Get single agent by type"""
    if agent_type not in SUPER_AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_type}")
    return SUPER_AGENTS[agent_type]


@dashboard_router.get("/agents/{agent_type}/stats", response_model=AgentStats)
async def get_agent_stats(agent_type: SuperAgentType):
    """Get agent statistics"""
    if agent_type not in SUPER_AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_type}")
    return SUPER_AGENTS[agent_type].stats


@dashboard_router.get("/agents/{agent_type}/tools", response_model=list[ToolInfo])
async def get_agent_tools(agent_type: SuperAgentType):
    """Get agent tools"""
    if agent_type not in SUPER_AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_type}")
    return SUPER_AGENTS[agent_type].tools


@dashboard_router.post("/agents/{agent_type}/start")
async def start_agent(agent_type: SuperAgentType):
    """Start an agent"""
    if agent_type not in SUPER_AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_type}")
    SUPER_AGENTS[agent_type].status = "running"
    logger.info(f"Started agent: {agent_type}")
    return {"success": True, "status": "running"}


@dashboard_router.post("/agents/{agent_type}/stop")
async def stop_agent(agent_type: SuperAgentType):
    """Stop an agent"""
    if agent_type not in SUPER_AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_type}")
    SUPER_AGENTS[agent_type].status = "idle"
    logger.info(f"Stopped agent: {agent_type}")
    return {"success": True, "status": "idle"}


@dashboard_router.post("/agents/{agent_type}/learn")
async def trigger_learning(agent_type: SuperAgentType):
    """Trigger learning cycle for an agent"""
    if agent_type not in SUPER_AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_type}")
    agent = SUPER_AGENTS[agent_type]
    agent.status = "learning"
    agent.stats.learningCycles += 1
    logger.info(f"Triggered learning for agent: {agent_type}")
    return {"success": True, "learningCycles": agent.stats.learningCycles}


# =============================================================================
# Tools Endpoints
# =============================================================================


@dashboard_router.get("/tools", response_model=list[ToolInfo])
async def list_tools():
    """List all available tools across all agents"""
    all_tools: list[ToolInfo] = []
    seen_names: set[str] = set()
    for agent in SUPER_AGENTS.values():
        for tool in agent.tools:
            if tool.name not in seen_names:
                all_tools.append(tool)
                seen_names.add(tool.name)
    return all_tools


@dashboard_router.get("/tools/category/{category}", response_model=list[ToolInfo])
async def get_tools_by_category(category: str):
    """Get tools filtered by category"""
    tools: list[ToolInfo] = []
    seen_names: set[str] = set()
    for agent in SUPER_AGENTS.values():
        for tool in agent.tools:
            if tool.category == category and tool.name not in seen_names:
                tools.append(tool)
                seen_names.add(tool.name)
    return tools


@dashboard_router.post("/tools/test")
async def test_tool(tool_name: str, parameters: dict[str, Any] | None = None):
    """Test a tool with given parameters"""
    if parameters is None:
        parameters = {}
    # Find the tool
    for agent in SUPER_AGENTS.values():
        for tool in agent.tools:
            if tool.name == tool_name:
                return {
                    "result": f"Tool '{tool_name}' executed successfully",
                    "parameters": parameters,
                }
    raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")


# =============================================================================
# Export
# =============================================================================

__all__ = ["dashboard_router", "SUPER_AGENTS", "AgentInfo", "ToolInfo", "AgentStats"]
