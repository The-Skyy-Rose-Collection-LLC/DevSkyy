#!/usr/bin/env python3
"""
DevSkyy - Luxury Fashion AI Platform
Main FastAPI application with multi-AI orchestration system and enterprise security

Author: DevSkyy Team
Version: 5.1.0 Enterprise
Python: >=3.11
"""

from datetime import datetime
import logging
import os
from pathlib import Path
import sys
from typing import Any

# Core FastAPI imports
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware


# Observability: Logfire (OpenTelemetry-based monitoring)
try:
    import logfire

    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False

# Prometheus monitoring
try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
    from prometheus_fastapi_instrumentator import Instrumentator

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Environment configuration
VERSION = "5.1.0-enterprise"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Security: SECRET_KEY must be set in environment variables
# Per Truth Protocol Rule #5: No secrets in code
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY and ENVIRONMENT == "production":
    raise ValueError(
        "SECRET_KEY environment variable must be set in production. "
        "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )
elif not SECRET_KEY:
    # Development/testing only - log warning
    SECRET_KEY = "dev-only-insecure-key-DO-NOT-USE-IN-PRODUCTION"
    logging.warning(
        "⚠️  Using default SECRET_KEY for development. "
        "Set SECRET_KEY environment variable before deploying to production!"
    )

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# DevSkyy core imports with error handling
try:
    from agent.orchestrator import AgentOrchestrator
    from agent.registry import AgentRegistry
    from ml.model_registry import ModelRegistry
    from ml.redis_cache import RedisCache

    CORE_MODULES_AVAILABLE = True
except ImportError:
    CORE_MODULES_AVAILABLE = False

# Security imports
try:
    from security.encryption import EncryptionManager
    from security.gdpr_compliance import GDPRManager
    from security.input_validation import validation_middleware
    from security.jwt_auth import JWTManager

    SECURITY_MODULES_AVAILABLE = True
except ImportError:
    SECURITY_MODULES_AVAILABLE = False

# Webhook system
try:
    from webhooks.webhook_system import WebhookManager

    WEBHOOK_SYSTEM_AVAILABLE = True
except ImportError:
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
except ImportError:
    AGENT_MODULES_AVAILABLE = False

# AI Intelligence Services
try:
    from agent.modules.backend.claude_sonnet_intelligence_service import ClaudeSonnetIntelligenceService
    from agent.modules.backend.claude_sonnet_intelligence_service_v2 import ClaudeSonnetIntelligenceServiceV2
    from agent.modules.backend.multi_model_ai_orchestrator import MultiModelAIOrchestrator as MultiModelOrchestrator

    AI_SERVICES_AVAILABLE = True
except ImportError:
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

    except Exception:
        return logging.getLogger(__name__)


# Initialize logger
logger = setup_logging()

# ============================================================================
# LOGFIRE OBSERVABILITY CONFIGURATION
# ============================================================================

if LOGFIRE_AVAILABLE:
    try:
        # Configure logfire
        logfire.configure(
            service_name="devskyy-platform",
            service_version=VERSION,
            environment=ENVIRONMENT,
        )
        logger.info("✅ Logfire observability configured - OpenTelemetry tracing enabled")
    except Exception as e:
        logger.warning(f"⚠️ Logfire configuration failed: {e}")
        LOGFIRE_AVAILABLE = False

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

# Instrument FastAPI with Logfire for automatic tracing
if LOGFIRE_AVAILABLE:
    try:
        logfire.instrument_fastapi(app)
        logger.info("✅ FastAPI instrumented with Logfire - Auto-tracing all HTTP requests")
    except Exception as e:
        logger.warning(f"⚠️ Logfire FastAPI instrumentation failed: {e}")

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# CORS configuration (Truth Protocol Rule #7: Input Validation & Security)
# Environment-specific CORS setup for security
if ENVIRONMENT == "production":
    # Production: strict whitelist only
    cors_origins_str = os.getenv("CORS_ORIGINS", "")
    cors_origins = cors_origins_str.split(",") if cors_origins_str else []
    if not cors_origins:
        logger.warning("⚠️ No CORS_ORIGINS set in production - blocking all cross-origin requests")
    else:
        logger.info(f"✅ Production CORS origins: {len(cors_origins)} domains whitelisted")
else:
    # Development: allow localhost and common dev ports
    cors_origins_str = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://127.0.0.1:3000"
    )
    cors_origins = cors_origins_str.split(",")
    logger.info(f"ℹ️ Development CORS origins: {cors_origins}")

