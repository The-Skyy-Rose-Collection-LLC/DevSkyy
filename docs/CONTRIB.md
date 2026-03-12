# DevSkyy Contributor Guide

**Last Updated**: 2026-03-12
**Source of Truth**: `package.json`, `Makefile`, `.env.example`

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

| Venv | Purpose | Setup |
|------|---------|-------|
| `.venv` | Main (FastAPI, diffusers, torch) | `python -m venv .venv && pip install -r requirements.txt` |
| `.venv-imagery` | Image processing (rembg, BRIA, genai) | `python -m venv .venv-imagery && pip install -r requirements-imagery.txt` |
| `.venv-lora` | LoRA training | `python -m venv .venv-lora` |
| `.venv-agents` | Google ADK (conflicts with numpy) | `python -m venv .venv-agents` |

## Available Scripts

### Python (via Makefile)

| Command | Description |
|---------|-------------|
| `make install` | Install production Python dependencies |
| `make dev` | Install Python + TypeScript dev dependencies |
| `make test` | `pytest tests/ -v --tb=short` |
| `make test-fast` | `pytest -x -q` (stop on first failure) |
| `make test-cov` | pytest with coverage report |
| `make format` | `isort . && ruff check --fix && black .` |
| `make lint` | `ruff check . && mypy` |
| `make format-all` | Python + TypeScript formatting |
| `make lint-all` | Python + TypeScript linting |
| `make ci` | Full local CI (lint-all + test-all) |

### Node.js (via npm)

| Command | Description |
|---------|-------------|
| `npm run build` | TypeScript compilation |
| `npm run build:watch` | TypeScript compilation (watch mode) |
| `npm run dev` | Dev server with nodemon |
| `npm run start` | Production server |
| `npm run test` | Jest test suite |
| `npm run test:watch` | Jest in watch mode |
| `npm run test:coverage` | Jest with coverage |
| `npm run test:ci` | CI mode (no watch, coverage) |
| `npm run lint` | ESLint |
| `npm run lint:fix` | ESLint with auto-fix |
| `npm run format` | Prettier (write) |
| `npm run format:check` | Prettier (check only) |
| `npm run type-check` | TypeScript type checking |
| `npm run clean` | Remove dist/ and coverage/ |
| `npm run prepare` | Husky setup + build (runs on `npm install`) |
| `npm run precommit` | lint + type-check + test:ci |
| `npm run security:audit` | `npm audit` |
| `npm run security:fix` | `npm audit fix` |
| `npm run deps:check` | `npm outdated` |
| `npm run deps:update` | `npm update` |
| `npm run demo:collections` | List all available 3D demos |
| `npm run demo:black-rose` | Launch Black Rose 3D demo |
| `npm run demo:signature` | Launch Signature 3D demo |
| `npm run demo:love-hurts` | Launch Love Hurts 3D demo |
| `npm run demo:showroom` | Launch Showroom 3D experience |
| `npm run demo:runway` | Launch Runway 3D experience |
| `npm run test:collections` | Test collection experiences |

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
├── main_enterprise.py          # FastAPI app (47+ endpoints)
├── devskyy_mcp.py              # MCP server (20+ tools)
├── frontend/                   # Next.js 16 + React 19
├── wordpress-theme/            # SkyyRose Flagship theme
│   └── skyyrose-flagship/
├── agents/                     # 54 specialized agents
├── api/v1/                     # REST routes
├── core/                       # Foundation (zero external deps)
├── orchestration/              # RAG, LangGraph workflows
├── services/                   # ML, 3D, Analytics
├── security/                   # JWT, OAuth2, AES-256-GCM
├── scripts/                    # Active utilities (deploy, verify, php-lint)
├── tests/                      # pytest + jest
└── docs/                       # Documentation
    └── archive/                # Historical docs
```

## Critical Rules

- Files < 800 lines, functions < 50 lines
- No hardcoded secrets — use env vars
- Validate inputs: Zod (frontend), Pydantic (backend)
- Python line length: 100
- Use `npm` not `pnpm` (Vercel compat on Node 22+)
- WordPress: extend via hooks, never modify core
