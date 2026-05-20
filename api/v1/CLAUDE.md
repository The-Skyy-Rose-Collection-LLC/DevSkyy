<claude-mem-context>

</claude-mem-context>

# api/v1/ — Versioned REST routers (25+ routers)

The stable v1 API surface. Each file or subpackage exports a FastAPI `APIRouter` consumed by `api/v1/__init__.py` and mounted into `main_enterprise.py`. Versioning policy: additive changes only; breaking shapes move to `api/v2/`.

## Key routers (exported in `__init__.py`)

- `analytics/` — 6 sub-routers (business, dashboard, alerts, alert_configs, health, ml_pipelines)
- `approval.py` — review/approve gates for render and content drops
- `assets.py` — asset processing job submission + status
- `autonomous.py` — autonomous agent loops (status, start, stop)
- `brand_assets.py` — brand asset library (fonts, logos, palettes)
- `catalog.py` — SkyyRose product catalog read API (33 SKUs from `skyyrose-catalog.csv`)
- `claude_sdk.py` — Claude Agent SDK orchestration endpoints
- `clothing_3d/` — TRELLIS clothing 3D pipeline (sync + async + Prometheus metrics)
- `code.py` — code scanning + auto-fix
- `commerce.py` — bulk product mutation, dynamic pricing
- `competitors.py` — competitor monitoring
- `descriptions.py` — product description generation
- `hf_spaces.py` — HuggingFace Spaces job dispatch
- `marketing.py` — campaign authoring
- `media.py` — 3D + media generation hub
- `ml.py` — direct ML prediction endpoints
- `monitoring.py` — system metrics + agent directory
- `orchestration.py` — multi-agent workflow submission
- `portal/` — tenant self-service (subscriptions, usage, billing, team)
- `social_media.py` — social content generation, scheduling, analytics
- `sync.py` — HF ↔ DevSkyy ↔ WordPress asset sync pipeline
- `training_status.py` — LoRA training progress polling
- `wordpress_agent.py` — WordPress agent invocation (read-only ops, never deploys directly)
- `wordpress_theme.py` — theme generation jobs

## Conventions

- Mount path is owned by `main_enterprise.py`, not by the router file. Routers declare `prefix=`/tags only at their own scope.
- Anything paid (FASHN, Tripo, Meshy, Replicate, fal, Stripe) goes through `services/` or `agents/`. Never call the provider SDK from a v1 handler.
- Long jobs use the async pattern in `clothing_3d/router.py`: `POST /generate/async` returns `202 + job_id + status_url`; `GET /jobs/{id}` polls. Redis Streams when `REDIS_URL` set, in-memory otherwise.
- Idempotency: jobs that can be replayed (TRELLIS, generate) use `IdempotencyCache` from `pipelines/clothing_3d/reliability.py`. Hash inputs, return cached result on hit.
- Auth: tenant endpoints require `Depends(get_current_user)` from `security/jwt_oauth2_auth.py`; service endpoints accept `X-API-Key` header (env `API_KEY`).

## Don't

- Don't create a new top-level router file without adding it to `api/v1/__init__.py`. Unimported routers are dead.
- Don't break field shapes in v1 — add fields, never remove or rename. Breaking changes belong in `api/v2/`.
- Don't bypass STOP-AND-SHOW for any handler that triggers a paid model call. Confirmation gate lives in the agent, not the endpoint, but the endpoint must surface cost in the response when relevant.

## Related

- Mount point: `main_enterprise.py`
- Service layer: `services/`
- Agent layer: `agents/`
- v2 successor: `api/v2/`
- Pipelines: `pipelines/clothing_3d/`
