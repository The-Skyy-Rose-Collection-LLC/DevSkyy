"""
DevSkyy API Handler
===================
Serverless ASGI handler for Vercel deployment.

This module provides a complete API with endpoints that the dashboard
can consume. It includes mock data for development and real integration
points for production.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Create FastAPI app
app = FastAPI(
    title="DevSkyy API",
    description="AI Agent Orchestration Platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Pydantic Models
# ============================================

class AgentStats(BaseModel):
    tasksCompleted: int
    successRate: float
    avgResponseTime: float

class Tool(BaseModel):
    name: str
    category: str

class Agent(BaseModel):
    id: str
    type: str
    name: str
    description: str
    status: str
    stats: AgentStats
    tools: List[Tool]
    mlModels: List[str]

class AgentAction(BaseModel):
    success: bool
    message: str

class DashboardMetrics(BaseModel):
    totalAgents: int
    activeAgents: int
    totalTasks: int
    successRate: float
    avgResponseTime: float
    uptime: float

# ============================================
# Mock Data for Development
# ============================================

MOCK_AGENTS: List[Dict[str, Any]] = [
    {
        "id": "commerce-001",
        "type": "commerce",
        "name": "Commerce Agent",
        "description": "Manages e-commerce operations, product catalog, and inventory for SkyyRose boutique",
        "status": "running",
        "stats": {"tasksCompleted": 1247, "successRate": 0.98, "avgResponseTime": 0.8},
        "tools": [
            {"name": "Product Sync", "category": "inventory"},
            {"name": "Price Optimizer", "category": "pricing"},
            {"name": "Stock Monitor", "category": "inventory"},
            {"name": "WooCommerce Bridge", "category": "integration"},
        ],
        "mlModels": ["demand-forecast", "price-elasticity"],
    },
    {
        "id": "creative-001",
        "type": "creative",
        "name": "Creative Agent",
        "description": "Generates visual content, product imagery, and marketing assets using AI",
        "status": "running",
        "stats": {"tasksCompleted": 856, "successRate": 0.95, "avgResponseTime": 2.3},
        "tools": [
            {"name": "Image Generator", "category": "visual"},
            {"name": "Style Transfer", "category": "visual"},
            {"name": "Background Removal", "category": "editing"},
            {"name": "3D Asset Creator", "category": "3d"},
        ],
        "mlModels": ["stable-diffusion", "clip", "hunyuan3d"],
    },
    {
        "id": "marketing-001",
        "type": "marketing",
        "name": "Marketing Agent",
        "description": "Creates marketing copy, social media content, and campaigns",
        "status": "idle",
        "stats": {"tasksCompleted": 534, "successRate": 0.92, "avgResponseTime": 1.5},
        "tools": [
            {"name": "Copy Generator", "category": "content"},
            {"name": "SEO Optimizer", "category": "seo"},
            {"name": "Campaign Planner", "category": "planning"},
            {"name": "Social Scheduler", "category": "social"},
        ],
        "mlModels": ["gpt-4o", "claude-3.5-sonnet"],
    },
    {
        "id": "support-001",
        "type": "support",
        "name": "Support Agent",
        "description": "Handles customer inquiries and support tickets with AI assistance",
        "status": "running",
        "stats": {"tasksCompleted": 2341, "successRate": 0.97, "avgResponseTime": 0.5},
        "tools": [
            {"name": "Ticket Router", "category": "routing"},
            {"name": "FAQ Bot", "category": "response"},
            {"name": "Sentiment Analyzer", "category": "analysis"},
            {"name": "Escalation Manager", "category": "workflow"},
        ],
        "mlModels": ["bert-sentiment", "gpt-4o-mini"],
    },
    {
        "id": "operations-001",
        "type": "operations",
        "name": "Operations Agent",
        "description": "Manages logistics, shipping, and fulfillment operations",
        "status": "running",
        "stats": {"tasksCompleted": 1823, "successRate": 0.99, "avgResponseTime": 0.3},
        "tools": [
            {"name": "Route Optimizer", "category": "logistics"},
            {"name": "Inventory Tracker", "category": "inventory"},
            {"name": "Fulfillment Manager", "category": "fulfillment"},
            {"name": "Shipping Calculator", "category": "shipping"},
        ],
        "mlModels": ["route-optimization", "demand-forecast"],
    },
    {
        "id": "analytics-001",
        "type": "analytics",
        "name": "Analytics Agent",
        "description": "Analyzes data, generates reports, and provides business insights",
        "status": "learning",
        "stats": {"tasksCompleted": 678, "successRate": 0.94, "avgResponseTime": 1.8},
        "tools": [
            {"name": "Report Generator", "category": "reporting"},
            {"name": "Trend Analyzer", "category": "analysis"},
            {"name": "Dashboard Builder", "category": "visualization"},
            {"name": "Anomaly Detector", "category": "monitoring"},
        ],
        "mlModels": ["prophet", "arima", "xgboost"],
    },
]

# ============================================
# API Routes
# ============================================

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "DevSkyy API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "devskyy-api",
    }

@app.get("/v1/agents", response_model=List[Dict[str, Any]])
async def list_agents(
    status: Optional[str] = Query(None, description="Filter by agent status"),
    type: Optional[str] = Query(None, description="Filter by agent type"),
):
    """List all agents with optional filtering."""
    agents = MOCK_AGENTS
    if status:
        agents = [a for a in agents if a["status"] == status]
    if type:
        agents = [a for a in agents if a["type"] == type]
    return agents

@app.get("/v1/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get a specific agent by ID or type."""
    agent = next(
        (a for a in MOCK_AGENTS if a["id"] == agent_id or a["type"] == agent_id),
        None,
    )
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return agent

