# OpenWolf

@.wolf/OPENWOLF.md

This project uses OpenWolf for context management. Read and follow .wolf/OPENWOLF.md every session. Check .wolf/cerebrum.md before generating code. Check .wolf/anatomy.md before reading files.


# DevSkyy — Claude Code Configuration

## Identity
You are the DevSkyy engineering agent. 100% quality, no stubs, no partial deliverables.

---

## Anti-Hallucination Protocol
**If you haven't read it, you don't know it.** Every claim traces to a tool call or user confirmation from THIS session. Say "I don't know" when you don't. Read source → Search codebase → Check memory → Ask user → State uncertainty. Never invent.

---

## Commands by Workspace

### Python API (root)
```bash
make install                         # pip install -e ".[all]"
make dev                             # install + dev deps
uvicorn main_enterprise:app --host 0.0.0.0 --port 8000 --reload
make test                            # pytest tests/
make test-fast                       # pytest -x --timeout=10
make test-cov                        # pytest --cov
make format                          # isort . && ruff check --fix && black .
make lint                            # ruff check . && black --check .
```

### Dashboard (frontend/)
```bash
cd frontend
npm install                          # install deps
npm run dev                          # dev server
npm run type-check && npm run lint   # verify
npm run build                        # production build
```

### WordPress (wordpress-theme/)
```bash
cd wordpress-theme
npm run deploy                       # deploy to skyyrose.co
npm run deploy:dry                   # preview without touching server
npm run lint:php                     # PHP syntax check all files
npm run verify                       # full verification
# SSH key: ~/.ssh/skyyrose-deploy | Server: sftp.wp.com
```

---

## Architecture

**AI-driven luxury fashion e-commerce platform (SkyyRose brand)**
Python 3.11+ · FastAPI · Next.js · WordPress/WooCommerce · Three.js

```
core/           → Foundation: auth, cache, events, registry (zero external deps)
security/       → JWT, OAuth2, AES-256-GCM encryption
database/       → Alembic migrations, models
llm/            → 6 providers: OpenAI, Anthropic, Google, Mistral, Cohere, Groq
orchestration/  → RAG, LangGraph, CrewAI workflows
services/       → ML models, 3D generation, analytics
agents/         → Specialized agents (base_super_agent.py = foundation)
api/            → FastAPI REST (v1/) + GraphQL (graphql/)
frontend/       → Next.js dashboard (devskyy-dashboard)
wordpress-theme/skyyrose-flagship/  → Production WP theme (v1.0.0 — commercial)
scripts/        → Deploy, sync, generation scripts
```

**Dependency flow:** `core → security → database/llm → orchestration/services → agents → api`

### Entry Points
| File | Purpose |
|------|---------|
| `main_enterprise.py` | FastAPI app — REST + GraphQL + webhooks |
| `devskyy_mcp.py` | MCP server — 20+ tools |
| `frontend/` | Next.js 16 + React 19 dashboard |
| `wordpress-theme/skyyrose-flagship/` | Production WordPress theme |
| `skyyrose/elite_studio/` | Multi-agent image pipeline |
| `agents/base_super_agent/agent.py` | EnhancedSuperAgent base class |

### Workspaces (Isolated Environments)

| Workspace | Runtime | Root | Install | Dev |
|-----------|---------|------|---------|-----|
| **Python API** | Python 3.11+ | `/` | `make install` | `make dev` |
| **Dashboard** | Node.js 22 | `frontend/` | `npm install` | `npm run dev` |
| **WordPress** | PHP 8.2 | `wordpress-theme/` | N/A (deploy only) | `npm run deploy` |
| **Imagery (Nano Banana 2)** | Python 3.13 | `.venv/` | `pip install -r requirements-imagery.txt` | `source .venv/bin/activate && python scripts/nano-banana-run.py generate --sku br-001 --pro` — see `docs/NANO_BANANA.md` |
| **ADK Agents** | Python (isolated) | `.venv-agents/` (create as needed) | `pip install google-adk` | — |

**Each workspace is self-contained.** Don't mix `frontend/node_modules` with root. Don't use `.venv` for ADK (numpy conflicts — create `.venv-agents/` for it). Nano Banana shares the main `.venv/`; `.venv-imagery/` was an earlier design that was never created.

---

## WordPress Theme (SkyyRose v1.0.0)

**Commercial marketplace theme. Production at skyyrose.co**
**Theme Name:** SkyyRose | **Text Domain:** `skyyrose` | **@package:** SkyyRose

