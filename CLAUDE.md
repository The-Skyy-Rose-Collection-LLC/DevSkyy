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

1. **Context7** → `resolve-library-id` → `query-docs` BEFORE any library code
2. Read existing code first, then `Edit` (targeted) or `Write` (new files only)
3. TDD: RED → GREEN → IMPROVE
4. `pytest -v` after EVERY change — target 85%+ coverage
5. Format: `isort . && ruff check --fix && black .`
6. After corrections → add Learnings entry, commit fix + learning together

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
- Collection page CSS loads via `$standalone_css_map` — don't duplicate with inline enqueues
- Holo card grid: only `.product-grid`, `.product-grid__items`, `.br-product-grid__items` should be `display: grid`

### Hooks (macOS)
- Canonicalize paths (`/tmp` → `/private/tmp`)
- Use `${VAR:-default}` for testable paths
- Reject flag-like targets: `case "$target" in -*) exit 0 ;; esac`

### Vercel
- `rootDirectory` set → reads that dir's `vercel.json`, not root

---

## Self-Correction

1. Fix the issue → 2. Add Learnings entry above → 3. Commit both together
