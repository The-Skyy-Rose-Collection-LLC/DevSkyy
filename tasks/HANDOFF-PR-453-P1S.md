# Handoff — PR #453 P1 Hotfix (`hotfix/pr-453-p1s`)

**Base:** `main` @ `183058c9b` (PR #453 merge commit)
**Branch:** `hotfix/pr-453-p1s`
**Commits:** 6 (4 P1 clusters + 1 test update + 1 simplify pass)
**Scope:** 19 files changed, +326/-65 lines
**Verification:** 67 tests pass, ruff clean, compile clean, PHP/JS syntax clean

---

## What this PR does

Closes the 16 P1 findings from bot reviews of PR #453 (cubic-dev-ai + chatgpt-codex-connector) that were merged to `main` on 2026-04-19 without being addressed. Every finding was confirmed in code before fixing.

| Cluster | Commit | P1s closed |
|---|---|---|
| billing / tenant | `2e3aad9bf` | 5 |
| elite-studio / agents runtime | `95d1fb182` | 6 |
| brand SoT / deps | `44680bec4` | 2 |
| WP theme Phase 4 | `df0d66916` | 3 |
| tenant test contract | follow-up | — |
| simplify-pass perf + cleanup | follow-up | — |

---

## ⚠️ Breaking config changes — must configure before deploy

The tenant middleware fix closes two independent tenancy-spoof vectors that both depended on permissive defaults. **Existing services that relied on the old behavior will silently lose tenant context until the new config is in place.**

### 1. `JWT_SECRET_KEY` is now REQUIRED for tenant resolution from JWT

**Before this PR:** `core/middleware/tenant.py` decoded JWTs with `verify_signature=False`. Any token (forged, expired, unsigned) would be read for its `tenant_id` and `tier` claims. This was the highest-severity finding — a client could mint a token with `tenant_id=victim_tenant` and impersonate any tenant.

**After this PR:** JWTs are decoded with full signature verification + required `exp` claim. If `JWT_SECRET_KEY` is not set in the environment, the middleware refuses to trust ANY token (returns empty tenant context instead of falling back to unverified decode).

**What you need to do:**
- Set `JWT_SECRET_KEY` to match whatever `security/jwt_oauth2_auth.py` is using to sign tokens. These must be identical — they're the same secret.
- If you're running multiple services (API, workers, background agents), **every one of them** needs the same `JWT_SECRET_KEY` env var set.
- Accepted algorithms are now `HS256` and `HS512` only. If your tokens are signed with `RS256`, extend the `algorithms=[...]` list in `core/middleware/tenant.py:_extract_jwt_claims`.
- Tokens without an `exp` claim will now be rejected. Issue fresh tokens if needed.

### 2. `TENANT_HEADER_TRUST_TOKEN` gates the `X-Tenant-ID` header override

**Before this PR:** Any client sending `X-Tenant-ID: whatever` would have that value accepted as the tenant. Silent, trivial spoof.

**After this PR:** `X-Tenant-ID` is honored **only** when the caller also presents a matching `X-Internal-Service-Token` header, and only when `TENANT_HEADER_TRUST_TOKEN` is set in the environment. Defaults-closed: if the env var is unset, the header is ignored entirely.

**What you need to do:**
- Internal services that need to impersonate tenants (background workers, admin CLIs, scheduled jobs) must:
  1. Run in an env where `TENANT_HEADER_TRUST_TOKEN` is set to a high-entropy shared secret
  2. Send BOTH `X-Tenant-ID: <tenant>` AND `X-Internal-Service-Token: <matching value>` on every request
- External clients should NEVER see this token. Rotate it periodically.
- If no internal service needs the header override, leave `TENANT_HEADER_TRUST_TOKEN` unset — that's the safest posture.

### 3. Billing middleware now enforces ALL `/api/v*/elite-studio/*` and `/api/v*/portal/*`

**Before this PR:** Only `/api/v1/...` paths were enforced. A new `/api/v2/creative/...` endpoint already existed and was bypassing quota.

**After this PR:** Regex `^/api/v\d+/(elite-studio|portal)/` matches every API version. If you have internal endpoints that borrow this path shape but should NOT be quota-enforced, either rename them or add an explicit bypass list.

---

## ⚠️ Agent configuration issues to investigate

The bot reviews surfaced several P1s that point at deeper configuration problems in the agent stack. These are **not fixed in this PR** — each needs a design conversation before touching the code.

### Agent 1 — `agents/support_agent.py`

**Fixed:** RAG context type mismatch (`list[str]` → `list[dict]`).

**Still suspect:**
- `self._rag_service` is imported lazily; failure silently falls through to `_get_relevant_faqs()` (static list). Unclear whether the RAG service is actually reachable in production or if every FAQ is being served from the static fallback. Add a startup health check or emit a `rag.fallback_hit` counter.
- `self._rag_collection` is pulled from somewhere but not declared in the fix diff — verify it's configured per-tenant, not globally. If every tenant hits the same collection, we've got cross-tenant retrieval.

### Agent 2 — `sdk/python/agent_sdk/worker.py`

**Fixed:** hardcoded `status: completed` wrapping tool failures.

**Still suspect:**
- `process_generate_3d` hardcodes `collection="SIGNATURE"` and `garment_type="tee"` regardless of what the user requested (lines 142, 146, 155, 160). Every 3D generation task is forced into the Signature collection with a tee — the actual `prompt`/`style` is buried in `additional_details`. That's a config pipeline break: task_data should carry the real collection/garment_type but doesn't.
- Same function hardcodes `task_data.get("prompt", "")` as `product_name` — conflating two different inputs.
- There's no Intent enum at the worker boundary; `task_type` is a raw string matched with `==`. Typos in producers become "Unknown task type" failures silently.

### Agent 3 — `skyyrose/elite_studio/prompts/enhancer.py`

**Fixed:** cache cross-contamination via context digest.

**Still suspect:**
- `fashion_context` and `brand_context` are typed as `dict | None` everywhere but there's no schema — any shape goes. When we hash them for the partition key, the hash is only as stable as `json.dumps(..., sort_keys=True)` — if anyone passes a non-JSON-serializable value (datetime, path), we fall to `repr()` which is fragile. Define a `FashionContext` / `BrandContext` Pydantic model and validate at the enhancer boundary.
- The context is passed as positional arg all the way down. If a caller forgets it, they get the no-context partition, which is technically correct but hides the bug.

### Agent 4 — `skyyrose/elite_studio/queue/producer.py`

**Fixed:** `asyncio.run()` in async context, added `aenqueue_*` variants.

**Still suspect:**
- The sync `enqueue_*` functions still exist for CLI callers. Inside an async API handler, they now route through `_SYNC_BRIDGE_POOL` — which works but burns a thread per call. Every remaining sync call site inside an async handler is a latent perf issue. Audit: who still calls `enqueue_produce` from an async context?
- `_get_queue()` creates a fresh `TaskQueue` per call and disconnects at end of `_async_enqueue`. Redis connection setup/teardown per request is wasteful. Worth pooling.
- `REDIS_URL` defaults to `redis://localhost:6379/0` — in production without the env var set, the worker silently tries localhost and fails. Should refuse to boot without REDIS_URL in prod mode.

### Agent 5 — `skyyrose/elite_studio/graph/runner.py`

**Fixed:** batch abort on single SKU failure.

**Still suspect:**
- Failed SKUs emit a `ProductionResult` but no retry logic. The DLQ exists in `sdk/python/agent_sdk/worker.py` but isn't wired into the graph batch runner. Decide: should graph batch failures push to DLQ, or is "failed result in list" enough?

### Agent 6 — Tenant / auth config surface

**Fixed:** JWT verification + header-trust gate.

**Still suspect:**
- The JWT decoder in `core/middleware/tenant.py` is a separate code path from `security/jwt_oauth2_auth.py::JWTManager`. They should share. Currently tenant middleware only honors HS256/HS512 while JWTManager supports HS512 by default — if anyone changes the algorithm in one place, the other will silently reject all tokens.
- `TENANT_HEADER_TRUST_TOKEN` and `JWT_SECRET_KEY` are two independent secrets. No secret manager abstraction — both are raw env vars. If you're already using Vault / AWS Secrets Manager / 1Password for one, route both through it.
- No rate limiting on failed JWT verifies — an attacker can spray bad tokens to probe for secret format. Add a limiter or rely on the existing request-rate middleware.

---

## Required follow-up work (tracked, not blocking this PR)

From the simplify-pass review, these were deferred:

1. Centralize JWT verification through `security.JWTManager` (avoid two code paths diverging)
2. Consolidate sync/async `enqueue_*` variants so there's one canonical implementation
3. Move `record()` inside the `EntitlementChecker.check()` flow to close the quota increment race
4. Extract a shared `verify_shared_secret(header, env_var)` helper — pattern exists in 6+ places
5. Define `Intent` / `TaskType` enums at the worker + billing boundary instead of raw strings
6. Fashion/brand context Pydantic schemas
7. Audit remaining `enqueue_*` sync call sites in async handlers

---

## Deploy checklist

- [ ] Confirm `JWT_SECRET_KEY` is set in every environment (API, workers, agents, Docker compose, Vercel, HF Spaces)
- [ ] Decide whether `TENANT_HEADER_TRUST_TOKEN` is needed. If yes, set it. If no, leave unset (safer).
- [ ] Issue fresh JWTs with `exp` claim before deploy (old tokens without exp will be rejected)
- [ ] Verify any internal services that send `X-Tenant-ID` also send `X-Internal-Service-Token`
- [ ] Verify no `/api/v*/elite-studio/*` path exists that should bypass billing (or add explicit allowlist)
- [ ] Watch logs for `billing.record_failed` after deploy — indicates Redis blips dropping quota increments
- [ ] Run `pytest tests/test_saas_infrastructure.py` and confirm the new tenant contract tests pass
- [ ] Test analytics ingestion: trigger a product_view and confirm the row appears in `wp_skyyrose_analytics`
- [ ] Open a WP admin dashboard page and confirm no JS parse error in DevTools console
- [ ] Test quick-view modal on Safari 14 or a dialog-unsupported browser (if possible) to confirm fallback works

---

## Cross-reference

- Parent PR: #453 — "feat: Elite Studio Creative Operations Platform — Phases 0-6" (merged 2026-04-19)
- Triage report: `tasks/pr-453-action-report.md`
- Cubic review passes: 2026-04-16 + 2026-04-17 19:45Z + 2026-04-17 19:55Z
- Codex pass: 2026-04-14 (subsequently skipped due to PR size)
- CodeRabbit: skipped (298 files > 150 limit)