```
wordpress-theme/skyyrose-flagship/
├── assets/css/      43 files (page CSS, holo cards, tokens, components)
├── assets/js/       23 files (holo cards, navigation, page-specific)
├── assets/fonts/    19 files (self-hosted woff2, zero Google Fonts CDN)
├── inc/             21 modules (enqueue, security, WC, ajax, SEO)
├── inc/builders/    6 files (detection, elementor, divi, beaver, bricks)
├── template-parts/  37 partials (product-card-holo.php = holo card system)
├── patterns/        4 collection hero block patterns
├── woocommerce/     5 overrides (cart, checkout, single-product)
├── blueprints/      WC Blueprints for one-click demo import
├── docs/            11 HTML documentation files (ThemeForest submission)
└── *.php            24 page templates + 3 builder templates
```

**Active templates:**
- `front-page.php` — Three.js portals (3 collection rings + particles)
- `template-collection-{signature,black-rose,love-hurts,kids-capsule}.php` — Collection pages
- `template-landing-{black-rose,love-hurts,signature}.php` — Conversion landing pages
- `template-preorder-gateway.php` — Pre-order with collection selector
- `template-immersive-{signature,black-rose,love-hurts,kids-capsule}.php` — 3D experiences
- `template-about.php` — Brand story + timeline
- `template-elementor-canvas.php` / `template-elementor-fullwidth.php` — Builder templates

**Key systems:**
- `product-card-holo.css/js` — Holographic glass cards with magnetic tilt
- `inc/enqueue.php` — All CSS/JS loading, template slug detection
- `inc/security.php` — CSP headers, rate limiting, ABSPATH guards
- `inc/builders/detection.php` — `skyyrose_active_builder()` + `skyyrose_builder_owns_template()`
- `inc/patterns.php` — Block pattern registration for all collections
- `inc/performance.php` — Google Fonts removal, AVIF support, custom image sizes
- `functions.php` — Theme constants, includes array (v1.0.0)

**PHPCS compliance:**
- `.phpcs.xml` in theme root — WordPress standard, `skyyrose` prefix
- Run: `cd wordpress-theme/skyyrose-flagship && vendor/bin/phpcs --standard=.phpcs.xml -s .`
- Auto-fix: `vendor/bin/phpcbf --standard=.phpcs.xml .`
- Composer must be installed first: `~/.local/bin/composer install`

### WordPress Rules
- Extend via hooks (actions/filters), never modify core
- API: `index.php?rest_route=` NOT `/wp-json/`
- Escape output: `esc_html()`, `esc_attr()`, `esc_url()`, `wp_kses_post()`
- Sanitize input: `sanitize_text_field()`, `absint()`
- Always `$wpdb->prepare()` — never concatenate untrusted input
- Nonce + capability checks on all write actions
- No `innerHTML` in JS — use `createElement` + `textContent`

---

## Development Protocol

**MANDATORY — EVERY TASK:** Before writing ANY code that touches an external library or API:
→ `Context7: resolve-library-id` → `Context7: query-docs` → verify signatures → THEN code.
No exceptions. This applies to google-genai, httpx, Pydantic, LangGraph, FastAPI, WooCommerce REST, and every non-stdlib library. Skipping costs more tokens fixing wrong usage than the lookup saves.

1. **Context7 first** (see above — non-negotiable on every task)
2. Read existing code first, then `Edit` (targeted) or `Write` (new files only)
3. TDD: RED → GREEN → IMPROVE
4. `pytest -v` after EVERY change — target 85%+ coverage
5. Format: `isort . && ruff check --fix && black .`
6. After corrections → add Learnings entry, commit fix + learning together

---

## Loop Protocol

Every task runs as a loop, not a line:

1. Write the change.
2. Run the checks: tests, linter, type checker.
3. If anything fails, read the error, fix the cause, go back to step 2.
4. Repeat up to 5 times.

Stop conditions:
- All checks pass: report "done" with the passing output as proof.
- 5 attempts used: stop and report what still fails and what you tried.
- Same error appears twice in a row: stop. You're guessing, not fixing.

Never report "done" without check output from this session.
Never fix a test by weakening it. Fix the code, not the test.

---

## Critical Rules

- Files <800 lines, functions <50 lines
- Immutability: `{...obj, key}` not `obj.key = val`
- No hardcoded secrets — use env vars (`.env`, `.env.wordpress`, `.env.secrets`)
- Generic errors to clients, detailed logs server-side only
- Validate: Zod (frontend) / Pydantic (backend) at system boundaries
- Git: `<type>: <description>` (feat, fix, refactor, docs, test, chore)
- Python line length: 100 (black + ruff + isort)
- Use npm not pnpm for Vercel deploys (ERR_INVALID_THIS on Node 22+)
- Fix everything in one batch, test all pages, deploy ONCE (no back-and-forth)
- When cleaning up: update EVERY file that references deleted code

---

## Brand

