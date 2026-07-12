# Current Tasks

## ACTIVE — Build the Signature Collection (all assets) — 2026-07-11

Founder: emblem + bespoke font + page pass. Sequence each; gate every money/deploy step. 3 scouts running.

> ⏸ Queued: bespoke BR Script + LH Graffiti fonts committed (`13c61beda`, v1.10.3) with clean-worktree
> deploy manifest shown — awaiting founder `y`. Sits atop the v1.10.2 deploy train (also gated, line below).

- [ ] **Track A — Signature font** (replace Pinyon Script): feasibility pending scout → build if autonomous,
      STOP-AND-SHOW if paid glyph gen. Wire like BR/LH (fonts.css/identity/sot/typography/design-tokens/.impeccable).
- [ ] **Track B — Signature emblem** (gold star-rose): source pending scout → compose from existing gold-rose+star
      (zero-paid) OR STOP-AND-SHOW paid render. Output `assets/images/emblems/signature-emblem.webp`; auto-wires via
      file-gated `.col-hero__emblem`. Eyes-on pixels before it touches the site.
- [ ] **Track C — Signature page pass**: autonomous copy/layout/imagery/experience per .impeccable.md; gate any new
      render (money) or WooCommerce/live-data write; verify all 12 SIG products resolve via SOT.
- [ ] Batch to ONE gated deploy (no drip); bundle with the queued font deploy if founder wants.

## ACTIVE — WS7 launch-night wiring + gap closure (2026-07-11)

Spec: `.planning/SKYYROSE_LAUNCH_NIGHT_SPEC_V2.html` (committed to main 2026-07-11).
This workstream previously had NO todo.md entry — tracked only in project memory. Register created
during the 2026-07-11 gap-closure sweep; full detail in memory `project_structural_remediation_2026_07_05`.

- [x] Sync: main==origin/main; launch spec + typography previews committed; feeds/ + tasks/assets/ gitignored
- [x] bug-222 /cart/ + /checkout/ shell restored (template_include override, commit 940665873, v1.10.2)
- [x] HG-5 skip links — verified ALREADY CLOSED (live audit 99/0, 2026-07-11)
- [x] WS5.4 root fix — session cookie now set at guest wishlist write time, not every pageview (f75c92cb4)
- [x] C5 /analytics/events shared-key gate — __return_true removed from write route (cdb76a951)
- [x] C6 wiring_audit.py FIRST RUN: 8/8 read-only PASS (after .env WP_APP_PASSWORD quoting fix +
      audit scope/pattern fixes). Write round-trips still gated (--write + STOPSHOW_ACK=1).
- [x] WS4.7 orphan categorization DONE 2026-07-11 (founder-approved): lh-005→love-hurts,
      sg-015→signature. Live verified: 33/33 in collections, uncategorized=0.
- [x] C4 webhooks REGISTERED 2026-07-11 (founder-approved): 5 topics active →
      https://www.devskyy.app/api/webhooks/woocommerce (product.create/update/delete, order.create/update).
- [x] Cookie-policy duplicate <h1> removed from page 10143 body (founder-approved) —
      live renders exactly one h1.
- [x] wiring_audit.py --write: **10/10 PASS** 2026-07-11 (after fixing the audit's settings
      round-trip to use whitelisted fastapi_url — endpoint whitelist was correct, probe was wrong).
- [ ] ⛔ GATED (founder y — NOT yet approved): theme deploy train v1.10.2 — 6 committed fixes
      (cart shell, session cookie, analytics key, policy titles, lockup CLS, PDP size-chip)
      inert on live until deployed.
- [ ] FOUNDER DECISION: dashboard font migration (spec C5: Fraunces/Archivo/JetBrains vs current
      Playfair/Cormorant/Space Mono in frontend/lib/fonts.ts) — spec cites nonexistent skyyrose-tokens.css;
      brand canon cut Playfair/Cormorant 2026-07-10. Needs a call, then execution.
- [ ] FOUNDER/OPS: `agents-manager` REST namespace live on production but in NO repo source — identify
      what serves it (plugin? leftover deploy?), bring under version control or retire.
- [ ] FOUNDER: HG-3 real pre-order ship window for /faq/; HG-1 TikTok/X handle confirm.
- [ ] Spec DoD amendment needed: "zero __return_true on write routes" now satisfied; consider
      documenting the shared-key analytics exemption model in the spec.
- [x] Go-live sweep reconcile: 9/11 theme fixes hold; 2 regressions (policy bare <title>,
      scene.php lockup CLS heights) re-fixed 2026-07-11
