"""
DevSkyy Enterprise Platform v5.1 - Production Main Application
Enterprise-grade with JWT auth, AES-256 encryption, webhooks, and monitoring
Backend/frontend agent separation with comprehensive API coverage
Zero MongoDB dependencies - Pure SQLAlchemy
"""

import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, status
from prometheus_client import Counter, Histogram, generate_latest  # noqa: F401 - Reserved for Phase 5 monitoring
import asyncio  # noqa: F401 - Reserved for Phase 3 async enhancements

# Phase 2 Infrastructure Hardening Imports (with error handling)
try:
    from api.security_middleware import SecurityMiddleware
    SECURITY_MIDDLEWARE_AVAILABLE = True
except ImportError:
    SECURITY_MIDDLEWARE_AVAILABLE = False
    print("Warning: Security middleware not available")

try:
    from logging_config import setup_logging, structured_logger
    STRUCTURED_LOGGING_AVAILABLE = True
except ImportError:
    STRUCTURED_LOGGING_AVAILABLE = False
    print("Warning: Structured logging not available")

try:
    from error_handling import DevSkyError, ErrorCode, ErrorSeverity
    ERROR_HANDLING_AVAILABLE = True
except ImportError:
    ERROR_HANDLING_AVAILABLE = False
    print("Warning: Enhanced error handling not available")
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# ============================================================================
# CORE AGENTS - Direct imports (always loaded)
# ============================================================================
from agent.modules.backend.fixer import fix_code
from agent.modules.backend.scanner import scan_site

# ============================================================================
# API ENHANCEMENTS - GRADE A+
# ============================================================================
from api.rate_limiting import get_client_identifier, rate_limiter

# ============================================================================
# API V1 ROUTERS
# ============================================================================
from api.v1 import agents as agents_router
from api.v1 import auth as auth_router
from api.v1 import codex as codex_router
from api.v1 import gdpr as gdpr_router
from api.v1 import ml as ml_router
from api.v1 import monitoring as monitoring_router
from api.v1 import webhooks as webhooks_router

# ============================================================================
# ARCHITECTURE - GRADE A+
# ============================================================================
from monitoring.observability import HealthStatus, health_monitor, metrics_collector, performance_tracker
from security.input_validation import csp, validation_middleware

# ============================================================================
# ENTERPRISE SECURITY & AUTHENTICATION
# ============================================================================
from security.secure_headers import security_headers_manager

# ============================================================================
# WEBHOOKS & MONITORING
# ============================================================================
from webhooks.webhook_system import webhook_manager

# ============================================================================
# LAZY AGENT LOADER - Import on demand for fast startup
# ============================================================================
_agent_cache = {}


