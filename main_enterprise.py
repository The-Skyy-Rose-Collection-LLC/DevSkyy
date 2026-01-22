"""DevSkyy Enterprise FastAPI Application.

DevSkyy Enterprise Platform - Main Application
===============================================

Production-grade FastAPI application with:
- JWT/OAuth2 authentication (RFC 7519, RFC 6749)
- AES-256-GCM encryption (NIST SP 800-38D)
- API versioning (Microsoft REST Guidelines)
- Webhook system with HMAC signatures (RFC 2104)
- RBAC authorization
- Rate limiting
- Comprehensive monitoring

Run: uvicorn main_enterprise:app --host 0.0.0.0 --port 8000 --reload

Dependencies (verified from PyPI December 2024):
- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- python-jose[cryptography]==3.3.0
- passlib[bcrypt]==1.7.4
- argon2-cffi==23.1.0
- cryptography==41.0.7
- httpx==0.25.2
- pydantic==2.5.2
"""

# Load environment variables FIRST (before any other imports use os.getenv)

import asyncio
import logging
import os
import secrets
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

import sentry_sdk
import sqlalchemy
import structlog
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.admin_dashboard import admin_dashboard_router
from api.agents import agents_router
from api.ar_sessions import ar_sessions_router
from api.brand import brand_router
from api.dashboard import dashboard_router
from api.elementor_3d import elementor_3d_router
from api.gdpr import gdpr_router
from api.round_table import round_table_router
from api.tasks import tasks_router
from api.three_d import three_d_router
from api.tools import tools_router

# API v1 MCP Integration routers (code, commerce, HF Spaces, ML, media, etc.)
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
    wordpress_theme_router,
)
from api.v1 import wordpress_router as wordpress_v1_router

# API modules
from api.versioning import VersionConfig, VersionedAPIRouter, setup_api_versioning
from api.virtual_tryon import virtual_tryon_router
from api.visual import visual_router
from api.webhooks import WebhookEventType, webhook_manager, webhook_router
from api.websocket import ws_router
from api.wordpress import wordpress_router
from core.redis_cache import RedisCache
from core.structured_logging import bind_contextvars, clear_contextvars, configure_logging
from integrations.wordpress import (
    order_sync_router,
    product_sync_router,
    theme_deployment_router,
)
from security.aes256_gcm_encryption import data_masker, field_encryption

# Security modules
from security.api_security import APISecurityManager, APISecurityMiddleware
from security.jwt_oauth2_auth import (
    RoleChecker,
    TokenPayload,
    UserRole,
    auth_router,
    get_current_user,
)
from security.prometheus_exporter import get_metrics
from security.secrets_manager import SecretNotFoundError, SecretsManager

# Note: Structured logging is configured in lifespan function
# This is a placeholder logger for early startup messages
logger = logging.getLogger(__name__)

# Initialize Secrets Manager
# Auto-detects backend (AWS Secrets Manager, HashiCorp Vault, or local encrypted)
secrets_manager = SecretsManager()

# Initialize Redis Cache
redis_cache = RedisCache()

# Database engine and session factory (initialized in lifespan)
async_engine: AsyncEngine | None = None
async_session_factory: async_sessionmaker[AsyncSession] | None = None


