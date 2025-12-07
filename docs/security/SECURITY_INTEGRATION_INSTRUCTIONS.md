# Security Integration Instructions

## Required Imports

```python
from security.encryption import EncryptionManager
from security.gdpr_compliance import GDPRManager
from webhooks.webhook_system import WebhookManager

# API routers (match main application module paths)
from api.v1.auth import router as auth_router
from api.v1.webhooks import router as webhooks_router
from api.v1.monitoring import router as monitoring_router
```

> Note: In the main application these imports are attempted inside try/except blocks to allow optional components. Import failures are handled gracefully at startup.

## Router Mounting

```python
# Mount/auth routers using the router objects imported from api.v1 modules
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(webhooks_router, prefix="/api/v1/webhooks")
app.include_router(monitoring_router, prefix="/api/v1/monitoring")
```

Notes:
- The router names and import paths above match the main FastAPI application (`main.py`) which imports routers from `api.v1.*` modules and registers them with prefixes like `/api/v1`.
- Use the router objects (e.g., `auth_router`) directly when calling `app.include_router(...)` — do not append duplicate suffixes like `_router_router`.
- Wrap optional integrations in try/except when used in startup code so the app can run even if a subsystem is not installed.
