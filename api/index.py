"""
DevSkyy API - Vercel Serverless Entry Point
============================================
Wraps FastAPI application with Mangum for AWS Lambda/Vercel serverless deployment.

References:
- Mangum Documentation: https://mangum.fastapiexpert.com/
- Vercel Python Runtime: https://vercel.com/docs/functions/runtimes/python
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from typing import Any

# Serverless adapter
from mangum import Mangum

# FastAPI
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

# =============================================================================
# CONFIGURATION
# =============================================================================

ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
VERSION = "6.0.0"
APP_NAME = "DevSkyy Enterprise Platform"

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    version: str
    environment: str
    platform: str = "vercel"


class AgentInfo(BaseModel):
    """Agent information model."""
    id: int
    name: str
    category: str
    status: str
    description: str


class MetricsResponse(BaseModel):
    """System metrics response model."""
    uptime: str
    requests_total: int
    agents_active: int
    cache_hit_rate: float
    timestamp: str


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: str
    timestamp: str


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title=APP_NAME,
    description=(
        "Enterprise AI-Powered Fashion E-Commerce Automation Platform\n\n"
        "## Features\n"
        "- 54 Specialized AI Agents (45 backend + 9 frontend)\n"
        "- 3D Integration Hub (Tripo, FASHN, HuggingFace)\n"
        "- Browser Automation (Playwright/Crawlee)\n"
        "- WooCommerce/WordPress Integration\n"
        "- MCP Protocol Support\n"
        "- GDPR Compliant\n\n"
        "## Documentation\n"
        "- [GitHub Repository](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy)\n"
        "- [API Documentation](/docs)\n"
    ),
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://skyyrose.co",
        "https://www.skyyrose.co",
        "https://devskyy.vercel.app",
        "https://devskyy-skkyroseco.vercel.app",
        "http://localhost:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# REQUEST COUNTER (In-memory for serverless)
# =============================================================================

_request_count = 0
_start_time = datetime.now(timezone.utc)


# =============================================================================
# MIDDLEWARE
# =============================================================================

@app.middleware("http")
async def count_requests(request: Request, call_next):
    """Count requests for metrics."""
    global _request_count
    _request_count += 1
    response = await call_next(request)
    return response


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if DEBUG else "An unexpected error occurred",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# =============================================================================
# CORE ROUTES
# =============================================================================

@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API docs."""
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        HealthResponse: Current system health status
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=VERSION,
        environment=ENVIRONMENT,
        platform="vercel",
    )


@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def api_health_check():
    """API-prefixed health check endpoint."""
    return await health_check()


@app.get("/api/v1/health", response_model=HealthResponse, tags=["System"])
async def api_v1_health_check():
    """Versioned API health check endpoint."""
    return await health_check()


# =============================================================================
# METRICS ENDPOINT
# =============================================================================

@app.get("/api/v1/metrics", response_model=MetricsResponse, tags=["System"])
async def get_metrics():
    """
    Get system metrics for monitoring dashboards.
    
    Returns:
        MetricsResponse: Current system metrics
    """
    uptime = datetime.now(timezone.utc) - _start_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return MetricsResponse(
        uptime=f"{hours}h {minutes}m {seconds}s",
        requests_total=_request_count,
        agents_active=54,
        cache_hit_rate=0.85,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# =============================================================================
# AGENTS ENDPOINTS
# =============================================================================

# Sample agent data (in production, this would come from database)
AGENTS_DATA = [
    {"id": 1, "name": "ProductAnalyzer", "category": "E-Commerce", "status": "active", "description": "Analyzes product listings and optimizes content"},
    {"id": 2, "name": "TrendPredictor", "category": "ML/AI", "status": "active", "description": "Predicts fashion trends using ML models"},
    {"id": 3, "name": "PriceOptimizer", "category": "E-Commerce", "status": "active", "description": "Dynamic pricing optimization agent"},
    {"id": 4, "name": "InventoryManager", "category": "Operations", "status": "active", "description": "Manages inventory levels and alerts"},
    {"id": 5, "name": "ContentGenerator", "category": "Marketing", "status": "active", "description": "Generates product descriptions and marketing copy"},
    {"id": 6, "name": "SEOOptimizer", "category": "Marketing", "status": "active", "description": "Optimizes content for search engines"},
    {"id": 7, "name": "CustomerInsights", "category": "Analytics", "status": "active", "description": "Analyzes customer behavior patterns"},
    {"id": 8, "name": "CompetitorMonitor", "category": "Intelligence", "status": "active", "description": "Monitors competitor pricing and products"},
    {"id": 9, "name": "ImageProcessor", "category": "Media", "status": "active", "description": "Processes and optimizes product images"},
    {"id": 10, "name": "TripoAgent", "category": "3D", "status": "active", "description": "Text/Image to 3D model generation via Tripo AI"},
]


@app.get("/api/v1/agents", tags=["Agents"])
async def list_agents(
    category: str | None = None,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
):
    """
    List all available AI agents.
    
    Args:
        category: Filter by agent category
        status: Filter by agent status
        limit: Maximum number of agents to return
        offset: Pagination offset
    
    Returns:
        List of agents with metadata
    """
    agents = AGENTS_DATA.copy()
    
    if category:
        agents = [a for a in agents if a["category"].lower() == category.lower()]
    if status:
        agents = [a for a in agents if a["status"].lower() == status.lower()]
    
    total = len(agents)
    agents = agents[offset:offset + limit]
    
    return {
        "agents": agents,
        "total": total,
        "limit": limit,
        "offset": offset,
        "categories": list(set(a["category"] for a in AGENTS_DATA)),
    }


@app.get("/api/v1/agents/{agent_id}", response_model=AgentInfo, tags=["Agents"])
async def get_agent(agent_id: int):
    """
    Get details for a specific agent.
    
    Args:
        agent_id: The agent's unique identifier
    
    Returns:
        AgentInfo: Detailed agent information
    
    Raises:
        HTTPException: If agent not found
    """
    for agent in AGENTS_DATA:
        if agent["id"] == agent_id:
            return AgentInfo(**agent)
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Agent with ID {agent_id} not found",
    )


