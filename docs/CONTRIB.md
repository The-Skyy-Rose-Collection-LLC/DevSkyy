# DevSkyy Contributor Guide

**Last Updated**: 2026-05-07
**Source of Truth**: `package.json`, `frontend/package.json`, `Makefile`, `.env.example`

> Sections marked `<!-- AUTO-GENERATED -->` are synced from source-of-truth files by `/update-docs`. Edit the source, not the table — manual changes between markers will be overwritten.

---

## Quick Start

```bash
# 1. Clone & install
git clone https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy.git
cd DevSkyy
make install                  # Python production deps
npm install                   # Node deps (use npm, NOT pnpm)

# 2. Environment
cp .env.example .env          # Fill in API keys
cp .env.wordpress.example .env.wordpress  # WordPress credentials

# 3. Verify
python -c "import fastapi; print('Python OK')"
npm run type-check            # TypeScript OK
```

## Virtual Environments

Each workspace is self-contained. Don't mix `frontend/node_modules` with root, and don't share venvs across runtimes that conflict (ADK + numpy).

| Venv | Runtime | Purpose | Setup |
|------|---------|---------|-------|
| `.venv` | Python 3.13 | Main (FastAPI, diffusers, torch) + Nano Banana imagery | `python -m venv .venv && pip install -e ".[all]"` |
| `.venv-agents` | Python (isolated) | Google ADK agents (conflicts with numpy in `.venv`) | `python -m venv .venv-agents && pip install google-adk` |

> `.venv-imagery` was an earlier design that was never created — Nano Banana shares the main `.venv/`. Do not create a separate imagery venv.

## Available Scripts

<!-- AUTO-GENERATED:scripts:Makefile + package.json + frontend/package.json -->

### Python (via Makefile, run from repo root)

| Command | Description |
|---------|-------------|
| `make install` | `pip install -e .` — install production Python deps |
| `make dev` | `pip install -e ".[dev]" && npm install` — install Python + Node dev deps |
| `make lint` | `ruff check . && mypy --ignore-missing-imports .` (mypy non-blocking) |
| `make lint-strict` | Same as `lint`, but mypy errors block |
| `make format` | `isort . && ruff check --fix && black .` |
| `make test` | `pytest tests/ -v --tb=short` |
| `make test-fast` | `pytest -x -q` (stop on first failure) |
| `make test-cov` | pytest with HTML + terminal coverage report |
| `make security` | `bandit -r . -x ./tests -ll && npm audit` |
| `make clean` | Remove `build/ dist/ *.egg-info/ .pytest_cache/ .mypy_cache/ .ruff_cache/ htmlcov/ .coverage __pycache__/ *.pyc` |

### TypeScript (via Makefile, delegates to npm)

| Command | Description |
|---------|-------------|
| `make ts-build` | `npm run build` — compile TypeScript |
| `make ts-lint` | `npm run lint` — ESLint |
| `make ts-lint-fix` | `npm run lint:fix` — ESLint with auto-fix |
| `make ts-test` | `npm run test -- --passWithNoTests --no-coverage` (coverage non-blocking) |
| `make ts-test-strict` | `npm run test` (coverage thresholds enforced) |
| `make ts-test-collections` | `npm run test:collections` |
| `make ts-type-check` | `npm run type-check` — `tsc --noEmit` |
| `make ts-format` | `npm run format` — Prettier write |

### Unified

| Command | Description |
|---------|-------------|
| `make test-all` | `make test && make ts-test` |
| `make lint-all` | `make lint && make ts-type-check` |
| `make format-all` | `make format && make ts-format` |
| `make ci` | `make lint-all && make test-all` — full local CI pipeline |
| `make build` | `make clean && make ts-build && python -m build` |

### 3D Collection Demos

| Command | Description |
|---------|-------------|
| `make demo-black-rose` | Vite preview of Black Rose 3D experience |
| `make demo-signature` | Vite preview of Signature 3D experience |
| `make demo-love-hurts` | Vite preview of Love Hurts 3D experience |
| `make demo-showroom` | Vite preview of Showroom experience |
| `make demo-runway` | Vite preview of Runway experience |

### Docker

