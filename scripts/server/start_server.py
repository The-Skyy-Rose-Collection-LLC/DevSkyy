#!/usr/bin/env python3
"""
DevSkyy API Server - Simplified Startup
Bypasses complex initialization for quick MCP testing
"""

from datetime import datetime
import logging
import os
import sys


# Set up basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv


load_dotenv()

# Basic configuration
API_KEY = os.getenv("DEVSKYY_API_KEY", "")
API_URL = os.getenv("DEVSKYY_API_URL", "http://localhost:8000")
PORT = int(os.getenv("PORT", "8000"))


if not API_KEY:
    sys.exit(1)

try:
    # Import FastAPI
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn

    # Create FastAPI app
    app = FastAPI(
        title="DevSkyy API Server", description="Multi-Agent AI Platform - Simplified for MCP Testing", version="1.1.0"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Basic health check
    @app.get("/")
    async def root():
        return {
            "message": "DevSkyy API Server - Ready for MCP Integration",
            "version": "1.1.0",
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "mcp_ready": True,
        }

    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "api_key_set": bool(API_KEY),
            "mcp_integration": "ready",
        }

    # Mock endpoints for MCP testing
    @app.get("/api/v1/agents")
    async def list_agents():
        """Mock endpoint for MCP agent listing"""
        return {
            "agents": [
                {"id": "scanner", "name": "Code Scanner", "category": "development"},
                {"id": "fixer", "name": "Code Fixer", "category": "development"},
                {"id": "security", "name": "Security Scanner", "category": "security"},
                {"id": "analytics", "name": "Analytics Engine", "category": "analytics"},
            ],
            "total": 4,
            "status": "mock_data",
        }

    @app.post("/api/v1/scan")
    async def scan_code(request: dict):
        """Mock endpoint for code scanning"""
        return {
            "scan_id": "scan_123",
            "status": "completed",
            "issues_found": 0,
            "message": "Mock scan completed - no issues found",
            "timestamp": datetime.now().isoformat(),
        }

    @app.post("/api/v1/fix")
    async def fix_code(request: dict):
        """Mock endpoint for code fixing"""
        return {
            "fix_id": "fix_123",
            "status": "completed",
            "fixes_applied": 0,
            "message": "Mock fix completed - no fixes needed",
            "timestamp": datetime.now().isoformat(),
        }

    @app.post("/api/v1/security/comprehensive-scan")
    async def security_scan(request: dict):
        """Mock endpoint for security scanning"""
        return {
            "security_score": 95,
            "security_grade": "A",
            "vulnerabilities": {"critical": 0, "high": 0, "medium": 1, "low": 2},
            "status": "mock_scan_completed",
            "timestamp": datetime.now().isoformat(),
        }

    @app.get("/api/v1/analytics/dashboard")
    async def analytics_dashboard():
        """Mock endpoint for analytics dashboard"""
        return {
            "key_metrics": {"active_users": 150, "api_requests": 1250, "agent_executions": 89, "revenue": 2500.00},
            "performance": {"avg_response_time": 245.5, "success_rate": 99.2, "uptime": 99.8},
            "status": "mock_analytics",
            "timestamp": datetime.now().isoformat(),
        }

    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")

except ImportError:
    sys.exit(1)
except Exception:
    sys.exit(1)