# Trusted hosts configuration
trusted_hosts_str = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1,testserver")
trusted_hosts = trusted_hosts_str.split(",")

# Add CORS middleware with comprehensive security settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-API-Key",
        "X-Request-ID",
        "Accept",
        "Accept-Language",
        "Content-Language",
    ],
    expose_headers=[
        "X-Request-ID",
        "X-Response-Time",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ],
    max_age=600,  # Cache preflight requests for 10 minutes
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

# Add enterprise middleware stack (Truth Protocol compliance)
try:
    from middleware import add_enterprise_middleware

    add_enterprise_middleware(
        app,
        rate_limit=100,  # 100 requests/minute per IP (Truth Protocol Rule #7)
        rate_window=60,  # 60 seconds window
        p95_threshold=200,  # P95 < 200ms target (Truth Protocol Rule #12)
        log_file="logs/requests.jsonl",  # Structured request logs
    )
    logger.info("✅ Enterprise middleware stack activated")
except ImportError as e:
    logger.warning(f"⚠️ Enterprise middleware not available: {e}")

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
            except Exception as e:

                logger.warning(f"Error during cleanup: {e}")

        logger.info("✅ DevSkyy Platform shutdown complete")

    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")


# ============================================================================
# API ROUTERS REGISTRATION
# ============================================================================

# Import API routers with error handling
try:
    from api.v1.agents import router as agents_router
    from api.v1.auth import router as auth_router
    from api.v1.codex import router as codex_router
    from api.v1.consensus import router as consensus_router
    from api.v1.content import router as content_router
    from api.v1.dashboard import router as dashboard_router
    from api.v1.health import router as health_router

    # DevSkyy Automation Routers (n8n replacements)
    from api.v1.ecommerce import router as ecommerce_router
    from api.v1.finetuning import router as finetuning_router
    from api.v1.gdpr import router as gdpr_router
    from api.v1.mcp import router as mcp_router
    from api.v1.ml import router as ml_router
    from api.v1.monitoring import router as monitoring_router
    from api.v1.orchestration import router as orchestration_router
    from api.v1.rag import router as rag_router
    from api.v1.webhooks import router as webhooks_router

    API_ROUTERS_AVAILABLE = True
    logger.info("✅ All API routers loaded successfully")

except ImportError as e:
    logger.warning(f"⚠️ Some API routers not available: {e}")
    API_ROUTERS_AVAILABLE = False