| Command | Description |
|---------|-------------|
| `make docker-build` | `docker build -t devskyy:latest .` |
| `make docker-run` | `docker run -p 8000:8000 devskyy:latest` |

### Root npm scripts (`package.json`)

| Command | Description |
|---------|-------------|
| `npm run build` | `tsc --project config/typescript/tsconfig.json` |
| `npm run build:watch` | TypeScript compile in watch mode |
| `npm run dev` | Dev server with nodemon (`src/index.ts`) |
| `npm run start` | `node dist/index.js` |
| `npm run test` | Jest (`config/testing/jest.config.cjs`) |
| `npm run test:watch` | Jest watch mode |
| `npm run test:coverage` | Jest with coverage |
| `npm run test:ci` | CI mode (no watch, coverage, `--watchAll=false`) |
| `npm run lint` / `lint:fix` | ESLint (with auto-fix on the second) |
| `npm run format` / `format:check` | Prettier (write / check-only) |
| `npm run type-check` | `tsc --noEmit` |
| `npm run clean` | `rm -rf dist coverage` |
| `npm run prepare` | Husky setup + build (runs on `npm install`) |
| `npm run precommit` | `lint && type-check && test:ci` |
| `npm run security:audit` / `security:fix` | `npm audit` / `npm audit fix` |
| `npm run deps:check` / `deps:update` | `npm outdated` / `npm update` |
| `npm run demo:black-rose` / `signature` / `love-hurts` / `showroom` / `runway` | Vite-served 3D collection demos |
| `npm run test:collections` | Jest tests for collection experiences |

### Dashboard (`frontend/package.json`, run from `frontend/`)

The Vercel-deployed Next.js admin dashboard at devskyy.app. **Use `npm`, not `pnpm`** — pnpm fails on Vercel with `ERR_INVALID_THIS` on Node 22+.

| Command | Description |
|---------|-------------|
| `npm run dev` | `next dev` — local dev server |
| `npm run build` | `next build` — production build |
| `npm run start` | `next start` — serve production build |
| `npm run lint` | ESLint |
| `npm run type-check` | `tsc --noEmit` |
| `npm run test:e2e` | `playwright test` |
| `npm run test:e2e:ui` | Playwright with the UI runner |
| `npm run deploy` / `deploy:prod` | `vercel` / `vercel --prod` |
| `npm run deploy:auto` / `deploy:auto:prod` | Scripted deploy via `tsx scripts/deploy.ts` |
| `npm run vercel:link` / `vercel:link:auto` | Link CLI to the `devskyy` Vercel project |
| `npm run vercel:env:pull` / `vercel:env:push` | Sync Vercel env to `.env.local` / push to production |
| `npm run vercel:logs` / `vercel:inspect` / `vercel:project` | Vercel diagnostics |

<!-- /AUTO-GENERATED:scripts -->

## Environment Variables

Copy `.env.example` and fill in values. Required variables by category:

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET_KEY` | **Production** | 64+ char secret for JWT signing |
| `ENCRYPTION_MASTER_KEY` | **Production** | Base64-encoded AES-256 key |
| `DATABASE_URL` | Yes | SQLite (dev) or PostgreSQL (prod) |
| `OPENAI_API_KEY` | Optional | OpenAI API access |
| `ANTHROPIC_API_KEY` | Optional | Anthropic API access |
| `GOOGLE_AI_API_KEY` | Optional | Google AI API access |
| `STRIPE_API_KEY` | Optional | Stripe payments |
| `STRIPE_WEBHOOK_SECRET` | Optional | Stripe webhook verification |
| `HF_TOKEN` | Optional | HuggingFace inference/datasets |
| `TRIPO_API_KEY` | Optional | Tripo3D 3D asset generation |
| `FASHN_API_KEY` | Optional | FASHN virtual try-on |
| `WORDPRESS_URL` | Optional | WordPress site URL |
| `WOOCOMMERCE_KEY` | Optional | WooCommerce REST API consumer key |
| `WOOCOMMERCE_SECRET` | Optional | WooCommerce REST API consumer secret |
| `KLAVIYO_PRIVATE_KEY` | Optional | Klaviyo email marketing |
| `REDIS_URL` | Optional | Redis caching |
| `SENTRY_DSN` | Optional | Error monitoring |
| `RATE_LIMIT_REQUESTS` | Optional | Requests per window (default: 100) |
| `RATE_LIMIT_WINDOW_SECONDS` | Optional | Rate limit window (default: 60s) |

**Frontend** (in `frontend/.env.local`, copy from `frontend/.env.example`):

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend API URL |
| `NEXT_PUBLIC_WS_URL` | Yes | WebSocket URL |
| `NEXTAUTH_SECRET` | Yes | NextAuth session secret |
| `NEXT_PUBLIC_WORDPRESS_URL` | Optional | WordPress for WooCommerce integration |

Generate secrets:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"         # JWT key
python -c "import secrets,base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"  # AES key
```

