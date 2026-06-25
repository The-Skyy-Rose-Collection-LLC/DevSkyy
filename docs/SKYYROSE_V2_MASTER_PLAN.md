# SKYYROSE V2 — MASTER EXECUTION PLAN

**Status:** Source of truth for Claude Code autonomous execution
**Owner:** Corey Foster, The Skyy Rose Collection LLC
**Target:** skyyrose.co — first-of-its-kind Editorial × WebGL × XR × Drop × AR fashion commerce theme
**Out of scope:** ThemeForest submission. Everything else is in scope.

---

## 0. Operating Contract for Autonomous Execution

### 0.1 Motto (governs every action)

> Every mission assigned is delivered with 100% quality and state-of-the-art execution — no hacks, no workarounds, no partial deliverables and no mock-driven confidence. Mocks/stubs may exist in unit tests for I/O boundaries; final validation must rely on real integration and end-to-end tests.

### 0.2 Definition of "autonomous" here

Claude Code drives the build end-to-end. It does **NOT** ask the user to confirm individual edits, file deletes, page reassignments, or design choices. It applies the rules in §1 (Locked Decisions) and the per-phase exit criteria in §5. It only stops and waits for the user at three explicit gates:

| Gate | When | What is asked |
|------|------|---------------|
| **G1: Eval approval** | End of Phase 0 | Confirm eval criteria are correct before any code is written |
| **G2: Pre-deploy review** | End of Phase 6 | Confirm `/ship-check wp` SHIP report; user signs off on deploy |
| **G3: Cost-cap exception** | Anytime cost > defined threshold (FASHN, AIDesigner, Anthropic) | Confirm budget burn before continuing |

Anything else — proceed. Apply the decision rules in §1.

### 0.3 Mandatory per-edit workflow (from repo `AGENTS.md` + Compound Learning Loop)

Before **every** file write, prepend:

```bash
# Step 0 — Pre-edit knowledge consult (Compound Learning Loop, Layer 1)
grep -r "<task-keywords>" knowledge-base/patterns/   # prior solutions
grep -r "<task-keywords>" knowledge-base/lessons/    # known traps
grep -r "<task-keywords>" knowledge-base/decisions/  # constraining ADRs
# Load matches into context. Begin work informed, not from scratch.
```

After **every** file write, in this order, no skipping:

```bash
npm run lint:php                # 1. PHPCS WordPress standard
node scripts/verify-impl.js     # 2. NEW — verified-implementation cross-check (Layer 2)
/simplify                       # 3. remove redundancy
post-simplify-verify            # 4. verify simplify didn't break intent
/verification-loop              # 5. live HTTP curl gate
node scripts/kb-distill.js      # 6. NEW — write KB entry (Layer 3)
```

**Step 2 — verify-impl — what it does:**

Cross-checks the just-written code against the trusted reference set (defined in WordPress plan §1.5.4). It does three things:

1. Web-searches for current best-practice on the specific pattern just implemented (query auto-derived from changed file path + exported symbols)
2. Compares the diff against the canonical source in the trusted set for that domain
3. Greps the diff against `knowledge-base/lessons/anti-patterns.md`

Output: `eval/verify-impl/<task-id>.md` with: source URL, accessed date, alignment statement (matches/surpasses/diverges with justification), and any anti-patterns flagged. No clean output = no advance to step 3.

**Step 4 — post-simplify-verify — what it does:**

`/simplify` removes what looks redundant. Sometimes what looks redundant is actually load-bearing (a guard clause, a deliberate fallback, a comment that anchored future work, an early-return that prevented an exception three branches down). Step 4 catches that before it ships.

The post-simplify-verify is mandatory and consists of four checks, in order:

1. **Diff inspection.** Run `git diff <file>` after `/simplify`. Read every removed line. For each removal, ask: *what was this protecting against?* If "nothing" → keep the removal. If "I'm not sure" → restore the line and re-simplify with that line marked do-not-touch.
2. **Re-lint.** Run `npm run lint:php` (or language equivalent) on the simplified version. If lint now fails, simplify introduced a bug — revert.
3. **Intent re-read.** Read the simplified file top to bottom against the original spec or the function/file docstring. Does it still do what it was written to do? Edge cases still handled? Errors still raised? If anything is now silently missing → revert that specific change, log to `eval/simplify-rejects.md`.
4. **Test rerun.** If unit tests exist for the file, run them. If integration tests exist for the surface, run them too. No green tests → revert.

Failure of any of the four checks → revert the simplify → log to `eval/simplify-rejects.md` with the over-prune diagnosed → retry simplify once with the restored line(s) marked do-not-touch. Two consecutive failures on the same file → escalate G3.

**Step 6 — kb-distill — what it does:**

After all checks pass, the loop must compound. `kb-distill.js` writes an entry to `knowledge-base/patterns/<domain>/<slug>.md` capturing: the problem, sources consulted (from step 2), chosen implementation, why-over-alternatives, when-to-use / when-NOT-to-use, loop-count-to-converge. If the loop took more than one iteration, a parallel `knowledge-base/lessons/<slug>.md` entry is written for the rejected v1 approach.

**Why this is non-optional:** Simplify regret is the silent killer of "premium" projects. Verified-implementation skipping is the silent killer of "current" projects. KB skipping is the silent killer of "compounding" projects. All three steps catch failure modes that don't announce themselves until production or until the next similar task starts from zero.

Failure of any step in the six-step workflow → revert the edit → log the failure to `knowledge-base/lessons/` → retry once with the fix. Two consecutive failures on the same edit → escalate (G3-class stop).