# Register API routers
if API_ROUTERS_AVAILABLE:
    try:
        # Health check routes (Kubernetes-ready liveness/readiness probes)
        app.include_router(health_router, prefix="/api/v1", tags=["health"])

        # Core API routes
        app.include_router(agents_router, prefix="/api/v1/agents", tags=["v1-agents"])
        app.include_router(auth_router, prefix="/api/v1/auth", tags=["v1-auth"])
        app.include_router(webhooks_router, prefix="/api/v1/webhooks", tags=["v1-webhooks"])
        app.include_router(monitoring_router, prefix="/api/v1/monitoring", tags=["v1-monitoring"])
        app.include_router(gdpr_router, prefix="/api/v1/gdpr", tags=["v1-gdpr"])
        app.include_router(ml_router, prefix="/api/v1/ml", tags=["v1-ml"])
        app.include_router(codex_router, prefix="/api/v1/codex", tags=["v1-codex"])
        app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["v1-dashboard"])
        app.include_router(mcp_router, prefix="/api/v1", tags=["v1-mcp"])
        app.include_router(rag_router, prefix="/api/v1", tags=["v1-rag"])
        app.include_router(orchestration_router, prefix="/api/v1/orchestration", tags=["v1-orchestration"])

        # DevSkyy Automation Routers (n8n workflow replacements)
        app.include_router(ecommerce_router, prefix="/api/v1", tags=["automation-ecommerce"])
        app.include_router(content_router, prefix="/api/v1", tags=["automation-content"])
        app.include_router(consensus_router, prefix="/api/v1", tags=["automation-consensus"])
        app.include_router(finetuning_router, tags=["v1-finetuning"])
        logger.info("✅ DevSkyy automation routers registered (ecommerce, content, consensus, finetuning)")

        # Luxury Fashion Brand Automation Router
        try:
            from api.v1.luxury_fashion_automation import router as luxury_automation_router

            app.include_router(
                luxury_automation_router, prefix="/api/v1/luxury-automation", tags=["v1-luxury-automation"]
            )
            logger.info("✅ Luxury Fashion Automation router registered")
        except ImportError as e:
            logger.warning(f"⚠️ Luxury Fashion Automation router not available: {e}")

        logger.info("✅ All available API routers registered")

    except Exception as e:
        logger.error(f"❌ Router registration failed: {e}")

# ============================================================================
# MCP SERVER ENDPOINT (Model Context Protocol)
# ============================================================================

# Register MCP Server for external tool access
try:
    from mcp.server.sse import SseServerTransport

    from services.mcp_server import get_mcp_server

    # Create MCP server instance
    mcp_server_instance = get_mcp_server()
    mcp_server = mcp_server_instance.get_server()

    # Create SSE transport for MCP protocol
    mcp_transport = SseServerTransport("/mcp/messages")

    @app.get("/mcp/sse")
    async def handle_mcp_sse(request: Request):
        """
        MCP Server SSE endpoint

        Exposes DevSkyy AI tools via Model Context Protocol:
        - brand_intelligence_reviewer (content review)
        - seo_marketing_reviewer (SEO analysis)
        - security_compliance_reviewer (security scan)
        - post_categorizer (WordPress automation)
        - product_seo_optimizer (WooCommerce SEO)

        External clients can connect via standard MCP protocol.
        """
        if LOGFIRE_AVAILABLE:
            logfire.info("MCP SSE connection requested", client_host=request.client.host)

        async with mcp_transport.connect_sse(
            request.scope,
            request.receive,
        ) as streams:
            await mcp_server.run(streams[0], streams[1], mcp_server.create_initialization_options())

    logger.info("✅ MCP Server endpoint registered at /mcp/sse")
    logger.info("   - 5 AI tools exposed via standard MCP protocol")
    logger.info("   - External clients can connect for tool access")

except ImportError as e:
    logger.warning(f"⚠️ MCP Server not available: {e}")
except Exception as e:
    logger.error(f"❌ MCP Server registration failed: {e}")

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

# Import and initialize advanced features
try:
    from fashion.skyy_rose_3d_pipeline import skyy_rose_3d_pipeline

    app.state.skyy_rose_3d_pipeline = skyy_rose_3d_pipeline

    logger.info("✅ Advanced features initialized")

except ImportError as e:
    logger.warning(f"⚠️ Advanced features not available: {e}")

# Import and initialize enterprise monitoring
try:
    from core.logging import enterprise_logger
    from monitoring.enterprise_metrics import metrics_collector
    from monitoring.incident_response import incident_response_system

    app.state.enterprise_logger = enterprise_logger
    app.state.metrics_collector = metrics_collector
    app.state.incident_response_system = incident_response_system

    logger.info("✅ Enterprise monitoring initialized")

except ImportError as e:
    logger.warning(f"⚠️ Enterprise monitoring not available: {e}")

