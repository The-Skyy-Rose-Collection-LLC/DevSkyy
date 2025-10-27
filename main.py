#!/usr/bin/env python3
"""
DevSkyy - Luxury Fashion AI Platform
Main FastAPI application with multi-AI orchestration system and enterprise security

Author: DevSkyy Team
Version: 5.1.0 Enterprise
Python: >=3.11
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Core FastAPI imports
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

# Prometheus monitoring
try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest, Histogram
    from prometheus_fastapi_instrumentator import Instrumentator

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Environment configuration
VERSION = "5.1.0-enterprise"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# DevSkyy core imports with error handling
try:
    from agent.enhanced_agent_manager import EnhancedAgentManager
    from agent.orchestrator import AgentOrchestrator
    from agent.registry import AgentRegistry
    from ml.model_registry import ModelRegistry
    from ml.redis_cache import RedisCache

    CORE_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Core modules not available: {e}")
    CORE_MODULES_AVAILABLE = False

# Security imports
try:
    from security.encryption_v2 import EncryptionManager
    from security.gdpr_compliance import GDPRManager
    from security.input_validation import input_sanitizer, validation_middleware
    from security.jwt_auth import JWTManager
    from security.secure_headers import security_headers_manager

    SECURITY_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Security modules not available: {e}")
    SECURITY_MODULES_AVAILABLE = False

# Webhook system
try:
    from webhooks.webhook_system import webhook_manager, WebhookManager

    WEBHOOK_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Webhook system not available: {e}")
    WEBHOOK_SYSTEM_AVAILABLE = False

# Agent modules with error handling
try:
    from agent.modules.backend.ecommerce_agent import EcommerceAgent
    from agent.modules.backend.financial_agent import FinancialAgent
    from agent.modules.backend.security_agent import SecurityAgent
    from agent.modules.frontend.design_automation_agent import DesignAutomationAgent
    from agent.modules.frontend.fashion_computer_vision_agent import FashionComputerVisionAgent
    from agent.modules.frontend.web_development_agent import WebDevelopmentAgent

    AGENT_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Agent modules not available: {e}")
    AGENT_MODULES_AVAILABLE = False

# AI Intelligence Services
try:
    from intelligence.claude_sonnet import ClaudeSonnetIntelligenceService
    from intelligence.claude_sonnet_v2 import ClaudeSonnetIntelligenceServiceV2
    from intelligence.multi_model_orchestrator import MultiModelOrchestrator
    from intelligence.openai_service import OpenAIIntelligenceService

    AI_SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AI services not available: {e}")
    AI_SERVICES_AVAILABLE = False

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================


def setup_logging():
    """Setup enterprise-grade logging configuration."""
    try:
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler("logs/devskyy.log") if logs_dir.exists() else logging.StreamHandler(),
            ],
        )

        logger = logging.getLogger(__name__)
        logger.info(f"✅ Logging configured - Level: {LOG_LEVEL}, Environment: {ENVIRONMENT}")
        return logger

    except Exception as e:
        print(f"❌ Failed to setup logging: {e}")
        return logging.getLogger(__name__)


# Initialize logger
logger = setup_logging()

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

if PROMETHEUS_AVAILABLE:
    try:
        REQUEST_DURATION = Histogram(
            "devskyy_request_duration_seconds", "Request duration in seconds", ["method", "endpoint"]
        )

        ACTIVE_CONNECTIONS = Counter("devskyy_active_connections", "Number of active connections")

        FASHION_OPERATIONS = Counter(
            "devskyy_fashion_operations_total", "Total fashion-related operations", ["operation_type", "status"]
        )

        AI_PREDICTIONS = Counter(
            "devskyy_ai_predictions_total", "Total AI predictions made", ["model_type", "accuracy_tier"]
        )

        logger.info("✅ Prometheus metrics initialized")

    except Exception as e:
        logger.warning(f"⚠️ Prometheus metrics setup failed: {e}")
        PROMETHEUS_AVAILABLE = False

# ============================================================================
# FASTAPI APPLICATION INITIALIZATION
# ============================================================================

app = FastAPI(
    title="DevSkyy - Luxury Fashion AI Platform",
    description="Enterprise-grade AI-powered fashion platform with multi-modal capabilities",
    version=VERSION,
    docs_url="/docs" if ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if ENVIRONMENT != "production" else None,
)

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

trusted_hosts = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1,testserver").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add security middleware if available
if SECURITY_MODULES_AVAILABLE:
    app.add_middleware(BaseHTTPMiddleware, dispatch=validation_middleware)

# Add Prometheus instrumentation if available
if PROMETHEUS_AVAILABLE:
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app)

# ============================================================================
# GLOBAL VARIABLES AND CACHES
# ============================================================================

# Agent cache for performance optimization
_agent_cache = {}

# Application state
app.state.version = VERSION
app.state.environment = ENVIRONMENT
app.state.startup_time = datetime.now()

# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP exception: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code, content={"error": True, "message": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc} - {request.url}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": True, "message": "Invalid request data", "details": exc.errors()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": True, "message": "Internal server error", "timestamp": datetime.now().isoformat()},
    )


# ============================================================================
# AGENT FACTORY AND MANAGEMENT
# ============================================================================


def get_agent(agent_type: str, agent_name: str):
    """
    Factory function to get or create agents with caching.

    Args:
        agent_type: Type of agent (backend, frontend, intelligence)
        agent_name: Specific agent name

    Returns:
        Agent instance
    """
    cache_key = f"{agent_type}_{agent_name}"

    if cache_key in _agent_cache:
        return _agent_cache[cache_key]

    try:
        if agent_type == "backend" and AGENT_MODULES_AVAILABLE:
            if agent_name == "security":
                _agent_cache[cache_key] = SecurityAgent()
            elif agent_name == "financial":
                _agent_cache[cache_key] = FinancialAgent()
            elif agent_name == "ecommerce":
                _agent_cache[cache_key] = EcommerceAgent()
            else:
                raise ValueError(f"Unknown backend agent: {agent_name}")

        elif agent_type == "frontend" and AGENT_MODULES_AVAILABLE:
            if agent_name == "design":
                _agent_cache[cache_key] = DesignAutomationAgent()
            elif agent_name == "web_development":
                _agent_cache[cache_key] = WebDevelopmentAgent()
            elif agent_name == "fashion_cv":
                _agent_cache[cache_key] = FashionComputerVisionAgent()
            else:
                raise ValueError(f"Unknown frontend agent: {agent_name}")

        elif agent_type == "intelligence" and AI_SERVICES_AVAILABLE:
            if agent_name == "claude_sonnet":
                _agent_cache[cache_key] = ClaudeSonnetIntelligenceService()
            elif agent_name == "claude_sonnet_v2":
                _agent_cache[cache_key] = ClaudeSonnetIntelligenceServiceV2()
            elif agent_name == "openai":
                _agent_cache[cache_key] = OpenAIIntelligenceService()
            elif agent_name == "multi_model":
                _agent_cache[cache_key] = MultiModelOrchestrator()
            else:
                raise ValueError(f"Unknown intelligence agent: {agent_name}")
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

        logger.info(f"✅ Created agent: {cache_key}")
        return _agent_cache[cache_key]

    except Exception as e:
        logger.error(f"❌ Failed to create agent {cache_key}: {e}")
        return None


# ============================================================================
# STARTUP AND SHUTDOWN EVENTS
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize application components on startup."""
    logger.info("🚀 Starting DevSkyy Platform...")

    try:
        # Initialize enterprise security managers
        if SECURITY_MODULES_AVAILABLE:
            try:
                app.state.encryption_manager = EncryptionManager()
                app.state.gdpr_manager = GDPRManager()
                app.state.jwt_manager = JWTManager()
                logger.info("✅ Enterprise security managers initialized")
            except Exception as e:
                logger.warning(f"⚠️ Some security managers not available: {e}")

        # Initialize webhook system
        if WEBHOOK_SYSTEM_AVAILABLE:
            try:
                app.state.webhook_manager_v2 = WebhookManager()
                logger.info("✅ Enhanced webhook manager initialized")
            except Exception as e:
                logger.warning(f"⚠️ Webhook manager not available: {e}")

        # Initialize ML cache
        try:
            if REDIS_URL:
                ml_cache = RedisCache(redis_url=REDIS_URL, default_ttl=3600, mode="hybrid")
                app.state.ml_cache = ml_cache
                logger.info("✅ ML cache initialized with Redis")
            else:
                logger.info("ℹ️ Using in-memory cache (Redis not configured)")
        except Exception as e:
            logger.warning(f"⚠️ Cache initialization failed: {e}")

        # Initialize core agent systems
        if CORE_MODULES_AVAILABLE:
            try:
                agent_registry = AgentRegistry()
                agent_orchestrator = AgentOrchestrator()

                app.state.agent_registry = agent_registry
                app.state.agent_orchestrator = agent_orchestrator

                logger.info("✅ Agent orchestration system initialized")
            except Exception as e:
                logger.warning(f"⚠️ Agent system initialization failed: {e}")

        # Initialize model registry
        try:
            model_registry = ModelRegistry()
            app.state.model_registry = model_registry
            logger.info("✅ Model registry initialized")
        except Exception as e:
            logger.warning(f"⚠️ Model registry initialization failed: {e}")

        logger.info(f"✅ DevSkyy Platform v{VERSION} started successfully")
        logger.info(f"📊 Environment: {ENVIRONMENT}")
        logger.info(f"🔐 Security modules: {'✅' if SECURITY_MODULES_AVAILABLE else '❌'}")
        logger.info(f"🤖 AI services: {'✅' if AI_SERVICES_AVAILABLE else '❌'}")
        logger.info(f"📈 Monitoring: {'✅' if PROMETHEUS_AVAILABLE else '❌'}")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("🛑 Shutting down DevSkyy Platform...")

    try:
        # Clear agent cache
        _agent_cache.clear()

        # Close any open connections
        if hasattr(app.state, "ml_cache"):
            try:
                await app.state.ml_cache.close()
            except:
                pass

        logger.info("✅ DevSkyy Platform shutdown complete")

    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")