@app.get("/v1/agents/{agent_id}/stats")
async def get_agent_stats(agent_id: str):
    """Get stats for a specific agent."""
    agent = next(
        (a for a in MOCK_AGENTS if a["id"] == agent_id or a["type"] == agent_id),
        None,
    )
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return agent.get("stats", {})

@app.get("/v1/agents/{agent_id}/tools")
async def get_agent_tools(agent_id: str):
    """Get tools for a specific agent."""
    agent = next(
        (a for a in MOCK_AGENTS if a["id"] == agent_id or a["type"] == agent_id),
        None,
    )
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return agent.get("tools", [])

@app.post("/v1/agents/{agent_id}/start")
async def start_agent(agent_id: str):
    """Start a specific agent."""
    agent = next(
        (a for a in MOCK_AGENTS if a["id"] == agent_id or a["type"] == agent_id),
        None,
    )
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return {"success": True, "message": f"Agent {agent['name']} started", "status": "running"}

@app.post("/v1/agents/{agent_id}/stop")
async def stop_agent(agent_id: str):
    """Stop a specific agent."""
    agent = next(
        (a for a in MOCK_AGENTS if a["id"] == agent_id or a["type"] == agent_id),
        None,
    )
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return {"success": True, "message": f"Agent {agent['name']} stopped", "status": "stopped"}

@app.get("/v1/metrics/dashboard", response_model=DashboardMetrics)
async def dashboard_metrics():
    """Get dashboard metrics.

    Returns aggregated metrics across all agents including task counts,
    success rates, and response times.

    Handles edge cases like empty agent lists gracefully.
    """
    try:
        # Guard against empty agent list
        if not MOCK_AGENTS:
            return {
                "totalAgents": 0,
                "activeAgents": 0,
                "totalTasks": 0,
                "successRate": 0.0,
                "avgResponseTime": 0.0,
                "uptime": 99.9,
            }

        active = sum(1 for a in MOCK_AGENTS if a.get("status") == "running")

        # Safely sum tasks, defaulting to 0 for missing/invalid stats
        total_tasks = sum(
            a.get("stats", {}).get("tasksCompleted", 0)
            for a in MOCK_AGENTS
        )

        # Calculate averages with protection against division by zero
        # and None/missing values
        success_rates = [
            a.get("stats", {}).get("successRate")
            for a in MOCK_AGENTS
            if a.get("stats", {}).get("successRate") is not None
        ]
        avg_success = (
            sum(success_rates) / len(success_rates)
            if success_rates else 0.0
        )

        response_times = [
            a.get("stats", {}).get("avgResponseTime")
            for a in MOCK_AGENTS
            if a.get("stats", {}).get("avgResponseTime") is not None
        ]
        avg_response = (
            sum(response_times) / len(response_times)
            if response_times else 0.0
        )

        return {
            "totalAgents": len(MOCK_AGENTS),
            "activeAgents": active,
            "totalTasks": total_tasks,
            "successRate": round(avg_success, 2),
            "avgResponseTime": round(avg_response, 2),
            "uptime": 99.9,
        }
    except (TypeError, ValueError) as e:
        # Handle unexpected data types in stats
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating metrics: {e}. Agent data may be corrupted.",
        )
    except Exception as e:
        # Catch-all for unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Internal error calculating dashboard metrics: {e}",
        )

@app.get("/v1/tools")
async def list_tools():
    """List all available tools across all agents."""
    all_tools = []
    for agent in MOCK_AGENTS:
        for tool in agent.get("tools", []):
            tool_with_agent = {**tool, "agentId": agent["id"], "agentType": agent["type"]}
            all_tools.append(tool_with_agent)
    return all_tools

@app.get("/v1/3d/status")
async def get_3d_pipeline_status():
    """Get 3D pipeline status for the 3D Asset Dashboard."""
    return {
        "status": "operational",
        "models": ["hunyuan3d-2.1", "triposr", "stable-diffusion-3d"],
        "queueLength": 3,
        "processingTime": 45.2,
        "lastGenerated": datetime.now(timezone.utc).isoformat(),
    }
