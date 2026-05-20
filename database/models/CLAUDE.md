# database/models/ — Per-Model File Split (Multi-Tenancy)

**Newer model files separated from the `db.py` monolith.** Currently houses multi-tenancy models. Imports `Base` from `database.db` — same metadata, same Alembic migration target.

## Models

| Model | File | Purpose |
|-------|------|---------|
| `Tenant` | `tenant.py` | Top-level tenancy record (org/team/company). Holds plan tier + Stripe linkage + settings JSON |
| `TenantUser` | `tenant_user.py` | Joins users to tenants. Per-tenant role assignment |

## Public Surface (`database/models/__init__.py`)

- `Tenant`, `TenantUser`

## Tenant Schema (`tenant.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `String(36)` PK | UUID, default-generated via `uuid4()` |
| `name` | `String(255)` | Display name |
| `slug` | `String(100)` unique, indexed | URL-safe identifier |
| `stripe_customer_id` | `String(255)?` indexed | Linkage to Stripe Customer. Consumed by `billing/` + `api/v1/portal/billing.py` |
| `stripe_subscription_id` | `String(255)?` indexed | Active Stripe subscription |
| `tier` | `String(50)` indexed, default `"free"` | One of `free` / `starter` / `pro` / `enterprise`. Drives `billing.entitlements.EntitlementChecker` |
| `settings` | `Text` default `"{}"` | JSON blob — use `.get_settings()` / `.set_settings()` helpers |
| `created_at`, `updated_at` | `DateTime(timezone=True)` | UTC. `onupdate` auto-bumps |
| `is_active` | `Boolean` indexed, default `True` | Soft-delete gate |

## Hard Rules

### Shared `Base`

- **Both `Tenant` and `TenantUser` import `Base` from `database.db`** — same `MetaData` instance, same migration scope
- Adding a new model: create `models/<name>.py`, import `Base` from `database.db`, add to `models/__init__.py`. Otherwise Alembic autogenerate WILL miss it
- Never create a separate `DeclarativeBase` here — splits metadata, breaks `Base.metadata.create_all` and Alembic

### Tier Field Is Canonical

- `Tenant.tier` is the **single source of truth** for plan resolution. `billing/` reads it via `request.state.tenant_tier` (set by `tenant_middleware`)
- Tier values must match `billing.plans.TIER_LIMITS` keys exactly. Lowercase, no spaces: `free`, `starter`, `pro`, `enterprise`
- Default `"free"` ensures new tenants land on free tier without explicit assignment

### Stripe Linkage

- `stripe_customer_id` is **nullable** — tenants exist before checkout. Set on first successful Stripe checkout
- Both Stripe IDs indexed for webhook reverse-lookup (`customer.subscription.updated` → find tenant)
- Update via `billing.webhooks.handle_stripe_webhook` flow, NOT via direct write from API handlers

### Settings JSON Blob

- Stored as `Text` + `json.dumps/loads` helpers — keeps SQLite portable
- **Use the helpers** (`tenant.get_settings()` / `tenant.set_settings({...})`), never raw `tenant.settings = json.dumps(...)`. The helpers handle malformed JSON gracefully (returns `{}`)
- Settings is a free-form extensibility hatch — schema discipline lives in the calling code, not here

### Multi-Tenancy Pattern

- Every tenanted query: `WHERE tenant_id = ?` — enforced at repository / handler layer, NOT at DB layer (no row-level security yet)
- `TenantUser` row count = (tenant × user) join cardinality. A user can belong to multiple tenants
- Never look up a `Tenant` by `name` — always by `id` or `slug` (both indexed). `name` is display-only

## Consumers

- `billing/middleware.py` — reads `request.state.tenant_id` + `request.state.tenant_tier` (populated upstream from `Tenant` row)
- `billing/webhooks.py` — updates `Tenant.tier` + `Tenant.stripe_subscription_id` on `customer.subscription.*` events
- `api/v1/portal/*` — tenant self-service: subscriptions, billing portal, settings
- `core/middleware/tenant.py` — resolves `Tenant` from JWT / headers, attaches to `request.state`

## Not Yet Exported from `database/__init__.py`

- `Tenant` and `TenantUser` are imported directly: `from database.models import Tenant` (or `from database.models.tenant import Tenant`). Not re-exported from the top-level `database` package
- If you want them in the top-level public surface, update `database/__init__.py` AND keep backwards compatibility with existing direct-import callers