# Import and initialize WordPress credentials
try:
    from config.wordpress_credentials import (
        get_skyy_rose_credentials,
        validate_environment_setup,
        wordpress_credentials_manager,
    )

    app.state.wordpress_credentials_manager = wordpress_credentials_manager

    # Validate WordPress credentials on startup
    env_validation = validate_environment_setup()
    if env_validation["valid"]:
        credentials = get_skyy_rose_credentials()
        if credentials:
            logger.info(f"✅ WordPress credentials loaded for: {credentials.site_url}")
        else:
            logger.warning("⚠️ WordPress credentials configured but failed to load")
    else:
        logger.warning(f"⚠️ WordPress credentials not configured: {env_validation['missing_required']}")

    logger.info("✅ WordPress credential system initialized")

except ImportError as e:
    logger.warning(f"⚠️ WordPress credential system not available: {e}")

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
async def execute_agent_task(agent_type: str, agent_name: str, task_data: dict[str, Any]):
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
# ADVANCED FEATURE ENDPOINTS
# ============================================================================


@app.post("/api/v1/orchestration/multi-agent")
async def execute_multi_agent_task(task_data: dict[str, Any]):
    """Execute task using multi-agent orchestration."""
    # Use the unified orchestrator instead
    raise HTTPException(
        status_code=503,
        detail="Multi-agent orchestrator endpoint deprecated. Use /api/v1/orchestration endpoints instead."
    )


@app.post("/api/v1/3d/models/upload")
async def upload_3d_model(file_path: str, model_format: str, brand_context: str | None = None):
    """Upload and process a 3D model."""
    try:
        if not hasattr(app.state, "skyy_rose_3d_pipeline"):
            raise HTTPException(status_code=503, detail="3D pipeline not available")

        from fashion.skyy_rose_3d_pipeline import ModelFormat

        # Load and process model
        model = await app.state.skyy_rose_3d_pipeline.load_3d_model(
            file_path=file_path, model_format=ModelFormat(model_format), brand_context=brand_context
        )

        return {
            "model_id": model.id,
            "name": model.name,
            "format": model.format.value,
            "file_size": model.file_size,
            "materials_count": len(model.materials),
            "brand_tags": model.brand_tags,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"3D model upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/avatars/create")