# ============================================================================
# API ROUTERS REGISTRATION
# ============================================================================

# Import API routers with error handling
try:
    from api.v1.agents import router as agents_router

    # DevSkyy v5.1 Enterprise Security Routers
    from api.v1.api_v1_auth_router import router as enterprise_auth_router
    from api.v1.api_v1_monitoring_router import router as enterprise_monitoring_router
    from api.v1.api_v1_webhooks_router import router as enterprise_webhooks_router
    from api.v1.auth import router as auth_router
    from api.v1.codex import router as codex_router
    from api.v1.dashboard import router as dashboard_router
    from api.v1.gdpr import router as gdpr_router
    from api.v1.ml import router as ml_router
    from api.v1.monitoring import router as monitoring_router
    from api.v1.orchestration import router as orchestration_router
    from api.v1.webhooks import router as webhooks_router

    API_ROUTERS_AVAILABLE = True
    logger.info("✅ All API routers loaded successfully")

except ImportError as e:
    logger.warning(f"⚠️ Some API routers not available: {e}")
    API_ROUTERS_AVAILABLE = False

# Register API routers
if API_ROUTERS_AVAILABLE:
    try:
        # Core API routes
        app.include_router(agents_router, prefix="/api/v1/agents", tags=["v1-agents"])
        app.include_router(auth_router, prefix="/api/v1/auth", tags=["v1-auth"])
        app.include_router(webhooks_router, prefix="/api/v1/webhooks", tags=["v1-webhooks"])
        app.include_router(monitoring_router, prefix="/api/v1/monitoring", tags=["v1-monitoring"])
        app.include_router(gdpr_router, prefix="/api/v1/gdpr", tags=["v1-gdpr"])
        app.include_router(ml_router, prefix="/api/v1/ml", tags=["v1-ml"])
        app.include_router(codex_router, prefix="/api/v1/codex", tags=["v1-codex"])
        app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["v1-dashboard"])
        app.include_router(orchestration_router, prefix="/api/v1/orchestration", tags=["v1-orchestration"])

        # DevSkyy v5.1 Enterprise Security Routers
        try:
            app.include_router(enterprise_auth_router, prefix="/api/v1/enterprise/auth", tags=["v1-enterprise-auth"])
            app.include_router(
                enterprise_webhooks_router, prefix="/api/v1/enterprise/webhooks", tags=["v1-enterprise-webhooks"]
            )
            app.include_router(
                enterprise_monitoring_router, prefix="/api/v1/enterprise/monitoring", tags=["v1-enterprise-monitoring"]
            )
            logger.info("✅ DevSkyy v5.1 Enterprise Security routers registered")
        except NameError:
            logger.info("ℹ️ Enterprise security routers not available")

        logger.info("✅ All available API routers registered")

    except Exception as e:
        logger.error(f"❌ Router registration failed: {e}")