## Testing

```bash
# Python
make test                              # Full suite
make test-fast                         # Stop on first failure
pytest tests/unit/test_foo.py -v       # Single file
pytest tests/ -k "test_name" -v       # Single test by name
pytest tests/ -m integration           # By marker

# TypeScript
npm run test                           # Jest
npm run test:coverage                  # With coverage

# Both
make test-all                          # Python + TypeScript
```

Target: **85%+ coverage**. Run `make test-cov` to check.

## Code Style

| Tool | Language | Config |
|------|----------|--------|
| Black | Python | Line length: 100 |
| Ruff | Python | Linting + import sorting |
| isort | Python | Import organization |
| ESLint | TypeScript | `src/**/*.{ts,tsx}` |
| Prettier | TypeScript | `src/**/*.{ts,tsx}` |
| mypy | Python | Type checking |

Run before committing: `make format && make lint`

## Git Conventions

**Branch naming**: `<type>/<description>` (e.g., `feat/immersive-worlds`, `fix/wp-csp-headers`)

**Commit messages**: `<type>: <description>`

| Type | Use for |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code restructuring |
| `docs` | Documentation |
| `test` | Tests |
| `chore` | Maintenance |
| `perf` | Performance |
| `style` | Formatting |

## Project Structure

```
DevSkyy/
├── main_enterprise.py          # FastAPI app — REST + GraphQL + webhooks
├── devskyy_mcp.py              # MCP server (20+ tools)
├── frontend/                   # Next.js 16 + React 19 admin dashboard (devskyy.app)
├── wordpress-theme/
│   └── skyyrose-flagship/      # Production WordPress theme (skyyrose.co)
│       └── data/
│           └── skyyrose-catalog.csv   # CANONICAL product catalog (33 SKUs)
│       └── data/dossiers/      # Per-product design dossiers (RAS pipeline reads)
├── agents/                     # Specialized agents (count varies; never cite a fixed number)
│   └── base_super_agent/       # EnhancedSuperAgent foundation (PACKAGE, not flat .py)
├── api/v1/                     # REST routes
├── api/graphql/                # GraphQL schema + dataloaders
├── core/                       # Foundation: auth, cache, events, registry (zero external deps)
├── llm/                        # 6 providers: OpenAI, Anthropic, Google, Mistral, Cohere, Groq
├── orchestration/              # RAG, LangGraph, CrewAI workflows
├── services/                   # ML, 3D generation, analytics
├── security/                   # JWT, OAuth2, AES-256-GCM
├── skyyrose/elite_studio/      # Multi-agent image pipeline (compositor, creative graph)
├── scripts/                    # Active utilities (deploy, verify, php-lint, nano-banana)
├── tests/                      # pytest (Python) + jest (TypeScript)
└── docs/                       # Documentation
    └── archive/                # Historical docs
```

**Dependency flow:** `core → security → database/llm → orchestration/services → agents → api`

**Two independent systems** — do NOT cross-wire API calls or assume data sharing:
- `skyyrose.co` = WordPress.com Business plan (WooCommerce store, customer-facing) — no wp-cli, SFTP deploy only, no direct DB access
- `devskyy.app` = Vercel Next.js dashboard (internal pipelines, agent tools)

## Critical Rules

- Files < 800 lines, functions < 50 lines
- No hardcoded secrets — use env vars
- Validate inputs: Zod (frontend), Pydantic (backend)
- Python line length: 100
- Use `npm` not `pnpm` (Vercel compat on Node 22+)
- WordPress: extend via hooks, never modify core
