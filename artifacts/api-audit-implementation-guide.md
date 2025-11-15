# API Audit Implementation Guide - Quick Start

**Date:** 2025-11-15
**Target:** Fix critical P0 issues before production deployment
**Timeline:** 2 weeks (Phase 1 + Phase 2)

---

## Prerequisites

Install required dependencies:

```bash
# OpenAPI validation
pip install openapi-spec-validator

# Client SDK generation (optional)
npm install -g @openapitools/openapi-generator-cli

# Redis for rate limiting (production)
pip install redis aioredis
```

---

## Phase 1: Critical Fixes (Week 1)

### Fix 1: Implement OpenAPI Auto-Generation (Days 1-2)

**File:** `/home/user/DevSkyy/utils/openapi_generator.py` ✅ Already created

**Step 1:** Add to main.py startup event

```python
# File: /home/user/DevSkyy/main.py

# Add import at top
from utils.openapi_generator import setup_openapi_export

# Add to existing startup_event() function (around line 360)
@app.on_event("startup")
async def startup_event():
    """Initialize application components on startup."""
    logger.info("🚀 Starting DevSkyy Platform...")

    # ... existing initialization code ...

    # ADD THIS: Export OpenAPI specification
    try:
        setup_openapi_export(app)
        logger.info("✅ OpenAPI specification exported")
    except Exception as e:
        logger.warning(f"⚠️ OpenAPI export failed: {e}")

    # ... rest of existing code ...
```

**Step 2:** Create static endpoint to serve OpenAPI spec

```python
# File: /home/user/DevSkyy/main.py

# Add this endpoint after line 694 (after /status endpoint)
@app.get("/api/openapi.json")
async def get_openapi_spec():
    """
    Get OpenAPI specification (always available, even in production)

    Returns:
        OpenAPI 3.1.0 specification in JSON format

    Standards:
        - OpenAPI 3.1.0: https://spec.openapis.org/oas/v3.1.0
    """
    try:
        import json
        from pathlib import Path

        spec_path = Path("artifacts/openapi.json")

        if not spec_path.exists():
            # Generate on-the-fly if not found
            from utils.openapi_generator import export_openapi_spec

            spec = export_openapi_spec(app)
            return spec

        with open(spec_path) as f:
            return json.load(f)

    except Exception as e:
        logger.error(f"Failed to serve OpenAPI spec: {e}")
        raise HTTPException(status_code=500, detail="OpenAPI spec not available")
```

**Step 3:** Test the implementation

```bash
# Start the server
python main.py

# In another terminal, verify OpenAPI spec
curl http://localhost:8000/api/openapi.json | jq '.info.title'
# Expected: "DevSkyy - Luxury Fashion AI Platform"

# Validate the spec
python -c "from utils.openapi_generator import validate_openapi_spec; validate_openapi_spec()"
# Expected: ✅ OpenAPI spec is valid
```

**Step 4:** Add to documentation

Create `/home/user/DevSkyy/docs/api-documentation.md`:

```markdown
# API Documentation

## OpenAPI Specification

The DevSkyy API follows OpenAPI 3.1.0 specification.

**Access:**
- JSON Spec: `GET /api/openapi.json`
- Swagger UI: `GET /docs` (development only)
- ReDoc: `GET /redoc` (development only)

**Download:**
```bash
curl https://api.devskyy.com/api/openapi.json > openapi.json
```

**Validation:**
```bash
pip install openapi-spec-validator
openapi-spec-validator openapi.json
```
```

---

### Fix 2: Add Authentication to Unprotected Endpoints (Days 3-4)

**Affected Files:** All API routers in `/home/user/DevSkyy/api/v1/`

**Endpoints Requiring Authentication:**

**File: `/home/user/DevSkyy/api/v1/ecommerce.py`**