### 0.4 AGENTS.md scope is hard

| Directory | Allowed agents/skills | Forbidden |
|-----------|----------------------|-----------|
| `inc/` | wordpress-pro, php-pro, woocommerce-backend-dev, security-reviewer | Touching `assets/css/` or `frontend/` |
| `template-parts/` | wordpress-pro | Cross-directory edits without coordinating with `inc/` agent |
| `assets/js/` | design-taste-frontend, gpt-taste, overdrive | PHP edits |
| `assets/js/experiences/` | immersive-interactive-architect, overdrive | Anything outside Three.js scope |
| `assets/css/` | impeccable, high-end-visual-design, design-taste-frontend, polish | JS or PHP edits |
| `frontend/` (Vercel) | vercel:ai-architect, vercel:deployment-expert, design-taste-frontend | WP PHP edits |
| `eval/` | eval-harness | Any code agent without explicit phase assignment |

Every agent reads its `AGENTS.md` before its first edit in that directory. Cross-boundary work requires a sequenced handoff (agent A writes, exits, agent B reads, writes), never a simultaneous edit.

### 0.5 Definition of Done per phase

A phase is done when **all four** are true:

1. Every task in the phase task list is committed to git on a feature branch
2. Mandatory per-edit workflow passed for every commit
3. Phase exit criteria (machine-checkable) all return PASS
4. Phase eval rubric from `eval/` returns PASS

Then and only then does Claude Code move to the next phase.

---

## 1. Locked Decisions (no asking — apply these rules)

These resolve every "ask user per page" in the prior plans. Claude Code applies them directly.

### 1.1 Page-level decisions

| Page slug | Decision | Rule applied |
|-----------|----------|--------------|
| `faq` | Reassign to `template-faq.php` | Custom template exists; default is wrong |
| `faq-2` | Delete | Duplicate; check internal links first, build redirect map for any external |
| `shipping-returns` | Reassign to `template-shipping-returns.php` | Same logic |
| `shipping-returns-2` | Delete | Duplicate |
| `terms-of-service` | Reassign to new `template-info-page.php` (built Phase 3.3) | Default → custom |
| `privacy-policy` | Reassign to `template-info-page.php` | Same |
| `cart` | Build `skyyrose-canvas.php` AS universal builder canvas + fully style WC blocks | Both paths: canvas is the shell, WC blocks are content. Solves ghost reference AND #1 category problem |
| `checkout` | Same — WC blocks fully styled inside skyyrose-canvas shell, Stripe wired (Phase 5.10) | Same logic |
| `collections` | Reassign to `skyyrose-canvas.php` (rendered as collections index via canvas hooks) | Reuse canvas; no separate template needed |
| `experience` | Build `template-experiences.php` (Phase 4) | Immersive hub |
| `spatial` | Build `template-spatial-home.php` Phase 4 stub + Phase 5.8 full WebXR | NOT deferred |
| `style-quiz` | Build `template-style-quiz.php` (Phase 4) | One of the 7 marketplace gaps |
| Any other ghost | Build the corresponding template | Default action: build, don't delete pages |

### 1.2 Architectural decisions

| Question | Decision |
|----------|----------|
| WP.com long-running work | All on Vercel; WP only request/response |
| FASHN cost cap | $50/day global, $1.50/user/day, hard-stop at limit |
| Pinecone reindex cadence | Vercel cron nightly + on-product-save webhook |
| Avatar `assets/models/skyy.glb` | Run rig-check in Phase 5.0 prerequisites; if broken AND used in 5.6/5.8 → fail-fast escalation |
| Marketplace author URI in `style.css` | Keep as `https://skyyrose.co` (TF submission out of scope) |
| Drop queue WebSocket transport | Pusher (managed); fallback to polling if Pusher down |
| WebXR fallback | Always provide standard 3D path; never block desktop browsing |
| Eval failures during build | Hard stop the phase, fix, re-run; never advance with red eval |
| Rollback strategy | Every phase merges to `main` only after full pass; deploys are atomic hot-swap |

### 1.3 Cost-cap thresholds (G3 escalation triggers)

| Service | Threshold per build | Action |
|---------|---------------------|--------|
| Anthropic API (build-time) | $25 | Escalate before continuing |
| AIDesigner credits | 50 generations | Escalate before continuing |
| FASHN test calls | 30 | Escalate before continuing |
| Pinecone embedding API | $10 | Escalate before continuing |

> **NOTE — superseded in this build by `eval/cost-cap-policy.md`** (per Phase 0 grill Branch 1, Option C). Hybrid stance: any single call >$1 follows CLAUDE.md STOP-AND-SHOW; calls ≤$1 are autonomous up to the per-service threshold above. The thresholds above remain the autonomous-tier ceiling.

---

## 2. Thesis & Differentiators

**SkyyRose v2 = Editorial × WebGL × XR × Drop × AR.**

First WordPress fashion theme to ship native WebGL product canvas + WebXR spatial layer + scroll-narrative editorial product pages + cohesive drop system + integrated AR try-on + AI semantic search, all under one editorial design language with no seam between content and commerce. Five marketplace-first features in one cohesive theme — an entirely new category.

**The three thesis pillars** (these define "shocking, not impressive"):

