"""
DevSkyy Enterprise Platform
============================

Run: uvicorn main_enterprise:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import structlog
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

logger = logging.getLogger(__name__)


# =============================================================================
# Lifespan — startup / shutdown
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database, logging, optional services."""
    from core.structured_logging import configure_logging

    log_level = os.getenv("LOG_LEVEL", "INFO")
    configure_logging(log_level=log_level, include_timestamp=True)
    log = structlog.get_logger(__name__)

    environment = os.getenv("ENVIRONMENT", "development")
    log.info("platform_starting", environment=environment)

    # Sentry (optional)
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        import sentry_sdk

        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            traces_sample_rate=0.1 if environment == "production" else 1.0,
            send_default_pii=False,
        )
        log.info("sentry_initialized")

    # Database
    from database.db import db_manager

    await db_manager.initialize()
    app.state.db_manager = db_manager
    log.info("database_initialized")

    # OpenTelemetry (optional)
    try:
        from core.telemetry.tracer import init_telemetry

        init_telemetry(service_name="devskyy-api")
        log.info("opentelemetry_initialized")
    except Exception:
        pass

    log.info("platform_ready", routes=len([r for r in app.routes if hasattr(r, "path")]))

    yield

    # Shutdown
    log.info("platform_shutting_down")
    await db_manager.close()
    log.info("platform_shutdown_complete")


# =============================================================================
# App
# =============================================================================

app = FastAPI(
    title="DevSkyy Enterprise Platform",
    description="AI-Driven Multi-Agent Orchestration for SkyyRose",
    version="3.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# =============================================================================
# Middleware
# =============================================================================

# CORS
cors_origins = os.getenv("CORS_ORIGINS", "").split(",")
cors_origins = [o.strip() for o in cors_origins if o.strip()] or [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://skyyrose.co",
    "https://devskyy.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.(vercel\.app|devskyy\.app)",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID", "X-Correlation-ID"],
    expose_headers=["X-Response-Time", "X-Correlation-ID"],
)


# Correlation ID
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


# Response timing
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    import time

    start = time.time()
    response = await call_next(request)
    ms = (time.time() - start) * 1000
    response.headers["X-Response-Time"] = f"{ms:.2f}ms"
    return response


# Security headers
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# =============================================================================
# Routers
# =============================================================================

# Core dashboard & agent routers
from api.dashboard import dashboard_router
from api.tasks import tasks_router
from api.round_table import round_table_router
from api.brand import brand_router
from api.tools import tools_router
from api.three_d import three_d_router
from api.visual import visual_router
from api.agents import agents_router
from api.admin_dashboard import admin_dashboard_router

app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(round_table_router, prefix="/api/v1")
app.include_router(brand_router, prefix="/api/v1")
app.include_router(tools_router, prefix="/api/v1")
app.include_router(three_d_router, prefix="/api/v1")
app.include_router(visual_router, prefix="/api/v1")
app.include_router(agents_router)
app.include_router(admin_dashboard_router, prefix="/api/v1")

# WordPress & e-commerce
from api.ar_sessions import ar_sessions_router
from api.virtual_tryon import virtual_tryon_router
from api.elementor_3d import elementor_3d_router
from api.gdpr import gdpr_router
from api.webhooks import webhook_router
from api.websocket import ws_router

app.include_router(ar_sessions_router, prefix="/api/v1")
app.include_router(virtual_tryon_router, prefix="/api/v1")
app.include_router(elementor_3d_router, prefix="/api/v1")
app.include_router(gdpr_router)
app.include_router(webhook_router)
app.include_router(ws_router)

# API v1 MCP routers
from api.v1 import (
    code_router,
    commerce_router,
    hf_spaces_router,
    marketing_router,
    media_router,
    ml_router,
    monitoring_router,
    orchestration_router,
    sync_router,
    training_router,
    wordpress_agent_router,
    wordpress_theme_router,
)

app.include_router(code_router, prefix="/api/v1")
app.include_router(commerce_router, prefix="/api/v1")
app.include_router(hf_spaces_router, prefix="/api/v1")
app.include_router(marketing_router, prefix="/api/v1")
app.include_router(media_router, prefix="/api/v1")
app.include_router(ml_router, prefix="/api/v1")
app.include_router(monitoring_router, prefix="/api/v1")
app.include_router(orchestration_router, prefix="/api/v1")
app.include_router(sync_router, prefix="/api/v1")
app.include_router(training_router, prefix="/api/v1")
app.include_router(wordpress_agent_router, prefix="/api/v1")
app.include_router(wordpress_theme_router, prefix="/api/v1")

# WordPress integration
from api.v1.wordpress_integration import router as wordpress_router

app.include_router(wordpress_router, prefix="/api/v1")

# Analytics & pipeline
from api.v1 import (
    approval_router,
    assets_router,
    brand_assets_router,
    business_router,
    competitors_router,
    descriptions_router,
)

app.include_router(business_router, prefix="/api/v1")
app.include_router(assets_router, prefix="/api/v1")
app.include_router(approval_router, prefix="/api/v1")
app.include_router(brand_assets_router, prefix="/api/v1")
app.include_router(competitors_router, prefix="/api/v1")
app.include_router(descriptions_router, prefix="/api/v1")

from api.v1.analytics.dashboard import router as analytics_dashboard_router

app.include_router(analytics_dashboard_router, prefix="/api/v1")

from api.v1.pipeline import router as pipeline_router

app.include_router(pipeline_router, prefix="/api/v1")

# GraphQL
from api.graphql_server import graphql_router

app.include_router(graphql_router, prefix="/graphql", tags=["GraphQL"])


# =============================================================================
# Health & Status
# =============================================================================


@app.get("/", tags=["Root"])
async def root():
    return {
        "platform": "DevSkyy Enterprise",
        "version": "3.2.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/health", tags=["Health"])
async def health_check():
    db_status = "unknown"
    try:
        db = app.state.db_manager
        health = await db.health_check()
        db_status = health.get("status", "unknown")
    except Exception:
        db_status = "unavailable"

    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "3.2.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "services": {
            "api": "operational",
            "database": db_status,
        },
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    return {"ready": True}


@app.get("/live", tags=["Health"])
async def liveness_check():
    return {"alive": True}


# =============================================================================
# Error Handlers
# =============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail,
            "path": str(request.url.path),
            "timestamp": datetime.now(UTC).isoformat(),
            "correlation_id": getattr(request.state, "correlation_id", None),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    log = structlog.get_logger(__name__)
    log.error(
        "unhandled_exception",
        exception_type=type(exc).__name__,
        path=str(request.url.path),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "message": "Internal server error",
            "path": str(request.url.path),
            "timestamp": datetime.now(UTC).isoformat(),
            "correlation_id": getattr(request.state, "correlation_id", None),
        },
    )


# =============================================================================
# Dev Server
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main_enterprise:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
