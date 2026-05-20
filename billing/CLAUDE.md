# billing/ — Multi-Tier SaaS Billing

**Complete quota + entitlement + Stripe integration for the DevSkyy/SkyyRose platform.** 7 files, no external service stubs — graceful-degradation everywhere.

## Tier Catalogue (`plans.py:77`)

| Tier | Price | Renders/mo | 3D models/mo | Social packs/mo | Characters | API req/min | Storage | Intents |
|------|-------|------------|--------------|------------------|-----------|-------------|---------|---------|
| `free` | $0 | 10 | 2 | 5 | 1 | 10 | 1 GB | `product-render`, `product-copy` |
| `starter` | $29/mo | 100 | 20 | 50 | 5 | 60 | 10 GB | 8 intents (incl. virtual-tryon, RAG) |
| `pro` | $99/mo | 1000 | 200 | 500 | 25 | 300 | 100 GB | `*` (all) |
| `enterprise` | custom | unlimited | unlimited | unlimited | unlimited | 1000 | 1 TB | `*` (all) |

## Public Surface (`billing/__init__.py`)

| Symbol | Source | Purpose |
|--------|--------|---------|
| `TIER_LIMITS`, `TierLimits` | `plans.py` | Frozen dataclass dict — single source of truth |
| `get_limits(tier)`, `intent_allowed(tier, intent)`, `quota_remaining(tier, intent, used)` | `plans.py` | Pure read helpers |
| `UsageMetering` | `metering.py` | Per-tenant per-intent counters (Redis or in-process fallback) |
| `EntitlementChecker`, `EntitlementResult` | `entitlements.py` | Combined plan + quota check |
| `StripeClient` | `stripe_client.py` | Stripe SDK wrapper with stub-mode degradation |
| `handle_stripe_webhook(payload, signature)` | `webhooks.py` | Sync dispatcher; idempotent; never raises |

## Hard Rules

### Unlimited Sentinel

- **`-1` means unlimited** in every `*_per_month` field AND in `quota_remaining()` return value
- **Correct check**: `if remaining == -1 or remaining > 0: allow()`. Writing `if remaining > 0` rejects all enterprise traffic
- `frozenset(["*"])` in `allowed_intents` = wildcard, all intents allowed. Test with `"*" in limits.allowed_intents`

### Graceful Degradation

- `StripeClient` operates in **stub mode** when `STRIPE_SECRET_KEY` absent or `stripe` package not installed — every method returns `None`/`False`/`[]`, never raises. Platform boots without Stripe (`stripe_client.py:38-55`)
- `UsageMetering` falls back to in-process `defaultdict(int)` when Redis unavailable (`metering.py:54-60`) — **counters lost on restart** in fallback mode
- `billing_middleware` **fails open** on entitlement-check error (`middleware.py:100-103`) — never blocks legitimate traffic because Redis is flaky. Logged as `billing_middleware entitlement check error`

### Middleware Wiring

- **Mount order in `main_enterprise.py`**: tenant_middleware → billing_middleware → route handlers. `billing_middleware` reads `request.state.tenant_id` + `request.state.tenant_tier` set by tenant_middleware
- **Path gate**: `_CREATIVE_PATH_RE = ^/api/v\d+/(elite-studio|portal)/` (`middleware.py:37`). Any future `v3`, `v4`, etc. is **auto-enforced** — do not add per-route gates
- **Intent header**: `X-Creative-Intent` — caller declares operation. Missing header = pass-through (route handler validates further)
- **Response headers added**: `X-Quota-Remaining` (or `"unlimited"`), `X-Quota-Intent`
- **Quota exhausted = HTTP 402** with JSON body `{error, message, intent, tier, upgrade_to, upgrade_url}`

### Metering Discipline

- **Out-of-band write**: `asyncio.create_task(_record_usage_async(...))` after response returns. Redis RTT does not block user. Trade-off: worker crash between response-send and increment = free request (logged as `billing.record_failed`)
- **Only 2xx/3xx consume quota** — 4xx/5xx skip metering (`middleware.py:129`)
- **Redis key schema**: `elite_studio:usage:{tenant_id}:{intent}:{YYYY-MM}` with 62-day TTL — auto-eviction, no cleanup job (`metering.py:28-29`)
- New intents MUST add an entry to `_INTENT_QUOTA_MAP` (`plans.py:128`) — missing intent silently bills against `renders_per_month`

### Stripe Wiring

- `STRIPE_PRICE_IDS` env format: `starter:price_abc123,pro:price_def456` (comma-separated `tier:price_id` pairs, `stripe_client.py:212-237`)
- `STRIPE_WEBHOOK_SECRET` env: required in prod for signature verification. Missing = dev mode (warning + parse without verify, `webhooks.py:73-83`)
- **Handled webhook events** (`webhooks.py:35-41`): `customer.subscription.{created,updated,deleted}`, `invoice.paid`, `invoice.payment_failed`
- **Webhook handler is sync + idempotent** — returns `{"event": str, "processed": bool}`. Router returns HTTP 200 even on `processed=False` to prevent Stripe retry storms
- **Tier resolved from `price.metadata.tier`** preferred, falls back to nickname substring match in `["enterprise", "pro", "starter", "free"]` (`webhooks.py:185-201`)

### Subscription Status → Tier

- `canceled`, `unpaid`, `incomplete_expired` → tier downgrades to `free`
- `active`, `trialing`, `past_due` → tier from price metadata (above)

## Patterns

```python
# Check entitlement before paid op
from billing import EntitlementChecker, UsageMetering

checker = EntitlementChecker(UsageMetering(redis_url=os.getenv("REDIS_URL")))
result = checker.check(tenant_id="t1", tier="starter", intent="virtual-tryon")
if not result.allowed:
    raise HTTPException(402, result.reason)

# Stripe portal session
from billing import StripeClient

stripe = StripeClient()
url = stripe.create_portal_session(customer_id, return_url="https://app/account")
```

## Consumers

- `api/v1/portal/billing.py` — `StripeClient.create_portal_session`, `list_invoices`, `cancel_subscription`
- `api/v1/portal/subscriptions.py` — `StripeClient.create_subscription`, `get_price_id`
- `api/v1/portal/webhooks.py` — POST `/portal/webhooks/stripe` calls `handle_stripe_webhook`
- `main_enterprise.py` — `app.middleware("http")(billing_middleware)` mount
- Anywhere a paid intent dispatches — explicit `EntitlementChecker.check()` call OR rely on middleware-level enforcement

## Not Yet Wired

- Webhook handler emits structured logs (`tenant_tier_update customer=... new_tier=...`) but **does not directly persist tenant records** — relies on caller / background worker to consume the log lines and update DB. The async DB update is a TODO at `webhooks.py:142-153`. If you wire it, do so via `database/` models, not inside webhook handler

## STOP-AND-SHOW

Any code path that calls `StripeClient.create_subscription`, `cancel_subscription`, or touches Stripe Customer creation is a **production-money path**. Per project STOP-AND-SHOW protocol, surface customer_id + tier + price_id before dispatch. Do not bury Stripe writes inside background tasks without explicit confirmation in the call chain