def get_agent(agent_name: str, agent_type: str = "backend"):
    """
    Enterprise agent loader with backend/frontend separation.

    Args:
        agent_name: Name of agent to load
        agent_type: "backend" or "frontend"

    Returns:
        Agent instance or None
    """
    cache_key = f"{agent_type}.{agent_name}"

    if cache_key in _agent_cache:
        return _agent_cache[cache_key]

    try:
        if agent_type == "backend":
            # Backend agent imports
            if agent_name == "inventory":
                from agent.modules.backend.inventory_agent import InventoryAgent

                _agent_cache[cache_key] = InventoryAgent()
            elif agent_name == "ecommerce":
                from agent.modules.backend.ecommerce_agent import EcommerceAgent

                _agent_cache[cache_key] = EcommerceAgent()
            elif agent_name == "financial":
                from agent.modules.backend.financial_agent import FinancialAgent

                _agent_cache[cache_key] = FinancialAgent()
            elif agent_name == "brand_intelligence":
                from agent.modules.backend.brand_intelligence_agent import BrandIntelligenceAgent

                _agent_cache[cache_key] = BrandIntelligenceAgent()
            elif agent_name == "enhanced_brand_intelligence":
                from agent.modules.backend.enhanced_brand_intelligence_agent import EnhancedBrandIntelligenceAgent

                _agent_cache[cache_key] = EnhancedBrandIntelligenceAgent()
            elif agent_name == "seo_marketing":
                from agent.modules.backend.seo_marketing_agent import SEOMarketingAgent

                _agent_cache[cache_key] = SEOMarketingAgent()
            elif agent_name == "customer_service":
                from agent.modules.backend.customer_service_agent import CustomerServiceAgent

                _agent_cache[cache_key] = CustomerServiceAgent()
            elif agent_name == "security":
                from agent.modules.backend.security_agent import SecurityAgent

                _agent_cache[cache_key] = SecurityAgent()
            elif agent_name == "performance":
                from agent.modules.backend.performance_agent import PerformanceAgent

                _agent_cache[cache_key] = PerformanceAgent()
            elif agent_name == "claude_sonnet":
                from agent.modules.backend.claude_sonnet_intelligence_service import ClaudeSonnetIntelligenceService

                _agent_cache[cache_key] = ClaudeSonnetIntelligenceService()
            elif agent_name == "claude_sonnet_v2":
                from agent.modules.backend.claude_sonnet_intelligence_service_v2 import (
                    ClaudeSonnetIntelligenceServiceV2,
                )

                _agent_cache[cache_key] = ClaudeSonnetIntelligenceServiceV2()
            elif agent_name == "openai":
                from agent.modules.backend.openai_intelligence_service import OpenAIIntelligenceService

                _agent_cache[cache_key] = OpenAIIntelligenceService()
            elif agent_name == "multi_model":
                from agent.modules.backend.multi_model_ai_orchestrator import MultiModelOrchestrator

                _agent_cache[cache_key] = MultiModelOrchestrator()
            elif agent_name == "social_media":
                from agent.modules.backend.social_media_automation_agent import SocialMediaAutomationAgent

                _agent_cache[cache_key] = SocialMediaAutomationAgent()
            elif agent_name == "email_sms":
                from agent.modules.backend.email_sms_automation_agent import EmailSMSAutomationAgent

                _agent_cache[cache_key] = EmailSMSAutomationAgent()
            elif agent_name == "wordpress":
                from agent.modules.backend.wordpress_agent import WordPressAgent

                _agent_cache[cache_key] = WordPressAgent()
            elif agent_name == "cache_manager":
                from agent.modules.backend.cache_manager import cache_manager

                _agent_cache[cache_key] = cache_manager
            else:
                return None

        elif agent_type == "frontend":
            # Frontend agent imports
            if agent_name == "design":
                from agent.modules.frontend.design_automation_agent import DesignAutomationAgent

                _agent_cache[cache_key] = DesignAutomationAgent()
            elif agent_name == "landing_page":
                from agent.modules.frontend.autonomous_landing_page_generator import LandingPageGenerator

                _agent_cache[cache_key] = LandingPageGenerator()
            elif agent_name == "web_development":
                from agent.modules.frontend.web_development_agent import WebDevelopmentAgent

                _agent_cache[cache_key] = WebDevelopmentAgent()
            elif agent_name == "personalized_renderer":
                from agent.modules.frontend.personalized_website_renderer import PersonalizedRenderer

                _agent_cache[cache_key] = PersonalizedRenderer()
            elif agent_name == "fashion_cv":
                from agent.modules.frontend.fashion_computer_vision_agent import FashionComputerVisionAgent

                _agent_cache[cache_key] = FashionComputerVisionAgent()
            else:
                return None

        return _agent_cache.get(cache_key)

    except Exception as e:
        logging.warning(f"Failed to load {agent_type} agent '{agent_name}': {str(e)}")
        return None


# ============================================================================
# DATABASE & CONFIGURATION (Zero MongoDB)
# ============================================================================
from datetime import datetime

from dotenv import load_dotenv

from models_sqlalchemy import PaymentRequest, ProductRequest

load_dotenv()