```python
# BEFORE (line 97):
@router.post("/import-products", response_model=ImportProductsResponse)
async def import_products(
    request: ImportProductsRequest,
    background_tasks: BackgroundTasks,
    importer: WooCommerceImporterService = Depends(get_importer_service),
):

# AFTER:
from security.jwt_auth import get_current_active_user, require_developer, TokenData

@router.post("/import-products", response_model=ImportProductsResponse)
async def import_products(
    request: ImportProductsRequest,
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(require_developer),  # ADD THIS
    importer: WooCommerceImporterService = Depends(get_importer_service),
):
```

**Apply to ALL endpoints in ecommerce.py:**
- `POST /import-products` - Add `Depends(require_developer)`
- `POST /generate-seo` - Add `Depends(get_current_active_user)`
- `POST /workflow/complete` - Add `Depends(require_developer)`
- `GET /health` - Keep public (no auth)

**File: `/home/user/DevSkyy/main.py` - Theme Builder Endpoints**

```python
# Around line 1048 - build_and_deploy_theme
@app.post("/api/v1/themes/build-and-deploy")
async def build_and_deploy_theme(
    theme_request: dict[str, Any],
    current_user: TokenData = Depends(require_developer),  # ADD THIS
):

# Apply to all theme endpoints:
# - POST /api/v1/themes/build-and-deploy
# - GET /api/v1/themes/build-status/{build_id}
# - POST /api/v1/themes/upload-only
# - GET /api/v1/themes/system-status (read-only, use get_current_active_user)
# - POST /api/v1/themes/skyy-rose/build
# - GET /api/v1/themes/credentials/status
# - POST /api/v1/themes/credentials/test
```

**File: `/home/user/DevSkyy/api/v1/content.py`**

```python
# Add to all content generation endpoints
from security.jwt_auth import get_current_active_user, TokenData

# Apply to:
# - POST /generate
# - POST /batch
# - GET /templates
# - POST /templates
# - GET /history
```

**Create Authentication Audit Script:**

```python
# File: /home/user/DevSkyy/scripts/audit_authentication.py

import ast
import os
from pathlib import Path


def check_endpoint_auth(file_path: str) -> list[str]:
    """Check if endpoint has authentication dependency."""
    with open(file_path) as f:
        content = f.read()

    tree = ast.parse(content)
    endpoints_without_auth = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check if it's a route decorator
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    if hasattr(decorator.func, "attr") and decorator.func.attr in [
                        "get",
                        "post",
                        "put",
                        "patch",
                        "delete",
                    ]:
                        # Check if function has auth dependency
                        has_auth = False
                        for arg in node.args.args:
                            if arg.annotation and "Depends" in ast.unparse(arg.annotation):
                                if any(
                                    auth in ast.unparse(arg.annotation)
                                    for auth in [
                                        "get_current_active_user",
                                        "require_admin",
                                        "require_developer",
                                    ]
                                ):
                                    has_auth = True
                                    break

                        if not has_auth:
                            # Get route path
                            route_path = decorator.args[0].value if decorator.args else "unknown"
                            endpoints_without_auth.append(f"{node.name} - {route_path}")

    return endpoints_without_auth


def audit_all_endpoints():
    """Audit all API endpoints for authentication."""
    api_dir = Path("api/v1")
    all_unprotected = []

    for file_path in api_dir.glob("*.py"):
        if file_path.name.startswith("__"):
            continue

        unprotected = check_endpoint_auth(str(file_path))
        if unprotected:
            all_unprotected.append((str(file_path), unprotected))

    print("🔍 Authentication Audit Report")
    print("=" * 60)

    if not all_unprotected:
        print("✅ All endpoints have authentication!")
    else:
        print(f"⚠️  Found {sum(len(u) for _, u in all_unprotected)} unprotected endpoints:")
        print()

        for file_path, endpoints in all_unprotected:
            print(f"📄 {file_path}")
            for endpoint in endpoints:
                print(f"   - {endpoint}")
            print()


if __name__ == "__main__":
    audit_all_endpoints()
```

**Run the audit:**