| Token | Value | Usage |
|-------|-------|-------|
| Rose Gold | `#B76E79` | Global accent, Kids Capsule |
| Dark | `#0A0A0A` | Background |
| Silver | `#C0C0C0` | Black Rose accent |
| Crimson | `#DC143C` | Love Hurts accent |
| Gold | `#D4AF37` | Signature accent |

- Tagline: "Luxury Grows from Concrete."
- Collections: Signature, Black Rose, Love Hurts, Kids Capsule
- Fonts: Cinzel (BR headings), Playfair Display (SIG/LH/KC), Cormorant Garamond (body), Bebas Neue (UI), Inter (system)
- All 9 font families declared in `theme.json` via WordPress Font Library (zero external CDN)

---

## Deploy

| Target | Command | Config |
|--------|---------|--------|
| WordPress | `bash scripts/deploy-theme.sh` | `.env.wordpress` |
| Frontend | `cd frontend && npm run deploy` | `vercel.json` |
| API | `docker compose up -d` | `docker-compose.yml` |
| HF Spaces | `bash scripts/deploy_hf_spaces.sh` | `.env` |

---

## Learnings

### Architecture
- `agents/base_super_agent/agent.py` is the foundation — the directory `agents/base_super_agent/` is a package, not a flat file. (Cerebrum: never create `agents/base_super_agent.py` as a flat file; Python silently ignores the .py if the package exists.)
- DataLoaders → `api/graphql/dataloaders/` (not `core/`)
- Integration tests → `tests/integration/` (not `tests/api/`)

### Python Packaging
- Every top-level package directory MUST contain `__init__.py`. No implicit namespace packages. `mypy.ini` has `namespace_packages = False` to enforce this.
- Why: implicit namespace packages let mypy resolve the same `.py` file under two module names (e.g., `preflight` and `renders.preflight`), producing "Source file found twice under different module names" errors that silently block commits.
- If you add a new top-level package dir (e.g., `newthing/`), add `newthing/__init__.py` in the same commit — even if empty, a one-line docstring is fine.
- `.claude/worktrees/` are LIVE git worktrees (per `git worktree list`). Pre-commit's `mypy . --ignore-missing-imports --exclude '\.claude/'` keeps duplicate file paths out of module discovery.

### Google ADK
- Agent names: underscores only (valid Python identifiers)
- Loop per-product with `time.sleep(8)` to avoid 429s
- Use `.venv-agents/` (ADK conflicts with numpy)

### Security
- Validate backend URLs against allowlist; block `169.254.x.x`, `file://`, `gopher://`
- Cap in-memory tracking with LRU eviction
- Whitelist config keys before `**unpacking`
- No `innerHTML` in JS — all DOM construction via `createElement`