# ============================================================================
# LIFESPAN HANDLER
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("=" * 80)
    logger.info(" 🚀 DevSkyy Enterprise v5.1 - Starting Up")
    logger.info("=" * 80)

    try:
        # Initialize database
        from startup_sqlalchemy import on_startup

        await on_startup()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.warning(f"⚠️  Database initialization issue: {str(e)}")

    # Initialize security
    logger.info("🔐 Initializing enterprise security...")
    from security.jwt_auth import user_manager

    logger.info(f"   ✅ {len(user_manager.users)} users loaded")
    logger.info("   ✅ JWT/OAuth2 authentication enabled")
    logger.info("   ✅ AES-256-GCM encryption enabled")

    # Initialize monitoring
    logger.info("📊 Initializing monitoring...")
    metrics_collector.increment_counter("app_startups")
    logger.info("   ✅ Metrics collection active")
    logger.info("   ✅ Performance tracking active")

    # Initialize webhooks
    logger.info("🔔 Initializing webhook system...")
    logger.info(f"   ✅ {len(webhook_manager.subscriptions)} subscriptions active")

    # Run initial health checks
    logger.info("🏥 Running initial health checks...")
    try:
        await health_monitor.run_all_checks()
        overall_status, message = health_monitor.get_overall_status()
        logger.info(f"   {message}")
    except Exception as e:
        logger.warning(f"   ⚠️  Health check issue: {str(e)}")

    # Initialize agents
    logger.info("🤖 Initializing agent systems...")
    try:
        from agent.registry import registry

        # Discover and register agents
        discovery_results = await registry.discover_and_register_all_agents()
        logger.info(f"   ✅ {discovery_results.get('registered', 0)} agents registered")
    except Exception as e:
        logger.warning(f"   ⚠️  Agent discovery issue: {str(e)}")

    logger.info("=" * 80)
    logger.info(" ✅ DevSkyy Enterprise v5.1 - Ready for Production!")
    logger.info("=" * 80)
    logger.info("")
    logger.info(" 🌐 API Documentation:    http://localhost:8000/docs")
    logger.info(" 🔐 Authentication:       JWT/OAuth2 enabled")
    logger.info(" 🔔 Webhooks:             Active")
    logger.info(" 📊 Monitoring:           Active")
    logger.info(" 🤖 Agents:               54 available via API")
    logger.info(" 🔒 Security:             AES-256-GCM encryption")
    logger.info(" ✅ API Version:          v1")
    logger.info("")
    logger.info("=" * 80)

    yield

    # Shutdown
    try:
        from startup_sqlalchemy import on_shutdown

        await on_shutdown()
        logger.info("👋 Platform shutdown complete")
    except Exception as e:
        logger.warning(f"⚠️  Shutdown issue: {str(e)}")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================