```bash
python scripts/audit_authentication.py
```

---

### Fix 3: Implement Error Ledger (Day 5)

**File:** `/home/user/DevSkyy/utils/error_ledger.py`

```python
"""
Error Ledger for DevSkyy Platform

WHY: Track all errors across application runs per Truth Protocol Rule 14
HOW: JSON file with structured error records, correlation IDs, context
IMPACT: Enables error analysis, debugging, and continuous improvement

Truth Protocol Rule 14: Error ledger required for every run and CI cycle
"""

import json
import logging
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ErrorLedger:
    """
    Enterprise error ledger with structured logging.

    Records all errors with:
    - Timestamp and correlation ID
    - Error type and message
    - Full stack trace
    - Request context
    - User information
    """

    def __init__(self, run_id: Optional[str] = None, output_dir: str = "artifacts"):
        """
        Initialize error ledger.

        Args:
            run_id: Unique run identifier (auto-generated if not provided)
            output_dir: Directory for error ledger files
        """
        self.run_id = run_id or str(uuid.uuid4())[:8]
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.ledger_path = self.output_dir / f"error-ledger-{self.run_id}.json"
        self.errors: list[dict[str, Any]] = []

        # Create initial ledger file
        self._initialize_ledger()

        logger.info(f"✅ Error ledger initialized: {self.ledger_path}")

    def _initialize_ledger(self):
        """Initialize error ledger file with metadata."""
        metadata = {
            "run_id": self.run_id,
            "started_at": datetime.now().isoformat(),
            "platform": "DevSkyy Enterprise v5.1.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "errors": [],
        }

        with open(self.ledger_path, "w") as f:
            json.dump(metadata, f, indent=2)

    def log_error(
        self,
        error: Exception,
        context: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """
        Log error to ledger.

        Args:
            error: Exception instance
            context: Additional context (request data, etc.)
            request_id: Request correlation ID
            user_id: User identifier (if authenticated)
        """
        error_record = {
            "error_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "user_id": user_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stack_trace": traceback.format_exc(),
            "context": context or {},
        }

        self.errors.append(error_record)

        # Append to file
        self._append_to_ledger(error_record)

        logger.error(
            f"❌ Error logged to ledger: {error_record['error_type']} - {error_record['error_message'][:100]}"
        )

    def _append_to_ledger(self, error_record: dict[str, Any]):
        """Append error record to ledger file."""
        try:
            with open(self.ledger_path) as f:
                ledger = json.load(f)

            ledger["errors"].append(error_record)
            ledger["total_errors"] = len(ledger["errors"])
            ledger["last_updated"] = datetime.now().isoformat()

            with open(self.ledger_path, "w") as f:
                json.dump(ledger, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to append to error ledger: {e}")

    def get_summary(self) -> dict[str, Any]:
        """Get error ledger summary."""
        error_types = {}
        for error in self.errors:
            error_type = error["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1

        return {
            "run_id": self.run_id,
            "total_errors": len(self.errors),
            "error_types": error_types,
            "ledger_path": str(self.ledger_path),
        }


# Global error ledger instance
_error_ledger: Optional[ErrorLedger] = None


def get_error_ledger() -> ErrorLedger:
    """Get global error ledger instance."""
    global _error_ledger
    if _error_ledger is None:
        _error_ledger = ErrorLedger()
    return _error_ledger


def log_error(
    error: Exception,
    context: Optional[dict[str, Any]] = None,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """
    Convenience function to log error to global ledger.

    Example:
        try:
            risky_operation()
        except Exception as e:
            log_error(e, context={"operation": "risky_operation"})
            # Continue processing per Truth Protocol Rule 10
    """
    ledger = get_error_ledger()
    ledger.log_error(error, context, request_id, user_id)
```

**Step 2: Integrate with main.py exception handlers**