### WordPress
- CDN caches CSS aggressively — bump `SKYYROSE_VERSION` or use `?nocache=` to verify
- `enqueue.php` template slug map must match actual template filenames exactly
- Collection pages use unified `collection-pages.css` + `collection-pages.js` (one CSS replaces 4 separate files)
- Collection pages use `col-*` classes with `data-collection` attribute for palette switching via CSS custom properties
- Collection pages use IntersectionObserver scroll-reveal (`.col-reveal`), NOT GSAP — GSAP only for preorder/about/immersive
- Holo card grid: only `.product-grid`, `.product-grid__items`, `.br-product-grid__items` should be `display: grid`
- Don't duplicate content sections — if showcase cards show collections, don't add separate narrative cards with same data
- Showcase card content should be visible by default (`opacity: 1`), not hidden until hover — mobile has no hover
- When removing a PHP section, also remove its CSS rules AND responsive breakpoint overrides
- Premium animation system: `animations-premium.css` + `premium-interactions.js` loaded globally — use `rv-clip-*`, `rv-blur*`, `rv-split-*`, `stagger-grid`, `magnetic`, `btn-sweep`, `btn-border-draw` classes
- `php-lint.sh` needs explicit Homebrew PHP path (`/opt/homebrew/bin/php`) — lint-staged subshell doesn't inherit brew paths
- Image cache-bust: append `?v=' . SKYYROSE_VERSION` to branding image URLs in templates
- Cursor disappearing: caused by Jetpack Instant Search invisible overlay (z-index max, opacity 0, pointer-events auto) — fix with `pointer-events: none !important` in design-tokens.css
- `front-page.php` uses its own inline footer (`.ft` class) + `wp_footer()` instead of `get_footer()` — shared template parts (mobile-nav, cookie-consent, size-guide, toast-container) must be manually included before `wp_footer()`
- Jetpack Instant Search hijacks search results with a white overlay — our custom `search.php` only renders when Instant Search is disabled
- Any new template part added to `footer.php` must ALSO be added to `front-page.php` before `wp_footer()`
- Landing pages use `lp-*` classes with `[data-collection]` palette switching (same pattern as collection pages but `--lp-*` CSS vars)
- Landing pages use `.lp-rv` scroll-reveal (IntersectionObserver) — NOT `.col-reveal` or GSAP
- Landing page templates registered as slug `'landing'` in enqueue.php — loads `landing-pages.css` + `landing-pages.js` + holo cards
- Hero overlays live in `assets/images/hero-overlays/` (deployed with theme) — source PNGs in `assets/techflats/hero-overlays/` (repo root)
- Landing page template parts in `template-parts/landing/` accept `$args` arrays: hero.php, product-grid.php, faq.php
- Product grid template part pulls from `product-catalog.php` by SKU array — if SKU not in catalog, card is silently skipped
- **Theme name is "SkyyRose"** (not "SkyyRose Flagship") — text domain is `skyyrose`, @package is `SkyyRose`, folder stays `skyyrose-flagship/` for deploy compat
- **Version is 1.0.0** for commercial release — synced across style.css, readme.txt, and `SKYYROSE_VERSION` constant
- **PHPCS WordPress standard enforced** — `.phpcs.xml` in theme root, run `vendor/bin/phpcs` before commits. Composer installed at `~/.local/bin/composer`
- Leading-underscore functions (`_skyyrose_*`) renamed to `skyyrose_*` — WPCS requires theme prefix without underscore
- `skyyrose_nav_fallback()` (was `skyyrose_flagship_nav_fallback()`) — used as fallback_cb in header.php wp_nav_menu calls
- Builder detection: `skyyrose_active_builder()` returns slug ('elementor'|'divi'|'beaver-builder'|'bricks'|'gutenberg')
- Block patterns registered in `inc/patterns.php` — pattern files in `patterns/` directory
- Store API v1 cart was in `assets/src/js/cart.js` (268L, exposed `window.SkyyRoseCart`) — RETIRED in commit `87e420883` (legacy build cleanup) and the dormant enqueue removed from `inc/woocommerce.php` on 2026-04-27. To revive, `git show 87e4208838~1:wordpress-theme/skyyrose-flagship/assets/src/js/cart.js > <path>` and re-add the `wp_enqueue_script` block.
- Brand palette helper is **`skyyrose_brand_colors()`** (12 keys: rose_gold, gold, crimson, silver, dark, deep_black, deep_red, purple, navy, deep_blue, soft_pink, lavender) in `inc/brand-colors.php:41`. Do not invent `skyyrose_brand_palette()` — it doesn't exist. Builder palette callbacks pull hex values from this helper; only `#FFFFFF` (white) stays inline since white isn't part of the brand.
- Builder integrations (Divi, Beaver, Bricks) use a shared scaffold: `skyyrose_register_builder_compat($slug, $config)` in `inc/builders/shared.php`. Each builder file passes a `theme_support` callback and a `palette_callback` that receives `skyyrose_brand_colors()` plus the hook's args. Elementor keeps its richer integration inline (widgets, breakpoints, schemes, Google-Fonts disable) but calls `skyyrose_brand_colors()` for the schemes hex values.
- **`design-tokens.css` is enqueued globally** by `inc/enqueue.php:71-76` at priority 10 inside `skyyrose_enqueue_global_styles()`. Per-builder enqueues are forbidden — `wp_enqueue_style('skyyrose-design-tokens', ...)` should appear in `inc/enqueue.php` only. The `skyyrose-product-card-holo` enqueue inside `inc/builders/elementor.php:127` is allowed because it's Elementor-frontend-conditional, not redundant.
- Bootstrap order in `functions.php:118-148` matters: `detection.php` → `shared.php` → builder-specific files. The shared helper must load before the four builder files since they call `skyyrose_register_builder_compat()` at file-include time.
- **Per-collection palette is owned by `assets/css/design-tokens.css`** under `:root` (default) + `[data-collection="signature"|"black-rose"|"love-hurts"]` selectors. Tokens: `--skyyrose-accent`, `--skyyrose-accent-rgb`, `--skyyrose-accent-dark`, `--skyyrose-secondary`, `--skyyrose-bg`, `--skyyrose-text`, `--skyyrose-text-muted`, `--skyyrose-font-display`, `--skyyrose-font-body`, `--skyyrose-font-mono`, `--skyyrose-font-ui`, `--skyyrose-ease`, `--skyyrose-radius`. Feature CSS (`landing-pages.css`, `system/animations-premium.css`) and PHP inline styles consume these via `var(--skyyrose-*)` directly — no `--col-*` or `--lp-*` aliases exist. To add a new collection: add a `[data-collection="<new-slug>"]` block to design-tokens.css and emit the attribute on the page wrapper. Retired in U-4 (2026-05-04); do not reintroduce the legacy aliases.
- **Single scroll-reveal IntersectionObserver** lives in `assets/js/premium-interactions.js` inside the IIFE. Selector list managed via the `revealSelectors` variable: `.rv-clip-{up,left,right,diagonal}, .rv-blur, .rv-blur-down, .stagger-grid, .rv-split-{char,word,line}, .col-reveal, .lp-rv, .abt-page .rv`. Toggles `.is-visible` once per element, then `unobserve`s. Threshold `0.12`, rootMargin `0px 0px -40px 0px`. Reduced-motion early-return forces `.is-visible` on all matching elements. To add new reveal classes: extend `revealSelectors` (single source of truth shared by both the Motion One inView() path and the IntersectionObserver fallback). Per-page reveal observers were retired in U-1 (2026-05-04); `landing-pages.js` and `about.js` no longer have local observers. **Exception (intentional):** `assets/js/homepage-v2.js` keeps its own front-page observer — different class (`.vis`), no `unobserve`, separate semantics. Other observers in the theme (product-card-holo entrance stagger, experience-analyzer, preorder-gateway, single-product, page-transitions prefetch, experiences/* 3D scene) serve different purposes and stay separate.
- **About page reveal CSS lives in BOTH `about.css` source AND `about.min.css`** as of U-1. Pre-existing source/min drift was repaired during U-1 — `.abt-page .rv` and `.abt-page .rv.is-visible` rules are now in source. The toggled state class changed from `.vis` to `.is-visible` to align with the unified observer.
- **Theme page creation is one-shot, gated by `SKYYROSE_SETUP_VERSION`** (`inc/theme-activation-setup.php`). Init hook (`add_action('init', ..., 30)`) calls `skyyrose_run_activation_setup()` exactly once per setup version — gate: `if (get_option('skyyrose_activation_setup_version') === SKYYROSE_SETUP_VERSION) return;`. To re-create theme-owned pages that were deleted from WP admin, bump the constant in source. Next request fires `wp_insert_post()` for any missing slug returned by `get_page_by_path()`, assigning `_wp_page_template` meta. Bumped `4.0.0 → 4.1.0` on 2026-05-12 (theme 1.1.2, commit `016f7025f`) to fix DATA-01 where all four `/collection-{slug}/` URLs were serving page-id-9822 (homepage) because the collection pages had been deleted. Post-deploy: pages now resolve to page-id 9454/9455/9456/9651. **DO NOT touch the DB or ask the user to re-create pages manually — bump the constant.**
- **Cursor/global enqueues that must vary by template gate on `skyyrose_get_current_template_slug()`.** Helper defined in `inc/enqueue.php`, maps `template-immersive-*.php → 'immersive'`. Any enqueue inside `skyyrose_enqueue_global_scripts()` (priority 10, every page) that should be suppressed on immersive must wrap in `if ('immersive' !== skyyrose_get_current_template_slug()) { wp_enqueue_script(...); }`. **CURS-03 fix** (theme 1.1.2, commit `016f7025f`): `skyyrose-luxury-cursor` enqueue at `inc/enqueue.php:247-263` was unconditional; cursor JS shipped to immersive pages where the cursor is CSS-hidden. Now gated; cursor JS no longer downloads on `/experience-{slug}/` URLs. If an asset is CSS-hidden on a template, the JS enqueue should also be suppressed — don't ship dead bytes. The slug helper is the project's canonical mechanism; do not introduce parallel `is_page_template()` checks.

- **Sherpa render identity (2026-06-10, founder-confirmed):** the red-rose closed-jacket render mis-filed at `black-rose-sherpa-jacket/black-rose-sherpa-jacket-front-model.webp` is the SIGNATURE Sherpa — renamed to `signature-sherpa-jacket-front-closed.webp` and wired as sg-009 `front_model_image` (was ghost). br-006's true front model = flat `black-rose-sherpa-jacket-front-model.webp` (hooded satin, silver rose). Never reuse `black-rose-sherpa-jacket/` subdir filenames as identity evidence — verify the pixels.

### WordPress Deploy
- Dirty working tree on main blocks `git merge` — always stash unrelated changes before merging worktree branches
- `mv: preserving permissions` warnings during deploy are cosmetic (WordPress.com hosting restriction) — files transfer correctly
- After deploy: verify HTTP status on homepage + search + 404 + cart + shop AND verify new asset URLs return 200
- Search page uses `'search'` slug in `enqueue.php` — must come BEFORE the `is_home() || is_archive() || is_search()` blog catch-all
- Size guide modal, cookie consent, mobile nav are all `get_template_part()` calls in `footer.php` — order matters (size guide → cookie consent → mobile nav → toast container)
- Pre-order functions extracted to `inc/woocommerce-preorder.php` — woocommerce.php no longer has pre-order meta boxes
- `toast.js` provides global `window.skyyToast(msg, type, duration)` — all components should use this, not custom toast implementations
- **Hot-swap deploy is the default** (since 2026-04-11) — `scripts/deploy-theme.sh` uses atomic mv on the remote (`mv current → .old.$ts; mv new → path`) instead of the old `wp maintenance-mode` + `rm -rf && mv` pattern. The swap window is microseconds instead of ~60 seconds, so Jetpack Uptime stops firing false-positive "site is down" alerts on every deploy. Pass `--with-maintenance` only when deploying DB migrations or plugin changes that require the site to be locked.
- **Deploy script has a post-verify gate** — `verify_live()` curls `https://skyyrose.co/?deploy_verify=$ts` after cache flush and asserts HTTP 200, response size >= 50 KB, and absence of PHP error markers (`Fatal error`, `Parse error`, `Call to undefined`, `There has been a critical error`). Deploy exits non-zero on failure. Override target URL via `PUBLIC_URL` env var.
- **Jetpack Uptime alerts during deploy are a lagging indicator** — if one fires immediately after a deploy, it almost always points at a 503 window from `--with-maintenance` mode. Ignore the first alert within ~5 min of a legacy maintenance-mode deploy; investigate only if Jetpack's next poll cycle still reports down.

### Audit Discipline
- **[2026-05-24] WebFetch strips `<script>` tags during HTML → Markdown conversion. Never use it to audit JSON-LD, OpenGraph script blocks, inline JS, or any content inside `<script>`.** Use `curl -s URL | grep` or `curl -s URL | grep -oE '<meta property="og:..."'` instead. **Why:** the 2026-05-23 SEO audit reported "zero JSON-LD on all 4 pages, OG tags absent" as a P0 finding. Live curl + grep showed 2 JSON-LD blocks per page (Product, BreadcrumbList, ItemList, Organization) + full OG markup. The audit agent had used WebFetch which stripped both. Cost: ~1500 tokens of bad analysis + a near-miss on shipping a "fix" for a non-bug. **How to apply:** any structured-data audit agent brief must explicitly forbid WebFetch and require curl + grep for inspection.
- **[2026-05-24] WP.com Batcache serves stale HTML for ~minutes after `wp cache flush`. Always cache-bust post-deploy verifies with a unique query param.** Use `curl -s "https://skyyrose.co/?cb=$(date +%s)"` not `curl -s https://skyyrose.co/`. **Why:** PERF-03 from the audit was reported as a real bug because un-cache-busted curl showed `<div style="background-image">` (pre-deploy markup), but the deploy had already shipped the v1.5.17 LCP refactor with `<picture><img fetchpriority="high">`. Cache-busted curl confirmed source matched live.
- **[2026-05-24] Cerebrum claim "All innerHTML Uses Cleared" (obs #6378) is stale.** As of theme v1.1.2, `assets/js/smart-showcase.js:34,107,115` and `assets/js/immersive-wc-bridge.js:56` still have active `innerHTML` writes. Two HIGH security findings open per security-audit.md. Fix path: `createElement` for the hardcoded template, `DOMParser.parseFromString` for the WC AJAX fragment parse.
- **[2026-05-24] aos/cognition/reflector.py `classify_failure` is the public name (renamed from `_classify_failure`).** `aos/kernel/kernel.py:466` imports and calls it. Helpers used cross-module become public — strip the underscore.
- **[2026-05-24] WordPress Site Title canonical = "SkyyRose"** — not "The Skyy Rose Collection". Lives in wp-admin → Settings → General, propagates through every `<title>` + `og:site_name`.
- **[2026-05-24] Cart page must use `[woocommerce_cart]` shortcode, NOT Elementor HTML widget.** Theme's `woocommerce/cart/cart.php` override only renders along the shortcode path. Elementor widget content bypasses → coupon input has no backend (100% broken), "Continue Shopping" goes to homepage, checkout URL hardcoded to `/?page_id=9452`.
- **[2026-05-24] "Complete the Look" cross-sell unhooked per founder canon.** `add_action('woocommerce_single_product_summary', 'skyyrose_complete_the_look', 50)` at `inc/woocommerce.php:541` commented out. Template + function retained for one-line reactivation if revisited. Founder rule: no related products on PDP, garment is the protagonist.
- **[2026-05-24] Multi-agent audit P0 false-positive rate ~25%.** The 2026-05-23 audit reported 12 P0s; verification collapsed to 9 actionable. Always curl + grep live state before drafting any audit fix. The audit is the starting point, not the truth.
- **[2026-05-24] Cavecrew chain (investigator → builder → reviewer) compresses subagent tool-result tokens ~60-70% vs vanilla Explore + Edit + Code Reviewer.** For audit-driven sprints with 5+ delegations, this is the difference between finishing the session and hitting handoff. Don't use for prose-heavy review or architecture critique — vanilla is correct there.

### Hooks (macOS)
- Canonicalize paths (`/tmp` → `/private/tmp`)
- Use `${VAR:-default}` for testable paths
- Reject flag-like targets: `case "$target" in -*) exit 0 ;; esac`

### Vercel
- `rootDirectory` set → reads that dir's `vercel.json`, not root
- **`outputFileTracingRoot` above the Vercel project root causes a doubled-path bug.** With `rootDirectory=frontend`, Vercel's project cwd is `/vercel/path1/`. If `frontend/next.config.ts` sets `outputFileTracingRoot: path.resolve(__dirname, '..')` = `/vercel/`, the post-build trace stage emits paths relative to that root (`path1/.next/...`), then Vercel re-prepends the project cwd when resolving — yielding `/vercel/path1/path1/.next/routes-manifest.json` and crashing with `ENOENT: no such file or directory`. **Fix**: gate the override on `process.env.VERCEL` so it only applies locally. On Vercel, only `frontend/` is uploaded, so the override isn't needed (no ambiguous-lockfile warning to suppress). See `frontend/next.config.ts` (PR #494, 2026-05-07).
- A failed Vercel build does NOT take production down. Vercel keeps the alias on the last green deployment when new builds fail — the site stays up serving stale code. Symptom: every recent deploy shows `state: ERROR` in `vercel list_deployments`, but `curl https://devskyy.app/` returns 200. Treat as P1 (deploy pipeline blocked) not P0 (site down).

### Frontend (Next.js 16, `frontend/`)
- **Cache Components mode (`cacheComponents: true`) requires `<Suspense>` boundaries around every request-time data reader.** That includes `usePathname()`, `useSearchParams()`, `use(params)`, `use(searchParams)`, `cookies()`, and `headers()`. Without a `<Suspense>` wrapper, the build fails with `Error: Route "X": Uncached data was accessed outside of <Suspense>. This delays the entire page from rendering, resulting in a slow user experience` and exits 1 during static prerender.
- **Two patterns to wrap them**:
  1. **Wrap at the mount point** (best for layouts that compose dynamic chrome like sidebars, mascots): in the parent layout, do `<Suspense fallback={null}><Component /></Suspense>`.
  2. **Internal split** (best for reusable components and pages): rename the original function to `*Content`, then export a small wrapper that does `<Suspense fallback={<Skeleton/>}><Content /></Suspense>`.
- For decorative chrome (sidebar, tab bar, mascot bubble), `fallback={null}` is fine — the component would render nothing pre-hydration anyway. For data-heavy pages, the fallback is a skeleton matching the eventual content shape.
- Routes that correctly use the pattern show as `◐ (Partial Prerender)` in the build's route table — that's the desired Cache Components outcome (static shell + streaming dynamic content). See `frontend/app/admin/elite-studio/operations/[id]/page.tsx` for the canonical split. (PR #493, 2026-05-07).

---

## Behavioral Standards — How Claude Operates in This Project

These rules govern every action, not just pipelines. They apply to tool use, web search, code, communication, and decisions.

---

### Communication

**Never say these things:**
- "I'll now...", "Let me...", "Great!", "Certainly!", "Of course!"
- "I hope this helps", "Let me know if you need anything else"
- "I apologize for the confusion" — fix it, don't announce it
- Any preamble before the answer. Start with the answer.
- Any summary after the answer unless explicitly asked for one

**Do say:**
- The answer, immediately
- What you did, in one line, after doing it
- "I don't know" when you don't — then say what you'll do to find out
- "Wrong approach — here's why, and here's the correct path" when correcting course

**Tone:** Staff engineer talking to the founder. Direct, specific, no hedging, no performance of effort.

---

### Tool Use — Efficiency Rules

**Before making any tool call, ask: do I already have this?**

If the answer is in your context window → use it. Do not search.
If you read a file earlier in this session → use that. Do not re-read.
If you know the API → use it. Do not fetch the docs.

**Specific rules:**

- **No redundant reads.** File read once = available for the rest of the session. Re-reading wastes tokens and time.
- **Batch file reads.** If you need 3 files, call `read_multiple_files` once. Not 3 separate reads.
- **No confirmation fetches.** Don't fetch a URL to confirm something you can verify logically or from context.
- **No exploratory tool spam.** Don't list a directory, then read 5 files one by one, then list again. Plan first, then execute in the minimum tool calls.
- **One search, targeted.** If searching, write the query that gets the answer in one call. Three vague searches ≠ one good search.

---

### Web Search — Decision Rules

**Search when:**
- The answer depends on current state (prices, live site content, API status, recent events)
- You need a real URL, version number, or spec that could have changed
- The user explicitly asks you to look something up

**Do NOT search when:**
- You already know the answer from training or this session's context
- The question is about this codebase — read the code instead
- You're searching "just to be sure" — that's insecurity, not diligence
- You already searched for this in the current session

**If you search and get the answer → cite it and move on. Do not search again to verify the first search.**

---

### The Act vs Ask Decision Gate

One rule: **does this action cost money, touch production, or is it irreversible?**

| Condition | Action |
|-----------|--------|
| Costs money (any paid API call) | Show manifest + cost → ask |
| Touches production (deploy, WC write, media upload) | Show exactly what → ask |
| Irreversible (delete, overwrite, rename real data) | Show exactly what → ask |
| Everything else | Do it |

Do not ask permission to read files, write code, run tests, or do research. Do not ask "should I proceed?" after every step of a multi-step task. Plan → confirm the plan → execute without interruption.

**Asking a clarifying question is not weakness. Burning money or breaking the site because you assumed is.**

---

### Output Quality — Production Standard

Every output delivered in this project is production-ready. Not a draft. Not a proof of concept. Not "good enough for now."

**Code:**
- Error handling on every external call
- No `TODO`, `FIXME`, `pass`, or `raise NotImplementedError` in delivered code
- Follows existing patterns in this codebase — read before writing
- Tested or testable — if not, say why

**Files and configs:**
- Complete, not partial. If the task is "write this config", the config is complete.
- No placeholder values unless the user is expected to fill them (and they're clearly marked)

**Answers:**
- If you're not sure, say so — then give your best answer with the uncertainty named
- Don't give a confident wrong answer. Don't give a hedged correct one either.
- One clear answer > three possibilities with caveats

---

### After a Mistake

1. Fix it
2. In one sentence: what was wrong and why
3. In one sentence: what you changed to prevent it recurring
4. Update `tasks/lessons.md`
5. Move on

Do not: apologize repeatedly, re-explain the mistake at length, ask if the fix is acceptable before showing it. Fix it, show it, name the lesson.

---

### Task Execution

For any task with 3+ steps:
1. Write the plan to `tasks/todo.md` (checkboxes)
2. State the plan in one paragraph — get confirmation before implementing
3. Execute without interruption
4. Mark items complete as you go
5. At the end: one-paragraph summary of what changed and how to verify

For single-step tasks: just do it.

For ambiguous tasks: state your interpretation, execute against it. Don't ask for clarification on something you can resolve with a reasonable assumption — state the assumption.

---

## STOP AND SHOW — Non-Negotiable Confirmation Protocol

**This section overrides every other instruction in this file.**

Before taking any of the actions below, Claude MUST stop, print exactly what it is about to do, and wait for explicit "y" or "yes" from the user. No exceptions. Apologizing after is not acceptable — the damage is already done.

### Actions that require explicit confirmation BEFORE execution:

**Money / Credits**
- Any call to FASHN API (tryon, product-to-model, edit, model-create, image-to-video)
- Any call to Gemini, GPT-Image, FLUX, or other paid image generation endpoints
- Any call to OpenAI, Anthropic, or Google APIs that incur per-token or per-image cost
- Any HuggingFace Space invocation that uses paid compute

**Production site**
- Any `deploy-theme.sh` execution or SFTP file transfer to skyyrose.co
- Any WooCommerce REST API write (create/update/delete product, order, or media)
- Any WordPress Media Library upload
- Any cache flush or CDN purge on the live site

**File operations with real data**
- Reading from Photos Library or `~/Pictures/` paths is ALLOWED when the user has shared a specific file path in the current conversation (pasted or attached). Confirmation is implicit in the share.
- Using any file as the source image for a PAID API call (FASHN, Gemini generation, FLUX, Replicate, etc.) — must confirm the file is the correct garment before dispatch.
- Uploading any file to WooCommerce, the live WordPress site, or any external destination — must confirm.
- Deleting, overwriting, or renaming any file outside `/tmp/` or `renders/output/` — must confirm.

### What the confirmation must look like:

```
STOP — Confirm before proceeding:

Action : FASHN tryon
SKU    : br-001
Source : /path/to/exact/file.jpg  (81KB, 2023-10-02)
Cost   : ~$1.20  (4 models × 4 samples × $0.075)

Proceed? [y/N]
```

Show the exact file path, exact cost, and exact action — not a summary, the literal values. Then wait.

### What "autonomous" means in this project:

"Autonomous" means Claude handles implementation without hand-holding **after the user has confirmed the plan and inputs**. It does NOT mean Claude decides what files to use, what to deploy, or what API calls to make without checking first.

The pattern "act → apologize → act again → apologize again" is a bug, not a feature. If the right source file is unclear, ask. If the deploy target is ambiguous, ask. One question costs zero dollars. Getting it wrong costs real money and breaks the live site.

---

## Self-Correction

1. Fix the issue → 2. Add Learnings entry above → 3. Commit both together
