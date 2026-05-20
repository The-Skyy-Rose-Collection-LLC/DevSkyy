# core/middleware/ — FastAPI ASGI Middleware

**Cross-cutting request middleware for the FastAPI app.** Mounted in `main_enterprise.py`.

## Public Surface (`core/middleware/__init__.py`)

- `tenant_middleware` — resolves tenant context from request headers / JWT → attaches to `request.state.tenant`

## Hard Rules

- Middleware functions MUST be `async` and follow ASGI signature: `async def mw(request, call_next)`
- Set `request.state.<key>` for downstream handler access. Never store request-scoped data in module globals (race conditions across concurrent requests)
- Mount order matters in `main_enterprise.py` — tenant middleware must run BEFORE any handler that calls `request.state.tenant`
- Auth middleware (lives in `security/` or `api/middleware/`, not here) must run before tenant middleware — tenant resolution often reads `request.state.user`

## Consumers

- `main_enterprise.py` — `app.middleware("http")(tenant_middleware)`
- `api/v1/portal/*` — reads `request.state.stripe_customer_id` (tenant-scoped Stripe IDs)
- `api/v2/*` — `elite_studio:v2:` Redis keys partitioned by tenant
