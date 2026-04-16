# Current Tasks

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
- [ ] Create `frontend/app/api/settings/route.ts` — GET/PUT settings via FastAPI or local file
- [ ] Wire `frontend/app/admin/settings/page.tsx` — replace localStorage with API calls
- [ ] Remove `// TODO: Also save to backend API` comment

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
- [ ] Wire `frontend/app/admin/monitoring/page.tsx` to FastAPI health endpoints
- [ ] Replace `setTimeout + random data` in refreshMetrics with actual API calls
- [ ] Add real service health checks (WordPress, Vercel, FastAPI, DB)

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
