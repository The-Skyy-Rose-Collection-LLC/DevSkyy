# Wave 2 Agent A — P0 Leftover Security: Final Status

**Date:** 2026-05-06
**Branch (auth):** `fix/p0-wave2-auth-rollout`
**Branch (SSRF):** `fix/p0-wave2-ssrf-allowlist`

---

## Summary Table

| # | Finding | Branch | Status | Notes |
|---|---------|--------|--------|-------|
| 2 | 12 unauthenticated endpoints (cost/data exposure) | `fix/p0-wave2-auth-rollout` | DONE — pushed | REST endpoints gated with `Depends(get_current_user)`; WebSocket endpoints gated with `?token=<jwt>` query param; WooCommerce webhook deferred (HMAC-SHA256, not JWT); 401 regression tests in `tests/test_p0_auth_regression.py` |
| 4 | SSRF — `_download_model` fetches provider-returned URLs without validation | `fix/p0-wave2-ssrf-allowlist` | DONE — pushed | `_services_ssrf` module-level instance added to `services/three_d/replicate_provider.py`; SSRF check in `_download_model()` before HTTP I/O; blocked URLs raise `ThreeDProviderError(retryable=False)`; 16 unit tests in `tests/test_p0_ssrf_replicate.py` |
| 6 | Round Table auto-publishes WordPress posts as `'publish'` | — | INVESTIGATED — decision memo written | See `tasks/codebase-cleanup/decisions/06-roundtable-publish-status.md`; change is one line but requires owner confirmation on intent before fixing |

---

## Finding #2 Detail

**Files modified:**
- `api/websocket.py` — JWT validation via `jwt_manager.validate_token(token)` on all 6 WebSocket routes; query-param `?token=` added to each handler signature
- `api/v1/catalog.py` — `Depends(get_current_user)` on `/answer`, `/answer/stream`, `/cache/clear`
- `api/virtual_tryon.py` — `Depends(get_current_user)` on all 4 FASHN endpoints
- `api/ar_sessions.py` — `Depends(get_current_user)` on 3 write endpoints
- `api/v1/sync.py` — `Depends(get_current_user)` on `POST /trigger`, `POST /rt-to-hf`
- `api/v1/wordpress.py` — `Depends(get_current_user)` on both endpoints
- `api/v1/wordpress_agent.py` — `Depends(get_current_user)` on `/execute`; `/webhooks/dispatch` left unauthenticated with `# SECURITY-DEFERRED-WEBHOOK-HMAC` comment

**Tests added:** `tests/test_p0_auth_regression.py`

**Deferral — WooCommerce webhook:** `/webhooks/dispatch` is called by WooCommerce with HMAC-SHA256 signatures in the `X-WC-Webhook-Signature` header. Adding JWT auth would break WooCommerce delivery. Correct fix is to validate the HMAC signature against `WOOCOMMERCE_SECRET`. Tracked as `SECURITY-DEFERRED-WEBHOOK-HMAC` in the source comment.

---

## Finding #4 Detail

**Root cause:** `_download_model()` in `services/three_d/replicate_provider.py` called `http_client.get(url)` on a URL supplied by the Replicate API response without any validation. An attacker who controls the Replicate response (or a compromised Replicate account) could route requests to internal services including the AWS metadata endpoint at `169.254.169.254`.

**Fix:** `_services_ssrf` instance uses `SSRFProtection(allowed_domains=None, block_private_ips=True, block_localhost=True, block_metadata_services=True)`. The production global `ssrf_protection` was not reused because it has a narrow OpenAI/Anthropic/Google domain allowlist that would reject Replicate CDN URLs (e.g., `replicate.delivery`).

**Tests added:** `tests/test_p0_ssrf_replicate.py` — 16 tests covering blocked addresses, allowed CDN URLs, correct exception type, and `retryable=False` flag.

---

## Finding #6 Detail

See `tasks/codebase-cleanup/decisions/06-roundtable-publish-status.md` for full analysis.

**Short version:** `round-table-auto-trigger.ts:101` passes `status: 'publish'` to the WordPress sync service. All round table winners go live on `skyyrose.co` without human review. The in-code comment marks this as intentional. Recommended fix is `status: 'draft'` or an env-var gate, but owner must confirm intent before the line is changed.

---

## Branches Pushed

```
fix/p0-wave2-auth-rollout      → pushed (prior session)
fix/p0-wave2-ssrf-allowlist    → pushed 2026-05-06
```

No PRs opened per task constraint.