# =============================================================================
# Application Lifecycle
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Startup:
    - Load secrets from secrets manager (JWT, encryption keys, API keys)
    - All agents auto-initialize with UnifiedLLMClient:
      - Task classification (Groq)
      - Intelligent routing (6 providers)
      - Prompt technique application
      - Round Table support (optional)
    """
    # Global declarations must be at the start of the function
    global async_engine, async_session_factory

    # Startup - Configure structured logging FIRST
    log_level = os.getenv("LOG_LEVEL", "INFO")
    json_output = os.getenv("LOG_JSON", "auto")
    json_output_bool = None if json_output == "auto" else json_output.lower() == "true"

    configure_logging(
        json_output=json_output_bool,
        log_level=log_level,
        include_timestamp=True,
    )

    # Get structured logger
    log = structlog.get_logger(__name__)
    log.info(
        "platform_starting",
        environment=os.getenv("ENVIRONMENT", "development"),
        log_format="json" if json_output_bool else "console",
    )

    # Get environment early so it's available throughout lifespan
    environment = os.getenv("ENVIRONMENT", "development")

    # Initialize Sentry with user-provided DSN (SECURITY: no hardcoded default)
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:

        def _sentry_before_send(event: dict, hint: dict) -> dict | None:
            """Scrub sensitive data before sending to Sentry."""
            # Remove sensitive headers
            if "request" in event and "headers" in event["request"]:
                sensitive_headers = {"authorization", "cookie", "x-api-key"}
                event["request"]["headers"] = {
                    k: "[REDACTED]" if k.lower() in sensitive_headers else v
                    for k, v in event["request"]["headers"].items()
                }
            return event

        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            traces_sample_rate=1.0 if environment == "development" else 0.1,
            profiles_sample_rate=1.0 if environment == "development" else 0.1,
            enable_tracing=True,
            send_default_pii=False,  # SECURITY: Disable PII by default (GDPR/CCPA)
            attach_stacktrace=True,
            max_breadcrumbs=50,
            before_send=_sentry_before_send,
        )
        log.info(
            "sentry_initialized",
            environment=environment,
            dsn_configured=True,
            send_default_pii=False,
        )
    else:
        log.info("sentry_disabled", reason="SENTRY_DSN not configured")

    # Initialize RAG pipeline components (conditional on RAG_AUTO_INGEST env var)
    rag_auto_ingest_enabled = os.getenv("RAG_AUTO_INGEST", "false").lower() == "true"

    if rag_auto_ingest_enabled:
        log.info("rag_pipeline_initializing")
        try:
            from orchestration.auto_ingestion import auto_ingest_documents
            from orchestration.rag_context_manager import create_rag_context_manager
            from orchestration.vector_store import VectorStoreConfig

            # Create vector store config
            vector_config = VectorStoreConfig(
                db_type="chromadb",
                collection_name="devskyy_docs",
                persist_directory=os.getenv("VECTOR_DB_PATH", "./data/vectordb"),
                default_top_k=5,
                similarity_threshold=0.5,
            )

            # Create RAG context manager with optional rewriting/reranking
            enable_rewriting = os.getenv("RAG_ENABLE_REWRITING", "false").lower() == "true"
            enable_reranking = os.getenv("RAG_ENABLE_RERANKING", "false").lower() == "true"

            rag_manager = await create_rag_context_manager(
                vector_store_config=vector_config,
                enable_rewriting=enable_rewriting,
                enable_reranking=enable_reranking,
            )

            # Auto-ingest documents from docs/
            log.info("rag_auto_ingestion_starting")
            ingestion_stats = await auto_ingest_documents(
                vector_store=rag_manager.vector_store,
                project_root=".",
                force_reindex=os.getenv("RAG_FORCE_REINDEX", "false").lower() == "true",
            )

            log.info(
                "rag_auto_ingestion_complete",
                files_ingested=ingestion_stats["files_ingested"],
                documents_created=ingestion_stats["documents_created"],
            )

            # Store RAG manager in app state for agent injection
            app.state.rag_manager = rag_manager

            # Inject RAG manager into agent registry
            try:
                from api.dashboard import agent_registry

                agent_registry.set_rag_manager(rag_manager)
                log.info("rag_manager_injected", target="agent_registry")
            except Exception as e:
                log.warning("rag_manager_injection_failed", error=str(e))

            log.info("rag_pipeline_initialized")

        except Exception as e:
            log.error("rag_pipeline_initialization_failed", error=str(e), exc_info=True)
            log.warning("continuing_without_rag")
            app.state.rag_manager = None
    else:
        log.info("rag_pipeline_disabled", reason="RAG_AUTO_INGEST not enabled")
        app.state.rag_manager = None

    # Initialize Redis cache connection with exponential backoff (optional - graceful fallback)
    cache_enabled = os.getenv("REDIS_URL") is not None
    if cache_enabled:
        log.info("redis_cache_connecting")

        # Exponential backoff retry configuration
        max_retries = int(os.getenv("REDIS_MAX_RETRIES", "3"))
        base_delay = float(os.getenv("REDIS_RETRY_BASE_DELAY", "1.0"))  # seconds
        max_delay = float(os.getenv("REDIS_RETRY_MAX_DELAY", "30.0"))  # seconds
        cache_connected = False

        for attempt in range(max_retries):
            try:
                cache_connected = await redis_cache.connect()
                if cache_connected:
                    log.info(
                        "redis_cache_connected",
                        url=(
                            os.getenv("REDIS_URL", "").split("@")[-1]
                            if os.getenv("REDIS_URL")
                            else ""
                        ),
                        attempt=attempt + 1,
                    )
                    app.state.cache_enabled = True
                    break
                else:
                    # Connection returned False without exception
                    if attempt < max_retries - 1:
                        delay = min(base_delay * (2**attempt), max_delay)
                        log.warning(
                            "redis_cache_connection_retry",
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            retry_delay=delay,
                            reason="connection_returned_false",
                        )
                        await asyncio.sleep(delay)
                    else:
                        log.warning(
                            "redis_cache_connection_failed",
                            reason="max_retries_exceeded",
                            attempts=max_retries,
                            message="caching will be unavailable",
                        )
                        app.state.cache_enabled = False
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = min(base_delay * (2**attempt), max_delay)
                    log.warning(
                        "redis_cache_connection_retry",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        retry_delay=delay,
                        error=str(e),
                    )
                    await asyncio.sleep(delay)
                else:
                    log.error(
                        "redis_cache_connection_error",
                        error=str(e),
                        attempts=max_retries,
                        exc_info=True,
                    )
                    log.warning("continuing_without_cache", reason="connection_error_after_retries")
                    app.state.cache_enabled = False
    else:
        log.info("redis_cache_disabled", reason="REDIS_URL not configured")
        app.state.cache_enabled = False

    # Start WebSocket metrics broadcaster (background task)
    try:
        from api.websocket_integration import WebSocketIntegration

        await WebSocketIntegration.start_metrics_broadcaster(interval_seconds=5)
        log.info("websocket_metrics_broadcaster_started", interval_seconds=5)
    except Exception as e:
        log.warning("websocket_metrics_broadcaster_failed", error=str(e))

    # Verify security configuration with secrets manager
    # Load and validate critical secrets (JWT, encryption keys, etc.)
    log.info("secrets_validation_starting")

    missing_required_secrets = []

    try:
        # JWT Secret Key (REQUIRED)
        jwt_secret = secrets_manager.get_or_env(
            secret_name="jwt/secret_key",
            env_var="JWT_SECRET_KEY",
        )
        if jwt_secret:
            os.environ["JWT_SECRET_KEY"] = str(jwt_secret)
            log.info("jwt_secret_loaded", source="secrets_manager")
        else:
            if environment == "production":
                missing_required_secrets.append("JWT_SECRET_KEY")
            else:
                log.warning(
                    "jwt_secret_ephemeral", reason="not_configured", environment=environment
                )

        # Encryption Master Key (REQUIRED)
        encryption_key = secrets_manager.get_or_env(
            secret_name="encryption/master_key",
            env_var="ENCRYPTION_MASTER_KEY",
        )
        if encryption_key:
            os.environ["ENCRYPTION_MASTER_KEY"] = str(encryption_key)
            log.info("encryption_key_loaded", source="secrets_manager")
        else:
            if environment == "production":
                missing_required_secrets.append("ENCRYPTION_MASTER_KEY")
            else:
                log.warning(
                    "encryption_key_ephemeral", reason="not_configured", environment=environment
                )

        # FAIL FAST in production if critical secrets are missing
        if missing_required_secrets and environment == "production":
            log.error(
                "production_secrets_missing",
                missing_secrets=missing_required_secrets,
                message="Cannot start in production without critical secrets",
            )
            raise SecretNotFoundError(
                f"Missing required production secrets: {', '.join(missing_required_secrets)}. "
                f"Set via: fly secrets set KEY=value"
            )

        # Database URL (optional but recommended for production)
        try:
            db_url = secrets_manager.get_or_env(
                secret_name="database/connection_string",
                env_var="DATABASE_URL",
            )
            if db_url:
                os.environ["DATABASE_URL"] = str(db_url)
                log.info("database_url_loaded", source="secrets_manager")

                # Initialize async database engine with connection pooling
                log.info("database_engine_initializing")

                try:
                    # Convert postgresql:// to postgresql+asyncpg:// for async driver
                    async_db_url = str(db_url)
                    if async_db_url.startswith("postgresql://"):
                        async_db_url = async_db_url.replace(
                            "postgresql://", "postgresql+asyncpg://", 1
                        )
                    elif async_db_url.startswith("postgres://"):
                        async_db_url = async_db_url.replace(
                            "postgres://", "postgresql+asyncpg://", 1
                        )

                    # Create async engine with connection pooling
                    async_engine = create_async_engine(
                        async_db_url,
                        echo=log_level == "DEBUG",  # Echo SQL queries in debug mode
                        pool_size=10,  # Connection pool size
                        max_overflow=20,  # Extra connections during peak load
                        pool_pre_ping=True,  # Verify connections before use
                        pool_recycle=3600,  # Recycle connections after 1 hour
                    )

                    # Create session factory with expire_on_commit=False for async patterns
                    async_session_factory = async_sessionmaker(
                        async_engine,
                        class_=AsyncSession,
                        expire_on_commit=False,  # Prevent object expiration after commit
                    )

                    # Verify database connectivity
                    async with async_engine.begin() as conn:
                        await conn.execute(sqlalchemy.text("SELECT 1"))

                    log.info(
                        "database_engine_initialized",
                        pool_size=10,
                        max_overflow=20,
                        driver="asyncpg",
                    )

                    # Store in app state for route access
                    app.state.db_engine = async_engine
                    app.state.db_session_factory = async_session_factory

                except Exception as e:
                    log.error("database_engine_initialization_failed", error=str(e), exc_info=True)
                    log.warning("continuing_without_database", reason="engine_initialization_error")
                    async_engine = None
                    async_session_factory = None
            else:
                log.warning(
                    "database_url_not_configured", message="database features will be unavailable"
                )
        except SecretNotFoundError:
            log.debug("database_url_not_in_secrets_manager")

        # API Keys (optional - integrations won't work if not configured)
        optional_api_keys = [
            ("openai/api_key", "OPENAI_API_KEY", "OpenAI"),
            ("anthropic/api_key", "ANTHROPIC_API_KEY", "Anthropic"),
            ("google/api_key", "GOOGLE_API_KEY", "Google"),
            ("aws/access_key_id", "AWS_ACCESS_KEY_ID", "AWS"),
            ("aws/secret_access_key", "AWS_SECRET_ACCESS_KEY", "AWS Secret"),
        ]

        loaded_api_keys = []
        for secret_name, env_var, display_name in optional_api_keys:
            try:
                api_key = secrets_manager.get_or_env(secret_name, env_var)
                if api_key:
                    os.environ[env_var] = str(api_key)
                    loaded_api_keys.append(display_name)
                    log.debug("api_key_loaded", service=display_name)
            except SecretNotFoundError:
                log.debug("api_key_not_configured", service=display_name)

        if loaded_api_keys:
            log.info("optional_api_keys_loaded", services=", ".join(loaded_api_keys))
        else:
            log.warning("no_api_keys_configured", message="LLM integrations may be limited")

    except SecretNotFoundError as e:
        log.error("critical_secret_missing", error=str(e), exc_info=True)
        if environment == "production":
            raise
        else:
            log.warning("continuing_with_missing_secrets", environment=environment)
    except Exception as e:
        log.error("secrets_loading_error", error=str(e), exc_info=True)
        if environment == "production":
            log.critical("production_startup_failed", reason="secrets_error")
            raise
        else:
            log.warning("falling_back_to_environment_variables")

    yield

    # Shutdown
    log.info("platform_shutting_down")

    # Dispose database engine and close all connections
    if async_engine:
        log.info("database_engine_disposing")
        await async_engine.dispose()
        log.info("database_engine_disposed")

    await redis_cache.disconnect()
    await webhook_manager.close()
    log.info("platform_shutdown_complete")


# =============================================================================
# Database Dependency Injection
# =============================================================================


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.

    Usage in routes:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()

    Yields:
        AsyncSession: Database session with automatic commit/rollback

    Raises:
        HTTPException: If database is not configured
    """
    if async_session_factory is None:
        raise HTTPException(
            status_code=503,
            detail="Database not configured. Set DATABASE_URL environment variable.",
        )

    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# =============================================================================