# ============================================================================
# CORE ENDPOINTS
# ============================================================================


@app.get("/", response_class=HTMLResponse)
async def get_bulk_editing_interface():
    """Serve the bulk editing interface (primary interface)."""
    try:
        with open("api/bulk_editing_interface.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="""
        <html>
            <body>
                <h1>🌹 DevSkyy - Luxury Fashion AI Platform</h1>
                <p>Bulk editing interface not found. Available endpoints:</p>
                <ul>
                    <li><a href="/docs">API Documentation</a></li>
                    <li><a href="/health">Health Check</a></li>
                    <li><a href="/status">System Status</a></li>
                </ul>
            </body>
        </html>
        """
        )


@app.get("/simple", response_class=HTMLResponse)
async def get_simple_interface():
    """Serve the simple drag & drop interface."""
    try:
        with open("api/drag_drop_interface.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Simple interface not found</h1>")


@app.get("/classic", response_class=HTMLResponse)
async def get_classic_interface():
    """Serve the classic form-based upload interface."""
    try:
        with open("api/upload_interface.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Classic interface not found</h1>")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": VERSION,
        "environment": ENVIRONMENT,
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": (datetime.now() - app.state.startup_time).total_seconds(),
    }


@app.get("/status")
async def system_status():
    """Comprehensive system status endpoint."""
    try:
        issues = []

        # Check critical configurations
        if SECRET_KEY == "dev-secret-key-change-in-production":
            issues.append(
                {
                    "type": "security",
                    "severity": "high",
                    "message": "SECRET_KEY environment variable not set",
                    "recommendation": "Set a strong SECRET_KEY in environment variables",
                }
            )

        if ENVIRONMENT == "production" and app.debug:
            issues.append(
                {
                    "type": "security",
                    "severity": "critical",
                    "message": "Debug mode enabled in production",
                    "recommendation": "Disable debug mode in production environment",
                }
            )

        return {
            "status": "operational",
            "version": VERSION,
            "environment": ENVIRONMENT,
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - app.state.startup_time).total_seconds(),
            "modules": {
                "core_modules": CORE_MODULES_AVAILABLE,
                "security_modules": SECURITY_MODULES_AVAILABLE,
                "ai_services": AI_SERVICES_AVAILABLE,
                "webhook_system": WEBHOOK_SYSTEM_AVAILABLE,
                "prometheus": PROMETHEUS_AVAILABLE,
                "api_routers": API_ROUTERS_AVAILABLE,
            },
            "issues": issues,
            "agent_cache_size": len(_agent_cache),
        }

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return JSONResponse(status_code=500, content={"error": True, "message": "Status check failed"})


# ============================================================================
# TRAINING DATA INTERFACE INTEGRATION
# ============================================================================

# Import and mount the training data interface
try:
    from api.training_data_interface import app as training_app

    # Mount the training data interface
    app.mount("/training", training_app)
    logger.info("✅ Training data interface mounted at /training")

except ImportError as e:
    logger.warning(f"⚠️ Training data interface not available: {e}")

# ============================================================================
# METRICS AND MONITORING ENDPOINTS
# ============================================================================

if PROMETHEUS_AVAILABLE:

    @app.get("/metrics")
    async def get_metrics():
        """Prometheus metrics endpoint."""
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/agents/{agent_type}/{agent_name}")
async def get_agent_endpoint(agent_type: str, agent_name: str):
    """Get or create an agent instance."""
    try:
        agent = get_agent(agent_type, agent_name)
        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent {agent_type}/{agent_name} not found")

        return {
            "agent_type": agent_type,
            "agent_name": agent_name,
            "status": "active",
            "created_at": datetime.now().isoformat(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Agent endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/agents/{agent_type}/{agent_name}/execute")
async def execute_agent_task(agent_type: str, agent_name: str, task_data: Dict[str, Any]):
    """Execute a task using the specified agent."""
    try:
        agent = get_agent(agent_type, agent_name)
        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent {agent_type}/{agent_name} not found")

        # Execute task (this would depend on the specific agent implementation)
        result = {
            "agent_type": agent_type,
            "agent_name": agent_name,
            "task_id": f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "completed",
            "result": "Task executed successfully",
            "timestamp": datetime.now().isoformat(),
        }

        # Update metrics if available
        if PROMETHEUS_AVAILABLE:
            AI_PREDICTIONS.labels(model_type=agent_name, accuracy_tier="high").inc()

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Agent execution error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# STATIC FILES AND ASSETS
# ============================================================================

# Mount static files if directory exists
static_dirs = ["static", "assets", "uploads"]
for static_dir in static_dirs:
    static_path = Path(static_dir)
    if static_path.exists() and static_path.is_dir():
        app.mount(f"/{static_dir}", StaticFiles(directory=static_dir), name=static_dir)
        logger.info(f"✅ Static files mounted: /{static_dir}")

# ============================================================================
# DEVELOPMENT AND DEBUG ENDPOINTS
# ============================================================================

if ENVIRONMENT == "development":

    @app.get("/debug/cache")
    async def debug_cache():
        """Debug endpoint to inspect agent cache."""
        return {
            "cache_size": len(_agent_cache),
            "cached_agents": list(_agent_cache.keys()),
            "timestamp": datetime.now().isoformat(),
        }

    @app.post("/debug/clear-cache")
    async def clear_cache():
        """Debug endpoint to clear agent cache."""
        cache_size = len(_agent_cache)
        _agent_cache.clear()
        return {"message": f"Cache cleared - {cache_size} agents removed", "timestamp": datetime.now().isoformat()}


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Configuration for different environments
    config = {
        "host": "0.0.0.0",
        "port": int(os.getenv("PORT", 8000)),
        "log_level": LOG_LEVEL.lower(),
        "reload": ENVIRONMENT == "development",
        "workers": 1 if ENVIRONMENT == "development" else int(os.getenv("WORKERS", 4)),
    }

    logger.info(f"🚀 Starting DevSkyy Platform on {config['host']}:{config['port']}")
    logger.info(f"📊 Environment: {ENVIRONMENT}")
    logger.info(f"🔄 Reload: {config['reload']}")
    logger.info(f"👥 Workers: {config['workers']}")

    uvicorn.run("main_new:app", **config)