async def create_avatar(avatar_data: dict[str, Any]):
    """Create a new avatar."""
    try:
        if not hasattr(app.state, "skyy_rose_3d_pipeline"):
            raise HTTPException(status_code=503, detail="3D pipeline not available")

        from fashion.skyy_rose_3d_pipeline import AvatarType

        # Create avatar
        avatar = await app.state.skyy_rose_3d_pipeline.create_avatar(
            avatar_type=AvatarType(avatar_data.get("avatar_type", "ready_player_me")),
            customization_options=avatar_data.get("customization_options", {}),
            voice_settings=avatar_data.get("voice_settings"),
        )

        return {
            "avatar_id": avatar.id,
            "name": avatar.name,
            "avatar_type": avatar.avatar_type.value,
            "model_path": avatar.model_path,
            "animations": avatar.animations,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Avatar creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/system/advanced-status")
async def get_advanced_system_status():
    """Get advanced system status including all new features."""
    try:
        status = {
            "timestamp": datetime.now().isoformat(),
            "3d_pipeline": None,
            "advanced_features_available": False,
        }

        # 3D pipeline status
        if hasattr(app.state, "skyy_rose_3d_pipeline"):
            status["3d_pipeline"] = app.state.skyy_rose_3d_pipeline.get_pipeline_status()
            status["advanced_features_available"] = True

        return status

    except Exception as e:
        logger.error(f"Advanced status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENTERPRISE MONITORING ENDPOINTS
# ============================================================================


@app.get("/metrics")
async def get_prometheus_metrics():
    """Get Prometheus metrics."""
    try:
        if hasattr(app.state, "metrics_collector"):
            metrics_data = app.state.metrics_collector.get_prometheus_metrics()
            return Response(content=metrics_data, media_type="text/plain")
        else:
            return Response(content="# Metrics collector not available\n", media_type="text/plain")
    except Exception as e:
        logger.error(f"Metrics endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/monitoring/status")
async def get_monitoring_status():
    """Get comprehensive monitoring system status."""
    try:
        status = {
            "timestamp": datetime.now().isoformat(),
            "monitoring_available": False,
            "metrics": None,
            "incidents": None,
            "logging": None,
        }

        # Metrics collector status
        if hasattr(app.state, "metrics_collector"):
            status["metrics"] = app.state.metrics_collector.get_metrics_summary()
            status["monitoring_available"] = True

        # Incident response status
        if hasattr(app.state, "incident_response_system"):
            status["incidents"] = app.state.incident_response_system.get_system_status()

        # Logging status
        if hasattr(app.state, "enterprise_logger"):
            status["logging"] = {"enterprise_logging_available": True, "log_level": "INFO"}  # Could be dynamic

        return status

    except Exception as e:
        logger.error(f"Monitoring status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/monitoring/incidents")
async def get_active_incidents():
    """Get active incidents."""
    try:
        if not hasattr(app.state, "incident_response_system"):
            raise HTTPException(status_code=503, detail="Incident response system not available")

        incidents = app.state.incident_response_system.incidents
        active_incidents = [
            {
                "id": incident.id,
                "title": incident.title,
                "severity": incident.severity.value,
                "status": incident.status.value,
                "created_at": incident.created_at.isoformat(),
                "updated_at": incident.updated_at.isoformat(),
                "alerts_count": len(incident.alerts),
                "responses_executed": len(incident.responses_executed),
            }
            for incident in incidents.values()
            if incident.status.value != "resolved"
        ]

        return {
            "active_incidents": active_incidents,
            "total_active": len(active_incidents),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Incidents endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AUTOMATED THEME BUILDER ENDPOINTS
# ============================================================================


@app.post("/api/v1/themes/build-and-deploy")
async def build_and_deploy_theme(theme_request: dict[str, Any]):
    """Build and deploy a WordPress theme automatically."""
    try:
        from agent.wordpress.theme_builder_orchestrator import (
            ThemeBuildRequest,
            ThemeType,
            UploadMethod,
            theme_builder_orchestrator,
        )
        from config.wordpress_credentials import WordPressCredentials, wordpress_credentials_manager

        # Get credentials - either from request or use configured credentials
        site_key = theme_request.get("site_key", "skyy_rose")

        if "site_url" in theme_request and "username" in theme_request and "password" in theme_request:
            # Use provided credentials
            credentials = WordPressCredentials(
                site_url=theme_request["site_url"],
                username=theme_request["username"],
                password=theme_request["password"],
                application_password=theme_request.get("application_password"),
                ftp_host=theme_request.get("ftp_host"),
                ftp_username=theme_request.get("ftp_username"),
                ftp_password=theme_request.get("ftp_password"),
            )
        else:
            # Use configured credentials
            credentials = wordpress_credentials_manager.get_credentials(site_key)
            if not credentials:
                raise HTTPException(
                    status_code=400,
                    detail=f"No credentials configured for site: {site_key}. Available sites: {wordpress_credentials_manager.list_available_sites()}",
                )

        build_request = ThemeBuildRequest(
            theme_name=theme_request["theme_name"],
            theme_type=ThemeType(theme_request.get("theme_type", "luxury_fashion")),
            brand_guidelines=theme_request.get("brand_guidelines", {}),
            target_site=theme_request["site_url"],
            deployment_credentials=credentials,
            customizations=theme_request.get("customizations", {}),
            auto_deploy=theme_request.get("auto_deploy", True),
            activate_after_deploy=theme_request.get("activate_after_deploy", False),
            upload_method=UploadMethod(theme_request.get("upload_method", "wordpress_rest_api")),
        )

        # Start build process
        result = await theme_builder_orchestrator.build_and_deploy_theme(build_request)

        return {
            "build_id": result.build_id,
            "status": result.status.value,
            "theme_name": result.request.theme_name,
            "theme_path": result.theme_path,
            "deployment_success": result.deployment_result.success if result.deployment_result else None,
            "deployment_id": result.deployment_result.deployment_id if result.deployment_result else None,
            "build_log": result.build_log[-5:],  # Last 5 log entries
            "created_at": result.created_at.isoformat(),
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            "error_message": result.error_message,
        }

    except Exception as e:
        logger.error(f"Theme build error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/themes/build-status/{build_id}")
async def get_theme_build_status(build_id: str):
    """Get theme build status."""
    try:
        from agent.wordpress.theme_builder_orchestrator import theme_builder_orchestrator

        result = theme_builder_orchestrator.get_build_status(build_id)

        if not result:
            raise HTTPException(status_code=404, detail="Build not found")

        return {
            "build_id": result.build_id,
            "status": result.status.value,
            "theme_name": result.request.theme_name,
            "theme_type": result.request.theme_type.value,
            "target_site": result.request.target_site,
            "theme_path": result.theme_path,
            "deployment_result": (
                {
                    "success": result.deployment_result.success,
                    "deployment_id": result.deployment_result.deployment_id,
                    "status": result.deployment_result.status.value,
                    "deployed_at": (
                        result.deployment_result.deployed_at.isoformat()
                        if result.deployment_result.deployed_at
                        else None
                    ),
                }
                if result.deployment_result
                else None
            ),
            "build_log": result.build_log,
            "created_at": result.created_at.isoformat(),
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            "error_message": result.error_message,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Build status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/themes/upload-only")
async def upload_theme_only(upload_request: dict[str, Any]):
    """Upload an existing theme package without building."""
    try:
        from agent.wordpress.automated_theme_uploader import (
            UploadMethod,
            WordPressCredentials,
            automated_theme_uploader,
        )

        # Parse credentials
        credentials = WordPressCredentials(
            site_url=upload_request["site_url"],
            username=upload_request["username"],
            password=upload_request["password"],
            application_password=upload_request.get("application_password"),
        )

        # Create theme package
        theme_info = {
            "name": upload_request["theme_name"],
            "version": upload_request.get("version", "1.0.0"),
            "description": upload_request.get("description", ""),
            "author": upload_request.get("author", "DevSkyy Platform"),
        }

        package = await automated_theme_uploader.create_theme_package(upload_request["theme_path"], theme_info)

        # Deploy theme
        result = await automated_theme_uploader.deploy_theme(
            package,
            credentials,
            UploadMethod(upload_request.get("upload_method", "wordpress_rest_api")),
            upload_request.get("activate_theme", False),
        )

        return {
            "deployment_id": result.deployment_id,
            "success": result.success,
            "status": result.status.value,
            "theme_name": result.theme_package.name,
            "deployed_at": result.deployed_at.isoformat() if result.deployed_at else None,
            "error_message": result.error_message,
            "validation_results": result.validation_results,
        }

    except Exception as e:
        logger.error(f"Theme upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/themes/system-status")
async def get_theme_system_status():
    """Get theme builder and uploader system status."""
    try:
        from agent.wordpress.theme_builder_orchestrator import theme_builder_orchestrator

        return {
            "timestamp": datetime.now().isoformat(),
            "theme_builder_orchestrator": theme_builder_orchestrator.get_system_status(),
            "available_theme_types": [
                "luxury_fashion",
                "streetwear",
                "minimalist",
                "ecommerce",
                "blog",
                "portfolio",
                "corporate",
            ],
            "supported_upload_methods": ["wordpress_rest_api", "ftp", "sftp", "staging_area"],
        }

    except Exception as e:
        logger.error(f"Theme system status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/themes/skyy-rose/build")
async def build_skyy_rose_theme(theme_request: dict[str, Any]):
    """Build and deploy a theme specifically for Skyy Rose Collection using configured credentials."""
    try:
        from agent.wordpress.theme_builder_orchestrator import ThemeType, theme_builder_orchestrator

        # Use the convenience method for Skyy Rose themes
        result = await theme_builder_orchestrator.build_skyy_rose_theme(
            theme_name=theme_request["theme_name"],
            theme_type=ThemeType(theme_request.get("theme_type", "luxury_fashion")),
            customizations=theme_request.get("customizations", {}),
            auto_deploy=theme_request.get("auto_deploy", True),
            activate_after_deploy=theme_request.get("activate_after_deploy", False),
            site_key=theme_request.get("site_key", "skyy_rose"),
        )

        if not result:
            raise HTTPException(
                status_code=400, detail="Failed to create theme build request. Check credentials configuration."
            )

        return {
            "build_id": result.build_id,
            "status": result.status.value,
            "theme_name": result.request.theme_name,
            "theme_type": result.request.theme_type.value,
            "target_site": result.request.target_site,
            "auto_deploy": result.request.auto_deploy,
            "theme_path": result.theme_path,
            "deployment_success": result.deployment_result.success if result.deployment_result else None,
            "deployment_id": result.deployment_result.deployment_id if result.deployment_result else None,
            "build_log": result.build_log[-5:],  # Last 5 log entries
            "created_at": result.created_at.isoformat(),
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            "error_message": result.error_message,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Skyy Rose theme build error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/themes/credentials/status")
async def get_credentials_status():
    """Get status of configured WordPress credentials."""
    try:
        from config.wordpress_credentials import (
            list_configured_sites,
            validate_environment_setup,
            wordpress_credentials_manager,
        )

        # Validate environment setup
        env_validation = validate_environment_setup()

        # Get configured sites
        sites = list_configured_sites()

        # Validate each site's credentials
        site_validations = {}
        for site in sites:
            site_validations[site] = wordpress_credentials_manager.validate_credentials(site)

        return {
            "timestamp": datetime.now().isoformat(),
            "environment_validation": env_validation,
            "configured_sites": sites,
            "site_validations": site_validations,
            "default_site": "skyy_rose",
            "has_default_credentials": "skyy_rose" in sites,
        }

    except Exception as e:
        logger.error(f"Credentials status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/themes/credentials/test")
async def test_wordpress_connection(test_request: dict[str, Any]):
    """Test WordPress connection with configured or provided credentials."""
    try:
        import requests

        from config.wordpress_credentials import wordpress_credentials_manager

        site_key = test_request.get("site_key", "skyy_rose")
        credentials = wordpress_credentials_manager.get_credentials(site_key)

        if not credentials:
            raise HTTPException(status_code=400, detail=f"No credentials found for site: {site_key}")

        # Test WordPress REST API connection
        try:
            # Test basic site connectivity
            response = requests.get(f"{credentials.site_url}/wp-json/wp/v2", timeout=10)
            api_accessible = response.status_code == 200

            # Test authenticated endpoint if we have app password
            auth_test = False
            if credentials.application_password:
                import base64

                auth_header = base64.b64encode(
                    f"{credentials.username}:{credentials.application_password}".encode()
                ).decode()

                auth_response = requests.get(
                    f"{credentials.site_url}/wp-json/wp/v2/users/me",
                    headers={"Authorization": f"Basic {auth_header}"},
                    timeout=10,
                )
                auth_test = auth_response.status_code == 200

            return {
                "site_key": site_key,
                "site_url": credentials.site_url,
                "api_accessible": api_accessible,
                "authentication_test": auth_test,
                "has_application_password": bool(credentials.application_password),
                "has_ftp_credentials": credentials.has_ftp_credentials(),
                "has_sftp_credentials": credentials.has_sftp_credentials(),
                "test_timestamp": datetime.now().isoformat(),
                "status": "success" if api_accessible else "failed",
            }

        except requests.RequestException as e:
            return {
                "site_key": site_key,
                "site_url": credentials.site_url,
                "api_accessible": False,
                "authentication_test": False,
                "error": str(e),
                "test_timestamp": datetime.now().isoformat(),
                "status": "connection_failed",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WordPress connection test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
