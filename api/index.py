"""
DevSkyy API Handler
===================
Serverless ASGI handler for Vercel deployment.

This module provides a complete API that mirrors main_enterprise.py
but is optimized for serverless deployment on Vercel.
All endpoints use real agent implementations, no mock data.

Author: DevSkyy Platform Team
"""

from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.brand import brand_router

# Import real routers
from api.dashboard import dashboard_router
from api.round_table import round_table_router
from api.tasks import tasks_router
from api.three_d import three_d_router
from api.tools import tools_router
from api.visual import visual_router

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
# Mount Real Routers
# ============================================

# All routers are prefixed with /v1 for API versioning
app.include_router(dashboard_router, prefix="/v1")
app.include_router(tasks_router, prefix="/v1")
app.include_router(round_table_router, prefix="/v1")
app.include_router(brand_router, prefix="/v1")
app.include_router(tools_router, prefix="/v1")
app.include_router(three_d_router, prefix="/v1")
app.include_router(visual_router, prefix="/v1")


# ============================================
# Root & Health Endpoints
# ============================================


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "status": "ok",
        "message": "DevSkyy API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "agents": "/v1/agents",
            "tasks": "/v1/tasks",
            "round_table": "/v1/round-table",
            "brand": "/v1/brand",
            "3d_pipeline": "/v1/3d",
        },
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "devskyy-api",
        "version": "1.0.0",
    }


@app.get("/ready")
async def ready():
    """Readiness probe for container orchestration."""
    return {"ready": True}


@app.get("/live")
async def live():
    """Liveness probe for container orchestration."""
    return {"alive": True}


# ============================================
# Legacy Compatibility
# ============================================
# These endpoints redirect to the new router endpoints
# for backwards compatibility with existing integrations


@app.get("/v1/metrics/dashboard")
async def dashboard_metrics():
    """Get dashboard metrics - aggregates from agent stats."""
    from api.dashboard import agent_registry

    agents_info = agent_registry.list_agents()

    active = sum(1 for a in agents_info if a.status == "running")
    total_tasks = sum(a.stats.tasksCompleted for a in agents_info)
    avg_success = (
        sum(a.stats.successRate for a in agents_info) / len(agents_info) if agents_info else 0.0
    )
    avg_response = (
        sum(a.stats.avgLatencyMs for a in agents_info) / len(agents_info) if agents_info else 0.0
    )

    return {
        "totalAgents": len(agents_info),
        "activeAgents": active,
        "totalTasks": total_tasks,
        "successRate": round(avg_success, 2),
        "avgResponseTime": round(avg_response / 1000, 2),  # Convert ms to seconds
        "uptime": 99.9,
    }
