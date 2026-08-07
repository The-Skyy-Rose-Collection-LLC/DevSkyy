# SkyyRose Theme Team Charter

**Scope:** `wordpress-theme/skyyrose-flagship/` — the production WordPress/WooCommerce theme for skyyrose.co.
**Standard:** award-caliber fashion e-commerce that converts. This is a store, not a portfolio.
**Synthesized:** 2026-07-28 from 44 audited skill/agent candidates. Seats below are the survivors; everything else on the audit list is absorbed into a seat or rejected as overlap.
**Canon authority:** brand tokens, fonts, cut-fonts list, contrast rules, and collection identities in `CLAUDE.md` §6 are LOCKED and outrank every skill's internal brand notes. Where a skill's own brand section disagrees (notably `immersive-interactive-architect`), the skill's *techniques* are used and its *brand facts* are discarded.

---

## 1. The Team (12 seats)

Roster convention: **Doctrine** = skills loaded into whoever holds the seat. **Hands** = the dispatchable agent. A seat with no concrete dispatch trigger does not exist; every trigger below is an observable event.

### Seat 1 — Theme Architect (doctrine anchor)
- **Filled by:** `skyyrose-wp-platform` (skill, repo-local) + `devskyy-patterns` (skill).
- **Mandate:** Every task starts from this theme's real doctrine — template inventory, `.min` pipeline, SOT-gated WC plumbing, `loadThree()` mechanics, quality-gate map, hot-surface commit conventions — before any line is written.
- **Dispatch trigger:** The first tool call of ANY task touching theme PHP, templates, CSS/JS, WC wiring, or Three.js scenes.
- **Hard limits:** Load SKILL.md + exactly ONE reference file (its own router rule), not all four. This seat informs; it does not build. Repo facts it asserts must be re-verified when stale-marked.

### Seat 2 — Creative Director (taste authority)
- **Filled by:** `luxury-design-taste` (skill, repo-local — the precedence-chain tiebreaker) + `impeccable` (repo-local, `teach` mode installs `.impeccable.md` context once) + `extract-design` (benchmarks vs the Five) + `parallel-prototyping` + `luxury-mockup-pipeline`.
- **Mandate:** Owns every taste verdict — one accent per surface, lockup-images-never-type-rendered heroes, house ease `cubic-bezier(.16,1,.3,1)`, the slop-detector — and resolves conflicts between all other design skills via its precedence chain.
- **Dispatch trigger:** A new surface needs art direction; a visual call is contested (then: minimum 5 genuinely distinct parallel prototypes, winner merges, never rewritten); a standalone HTML mockup needs elevation before PHP porting.
- **Hard limits:** `extract-design` output is reference-only — extracted palettes/fonts NEVER enter the theme. Prototyping is for taste-contested surfaces only (hero, collection-card language, PDP gallery), never utility pages. Cannot override locked tokens/fonts; nothing can.

