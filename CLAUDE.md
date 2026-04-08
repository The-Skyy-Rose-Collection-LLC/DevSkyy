# DevSkyy — Claude Code Configuration

## Identity
You are the DevSkyy engineering agent. 100% quality, no stubs, no partial deliverables.

---

## Anti-Hallucination Protocol
**If you haven't read it, you don't know it.** Every claim traces to a tool call or user confirmation from THIS session. Say "I don't know" when you don't. Read source → Search codebase → Check memory → Ask user → State uncertainty. Never invent.

---

## Harness Architecture

Each component owns exactly ONE concern. If a clause appears in two places, one must be deleted.

| Component | Location | Source of Truth For |
|-----------|----------|---------------------|
| **CLAUDE.md** | This file | Project identity, architecture, workspaces, brand, deploy, learnings |
| **Rules** | `.claude/rules/` | Constraints and boundaries (coding, testing, security, git, WordPress, workflow) |
| **Hooks** | `.claude/hooks/` | Automated lifecycle behaviors (format, lint, deploy verify, memory) |
| **Agents** | `.claude/agents/` | Specialized roles — WHO does the work |
| **Commands** | `.claude/commands/` | User-invocable workflows — WHAT verbs to run |
| **Skills** | `.claude/skills/` | Reusable domain knowledge — expertise modules |
| **Contexts** | `.claude/contexts/` | Behavioral modes — HOW to operate |

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
wordpress-theme/skyyrose-flagship/  → Production WP theme (v5.2.0)
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
| **Imagery** | Python (isolated) | `.venv-imagery/` | `pip install rembg` | — |
| **ADK Agents** | Python (isolated) | `.venv-agents/` | `pip install google-adk` | — |

**Each workspace is self-contained.** Don't mix `frontend/node_modules` with root. Don't use `.venv` for ADK (numpy conflicts).

---

## WordPress Theme (skyyrose-flagship)

**256 files, 20 directories. Production at skyyrose.co**

```
wordpress-theme/skyyrose-flagship/
├── assets/css/      43 files (page CSS, holo cards, tokens, components)
├── assets/js/       23 files (holo cards, navigation, page-specific)
├── assets/fonts/    19 files (self-hosted woff2, GDPR-compliant)
├── inc/             21 modules (enqueue, security, WC, ajax, SEO)
├── template-parts/  37 partials (product-card-holo.php = holo card system)
├── woocommerce/      5 overrides (cart, checkout, single-product)
└── *.php            24 page templates
```

**Active templates:**
- `front-page.php` — Three.js portals (3 collection rings + particles)
- `template-collection-{signature,black-rose,love-hurts,kids-capsule}.php` — Collection pages
- `template-preorder-gateway.php` — Pre-order with collection selector
- `template-immersive-{signature,black-rose,love-hurts}.php` — 3D experiences
- `template-about.php` — Brand story + timeline

**Key systems:**
- `product-card-holo.css/js` — Holographic glass cards with magnetic tilt
- `inc/enqueue.php` — All CSS/JS loading, template slug detection
- `inc/security.php` — CSP headers, rate limiting, ABSPATH guards
- `functions.php` — Theme constants, includes array (v5.2.0)

> WordPress coding rules → See `.claude/rules/wordpress.md`

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
- `agents/base_super_agent.py` is the foundation (not legacy files)
- DataLoaders → `api/graphql/dataloaders/` (not `core/`)
- Integration tests → `tests/integration/` (not `tests/api/`)

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

### WordPress Deploy
- Dirty working tree on main blocks `git merge` — always stash unrelated changes before merging worktree branches
- `mv: preserving permissions` warnings during deploy are cosmetic (WordPress.com hosting restriction) — files transfer correctly
- After deploy: verify HTTP status on homepage + search + 404 + cart + shop AND verify new asset URLs return 200
- Search page uses `'search'` slug in `enqueue.php` — must come BEFORE the `is_home() || is_archive() || is_search()` blog catch-all
- Size guide modal, cookie consent, mobile nav are all `get_template_part()` calls in `footer.php` — order matters (size guide → cookie consent → mobile nav → toast container)
- Pre-order functions extracted to `inc/woocommerce-preorder.php` — woocommerce.php no longer has pre-order meta boxes
- `toast.js` provides global `window.skyyToast(msg, type, duration)` — all components should use this, not custom toast implementations

### Hooks (macOS)
- Canonicalize paths (`/tmp` → `/private/tmp`)
- Use `${VAR:-default}` for testable paths
- Reject flag-like targets: `case "$target" in -*) exit 0 ;; esac`

### Vercel
- `rootDirectory` set → reads that dir's `vercel.json`, not root

---

## Self-Correction

1. Fix the issue → 2. Add Learnings entry above → 3. Commit both together