- [ ] WP-ADMIN (not code): site title "The Skyy Rose Collection"→"SkyyRose"; Jetpack SEO Tools
      duplicate meta-description toggle (now SITEWIDE, worse than register said); /kids-capsule/
      → /collections/kids-capsule/ redirect rule (live 404 today)
- [ ] ⛔ GATED (live content edit): cookie-policy page body carries its own <h1> duplicating the
      template's — remove via wp-admin editor
- [ ] IMAGERY (founder-gated, paid): KC hero brand-script lockup asset (Grand Hotel per canon) —
      scene.php still falls back to sr-monogram
- [ ] PERF BACKLOG: homepage stylesheet count grew 37→40
- [ ] SDK regressions (2026-04-15 consolidation kept the UNFIXED duplicate): 4 fixes being
      re-applied to sdk/python/agent_sdk — worker await-crash is production-critical
      (docker-compose runs agent_sdk.worker)

## DONE — Tier-3 stub-body wires → real agent delegation (2026-06-28)

Replace 4 hardcoded-fixture handler bodies with real agent delegation. TDD, tests green, scope-clean.
Wiring is autonomous-safe; runtime paid/prod gates stay intact (tests MUST mock paid/prod calls).
Register: `tasks/wiring-gaps-register.md` (T3-1..T3-4) — but 3 of its 4 specifics were wrong; wired from verified source.

