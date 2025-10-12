"""
FastAPI Enterprise Security Configuration
Production-grade security middleware and configurations
"""

import logging
import os
import time
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException

from .enterprise_security import EnterpriseSecurityManager, SecurityHeaders

logger = logging.getLogger(__name__)


def configure_security(app: FastAPI) -> None:
    """
    Configure comprehensive security for FastAPI application.
    """

    # Initialize security manager
    security_manager = EnterpriseSecurityManager()

    # 1. CORS Configuration (Restrictive)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("ALLOWED_ORIGINS", "https://skyyrose.com").split(","),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        max_age=3600,  # Cache preflight for 1 hour
    )

    # 2. Trusted Host Middleware (Prevent Host Header Attacks)
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=os.getenv("ALLOWED_HOSTS", "skyyrose.com,*.skyyrose.com").split(",")
    )

    # 3. GZip Compression (Performance & Security)
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 4. Security Headers Middleware
    app.add_middleware(SecurityHeaders)

    # 5. Rate Limiting
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["100 per minute", "1000 per hour"],
        storage_uri=os.getenv("REDIS_URL", "memory://"),
        enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # 6. Request ID Middleware (Tracing)
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", security_manager.generate_secure_token(16))
        request.state.request_id = request_id

        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        # Log request
        logger.info(
            f"Request {request_id}: {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)"
        )

        return response

    # 7. Security Logging Middleware
    @app.middleware("http")
    async def security_logging(request: Request, call_next):
        # Log suspicious patterns
        user_agent = request.headers.get("User-Agent", "")
        suspicious_patterns = ["sqlmap", "nikto", "burp", "nmap", "metasploit"]

        for pattern in suspicious_patterns:
            if pattern.lower() in user_agent.lower():
                security_manager.log_security_event(
                    "suspicious_user_agent",
                    {
                        "ip": request.client.host,
                        "user_agent": user_agent,
                        "path": request.url.path,
                    },
                )
                return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "Forbidden"})

        # Check for SQL injection attempts in query params
        query_params = str(request.url.query)
        sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "UNION", "EXEC"]

        for keyword in sql_keywords:
            if keyword in query_params.upper():
                security_manager.log_security_event(
                    "sql_injection_attempt",
                    {
                        "ip": request.client.host,
                        "query": query_params,
                        "path": request.url.path,
                    },
                )
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Invalid request"})

        response = await call_next(request)
        return response

    # 8. IP Blocking Middleware
    @app.middleware("http")
    async def ip_blocking(request: Request, call_next):
        client_ip = request.client.host

        # Check if IP is blocked
        if client_ip in security_manager.blocked_ips:
            security_manager.log_security_event("blocked_ip_attempt", {"ip": client_ip, "path": request.url.path})
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "Access denied"})

        response = await call_next(request)
        return response

    # 9. Content Size Limiting
    @app.middleware("http")
    async def limit_content_size(request: Request, call_next):
        max_size = 10 * 1024 * 1024  # 10MB
        content_length = request.headers.get("Content-Length")

        if content_length and int(content_length) > max_size:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, content={"detail": "Request entity too large"}
            )

        response = await call_next(request)
        return response

    # 10. Exception Handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        # Don't leak internal information
        if exc.status_code >= 500:
            security_manager.log_security_event(
                "server_error",
                {
                    "path": request.url.path,
                    "method": request.method,
                    "status": exc.status_code,
                },
            )
            return JSONResponse(status_code=exc.status_code, content={"detail": "Internal server error"})

        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Log validation errors (potential attacks)
        security_manager.log_security_event(
            "validation_error",
            {
                "path": request.url.path,
                "errors": str(exc.errors()[:3]),  # Limit logged errors
            },
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": "Invalid request data"}
        )

    # 11. Health Check Endpoint (No Auth Required)
    @app.get("/health", tags=["monitoring"])
    async def health_check():
        """Health check endpoint for monitoring."""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": os.getenv("APP_VERSION", "1.0.0"),
        }

    # 12. Security Headers Check Endpoint
    @app.get("/api/security/headers", tags=["security"])
    async def security_headers_check(request: Request):
        """Check security headers."""
        headers = dict(request.headers)
        required_headers = [
            "strict-transport-security",
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection",
            "content-security-policy",
        ]

        missing_headers = []
        for header in required_headers:
            if header not in headers:
                missing_headers.append(header)

        return {
            "all_headers_present": len(missing_headers) == 0,
            "missing_headers": missing_headers,
            "recommendation": "All security headers should be present for production",
        }

    logger.info("🔐 Enterprise security configuration applied to FastAPI")


def configure_production_logging(app: FastAPI) -> None:
    """
    Configure production-grade logging with security focus.
    """
    import logging.handlers

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(detailed_formatter)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        "logs/app.log", maxBytes=10 * 1024 * 1024, backupCount=10  # 10MB
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Security log handler
    security_handler = logging.handlers.RotatingFileHandler(
        "logs/security.log", maxBytes=10 * 1024 * 1024, backupCount=30  # Keep 30 days of security logs
    )
    security_handler.setLevel(logging.WARNING)
    security_handler.setFormatter(detailed_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Configure security logger
    security_logger = logging.getLogger("security")
    security_logger.addHandler(security_handler)

    logger.info("📝 Production logging configured")


def create_secure_app() -> FastAPI:
    """
    Create FastAPI app with full security configuration.
    """
    app = FastAPI(
        title="DevSkyy API",
        description="Enterprise AI Platform for Luxury Fashion",
        version="1.0.0",
        docs_url=None if os.getenv("ENVIRONMENT") == "production" else "/docs",
        redoc_url=None if os.getenv("ENVIRONMENT") == "production" else "/redoc",
        openapi_url=None if os.getenv("HIDE_DOCS", "false").lower() == "true" else "/openapi.json",
    )

    # Apply security configuration
    configure_security(app)

    # Configure logging
    configure_production_logging(app)

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        logger.info("🚀 DevSkyy API starting with enterprise security")

        # Run security scan on startup
        security_manager = EnterpriseSecurityManager()
        scan_results = security_manager.scan_for_vulnerabilities()

        if scan_results["critical"] > 0:
            logger.critical(f"⚠️ {scan_results['critical']} critical vulnerabilities found!")

        logger.info(f"Security scan complete: {scan_results['total_found']} issues found")

    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("👋 DevSkyy API shutting down")

    return app


# Example usage
if __name__ == "__main__":
    import uvicorn

    app = create_secure_app()

    # Production configuration
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_keyfile=os.getenv("SSL_KEY_FILE"),
        ssl_certfile=os.getenv("SSL_CERT_FILE"),
        log_level="info",
        access_log=True,
        use_colors=False,
        server_header=False,  # Don't expose server info
        date_header=False,  # Don't expose date
    )