1. **WebGL native** — formalize existing `experience-base.js` (492-line Three.js engine) as the theme's defining identity. Zero ThemeForest fashion themes ship native WebGL product canvases.
2. **Editorial scroll narratives** — unify editorial themes (Uncode, Salient) and shop themes. Every product page is a story that ends at the cart button.
3. **Drop mechanics** — pre-styled countdown → waitlist → unlock → live restock, extending existing `template-preorder-gateway.php` and `inc/woocommerce-preorder.php` infrastructure.

**Failure modes explicitly attacked:**

- WC block cart/checkout styling (#1 unsolved problem in category)
- Mobile-native (swipe galleries, tap-expand, native pinch-zoom — not just responsive)
- Performance under real load (5 plugins + 50-product cart + Klaviyo + reviews)

---

## 3. Integration Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  WORDPRESS.COM (skyyrose.co)                                     │
│  Theme PHP, WooCommerce, Klaviyo client, basic search, pages     │
│  Stateless. No background work. Only request/response.           │
└────────────────┬─────────────────────────────────────────────────┘
                 │ HTTPS + HMAC-signed shared secret
                 ▼
┌──────────────────────────────────────────────────────────────────┐
│  VERCEL (devskyy.app)                                            │
│  Next.js dashboard + API routes:                                 │
│  - /api/fashn-tryon          AR proxy → FASHN API                │
│  - /api/semantic-search      Pinecone query proxy                │
│  - /api/embed-products       Cron: index WC products nightly     │
│  - /api/drop-queue           WebSocket-backed live drop queue    │
│  - /api/claude-lab/*         Prompt-eval admin tool              │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────┐
│  EXTERNAL SERVICES                                               │
│  Pinecone (vector index)  │  FASHN (AR try-on)                   │
│  Stripe (payments)        │  Klaviyo (email — already wired)     │
│  Anthropic (Claude API)   │  HuggingFace Spaces (FLUX upscaler)  │
│  Pusher (drop queue WS)   │                                      │
└──────────────────────────────────────────────────────────────────┘
```

**Bridge:** `inc/fastapi-client.php` (already exists). Each integration extends this file with one function per Vercel route. Shared secret stored as a WP option, rotated quarterly.

**Why this architecture is non-negotiable:** WordPress.com Business plan has no shell, no cron, no DB write access for custom tables. Anything stateful or long-running cannot live there.

---

## 4. Skill & Agent Orchestration Map

### 4.1 SkyyRose-specific skills (project-local — load FIRST every phase)

| Skill | Phase entries | Surface | Contract |
|-------|---------------|---------|----------|
| `skyyrose-brand-dna` | EVERY phase | All design surfaces | Voice rules, banned phrases, palette, "say The Town not the Bay Area" |
| `skyyrose-launch-commander` | Phase 5.4 | Drop launch sprint | Orchestrates the 6 below on T-30 → T+7 timeline |
| `skyyrose-product-copy` | Phase 4 + 5.3 | Product detail pages | Per-collection voice, character limits, 10-point checklist |
| `skyyrose-content-engine` | Phase 5.4 + 6 | Marketing surfaces | 5 pillars, video scripts, captions, hashtags |
| `skyyrose-paid-media` | Phase 6.5 | Ad creative for launch | Meta/TikTok/Google structure, hooks, ROAS calc |
| `skyyrose-email-flows` | Phase 5.4 + 6 | Klaviyo flows | Welcome (5), Pre-order Drop (7), Abandoned Cart (3), Post-Purchase (4), Seasonal |
| `skyyrose-seo-commerce` | Phase 4 + 5 + 6 | Every product/collection | Keyword matrix, JSON-LD schemas, URL hierarchy |

### 4.2 Generic design lens skills

| Skill | When | Surface |
|-------|------|---------|
| `image-taste-frontend` | Design phase | Image-first reference before any AIDesigner call |
| `aidesigner` (MCP) | Design phase | Second visual reference; capture + adopt CLI |
| `ui-ux-pro-max` | Design phase | Lookup palette/font from 96-palette catalog (constrained by brand-dna) |
| `high-end-visual-design` | Build phase | Structural archetypes (Double-Bezel, Z-Axis, Editorial Luxury, Soft Structuralism) |
| `impeccable craft` | Build phase | Anti-slop production code (supersedes frontend-design) |
| `design-taste-frontend` | Build phase | RSC safety, Tailwind lock, viewport stability |
| `gpt-taste` | Motion phase | GSAP scroll narrative — ONLY immersive/preorder/about/experiences (theme rule) |
| `overdrive` | Motion phase | Three.js shaders + spring physics — ONLY immersive/spatial templates |
| `delight` | Polish phase | Micro-interactions, personality, empty states |
| `bolder` | Polish phase | Amplify if a design is too restrained |
| `polish` | Pre-ship | Pixel tightening, alignment, consistency |
| `redesign-existing-projects` | Phase 3 | Retrofit consolidation (preserve content, upgrade chrome) |

### 4.3 Validation skills

| Skill | When | What |
|-------|------|------|
| `eval-harness` | Phase 0 | Pass/fail criteria per surface; truth doc throughout |
| `simplify` | After EVERY edit | Mandated by `AGENTS.md` |
| `verification-loop` | After EVERY edit | Mandated by `AGENTS.md`; live HTTP curl checks |
| `audit` | Phase entry + pre-ship | P0–P3 scored report (a11y, perf, theming, anti-patterns) |
| `critique` | Phase entry + pre-ship | UX/emotional resonance, persona-based testing |
| `e2e-testing` | Phase 7 | Playwright: cart, checkout, drop unlock, AR try-on, semantic search |
| `ship-check wp` | Phase 7 final | Composes lint + verify + e2e + preflight; returns SHIP/FIX/HOLD |

### 4.4 Specialized agents (12)

| Agent | Phase | Surface |
|-------|-------|---------|
| `wordpress-pro` | 1–7 | All `inc/` PHP, WC hooks, schema output |
| `woocommerce-backend-dev` | 5.1, 5.10 | Cart/checkout PHP, payment gateway, pre-order extension |
| `php-pro` | 5.6, 5.7 | FASHN + Pinecone glue in `inc/fastapi-client.php` |
| `security-reviewer` | 5.1, 5.6, 5.10 | CSP for Stripe.js, FASHN CDN; payment security |
| `websocket-engineer` | 5.4 | Live drop queue, real-time inventory countdown |
| `immersive-interactive-architect` | 5.8 | WebXR session layer on existing Three.js engine |
| `rag-architect` | 5.7 | Pinecone integration: embedding pipeline, namespaces, query proxy |
| `playwright-expert` | 7 | E2E test suite (currently nonexistent in repo) |
| `vercel:ai-architect` | 5.9 | Claude Lab admin tool architecture |
| `Backend Architect` | 5.6, 5.7, 5.10 | Cross-system: FASHN + Pinecone + Stripe + Vercel-WP bridge |
| `Accessibility Auditor` | 6.3 | WCAG 2.2 sweep |
| `Tracking & Measurement Specialist` | 6.6 | GTM, GA4, conversion tracking, Meta CAPI |

### 4.5 Plugin / MCP skills (use directly)

| Plugin/MCP | Phase | Use |
|------------|-------|-----|
| `pinecone:quickstart` | 5.7 entry | Set up index for WC product embeddings |
| `mcp__plugin_pinecone__upsert-records` | 5.7 | Index products without writing PHP first |
| `mcp__plugin_pinecone__search-records` | 5.7 | Validate query results before WP integration |
| `mcp__claude_ai_Klaviyo__*` | 5.4 | Build/inspect Klaviyo flows; validate `skyyrose-email-flows` output |
| `vercel:vercel-sandbox` | 5.6, 5.7 | Test FASHN + Pinecone proxies before WP wires them |
| `mcp__stripe__authenticate` | 5.10 | Verify Stripe account before checkout wiring |
| `commit-commands:commit-push-pr` | After every milestone | Wraps lint/verify/commit/PR cleanly |

---

## 5. Execution Phases

### Phase 0 — Define evals (BEFORE writing any code) — **G1 GATE AT END**

**Outputs to `eval/`:**

- `eval/templates.md` — pass/fail rubric per template type
- `eval/integrations.md` — pass/fail rubric per integration (Stripe checkout, FASHN roundtrip, Pinecone latency, WebXR session start, drop queue, Claude Lab)
- `eval/marketplace.md` — readiness checklist (one-click demo install, WCAG 2.2, perf budget, demo coverage, docs)
- `eval/shocking.md` — observable "haven't seen this before" criteria
- `eval/brand.md` — `skyyrose-brand-dna` voice/visual rules in eval form
- `eval/page-flow.md` — IA / nav / menu user-journey rubric (built in Phase 1.5)

**Skills:** `eval-harness`, `skyyrose-brand-dna`.

**Exit criteria (machine-checkable):**

- All six eval files exist in `eval/`
- Each eval file has at minimum: scope, criteria table, pass threshold, test command
- `npm run lint:md` passes on all eval files

**G1 GATE — STOP HERE.** User reviews eval criteria. Phase 1 does not start until user replies "approved" or equivalent.

---

### Phase 0.5 — Pre-flight prerequisites (autonomous)

| Check | Command/method | Pass condition |
|-------|---------------|----------------|
| Stripe account | `mcp__stripe__authenticate` | Returns valid account |
| FASHN API key | Env var `FASHN_API_KEY` set in Vercel | Present, format-valid |
| Pinecone account | `pinecone:quickstart` provisioning | Index `skyyrose-products` exists or creatable |
| Anthropic API key | Env var `ANTHROPIC_API_KEY` set | Present |
| Avatar GLB rig | `node scripts/check-glb-rig.js assets/models/skyy.glb` | If used in 5.6/5.8: bones > 0, animations > 0 |
| WP REST API auth | `curl -u $WP_USER:$WP_APP_PASS https://skyyrose.co/wp-json/wp/v2/pages?per_page=1` | HTTP 200 |
| Vercel CLI auth | `vercel whoami` | Returns user |
| Pusher account | Env var `PUSHER_APP_ID` set | Present |

**Failure handling:** Any FAIL → output blocking issue list to `eval/blocking-prerequisites.md` → escalate as G3-class stop with fix instructions.

---

### Phase 1 — Admin cleanup (WP REST API only, no PHP)

Pure WordPress REST API. No PHP edits in this phase.

**Tasks (apply rules from §1.1, no per-page asking):**

1. Reassign `faq` page → `template-faq.php`
2. Reassign `shipping-returns` → `template-shipping-returns.php`
3. Reassign `terms-of-service` → `template-info-page.php` (template built in Phase 3.3 — defer reassignment until template exists)
4. Reassign `privacy-policy` → `template-info-page.php` (defer)
5. Build redirect map (`inc/redirects.php` array) for `faq-2` and `shipping-returns-2`
6. Delete duplicate `faq-2` (after redirect entry exists)
7. Delete duplicate `shipping-returns-2`
8. For each ghost (`cart`, `checkout`, `collections`, `experience`, `spatial`, `style-quiz`): apply rule from §1.1

**Exit criteria:**

```bash
# All affected pages return HTTP 200, ≥50KB, no PHP error markers
for slug in faq shipping-returns cart checkout collections experience spatial style-quiz; do
  curl -sS -o /tmp/$slug.html -w "%{http_code}" https://skyyrose.co/$slug/ | grep -q 200 || exit 1
  [ $(wc -c < /tmp/$slug.html) -ge 51200 ] || exit 1
  ! grep -q "Fatal error\|Parse error\|Warning:" /tmp/$slug.html || exit 1
done
```

---

### Phase 1.5 — Site IA / navigation / menu redesign

Currently 6 menu locations, default `wp_nav_menu()`, no walker, no mega menu, no breadcrumbs.

**Tasks:**

1. Build `inc/class-skyyrose-mega-menu-walker.php` — custom `Walker_Nav_Menu` for hover panels with collection imagery
2. Build `template-parts/header/mobile-drawer.php` — full-screen overlay with collection-color palette swap
3. Build `inc/breadcrumbs.php` — function reading `is_*()` conditionals → JSON-LD schema (use `skyyrose-seo-commerce` skill output)
4. Refresh `template-parts/footer/main.php` — three-column structure: Shop / About / Legal
5. Build `assets/js/sticky-header.js` — scroll-aware: fade in shadow at scroll > 100px, compact logo
6. Generate `eval/page-flow.md` — for every page document arrival, next, CTA

**Skills:** UX Architect agent + `gpt-taste` (header motion only, NOT mega menu) + `design-taste-frontend` + `wordpress-pro`.

**Exit criteria:**

- All 6 files committed
- `critique` persona walkthrough: first-time customer reaches a drop within 2 clicks (PASS)
- Mobile drawer keyboard-navigable (Tab cycle complete, Esc closes)
- Breadcrumb JSON-LD validates against schema.org BreadcrumbList

---

### Phase 2 — Audit & dead code removal

**Tasks:**

1. Map every orphan asset:

   ```bash
   for f in assets/css/*.min.css assets/js/*.min.js; do
     base=$(basename "$f" .min.${f##*.})
     grep -rq "$base" inc/ template-parts/ *.php || echo "ORPHAN: $f"
   done > eval/orphan-assets.txt
   ```
2. Bulk delete confirmed orphans (36 CSS + 34 JS) in single commit per asset class
3. Identify and remove 7 unused `template-parts/` (audit confirms zero `get_template_part()` references)
4. Remove dormant Store API cart code (already retired in commit `87e420883`, confirm removal)
5. Leave min-only registrations in `inc/enqueue.php` for ghost templates being built in Phase 4

**Skills:** `simplify`, `audit`, `verification-loop`.

**Exit criteria:**

- `eval/orphan-assets.txt` shows 0 remaining orphans
- Live curl on home, all 4 collection pages, all 3 immersive pages: HTTP 200 + ≥50KB + no PHP errors
- `npm run lint:php` passes
- No 404s in browser console on home page (run `playwright test smoke/no-404s.spec.ts`)

---

### Phase 3 — Template consolidation

**3.1 Landing templates (highest leverage — 809L → ~120L)**

- Promote shared sections (press, story, parallax, editorial, reviews, craft, cta) → `template-parts/landing/page.php`
- Per-collection content → `inc/landing-data.php` (pattern: `inc/product-catalog.php`)
- Templates `template-landing-{black-rose,love-hurts,signature}.php` become 16-line stubs

**3.2 Immersive data extraction (487L → ~70L)**

- Per-collection room arrays → `inc/immersive-data.php`
- All 4 immersive templates become 16-line delegators

**3.3 FAQ + shipping-returns + new info-page partial**

- Common quiet-premium chrome → `template-parts/info-page.php`
- Build `template-info-page.php` (used for terms/privacy)
- Per-page content stays in templates (small enough to inline)

**Skills:** `redesign-existing-projects` + mandatory quality workflow.

**Exit criteria:**

- Pre/post visual diff on every consolidated page (curl + headless render via Playwright `page.screenshot()`) — pixel-match within 2% tolerance
- Eval criteria from `eval/templates.md` PASS for each consolidated template
- Total LoC reduction logged: landing 809→~120, immersive 487→~70

---

### Phase 4 — Build missing premium templates

For **each** new template, run the design-skill chain in this exact order:

1. **Brief** — load `skyyrose-brand-dna` constraint
2. **Eval target** — `eval-harness` opens row in `eval/templates.md` for this template
3. **Design ref A** — `image-taste-frontend` generates image-first reference
4. **Design ref B** — `aidesigner` MCP generates second reference; capture + adopt
5. **Lookup** — `ui-ux-pro-max` palette/font selection
6. **Structure** — `high-end-visual-design` archetype selection
7. **Build** — `impeccable craft` + `design-taste-frontend`
8. **Motion** — `gpt-taste` (only on permitted templates per `CLAUDE.md`)
9. **Polish** — `delight` + `bolder` if too restrained
10. **Validate** — `simplify` → `verification-loop`
11. **Score** — `audit` + `critique` against eval criteria

**Templates to build:**

| Template | Purpose | Motion allowed? |
|----------|---------|-----------------|
| `template-info-page.php` | Terms/privacy/legal | No (info-quiet) |
| `template-experiences.php` | Immersive hub | Yes (`gpt-taste`) |
| `template-style-quiz.php` | Quiz → curated products | `delight` only |
| `skyyrose-canvas.php` | Universal builder shell (Elementor/Divi/Bricks-friendly) | No |
| `template-spatial-home.php` | WebXR landing surface (stub here, full build in 5.8) | `overdrive` allowed |

**Exit criteria per template:** No P0/P1 issues from `audit`; `critique` UX score ≥ threshold from `eval/templates.md`; `verification-loop` PASS on the WP page assigned to it.

---

### Phase 5 — Shock features (10 sub-phases — fully integrated)

#### 5.0 Prerequisites (autonomous gate, blocks 5.6 and 5.8)

```bash
node scripts/check-glb-rig.js assets/models/skyy.glb
# If FAIL and (5.6 needs avatar OR 5.8 needs avatar) → escalate G3
```

If avatar is broken AND used: pause 5.6/5.8, output Blender/Mixamo rig instructions to `eval/avatar-rig-required.md`, escalate.

#### 5.1 WC block cart/checkout fix (#1 unsolved category problem)

- Audit current block cart/checkout rendering (`audit` P0 sweep)
- Build SCSS for WC block templates; register `block.json` overrides
- Solve "flash of unstyled content"
- **Skills:** `audit` + `redesign-existing-projects` + `design-taste-frontend` + `woocommerce-backend-dev` agent
- **Eval:** Cart-to-confirmation Playwright e2e passes on real WC8/WC9/WC10

#### 5.2 Native WebGL product canvas

- Extend `assets/js/experiences/experience-base.js` to a single-product variant
- Spring-physics camera + scroll-pinned reveal
- Mobile fallback: 3-photo swipe gallery
- **Skills:** `overdrive` + `gpt-taste` + `design-taste-frontend`
- **Eval:** 60fps on M1 MacBook + iPhone 13+; graceful WebGL-disabled degradation

#### 5.3 Editorial scroll-narrative product page

- New variant `single-product-narrative.php`
- Each section is a chapter (origin → craft → wear); CTA at chapter 4
- Falls back to standard product page if narrative content not authored
- **Skills:** `image-taste-frontend` + `aidesigner` + `impeccable craft` + `delight` + `skyyrose-product-copy`
- **Eval:** Time-to-add-to-cart < 90s on narrative page; abandonment rate ≤ standard product page

#### 5.4 Drop-mechanics template set (orchestrated by `skyyrose-launch-commander`)

- `template-drop-day.php` — countdown + teaser hero
- `template-drop-live.php` — live restock view + queue position UI
- WebSocket-backed queue (Vercel function + Pusher)
- Pre-order infrastructure extended into full drop system
- Klaviyo "drop-day" flow extension via `skyyrose-email-flows`
- `skyyrose-launch-commander` calls (in sequence): product-copy → photography → email-flows → paid-media → content-engine → seo-commerce
- **Skills:** `gpt-taste` + `bolder` + `delight` + `websocket-engineer` agent
- **Eval:** Drop-day stress test — 1000 concurrent waitlist subscribers; <500ms unlock-to-cart

#### 5.5 Mobile-native gallery patterns

- Swipe-to-next-product on collection pages
- Tap-expand product gallery (replaces hover for desktop, primary on mobile)
- Pinch-zoom overlay on product images
- **Skills:** `design-taste-frontend` + `audit` (CWV)
- **Eval:** Mobile LCP < 2.5s, INP < 200ms, CLS < 0.1

#### 5.6 AR try-on integration (FASHN)

- `inc/fastapi-client.php` extension: `skyyrose_fashn_tryon($product_id, $user_image_id)`
- Vercel API route `/api/fashn-tryon` proxies to FASHN with retry + cost guard
- Theme UI: "Try on" button on product page → modal → upload → 4-model output → carousel
- Cost ceiling enforced server-side (per-user/per-day caps from §1.3)
- **Skills:** `php-pro` + `Backend Architect` + `security-reviewer` + `vercel:ai-architect`
- **Eval:** Roundtrip < 8s avg; cost < $0.30/try-on; falls back to size guide on failure

#### 5.7 AI semantic search (Pinecone)

- `inc/fastapi-client.php` extension: `skyyrose_semantic_search($query)`
- Vercel API route `/api/semantic-search` queries Pinecone index
- Vercel cron `/api/embed-products` reindexes WC products nightly
- Theme UI: replace standard `search.php` with semantic results when available; fall back to WP search if Pinecone unavailable
- **Skills:** `pinecone:quickstart` + `rag-architect` + (optional `huggingface-skills:hugging-face-model-trainer` for fashion fine-tune)
- **Eval:** Query latency < 300ms p95; relevance test against 50 hand-graded queries (precision@5 ≥ 0.7)

#### 5.8 WebXR / spatial layer

- `assets/js/experiences/experience-base.js` extension: enable `renderer.xr.enabled = true`
- WebXR session button on each immersive world (collection-aware copy)
- Hand-tracking controls for Vision Pro / Quest 3
- `template-spatial-home.php` Phase 5 build: WebXR landing with device detection
- **Skills:** `immersive-interactive-architect` + `overdrive`
- **Prerequisite:** Avatar rig pass from 5.0
- **Eval:** WebXR session starts on Vision Pro Safari, Quest 3 browser; falls back to standard 3D on unsupported devices

#### 5.9 Persistent prompt-eval Claude Lab admin tool

- Lives at `frontend/app/admin/claude-lab/` on Vercel (devskyy.app), NOT WP
- Sandbox + Eval combined per earlier separately-archived plan
- Test prompts for: product copy generation, email subject lines, social captions, FAQ answers
- **Skills:** `vercel:ai-architect` + `eval-harness`
- **Eval:** Cache-hit indicator works; cost telemetry accurate; eval suites runnable

#### 5.10 Payment processing fully wired

- Install + configure WooCommerce Stripe plugin
- Apple Pay / Google Pay express checkout enabled
- PayPal Payments enabled
- Stripe Tax integration if applicable
- Block-based checkout fully styled (extends 5.1)
- 3DS / SCA compliance verified
- **Skills:** `mcp__stripe__authenticate` + `woocommerce-backend-dev` + `security-reviewer` + `Backend Architect`
- **Eval:** Successful test charge in test mode; 3DS challenge handled; refund flow works

**Phase 5 validation cadence:** Every sub-phase passes `simplify` + `verification-loop` + sub-phase-specific eval before next sub-phase begins. Sub-phases run sequentially, not in parallel, to keep `AGENTS.md` scope clean.

---

### Phase 6 — Marketplace polish (no TF submission)

| Sub-phase | Tasks | Agent / Skill |
|-----------|-------|---------------|
| 6.1 Demo content | Extend `blueprints/skyyrose-demo-setup.json` to cover every page template | `wordpress-pro` |
| 6.2 Documentation | Audit existing 11 HTML docs in `docs/`; add: drop setup, WebGL config, AR config, semantic search config, style-quiz authoring | `wordpress-pro` |
| 6.3 WCAG 2.2 a11y | Full sweep; keyboard nav on every surface (incl. WebGL); SR landmarks on immersive | `Accessibility Auditor` |
| 6.4 Asset splitting | Audit conditional loading; ensure templates load only their assets | `audit` |
| 6.5 Performance | Test with 5 plugins + 50-product cart + Klaviyo embed; LCP<2.5s, CLS<0.1, INP<200ms | `Performance Benchmarker` + `vercel:performance-optimizer` |
| 6.6 Conversion tracking | GTM + GA4 + Meta CAPI + LinkedIn Insight Tag | `Tracking & Measurement Specialist` |
| 6.7 SEO | JSON-LD on every product/collection; sitemap; canonicals | `skyyrose-seo-commerce` |
| 6.8 Brand consistency | Review every surface against brand-dna; fix drift | `Brand Guardian` |
| 6.9 Cultural intelligence | Imagery + copy review | `Cultural Intelligence Strategist` + `Inclusive Visuals Specialist` |

**Exit criteria:** Marketplace readiness checklist (`eval/marketplace.md`) passes 100%.

---

### Phase 7 — Ship gate — **G2 GATE BEFORE DEPLOY**

```bash
/ship-check wp
# Composes:
#   npm run lint:php       (PHPCS)
#   npm run verify         (full local verification)
#   npx playwright test    (cart, checkout, drop unlock, AR try-on, semantic search, payment)
#   node scripts/preflight.js (renders/garment fidelity drift)
# Returns: SHIP | FIX-FIRST | HOLD-FOR-REVIEW
```

**If SHIP:**

1. `npm run deploy:dry` — preview output
2. **G2 GATE — STOP HERE.** User reviews preview, signs off
3. `npm run deploy` — atomic hot-swap (microsecond window)
4. `vercel deploy --prod` — Vercel API routes deploy in parallel

**Post-deploy autonomous verification:**

```bash
ts=$(date +%s)
curl -sS "https://skyyrose.co/?deploy_verify=$ts" | grep -q "skyyrose-v2" || echo "DEPLOY VERIFY FAIL"
for route in fashn-tryon semantic-search drop-queue; do
  curl -sS "https://devskyy.app/api/$route/health" | grep -q "ok" || echo "VERCEL HEALTH FAIL: $route"
done
npx playwright test smoke/post-deploy.spec.ts
```

If post-deploy verification fails: roll back via `npm run deploy:rollback` (atomic to previous commit), escalate G3.

---

## 6. Per-Page Accountability Table

29 WP pages → 27 (after deleting `faq-2` + `shipping-returns-2`).

| Slug | Phase action | Final state |
|------|--------------|-------------|
| `(front-page)` | Audit + polish (P6) | Polished |
| `about` | Audit + polish (P6) | Polished |
| `contact` | Audit (351L) + possible refactor (P6) | Polished or refactored |
| `faq` | Reassign → `template-faq.php` (P1) | Custom template |
| `faq-2` | Delete (P1) | Gone |
| `shipping-returns` | Reassign → `template-shipping-returns.php` (P1) | Custom template |
| `shipping-returns-2` | Delete (P1) | Gone |
| `terms-of-service` | Reassign → `template-info-page.php` (P3.3) | Polished info page |
| `privacy-policy` | Reassign → `template-info-page.php` (P3.3) | Polished info page |
| `pre-order` | Extends to drop-mechanics (P5.4) | Drop launchpad |
| `wishlist` | Audit (P6) | Polished |
| `landing-black-rose` | Consolidated (P3.1) | 16-line stub |
| `landing-love-hurts` | Consolidated (P3.1) | 16-line stub |
| `landing-signature` | Consolidated (P3.1) | 16-line stub |
| `collection-*` (4) | Already consolidated; polish (P6) | Polished |
| `experience-*` (3) | Consolidated to data file (P3.2) | 16-line stub |
| `experience` | Build `template-experiences.php` (P4) | Immersive hub |
| `spatial` | Build stub (P4) + full WebXR (P5.8) | WebXR landing |
| `style-quiz` | Build `template-style-quiz.php` (P4) | Quiz-to-cart |
| `cart` | Build `skyyrose-canvas.php` shell + style WC blocks (P5.1) + Stripe (P5.10) | Block-based, fully styled |
| `checkout` | Same | Block-based, payments live |
| `collections` | Reassign to `skyyrose-canvas.php` (P1) | Collections index via canvas |
| `shop` | Audit + polish (P6) | Polished WC archive |
| `my-account` | Audit + polish (P6) | Polished |

---

## 7. Critical Files to Read Before Each Phase

| Phase | Files |
|-------|-------|
| 1 | `inc/enqueue.php` (slug map verification after reassignments) |
| 1.5 | `inc/menus.php`, all `header*.php` files, existing footer templates |
| 2 | `inc/enqueue.php`, every CSS/JS suspected of orphan registration |
| 3 | `template-landing-{black-rose,love-hurts,signature}.php`, `template-parts/landing/*`, all 4 `template-immersive-*.php`, `template-parts/immersive-scene.php`, `template-faq.php`, `template-shipping-returns.php`, `inc/product-catalog.php` (pattern reference) |
| 4 | `template-elementor-canvas.php`, orphan `assets/css/style-quiz.min.css`, orphan `assets/css/spatial-home.min.css` |
| 5.1, 5.10 | `woocommerce/checkout/form-checkout.php`, `inc/security.php` (CSP for Stripe.js) |
| 5.2, 5.8 | `assets/js/experiences/experience-base.js`, all 3 collection world files, `assets/models/skyy.glb` |
| 5.4 | `template-preorder-gateway.php`, `inc/woocommerce-preorder.php`, `inc/klaviyo-integration.php` |
| 5.6, 5.7 | `inc/fastapi-client.php`, WC product schema |
| 5.9 | Original Claude Lab plan spec (preserved separately); `frontend/app/` patterns |
| 6 | `style.css`, `theme.json`, `blueprints/skyyrose-demo-setup.json`, all 11 HTML docs in `docs/` |
| 7 | `package.json` scripts, `scripts/deploy-theme.sh` |

---

## 8. Eval Framework (overview — full content built in Phase 0)

| Eval file | What it measures | Pass threshold |
|-----------|------------------|----------------|
| `eval/templates.md` | Per-template UX score, P0/P1 issue count, perf budget | UX ≥ 8/10, P0=0, P1≤2, LCP<2.5s |
| `eval/integrations.md` | Roundtrip latency, error rate, fallback correctness | p95 latency per service, error rate <1%, fallback verified |
| `eval/marketplace.md` | Readiness checklist | 100% green |
| `eval/shocking.md` | Observable "haven't seen this before" criteria | ≥3/5 pillars demonstrably first-of-kind |
| `eval/brand.md` | Voice/visual rules adherence | 0 banned phrases, palette match |
| `eval/page-flow.md` | Customer journey (built P1.5) | Drop reachable in ≤2 clicks from any page |

---

## 9. Risk Matrix

| Risk | Mitigation |
|------|-----------|
| FASHN cost runaway | Server-side per-user/per-day cap + global $50/day; G3 escalation at threshold |
| Pinecone index drift | Vercel cron nightly + on-product-save webhook |
| WebXR breaks on devices | Feature detect; fall back to standard 3D; never block desktop |
| Drop queue WS fails under load | Pusher managed; fallback to polling on Pusher down |
| Stripe key leak | Keys in Vercel env only; CSP enforced; security review pre-deploy |
| AGENTS.md scope violation | Each agent reads its `AGENTS.md` first; cross-boundary edits require sequenced handoff |
| Avatar GLB broken when needed | Phase 5.0 prerequisite check; fail-fast if 5.6/5.8 depend |
| Theme deploy breaks live site | Atomic hot-swap (microsecond window); deploy verification gate |
| WP.com hosting limits hit | Stateful work on Vercel; WP only request/response |
| Eval-as-theatre (build looks impressive but generic) | `eval/shocking.md` defines observable criteria; `critique` runs persona test |

---

## 10. Quality controller (always-on, invisible)

After every response Claude Code generates, iterate the 7 pillars until all pass:

1. **Correct** — does what was specified
2. **Complete** — no TODOs, no half-built features
3. **Production-ready** — handles error paths, logs, observability
4. **Best practices** — idiomatic per language/framework, follows repo conventions
5. **Clear** — readable by another senior engineer with no extra context
6. **Efficient** — no obvious perf footguns
7. **Maintainable** — small functions, clear names, tested where it matters

If any pillar fails on a generated artifact: do not present it; iterate silently until pass; then present.

---

## 11. Execution control summary

**Autonomous:** All file edits, all page reassignments, all design choices, all integration wiring, all consolidations, all polishing.

**Stop-and-ask (only 3):**

- G1: After Phase 0, before any code
- G2: After `/ship-check wp` SHIP, before deploy
- G3: Cost-cap exceeded, prerequisite missing, or two consecutive failures on the same edit

**Branching strategy:** Each phase on its own feature branch (`feat/phase-N-description`). Merge to `main` only after phase exit criteria PASS.

**Commit cadence:** Use `commit-commands:commit-push-pr` after every milestone (typically every sub-phase).

**Post-merge verification:** `verification-loop` runs against live preview environment before next phase begins.

---

## 12. Out of scope (excluded per user directive)

- ThemeForest submission (account creation, screenshots, video, marketplace listing).

Everything else is **IN SCOPE**.

---

**End of master plan. Ready for G1 (eval approval).**
