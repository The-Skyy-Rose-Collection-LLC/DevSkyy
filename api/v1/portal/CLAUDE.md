# api/v1/portal/ — Tenant self-service portal

Customer-facing endpoints for tenants to manage their own subscriptions, usage, billing, and team. Auth-gated by `Depends(get_current_user)` from `security/jwt_oauth2_auth.py`. All routers nest under `/api/v1/portal/`.

## Key files

- `__init__.py` — composes the four sub-routers into `portal_router` (prefix `/portal`, tag `Portal`).
- `subscriptions.py` — subscribe / upgrade / cancel plan; reads plan catalog from billing config.
- `usage.py` — per-tenant usage summary (API calls, generation count, storage).
- `billing.py` — `GET /billing/invoices` (last 10 from Stripe), `POST /billing/portal-session` (Stripe Billing Portal redirect URL).
- `team.py` — list/invite/remove team members within the tenant.

## Conventions

- Stripe access goes through `billing.stripe_client.StripeClient` — never call the `stripe` SDK directly from a portal handler.
- Customer ID resolution: read `request.state.stripe_customer_id` (populated by `tenant_middleware` + tenant DB lookup). If absent and the operation requires a customer, return `422` with a clear "subscribe first" message — not a 5xx.
- `limit` query parameter is always clamped: `max(1, min(limit, 100))`.
- Tenant scoping is implicit via `get_current_user` → `TokenPayload`. Never accept `tenant_id` from the request body — it must come from the authenticated token.

## Don't

- Don't hit Stripe production from tests. The `StripeClient` accepts an injected fake; portal tests use it via `request.state`.
- Don't expose another tenant's invoices or usage. Every query must include the authenticated tenant's customer ID in the filter.
- Don't return raw Stripe responses to the client. Wrap in the local `InvoiceItem` / `PortalSessionResponse` models so renames in Stripe's API don't leak.

## Related

- Stripe client: `billing/stripe_client.py`
- Auth: `security/jwt_oauth2_auth.py`, `core/auth/token_payload.py`
- Tenant middleware: `core/middleware/` (populates `request.state.stripe_customer_id`)
- Mount: `api/v1/__init__.py`
