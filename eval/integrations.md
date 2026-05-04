---
name: Integration Roundtrip Latency, Error Rate, Fallback Correctness
specified_by: [v2: §5 Phase 0, §3 integration architecture, §5 Phase 5]
phase: 0
test_command: node scripts/measurement/run-integration-eval.js --integration=<name>  # PHASE 0.5 DELIVERABLE — script does not exist yet; running it will exit 1 with a 'Phase 0.5 not started' message until the runner is built. See scripts/measurement/README.md.
pass_threshold: p95 latency per service met, error rate < 1%, fallback verified to activate on primary failure
last_updated: 2026-05-03
last_updated_by: eval-harness (Phase 0)
---

# Per-Integration Eval Rubric

For each external integration on the Skyyrose stack, this rubric scores roundtrip latency, error rate, and fallback correctness. Integrations are the highest-blast-radius surface — failures here look like the site being down, even when the theme is fine.

## Integrations covered

| Integration | Phase | Primary path | Fallback path | p95 latency target | Error budget |
|-------------|-------|--------------|---------------|---------------------|--------------|
| **Stripe checkout** | 5.10 | Stripe.js + WC blocks; 3DS challenge when triggered | Decline → user-visible message; refund flow on disputed | < 2s checkout init; < 5s authorization | < 1% non-customer-error failures |
| **FASHN AR try-on** | 5.6 | Vercel `/api/fashn-tryon` → FASHN API; 4-model output | Falls back to size guide on FASHN error, timeout, or cost-cap breach | < 8s avg roundtrip | < 1% (excluding cost-cap and validation rejections) |
| **Pinecone semantic search** | 5.7 | Vercel `/api/semantic-search` → Pinecone `skyyrose-products` index | Falls back to standard WP search if Pinecone unavailable | < 300ms p95 | < 1% |
| **WebXR session start** | 5.8 | `experience-base.js` → `renderer.xr.requestSession` | Falls back to standard 3D scene on unsupported devices or session error | < 2s on Vision Pro Safari, Quest 3 browser | < 1% (device support is feature-detected, not error) |
| **Drop queue** | 5.4 | Vercel `/api/drop-queue` → Pusher | Falls back to polling if Pusher down | < 500ms unlock-to-cart | < 1% |
| **Klaviyo flows** | 5.4, 6 | MCP `mcp__claude_ai_Klaviyo__*` for flow inspection; existing `inc/klaviyo-integration.php` for events | None (Klaviyo down → events queued client-side, sent on next page load) | N/A — async event emission | Event delivery > 99% |
| **WC REST API** | 0.5+ | Read-only via consumer key/secret in Vercel env | None (read-only; failures are diagnostic only) | < 1s p95 for read | < 1% |
| **WordPress.com MCP** | 1, 4 | `wpcom-mcp-content-authoring` for page reassignments + media | Falls back to raw WP REST API if MCP unavailable | < 2s p95 | < 1% |
| **Anthropic API** (build-time) | 0+ | Direct API call from Claude Code session | STOP-AND-SHOW per `eval/cost-cap-policy.md` if call >$1 | < 10s p95 thinking pass | Cost ceiling $25 build-cap |
| **Context7 MCP** (verify-impl Step 2) | 0.5+ | `mcp__claude_ai_Context7__query-docs` for canonical doc lookup | Falls back to web search via WebSearch tool if Context7 unavailable | < 5s p95 | < 1% |
| **GitHub MCP** | 7 | `mcp__github__*` for PR creation, branch ops | Falls back to gh CLI if MCP unavailable | < 3s p95 | < 1% |
| **Vercel MCP** | 0.5, 5, 7 | `mcp__claude_ai_Vercel__*` for deploy, env, log reads | Falls back to vercel CLI if MCP unavailable | < 3s p95 | < 1% |
| **Sentry MCP** | 6.5, 7 | `mcp__claude_ai_Sentry__*` for issue/replay reads | Falls back to Sentry web UI if MCP unavailable | < 2s p95 | < 1% |

## Test command

```bash
node scripts/measurement/run-integration-eval.js --integration=<name>
```

Exits 0 on PASS, 1 on FAIL with diagnostic output. Reads `eval/integrations-rows/<name>.md` for per-integration scores. The script can also be invoked with `--all` to run every integration sequentially.

## Per-integration row format

```yaml
---
integration: <name>
phase: <where it was wired>
primary_path_p95_latency_ms: <number>
fallback_path_verified: <bool>
fallback_trigger_on_failure: <description of what triggers fallback>
error_rate_30d: <decimal>  # Phase 6.5+ only; Phase 0-6 leaves blank
cost_30d_usd: <decimal>    # Per cost-cap-policy.md tracking
last_evaluated: <YYYY-MM-DD>
status: <PASS | FAIL>
---

<prose explaining latency profile, observed errors, fallback activations, cost trajectory>
```

## Phase entry checklist

Phase 5 sub-phases that wire an integration must populate the corresponding row before sub-phase exit. Phase 7 ship-check verifies every row is PASS before deploy.

## Notes on fallback verification

For each integration with a fallback, the eval includes a forced-failure test:

```bash
# Example: force FASHN failure to verify fallback
FASHN_FORCE_FAILURE=1 curl -X POST https://devskyy.app/api/fashn-tryon \
  -H "X-Test-Token: $TEST_TOKEN" \
  -d '{"product_id": 123, "user_image_id": "test"}'
# Should return: { "fallback": "size-guide", ... }
```

The forced-failure test is a Phase 5 sub-phase deliverable, not Phase 0 work. Phase 0 just defines the rubric.
