# Consolidated Cleanup Targets — Across All 8 Digests

_Synthesized 2026-05-06 from 235KB of digest output. Each finding cites which digest surfaced it. Severities applied by cross-cutting impact, not raw line count._

---

## Status snapshot — updated 2026-05-06 04:00 PDT

**Wave 1 (P0 hotfix)** — 4 items in commit `2b6e7ee5c` on `fix/p0-critical-cleanup-2026-05-06` (PR #489, blocked on org GitHub Actions billing lock):
- ✅ #1 GDPR Article 17 bypass → `api/gdpr.py` (hmac.compare_digest)
- ✅ #3 audit_log read→DATA_CREATED enum bug → `security/audit_log.py`
- ✅ #5 CostTracker hard-cap kill-switch → `skyyrose/elite_studio/queue/cost_tracker.py`
- ✅ Frontend dual auth-token keys → `frontend/contexts/AuthContext.tsx` (P1 #13)

**Wave 2 (parallel agent dispatch, 4 agents)** — 7 closed branches pushed to origin:
| # | Item | Branch | Commits |
|---|------|--------|---------|
| ✅ #2 | 12 unauth endpoints | `fix/p0-wave2-auth-rollout` | 1 + tests |
| ✅ #4 | SSRF replicate provider | `fix/p0-wave2-ssrf-allowlist` | 1 + 16 tests |
| 📝 #6 | Round Table auto-publish | (memo only) | `decisions/06-roundtable-publish-status.md` |
| ✅ #14 | UserRole defined twice | `fix/p1-wave2-enum-and-import-bugs` | (3 commits, +228/-69) |
| ✅ #15 | AlertSeverity mismatch | `fix/p1-wave2-enum-and-import-bugs` | extracted to `services/analytics/severity.py` |
| ✅ #16 | GeminiModel.GEMINI_PRO bug | `fix/p1-wave2-enum-and-import-bugs` | + regression test |
| ✅ #17 | base_legacy re-export | `fix/p1-wave2-enum-and-import-bugs` | |
| ✅ #18 | Sync I/O in async (3 places) | `fix/p1-wave2-async-blocking-io` | asyncio.to_thread |
| ➡️ #24 | Three.js dormant 3D | `fix/p2-threejs-feature-flag-2026-05-06` | feature-flagged off; full DEFER vs REMOVE pending |
| ⏭️ #27 | .venv committed virtualenv | (false positive) | already gitignored — verified |
| 📝 #28 | Scene WebPs missing | (user-decision) | needs Elite Studio imagery pipeline run |
| ✅ #29 | Version drift CLAUDE.md | `fix/p3-wave2-stale-code-cleanup` | + new CI gate |
| ✅ #30 | front-page.php footer mirror | `fix/p3-wave2-stale-code-cleanup` | |
| ✅ #31 | smoke-test.sh skyyrose.com typo | `fix/p3-wave2-stale-code-cleanup` | |

**Net Wave 2 closure:** 9 fully-closed items + 2 user-decision memos + 1 interim fix + 1 false positive = 13 of 28 P0–P3 items addressed (46%).

**Remaining (Wave 3 candidate):** 13 items
- **P1 silent-success stubs (HIGH PRIORITY):** #7, #8, #9, #10, #11, #12 — Agent B stalled at 600s before reaching them
- **P2 architectural debt (research-heavy):** #19, #20, #21, #22, #23, #25, #26 — Agent C produced no output; needs re-dispatch with output-first ordering

**User-decision items pending:**
- #6 Round Table publish status — `decisions/06-roundtable-publish-status.md` recommends `'draft'` or env-gated, awaiting confirmation it wasn't intentional for content workflow
- #28 Scene WebPs (6 files) — need imagery pipeline run, not a code fix
- #24 Three.js — DEFER (interim applied) vs REMOVE entirely

**Agent quota notes:** Agent B stalled (watchdog kill at 600s, 4 commits landed before stall). Agent C produced zero output despite 80K tokens / 100 tool uses (final message "Writing all memos now" got cut off — likely token cap). Both need scoped re-dispatch with smaller chunks and output-first ordering.

---

## P0 — Compliance / Security / Customer Cost

These are not "cleanup" in the maintenance sense; they're production-grade vulnerabilities that should be triaged separately and fixed before any large-scale refactor pass.

### 1. GDPR Article 17 delete bypass string  `[api.md]`

**File:** `api/v1/...` (GDPR delete endpoint)
**Issue:** Endpoint accepts hardcoded confirmation string `"CONFIRM_DELETE"` in lieu of the cryptographic sha256 confirmation code the API contract implies. Any authenticated user who knows the string can trigger user-data deletion.
**Severity:** Compliance violation (GDPR, also CCPA implications).
**Action:** Replace the string-equality check with an HMAC-validated confirmation flow that requires a server-issued nonce.

### 2. 12 unauthenticated endpoints with cost or data exposure  `[api.md]`

**Most dangerous:**
- `POST /virtual_tryon/fashn` — no auth, $0.075/image, hits FASHN paid API
- `POST /v1/catalog/answer` — no auth, makes Claude LLM calls
- `/ws/{channel}` WebSockets — real-time pipeline data, no auth
**Action:** Apply auth dependency to every paid endpoint. Catalog answer endpoint's docstring already acknowledges the risk; act on it.

### 3. `audit_log.py:log_data_access()` maps "read" to `DATA_CREATED`  `[core-orchestration.md]`

**Issue:** Copy-paste bug. Audit chain hash still validates (cryptographically intact), but every read access is misclassified as a create event in audit reports. For SOC2/HIPAA/etc. compliance audits, this looks like the system creates data on every page view.
**Action:** One-line fix in `audit_log.py`. Add a regression test on enum→event mapping.

### 4. No SSRF protection at services layer  `[services-llm-ai3d.md]`

**Issue:** Replicate/HuggingFace provider responses contain URLs that get fetched downstream without allowlist validation. SSRF surface for any compromised provider response.
**Action:** Add URL allowlist check to provider response handlers. Block 169.254.x.x, file://, gopher://, internal hostnames per project policy.

### 5. `CostTracker` has no hard cap — unbounded FLUX cost on retry loops  `[skyyrose-python.md]`

**Issue:** Tier alerts log at $5/$10/$20/$50, but no automatic stop. A stuck retry loop incurs unbounded FLUX API cost.
**Action:** Add a hard kill-switch (e.g., `OVERRIDE_COST_CAP=true` to disable, default $100 ceiling). Wire to all paid API call sites.

### 6. Round Table auto-publishes to live WordPress as `status: 'publish'`  `[frontend.md]`

**File:** `lib/wordpress/sync-service.ts`
**Issue:** Every automated Round Table competition creates a public WordPress post with no review gate. Could surface to customers immediately.
**Action:** Verify intent. If unintended, change default to `'draft'` and add an explicit publish step.

---

## P1 — Production Stubs Returning Success ("silent stubs")

This is a recurrent pattern across 6+ modules: function logs success but doesn't perform the work. Downstream code treats output as transformed, but it's the input unchanged. Hard-to-debug class of failures.

### 7. `TryOnAgent`, `VariantAgent`, `ColorCorrectionAgent`  `[skyyrose-python.md]`

**Behavior:** Log to ADK, return input unchanged.
**Downstream impact:** Anything treating their output as transformed imagery is silently wrong.
**Action:** Implement, OR remove + return typed `NotImplementedError`. Pretend-success is the failure mode.

### 8. `_enhance_quality()` in 3D Round Table  `[core-orchestration.md]`

**File:** `orchestration/threed_round_table.py`
**Behavior:** Sets metadata flags only. No actual mesh/texture processing.
**Compounded impact:** Tournament still adds `+5 enhancement_bonus` to every successful provider's score, making rankings slightly optimistic.
**Action:** Either implement enhancement, or remove the bonus from scoring.

### 9. `SelfLearningModule.flush_rag_queue()`  `[agents.md]`

**Behavior:** High-scoring responses (≥0.8) are added to an in-memory dict. Never reach a vector store. Lost on restart.
**Action:** Wire to Pinecone (project memory: `skyyrose-catalog` index, us-west-2, 1024-dim). OR remove the queue and document the absence.

### 10. `MLCapabilitiesModule` auto-trains on synthetic random data  `[agents.md]`

**Behavior:** All three model wrappers (sklearn / Prophet / transformers) auto-fit with synthetic random data when no real training set is present. Returns predictions with confidence=0.6 silently. No warning, log, or error.
**Action:** Raise `RuntimeError` when training data is absent. Confidence values from synthetic-trained models must NEVER reach the production scoring path.

### 11. `_queue_for_processing` in `image_ingestion.py`  `[services-llm-ai3d.md]`

**Behavior:** Method exists, looks like queue submission, never actually submits.
**Action:** Wire to actual queue. OR delete the function and inline its callers' fallback path.

### 12. `background_removal.py` `SOLID_COLOR` / `CUSTOM_IMAGE` paths  `[services-llm-ai3d.md]`

**Behavior:** Dead stub paths. Code structure suggests they composite, but they don't.
**Action:** Implement OR remove the enum variants entirely.

---

## P1 — Real Bugs (not stubs, but currently broken)

### 13. Dual localStorage auth keys cause silent 401s  `[frontend.md]`

- `AuthContext.tsx` writes `'auth_token'`
- `lib/api/client.ts` reads `'access_token'`
- `app/login/page.tsx` writes `'access_token'`
**Result:** Components that authenticate via context but call the API through the modular client send empty Bearer tokens. Every protected endpoint returns 401 with no obvious cause.
**Action:** Pick one key; replace all references. `grep -rn "auth_token\|access_token" frontend/lib frontend/contexts` shows the touch surface.

### 14. `UserRole` defined twice  `[core-orchestration.md]`

- `core/auth/types.py`
- `security/jwt_oauth2_auth.py`
**Risk:** JWT runtime uses security copy; RBAC logic uses core copy. Adding a role to one but not the other ships tokens with unresolvable role names.
**Action:** Promote one as canonical, re-export from the other. Add a unit test that asserts equality of the two enums.

### 15. Mismatched `AlertSeverity` enums  `[services-llm-ai3d.md]`

**Files:** `alert_engine.py` and `alert_notifier.py` define different enum values.
**Risk:** Any test that routes a HIGH or CRITICAL alert through both modules raises `KeyError`.
**Action:** One canonical enum. Same as #14 — extract to a shared module.

### 16. `GeminiModel.GEMINI_PRO` bug in `image_description_pipeline.py`  `[services-llm-ai3d.md]`

**Issue:** Reference to non-existent enum value. Would crash at first integration call.
**Action:** Use the correct enum (likely `GEMINI_3_PRO_PREVIEW` per memory). Add an integration smoke test.

### 17. `agents.core.base.SuperAgent` re-exports deprecated `base_legacy`  `[agents.md]`

**Issue:** `from agents.core.base import SuperAgent` silently resolves to deprecated `base_legacy.SuperAgent`. Every FASHN/Tripo import relies on this aliasing without knowing it.
**Action:** Either remove the re-export and force callers to update, or formally deprecate with `DeprecationWarning`.

### 18. Sync I/O inside async methods (3 places)  `[services-llm-ai3d.md]`

- `huggingface_provider.py` — sync Gradio calls
- `email_notifications.py` — sync `smtplib`
- `monitoring/stream_processor.py` — sync `consumer.poll()` (mitigated by `await asyncio.sleep(0)`)
**Result:** Event loop blocks for the duration of the sync call. Other async tasks stall.
**Action:** Wrap in `run_in_executor` or use async libraries (`aiosmtplib`, `aiogradio` if exists, `aiokafka`).

---

## P2 — Architectural Debt / Duplicates

### 19. Duplicate `/preorder/` redirect on production  `[wp-theme.md]`

**Both active:**
- `inc/accessibility-fix.php` — legacy, registered on `init` action
- `inc/redirects.php` — canonical v6.7.0, registered on `template_redirect` priority 1
**Not a runtime bug** (canonical fires first), but maintenance hazard. The redirect I added in this session's PR #483 wasn't actually adding new behavior — it was duplicating existing.
**Action:** Remove the legacy block from `inc/accessibility-fix.php`. Consolidate to `inc/redirects.php`.

### 20. `lib/api.ts` (root) vs `lib/api/` (directory) parallel implementations  `[frontend.md]`

**Issue:** Root monolith hasn't been deleted but is still importable. Components that import from the root file get legacy 3D URL behavior (external `API_URL` instead of relative Next.js routes). Pipeline URL split is "load-bearing" duplication.
**Action:** Pick the modular `lib/api/` as canonical. `grep -r "from '@/lib/api'"` to find all root-monolith importers, migrate, delete root file.

### 21. Five caches across the codebase with no consolidation plan  `[core-orchestration.md]`

- `core/multi_tier_cache.py`
- `core/redis_cache.py`
- `core/performance.py` (cache helpers)
- `orchestration/.../VectorSearchCache`
- `orchestration/.../RerankingCache`
Each has its own invalidation semantics. Cache-coherence bugs possible.
**Action:** Audit. Decide which two are required (likely L1 in-process + L2 Redis), retire the others.

### 22. 15+ in-memory stores process-scoped  `[api.md]`

Pipeline jobs, AR sessions, competitor data, team membership, admin stores — all unbounded Python dicts. On any pod restart or horizontal scale event, all in-progress job state vanishes. `TaskStore` (deque maxlen=1000) is the only one with a capacity bound.
**Action:** Migrate state to Redis (sorted sets + TTL) following the v2 router pattern from `api/v2/operations.py`. The infrastructure is already there.

### 23. Four parallel agent hierarchies  `[agents.md]`

- `CoreAgent` (SelfHealingMixin-based, newest, no learning module)
- `EnhancedSuperAgent` (ADK-backed, learning module, no healing)
- legacy `SuperAgent` (still active in FASHN/Tripo)
- `SDKSubAgent` (Claude Agent SDK tool-use)
ZERO agents have both healing AND learning. `CommerceCoreAgent` wraps `CommerceAgent` wraps the same domain — three layers of indirection.
**Action:** Decide on a canonical hierarchy. Migrate. Consolidate.

### 24. Three.js 3D experience system is dormant theme-wide  `[wp-theme.md]`

**Files:**
- `assets/js/experiences/experience-base.js` (492 lines)
- `assets/js/experiences/blackrose-experience.js` (757)
- `assets/js/experiences/lovehurts-experience.js` (696)
- `assets/js/experiences/signature-experience.js` (521)
- `assets/js/experiences/init-3d.js` (385)
**Status:** Loaded on every immersive page. Bind to nothing because no PHP template renders the activating containers (`#${collection}-experience` IDs). The immersive templates moved to a 2D engine per their own docblocks.
**Decision needed:**
  (a) Revive 3D on a specific page (feature decision, not cleanup)
  (b) Remove ALL the experience JS + the init-3d.js orchestrator + their enqueues — saves ~80KB on every page load
**Action:** User-call. The bug_001 fix landed today is for a code path that doesn't fire. Either path is safe.

### 25. Two parallel API versioning systems with mismatched auth  `[api.md]`

v1 uses JWT, v2 uses X-API-Key. Same caller can't reuse credentials between versions.
**Action:** Unify. Either migrate v2 endpoints to JWT, or expose X-API-Key→JWT exchange.

### 26. Hexagonal architecture violation in `core/`  `[core-orchestration.md]`

`core/runtime/input_validator.py` imports `SecurityValidator` from `security/`. Documented but unfixed.
**Action:** Either accept the hole and document loudly in `core/__init__.py`, or invert the dependency (define a `Validator` Protocol in `core/`, implement in `security/`).

---

## P3 — Stale Code / Cruft

### 27. ~~`agents/devskyy-a2a/.venv/` committed virtualenv~~ — **RESOLVED-FALSE-POSITIVE 2026-05-06**

**Verification:** `git ls-files | grep -c "\.venv/"` → **0**. The .venv is NOT tracked in git, despite the digest's claim of "7,941 vendored Python files committed". The 562 MB on disk is local development cruft only, properly excluded by `.gitignore` lines 33, 34, 285, and 385 (`.venv/`, `.venv-agents/`, `.venv-*/`, `**/.venv/`).

**Lesson for future digests:** verify "committed" claims with `git ls-files <path>` before recommending action. The digest agent saw the directory existed on disk and incorrectly assumed it was tracked.

### 28. Scene WebP background images missing from theme deploy  `[wp-theme.md]`

Prior session observation (claude-mem #1208, Apr 18). Scene WebP background images referenced in immersive templates were missing from deployed theme assets directory.
**Action:** Verify `assets/images/` includes all `scene-bg/*.webp` before next immersive-template deploy.

### 29. Version mismatch between code and CLAUDE.md  `[wp-theme.md]`

- `SKYYROSE_VERSION='1.1.0'` in `functions.php` and `style.css`
- CLAUDE.md says `1.0.0`
Code is authoritative, doc is stale.
**Action:** Bump CLAUDE.md to match. Add a check in deploy-theme.sh preflight that asserts they match.

### 30. `front-page.php` has its own footer, must mirror `footer.php`  `[wp-theme.md]`

Any template part added to `footer.php` (size-guide-modal, cookie-consent, mobile-nav, toast-container, skyy-mascot) must also be added to `front-page.php` before `wp_footer()`. Easy to forget — homepage features silently break.
**Action:** Either consolidate to `get_footer()` in `front-page.php`, or extract the must-include parts into a `footer-shared.php` partial included by both.

### 31. `smoke-test.sh` hardcodes `skyyrose.com`  `[scripts-and-entry.md]`

Stale. Live domain is `skyyrose.co`. Must override via `WORDPRESS_URL` env var or the test fails on the wrong domain.
**Action:** Change default to `skyyrose.co`.

### 32. `inc/accessibility-fix.php` legacy redirect block  `[wp-theme.md]`

(Same as #19 from a different angle.) The file's name suggests it's also a hold-over for legacy a11y fixes that have since moved into `accessibility-seo.php` and `system/animations-premium.css`. Audit what else lives there.

---

## Cumulative pattern: Stubs that score success

`_enhance_quality()`, `_queue_for_processing`, `flush_rag_queue()`, `MLCapabilitiesModule.fit()`, `TryOnAgent.process()`, `VariantAgent.process()`, `ColorCorrectionAgent.process()`, `background_removal SOLID_COLOR/CUSTOM_IMAGE` — at least 8 functions across 4 modules pretend success without doing work. Often paired with score-bonus contributions or downstream consumers that treat output as transformed.

**Cross-cutting recommendation:** A dedicated audit pass that greps for `pass\s*$|return self\.input|return data` inside method bodies, cross-referenced with whether the method has a non-trivial docstring claiming it transforms data. Should produce a categorized list. Likely surfaces more than the 8 listed.

---

## Stale-file CLAUDE.md proliferation

18+ auto-generated `CLAUDE.md` files scattered across subdirectories from `claude-mem` plugin observations. They're harmless but bloat the tree.
**Action:** `find . -name CLAUDE.md -not -path "./CLAUDE.md" | grep -v wordpress-theme` to see candidates. Decide whether to gitignore the auto-generated ones.

---

## What this list is for

- **Wave 2 (when quota resets at 01:30 PDT):** dispatch focused cleanup agents per category (P0/P1/P2/P3) that produce per-file remediation plans. Each agent reads only the relevant digest + affected files.
- **Wave 3 (after user review):** approved-only modification agents that apply remediations.
- **NEVER auto-apply** anything from this list. Each candidate has a "this might be load-bearing" path that needs human review.

_End of consolidated cleanup-targets file._