- [x] **T3-1 code/scan** — DONE. Verified 5/5 via rtk; path-injection guard; `asyncio.to_thread`. — `api/v1/code.py:170-194` mock `ScanIssue` list → `CodeSecurityAnalyzer.analyze_directory()`
      (real source SAST, `security/code_analysis.py`; NOT the register's dependency-CVE scanner). Map
      `SecurityFinding{file_path,line_number,severity,category,recommendation}` → `ScanIssue`. Fix MCP route
      `mcp_tools/tools/infrastructure.py:163` `"scanner/scan"`→`"code/scan"`.
- [x] **T3-2 commerce/bulk** — DONE. Wire 3/3; bug-165 (CommerceAgent WC integration) FIXED full per founder: alias + `WordPressClient.from_env()` + lifecycle reconcile + dashboard.py 3 sites. 231 passed, no regression. — `api/v1/commerce.py:156-182,308-340` mock loops → `CommerceAgent` (init pattern proven
      at `commerce.py:467`). create→`sync_product_to_woocommerce`, update→`update_woocommerce_product(product_id,updates)`,
      delete→honest (no agent method; WC client or unsupported-result). Fix MCP endpoint_map `ecommerce.py:133-137`→`"commerce/products/bulk"`.
- [x] **T3-3 3D text/image-to-3D** — DONE. 4/4 via rtk; async BackgroundTask + status endpoint; +my fixes (SSRF follow_redirects=False, close() comment). — `api/v1/media.py:173-196,255-278` fake URLs → `TripoAssetAgent` (real class name;
      generators `_tool_generate_from_text`/`_tool_generate_from_image` → `GenerationResult`; PAID at runtime → MOCK in tests).
      Fix MCP routes `threed.py:149,203` → `media/3d/generate/text`, `media/3d/generate/image`.
- [x] **T3-4 theme deploy** — DONE. 3/3 via rtk (subprocess MOCKED, never ran real deploy); `create_subprocess_exec`+600s timeout; non-prod→`--dry-run`. — `api/v1/wordpress_theme.py:46-56` `success=False` stub → `subprocess.run(["bash","scripts/deploy-theme.sh",...])`
      (flag-driven: `--dry-run`/`--with-maintenance`, NOT env). non-prod env→`--dry-run`. PROD-touching at runtime → MOCK subprocess in tests, never run live.

### Verify (main thread, after agents — never on a subagent's word)
- [x] Re-run pytest for all 4 modules myself · `git diff --name-only` scope-clean · ruff/black/isort clean on touched files
- [x] Update buglog/anatomy/cerebrum/memory; mark register items done; report

## ACTIVE — Phase 2 `skyyrose/core/embeddings/` package (Track E) — 2026-06-24

Branch `feat/embeddings-phase2` off `origin/main`. Spec: `docs/superpowers/specs/2026-06-22-embeddings-reframe-design.md` §Track E.
Base: Phase 0 (frozen contract + golden gate) IS in main; Phase 1 (Track P) is NOT (open PR #604) — Track E is orthogonal.

**Approach (decided):** Shim migration — `skyyrose/core/clip_embedder.py` + `dino_embedder.py` become thin facades over the new
package → zero consumer churn (6 in-repo sites + `capability.py` importlib string-probe + 2 scripts unchanged). `store.py`
(sqlite LocalVectorStore) DEFERRED — no current consumer (YAGNI); E-store covered by atomic-centroid + space-guard on the
live `.npz` path. All tests model-free (CI red on HF Hub 429 — never download a model in a test).

Foundation: [x] errors.py [x] device.py [x] space.py [x] config.py [x] base.py
Encoders:   [x] clip.py [x] dino.py [x] cache.py
Wire:       [x] embedding_gate (E-encoder-gate) [x] brand_centroid (E-space/E-store) [x] shims
Migrate:    [x] repoint visual_product_recognition [x] delete scripts/image_embeddings (E-delete)
Verify:     [x] new unit suite green (50) [x] Phase-0 golden+contract still green (11) [x] elite_studio CI-mode green (185) + lint clean
            [~] adversarial 5-lens review running (wf_5bc8945c-3d3) → triage + fix → commit
DEFER:      store.py (sqlite LocalVectorStore) — no consumer, YAGNI; E-store covered by atomic centroid + dim guard.

## ACTIVE — MCP over HTTP, connected to dashboard + WordPress (2026-06-15)

Goal: expose the devskyy MCP (tool count computed at runtime — see mcp_service.py
/health) over authenticated HTTP so the Next.js
dashboard (AI console) and skyyrose.co (wp-admin buttons) can both consume it, AND
the tools can read/act on those surfaces' data. Branch `feat/mcp-http-surfaces`.
Architecture: mount the FastMCP `streamable_http_app()` into `main_enterprise` at
`/mcp` (→ `api.devskyy.app/mcp/`); reuse the backend both surfaces already call.

- [x] P0 Research — Context7 confirmed `app.mount("/mcp", mcp.streamable_http_app())` +
      `session_manager.run()` in lifespan + Bearer auth. SDK FastMCP already has the methods.
- [x] P1 HTTP mount — `api/mcp_mount.py` + lifespan wrap + mount in main_enterprise.
      Fixed double-path (`streamable_http_path="/"`). Verified: `/mcp/` → 200 + session.
- [x] P2 Auth — `BearerAuthMiddleware` (MCP_SERVICE_TOKEN). Verified 401 without/wrong token,
      200 with. Enforced when token set; warns if unset in non-dev.
- [x] P3a fly.toml pinned to 1 always-on machine (commit 624631520); MCP_SERVICE_TOKEN generated.
- [x] P3b Backend deploy — LIVE at https://devskyy-api.fly.dev/mcp/ (Fly app `devskyy-api`, 1 machine,
      MCP_SERVICE_TOKEN set). Pivoted from the torch monolith to a SLIM standalone MCP service
      (`mcp_service.py` + `Dockerfile.mcp`, no ML stack) — the full main_enterprise image is a
      ~6-10GB torch monolith with a broken Dockerfile + unsatisfiable [all] dep graph. Verified live:
      initialize→200+Mcp-Session-Id, tools/list→42 tools (stale point-in-time reading;
      live count is now served by /health's tool_count field), 401 w/o Bearer, foreign Host→421.
      Commit f08691b6b. Follow-up: `fly secrets set WC_CONSUMER_KEY/SECRET` to make WC tools callable.
- [x] P4 Dashboard AI console — `app/api/mcp` NextAuth-gated proxy (token server-side) + `app/admin/mcp`
      console UI; @modelcontextprotocol/sdk added (commit 8977cc5c1). type-check+lint+build green.
      Vercel deploy ⚠️ PENDING.
- [x] P5 WP-admin console — `inc/mcp-bridge.php` (PHP streamable-HTTP client: initialize →
      notifications/initialized → tools/call, SSE-frame parse, session DELETE teardown;
      SSRF-guarded via `skyyrose_see_is_safe_url`; Bearer from SKYYROSE_MCP_TOKEN const/env/option).
      Tools → DevSkyy MCP page + `assets/js/admin-mcp-console.js` (createElement only, no innerHTML),
      nonce + `manage_options` gated AJAX relay. Wired in functions.php after fastapi-client.php.
      WC catalog/orders read = ALREADY covered by `mcp_tools/tools/wc_client.py`
      (`wc_get_products`/`wc_get_product`/`wc_get_orders`) — no redundant resources built.
      php -l + PHPCS clean. Deploy skyyrose.co ⚠️ PENDING (gate on backend live first).
- [x] P6 docs — `docs/mcp-http-architecture.md` covers the mount, Bearer auth, both consumer
      surfaces (dashboard proxy + WP bridge), env var matrix, and failure modes (401/421).
      `scripts/verify-mcp-surfaces.sh` is a read-only E2E verifier (initialize -> tools/list,
      401-without-token) — CI-safe (SKIPPED + exit 0 when MCP_URL/MCP_SERVICE_TOKEN unset).
      Live E2E (both surfaces invoking a tool against production /mcp) is prepared — pending
      gated go-live, see `tasks/mcp-golive-manifest.md`.

  Remaining wiring (backend now LIVE at https://devskyy-api.fly.dev/mcp/) — exact gated
  commands + verify steps are in `tasks/mcp-golive-manifest.md`:
  - P4 Vercel env: MCP_URL + MCP_SERVICE_TOKEN (Production), redeploy frontend. ⚠️
  - P5 WP deploy: SKYYROSE_MCP_URL + SKYYROSE_MCP_TOKEN (option/wp-config const), then
    `bash scripts/deploy-theme.sh` if needed. ⚠️
  - DNS (optional, cleaner): point api.devskyy.app → Fly, then the committed default URLs
    work without per-surface overrides.
  - WC tools: `fly secrets set WC_CONSUMER_KEY/WC_CONSUMER_SECRET -a devskyy-api`.
  - Post every step: `bash scripts/verify-mcp-surfaces.sh` (MCP_URL/MCP_SERVICE_TOKEN exported)
    to confirm the surface is still healthy.

## ACTIVE — Consolidation Sweep (2026-06-10 standup plan)

Source: `~/.claude-mem/STANDUP.md` (10-agent standup; all decisions founder-approved 2026-06-10).
Context: org Actions block = ALL PR checks red regardless of code. Gate every merge on
LOCAL verification, not GitHub CI. Execute via `/do`. Sequenced by dependency.

### Phase 1 — Independent quick lands — DONE 2026-06-10
- [x] 1.1 Merge PR #537 — gate 20/20 tests green; merged `9169db1d`
- [x] 1.2 Merge PR #539 — php -l + ast + import gates clean; merged `dfe5254c`
- [x] 1.3 Land fix/ci-bandit-debt (consolidated assets + hook fix; PR #546)
      [this session: fad555a50 landed via PR #543; PR #546 = parallel session's follow-up, still OPEN]
- [x] 1.4 Close PR #501 — CLOSED with superseded comment

### Phase 2 — oai_render pipeline — DONE 2026-06-10 (with recovery)
- [x] 2.1 Pushed 409187921 → feat/oai-render-pipeline. CORRECTION: commit order was inverted —
      2b2ab382a was the TIP (child of 409187921), not parent; it was stranded by the push.
- [x] 2.2 PR #540 merged `948b59b25` (51/51 tests + dry-run smoke: 75 imgs/30 SKUs, 3 excluded).
      Stranded tip recovered via PR #544, merged `0f0ea0c43`, 52/52 tests. Both SHAs verified
      ancestors of origin/main. Lesson logged as buglog bug-124 (push tips, not assumed parents).
- [x] 2.3 render-fixes worktree + feat/legal-policies-shipping-sync branch deleted;
      be3a072c (.claude/-deletion hazard) now unreachable.

### Phase 3 — WP theme — DONE/DEFERRED 2026-06-10
- [x] 3.1 PR #534 CLOSED; partition B re-cut as PR #545, merged `6fb5350d4`.
      php -l clean; buglog merged additively (4 entries renumbered bug-120..123); webps carried.
- [x] 3.2 DEFERRED (founder call 2026-06-10): refactor/wp-template-consolidation is a stale
      reference snapshot (own commit message says "not mergeable code"); 9 main commits rewrote
      the 4 landing templates since branch point — merging would wipe brand/a11y/perf work.
      Branch kept as pattern reference. Redo on current main when templates stabilize.
- [x] 3.3 Not triggered: #545 = docblocks/artifacts only, no CSS/JS source changes this sweep.
      NOTE: #539's PDP size-chip JS (min rebuilt in-branch) is on main but NOT yet deployed
      to skyyrose.co — rides the next deploy train.

### Phase 4 — Holds + hygiene
- [ ] 4.1 HOLD wip/codex-homepage-v2 (51ee222a2). Trigger: OAI render batch re-run + validated
      (sections hard-reference deleted render image paths). Then cherry-pick onto theme branch.
- [ ] 4.2 HOLD PR #538 (pipeline3d draft). Trigger: founder picks 3D path (tasks/3d-pipeline-handoff.md).
- [x] 4.3 Main-checkout cleanup — DONE 2026-06-12 (landed on main via 525c6799a):
      frontend/.next.stale-20260609/ (252MB) DELETED (commit 76acaa98e);
      claude-mem CLAUDE.md churn ROOT-FIXED — redirected to gitignored CLAUDE.local.md
      (FOLDER_USE_LOCAL_MD=true) + worker restarted; 265 stub CLAUDE.md deleted, 77
      stripped, 0 blocks left tracked (commit 525c6799a); prototypes/ gitignored.
      Doctrine: docs/memory-architecture.html. clip bug-128 + theme v1.6.2 also landed.

**Done when:** main = #537 + #539 + #540(+2 commits) + #534-partition-B + wp-templates + fad555a50;
#501 + #534 closed; render-fixes worktree gone; every merge locally verified.

---

## ACTIVE — 3D products on skyyrose.co PDPs (2026-05-31)

**Decisions (founder):** Balanced KTX2+meshopt · Cloudflare R2 hosting · PDP-only · Google `<model-viewer>`.
**Verified:** 33 GLBs `renders/3d/{sku}.glb`, avg 7.5MB / ~74% textures. No viewer in theme (April mascot stripped). `.glb` not upload-allowed (only AVIF in `inc/performance.php`). PDP = `woocommerce/single-product.php`. No R2 creds / no compression tool yet.

### Phase 1 — Compress (local, no gate)
- [ ] Install `gltfpack` (meshoptimizer; bundles Basis/KTX2)
- [ ] Validate on br-003 (smallest): `-cc -tc`, confirm ~1–2MB + integrity
- [ ] Batch all 33 → `renders/3d/web/{sku}.glb`
- [ ] Report per-SKU before/after; flag non-shrinkers / degraded

### Phase 2 — Theme integration (local, deploy-gated by sweep)
- [ ] Self-host `model-viewer.min.js` → `assets/js/vendor/`
- [ ] `SKYYROSE_3D_CDN_BASE` constant (functions.php), empty = viewer off
- [ ] Enqueue model-viewer (`is_product()` only, ES module)
- [ ] Inject `<model-viewer>` in `woocommerce/single-product.php`: SKU→`{CDN_BASE}/{sku}.glb`, poster=product image, lazy, reveal=interaction, camera-controls, ar
- [ ] Graceful: no GLB for SKU → render nothing
- [ ] `assets/css/product-3d.css` + build `.min`
- [ ] Sweep: php -l + phpcs + WP health + /wp-simplify + animation verify

### Phase 3 — R2 hosting (BLOCKED on founder; STOP-AND-SHOW on upload)
- [ ] **NEEDS FOUNDER:** Cloudflare → R2 bucket `skyyrose-3d` → public (r2.dev or `cdn.skyyrose.co`) → API token
- [ ] Creds → `.env.secrets` (R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET, SKYYROSE_3D_CDN_BASE)
- [ ] CORS: allow `https://skyyrose.co` GET
- [ ] Upload script (boto3/rclone), dry-run first → **STOP-AND-SHOW** → real upload
- [ ] Set `SKYYROSE_3D_CDN_BASE` live → viewers activate

### Phase 4 — Verify live
- [ ] Cache-busted PDP curl: `<model-viewer>` present + GLB 200 + correct MIME
- [ ] WebGL renders desktop + mobile; poster pre-interaction
- [ ] Docs + lessons + memory updated

**Order:** Phase 1+2 now (no creds). Phase 3 waits on R2. Code ships complete; 3D activates when `SKYYROSE_3D_CDN_BASE` set.

---

## Session Summary (Apr 6, 2026)

### Completed This Session
- [x] Monorepo cleanup: .gitignore gaps fixed (.agents/, .mcp.json, .aidesigner/)
- [x] 21 Python files formatted (ruff/black/isort) + 7 lint errors fixed (StrEnum, unused vars)
- [x] PR Intelligence Agent built (pr-automator.md + /pr-auto command + pr-agent.yml workflow)
- [x] PR audit dry-run completed: 42 open PRs classified, 28 actionable, 14 need review
- [x] Experience Engine Phase 1: 4 PHP theme modules (experience-engine, experience-analyzer, fastapi-client, rest-api-experience) + functions.php wired
- [x] Experience Dashboard page: frontend/app/admin/experience/page.tsx — all 5 sections built
- [x] Full dashboard audit: 18 pages analyzed, 12 production-ready, 6 need work

---

## Experience Engine — Remaining Phases

### Phase 2: Performance + Atmosphere — COMPLETE (Apr 15, 2026)
- [x] `inc/performance-guardian.php` — CLS prevention CSS, animation budget config
- [x] `assets/js/performance-guardian.js` — Animation budget manager, FPS watchdog
- [x] `assets/js/brand-atmosphere.js` — Canvas particle system per collection
- [x] `assets/css/brand-atmosphere.css` — Canvas overlay, particle container
- [x] Update `inc/enqueue.php` — register Phase 2 assets (priority 30)

### Phase 3: WooCommerce Integration — COMPLETE (Apr 15, 2026)
- [x] `assets/js/experience-analyzer.js` — IntersectionObserver views, dwell timing, click tracking, sendBeacon flush
- [x] `assets/js/smart-showcase.js` — Native <dialog> quick-view, zero-AJAX (reads card DOM), focus trap
- [x] `assets/js/micro-interactions.js` — Cart fly-to arc animation, wishlist heart burst (8 particles)
- [x] `assets/css/smart-showcase.css` — Dialog + quick-view button + cart bounce keyframe + reduced-motion
- [x] Update `inc/woocommerce.php` — skyyrose_wc_inject_product_attrs() on woocommerce_before_shop_loop_item_title
- [x] Update `inc/enqueue.php` — skyyrose_enqueue_phase3_assets() at priority 40; holo card gets data-collection + data-name + quick-view button

### Phase 4: Personalization
- [ ] `inc/personalization.php` — Curated For You section, REST recommendations
- [ ] `assets/js/personalization.js` — Visitor profiling, affinity scoring
- [ ] `assets/css/personalization.css` — Curated For You grid
- [ ] Update `inc/enqueue.php` — register Phase 4 assets

### Phase 5: Admin Dashboard (WordPress side)
- [ ] `inc/admin-experience-dashboard.php` — Admin page: module status, analytics, narratives

---

## Dashboard (devskyy.app) — Gaps to Fill

### Priority 1: Settings Persistence
SHIPPED — `frontend/app/api/settings/route.ts` exists (GET/PUT, real handler);
`frontend/app/admin/settings/page.tsx` already wired per
`tasks/wiring-gaps-register.md` T2-4. This section is stale, kept for history.

### Priority 2: Tasks Page Expansion
- [ ] Expand `frontend/app/admin/tasks/page.tsx` (122L) — add task list, filtering, history, status tracking
- [ ] Add task creation form with type selector (content, image, deploy, general)
- [ ] Show Round Table competition results inline

### Priority 3: Agents Page — Dynamic Loading
- [ ] Remove hardcoded "54 agents" from `frontend/app/admin/agents/page.tsx`
- [ ] Load agent list dynamically from API or file system scan
- [ ] Add live status indicators (connected to actual agent health)
- [ ] Expand specialized agents list (currently "+42 more agents..." placeholder)

### Priority 4: Monitoring — Real API Wiring
Backend SHIPPED — `api/v1/monitoring.py:360` `/monitoring/metrics` route,
mounted `main_enterprise.py:286`. Remaining: frontend `metrics()` client
method + `useMonitoring` wire per `tasks/wiring-gaps-register.md` T3-9
(frontend-only).

### Priority 5: Autonomous — Live Data
- [ ] Wire `frontend/app/admin/autonomous/page.tsx` to selfHealingService real endpoints
- [ ] Add start/stop controls for autonomous operations
- [ ] Add execution history log

### Priority 6: Assets — API-Backed Gallery
- [ ] Wire `frontend/app/admin/assets/page.tsx` to HuggingFace datasets API or local asset scan
- [ ] Add search/filter functionality with real data
- [ ] Show product image count per SKU

---

## PR Management

### Open PRs Requiring Action
- [ ] PR #393: Experience Engine plugin — CLOSE with comment (pivoted to theme integration)
- [ ] PR #379: skill-prompt-generator — CLOSE (functionality exists as Claude Code skills)
- [ ] PR #433: cryptography 46.0.5→46.0.6 — MERGE PRIORITY (security patch)
- [ ] 26 Dependabot patch/minor PRs — BATCH into pip + npm combined PRs
- [ ] 8 Dependabot MAJOR PRs — review individually (vite 8.0, psutil 7.x, lucide-react 1.0)
- [ ] 4 GitHub Actions MAJOR PRs — review together (artifact v7/v8, docker v6/v7)

---

## Files Over 800-Line Limit (monitor, don't split)
> Splitting CSS adds HTTP requests. These work fine in production.
- `about.css` — 1,401 lines
- `homepage-v2.css` — 1,339 lines
- `contact.css` — 1,252 lines
- `immersive.css` — 1,216 lines
- `404.css` — 1,207 lines
- `single-product.css` — 1,133 lines
- `preorder-gateway.js` — 985 lines
- `product-catalog.php` — 918 lines
- `header.css` — 811 lines
- `frontend: conversion/page.tsx` — 1,822 lines (needs component extraction)
- `frontend: huggingface/page.tsx` — 1,218 lines (needs component extraction)

---

## Hero Images Needed (1-shot fix batch)
- [ ] Black Rose logo — dark chrome on dark bg, needs lighter version or glow
- [ ] Pre-Order hero — needs tri-split scene images
- [ ] About hero — needs Skyy Rose photo from user
- [ ] Kids Capsule hero — needs scene image + logo wordmark
- [ ] Love Hurts hero — user wants Beast with back turned (image not in repo)

## Post-Launch
- [ ] Run build.sh to generate missing .min.css/.min.js for new files
- [ ] Lighthouse audit: target Performance >90, Accessibility >90
- [ ] Mobile viewport test (375px)

# WP Port — Landing v3 + Pre-Order Flagship (2026-06-12)

Founder picks (2026-06-12): landing = prototypes/landing-collections/v3-split-scrollytell; pre-order = prototypes/preorder-page/flagship-full-throttle (video hero, conversion-led order).

- [ ] 1. Two parallel port builders (landing v3 → 3 landing templates + landing-scrollytell.css/js; pre-order flagship → template-preorder-gateway.php + preorder-gateway.css/js rewrite, hero-cinematic part with preorder-hero.mp4, WC cart wiring, meters OFF until real stock — edition chips only)
- [ ] 2. Verify: php -l, PHPCS, escaping/nonces, visual-manifest compliance, .min rebuild, grep source+min
- [ ] 3. Full sweep clean
- [ ] 4. STOP-AND-SHOW manifest → deploy (standing auth) → post-verify curl+Playwright mobile+desktop
- [ ] 5. Logs: memory/cerebrum/anatomy

Decisions: stub reserve counts NEVER ship live (canon) — factual "Edition of N" chips only until WC stock wired. Landing filenames unchanged (no SETUP_VERSION bump). landing-pages.css/js unenqueued for these templates, files kept for cleanup lane.

# Collection Identity SOT (2026-06-14)

Spec: `docs/superpowers/specs/2026-06-14-collection-identity-sot-design.md` (approved). Branch: `feat/collection-identity-sot`.
Per-collection folders `data/collections/<slug>/` = single source: `identity.json` (canon) + `copy.md` + generated `sot.json` + `index.html`. Canon-driven design-tokens rebuild + OFL fonts (Yellowtail/Kaushan/Pinyon, specimen-confirm). Hard cut-over: repoint all refs → delete all old.

- [x] P0 Canon scaffold — schema + 4 identity.json + load_identity() (7e4ad264c, df25936f4, 232225497)
- [x] P1 Fonts — Yellowtail/Kaushan/Pinyon self-hosted woff2 + @font-face (f3b1a4ad0)
- [x] P2 design-tokens rebuild — generated [data-collection] blocks; palettes fixed, accent-rgb preserved, 2-role fonts, font-gothic dropped, LH secondary fixed (5cfe4fc92, 8e90f601d)
- [x] P3/SOT builder — sot_common.py loader + ext-pref resolver + responsive-aware builder → per-folder sot.json + global _orphans.json (3026518dc, 421984f7d, b528b0536, e32f008eb)
- [x] P4 Designer bundle — 4 copy.md (verbatim canon) + generated index.html hub (62bfd5ef1)
- [x] P5 Verify + tests — full drift gate + golden test; 20 unit tests green; verifier 33/33 SKUs, 0 broken refs (78678d44f). [catalog-drift-guard hook re-point deferred to P6]
- [x] P6 census — DONE (non-destructive). FINDING: ZERO repoint work — no production PHP/JS/Python reads the flat JSONs or data/collections/. Cut-over = pure deletion w/ proof of zero consumers.
- [x] **P6 ⛔ GATE — FOUNDER WALKTHROUGH.** APPROVED 2026-06-14 ("Yes — run cut-over + P7").
- [x] P6 Cut-over — deleted flat JSONs + retired woff2 + old fonts.css block → rebuilt .min → re-pointed catalog-drift-guard hook (identity.json trigger) → updated README/docs (commit 56bb9a898).
- [x] P7 Verify + review gate — 20 unit tests green · drift gate 33/33 SKUs 0 broken refs · holistic review VERDICT ship · CSS-injection fix landed (font.family schema pattern, 02ca2b7fc) · 4 LOW/INFO follow-ups logged on PR #550.

Standing rules (§14): authoritative sources only (trace every value to a master); new SOT is the single reference post cut-over; repoint-first deletion (census proves zero live refs); no "done" without P7 proof.

## P6 DELETION CENSUS (running list — for the founder walkthrough; NOTHING deleted until sign-off)
- Flat `data/collections/{black-rose,love-hurts,signature,kids-capsule}.json` — superseded by per-folder `sot.json`.
- `assets/css/fonts.css` OLD `collections/` @font-face section: `Italiana` + `UnifrakturMaguntia` (NOT in canon — dead), and the superseded `Yellowtail`/`Pinyon Script` blocks pointing at `../fonts/collections/` (now duplicated by the canonical root-path blocks added in P1; root wins via cascade so site is correct, but the old blocks are dead weight).
- `assets/fonts/collections/{italiana,unifraktur-maguntia,yellowtail,pinyon-script}-latin.woff2` — old placeholder/duplicate font files (canon now uses root `assets/fonts/{yellowtail,kaushan-script,pinyon-script}-latin.woff2`).
- `COLLECTIONS` dict + per-collection regex in old `build-collection-sot.py` (replaced by identity.json in the P3 builder rewrite).
- Contaminated `[data-collection]` secondaries in `design-tokens.css` (replaced by P2 generation).
- NOTE: my earlier claim "no custom fonts self-hosted" was WRONG — they were in `assets/fonts/collections/`, just wrongly assigned. Verified 2026-06-14.

## P5 — Backend production home (run 20260707-4, started 2026-07-07)

- [x] WS1 ml-extra: move transformers/sentence-transformers/chromadb/diffusers from base deps → `ml` extra; import-site guards; resolve proofs
- [x] WS2 dockerfile-api: Dockerfile.api slim image ([api] on slimmed base); fail-loud DATABASE_URL in production (database/db.py:58)
- [x] WS3 fly-backend: fly.backend.toml (devskyy-backend); CORS wildcard fix; Sentry sample-rate wiring; tasks/backend-golive-manifest.md (gated)
- [x] Fable audit each branch (standing order), merge in order WS1→WS2→WS3
- [x] Post-merge: real `docker build -f Dockerfile.api` proof (main thread)
- [x] devskyy-backend deployed (Neon DB, /health+/ready 200); MPG destroyed; api.devskyy.app repointed to Fly (cert issued, public-resolver verified) 2026-07-09
- [x] P6 COMPLETE (2026-07-09): Blocks 1-3 wired+verified, MCP redeployed 82 tools/py3.12, api.devskyy.app repointed. Orig marker:: Block1 done (WC secrets on devskyy-api), Block2 done (Vercel env+deploy, live-verified); Block3 DONE via WP-CLI/SSH (bridge e2e proof: 44 tools); DNS deferred; MCP go-live (Fly WC secrets → Vercel env → WP config + theme deploy) per tasks/mcp-golive-manifest.md

## ACTIVE — Love Hurts Girl web build + world integration — 2026-07-12 (this session)

Branch: feat/love-hurts-girl-web (off origin/main) · Source: mascot-worktree renders/3d/girl-love-hurts/love-hurts-girl-v1.glb (25.5MB, 1 walk clip) · PR #736 = source assets

- [ ] A1 Context7: @gltf-transform/cli v4 draco+webp+resize flags · verify: docs quote
- [ ] A2 Compress → lh-girl.glb (prune, dedup, webp 2048, draco; NO meshopt) · verify: inspect shows walk anim + skin intact, ≤2.5MB
- [ ] B1 Read skyy-3d.js / enqueue.php regions / scene.php / mascot-config.php
- [ ] B2 theme assets/models/lh-girl.glb
- [ ] B3 assets/js/lh-girl-3d.js — walk-on cameo, enters LEFT (Skyy owns right), IntersectionObserver once, dispose after exit; reduced-motion/no-WebGL/no-container → no-op; DPR cap; hidden-tab pause
- [ ] B4 enqueue gated to /collections/love-hurts/ only; model URL ?ver=SKYYROSE_VERSION (mascot pattern)
- [ ] C1 fix stale skyyrose-flagship/CLAUDE.md SKYY_3D_CONFIG line
- [ ] C2 npm run build (.min) + SKYYROSE_VERSION bump · verify: .min contains new module
- [ ] D1 php -l + prod-mirror Playwright battery (canvas, glb fetch, no pageerrors, reduced-motion skip, mobile+desktop)
- [ ] D2 commit + PR
