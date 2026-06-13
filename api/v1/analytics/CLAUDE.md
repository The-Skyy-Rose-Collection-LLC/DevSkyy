# api/v1/analytics/ — Admin analytics surface

Six routers powering the DevSkyy admin dashboard's analytics views. Reads from production metrics stores (Prometheus, Redis, DB) and aggregates into dashboard-ready shapes.

## Key files

- `business.py` — business KPIs: revenue, orders, AOV, funnel conversion.
- `dashboard.py` — composite dashboard endpoint (cards, charts, time-series).
- `alerts.py` — alert event stream + acknowledge/resolve.
- `alert_configs.py` — alert rule CRUD (threshold, recipient, cooldown).
- `health.py` — operational health rollup across services + agents.
- `ml_pipelines.py` — ML pipeline run history, success rate, latency.

`__init__.py` exports all six routers individually; `api/v1/__init__.py` then re-exports `business_router` and `analytics_dashboard_router` at the top-level v1 surface, leaving the others to be mounted on demand by the admin app.

## Conventions

- Read-only. Analytics never writes to product/order/customer tables. Acknowledging alerts is the lone exception and goes through a dedicated alert store.
- Aggregations use time-window query parameters (`window=24h|7d|30d`) — never raw date ranges from the client.
- Long-running aggregations cache via `core.caching.multi_tier_cache.cached` with TTL matched to the window (shorter window = shorter TTL).
- Tenant scoping is implicit through `get_current_user`. Admin-only endpoints add a role check via `require_role("admin")` from `security/`.

## Don't

- Don't expose raw Prometheus queries to the client. Wrap in typed Pydantic response models so the metric surface can change without breaking the dashboard.
- Don't compute revenue from ad-hoc DB joins. Use the canonical aggregations in `services/analytics/` so business and dashboard endpoints agree to the cent.
- Don't mix alert delivery with alert config CRUD. `alerts.py` is the event surface; `alert_configs.py` is the rule surface — they share a store, not a router.

## Related

- Service layer: `services/analytics/`
- Cache: `core/caching/multi_tier_cache.py`
- Frontend consumer: `frontend/app/admin/` analytics pages
- Mount: `api/v1/__init__.py` (re-exports `analytics_dashboard_router`, `business_router`)