```python
# File: /home/user/DevSkyy/main.py

# Add import
from utils.error_ledger import get_error_ledger, log_error

# Update exception handlers (around line 265-288)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP exception: {exc.detail} - {request.url}")

    # ADD THIS: Log to error ledger
    log_error(
        exc,
        context={"url": str(request.url), "method": request.method, "status_code": exc.status_code},
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(
        status_code=exc.status_code, content={"error": True, "message": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # ADD THIS: Log to error ledger
    log_error(
        exc,
        context={"url": str(request.url), "method": request.method, "unhandled": True},
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": True, "message": "Internal server error", "timestamp": datetime.now().isoformat()},
    )


# Add shutdown event to log summary
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("🛑 Shutting down DevSkyy Platform...")

    try:
        # ADD THIS: Log error ledger summary
        ledger = get_error_ledger()
        summary = ledger.get_summary()
        logger.info(f"📊 Error Ledger Summary:")
        logger.info(f"   Run ID: {summary['run_id']}")
        logger.info(f"   Total Errors: {summary['total_errors']}")
        logger.info(f"   Ledger Path: {summary['ledger_path']}")

        # ... existing cleanup code ...

    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")
```

**Step 3: Test error ledger**

```bash
# Start the server
python main.py

# Trigger an error (invalid endpoint)
curl http://localhost:8000/api/v1/invalid-endpoint

# Check error ledger
cat artifacts/error-ledger-*.json | jq '.total_errors'
# Expected: 1
```

---

## Phase 2: Production Hardening (Week 2)

### Fix 4: Redis-Backed Rate Limiting (Days 1-2)

**Install Redis:**

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

**File:** `/home/user/DevSkyy/utils/redis_rate_limiter.py`

```python
"""
Redis-backed rate limiting for production deployments

WHY: Share rate limit state across workers and persist across restarts
HOW: Use Redis with sliding window algorithm
IMPACT: Consistent rate limiting in distributed environments
"""

import logging
import time
from typing import Optional, Tuple

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """
    Production-ready rate limiter using Redis.

    Features:
    - Sliding window algorithm
    - Distributed state (shared across workers)
    - Persistent across restarts
    - Configurable per endpoint
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize Redis rate limiter.

        Args:
            redis_url: Redis connection URL
        """
        self.redis = redis.from_url(redis_url, decode_responses=True)
        logger.info(f"✅ Redis rate limiter initialized: {redis_url}")

    async def is_allowed(
        self, client_id: str, max_requests: int = 60, window_seconds: int = 60
    ) -> Tuple[bool, Optional[dict]]:
        """
        Check if request is allowed under rate limit.

        Args:
            client_id: Unique client identifier (IP, user_id, API key)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        try:
            current_time = time.time()
            window_start = current_time - window_seconds

            key = f"rate_limit:{client_id}:{max_requests}:{window_seconds}"

            # Remove old entries
            await self.redis.zremrangebyscore(key, 0, window_start)

            # Count requests in window
            count = await self.redis.zcard(key)

            rate_limit_info = {
                "limit": max_requests,
                "remaining": max(0, max_requests - count),
                "reset": int(current_time + window_seconds),
            }

            if count < max_requests:
                # Add current request
                await self.redis.zadd(key, {str(current_time): current_time})
                await self.redis.expire(key, window_seconds)
                return True, rate_limit_info
            else:
                return False, rate_limit_info

        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # Fail open (allow request if Redis is down)
            return True, None

    async def reset(self, client_id: str):
        """Reset rate limit for a client."""
        pattern = f"rate_limit:{client_id}:*"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

    async def close(self):
        """Close Redis connection."""
        await self.redis.close()


# Global instance
_redis_rate_limiter: Optional[RedisRateLimiter] = None


def get_redis_rate_limiter() -> RedisRateLimiter:
    """Get global Redis rate limiter instance."""
    global _redis_rate_limiter
    if _redis_rate_limiter is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _redis_rate_limiter = RedisRateLimiter(redis_url)
    return _redis_rate_limiter
```