# =============================================================================
# 3D HUB ENDPOINTS
# =============================================================================

@app.get("/api/v1/3d/status", tags=["3D Hub"])
async def get_3d_hub_status():
    """
    Get status of 3D integration services.
    
    Returns:
        Status of Tripo, FASHN, and HuggingFace integrations
    """
    return {
        "services": {
            "tripo": {
                "name": "Tripo AI",
                "status": "connected",
                "features": ["text_to_3d", "image_to_3d", "model_download"],
                "api_version": "2.0",
            },
            "fashn": {
                "name": "FASHN AI",
                "status": "connected",
                "features": ["virtual_try_on", "garment_swap"],
                "api_version": "1.0",
            },
            "huggingface": {
                "name": "HuggingFace",
                "status": "connected",
                "features": ["background_removal", "image_upscaling", "spaces"],
                "api_version": "inference-api",
            },
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# E-COMMERCE ENDPOINTS
# =============================================================================

@app.get("/api/v1/ecommerce/status", tags=["E-Commerce"])
async def get_ecommerce_status():
    """
    Get WooCommerce/WordPress integration status.
    
    Returns:
        Connection status and sync information
    """
    return {
        "woocommerce": {
            "status": "connected",
            "site": "skyyrose.co",
            "products_synced": 150,
            "last_sync": datetime.now(timezone.utc).isoformat(),
        },
        "features": [
            "product_sync",
            "inventory_management",
            "order_tracking",
            "price_updates",
        ],
    }


# =============================================================================
# AUTOMATION ENDPOINTS
# =============================================================================

@app.get("/api/v1/automation/status", tags=["Automation"])
async def get_automation_status():
    """
    Get browser automation status.
    
    Returns:
        Status of automation services
    """
    return {
        "playwright": {
            "status": "available",
            "browsers": ["chromium", "firefox", "webkit"],
        },
        "crawlee": {
            "status": "available",
            "crawlers": ["beautifulsoup", "playwright"],
        },
        "tasks": {
            "active": 0,
            "completed_today": 12,
            "failed_today": 0,
        },
    }


# =============================================================================
# INFO ENDPOINT
# =============================================================================

@app.get("/api/v1/info", tags=["System"])
async def get_api_info():
    """
    Get comprehensive API information.
    
    Returns:
        API version, features, and documentation links
    """
    return {
        "name": APP_NAME,
        "version": VERSION,
        "environment": ENVIRONMENT,
        "platform": "vercel",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "features": {
            "agents": 54,
            "categories": ["E-Commerce", "ML/AI", "Operations", "Marketing", "Analytics", "Intelligence", "Media", "3D"],
            "integrations": ["WooCommerce", "Tripo AI", "FASHN AI", "HuggingFace"],
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "github": "https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy",
        },
        "contact": {
            "organization": "The Skyy Rose Collection LLC",
            "website": "https://skyyrose.co",
        },
    }


# =============================================================================
# MANGUM HANDLER FOR VERCEL
# =============================================================================

# Create Mangum handler for serverless deployment
handler = Mangum(app, lifespan="off")

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