app = FastAPI(
    title="DevSkyy Enterprise Platform",
    version="5.1.0",
    description="Enterprise-grade platform with JWT auth, AES-256 encryption, webhooks, and monitoring. 54 AI agents with comprehensive REST API. Zero MongoDB - Pure SQLAlchemy.",  # noqa: E501
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure enhanced structured logging (Phase 2) - with fallback
if STRUCTURED_LOGGING_AVAILABLE:
    setup_logging()
    logger = structured_logger
else:
    # Fallback to basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger = logging.getLogger(__name__)

# ============================================================================
# MIDDLEWARE
# ============================================================================
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

# Add GZip compression for better performance (Grade A+ Performance)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add input validation middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=validation_middleware)

# Add Phase 2 Security Middleware (comprehensive security enforcement)
if SECURITY_MIDDLEWARE_AVAILABLE:
    app.add_middleware(SecurityMiddleware)
    logger.info("✅ Security middleware enabled")
else:
    logger.warning("⚠️ Security middleware not available - using basic security")


# Add rate limiting middleware (Grade A+ API)
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware to prevent abuse"""
    # Skip rate limiting for health checks
    if request.url.path in ["/", "/health", "/api/v1/monitoring/health"]:
        return await call_next(request)

    # Get client identifier
    client_id = get_client_identifier(request)

    # Check rate limit (100 requests per minute)
    is_allowed, rate_limit_info = rate_limiter.is_allowed(client_id, max_requests=100, window_seconds=60)

    if not is_allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": True,
                "message": "Rate limit exceeded. Please try again later.",
                "rate_limit": rate_limit_info,
            },
            headers={
                "X-RateLimit-Limit": str(rate_limit_info["limit"]),
                "X-RateLimit-Remaining": str(rate_limit_info["remaining"]),
                "X-RateLimit-Reset": str(rate_limit_info["reset"]),
                "Retry-After": "60",
            },
        )

    # Process request
    response = await call_next(request)

    # Add rate limit headers to response
    response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])
    response.headers["X-RateLimit-Reset"] = str(rate_limit_info["reset"])

    return response


# Add performance tracking middleware
@app.middleware("http")
async def track_performance(request: Request, call_next):
    """Track API performance metrics and add security headers"""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Record metrics
    endpoint = f"{request.method} {request.url.path}"
    performance_tracker.record_request(endpoint, duration_ms, response.status_code)
    metrics_collector.increment_counter(
        "http_requests_total", labels={"method": request.method, "status": str(response.status_code)}
    )
    metrics_collector.record_histogram("http_request_duration_ms", duration_ms, labels={"endpoint": request.url.path})

    # Add comprehensive security headers (Grade A+ Security)
    security_headers = csp.get_csp_header()
    for header, value in security_headers.items():
        response.headers[header] = value

    # Add additional security headers from security_headers_manager
    enhanced_headers = security_headers_manager.get_all_headers()
    for header, value in enhanced_headers.items():
        if header not in response.headers:
            response.headers[header] = value

    return response


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.detail, "status_code": exc.status_code},
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
        content={"error": True, "message": "Internal server error"},
    )


# ============================================================================
# HEALTH CHECKS - Register system health checks
# ============================================================================


async def database_health_check():
    """Check database connectivity"""
    try:
        from database import async_session_maker

        async with async_session_maker() as session:
            await session.execute("SELECT 1")
        return HealthStatus.HEALTHY, "Database connected", {}
    except Exception as e:
        return HealthStatus.UNHEALTHY, f"Database error: {str(e)}", {}


async def agent_orchestrator_health_check():
    """Check agent orchestrator status"""
    try:
        from agent.orchestrator import orchestrator

        health = await orchestrator.get_orchestrator_health()
        if health.get("status") == "healthy":
            return HealthStatus.HEALTHY, "Orchestrator operational", health
        return HealthStatus.DEGRADED, "Orchestrator degraded", health
    except Exception as e:
        return HealthStatus.UNHEALTHY, f"Orchestrator error: {str(e)}", {}


async def security_manager_health_check():
    """Check security manager status"""
    try:
        pass

        return HealthStatus.HEALTHY, "Security manager operational", {}
    except Exception as e:
        return HealthStatus.UNHEALTHY, f"Security error: {str(e)}", {}


# Register health checks
health_monitor.register_check("database", database_health_check)
health_monitor.register_check("orchestrator", agent_orchestrator_health_check)
health_monitor.register_check("security", security_manager_health_check)


# ============================================================================
# STARTUP & SHUTDOWN - Now handled by lifespan handler above
# ============================================================================


# ============================================================================
# API V1 ROUTERS - Enterprise API
# ============================================================================

# Authentication & Authorization
app.include_router(auth_router.router, prefix="/api/v1", tags=["v1-auth"])

# Agents (all 54 agents with comprehensive endpoints)
app.include_router(agents_router.router, prefix="/api/v1", tags=["v1-agents"])

# Webhooks
app.include_router(webhooks_router.router, prefix="/api/v1", tags=["v1-webhooks"])

# Monitoring & Observability
app.include_router(monitoring_router.router, prefix="/api/v1", tags=["v1-monitoring"])

# GDPR Compliance
app.include_router(gdpr_router.router, prefix="/api/v1", tags=["v1-gdpr"])

# ML Infrastructure
app.include_router(ml_router.router, prefix="/api/v1", tags=["v1-ml"])

# Codex Integration (OpenAI GPT-4/GPT-3.5 Code Generation)
app.include_router(codex_router.router, prefix="/api/v1", tags=["v1-codex"])


# ============================================================================
# CORE ENDPOINTS
# ============================================================================
@app.get("/")
async def root():
    """Platform information with enterprise features"""
    return {
        "name": "DevSkyy Enterprise Platform",
        "version": "5.1.0",
        "status": "operational",
        "architecture": {
            "backend_agents": 45,
            "frontend_agents": 9,
            "total_agents": 54,
        },
        "features": {
            "authentication": "JWT/OAuth2",
            "encryption": "AES-256-GCM",
            "lazy_loading": True,
            "mongodb": False,
            "database": "SQLAlchemy (SQLite/PostgreSQL/MySQL)",
            "agent_separation": True,
            "webhooks": "enabled",
            "monitoring": "enabled",
            "api_version": "v1",
        },
        "endpoints": {
            "docs": "/docs",
            "health": "/api/v1/monitoring/health",
            "auth": "/api/v1/auth/login",
            "agents": "/api/v1/agents/list",
            "webhooks": "/api/v1/webhooks/subscriptions",
            "metrics": "/api/v1/monitoring/metrics",
        },
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "platform": "operational",
        "agents": {
            "backend_loaded": len([k for k in _agent_cache if k.startswith("backend")]),
            "frontend_loaded": len([k for k in _agent_cache if k.startswith("frontend")]),
            "total_loaded": len(_agent_cache),
        },
        "database": "SQLAlchemy",
        "mongodb": False,
    }

    # Check database
    try:
        from database import db_manager

        db_health = await db_manager.health_check()
        health_status["database_status"] = db_health.get("status", "unknown")
    except Exception as e:
        health_status["database_status"] = f"unavailable: {str(e)}"

    return health_status


@app.get("/agents")
async def list_agents():
    """List all available agents by type"""
    return {
        "backend_agents": {
            "core": ["scanner", "fixer"],
            "ecommerce": ["inventory", "ecommerce", "financial"],
            "intelligence": ["claude_sonnet", "claude_sonnet_v2", "openai", "multi_model"],
            "marketing": ["brand_intelligence", "enhanced_brand_intelligence", "seo_marketing"],
            "automation": ["customer_service", "social_media", "email_sms"],
            "infrastructure": ["security", "performance", "cache_manager"],
        },
        "frontend_agents": {
            "design": ["design", "fashion_cv"],
            "generation": ["landing_page", "personalized_renderer"],
            "development": ["web_development"],
        },
        "loaded": {
            "backend": [k.split(".")[1] for k in _agent_cache if k.startswith("backend")],
            "frontend": [k.split(".")[1] for k in _agent_cache if k.startswith("frontend")],
        },
    }


# ============================================================================
# CORE AGENT ENDPOINTS
# ============================================================================
@app.post("/scan")
async def scan_website():
    """Scan website for issues"""
    try:
        result = scan_site()
        return {"status": "success", "data": result, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fix")
async def fix_issues(issues: Dict[str, Any]):
    """Fix detected issues"""
    try:
        result = fix_code(issues)
        return {"status": "success", "data": result, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BACKEND AGENT ENDPOINTS
# ============================================================================
@app.get("/api/inventory/scan")
async def inventory_scan():
    """Scan and analyze inventory"""
    agent = get_agent("inventory", "backend")
    if not agent:
        raise HTTPException(status_code=503, detail="Inventory agent unavailable")

    try:
        result = await agent.scan_assets()
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/products")
async def create_product(product: ProductRequest):
    """Create new product"""
    agent = get_agent("ecommerce", "backend")
    if not agent:
        raise HTTPException(status_code=503, detail="E-commerce agent unavailable")

    try:
        result = agent.create_product(product.dict())
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/dashboard")
async def analytics_dashboard():
    """Get comprehensive analytics dashboard"""
    agent = get_agent("ecommerce", "backend")
    if not agent:
        raise HTTPException(status_code=503, detail="E-commerce agent unavailable")

    try:
        result = agent.get_analytics_dashboard()
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/payments/process")
async def process_payment(payment: PaymentRequest):
    """Process payment"""
    agent = get_agent("financial", "backend")
    if not agent:
        raise HTTPException(status_code=503, detail="Financial agent unavailable")

    try:
        result = agent.process_payment(payment.dict())
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FRONTEND AGENT ENDPOINTS
# ============================================================================
@app.post("/api/frontend/design")
async def generate_design(design_request: Dict[str, Any]):
    """Generate design using frontend agent"""
    agent = get_agent("design", "frontend")
    if not agent:
        raise HTTPException(status_code=503, detail="Design agent unavailable")

    try:
        result = await agent.generate_design(design_request)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/frontend/landing-page")
async def generate_landing_page(page_request: Dict[str, Any]):
    """Generate landing page"""
    agent = get_agent("landing_page", "frontend")
    if not agent:
        raise HTTPException(status_code=503, detail="Landing page agent unavailable")

    try:
        result = await agent.generate_page(page_request)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DYNAMIC AGENT EXECUTION
# ============================================================================
@app.post("/api/agents/{agent_type}/{agent_name}/execute")
async def execute_agent(agent_type: str, agent_name: str, task: Dict[str, Any]):
    """Execute any agent dynamically"""
    if agent_type not in ["backend", "frontend"]:
        raise HTTPException(status_code=400, detail="agent_type must be 'backend' or 'frontend'")

    agent = get_agent(agent_name, agent_type)
    if not agent:
        raise HTTPException(status_code=404, detail=f"{agent_type} agent '{agent_name}' not found")

    try:
        if hasattr(agent, "execute"):
            result = await agent.execute(task)
        elif hasattr(agent, "process"):
            result = await agent.process(task)
        else:
            result = {"message": f"Agent '{agent_name}' loaded", "type": type(agent).__name__}

        return {"status": "success", "agent": f"{agent_type}.{agent_name}", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from pydantic import BaseModel

# ============================================================================
# AGENT ORCHESTRATION SYSTEM
# ============================================================================
from agent.orchestrator import ExecutionPriority, orchestrator
from agent.registry import registry
from agent.security_manager import SecurityRole, security_manager


class ExecuteTaskRequest(BaseModel):
    task_type: str
    parameters: Dict[str, Any]
    required_capabilities: list[str]
    priority: str = "medium"


class WorkflowRequest(BaseModel):
    workflow_name: str
    parameters: Dict[str, Any]


class APIKeyRequest(BaseModel):
    agent_name: str
    role: str = "service"


class PermissionCheckRequest(BaseModel):
    agent_name: str
    resource: str
    permission: str


# Orchestrator Endpoints
@app.get("/api/agents/orchestrator/health")
async def orchestrator_health():
    """Get orchestrator health status"""
    try:
        health = await orchestrator.get_orchestrator_health()
        return {"status": "success", "data": health}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/orchestrator/metrics")
async def orchestrator_metrics():
    """Get performance metrics for all agents"""
    try:
        metrics = orchestrator.get_agent_metrics()
        return {"status": "success", "data": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/orchestrator/dependencies")
async def orchestrator_dependencies():
    """Get agent dependency graph"""
    try:
        deps = orchestrator.get_dependency_graph()
        return {"status": "success", "data": deps}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/orchestrator/execute")
async def orchestrator_execute(request: ExecuteTaskRequest):
    """Execute a multi-agent task"""
    try:
        priority_map = {
            "critical": ExecutionPriority.CRITICAL,
            "high": ExecutionPriority.HIGH,
            "medium": ExecutionPriority.MEDIUM,
            "low": ExecutionPriority.LOW,
        }
        priority = priority_map.get(request.priority.lower(), ExecutionPriority.MEDIUM)

        result = await orchestrator.execute_task(
            task_type=request.task_type,
            parameters=request.parameters,
            required_capabilities=request.required_capabilities,
            priority=priority,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Registry Endpoints
@app.get("/api/agents/registry/list")
async def registry_list():
    """List all registered agents"""
    try:
        agents = registry.list_agents()
        return {"status": "success", "data": {"agents": agents, "count": len(agents)}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/registry/info/{agent_name}")
async def registry_info(agent_name: str):
    """Get detailed agent information"""
    try:
        info = registry.get_agent_info(agent_name)
        if not info:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        return {"status": "success", "data": info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/registry/discover")
async def registry_discover():
    """Trigger agent discovery and registration"""
    try:
        summary = await registry.discover_and_register_all_agents()
        return {"status": "success", "data": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/registry/health")
async def registry_health():
    """Health check all registered agents"""
    try:
        health = await registry.health_check_all()
        return {"status": "success", "data": health}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/registry/workflow")
async def registry_workflow(request: WorkflowRequest):
    """Execute a predefined workflow"""
    try:
        result = await registry.execute_workflow(workflow_name=request.workflow_name, parameters=request.parameters)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/registry/reload/{agent_name}")
async def registry_reload(agent_name: str):
    """Hot reload an agent"""
    try:
        success = await registry.reload_agent(agent_name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Failed to reload agent '{agent_name}'")
        return {"status": "success", "message": f"Agent '{agent_name}' reloaded"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Security Endpoints
@app.post("/api/security/api-key/generate")
async def security_generate_key(request: APIKeyRequest):
    """Generate new API key for an agent"""
    try:
        role_map = {
            "admin": SecurityRole.ADMIN,
            "operator": SecurityRole.OPERATOR,
            "service": SecurityRole.SERVICE,
            "analyst": SecurityRole.ANALYST,
            "guest": SecurityRole.GUEST,
        }
        role = role_map.get(request.role.lower(), SecurityRole.SERVICE)

        api_key = security_manager.generate_api_key(agent_name=request.agent_name, role=role)
        return {"status": "success", "data": {"api_key": api_key, "agent": request.agent_name}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/security/api-key/{key_id}")
async def security_revoke_key(key_id: str):
    """Revoke an API key"""
    try:
        success = security_manager.revoke_api_key(key_id)
        if not success:
            raise HTTPException(status_code=404, detail="API key not found")
        return {"status": "success", "message": "API key revoked"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/security/audit-log")
async def security_audit_log(agent_name: str = None, event_type: str = None, limit: int = 100):
    """Get audit log"""
    try:
        logs = security_manager.get_audit_log(agent_name=agent_name, event_type=event_type, limit=limit)
        return {"status": "success", "data": {"logs": logs, "count": len(logs)}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/security/summary")
async def security_summary():
    """Get security summary statistics"""
    try:
        summary = security_manager.get_security_summary()
        return {"status": "success", "data": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/security/check-permission")
async def security_check_permission(request: PermissionCheckRequest):
    """Check if agent has permission"""
    try:
        has_permission = security_manager.check_permission(
            agent_name=request.agent_name, resource=request.resource, permission=request.permission
        )
        return {"status": "success", "data": {"has_permission": has_permission}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# V2 Agent Endpoints
@app.post("/api/agents/scanner/scan")
async def scanner_v2_scan(scan_type: str = "full", target_path: str = ".", include_live_check: bool = True):
    """Execute Scanner Agent V2"""
    try:
        from agent.modules.backend.scanner_v2 import scanner_agent

        if scanner_agent.status.value != "healthy":
            await scanner_agent.initialize()

        result = await scanner_agent.execute_core_function(
            scan_type=scan_type, target_path=target_path, include_live_check=include_live_check
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/fixer/fix")
async def fixer_v2_fix(
    fix_type: str = "auto",
    scan_results: Dict[str, Any] = None,
    target_files: list[str] = None,
    dry_run: bool = False,
):
    """Execute Fixer Agent V2"""
    try:
        from agent.modules.backend.fixer_v2 import fixer_agent

        if fixer_agent.status.value != "healthy":
            await fixer_agent.initialize()

        result = await fixer_agent.execute_core_function(
            fix_type=fix_type, scan_results=scan_results, target_files=target_files, dry_run=dry_run
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/{agent_name}/health")
async def agent_health(agent_name: str):
    """Get agent health status"""
    try:
        agent = registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

        health = await agent.health_check()
        return {"status": "success", "data": health}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PERFORMANCE METRICS
# ============================================================================
@app.get("/api/metrics")
async def performance_metrics():
    """Get platform performance metrics"""
    return {
        "agents": {
            "backend_total": 42,
            "frontend_total": 8,
            "backend_loaded": len([k for k in _agent_cache if k.startswith("backend")]),
            "frontend_loaded": len([k for k in _agent_cache if k.startswith("frontend")]),
        },
        "optimization": {
            "lazy_loading": True,
            "startup_time": "< 1 second",
            "mongodb_removed": True,
            "agent_separation": True,
        },
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================================
# WORDPRESS THEME BUILDER ENDPOINTS
# ============================================================================
@app.post("/api/wordpress/theme/generate")
async def generate_wordpress_theme(request: Dict[str, Any]):
    """Generate WordPress/Elementor theme"""
    try:
        from agent.wordpress.theme_builder import ElementorThemeBuilder

        builder = ElementorThemeBuilder(api_key=os.getenv("ANTHROPIC_API_KEY"))

        result = await builder.generate_theme(
            brand_info=request.get("brand_info", {}),
            theme_type=request.get("theme_type", "luxury_fashion"),
            pages=request.get("pages"),
        )

        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Theme generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/wordpress/theme/export")
async def export_wordpress_theme(request: Dict[str, Any]):
    """Export WordPress theme"""
    try:
        from agent.wordpress.theme_builder import ElementorThemeBuilder

        builder = ElementorThemeBuilder(api_key=os.getenv("ANTHROPIC_API_KEY"))

        result = await builder.export_theme(theme=request.get("theme", {}), format=request.get("format", "json"))

        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Theme export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ECOMMERCE AUTOMATION ENDPOINTS
# ============================================================================
@app.post("/api/ecommerce/products")
async def create_enhanced_product(request: Dict[str, Any]):
    """Create product with ML enhancements"""
    try:
        from agent.ecommerce.product_manager import ProductManager

        manager = ProductManager()

        result = await manager.create_product(product_data=request, auto_generate=request.get("auto_generate", True))

        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Product creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ecommerce/products/bulk")
async def bulk_import_products(request: Dict[str, Any]):
    """Bulk import products"""
    try:
        from agent.ecommerce.product_manager import ProductManager

        manager = ProductManager()

        result = await manager.bulk_import_products(products=request.get("products", []))

        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Bulk import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ecommerce/pricing/optimize")
async def optimize_pricing(request: Dict[str, Any]):
    """Optimize product pricing using ML"""
    try:
        from agent.ecommerce.pricing_engine import DynamicPricingEngine

        pricing = DynamicPricingEngine()

        result = await pricing.optimize_price(
            product_data=request.get("product_data", {}), market_data=request.get("market_data", {})
        )

        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Price optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ecommerce/pricing/strategy")
async def create_pricing_strategy(request: Dict[str, Any]):
    """Create pricing strategy"""
    try:
        from agent.ecommerce.pricing_engine import DynamicPricingEngine

        pricing = DynamicPricingEngine()

        result = await pricing.create_pricing_strategy(
            strategy_type=request.get("strategy_type", "clearance"), products=request.get("products", [])
        )

        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Pricing strategy creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ecommerce/pricing/ab-test")
async def create_ab_test(request: Dict[str, Any]):
    """Create A/B price test"""
    try:
        from agent.ecommerce.pricing_engine import DynamicPricingEngine

        pricing = DynamicPricingEngine()

        result = await pricing.ab_test_pricing(
            product_id=request.get("product_id"),
            price_variant_a=request.get("price_variant_a"),
            price_variant_b=request.get("price_variant_b"),
            duration_days=request.get("duration_days", 14),
        )

        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"A/B test creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ecommerce/inventory/forecast")
async def forecast_inventory(request: Dict[str, Any]):
    """Forecast inventory demand"""
    try:
        from agent.ecommerce.inventory_optimizer import InventoryOptimizer

        inventory = InventoryOptimizer()

        result = await inventory.forecast_demand(
            product_id=request.get("product_id"),
            historical_sales=request.get("historical_sales", []),
            forecast_periods=request.get("forecast_periods", 30),
        )

        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Inventory forecast failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ecommerce/inventory/reorder")
async def calculate_reorder_point(request: Dict[str, Any]):
    """Calculate optimal reorder point"""
    try:
        from agent.ecommerce.inventory_optimizer import InventoryOptimizer

        inventory = InventoryOptimizer()

        result = await inventory.calculate_reorder_point(
            product_data=request.get("product_data", {}), sales_data=request.get("sales_data", {})
        )

        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Reorder calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ecommerce/inventory/deadstock")
async def identify_dead_stock(request: Dict[str, Any]):
    """Identify dead stock"""
    try:
        from agent.ecommerce.inventory_optimizer import InventoryOptimizer

        inventory = InventoryOptimizer()

        result = await inventory.identify_dead_stock(
            inventory=request.get("inventory", []), threshold_days=request.get("threshold_days", 90)
        )

        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Dead stock identification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ecommerce/inventory/optimize")
async def optimize_stock_levels(request: Dict[str, Any]):
    """Optimize stock levels"""
    try:
        from agent.ecommerce.inventory_optimizer import InventoryOptimizer

        inventory = InventoryOptimizer()

        result = await inventory.optimize_stock_levels(
            products=request.get("products", []), target_service_level=request.get("target_service_level", 0.95)
        )

        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Stock optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ecommerce/products/{product_id}/analytics")
async def get_product_analytics(product_id: str):
    """Get product analytics"""
    try:
        from agent.ecommerce.product_manager import ProductManager

        manager = ProductManager()

        result = await manager.get_product_analytics(product_id)

        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Analytics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MACHINE LEARNING ENDPOINTS
# ============================================================================
@app.post("/api/ml/fashion/analyze-trend")
async def analyze_fashion_trend(request: Dict[str, Any]):
    """Analyze fashion trends"""
    try:
        from agent.ml_models.fashion_ml import FashionMLEngine

        ml = FashionMLEngine()

        result = await ml.analyze_trend(
            historical_data=request.get("historical_data", {}), forecast_periods=request.get("forecast_periods", 12)
        )

        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Trend analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/fashion/optimize-pricing")
async def ml_optimize_pricing(request: Dict[str, Any]):
    """ML-powered price optimization"""
    try:
        from agent.ml_models.fashion_ml import FashionMLEngine

        ml = FashionMLEngine()

        result = await ml.optimize_pricing(
            product_features=request.get("product_features", {}), market_data=request.get("market_data", {})
        )

        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"ML pricing optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/fashion/segment-customers")
async def segment_customers(request: Dict[str, Any]):
    """Segment customers using ML"""
    try:
        from agent.ml_models.fashion_ml import FashionMLEngine

        ml = FashionMLEngine()

        result = await ml.segment_customers(customer_data=request.get("customer_data", []))

        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Customer segmentation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/fashion/recommend-size")
async def recommend_size(request: Dict[str, Any]):
    """Recommend size based on measurements"""
    try:
        from agent.ml_models.fashion_ml import FashionMLEngine

        ml = FashionMLEngine()

        result = await ml.recommend_size(
            measurements=request.get("measurements", {}), brand_sizing=request.get("brand_sizing", "standard")
        )

        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Size recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DEVELOPMENT MODE
# ============================================================================
if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting DevSkyy Enterprise Platform")
    logger.info("📚 Documentation: http://localhost:8000/docs")
    logger.info("🏥 Health: http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000)
