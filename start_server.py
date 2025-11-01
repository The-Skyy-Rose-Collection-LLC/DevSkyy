#!/usr/bin/env python3
"""
DevSkyy API Server - Simplified Startup
Bypasses complex initialization for quick MCP testing
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

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

logger.info("╔══════════════════════════════════════════════════════════════════╗")
logger.info("║   DevSkyy API Server - Simplified Startup                       ║")
logger.info("║   Ready for MCP Integration Testing                              ║")
logger.info("╚══════════════════════════════════════════════════════════════════╝")
logger.info()

logger.info("✅ Configuration:")
logger.info(f"   API Key: {'Set ✓' if API_KEY else 'Not Set ❌'}")
logger.info(f"   API URL: {API_URL}")
logger.info(f"   Port: {PORT}")
logger.info()

if not API_KEY:
    logger.info("❌ API Key not set. Please run:")
    logger.info("   export DEVSKYY_API_KEY='your-key-here'")
    logger.info("   or source .env")
    sys.exit(1)

try:
    # Import FastAPI
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
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

    logger.info("🚀 Starting DevSkyy API Server...")
    logger.info(f"📡 Server will be available at: {API_URL}")
    logger.info("🔌 MCP tools can now connect to this server")
    logger.info()
    logger.info("📋 Available Mock Endpoints:")
    logger.info("   GET  /                              - Root endpoint")
    logger.info("   GET  /health                        - Health check")
    logger.info("   GET  /api/v1/agents                 - List agents")
    logger.info("   POST /api/v1/scan                   - Code scanning")
    logger.info("   POST /api/v1/fix                    - Code fixing")
    logger.info("   POST /api/v1/security/comprehensive-scan - Security scan")
    logger.info("   GET  /api/v1/analytics/dashboard    - Analytics")
    logger.info()
    logger.info("✅ Ready for MCP testing!")
    logger.info("🔧 Test with: python3 devskyy_mcp.py")
    logger.info()

    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")

except ImportError as e:
    logger.info(f"❌ Missing dependencies: {e}")
    logger.info("Install with: pip install fastapi uvicorn python-dotenv")
    sys.exit(1)
except Exception as e:
    logger.error(f"❌ Error starting server: {e}")
    sys.exit(1)
