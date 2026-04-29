<claude-mem-context>

</claude-mem-context>

# api/ — FastAPI endpoint layer (78 Python files)

HTTP surface for the platform. Every file is an `APIRouter` mounted into the app. One file per resource.

## Key endpoints

- `dashboard.py` — backend for the Next.js `frontend/` dashboard, exposes the 6 SuperAgents (`/agents`, `/agents/{type}`, `/agents/{type}/execute`, etc.)
- `agents.py` — direct agent invocation
- `gateway.py` — external request routing
- `graphql_server.py` — GraphQL surface (alternative to REST)
- `ai_3d_endpoints.py` — 3D generation (delegates to `ai_3d/`)
- `ar_sessions.py` — AR fitting room session lifecycle
- `elementor_3d.py` — Elementor widget endpoints for the WP theme
- `gdpr.py` — data export, deletion, consent endpoints
- `brand.py` — brand-voice metadata
- `admin_dashboard.py` — admin-only ops (auth required)

## Conventions

- Use `APIRouter()` per file with a clear prefix and tags. Mount in `main_enterprise.py`.
- Endpoint typing: use `Literal[...]` for enum-like path/query params, not bare `str`.
- Errors: raise `HTTPException` with proper status codes. 4xx for client errors, 5xx for server.
- Response models are Pydantic models; declare them, do not return bare dicts (FastAPI wraps but type safety improves).
- Auth: gated endpoints use the dependency from `security/auth.py`. GDPR-relevant endpoints additionally pull from `security_ops_agent`.
- Any endpoint that triggers a paid model call (FASHN, Tripo, Meshy) MUST go through the corresponding agent — never call the provider directly.

## Don't

- Don't put business logic in endpoint handlers. Endpoints are thin: parse → call agent/service → format response.
- Don't do DB writes from an endpoint without going through `services/` or an agent.
- Don't hardcode SkyyRose product IDs, collection slugs, or URLs. Use config from `config/`.

## Related

- Agents: `agents/` (SuperAgent layer)
- Services consumed: `services/`
- Frontend client: `frontend/lib/api/`
- Auth: `security/`