**Update security middleware:**

```python
# File: /home/user/DevSkyy/api/security_middleware.py

# Add import
from utils.redis_rate_limiter import get_redis_rate_limiter

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware"""

    def __init__(self, app, use_redis_rate_limiter: bool = True):
        super().__init__(app)
        self.use_redis = use_redis_rate_limiter

        if use_redis:
            self.redis_rate_limiter = get_redis_rate_limiter()
        else:
            self.rate_limiter = RateLimiter()  # In-memory fallback

        self.threat_detector = ThreatDetector()
        self.request_log = deque(maxlen=1000)

    async def dispatch(self, request: Request, call_next):
        # ... existing code ...

        # Replace rate limiting section (around line 202)
        endpoint_category = self._get_endpoint_category(request.url.path)

        if self.use_redis:
            is_allowed, rate_info = await self.redis_rate_limiter.is_allowed(
                client_ip, max_requests=self._get_rate_limit(endpoint_category)
            )
        else:
            is_allowed, rate_message = self.rate_limiter.is_allowed(client_ip, endpoint_category)
            rate_info = {"message": rate_message}

        if not is_allowed:
            return await self._rate_limit_response(request_id, client_ip, rate_info.get("message", "Rate limit exceeded"))

        # ... rest of existing code ...

    def _get_rate_limit(self, category: str) -> int:
        """Get rate limit for category."""
        limits = {
            "default": 60,
            "auth": 10,
            "ml": 30,
            "agents": 100,
            "admin": 200,
        }
        return limits.get(category, 60)
```

**Update main.py to use Redis rate limiter:**

```python
# File: /home/user/DevSkyy/main.py

# Update middleware registration (around line 240)
if SECURITY_MODULES_AVAILABLE:
    use_redis = ENVIRONMENT == "production"  # Use Redis in production
    app.add_middleware(BaseHTTPMiddleware, dispatch=lambda req, call_next: SecurityMiddleware(app, use_redis_rate_limiter=use_redis).dispatch(req, call_next))
```

---

### Fix 5: Add Request Body Size Limits (Day 3)

**File:** `/home/user/DevSkyy/middleware/size_limit.py`

```python
"""Request body size limit middleware"""

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware


class LimitUploadSize(BaseHTTPMiddleware):
    """
    Middleware to limit request body size.

    Prevents DoS attacks via large payloads.
    """

    def __init__(self, app, max_upload_size: int = 10_000_000):
        """
        Initialize size limit middleware.

        Args:
            max_upload_size: Maximum request body size in bytes (default: 10MB)
        """
        super().__init__(app)
        self.max_upload_size = max_upload_size

    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")

            if content_length:
                content_length = int(content_length)
                if content_length > self.max_upload_size:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Request body too large. Maximum size: {self.max_upload_size / 1_000_000:.1f}MB",
                    )

        response = await call_next(request)
        return response
```

**Add to main.py:**

```python
# File: /home/user/DevSkyy/main.py

# Add import
from middleware.size_limit import LimitUploadSize

# Add middleware (around line 237, before GZipMiddleware)
app.add_middleware(LimitUploadSize, max_upload_size=10_000_000)  # 10MB limit
```

---

## Verification Steps

### 1. Test OpenAPI Spec

```bash
# Generate spec
python -c "from main import app; from utils.openapi_generator import export_openapi_spec; export_openapi_spec(app)"

# Validate
python -c "from utils.openapi_generator import validate_openapi_spec; validate_openapi_spec()"

# Access via API
curl http://localhost:8000/api/openapi.json | jq '.info.version'
```

### 2. Test Authentication

```bash
# Attempt unauthenticated request to protected endpoint
curl -X POST http://localhost:8000/api/v1/ecommerce/import-products
# Expected: 401 Unauthorized

# Login and get token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=test&password=test123" | jq -r '.access_token')

# Retry with token
curl -X POST http://localhost:8000/api/v1/ecommerce/import-products \
  -H "Authorization: Bearer $TOKEN"
# Expected: Success or 400 (requires valid data)
```

