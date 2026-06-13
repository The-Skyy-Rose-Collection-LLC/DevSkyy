# api/v2/ — Enterprise unified API (creative ops, characters, assets, webhooks)

Successor surface to `api/v1/`. Mounted under `/api/v2` from `main_enterprise.py`. Used when v1 field shapes would break backward compatibility or when consolidating fragmented v1 endpoints behind a single resource.

## Key routers

- `creative.py` — unified creative operations (renders, edits, generations) — replaces fragmented v1 paths
- `characters.py` — character/persona management (mascot, brand voices, training subjects)
- `assets.py` — unified asset CRUD across image/3D/video
- `webhooks.py` — expanded webhook subscriptions (tenant-scoped event filters)
- `health.py` — liveness + per-tenant usage summary; reports Redis + LangGraph state

## Conventions

- Auth: `X-API-Key` header validated against env `API_KEY`. Same pattern as v1 service endpoints — `_get_api_key_dependency()` in each router file.
- Redis keys are namespaced: `elite_studio:v2:operation:{op_id}`, `elite_studio:result:{result_id}`, `queue:elite_studio_produce`. Don't reuse v1 key prefixes.
- Pydantic v2 models only. `BaseModel` with explicit field types; `field_validator` for cross-field rules.
- Long jobs flow through the Elite Studio queue (`queue:elite_studio_produce`), not directly through the handler. Handler enqueues, returns `op_id`, client polls.

## Don't

- Don't re-export v1 routers into v2. v2 is a deliberate API generation, not a re-mount.
- Don't share Redis keys with v1. Namespace collisions corrupt operation state across versions.
- Don't make v2 endpoints depend on v1 routers — the dependency direction is `main_enterprise.py → v2 → services/`. v2 has its own complete service path.

## Related

- v1 predecessor: `api/v1/`
- Elite Studio pipeline: `skyyrose/elite_studio/`
- Service singletons: `services/`
- Webhook delivery: `api/webhooks.py` (v0/global)