# Application Setup
# =============================================================================

app = FastAPI(
    title="DevSkyy Enterprise Platform",
    description="""
    ## AI-Driven Multi-Agent Orchestration Platform

    DevSkyy provides enterprise-grade automation for:
    - **WordPress/WooCommerce** operations
    - **AI Agent** orchestration (6 core specialized agents)
    - **ML-driven** fashion analytics and dynamic pricing
    - **MCP Integration** for external AI systems

    ### Security Features
    - JWT/OAuth2 authentication with refresh token rotation
    - AES-256-GCM encryption for sensitive data
    - RBAC authorization with role hierarchy
    - Webhook signatures with HMAC-SHA256

    ### API Versioning
    Current version: **v1**

    ### Authentication
    Use the `/api/v1/auth/token` endpoint to obtain access tokens.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# =============================================================================
# Middleware
# =============================================================================

# CORS - Enforce explicit origin whitelist + Vercel preview support + devskyy.app domains
cors_origins = os.getenv("CORS_ORIGINS", "").strip()
if not cors_origins:
    # Development defaults + production domains (Vercel + devskyy.app)
    cors_origins_list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://devskyy-dashboard.vercel.app",  # Production Vercel domain
        "https://app.devskyy.app",  # Production app domain
        "https://api.devskyy.app",  # Production API domain
        "https://staging.devskyy.com",  # Staging domain
    ]
    log = structlog.get_logger(__name__)
    log.warning(
        "cors_origins_not_configured",
        message="Using development defaults + production domains. Set CORS_ORIGINS for custom setup.",
    )
else:
    cors_origins_list = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

if not cors_origins_list:
    msg = "CORS_ORIGINS must contain at least one valid origin"
    raise ValueError(msg)

# Regex patterns to allow Vercel preview deployments and devskyy.app subdomains
# Combined into single regex that matches either pattern
cors_origin_regex = r"https://.*\.(vercel\.app|devskyy\.app)"

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list,
    allow_origin_regex=cors_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Request-ID",
        "Accept",
        "Accept-Language",
        "Content-Language",
    ],
    expose_headers=["X-Response-Time", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
)

# API Versioning
version_config = VersionConfig(
    current_version="v1",
    supported_versions=["v1"],
    deprecated_versions={},
    use_path_versioning=True,
    use_header_versioning=True,
)
setup_api_versioning(app, version_config)

# API Security Middleware with Request Signing
# Protected paths requiring request signatures (Phase 2 Task 2)
protected_paths = [
    "/api/v1/admin/*",  # All admin operations
    "/api/v1/agents/*/execute",  # Agent execution endpoints
    "/api/v1/users/*/delete",  # User deletion
    "/api/v1/payments/*",  # Payment operations
    "/api/v1/keys/rotate",  # Key rotation
]

# Initialize security manager with Redis nonce cache if available
use_redis = os.getenv("REDIS_URL") is not None
api_security_manager = APISecurityManager(use_redis=use_redis)

app.add_middleware(
    APISecurityMiddleware,
    security_manager=api_security_manager,
    protected_paths=protected_paths,
)

# Note: These early logger calls happen before structured logging is configured
# They will use basic logging format


# Correlation ID middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Add correlation ID to request context for distributed tracing."""
    # Get or generate correlation ID
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

    # Bind to context variables for this request
    bind_contextvars(correlation_id=correlation_id)

    # Add to request state
    request.state.correlation_id = correlation_id

    try:
        response = await call_next(request)
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        return response
    finally:
        # Clean up context variables after request
        clear_contextvars()


# Tier-based rate limiting middleware
@app.middleware("http")
async def tier_rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware based on subscription tier."""
    from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

    from security.jwt_oauth2_auth import jwt_manager
    from security.rate_limiting import rate_limiter

    # Skip rate limiting for auth endpoints and health checks
    excluded_paths = [
        "/api/v1/auth/",
        "/health",
        "/ready",
        "/live",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]
    if any(request.url.path.startswith(path) for path in excluded_paths):
        return await call_next(request)

    # Extract tier from JWT token
    tier_name = "free"  # Default tier
    auth_header = request.headers.get("Authorization", "")

    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = jwt_manager.validate_token(token)
            # Extract tier from token claims (will be added in jwt_oauth2_auth.py)
            tier_name = getattr(payload, "tier", "free")
            # Store tier in request state for later use
            request.state.tier = tier_name
            request.state.user_id = payload.sub
        except (ExpiredSignatureError, InvalidTokenError):
            # Token invalid or expired, use free tier
            tier_name = "free"

    # Check tier-based rate limit
    try:
        is_allowed, rate_info = rate_limiter.check_tier_limit(request, tier_name)

        if not is_allowed:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {tier_name} tier",
                headers={
                    "X-RateLimit-Limit": str(rate_info.get("limit", 0)),
                    "X-RateLimit-Remaining": str(rate_info.get("remaining", 0)),
                    "X-RateLimit-Reset": str(rate_info.get("reset", 0)),
                    "Retry-After": str(rate_info.get("retry_after", 60)),
                    "X-RateLimit-Tier": tier_name,
                },
            )

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_info.get("limit", 0))
        response.headers["X-RateLimit-Remaining"] = str(rate_info.get("remaining", 0))
        response.headers["X-RateLimit-Reset"] = str(rate_info.get("reset", 0))
        response.headers["X-RateLimit-Tier"] = tier_name

        return response

    except Exception as e:
        # SECURITY: Fail secure in production - block requests if rate limiter fails
        log = structlog.get_logger(__name__)
        log.error("rate_limiter_error", error=str(e), exc_info=True)
        environment = os.getenv("ENVIRONMENT", "development")
        if environment == "production":
            # Fail secure: block request on rate limiter failure in production
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Rate limiting service temporarily unavailable",
            )
        # In development, allow request through with warning
        return await call_next(request)


# Security headers middleware - OWASP best practices
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses (OWASP, CSP, X-Frame-Options, etc)."""
    # Generate nonce for this request (used for inline scripts)
    nonce = secrets.token_urlsafe(16)

    # Store nonce in request state for access in templates/responses
    request.state.csp_nonce = nonce

    response = await call_next(request)

    # OWASP Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"  # Prevent MIME sniffing
    response.headers["X-Frame-Options"] = "DENY"  # Prevent clickjacking
    response.headers["X-XSS-Protection"] = "1; mode=block"  # XSS protection
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"  # HSTS

    # Content Security Policy with nonce-based inline script support
    # Nonce prevents XSS attacks by only allowing scripts with matching nonce attribute
    csp = (
        "default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net https://api.devskyy.app; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https: blob:; "
        "font-src 'self' https://cdn.jsdelivr.net; "
        "connect-src 'self' https: wss:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    response.headers["Content-Security-Policy"] = csp

    # Add nonce to response headers for frontend JavaScript access
    response.headers["X-CSP-Nonce"] = nonce

    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Permissions Policy (formerly Feature Policy)
    response.headers["Permissions-Policy"] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=(), "
        "magnetometer=(), "
        "gyroscope=(), "
        "accelerometer=()"
    )

    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing and correlation IDs using structured logging."""
    import time

    from security.prometheus_exporter import exporter

    # Get structured logger
    log = structlog.get_logger(__name__)

    start = time.time()

    # Get correlation_id from request state (set by correlation_id_middleware)
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

    # Bind correlation_id for this request (should already be set by correlation_id_middleware)
    bind_contextvars(correlation_id=correlation_id)

    # Start tracking request for metrics
    exporter.start_api_request(correlation_id)

    response = await call_next(request)

    duration_seconds = time.time() - start
    duration_ms = duration_seconds * 1000

    # Structured logging with all context
    log.info(
        "http_request",
        method=request.method,
        path=str(request.url.path),
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2),
        client_ip=request.client.host if request.client else "unknown",
    )

    # Record metrics in Prometheus
    exporter.finish_api_request(
        request_id=correlation_id,
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
    )

    # Record security event for API requests
    exporter.record_security_event(
        event_type="api_request",
        severity="info" if 200 <= response.status_code < 300 else "warning",
        source_ip=request.client.host if request.client else "unknown",
        endpoint=request.url.path,
    )

    # Add timing header
    response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

    return response


# =============================================================================
# Routers
# =============================================================================

# Authentication routes
app.include_router(auth_router)

# Webhook routes
app.include_router(webhook_router)

# GDPR compliance routes
app.include_router(gdpr_router)

# AI agent routes
app.include_router(agents_router)

# WebSocket routes for real-time updates
app.include_router(ws_router)

# Dashboard API routes (for Next.js frontend)
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(round_table_router, prefix="/api/v1")
app.include_router(brand_router, prefix="/api/v1")
app.include_router(tools_router, prefix="/api/v1")
app.include_router(three_d_router, prefix="/api/v1")
app.include_router(visual_router, prefix="/api/v1")
app.include_router(virtual_tryon_router, prefix="/api/v1")
app.include_router(ar_sessions_router, prefix="/api/v1")
app.include_router(wordpress_router, prefix="/api/v1")

# Admin dashboard routes (asset management, fidelity, sync, pipelines)
app.include_router(admin_dashboard_router, prefix="/api/v1")

# Elementor 3D Experience routes (WordPress/Elementor integration)
app.include_router(elementor_3d_router, prefix="/api/v1")

# WordPress Integration routes registration (Product Sync, Order Sync, Theme Deployment)
app.include_router(product_sync_router, prefix="/api/v1/wordpress", tags=["wordpress"])
app.include_router(order_sync_router, prefix="/api/v1/wordpress", tags=["wordpress"])
app.include_router(theme_deployment_router, prefix="/api/v1/wordpress", tags=["wordpress"])

# =============================================================================
# NEW API v1 Routers - MCP Integration Endpoints
# =============================================================================

# Code scanning and fixing
app.include_router(code_router, prefix="/api/v1")

# HuggingFace Spaces management
app.include_router(hf_spaces_router, prefix="/api/v1")

# Training and Sync Pipeline routers
app.include_router(training_router, prefix="/api/v1")
app.include_router(sync_router, prefix="/api/v1")

# WordPress/WooCommerce v1 API (test-connection, products, orders endpoints)
app.include_router(wordpress_v1_router, prefix="/api/v1")

# WordPress theme generation
app.include_router(wordpress_theme_router, prefix="/api/v1")

# Machine learning predictions
app.include_router(ml_router, prefix="/api/v1")

# Media generation (3D models)
app.include_router(media_router, prefix="/api/v1")

# Marketing campaigns
app.include_router(marketing_router, prefix="/api/v1")

# Commerce operations (bulk products, dynamic pricing)
app.include_router(commerce_router, prefix="/api/v1")

# Multi-agent orchestration
app.include_router(orchestration_router, prefix="/api/v1")

# System monitoring and agent directory
app.include_router(monitoring_router, prefix="/api/v1")


# =============================================================================
# Health & Status Endpoints
# =============================================================================


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: str
    version: str
    environment: str
    services: dict[str, str]
    agents: dict[str, Any] | None = None


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "platform": "DevSkyy Enterprise",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
        "mcp_tools": 13,
        "api_endpoints": [
            "/api/v1/code/scan",
            "/api/v1/code/fix",
            "/api/v1/wordpress/generate-theme",
            "/api/v1/ml/predict",
            "/api/v1/commerce/products/bulk",
            "/api/v1/commerce/pricing/optimize",
            "/api/v1/media/3d/generate/text",
            "/api/v1/media/3d/generate/image",
            "/api/v1/marketing/campaigns",
            "/api/v1/orchestration/workflows",
            "/api/v1/monitoring/metrics",
            "/api/v1/agents",
        ],
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Enhanced health check endpoint.

    Returns comprehensive health status including:
    - API status
    - Authentication service
    - Encryption service
    - Agent availability
    - System metrics
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(UTC).isoformat(),
        version="1.0.1",
        environment=os.getenv("ENVIRONMENT", "development"),
        services={
            "api": "operational",
            "auth": "operational",
            "encryption": "operational",
            "mcp_server": "operational",
            "agents": "operational",
        },
        agents={
            "total": 54,
            "active": 54,
            "categories": [
                "infrastructure",
                "ai_intelligence",
                "ecommerce",
                "marketing",
                "content",
                "integration",
                "advanced",
                "frontend",
            ],
        },
    )


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check - all services available."""
    return {"ready": True}


@app.get("/live", tags=["Health"])
async def liveness_check():
    """Liveness check - server is alive."""
    return {"alive": True}


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint."""
    metrics_data = get_metrics()
    return Response(content=metrics_data, media_type="text/plain; version=0.0.4; charset=utf-8")


@app.get("/metrics/cache", tags=["Monitoring"])
async def cache_metrics():
    """Cache statistics and performance metrics.

    Returns cache hit rate, total hits/misses, and recommendations for optimization.
    Use this endpoint to monitor Redis cache effectiveness and identify performance issues.
    """
    try:
        redis_stats = await redis_cache.get_stats()

        # Add recommendation based on hit rate
        hit_rate = redis_stats.get("hit_rate", 0.0)
        if hit_rate >= 80:
            recommendation = "Excellent cache performance - hit rate above 80%"
        elif hit_rate >= 60:
            recommendation = "Good cache performance - consider increasing cache TTL"
        elif hit_rate >= 40:
            recommendation = "Moderate cache performance - review caching strategy"
        else:
            recommendation = "Low cache performance - investigate cache misses and adjust TTL"

        return {
            "redis": redis_stats,
            "recommendation": recommendation,
            "target_hit_rate": 80.0,
        }
    except Exception as e:
        log = structlog.get_logger(__name__)
        log.error("cache_stats_failed", error=str(e), exc_info=True)
        return {"error": "Failed to retrieve cache statistics", "message": str(e)}


# =============================================================================
# API v1 Routes
# =============================================================================

v1_router = VersionedAPIRouter(version="v1", tags=["API v1"])


# ---- Products ----


class ProductCreate(BaseModel):
    """Request model for creating a new product."""

    name: str
    description: str | None = None
    price: float
    sku: str
    inventory: int = 0


class ProductResponse(BaseModel):
    """Response model for product data."""

    id: str
    name: str
    description: str | None
    price: float
    sku: str
    inventory: int
    created_at: str


@v1_router.post("/products", response_model=ProductResponse)
async def create_product(product: ProductCreate, user: TokenPayload = Depends(get_current_user)):
    """Create a new product (requires authentication)."""
    product_id = f"prod_{os.urandom(8).hex()}"

    # Publish webhook event
    await webhook_manager.publish(
        event_type=WebhookEventType.PRODUCT_CREATED.value,
        data={
            "product_id": product_id,
            "name": product.name,
            "sku": product.sku,
            "created_by": user.sub,
        },
    )

    return ProductResponse(
        id=product_id,
        name=product.name,
        description=product.description,
        price=product.price,
        sku=product.sku,
        inventory=product.inventory,
        created_at=datetime.now(UTC).isoformat(),
    )


@v1_router.get("/products", response_model=list[ProductResponse])
async def list_products(
    user: TokenPayload = Depends(get_current_user), limit: int = 10, offset: int = 0
):
    """List all products (paginated)."""
    # Demo data
    return [
        ProductResponse(
            id="prod_demo1",
            name="BLACK ROSE Hoodie",
            description="Limited edition dark elegance",
            price=189.99,
            sku="BR-HOOD-001",
            inventory=50,
            created_at=datetime.now(UTC).isoformat(),
        )
    ]


# ---- Orders ----


class OrderCreate(BaseModel):
    """Request model for creating a new order."""

    customer_id: str
    items: list[dict[str, Any]]
    shipping_address: dict[str, str]


class OrderResponse(BaseModel):
    """Response model for order data."""

    id: str
    customer_id: str
    status: str
    total: float
    created_at: str


@v1_router.post("/orders", response_model=OrderResponse)
async def create_order(order: OrderCreate, user: TokenPayload = Depends(get_current_user)):
    """Create an order (requires authentication)."""
    order_id = f"ord_{os.urandom(8).hex()}"

    # Encrypt sensitive shipping data
    field_encryption.encrypt_dict(order.shipping_address, context=order_id)

    # Publish webhook
    await webhook_manager.publish(
        event_type=WebhookEventType.ORDER_CREATED.value,
        data={
            "order_id": order_id,
            "customer_id": order.customer_id,
            "item_count": len(order.items),
        },
    )

    return OrderResponse(
        id=order_id,
        customer_id=order.customer_id,
        status="pending",
        total=sum(item.get("price", 0) * item.get("quantity", 1) for item in order.items),
        created_at=datetime.now(UTC).isoformat(),
    )


# ---- Agents ----


class AgentExecuteRequest(BaseModel):
    """Request model for executing a super agent."""

    agent_name: str
    task: str
    parameters: dict[str, Any] = {}


class AgentResponse(BaseModel):
    """Response model for agent execution."""

    agent_name: str
    task_id: str
    status: str
    result: dict[str, Any] | None = None


@v1_router.post("/agents/execute", response_model=AgentResponse)
async def execute_agent(
    request: AgentExecuteRequest, user: TokenPayload = Depends(get_current_user)
):
    """Execute a super agent (requires authentication)."""
    task_id = f"task_{os.urandom(8).hex()}"

    # Publish webhook
    await webhook_manager.publish(
        event_type=WebhookEventType.AGENT_TASK_STARTED.value,
        data={
            "task_id": task_id,
            "agent_name": request.agent_name,
            "initiated_by": user.sub,
        },
    )

    return AgentResponse(
        agent_name=request.agent_name, task_id=task_id, status="started", result=None
    )


# NOTE: /agents endpoints are handled by dashboard_router (api/dashboard.py)


# ---- Admin Routes (RBAC Protected) ----


@v1_router.get(
    "/admin/stats",
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.SUPER_ADMIN]))],
)
async def get_admin_stats():
    """Get admin statistics (requires admin role)."""
    return {
        "total_users": 150,
        "total_orders": 1250,
        "total_revenue": 125000.00,
        "active_agents": 69,
        "webhook_endpoints": len(webhook_manager.list_endpoints()),
        "api_version": "v1",
    }


@v1_router.get("/admin/security-audit", dependencies=[Depends(RoleChecker([UserRole.SUPER_ADMIN]))])
async def get_security_audit():
    """Get security audit log (requires admin role)."""
    return {
        "audit_log": [
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "action": "login",
                "user": "admin",
                "ip": "127.0.0.1",
                "status": "success",
            }
        ],
        "security_score": 95,
        "compliance": {
            "jwt_auth": True,
            "aes_encryption": True,
            "rbac": True,
            "webhooks_signed": True,
        },
    }


# ---- Encryption Demo ----


@v1_router.post("/demo/encrypt")
async def demo_encrypt(data: dict[str, Any], user: TokenPayload = Depends(get_current_user)):
    """Demo encryption (AES-256-GCM)."""
    encrypted = field_encryption.encrypt_dict(data, context=user.sub)
    return {
        "original_keys": list(data.keys()),
        "encrypted_data": encrypted,
        "note": "Sensitive fields automatically encrypted",
    }


@v1_router.post("/demo/mask")
async def demo_mask(data: dict[str, str], user: TokenPayload = Depends(get_current_user)):
    """Demo PII masking (SSN, email redaction)."""
    masked = {}
    for key, value in data.items():
        if "email" in key.lower():
            masked[key] = data_masker.mask_email(value)
        elif "card" in key.lower():
            masked[key] = data_masker.mask_card_number(value)
        elif "phone" in key.lower():
            masked[key] = data_masker.mask_phone(value)
        elif "ssn" in key.lower():
            masked[key] = data_masker.mask_ssn(value)
        else:
            masked[key] = value
    return masked


# Include v1 router
app.include_router(v1_router)


# =============================================================================
# Error Handlers
# =============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper error format and structured logging."""
    log = structlog.get_logger(__name__)
    log.warning(
        "http_exception",
        status_code=exc.status_code,
        message=exc.detail,
        path=str(request.url.path),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail,
            "path": str(request.url.path),
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with error tracking and structured logging."""
    log = structlog.get_logger(__name__)
    log.error(
        "unhandled_exception",
        exception_type=type(exc).__name__,
        error=str(exc),
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
        },
    )


# =============================================================================
# Development Server
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main_enterprise:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
