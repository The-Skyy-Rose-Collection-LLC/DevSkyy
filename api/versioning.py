"""
DevSkyy Enterprise API Versioning Module
=========================================

Production-grade API versioning following:
- Microsoft REST API Guidelines
- Google Cloud API Design Guide
- Stripe API Versioning Best Practices

Features:
- URL path versioning (/api/v1/, /api/v2/)
- Header-based versioning (API-Version header)
- Query parameter versioning (?version=1)
- Sunset headers for deprecation
- Version negotiation
- Backward compatibility support

Dependencies (verified from PyPI December 2024):
- fastapi==0.104.1
- pydantic==2.5.2
"""

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import Enum
from functools import wraps

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    status,
)
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class VersionConfig:
    """API Versioning configuration"""

    # Current versions
    current_version: str = "v1"
    supported_versions: list[str] = field(default_factory=lambda: ["v1"])
    default_version: str = "v1"

    # Deprecated versions (still work but sunset warning sent)
    deprecated_versions: dict[str, date] = field(default_factory=dict)

    # Sunset versions (no longer work)
    sunset_versions: list[str] = field(default_factory=list)

    # Versioning strategy
    use_path_versioning: bool = True  # /api/v1/resource
    use_header_versioning: bool = True  # API-Version: 1
    use_query_versioning: bool = False  # ?version=1

    # Header names
    version_header: str = "API-Version"
    accept_version_header: str = "Accept-Version"

    # Response headers
    include_version_header: bool = True
    include_sunset_header: bool = True
    include_deprecation_header: bool = True


class VersionStatus(str, Enum):
    """API version lifecycle status"""

    CURRENT = "current"  # Latest stable version
    SUPPORTED = "supported"  # Still supported
    DEPRECATED = "deprecated"  # Works but sunset scheduled
    SUNSET = "sunset"  # No longer available


# =============================================================================
# Version Models
# =============================================================================


class APIVersion(BaseModel):
    """API version information"""

    version: str
    status: VersionStatus
    released: date | None = None
    deprecated: date | None = None
    sunset: date | None = None
    changelog_url: str | None = None


class VersionInfo(BaseModel):
    """Complete version information response"""

    current_version: str
    supported_versions: list[str]
    deprecated_versions: list[str]
    api_versions: list[APIVersion]


# =============================================================================
# Version Extraction
# =============================================================================


class VersionExtractor:
    """Extract API version from request"""

    def __init__(self, config: VersionConfig):
        self.config = config
        self._path_pattern = re.compile(r"/api/v(\d+(?:\.\d+)?(?:\.\d+)?)")

    def extract(self, request: Request) -> str | None:
        """
        Extract version from request using configured strategies

        Priority:
        1. URL path (/api/v1/)
        2. Header (API-Version: 1)
        3. Query parameter (?version=1)
        4. Default version
        """
        version = None

        # 1. Path versioning
        if self.config.use_path_versioning:
            version = self._extract_from_path(request.url.path)
            if version:
                return version

        # 2. Header versioning
        if self.config.use_header_versioning:
            version = self._extract_from_header(request)
            if version:
                return version

        # 3. Query versioning
        if self.config.use_query_versioning:
            version = request.query_params.get("version")
            if version:
                return f"v{version}" if not version.startswith("v") else version

        # 4. Default
        return self.config.default_version

    def _extract_from_path(self, path: str) -> str | None:
        """Extract version from URL path"""
        match = self._path_pattern.search(path)
        if match:
            return f"v{match.group(1)}"
        return None

    def _extract_from_header(self, request: Request) -> str | None:
        """Extract version from headers"""
        # Try main header
        version = request.headers.get(self.config.version_header)
        if version:
            return f"v{version}" if not version.startswith("v") else version

        # Try accept header
        version = request.headers.get(self.config.accept_version_header)
        if version:
            return f"v{version}" if not version.startswith("v") else version

        return None


# =============================================================================
# Version Middleware
# =============================================================================


class VersionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle API versioning

    - Validates requested version
    - Adds version headers to response
    - Handles deprecation warnings
    - Blocks sunset versions
    """

    def __init__(self, app, config: VersionConfig = None):
        super().__init__(app)
        self.config = config or VersionConfig()
        self.extractor = VersionExtractor(self.config)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip non-API routes
        if not request.url.path.startswith("/api"):
            return await call_next(request)

        # Extract version
        version = self.extractor.extract(request)

        # Store in request state for handlers
        request.state.api_version = version

        # Check if version is sunset
        if version in self.config.sunset_versions:
            return JSONResponse(
                status_code=status.HTTP_410_GONE,
                content={
                    "error": "API version no longer available",
                    "version": version,
                    "current_version": self.config.current_version,
                    "supported_versions": self.config.supported_versions,
                    "message": f"API {version} has been sunset. Please upgrade to {self.config.current_version}",
                },
            )

        # Check if version is supported
        all_supported = self.config.supported_versions + list(
            self.config.deprecated_versions.keys()
        )
        if version not in all_supported:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Unsupported API version",
                    "requested_version": version,
                    "supported_versions": self.config.supported_versions,
                    "message": f"Version {version} is not supported. Use one of: {', '.join(self.config.supported_versions)}",
                },
            )

        # Process request
        response = await call_next(request)

        # Add version headers
        if self.config.include_version_header:
            response.headers["X-API-Version"] = version

        # Add deprecation headers
        if version in self.config.deprecated_versions:
            sunset_date = self.config.deprecated_versions[version]

            if self.config.include_deprecation_header:
                response.headers["Deprecation"] = "true"
                response.headers["X-Deprecated-Version"] = version

            if self.config.include_sunset_header and sunset_date:
                # RFC 8594 Sunset header format
                response.headers["Sunset"] = sunset_date.strftime("%a, %d %b %Y 00:00:00 GMT")
                response.headers["X-Sunset-Date"] = sunset_date.isoformat()

        return response


# =============================================================================
# Versioned Router
# =============================================================================


class VersionedAPIRouter(APIRouter):
    """
    API Router with built-in versioning support

    Usage:
        router_v1 = VersionedAPIRouter(version="v1", prefix="/api/v1")
        router_v2 = VersionedAPIRouter(version="v2", prefix="/api/v2")

        @router_v1.get("/users")
        async def get_users_v1():
            return {"version": "v1", "users": [...]}

        @router_v2.get("/users")
        async def get_users_v2():
            return {"version": "v2", "users": [...], "pagination": {...}}
    """

    def __init__(
        self,
        version: str,
        prefix: str = None,
        deprecated: bool = False,
        sunset_date: date = None,
        **kwargs,
    ):
        prefix = prefix or f"/api/{version}"
        super().__init__(prefix=prefix, **kwargs)

        self.api_version = version
        self.deprecated = deprecated
        self.sunset_date = sunset_date

    def add_api_route(self, path: str, endpoint: Callable, **kwargs):
        """Override to add version metadata to routes"""
        # Add version to operation_id if not set
        if "operation_id" not in kwargs:
            kwargs["operation_id"] = f"{endpoint.__name__}_{self.api_version}"

        # Add version tag
        tags = kwargs.get("tags") or []
        if self.api_version not in tags:
            tags.append(self.api_version)
        kwargs["tags"] = tags

        super().add_api_route(path, endpoint, **kwargs)


# =============================================================================
# Version-Aware Dependency
# =============================================================================


def get_api_version(request: Request) -> str:
    """
    Dependency to get current API version

    Usage:
        @app.get("/resource")
        async def get_resource(version: str = Depends(get_api_version)):
            if version == "v1":
                return v1_response()
            else:
                return v2_response()
    """
    return getattr(request.state, "api_version", "v1")


class RequireVersion:
    """
    Dependency to require specific API version

    Usage:
        @app.get("/new-feature", dependencies=[Depends(RequireVersion("v2"))])
        async def new_feature():
            return {"message": "Only available in v2"}
    """

    def __init__(self, minimum_version: str, maximum_version: str = None):
        self.minimum = self._parse_version(minimum_version)
        self.maximum = self._parse_version(maximum_version) if maximum_version else None

    def _parse_version(self, version: str) -> tuple:
        """Parse version string to tuple for comparison"""
        v = version.lstrip("v")
        parts = v.split(".")
        return tuple(int(p) for p in parts)

    async def __call__(self, request: Request):
        current = getattr(request.state, "api_version", "v1")
        current_tuple = self._parse_version(current)

        if current_tuple < self.minimum:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This endpoint requires API version v{'.'.join(map(str, self.minimum))} or higher",
            )

        if self.maximum and current_tuple > self.maximum:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This endpoint is not available in API version {current}. Maximum: v{'.'.join(map(str, self.maximum))}",
            )


# =============================================================================
# Version Decorator
# =============================================================================


def versioned(introduced: str, deprecated: str = None, sunset: str = None, replacement: str = None):
    """
    Decorator to mark endpoint version lifecycle

    Usage:
        @app.get("/old-endpoint")
        @versioned(introduced="v1", deprecated="v2", sunset="v3", replacement="/api/v2/new-endpoint")
        async def old_endpoint():
            return {"data": "..."}
    """

    def decorator(func: Callable):
        # Store version metadata
        func._api_version_introduced = introduced
        func._api_version_deprecated = deprecated
        func._api_version_sunset = sunset
        func._api_version_replacement = replacement

        @wraps(func)
        async def wrapper(*args, request: Request = None, **kwargs):
            # Add deprecation warning to response headers if applicable
            if deprecated and request:
                # This would need response middleware to actually set headers
                pass
            return await func(*args, request=request, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# Version Management API
# =============================================================================

version_router = APIRouter(prefix="/api", tags=["API Version"])


@version_router.get("/versions", response_model=VersionInfo)
async def get_api_versions():
    """Get information about all API versions"""
    config = VersionConfig()

    versions = []

    # Current version
    versions.append(APIVersion(version=config.current_version, status=VersionStatus.CURRENT))

    # Supported versions
    for v in config.supported_versions:
        if v != config.current_version:
            versions.append(APIVersion(version=v, status=VersionStatus.SUPPORTED))

    # Deprecated versions
    for v, sunset_date in config.deprecated_versions.items():
        versions.append(APIVersion(version=v, status=VersionStatus.DEPRECATED, sunset=sunset_date))

    # Sunset versions
    for v in config.sunset_versions:
        versions.append(APIVersion(version=v, status=VersionStatus.SUNSET))

    return VersionInfo(
        current_version=config.current_version,
        supported_versions=config.supported_versions,
        deprecated_versions=list(config.deprecated_versions.keys()),
        api_versions=versions,
    )


@version_router.get("/version")
async def get_current_version(version: str = Depends(get_api_version)):
    """Get current API version from request"""
    return {"version": version, "timestamp": datetime.now(UTC).isoformat()}


# =============================================================================
# Setup Helper
# =============================================================================


def setup_api_versioning(app: FastAPI, config: VersionConfig = None) -> None:
    """
    Configure API versioning for FastAPI application

    Usage:
        app = FastAPI()
        setup_api_versioning(app, VersionConfig(
            current_version="v2",
            supported_versions=["v1", "v2"],
            deprecated_versions={"v1": date(2025, 6, 1)}
        ))
    """
    config = config or VersionConfig()

    # Add middleware
    app.add_middleware(VersionMiddleware, config=config)

    # Add version routes
    app.include_router(version_router)

    # Update OpenAPI schema
    if app.openapi_schema:
        app.openapi_schema["info"]["version"] = config.current_version

    logger.info(f"API versioning configured. Current: {config.current_version}")


# =============================================================================
# Multi-Version Router Factory
# =============================================================================


class APIVersionFactory:
    """
    Factory to create versioned API structure

    Usage:
        factory = APIVersionFactory()

        # Create v1 endpoints
        v1 = factory.create_version("v1")

        @v1.get("/users")
        async def get_users_v1():
            return {"users": [...]}

        # Create v2 with changes
        v2 = factory.create_version("v2")

        @v2.get("/users")
        async def get_users_v2():
            return {"users": [...], "total": 100, "page": 1}

        # Apply to app
        factory.setup(app)
    """

    def __init__(self, config: VersionConfig = None):
        self.config = config or VersionConfig()
        self.versions: dict[str, VersionedAPIRouter] = {}

    def create_version(
        self,
        version: str,
        deprecated: bool = False,
        sunset_date: date = None,
        tags: list[str] = None,
    ) -> VersionedAPIRouter:
        """Create a new version router"""
        router = VersionedAPIRouter(
            version=version,
            deprecated=deprecated,
            sunset_date=sunset_date,
            tags=tags or [f"API {version}"],
        )
        self.versions[version] = router
        return router

    def setup(self, app: FastAPI) -> None:
        """Apply all version routers to app"""
        # Add middleware
        app.add_middleware(VersionMiddleware, config=self.config)

        # Add version info route
        app.include_router(version_router)

        # Add all version routers
        for _version, router in self.versions.items():
            app.include_router(router)

        logger.info(f"Configured versions: {list(self.versions.keys())}")


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Config
    "VersionConfig",
    "VersionStatus",
    # Models
    "APIVersion",
    "VersionInfo",
    # Classes
    "VersionExtractor",
    "VersionMiddleware",
    "VersionedAPIRouter",
    "RequireVersion",
    "APIVersionFactory",
    # Dependencies
    "get_api_version",
    # Decorators
    "versioned",
    # Routers
    "version_router",
    # Setup
    "setup_api_versioning",
]