### Seat 3 — Lead Surface Builder
- **Filled by:** `fashion-theme-architect` (agent, Opus — the hands) with doctrine `frontend-design` + `impeccable` (`craft`) + `typeset` + `layout` + `animate` + `polish` + `css-cascade-discipline`.
- **Mandate:** Builds complete, gate-passing theme surfaces end to end — structure, type, composition, micro-motion, final-mile polish — and returns a worktree plus a structured build report.
- **Dispatch trigger:** Any new or rebuilt surface (a template, a funnel step, a full-theme plan item). Not for ≤3-file structural edits (Seat 4's lane).
- **Hard limits (from its own charter):** NEVER deploys, commits, bumps `SKYYROSE_VERSION`, uploads media, or makes any paid API call (incl. new gpt-image-2 renders). Aspects it cannot execute (`responsive`, `a11y-interactive`, `cwv`, `product-fidelity`) are marked SKIP and flagged — **a SKIP is not a pass**; Seat 10 must close them. Copy comes from Seat 7, never invented (the `no-placeholders` gate makes real copy a build dependency).

### Seat 4 — Structural Scalpel
- **Filled by:** `wp-theme-dev` (agent, Sonnet) with doctrine `css-cascade-discipline` + `devskyy-patterns`.
- **Mandate:** Cheap, surgical edits to the theme skeleton — `functions.php`, `inc/` modules, template routing, enqueue inventory, cascade-safe CSS fixes — where the Opus builder is overkill.
- **Dispatch trigger:** Targeted change ≤3 files: enqueue wiring, an `inc/` module, header/footer chrome, a "style isn't applying" cascade bug (specificity math BEFORE writing the override).
- **Hard limits:** Its agent file has no deploy/commit refusal — **the caller holds STOP-AND-SHOW for it**. Escalates anything growing past ~3 files to Seat 3. Never `!important` escalation; every CSS edit rebuilds `.min`.

### Seat 5 — Immersive Engineer
- **Filled by:** `wp-immersive` (agent — the hands) with doctrine `skyyrose-3d-web-os` (router) + `immersive-interactive-architect` (repo-local; **techniques only** — its brand section drifts from canon: `#8B0000`, rose-gold Black Rose, white-studio Signature are all WRONG) + `threejs-shaders` + `threejs-postprocessing` + `overdrive`.
- **Mandate:** Top-of-funnel 3D/scroll storytelling — collection worlds, drop-page reveals, bespoke GLSL materials (rose-gold iridescence, silver armor sheen, crimson glow) and cinematic post grade — at 60fps with mandatory fallbacks (reduced-motion, WebGL-unsupported, low-end mobile).
- **Dispatch trigger:** Any work on `template-immersive-*.php`, `template-collections-world.php` + `SKYY_SCROLL_WORLD_CONFIG` (`inc/enqueue.php:819`), `assets/js/immersive.js`, `assets/scenes/`, or any new Three.js scene.
- **Hard limits:** Storytelling only — never product-grid/catalog work; the ONE sanctioned shopping crossover is the `immersive-wc-bridge.js` hotspot→product link. Respects `loadThree()` via jsdelivr `/+esm` with NO importmap; wait-for-three-ready before scene init. Light hexes from CLAUDE.md tokens only (`0xdc143c` for Love Hurts, never `0x8b0000`). Every mesh must earn its render cost — a 3D moment slower or less emotional than a good 2D page gets cut.

### Seat 6 — Commerce Engineer
- **Filled by:** `wc-pdp-correctness` (skill, repo-local) + `wp-catalog-sync` (agent).
- **Mandate:** Revenue-path correctness (AJAX add-to-cart contract, variable-product quick-add, the three button states) and catalog truth — the store conforms to `skyyrose-catalog.csv`, never the reverse.
- **Dispatch trigger:** Building/changing/reviewing single-product templates, product cards, mini-cart, or any add-to-cart surface (run the 7-step live verification battery before sign-off); any price/name/status drift between site and CSV.
- **Hard limits:** Never creates a WC product not in the CSV first. Product imagery resolves ONLY via `data/sot-images.json` / `skyyrose.core.sot_images` — filenames are not identity. All WC REST writes are STOP-AND-SHOW. Kids Capsule showing 0 cards is launch-mode BY DESIGN — do not "fix" it. Its own agent file's collection table is stale (3 collections) — the CSV is authority, per its own rule.

### Seat 7 — Voice & Findability
- **Filled by:** `skyyrose-command-center` (skill, routing gate) + `skyyrose-content-engine` (agent — copy hands) + `skyyrose-seo-commerce` (agent — schema hands) + `seo` (skill, repo-local checklist).
- **Mandate:** Every user-facing string ships in Corey's voice from canonical product data (CSV → dossier → flag gap, never invent — lh-005 is the counter-example), and every page is structurally findable (Product+Offer JSON-LD with `@id` anchors, BreadcrumbList, per-collection voice isolation, canonical/meta discipline).
- **Dispatch trigger:** Any template needing copy authored or changed (collection intros, PDP microcopy, empty states, CTAs, alt text); any schema/meta/sitemap work; any pre-launch SEO audit.
- **Hard limits:** Authoring plane only — drafts and payloads; never executes WC writes, Klaviyo sends, or deploys without STOP-AND-SHOW `y`. Products by NAME, never SKU-first. JSON-LD/OG audits via cache-busted `curl | grep` — NEVER WebFetch (strips `<script>`). No urgency timers, ever.

### Seat 8 — Performance Engineer
- **Filled by:** `web-vitals-budgets` (skill, repo-local — browser half) + `wp-performance` (skill, repo-local — server half) + `optimize` (remediation patterns).
- **Mandate:** Green Core Web Vitals with browser-measured numbers under the budgets in §4, and server-side pursuit of the tracked ~2.3–3.4s TTFB debt.
- **Dispatch trigger:** Before AND after any above-fold media change ships; after any Three.js scene or overdrive showpiece merges; whenever a QA gate flags perf P0–P2. `wp-performance` fires only when browser measurement attributes the regression to TTFB/server time.
- **Hard limits:** Numbers-not-vibes: DevTools trace or Playwright PerformanceObserver, mobile+desktop, 3-run median, LCP element attribution — a report not in this format doesn't count. Measure logged-out (admin-bar CLS trap); mind Batcache deploy-window skew. Never "fixes" performance by deleting the showpiece — budget it in or escalate the taste call to Seat 2.

### Seat 9 — Code Review Gate (reviewer ≠ builder)
- **Filled by:** `code-reviewer` (agent, Fable — per the founder's standing rule for review verdicts) + `wp-security` (agent, read-only WP checklist: CSP vs `inc/security.php`, nonces, escaping, `$wpdb->prepare`, `permission_callback`) + `wp-code-simplifier` (agent, Haiku — dead-ref/bloat/duplicate-selector sweep).
- **Mandate:** No change moves toward deploy without independent review: general correctness (diff-scoped), WP-conventions security, and mechanical hygiene, as three cheap-to-expensive layers.
- **Dispatch trigger:** Any builder seat (3, 4, 5) finishes a checkpoint. `wp-security` additionally fires before shipping any PHP touching user input/output. Simplifier's clean report is a declared precondition of Seat 11.
- **Hard limits:** Reviewers never fix — findings return to the originating builder; the reviewer re-verifies the fix. `wp-security` and simplifier are read-only by toolset. Simplifier flags SOURCE only, never `.min` artifacts; it is not a substitute for `php -l`.

### Seat 10 — Eyes-On QA (browser evidence)
- **Filled by:** `e2e-runner` (agent — the hands: Playwright journeys, responsive, axe) + `design-qc` (skill, repo-local — brand-locked pixel review) + `critique` (dual-blind UX assessment) + `audit` (scored a11y/perf/theming/responsive report) + `accessibility` (skill, repo-local — WAI-ARIA patterns for bespoke components: holo cards, hotspots, mascot).
- **Mandate:** Close every SKIP the builder flagged with executed browser evidence, and verify rendered pixels against brand canon — the drift test is "does it read Kith/Oaklandish/Culture Kings/FoG/Palm Angels, or European-serif."
- **Dispatch trigger:** Any build report containing SKIP flags (`responsive`, `a11y-interactive`, `cwv`, `product-fidelity`); any visual change before deploy; live pages after deploy; pre-deploy critical-funnel journey runs (add-to-cart → cart AJAX → checkout).
- **Hard limits:** Full-res captures only — never judge from a contact sheet. Fresh captures after every fix round; stale evidence is no evidence. A capture/gate that errors is an artifact, not a pass — fail CLOSED (bug-230). Cut-font grep hits are a hard fail regardless of how the page looks. Mobile (390px) AND desktop, always; `img.decode()` before screenshot.

### Seat 11 — Release & Recovery (the only production toucher)
- **Filled by:** `deploy-and-verify` (agent — the hands) + `wordpress-platform-pipeline` (skill — the PHPCS → phpstan → wp-playground smoke → hot-swap → cache-busted-verify chain) + `theme-heal-doctor` (agent — live-regression surgeon).
- **Mandate:** Atomic, verified, reversible releases: 4-check pre-deploy sweep, STOP-AND-SHOW manifest, hot-swap deploy, 9-page cache-busted post-deploy verification (HTTP 200, hero lockup, grid, clean console, correct collection accent, ≥50KB body); root-cause heals when live regresses.
- **Dispatch trigger:** Deploy — only after Seats 9+10 are clean AND founder `y` (or the standing sweep-clean auto-deploy auth) is in hand. Heal — an authoritative live-regression signal (S1 HTTP/size/PHP-error, S2 canon drift, S3 asset-version), one invocation per regression, reproduce-first (~25% of audit claims are false positives — exit without fixing on a false positive).
- **Hard limits:** On ANY page failure: stop, capture evidence, `git revert`, redeploy the revert — never hot-patch live, never re-deploy without reverting, never declare "partial success." Refuses to run on failing `php -l`, unresolved DEAD-REF/BLOAT, or an unreviewed branch. Heal doctor never deploys, commits, or bumps versions — it hands the healed worktree back to the loop. Deploy-source completeness: the tracked-file preflight is blind to the 3 untracked riders (`.gitignore:290`) — check them by hand until the gate exists (§5).

### Seat 12 — Fashion Design System Engineer (anti-generic authority)
- **Filled by:** `fashion-design-system-engineer` (architect) commanding the inner pod documented at `docs/design/fashion-design-system-team.md`: brand systems research, token foundations, typography/layout, component/commerce, motion/responsive, accessibility/content, DesignOps/governance, and an independent visual QA red team. Doctrine is loaded on demand; rendered approval belongs to the red team with Seat 10 via `design-qc`.
- **Mandate:** Converts art direction into an enforceable system: canonical tokens, typography roles, composition grammar, recognition devices, full commerce-component state coverage, responsive transformations, motion/reduced-motion rules, and a route/state verification matrix. Owns the anti-generic hard-fail list, 100-point distinctiveness score, and logo-off recognition test.
- **Dispatch trigger:** After Seat 2 art direction and before any new or substantially redesigned surface enters Seat 3; whenever a page reads generic; whenever token, typography, component, or motion drift is found.
- **Hard limits:** Never creates a parallel token system when canon exists; never invents brand facts or product imagery; never approves its own rendered pixels. Builder handoff requires >=85/100, every category >=70%, zero instant fails, fresh 390/768/1440 evidence, and independent Seat 10 approval. Missing evidence is `UNVERIFIED`, never PASS. All tools remain callable, but no more than three skill instruction sets may be loaded at once.

**Rejected as redundant** (absorbed by the seats above): global `impeccable`/`immersive-interactive-architect`/`design-qc` duplicates (repo-local versions win), `skyyrose-3d-web-os` as a standalone seat (doctrine under Seat 5), `overdrive`/`animate`/`typeset`/`layout`/`polish` as standalone seats (instruments of Seats 3/5), `frontend-design` standalone (doctrine under Seat 3), generic `wp-frontend`-class candidates (subsumed by `fashion-theme-architect`).

---

## 2. The Pipeline

One surface, brief → shipped. Steps 2–3 may run in parallel; everything else is ordered. Every handoff is a named artifact — no artifact, no handoff.

| # | Step | Seat | Artifact handed to the next step |
|---|------|------|----------------------------------|
| 0 | **Doctrine load + plan** | 1 | `tasks/todo.md` plan (3+ steps) naming which reference file governs and which seats fire |
| 1 | **Art direction** | 2 | Direction spec at `docs/design/<surface>-direction.md` citing the 176-pattern shortlist; if contested, 5 parallel prototype variants + the merged winner |
| 2 | **Design-system contract** | 12 | `docs/design/<surface>-design-system.md`: recognition devices, token/component/state rules, distinctiveness baseline, responsive/motion matrix, and builder handoff verdict |
| 3 | **Copy & schema authoring** (parallel with 1–2) | 7 | Copy deck + paste-ready WC REST payloads + JSON-LD plan — real words enter the build, so `no-placeholders` can pass |
| 4 | **Build** | 3 (surface) / 4 (≤3-file) / 5 (immersive) | Gate-passing worktree + structured build report: `verify:theme` output attached, SKIP aspects explicitly flagged |
| 4 | **Commerce battery** (WC surfaces only) | 6 | 7-step add-to-cart verification log (button states, AJAX contract, variation rules) |
| 5 | **Code review gate** | 9 | Simplifier findings checklist → security findings → Fable review verdict. Findings return to the builder; loop until clean. **Gate: no unresolved CRITICAL/HIGH.** |
| 6 | **Eyes-on QA — SKIP closure** | 10 | Screenshot/trace set (390px + desktop), axe results, journey-test results, design-qc capture verdict. **Gate: every builder SKIP closed by executed evidence.** |
| 7 | **Performance verdict** | 8 | CWV attribution report (3-run median, mobile+desktop, LCP element named) vs §4 budgets. **Gate: budgets green or an accepted, founder-visible exception.** |
| 8 | **Final mile** | 3 (polish) + 4 (mechanics) | `.min` rebuild (byte-identical), `SKYYROSE_VERSION` triple bump (`functions.php`/`style.css`/`readme.txt`), deploy manifest |
| 9 | **Release** | 11 | STOP-AND-SHOW manifest → founder `y` → atomic deploy → 9-page post-deploy verification log. Any failure → revert log |
| 10 | **Live drift watch** | 10 then 11 | Post-deploy design-qc captures of live pages; on regression, heal-doctor's `HEAL_SCHEMA` JSON + lesson entry |

**Standing rules of the pipeline:** builders never review their own work; reviewers never fix; Seat 11 is the only production toucher; every paid call and every WC/media write gets its own manifest and its own `y`; fix everything in one batch, test all pages, deploy ONCE.

---

## 3. Modern Design Standard

The bar is what wins in 2026 fashion e-commerce, anchored to the Five — Kith, Oaklandish, Culture Kings, Fear of God, Palm Angels — NEVER European luxury houses. Every criterion is checkable; "looks good to me" is not a check.

1. **Editorial, asymmetric composition.** Collection/shop pages read as editorial spreads, not uniform shop grids: varied card scale, intentional density shifts, no more than two consecutive identical-width rows. *Check:* Seat 10 screenshot review against the layout-assessment framework + the 176-pattern shortlist; Seat 2 verdict recorded in the direction spec.
2. **Type as image.** Hero titles are the brand-script lockup IMAGES, never type-rendered; display type is Archivo with `font-variation-settings: 'wdth' 125`; UI accent labels are Anton 10–13px wide-tracked. *Check:* grep templates for lockup asset references (no `<h1>` styled in a script font); Playwright `getComputedStyle` on hero/display elements.
3. **Zero canon drift.** No cut font (Playfair Display, Cormorant Garamond, Bebas Neue, Yellowtail) anywhere; every hex traces to the five tokens (#B76E79, #0A0A0A, #C0C0C0, #DC143C, #D4AF37) or a derived token in `design-tokens.css`. *Check:* grep new CSS/JS for cut-font names (any hit = hard fail); hex extraction diffed against the token set.
4. **One accent per surface.** Each collection surface carries its own single accent on #0A0A0A — two accents on one screen is a flea market. *Check:* design-qc capture review per collection page; computed accent inventory per viewport.
5. **Restraint in motion.** House ease `cubic-bezier(.16,1,.3,1)`, reveals 0.6–1.2s, at most ONE showpiece moment per page, `prefers-reduced-motion` fallback on every animation with no exceptions. *Check:* grep every new animation/transition for the reduced-motion guard; Seat 10 motion QA against §5.2 of the architect's gate.
6. **Choreographed scroll, never scroll-jacking.** Scroll-driven reveals tied to narrative beats; native scroll position always honored; no wheel-event hijack. *Check:* Playwright scrub test (scroll → assert reveal states); grep for `preventDefault` on wheel/touchmove outside sanctioned canvas contexts.
7. **Real product photography, garment as protagonist.** Every product image resolves via the SOT and is pixel-verified as the correct garment for its SKU; imagery desaturated 30–40% only in ambient/background use; garment crops 3:4 or 2:3. *Check:* `product-fidelity` aspect — vision-read pixels vs catalog, never filenames; grep templates for SOT resolution (no hardcoded product image paths).
8. **Considered empty states.** Cart-empty, search-no-results, and launch-mode collections (Kids Capsule 0 cards is BY DESIGN) each get designed, on-voice states — never a bare "no products found." *Check:* Playwright visits each empty state; copy present from Seat 7's deck; screenshot review.
9. **Tactile microinteraction.** Product cards have a deliberate hover/focus language; add-to-cart styles all three button states (default/loading/added); form feedback is immediate. *Check:* CSS presence of `:hover`/`:focus-visible`/`:active` + state classes on the touched components; eyes-on interaction pass in Seat 6's battery.
10. **Dark-mode-native, measured contrast.** #0A0A0A is the ground truth, not an inverted afterthought. Crimson #DC143C (3.63:1) never carries body text — fills/borders/glows only; de-emphasized text is `--color-text-muted` #B3B3B3 (9.44:1), never low-alpha white. *Check:* automated computed-contrast pass on all text nodes (≥4.5:1 body, ≥3:1 large); grep for `rgba(255,255,255,` used as text color.
11. **Immersive that earns its render cost.** Every 3D scene has reduced-motion, WebGL-unsupported, and low-end-mobile fallbacks, holds 60fps on a mid-tier phone, and delivers an emotional beat a 2D page couldn't. *Check:* fallback grep + Playwright with WebGL disabled; frame-rate trace during the scene; Seat 2 verdict on the beat.
12. **The drift test.** Final captures of every surface answer one question: does this read as the Five, or as a European maison? *Check:* design-qc's explicit drift question, answered per surface in the QA verdict, with the reasoning written down.

---

## 4. ROI Criteria

Mobile-first: >70% of traffic is assumed mobile — every budget is measured at 390px on a mid-tier device profile first; desktop is the secondary pass.

### Numeric targets

| Metric | Target | Measured by | Owner |
|---|---|---|---|
| LCP (mobile p75) | ≤2.5s — excluding the tracked ~2.3–3.4s TTFB debt, which must be attributed separately, never hidden | DevTools trace / Playwright PerformanceObserver, 3-run median, LCP element named | Seat 8 |
| INP | ≤200ms | Same battery; worst interaction attributed | Seat 8 |
| CLS | ≤0.05 (stricter than the 0.1 floor) — measured logged-out | Same battery | Seat 8 |
| Above-fold media weight | ≤1.5MB; header animated asset ≤400KB; hero video poster is the LCP candidate, nav video must NOT steal LCP candidacy | Network trace on first load | Seat 8 |
| 3D scene frame rate | 60fps sustained on mid-tier mobile profile; no long task >200ms during scene init | Performance trace during scroll-scrub | Seats 5+8 |
| Hero → collection CTR | ≥25% of homepage sessions click into a collection surface | GA4 event on portal CTAs | Seat 2 (direction accountability) |
| PDP scroll depth | Median session reaches ≥70% of PDP height (the story below the fold is being read) | GA4 scroll events | Seats 3+7 |
| Add-to-cart rate | ≥8% of PDP sessions | GA4 + WC funnel | Seat 6 |
| Cart abandonment | ≤65% (fashion baseline runs 70–75%; beat it on trust and speed, not pressure) | WC checkout funnel | Seat 6 |
| Email capture | ≥3% of sessions via inline/footer modules — never an entry interstitial | Klaviyo list growth / sessions | Seat 7 |
| Post-deploy page health | 9/9 pages: HTTP 200, ≥50KB body, zero console errors, correct collection accent | Seat 11's verification log | Seat 11 |

Where analytics events don't exist yet for a metric, wiring the event is part of the surface's definition of done — a target nobody measures is decoration.

### What this brand will NOT do to convert
- **No urgency timers. No fake scarcity. No fake "X people are viewing."** Founder-banned; also a design-qc hard fail.
- **No popup interstitial on entry.** Email capture is inline, contextual, post-engagement.
- **No autoplay audio. No scroll-jacking. No dark-pattern cart adds** (nothing enters the cart the user didn't tap).
- **The garment is the protagonist** — no treatment (motion, overlay, model styling, crop) that makes the product secondary to the effect.
- **No urgency-voice copy** — drops are announced with confidence, not countdown anxiety.
- **No pressure-based cart-recovery** — recovery emails restate the garment's story, not a ticking clock.

---

## 5. Quality Gates

### Existing gates → owners

`verify:theme` aspect inventory confirmed against `skyyrose-flagship/scripts/verify-theme.sh --list` this session `[repro]`. Exit 0 = no FAIL; WARN/SKIP never auto-pass — SKIPs are Seat 10's queue.

| Gate | What it proves | Owner (runs it) | Enforced at |
|---|---|---|---|
| `php-syntax` (CLI) | `php -l` clean on every delivered file | Builder seats 3/4/5 | Pipeline step 3; re-run by Seat 11 preflight |
| `phpcs` (CLI) | WP+WC coding standards (`.phpcs.xml`) | Builders; Seat 11 preflight | Steps 3, 9 |
| `phpstan` (CLI) | Static analysis at configured level | Seat 9 (with `wp-phpstan` skill for config/baseline work) | Step 5 |
| `style-header`, `screenshot`, `templates`, `wc-support`, `pot`, `json-manifests` (CLI) | Theme-marketplace structural completeness | Seat 3 | Step 3 |
| `min-sync` (CLI) | Every source CSS/JS has a fresh `.min` sibling (byte-identity vs fresh build) | Builders after every edit; Seat 11 blocks on it | Steps 3, 8, 9 |
| `no-placeholders` (CLI) | No TODO/lorem/"Coming soon" in delivered code | Seat 3 (satisfied by Seat 7's copy deck) | Step 3 |
| `no-secrets` (CLI) | No hardcoded keys/passwords | Seat 9 (`wp-security` + reviewer pre-checks) | Step 5 |
| `i18n-domain` (CLI) | `skyyrose` text domain on all translation calls | Seat 3 | Step 3 |
| `file-size` (CLI) | No delivered PHP >800 lines | Seats 3/4; simplifier flags approach at >400 | Steps 3, 5 |
| `escaping`, `a11y-static` (CLI, advisory WARN) | Raw echo / missing alt / skip-link smells | Seat 9 escalates WARN→FAIL judgment | Step 5 |
| `cwv` (BROWSER, Lighthouse `--url`) | LCP/CLS/TBT on a live URL | Seat 8 (plus its own PerformanceObserver battery — Lighthouse alone is not the attribution format) | Step 7 |
| `responsive` (BROWSER SKIP) | 390px + desktop render | Seat 10 via `e2e-runner` | Step 6 |
| `a11y-interactive` (BROWSER SKIP) | Keyboard/focus/contrast, axe pass | Seat 10 (doctrine: `accessibility` skill) | Step 6 |
| `product-fidelity` (VISION SKIP) | Garment ↔ SKU pixel match vs catalog | Seat 10 (vision read; batch, never retry image reads) | Step 6 |
| PHPCS→phpstan→playground→deploy→verify chain | End-to-end release pipeline | Seat 11 (`wordpress-platform-pipeline`) | Step 9 |
| Playwright journeys (add-to-cart, cart AJAX, checkout) | Funnel actually works | Seat 10 | Steps 6, 9 (pre-deploy regression run) |
| 9-page post-deploy sweep | Live site healthy, cache-busted | Seat 11 | Step 9 |
| Stop-test-gate hook | Session cwd's tests reproduce before stop | All seats (worktree-aware, blocks on reproduction) | Continuous |

### Gates that do NOT yet exist — build these

1. **`brand-canon` aspect (CLI).** Automate what is manual in design-qc/§5.2: grep delivered CSS/JS/PHP for the four cut fonts (hard FAIL), extract all hex/rgba literals and diff against the token set, grep every `animation`/`transition` for a `prefers-reduced-motion` guard. Owner: Seat 12 defines, Seat 4 wires into `verify-theme.sh`, Seat 10 corroborates against rendered pixels. Highest-leverage missing gate — canon violations currently depend on a human remembering to grep.
2. **`contrast` aspect (BROWSER).** Computed-contrast pass over rendered text nodes: FAIL on body text <4.5:1, on #DC143C carrying text, on low-alpha-white text colors. Owner: Seat 10. The crimson rule is currently only prose in CLAUDE.md.
3. **`sot-imagery` aspect (CLI).** Every product image reference in templates/PHP resolves through the SOT layer; FAIL on any hardcoded product image path. Owner: Seat 6. Filenames-are-not-identity is currently convention, not a gate.
4. **CWV budget gate in CI.** The §4 numbers as machine-enforced budgets (Lighthouse CI or the Playwright battery) run on PR, not just pre-deploy — a vitals regression should fail review, not be discovered at step 7. Owner: Seat 8.
5. **Untracked-rider completeness gate.** `preflight_completeness()` (`scripts/deploy-theme.sh:313`) only checks git-tracked files; the 3 untracked `*-v2-avatar.webp` riders are invisible to it and a clean-tree deploy silently drops them. Either `git add -f` the riders under the gate or extend preflight with an explicit rider manifest that fails CLOSED. Owner: Seat 11. (bug-252 / bug-230 class.)
6. **`jsonld` aspect (CLI, live).** Cache-busted `curl` + structured-data validation of Product/Offer/BreadcrumbList on PDP and collection pages, wired into the 9-page sweep. Owner: Seat 7 authors, Seat 11 runs. WebFetch is banned for this check by construction.
7. **HG-5 closure gate.** Promote the skip-link/a11y-static WARN to FAIL once Seat 10 lands the fix — an advisory that stays advisory forever is a fail-open gate. Owner: Seat 10.
8. **Version-bump tripwire (CLI).** FAIL when any CSS/JS content changed but the `SKYYROSE_VERSION` triple did not — stale-cache-on-returning-visitors is a deploy-correctness bug, currently caught only by discipline. Owner: Seat 4 wires; Seat 11 enforces.

---

*Charter maintenance: this document lives at `docs/theme-team-charter.md`. Amend it when a seat's filling skill/agent materially changes, when a missing gate from §5 lands (move it to the existing-gates table), or when the founder overrides a target in §4. Every amendment is a normal reviewed commit — the charter is code.*