### 3. Test Error Ledger

```bash
# Start server
python main.py

# Trigger error
curl http://localhost:8000/invalid-endpoint

# Check ledger
ls -lh artifacts/error-ledger-*.json
cat artifacts/error-ledger-*.json | jq '.total_errors'
```

### 4. Test Rate Limiting

```bash
# Test local rate limiter
for i in {1..15}; do
  curl http://localhost:8000/health
  echo "Request $i"
done
# Expected: Some requests return 429 after limit exceeded

# With Redis (production)
export REDIS_URL=redis://localhost:6379
python main.py
# Test same as above
```

### 5. Test Request Size Limits

```bash
# Generate large payload (20MB - should fail)
dd if=/dev/zero of=/tmp/large.bin bs=1M count=20

# Send large request
curl -X POST http://localhost:8000/api/v1/test \
  --data-binary @/tmp/large.bin
# Expected: 413 Payload Too Large
```

---

## CI/CD Integration

Add to `.github/workflows/api-validation.yml`:

```yaml
name: API Validation & Error Ledger

on: [push, pull_request]

jobs:
  validate-api:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install openapi-spec-validator

      - name: Generate OpenAPI spec
        run: |
          python -c "from main import app; from utils.openapi_generator import export_openapi_spec; export_openapi_spec(app)"

      - name: Validate OpenAPI spec
        run: |
          python -c "from utils.openapi_generator import validate_openapi_spec; assert validate_openapi_spec()"

      - name: Check authentication coverage
        run: |
          python scripts/audit_authentication.py

      - name: Verify error ledger
        run: |
          test -f artifacts/error-ledger-*.json || (echo "Error ledger not found" && exit 1)

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: api-artifacts
          path: |
            artifacts/openapi.json
            artifacts/error-ledger-*.json
```

---

## Production Deployment Checklist

Before deploying to production, verify:

- [ ] OpenAPI spec generated and accessible at `/api/openapi.json`
- [ ] All business logic endpoints have authentication
- [ ] Error ledger created on startup
- [ ] Redis rate limiting configured and tested
- [ ] Request body size limits enforced
- [ ] CORS origins restricted to production domains
- [ ] SECRET_KEY set via environment variable
- [ ] Logging configured (Logfire or alternative)
- [ ] Monitoring enabled (Prometheus metrics)
- [ ] Documentation endpoints disabled (`/docs`, `/redoc`)
- [ ] Debug endpoints removed or secured

---

## Rollback Plan

If issues arise after deployment:

1. **Disable OpenAPI generation:**
   ```python
   # Comment out in main.py startup_event()
   # setup_openapi_export(app)
   ```

2. **Revert authentication changes:**
   - Remove `Depends(get_current_active_user)` from specific endpoints
   - Deploy updated code

3. **Fallback to in-memory rate limiting:**
   ```python
   # In main.py
   use_redis = False  # Force in-memory
   ```

4. **Monitor error ledger:**
   ```bash
   tail -f artifacts/error-ledger-*.json | jq '.errors[-1]'
   ```

---

## Support & Resources

**Full Audit Report:** `/home/user/DevSkyy/artifacts/api-audit-report-2025-11-15.md`

**Summary Report:** `/home/user/DevSkyy/artifacts/api-audit-summary.md`

**OpenAPI Generator:** `/home/user/DevSkyy/utils/openapi_generator.py`

**Next Steps After Implementation:**
1. Run full test suite: `pytest tests/ --cov`
2. Performance testing: `autocannon http://localhost:8000/health`
3. Security scan: `bandit -r api/`
4. Dependency audit: `pip-audit`

---

**Implementation Status:** Ready for Week 1 deployment

**Estimated Completion:** 2 weeks (Phase 1 + Phase 2)

**Production Ready After:** Phase 1 + Phase 2 completion
